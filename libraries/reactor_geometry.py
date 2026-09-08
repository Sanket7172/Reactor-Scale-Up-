import math


REACTOR_HEADS = {
    "Flat": {
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
}


def _safe_float(value, default=0.0):

    try:
        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def _head_depth(
    diameter_m,
    head_type,
):

    D = _safe_float(
        diameter_m,
        0.0,
    )

    if D <= 0:
        return 0.0

    data = REACTOR_HEADS.get(
        head_type,
        {},
    )

    depth_ratio = _safe_float(
        data.get("depth_ratio"),
        0.0,
    )

    return depth_ratio * D


def _ellipsoidal_head_volume(
    diameter_m,
):

    D = _safe_float(
        diameter_m,
        0.0,
    )

    if D <= 0:
        return 0.0

    # Approximate 2:1 ellipsoidal head:
    # semi-major radius = D/2
    # semi-minor depth = D/4
    #
    # V = 2/3*pi*a*b*h for one half ellipsoid
    #
    # simplified engineering approximation

    return math.pi * D**3 / 24.0


def _torispherical_head_volume(
    diameter_m,
):

    D = _safe_float(
        diameter_m,
        0.0,
    )

    if D <= 0:
        return 0.0

    # Preliminary approximation only.
    return math.pi * D**3 / 40.0


def calculate_head_volume(
    diameter_m,
    head_type,
):

    name = str(
        head_type or ""
    ).lower()

    if "ellipsoidal" in name:
        return _ellipsoidal_head_volume(
            diameter_m
        )

    if "torispherical" in name:
        return _torispherical_head_volume(
            diameter_m
        )

    return 0.0


def calculate_total_volume(
    diameter_m,
    straight_height_m,
    bottom_type,
    top_type,
):

    D = _safe_float(
        diameter_m,
        0.0,
    )

    H = _safe_float(
        straight_height_m,
        0.0,
    )

    if D <= 0 or H <= 0:
        raise ValueError(
            "Diameter and straight height must be greater than zero."
        )

    cylindrical_volume = (
        math.pi
        * D**2
        * H
        / 4.0
    )

    bottom_volume = calculate_head_volume(
        D,
        bottom_type,
    )

    top_volume = calculate_head_volume(
        D,
        top_type,
    )

    return (
        cylindrical_volume
        + bottom_volume
        + top_volume
    )


def liquid_height_from_volume(
    volume_m3,
    diameter_m,
    straight_height_m,
    bottom_type,
    top_type,
):

    V = _safe_float(
        volume_m3,
        0.0,
    )

    D = _safe_float(
        diameter_m,
        0.0,
    )

    H = _safe_float(
        straight_height_m,
        0.0,
    )

    if V <= 0:
        return 0.0

    if D <= 0 or H <= 0:
        raise ValueError(
            "Invalid vessel geometry."
        )

    total_volume = calculate_total_volume(
        D,
        H,
        bottom_type,
        top_type,
    )

    if V > total_volume:
        raise ValueError(
            "Working volume exceeds estimated vessel volume."
        )

    cylindrical_area = (
        math.pi
        * D**2
        / 4.0
    )

    # Preliminary liquid-height calculation.
    # Head geometry is not fully resolved here.
    cylindrical_height = V / cylindrical_area

    return min(
        H,
        max(
            0.0,
            cylindrical_height,
        ),
    )


def calculate_geometry_summary(
    diameter_m,
    straight_height_m,
    working_volume_m3,
    bottom_type,
    top_type,
):

    total_volume = calculate_total_volume(
        diameter_m,
        straight_height_m,
        bottom_type,
        top_type,
    )

    liquid_height = liquid_height_from_volume(
        working_volume_m3,
        diameter_m,
        straight_height_m,
        bottom_type,
        top_type,
    )

    fill_fraction = (
        working_volume_m3 / total_volume
        if total_volume > 0
        else 0.0
    )

    return {
        "tank_diameter_m": diameter_m,
        "straight_height_m": straight_height_m,
        "bottom_type": bottom_type,
        "top_type": top_type,
        "vessel_volume_m3": total_volume,
        "working_volume_m3": working_volume_m3,
        "liquid_height_m": liquid_height,
        "fill_fraction": fill_fraction,
        "H_T": (
            liquid_height / diameter_m
            if diameter_m > 0
            else 0.0
        ),
    }
