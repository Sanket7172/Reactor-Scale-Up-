import math

from libraries.agitator_geometry import AGITATORS


G = 9.81


# =========================================================
# HELPERS
# =========================================================

def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _positive(value, name):
    value = _safe_float(value)

    if value is None or value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


# =========================================================
# MAIN REACTOR CALCULATION
# =========================================================

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

    # -----------------------------------------------------
    # Gas-Liquid inputs
    # -----------------------------------------------------

    gas_flow_m3_h=0.0,
    gas_density_kg_m3=1.2,
    gas_viscosity_pa_s=1.8e-5,
    gas_diffusivity_m2_s=2.0e-9,
    bubble_diameter_mm=3.0,
    gas_holdup_fraction=0.05,
):
    """
    Preliminary process engineering calculation engine.

    Units:
        volume                 m3
        diameter/height       m
        density                kg/m3
        viscosity              Pa.s
        surface tension        N/m
        RPM                    rev/min
        gas flow               m3/h
        bubble diameter        mm

    IMPORTANT:
        This is a screening-level engineering model.
        Final Np/Nq, Njs, kLa, flooding, blend time and
        mechanical design require validated correlations,
        vendor data and/or experimental data.
    """

    # =====================================================
    # INPUT VALIDATION
    # =====================================================

    V = _positive(volume_m3, "Working volume")
    T = _positive(tank_diameter_m, "Tank diameter")
    H = _positive(liquid_height_m, "Liquid height")
    rho = _positive(density_kg_m3, "Liquid density")
    mu = _positive(viscosity_pa_s, "Liquid viscosity")
    sigma = _positive(
        surface_tension_n_m,
        "Surface tension"
    )
    rpm = _positive(rpm, "RPM")
    D = _positive(
        impeller_diameter_m,
        "Impeller diameter"
    )

    nimp = int(number_impellers)

    if nimp < 1:
        raise ValueError(
            "Number of impellers must be at least 1."
        )

    if agitator not in AGITATORS:
        raise ValueError(
            f"Agitator '{agitator}' is not available."
        )

    if impeller_clearance_m is not None:
        if impeller_clearance_m < 0:
            raise ValueError(
                "Impeller clearance cannot be negative."
            )

    # =====================================================
    # AGITATOR DATA
    # =====================================================

    agitator_data = AGITATORS[agitator]

    Np = agitator_data.get("np")
    Nq = agitator_data.get("nq")

    # =====================================================
    # BASIC VARIABLES
    # =====================================================

    N = rpm / 60.0

    # =====================================================
    # GEOMETRY RATIOS
    # =====================================================

    D_T = D / T

    H_T = H / T

    clearance_T = None

    if impeller_clearance_m is not None:
        clearance_T = (
            impeller_clearance_m / T
        )

    # =====================================================
    # TIP SPEED
    # =====================================================

    tip_speed = math.pi * D * N

    # =====================================================
    # REYNOLDS NUMBER
    # =====================================================

    Re = (
        rho *
        N *
        D**2 /
        mu
    )

    # =====================================================
    # FROUDE NUMBER
    # =====================================================

    Fr = (
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
            power_w / V
        )

        power_volume_kw_m3 = (
            power_volume_w_m3 / 1000.0
        )

        torque_nm = (
            power_w /
            (2.0 * math.pi * N)
        )

    # =====================================================
    # PUMPING CAPACITY
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
            V
        )

        if qv_1_h > 0:
            turnover_time_min = (
                60.0 /
                qv_1_h
            )

    # =====================================================
    # MIXING REGIME
    # =====================================================

    if Re < 10:
        regime = "Laminar"

    elif Re < 10000:
        regime = "Transitional"

    else:
        regime = "Turbulent"

    # =====================================================
    # GAS-LIQUID CALCULATIONS
    # =====================================================

    gas_results = calculate_gas_liquid_parameters(
        tank_diameter_m=T,
        liquid_height_m=H,
        liquid_density_kg_m3=rho,
        liquid_viscosity_pa_s=mu,
        gas_flow_m3_h=gas_flow_m3_h,
        gas_density_kg_m3=gas_density_kg_m3,
        gas_viscosity_pa_s=gas_viscosity_pa_s,
        diffusivity_m2_s=gas_diffusivity_m2_s,
        bubble_diameter_mm=bubble_diameter_mm,
        gas_holdup_fraction=gas_holdup_fraction,
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        # -------------------------------------------------
        # BASIC
        # -------------------------------------------------

        "volume_m3": V,
        "tank_diameter_m": T,
        "liquid_height_m": H,

        # -------------------------------------------------
        # MIXING
        # -------------------------------------------------

        "tip_speed": tip_speed,

        "Re": Re,
        "reynolds_number": Re,

        "Fr": Fr,
        "froude_number": Fr,

        "mixing_regime": regime,

        # -------------------------------------------------
        # AGITATOR
        # -------------------------------------------------

        "Np": Np,
        "Nq": Nq,

        "agitator": agitator,

        "number_impellers": nimp,

        "impeller_diameter_m": D,

        # -------------------------------------------------
        # POWER
        # -------------------------------------------------

        "power_w": power_w,

        "power_kw": power_kw,

        "power_volume": power_volume_w_m3,

        "power_per_volume": power_volume_w_m3,

        "power_volume_w_m3": power_volume_w_m3,

        "power_volume_kw_m3": power_volume_kw_m3,

        "specific_power_kw_m3":
            power_volume_kw_m3,

        # -------------------------------------------------
        # TORQUE
        # -------------------------------------------------

        "torque_nm": torque_nm,

        # -------------------------------------------------
        # PUMPING
        # -------------------------------------------------

        "pumping_m3_s": pumping_m3_s,

        "pumping_m3_h": pumping_m3_h,

        "qv_1_h": qv_1_h,

        "pumping_per_volume": qv_1_h,

        "turnover_time_min":
            turnover_time_min,

        # -------------------------------------------------
        # GEOMETRY
        # -------------------------------------------------

        "D_T": D_T,

        "H_T": H_T,

        "clearance_T": clearance_T,

        # -------------------------------------------------
        # PROPERTIES
        # -------------------------------------------------

        "density_kg_m3": rho,

        "viscosity_pa_s": mu,

        "surface_tension_n_m": sigma,

        # -------------------------------------------------
        # GAS-LIQUID
        # -------------------------------------------------

        **gas_results,
    }


