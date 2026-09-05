# libraries/reactor_geometry.py

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


# =========================================================
# COMPATIBILITY ALIAS
# =========================================================
# app.py expects HEADS

HEADS = REACTOR_HEADS


# =========================================================
# HEAD DEPTH
# =========================================================

def head_depth(
    diameter_m,
    head_type
):
    """
    Calculate reactor head depth.

    Parameters
    ----------
    diameter_m : float
        Reactor diameter in metres.

    head_type : str
        Reactor head type.

    Returns
    -------
    float
        Head depth in metres.
    """

    if head_type not in REACTOR_HEADS:
        raise ValueError(
            f"Unknown reactor head type: {head_type}"
        )

    ratio = REACTOR_HEADS[
        head_type
    ]["depth_ratio"]

    return diameter_m * ratio


# =========================================================
# CYLINDRICAL VOLUME
# =========================================================

def cylindrical_volume(
    diameter_m,
    straight_height_m
):
    """
    Calculate cylindrical vessel volume.

    Inputs are in metres.
    Output is m3.
    """

    radius = diameter_m / 2.0

    return (
        math.pi *
        radius**2 *
        straight_height_m
    )


# =========================================================
# HEAD VOLUME
# =========================================================

def head_volume(
    diameter_m,
    head_type
):
    """
    Approximate reactor-head volume.

    This is a conceptual engineering approximation
    intended for the dashboard geometry model.
    """

    radius = diameter_m / 2.0

    depth = head_depth(
        diameter_m,
        head_type
    )

    head_info = REACTOR_HEADS[
        head_type
    ]

    head_kind = head_info["type"]

    # -----------------------------------------------------
    # Flat
    # -----------------------------------------------------

    if head_kind == "flat":

        return 0.0

    # -----------------------------------------------------
    # Hemispherical
    # -----------------------------------------------------

    elif head_kind == "hemispherical":

        return (
            (2.0 / 3.0)
            *
            math.pi
            *
            radius**2
            *
            depth
        )

    # -----------------------------------------------------
    # 2:1 Ellipsoidal
    # -----------------------------------------------------

    elif head_kind == "ellipsoidal":

        return (
            (2.0 / 3.0)
            *
            math.pi
            *
            radius**2
            *
            depth
        )

    # -----------------------------------------------------
    # Torispherical
    # -----------------------------------------------------

    elif head_kind == "torispherical":

        return (
            0.65
            *
            math.pi
            *
            radius**2
            *
            depth
        )

    # -----------------------------------------------------
    # Conical
    # -----------------------------------------------------

    elif head_kind == "conical":

        return (
            (1.0 / 3.0)
            *
            math.pi
            *
            radius**2
            *
            depth
        )

    return 0.0


