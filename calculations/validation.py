"""
Engineering validation / screening logic.
"""


def validate_design(
    geometry,
    stages,
    process_type="General Mixing",
):
    checks = []

    working_volume = geometry.get(
        "working_volume_m3",
        0.0,
    )

    total_volume = geometry.get(
        "total_volume_m3",
        0.0,
    )

    tank_D = geometry.get(
        "tank_diameter_m",
        0.0,
    )

    fill = (
        100.0 * working_volume / total_volume
        if total_volume > 0
        else 0.0
    )

    if total_volume <= 0:
        checks.append({
            "severity": "FAIL",
            "message": "Calculated vessel volume is zero or invalid.",
        })

    elif working_volume > total_volume:
        checks.append({
            "severity": "FAIL",
            "message": (
                f"Working volume {working_volume:.2f} m³ "
                f"exceeds calculated vessel capacity "
                f"{total_volume:.2f} m³."
            ),
        })

    else:
        checks.append({
            "severity": "PASS",
            "message": (
                f"Working volume = {fill:.1f}% "
                "of calculated vessel capacity."
            ),
        })

    if 20.0 <= fill <= 85.0:
        checks.append({
            "severity": "PASS",
            "message": (
                f"Operating fill {fill:.1f}% is within "
                "the preliminary 20–85% screening range."
            ),
        })
    elif fill > 85.0:
        checks.append({
            "severity": "REVIEW",
            "message": (
                f"High operating fill: {fill:.1f}%. "
                "Confirm required headspace and process allowance."
            ),
        })
    else:
        checks.append({
            "severity": "REVIEW",
            "message": (
                f"Low operating fill: {fill:.1f}%. "
                "Confirm impeller immersion and circulation."
            ),
        })

    baffles = geometry.get(
        "baffles",
        0,
    )

    if baffles >= 4:
        checks.append({
            "severity": "PASS",
            "message": (
                f"{baffles} baffles specified. "
                "Confirm actual width, thickness and clearance."
            ),
        })
    else:
        checks.append({
            "severity": "REVIEW",
            "message": (
                f"Only {baffles} baffles specified. "
                "Confirm baffling requirement for the actual regime."
            ),
        })

    for i, stage in enumerate(stages, start=1):

        D = stage.get(
            "impeller_diameter_m",
            0.0,
        )

        D_T = (
            D / tank_D
            if tank_D > 0
            else 0.0
        )

        if 0.20 <= D_T <= 0.90:
            severity = "PASS"
        else:
            severity = "REVIEW"

        checks.append({
            "severity": severity,
            "message": (
                f"Stage {i}: D/T = {D_T:.3f}. "
                "Confirm against selected impeller geometry."
            ),
        })

        clearance_T = stage.get(
            "clearance_T",
            None,
        )

        if clearance_T is not None:
            if 0.05 <= clearance_T <= 0.50:
                severity = "PASS"
            else:
                severity = "REVIEW"

            checks.append({
                "severity": severity,
                "message": (
                    f"Stage {i}: C/T = "
                    f"{clearance_T:.3f}. "
                    "Review impeller elevation and bottom coverage."
                ),
            })

        Re = stage.get(
            "Re",
            0.0,
        )

        regime = stage.get(
            "mixing_regime",
            "Unknown",
        )

        if Re > 10000:
            severity = "PASS"
            msg = (
                f"Stage {i}: Re = {Re:,.0f}; "
                "turbulent-regime screening correlations may be applicable."
            )
        elif Re > 0:
            severity = "REVIEW"
            msg = (
                f"Stage {i}: Re = {Re:,.0}; "
                f"{regime} regime. Confirm Np/Nq correlation."
            )
        else:
            severity = "FAIL"
            msg = (
                f"Stage {i}: Reynolds number is invalid."
            )

        checks.append({
            "severity": severity,
            "message": msg,
        })

        njs = stage.get(
            "njs_rpm",
            None,
        )

        if (
            process_type in [
                "Solid-Liquid",
                "Gas-Liquid-Solid",
                "Crystallization",
            ]
            and njs is not None
        ):
            rpm = stage.get(
                "rpm",
                0.0,
            )

            ratio = (
                rpm / njs
                if njs > 0
                else 0.0
            )

            if ratio >= 1.0:
                severity = "PASS"
            else:
                severity = "REVIEW"

            checks.append({
                "severity": severity,
                "message": (
                    f"Stage {i}: N/Njs = {ratio:.2f}. "
                    "Njs is a screening estimate; validate with "
                    "geometry-specific S factor or pilot data."
                ),
            })

    return checks


def overall_status(checks):
    if any(
        x["severity"] == "FAIL"
        for x in checks
    ):
        return "FAIL"

    if any(
        x["severity"] == "REVIEW"
        for x in checks
    ):
        return "REVIEW"

    return "PASS"


def recommendations(
    process_type,
    train,
):
    power = train.get(
        "total_power_kw",
        0.0,
    )

    q = train.get(
        "total_Q_m3_h",
        0.0,
    )

    pv = train.get(
        "P_per_V_kW_m3",
        0.0,
    )

    qv = train.get(
        "Q_per_volume_1_s",
        0.0,
    )

    guidance = {

        "Liquid-Liquid": (
            "Prioritize bulk circulation, phase contact and measured "
            "blend time. Compare Q/V and P/V rather than RPM alone."
        ),

        "Solid-Liquid": (
            "Prioritize N/Njs and solids suspension. Confirm particle "
            "properties, impeller clearance and actual solids loading."
        ),

        "Gas-Liquid": (
            "Prioritize gas dispersion, flooding behaviour, gas rate, "
            "P/V and validated kLa correlation."
        ),

        "Gas-Liquid-Solid": (
            "Simultaneously demonstrate solids suspension and gas "
            "dispersion. Validate N/Njs and kLa."
        ),

        "Crystallization": (
            "Balance suspension and circulation against crystal shear. "
            "Confirm crystal size distribution experimentally."
        ),

        "High-Viscosity": (
            "Prioritize torque, shaft loading, gearbox capacity, "
            "laminar power correlation and heat-transfer performance."
        ),

        "General Mixing": (
            "Use Q/V and measured blend time as the primary mixing "
            "performance indicators, supported by P/V and Re."
        ),

        "Heat-Controlled Reaction": (
            "Check mixing uniformity together with heat-transfer "
            "capacity and credible reaction heat-release duty."
        ),
    }

    return [
        guidance.get(
            process_type,
            guidance["General Mixing"],
        ),

        (
            f"Calculated total shaft power = "
            f"{power:.2f} kW."
        ),

        (
            f"Calculated total pumping capacity = "
            f"{q:.2f} m³/h."
        ),

        (
            f"Overall P/V = {pv:.3f} kW/m³ "
            f"and Q/V = {qv:.5f} s⁻¹."
        ),

        (
            "Np/Nq, Njs, kLa and blend-time correlations are "
            "screening inputs. Final design should use "
            "validated impeller/vendor data and pilot results."
        ),
    ]
