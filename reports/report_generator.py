# ============================================================
# ENGINEERING REPORT GENERATOR
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
# HELPERS
# ============================================================

def fmt(value, decimals=3):

    if value is None:
        return "—"

    try:
        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):
        return str(value)


def safe_value(data, *keys):

    if not isinstance(data, dict):
        return None

    for key in keys:

        if key in data:
            value = data[key]

            if value is not None:
                return value

    return None


def safe_sheet_name(name):

    invalid = [
        "\\",
        "/",
        "*",
        "?",
        ":",
        "[",
        "]",
    ]

    result = str(name)

    for char in invalid:
        result = result.replace(
            char,
            "_",
        )

    return result[:31]


# ============================================================
# SUMMARY DATAFRAME
# ============================================================

def create_summary_dataframe(reactors):

    rows = []

    fields = [
        (
            "Working Volume",
            "working_volume_m3",
            "m³",
        ),
        (
            "Vessel Volume",
            "vessel_volume_m3",
            "m³",
        ),
        (
            "Tank Diameter",
            "tank_diameter_m",
            "m",
        ),
        (
            "Straight Height",
            "straight_height_m",
            "m",
        ),
        (
            "Liquid Height",
            "liquid_height_m",
            "m",
        ),
        (
            "Bottom Head",
            "bottom_type",
            "-",
        ),
        (
            "Top Head",
            "top_type",
            "-",
        ),
        (
            "Agitator",
            "agitator",
            "-",
        ),
        (
            "Impeller Diameter",
            "impeller_diameter_m",
            "m",
        ),
        (
            "Number of Impellers",
            "number_impellers",
            "-",
        ),
        (
            "RPM",
            "rpm",
            "RPM",
        ),
        (
            "Baffles",
            "number_baffles",
            "-",
        ),
        (
            "Power",
            "power_kw",
            "kW",
        ),
        (
            "P/V",
            "power_volume_kw_m3",
            "kW/m³",
        ),
        (
            "Tip Speed",
            "tip_speed_m_s",
            "m/s",
        ),
        (
            "Reynolds Number",
            "reynolds_number",
            "-",
        ),
        (
            "Froude Number",
            "froude_number",
            "-",
        ),
        (
            "Pumping Capacity",
            "pumping_capacity_m3_s",
            "m³/s",
        ),
        (
            "Turnover Time",
            "turnover_time_s",
            "s",
        ),
        (
            "Gas Flow",
            "gas_flow_m3_h",
            "m³/h",
        ),
        (
            "Gas Holdup",
            "gas_holdup_fraction",
            "-",
        ),
        (
            "Bubble Diameter",
            "bubble_diameter_mm",
            "mm",
        ),
        (
            "kLa",
            "kLa_1_h",
            "1/h",
        ),
    ]

    for reactor in reactors:

        reactor_name = reactor.get(
            "name",
            "Reactor",
        )

        for label, key, unit in fields:

            value = reactor.get(key)

            rows.append(
                {
                    "Reactor": reactor_name,
                    "Parameter": label,
                    "Value": value,
                    "Unit": unit,
                }
            )

    return pd.DataFrame(rows)


