import math

from libraries.agitator_geometry import AGITATORS


G = 9.81


def _positive(value, name):

    try:
        value = float(value)
    except (TypeError, ValueError):

        raise ValueError(
            f"{name} must be numeric."
        )

    if not math.isfinite(value) or value <= 0:

        raise ValueError(
            f"{name} must be greater than zero."
        )

    return value


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

    result = {
        "gas_flow_m3_h": float(
            gas_flow_m3_h or 0.0
        ),
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

    Qg_h = float(
        gas_flow_m3_h or 0.0
    )

    if Qg_h <= 0:
        return result

    D = _positive(
        tank_diameter_m,
        "Tank diameter",
    )

    H = _positive(
        liquid_height_m,
        "Liquid height",
    )

    rho = _positive(
        liquid_density_kg_m3,
        "Liquid density",
    )

    mu = _positive(
        liquid_viscosity_pa_s,
        "Liquid viscosity",
    )

    diffusivity = _positive(
        diffusivity_m2_s,
        "Diffusivity",
    )

    bubble_diameter_m = (
        _positive(
            bubble_diameter_mm,
            "Bubble diameter",
        )
        / 1000.0
    )

    epsilon = max(
        0.001,
        min(
            0.50,
            float(gas_holdup_fraction),
        ),
    )

    area = (
        math.pi
        * D**2
        / 4.0
    )

    Qg_s = Qg_h / 3600.0

    superficial_velocity = (
        Qg_s / area
    )

    # Screening approximation.
    bubble_velocity = (
        0.71
        * math.sqrt(
            G
            * bubble_diameter_m
        )
    )

    bubble_velocity = max(
        0.01,
        bubble_velocity,
    )

    residence_time_s = (
        H / bubble_velocity
    )

    bubble_reynolds = (
        rho
        * bubble_velocity
        * bubble_diameter_m
        / mu
    )

    schmidt = (
        mu
        / (
            rho
            * diffusivity
        )
    )

    sherwood = (
        2.0
        + 0.6
        * math.sqrt(
            max(
                bubble_reynolds,
                0.0,
            )
        )
        * schmidt ** (
            1.0 / 3.0
        )
    )

    kL = (
        sherwood
        * diffusivity
        / bubble_diameter_m
    )

    interfacial_area = (
        6.0
        * epsilon
        / bubble_diameter_m
    )

    kLa_s = (
        kL
        * interfacial_area
    )

    result.update(
        {
            "gas_flow_m3_h": Qg_h,
            "gas_superficial_velocity_m_s":
                superficial_velocity,
            "gas_holdup_fraction":
                epsilon,
            "bubble_diameter_m":
                bubble_diameter_m,
            "bubble_rise_velocity_m_s":
                bubble_velocity,
            "bubble_residence_time_s":
                residence_time_s,
            "bubble_residence_time_min":
                residence_time_s / 60.0,
            "bubble_reynolds":
                bubble_reynolds,
            "schmidt_number":
                schmidt,
            "sherwood_number":
                sherwood,
            "kL_m_s":
                kL,
            "interfacial_area_m2_m3":
                interfacial_area,
            "kLa_1_s":
                kLa_s,
            "kLa_1_h":
                kLa_s * 3600.0,
            "gas_liquid_status":
                "SCREENING ESTIMATE",
        }
    )

    return result


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
    gas_flow_m3_h=0.0,
    gas_density_kg_m3=1.2,
    gas_viscosity_pa_s=1.8e-5,
    gas_diffusivity_m2_s=2.0e-9,
    bubble_diameter_mm=3.0,
    gas_holdup_fraction=0.05,
):

    V = _positive(
        volume_m3,
        "Working volume",
    )

    T = _positive(
        tank_diameter_m,
        "Tank diameter",
    )

    H = _positive(
        liquid_height_m,
        "Liquid height",
    )

    rho = _positive(
        density_kg_m3,
        "Liquid density",
    )

    mu = _positive(
        viscosity_pa_s,
        "Liquid viscosity",
    )

    sigma = _positive(
        surface_tension_n_m,
        "Surface tension",
    )

    rpm = _positive(
        rpm,
        "RPM",
    )

    D = _positive(
        impeller_diameter_m,
        "Impeller diameter",
    )

    nimp = int(
        number_impellers
    )

    if nimp < 1:
        raise ValueError(
            "Number of impellers must be at least 1."
        )

    if D >= T:
        raise ValueError(
            "Impeller diameter must be smaller than tank diameter."
        )

    if agitator not in AGITATORS:

        raise ValueError(
            f"Agitator '{agitator}' "
            "is not available in the agitator database."
        )

    agitator_data = AGITATORS[
        agitator
    ]

    Np = agitator_data.get(
        "np"
    )

    Nq = agitator_data.get(
        "nq"
    )

    N = rpm / 60.0

    D_T = D / T
    H_T = H / T

    tip_speed = (
        math.pi
        * D
        * N
    )

    Re = (
        rho
        * N
        * D**2
        / mu
    )

    Fr = (
        N**2
        * D
        / G
    )

    power_w = None
    power_kw = None
    power_volume_w_m3 = None
    power_volume_kw_m3 = None
    torque_nm = None

    if Np is not None:

        Np = float(Np)

        power_w = (
            Np
            * rho
            * N**3
            * D**5
            * nimp
        )

        power_kw = (
            power_w / 1000.0
        )

        power_volume_w_m3 = (
            power_w / V
        )

        power_volume_kw_m3 = (
            power_volume_w_m3
            / 1000.0
        )

        torque_nm = (
            power_w
            / (
                2.0
                * math.pi
                * N
            )
        )

    pumping_m3_s = None
    pumping_m3_h = None
    qv_1_h = None
    turnover_time_min = None

    if Nq is not None:

        Nq = float(Nq)

        pumping_m3_s = (
            Nq
            * N
            * D**3
            * nimp
        )

        pumping_m3_h = (
            pumping_m3_s
            * 3600.0
        )

        qv_1_h = (
            pumping_m3_h
            / V
        )

        if qv_1_h > 0:

            turnover_time_min = (
                60.0
                / qv_1_h
            )

    if Re < 10:
        regime = "Laminar"

    elif Re < 10000:
        regime = "Transitional"

    else:
        regime = "Turbulent"

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

    return {
        "volume_m3": V,
        "working_volume_m3": V,
        "tank_diameter_m": T,
        "liquid_height_m": H,
        "density_kg_m3": rho,
        "viscosity_pa_s": mu,
        "surface_tension_n_m": sigma,
        "rpm": rpm,
        "number_impellers": nimp,
        "agitator": agitator,
        "impeller_diameter_m": D,
        "impeller_clearance_m":
            impeller_clearance_m,
        "Np": Np,
        "Nq": Nq,
        "D_T": D_T,
        "H_T": H_T,
        "tip_speed": tip_speed,
        "Re": Re,
        "reynolds_number": Re,
        "Fr": Fr,
        "froude_number": Fr,
        "mixing_regime": regime,
        "power_w": power_w,
        "power_kw": power_kw,
        "power_volume_w_m3":
            power_volume_w_m3,
        "power_volume_kw_m3":
            power_volume_kw_m3,
        "specific_power_kw_m3":
            power_volume_kw_m3,
        "torque_nm": torque_nm,
        "pumping_m3_s":
            pumping_m3_s,
        "pumping_m3_h":
            pumping_m3_h,
        "qv_1_h":
            qv_1_h,
        "pumping_per_volume":
            qv_1_h,
        "turnover_time_min":
            turnover_time_min,
        **gas_results,
    }
