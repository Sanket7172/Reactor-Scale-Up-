"""
Engineering PDF report generator.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def _fmt(value, digits=3):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def build_pdf(data):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title = styles["Title"]
    heading = styles["Heading2"]
    body = styles["BodyText"]

    story = []

    story.append(
        Paragraph(
            "Reactor Scale-Up Engineering Report",
            title,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            "Preliminary engineering / scale-up screening report",
            body,
        )
    )

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "1. Design Basis",
            heading,
        )
    )

    story.append(
        Paragraph(
            f"Process type: {data.get('process_type', 'N/A')}",
            body,
        )
    )

    story.append(
        Paragraph(
            f"Study mode: {data.get('study_mode', 'N/A')}",
            body,
        )
    )

    story.append(
        Paragraph(
            f"Scale-up basis: {data.get('scaleup_basis', 'N/A')}",
            body,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    geom = data.get(
        "geometry",
        {},
    )

    story.append(
        Paragraph(
            "2. Reactor Geometry",
            heading,
        )
    )

    geometry_table = [
        ["Parameter", "Value"],
        [
            "Working Volume",
            f"{_fmt(geom.get('working_volume_m3'))} m³",
        ],
        [
            "Total Vessel Volume",
            f"{_fmt(geom.get('total_volume_m3'))} m³",
        ],
        [
            "Tank Diameter",
            f"{_fmt(geom.get('tank_diameter_m'))} m",
        ],
        [
            "Straight Side",
            f"{_fmt(geom.get('straight_height_m'))} m",
        ],
        [
            "Liquid Height",
            f"{_fmt(geom.get('liquid_height_m'))} m",
        ],
        [
            "Fill",
            f"{_fmt(geom.get('fill_percent'), 1)} %",
        ],
        [
            "Baffles",
            str(geom.get("baffles", "N/A")),
        ],
    ]

    table = Table(
        geometry_table,
        colWidths=[
            75 * mm,
            80 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#17233c"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "3. Agitator Train",
            heading,
        )
    )

    stages = data.get(
        "stages",
        [],
    )

    stage_table = [
        [
            "Stage",
            "Agitator",
            "D (m)",
            "RPM",
            "Re",
            "P (kW)",
            "Q (m³/h)",
            "P/V",
            "Tip",
            "Njs",
            "N/Njs",
        ]
    ]

    for i, stage in enumerate(
        stages,
        start=1,
    ):
        njs = stage.get(
            "njs_rpm",
            None,
        )

        ratio = (
            stage.get("rpm", 0.0) / njs
            if njs and njs > 0
            else None
        )

        stage_table.append(
            [
                str(i),
                stage.get(
                    "agitator",
                    "N/A",
                ),
                _fmt(
                    stage.get(
                        "impeller_diameter_m"
                    ),
                    3,
                ),
                _fmt(
                    stage.get("rpm"),
                    1,
                ),
                _fmt(
                    stage.get("Re"),
                    0,
                ),
                _fmt(
                    stage.get("power_kw"),
                    3,
                ),
                _fmt(
                    stage.get("Q_m3_h"),
                    2,
                ),
                _fmt(
                    stage.get(
                        "power_per_volume_kw_m3"
                    ),
                    3,
                ),
                _fmt(
                    stage.get(
                        "tip_speed_m_s"
                    ),
                    2,
                ),
                _fmt(
                    njs,
                    1,
                ),
                _fmt(
                    ratio,
                    2,
                ),
            ]
        )

    table = Table(
        stage_table,
        repeatRows=1,
        colWidths=[
            9 * mm,
            34 * mm,
            17 * mm,
            17 * mm,
            20 * mm,
            18 * mm,
            24 * mm,
            18 * mm,
            17 * mm,
            18 * mm,
            18 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#17233c"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 12)
    )

    train = data.get(
        "train",
        {},
    )

    story.append(
        Paragraph(
            "4. Agitation Summary",
            heading,
        )
    )

    summary = [
        [
            "Total Shaft Power",
            f"{_fmt(train.get('total_power_kw'), 3)} kW",
        ],
        [
            "Total Pumping",
            f"{_fmt(train.get('total_Q_m3_h'), 2)} m³/h",
        ],
        [
            "P/V",
            f"{_fmt(train.get('P_per_V_kW_m3'), 3)} kW/m³",
        ],
        [
            "Q/V",
            f"{_fmt(train.get('Q_per_volume_1_s'), 5)} s⁻¹",
        ],
        [
            "Turnover Time",
            f"{_fmt(train.get('turnover_time_min'), 3)} min",
        ],
        [
            "System Njs",
            f"{_fmt(train.get('system_Njs_rpm'), 1)} RPM",
        ],
        [
            "Average Tip Speed",
            f"{_fmt(train.get('average_tip_speed_m_s'), 2)} m/s",
        ],
    ]

    table = Table(
        summary,
        colWidths=[
            80 * mm,
            75 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "5. Engineering Validation",
            heading,
        )
    )

    checks = data.get(
        "checks",
        [],
    )

    validation_table = [
        [
            "Status",
            "Engineering Check",
        ]
    ]

    for check in checks:
        validation_table.append(
            [
                check.get(
                    "severity",
                    "REVIEW",
                ),
                check.get(
                    "message",
                    "",
                ),
            ]
        )

    table = Table(
        validation_table,
        colWidths=[
            30 * mm,
            125 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#17233c"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "6. Engineering Recommendation",
            heading,
        )
    )

    for recommendation in data.get(
        "recommendations",
        [],
    ):
        story.append(
            Paragraph(
                f"• {recommendation}",
                body,
            )
        )

        story.append(
            Spacer(1, 4)
        )

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "Engineering limitation: This report is a preliminary "
            "engineering screening document. Np/Nq, Njs, blend time, "
            "kLa, heat transfer and mechanical design must be validated "
            "using applicable literature, vendor data, pilot trials, "
            "plant data and detailed mechanical/process design.",
            body,
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()