# ============================================================
# WORD REPORT
# ============================================================

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

    section = document.sections[0]

    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = document.add_heading(
        "Reactor Scale-Up Engineering Report",
        level=0,
    )

    title.alignment = 1

    subtitle = document.add_paragraph()

    subtitle.alignment = 1

    run = subtitle.add_run(
        "Engineering Calculation and Scale-Up Study"
    )

    run.bold = True
    run.font.size = Pt(12)

    document.add_paragraph()

    # --------------------------------------------------------
    # PROJECT INFORMATION
    # --------------------------------------------------------

    document.add_heading(
        "1. Project Information",
        level=1,
    )

    info_table = document.add_table(
        rows=5,
        cols=2,
    )

    info_table.style = "Table Grid"

    info_data = [
        (
            "Project Name",
            project_name,
        ),
        (
            "Prepared By",
            prepared_by,
        ),
        (
            "Process Type",
            process_type,
        ),
        (
            "Study Mode",
            study_mode,
        ),
        (
            "Scale-Up Basis",
            scaleup_basis,
        ),
    ]

    for row, (label, value) in zip(
        info_table.rows,
        info_data,
    ):

        row.cells[0].text = str(label)
        row.cells[1].text = str(value)

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    document.add_paragraph(
        "Report Date: "
        + datetime.now().strftime(
            "%d-%b-%Y %H:%M"
        )
    )

    # --------------------------------------------------------
    # EXECUTIVE SUMMARY
    # --------------------------------------------------------

    document.add_heading(
        "2. Reactor Summary",
        level=1,
    )

    summary_df = create_summary_dataframe(
        reactors
    )

    summary_table = document.add_table(
        rows=1,
        cols=4,
    )

    summary_table.style = "Table Grid"

    headers = [
        "Reactor",
        "Parameter",
        "Value",
        "Unit",
    ]

    for index, header in enumerate(headers):

        cell = summary_table.rows[0].cells[index]

        cell.text = header

        for paragraph in cell.paragraphs:

            for run in paragraph.runs:

                run.bold = True

    for _, row_data in summary_df.iterrows():

        cells = summary_table.add_row().cells

        cells[0].text = str(
            row_data["Reactor"]
        )

        cells[1].text = str(
            row_data["Parameter"]
        )

        cells[2].text = fmt(
            row_data["Value"]
        )

        cells[3].text = str(
            row_data["Unit"]
        )

    # --------------------------------------------------------
    # INDIVIDUAL REACTOR DETAILS
    # --------------------------------------------------------

    document.add_heading(
        "3. Reactor Engineering Details",
        level=1,
    )

    for reactor in reactors:

        reactor_name = reactor.get(
            "name",
            "Reactor",
        )

        document.add_heading(
            reactor_name,
            level=2,
        )

        details = [
            (
                "Working Volume",
                safe_value(
                    reactor,
                    "working_volume_m3",
                ),
                "m³",
            ),
            (
                "Vessel Volume",
                safe_value(
                    reactor,
                    "vessel_volume_m3",
                ),
                "m³",
            ),
            (
                "Tank Diameter",
                safe_value(
                    reactor,
                    "tank_diameter_m",
                ),
                "m",
            ),
            (
                "Straight Side Height",
                safe_value(
                    reactor,
                    "straight_height_m",
                ),
                "m",
            ),
            (
                "Liquid Height",
                safe_value(
                    reactor,
                    "liquid_height_m",
                ),
                "m",
            ),
            (
                "Bottom Head",
                safe_value(
                    reactor,
                    "bottom_type",
                ),
                "",
            ),
            (
                "Top Head",
                safe_value(
                    reactor,
                    "top_type",
                ),
                "",
            ),
            (
                "Agitator",
                safe_value(
                    reactor,
                    "agitator",
                ),
                "",
            ),
            (
                "Impeller Diameter",
                safe_value(
                    reactor,
                    "impeller_diameter_m",
                ),
                "m",
            ),
            (
                "Number of Impellers",
                safe_value(
                    reactor,
                    "number_impellers",
                ),
                "",
            ),
            (
                "Agitator Speed",
                safe_value(
                    reactor,
                    "rpm",
                ),
                "RPM",
            ),
            (
                "Number of Baffles",
                safe_value(
                    reactor,
                    "number_baffles",
                ),
                "",
            ),
            (
                "Impeller Clearance",
                safe_value(
                    reactor,
                    "impeller_clearance_m",
                ),
                "m",
            ),
            (
                "Power",
                safe_value(
                    reactor,
                    "power_kw",
                    "power",
                ),
                "kW",
            ),
            (
                "P/V",
                safe_value(
                    reactor,
                    "power_volume_kw_m3",
                    "power_volume",
                ),
                "kW/m³",
            ),
            (
                "Tip Speed",
                safe_value(
                    reactor,
                    "tip_speed_m_s",
                    "tip_speed",
                ),
                "m/s",
            ),
            (
                "Reynolds Number",
                safe_value(
                    reactor,
                    "reynolds_number",
                    "re",
                ),
                "",
            ),
            (
                "Froude Number",
                safe_value(
                    reactor,
                    "froude_number",
                ),
                "",
            ),
        ]

        table = document.add_table(
            rows=1,
            cols=3,
        )

        table.style = "Table Grid"

        table.rows[0].cells[0].text = "Parameter"
        table.rows[0].cells[1].text = "Value"
        table.rows[0].cells[2].text = "Unit"

        for cell in table.rows[0].cells:

            for paragraph in cell.paragraphs:

                for run in paragraph.runs:

                    run.bold = True

        for label, value, unit in details:

            row = table.add_row().cells

            row[0].text = label
            row[1].text = fmt(value)
            row[2].text = unit

        # ----------------------------------------------------
        # GAS LIQUID
        # ----------------------------------------------------

        if process_type in [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ]:

            document.add_paragraph()

            document.add_heading(
                "Gas-Liquid Parameters",
                level=3,
            )

            gas_details = [
                (
                    "Gas Flow",
                    reactor.get(
                        "gas_flow_m3_h"
                    ),
                    "m³/h",
                ),
                (
                    "Superficial Gas Velocity",
                    reactor.get(
                        "superficial_gas_velocity_m_s"
                    ),
                    "m/s",
                ),
                (
                    "Gas Holdup",
                    reactor.get(
                        "gas_holdup_fraction"
                    ),
                    "-",
                ),
                (
                    "Bubble Diameter",
                    reactor.get(
                        "bubble_diameter_mm"
                    ),
                    "mm",
                ),
                (
                    "Bubble Rise Velocity",
                    reactor.get(
                        "bubble_rise_velocity_m_s"
                    ),
                    "m/s",
                ),
                (
                    "Bubble Reynolds Number",
                    reactor.get(
                        "bubble_reynolds_number"
                    ),
                    "-",
                ),
                (
                    "Schmidt Number",
                    reactor.get(
                        "schmidt_number"
                    ),
                    "-",
                ),
                (
                    "Sherwood Number",
                    reactor.get(
                        "sherwood_number"
                    ),
                    "-",
                ),
                (
                    "kL",
                    reactor.get(
                        "kL_m_s"
                    ),
                    "m/s",
                ),
                (
                    "Interfacial Area",
                    reactor.get(
                        "interfacial_area_m2_m3"
                    ),
                    "m²/m³",
                ),
                (
                    "kLa",
                    reactor.get(
                        "kLa_1_h"
                    ),
                    "1/h",
                ),
            ]

            gas_table = document.add_table(
                rows=1,
                cols=3,
            )

            gas_table.style = "Table Grid"

            gas_table.rows[0].cells[0].text = "Parameter"
            gas_table.rows[0].cells[1].text = "Value"
            gas_table.rows[0].cells[2].text = "Unit"

            for cell in gas_table.rows[0].cells:

                for paragraph in cell.paragraphs:

                    for run in paragraph.runs:

                        run.bold = True

            for label, value, unit in gas_details:

                row = gas_table.add_row().cells

                row[0].text = label
                row[1].text = fmt(value)
                row[2].text = unit

    # --------------------------------------------------------
    # SCALE-UP
    # --------------------------------------------------------

    if scaleup_result is not None:

        document.add_heading(
            "4. Scale-Up Analysis",
            level=1,
        )

        if isinstance(
            scaleup_result,
            dict,
        ):

            scale_table = document.add_table(
                rows=1,
                cols=2,
            )

            scale_table.style = "Table Grid"

            scale_table.rows[0].cells[0].text = "Parameter"
            scale_table.rows[0].cells[1].text = "Value"

            for key, value in scaleup_result.items():

                if isinstance(
                    value,
                    (dict, list, tuple),
                ):
                    continue

                row = scale_table.add_row().cells

                row[0].text = str(key)
                row[1].text = fmt(value)

        else:

            document.add_paragraph(
                str(scaleup_result)
            )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    document.add_heading(
        "5. Engineering Validation",
        level=1,
    )

    for reactor in reactors:

        document.add_heading(
            reactor.get(
                "name",
                "Reactor",
            ),
            level=2,
        )

        validation = reactor.get(
            "validation"
        )

        if isinstance(
            validation,
            dict,
        ):

            for key, value in validation.items():

                if isinstance(
                    value,
                    (dict, list, tuple),
                ):
                    continue

                document.add_paragraph(
                    f"{key}: {value}"
                )

        else:

            document.add_paragraph(
                str(validation)
            )

    # --------------------------------------------------------
    # ENGINEERING NOTE
    # --------------------------------------------------------

    document.add_heading(
        "6. Engineering Note",
        level=1,
    )

    document.add_paragraph(
        "The calculations presented in this report are "
        "engineering estimates intended for process design, "
        "scale-up evaluation and comparison. Final equipment "
        "design and specification shall be verified against "
        "project-specific operating conditions, applicable "
        "codes, vendor data, process safety requirements and "
        "mechanical design requirements."
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output = BytesIO()

    document.save(output)

    output.seek(0)

    return output


# ============================================================
# EXCEL REPORT
# ============================================================

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

    # --------------------------------------------------------
    # SUMMARY SHEET
    # --------------------------------------------------------

    summary_sheet = workbook.active

    summary_sheet.title = "Summary"

    summary_sheet["A1"] = (
        "Reactor Scale-Up Engineering Report"
    )

    summary_sheet["A1"].font = Font(
        bold=True,
        size=16,
    )

    summary_sheet["A3"] = "Project Name"
    summary_sheet["B3"] = project_name

    summary_sheet["A4"] = "Prepared By"
    summary_sheet["B4"] = prepared_by

    summary_sheet["A5"] = "Process Type"
    summary_sheet["B5"] = process_type

    summary_sheet["A6"] = "Study Mode"
    summary_sheet["B6"] = study_mode

    summary_sheet["A7"] = "Scale-Up Basis"
    summary_sheet["B7"] = scaleup_basis

    summary_sheet["A8"] = "Report Date"

    summary_sheet["B8"] = datetime.now().strftime(
        "%d-%b-%Y %H:%M"
    )

    summary_df = create_summary_dataframe(
        reactors
    )

    start_row = 11

    for column_index, column_name in enumerate(
        summary_df.columns,
        start=1,
    ):

        cell = summary_sheet.cell(
            row=start_row,
            column=column_index,
            value=column_name,
        )

        cell.font = Font(
            bold=True
        )

    for row_index, row_data in enumerate(
        summary_df.itertuples(
            index=False
        ),
        start=start_row + 1,
    ):

        for column_index, value in enumerate(
            row_data,
            start=1,
        ):

            summary_sheet.cell(
                row=row_index,
                column=column_index,
                value=value,
            )

    # --------------------------------------------------------
    # REACTOR DETAILS SHEETS
    # --------------------------------------------------------

    for reactor in reactors:

        name = reactor.get(
            "name",
            "Reactor",
        )

        sheet = workbook.create_sheet(
            safe_sheet_name(name)
        )

        sheet["A1"] = (
            f"{name} Reactor Engineering Data"
        )

        sheet["A1"].font = Font(
            bold=True,
            size=14,
        )

        details = [
            (
                "Process Type",
                process_type,
                "",
            ),
            (
                "Working Volume",
                reactor.get(
                    "working_volume_m3"
                ),
                "m³",
            ),
            (
                "Vessel Volume",
                reactor.get(
                    "vessel_volume_m3"
                ),
                "m³",
            ),
            (
                "Tank Diameter",
                reactor.get(
                    "tank_diameter_m"
                ),
                "m",
            ),
            (
                "Straight Height",
                reactor.get(
                    "straight_height_m"
                ),
                "m",
            ),
            (
                "Liquid Height",
                reactor.get(
                    "liquid_height_m"
                ),
                "m",
            ),
            (
                "Bottom Head",
                reactor.get(
                    "bottom_type"
                ),
                "",
            ),
            (
                "Top Head",
                reactor.get(
                    "top_type"
                ),
                "",
            ),
            (
                "Density",
                reactor.get(
                    "density_kg_m3"
                ),
                "kg/m³",
            ),
            (
                "Viscosity",
                reactor.get(
                    "viscosity_pa_s"
                ),
                "Pa·s",
            ),
            (
                "Surface Tension",
                reactor.get(
                    "surface_tension_n_m"
                ),
                "N/m",
            ),
            (
                "Agitator",
                reactor.get(
                    "agitator"
                ),
                "",
            ),
            (
                "Impeller Diameter",
                reactor.get(
                    "impeller_diameter_m"
                ),
                "m",
            ),
            (
                "Number of Impellers",
                reactor.get(
                    "number_impellers"
                ),
                "",
            ),
            (
                "RPM",
                reactor.get(
                    "rpm"
                ),
                "RPM",
            ),
            (
                "Number of Baffles",
                reactor.get(
                    "number_baffles"
                ),
                "",
            ),
            (
                "Impeller Clearance",
                reactor.get(
                    "impeller_clearance_m"
                ),
                "m",
            ),
            (
                "Power",
                reactor.get(
                    "power_kw"
                ),
                "kW",
            ),
            (
                "P/V",
                reactor.get(
                    "power_volume_kw_m3"
                ),
                "kW/m³",
            ),
            (
                "Tip Speed",
                reactor.get(
                    "tip_speed_m_s"
                ),
                "m/s",
            ),
            (
                "Reynolds Number",
                reactor.get(
                    "reynolds_number"
                ),
                "",
            ),
            (
                "Froude Number",
                reactor.get(
                    "froude_number"
                ),
                "",
            ),
            (
                "Pumping Capacity",
                reactor.get(
                    "pumping_capacity_m3_s"
                ),
                "m³/s",
            ),
            (
                "Q/V",
                reactor.get(
                    "q_over_v_1_s"
                ),
                "1/s",
            ),
            (
                "Turnover Time",
                reactor.get(
                    "turnover_time_s"
                ),
                "s",
            ),
            (
                "Gas Flow",
                reactor.get(
                    "gas_flow_m3_h"
                ),
                "m³/h",
            ),
            (
                "Gas Holdup",
                reactor.get(
                    "gas_holdup_fraction"
                ),
                "-",
            ),
            (
                "Bubble Diameter",
                reactor.get(
                    "bubble_diameter_mm"
                ),
                "mm",
            ),
            (
                "Superficial Gas Velocity",
                reactor.get(
                    "superficial_gas_velocity_m_s"
                ),
                "m/s",
            ),
            (
                "kLa",
                reactor.get(
                    "kLa_1_h"
                ),
                "1/h",
            ),
        ]

        sheet["A3"] = "Parameter"
        sheet["B3"] = "Value"
        sheet["C3"] = "Unit"

        for cell in sheet[3]:

            cell.font = Font(
                bold=True
            )

        for row_number, detail in enumerate(
            details,
            start=4,
        ):

            label, value, unit = detail

            sheet.cell(
                row=row_number,
                column=1,
                value=label,
            )

            sheet.cell(
                row=row_number,
                column=2,
                value=value,
            )

            sheet.cell(
                row=row_number,
                column=3,
                value=unit,
            )

    # --------------------------------------------------------
    # SCALE-UP SHEET
    # --------------------------------------------------------

    if scaleup_result is not None:

        scale_sheet = workbook.create_sheet(
            "Scale-Up"
        )

        scale_sheet["A1"] = (
            "Scale-Up Analysis"
        )

        scale_sheet["A1"].font = Font(
            bold=True,
            size=14,
        )

        scale_sheet["A3"] = "Parameter"
        scale_sheet["B3"] = "Value"

        scale_sheet["A3"].font = Font(
            bold=True
        )

        scale_sheet["B3"].font = Font(
            bold=True
        )

        if isinstance(
            scaleup_result,
            dict,
        ):

            row_number = 4

            for key, value in scaleup_result.items():

                if isinstance(
                    value,
                    (dict, list, tuple),
                ):
                    continue

                scale_sheet.cell(
                    row=row_number,
                    column=1,
                    value=str(key),
                )

                scale_sheet.cell(
                    row=row_number,
                    column=2,
                    value=value,
                )

                row_number += 1

        else:

            scale_sheet["A4"] = str(
                scaleup_result
            )

    # --------------------------------------------------------
    # VALIDATION SHEET
    # --------------------------------------------------------

    validation_sheet = workbook.create_sheet(
        "Validation"
    )

    validation_sheet["A1"] = (
        "Engineering Validation"
    )

    validation_sheet["A1"].font = Font(
        bold=True,
        size=14,
    )

    validation_sheet["A3"] = "Reactor"
    validation_sheet["B3"] = "Check"
    validation_sheet["C3"] = "Result"

    for cell in validation_sheet[3]:

        cell.font = Font(
            bold=True
        )

    row_number = 4

    for reactor in reactors:

        reactor_name = reactor.get(
            "name",
            "Reactor",
        )

        validation = reactor.get(
            "validation"
        )

        if isinstance(
            validation,
            dict,
        ):

            for key, value in validation.items():

                if isinstance(
                    value,
                    (dict, list, tuple),
                ):
                    continue

                validation_sheet.cell(
                    row=row_number,
                    column=1,
                    value=reactor_name,
                )

                validation_sheet.cell(
                    row=row_number,
                    column=2,
                    value=str(key),
                )

                validation_sheet.cell(
                    row=row_number,
                    column=3,
                    value=value,
                )

                row_number += 1

        else:

            validation_sheet.cell(
                row=row_number,
                column=1,
                value=reactor_name,
            )

            validation_sheet.cell(
                row=row_number,
                column=2,
                value="Validation",
            )

            validation_sheet.cell(
                row=row_number,
                column=3,
                value=str(validation),
            )

            row_number += 1

    # --------------------------------------------------------
    # ASSUMPTIONS
    # --------------------------------------------------------

    assumptions = workbook.create_sheet(
        "Assumptions"
    )

    assumptions["A1"] = (
        "Engineering Assumptions and Notes"
    )

    assumptions["A1"].font = Font(
        bold=True,
        size=14,
    )

    notes = [
        "Results are engineering calculations.",
        "Final equipment design requires engineering verification.",
        "Mechanical design shall be checked against applicable codes.",
        "Agitator and motor selection should be verified with vendor data.",
        "Scale-up criteria should be selected according to process requirements.",
        "Gas-liquid mass transfer correlations depend on system-specific data.",
        "Final process design shall consider process safety requirements.",
    ]

    for index, note in enumerate(
        notes,
        start=3,
    ):

        assumptions.cell(
            row=index,
            column=1,
            value=note,
        )

    # --------------------------------------------------------
    # FORMATTING
    # --------------------------------------------------------

    for sheet in workbook.worksheets:

        for column_cells in sheet.columns:

            max_length = 0

            column_letter = get_column_letter(
                column_cells[0].column
            )

            for cell in column_cells:

                try:

                    cell.alignment = Alignment(
                        vertical="top",
                        wrap_text=True,
                    )

                    value_length = len(
                        str(cell.value)
                    )

                    if value_length > max_length:
                        max_length = value_length

                except Exception:
                    pass

            sheet.column_dimensions[
                column_letter
            ].width = min(
                max(max_length + 2, 12),
                45,
            )

        sheet.freeze_panes = "A3"

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return output
