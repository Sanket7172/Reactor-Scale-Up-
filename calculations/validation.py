def _check(
    name,
    value,
    minimum=None,
    maximum=None,
):

    if value is None:

        return {
            "Check": name,
            "Result": "REVIEW",
            "Value": "N/A",
            "Comment": "No value available.",
        }

    if minimum is not None and value < minimum:

        return {
            "Check": name,
            "Result": "REVIEW",
            "Value": value,
            "Comment": f"Below preliminary minimum of {minimum}.",
        }

    if maximum is not None and value > maximum:

        return {
            "Check": name,
            "Result": "REVIEW",
            "Value": value,
            "Comment": f"Above preliminary maximum of {maximum}.",
        }

    return {
        "Check": name,
        "Result": "PASS",
        "Value": value,
        "Comment": "Within preliminary screening range.",
    }


def validate_reactor(result):

    if not isinstance(result, dict):

        raise ValueError(
            "Validation requires a result dictionary."
        )

    checks = []

    D_T = result.get(
        "D_T"
    )

    H_T = result.get(
        "H_T"
    )

    rpm = result.get(
        "rpm"
    )

    power = result.get(
        "power_kw"
    )

    Re = result.get(
        "reynolds_number"
    )

    volume = result.get(
        "volume_m3"
    )

    vessel_volume = result.get(
        "vessel_volume_m3"
    )

    checks.append(
        _check(
            "Impeller D/T",
            D_T,
            0.25,
            0.70,
        )
    )

    checks.append(
        _check(
            "Liquid H/T",
            H_T,
            0.2,
            5.0,
        )
    )

    checks.append(
        _check(
            "Agitator RPM",
            rpm,
            0.1,
        )
    )

    checks.append(
        _check(
            "Power",
            power,
            0.0,
        )
    )

    checks.append(
        _check(
            "Reynolds Number",
            Re,
            0.0,
        )
    )

    if (
        volume is not None
        and vessel_volume is not None
        and vessel_volume > 0
    ):

        fill_fraction = (
            volume
            / vessel_volume
        )

        checks.append(
            _check(
                "Vessel Fill Fraction",
                fill_fraction,
                0.0,
                0.90,
            )
        )

    return checks
