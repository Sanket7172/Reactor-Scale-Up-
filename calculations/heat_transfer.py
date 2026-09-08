"""
Heat-transfer screening calculations.
"""

import math


def lmtd(delta_t1, delta_t2):
    dt1 = float(delta_t1)
    dt2 = float(delta_t2)

    if dt1 <= 0 or dt2 <= 0:
        return None

    if abs(dt1 - dt2) < 1e-12:
        return dt1

    return (
        (dt1 - dt2)
        / math.log(dt1 / dt2)
    )


def heat_transfer_duty_kw(
    U_W_m2K,
    area_m2,
    delta_t_lmtd_K,
):
    return (
        float(U_W_m2K)
        * float(area_m2)
        * float(delta_t_lmtd_K)
        / 1000.0
    )


def required_area_m2(
    duty_kw,
    U_W_m2K,
    delta_t_lmtd_K,
):
    denominator = (
        float(U_W_m2K)
        * float(delta_t_lmtd_K)
    )

    if denominator <= 0:
        return None

    return (
        float(duty_kw)
        * 1000.0
        / denominator
    )


def heat_removal_margin(
    available_duty_kw,
    required_duty_kw,
):
    if required_duty_kw <= 0:
        return None

    return (
        available_duty_kw
        / required_duty_kw
    )
