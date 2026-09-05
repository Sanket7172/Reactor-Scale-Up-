import streamlit as st
import pandas as pd

from calculations.engine import calculate_reactor
from calculations.scaleup import calculate_scaleup
from calculations.validation import validate_reactor

from libraries.agitator_geometry import AGITATORS
from libraries.reactor_geometry import (
    REACTOR_HEADS,
    calculate_total_volume,
    liquid_height_from_volume,
)

from visualization.reactor_3d import create_reactor_animation


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# PROFESSIONAL DASHBOARD CSS
# =========================================================
#
# IMPORTANT:
# We use CSS ONLY for styling.
# We do NOT use HTML cards for dashboard content.
# This prevents the previous raw-HTML rendering problem.
# =========================================================

st.markdown(
    """
    <style>

    /* -----------------------------------------------------
       GLOBAL
    ----------------------------------------------------- */

    .stApp {
        background-color: #f4f7fb;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Main text */
    html, body, [class*="css"] {
        font-family: "Segoe UI", Arial, sans-serif;
    }

    /* -----------------------------------------------------
       HEADINGS
    ----------------------------------------------------- */

    h1 {
        color: #102a43 !important;
        font-weight: 800 !important;
        letter-spacing: -0.6px;
    }

    h2 {
        color: #102a43 !important;
        font-weight: 750 !important;
    }

    h3 {
        color: #173f5f !important;
        font-weight: 750 !important;
    }

    h4 {
        color: #244b63 !important;
        font-weight: 700 !important;
    }

    p {
        color: #334e68;
    }

    /* -----------------------------------------------------
       SIDEBAR
    ----------------------------------------------------- */

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #d9e2ec;
    }

    [data-testid="stSidebar"] * {
        color: #243b53;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #102a43 !important;
    }

    /* -----------------------------------------------------
       LABELS
    ----------------------------------------------------- */

    label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: #243b53 !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
    }

    /* Help text */
    [data-testid="stWidgetLabel"] small {
        color: #627d98 !important;
    }

    /* -----------------------------------------------------
       INPUT BOXES
    ----------------------------------------------------- */

    input,
    textarea {
        color: #102a43 !important;
        background-color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Number input */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #bcccdc !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="input"]:focus-within {
        border: 2px solid #2f80ed !important;
        box-shadow: 0 0 0 2px rgba(47,128,237,0.10);
    }

    /* -----------------------------------------------------
       SELECTBOX
    ----------------------------------------------------- */

    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #bcccdc !important;
        border-radius: 10px !important;
        color: #102a43 !important;
        min-height: 44px;
    }

    div[data-baseweb="select"] * {
        color: #102a43 !important;
    }

    div[data-baseweb="select"] span {
        color: #102a43 !important;
        font-weight: 600 !important;
    }

    /* Dropdown menu */
    ul[role="listbox"] {
        background-color: #ffffff !important;
    }

    li[role="option"] {
        color: #102a43 !important;
        background-color: #ffffff !important;
    }

    li[role="option"]:hover {
        background-color: #edf2f7 !important;
    }

    /* -----------------------------------------------------
       CHECKBOX / RADIO
    ----------------------------------------------------- */

    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label {
        color: #243b53 !important;
        font-weight: 650 !important;
    }

    /* -----------------------------------------------------
       METRIC CARDS
    ----------------------------------------------------- */

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d9e2ec;
        border-radius: 16px;
        padding: 18px 20px;
        min-height: 125px;
        box-shadow: 0 5px 18px rgba(16, 42, 67, 0.07);
    }

    [data-testid="stMetricLabel"] {
        color: #486581 !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }

    [data-testid="stMetricValue"] {
        color: #102a43 !important;
        font-weight: 800 !important;
        font-size: 1.65rem !important;
    }

    [data-testid="stMetricDelta"] {
        font-weight: 650 !important;
    }

    /* -----------------------------------------------------
       CONTAINERS
    ----------------------------------------------------- */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border: 1px solid #d9e2ec !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(16, 42, 67, 0.045);
    }

    /* -----------------------------------------------------
       TABS
    ----------------------------------------------------- */

    div[data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        padding: 7px;
        border-radius: 14px;
        border: 1px solid #d9e2ec;
    }

    button[data-baseweb="tab"] {
        color: #486581 !important;
        font-weight: 750 !important;
        border-radius: 9px !important;
        padding: 10px 18px !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background-color: #173f5f !important;
    }

    /* -----------------------------------------------------
       BUTTONS
    ----------------------------------------------------- */

    .stButton > button {
        width: 100%;
        min-height: 44px;
        border-radius: 10px;
        border: 1px solid #bcccdc;
        background-color: #ffffff;
        color: #102a43 !important;
        font-weight: 750;
    }

    .stButton > button:hover {
        border-color: #2f80ed;
        color: #2f80ed !important;
        background-color: #f0f7ff;
    }

    /* -----------------------------------------------------
       EXPANDERS
    ----------------------------------------------------- */

    details {
        border: 1px solid #d9e2ec !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
    }

    summary {
        color: #102a43 !important;
        font-weight: 750 !important;
    }

    /* -----------------------------------------------------
       DATAFRAME
    ----------------------------------------------------- */

    [data-testid="stDataFrame"] {
        border: 1px solid #d9e2ec;
        border-radius: 12px;
        overflow: hidden;
    }

    /* -----------------------------------------------------
       ALERTS
    ----------------------------------------------------- */

    [data-testid="stAlert"] {
        border-radius: 12px !important;
    }

    /* -----------------------------------------------------
       DIVIDER
    ----------------------------------------------------- */

    hr {
        border-color: #d9e2ec !important;
    }

    /* -----------------------------------------------------
       PROGRESS BAR
    ----------------------------------------------------- */

    [data-testid="stProgressBar"] {
        height: 10px;
    }

    /* -----------------------------------------------------
       CAPTIONS
    ----------------------------------------------------- */

    .stCaption,
    [data-testid="stCaptionContainer"] {
        color: #627d98 !important;
    }

    /* -----------------------------------------------------
       REMOVE EXCESS TOP SPACE
    ----------------------------------------------------- */

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CONSTANTS
# =========================================================

PROCESS_TYPES = [
    "Liquid-Liquid",
    "Solid-Liquid",
    "Gas-Liquid",
    "Gas-Liquid-Solid",
    "Crystallization",
    "High-Viscosity",
    "General Mixing",
]

SCALEUP_BASES = [
    "Constant P/V",
    "Constant Tip Speed",
    "Constant RPM",
    "Constant Froude Number",
    "Constant Reynolds Number",
    "Constant Pumping / Volume",
    "Constant N/Njs",
    "Constant KLa",
    "User Defined",
]

STUDY_MODES = [
    "Single Reactor",
    "Lab vs Pilot",
    "Pilot vs Commercial",
    "Lab vs Commercial",
    "Lab vs Pilot vs Commercial",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def fmt(value, decimals=2, unit=""):
    if value is None:
        return "—"

    try:
        return f"{float(value):,.{decimals}f}{unit}"
    except Exception:
        return "—"


def engineering_status(validation):
    if not validation:
        return "REVIEW"

    if validation.get("overall") == "FAIL":
        return "FAIL"

    if validation.get("overall") == "REVIEW":
        return "REVIEW"

    return "PASS"


def status_message(status):
    if status == "PASS":
        st.success("● DESIGN STATUS: PASS")
    elif status == "FAIL":
        st.error("● DESIGN STATUS: FAIL")
    else:
        st.warning("● DESIGN STATUS: REVIEW")


def calculate_fill_percent(working_volume, vessel_volume):
    if vessel_volume <= 0:
        return 0.0

    return working_volume / vessel_volume * 100.0


def get_process_guidance(process_type):
    guidance = {
        "Liquid-Liquid": (
            "Focus on blend time, circulation, power/volume, tip speed and "
            "impeller selection."
        ),
        "Solid-Liquid": (
            "Focus on solids suspension, Njs, off-bottom suspension, "
            "P/V and impeller clearance."
        ),
        "Gas-Liquid": (
            "Focus on gas dispersion, P/V, tip speed, flooding, gas handling "
            "and KLa."
        ),
        "Gas-Liquid-Solid": (
            "Focus on gas dispersion, solids suspension, Njs, P/V and KLa."
        ),
        "Crystallization": (
            "Focus on suspension, shear sensitivity, circulation, P/V and "
            "crystal quality."
        ),
        "High-Viscosity": (
            "Focus on torque, power, laminar/transitional regime and "
            "close-clearance impeller selection."
        ),
        "General Mixing": (
            "Use P/V, tip speed, Re, Fr, pumping capacity and geometry ratios "
            "as primary screening parameters."
        ),
    }

    return guidance.get(process_type, guidance["General Mixing"])


def process_parameter_visibility(process_type):
    if process_type == "Solid-Liquid":
        return ["P/V", "Tip Speed", "Njs", "Re", "Q/V"]

    if process_type == "Gas-Liquid":
        return ["P/V", "Tip Speed", "Re", "KLa", "Q/V"]

    if process_type == "Gas-Liquid-Solid":
        return ["P/V", "Tip Speed", "Njs", "KLa", "Re", "Q/V"]

    if process_type == "High-Viscosity":
        return ["P/V", "Tip Speed", "Re", "Torque"]

    if process_type == "Crystallization":
        return ["P/V", "Tip Speed", "Njs", "Re", "Q/V"]

    return ["P/V", "Tip Speed", "Re", "Fr", "Q/V"]


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ⚗️ Reactor Studio")

    st.caption("Professional Process Engineering Dashboard")

    st.divider()

    st.markdown("### 📁 Project")

    project_name = st.text_input(
        "Project Name",
        value="Reactor Scale-Up Study",
        help="Enter the project or process study name.",
    )

    prepared_by = st.text_input(
        "Prepared By",
        value="Process Engineering",
    )

    st.divider()

    st.markdown("### ⚙️ Study Configuration")

    study_mode = st.selectbox(
        "Study Mode",
        STUDY_MODES,
        index=0,
    )

    process_type = st.selectbox(
        "Reaction / Process Type",
        PROCESS_TYPES,
        index=0,
    )

    scaleup_basis = st.selectbox(
        "Primary Scale-Up Basis",
        SCALEUP_BASES,
        index=0,
    )

    st.divider()

    st.markdown("### 🎯 Engineering Focus")

    visible_parameters = process_parameter_visibility(process_type)

    for parameter in visible_parameters:
        st.checkbox(
            parameter,
            value=True,
            disabled=True,
            key=f"focus_{parameter}",
        )

    st.divider()

    st.caption(
        "Screening-level engineering calculations. "
        "Validate correlations and equipment/vendor data before final design."
    )


# =========================================================
# HEADER
# =========================================================

st.title("⚗️ Reactor Scale-Up Engineering Studio")

st.caption(
    f"{project_name}  •  {process_type}  •  "
    f"{study_mode}  •  Scale-Up: {scaleup_basis}"
)

st.divider()


# =========================================================
# INITIAL REACTOR CONFIGURATION
# =========================================================

if study_mode == "Single Reactor":
    reactor_names = ["Reactor"]

elif study_mode == "Lab vs Pilot":
    reactor_names = ["Lab", "Pilot"]

elif study_mode == "Pilot vs Commercial":
    reactor_names = ["Pilot", "Commercial"]

elif study_mode == "Lab vs Commercial":
    reactor_names = ["Lab", "Commercial"]

else:
    reactor_names = ["Lab", "Pilot", "Commercial"]


# =========================================================
# REACTOR INPUT FUNCTION
# =========================================================

def reactor_input_panel(name, index):

    st.markdown(f"### ⚗️ {name} Reactor")

    with st.container(border=True):

        # -------------------------------------------------
        # PROCESS CONDITIONS
        # -------------------------------------------------

        st.markdown("#### 1. Process Conditions")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            working_volume = st.number_input(
                "Working Volume",
                min_value=0.001,
                value=1.0 if name == "Lab" else 10.0 if name == "Pilot" else 50.0,
                step=0.5,
                format="%.3f",
                key=f"{name}_working_volume",
                help="Actual liquid/slurry working volume inside the reactor.",
            )
            st.caption("Unit: m³")

        with c2:
            density = st.number_input(
                "Density",
                min_value=0.001,
                value=1000.0,
                step=10.0,
                format="%.1f",
                key=f"{name}_density",
                help="Bulk process density.",
            )
            st.caption("Unit: kg/m³")

        with c3:
            viscosity_mpas = st.number_input(
                "Viscosity",
                min_value=0.001,
                value=1.0,
                step=0.1,
                format="%.3f",
                key=f"{name}_viscosity",
                help="Dynamic viscosity.",
            )
            st.caption("Unit: mPa·s")

        with c4:
            surface_tension = st.number_input(
                "Surface Tension",
                min_value=0.001,
                value=0.072,
                step=0.001,
                format="%.4f",
                key=f"{name}_surface_tension",
                help="Surface tension for gas-liquid or dispersion screening.",
            )
            st.caption("Unit: N/m")

        viscosity_pa_s = viscosity_mpas / 1000.0

        st.divider()

        # -------------------------------------------------
        # VESSEL GEOMETRY
        # -------------------------------------------------

        st.markdown("#### 2. Reactor Geometry")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            tank_diameter = st.number_input(
                "Tank Internal Diameter",
                min_value=0.05,
                value=1.0 if name == "Lab" else 2.0 if name == "Pilot" else 3.0,
                step=0.05,
                format="%.3f",
                key=f"{name}_tank_diameter",
            )
            st.caption("Unit: m")

        with c2:
            straight_height = st.number_input(
                "Straight Side Height",
                min_value=0.05,
                value=1.5 if name == "Lab" else 2.5 if name == "Pilot" else 4.0,
                step=0.05,
                format="%.3f",
                key=f"{name}_straight_height",
            )
            st.caption("Unit: m")

        with c3:
            bottom_type = st.selectbox(
                "Bottom Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{name}_bottom",
            )

        with c4:
            top_type = st.selectbox(
                "Top Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{name}_top",
            )

        vessel_volume = calculate_total_volume(
            D=tank_diameter,
            straight_height=straight_height,
            bottom_type=bottom_type,
            top_type=top_type,
        )

        liquid_height, _ = liquid_height_from_volume(
            working_volume=working_volume,
            D=tank_diameter,
            straight_height=straight_height,
            bottom_type=bottom_type,
            top_type=top_type,
        )

        fill_percent = calculate_fill_percent(
            working_volume,
            vessel_volume,
        )

        g1, g2, g3 = st.columns(3)

        with g1:
            st.metric(
                "Calculated Vessel Capacity",
                fmt(vessel_volume, 3, " m³"),
            )

        with g2:
            st.metric(
                "Calculated Liquid Height",
                fmt(liquid_height, 3, " m"),
            )

        with g3:
            st.metric(
                "Operating Fill",
                fmt(fill_percent, 1, " %"),
            )

        st.progress(
            min(max(fill_percent / 100.0, 0.0), 1.0)
        )

        if fill_percent > 100:
            st.error(
                "Working volume exceeds calculated vessel capacity. "
                "Increase vessel geometry or reduce working volume."
            )

        elif fill_percent > 90:
            st.warning(
                "High operating fill. Review required headspace and mixing behavior."
            )

        st.divider()

        # -------------------------------------------------
        # AGITATION
        # -------------------------------------------------

        st.markdown("#### 3. Agitation System")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            agitator = st.selectbox(
                "Agitator Type",
                list(AGITATORS.keys()),
                index=1,
                key=f"{name}_agitator",
            )

        agitator_data = AGITATORS.get(agitator, {})

        default_ratio = agitator_data.get(
            "default_diameter_ratio",
            0.33,
        )

        default_impeller = max(
            0.05,
            round(
                tank_diameter * default_ratio,
                3,
            ),
        )

        with c2:
            impeller_diameter = st.number_input(
                "Impeller Diameter",
                min_value=0.02,
                value=default_impeller,
                step=0.01,
                format="%.3f",
                key=f"{name}_impeller_diameter",
            )
            st.caption("Unit: m")

        with c3:
            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{name}_number_impellers",
            )
            st.caption("Unit: count")

        with c4:
            rpm = st.number_input(
                "Agitator Speed",
                min_value=0.1,
                value=150.0,
                step=5.0,
                format="%.1f",
                key=f"{name}_rpm",
            )
            st.caption("Unit: RPM")

        # Agitator information

        info1, info2, info3, info4 = st.columns(4)

        with info1:
            st.metric(
                "Flow Pattern",
                agitator_data.get("flow", "—"),
            )

        with info2:
            st.metric(
                "Blade Count",
                str(agitator_data.get("blades", "—")),
            )

        with info3:
            np_value = agitator_data.get("np")
            st.metric(
                "Power Number, Np",
                fmt(np_value, 3) if np_value is not None else "N/A",
            )

        with info4:
            nq_value = agitator_data.get("nq")
            st.metric(
                "Pumping Number, Nq",
                fmt(nq_value, 3) if nq_value is not None else "N/A",
            )

        if agitator_data.get("description"):
            st.info(
                f"**{agitator}** — {agitator_data['description']}"
            )

        if agitator_data.get("recommended_for"):
            st.caption(
                "Recommended applications: "
                + ", ".join(agitator_data["recommended_for"])
            )

        st.divider()

        # -------------------------------------------------
        # BAFFLES / CLEARANCE
        # -------------------------------------------------

        st.markdown("#### 4. Internal Arrangement")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            number_baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{name}_baffles",
            )
            st.caption("Unit: count")

        with c2:
            impeller_clearance = st.number_input(
                "Bottom Clearance",
                min_value=0.0,
                value=max(0.05, tank_diameter * 0.20),
                step=0.01,
                format="%.3f",
                key=f"{name}_clearance",
            )
            st.caption("Unit: m")

        with c3:
            vortex_depth = st.number_input(
                "Vortex Depth",
                min_value=0.0,
                value=0.0,
                step=0.01,
                format="%.3f",
                key=f"{name}_vortex",
            )
            st.caption("Unit: m")

        with c4:
            st.metric(
                "D/T Ratio",
                fmt(
                    impeller_diameter / tank_diameter
                    if tank_diameter > 0
                    else 0,
                    3,
                ),
            )

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------

        try:

            result = calculate_reactor(
                volume_m3=working_volume,
                tank_diameter_m=tank_diameter,
                liquid_height_m=liquid_height,
                density_kg_m3=density,
                viscosity_pa_s=viscosity_pa_s,
                surface_tension_n_m=surface_tension,
                rpm=rpm,
                impeller_diameter_m=impeller_diameter,
                number_impellers=number_impellers,
                agitator=agitator,
                impeller_clearance_m=impeller_clearance,
            )

            result["name"] = name
            result["working_volume"] = working_volume
            result["vessel_volume"] = vessel_volume
            result["tank_diameter_m"] = tank_diameter
            result["straight_height_m"] = straight_height
            result["bottom_type"] = bottom_type
            result["top_type"] = top_type
            result["liquid_height_m"] = liquid_height
            result["density"] = density
            result["density_kg_m3"] = density
            result["viscosity_pa_s"] = viscosity_pa_s
            result["surface_tension_n_m"] = surface_tension
            result["rpm"] = rpm
            result["impeller_diameter_m"] = impeller_diameter
            result["number_impellers"] = number_impellers
            result["agitator"] = agitator
            result["number_baffles"] = number_baffles
            result["vortex_depth"] = vortex_depth
            result["impeller_clearance_m"] = impeller_clearance

            # Compatibility for scale-up module
            result["pumping_per_volume"] = result.get("qv_1_h")

            validation = validate_reactor(
                volume_m3=working_volume,
                vessel_volume_m3=vessel_volume,
                tank_diameter_m=tank_diameter,
                straight_height_m=straight_height,
                liquid_height_m=liquid_height,
                impeller_diameter_m=impeller_diameter,
                number_impellers=number_impellers,
                number_baffles=number_baffles,
                rpm=rpm,
                agitator=agitator,
                density_kg_m3=density,
                viscosity_pa_s=viscosity_pa_s,
            )

            result["validation"] = validation

            return result

        except Exception as exc:

            st.error(
                f"Calculation error for {name}: {exc}"
            )

            return {
                "name": name,
                "working_volume": working_volume,
                "vessel_volume": vessel_volume,
                "tank_diameter_m": tank_diameter,
                "straight_height_m": straight_height,
                "bottom_type": bottom_type,
                "top_type": top_type,
                "liquid_height_m": liquid_height,
                "density": density,
                "density_kg_m3": density,
                "viscosity_pa_s": viscosity_pa_s,
                "surface_tension_n_m": surface_tension,
                "rpm": rpm,
                "impeller_diameter_m": impeller_diameter,
                "number_impellers": number_impellers,
                "agitator": agitator,
                "number_baffles": number_baffles,
                "vortex_depth": vortex_depth,
                "impeller_clearance_m": impeller_clearance,
                "validation": {
                    "overall": "FAIL",
                    "failures": 1,
                    "warnings": 0,
                    "checks": [],
                },
            }


# =========================================================
# MAIN TABS
# =========================================================

tab_setup, tab_performance, tab_scaleup, tab_validation, tab_3d, tab_insights = st.tabs(
    [
        "📐 Reactor Setup",
        "📊 Performance",
        "📈 Scale-Up",
        "✅ Validation",
        "🧊 3D Reactor",
        "💡 Engineering Insights",
    ]
)


# =========================================================
# TAB 1 — REACTOR SETUP
# =========================================================

with tab_setup:

    st.markdown("## Reactor Configuration")

    st.caption(
        "Define process conditions, vessel geometry, agitator arrangement "
        "and operating parameters."
    )

    reactors = []

    for i, name in enumerate(reactor_names):

        reactor = reactor_input_panel(
            name=name,
            index=i,
        )

        reactors.append(reactor)

        if i < len(reactor_names) - 1:
            st.markdown("")


# =========================================================
# GLOBAL STATUS
# =========================================================

statuses = [
    engineering_status(
        r.get("validation")
    )
    for r in reactors
]

if "FAIL" in statuses:
    overall_status = "FAIL"
elif "REVIEW" in statuses:
    overall_status = "REVIEW"
else:
    overall_status = "PASS"


# =========================================================
# TOP SUMMARY
# =========================================================

st.divider()

st.markdown("## 📌 Engineering Dashboard Summary")

s1, s2, s3, s4 = st.columns(4)

with s1:
    st.metric(
        "Reactors in Study",
        str(len(reactors)),
    )

with s2:
    st.metric(
        "Process Type",
        process_type,
    )

with s3:
    st.metric(
        "Scale-Up Basis",
        scaleup_basis,
    )

with s4:
    st.metric(
        "Overall Status",
        overall_status,
    )


# =========================================================
# TAB 2 — PERFORMANCE
# =========================================================

with tab_performance:

    st.markdown("## 📊 Mixing & Agitation Performance")

    st.info(
        f"**Engineering focus for {process_type}:** "
        f"{get_process_guidance(process_type)}"
    )

    for reactor in reactors:

        name = reactor["name"]

        st.markdown(f"### ⚗️ {name}")

        with st.container(border=True):

            p1, p2, p3, p4 = st.columns(4)

            with p1:
                st.metric(
                    "Agitator Power",
                    fmt(
                        reactor.get("power_kw"),
                        2,
                        " kW",
                    ),
                )

            with p2:
                st.metric(
                    "Power / Volume",
                    fmt(
                        reactor.get("power_volume"),
                        2,
                        " W/m³",
                    ),
                )

            with p3:
                st.metric(
                    "Tip Speed",
                    fmt(
                        reactor.get("tip_speed"),
                        2,
                        " m/s",
                    ),
                )

            with p4:
                st.metric(
                    "Reynolds Number",
                    fmt(
                        reactor.get("Re"),
                        0,
                    ),
                )

            st.markdown("")

            p5, p6, p7, p8 = st.columns(4)

            with p5:
                st.metric(
                    "Froude Number",
                    fmt(
                        reactor.get("Fr"),
                        4,
                    ),
                )

            with p6:
                st.metric(
                    "Pumping Capacity",
                    fmt(
                        reactor.get("pumping_m3_h"),
                        2,
                        " m³/h",
                    ),
                )

            with p7:
                st.metric(
                    "Q / V",
                    fmt(
                        reactor.get("qv_1_h"),
                        3,
                        " 1/h",
                    ),
                )

            with p8:
                st.metric(
                    "Turnover Time",
                    fmt(
                        reactor.get("turnover_time_min"),
                        2,
                        " min",
                    ),
                )

            st.divider()

            d1, d2, d3, d4 = st.columns(4)

            with d1:
                st.metric(
                    "Impeller / Tank",
                    fmt(
                        reactor.get("D_T"),
                        3,
                    ),
                )

            with d2:
                st.metric(
                    "Liquid Height / Tank",
                    fmt(
                        reactor.get("H_T"),
                        3,
                    ),
                )

            with d3:
                st.metric(
                    "Impeller Clearance / Tank",
                    fmt(
                        reactor.get("clearance_T"),
                        3,
                    ),
                )

            with d4:
                st.metric(
                    "Mixing Regime",
                    reactor.get(
                        "mixing_regime",
                        "—",
                    ),
                )

            st.divider()

            # Operating data table

            performance_data = pd.DataFrame(
                {
                    "Parameter": [
                        "Working Volume",
                        "Vessel Capacity",
                        "Liquid Height",
                        "Tank Diameter",
                        "Straight Height",
                        "Impeller Diameter",
                        "Number of Impellers",
                        "Agitator Speed",
                        "Density",
                        "Viscosity",
                        "Surface Tension",
                        "Number of Baffles",
                    ],
                    "Value": [
                        fmt(reactor["working_volume"], 3),
                        fmt(reactor["vessel_volume"], 3),
                        fmt(reactor["liquid_height_m"], 3),
                        fmt(reactor["tank_diameter_m"], 3),
                        fmt(reactor["straight_height_m"], 3),
                        fmt(reactor["impeller_diameter_m"], 3),
                        str(reactor["number_impellers"]),
                        fmt(reactor["rpm"], 1),
                        fmt(reactor["density"], 1),
                        fmt(reactor["viscosity_pa_s"], 5),
                        fmt(reactor["surface_tension_n_m"], 4),
                        str(reactor["number_baffles"]),
                    ],
                    "Unit": [
                        "m³",
                        "m³",
                        "m",
                        "m",
                        "m",
                        "m",
                        "count",
                        "RPM",
                        "kg/m³",
                        "Pa·s",
                        "N/m",
                        "count",
                    ],
                }
            )

            st.dataframe(
                performance_data,
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# TAB 3 — SCALE-UP
# =========================================================

with tab_scaleup:

    st.markdown("## 📈 Scale-Up Analysis")

    if len(reactors) < 2:

        st.info(
            "Select a comparison study mode such as "
            "**Lab vs Pilot**, **Pilot vs Commercial**, or "
            "**Lab vs Pilot vs Commercial** to perform scale-up analysis."
        )

    else:

        base = reactors[0]
        target = reactors[1]

        st.markdown(
            f"### {base['name']} → {target['name']}"
        )

        with st.container(border=True):

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Base Volume",
                    fmt(
                        base["working_volume"],
                        3,
                        " m³",
                    ),
                )

            with c2:
                st.metric(
                    "Target Volume",
                    fmt(
                        target["working_volume"],
                        3,
                        " m³",
                    ),
                )

            with c3:

                scale_ratio = (
                    target["working_volume"]
                    / base["working_volume"]
                    if base["working_volume"] > 0
                    else 0
                )

                st.metric(
                    "Volume Scale Ratio",
                    fmt(
                        scale_ratio,
                        2,
                        " ×",
                    ),
                )

            with c4:

                diameter_ratio = (
                    target["tank_diameter_m"]
                    / base["tank_diameter_m"]
                    if base["tank_diameter_m"] > 0
                    else 0
                )

                st.metric(
                    "Tank Diameter Ratio",
                    fmt(
                        diameter_ratio,
                        2,
                        " ×",
                    ),
                )

            st.divider()

            try:

                scale_result = calculate_scaleup(
                    base=base,
                    target=target,
                    basis=scaleup_basis,
                )

            except Exception as exc:

                scale_result = {
                    "status": "REVIEW",
                    "message": str(exc),
                    "target_rpm": None,
                    "target_tip_speed": None,
                    "target_power_volume": None,
                    "target_qv": None,
                }

            st.markdown("#### Scale-Up Result")

            r1, r2, r3, r4 = st.columns(4)

            with r1:

                st.metric(
                    "Scale-Up Basis",
                    scaleup_basis,
                )

            with r2:

                st.metric(
                    "Calculated Target RPM",
                    fmt(
                        scale_result.get("target_rpm"),
                        1,
                        " RPM",
                    ),
                )

            with r3:

                st.metric(
                    "Target Tip Speed",
                    fmt(
                        scale_result.get("target_tip_speed"),
                        2,
                        " m/s",
                    ),
                )

            with r4:

                st.metric(
                    "Target P/V",
                    fmt(
                        scale_result.get("target_power_volume"),
                        2,
                        " W/m³",
                    ),
                )

            st.divider()

            if scale_result.get("message"):

                st.info(
                    scale_result["message"]
                )

            # Comparison table

            comparison = pd.DataFrame(
                {
                    "Parameter": [
                        "Working Volume",
                        "Tank Diameter",
                        "Impeller Diameter",
                        "RPM",
                        "Tip Speed",
                        "P/V",
                        "Reynolds Number",
                        "Froude Number",
                        "Q/V",
                        "Power",
                    ],
                    base["name"]: [
                        fmt(base["working_volume"], 3, " m³"),
                        fmt(base["tank_diameter_m"], 3, " m"),
                        fmt(base["impeller_diameter_m"], 3, " m"),
                        fmt(base["rpm"], 1, " RPM"),
                        fmt(base.get("tip_speed"), 2, " m/s"),
                        fmt(base.get("power_volume"), 2, " W/m³"),
                        fmt(base.get("Re"), 0),
                        fmt(base.get("Fr"), 4),
                        fmt(base.get("qv_1_h"), 3, " 1/h"),
                        fmt(base.get("power_kw"), 2, " kW"),
                    ],
                    target["name"]: [
                        fmt(target["working_volume"], 3, " m³"),
                        fmt(target["tank_diameter_m"], 3, " m"),
                        fmt(target["impeller_diameter_m"], 3, " m"),
                        fmt(target["rpm"], 1, " RPM"),
                        fmt(target.get("tip_speed"), 2, " m/s"),
                        fmt(target.get("power_volume"), 2, " W/m³"),
                        fmt(target.get("Re"), 0),
                        fmt(target.get("Fr"), 4),
                        fmt(target.get("qv_1_h"), 3, " 1/h"),
                        fmt(target.get("power_kw"), 2, " kW"),
                    ],
                }
            )

            st.markdown("#### Base vs Target Comparison")

            st.dataframe(
                comparison,
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# TAB 4 — VALIDATION
# =========================================================

with tab_validation:

    st.markdown("## ✅ Engineering Validation")

    if overall_status == "PASS":

        st.success(
            "Overall screening status: PASS — no major validation flags detected."
        )

    elif overall_status == "REVIEW":

        st.warning(
            "Overall screening status: REVIEW — one or more engineering "
            "checks require attention."
        )

    else:

        st.error(
            "Overall screening status: FAIL — one or more critical checks failed."
        )

    for reactor in reactors:

        st.markdown(
            f"### {reactor['name']} Reactor"
        )

        validation = reactor.get("validation", {})

        with st.container(border=True):

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Status",
                    validation.get(
                        "overall",
                        "REVIEW",
                    ),
                )

            with c2:
                st.metric(
                    "Failures",
                    str(
                        validation.get(
                            "failures",
                            0,
                        )
                    ),
                )

            with c3:
                st.metric(
                    "Warnings",
                    str(
                        validation.get(
                            "warnings",
                            0,
                        )
                    ),
                )

            st.divider()

            checks = validation.get(
                "checks",
                [],
            )

            if checks:

                validation_table = pd.DataFrame(
                    {
                        "Status": [
                            c.get(
                                "severity",
                                "REVIEW",
                            )
                            for c in checks
                        ],
                        "Engineering Check": [
                            c.get(
                                "message",
                                "",
                            )
                            for c in checks
                        ],
                    }
                )

                st.dataframe(
                    validation_table,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No validation checks available."
                )


# =========================================================
# TAB 5 — 3D REACTOR
# =========================================================

with tab_3d:

    st.markdown("## 🧊 3D Reactor Visualization")

    st.caption(
        "Interactive reactor geometry and agitator visualization."
    )

    selected_reactor_name = st.selectbox(
        "Select Reactor",
        [r["name"] for r in reactors],
        key="selected_3d_reactor",
    )

    selected = next(
        r for r in reactors
        if r["name"] == selected_reactor_name
    )

    with st.container(border=True):

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Tank Diameter",
                fmt(
                    selected["tank_diameter_m"],
                    3,
                    " m",
                ),
            )

        with c2:
            st.metric(
                "Liquid Height",
                fmt(
                    selected["liquid_height_m"],
                    3,
                    " m",
                ),
            )

        with c3:
            st.metric(
                "Impeller Diameter",
                fmt(
                    selected["impeller_diameter_m"],
                    3,
                    " m",
                ),
            )

        with c4:
            st.metric(
                "Agitator Speed",
                fmt(
                    selected["rpm"],
                    1,
                    " RPM",
                ),
            )

    try:

        reactor_figure = create_reactor_animation(
            D=selected["tank_diameter_m"],
            straight_height=selected["straight_height_m"],
            bottom_type=selected["bottom_type"],
            top_type=selected["top_type"],
            liquid_height=selected["liquid_height_m"],
            agitator=selected["agitator"],
            impeller_diameter=selected["impeller_diameter_m"],
            number_impellers=selected["number_impellers"],
            rpm=selected["rpm"],
            number_baffles=selected["number_baffles"],
            vortex_depth=selected["vortex_depth"],
            frames_count=36,
        )

        if reactor_figure is not None:

            st.plotly_chart(
                reactor_figure,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "displaylogo": False,
                },
            )

        else:

            st.warning(
                "The 3D visualization function did not return a figure."
            )

    except Exception as exc:

        st.error(
            f"3D visualization error: {exc}"
        )

        st.info(
            "The calculation dashboard can continue to operate even if "
            "the visualization module requires correction."
        )


# =========================================================
# TAB 6 — ENGINEERING INSIGHTS
# =========================================================

with tab_insights:

    st.markdown("## 💡 Engineering Insights")

    st.info(
        f"### Process Focus — {process_type}\n\n"
        f"{get_process_guidance(process_type)}"
    )

    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']} Reactor"
        )

        with st.container(border=True):

            insights = []

            # ---------------------------------------------
            # D/T
            # ---------------------------------------------

            dt_ratio = reactor.get("D_T")

            if dt_ratio is not None:

                if dt_ratio < 0.20:

                    insights.append(
                        "⚠️ Impeller diameter is relatively small compared "
                        "with tank diameter. Review circulation and blend-time performance."
                    )

                elif dt_ratio > 0.60:

                    insights.append(
                        "⚠️ Large impeller/tank ratio detected. Review "
                        "clearance, power, torque and mechanical loading."
                    )

                else:

                    insights.append(
                        "✅ Impeller/tank diameter ratio is within the "
                        "screening range used by the validation module."
                    )

            # ---------------------------------------------
            # REYNOLDS
            # ---------------------------------------------

            reynolds = reactor.get("Re")

            if reynolds is not None:

                if reynolds < 10:

                    insights.append(
                        "⚠️ Laminar regime indicated. Verify that the "
                        "selected power correlation is valid for the impeller."
                    )

                elif reynolds < 10000:

                    insights.append(
                        "⚠️ Transitional mixing regime. Scale-up correlation "
                        "selection requires particular attention."
                    )

                else:

                    insights.append(
                        "✅ Turbulent mixing regime indicated."
                    )

            # ---------------------------------------------
            # BAFFLES
            # ---------------------------------------------

            baffles = reactor.get(
                "number_baffles",
                0,
            )

            if baffles >= 4:

                insights.append(
                    "✅ Four or more baffles are provided for vortex suppression screening."
                )

            elif baffles > 0:

                insights.append(
                    "⚠️ Limited baffle count. Review vortexing and rotational flow."
                )

            else:

                insights.append(
                    "⚠️ No baffles selected. Strong rotational motion and vortexing may occur."
                )

            # ---------------------------------------------
            # FILL
            # ---------------------------------------------

            fill = calculate_fill_percent(
                reactor["working_volume"],
                reactor["vessel_volume"],
            )

            if fill > 90:

                insights.append(
                    "⚠️ High operating fill. Confirm required headspace for "
                    "foaming, gas disengagement and thermal expansion."
                )

            elif fill < 25:

                insights.append(
                    "⚠️ Low operating fill. Confirm that impeller immersion "
                    "and circulation are adequate."
                )

            else:

                insights.append(
                    "✅ Operating fill is within the screening range."
                )

            # ---------------------------------------------
            # POWER
            # ---------------------------------------------

            power_volume = reactor.get(
                "power_volume"
            )

            if power_volume is not None:

                insights.append(
                    f"ℹ️ Calculated power density is "
                    f"{power_volume:,.2f} W/m³."
                )

            # ---------------------------------------------
            # PROCESS-SPECIFIC
            # ---------------------------------------------

            if process_type in [
                "Solid-Liquid",
                "Gas-Liquid-Solid",
                "Crystallization",
            ]:

                insights.append(
                    "🔬 For solids-containing systems, validate Njs using "
                    "an appropriate solids-suspension correlation or experimental data."
                )

            if process_type in [
                "Gas-Liquid",
                "Gas-Liquid-Solid",
            ]:

                insights.append(
                    "🫧 For gas-liquid systems, validate gas dispersion, "
                    "flooding and KLa using an appropriate correlation or test data."
                )

            if process_type == "High-Viscosity":

                insights.append(
                    "⚙️ High-viscosity service should be checked for torque, "
                    "motor sizing, gearbox limitations and laminar power correlation."
                )

            for insight in insights:

                st.write(
                    insight
                )


# =========================================================
# ENGINEERING DISCLAIMER
# =========================================================

st.divider()

st.caption(
    "⚠️ Engineering note: This dashboard provides preliminary/screening-level "
    "calculations. Np/Nq, Njs, KLa, blend time, flooding and other scale-up "
    "correlations should be validated against applicable literature, vendor "
    "data, pilot experiments and site-specific engineering standards before "
    "final equipment design or procurement."
)
