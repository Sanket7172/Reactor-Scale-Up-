"""
Reactor geometry calculations.

Geometry is intended for preliminary engineering screening.
Actual pressure-vessel geometry must be confirmed against
fabrication drawings and applicable vessel codes.
"""

import math


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


def head_depth(D, head_type):
    D = max(float(D), 0.0)

    if head_type not in REACTOR_HEADS:
        return 0.0

    return D * REACTOR_HEADS[head_type]["depth_ratio"]


def cylindrical_volume(D, H):
    D = max(float(D), 0.0)
    H = max(float(H), 0.0)

    return math.pi * D**2 / 4.0 * H


def head_volume(D, head_type):
    D = max(float(D), 0.0)
    R = D / 2.0
    h = head_depth(D, head_type)

    if h <= 0:
        return 0.0

    if head_type == "Hemispherical":
        return 2.0 * math.pi * R**3 / 3.0

    if head_type == "Conical":
        return math.pi * R**2 * h / 3.0

    # Approximation for preliminary screening of ellipsoidal /
    # torispherical heads.
    return math.pi * h * (3.0 * R**2 + h**2) / 6.0


def calculate_total_volume(
    D,
    straight_height,
    bottom_type,
    top_type,
):
    return (
        cylindrical_volume(D, straight_height)
        + head_volume(D, bottom_type)
        + head_volume(D, top_type)
    )


def calculate_cylindrical_fill_volume(D, liquid_height):
    return cylindrical_volume(D, liquid_height)


def liquid_height_from_volume(
    working_volume,
    D,
    straight_height,
    bottom_type,
    top_type,
):
    """
    Preliminary liquid-height estimate.

    The vessel is treated as:
        bottom head + cylindrical straight side + top head.

    For liquid levels below the top head, the top head is excluded.
    """

    V = max(float(working_volume), 0.0)
    D = max(float(D), 1e-9)
    H = max(float(straight_height), 0.0)

    bottom_V = head_volume(D, bottom_type)
    top_h = head_depth(D, top_type)

    total_V = calculate_total_volume(
        D,
        H,
        bottom_type,
        top_type,
    )

    if V <= 0:
        return 0.0

    if V >= total_V:
        return H + top_h

    # Bottom head + cylindrical section.
    if V <= bottom_V:
        # Simple equivalent-height approximation inside bottom head.
        h_bottom = head_depth(D, bottom_type)

        if h_bottom <= 0:
            return 0.0

        return h_bottom * V / bottom_V

    V_remaining = V - bottom_V

    cyl_area = math.pi * D**2 / 4.0

    cyl_height = V_remaining / cyl_area

    if cyl_height <= H:
        return cyl_height

    # Remaining volume in top head.
    remaining_top = V_remaining - cyl_area * H

    if top_h <= 0:
        return H

    top_fraction = min(
        max(remaining_top / max(head_volume(D, top_type), 1e-12), 0.0),
        1.0,
    )

    return H + top_fraction * top_h


def calculate_fill_percent(working_volume, total_volume):
    if total_volume <= 0:
        return 0.0

    return 100.0 * working_volume / total_volume
