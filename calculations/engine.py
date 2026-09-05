import math

from libraries.agitator_geometry import AGITATORS


def calculate_results(
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
    """
    Reactor mixing and scale-up calculations.

    All calculation inputs are expected in SI units:
        volume_m3              -> m3
        tank_diameter_m        -> m
        liquid_height_m        -> m
        density_kg_m3          -> kg/m3
        viscosity_pa_s         -> Pa.s
        surface_tension_n_m    -> N/m
        rpm                    -> rev/min
        impeller_diameter_m    -> m
        number_impellers       -> dimensionless
    """

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    if volume_m3 <= 0:
        raise ValueError("Working volume must be greater than zero.")

    if tank_diameter_m <= 0:
        raise ValueError("Tank diameter must be greater than zero.")

    if liquid_height_m < 0:
        raise ValueError("Liquid height cannot be negative.")

    if density_kg_m3 <= 0:
        raise ValueError("Density must be greater than zero.")

    if viscosity_pa_s <= 0:
        raise ValueError("Viscosity must be greater than zero.")

    if rpm <= 0:
        raise ValueError("RPM must be greater than zero.")

    if impeller_diameter_m <= 0:
        raise ValueError("Impeller diameter must be greater than zero.")

    if number_impellers <= 0:
        raise ValueError(
            "Number of impellers must be greater than zero."
        )

    # ---------------------------------------------------------
    # AGITATOR DATA
    # ---------------------------------------------------------

    agitator_data = AGITATORS.get(agitator)

    if agitator_data is None:
        raise ValueError(
            f"Unknown agitator type: {agitator}"
        )

    Np = agitator_data.get("np")
    Nq = agitator_data.get("nq")

    # ---------------------------------------------------------
    # SPEED
    # ---------------------------------------------------------

    # RPM -> revolutions per second
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
        impeller_diameter_m ** 2
        /
        viscosity_pa_s
    )

    # ---------------------------------------------------------
    # FROUDE NUMBER
    # ---------------------------------------------------------

    g = 9.81

    froude = (
        N ** 2 *
        impeller_diameter_m
        /
        g
    )

    # ---------------------------------------------------------
    # POWER CALCULATION
    # ---------------------------------------------------------

    if Np is not None:

        power_per_impeller_w = (
            Np *
            density_kg_m3 *
            N ** 3 *
            impeller_diameter_m ** 5
        )

        total_power_w = (
            power_per_impeller_w *
            number_impellers
        )

        power_kw = (
            total_power_w /
            1000.0
        )

        # W/m3
        power_per_volume = (
            total_power_w /
            volume_m3
        )

    else:

        # RCI or other agitators where Np
        # is not yet defined
        power_kw = float("nan")

        power_per_volume = float("nan")

    # ---------------------------------------------------------
    # TORQUE
    # ---------------------------------------------------------

    if (
        N > 0
        and not math.isnan(power_kw)
    ):

        torque_nm = (
            power_kw *
            1000.0
            /
            (
                2.0 *
                math.pi *
                N
            )
        )

    else:

        torque_nm = float("nan")

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

        pumping_m3_h = float("nan")

    # ---------------------------------------------------------
    # TURNOVER TIME
    # ---------------------------------------------------------

    if (
        pumping_m3_h > 0
        and not math.isnan(pumping_m3_h)
    ):

        turnover_time_min = (
            volume_m3 /
            pumping_m3_h *
            60.0
        )

    else:

        turnover_time_min = float("nan")

    # ---------------------------------------------------------
    # RETURN RESULTS
    # ---------------------------------------------------------

    return {

        # Geometry / liquid
        "liquid_height": liquid_height_m,

        # Mixing
        "tip_speed": tip_speed,

        "reynolds_number": reynolds,

        "Re": reynolds,

        "froude_number": froude,

        "Fr": froude,

        # Power
        "power_kw": power_kw,

        "power_per_volume": power_per_volume,

        "power_volume": power_per_volume,

        # Mechanical
        "torque_nm": torque_nm,

        # Pumping
        "pumping_m3_h": pumping_m3_h,

        "turnover_time_min": turnover_time_min,

        # Additional inputs for future calculations
        "density_kg_m3": density_kg_m3,

        "viscosity_pa_s": viscosity_pa_s,

        "surface_tension_n_m": surface_tension_n_m,

        "rpm": rpm,

        "impeller_diameter_m": impeller_diameter_m,

        "number_impellers": number_impellers,

        "agitator": agitator,
    }
