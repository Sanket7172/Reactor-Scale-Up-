import math


def _positive(value, name):

    value = float(value)

    if value <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return value


def calculate_scaleup(
    reference_volume,
    target_volume,
    basis,
    reference_diameter=None,
    reference_rpm=None,
    reference_power_per_volume=None,
    reference_tip_speed=None,
):

    V1 = _positive(
        reference_volume,
        "Reference volume",
    )

    V2 = _positive(
        target_volume,
        "Target volume",
    )

    scale_ratio = (
        V2 / V1
    )

    geometric_ratio = (
        scale_ratio ** (
            1.0 / 3.0
        )
    )

    D1 = (
        float(reference_diameter)
        if reference_diameter
        else None
    )

    rpm1 = (
        float(reference_rpm)
        if reference_rpm
        else None
    )

    pv1 = (
        float(reference_power_per_volume)
        if reference_power_per_volume
        else None
    )

    tip1 = (
        float(reference_tip_speed)
        if reference_tip_speed
        else None
    )

    D2 = None
    rpm2 = None
    pv2 = None
    tip2 = None
    power2 = None

    if D1 is not None:
        D2 = D1 * geometric_ratio

    if basis == "Constant Tip Speed":

        if rpm1 is not None and D1:

            rpm2 = (
                rpm1
                * D1
                / D2
            )

        if tip1 is not None:
            tip2 = tip1

        if pv1 is not None:

            pv2 = (
                pv1
                * (
                    rpm2 / rpm1
                )**3
                * (
                    D2 / D1
                )**5
                / scale_ratio
            ) if rpm1 and D1 else None

    elif basis == "Constant P/V":

        if pv1 is not None:

            pv2 = pv1

        if rpm1 is not None and D1:

            # P/V ∝ N³D⁵/V
            rpm2 = (
                rpm1
                * (
                    scale_ratio
                    / geometric_ratio**5
                ) ** (
                    1.0 / 3.0
                )
            )

        if rpm2 is not None and D2:

            tip2 = (
                math.pi
                * D2
                * rpm2
                / 60.0
            )

    elif basis == "Constant RPM":

        if rpm1 is not None:
            rpm2 = rpm1

        if rpm2 is not None and D2:

            tip2 = (
                math.pi
                * D2
                * rpm2
                / 60.0
            )

    else:

        raise ValueError(
            f"Unsupported scale-up basis: {basis}"
        )

    if (
        pv2 is not None
        and V2 > 0
    ):

        power2 = (
            pv2
            * V2
        )

    return {
        "reference_volume_m3": V1,
        "target_volume_m3": V2,
        "volume_scale_ratio": scale_ratio,
        "linear_scale_ratio": geometric_ratio,
        "basis": basis,
        "reference_diameter_m": D1,
        "target_diameter_m": D2,
        "reference_rpm": rpm1,
        "target_rpm": rpm2,
        "reference_power_per_volume_kw_m3": pv1,
        "target_power_per_volume_kw_m3": pv2,
        "reference_tip_speed_m_s": tip1,
        "target_tip_speed_m_s": tip2,
        "estimated_target_power_kw": power2,
    }
