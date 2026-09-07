# ============================================================
# REPORT GENERATOR
# Reactor Scale-Up Engineering Studio
# ============================================================

from io import BytesIO
from datetime import datetime

import pandas as pd

from docx import Document
from docx.shared import Inches, Pt

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_value(value, default=""):
    if value is None:
        return default

    if isinstance(value, float):
        if pd.isna(value):
            return default

    return value


def _fmt(value, decimals=3):
    if value is None:
        return ""

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _safe_sheet_name(name):
    invalid = ['\\', '/', '*', '[', ']', ':', '?']

    result = str(name)

    for char in invalid:
        result = result.replace(char, "_")

    return result[:31]


# ============================================================
# SUMMARY DATAFRAME
# ============================================================

def create_summary_dataframe(reactors):
    rows = []

    for reactor in reactors:
        rows.append(
            {
                "Reactor": reactor.get("name", ""),
                "Working Volume (m3)": reactor.get(
                    "working_volume_m3",
                    reactor.get("working_volume", "")
                ),
                "Vessel Volume (m3)": reactor.get(
                    "vessel_volume_m3",
                    reactor.get("vessel_volume", "")
                ),
                "Tank Diameter (m)": reactor.get(
                    "tank_diameter_m",
                    ""
                ),
                "Straight Height (m)": reactor.get(
                    "straight_height_m",
                    ""
                ),
                "Liquid Height (m)": reactor.get(
                    "liquid_height_m",
                    ""
                ),
                "Agitator": reactor.get(
                    "agitator",
                    ""
                ),
                "Impeller Diameter (m)": reactor.get(
                    "impeller_diameter_m",
                    ""
                ),
                "No. of Impellers": reactor.get(
                    "number_impellers",
                    ""
                ),
                "RPM": reactor.get(
                    "rpm",
                    ""
                ),
                "Power (kW)": reactor.get(
                    "power_kw",
                    reactor.get("power", "")
                ),
                "P/V (kW/m3)": reactor.get(
                    "power_volume_kw_m3",
                    ""
                ),
                "Tip Speed (m/s)": reactor.get(
                    "tip_speed_m_s",
                    ""
                ),
                "Reynolds Number": reactor.get(
                    "reynolds_number",
                    ""
                ),
                "Gas Flow (m3/h)": reactor.get(
                    "gas_flow_m3_h",
                    ""
                ),
                "kLa (1/h)": reactor.get(
                    "kLa_1_h",
                    ""
                ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# WORD REPORT
# ============================================================

def create_word_report(
    project_name="Reactor Scale-Up Study",
    prepared_by="",
    process_type="",
    study_mode="",
    scaleup_basis="",
    reactors=None,
    scaleup_result=None,
):
    if reactors is None:
        reactors = []

    document = Document()

    # --------------------------------------------------------
    # PAGE SETUP
    # --------------------------------------------------------

    section = document.sections[0]

    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    # --------------------------------------------------------
    # DEFAULT FONT
    # --------------------------------------------------------

    styles = document.styles

    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(9)

    styles["Title"].font.name = "Arial"
    styles["Title"].font.size = Pt(20)

    styles["Heading 1"].font.name = "Arial"
    styles["Heading 1"].font.size = Pt(14)

    styles["Heading 2"].font.name = "Arial"
    styles["Heading 2"].font.size = Pt(11)

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = document.add_paragraph()

    title.alignment = 1

    run = title.add_run("REACTOR SCALE-UP ENGINEERING REPORT")
    run.bold = True
    run.font.size = Pt(18)

    subtitle = document.add_paragraph()

    subtitle.alignment = 1

    run = subtitle.add_run(
        str(project_name)
    )

    run.bold = True
    run.font.size = Pt(13)

    document.add_paragraph("")

    # --------------------------------------------------------
    # PROJECT INFORMATION
    # --------------------------------------------------------

    document.add_heading("1. Project Information", level=1)

    info_table = document.add_table(
        rows=0,
        cols=2
    )

    info_table.style = "Table Grid"

    project_info = [
        ("Project Name", project_name),
        ("Prepared By", prepared_by),
        ("Process Type", process_type),
        ("Study Mode", study_mode),
        ("Scale-Up Basis", scaleup_basis),
        (
            "Report Date",
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ),
    ]

    for label, value in project_info:
        cells = info_table.add_row().cells

        cells[0].text = str(label)
        cells[1].text = str(_safe_value(value))

        cells[0].paragraphs[0].runs[0].bold = True

    document.add_paragraph("")

    # --------------------------------------------------------
    # EXECUTIVE SUMMARY
    # --------------------------------------------------------

    document.add_heading("2. Executive Summary", level=1)

    document.add_paragraph(
        "This report summarizes the reactor scale-up "
        "engineering calculations, reactor geometry, "
        "mixing parameters, agitation performance, "
        "gas-liquid parameters where applicable, and "
        "validation checks."
    )

    # --------------------------------------------------------
    # REACTOR SUMMARY
    # --------------------------------------------------------

    document.add_heading("3. Reactor Summary", level=1)

    summary_df = create_summary_dataframe(reactors)

    if not summary_df.empty:

        table = document.add_table(
            rows=1,
            cols=len(summary_df.columns)
        )

        table.style = "Table Grid"

        header_cells = table.rows[0].cells

        for index, column in enumerate(summary_df.columns):

            header_cells[index].text = str(column)

            for run in header_cells[index].paragraphs[0].runs:
                run.bold = True
                run.font.size = Pt(7)

        for _, row in summary_df.iterrows():

            cells = table.add_row().cells

            for index, value in enumerate(row):

                if isinstance(value, (float, int)):
                    text = _fmt(value)
                else:
                    text = str(value)

                cells[index].text = text

                for run in cells[index].paragraphs[0].runs:
                    run.font.size = Pt(7)

    else:
        document.add_paragraph(
            "No reactor calculation data available."
        )

    # --------------------------------------------------------
    # DETAILED REACTOR CALCULATIONS
    # --------------------------------------------------------

    document.add_heading(
        "4. Detailed Reactor Calculations",
        level=1
    )

    fields = [
        ("Working Volume", "working_volume_m3", "m3"),
        ("Vessel Volume", "vessel_volume_m3", "m3"),
        ("Tank Diameter", "tank_diameter_m", "m"),
        ("Straight Height", "straight_height_m", "m"),
        ("Liquid Height", "liquid_height_m", "m"),
        ("Bottom Head", "bottom_type", ""),
        ("Top Head", "top_type", ""),
        ("Density", "density_kg_m3", "kg/m3"),
        ("Viscosity", "viscosity_pa_s", "Pa.s"),
        ("Surface Tension", "surface_tension_n_m", "N/m"),
        ("Agitator", "agitator", ""),
        ("Impeller Diameter", "impeller_diameter_m", "m"),
        ("Number of Impellers", "number_impellers", ""),
        ("RPM", "rpm", "rpm"),
        ("Number of Baffles", "number_baffles", ""),
        ("Impeller Clearance", "impeller_clearance_m", "m"),
        ("Power", "power_kw", "kW"),
        ("Power / Volume", "power_volume_kw_m3", "kW/m3"),
        ("Tip Speed", "tip_speed_m_s", "m/s"),
        ("Reynolds Number", "reynolds_number", ""),
        ("Froude Number", "froude_number", ""),
        ("Pumping Capacity", "pumping_capacity_m3_s", "m3/s"),
        ("Pumping Capacity", "pumping_capacity_m3_h", "m3/h"),
        ("Turnover Time", "turnover_time_min", "min"),
        ("Q/V", "qv_1_s", "1/s"),
        ("Gas Flow", "gas_flow_m3_h", "m3/h"),
        ("Superficial Gas Velocity", "superficial_gas_velocity_m_s", "m/s"),
        ("Gas Holdup", "gas_holdup_fraction", ""),
        ("Bubble Diameter", "bubble_diameter_mm", "mm"),
        ("Bubble Rise Velocity", "bubble_rise_velocity_m_s", "m/s"),
        ("Bubble Reynolds Number", "bubble_reynolds_number", ""),
        ("Schmidt Number", "schmidt_number", ""),
        ("Sherwood Number", "sherwood_number", ""),
        ("Liquid Mass Transfer Coefficient", "kL_m_s", "m/s"),
        ("Interfacial Area", "interfacial_area_m2_m3", "m2/m3"),
        ("kLa", "kLa_1_h", "1/h"),
    ]

    for reactor in reactors:

        name = reactor.get(
            "name",
            "Reactor"
        )

        document.add_heading(
            str(name),
            level=2
        )

        table = document.add_table(
            rows=1,
            cols=3
        )

        table.style = "Table Grid"

        headers = [
            "Parameter",
            "Value",
            "Unit",
        ]

        for i, header in enumerate(headers):
            table.rows[0].cells[i].text = header

            for run in table.rows[0].cells[i].paragraphs[0].runs:
                run.bold = True

        for label, key, unit in fields:

            value = reactor.get(key)

            if value is None:
                continue

            if isinstance(value, (float, int)):
                display_value = _fmt(value)
            else:
                display_value = str(value)

            cells = table.add_row().cells

            cells[0].text = label
            cells[1].text = display_value
            cells[2].text = unit

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    document.add_heading(
        "5. Engineering Validation",
        level=1
    )

    for reactor in reactors:

        name = reactor.get(
            "name",
            "Reactor"
        )

        document.add_heading(
            str(name),
            level=2
        )

        validation = reactor.get(
            "validation",
            {}
        )

        if isinstance(validation, dict) and validation:

            table = document.add_table(
                rows=1,
                cols=3
            )

            table.style = "Table Grid"

            table.rows[0].cells[0].text = "Check"
            table.rows[0].cells[1].text = "Status"
            table.rows[0].cells[2].text = "Details"

            for cell in table.rows[0].cells:
                for run in cell.paragraphs[0].runs:
                    run.bold = True

            for key, value in validation.items():

                if isinstance(value, dict):

                    status = value.get(
                        "status",
                        value.get("result", "")
                    )

                    details = value.get(
                        "message",
                        value.get("details", "")
                    )

                else:

                    status = value
                    details = ""

                cells = table.add_row().cells

                cells[0].text = str(key)
                cells[1].text = str(status)
                cells[2].text = str(details)

        else:

            document.add_paragraph(
                "No validation data available."
            )

    # --------------------------------------------------------
    # SCALE-UP
    # --------------------------------------------------------

    if scaleup_result is not None:

        document.add_heading(
            "6. Scale-Up Analysis",
            level=1
        )

        if isinstance(scaleup_result, dict):

            table = document.add_table(
                rows=1,
                cols=2
            )

            table.style = "Table Grid"

            table.rows[0].cells[0].text = "Parameter"
            table.rows[0].cells[1].text = "Value"

            for cell in table.rows[0].cells:
                for run in cell.paragraphs[0].runs:
                    run.bold = True

            for key, value in scaleup_result.items():

                if isinstance(value, (dict, list, tuple)):
                    value_text = str(value)
                elif isinstance(value, (float, int)):
                    value_text = _fmt(value)
                else:
                    value_text = str(value)

                cells = table.add_row().cells

                cells[0].text = str(key)
                cells[1].text = value_text

    # --------------------------------------------------------
    # ENGINEERING NOTES
    # --------------------------------------------------------

    document.add_heading(
        "7. Engineering Notes",
        level=1
    )

    notes = [
        "Calculated values are based on the input parameters entered in the dashboard.",
        "Final equipment design should be verified against process, mechanical and vendor requirements.",
        "Agitator power and mixing correlations depend on impeller geometry, Reynolds number and vessel configuration.",
        "Gas-liquid calculations are correlation based and should be validated experimentally or using CFD where required.",
        "Scale-up criteria should be selected according to the controlling process requirement.",
    ]

    for note in notes:
        document.add_paragraph(
            note,
            style="List Bullet"
        )

    # --------------------------------------------------------
    # DISCLAIMER
    # --------------------------------------------------------

    document.add_heading(
        "8. Disclaimer",
        level=1
    )

    document.add_paragraph(
        "This report is intended as an engineering calculation "
        "and scale-up aid. It should not replace detailed "
        "process design, mechanical design, HAZOP, equipment "
        "vendor confirmation, laboratory validation, pilot "
        "testing or other required engineering reviews."
    )

    # --------------------------------------------------------
    # SAVE TO MEMORY
    # --------------------------------------------------------

    output = BytesIO()

    document.save(output)

    output.seek(0)

    return output


# ============================================================
# EXCEL REPORT
# ============================================================

def create_excel_report(
    project_name="Reactor Scale-Up Study",
    prepared_by="",
    process_type="",
    study_mode="",
    scaleup_basis="",
    reactors=None,
    scaleup_result=None,
):
    if reactors is None:
        reactors = []

    workbook = Workbook()

    # --------------------------------------------------------
    # SUMMARY SHEET
    # --------------------------------------------------------

    summary_ws = workbook.active
    summary_ws.title = "Summary"

    summary_ws["A1"] = "REACTOR SCALE-UP ENGINEERING REPORT"

    summary_ws["A1"].font = Font(
        bold=True,
        size=16
    )

    summary_ws["A3"] = "Project Name"
    summary_ws["B3"] = project_name

    summary_ws["A4"] = "Prepared By"
    summary_ws["B4"] = prepared_by

    summary_ws["A5"] = "Process Type"
    summary_ws["B5"] = process_type

    summary_ws["A6"] = "Study Mode"
    summary_ws["B6"] = study_mode

    summary_ws["A7"] = "Scale-Up Basis"
    summary_ws["B7"] = scaleup_basis

    summary_ws["A8"] = "Report Date"
    summary_ws["B8"] = datetime.now().strftime(
        "%d-%m-%Y %H:%M"
    )

    for row in range(3, 9):
        summary_ws.cell(
            row=row,
            column=1
        ).font = Font(
            bold=True
        )

    # --------------------------------------------------------
    # REACTOR SUMMARY
    # --------------------------------------------------------

    summary_ws["A10"] = "Reactor Summary"

    summary_ws["A10"].font = Font(
        bold=True,
        size=12
    )

    summary_df = create_summary_dataframe(reactors)

    if not summary_df.empty:

        start_row = 12

        for col_index, column in enumerate(
            summary_df.columns,
            start=1
        ):

            cell = summary_ws.cell(
                row=start_row,
                column=col_index
            )

            cell.value = column

            cell.font = Font(
                bold=True
            )

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )

        for row_index, row in enumerate(
            summary_df.itertuples(index=False),
            start=start_row + 1
        ):

            for col_index, value in enumerate(
                row,
                start=1
            ):

                summary_ws.cell(
                    row=row_index,
                    column=col_index,
                    value=value
                )

    # --------------------------------------------------------
    # REACTOR DETAIL SHEETS
    # --------------------------------------------------------

    fields = [
        ("Working Volume", "working_volume_m3", "m3"),
        ("Vessel Volume", "vessel_volume_m3", "m3"),
        ("Tank Diameter", "tank_diameter_m", "m"),
        ("Straight Height", "straight_height_m", "m"),
        ("Liquid Height", "liquid_height_m", "m"),
        ("Bottom Head", "bottom_type", ""),
        ("Top Head", "top_type", ""),
        ("Density", "density_kg_m3", "kg/m3"),
        ("Viscosity", "viscosity_pa_s", "Pa.s"),
        ("Surface Tension", "surface_tension_n_m", "N/m"),
        ("Agitator", "agitator", ""),
        ("Impeller Diameter", "impeller_diameter_m", "m"),
        ("Number of Impellers", "number_impellers", ""),
        ("RPM", "rpm", "rpm"),
        ("Number of Baffles", "number_baffles", ""),
        ("Impeller Clearance", "impeller_clearance_m", "m"),
        ("Power", "power_kw", "kW"),
        ("Power / Volume", "power_volume_kw_m3", "kW/m3"),
        ("Tip Speed", "tip_speed_m_s", "m/s"),
        ("Reynolds Number", "reynolds_number", ""),
        ("Froude Number", "froude_number", ""),
        ("Pumping Capacity", "pumping_capacity_m3_s", "m3/s"),
        ("Pumping Capacity", "pumping_capacity_m3_h", "m3/h"),
        ("Turnover Time", "turnover_time_min", "min"),
        ("Q/V", "qv_1_s", "1/s"),
        ("Gas Flow", "gas_flow_m3_h", "m3/h"),
        ("Superficial Gas Velocity", "superficial_gas_velocity_m_s", "m/s"),
        ("Gas Holdup", "gas_holdup_fraction", ""),
        ("Bubble Diameter", "bubble_diameter_mm", "mm"),
        ("Bubble Rise Velocity", "bubble_rise_velocity_m_s", "m/s"),
        ("Bubble Reynolds Number", "bubble_reynolds_number", ""),
        ("Schmidt Number", "schmidt_number", ""),
        ("Sherwood Number", "sherwood_number", ""),
        ("Liquid Mass Transfer Coefficient", "kL_m_s", "m/s"),
        ("Interfacial Area", "interfacial_area_m2_m3", "m2/m3"),
        ("kLa", "kLa_1_h", "1/h"),
    ]

    for reactor in reactors:

        name = reactor.get(
            "name",
            "Reactor"
        )

        sheet_name = _safe_sheet_name(
            str(name)
        )

        if sheet_name in workbook.sheetnames:
            sheet_name = _safe_sheet_name(
                str(name) + "_Detail"
            )

        ws = workbook.create_sheet(
            title=sheet_name
        )

        ws["A1"] = str(name)

        ws["A1"].font = Font(
            bold=True,
            size=14
        )

        ws["A3"] = "Parameter"
        ws["B3"] = "Value"
        ws["C3"] = "Unit"

        for cell in ws[3]:
            cell.font = Font(
                bold=True
            )

        row_number = 4

        for label, key, unit in fields:

            value = reactor.get(key)

            if value is None:
                continue

            ws.cell(
                row=row_number,
                column=1,
                value=label
            )

            ws.cell(
                row=row_number,
                column=2,
                value=value
            )

            ws.cell(
                row=row_number,
                column=3,
                value=unit
            )

            row_number += 1

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        row_number += 2

        ws.cell(
            row=row_number,
            column=1,
            value="Engineering Validation"
        )

        ws.cell(
            row=row_number,
            column=1
        ).font = Font(
            bold=True,
            size=12
        )

        row_number += 2

        ws.cell(
            row=row_number,
            column=1,
            value="Check"
        )

        ws.cell(
            row=row_number,
            column=2,
            value="Status"
        )

        ws.cell(
            row=row_number,
            column=3,
            value="Details"
        )

        for col in range(1, 4):
            ws.cell(
                row=row_number,
                column=col
            ).font = Font(
                bold=True
            )

        row_number += 1

        validation = reactor.get(
            "validation",
            {}
        )

        if isinstance(validation, dict):

            for key, value in validation.items():

                if isinstance(value, dict):

                    status = value.get(
                        "status",
                        value.get(
                            "result",
                            ""
                        )
                    )

                    details = value.get(
                        "message",
                        value.get(
                            "details",
                            ""
                        )
                    )

                else:

                    status = value
                    details = ""

                ws.cell(
                    row=row_number,
                    column=1,
                    value=str(key)
                )

                ws.cell(
                    row=row_number,
                    column=2,
                    value=str(status)
                )

                ws.cell(
                    row=row_number,
                    column=3,
                    value=str(details)
                )

                row_number += 1

        # ----------------------------------------------------
        # COLUMN WIDTHS
        # ----------------------------------------------------

        ws.column_dimensions["A"].width = 32
        ws.column_dimensions["B"].width = 24
        ws.column_dimensions["C"].width = 18

    # --------------------------------------------------------
    # SCALE-UP SHEET
    # --------------------------------------------------------

    if scaleup_result is not None:

        ws = workbook.create_sheet(
            title="Scale-Up"
        )

        ws["A1"] = "Scale-Up Analysis"

        ws["A1"].font = Font(
            bold=True,
            size=14
        )

        ws["A3"] = "Parameter"
        ws["B3"] = "Value"

        ws["A3"].font = Font(
            bold=True
        )

        ws["B3"].font = Font(
            bold=True
        )

        row_number = 4

        if isinstance(scaleup_result, dict):

            for key, value in scaleup_result.items():

                ws.cell(
                    row=row_number,
                    column=1,
                    value=str(key)
                )

                ws.cell(
                    row=row_number,
                    column=2,
                    value=value
                )

                row_number += 1

        ws.column_dimensions["A"].width = 35
        ws.column_dimensions["B"].width = 35

    # --------------------------------------------------------
    # ASSUMPTIONS
    # --------------------------------------------------------

    ws = workbook.create_sheet(
        title="Assumptions"
    )

    ws["A1"] = "Engineering Assumptions"

    ws["A1"].font = Font(
        bold=True,
        size=14
    )

    assumptions = [
        "Values are calculated from dashboard input parameters.",
        "Mixing correlations depend on impeller geometry and operating regime.",
        "Gas-liquid calculations are correlation based.",
        "Scale-up basis should be selected according to the controlling process requirement.",
        "Final equipment design requires process and mechanical engineering verification.",
        "Vendor confirmation should be obtained for final agitator and drive selection.",
        "CFD or pilot testing may be required for critical mixing applications.",
    ]

    for index, assumption in enumerate(
        assumptions,
        start=3
    ):

        ws.cell(
            row=index,
            column=1,
            value=assumption
        )

    ws.column_dimensions["A"].width = 100

    # --------------------------------------------------------
    # GENERAL FORMATTING
    # --------------------------------------------------------

    for ws in workbook.worksheets:

        for row in ws.iter_rows():

            for cell in row:

                cell.alignment = Alignment(
                    vertical="center"
                )

        ws.freeze_panes = "A3"

    # --------------------------------------------------------
    # SAVE TO MEMORY
    # --------------------------------------------------------

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return output
