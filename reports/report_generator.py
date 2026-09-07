from io import BytesIO
from datetime import datetime

import pandas as pd

from docx import Document
from docx.shared import Inches, Pt

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


# =========================================================
# SUMMARY DATAFRAME
# =========================================================

def create_summary_dataframe(
    reactors,
):

    rows = []

    for r in reactors:

        rows.append(
            {
                "Reactor":
                    r.get("name"),

                "Working Volume (m3)":
                    r.get("working_volume"),

                "Vessel Capacity (m3)":
                    r.get("vessel_volume"),

                "Tank ID (m)":
                    r.get("tank_diameter_m"),

                "Liquid Height (m)":
                    r.get("liquid_height_m"),

                "Agitator":
                    r.get("agitator"),

                "Impeller Diameter (m)":
                    r.get("impeller_diameter_m"),

                "RPM":
                    r.get("rpm"),

                "Power (kW)":
                    r.get("power_kw"),

                "P/V (kW/m3)":
                    r.get(
                        "power_volume_kw_m3"
                    ),

                "Tip Speed (m/s)":
                    r.get("tip_speed"),

                "Re":
                    r.get("Re"),

                "Fr":
                    r.get("Fr"),

                "Q (m3/h)":
                    r.get("pumping_m3_h"),

                "Q/V (1/h)":
                    r.get("qv_1_h"),

                "Turnover Time (min)":
                    r.get(
                        "turnover_time_min"
                    ),

                "Gas Flow (m3/h)":
                    r.get(
                        "gas_flow_m3_h"
                    ),

                "Bubble Residence (min)":
                    r.get(
                        "bubble_residence_time_min"
                    ),

                "kLa (1/h)":
                    r.get(
                        "kLa_1_h"
                    ),

                "Validation":
                    r.get(
                        "validation",
                        {}
                    ).get(
                        "overall",
                        "REVIEW"
                    ),
            }
        )

    return pd.DataFrame(rows)


# =========================================================
# WORD REPORT
# =========================================================

