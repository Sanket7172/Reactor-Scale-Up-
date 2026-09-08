"""
Reactor scale-up calculations.
"""


import math


def scale_rpm(
    reference,
    target,
    basis,
):
    """
    Calculate starting-point target RPM.
    """

    Nr = float(
        reference.get("rpm", 0.0)
    )

    Dr = max(
        float(
            reference.get(
                "impeller_diameter_m",
                0.001,
            )
        ),
        1e-9,
    )

    Dt = max(
        float(
            target.get(
                "impeller_diameter_m",
                0.001,
            )
        ),
        1e-9,
    )

    Vr = max(
        float(
            reference.get(
                "volume_m3",
                0.001,
            )
        ),
        1e-9,
    )

    Vt = max(
        float(
            target.get(
                "volume_m3",
                0.001,
            )
        ),
        1e-9,
    )

    if basis == "Constant Tip Speed":

        return Nr * Dr / Dt

    if basis == "Constant RPM":

        return Nr

    if basis == "Constant Froude":

        return Nr * math.sqrt(
            Dr / Dt
        )

    if basis == "Constant Reynolds":

        return Nr * (
            Dr / Dt
        ) ** 2

    if basis == "Constant P/V":

        return Nr * (
            (
                (Dr**5 / Vr)
                /
                (Dt**5 / Vt)
            )
            ** (1.0 / 3.0)
        )

    if basis == "Constant Q/V":

        return Nr * (
            (
                (Dr**3 / Vr)
                /
                (Dt**3 / Vt)
            )
        )

    return Nr
