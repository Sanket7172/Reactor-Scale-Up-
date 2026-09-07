import math

from libraries.agitator_geometry import AGITATORS


G = 9.81


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
    impeller_clearance_m=None,

    # Gas-liquid inputs
    gas_flow_m3_h=0.0,
    gas_density_kg_m3=1.20,
    bubble_diameter_m=0.003,
    gas_holdup_fraction=0.0,
):
    """
    Preliminary reactor mixing calculation.

    All results are screening-level unless supported by
    validated impeller/vendor/literature correlations.
    """

    # =====================================================
    # INPUT VALIDATION
    # =====================================================

    if volume_m3 <= 0:
        raise ValueError("Working volume must be greater than zero.")

    if tank_diameter_m <= 0:
        raise ValueError("Tank diameter must be greater than zero.")

    if liquid_height_m <= 0:
        raise ValueError("Liquid height must be greater than zero.")

    if density_kg_m3 <= 0:
        raise ValueError("Density must be greater than zero.")

    if viscosity_pa_s <= 0:
        raise ValueError("Viscosity must be greater than zero.")

    if surface_tension_n_m <= 0:
        raise ValueError("Surface tension must be greater than zero.")

    if rpm <= 0:
        raise ValueError("Agitator speed must be greater than zero.")

    if impeller_diameter_m <= 0:
        raise ValueError("Impeller diameter must be greater than zero.")

    if number_impellers < 1:
        raise ValueError("Number of impellers must be at least 1.")

    if agitator not in AGITATORS:
        raise ValueError(
            f"Agitator '{agitator}' is not available."
        )

    # =====================================================
    # BASIC VARIABLES
    # =====================================================

    rho = float(density_kg_m3)
    mu = float(viscosity_pa_s)
    D = float(impeller_diameter_m)
    T = float(tank_diameter_m)

    N_rpm = float(rpm)
    N = N_rpm / 60.0

    nimp = int(number_impellers)

    agitator_data = AGITATORS[agitator]

    Np = agitator_data.get("np")
    Nq = agitator_data.get("nq")

    # =====================================================
    # GEOMETRY RATIOS
    # =====================================================

    D_T = D / T

    H_T = liquid_height_m / T

    clearance_T = None

    if impeller_clearance_m is not None:

        if impeller_clearance_m < 0:
            raise ValueError(
                "Impeller clearance cannot be negative."
            )

        clearance_T = impeller_clearance_m / T

    # =====================================================
    # TIP SPEED
    # =====================================================

    tip_speed = math.pi * D * N

    # =====================================================
    # REYNOLDS NUMBER
    # =====================================================

    reynolds = (
        rho *
        N *
        D**2 /
        mu
    )

    # =====================================================
    # FROUDE NUMBER
    # =====================================================

    froude = (
        N**2 *
        D /
        G
    )

    # =====================================================
    # POWER
    # =====================================================

    power_w = None
    power_kw = None
    power_volume_w_m3 = None
    power_volume_kw_m3 = None
    torque_nm = None

    if Np is not None:

        power_w = (
            Np *
            rho *
            N**3 *
            D**5 *
            nimp
        )

        power_kw = power_w / 1000.0

        power_volume_w_m3 = (
            power_w /
            volume_m3
        )

        # PRIMARY ENGINEERING RESULT
        power_volume_kw_m3 = (
            power_kw /
            volume_m3
        )

        torque_nm = (
            power_w /
            (2.0 * math.pi * N)
        )

    # =====================================================
    # PUMPING
    # =====================================================

    pumping_m3_s = None
    pumping_m3_h = None
    qv_1_h = None
    turnover_time_min = None

    if Nq is not None:

        pumping_m3_s = (
            Nq *
            N *
            D**3 *
            nimp
        )

        pumping_m3_h = (
            pumping_m3_s *
            3600.0
        )

        qv_1_h = (
            pumping_m3_h /
            volume_m3
        )

        if qv_1_h > 0:

            turnover_time_min = (
                60.0 /
                qv_1_h
            )

    # =====================================================
    # MIXING REGIME
    # =====================================================

    if reynolds < 10:
        mixing_regime = "Laminar"

    elif reynolds < 10000:
        mixing_regime = "Transitional"

    else:
        mixing_regime = "Turbulent"

    # =====================================================
    # GAS-LIQUID SCREENING
    # =====================================================

    gas_result = calculate_gas_liquid_screening(
        volume_m3=volume_m3,
        liquid_height_m=liquid_height_m,
        tank_diameter_m=T,
        gas_flow_m3_h=gas_flow_m3_h,
        gas_density_kg_m3=gas_density_kg_m3,
        bubble_diameter_m=bubble_diameter_m,
        density_kg_m3=rho,
        viscosity_pa_s=mu,
        surface_tension_n_m=surface_tension_n_m,
        power_volume_w_m3=power_volume_w_m3,
        gas_holdup_fraction=gas_holdup_fraction,
    )

    return {

        "tip_speed": tip_speed,

        "Re": reynolds,
        "reynolds_number": reynolds,

        "Fr": froude,
        "froude_number": froude,

        "Np": Np,
        "Nq": Nq,

        "agitator": agitator,
        "number_impellers": nimp,
        "impeller_diameter_m": D,

        "power_w": power_w,
        "power_kw": power_kw,

        # W/m3 retained for reference
        "power_volume": power_volume_w_m3,
        "power_volume_w_m3": power_volume_w_m3,

        # NEW PRIMARY VALUE
        "power_volume_kw_m3": power_volume_kw_m3,

        "specific_power_kw_m3": power_volume_kw_m3,

        "torque_nm": torque_nm,

        "pumping_m3_s": pumping_m3_s,
        "pumping_m3_h": pumping_m3_h,

        "qv_1_h": qv_1_h,
        "pumping_per_volume": qv_1_h,

        "turnover_time_min": turnover_time_min,

        "D_T": D_T,
        "H_T": H_T,
        "clearance_T": clearance_T,

        "mixing_regime": mixing_regime,

        "viscosity_pa_s": mu,
        "density_kg_m3": rho,
        "surface_tension_n_m": surface_tension_n_m,

        # Gas-liquid
        **gas_result,
    }


