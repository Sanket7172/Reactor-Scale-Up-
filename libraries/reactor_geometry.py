import math
import numpy as np


# =========================================================
# REACTOR HEAD LIBRARY
# =========================================================

REACTOR_HEADS = {

    "Flat Bottom": {
        "type": "flat",
        "depth_ratio": 0.0,
        "description": "Flat reactor bottom",
    },

    "2:1 Ellipsoidal": {
        "type": "ellipsoidal",
        "depth_ratio": 0.25,
        "description": "2:1 ellipsoidal head",
    },

    "10% Torispherical": {
        "type": "torispherical",
        "depth_ratio": 0.10,
        "description": "10% torispherical head",
    },

    "6% Torispherical": {
        "type": "torispherical",
        "depth_ratio": 0.06,
        "description": "6% torispherical head",
    },

    "Hemispherical": {
        "type": "hemispherical",
        "depth_ratio": 0.50,
        "description": "Hemispherical head",
    },

    "Conical": {
        "type": "conical",
        "depth_ratio": 0.25,
        "description": "Conical bottom/top",
    },
}


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================
# Your older app.py uses HEADS.
# Keeping this alias prevents:
#
# ImportError: cannot import name 'HEADS'
#
# =========================================================

HEADS = REACTOR_HEADS


# =========================================================
# HEAD DEPTH
# =========================================================

def head_depth(D, head_type):
    """
    Calculate approximate head depth.

    Parameters
    ----------
    D : float
        Reactor inside diameter [m]

    head_type : str
        Reactor head type

    Returns
    -------
    float
        Head depth [m]
    """

    if D <= 0:
        return 0.0

    if head_type not in REACTOR_HEADS:
        raise ValueError(
            f"Unknown reactor head type: {head_type}"
        )

    ratio = REACTOR_HEADS[head_type]["depth_ratio"]

    return D * ratio


# =========================================================
# CYLINDRICAL VOLUME
# =========================================================

def cylindrical_volume(
    D,
    straight_height
):
    """
    Calculate cylindrical section volume.

    D                  -> m
    straight_height    -> m

    Returns volume in m3.
    """

    if D <= 0 or straight_height <= 0:
        return 0.0

    return (
        math.pi *
        D ** 2 /
        4.0 *
        straight_height
    )


# =========================================================
# APPROXIMATE HEAD VOLUME
# =========================================================

def head_volume(
    D,
    head_type
):
    """
    Approximate reactor head volume.

    This is a simplified engineering visualization
    model and should not be used as a final vessel
    fabrication volume calculation.
    """

    depth = head_depth(
        D,
        head_type
    )

    area = (
        math.pi *
        D ** 2 /
        4.0
    )

    return area * depth


# =========================================================
# TOTAL REACTOR VOLUME
# =========================================================

def calculate_total_volume(
    D,
    straight_height,
    bottom_type,
    top_type
):
    """
    Calculate approximate total reactor volume.

    Parameters
    ----------
    D : float
        Reactor inside diameter [m]

    straight_height : float
        Straight shell height [m]

    bottom_type : str
        Bottom head type

    top_type : str
        Top head type

    Returns
    -------
    float
        Approximate total volume [m3]
    """

    if D <= 0:
        raise ValueError(
            "Reactor diameter must be greater than zero."
        )

    if straight_height <= 0:
        raise ValueError(
            "Straight height must be greater than zero."
        )

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
# VOLUME AT A GIVEN LIQUID HEIGHT
# =========================================================

def volume_at_height(
    height,
    D,
    straight_height,
    bottom_type,
    top_type
):
    """
    Calculate approximate liquid volume at a
    specified liquid height.

    All dimensions are in meters.
    """

    bottom_depth = head_depth(
        D,
        bottom_type
    )

    top_depth = head_depth(
        D,
        top_type
    )

    cylinder_area = (
        math.pi *
        D ** 2 /
        4.0
    )

    total_height = (
        bottom_depth +
        straight_height +
        top_depth
    )

    # Limit height to vessel boundaries
    height = max(
        0.0,
        min(
            height,
            total_height
        )
    )

    # -----------------------------------------------------
    # BOTTOM HEAD
    # -----------------------------------------------------

    if height <= bottom_depth:

        if bottom_depth <= 0:
            return 0.0

        fraction = (
            height /
            bottom_depth
        )

        return (
            cylinder_area *
            bottom_depth *
            fraction ** 2
        )

    # -----------------------------------------------------
    # CYLINDRICAL SECTION
    # -----------------------------------------------------

    cylinder_start = bottom_depth

    cylinder_end = (
        bottom_depth +
        straight_height
    )

    if height <= cylinder_end:

        cylinder_height = (
            height -
            cylinder_start
        )

        return (
            head_volume(
                D,
                bottom_type
            )
            +
            cylinder_area *
            cylinder_height
        )

    # -----------------------------------------------------
    # TOP HEAD
    # -----------------------------------------------------

    liquid_in_top = (
        height -
        cylinder_end
    )

    if top_depth > 0:

        top_fraction = (
            liquid_in_top /
            top_depth
        )

    else:

        top_fraction = 1.0

    top_fraction = max(
        0.0,
        min(
            top_fraction,
            1.0
        )
    )

    top_total_volume = head_volume(
        D,
        top_type
    )

    # Approximate spherical-cap type filling
    top_volume = (
        top_total_volume *
        (
            2.0 *
            top_fraction -
            top_fraction ** 2
        )
    )

    return (
        head_volume(
            D,
            bottom_type
        )
        +
        cylindrical_volume(
            D,
            straight_height
        )
        +
        top_volume
    )


