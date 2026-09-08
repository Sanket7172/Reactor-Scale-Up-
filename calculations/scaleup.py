"""
Scale-up calculations.

RPM is derived from the selected scale-up criterion.
This module intentionally separates calculation from
engineering judgement.
"""

import math


def _positive(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def scale_rpm(reference, target, basis):
    """
    Calculate target RPM from reference conditions.

    Supported:
        Constant Tip Speed
        Constant RPM
        Constant Froude Number
        Constant Reynolds Number
        Constant P/V
        Constant Q/V
    """

    Nr = float(reference["rpm"])
    Dr = float(reference["impeller_diameter_m"])
    Vr = float(reference["volume_m3"])

    Dt = float(target["impeller_diameter_m"])
    Vt = float(target["volume_m3"])

    if not all(
        _positive(x)
        for x in [Nr, Dr, Vr, Dt, Vt]
    ):
        raise ValueError(
            "Reference/target RPM, impeller diameter "
            "and volume must be greater than zero."
        )

    b = str(basis).lower()

    if "tip" in b:
        return Nr * Dr / Dt

    if "rpm" in b:
        return Nr

    if "froude" in b:
        return Nr * math.sqrt(Dr / Dt)

    if "reynolds" in b:
        return Nr * (Dr / Dt) ** 2

    if "p/v" in b or "p v" in b:
        return Nr * (
            (
                (Dr**5 / Vr)
                /
                (Dt**5 / Vt)
            ) ** (1.0 / 3.0)
        )

    if (
        "pumping" in b
        or "q/v" in b
        or "q v" in b
    ):
        return Nr * (
            (Dr**3 / Vr)
            /
            (Dt**3 / Vt)
        )

    raise ValueError(
        f"Unsupported scale-up basis: {basis}"
    )


def calculate_scaleup(
    reference,
    target,
    basis,
):
    target_rpm = scale_rpm(
        reference,
        target,
        basis,
    )

    Dt = float(
        target["impeller_diameter_m"]
    )

    Vt = float(
        target["volume_m3"]
    )

    target_tip_speed = (
        math.pi
        * Dt
        * target_rpm
        / 60.0
    )

    # P/V for geometric similarity.
    # This is useful for comparison even when the
    # selected criterion is something else.
    target_pv_relative = (
        target_rpm**3
        * Dt**5
        / Vt
    )

    target_qv_relative = (
        target_rpm
        * Dt**3
        / Vt
    )

    return {
        "basis": basis,
        "target_rpm": target_rpm,
        "target_tip_speed": target_tip_speed,
        "target_power_volume_relative": (
            target_pv_relative
        ),
        "target_qv_relative": (
            target_qv_relative
        ),
    }


def compare_metric(
    reference_value,
    target_value,
):
    if (
        reference_value is None
        or target_value is None
        or reference_value == 0
    ):
        return None

    return target_value / reference_value
