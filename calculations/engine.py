"""
Reactor Scale-Up Engineering Studio
------------------------------------
Core reactor agitation calculations.

Engineering basis:
    Re = rho * N * D^2 / mu
    P = Np * rho * N^3 * D^5 * n
    Q = Nq * N * D^3 * n
    P/V = P / V
    Q/V = Q / V
    Tip speed = pi * D * N
    Torque = P / (2*pi*N)
    Fr = N^2 * D / g

Njs:
    Zwietering-type screening correlation for solid suspension.
    This is a screening calculation and must be validated against
    process-specific experimental/vendor data.
"""

import math
from typing import Dict, List, Optional, Tuple


G = 9.81


# ============================================================
# BASIC UTILITIES
# ============================================================

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safe division."""
    if abs(b) < 1e-15:
        return default
    return a / b


# ============================================================
# SINGLE AGITATOR CALCULATION
# ============================================================

def calculate_agitator(
    agitator: str,
    np_value: Optional[float],
    nq_value: Optional[float],
    impeller_diameter_m: float,
    rpm: float,
    number_impellers: int,
    volume_m3: float,
    density_kg_m3: float,
    viscosity_pa_s: float,
    elevation_m: float = 0.0,
    clearance_m: float = 0.0,
) -> Dict:

    D = max(float(impeller_diameter_m), 1e-6)
    rpm = max(float(rpm), 0.0)
    nimp = max(int(number_impellers), 1)
    V = max(float(volume_m3), 1e-9)
    rho = max(float(density_kg_m3), 1e-9)
    mu = max(float(viscosity_pa_s), 1e-9)

    # RPM -> rev/s
    N = rpm / 60.0

    # --------------------------------------------------------
    # Dimensionless numbers
    # --------------------------------------------------------

    Re = safe_divide(
        rho * N * D**2,
        mu,
        0.0,
    )

    Fr = safe_divide(
        N**2 * D,
        G,
        0.0,
    )

    tip_speed = math.pi * D * N

    # --------------------------------------------------------
    # Power
    # --------------------------------------------------------

    if np_value is not None and N > 0:

        power_w = (
            float(np_value)
            * rho
            * N**3
            * D**5
            * nimp
        )

    else:
        power_w = 0.0

    power_kw = power_w / 1000.0

    power_per_volume = safe_divide(
        power_w,
        V,
        0.0,
    )

    # --------------------------------------------------------
    # Pumping
    # --------------------------------------------------------

    if nq_value is not None and N > 0:

        Q_m3_s = (
            float(nq_value)
            * N
            * D**3
            * nimp
        )

    else:
        Q_m3_s = 0.0

    Q_m3_h = Q_m3_s * 3600.0

    Q_per_volume_1_s = safe_divide(
        Q_m3_s,
        V,
        0.0,
    )

    if Q_m3_s > 0:
        turnover_time_s = V / Q_m3_s
        turnover_time_min = turnover_time_s / 60.0
    else:
        turnover_time_min = None

    # --------------------------------------------------------
    # Torque
    # --------------------------------------------------------

    if N > 0:
        torque_Nm = power_w / (2.0 * math.pi * N)
    else:
        torque_Nm = 0.0

    # --------------------------------------------------------
    # Geometry ratios
    # --------------------------------------------------------

    clearance_ratio = safe_divide(
        clearance_m,
        D,
        0.0,
    )

    # --------------------------------------------------------
    # Mixing regime
    # --------------------------------------------------------

    if Re < 10:
        mixing_regime = "Laminar"

    elif Re < 10000:
        mixing_regime = "Transitional"

    else:
        mixing_regime = "Turbulent"

    return {
        "agitator": agitator,

        "Np": np_value,
        "Nq": nq_value,

        "impeller_diameter_m": D,
        "rpm": rpm,
        "N_s_inv": N,

        "number_impellers": nimp,

        "elevation_m": elevation_m,
        "clearance_m": clearance_m,

        "Re": Re,
        "reynolds_number": Re,

        "Fr": Fr,
        "froude_number": Fr,

        "tip_speed_m_s": tip_speed,
        "tip_speed": tip_speed,

        "power_w": power_w,
        "power_kw": power_kw,

        "power_per_volume_W_m3": power_per_volume,
        "power_per_volume": power_per_volume,

        "Q_m3_s": Q_m3_s,
        "Q_m3_h": Q_m3_h,

        "Q_per_volume_1_s": Q_per_volume_1_s,

        "turnover_time_min": turnover_time_min,

        "torque_Nm": torque_Nm,
        "torque_nm": torque_Nm,

        "clearance_ratio": clearance_ratio,

        "mixing_regime": mixing_regime,

        "density_kg_m3": rho,
        "viscosity_pa_s": mu,
        "volume_m3": V,
    }


# ============================================================
# AGITATOR TRAIN
# ============================================================

def calculate_train(
    stages: List[Dict],
    volume_m3: float,
) -> Tuple[List[Dict], Dict]:
    """
    Calculate all independent agitator stages.

    Each stage can have:
        - different agitator
        - different diameter
        - different RPM
        - different number of impellers
        - different clearance
        - different elevation
        - different Np/Nq

    Total system quantities:
        Total Power = sum(Pi)
        Total Q = sum(Qi)
        P/V = Total Power / V
        Q/V = Total Q / V

    For Njs:
        conservative system Njs = MAX(stage Njs)
    """

    V = max(float(volume_m3), 1e-9)

    results = []

    total_power_w = 0.0
    total_Q_m3_s = 0.0

    for stage in stages:

        result = calculate_agitator(
            agitator=stage.get("agitator", "Unknown"),

            np_value=stage.get("Np"),

            nq_value=stage.get("Nq"),

            impeller_diameter_m=stage.get(
                "impeller_diameter_m",
                0.5,
            ),

            rpm=stage.get(
                "rpm",
                100.0,
            ),

            number_impellers=stage.get(
                "number_impellers",
                1,
            ),

            volume_m3=V,

            density_kg_m3=stage.get(
                "density_kg_m3",
                1000.0,
            ),

            viscosity_pa_s=stage.get(
                "viscosity_pa_s",
                0.001,
            ),

            elevation_m=stage.get(
                "elevation_m",
                0.0,
            ),

            clearance_m=stage.get(
                "clearance_m",
                0.0,
            ),
        )

        results.append(result)

        total_power_w += result["power_w"]
        total_Q_m3_s += result["Q_m3_s"]

    # --------------------------------------------------------
    # Train totals
    # --------------------------------------------------------

    total_power_kw = total_power_w / 1000.0

    power_per_volume_W_m3 = safe_divide(
        total_power_w,
        V,
        0.0,
    )

    total_Q_m3_h = total_Q_m3_s * 3600.0

    Q_per_volume_1_s = safe_divide(
        total_Q_m3_s,
        V,
        0.0,
    )

    if total_Q_m3_s > 0:

        turnover_time_min = (
            V / total_Q_m3_s / 60.0
        )

    else:

        turnover_time_min = None

    # --------------------------------------------------------
    # Total torque
    # --------------------------------------------------------

    total_torque_Nm = sum(
        r["torque_Nm"]
        for r in results
    )

    # --------------------------------------------------------
    # Maximum Njs
    # --------------------------------------------------------

    njs_values = [
        r.get("Njs_s_inv")
        for r in results
        if r.get("Njs_s_inv") is not None
    ]

    system_njs_s_inv = (
        max(njs_values)
        if njs_values
        else None
    )

    train = {
        "number_of_stages": len(results),

        "total_power_w": total_power_w,
        "total_power_kw": total_power_kw,

        "power_per_volume_W_m3":
            power_per_volume_W_m3,

        "total_Q_m3_s": total_Q_m3_s,
        "total_Q_m3_h": total_Q_m3_h,

        "Q_per_volume_1_s":
            Q_per_volume_1_s,

        "turnover_time_min":
            turnover_time_min,

        "total_torque_Nm":
            total_torque_Nm,

        "system_Njs_s_inv":
            system_njs_s_inv,
    }

    return results, train


# ============================================================
# ZWIETERING Njs SCREENING
# ============================================================

def zwietering_njs(
    stage: Dict,
    solids_wt_pct: float,
    particle_diameter_m: float,
    solid_density_kg_m3: float,
    liquid_density_kg_m3: float,
    S_constant: float = 5.0,
) -> Optional[float]:
    """
    Zwietering-type minimum suspension speed screening.

    General form:

        Njs =
        S * nu^0.1 *
        [g * (rho_s-rho_l)/rho_l]^0.45 *
        X^0.13 *
        d_p^-0.2 *
        D^-0.85

    This implementation is intended as an engineering screening
    calculation.

    IMPORTANT:
    The Zwietering correlation contains system-specific constants
    and conventions. Final Njs should be validated against actual
    slurry data and/or vendor correlation for the selected impeller.
    """

    D = float(
        stage.get(
            "impeller_diameter_m",
            0.0,
        )
    )

    if D <= 0:
        return None

    rho_l = float(liquid_density_kg_m3)
    rho_s = float(solid_density_kg_m3)

    dp = float(particle_diameter_m)

    X = float(solids_wt_pct) / 100.0

    if rho_l <= 0 or rho_s <= rho_l:
        return None

    if dp <= 0 or X <= 0:
        return None

    mu = float(
        stage.get(
            "viscosity_pa_s",
            0.001,
        )
    )

    nu = mu / rho_l

    # Zwietering-style screening correlation
    delta_rho_ratio = (
        (rho_s - rho_l) / rho_l
    )

    Njs = (
        float(S_constant)
        * (nu ** 0.10)
        * (G * delta_rho_ratio) ** 0.45
        * (X ** 0.13)
        * (dp ** -0.20)
        * (D ** -0.85)
    )

    return max(Njs, 0.0)


# ============================================================
# APPLY Njs TO TRAIN
# ============================================================

def calculate_njs_for_train(
    results: List[Dict],
    solids_wt_pct: float,
    particle_diameter_m: float,
    solid_density_kg_m3: float,
    liquid_density_kg_m3: float,
    S_constant: float = 5.0,
) -> List[Dict]:

    for stage in results:

        njs = zwietering_njs(
            stage,
            solids_wt_pct,
            particle_diameter_m,
            solid_density_kg_m3,
            liquid_density_kg_m3,
            S_constant,
        )

        stage["Njs_s_inv"] = njs

        if njs and njs > 0:

            stage["N_Njs"] = safe_divide(
                stage["N_s_inv"],
                njs,
                0.0,
            )

            stage["N_over_Njs"] = stage["N_Njs"]

        else:

            stage["N_Njs"] = None
            stage["N_over_Njs"] = None

    return results


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

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
    Backward-compatible single-reactor calculation.

    Retained so older modules/app versions do not break.
    """

    np_value = None
    nq_value = None

    try:
        from libraries.agitator_geometry import AGITATORS

        spec = AGITATORS.get(agitator, {})

        np_value = spec.get("Np")
        nq_value = spec.get("Nq")

    except Exception:
        pass

    result = calculate_agitator(
        agitator=agitator,
        np_value=np_value,
        nq_value=nq_value,
        impeller_diameter_m=impeller_diameter_m,
        rpm=rpm,
        number_impellers=number_impellers,
        volume_m3=volume_m3,
        density_kg_m3=density_kg_m3,
        viscosity_pa_s=viscosity_pa_s,
        clearance_m=impeller_clearance_m or 0.0,
    )

    result["liquid_height_m"] = liquid_height_m
    result["tank_diameter_m"] = tank_diameter_m
    result["surface_tension_n_m"] = surface_tension_n_m

    result["D_T"] = safe_divide(
        impeller_diameter_m,
        tank_diameter_m,
        0.0,
    )

    result["H_T"] = safe_divide(
        liquid_height_m,
        tank_diameter_m,
        0.0,
    )

    return result
