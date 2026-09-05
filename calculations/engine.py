import math

from libraries.agitator_geometry import AGITATORS


# =========================================================
# CONSTANTS
# =========================================================

G = 9.81


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
    Calculate preliminary reactor mixing and agitation parameters.

    Parameters
    ----------
    volume_m3 : float
        Working liquid/slurry volume, m3

    tank_diameter_m : float
        Reactor internal diameter, m

    liquid_height_m : float
        Operating liquid height, m

    density_kg_m3 : float
        Process density, kg/m3

    viscosity_pa_s : float
        Dynamic viscosity, Pa.s

    surface_tension_n_m : float
        Surface tension, N/m

    rpm : float
        Agitator speed, RPM

    impeller_diameter_m : float
        Impeller diameter, m

    number_impellers : int
        Number of impellers

    agitator : str
        Agitator name from AGITATORS library

    impeller_clearance_m : float, optional
        Bottom clearance of impeller, m
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

    if rpm <= 0:
        raise ValueError("RPM must be greater than zero.")

    if impeller_diameter_m <= 0:
        raise ValueError(
            "Impeller diameter must be greater than zero."
        )

    if number_impellers <= 0:
        raise ValueError(
            "Number of impellers must be at least 1."
        )

    if agitator not in AGITATORS:
        raise ValueError(
            f"Agitator '{agitator}' is not available in the agitator library."
        )

    # =====================================================
    # AGITATOR DATA
    # =====================================================

    agitator_data = AGITATORS.get(
        agitator,
        {}
    )

    np_num = agitator_data.get("np")
    nq = agitator_data.get("nq")

    # =====================================================
    # BASIC VARIABLES
    # =====================================================

    rho = float(density_kg_m3)
    mu = float(viscosity_pa_s)
    D = float(impeller_diameter_m)
    T = float(tank_diameter_m)
    N_rpm = float(rpm)
    nimp = int(number_impellers)

    # Convert RPM to revolutions/sec
    N = N_rpm / 60.0

    # =====================================================
    # GEOMETRY RATIOS
    # =====================================================

    D_T = D / T if T > 0 else 0.0

    H_T = (
        liquid_height_m / T
        if T > 0
        else 0.0
    )

    clearance_T = None

    if impeller_clearance_m is not None:

        if impeller_clearance_m < 0:
            raise ValueError(
                "Impeller clearance cannot be negative."
            )

        clearance_T = (
            impeller_clearance_m / T
            if T > 0
            else 0.0
        )

    # =====================================================
    # TIP SPEED
    # =====================================================

    tip_speed = math.pi * D * N

    # =====================================================
    # REYNOLDS NUMBER
    # =====================================================

    reynolds = (
        rho
        * N
        * D**2
        / mu
    )

    # =====================================================
    # FROUDE NUMBER
    # =====================================================

    froude = (
        N**2
        * D
        / G
    )

    # =====================================================
    # POWER
    # =====================================================

    power_w = None
    power_kw = None
    power_volume = None
    torque_nm = None

    if np_num is not None:

        power_w = (
            np_num
            * rho
            * N**3
            * D**5
            * nimp
        )

        power_kw = power_w / 1000.0

        if volume_m3 > 0:
            power_volume = (
                power_w
                / volume_m3
            )

        if N > 0:
            torque_nm = (
                power_w
                / (2.0 * math.pi * N)
            )

    # =====================================================
    # PUMPING CAPACITY
    # =====================================================

    pumping_m3_s = None
    pumping_m3_h = None
    qv_1_h = None
    turnover_time_min = None

    if nq is not None:

        pumping_m3_s = (
            nq
            * N
            * D**3
            * nimp
        )

        pumping_m3_h = (
            pumping_m3_s
            * 3600.0
        )

        if volume_m3 > 0:

            qv_1_h = (
                pumping_m3_h
                / volume_m3
            )

            if qv_1_h > 0:

                turnover_time_min = (
                    60.0
                    / qv_1_h
                )

    # =====================================================
    # MIXING REGIME
    # =====================================================

    if reynolds < 10:

        regime = "Laminar"

    elif reynolds < 10000:

        regime = "Transitional"

    else:

        regime = "Turbulent"

    # =====================================================
    # VOLUME SCALE-UP RELATED VALUES
    # =====================================================

    specific_power_kw_m3 = None

    if power_kw is not None and volume_m3 > 0:

        specific_power_kw_m3 = (
            power_kw
            / volume_m3
        )

    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {

        # -------------------------------------------------
        # BASIC MIXING PARAMETERS
        # -------------------------------------------------

        "tip_speed": tip_speed,

        "Re": reynolds,

        "reynolds_number": reynolds,

        "Fr": froude,

        "froude_number": froude,

        # -------------------------------------------------
        # AGITATOR DATA
        # -------------------------------------------------

        "Np": np_num,

        "Nq": nq,

        "agitator": agitator,

        "number_impellers": nimp,

        "impeller_diameter_m": D,

        # -------------------------------------------------
        # POWER
        # -------------------------------------------------

        "power_w": power_w,

        "power_kw": power_kw,

        "power_volume": power_volume,

        "power_per_volume": power_volume,

        "specific_power_kw_m3": specific_power_kw_m3,

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

        # Compatibility with scale-up module
        "pumping_per_volume": qv_1_h,

        "turnover_time_min": turnover_time_min,

        # -------------------------------------------------
        # GEOMETRY
        # -------------------------------------------------

        "D_T": D_T,

        "H_T": H_T,

        "clearance_T": clearance_T,

        # -------------------------------------------------
        # MIXING REGIME
        # -------------------------------------------------

        "mixing_regime": regime,

        # -------------------------------------------------
        # PROCESS PROPERTIES
        # -------------------------------------------------

        "viscosity_pa_s": mu,

        "density_kg_m3": rho,

        "surface_tension_n_m": surface_tension_n_m,

    }
