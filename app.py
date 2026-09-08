```python
import copy
import math
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# APPLICATION PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ENGINEERING MODULES
# ============================================================

try:

    from calculations.engine import calculate_reactor

    from calculations.scaleup import calculate_scaleup

    from calculations.validation import validate_reactor

    from libraries.agitator_geometry import AGITATORS

    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )

    from visualization.reactor_3d import (
        create_reactor_animation,
    )

    from reporting.report_generator import (
        create_word_report,
        create_excel_report,
    )

except Exception as e:

    st.error("Engineering module loading failed.")

    st.code(
        f"{type(e).__name__}: {e}"
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "reactor_inputs": None,
    "reactor_result": None,
    "active_page": "Overview",
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# ENGINEERING COLORS / CSS
# ============================================================

st.markdown(
    """
<style>

/* =========================================================
   GLOBAL
   ========================================================= */

:root {
    --bg: #0b1118;
    --panel: #111a24;
    --panel-2: #16212d;
    --border: #263545;
    --text: #edf3f8;
    --muted: #8fa1b3;
    --accent: #4cc9f0;
    --success: #35d07f;
    --warning: #f5b942;
    --danger: #ff5c5c;
}

html,
body,
[data-testid="stAppViewContainer"] {

    background:
        radial-gradient(
            circle at 15% 10%,
            rgba(76, 201, 240, 0.055),
            transparent 28%
        ),
        radial-gradient(
            circle at 85% 20%,
            rgba(80, 120, 255, 0.035),
            transparent 30%
        ),
        var(--bg);

    color: var(--text);
}


/* =========================================================
   MAIN CONTENT
   ========================================================= */

.block-container {

    max-width: 1500px;

    padding-top: 1.4rem;
    padding-bottom: 3rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            #0c141d 0%,
            #0a1118 100%
        );

    border-right: 1px solid var(--border);
}


[data-testid="stSidebar"] * {

    color: var(--text);
}


/* =========================================================
   HEADER
   ========================================================= */

.engineering-header {

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 1.25rem 1.5rem;

    margin-bottom: 1.25rem;

    background:
        linear-gradient(
            135deg,
            rgba(22, 33, 45, 0.95),
            rgba(13, 22, 31, 0.95)
        );

    border: 1px solid var(--border);

    border-radius: 16px;

    box-shadow:
        0 12px 35px rgba(0, 0, 0, 0.20);
}


.engineering-title {

    font-size: 1.65rem;

    font-weight: 750;

    letter-spacing: -0.03em;

    color: #f4f8fb;
}


.engineering-subtitle {

    margin-top: 0.2rem;

    font-size: 0.82rem;

    color: var(--muted);
}


/* =========================================================
   SECTION HEADINGS
   ========================================================= */

.section-heading {

    display: flex;

    align-items: center;

    gap: 0.65rem;

    margin-top: 1.25rem;

    margin-bottom: 0.8rem;

    font-size: 1.05rem;

    font-weight: 700;

    color: var(--text);
}


.section-heading-line {

    width: 4px;

    height: 22px;

    border-radius: 5px;

    background: var(--accent);
}


/* =========================================================
   KPI CARDS
   ========================================================= */

.kpi-card {

    min-height: 125px;

    padding: 1rem 1.05rem;

    background:
        linear-gradient(
            145deg,
            rgba(22, 33, 45, 0.98),
            rgba(14, 23, 32, 0.98)
        );

    border: 1px solid var(--border);

    border-radius: 14px;

    transition:
        transform 0.15s ease,
        border-color 0.15s ease;
}


.kpi-card:hover {

    transform: translateY(-2px);

    border-color:
        rgba(76, 201, 240, 0.45);
}


.kpi-label {

    color: var(--muted);

    font-size: 0.74rem;

    text-transform: uppercase;

    letter-spacing: 0.08em;

    font-weight: 650;
}


.kpi-value {

    margin-top: 0.45rem;

    font-size: 1.55rem;

    font-weight: 750;

    color: #f5f8fa;
}


.kpi-unit {

    font-size: 0.75rem;

    color: var(--muted);

    margin-left: 0.25rem;
}


.kpi-note {

    margin-top: 0.35rem;

    font-size: 0.72rem;

    color: var(--muted);
}


/* =========================================================
   STATUS
   ========================================================= */

.status-pass {

    display: inline-flex;

    align-items: center;

    gap: 0.4rem;

    padding: 0.3rem 0.65rem;

    border-radius: 999px;

    background: rgba(53, 208, 127, 0.10);

    border: 1px solid rgba(53, 208, 127, 0.25);

    color: var(--success);

    font-size: 0.75rem;

    font-weight: 700;
}


.status-review {

    display: inline-flex;

    align-items: center;

    gap: 0.4rem;

    padding: 0.3rem 0.65rem;

    border-radius: 999px;

    background: rgba(245, 185, 66, 0.10);

    border: 1px solid rgba(245, 185, 66, 0.25);

    color: var(--warning);

    font-size: 0.75rem;

    font-weight: 700;
}


.status-risk {

    display: inline-flex;

    align-items: center;

    gap: 0.4rem;

    padding: 0.3rem 0.65rem;

    border-radius: 999px;

    background: rgba(255, 92, 92, 0.10);

    border: 1px solid rgba(255, 92, 92, 0.25);

    color: var(--danger);

    font-size: 0.75rem;

    font-weight: 700;
}


/* =========================================================
   ENGINEERING PANEL
   ========================================================= */

.engineering-panel {

    padding: 1rem 1.15rem;

    background:
        rgba(17, 26, 36, 0.90);

    border: 1px solid var(--border);

    border-radius: 14px;

    margin-bottom: 0.8rem;
}


.panel-title {

    font-size: 0.9rem;

    font-weight: 700;

    margin-bottom: 0.7rem;
}


.panel-subtitle {

    font-size: 0.75rem;

    color: var(--muted);
}


/* =========================================================
   COMPARISON
   ========================================================= */

.comparison-card {

    padding: 1rem;

    background: rgba(17, 26, 36, 0.88);

    border: 1px solid var(--border);

    border-radius: 14px;
}


.comparison-title {

    font-size: 0.78rem;

    color: var(--muted);

    text-transform: uppercase;

    letter-spacing: 0.08em;
}


.comparison-value {

    margin-top: 0.35rem;

    font-size: 1.35rem;

    font-weight: 750;
}


/* =========================================================
   ENGINEERING CONCLUSION
   ========================================================= */

.conclusion-box {

    padding: 1.2rem 1.3rem;

    margin-top: 1rem;

    border-radius: 15px;

    background:
        linear-gradient(
            135deg,
            rgba(20, 38, 50, 0.98),
            rgba(13, 24, 34, 0.98)
        );

    border: 1px solid
        rgba(76, 201, 240, 0.22);
}


.conclusion-title {

    font-size: 0.82rem;

    color: var(--accent);

    text-transform: uppercase;

    letter-spacing: 0.1em;

    font-weight: 750;
}


.conclusion-text {

    margin-top: 0.55rem;

    font-size: 0.95rem;

    line-height: 1.55;

    color: #dce6ed;
}


/* =========================================================
   NAVIGATION
   ========================================================= */

.nav-caption {

    margin-top: 0.9rem;

    margin-bottom: 0.4rem;

    color: #6f8497;

    font-size: 0.67rem;

    text-transform: uppercase;

    letter-spacing: 0.12em;

    font-weight: 700;
}


/* =========================================================
   INPUT GROUP
   ========================================================= */

.input-group {

    padding: 0.85rem;

    background: rgba(17, 26, 36, 0.55);

    border: 1px solid rgba(38, 53, 69, 0.7);

    border-radius: 12px;

    margin-bottom: 0.8rem;
}


/* =========================================================
   DATAFRAME
   ========================================================= */

[data-testid="stDataFrame"] {

    border-radius: 12px;

    overflow: hidden;
}


/* =========================================================
   BUTTONS
   ========================================================= */

.stButton > button {

    border-radius: 10px;

    font-weight: 650;

    border: 1px solid var(--border);
}


.stButton > button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #149ec1,
            #277bc2
        );

    border: none;
}


/* =========================================================
   DIVIDER
   ========================================================= */

hr {

    border-color: var(--border);
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 900px) {

    .block-container {

        padding-left: 1rem;
        padding-right: 1rem;

    }

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def sf(value, default=0.0):

    try:

        if value is None:
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):

        return default


def fmt(value, digits=3):

    if value is None:
        return "—"

    try:

        value = float(value)

        if not math.isfinite(value):
            return "—"

        return f"{value:,.{digits}f}"

    except (TypeError, ValueError):

        return str(value)


def safe_dataframe(data):

    if data is None:
        return pd.DataFrame()

    if isinstance(data, pd.DataFrame):

        df = data.copy()

    else:

        try:

            df = pd.DataFrame(data)

        except Exception:

            return pd.DataFrame()

    return df


def engineering_metric(
    label,
    value,
    unit="",
    note="",
):

    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">
            {value}
            <span class="kpi-unit">{unit}</span>
        </div>
        <div class="kpi-note">{note}</div>
    </div>
    """


def section_heading(title):

    st.markdown(
        f"""
        <div class="section-heading">
            <div class="section-heading-line"></div>
            <div>{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status):

    status = str(status).upper()

    if status in ("PASS", "OK", "ACCEPTABLE"):

        return (
            '<span class="status-pass">'
            '● PASS'
            '</span>'
        )

    if status in ("REVIEW", "WARNING"):

        return (
            '<span class="status-review">'
            '● REVIEW'
            '</span>'
        )

    return (
        '<span class="status-risk">'
        '● RISK'
        '</span>'
    )


# ============================================================
# AGITATOR CONFIGURATION
# ============================================================

POSITIONS = [
    "Bottom",
    "Middle",
    "Top",
]


def agitator_names():

    return [
        name
        for name, data in AGITATORS.items()
        if isinstance(data, dict)
    ]


# ============================================================
# IMPELLER ELEVATION
# ============================================================

def calculate_elevations(
    impellers,
    liquid_height,
    tank_diameter,
):

    H = sf(
        liquid_height,
        0.10,
    )

    T = sf(
        tank_diameter,
        1.0,
    )

    output = []

    for impeller in impellers:

        item = copy.deepcopy(
            impeller
        )

        position = item.get(
            "position",
            "Bottom",
        )

        clearance = max(
            0.0,
            sf(
                item.get(
                    "bottom_clearance_m"
                ),
                0.20 * T,
            ),
        )

        if position == "Bottom":

            elevation = clearance

        elif position == "Middle":

            elevation = 0.50 * H

        else:

            elevation = 0.75 * H

        elevation = min(
            elevation,
            max(
                0.05,
                H - 0.05,
            ),
        )

        item["elevation_m"] = elevation

        output.append(item)

    output.sort(
        key=lambda x:
        sf(
            x.get(
                "elevation_m"
            )
        )
    )

    return output


# ============================================================
# IMPELLER VALIDATION
# ============================================================

def validate_impellers(
    impellers,
    liquid_height,
    tank_diameter,
):

    messages = []

    H = sf(liquid_height)
    T = sf(tank_diameter)

    if not impellers:

        return [
            (
                "ERROR",
                "At least one impeller is required.",
            )
        ]

    elevations = []

    for i, impeller in enumerate(
        impellers,
        1,
    ):

        D = sf(
            impeller.get(
                "diameter_m"
            )
        )

        elevation = sf(
            impeller.get(
                "elevation_m"
            )
        )

        clearance = sf(
            impeller.get(
                "bottom_clearance_m"
            )
        )

        if D <= 0:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: diameter must be greater than zero.",
                )
            )

        if T > 0 and D >= T:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: diameter must be smaller than tank ID.",
                )
            )

        if H > 0 and elevation >= H:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: elevation is above liquid level.",
                )
            )

        if clearance < 0:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: clearance cannot be negative.",
                )
            )

        elevations.append(elevation)

    rounded = [
        round(value, 4)
        for value in elevations
    ]

    if len(rounded) != len(set(rounded)):

        messages.append(
            (
                "WARNING",
                "Two or more impellers have identical elevations.",
            )
        )

    if not messages:

        messages.append(
            (
                "OK",
                "Impeller arrangement is internally consistent.",
            )
        )

    return messages


# ============================================================
# REACTOR INPUT PAGE
# ============================================================

def reactor_design_page():

    section_heading(
        "Process & Reactor Definition"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        working_volume = st.number_input(
            "Working Volume",
            min_value=0.01,
            value=10.0,
            step=0.5,
            format="%.2f",
            key="working_volume",
        )

        density = st.number_input(
            "Liquid Density",
            min_value=0.1,
            value=1000.0,
            step=10.0,
            format="%.1f",
            key="density",
        )

        viscosity_cp = st.number_input(
            "Viscosity",
            min_value=0.001,
            value=1.0,
            step=0.1,
            format="%.3f",
            key="viscosity_cp",
        )

    with c2:

        tank_D = st.number_input(
            "Tank ID",
            min_value=0.10,
            value=2.0,
            step=0.05,
            format="%.3f",
            key="tank_D",
        )

        straight_height = st.number_input(
            "Straight Side Height",
            min_value=0.10,
            value=3.0,
            step=0.10,
            format="%.2f",
            key="straight_height",
        )

        surface_tension = st.number_input(
            "Surface Tension",
            min_value=0.1,
            value=30.0,
            step=1.0,
            format="%.2f",
            key="surface_tension",
        )

    with c3:

        rpm = st.number_input(
            "Agitator Speed",
            min_value=0.1,
            value=100.0,
            step=5.0,
            format="%.1f",
            key="rpm",
        )

        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=3,
            value=1,
            step=1,
            key="number_impellers",
        )

        number_baffles = st.number_input(
            "Number of Baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
            key="number_baffles",
        )

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    section_heading(
        "Vessel Geometry"
    )

    head_names = list(
        REACTOR_HEADS.keys()
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        bottom_type = st.selectbox(
            "Bottom Head",
            head_names,
            key="bottom_type",
        )

    with c2:

        top_type = st.selectbox(
            "Top Head",
            head_names,
            key="top_type",
        )

    try:

        vessel_volume = calculate_total_volume(
            tank_D,
            straight_height,
            bottom_type,
            top_type,
        )

    except Exception as e:

        vessel_volume = 0.0

        st.error(
            f"Geometry calculation failed: {e}"
        )

    try:

        liquid_height = liquid_height_from_volume(
            working_volume,
            tank_D,
            straight_height,
            bottom_type,
            top_type,
        )

    except Exception:

        liquid_height = min(
            straight_height,
            working_volume
            / (
                math.pi
                * tank_D**2
                / 4.0
            ),
        )

    with c3:

        st.markdown(
            engineering_metric(
                "Estimated Vessel Volume",
                fmt(vessel_volume, 2),
                "m³",
                "Calculated from vessel geometry",
            ),
            unsafe_allow_html=True,
        )

    if vessel_volume > 0:

        fill_ratio = (
            working_volume
            / vessel_volume
        )

        if working_volume > vessel_volume:

            st.error(
                "Working volume exceeds calculated vessel volume."
            )

        elif fill_ratio > 0.90:

            st.warning(
                "Working volume exceeds 90% of vessel volume. "
                "Check freeboard."
            )

    st.caption(
        f"Calculated liquid height: "
        f"{fmt(liquid_height, 3)} m"
    )

    # --------------------------------------------------------
    # AGITATOR
    # --------------------------------------------------------

    section_heading(
        "Agitator Configuration"
    )

    names = agitator_names()

    if not names:

        st.error(
            "No agitators found in agitator_geometry.py."
        )

        st.stop()

    impellers = []

    for i in range(
        int(number_impellers)
    ):

        with st.container(border=True):

            st.markdown(
                f"**Impeller {i + 1}**"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                position = st.selectbox(
                    "Position",
                    POSITIONS,
                    index=min(
                        i,
                        len(POSITIONS) - 1,
                    ),
                    key=f"position_{i}",
                )

            with c2:

                agitator = st.selectbox(
                    "Impeller Type",
                    names,
                    key=f"agitator_{i}",
                )

            with c3:

                max_D = max(
                    0.02,
                    0.95 * tank_D,
                )

                default_D = max(
                    0.05,
                    min(
                        0.50 * tank_D,
                        max_D,
                    ),
                )

                D = st.number_input(
                    "Impeller Diameter",
                    min_value=0.01,
                    max_value=max_D,
                    value=default_D,
                    step=0.05,
                    key=f"D_{i}",
                )

            with c4:

                max_clearance = max(
                    0.05,
                    liquid_height,
                )

                default_clearance = min(
                    0.20 * tank_D,
                    max_clearance,
                )

                clearance = st.number_input(
                    "Bottom Clearance",
                    min_value=0.0,
                    max_value=max_clearance,
                    value=default_clearance,
                    step=0.05,
                    key=f"C_{i}",
                )

            impellers.append(
                {
                    "position": position,
                    "agitator_type": agitator,
                    "type": agitator,
                    "diameter_m": D,
                    "D": D,
                    "bottom_clearance_m": clearance,
                }
            )

    impellers = calculate_elevations(
        impellers,
        liquid_height,
        tank_D,
    )

    messages = validate_impellers(
        impellers,
        liquid_height,
        tank_D,
    )

    for level, message in messages:

        if level == "ERROR":
            st.error(message)

        elif level == "WARNING":
            st.warning(message)

        else:
            st.success(message)

    # --------------------------------------------------------
    # PROCESS CLASSIFICATION
    # --------------------------------------------------------

    section_heading(
        "Process Classification"
    )

    process_type = st.selectbox(
        "Primary Process Type",
        [
            "Liquid–Liquid",
            "Solid–Liquid",
            "Gas–Liquid",
            "Gas–Liquid–Solid",
            "Crystallization",
            "High Viscosity",
            "Heat Transfer Controlled",
            "General Blending",
        ],
        key="process_type",
    )

    # --------------------------------------------------------
    # SOLID SYSTEM
    # --------------------------------------------------------

    solids_active = process_type in [
        "Solid–Liquid",
        "Gas–Liquid–Solid",
        "Crystallization",
    ]

    solid_data = {}

    if solids_active:

        with st.container(border=True):

            st.markdown(
                "**Solid Suspension Inputs**"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                solids_wt = st.number_input(
                    "Solids Loading (wt%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=10.0,
                    step=1.0,
                    key="solids_wt",
                )

            with c2:

                particle_size = st.number_input(
                    "Particle Size (µm)",
                    min_value=0.1,
                    value=150.0,
                    step=10.0,
                    key="particle_size",
                )

            with c3:

                solid_density = st.number_input(
                    "Solid Density (kg/m³)",
                    min_value=1.0,
                    value=1800.0,
                    step=50.0,
                    key="solid_density",
                )

            with c4:

                solids_settling_factor = st.number_input(
                    "Suspension Correlation Factor",
                    min_value=0.01,
                    value=1.0,
                    step=0.05,
                    key="solids_settling_factor",
                )

            solid_data = {
                "solids_wt_percent": solids_wt,
                "particle_size_um": particle_size,
                "solid_density_kg_m3": solid_density,
                "suspension_factor": solids_settling_factor,
            }

    # --------------------------------------------------------
    # GAS-LIQUID
    # --------------------------------------------------------

    gas_active = process_type in [
        "Gas–Liquid",
        "Gas–Liquid–Solid",
    ]

    gas_flow = 0.0
    bubble_diameter = 3.0
    gas_holdup = 0.05

    if gas_active:

        with st.container(border=True):

            st.markdown(
                "**Gas–Liquid Inputs**"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                gas_flow = st.number_input(
                    "Gas Flow (m³/h)",
                    min_value=0.001,
                    value=10.0,
                    step=1.0,
                    key="gas_flow",
                )

            with c2:

                bubble_diameter = st.number_input(
                    "Bubble Diameter (mm)",
                    min_value=0.1,
                    value=3.0,
                    step=0.5,
                    key="bubble_diameter",
                )

            with c3:

                gas_holdup = st.number_input(
                    "Gas Holdup Fraction",
                    min_value=0.001,
                    max_value=0.50,
                    value=0.05,
                    step=0.01,
                    key="gas_holdup",
                )

    return {

        "process_type":
            process_type,

        "working_volume_m3":
            working_volume,

        "volume_m3":
            working_volume,

        "tank_diameter_m":
            tank_D,

        "diameter_m":
            tank_D,

        "straight_height_m":
            straight_height,

        "liquid_height_m":
            liquid_height,

        "density_kg_m3":
            density,

        "viscosity_cp":
            viscosity_cp,

        "viscosity_pa_s":
            viscosity_cp * 0.001,

        "surface_tension_mN_m":
            surface_tension,

        "surface_tension_n_m":
            surface_tension * 0.001,

        "rpm":
            rpm,

        "number_impellers":
            int(number_impellers),

        "number_baffles":
            int(number_baffles),

        "bottom_type":
            bottom_type,

        "top_type":
            top_type,

        "vessel_volume_m3":
            vessel_volume,

        "impellers":
            impellers,

        "agitator":
            impellers[0]["agitator_type"],

        "impeller_diameter_m":
            impellers[0]["diameter_m"],

        "impeller_clearance_m":
            impellers[0]["bottom_clearance_m"],

        "gas_flow_m3_h":
            gas_flow,

        "bubble_diameter_mm":
            bubble_diameter,

        "gas_holdup_fraction":
            gas_holdup,

        **solid_data,
    }


# ============================================================
# ENGINE ADAPTER
# ============================================================

def run_calculation(inputs):

    primary = inputs["impellers"][0]

    result = calculate_reactor(

        volume_m3=inputs[
            "working_volume_m3"
        ],

        tank_diameter_m=inputs[
            "tank_diameter_m"
        ],

        liquid_height_m=inputs[
            "liquid_height_m"
        ],

        density_kg_m3=inputs[
            "density_kg_m3"
        ],

        viscosity_pa_s=inputs[
            "viscosity_pa_s"
        ],

        surface_tension_n_m=inputs[
            "surface_tension_n_m"
        ],

        rpm=inputs[
            "rpm"
        ],

        impeller_diameter_m=primary[
            "diameter_m"
        ],

        number_impellers=inputs[
            "number_impellers"
        ],

        agitator=primary[
            "agitator_type"
        ],

        impeller_clearance_m=primary[
            "bottom_clearance_m"
        ],

        gas_flow_m3_h=inputs[
            "gas_flow_m3_h"
        ],

        bubble_diameter_mm=inputs[
            "bubble_diameter_mm"
        ],

        gas_holdup_fraction=inputs[
            "gas_holdup_fraction"
        ],
    )

    result.update(
        {

            "process_type":
                inputs["process_type"],

            "rpm":
                inputs["rpm"],

            "straight_height_m":
                inputs[
                    "straight_height_m"
                ],

            "bottom_type":
                inputs["bottom_type"],

            "top_type":
                inputs["top_type"],

            "number_baffles":
                inputs["number_baffles"],

            "vessel_volume_m3":
                inputs[
                    "vessel_volume_m3"
                ],

            "impellers":
                copy.deepcopy(
                    inputs["impellers"]
                ),

            "working_volume_m3":
                inputs[
                    "working_volume_m3"
                ],

            "viscosity_cp":
                inputs["viscosity_cp"],

            "surface_tension_mN_m":
                inputs[
                    "surface_tension_mN_m"
                ],

            "density_kg_m3":
                inputs[
                    "density_kg_m3"
                ],

            "gas_flow_m3_h":
                inputs[
                    "gas_flow_m3_h"
                ],

            "bubble_diameter_mm":
                inputs[
                    "bubble_diameter_mm"
                ],

            "gas_holdup_fraction":
                inputs[
                    "gas_holdup_fraction"
                ],

        }
    )

    return result


# ============================================================
# OVERVIEW
# ============================================================

def overview_page(result):

    section_heading(
        "Scale-Up Engineering Overview"
    )

    process_type = result.get(
        "process_type",
        "General Blending",
    )

    st.markdown(
        f"""
        <div class="engineering-panel">
            <div class="panel-title">
                {process_type}
            </div>
            <div class="panel-subtitle">
                Reactor scale-up engineering workspace
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # KPI ROW
    # --------------------------------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        st.markdown(
            engineering_metric(
                "Working Volume",
                fmt(
                    result.get(
                        "working_volume_m3"
                    ),
                    2,
                ),
                "m³",
                "Design basis",
            ),
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            engineering_metric(
                "Agitator Speed",
                fmt(
                    result.get(
                        "rpm"
                    ),
                    1,
                ),
                "RPM",
                "Operating condition",
            ),
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            engineering_metric(
                "Tip Speed",
                fmt(
                    result.get(
                        "tip_speed"
                    ),
                    2,
                ),
                "m/s",
                "Impeller peripheral speed",
            ),
            unsafe_allow_html=True,
        )

    with c4:

        st.markdown(
            engineering_metric(
                "Specific Power",
                fmt(
                    result.get(
                        "power_volume_kw_m3"
                    ),
                    3,
                ),
                "kW/m³",
                "Power density",
            ),
            unsafe_allow_html=True,
        )

    with c5:

        st.markdown(
            engineering_metric(
                "Reynolds",
                fmt(
                    result.get(
                        "reynolds_number"
                    ),
                    0,
                ),
                "",
                "Mixing regime indicator",
            ),
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # REACTOR / ENGINEERING STATUS
    # --------------------------------------------------------

    section_heading(
        "Engineering Status"
    )

    c1, c2 = st.columns(
        [1.45, 1],
        gap="large",
    )

    with c1:

        st.markdown(
            """
            <div class="engineering-panel">
                <div class="panel-title">
                    Reactor Design Basis
                </div>
            """,
            unsafe_allow_html=True,
        )

        data = [

            {
                "Parameter":
                    "Working Volume",
                "Value":
                    fmt(
                        result.get(
                            "working_volume_m3"
                        ),
                        3,
                    ),
                "Unit":
                    "m³",
            },

            {
                "Parameter":
                    "Vessel Volume",
                "Value":
                    fmt(
                        result.get(
                            "vessel_volume_m3"
                        ),
                        3,
                    ),
                "Unit":
                    "m³",
            },

            {
                "Parameter":
                    "Tank ID",
                "Value":
                    fmt(
                        result.get(
                            "tank_diameter_m"
                        ),
                        3,
                    ),
                "Unit":
                    "m",
            },

            {
                "Parameter":
                    "Liquid Height",
                "Value":
                    fmt(
                        result.get(
                            "liquid_height_m"
                        ),
                        3,
                    ),
                "Unit":
                    "m",
            },

            {
                "Parameter":
                    "D/T",
                "Value":
                    fmt(
                        result.get(
                            "D_T"
                        ),
                        3,
                    ),
                "Unit":
                    "-",
            },

            {
                "Parameter":
                    "H/T",
                "Value":
                    fmt(
                        result.get(
                            "H_T"
                        ),
                        3,
                    ),
                "Unit":
                    "-",
            },

            {
                "Parameter":
                    "Baffles",
                "Value":
                    fmt(
                        result.get(
                            "number_baffles"
                        ),
                        0,
                    ),
                "Unit":
                    "No.",
            },

        ]

        st.dataframe(
            safe_dataframe(data),
            width="stretch",
            hide_index=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="engineering-panel">
                <div class="panel-title">
                    Primary Engineering Indicators
                </div>
            """,
            unsafe_allow_html=True,
        )

        indicators = [

            (
                "Geometry",
                "PASS",
            ),

            (
                "Mixing",
                "PASS",
            ),

            (
                "Agitator",
                "PASS",
            ),

        ]

        if process_type in [
            "Solid–Liquid",
            "Gas–Liquid–Solid",
            "Crystallization",
        ]:

            indicators.append(
                (
                    "Suspension",
                    "REVIEW",
                )
            )

        if process_type in [
            "Gas–Liquid",
            "Gas–Liquid–Solid",
        ]:

            indicators.append(
                (
                    "Gas Dispersion",
                    "REVIEW",
                )
            )

        indicators.append(
            (
                "Heat Transfer",
                "REVIEW",
            )
        )

        for name, status in indicators:

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:0.48rem 0;
                    border-bottom:1px solid #243342;
                ">
                    <span>{name}</span>
                    {status_badge(status)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # ENGINEERING CONCLUSION
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="conclusion-box">
            <div class="conclusion-title">
                Engineering Interpretation
            </div>
            <div class="conclusion-text">
                The current design basis is ready for
                scale-up evaluation. Final scale-up selection
                should be based on the process mechanism and
                validated engineering correlations rather than
                a single parameter such as RPM.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MIXING PAGE
# ============================================================

def mixing_page(result):

    section_heading(
        "Mixing Performance"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            engineering_metric(
                "Reynolds Number",
                fmt(
                    result.get(
                        "reynolds_number"
                    ),
                    0,
                ),
                "",
                "Flow regime",
            ),
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            engineering_metric(
                "Tip Speed",
                fmt(
                    result.get(
                        "tip_speed"
                    ),
                    2,
                ),
                "m/s",
                "Impeller speed",
            ),
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            engineering_metric(
                "Power",
                fmt(
                    result.get(
                        "power_kw"
                    ),
                    2,
                ),
                "kW",
                "Agitator power",
            ),
            unsafe_allow_html=True,
        )

    with c4:

        st.markdown(
            engineering_metric(
                "P/V",
                fmt(
                    result.get(
                        "power_volume_kw_m3"
                    ),
                    3,
                ),
                "kW/m³",
                "Specific power",
            ),
            unsafe_allow_html=True,
        )

    section_heading(
        "Mixing Parameters"
    )

    data = [

        {
            "Parameter": "Power",
            "Value": result.get("power_kw"),
            "Unit": "kW",
        },

        {
            "Parameter": "Specific Power",
            "Value": result.get(
                "power_volume_kw_m3"
            ),
            "Unit": "kW/m³",
        },

        {
            "Parameter": "Torque",
            "Value": result.get(
                "torque_nm"
            ),
            "Unit": "N·m",
        },

        {
            "Parameter": "Pumping Capacity",
            "Value": result.get(
                "pumping_m3_h"
            ),
            "Unit": "m³/h",
        },

        {
            "Parameter": "Q/V",
            "Value": result.get(
                "pumping_per_volume_h"
            ),
            "Unit": "1/h",
        },

        {
            "Parameter": "Turnover Time",
            "Value": result.get(
                "turnover_time_min"
            ),
            "Unit": "min",
        },

        {
            "Parameter": "Froude Number",
            "Value": result.get(
                "froude_number"
            ),
            "Unit": "-",
        },

        {
            "Parameter": "Mixing Regime",
            "Value": result.get(
                "mixing_regime"
            ),
            "Unit": "-",
        },

    ]

    st.dataframe(
        safe_dataframe(data),
        width="stretch",
        hide_index=True,
    )

    with st.expander(
        "Calculation Basis",
        expanded=False,
    ):

        st.write(
            """
            Mixing calculations should use consistent SI
            units. RPM is converted to revolutions per second
            where required. Reynolds number, power, pumping,
            specific power, tip speed and Froude number should
            be interpreted together rather than independently.
            """
        )


# ============================================================
# IMPELLER PAGE
# ============================================================

def agitator_page(result):

    section_heading(
        "Agitator & Impeller Arrangement"
    )

    impellers = result.get(
        "impellers",
        [],
    )

    if not impellers:

        st.warning(
            "No impeller configuration available."
        )

        return

    tank_D = sf(
        result.get(
            "tank_diameter_m"
        )
    )

    rows = []

    for i, imp in enumerate(
        impellers,
        1,
    ):

        D = sf(
            imp.get(
                "diameter_m"
            )
        )

        agitator = imp.get(
            "agitator_type",
            "Unknown",
        )

        data = AGITATORS.get(
            agitator,
            {},
        )

        rows.append(
            {
                "Impeller":
                    f"I-{i}",

                "Position":
                    imp.get(
                        "position"
                    ),

                "Agitator":
                    agitator,

                "Flow Type":
                    data.get(
                        "flow_type",
                        "",
                    ),

                "Diameter":
                    D,

                "D/T":
                    (
                        D / tank_D
                        if tank_D > 0
                        else None
                    ),

                "Elevation":
                    imp.get(
                        "elevation_m"
                    ),

                "Clearance":
                    imp.get(
                        "bottom_clearance_m"
                    ),

                "Np":
                    data.get(
                        "np"
                    ),

                "Nq":
                    data.get(
                        "nq"
                    ),

            }
        )

    st.dataframe(
        safe_dataframe(rows),
        width="stretch",
        hide_index=True,
    )

    section_heading(
        "Impeller Elevation"
    )

    chart = pd.DataFrame(
        {
            "Impeller":
                [
                    row["Impeller"]
                    for row in rows
                ],

            "Elevation (m)":
                [
                    sf(
                        row["Elevation"]
                    )
                    for row in rows
                ],
        }
    )

    st.bar_chart(
        chart.set_index(
            "Impeller"
        )
    )

    with st.expander(
        "Agitator Engineering Basis",
        expanded=False,
    ):

        st.write(
            """
            Impeller selection should be driven by process
            duty, required flow pattern, viscosity, solids
            suspension, gas dispersion requirement and heat
            transfer requirement. Np and Nq are impeller-specific
            parameters and should not be treated as universal
            constants.
            """
        )


# ============================================================
# SCALE-UP PAGE
# ============================================================

def scaleup_page(result):

    section_heading(
        "Scale-Up Engine"
    )

    st.markdown(
        """
        <div class="engineering-panel">
            <div class="panel-title">
                Pilot → Commercial Scale-Up
            </div>
            <div class="panel-subtitle">
                Select the governing scale-up criterion and
                evaluate secondary engineering parameters.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        V1 = st.number_input(
            "Reference Volume (m³)",
            min_value=0.01,
            value=1.0,
            step=0.1,
            key="scale_v1",
        )

    with c2:

        V2 = st.number_input(
            "Target Volume (m³)",
            min_value=0.01,
            value=float(
                result.get(
                    "volume_m3",
                    10.0,
                )
            ),
            step=0.5,
            key="scale_v2",
        )

    with c3:

        basis = st.selectbox(
            "Scale-Up Basis",
            [
                "Constant P/V",
                "Constant Tip Speed",
                "Constant RPM",
                "Constant Q/V",
                "Constant Froude",
                "Constant N/Njs",
                "Constant kLa",
                "User Defined",
            ],
            key="scale_basis",
        )

    if V1 > 0:

        scale_factor = V2 / V1

    else:

        scale_factor = 0.0

    st.markdown(
        engineering_metric(
            "Geometric Scale Factor",
            fmt(scale_factor, 2),
            "×",
            "Target volume / reference volume",
        ),
        unsafe_allow_html=True,
    )

    try:

        output = calculate_scaleup(

            reference_volume=V1,

            target_volume=V2,

            basis=basis,

            reference_diameter=sf(
                result.get(
                    "tank_diameter_m"
                )
            ),

            reference_rpm=sf(
                result.get(
                    "rpm"
                )
            ),

            reference_power_per_volume=sf(
                result.get(
                    "power_volume_kw_m3"
                )
            ),

            reference_tip_speed=sf(
                result.get(
                    "tip_speed"
                )
            ),

        )

        section_heading(
            "Scale-Up Calculation"
        )

        if isinstance(
            output,
            dict,
        ):

            rows = [

                {
                    "Parameter":
                        key,

                    "Result":
                        value,

                }

                for key, value
                in output.items()

            ]

        else:

            rows = output

        st.dataframe(
            safe_dataframe(rows),
            width="stretch",
            hide_index=True,
        )

    except Exception as e:

        st.error(
            "Scale-up calculation failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )

    with st.expander(
        "Scale-Up Engineering Philosophy",
        expanded=False,
    ):

        st.write(
            """
            No single scale-up criterion is universally
            applicable. The governing criterion should be
            selected according to the process mechanism.

            Examples:

            • Liquid–Liquid → blend time / Q/V

            • Solid–Liquid → N/Njs

            • Gas–Liquid → kLa / gas dispersion

            • Gas–Liquid–Solid → N/Njs + kLa

            • High viscosity → torque / P/V

            • Heat-transfer-controlled → heat-transfer capacity

            Secondary criteria should always be checked.
            """
        )


# ============================================================
# SOLID SUSPENSION PAGE
# ============================================================

def solid_suspension_page(result):

    section_heading(
        "Solid Suspension"
    )

    process_type = result.get(
        "process_type",
        "",
    )

    if process_type not in [
        "Solid–Liquid",
        "Gas–Liquid–Solid",
        "Crystallization",
    ]:

        st.info(
            "Solid suspension analysis is not active for "
            "the selected process type."
        )

        return

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            engineering_metric(
                "Solids Loading",
                fmt(
                    result.get(
                        "solids_wt_percent",
                        0.0,
                    ),
                    1,
                ),
                "wt%",
                "Process input",
            ),
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            engineering_metric(
                "Particle Size",
                fmt(
                    result.get(
                        "particle_size_um",
                        0.0,
                    ),
                    0,
                ),
                "µm",
                "Characteristic size",
            ),
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            engineering_metric(
                "Solid Density",
                fmt(
                    result.get(
                        "solid_density_kg_m3",
                        0.0,
                    ),
                    0,
                ),
                "kg/m³",
                "Particle density",
            ),
            unsafe_allow_html=True,
        )

    with c4:

        st.markdown(
            engineering_metric(
                "Operating RPM",
                fmt(
                    result.get(
                        "rpm"
                    ),
                    1,
                ),
                "RPM",
                "Agitator speed",
            ),
            unsafe_allow_html=True,
        )

    st.warning(
        """
        Njs must be calculated using the selected
        correlation and validated against the actual
        impeller/system. The screening result should not
        be interpreted as a universal design limit.
        """
    )

    if "njs_rpm" in result:

        njs = sf(
            result.get(
                "njs_rpm"
            )
        )

        rpm = sf(
            result.get(
                "rpm"
            )
        )

        if njs > 0:

            ratio = rpm / njs

            st.markdown(
                engineering_metric(
                    "N / Njs",
                    fmt(ratio, 2),
                    "",
                    "Operating speed / just-suspended speed",
                ),
                unsafe_allow_html=True,
            )

            st.metric(
                "Njs",
                f"{fmt(njs, 1)} RPM",
            )

    else:

        st.info(
            "Njs result is not currently returned by engine.py. "
            "The scale-up engine should expose Njs and N/Njs "
            "for solid-liquid scale-up."
        )


# ============================================================
# GAS-LIQUID PAGE
# ============================================================

def gas_liquid_page(result):

    section_heading(
        "Gas–Liquid Mass Transfer"
    )

    process_type = result.get(
        "process_type",
        "",
    )

    if process_type not in [
        "Gas–Liquid",
        "Gas–Liquid–Solid",
    ]:

        st.info(
            "Gas–liquid analysis is not active for the "
            "selected process type."
        )

        return

    data = [

        (
            "Gas Flow",
            result.get(
                "gas_flow_m3_h"
            ),
            "m³/h",
        ),

        (
            "Superficial Velocity",
            result.get(
                "gas_superficial_velocity_m_s"
            ),
            "m/s",
        ),

        (
            "Gas Holdup",
            result.get(
                "gas_holdup_fraction"
            ),
            "-",
        ),

        (
            "Bubble Diameter",
            result.get(
                "bubble_diameter_m"
            ),
            "m",
        ),

        (
            "Bubble Rise Velocity",
            result.get(
                "bubble_rise_velocity_m_s"
            ),
            "m/s",
        ),

        (
            "Bubble Residence Time",
            result.get(
                "bubble_residence_time_s"
            ),
            "s",
        ),

        (
            "Bubble Reynolds",
            result.get(
                "bubble_reynolds"
            ),
            "-",
        ),

        (
            "Schmidt Number",
            result.get(
                "schmidt_number"
            ),
            "-",
        ),

        (
            "Sherwood Number",
            result.get(
                "sherwood_number"
            ),
            "-",
        ),

        (
            "kL",
            result.get(
                "kL_m_s"
            ),
            "m/s",
        ),

        (
            "Interfacial Area",
            result.get(
                "interfacial_area_m2_m3"
            ),
            "m²/m³",
        ),

        (
            "kLa",
            result.get(
                "kLa_1_h"
            ),
            "1/h",
        ),

    ]

    rows = [

        {
            "Parameter":
                parameter,

            "Value":
                value,

            "Unit":
                unit,

        }

        for parameter, value, unit
        in data

    ]

    st.dataframe(
        safe_dataframe(rows),
        width="stretch",
        hide_index=True,
    )

    st.warning(
        """
        Gas–liquid calculations are screening-level
        estimates. kLa, gas holdup, bubble size and
        dispersion behaviour should be validated using
        appropriate pilot data, literature correlations
        or vendor data.
        """
    )


# ============================================================
# HEAT TRANSFER PAGE
# ============================================================

def heat_transfer_page(result):

    section_heading(
        "Heat Transfer"
    )

    # Try several common result-key names so the UI remains
    # compatible with different versions of heat_transfer.py.

    hta = result.get(
        "hta_m2",
        result.get(
            "HTA_m2",
            result.get(
                "heat_transfer_area_m2"
            ),
        ),
    )

    U = result.get(
        "U_W_m2_K",
        result.get(
            "overall_heat_transfer_coefficient"
        ),
    )

    lmtd = result.get(
        "lmtd_C",
        result.get(
            "LMTD_C"
        ),
    )

    available = result.get(
        "available_heat_removal_kw",
        result.get(
            "heat_removal_capacity_kw"
        ),
    )

    required = result.get(
        "required_heat_duty_kw",
        result.get(
            "reaction_heat_kw"
        ),
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            engineering_metric(
                "Heat Transfer Area",
                fmt(hta, 2),
                "m²",
                "Available HTA",
            ),
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            engineering_metric(
                "Overall U",
                fmt(U, 1),
                "W/m²K",
                "Overall heat-transfer coefficient",
            ),
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            engineering_metric(
                "LMTD",
                fmt(lmtd, 2),
                "°C",
                "Log mean temperature difference",
            ),
            unsafe_allow_html=True,
        )

    with c4:

        st.markdown(
            engineering_metric(
                "Available Duty",
                fmt(available, 1),
                "kW",
                "Calculated capacity",
            ),
            unsafe_allow_html=True,
        )

    section_heading(
        "Thermal Balance"
    )

    data = [

        {
            "Parameter":
                "Heat Transfer Area",

            "Value":
                hta,

            "Unit":
                "m²",
        },

        {
            "Parameter":
                "Overall U",

            "Value":
                U,

            "Unit":
                "W/m²K",
        },

        {
            "Parameter":
                "LMTD",

            "Value":
                lmtd,

            "Unit":
                "°C",
        },

        {
            "Parameter":
                "Available Heat Removal",

            "Value":
                available,

            "Unit":
                "kW",
        },

        {
            "Parameter":
                "Required Heat Duty",

            "Value":
                required,

            "Unit":
                "kW",
        },

    ]

    st.dataframe(
        safe_dataframe(data),
        width="stretch",
        hide_index=True,
    )

    if (
        available is not None
        and required is not None
        and sf(required) > 0
    ):

        margin = (
            sf(available)
            - sf(required)
        )

        margin_pct = (
            margin
            / sf(required)
            * 100
        )

        if margin >= 0:

            st.success(
                f"Calculated heat-transfer margin: "
                f"{fmt(margin, 1)} kW "
                f"({fmt(margin_pct, 1)}%)"
            )

        else:

            st.error(
                f"Calculated heat-transfer deficit: "
                f"{fmt(abs(margin), 1)} kW"
            )

    else:

        st.info(
            "Heat-transfer result data are not currently "
            "available from the active calculation engine."
        )


# ============================================================
# VALIDATION PAGE
# ============================================================

def validation_page(result):

    section_heading(
        "Engineering Validation"
    )

    try:

        output = validate_reactor(
            result
        )

        df = safe_dataframe(
            output
        )

        if df.empty:

            st.info(
                "No validation results were returned."
            )

            return

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
        )

    except Exception as e:

        st.error(
            "Validation failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )

    st.markdown(
        """
        <div class="conclusion-box">
            <div class="conclusion-title">
                Validation Philosophy
            </div>
            <div class="conclusion-text">
                Validation is intended to identify engineering
                inconsistencies and scale-up risks. It does not
                replace mechanical design, equipment vendor
                verification, HAZOP, process safety assessment,
                CFD or validated pilot/plant correlations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 3D REACTOR PAGE
# ============================================================

def three_d_page(result):

    section_heading(
        "Interactive Reactor Model"
    )

    st.caption(
        "Engineering visualization of vessel geometry, "
        "internals and selected mixing / gas-liquid layers."
    )

    view_mode = st.radio(
        "Visualization Mode",
        [
            "Equipment",
            "Cutaway",
            "Mixing",
            "Gas-Liquid",
            "Complete",
            "Custom",
        ],
        horizontal=True,
        key="reactor_3d_view_mode",
    )

    feature_library = [

        "Reactor Geometry",
        "Liquid Level",
        "Impeller & Shaft",
        "Baffles",
        "Vortex Formation",
        "Velocity Profile",
        "Flow Profile",
        "Dead Zone Analysis",
        "Mixing Particles",
        "Gas-Liquid Bubbles",
        "Dimensions",

    ]

    if view_mode in [
        "Equipment",
        "Cutaway",
    ]:

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Dimensions",
        ]

    elif view_mode == "Mixing":

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Vortex Formation",
            "Velocity Profile",
            "Flow Profile",
            "Dead Zone Analysis",
            "Mixing Particles",
        ]

    elif view_mode == "Gas-Liquid":

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Gas-Liquid Bubbles",
            "Flow Profile",
        ]

    elif view_mode == "Complete":

        selected_features = feature_library

    else:

        selected_features = st.multiselect(
            "Visualization Layers",
            feature_library,
            default=[
                "Reactor Geometry",
                "Liquid Level",
                "Impeller & Shaft",
            ],
            key="custom_3d_features",
        )

    if not selected_features:

        st.warning(
            "Select at least one visualization layer."
        )

        return

    with st.expander(
        "Display Settings",
        expanded=False,
    ):

        c1, c2, c3 = st.columns(3)

        with c1:

            show_animation = st.checkbox(
                "Rotation animation",
                value=False,
                key="show_3d_animation",
            )

        with c2:

            transparent_shell = st.checkbox(
                "Transparent vessel",
                value=True,
                key="transparent_shell",
            )

        with c3:

            engineering_axes = st.checkbox(
                "Engineering axes",
                value=True,
                key="engineering_axes",
            )

    working_volume = sf(
        result.get(
            "working_volume_m3",
            result.get(
                "volume_m3",
                10.0,
            ),
        ),
        10.0,
    )

    tank_diameter = sf(
        result.get(
            "tank_diameter_m",
            2.0,
        ),
        2.0,
    )

    straight_height = sf(
        result.get(
            "straight_height_m",
            3.0,
        ),
        3.0,
    )

    liquid_height = result.get(
        "liquid_height_m",
        None,
    )

    rpm = sf(
        result.get(
            "rpm",
            100.0,
        ),
        100.0,
    )

    impellers = result.get(
        "impellers",
        [],
    )

    bottom_type = result.get(
        "bottom_type",
        "10% Torispherical",
    )

    top_type = result.get(
        "top_type",
        "10% Torispherical",
    )

    number_baffles = int(
        sf(
            result.get(
                "number_baffles",
                4,
            ),
            4,
        )
    )

    density = sf(
        result.get(
            "density_kg_m3",
            1000.0,
        ),
        1000.0,
    )

    viscosity = sf(
        result.get(
            "viscosity_pa_s",
            0.001,
        ),
        0.001,
    )

    gas_flow = sf(
        result.get(
            "gas_flow_m3_h",
            0.0,
        ),
        0.0,
    )

    bubble_diameter = sf(
        result.get(
            "bubble_diameter_mm",
            3.0,
        ),
        3.0,
    )

    primary = (
        impellers[0]
        if impellers
        else {}
    )

    agitator = primary.get(
        "agitator_type",
        result.get(
            "agitator",
            "Rushton Turbine",
        ),
    )

    impeller_D = sf(
        primary.get(
            "diameter_m",
            result.get(
                "impeller_diameter_m",
                tank_diameter * 0.5,
            ),
        ),
        tank_diameter * 0.5,
    )

    clearance = sf(
        primary.get(
            "bottom_clearance_m",
            result.get(
                "impeller_clearance_m",
                0.4,
            ),
        ),
        0.4,
    )

    st.caption(
        "Active layers: "
        + ", ".join(
            selected_features
        )
    )

    try:

        fig = create_reactor_animation(

            volume_m3=working_volume,

            tank_diameter_m=tank_diameter,

            straight_height_m=straight_height,

            liquid_height_m=liquid_height,

            rpm=rpm,

            impellers=impellers,

            bottom_type=bottom_type,

            top_type=top_type,

            number_baffles=number_baffles,

            density_kg_m3=density,

            viscosity_pa_s=viscosity,

            gas_flow_m3_h=gas_flow,

            bubble_diameter_mm=bubble_diameter,

            selected_features=selected_features,

            D=tank_diameter,

            H=straight_height,

            volume=working_volume,

            liquid_level=liquid_height,

            agitator=agitator,

            impeller_diameter_m=impeller_D,

            number_impellers=len(
                impellers
            )
            if impellers
            else 1,

            impeller_clearance_m=clearance,

        )

        st.plotly_chart(

            fig,

            width="stretch",

            config={
                "displaylogo": False,
                "responsive": True,
                "scrollZoom": True,
                "displayModeBar": True,
                "displayModeBarButtonsToAdd": [
                    "resetCameraDefault3d",
                    "resetCameraLastSave3d",
                ],
            },

        )

    except Exception as e:

        st.error(
            "3D reactor visualization failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )

    st.caption(
        "Visualization note: flow, velocity, vortex, "
        "dead-zone and particle layers are engineering "
        "screening visualizations and are not a substitute "
        "for validated CFD."
    )


# ============================================================
# REPORT PAGE
# ============================================================

def reports_page(
    inputs,
    result,
):

    section_heading(
        "Engineering Report"
    )

    if inputs is None:

        st.info(
            "Run the reactor calculation before generating reports."
        )

        return

    st.markdown(
        """
        <div class="engineering-panel">
            <div class="panel-title">
                Scale-Up Engineering Documentation
            </div>
            <div class="panel-subtitle">
                Export the current engineering basis and
                calculation results.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:

        try:

            word_file = create_word_report(
                inputs,
                result,
            )

            st.download_button(
                "Download Word Engineering Report",
                data=word_file.getvalue(),
                file_name="reactor_scaleup_engineering_report.docx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                width="stretch",
            )

        except Exception as e:

            st.error(
                "Word report generation failed."
            )

            st.code(
                f"{type(e).__name__}: {e}"
            )

    with c2:

        try:

            excel_file = create_excel_report(
                inputs,
                result,
            )

            st.download_button(
                "Download Excel Engineering Report",
                data=excel_file.getvalue(),
                file_name="reactor_scaleup_engineering_report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
            )

        except Exception as e:

            st.error(
                "Excel report generation failed."
            )

            st.code(
                f"{type(e).__name__}: {e}"
            )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            padding:0.5rem 0 0.8rem 0;
        ">
            <div style="
                font-size:1.35rem;
                font-weight:800;
            ">
                ⚗️ Scale-Up Studio
            </div>

            <div style="
                font-size:0.72rem;
                color:#8fa1b3;
                margin-top:0.2rem;
            ">
                Process Engineering Workspace
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        '<div class="nav-caption">Workspace</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Engineering Workspace",
        [
            "Overview",
            "01  Reactor Design",
            "02  Agitator",
            "03  Mixing",
            "04  Scale-Up",
            "05  Solid Suspension",
            "06  Gas–Liquid",
            "07  Heat Transfer",
            "08  Validation",
            "09  3D Reactor",
            "10  Engineering Report",
        ],
        label_visibility="collapsed",
        key="active_page",
    )

    st.divider()

    stored_result = st.session_state.get(
        "reactor_result"
    )

    if stored_result is not None:

        st.markdown(
            '<div class="nav-caption">Current Design</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            f"Process: "
            f"{stored_result.get('process_type', '—')}"
        )

        st.caption(
            f"Volume: "
            f"{fmt(stored_result.get('working_volume_m3'), 2)} m³"
        )

        st.caption(
            f"RPM: "
            f"{fmt(stored_result.get('rpm'), 1)}"
        )

    st.divider()

    st.caption(
        "Engineering screening tool. Final equipment "
        "design must be confirmed using validated "
        "correlations, vendor data, pilot/plant data, "
        "mechanical design and process safety review."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="engineering-header">

        <div>

            <div class="engineering-title">
                ⚗️ Reactor Scale-Up Studio
            </div>

            <div class="engineering-subtitle">
                Process Engineering • Mixing • Scale-Up •
                Heat Transfer • Validation
            </div>

        </div>

        <div style="
            text-align:right;
            font-size:0.72rem;
            color:#8fa1b3;
        ">
            ENGINEERING WORKSPACE<br>
            <span style="color:#4cc9f0;">
                SCALE-UP MODE
            </span>
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MAIN ROUTING
# ============================================================

# ------------------------------------------------------------
# DESIGN INPUT PAGE
# ------------------------------------------------------------

if page == "01  Reactor Design":

    inputs = reactor_design_page()

    st.divider()

    c1, c2, c3 = st.columns(
        [1, 1, 1]
    )

    with c2:

        calculate = st.button(
            "▶  Run Engineering Calculation",
            type="primary",
            width="stretch",
        )

    if calculate:

        try:

            if (
                inputs["working_volume_m3"]
                >
                inputs["vessel_volume_m3"]
            ):

                st.error(
                    "Calculation stopped: working volume "
                    "exceeds calculated vessel volume."
                )

                st.stop()

            errors = [

                message

                for level, message

                in validate_impellers(
                    inputs["impellers"],
                    inputs["liquid_height_m"],
                    inputs["tank_diameter_m"],
                )

                if level == "ERROR"

            ]

            if errors:

                for message in errors:

                    st.error(message)

                st.stop()

            result = run_calculation(
                inputs
            )

            st.session_state[
                "reactor_inputs"
            ] = copy.deepcopy(
                inputs
            )

            st.session_state[
                "reactor_result"
            ] = copy.deepcopy(
                result
            )

            st.success(
                "Engineering calculation completed."
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Reactor calculation failed."
            )

            st.code(
                f"{type(e).__name__}: {e}"
            )


# ============================================================
# STORED RESULT
# ============================================================

result = st.session_state.get(
    "reactor_result"
)

stored_inputs = st.session_state.get(
    "reactor_inputs"
)


# ============================================================
# RESULT ROUTING
# ============================================================

if result is None:

    if page != "01  Reactor Design":

        st.markdown(
            """
            <div class="conclusion-box">
                <div class="conclusion-title">
                    No Active Engineering Case
                </div>

                <div class="conclusion-text">
                    Define the reactor and process basis in
                    <b>01 Reactor Design</b>, then run the
                    engineering calculation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "Start with Reactor Design."
        )

else:

    if page == "Overview":

        overview_page(
            result
        )

    elif page == "02  Agitator":

        agitator_page(
            result
        )

    elif page == "03  Mixing":

        mixing_page(
            result
        )

    elif page == "04  Scale-Up":

        scaleup_page(
            result
        )

    elif page == "05  Solid Suspension":

        solid_suspension_page(
            result
        )

    elif page == "06  Gas–Liquid":

        gas_liquid_page(
            result
        )

    elif page == "07  Heat Transfer":

        heat_transfer_page(
            result
        )

    elif page == "08  Validation":

        validation_page(
            result
        )

    elif page == "09  3D Reactor":

        three_d_page(
            result
        )

    elif page == "10  Engineering Report":

        reports_page(
            stored_inputs,
            result,
        )

    elif page == "01  Reactor Design":

        st.info(
            "Edit the reactor design basis above and "
            "run the engineering calculation."
        )
```
