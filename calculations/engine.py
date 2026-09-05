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
    agitator,
):

    if volume_m3 <= 0:
        raise ValueError("Volume must be greater than zero.")

    if tank_diameter_m <= 0:
        raise ValueError("Tank diameter must be greater than zero.")

    if density_kg_m3 <= 0:
        raise ValueError("Density must be greater than zero.")

    if viscosity_pa_s <= 0:
        raise ValueError("Viscosity must be greater than zero.")

    if rpm <= 0:
        raise ValueError("RPM must be greater than zero.")

    if impeller_diameter_m <= 0:
        raise ValueError(
            "Impeller diameter must be greater than zero."
        )

    info = AGITATORS.get(
        agitator,
        {}
    )

    Np = info.get("np")
    Nq = info.get("nq")

    N = rpm / 60.0

    # -----------------------------------------------------
    # TIP SPEED
    # -----------------------------------------------------

    tip_speed = (
        math.pi *
        impeller_diameter_m *
        N
    )

    # -----------------------------------------------------
    # REYNOLDS
    # -----------------------------------------------------

    Re = (
        density_kg_m3 *
        N *
        impeller_diameter_m ** 2 /
        viscosity_pa_s
    )

    # -----------------------------------------------------
    # FROUDE
    # -----------------------------------------------------

    Fr = (
        N ** 2 *
        impeller_diameter_m /
        9.81
    )

    # -----------------------------------------------------
    # POWER
    # P = Np rho N^3 D^5
    # -----------------------------------------------------

    if Np is not None:

        power_w_per_impeller = (
            Np *
            density_kg_m3 *
            N ** 3 *
            impeller_diameter_m ** 5
        )

        power_w = (
            power_w_per_impeller *
            number_impellers
        )

        power_kw = power_w / 1000.0

        power_volume = (
            power_w /
            volume_m3
        )

        torque_nm = (
            power_w /
            (2.0 * math.pi * N)
        )

    else:

        power_w = None
        power_kw = None
        power_volume = None
        torque_nm = None

    # -----------------------------------------------------
    # PUMPING
    # Q = Nq N D^3
    # -----------------------------------------------------

    if Nq is not None:

        pumping_m3_s_per_impeller = (
            Nq *
            N *
            impeller_diameter_m ** 3
        )

        pumping_m3_h = (
            pumping_m3_s_per_impeller *
            3600.0 *
            number_impellers
        )

    else:

        pumping_m3_h = None

    # -----------------------------------------------------
    # Q/V
    # -----------------------------------------------------

    if (
        pumping_m3_h is not None
        and volume_m3 > 0
    ):

        pumping_per_volume = (
            pumping_m3_h /
            volume_m3
        )

        turnover_time_min = (
            volume_m3 /
            pumping_m3_h *
            60.0
        )

    else:

        pumping_per_volume = None
        turnover_time_min = None

    # -----------------------------------------------------
    # POWER NUMBER / PUMPING NUMBER
    # -----------------------------------------------------

    return {

        "Np": Np,

        "Nq": Nq,

        "tip_speed": tip_speed,

        "Re": Re,

        "reynolds_number": Re,

        "Fr": Fr,

        "froude_number": Fr,

        "power_w": power_w,

        "power_kw": power_kw,

        "power_volume": power_volume,

        "power_per_volume": power_volume,

        "torque_nm": torque_nm,

        "pumping_m3_h": pumping_m3_h,

        "pumping_per_volume": pumping_per_volume,

        "turnover_time_min": turnover_time_min,

    }