def calculate_gas_liquid_screening(
    volume_m3,
    liquid_height_m,
    tank_diameter_m,
    gas_flow_m3_h,
    gas_density_kg_m3,
    bubble_diameter_m,
    density_kg_m3,
    viscosity_pa_s,
    surface_tension_n_m,
    power_volume_w_m3,
    gas_holdup_fraction=0.0,
):
    """
    Screening-level gas-liquid calculations.

    kLa should NOT be treated as a final design value.
    Use validated system-specific correlations or pilot data
    for final design.
    """

    result = {
        "gas_flow_m3_h": gas_flow_m3_h,
        "gas_superficial_velocity_m_s": None,
        "gas_holdup_percent": None,
        "bubble_rise_velocity_m_s": None,
        "bubble_residence_time_s": None,
        "bubble_residence_time_min": None,
        "interfacial_area_m2_m3": None,
        "kla_1_h": None,
        "kla_1_s": None,
    }

    if gas_flow_m3_h <= 0:
        return result

    if bubble_diameter_m <= 0:
        return result

    cross_section = (
        math.pi /
        4.0 *
        tank_diameter_m**2
    )

    gas_flow_m3_s = (
        gas_flow_m3_h /
        3600.0
    )

    superficial_velocity = (
        gas_flow_m3_s /
        cross_section
    )

    # =====================================================
    # BUBBLE RISE VELOCITY
    # =====================================================

    # Screening Stokes velocity.
    # Appropriate only for small, approximately spherical
    # bubbles in creeping-flow conditions.

    bubble_velocity_stokes = (
        (
            density_kg_m3 -
            gas_density_kg_m3
        )
        * G *
        bubble_diameter_m**2
        /
        (
            18.0 *
            viscosity_pa_s
        )
    )

    # Prevent unrealistic zero/negative velocity.
    bubble_velocity = max(
        0.001,
        bubble_velocity_stokes
    )

    # =====================================================
    # RESIDENCE TIME
    # =====================================================

    residence_time_s = (
        liquid_height_m /
        bubble_velocity
    )

    residence_time_min = (
        residence_time_s /
        60.0
    )

    # =====================================================
    # GAS HOLDUP
    # =====================================================

    if gas_holdup_fraction <= 0:

        # Very rough screening estimate.
        estimated_holdup = min(
            0.20,
            0.02 +
            0.0005 *
            max(power_volume_w_m3 or 0, 0) +
            0.01 *
            superficial_velocity
        )

        gas_holdup = estimated_holdup

    else:

        gas_holdup = min(
            max(gas_holdup_fraction, 0.0),
            0.80
        )

    # =====================================================
    # INTERFACIAL AREA
    # =====================================================

    # a = 6 * epsilon_g / d_b

    interfacial_area = (
        6.0 *
        gas_holdup /
        bubble_diameter_m
    )

    # =====================================================
    # SCREENING kLa
    # =====================================================

    # Approximate mass-transfer coefficient.
    #
    # This is deliberately labelled screening-level.
    # Actual kLa requires a validated correlation.

    kla_s = (
        0.10 *
        (
            max(
                power_volume_w_m3 or 0.0,
                0.001
            )
            ** 0.5
        )
        *
        (
            max(
                superficial_velocity,
                0.0001
            )
            ** 0.30
        )
    )

    kla_h = kla_s * 3600.0

    result.update(
        {
            "gas_superficial_velocity_m_s":
                superficial_velocity,

            "gas_holdup_percent":
                gas_holdup * 100.0,

            "bubble_rise_velocity_m_s":
                bubble_velocity,

            "bubble_residence_time_s":
                residence_time_s,

            "bubble_residence_time_min":
                residence_time_min,

            "interfacial_area_m2_m3":
                interfacial_area,

            "kla_1_s":
                kla_s,

            "kla_1_h":
                kla_h,
        }
    )

    return result
