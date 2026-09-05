import math

from libraries.agitator_geometry import AGITATORS


def calculate_reactor(
    volume_m3,
    tank_diameter_m,
    liquid_height_m,
    density_kg_m3,
    viscosity_pa_s,
    surface_tension_n_m,
    rpm,
    impeller_diameter_m,
    number_impellers,
    agitator
):

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    if volume_m3 <= 0:
        raise ValueError("Working volume must be greater than zero.")

    if tank_diameter_m <= 0:
        raise ValueError("Tank diameter must be greater than zero.")

    if impeller_diameter_m <= 0:
        raise ValueError("Impeller diameter must be greater than zero.")

    if rpm <= 0:
        raise ValueError("RPM must be greater than zero.")

    if density_kg_m3 <= 0:
        raise ValueError("Density must be greater than zero.")

    if viscosity_pa_s <= 0:
        raise ValueError("Viscosity must be greater than zero.")

    if number_impellers <= 0:
        raise ValueError("Number of impellers must be greater than zero.")

    # ---------------------------------------------------------
    # AGITATOR DATA
    # ---------------------------------------------------------

    agitator_info = AGITATORS.get(agitator, {})

    Np = agitator_info.get("np")
    Nq = agitator_info.get("nq")

    # ---------------------------------------------------------
    # BASIC SPEED
    # ---------------------------------------------------------

    N = rpm / 60.0

    # ---------------------------------------------------------
    # TIP SPEED
    # ---------------------------------------------------------

    tip_speed = (
        math.pi *
        impeller_diameter_m *
        N
    )

    # ---------------------------------------------------------
    # REYNOLDS NUMBER
    # ---------------------------------------------------------

    reynolds = (
        density_kg_m3 *
        N *
        impeller_diameter_m ** 2 /
        viscosity_pa_s
    )

    # ---------------------------------------------------------
    # FROUDE NUMBER
    # ---------------------------------------------------------

    g = 9.81

    froude = (
        N ** 2 *
        impeller_diameter_m /
        g
    )

    # ---------------------------------------------------------
    # POWER
    # ---------------------------------------------------------

    if Np is not None:

        power_per_impeller = (
            Np *
            density_kg_m3 *
            N ** 3 *
            impeller_diameter_m ** 5
        )

        total_power_w = (
            power_per_impeller *
            number_impellers
        )

        power_kw = total_power_w / 1000.0

        power_volume = (
            total_power_w /
            volume_m3
        )

    else:

        power_kw = None
        power_volume = None

    # ---------------------------------------------------------
    # TORQUE
    # ---------------------------------------------------------

    if power_kw is not None:

        torque_nm = (
            power_kw *
            1000.0 /
            (2.0 * math.pi * N)
        )

    else:

        torque_nm = None

    # ---------------------------------------------------------
    # PUMPING CAPACITY
    # ---------------------------------------------------------

    if Nq is not None:

        pumping_m3_s = (
            Nq *
            N *
            impeller_diameter_m ** 3
        )

        pumping_m3_h = (
            pumping_m3_s *
            3600.0 *
            number_impellers
        )

    else:

        pumping_m3_h = None

    # ---------------------------------------------------------
    # TURNOVER TIME
    # ---------------------------------------------------------

    if pumping_m3_h is not None and pumping_m3_h > 0:

        turnover_time_min = (
            volume_m3 /
            pumping_m3_h *
            60.0
        )

    else:

        turnover_time_min = None

    # ---------------------------------------------------------
    # RETURN RESULTS
    # ---------------------------------------------------------

    return {

        "tip_speed": tip_speed,

        "Re": reynolds,

        "reynolds_number": reynolds,

        "Fr": froude,

        "froude_number": froude,

        "power_kw": power_kw,

        "power_volume": power_volume,

        "power_per_volume": power_volume,

        "torque_nm": torque_nm,

        "pumping_m3_h": pumping_m3_h,

        "turnover_time_min": turnover_time_min,
    }
