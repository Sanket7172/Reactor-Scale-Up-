from io import BytesIO

import pandas as pd
from docx import Document
from docx.shared import Inches


def create_excel_report(
    project_name,
    prepared_by,
    process_type,
    study_mode,
    scaleup_basis,
    reactors,
):

    output = BytesIO()

    summary_rows = []

    for r in reactors:

        summary_rows.append(
            {
                "Reactor": r.get("name"),
                "Working Volume (m3)": r.get(
                    "working_volume"
                ),
                "Vessel Capacity (m3)": r.get(
                    "vessel_volume"
                ),
                "Liquid Height (m)": r.get(
                    "liquid_height_m"
                ),
                "Tank Diameter (m)": r.get(
                    "tank_diameter_m"
                ),
                "Impeller Diameter (m)": r.get(
                    "impeller_diameter_m"
                ),
                "RPM": r.get("rpm"),
                "Power (kW)": r.get(
                    "power_kw"
                ),
                "P/V (kW/m3)": r.get(
                    "power_volume_kw_m3"
                ),
                "Tip Speed (m/s)": r.get(
                    "tip_speed"
                ),
                "Reynolds Number": r.get(
                    "Re"
                ),
                "Froude Number": r.get(
                    "Fr"
                ),
                "Pumping (m3/h)": r.get(
                    "pumping_m3_h"
                ),
                "Q/V (1/h)": r.get(
                    "qv_1_h"
                ),
                "Turnover Time (min)": r.get(
                    "turnover_time_min"
                ),
                "Validation": r.get(
                    "validation",
                    {}
                ).get(
                    "overall"
                ),
            }
        )

    summary_df = pd.DataFrame(
        summary_rows
    )

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )

        for r in reactors:

            rows = []

            for key, value in r.items():

                if isinstance(value, dict):
                    continue

                rows.append(
                    {
                        "Parameter": key,
                        "Value": value,
                    }
                )

            pd.DataFrame(rows).to_excel(
                writer,
                sheet_name=str(
                    r.get("name", "Reactor")
                )[:31],
                index=False,
            )

        # Validation sheet

        validation_rows = []

        for r in reactors:

            validation = r.get(
                "validation",
                {}
            )

            for check in validation.get(
                "checks",
                []
            ):

                validation_rows.append(
                    {
                        "Reactor": r.get(
                            "name"
                        ),
                        "Severity": check.get(
                            "severity"
                        ),
                        "Engineering Check": check.get(
                            "message"
                        ),
                    }
                )

        pd.DataFrame(
            validation_rows
        ).to_excel(
            writer,
            sheet_name="Validation",
            index=False,
        )

    output.seek(0)

    return output.getvalue()


