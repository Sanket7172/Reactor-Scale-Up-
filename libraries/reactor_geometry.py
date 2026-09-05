import math
import numpy as np


# =========================================================
# REACTOR HEAD LIBRARY
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


# Backward compatibility
HEADS = REACTOR_HEADS


# =========================================================
# BASIC GEOMETRY
# =========================================================

def head_depth(D, head_type):

    data = REACTOR_HEADS.get(
        head_type,
        {}
    )

    ratio = data.get(
        "depth_ratio",
        0.0
    )

    return D * ratio


def cylindrical_volume(D, H):

    return (
        math.pi /
        4.0 *
        D**2 *
        H
    )


# =========================================================
# HEAD VOLUME
# =========================================================

def head_volume(D, head_type):

    h = head_depth(
        D,
        head_type
    )

    if h <= 0:

        return 0.0

    area = (
        math.pi /
        4.0 *
        D**2
    )

    head_kind = REACTOR_HEADS[
        head_type
    ]["type"]

    if head_kind == "hemispherical":

        return (
            2.0 /
            3.0 *
            math.pi *
            (D / 2.0)**3
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

        # Screening approximation for
        # ellipsoidal / torispherical heads
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
# 2D VESSEL PROFILE
# =========================================================

def profile(
    D,
    straight_height,
    bottom_type,
    top_type,
    n_points=200,
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
    if bottom_h > 0:

        zb = np.linspace(
            0,
            bottom_h,
            max(20, n_points // 5)
        )

        ratio = zb / bottom_h

        rb = (
            D / 2.0 *
            np.sqrt(
                np.clip(
                    ratio,
                    0,
                    1
                )
            )
        )

    else:

        zb = np.array([0.0])

        rb = np.array([D / 2.0])

    # Straight shell
    zs = np.linspace(
        bottom_h,
        bottom_h + straight_height,
        max(30, n_points // 2)
    )

    rs = np.full_like(
        zs,
        D / 2.0
    )

    # Top head
    if top_h > 0:

        zt = np.linspace(
            bottom_h + straight_height,
            bottom_h + straight_height + top_h,
            max(20, n_points // 5)
        )

        ratio = (
            zt -
            (
                bottom_h +
                straight_height
            )
        ) / top_h

        rt = (
            D / 2.0 *
            np.sqrt(
                np.clip(
                    1.0 - ratio,
                    0,
                    1
                )
            )
        )

    else:

        zt = np.array([
            bottom_h +
            straight_height
        ])

        rt = np.array([0.0])

    z = np.concatenate([
        zb,
        zs[1:],
        zt[1:],
    ])

    r = np.concatenate([
        rb,
        rs[1:],
        rt[1:],
    ])

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
        D,
        straight_height,
        bottom_type,
        top_type,
        n_points=400,
    )

    return float(
        np.interp(
            z,
            z_profile,
            r_profile
        )
    )


# =========================================================
# VOLUME AT HEIGHT
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
        D,
        straight_height,
        bottom_type,
        top_type,
        n_points=800,
    )

    z = min(
        z,
        z_profile[-1]
    )

    mask = (
        z_profile <= z
    )

    zz = z_profile[mask]
    rr = r_profile[mask]

    if len(zz) < 2:

        return 0.0

    area = (
        math.pi *
        rr**2
    )

    try:

        volume = np.trapezoid(
            area,
            zz
        )

    except AttributeError:

        volume = np.trapz(
            area,
            zz
        )

    return float(
        volume
    )


# =========================================================
# LIQUID HEIGHT FROM WORKING VOLUME
# =========================================================

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

    total_volume = calculate_total_volume(
        D=D,
        straight_height=straight_height,
        bottom_type=bottom_type,
        top_type=top_type,
    )

    if working_volume <= 0:

        return (
            0.0,
            total_volume
        )

    if working_volume >= total_volume:

        return (
            total_height,
            total_volume
        )

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
        total_volume
    )
