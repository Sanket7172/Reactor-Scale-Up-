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
):

    checks = []

    # =====================================================
    # VOLUME
    # =====================================================

    if volume_m3 <= vessel_volume_m3:

        checks.append({
            "severity": "PASS",
            "message": (
                "Operating volume is within calculated vessel capacity."
            ),
        })

    else:

        checks.append({
            "severity": "FAIL",
            "message": (
                "Operating volume exceeds calculated vessel capacity."
            ),
        })

    # =====================================================
    # FILL
    # =====================================================

    fill = (
        volume_m3 /
        vessel_volume_m3 *
        100
        if vessel_volume_m3 > 0
        else 0
    )

    if 40 <= fill <= 80:

        checks.append({
            "severity": "PASS",
            "message": (
                f"Operating fill = {fill:.1f}%."
            ),
        })

    elif 25 <= fill < 40 or 80 < fill <= 90:

        checks.append({
            "severity": "WARNING",
            "message": (
                f"Operating fill = {fill:.1f}%. "
                "Review process headspace and mixing performance."
            ),
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message": (
                f"Operating fill = {fill:.1f}%. "
                "This may be outside the preferred operating range."
            ),
        })

    # =====================================================
    # IMPeller / TANK RATIO
    # =====================================================

    D_ratio = (
        impeller_diameter_m /
        tank_diameter_m
        if tank_diameter_m > 0
        else 0
    )

    if 0.25 <= D_ratio <= 0.50:

        checks.append({
            "severity": "PASS",
            "message": (
                f"Impeller/Tank diameter ratio = {D_ratio:.3f}."
            ),
        })

    elif 0.20 <= D_ratio <= 0.60:

        checks.append({
            "severity": "WARNING",
            "message": (
                f"Impeller/Tank ratio = {D_ratio:.3f}. "
                "Review against impeller-specific design guidance."
            ),
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message": (
                f"Impeller/Tank ratio = {D_ratio:.3f}. "
                "This is outside a commonly screened range."
            ),
        })

    # =====================================================
    # BAFFLES
    # =====================================================

    if number_baffles >= 4:

        checks.append({
            "severity": "PASS",
            "message": (
                f"{number_baffles} baffles provided."
            ),
        })

    elif number_baffles > 0:

        checks.append({
            "severity": "WARNING",
            "message": (
                f"Only {number_baffles} baffles provided. "
                "Check vortex suppression."
            ),
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message": (
                "No baffles selected. Strong rotational motion may occur."
            ),
        })

    # =====================================================
    # LIQUID HEIGHT
    # =====================================================

    if liquid_height_m > 0:

        H_liquid_D = (
            liquid_height_m /
            tank_diameter_m
        )

        if H_liquid_D >= 1.0:

            checks.append({
                "severity": "PASS",
                "message": (
                    f"Liquid height/Tank diameter = {H_liquid_D:.2f}."
                ),
            })

        else:

            checks.append({
                "severity": "WARNING",
                "message": (
                    f"Liquid height/Tank diameter = {H_liquid_D:.2f}. "
                    "Review impeller coverage and circulation."
                ),
            })

    # =====================================================
    # RPM
    # =====================================================

    if rpm <= 300:

        checks.append({
            "severity": "PASS",
            "message": (
                f"Agitator speed = {rpm:.1f} RPM."
            ),
        })

    else:

        checks.append({
            "severity": "WARNING",
            "message": (
                f"High agitator speed = {rpm:.1f} RPM. "
                "Review mechanical and vortex limitations."
            ),
        })

    # =====================================================
    # RCI
    # =====================================================

    if agitator == "RCI":

        checks.append({
            "severity": "WARNING",
            "message": (
                "RCI selected. Use validated manufacturer/test Np/Nq data."
            ),
        })

    # =====================================================
    # VISCOSITY
    # =====================================================

    if viscosity_pa_s > 10:

        checks.append({
            "severity": "WARNING",
            "message": (
                "High viscosity detected. Verify power correlation "
                "and impeller suitability."
            ),
        })

    # =====================================================
    # RESULT
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