def create_word_report(
    project_name,
    prepared_by,
    process_type,
    study_mode,
    scaleup_basis,
    reactors,
    scaleup_result=None,
):

    document = Document()

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = document.add_heading(
        "Reactor Scale-Up Engineering Report",
        0
    )

    title.alignment = 1

    document.add_paragraph(
        f"Project: {project_name}"
    )

    document.add_paragraph(
        f"Prepared By: {prepared_by}"
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

    document.add_paragraph(
        f"Generated: "
        f"{datetime.now().strftime('%d-%m-%Y %H:%M')}"
    )

    document.add_page_break()

    # -----------------------------------------------------
    # EXECUTIVE SUMMARY
    # -----------------------------------------------------

    document.add_heading(
        "1. Executive Summary",
        level=1
    )

    document.add_paragraph(
        "This report presents a preliminary engineering "
        "assessment of reactor geometry, agitation "
        "performance and scale-up parameters."
    )

    document.add_paragraph(
        "The calculations are intended for engineering "
        "screening and preliminary scale-up assessment. "
        "Final equipment design shall be verified against "
        "validated correlations, vendor data, pilot trials "
        "and applicable mechanical design standards."
    )

    # -----------------------------------------------------
    # SUMMARY TABLE
    # -----------------------------------------------------

    document.add_heading(
        "2. Reactor Summary",
        level=1
    )

    df = create_summary_dataframe(
        reactors
    )

    table = document.add_table(
        rows=1,
        cols=len(df.columns)
    )

    table.style = "Table Grid"

    hdr = table.rows[0].cells

    for i, column in enumerate(
        df.columns
    ):

        hdr[i].text = str(
            column
        )

    for _, row in df.iterrows():

        cells = table.add_row().cells

        for i, value in enumerate(
            row
        ):

            if pd.isna(value):
                text = "—"
            else:
                text = str(value)

            cells[i].text = text

    # -----------------------------------------------------
    # DETAILED REACTOR RESULTS
    # -----------------------------------------------------

    document.add_heading(
        "3. Detailed Engineering Results",
        level=1
    )

    for r in reactors:

        document.add_heading(
            f"{r.get('name')} Reactor",
            level=2
        )

        results = [
            (
                "Working Volume",
                r.get("working_volume"),
                "m3"
            ),
            (
                "Vessel Capacity",
                r.get("vessel_volume"),
                "m3"
            ),
            (
                "Tank Diameter",
                r.get("tank_diameter_m"),
                "m"
            ),
            (
                "Liquid Height",
                r.get("liquid_height_m"),
                "m"
            ),
            (
                "Impeller Diameter",
                r.get("impeller_diameter_m"),
                "m"
            ),
            (
                "Agitator Speed",
                r.get("rpm"),
                "RPM"
            ),
            (
                "Power",
                r.get("power_kw"),
                "kW"
            ),
            (
                "P/V",
                r.get("power_volume_kw_m3"),
                "kW/m3"
            ),
            (
                "Tip Speed",
                r.get("tip_speed"),
                "m/s"
            ),
            (
                "Reynolds Number",
                r.get("Re"),
                "-"
            ),
            (
                "Froude Number",
                r.get("Fr"),
                "-"
            ),
            (
                "Pumping Capacity",
                r.get("pumping_m3_h"),
                "m3/h"
            ),
            (
                "Q/V",
                r.get("qv_1_h"),
                "1/h"
            ),
            (
                "Turnover Time",
                r.get("turnover_time_min"),
                "min"
            ),
            (
                "Bubble Residence Time",
                r.get(
                    "bubble_residence_time_min"
                ),
                "min"
            ),
            (
                "kLa",
                r.get("kLa_1_h"),
                "1/h"
            ),
        ]

        table = document.add_table(
            rows=1,
            cols=3
        )

        table.style = "Table Grid"

        table.rows[0].cells[0].text = (
            "Parameter"
        )

        table.rows[0].cells[1].text = (
            "Value"
        )

        table.rows[0].cells[2].text = (
            "Unit"
        )

        for parameter, value, unit in results:

            row = table.add_row().cells

            row[0].text = parameter

            if value is None:
                row[1].text = "—"
            else:
                try:
                    row[1].text = f"{float(value):.4f}"
                except (TypeError, ValueError):
                    row[1].text = str(value)

            row[2].text = unit

    # -----------------------------------------------------
    # SCALE-UP
    # -----------------------------------------------------

    if scaleup_result:

        document.add_heading(
            "4. Scale-Up Assessment",
            level=1
        )

        table = document.add_table(
            rows=1,
            cols=2
        )

        table.style = "Table Grid"

        table.rows[0].cells[0].text = (
            "Parameter"
        )

        table.rows[0].cells[1].text = (
            "Result"
        )

        scale_items = [
            (
                "Scale-Up Basis",
                scaleup_result.get("basis")
            ),
            (
                "Target RPM",
                scaleup_result.get(
                    "target_rpm"
                )
            ),
            (
                "Target Tip Speed",
                scaleup_result.get(
                    "target_tip_speed"
                )
            ),
            (
                "Target P/V",
                scaleup_result.get(
                    "target_power_volume_kw_m3"
                )
            ),
            (
                "Engineering Message",
                scaleup_result.get(
                    "message"
                )
            ),
        ]

        for parameter, value in scale_items:

            row = table.add_row().cells

            row[0].text = parameter

            row[1].text = (
                "—"
                if value is None
                else str(value)
            )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    document.add_heading(
        "5. Engineering Validation",
        level=1
    )

    for r in reactors:

        validation = r.get(
            "validation",
            {}
        )

        document.add_heading(
            f"{r.get('name')} Validation",
            level=2
        )

        document.add_paragraph(
            f"Overall Status: "
            f"{validation.get('overall', 'REVIEW')}"
        )

        for check in validation.get(
            "checks",
            []
        ):

            document.add_paragraph(
                f"{check.get('severity')}: "
                f"{check.get('message')}",
                style="List Bullet"
            )

    # -----------------------------------------------------
    # ASSUMPTIONS
    # -----------------------------------------------------

    document.add_heading(
        "6. Engineering Assumptions & Limitations",
        level=1
    )

    assumptions = [
        "Agitator Np and Nq values are representative screening values.",
        "Actual impeller geometry may require manufacturer-specific Np/Nq data.",
        "Njs requires a validated solids-suspension correlation.",
        "Blend time requires an appropriate mixing correlation or experimental data.",
        "Gas-liquid kLa is a preliminary estimate and must be validated.",
        "Bubble residence time is based on a simplified bubble-rise model.",
        "Torispherical and vessel-head geometry is preliminary and should be checked against the actual vessel standard.",
        "Mechanical shaft, gearbox, bearing and motor design are not included.",
        "CFD is not represented by the current 3D visualization.",
        "Final equipment design requires detailed process, mechanical and safety review.",
    ]

    for item in assumptions:

        document.add_paragraph(
            item,
            style="List Bullet"
        )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    output = BytesIO()

    document.save(
        output
    )

    output.seek(0)

    return output


# =========================================================
# EXCEL REPORT
# =========================================================

def create_excel_report(
    project_name,
    prepared_by,
    process_type,
    study_mode,
    scaleup_basis,
    reactors,
    scaleup_result=None,
):

    workbook = Workbook()

    # =====================================================
    # SUMMARY
    # =====================================================

    ws = workbook.active

    ws.title = "Summary"

    ws["A1"] = (
        "Reactor Scale-Up Engineering Report"
    )

    ws["A1"].font = Font(
        bold=True,
        size=16
    )

    metadata = [
        ("Project", project_name),
        ("Prepared By", prepared_by),
        ("Process Type", process_type),
        ("Study Mode", study_mode),
        ("Scale-Up Basis", scaleup_basis),
        (
            "Generated",
            datetime.now().strftime(
                "%d-%m-%Y %H:%M"
            )
        ),
    ]

    row = 3

    for key, value in metadata:

        ws.cell(
            row=row,
            column=1,
            value=key
        )

        ws.cell(
            row=row,
            column=2,
            value=value
        )

        ws.cell(
            row=row,
            column=1
        ).font = Font(
            bold=True
        )

        row += 1

    # =====================================================
    # REACTOR SUMMARY
    # =====================================================

    row += 2

    df = create_summary_dataframe(
        reactors
    )

    for col_idx, column in enumerate(
        df.columns,
        start=1
    ):

        cell = ws.cell(
            row=row,
            column=col_idx,
            value=column
        )

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center"
        )

    for r_idx, record in enumerate(
        df.itertuples(index=False),
        start=row + 1
    ):

        for c_idx, value in enumerate(
            record,
            start=1
        ):

            ws.cell(
                row=r_idx,
                column=c_idx,
                value=value
            )

    # =====================================================
    # DETAILED RESULTS
    # =====================================================

    for reactor in reactors:

        sheet_name = str(
            reactor.get("name", "Reactor")
        )[:31]

        detail = workbook.create_sheet(
            sheet_name
        )

        detail.append([
            "Parameter",
            "Value",
            "Unit",
        ])

        for cell in detail[1]:

            cell.font = Font(
                bold=True
            )

        parameters = [
            (
                "Working Volume",
                reactor.get(
                    "working_volume"
                ),
                "m3"
            ),
            (
                "Vessel Capacity",
                reactor.get(
                    "vessel_volume"
                ),
                "m3"
            ),
            (
                "Tank Diameter",
                reactor.get(
                    "tank_diameter_m"
                ),
                "m"
            ),
            (
                "Straight Height",
                reactor.get(
                    "straight_height_m"
                ),
                "m"
            ),
            (
                "Liquid Height",
                reactor.get(
                    "liquid_height_m"
                ),
                "m"
            ),
            (
                "Agitator",
                reactor.get(
                    "agitator"
                ),
                "-"
            ),
            (
                "Impeller Diameter",
                reactor.get(
                    "impeller_diameter_m"
                ),
                "m"
            ),
            (
                "Number of Impellers",
                reactor.get(
                    "number_impellers"
                ),
                "-"
            ),
            (
                "RPM",
                reactor.get(
                    "rpm"
                ),
                "RPM"
            ),
            (
                "Power",
                reactor.get(
                    "power_kw"
                ),
                "kW"
            ),
            (
                "P/V",
                reactor.get(
                    "power_volume_kw_m3"
                ),
                "kW/m3"
            ),
            (
                "P/V",
                reactor.get(
                    "power_volume_w_m3"
                ),
                "W/m3"
            ),
            (
                "Tip Speed",
                reactor.get(
                    "tip_speed"
                ),
                "m/s"
            ),
            (
                "Reynolds Number",
                reactor.get(
                    "Re"
                ),
                "-"
            ),
            (
                "Froude Number",
                reactor.get(
                    "Fr"
                ),
                "-"
            ),
            (
                "Pumping Capacity",
                reactor.get(
                    "pumping_m3_h"
                ),
                "m3/h"
            ),
            (
                "Q/V",
                reactor.get(
                    "qv_1_h"
                ),
                "1/h"
            ),
            (
                "Turnover Time",
                reactor.get(
                    "turnover_time_min"
                ),
                "min"
            ),
            (
                "Gas Flow",
                reactor.get(
                    "gas_flow_m3_h"
                ),
                "m3/h"
            ),
            (
                "Gas Superficial Velocity",
                reactor.get(
                    "gas_superficial_velocity_m_s"
                ),
                "m/s"
            ),
            (
                "Bubble Diameter",
                reactor.get(
                    "bubble_diameter_m"
                ),
                "m"
            ),
            (
                "Bubble Rise Velocity",
                reactor.get(
                    "bubble_rise_velocity_m_s"
                ),
                "m/s"
            ),
            (
                "Bubble Residence Time",
                reactor.get(
                    "bubble_residence_time_min"
                ),
                "min"
            ),
            (
                "Bubble Reynolds Number",
                reactor.get(
                    "bubble_reynolds"
                ),
                "-"
            ),
            (
                "Schmidt Number",
                reactor.get(
                    "schmidt_number"
                ),
                "-"
            ),
            (
                "Sherwood Number",
                reactor.get(
                    "sherwood_number"
                ),
                "-"
            ),
            (
                "Liquid Mass Transfer Coefficient",
                reactor.get(
                    "kL_m_s"
                ),
                "m/s"
            ),
            (
                "Interfacial Area",
                reactor.get(
                    "interfacial_area_m2_m3"
                ),
                "m2/m3"
            ),
            (
                "kLa",
                reactor.get(
                    "kLa_1_h"
                ),
                "1/h"
            ),
        ]

        for item in parameters:

            detail.append(
                list(item)
            )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        detail.append([])
        detail.append([
            "Validation",
            reactor.get(
                "validation",
                {}
            ).get(
                "overall",
                "REVIEW"
            ),
            "-"
        ])

        for check in reactor.get(
            "validation",
            {}
        ).get(
            "checks",
            []
        ):

            detail.append([
                check.get(
                    "severity"
                ),
                check.get(
                    "message"
                ),
                "-"
            ])

        # -------------------------------------------------
        # Column width
        # -------------------------------------------------

        for column_cells in detail.columns:

            max_length = 0

            column_letter = (
                get_column_letter(
                    column_cells[0].column
                )
            )

            for cell in column_cells:

                value = (
                    ""
                    if cell.value is None
                    else str(cell.value)
                )

                max_length = max(
                    max_length,
                    len(value)
                )

            detail.column_dimensions[
                column_letter
            ].width = min(
                max_length + 3,
                45
            )

    # =====================================================
    # SCALE-UP
    # =====================================================

    if scaleup_result:

        ws_scale = workbook.create_sheet(
            "Scale-Up"
        )

        ws_scale.append([
            "Parameter",
            "Value"
        ])

        for cell in ws_scale[1]:

            cell.font = Font(
                bold=True
            )

        scale_items = [
            (
                "Basis",
                scaleup_result.get(
                    "basis"
                )
            ),
            (
                "Target RPM",
                scaleup_result.get(
                    "target_rpm"
                )
            ),
            (
                "Target Tip Speed",
                scaleup_result.get(
                    "target_tip_speed"
                )
            ),
            (
                "Target P/V",
                scaleup_result.get(
                    "target_power_volume_kw_m3"
                )
            ),
            (
                "Message",
                scaleup_result.get(
                    "message"
                )
            ),
        ]

        for item in scale_items:

            ws_scale.append(
                list(item)
            )

    # =====================================================
    # COLUMN WIDTH
    # =====================================================

    for worksheet in workbook.worksheets:

        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = (
                get_column_letter(
                    column_cells[0].column
                )
            )

            for cell in column_cells:

                value = (
                    ""
                    if cell.value is None
                    else str(cell.value)
                )

                max_length = max(
                    max_length,
                    len(value)
                )

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 3,
                45
            )

    output = BytesIO()

    workbook.save(
        output
    )

    output.seek(0)

    return output