# =========================================================
# LIQUID HEIGHT FROM WORKING VOLUME
# =========================================================

def liquid_height_from_volume(
    working_volume,
    D,
    straight_height,
    bottom_type,
    top_type
):
    """
    Calculate liquid height corresponding to
    the specified working volume.

    Returns
    -------
    liquid_height_m
    total_vessel_volume_m3
    """

    total_volume = calculate_total_volume(
        D,
        straight_height,
        bottom_type,
        top_type
    )

    # -----------------------------------------------------
    # ZERO / NEGATIVE VOLUME
    # -----------------------------------------------------

    if working_volume <= 0:

        return (
            0.0,
            total_volume
        )

    # -----------------------------------------------------
    # WORKING VOLUME >= TOTAL VOLUME
    # -----------------------------------------------------

    if working_volume >= total_volume:

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

        return (
            total_height,
            total_volume
        )

    # -----------------------------------------------------
    # BINARY SEARCH
    # -----------------------------------------------------

    low = 0.0

    high = (
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

    for _ in range(80):

        mid = (
            low +
            high
        ) / 2.0

        calculated_volume = volume_at_height(
            mid,
            D,
            straight_height,
            bottom_type,
            top_type
        )

        if calculated_volume < working_volume:

            low = mid

        else:

            high = mid

    liquid_height = (
        low +
        high
    ) / 2.0

    return (
        liquid_height,
        total_volume
    )


# =========================================================
# REACTOR PROFILE FOR 3D VISUALIZATION
# =========================================================

def profile(
    D,
    straight_height,
    bottom_type,
    top_type,
    points=160
):
    """
    Generate a simplified reactor radial profile.

    Returns
    -------
    z : numpy array
        Vertical coordinates [m]

    r : numpy array
        Radius coordinates [m]

    Used by reactor_3d.py.
    """

    if D <= 0:
        raise ValueError(
            "Reactor diameter must be greater than zero."
        )

    if straight_height <= 0:
        raise ValueError(
            "Straight height must be greater than zero."
        )

    bottom_depth = head_depth(
        D,
        bottom_type
    )

    top_depth = head_depth(
        D,
        top_type
    )

    radius = D / 2.0

    # -----------------------------------------------------
    # BOTTOM HEAD
    # -----------------------------------------------------

    if bottom_depth > 0:

        z_bottom = np.linspace(
            0.0,
            bottom_depth,
            max(
                10,
                points // 4
            )
        )

        fraction = (
            z_bottom /
            bottom_depth
        )

        r_bottom = (
            radius *
            np.sqrt(
                fraction
            )
        )

    else:

        z_bottom = np.array([
            0.0
        ])

        r_bottom = np.array([
            radius
        ])

    # -----------------------------------------------------
    # CYLINDRICAL SHELL
    # -----------------------------------------------------

    z_cylinder = np.linspace(
        bottom_depth,
        bottom_depth +
        straight_height,
        max(
            20,
            points // 2
        )
    )

    r_cylinder = np.full_like(
        z_cylinder,
        radius
    )

    # -----------------------------------------------------
    # TOP HEAD
    # -----------------------------------------------------

    if top_depth > 0:

        z_top = np.linspace(
            bottom_depth +
            straight_height,

            bottom_depth +
            straight_height +
            top_depth,

            max(
                10,
                points // 4
            )
        )

        fraction = (
            z_top -
            (
                bottom_depth +
                straight_height
            )
        ) / top_depth

        r_top = (
            radius *
            np.sqrt(
                np.maximum(
                    0.0,
                    1.0 -
                    fraction
                )
            )
        )

    else:

        z_top = np.array([
            bottom_depth +
            straight_height
        ])

        r_top = np.array([
            radius
        ])

    # -----------------------------------------------------
    # COMBINE PROFILE
    # -----------------------------------------------------

    z = np.concatenate([
        z_bottom,
        z_cylinder[1:],
        z_top[1:]
    ])

    r = np.concatenate([
        r_bottom,
        r_cylinder[1:],
        r_top[1:]
    ])

    return z, r


# =========================================================
# RADIUS AT A GIVEN HEIGHT
# =========================================================

def radius_at_height(
    z,
    D,
    straight_height,
    bottom_type,
    top_type
):
    """
    Return reactor radius at a specified vertical
    coordinate.

    Used by reactor_3d.py.
    """

    bottom_depth = head_depth(
        D,
        bottom_type
    )

    top_depth = head_depth(
        D,
        top_type
    )

    radius = D / 2.0

    total_height = (
        bottom_depth +
        straight_height +
        top_depth
    )

    # Keep z within reactor limits
    z = max(
        0.0,
        min(
            z,
            total_height
        )
    )

    # -----------------------------------------------------
    # BOTTOM HEAD
    # -----------------------------------------------------

    if z <= bottom_depth:

        if bottom_depth <= 0:
            return radius

        fraction = (
            z /
            bottom_depth
        )

        return (
            radius *
            math.sqrt(
                max(
                    0.0,
                    fraction
                )
            )
        )

    # -----------------------------------------------------
    # CYLINDRICAL SECTION
    # -----------------------------------------------------

    cylinder_end = (
        bottom_depth +
        straight_height
    )

    if z <= cylinder_end:

        return radius

    # -----------------------------------------------------
    # TOP HEAD
    # -----------------------------------------------------

    if top_depth <= 0:

        return radius

    fraction = (
        z -
        cylinder_end
    ) / top_depth

    return (
        radius *
        math.sqrt(
            max(
                0.0,
                1.0 -
                fraction
            )
        )
    )
