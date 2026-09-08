"""
Reactor geometry calculations.

The geometry is represented using:
- cylindrical straight side
- simplified engineering head-depth ratios

This is intended for preliminary engineering screening.
"""

import math


HEAD_DEPTH_RATIO = {
    "Flat Bottom": 0.0,
    "2:1 Ellipsoidal": 0.25,
    "10% Torispherical": 0.10,
    "6% Torispherical": 0.06,
    "Hemispherical": 0.50,
    "Conical": 0.25,
}


def _cylinder_volume(diameter, height):
    radius = diameter / 2.0
    return math.pi * radius**2 * max(height, 0.0)


def _head_volume(diameter, head_type):
    """
    Approximate head volume using equivalent depth.

    For preliminary scale-up screening only.
    """

    ratio = HEAD_DEPTH_RATIO.get(head_type, 0.0)

    depth = diameter * ratio

    if depth <= 0:
        return 0.0

    # Approximate head as a spherical-cap-like volume.
    radius = diameter / 2.0

    if head_type == "Hemispherical":
        return (
            2.0
            / 3.0
            * math.pi
            * radius**3
        )

    # Engineering approximation.
    return (
        math.pi
        * radius**2
        * depth
        * 0.65
    )


def calculate_total_volume(
    D,
    straight_height,
    bottom_type,
    top_type,
):
    D = float(D)
    straight_height = float(straight_height)

    cylindrical = _cylinder_volume(
        D,
        straight_height,
    )

    bottom = _head_volume(
        D,
        bottom_type,
    )

    top = _head_volume(
        D,
        top_type,
    )

    return max(
        cylindrical + bottom + top,
        0.0,
    )


def liquid_height_from_volume(
    working_volume,
    D,
    straight_height,
    bottom_type,
    top_type,
):
    """
    Determine approximate liquid height.

    The returned value is limited to the straight-side
    liquid region for stable visualization.
    """

    working_volume = max(
        float(working_volume),
        0.0,
    )

    D = float(D)
    straight_height = float(straight_height)

    total_volume = calculate_total_volume(
        D,
        straight_height,
        bottom_type,
        top_type,
    )

    if total_volume <= 0:
        return 0.0

    # If volume is above vessel capacity,
    # return full straight-side height.
    if working_volume >= total_volume:
        return straight_height

    bottom_head = _head_volume(
        D,
        bottom_type,
    )

    # Simplified treatment:
    # bottom head fills first, then cylindrical section.
    if working_volume <= bottom_head and bottom_head > 0:

        ratio = working_volume / bottom_head

        return straight_height * 0.10 * ratio

    cylindrical_volume = max(
        working_volume - bottom_head,
        0.0,
    )

    area = math.pi * (D / 2.0) ** 2

    cylindrical_height = (
        cylindrical_volume / area
        if area > 0
        else 0.0
    )

    return min(
        max(cylindrical_height, 0.0),
        straight_height,
    )
