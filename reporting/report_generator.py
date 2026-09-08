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
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def build_pdf(
    report_data
):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
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
    normal = styles["BodyText"]

    story = []

    process_type = report_data.get(
        "process_type",
        "N/A",
    )

    geometry = report_data.get(
        "geometry",
        {},
    )

    stages = report_data.get(
        "stages",
        [],
    )

    train = report_data.get(
        "train",
        {},
    )

    checks = report_data.get(
        "checks",
        [],
    )

    recommendations = report_data.get(
        "recommendations",
        [],
    )

    story.append(
        Paragraph(
            "Reactor Scale-Up Engineering Report",
            title,
        )
    )

    story.append(
        Spacer(1, 6 * mm)
    )

    story.append(
        Paragraph(
            f"Process requirement: {process_type}",
            normal,
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    # --------------------------------------------------------
    # Geometry
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "1. Reactor Geometry",
            heading,
        )
    )

    geometry_data = [
        ["Parameter", "Value"],

        [
            "Tank diameter",
            f"{_fmt(geometry.get('tank_diameter_m'))} m",
        ],

        [
            "Working volume",
            f"{_fmt(geometry.get('working_volume_m3'))} m³",
        ],

        [
            "Total volume",
            f"{_fmt(geometry.get('total_volume_m3'))} m³",
        ],

        [
            "Liquid height",
            f"{_fmt(geometry.get('liquid_height_m'))} m",
        ],

        [
            "Baffles",
            str(
                geometry.get(
                    "baffles",
                    "N/A",
                )
            ),
        ],
    ]

    table = Table(
        geometry_data,
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
        Spacer(1, 6 * mm)
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "2. Agitator Train",
            heading,
        )
    )

    train_data = [
        [
            "Stage",
            "Agitator",
            "D (m)",
            "RPM",
            "Power (kW)",
            "Q (m³/h)",
            "Re",
            "Tip (m/s)",
        ]
    ]

    for i, stage in enumerate(
        stages,
        1,
    ):

        train_data.append(
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
                    stage.get("power_kw"),
                    3,
                ),
                _fmt(
                    stage.get("Q_m3_h"),
                    2,
                ),
                _fmt(
                    stage.get("Re"),
                    0,
                ),
                _fmt(
                    stage.get(
                        "tip_speed_m_s"
                    ),
                    2,
                ),
            ]
        )

    table = Table(
        train_data,
        repeatRows=1,
        colWidths=[
            12 * mm,
            40 * mm,
            18 * mm,
            18 * mm,
            20 * mm,
            22 * mm,
            20 * mm,
            22 * mm,
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
        Spacer(1, 6 * mm)
    )

    # --------------------------------------------------------
    # Overall performance
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "3. Overall Mixing Performance",
            heading,
        )
    )

    performance_data = [
        [
            "Parameter",
            "Value",
        ],

        [
            "Total power",
            f"{_fmt(train.get('total_power_kw'), 3)} kW",
        ],

        [
            "P/V",
            f"{_fmt(train.get('power_per_volume_W_m3'), 2)} W/m³",
        ],

        [
            "Total Q",
            f"{_fmt(train.get('total_Q_m3_h'), 2)} m³/h",
        ],

        [
            "Q/V",
            f"{_fmt(train.get('Q_per_volume_h'), 2)} h⁻¹",
        ],

        [
            "Turnover time",
            f"{_fmt(train.get('turnover_time_min'), 2)} min",
        ],
    ]

    table = Table(
        performance_data,
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
                    0.4,
                    colors.grey,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        PageBreak()
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "4. Engineering Validation",
            heading,
        )
    )

    validation_data = [
        [
            "Check",
            "Status",
            "Comment",
        ]
    ]

    for item in checks:

        if len(item) >= 3:

            name, ok, message = item[:3]

            validation_data.append(
                [
                    str(name),
                    "PASS" if ok else "REVIEW",
                    str(message),
                ]
            )

    table = Table(
        validation_data,
        repeatRows=1,
        colWidths=[
            55 * mm,
            20 * mm,
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
        Spacer(1, 6 * mm)
    )

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "5. Engineering Recommendations",
            heading,
        )
    )

    for item in recommendations:

        story.append(
            Paragraph(
                f"• {item}",
                normal,
            )
        )

        story.append(
            Spacer(1, 2 * mm)
        )

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            "Calculation Basis & Limitation",
            heading,
        )
    )

    story.append(
        Paragraph(
            "This report is intended for preliminary engineering "
            "screening and scale-up assessment. Mixing correlations, "
            "Np/Nq values and Njs estimates must be validated using "
            "pilot data, vendor data, literature correlations and "
            "detailed mechanical/process design before final equipment release.",
            normal,
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()