def create_word_report(
    project_name,
    prepared_by,
    process_type,
    study_mode,
    scaleup_basis,
    reactors,
):

    document = Document()

    document.add_heading(
        "Reactor Scale-Up Engineering Report",
        level=0,
    )

    document.add_paragraph(
        project_name
    )

    document.add_paragraph(
        f"Prepared by: {prepared_by}"
    )

    document.add_paragraph(
        f"Process Type: {process_type}"
    )

    document.add_paragraph(
        f"Study Mode: {study_mode}"
    )

    document.add_paragraph(
        f"Scale-Up Basis: {scaleup_basis}"
    )

    document.add_heading(
        "Executive Summary",
        level=1,
    )

    document.add_paragraph(
        "This report presents preliminary reactor "
        "mixing, agitation, scale-up and validation "
        "calculations. Results are intended for "
        "engineering screening and must be verified "
        "against validated correlations, vendor data "
        "and pilot-scale measurements before final design."
    )

    document.add_heading(
        "Reactor Performance Summary",
        level=1,
    )

    table = document.add_table(
        rows=1,
        cols=10,
    )

    headers = [
        "Reactor",
        "Volume",
        "Diameter",
        "Liquid Height",
        "RPM",
        "Power",
        "P/V",
        "Tip Speed",
        "Re",
        "Status",
    ]

    for i, header in enumerate(headers):

        table.rows[0].cells[i].text = header

    for r in reactors:

        values = [
            r.get("name", ""),
            f"{r.get('working_volume', 0):.3f} m³",
            f"{r.get('tank_diameter_m', 0):.3f} m",
            f"{r.get('liquid_height_m', 0):.3f} m",
            f"{r.get('rpm', 0):.1f}",
            f"{r.get('power_kw', 0) or 0:.3f} kW",
            f"{r.get('power_volume_kw_m3', 0) or 0:.4f} kW/m³",
            f"{r.get('tip_speed', 0) or 0:.3f} m/s",
            f"{r.get('Re', 0) or 0:.0f}",
            r.get(
                "validation",
                {}
            ).get(
                "overall",
                "REVIEW"
            ),
        ]

        cells = table.add_row().cells

        for i, value in enumerate(values):

            cells[i].text = str(value)

    document.add_heading(
        "Detailed Reactor Results",
        level=1,
    )

    for r in reactors:

        document.add_heading(
            f"{r.get('name', 'Reactor')}",
            level=2,
        )

        table = document.add_table(
            rows=1,
            cols=3,
        )

        table.rows[0].cells[0].text = "Parameter"
        table.rows[0].cells[1].text = "Value"
        table.rows[0].cells[2].text = "Unit"

        parameters = [
            ("Working Volume", r.get("working_volume"), "m³"),
            ("Vessel Capacity", r.get("vessel_volume"), "m³"),
            ("Tank Diameter", r.get("tank_diameter_m"), "m"),
            ("Liquid Height", r.get("liquid_height_m"), "m"),
            ("Impeller Diameter", r.get("impeller_diameter_m"), "m"),
            ("Agitator Speed", r.get("rpm"), "RPM"),
            ("Power", r.get("power_kw"), "kW"),
            ("Power / Volume", r.get("power_volume_kw_m3"), "kW/m³"),
            ("Tip Speed", r.get("tip_speed"), "m/s"),
            ("Reynolds Number", r.get("Re"), "-"),
            ("Froude Number", r.get("Fr"), "-"),
            ("Pumping Capacity", r.get("pumping_m3_h"), "m³/h"),
            ("Q/V", r.get("qv_1_h"), "1/h"),
            ("Turnover Time", r.get("turnover_time_min"), "min"),
        ]

        for parameter, value, unit in parameters:

            cells = table.add_row().cells

            cells[0].text = parameter

            if value is None:
                cells[1].text = "N/A"
            else:
                cells[1].text = f"{value:.4g}"

            cells[2].text = unit

        if process_type in [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ]:

            document.add_paragraph(
                "Gas-Liquid Screening Results"
            )

            gas_parameters = [
                (
                    "Gas Flow",
                    r.get("gas_flow_m3_h"),
                    "m³/h",
                ),
                (
                    "Superficial Gas Velocity",
                    r.get(
                        "gas_superficial_velocity_m_s"
                    ),
                    "m/s",
                ),
                (
                    "Gas Holdup",
                    r.get(
                        "gas_holdup_percent"
                    ),
                    "%",
                ),
                (
                    "Bubble Residence Time",
                    r.get(
                        "bubble_residence_time_min"
                    ),
                    "min",
                ),
                (
                    "Interfacial Area",
                    r.get(
                        "interfacial_area_m2_m3"
                    ),
                    "m²/m³",
                ),
                (
                    "Screening kLa",
                    r.get(
                        "kla_1_h"
                    ),
                    "1/h",
                ),
            ]

            for parameter, value, unit in gas_parameters:

                document.add_paragraph(
                    f"{parameter}: "
                    f"{'N/A' if value is None else f'{value:.4g}'} "
                    f"{unit}"
                )

    document.add_heading(
        "Engineering Validation",
        level=1,
    )

    for r in reactors:

        validation = r.get(
            "validation",
            {}
        )

        document.add_paragraph(
            f"{r.get('name')}: "
            f"{validation.get('overall', 'REVIEW')}"
        )

        for check in validation.get(
            "checks",
            []
        ):

            document.add_paragraph(
                f"[{check.get('severity')}] "
                f"{check.get('message')}",
                style="List Bullet",
            )

    document.add_heading(
        "Engineering Disclaimer",
        level=1,
    )

    document.add_paragraph(
        "This software provides preliminary engineering "
        "screening calculations. Final reactor design, "
        "agitator selection, motor sizing, solids suspension, "
        "gas dispersion, kLa, Njs, mechanical design and "
        "process performance shall be confirmed using "
        "validated correlations, vendor data, pilot trials "
        "and applicable engineering standards."
    )

    output = BytesIO()

    document.save(output)

    output.seek(0)

    return output.getvalue()
