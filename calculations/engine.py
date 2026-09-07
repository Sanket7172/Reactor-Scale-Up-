import math

from libraries.agitator_geometry import AGITATORS


# =========================================================
# CONSTANT
# =========================================================

G = 9.81  # m/s²


# =========================================================
# HELPER
# =========================================================

def _number(value, name):
    """Convert input to float and provide a clear error."""
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a numeric value.")


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
):
    """
    Reactor mixing and agitation calculations.

    INPUT UNITS
    -----------
    volume_m3            : m³
    tank_diameter_m     : m
    liquid_height_m     : m
    density_kg_m3       : kg/m³
    viscosity_pa_s      : Pa·s
    surface_tension_n_m : N/m
    rpm                  : rev/min
    impeller_diameter_m : m
    number_impellers    : -
    agitator             : key from AGITATORS
    impeller_clearance_m: m

    OUTPUT
    ------
    Power                 : W / kW
    Power density P/V     : W/m³ / kW/m³
    Tip speed             : m/s
    Reynolds number       : -
    Froude number         : -
    Weber number          : -
    Pumping               : m³/h
    Q/V                   : 1/h
    Turnover time         : min
    Torque                : N·m
    """

    # =====================================================
    # INPUT CONVERSION
    # =====================================================

    volume_m3 = _number(volume_m3, "Working volume")
    tank_diameter_m = _number(tank_diameter_m, "Tank diameter")
    liquid_height_m = _number(liquid_height_m, "Liquid height")
    density_kg_m3 = _number(density_kg_m3, "Density")
    viscosity_pa_s = _number(viscosity_pa_s, "Viscosity")
    surface_tension_n_m = _number(
        surface_tension_n_m,
        "Surface tension"
    )
    rpm = _number(rpm, "RPM")
    impeller_diameter_m = _number(
        impeller_diameter_m,
        "Impeller diameter"
    )

    try:
        number_impellers = int(number_impellers)
    except (TypeError, ValueError):
        raise ValueError(
            "Number of impellers must be an integer."
        )

    if impeller_clearance_m is not None:
        impeller_clearance_m = _number(
            impeller_clearance_m,
            "Impeller clearance"
        )

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
        raise ValueError(
            "Surface tension must be greater than zero."
        )

    if rpm <= 0:
        raise ValueError("RPM must be greater than zero.")

    if impeller_diameter_m <= 0:
        raise ValueError(
            "Impeller diameter must be greater than zero."
        )

    if number_impellers < 1:
        raise ValueError(
            "Number of impellers must be at least 1."
        )

    if impeller_clearance_m is not None:
        if impeller_clearance_m < 0:
            raise ValueError(
                "Impeller clearance cannot be negative."
            )

    # =====================================================
    # AGITATOR LIBRARY
    # =====================================================

    if agitator not in AGITATORS:
        raise ValueError(
            f"Agitator '{agitator}' not found in AGITATORS."
        )

    agitator_data = AGITATORS[agitator]

    if not isinstance(agitator_data, dict):
        raise ValueError(
            f"Invalid data for agitator '{agitator}'."
        )

    # Support both np/Np and nq/Nq naming
    np_value = agitator_data.get("np")

    if np_value is None:
        np_value = agitator_data.get("Np")

    nq_value = agitator_data.get("nq")

    if nq_value is None:
        nq_value = agitator_data.get("Nq")

    # Np is required for power calculation
    if np_value is None:
        raise ValueError(
            f"Np is missing for agitator '{agitator}'."
        )

    np_value = _number(
        np_value,
        f"Np for {agitator}"
    )

    if np_value <= 0:
        raise ValueError(
            f"Np must be greater than zero for '{agitator}'."
        )

    # Nq is optional
    if nq_value is not None:
        nq_value = _number(
            nq_value,
            f"Nq for {agitator}"
        )

        if nq_value <= 0:
            raise ValueError(
                f"Nq must be greater than zero for '{agitator}'."
            )

    # =====================================================
    # BASIC VARIABLES
    # =====================================================

    rho = density_kg_m3
    mu = viscosity_pa_s
    sigma = surface_tension_n_m

    T = tank_diameter_m
    D = impeller_diameter_m

    # =====================================================
    # RPM TO REV/S
    # =====================================================

    N = rpm / 60.0

    # =====================================================
    # GEOMETRY RATIOS
    # =====================================================

    D_T = D / T

    H_T = liquid_height_m / T

    C_T = None

    if impeller_clearance_m is not None:
        C_T = impeller_clearance_m / T

    # =====================================================
    # TIP SPEED
    #
    # u = πDN
    #
    # Result = m/s
    # =====================================================

    tip_speed_m_s = math.pi * D * N

    # =====================================================
    # REYNOLDS NUMBER
    #
    # Re = ρND² / μ
    # =====================================================

    reynolds_number = (
        rho
        * N
        * D**2
        / mu
    )

    # =====================================================
    # FROUDE NUMBER
    #
    # Fr = N²D / g
    # =====================================================

    froude_number = (
        N**2
        * D
        / G
    )

    # =====================================================
    # WEBER NUMBER
    #
    # We = ρN²D³ / σ
    # =====================================================

    weber_number = (
        rho
        * N**2
        * D**3
        / sigma
    )

    # =====================================================
    # POWER
    #
    # P = Np × ρ × N³ × D⁵
    #
    # P = W
    # =====================================================

    power_single_w = (
        np_value
        * rho
        * N**3
        * D**5
    )

    # Preliminary multi-impeller estimate
    power_total_w = (
        power_single_w
        * number_impellers
    )

    # =====================================================
    # POWER → kW
    # =====================================================

    power_single_kw = (
        power_single_w / 1000.0
    )

    power_total_kw = (
        power_total_w / 1000.0
    )

    # =====================================================
    # POWER / VOLUME
    #
    # W/m³
    # =====================================================

    power_density_w_m3 = (
        power_total_w
        / volume_m3
    )

    # =====================================================
    # POWER / VOLUME
    #
    # kW/m³
    #
    # 1 kW = 1000 W
    # =====================================================

    power_density_kw_m3 = (
        power_density_w_m3 / 1000.0
    )

    # =====================================================
    # TORQUE
    #
    # T = P / (2πN)
    #
    # P = W
    # N = rev/s
    #
    # Result = N·m
    # =====================================================

    torque_nm = (
        power_total_w
        / (2.0 * math.pi * N)
    )

    # =====================================================
    # PUMPING CAPACITY
    #
    # Q = Nq × N × D³
    #
    # Result = m³/s
    # =====================================================

    pumping_single_m3_s = None
    pumping_total_m3_s = None

    if nq_value is not None:

        pumping_single_m3_s = (
            nq_value
            * N
            * D**3
        )

        pumping_total_m3_s = (
            pumping_single_m3_s
            * number_impellers
        )

    # =====================================================
    # PUMPING → m³/h
    # =====================================================

    pumping_single_m3_h = None
    pumping_total_m3_h = None

    if pumping_single_m3_s is not None:

        pumping_single_m3_h = (
            pumping_single_m3_s
            * 3600.0
        )

        pumping_total_m3_h = (
            pumping_total_m3_s
            * 3600.0
        )

    # =====================================================
    # Q/V
    #
    # Q/V = (m³/h) / m³
    #
    # Result = 1/h
    # =====================================================

    qv_1_h = None

    if pumping_total_m3_h is not None:

        qv_1_h = (
            pumping_total_m3_h
            / volume_m3
        )

    # =====================================================
    # TURNOVER TIME
    #
    # Turnover time = V/Q
    #
    # Result = min
    # =====================================================

    turnover_time_min = None

    if qv_1_h is not None and qv_1_h > 0:

        turnover_time_min = (
            60.0 / qv_1_h
        )

    # =====================================================
    # MIXING REGIME
    # =====================================================

    if reynolds_number < 10:

        mixing_regime = "Laminar"

    elif reynolds_number < 10000:

        mixing_regime = "Transitional"

    else:

        mixing_regime = "Turbulent"

    # =====================================================
    # ENGINEERING WARNINGS
    # =====================================================

    engineering_warnings = []

    if D_T < 0.20:
        engineering_warnings.append(
            "D/T is low. Verify impeller diameter and circulation."
        )

    if D_T > 0.70:
        engineering_warnings.append(
            "D/T is high. Verify power and mechanical suitability."
        )

    if H_T < 0.50:
        engineering_warnings.append(
            "H/T is low. Verify impeller submergence."
        )

    if H_T > 2.50:
        engineering_warnings.append(
            "H/T is high. Check need for multiple impellers."
        )

    if C_T is not None and C_T < 0.15:
        engineering_warnings.append(
            "C/T is low. Verify bottom clearance."
        )

    if reynolds_number < 10:
        engineering_warnings.append(
            "Laminar regime detected. Verify applicability "
            "of the selected power correlation."
        )

    if number_impellers > 1:
        engineering_warnings.append(
            "Multiple-impeller power and pumping are estimated "
            "by additive scaling. Detailed hydrodynamic analysis "
            "is recommended for final design."
        )

    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {

        # =================================================
        # BASIC
        # =================================================

        "volume_m3": volume_m3,

        "tank_diameter_m": tank_diameter_m,

        "liquid_height_m": liquid_height_m,

        "rpm": rpm,

        "rotational_speed_rps": N,

        # =================================================
        # AGITATOR
        # =================================================

        "agitator": agitator,

        "Np": np_value,

        "Nq": nq_value,

        "number_impellers": number_impellers,

        "impeller_diameter_m": D,

        # =================================================
        # GEOMETRY
        # =================================================

        "D_T": D_T,

        "D_T_ratio": D_T,

        "H_T": H_T,

        "H_T_ratio": H_T,

        "C_T": C_T,

        "clearance_T": C_T,

        # =================================================
        # HYDRODYNAMIC PARAMETERS
        # =================================================

        "tip_speed": tip_speed_m_s,

        "tip_speed_m_s": tip_speed_m_s,

        "Re": reynolds_number,

        "reynolds_number": reynolds_number,

        "Fr": froude_number,

        "froude_number": froude_number,

        "We": weber_number,

        "weber_number": weber_number,

        # =================================================
        # POWER
        # =================================================

        "power_single_w": power_single_w,

        "power_single_kw": power_single_kw,

        "power_w": power_total_w,

        "power_kw": power_total_kw,

        # =================================================
        # P/V
        # =================================================

        "power_density_w_m3": power_density_w_m3,

        "power_density_kw_m3": power_density_kw_m3,

        "specific_power_kw_m3": power_density_kw_m3,

        # Compatibility aliases
        "power_volume": power_density_w_m3,

        "power_per_volume": power_density_w_m3,

        # =================================================
        # TORQUE
        # =================================================

        "torque_nm": torque_nm,

        # =================================================
        # PUMPING
        # =================================================

        "pumping_single_m3_s": pumping_single_m3_s,

        "pumping_single_m3_h": pumping_single_m3_h,

        "pumping_m3_s": pumping_total_m3_s,

        "pumping_m3_h": pumping_total_m3_h,

        # =================================================
        # Q/V
        # =================================================

        "qv_1_h": qv_1_h,

        "pumping_per_volume": qv_1_h,

        # =================================================
        # TURNOVER
        # =================================================

        "turnover_time_min": turnover_time_min,

        # =================================================
        # MIXING REGIME
        # =================================================

        "mixing_regime": mixing_regime,

        # =================================================
        # PROCESS PROPERTIES
        # =================================================

        "density_kg_m3": rho,

        "viscosity_pa_s": mu,

        "surface_tension_n_m": sigma,

        # =================================================
        # WARNINGS
        # =================================================

        "engineering_warnings": engineering_warnings,
    }
