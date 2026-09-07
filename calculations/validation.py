def validate_reactor(
    volume_m3,
    vessel_volume_m3,
    tank_diameter_m,
    straight_height_m,
    liquid_height_m,
    impeller_diameter_m,
    number_impellers,
    number_baffles,
    rpm,
    agitator,
    density_kg_m3,
    viscosity_pa_s,
    power_volume_kw_m3=None,
    gas_flow_m3_h=0.0,
    kLa_1_h=None,
):

    checks = []

    # =====================================================
    # BASIC GEOMETRY
    # =====================================================

    if vessel_volume_m3 <= 0:

        checks.append({
            "severity": "FAIL",
            "message":
                "Calculated vessel volume is invalid.",
        })

    elif volume_m3 <= vessel_volume_m3:

        checks.append({
            "severity": "PASS",
            "message":
                "Working volume is within vessel capacity.",
        })

    else:

        checks.append({
            "severity": "FAIL",
            "message":
                "Working volume exceeds vessel capacity.",
        })

    # =====================================================
    # FILL
    # =====================================================

    fill = (
        volume_m3 /
        vessel_volume_m3 *
        100.0
        if vessel_volume_m3 > 0
        else 0
    )

    if 40 <= fill <= 80:

        checks.append({
            "severity": "PASS",
            "message":
                f"Operating fill = {fill:.1f}%.",
        })

    elif 25 <= fill < 40 or 80 < fill <= 90:

        checks.append({
            "severity": "WARNING",
            "message":
                f"Operating fill = {fill:.1f}%. "
                "Review headspace and impeller immersion.",
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message":
                f"Operating fill = {fill:.1f}%. "
                "Confirm suitability for process operation.",
        })

    # =====================================================
    # D/T
    # =====================================================

    D_T = (
        impeller_diameter_m /
        tank_diameter_m
        if tank_diameter_m > 0
        else 0
    )

    if 0.25 <= D_T <= 0.50:

        checks.append({
            "severity": "PASS",
            "message":
                f"Impeller/Tank ratio = {D_T:.3f}.",
        })

    elif 0.20 <= D_T <= 0.60:

        checks.append({
            "severity": "WARNING",
            "message":
                f"Impeller/Tank ratio = {D_T:.3f}. "
                "Review impeller-specific guidance.",
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message":
                f"Impeller/Tank ratio = {D_T:.3f}. "
                "Outside common preliminary screening range.",
        })

    # =====================================================
    # BAFFLES
    # =====================================================

    if number_baffles >= 4:

        checks.append({
            "severity": "PASS",
            "message":
                f"{number_baffles} baffles provided.",
        })

    elif number_baffles > 0:

        checks.append({
            "severity": "WARNING",
            "message":
                f"{number_baffles} baffles provided. "
                "Review vortex suppression.",
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message":
                "No baffles provided. "
                "Strong rotational flow may occur.",
        })

    # =====================================================
    # H/T
    # =====================================================

    H_T = (
        liquid_height_m /
        tank_diameter_m
        if tank_diameter_m > 0
        else 0
    )

    if H_T >= 1.0:

        checks.append({
            "severity": "PASS",
            "message":
                f"Liquid height/Tank diameter = {H_T:.2f}.",
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message":
                f"Liquid height/Tank diameter = {H_T:.2f}. "
                "Review liquid coverage and circulation.",
        })

    # =====================================================
    # RPM
    # =====================================================

    if rpm <= 300:

        checks.append({
            "severity": "PASS",
            "message":
                f"Agitator speed = {rpm:.1f} RPM.",
        })

    elif rpm <= 500:

        checks.append({
            "severity": "WARNING",
            "message":
                f"Agitator speed = {rpm:.1f} RPM. "
                "Review mechanical loading and vortexing.",
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message":
                f"Agitator speed = {rpm:.1f} RPM. "
                "High-speed mechanical review required.",
        })

    # =====================================================
    # POWER/VOLUME
    # =====================================================

    if power_volume_kw_m3 is not None:

        if power_volume_kw_m3 <= 5:

            checks.append({
                "severity": "PASS",
                "message":
                    f"P/V = {power_volume_kw_m3:.3f} kW/m³.",
            })

        elif power_volume_kw_m3 <= 20:

            checks.append({
                "severity": "WARNING",
                "message":
                    f"P/V = {power_volume_kw_m3:.3f} kW/m³. "
                    "Review process requirement and motor load.",
            })

        else:

            checks.append({
                "severity": "WARNING",
                "message":
                    f"P/V = {power_volume_kw_m3:.3f} kW/m³. "
                    "High specific power; verify application.",
            })

    # =====================================================
    # RCI
    # =====================================================

    if agitator == "RCI":

        checks.append({
            "severity": "WARNING",
            "message":
                "RCI selected. Validate Np/Nq from manufacturer "
                "or test data before using calculated power.",
        })

    # =====================================================
    # VISCOSITY
    # =====================================================

    if viscosity_pa_s > 10:

        checks.append({
            "severity": "WARNING",
            "message":
                "High viscosity detected. "
                "Validate laminar power correlation, torque "
                "and gearbox selection.",
        })

    # =====================================================
    # GAS-LIQUID
    # =====================================================

    if gas_flow_m3_h and gas_flow_m3_h > 0:

        if kLa_1_h is not None:

            checks.append({
                "severity": "WARNING",
                "message":
                    f"Estimated kLa = {kLa_1_h:.2f} 1/h. "
                    "Validate with applicable gas-liquid "
                    "mass-transfer correlation or pilot data.",
            })

    # =====================================================
    # FINAL STATUS
    # =====================================================

    failures = sum(
        1
        for c in checks
        if c["severity"] == "FAIL"
    )

    warnings = sum(
        1
        for c in checks
        if c["severity"] == "WARNING"
    )

    if failures > 0:

        overall = "FAIL"

    elif warnings > 0:

        overall = "REVIEW"

    else:

        overall = "PASS"

    return {
        "overall": overall,
        "failures": failures,
        "warnings": warnings,
        "checks": checks,
    }
