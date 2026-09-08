"""
Core reactor mixing calculations.

Units:
- Diameter: m
- Volume: m3
- Density: kg/m3
- Viscosity: Pa.s
- RPM: rpm
- Power: W / kW
- Flow: m3/h
"""

import math


G = 9.81


def _safe(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def calculate_agitator(stage):
    """
    Calculate one independent agitator stage.
    """

    rho = _safe(
        stage.get("density_kg_m3"),
        1000.0,
    )

    mu = max(
        _safe(
            stage.get("viscosity_pa_s"),
            0.001,
        ),
        1e-9,
    )

    rpm = max(
        _safe(stage.get("rpm"), 0.0),
        0.0,
    )

    D = max(
        _safe(
            stage.get("impeller_diameter_m"),
            0.1,
        ),
        0.001,
    )

    n_imp = max(
        int(
            stage.get(
                "number_impellers",
                1,
            )
        ),
        1,
    )

    N = rpm / 60.0

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

    tip_speed = (
        math.pi
        * D
        * N
    )

    Np = stage.get("Np")

    Nq = stage.get("Nq")

    power_w = None
    power_kw = None

    if Np is not None:

        power_w = (
            float(Np)
            * rho
            * N**3
            * D**5
            * n_imp
        )

        power_kw = power_w / 1000.0

    Q_m3_h = None

    if Nq is not None:

        Q_m3_s = (
            float(Nq)
            * N
            * D**3
            * n_imp
        )

        Q_m3_h = (
            Q_m3_s
            * 3600.0
        )

    torque = None

    if power_w is not None and N > 0:

        torque = (
            power_w
            / (
                2.0
                * math.pi
                * N
            )
        )

    D_T = (
        D
        / max(
            _safe(
                stage.get("tank_diameter_m"),
                D,
            ),
            1e-9,
        )
    )

    return {
        **stage,

        "N_s_inv": N,

        "Re": Re,
        "reynolds_number": Re,

        "Fr": Fr,
        "froude_number": Fr,

        "tip_speed_m_s": tip_speed,
        "tip_speed": tip_speed,

        "power_w": power_w,
        "power_kw": power_kw,

        "torque_Nm": torque,
        "torque_nm": torque,

        "Q_m3_h": Q_m3_h,
        "pumping_m3_h": Q_m3_h,

        "D_T": D_T,

        "mixing_regime": (
            "Laminar"
            if Re < 10
            else
            "Transitional"
            if Re < 10000
            else
            "Turbulent"
        ),
    }


def calculate_train(
    stages,
    working_volume,
):
    """
    Calculate all independent agitator stages.
    """

    results = []

    for stage in stages:

        result = calculate_agitator(
            stage
        )

        results.append(result)

    total_power_w = sum(
        (
            x["power_w"]
            for x in results
            if x["power_w"] is not None
        )
    )

    total_Q_m3_h = sum(
        (
            x["Q_m3_h"]
            for x in results
            if x["Q_m3_h"] is not None
        )
    )

    volume = max(
        float(working_volume),
        1e-9,
    )

    power_per_volume = (
        total_power_w
        / volume
    )

    Q_per_volume_h = (
        total_Q_m3_h
        / volume
    )

    # Convert Q/V from h^-1 to s^-1.
    Q_per_volume_s = (
        Q_per_volume_h
        / 3600.0
    )

    turnover_time_min = None

    if total_Q_m3_h > 0:

        turnover_time_min = (
            volume
            / total_Q_m3_h
            * 60.0
        )

    train = {
        "total_power_w": total_power_w,

        "total_power_kw":
            total_power_w / 1000.0,

        "power_per_volume_W_m3":
            power_per_volume,

        "total_Q_m3_h":
            total_Q_m3_h,

        "Q_per_volume_h":
            Q_per_volume_h,

        "Q_per_volume_1_s":
            Q_per_volume_s,

        "turnover_time_min":
            turnover_time_min,

        "number_of_stages":
            len(results),
    }

    return results, train


def zwietering_njs(
    result,
    solids_wt_percent,
    particle_diameter_m,
    solid_density,
    liquid_density,
    S=5.0,
):
    """
    Screening Njs estimate.

    This is NOT a universal correlation.

    The result should be treated as an engineering
    screening estimate and validated against actual
    suspension data.

    Returns:
        Njs in s^-1
    """

    D = max(
        float(
            result.get(
                "impeller_diameter_m",
                0.1,
            )
        ),
        1e-6,
    )

    S = max(
        float(S),
        0.01,
    )

    dp = max(
        float(particle_diameter_m),
        1e-7,
    )

    rho_s = max(
        float(solid_density),
        1.0,
    )

    rho_l = max(
        float(liquid_density),
        1.0,
    )

    X = max(
        float(solids_wt_percent) / 100.0,
        0.0,
    )

    delta_rho_ratio = max(
        (rho_s - rho_l) / rho_l,
        0.0,
    )

    # Screening form.
    Njs = (
        S
        * (
            G
            * dp
            * delta_rho_ratio
        ) ** 0.45
        / D**0.85
        * (1.0 + 2.0 * X)
    )

    return max(
        Njs,
        0.0,
    )


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
    Backward-compatible single-stage calculation.
    """

    Np = None
    Nq = None

    flow_map = {
        "Rushton Turbine": (5.0, 0.75),
        "Pitched Blade Turbine": (1.5, 0.75),
        "Hydrofoil": (0.35, 0.70),
        "Marine Propeller": (0.50, 0.60),
        "Anchor": (2.0, 0.30),
        "Helical Ribbon": (1.0, 0.25),
        "RCI": (None, None),
    }

    if agitator in flow_map:

        Np, Nq = flow_map[agitator]

    result = calculate_agitator(
        {
            "agitator": agitator,
            "Np": Np,
            "Nq": Nq,
            "impeller_diameter_m":
                impeller_diameter_m,
            "rpm": rpm,
            "number_impellers":
                number_impellers,
            "elevation_m":
                0.5 * liquid_height_m,
            "clearance_m":
                impeller_clearance_m,
            "density_kg_m3":
                density_kg_m3,
            "viscosity_pa_s":
                viscosity_pa_s,
            "tank_diameter_m":
                tank_diameter_m,
        }
    )

    result["H_T"] = (
        liquid_height_m
        / tank_diameter_m
        if tank_diameter_m > 0
        else 0.0
    )

    result["clearance_T"] = (
        impeller_clearance_m
        / tank_diameter_m
        if impeller_clearance_m is not None
        and tank_diameter_m > 0
        else None
    )

    result["surface_tension_n_m"] = (
        surface_tension_n_m
    )

    result["volume_m3"] = volume_m3

    result["power_volume"] = (
        result["power_w"] / volume_m3
        if result["power_w"] is not None
        and volume_m3 > 0
        else None
    )

    result["power_per_volume"] = (
        result["power_volume"]
    )

    result["qv_1_h"] = (
        result["Q_m3_h"] / volume_m3
        if result["Q_m3_h"] is not None
        and volume_m3 > 0
        else None
    )

    return result