# =========================================================
# GAS-LIQUID ENGINE
# =========================================================

def calculate_gas_liquid_parameters(
    tank_diameter_m,
    liquid_height_m,
    liquid_density_kg_m3,
    liquid_viscosity_pa_s,
    gas_flow_m3_h=0.0,
    gas_density_kg_m3=1.2,
    gas_viscosity_pa_s=1.8e-5,
    diffusivity_m2_s=2.0e-9,
    bubble_diameter_mm=3.0,
    gas_holdup_fraction=0.05,
):
    """
    Screening-level gas-liquid mass-transfer calculation.

    Uses:
        Re_b = rho_L * u_b * d_b / mu_L

        Sc = mu_L / (rho_L * D_AB)

        Sh = 2 + 0.6 Re^0.5 Sc^1/3

        kL = Sh * D_AB / d_b

        a = 6 * epsilon_g / d_b

        kLa = kL * a

    Bubble rise velocity is estimated using a simplified
    terminal velocity expression.

    This is NOT a final design correlation.
    """

    result = {
        "gas_flow_m3_h": gas_flow_m3_h,
        "gas_superficial_velocity_m_s": None,
        "gas_holdup_fraction": None,
        "bubble_diameter_m": None,
        "bubble_rise_velocity_m_s": None,
        "bubble_residence_time_s": None,
        "bubble_residence_time_min": None,
        "bubble_reynolds": None,
        "schmidt_number": None,
        "sherwood_number": None,
        "kL_m_s": None,
        "interfacial_area_m2_m3": None,
        "kLa_1_s": None,
        "kLa_1_h": None,
        "gas_liquid_status": "NOT ACTIVE",
    }

    if gas_flow_m3_h is None or gas_flow_m3_h <= 0:
        return result

    d_b = (
        float(bubble_diameter_mm) /
        1000.0
    )

    if d_b <= 0:
        return result

    epsilon_g = max(
        0.001,
        min(
            float(gas_holdup_fraction),
            0.50
        )
    )

    area = (
        math.pi *
        tank_diameter_m**2 /
        4.0
    )

    if area <= 0:
        return result

    # -----------------------------------------------------
    # Gas superficial velocity
    # -----------------------------------------------------

    Qg = (
        float(gas_flow_m3_h) /
        3600.0
    )

    superficial_velocity = (
        Qg / area
    )

    # -----------------------------------------------------
    # Bubble rise velocity
    # -----------------------------------------------------
    #
    # Simplified screening expression.
    # For small bubbles:
    #
    # U ~ sqrt(g*d)
    #
    # with a correction factor.
    # -----------------------------------------------------

    bubble_velocity = (
        0.71 *
        math.sqrt(
            G * d_b
        )
    )

    bubble_velocity = max(
        0.01,
        bubble_velocity
    )

    # -----------------------------------------------------
    # Residence/contact time
    # -----------------------------------------------------

    residence_time_s = (
        liquid_height_m /
        bubble_velocity
    )

    # -----------------------------------------------------
    # Bubble Reynolds
    # -----------------------------------------------------

    bubble_re = (
        liquid_density_kg_m3 *
        bubble_velocity *
        d_b /
        liquid_viscosity_pa_s
    )

    # -----------------------------------------------------
    # Schmidt number
    # -----------------------------------------------------

    Sc = (
        liquid_viscosity_pa_s /
        (
            liquid_density_kg_m3 *
            diffusivity_m2_s
        )
    )

    # -----------------------------------------------------
    # Sherwood number
    # -----------------------------------------------------

    Sh = (
        2.0 +
        0.6 *
        math.sqrt(
            max(bubble_re, 0.0)
        ) *
        Sc ** (1.0 / 3.0)
    )

    # -----------------------------------------------------
    # Liquid-side mass transfer coefficient
    # -----------------------------------------------------

    kL = (
        Sh *
        diffusivity_m2_s /
        d_b
    )

    # -----------------------------------------------------
    # Interfacial area
    #
    # a = 6 epsilon / db
    # -----------------------------------------------------

    interfacial_area = (
        6.0 *
        epsilon_g /
        d_b
    )

    # -----------------------------------------------------
    # kLa
    # -----------------------------------------------------

    kLa_s = (
        kL *
        interfacial_area
    )

    kLa_h = (
        kLa_s *
        3600.0
    )

    result.update(
        {
            "gas_flow_m3_h":
                float(gas_flow_m3_h),

            "gas_superficial_velocity_m_s":
                superficial_velocity,

            "gas_holdup_fraction":
                epsilon_g,

            "bubble_diameter_m":
                d_b,

            "bubble_rise_velocity_m_s":
                bubble_velocity,

            "bubble_residence_time_s":
                residence_time_s,

            "bubble_residence_time_min":
                residence_time_s / 60.0,

            "bubble_reynolds":
                bubble_re,

            "schmidt_number":
                Sc,

            "sherwood_number":
                Sh,

            "kL_m_s":
                kL,

            "interfacial_area_m2_m3":
                interfacial_area,

            "kLa_1_s":
                kLa_s,

            "kLa_1_h":
                kLa_h,

            "gas_liquid_status":
                "SCREENING ESTIMATE",
        }
    )

    return result
