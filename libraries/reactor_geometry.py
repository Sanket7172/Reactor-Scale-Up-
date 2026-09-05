import math
import numpy as np


# =========================================================
# HEAD DATABASE
# =========================================================

REACTOR_HEADS = {

    "Flat Bottom": {
        "type": "flat",
        "depth_ratio": 0.0,
    },

    "2:1 Ellipsoidal": {
        "type": "ellipsoidal",
        "depth_ratio": 0.25,
    },

    "10% Torispherical": {
        "type": "torispherical",
        "depth_ratio": 0.10,
    },

    "6% Torispherical": {
        "type": "torispherical",
        "depth_ratio": 0.06,
    },

    "Hemispherical": {
        "type": "hemispherical",
        "depth_ratio": 0.50,
    },

    "Conical": {
        "type": "conical",
        "depth_ratio": 0.25,
    },
}


HEADS = REACTOR_HEADS


# =========================================================
# HEAD DEPTH
# =========================================================

def head_depth(
    D,
    head_type,
):

    data = REACTOR_HEADS.get(
        head_type,
        {}
    )

    ratio = data.get(
        "depth_ratio",
        0.0
    )

    return D * ratio


# =========================================================
# CYLINDER VOLUME
# =========================================================

def cylindrical_volume(
    D,
    H,
):

    return (
        math.pi /
        4.0 *
        D ** 2 *
        H
    )


# =========================================================
# APPROXIMATE HEAD VOLUME
# =========================================================

def head_volume(
    D,
    head_type,
):

    h = head_depth(
        D,
        head_type
    )

    if h <= 0:
        return 0.0

    area = (
        math.pi /
        4.0 *
        D ** 2
    )

    head = REACTOR_HEADS[
        head_type
    ]

    head_kind = head[
        "type"
    ]

    if head_kind == "hemispherical":

        return (
            2.0 /
            3.0 *
            math.pi *
            (D / 2.0) ** 3
        )

    elif head_kind == "conical":

        return (
            1.0 /
            3.0 *
            area *
            h
        )

    elif head_kind == "flat":

        return 0.0

    else:

        # Screening approximation
        return (
            0.65 *
            area *
            h
        )


# =========================================================
# TOTAL VOLUME
# =========================================================

def calculate_total_volume(
    D,
    straight_height,
    bottom_type,
    top_type,
):

    cylinder = cylindrical_volume(
        D,
        straight_height
    )

    bottom = head_volume(
        D,
        bottom_type
    )

    top = head_volume(
        D,
        top_type
    )

    return (
        cylinder +
        bottom +
        top
    )


# =========================================================
# PROFILE
# =========================================================

def profile(
    D,
    straight_height,
    bottom_type,
    top_type,
    n_points=100,
):

    bottom_h = head_depth(
        D,
        bottom_type
    )

    top_h = head_depth(
        D,
        top_type
    )

    # Bottom
    zb = np.linspace(
        0,
        bottom_h,
        max(
            10,
            n_points // 5
        )
    )

    rb = np.zeros_like(
        zb
    )

    if bottom_h > 0:

        ratio = (
            zb /
            bottom_h
        )

        rb = (
            D /
            2.0 *
            np.sqrt(
                np.clip(
                    ratio,
                    0,
                    1
                )
            )
        )

    # Straight
    zs = np.linspace(
        bottom_h,
        bottom_h + straight_height,
        max(
            10,
            n_points // 2
        )
    )

    rs = np.full_like(
        zs,
        D / 2.0
    )

    # Top
    zt = np.linspace(
        bottom_h + straight_height,
        bottom_h + straight_height + top_h,
        max(
            10,
            n_points // 5
        )
    )

    rt = np.zeros_like(
        zt
    )

    if top_h > 0:

        ratio = (
            (
                zt -
                (
                    bottom_h +
                    straight_height
                )
            )
            /
            top_h
        )

        rt = (
            D /
            2.0 *
            np.sqrt(
                np.clip(
                    1.0 - ratio,
                    0,
                    1
                )
            )
        )

    z = np.concatenate(
        [
            zb,
            zs[1:],
            zt[1:],
        ]
    )

    r = np.concatenate(
        [
            rb,
            rs[1:],
            rt[1:],
        ]
    )

    return z, r


# =========================================================
# RADIUS AT HEIGHT
# =========================================================

def radius_at_height(
    z,
    D,
    straight_height,
    bottom_type,
    top_type,
):

    z_profile, r_profile = profile(
        D=D,
        straight_height=straight_height,
        bottom_type=bottom_type,
        top_type=top_type,
        n_points=300,
    )

    return float(
        np.interp(
            z,
            z_profile,
            r_profile,
        )
    )


# =========================================================
# LIQUID HEIGHT FROM VOLUME
# =========================================================

def volume_at_height(
    z,
    D,
    straight_height,
    bottom_type,
    top_type,
):

    z = max(
        0.0,
        z
    )

    z_profile, r_profile = profile(
        D=D,
        straight_height=straight_height,
        bottom_type=bottom_type,
        top_type=top_type,
        n_points=500,
    )

    z = min(
        z,
        z_profile[-1]
    )

    mask = (
        z_profile <= z
    )

    zz = z_profile[
        mask
    ]

    rr = r_profile[
        mask
    ]

    if len(zz) < 2:
        return 0.0

    # Numerical integration
    volume = np.trapezoid(
        math.pi *
        rr ** 2,
        zz
    )

    return float(
        volume
    )


def liquid_height_from_volume(
    working_volume,
    D,
    straight_height,
    bottom_type,
    top_type,
):

    total_height = (
        head_depth(
            D,
            bottom_type
        )
        +
        straight_height
        +
        head_depth(
            D,
            top_type
        )
    )

    total_volume = (
        calculate_total_volume(
            D=D,
            straight_height=straight_height,
            bottom_type=bottom_type,
            top_type=top_type,
        )
    )

    if working_volume <= 0:
        return 0.0, total_volume

    if working_volume >= total_volume:
        return total_height, total_volume

    low = 0.0
    high = total_height

    for _ in range(70):

        mid = (
            low +
            high
        ) / 2.0

        volume = volume_at_height(
            mid,
            D,
            straight_height,
            bottom_type,
            top_type,
        )

        if volume < working_volume:

            low = mid

        else:

            high = mid

    return (
        (low + high) / 2.0,
        total_volume,
    )
