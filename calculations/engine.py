"""
Core reactor agitation calculations.

Internal units:
    D       = m
    N       = rev/s
    rho     = kg/m3
    mu      = Pa.s
    power   = W
    Q       = m3/s
    V       = m3
"""

import math


G = 9.80665
KW_TO_HP = 1.34102209


def safe(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def flow_regime(Re):
    if Re < 10:
        return "Laminar"

    if Re < 10000:
        return "Transitional"

    return "Turbulent"


def calculate_reynolds(
    density_kg_m3,
    rotational_speed_rps,
    diameter_m,
    viscosity_pa_s,
):
    rho = max(safe(density_kg_m3), 1e-12)
    N = max(safe(rotational_speed_rps), 0.0)
    D = max(safe(diameter_m), 1e-12)
    mu = max(safe(viscosity_pa_s), 1e-12)

    return rho * N * D**2 / mu


def calculate_power(
    Np,
    density_kg_m3,
    rotational_speed_rps,
    diameter_m,
    number_impellers=1,
):
    if Np is None:
        return None

    rho = max(safe(density_kg_m3), 0.0)
    N = max(safe(rotational_speed_rps), 0.0)
    D = max(safe(diameter_m), 0.0)
    ni = max(int(number_impellers), 1)

    return (
        float(Np)
        * rho
        * N**3
        * D**5
        * ni
    )


def calculate_pumping(
    Nq,
    rotational_speed_rps,
    diameter_m,
    number_impellers=1,
):
    if Nq is None:
        return None

    N = max(safe(rotational_speed_rps), 0.0)
    D = max(safe(diameter_m), 0.0)
    ni = max(int(number_impellers), 1)

    return (
        float(Nq)
        * N
        * D**3
        * ni
    )


def calculate_torque(power_w, rotational_speed_rps):
    if power_w is None:
        return None

    if rotational_speed_rps <= 0:
        return None

    return power_w / (
        2.0 * math.pi * rotational_speed_rps
    )


def calculate_tip_speed(diameter_m, rotational_speed_rps):
    return (
        math.pi
        * max(safe(diameter_m), 0.0)
        * max(safe(rotational_speed_rps), 0.0)
    )


def calculate_froude(diameter_m, rotational_speed_rps):
    return (
        max(safe(rotational_speed_rps), 0.0) ** 2
        * max(safe(diameter_m), 0.0)
        / G
    )


def zwietering_njs(
    stage,
    solids_wt_percent,
    particle_diameter_m,
    solid_density_kg_m3,
    liquid_density_kg_m3,
    S=4.5,
):
    """
    Zwietering-type minimum suspension speed.

    IMPORTANT:
    This is a screening correlation.

    X is converted from solids wt% to solids/liquid mass ratio:
        X = wt% / (100 - wt%)

    Returned value:
        RPM

    The S factor must be appropriate for the impeller/system.
    """

    rho_l = max(
        safe(liquid_density_kg_m3),
        1e-12,
    )

    rho_s = max(
        safe(solid_density_kg_m3),
        rho_l,
    )

    mu = max(
        safe(stage.get("viscosity_pa_s", 0.001)),
        1e-12,
    )

    nu = mu / rho_l

    dp = max(
        safe(particle_diameter_m),
        1e-9,
    )

    D = max(
        safe(stage.get("impeller_diameter_m", 0.1)),
        1e-9,
    )

    wt = min(
        max(safe(solids_wt_percent), 0.0),
        99.0,
    )

    if wt <= 0:
        return None

    X = wt / (100.0 - wt)

    density_ratio = max(
        (rho_s - rho_l) / rho_l,
        0.0,
    )

    if density_ratio <= 0:
        return None

    njs_rps = (
        float(S)
        * nu**0.1
        * (
            G
            * density_ratio
        )**0.45
        * X**0.13
        * dp**0.2
        * D**-0.85
    )

    return max(njs_rps * 60.0, 0.0)


def calculate_agitator_stage(stage):
    density = max(
        safe(stage.get("density_kg_m3", 1000.0)),
        1e-12,
    )

    viscosity = max(
        safe(stage.get("viscosity_pa_s", 0.001)),
        1e-12,
    )

    D = max(
        safe(stage.get("impeller_diameter_m", 0.1)),
        1e-9,
    )

    rpm = max(
        safe(stage.get("rpm", 0.0)),
        0.0,
    )

    N = rpm / 60.0

    n_imp = max(
        int(stage.get("number_impellers", 1)),
        1,
    )

    tank_D = max(
        safe(stage.get("tank_diameter_m", 1.0)),
        1e-9,
    )

    liquid_height = max(
        safe(stage.get("liquid_height_m", 0.0)),
        0.0,
    )

    working_volume = max(
        safe(stage.get("working_volume_m3", 0.0)),
        1e-12,
    )

    Np = stage.get("Np")
    Nq = stage.get("Nq")

    Re = calculate_reynolds(
        density,
        N,
        D,
        viscosity,
    )

    power_w = calculate_power(
        Np,
        density,
        N,
        D,
        n_imp,
    )

    q_m3_s = calculate_pumping(
        Nq,
        N,
        D,
        n_imp,
    )

    power_kw = (
        power_w / 1000.0
        if power_w is not None
        else None
    )

    power_hp = (
        power_w / 745.699872
        if power_w is not None
        else None
    )

    q_m3_h = (
        q_m3_s * 3600.0
        if q_m3_s is not None
        else None
    )

    pv_kw_m3 = (
        power_kw / working_volume
        if power_kw is not None
        else None
    )

    qv_s_inv = (
        q_m3_s / working_volume
        if q_m3_s is not None
        else None
    )

    turnover_min = (
        1.0 / qv_s_inv / 60.0
        if qv_s_inv and qv_s_inv > 0
        else None
    )

    torque = calculate_torque(
        power_w,
        N,
    )

    tip_speed = calculate_tip_speed(
        D,
        N,
    )

    Fr = calculate_froude(
        D,
        N,
    )

    D_T = D / tank_D

    C = safe(
        stage.get("clearance_m", 0.0)
    )

    C_T = C / tank_D

    H_T = (
        liquid_height / tank_D
        if tank_D > 0
        else None
    )

    return {
        **stage,

        "rpm": rpm,
        "N_rps": N,

        "Re": Re,
        "reynolds_number": Re,
        "mixing_regime": flow_regime(Re),

        "Fr": Fr,
        "froude_number": Fr,

        "D_T": D_T,
        "H_T": H_T,
        "clearance_T": C_T,

        "tip_speed_m_s": tip_speed,
        "tip_speed": tip_speed,

        "power_w": power_w,
        "power_kw": power_kw,
        "power_hp": power_hp,
        "power_per_volume_kw_m3": pv_kw_m3,
        "power_volume": pv_kw_m3,
        "power_per_volume": pv_kw_m3,

        "Q_m3_s": q_m3_s,
        "Q_m3_h": q_m3_h,
        "pumping_m3_h": q_m3_h,

        "Q_per_volume_s_inv": qv_s_inv,
        "Q_per_volume_1_s": qv_s_inv,

        "turnover_time_min": turnover_min,

        "torque_Nm": torque,
        "torque_nm": torque,

        "njs_rpm": stage.get("njs_rpm"),
        "Njs_RPM": stage.get("njs_rpm"),
        "Njs_s_inv": (
            stage.get("njs_rpm", 0.0) / 60.0
            if stage.get("njs_rpm")
            else None
        ),
    }


def calculate_train(stages, working_volume_m3):
    results = []

    for stage in stages:
        results.append(
            calculate_agitator_stage(stage)
        )

    total_power_kw = sum(
        x["power_kw"] or 0.0
        for x in results
    )

    total_power_w = total_power_kw * 1000.0

    total_q_m3_h = sum(
        x["Q_m3_h"] or 0.0
        for x in results
    )

    total_q_m3_s = total_q_m3_h / 3600.0

    V = max(
        safe(working_volume_m3),
        1e-12,
    )

    pv_kw_m3 = total_power_kw / V

    pv_w_m3 = total_power_w / V

    qv_s_inv = total_q_m3_s / V

    qv_h_inv = total_q_m3_h / V

    turnover_min = (
        1.0 / qv_s_inv / 60.0
        if qv_s_inv > 0
        else None
    )

    total_torque = sum(
        x["torque_Nm"] or 0.0
        for x in results
    )

    njs_values = [
        x["njs_rpm"]
        for x in results
        if x.get("njs_rpm") is not None
    ]

    system_njs = (
        max(njs_values)
        if njs_values
        else None
    )

    average_tip_speed = (
        sum(
            x["tip_speed_m_s"]
            for x in results
        )
        / len(results)
        if results
        else None
    )

    max_re = (
        max(x["Re"] for x in results)
        if results
        else None
    )

    return results, {
        "total_power_w": total_power_w,
        "total_power_kw": total_power_kw,
        "total_power_hp": (
            total_power_w / 745.699872
        ),

        "total_Q_m3_s": total_q_m3_s,
        "total_Q_m3_h": total_q_m3_h,

        "power_per_volume_W_m3": pv_w_m3,
        "P_per_V_kW_m3": pv_kw_m3,

        "Q_per_volume_1_s": qv_s_inv,
        "Q_per_volume_1_h": qv_h_inv,

        "turnover_time_min": turnover_min,

        "total_torque_Nm": total_torque,

        "system_Njs_rpm": system_njs,
        "system_Njs_s_inv": (
            system_njs / 60.0
            if system_njs
            else None
        ),

        "average_tip_speed_m_s": average_tip_speed,
        "maximum_reynolds": max_re,
    }


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
    from libraries.agitator_geometry import AGITATORS

    spec = AGITATORS.get(
        agitator,
        {},
    )

    stage = {
        "agitator": agitator,
        "Np": spec.get("Np"),
        "Nq": spec.get("Nq"),
        "impeller_diameter_m": impeller_diameter_m,
        "rpm": rpm,
        "number_impellers": number_impellers,
        "density_kg_m3": density_kg_m3,
        "viscosity_pa_s": viscosity_pa_s,
        "tank_diameter_m": tank_diameter_m,
        "liquid_height_m": liquid_height_m,
        "working_volume_m3": volume_m3,
        "clearance_m": (
            impeller_clearance_m
            if impeller_clearance_m is not None
            else 0.0
        ),
    }

    result = calculate_agitator_stage(stage)

    result["volume_m3"] = volume_m3
    result["surface_tension_n_m"] = (
        surface_tension_n_m
    )

    return result
