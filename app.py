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
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CLEAN ENGINEERING UI
# =========================================================

st.markdown(
    """
<style>

/* =======================================================
   GLOBAL
   ======================================================= */

.stApp {
    background: #f7f9fc;
}

.block-container {
    max-width: 1500px;
    padding-top: 1rem;
    padding-bottom: 2rem;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
}


/* =======================================================
   HEADINGS
   ======================================================= */

h1 {
    color: #17324d !important;
    font-weight: 750 !important;
    letter-spacing: -0.5px;
}

h2 {
    color: #17324d !important;
    font-weight: 700 !important;
}

h3 {
    color: #244a68 !important;
    font-weight: 700 !important;
}

h4 {
    color: #34566f !important;
    font-weight: 650 !important;
}


/* =======================================================
   SIDEBAR
   ======================================================= */

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

[data-testid="stSidebar"] * {
    color: #263f55;
}


/* =======================================================
   LABELS
   ======================================================= */

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
label {
    color: #334e68 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}


/* =======================================================
   INPUTS
   ======================================================= */

div[data-baseweb="input"] {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}

div[data-baseweb="input"]:focus-within {
    border: 1px solid #3274a8 !important;
    box-shadow: 0 0 0 1px #3274a8 !important;
}

input {
    color: #17324d !important;
    background: #ffffff !important;
    font-weight: 600 !important;
}


/* =======================================================
   SELECTBOX
   ======================================================= */

div[data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    min-height: 42px;
}

div[data-baseweb="select"] * {
    color: #17324d !important;
}

div[data-baseweb="select"] span {
    font-weight: 600 !important;
}


/* =======================================================
   EXPANDERS
   ======================================================= */

[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    margin-bottom: 10px;
}

[data-testid="stExpander"] summary {
    font-weight: 650 !important;
    color: #244a68 !important;
}


/* =======================================================
   TABS
   ======================================================= */

div[data-baseweb="tab-list"] {
    gap: 4px;
    padding: 4px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

button[data-baseweb="tab"] {
    color: #486581 !important;
    font-weight: 650 !important;
    border-radius: 7px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #244a68 !important;
    color: #ffffff !important;
}


/* =======================================================
   BUTTONS
   ======================================================= */

.stButton > button {
    min-height: 40px;
    border-radius: 8px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #244a68 !important;
    font-weight: 650;
}


/* =======================================================
   DIVIDERS
   ======================================================= */

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 1rem 0;
}


/* =======================================================
   KPI CARDS
   ======================================================= */

.eng-kpi {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 13px 15px;
    min-height: 95px;
}

.eng-kpi-label {
    color: #627d98;
    font-size: 0.78rem;
    font-weight: 650;
    margin-bottom: 7px;
}

.eng-kpi-value {
    color: #17324d;
    font-size: 1.35rem;
    font-weight: 750;
    line-height: 1.1;
    overflow-wrap: anywhere;
}

.eng-kpi-unit {
    color: #829ab1;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 5px;
}


/* =======================================================
   STATUS CARDS
   ======================================================= */

.status-pass {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #166534;
    border-radius: 9px;
    padding: 12px 15px;
    font-weight: 700;
}

.status-review {
    background: #fffbeb;
    border: 1px solid #fde68a;
    color: #92400e;
    border-radius: 9px;
    padding: 12px 15px;
    font-weight: 700;
}

.status-fail {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #991b1b;
    border-radius: 9px;
    padding: 12px 15px;
    font-weight: 700;
}


/* =======================================================
   HERO
   ======================================================= */

.hero {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 14px;
}

.hero-title {
    font-size: 1.75rem;
    font-weight: 750;
    color: #17324d;
    margin-bottom: 3px;
}

.hero-subtitle {
    color: #627d98;
    font-size: 0.9rem;
}


/* =======================================================
   SECTION LABEL
   ======================================================= */

.section-label {
    font-size: 0.82rem;
    font-weight: 750;
    color: #627d98;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-top: 8px;
    margin-bottom: 8px;
}


/* =======================================================
   REACTOR HEADER
   ======================================================= */

.reactor-header {
    background: #eef4f8;
    border-left: 4px solid #244a68;
    padding: 10px 14px;
    border-radius: 7px;
    margin: 10px 0;
}

.reactor-name {
    color: #17324d;
    font-size: 1.05rem;
    font-weight: 750;
}

.reactor-meta {
    color: #627d98;
    font-size: 0.78rem;
}


/* =======================================================
   DATAFRAME
   ======================================================= */

[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}


/* =======================================================
   PROGRESS BAR
   ======================================================= */

div[data-testid="stProgressBar"] {
    margin-top: 4px;
    margin-bottom: 5px;
}


/* =======================================================
   ALERTS
   ======================================================= */

[data-testid="stAlert"] {
    border-radius: 8px !important;
}


/* =======================================================
   CAPTION
   ======================================================= */

.stCaption {
    color: #829ab1 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def fmt_number(value, decimals=2):

    if value is None:
        return "—"

    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return "—"


def engineering_kpi(title, value, unit="", decimals=2):

    if value is None:
        display_value = "—"

    elif isinstance(value, str):
        display_value = value

    else:
        display_value = fmt_number(value, decimals)

    st.markdown(
        f"""
        <div class="eng-kpi">
            <div class="eng-kpi-label">{title}</div>
            <div class="eng-kpi-value">{display_value}</div>
            <div class="eng-kpi-unit">{unit}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def calculate_fill_percent(working_volume, vessel_volume):

    if vessel_volume <= 0:
        return 0.0

    return working_volume / vessel_volume * 100.0


def engineering_status(validation):

    if not validation:
        return "REVIEW"

    overall = validation.get("overall", "REVIEW")

    if overall == "FAIL":
        return "FAIL"

    if overall == "REVIEW":
        return "REVIEW"

    return "PASS"


def status_box(status):

    if status == "PASS":

        st.markdown(
            """
            <div class="status-pass">
                ✓ PASS — Engineering screening acceptable
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif status == "REVIEW":

        st.markdown(
            """
            <div class="status-review">
                ! REVIEW — Additional engineering review required
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="status-fail">
                ✕ FAIL — Engineering limits/checks require correction
            </div>
            """,
            unsafe_allow_html=True,
        )


def get_process_guidance(process_type):

    guidance = {

        "Liquid-Liquid":
            "Focus on blend time, circulation, P/V, tip speed and impeller selection.",

        "Solid-Liquid":
            "Focus on solids suspension, Njs, off-bottom suspension, P/V and clearance.",

        "Gas-Liquid":
            "Focus on gas dispersion, P/V, tip speed, flooding and KLa.",

        "Gas-Liquid-Solid":
            "Focus on gas dispersion, solids suspension, Njs, P/V and KLa.",

        "Crystallization":
            "Focus on suspension, circulation, P/V, shear and crystal quality.",

        "High-Viscosity":
            "Focus on torque, power, laminar mixing and close-clearance impeller selection.",

        "General Mixing":
            "Use P/V, tip speed, Re, Fr, pumping and geometry ratios as primary screening parameters.",
    }

    return guidance.get(
        process_type,
        guidance["General Mixing"],
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ⚗️ Reactor Studio")

    st.caption("Process Engineering Scale-Up Tool")

    st.divider()

    st.markdown("### Study")

    project_name = st.text_input(
        "Project Name",
        "Reactor Scale-Up Study",
    )

    prepared_by = st.text_input(
        "Prepared By",
        "Process Engineering",
    )

    study_mode = st.selectbox(
        "Study Mode",
        [
            "Single Reactor",
            "Lab vs Pilot",
            "Pilot vs Commercial",
            "Lab vs Commercial",
            "Lab vs Pilot vs Commercial",
        ],
    )

    st.divider()

    st.markdown("### Process")

    process_type = st.selectbox(
        "Process Type",
        [
            "Liquid-Liquid",
            "Solid-Liquid",
            "Gas-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
            "High-Viscosity",
            "General Mixing",
        ],
    )

    scaleup_basis = st.selectbox(
        "Scale-Up Basis",
        [
            "Constant P/V",
            "Constant Tip Speed",
            "Constant RPM",
            "Constant Froude Number",
            "Constant Reynolds Number",
            "Constant Pumping / Volume",
            "Constant N/Njs",
            "Constant KLa",
            "User Defined",
        ],
    )

    st.divider()

    st.markdown("### Engineering Focus")

    focus_parameters = [
        "P/V",
        "Tip Speed",
        "Reynolds Number",
        "Power",
        "Q/V",
    ]

    if process_type in [
        "Solid-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
    ]:
        focus_parameters.insert(2, "Njs")

    if process_type in [
        "Gas-Liquid",
        "Gas-Liquid-Solid",
    ]:
        focus_parameters.append("KLa")

    for item in focus_parameters:

        st.checkbox(
            item,
            value=True,
            disabled=True,
            key=f"focus_{item}",
        )


# =========================================================
# REACTOR NAMES
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
# HEADER
# =========================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">
            ⚗️ Reactor Scale-Up Engineering Studio
        </div>
        <div class="hero-subtitle">
            {project_name}
            &nbsp; • &nbsp;
            {process_type}
            &nbsp; • &nbsp;
            {study_mode}
            &nbsp; • &nbsp;
            Scale-Up: {scaleup_basis}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# REACTOR INPUT PANEL
# =========================================================

def reactor_input_panel(name):

    # -----------------------------------------------------
    # DEFAULTS
    # -----------------------------------------------------

    default_volume = (
        1.0
        if name == "Lab"
        else 10.0
        if name == "Pilot"
        else 50.0
    )

    default_diameter = (
        1.0
        if name == "Lab"
        else 2.0
        if name == "Pilot"
        else 3.0
    )

    default_height = (
        1.5
        if name == "Lab"
        else 2.5
        if name == "Pilot"
        else 4.0
    )

    # -----------------------------------------------------
    # REACTOR HEADER
    # -----------------------------------------------------

    st.markdown(
        f"""
        <div class="reactor-header">
            <div class="reactor-name">⚗️ {name} Reactor</div>
            <div class="reactor-meta">
                Process conditions • Vessel geometry • Agitation • Internal arrangement
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # PROCESS CONDITIONS
    # -----------------------------------------------------

    with st.expander(
        "01  Process Conditions",
        expanded=True,
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            working_volume = st.number_input(
                "Working Volume (m³)",
                min_value=0.001,
                value=default_volume,
                step=0.5,
                format="%.3f",
                key=f"{name}_working_volume",
            )

        with c2:

            density = st.number_input(
                "Density (kg/m³)",
                min_value=0.001,
                value=1000.0,
                step=10.0,
                format="%.1f",
                key=f"{name}_density",
            )

        with c3:

            viscosity_mpas = st.number_input(
                "Viscosity (mPa·s)",
                min_value=0.001,
                value=1.0,
                step=0.1,
                format="%.3f",
                key=f"{name}_viscosity",
            )

        with c4:

            surface_tension = st.number_input(
                "Surface Tension (N/m)",
                min_value=0.001,
                value=0.072,
                step=0.001,
                format="%.4f",
                key=f"{name}_surface_tension",
            )

        viscosity_pa_s = viscosity_mpas / 1000.0

    # -----------------------------------------------------
    # GEOMETRY
    # -----------------------------------------------------

    with st.expander(
        "02  Reactor Geometry",
        expanded=True,
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            tank_diameter = st.number_input(
                "Tank ID (m)",
                min_value=0.05,
                value=default_diameter,
                step=0.05,
                format="%.3f",
                key=f"{name}_tank_diameter",
            )

        with c2:

            straight_height = st.number_input(
                "Straight Side Height (m)",
                min_value=0.05,
                value=default_height,
                step=0.05,
                format="%.3f",
                key=f"{name}_straight_height",
            )

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

        k1, k2, k3 = st.columns(3)

        with k1:

            engineering_kpi(
                "Vessel Capacity",
                vessel_volume,
                "m³",
                3,
            )

        with k2:

            engineering_kpi(
                "Liquid Height",
                liquid_height,
                "m",
                3,
            )

        with k3:

            engineering_kpi(
                "Operating Fill",
                fill_percent,
                "%",
                1,
            )

        st.progress(
            min(
                max(fill_percent / 100, 0),
                1,
            )
        )

        if fill_percent > 100:

            st.error(
                "Working volume exceeds calculated vessel capacity."
            )

        elif fill_percent > 90:

            st.warning(
                "High operating fill. Review required headspace."
            )

    # -----------------------------------------------------
    # AGITATION
    # -----------------------------------------------------

    with st.expander(
        "03  Agitation System",
        expanded=True,
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            agitator = st.selectbox(
                "Agitator Type",
                list(AGITATORS.keys()),
                index=1,
                key=f"{name}_agitator",
            )

        agitator_data = AGITATORS.get(
            agitator,
            {},
        )

        ratio = agitator_data.get(
            "default_diameter_ratio",
            0.33,
        )

        default_impeller = max(
            0.05,
            round(tank_diameter * ratio, 3),
        )

        with c2:

            impeller_diameter = st.number_input(
                "Impeller Diameter (m)",
                min_value=0.02,
                value=default_impeller,
                step=0.01,
                format="%.3f",
                key=f"{name}_impeller",
            )

        with c3:

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{name}_impellers",
            )

        with c4:

            rpm = st.number_input(
                "Agitator Speed (RPM)",
                min_value=0.1,
                value=150.0,
                step=5.0,
                format="%.1f",
                key=f"{name}_rpm",
            )

        k1, k2, k3, k4 = st.columns(4)

        with k1:

            engineering_kpi(
                "Flow Pattern",
                agitator_data.get("flow", "—"),
                "Flow type",
            )

        with k2:

            engineering_kpi(
                "Blade Count",
                agitator_data.get("blades", "—"),
                "count",
                0,
            )

        with k3:

            engineering_kpi(
                "Power Number",
                agitator_data.get("np"),
                "Np",
                3,
            )

        with k4:

            engineering_kpi(
                "Pumping Number",
                agitator_data.get("nq"),
                "Nq",
                3,
            )

        st.caption(
            agitator_data.get(
                "description",
                "",
            )
        )

    # -----------------------------------------------------
    # INTERNAL ARRANGEMENT
    # -----------------------------------------------------

    with st.expander(
        "04  Internal Arrangement",
        expanded=False,
    ):

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

        with c2:

            impeller_clearance = st.number_input(
                "Bottom Clearance (m)",
                min_value=0.0,
                value=max(
                    0.05,
                    tank_diameter * 0.20,
                ),
                step=0.01,
                format="%.3f",
                key=f"{name}_clearance",
            )

        with c3:

            vortex_depth = st.number_input(
                "Vortex Depth (m)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                format="%.3f",
                key=f"{name}_vortex",
            )

        with c4:

            engineering_kpi(
                "Impeller / Tank",
                impeller_diameter / tank_diameter
                if tank_diameter > 0
                else None,
                "D/T",
                3,
            )

    # -----------------------------------------------------
    # CALCULATION
    # -----------------------------------------------------

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

        result.update(
            {
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
                "pumping_per_volume": result.get("qv_1_h"),
            }
        )

        result["validation"] = validate_reactor(
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
# TABS
# =========================================================

(
    tab_setup,
    tab_performance,
    tab_scaleup,
    tab_validation,
    tab_3d,
    tab_insights,
) = st.tabs(
    [
        "📐 Setup",
        "📊 Performance",
        "📈 Scale-Up",
        "✓ Validation",
        "🧊 3D View",
        "💡 Insights",
    ]
)


# =========================================================
# SETUP
# =========================================================

with tab_setup:

    st.markdown("## Reactor Configuration")

    st.caption(
        "Define process properties, vessel geometry and agitation parameters."
    )

    reactors = []

    for name in reactor_names:

        reactors.append(
            reactor_input_panel(name)
        )


# =========================================================
# OVERALL STATUS
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

s1, s2, s3, s4 = st.columns(4)

with s1:

    engineering_kpi(
        "Reactors",
        len(reactors),
        "in study",
        0,
    )

with s2:

    engineering_kpi(
        "Process",
        process_type,
        "",
    )

with s3:

    engineering_kpi(
        "Scale-Up Basis",
        scaleup_basis,
        "",
    )

with s4:

    engineering_kpi(
        "Status",
        overall_status,
        "engineering screening",
    )


# =========================================================
# PERFORMANCE
# =========================================================

with tab_performance:

    st.markdown("## Mixing Performance")

    st.info(
        f"**Engineering focus:** {get_process_guidance(process_type)}"
    )

    for reactor in reactors:

        st.markdown(
            f"### {reactor['name']}"
        )

        # -------------------------------------------------
        # PRIMARY KPIs
        # -------------------------------------------------

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            engineering_kpi(
                "Agitator Power",
                reactor.get("power_kw"),
                "kW",
                2,
            )

        with p2:

            # -------------------------------------------------
            # IMPORTANT:
            # P/V SHOULD BE SHOWN IN kW/m³
            # if power_volume is stored as kW/m³.
            # -------------------------------------------------

            power_volume = reactor.get(
                "power_volume"
            )

            engineering_kpi(
                "Power / Volume",
                power_volume,
                "kW/m³",
                4,
            )

        with p3:

            engineering_kpi(
                "Tip Speed",
                reactor.get("tip_speed"),
                "m/s",
                2,
            )

        with p4:

            engineering_kpi(
                "Reynolds Number",
                reactor.get("Re"),
                "dimensionless",
                0,
            )

        st.markdown("")

        # -------------------------------------------------
        # SECONDARY KPIs
        # -------------------------------------------------

        p5, p6, p7, p8 = st.columns(4)

        with p5:

            engineering_kpi(
                "Froude Number",
                reactor.get("Fr"),
                "dimensionless",
                4,
            )

        with p6:

            engineering_kpi(
                "Pumping Capacity",
                reactor.get("pumping_m3_h"),
                "m³/h",
                2,
            )

        with p7:

            engineering_kpi(
                "Q / V",
                reactor.get("qv_1_h"),
                "1/h",
                3,
            )

        with p8:

            engineering_kpi(
                "Turnover Time",
                reactor.get("turnover_time_min"),
                "min",
                2,
            )

        # -------------------------------------------------
        # DETAILED PARAMETERS
        # -------------------------------------------------

        with st.expander(
            "View detailed engineering parameters"
        ):

            data = pd.DataFrame(
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
                        "Impeller Clearance",
                        "Vessel Bottom",
                        "Vessel Top",
                    ],

                    "Value": [
                        fmt_number(
                            reactor["working_volume"],
                            3,
                        ),

                        fmt_number(
                            reactor["vessel_volume"],
                            3,
                        ),

                        fmt_number(
                            reactor["liquid_height_m"],
                            3,
                        ),

                        fmt_number(
                            reactor["tank_diameter_m"],
                            3,
                        ),

                        fmt_number(
                            reactor["straight_height_m"],
                            3,
                        ),

                        fmt_number(
                            reactor["impeller_diameter_m"],
                            3,
                        ),

                        reactor["number_impellers"],

                        fmt_number(
                            reactor["rpm"],
                            1,
                        ),

                        fmt_number(
                            reactor["density"],
                            1,
                        ),

                        fmt_number(
                            reactor["viscosity_pa_s"],
                            5,
                        ),

                        fmt_number(
                            reactor["surface_tension_n_m"],
                            4,
                        ),

                        reactor["number_baffles"],

                        fmt_number(
                            reactor["impeller_clearance_m"],
                            3,
                        ),

                        reactor["bottom_type"],

                        reactor["top_type"],
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
                        "m",
                        "type",
                        "type",
                    ],
                }
            )

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# SCALE-UP
# =========================================================

with tab_scaleup:

    st.markdown("## Scale-Up Analysis")

    if len(reactors) < 2:

        st.info(
            "Select a multi-reactor study mode from the sidebar "
            "to perform scale-up calculations."
        )

    else:

        base = reactors[0]
        target = reactors[1]

        st.markdown(
            f"### {base['name']} → {target['name']}"
        )

        scale_ratio = (
            target["working_volume"]
            / base["working_volume"]
            if base["working_volume"] > 0
            else 0
        )

        diameter_ratio = (
            target["tank_diameter_m"]
            / base["tank_diameter_m"]
            if base["tank_diameter_m"] > 0
            else 0
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            engineering_kpi(
                "Base Volume",
                base["working_volume"],
                "m³",
                3,
            )

        with c2:

            engineering_kpi(
                "Target Volume",
                target["working_volume"],
                "m³",
                3,
            )

        with c3:

            engineering_kpi(
                "Volume Ratio",
                scale_ratio,
                "×",
                2,
            )

        with c4:

            engineering_kpi(
                "Tank Diameter Ratio",
                diameter_ratio,
                "×",
                2,
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
                "target_rpm": None,
                "target_tip_speed": None,
                "target_power_volume": None,
                "target_qv": None,
                "message": str(exc),
            }

        st.markdown("### Target Operating Conditions")

        r1, r2, r3, r4 = st.columns(4)

        with r1:

            engineering_kpi(
                "Criterion",
                scaleup_basis,
                "",
            )

        with r2:

            engineering_kpi(
                "Target RPM",
                scale_result.get(
                    "target_rpm"
                ),
                "RPM",
                1,
            )

        with r3:

            engineering_kpi(
                "Target Tip Speed",
                scale_result.get(
                    "target_tip_speed"
                ),
                "m/s",
                2,
            )

        with r4:

            engineering_kpi(
                "Target P/V",
                scale_result.get(
                    "target_power_volume"
                ),
                "kW/m³",
                4,
            )

        if scale_result.get("message"):

            st.info(
                scale_result["message"]
            )


# =========================================================
# VALIDATION
# =========================================================

with tab_validation:

    st.markdown("## Engineering Validation")

    status_box(overall_status)

    st.markdown("")

    for reactor in reactors:

        validation = reactor.get(
            "validation",
            {},
        )

        st.markdown(
            f"### {reactor['name']}"
        )

        v1, v2, v3 = st.columns(3)

        with v1:

            engineering_kpi(
                "Status",
                validation.get(
                    "overall",
                    "REVIEW",
                ),
                "screening",
            )

        with v2:

            engineering_kpi(
                "Failures",
                validation.get(
                    "failures",
                    0,
                ),
                "count",
                0,
            )

        with v3:

            engineering_kpi(
                "Warnings",
                validation.get(
                    "warnings",
                    0,
                ),
                "count",
                0,
            )

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

            st.caption(
                "No validation checks available."
            )


# =========================================================
# 3D VIEW
# =========================================================

with tab_3d:

    st.markdown("## 3D Reactor View")

    selected_name = st.selectbox(
        "Select Reactor",
        [
            r["name"]
            for r in reactors
        ],
        key="3d_reactor",
    )

    selected = next(
        r
        for r in reactors
        if r["name"] == selected_name
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        engineering_kpi(
            "Tank ID",
            selected["tank_diameter_m"],
            "m",
            3,
        )

    with c2:

        engineering_kpi(
            "Liquid Height",
            selected["liquid_height_m"],
            "m",
            3,
        )

    with c3:

        engineering_kpi(
            "Impeller",
            selected["impeller_diameter_m"],
            "m",
            3,
        )

    with c4:

        engineering_kpi(
            "Speed",
            selected["rpm"],
            "RPM",
            1,
        )

    st.markdown("")

    try:

        fig = create_reactor_animation(
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

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "displaylogo": False,
                },
            )

    except Exception as exc:

        st.error(
            f"3D visualization error: {exc}"
        )


# =========================================================
# ENGINEERING INSIGHTS
# =========================================================

with tab_insights:

    st.markdown("## Engineering Insights")

    st.info(
        f"**{process_type}:** "
        f"{get_process_guidance(process_type)}"
    )

    for reactor in reactors:

        st.markdown(
            f"### {reactor['name']}"
        )

        dt = reactor.get("D_T")
        re = reactor.get("Re")

        fill = calculate_fill_percent(
            reactor["working_volume"],
            reactor["vessel_volume"],
        )

        # -------------------------------------------------
        # IMPELLER RATIO
        # -------------------------------------------------

        if dt is not None:

            if dt < 0.20:

                st.warning(
                    "Impeller diameter is relatively small. "
                    "Review circulation and blend performance."
                )

            elif dt > 0.60:

                st.warning(
                    "Large impeller/tank ratio. Review power, "
                    "torque and mechanical loading."
                )

            else:

                st.success(
                    "Impeller/tank ratio is within the screening range."
                )

        # -------------------------------------------------
        # REYNOLDS NUMBER
        # -------------------------------------------------

        if re is not None:

            if re < 10:

                st.warning(
                    "Laminar regime indicated. Verify the applicable "
                    "power correlation."
                )

            elif re < 10000:

                st.warning(
                    "Transitional mixing regime. Correlation selection "
                    "requires additional attention."
                )

            else:

                st.success(
                    "Turbulent mixing regime indicated."
                )

        # -------------------------------------------------
        # FILL
        # -------------------------------------------------

        if fill > 90:

            st.warning(
                "High operating fill. Confirm required headspace."
            )

        elif fill < 25:

            st.warning(
                "Low operating fill. Confirm impeller immersion."
            )

        else:

            st.success(
                "Operating fill is within the screening range."
            )

        # -------------------------------------------------
        # PROCESS-SPECIFIC
        # -------------------------------------------------

        if process_type in [
            "Solid-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
        ]:

            st.info(
                "Solids service: validate Njs, off-bottom suspension "
                "and solids distribution using suitable correlations "
                "or pilot data."
            )

        if process_type in [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ]:

            st.info(
                "Gas-liquid service: validate gas dispersion, flooding, "
                "gas holdup and KLa using appropriate correlations/test data."
            )

        if process_type == "High-Viscosity":

            st.info(
                "High-viscosity service: verify torque, motor sizing, "
                "gearbox limits and applicable laminar power correlation."
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Engineering screening tool | Validate Np/Nq, Njs, KLa, "
    "blend time, flooding, vessel geometry and mechanical design "
    "against applicable literature, vendor data, pilot trials "
    "and site engineering standards before final design."
)
