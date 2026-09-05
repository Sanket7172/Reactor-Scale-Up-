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


def head_depth(diameter_mm, head_type):

    ratio = REACTOR_HEADS[head_type]["depth_ratio"]

    return diameter_mm * ratio


def cylindrical_volume(
    diameter_mm,
    straight_height_mm
):

    D = diameter_mm / 1000.0
    H = straight_height_mm / 1000.0

    return (
        3.14159265359 *
        D**2 /
        4 *
        H
    )


def approximate_total_volume(
    diameter_mm,
    straight_height_mm,
    bottom_type,
    top_type
):

    D = diameter_mm / 1000.0

    cylinder = cylindrical_volume(
        diameter_mm,
        straight_height_mm
    )

    bottom_depth = (
        head_depth(
            diameter_mm,
            bottom_type
        ) / 1000.0
    )

    top_depth = (
        head_depth(
            diameter_mm,
            top_type
        ) / 1000.0
    )

    # Approximate head volumes.
    bottom_volume = (
        3.14159265359 *
        D**2 /
        4 *
        bottom_depth
    )

    top_volume = (
        3.14159265359 *
        D**2 /
        4 *
        top_depth
    )

    return (
        cylinder +
        bottom_volume +
        top_volume
    )
