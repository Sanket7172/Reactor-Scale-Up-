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


HEADS = REACTOR_HEADS


# =========================================================
# HEAD DEPTH
# =========================================================

def head_depth(D, head_type):

    data = REACTOR_HEADS.get(
        head_type,
        {}
    )

    return (
        D *
        data.get(
            "depth_ratio",
            0.0
        )
    )


# =========================================================
# CYLINDRICAL VOLUME
# =========================================================

def cylindrical_volume(D, H):

    return (
        math.pi *
        D**2 /
        4.0 *
        H
    )


# =========================================================
# HEAD VOLUME
# =========================================================

def head_volume(D, head_type):

    data = REACTOR_HEADS.get(
        head_type
    )

    if data is None:
        raise ValueError(
            f"Unknown reactor head: {head_type}"
        )

    kind = data["type"]

    h = head_depth(
        D,
        head_type
    )

    area = (
        math.pi *
        D**2 /
        4.0
    )

    if kind == "flat":
        return 0.0

    if kind == "hemispherical":

        R = D / 2.0

        return (
            2.0 /
            3.0 *
            math.pi *
            R**3
        )

    if kind == "conical":

        return (
            area *
            h /
            3.0
        )

    if kind == "ellipsoidal":

        # Ellipsoidal approximation
        # V = pi/6 * D² * h

        return (
            math.pi /
            6.0 *
            D**2 *
            h
        )

    if kind == "torispherical":

        # Preliminary engineering approximation.
        # Actual ASME geometry should be used for
        # final vessel fabrication design.

        return (
            0.85 *
            area *
            h
        )

    return 0.0


# =========================================================
# TOTAL VOLUME
# =========================================================

def calculate_total_volume(
    D,
    straight_height,
    bottom_type,
    top_type,
):

    return (
        cylindrical_volume(
            D,
            straight_height
        )
        +
        head_volume(
            D,
            bottom_type
        )
        +
        head_volume(
            D,
            top_type
        )
    )


# =========================================================
# PROFILE
# =========================================================

def profile(
    D,
    straight_height,
    bottom_type,
    top_type,
    n_points=300,
):

    bottom_h = head_depth(
        D,
        bottom_type
    )

    top_h = head_depth(
        D,
        top_type
    )

    # -----------------------------------------------------
    # Bottom
    # -----------------------------------------------------

    if bottom_h > 0:

        zb = np.linspace(
            0.0,
            bottom_h,
            max(
                30,
                n_points // 4
            )
        )

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
                    0.0,
                    1.0
                )
            )
        )

    else:

        zb = np.array([0.0])

        rb = np.array([
            D / 2.0
        ])

    # -----------------------------------------------------
    # Straight side
    # -----------------------------------------------------

    zs = np.linspace(
        bottom_h,
        bottom_h + straight_height,
        max(
            50,
            n_points // 2
        )
    )

    rs = np.full_like(
        zs,
        D / 2.0
    )

    # -----------------------------------------------------
    # Top
    # -----------------------------------------------------

    top_start = (
        bottom_h +
        straight_height
    )

    if top_h > 0:

        zt = np.linspace(
            top_start,
            top_start + top_h,
            max(
                30,
                n_points // 4
            )
        )

        ratio = (
            zt -
            top_start
        ) / top_h

        rt = (
            D /
            2.0 *
            np.sqrt(
                np.clip(
                    1.0 - ratio,
                    0.0,
                    1.0
                )
            )
        )

    else:

        zt = np.array([
            top_start
        ])

        rt = np.array([
            D / 2.0
        ])

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
# RADIUS
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
        top_type
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
        float(z)
    )

    z_profile, r_profile = profile(
        D,
        straight_height,
        bottom_type,
        top_type,
        n_points=1000,
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

    return float(volume)


# =========================================================
# LIQUID HEIGHT
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

    total_volume = (
        calculate_total_volume(
            D=D,
            straight_height=straight_height,
            bottom_type=bottom_type,
            top_type=top_type,
        )
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

        calculated_volume = (
            volume_at_height(
                mid,
                D,
                straight_height,
                bottom_type,
                top_type,
            )
        )

        if calculated_volume < working_volume:
            low = mid
        else:
            high = mid

    return (
        (low + high) / 2.0,
        total_volume
    )