# =========================================================
# TOTAL VESSEL VOLUME
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
        Reactor diameter in metres.

    straight_height : float
        Straight-side height in metres.

    bottom_type : str
        Bottom head type.

    top_type : str
        Top head type.

    Returns
    -------
    float
        Approximate vessel volume in m3.
    """

    cylinder = cylindrical_volume(
        D,
        straight_height
    )

    bottom_volume = head_volume(
        D,
        bottom_type
    )

    top_volume = head_volume(
        D,
        top_type
    )

    return (
        cylinder
        +
        bottom_volume
        +
        top_volume
    )


# =========================================================
# ORIGINAL FUNCTION - BACKWARD COMPATIBILITY
# =========================================================

def approximate_total_volume(
    diameter_mm,
    straight_height_mm,
    bottom_type,
    top_type
):
    """
    Backward-compatible version of the original function.

    Inputs:
        diameter_mm
        straight_height_mm

    Output:
        volume in m3
    """

    D = diameter_mm / 1000.0

    H = straight_height_mm / 1000.0

    return calculate_total_volume(
        D,
        H,
        bottom_type,
        top_type
    )


# =========================================================
# RADIUS AT HEIGHT
# =========================================================

def radius_at_height(
    D,
    z,
    head_depth_m,
    head_type,
    bottom=True
):
    """
    Estimate vessel radius at a particular position
    inside a reactor head.

    Used by the 3D visualization.

    Parameters
    ----------
    D : float
        Reactor diameter in metres.

    z : float
        Local height within the head in metres.

    head_depth_m : float
        Head depth in metres.

    head_type : str
        Reactor head type.

    bottom : bool
        True for bottom head.
        False for top head.
    """

    R = D / 2.0

    # Flat head
    if head_depth_m <= 0:

        return R

    # Normalized position
    t = np.clip(
        z / head_depth_m,
        0.0,
        1.0
    )

    head_kind = REACTOR_HEADS[
        head_type
    ]["type"]

    # -----------------------------------------------------
    # Flat
    # -----------------------------------------------------

    if head_kind == "flat":

        return R

    # -----------------------------------------------------
    # Hemispherical
    # -----------------------------------------------------

    elif head_kind == "hemispherical":

        if bottom:

            return (
                R *
                np.sqrt(
                    max(
                        0.0,
                        1.0 -
                        (1.0 - t)**2
                    )
                )
            )

        else:

            return (
                R *
                np.sqrt(
                    max(
                        0.0,
                        1.0 -
                        t**2
                    )
                )
            )

    # -----------------------------------------------------
    # 2:1 Ellipsoidal
    # -----------------------------------------------------

    elif head_kind == "ellipsoidal":

        if bottom:

            return (
                R *
                np.sqrt(
                    max(
                        0.0,
                        1.0 -
                        (1.0 - t)**2
                    )
                )
            )

        else:

            return (
                R *
                np.sqrt(
                    max(
                        0.0,
                        1.0 -
                        t**2
                    )
                )
            )

    # -----------------------------------------------------
    # Torispherical
    # -----------------------------------------------------

    elif head_kind == "torispherical":

        if bottom:

            return (
                R *
                (
                    0.5 -
                    0.5 *
                    np.cos(
                        np.pi * t
                    )
                )
            )

        else:

            return (
                R *
                (
                    0.5 +
                    0.5 *
                    np.cos(
                        np.pi * t
                    )
                )
            )

    # -----------------------------------------------------
    # Conical
    # -----------------------------------------------------

    elif head_kind == "conical":

        if bottom:

            return R * t

        else:

            return R * (1.0 - t)

    # -----------------------------------------------------
    # Default
    # -----------------------------------------------------

    return R


# =========================================================
# REACTOR PROFILE
# =========================================================

def profile(
    D,
    straight_height,
    bottom_type,
    top_type,
    points=160
):
    """
    Generate reactor radial profile for 3D visualization.

    Returns
    -------
    z : numpy.ndarray
        Vertical coordinates in metres.

    r : numpy.ndarray
        Radius coordinates in metres.
    """

    R = D / 2.0

    bottom_depth = head_depth(
        D,
        bottom_type
    )

    top_depth = head_depth(
        D,
        top_type
    )

    # =====================================================
    # NUMBER OF POINTS
    # =====================================================

    bottom_points = max(
        10,
        int(points * 0.20)
    )

    cylinder_points = max(
        20,
        int(points * 0.55)
    )

    top_points = max(
        10,
        int(points * 0.25)
    )

    # =====================================================
    # BOTTOM HEAD
    # =====================================================

    if bottom_depth > 0:

        z_bottom = np.linspace(
            0.0,
            bottom_depth,
            bottom_points
        )

        r_bottom = np.array([

            radius_at_height(
                D,
                z,
                bottom_depth,
                bottom_type,
                bottom=True
            )

            for z in z_bottom

        ])

    else:

        z_bottom = np.array([
            0.0
        ])

        r_bottom = np.array([
            R
        ])

    # =====================================================
    # STRAIGHT SIDE
    # =====================================================

    z_cylinder = np.linspace(

        bottom_depth,

        bottom_depth +
        straight_height,

        cylinder_points
    )

    r_cylinder = np.full_like(
        z_cylinder,
        R
    )

    # =====================================================
    # TOP HEAD
    # =====================================================

    if top_depth > 0:

        z_top = np.linspace(

            bottom_depth +
            straight_height,

            bottom_depth +
            straight_height +
            top_depth,

            top_points
        )

        local_z = (
            z_top
            -
            bottom_depth
            -
            straight_height
        )

        r_top = np.array([

            radius_at_height(
                D,
                z,
                top_depth,
                top_type,
                bottom=False
            )

            for z in local_z

        ])

    else:

        z_top = np.array([

            bottom_depth +
            straight_height

        ])

        r_top = np.array([
            R
        ])

    # =====================================================
    # COMBINE PROFILE
    # =====================================================

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
# VOLUME UP TO LIQUID HEIGHT
# =========================================================

def volume_up_to_height(
    liquid_height,
    D,
    straight_height,
    bottom_type,
    top_type
):
    """
    Estimate liquid volume corresponding to
    a particular liquid height.

    Inputs are in metres.
    """

    if liquid_height <= 0:

        return 0.0

    bottom_depth = head_depth(
        D,
        bottom_type
    )

    top_depth = head_depth(
        D,
        top_type
    )

    radius = D / 2.0

    cross_section = (
        math.pi *
        radius**2
    )

    total_height = (
        bottom_depth
        +
        straight_height
        +
        top_depth
    )

    # Prevent exceeding vessel
    liquid_height = min(
        liquid_height,
        total_height
    )

    # =====================================================
    # BOTTOM HEAD
    # =====================================================

    if (
        bottom_depth > 0
        and liquid_height < bottom_depth
    ):

        fraction = (
            liquid_height /
            bottom_depth
        )

        fraction = min(
            max(
                fraction,
                0.0
            ),
            1.0
        )

        return (
            head_volume(
                D,
                bottom_type
            )
            *
            fraction**1.5
        )

    # =====================================================
    # FULL BOTTOM HEAD
    # =====================================================

    volume = head_volume(
        D,
        bottom_type
    )

    remaining_height = (
        liquid_height -
        bottom_depth
    )

    # =====================================================
    # CYLINDRICAL SECTION
    # =====================================================

    cylinder_height = min(
        max(
            remaining_height,
            0.0
        ),
        straight_height
    )

    volume += (
        cross_section *
        cylinder_height
    )

    # =====================================================
    # TOP HEAD
    # =====================================================

    if (
        remaining_height >
        straight_height
        and
        top_depth > 0
    ):

        top_height = (
            remaining_height -
            straight_height
        )

        fraction = (
            top_height /
            top_depth
        )

        fraction = min(
            max(
                fraction,
                0.0
            ),
            1.0
        )

        volume += (
            head_volume(
                D,
                top_type
            )
            *
            fraction
        )

    return volume


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
    Calculate liquid height from operating volume.

    Returns:

        liquid_height_m,
        total_vessel_volume_m3
    """

    total_volume = calculate_total_volume(

        D=D,

        straight_height=straight_height,

        bottom_type=bottom_type,

        top_type=top_type
    )

    # =====================================================
    # ZERO / NEGATIVE VOLUME
    # =====================================================

    if working_volume <= 0:

        return (
            0.0,
            total_volume
        )

    # =====================================================
    # FULL VESSEL
    # =====================================================

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

    # =====================================================
    # TOTAL VESSEL HEIGHT
    # =====================================================

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

    # =====================================================
    # BINARY SEARCH
    # =====================================================

    low = 0.0

    high = total_height

    for _ in range(80):

        mid = (
            low +
            high
        ) / 2.0

        calculated_volume = (
            volume_up_to_height(

                liquid_height=mid,

                D=D,

                straight_height=
                    straight_height,

                bottom_type=
                    bottom_type,

                top_type=
                    top_type
            )
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
