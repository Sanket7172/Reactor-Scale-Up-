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
# PROFESSIONAL LIGHT ENGINEERING THEME
# =========================================================

st.markdown(
    """
<style>

/* =======================================================
   GLOBAL
   ======================================================= */

.stApp {
    background: #f3f6fa;
}

.block-container {
    max-width: 1550px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
}


/* =======================================================
   HEADINGS
   ======================================================= */

h1 {
    color: #102a43 !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
}

h2 {
    color: #102a43 !important;
    font-weight: 800 !important;
}

h3 {
    color: #173f5f !important;
    font-weight: 750 !important;
}

h4 {
    color: #243b53 !important;
    font-weight: 700 !important;
}


/* =======================================================
   SIDEBAR
   ======================================================= */

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #d9e2ec;
}

[data-testid="stSidebar"] * {
    color: #243b53;
}


/* =======================================================
   LABELS
   ======================================================= */

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
label {
    color: #243b53 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}


/* =======================================================
   INPUT FIELDS
   ======================================================= */

div[data-baseweb="input"] {
    background: #ffffff !important;
    border: 1px solid #bcccdc !important;
    border-radius: 10px !important;
}

div[data-baseweb="input"]:focus-within {
    border: 2px solid #2f80ed !important;
}

input {
    color: #102a43 !important;
    background: #ffffff !important;
    font-weight: 650 !important;
}


/* =======================================================
   SELECTBOX
   ======================================================= */

div[data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1px solid #bcccdc !important;
    border-radius: 10px !important;
    min-height: 44px;
}

div[data-baseweb="select"] * {
    color: #102a43 !important;
}

div[data-baseweb="select"] span {
    font-weight: 650 !important;
}


/* =======================================================
   CONTAINERS
   ======================================================= */

div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #d9e2ec !important;
    border-radius: 16px !important;
    background: #ffffff !important;
    box-shadow: 0 5px 18px rgba(16,42,67,0.05);
}


/* =======================================================
   TABS
   ======================================================= */

div[data-baseweb="tab-list"] {
    gap: 8px;
    padding: 7px;
    background: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 14px;
}

button[data-baseweb="tab"] {
    color: #486581 !important;
    font-weight: 750 !important;
    border-radius: 9px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #173f5f !important;
    color: #ffffff !important;
}


/* =======================================================
   BUTTONS
   ======================================================= */

.stButton > button {
    width: 100%;
    min-height: 44px;
    border-radius: 10px;
    background: #ffffff;
    border: 1px solid #bcccdc;
    color: #102a43 !important;
    font-weight: 750;
}


/* =======================================================
   DATAFRAME
   ======================================================= */

[data-testid="stDataFrame"] {
    border: 1px solid #d9e2ec;
    border-radius: 12px;
}


/* =======================================================
   ENGINEERING KPI CARD
   ======================================================= */

.engineering-kpi {
    background: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 15px;
    padding: 17px 18px;
    min-height: 118px;
    box-shadow: 0 4px 14px rgba(16,42,67,0.055);
}

.engineering-kpi-title {
    color: #486581;
    font-size: 0.86rem;
    font-weight: 750;
    margin-bottom: 9px;
    line-height: 1.25;
}

.engineering-kpi-number {
    color: #102a43;
    font-size: 1.65rem;
    font-weight: 850;
    line-height: 1.05;
    white-space: normal;
    overflow-wrap: anywhere;
}

.engineering-kpi-unit {
    color: #627d98;
    font-size: 0.84rem;
    font-weight: 700;
    margin-top: 7px;
    line-height: 1.15;
}


/* =======================================================
   SECTION HEADER
   ======================================================= */

.section-header {
    color: #173f5f;
    font-size: 1.05rem;
    font-weight: 800;
    margin-top: 6px;
    margin-bottom: 10px;
}


/* =======================================================
   INFO / WARNING / SUCCESS
   ======================================================= */

[data-testid="stAlert"] {
    border-radius: 12px !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
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
        <div class="engineering-kpi">
            <div class="engineering-kpi-title">
                {title}
            </div>
            <div class="engineering-kpi-number">
                {display_value}
            </div>
            <div class="engineering-kpi-unit">
                {unit}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def calculate_fill_percent(working_volume, vessel_volume):

    if vessel_volume <= 0:
        return 0.0

    return (
        working_volume
        / vessel_volume
        * 100.0
    )


def engineering_status(validation):

    if not validation:
        return "REVIEW"

    if validation.get("overall") == "FAIL":
        return "FAIL"

    if validation.get("overall") == "REVIEW":
        return "REVIEW"

    return "PASS"


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

    st.caption(
        "Process Engineering Scale-Up Dashboard"
    )

    st.divider()

    st.markdown("### 📁 Project")

    project_name = st.text_input(
        "Project Name",
        "Reactor Scale-Up Study",
    )

    prepared_by = st.text_input(
        "Prepared By",
        "Process Engineering",
    )

    st.divider()

    st.markdown("### ⚙️ Study Configuration")

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

    process_type = st.selectbox(
        "Reaction / Process Type",
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
        "Primary Scale-Up Basis",
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

    st.markdown("### 🎯 Engineering Focus")

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
        focus_parameters.insert(
            2,
            "Njs",
        )

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
# HEADER
# =========================================================

st.title(
    "⚗️ Reactor Scale-Up Engineering Studio"
)

st.caption(
    f"{project_name}  •  {process_type}  •  "
    f"{study_mode}  •  Scale-Up: {scaleup_basis}"
)

st.divider()


# =========================================================
# REACTOR NAMES
# =========================================================

if study_mode == "Single Reactor":

    reactor_names = [
        "Reactor"
    ]

elif study_mode == "Lab vs Pilot":

    reactor_names = [
        "Lab",
        "Pilot"
    ]

elif study_mode == "Pilot vs Commercial":

    reactor_names = [
        "Pilot",
        "Commercial"
    ]

elif study_mode == "Lab vs Commercial":

    reactor_names = [
        "Lab",
        "Commercial"
    ]

else:

    reactor_names = [
        "Lab",
        "Pilot",
        "Commercial"
    ]


# =========================================================
# REACTOR INPUT PANEL
# =========================================================

def reactor_input_panel(name):

    st.markdown(
        f"### ⚗️ {name} Reactor"
    )

    with st.container(border=True):

        # -------------------------------------------------
        # PROCESS CONDITIONS
        # -------------------------------------------------

        st.markdown(
            "#### 1. Process Conditions"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            working_volume = st.number_input(
                "Working Volume",
                min_value=0.001,
                value=1.0
                if name == "Lab"
                else 10.0
                if name == "Pilot"
                else 50.0,
                step=0.5,
                format="%.3f",
                key=f"{name}_working_volume",
            )

            st.caption("m³")

        with c2:

            density = st.number_input(
                "Density",
                min_value=0.001,
                value=1000.0,
                step=10.0,
                format="%.1f",
                key=f"{name}_density",
            )

            st.caption("kg/m³")

        with c3:

            viscosity_mpas = st.number_input(
                "Viscosity",
                min_value=0.001,
                value=1.0,
                step=0.1,
                format="%.3f",
                key=f"{name}_viscosity",
            )

            st.caption("mPa·s")

        with c4:

            surface_tension = st.number_input(
                "Surface Tension",
                min_value=0.001,
                value=0.072,
                step=0.001,
                format="%.4f",
                key=f"{name}_surface_tension",
            )

            st.caption("N/m")

        viscosity_pa_s = (
            viscosity_mpas / 1000.0
        )

        st.divider()

        # -------------------------------------------------
        # VESSEL GEOMETRY
        # -------------------------------------------------

        st.markdown(
            "#### 2. Reactor Geometry"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            tank_diameter = st.number_input(
                "Tank Internal Diameter",
                min_value=0.05,
                value=1.0
                if name == "Lab"
                else 2.0
                if name == "Pilot"
                else 3.0,
                step=0.05,
                format="%.3f",
                key=f"{name}_tank_diameter",
            )

            st.caption("m")

        with c2:

            straight_height = st.number_input(
                "Straight Side Height",
                min_value=0.05,
                value=1.5
                if name == "Lab"
                else 2.5
                if name == "Pilot"
                else 4.0,
                step=0.05,
                format="%.3f",
                key=f"{name}_straight_height",
            )

            st.caption("m")

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

            engineering_kpi(
                "Vessel Capacity",
                vessel_volume,
                "m³",
                3,
            )

        with g2:

            engineering_kpi(
                "Liquid Height",
                liquid_height,
                "m",
                3,
            )

        with g3:

            engineering_kpi(
                "Operating Fill",
                fill_percent,
                "%",
                1,
            )

        st.progress(
            min(
                max(
                    fill_percent / 100,
                    0
                ),
                1,
            )
        )

        if fill_percent > 100:

            st.error(
                "Working volume exceeds calculated vessel capacity."
            )

        elif fill_percent > 90:

            st.warning(
                "High operating fill. Review headspace."
            )

        st.divider()

        # -------------------------------------------------
        # AGITATION
        # -------------------------------------------------

        st.markdown(
            "#### 3. Agitation System"
        )

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
            round(
                tank_diameter * ratio,
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
                key=f"{name}_impeller",
            )

            st.caption("m")

        with c3:

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{name}_impellers",
            )

            st.caption("count")

        with c4:

            rpm = st.number_input(
                "Agitator Speed",
                min_value=0.1,
                value=150.0,
                step=5.0,
                format="%.1f",
                key=f"{name}_rpm",
            )

            st.caption("RPM")

        i1, i2, i3, i4 = st.columns(4)

        with i1:

            engineering_kpi(
                "Flow Pattern",
                agitator_data.get(
                    "flow",
                    "—",
                ),
                "Flow type",
            )

        with i2:

            engineering_kpi(
                "Blade Count",
                agitator_data.get(
                    "blades",
                    "—",
                ),
                "count",
                0,
            )

        with i3:

            engineering_kpi(
                "Power Number (Np)",
                agitator_data.get(
                    "np"
                ),
                "dimensionless",
                3,
            )

        with i4:

            engineering_kpi(
                "Pumping Number (Nq)",
                agitator_data.get(
                    "nq"
                ),
                "dimensionless",
                3,
            )

        st.info(
            f"**{agitator}** — "
            f"{agitator_data.get('description', '')}"
        )

        st.divider()

        # -------------------------------------------------
        # INTERNAL ARRANGEMENT
        # -------------------------------------------------

        st.markdown(
            "#### 4. Internal Arrangement"
        )

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

            st.caption("count")

        with c2:

            impeller_clearance = st.number_input(
                "Bottom Clearance",
                min_value=0.0,
                value=max(
                    0.05,
                    tank_diameter * 0.20,
                ),
                step=0.01,
                format="%.3f",
                key=f"{name}_clearance",
            )

            st.caption("m")

        with c3:

            vortex_depth = st.number_input(
                "Vortex Depth",
                min_value=0.0,
                value=0.0,
                step=0.01,
                format="%.3f",
                key=f"{name}_vortex",
            )

            st.caption("m")

        with c4:

            engineering_kpi(
                "D / T Ratio",
                impeller_diameter / tank_diameter,
                "dimensionless",
                3,
            )

        # -------------------------------------------------
        # CALCULATE
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
# SETUP
# =========================================================

with tab_setup:

    st.markdown(
        "## Reactor Configuration"
    )

    st.caption(
        "Enter vessel geometry, process properties and agitator configuration."
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
# SUMMARY
# =========================================================

st.divider()

st.markdown(
    "## 📌 Dashboard Summary"
)

s1, s2, s3, s4 = st.columns(4)

with s1:

    engineering_kpi(
        "Reactors in Study",
        len(reactors),
        "reactor(s)",
        0,
    )

with s2:

    engineering_kpi(
        "Process Type",
        process_type,
        "process",
    )

with s3:

    engineering_kpi(
        "Scale-Up Basis",
        scaleup_basis,
        "criterion",
    )

with s4:

    engineering_kpi(
        "Engineering Status",
        overall_status,
        "screening status",
    )


# =========================================================
# PERFORMANCE TAB
# =========================================================

with tab_performance:

    st.markdown(
        "## 📊 Mixing & Agitation Performance"
    )

    st.info(
        f"**Process focus — {process_type}:** "
        f"{get_process_guidance(process_type)}"
    )

    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        with st.container(border=True):

            # -------------------------------------------------
            # PRIMARY KPIs
            # -------------------------------------------------

            st.markdown(
                '<div class="section-header">Primary Mixing Performance</div>',
                unsafe_allow_html=True,
            )

            p1, p2, p3, p4 = st.columns(4)

            with p1:

                engineering_kpi(
                    "Agitator Power",
                    reactor.get("power_kw"),
                    "kW",
                    2,
                )

            with p2:

                engineering_kpi(
                    "Power / Volume",
                    reactor.get("power_volume"),
                    "W/m³",
                    2,
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

            st.markdown("")

            # -------------------------------------------------
            # GEOMETRY / MIXING
            # -------------------------------------------------

            p9, p10, p11, p12 = st.columns(4)

            with p9:

                engineering_kpi(
                    "Impeller / Tank",
                    reactor.get("D_T"),
                    "D/T — dimensionless",
                    3,
                )

            with p10:

                engineering_kpi(
                    "Liquid Height / Tank",
                    reactor.get("H_T"),
                    "H/T — dimensionless",
                    3,
                )

            with p11:

                engineering_kpi(
                    "Impeller Clearance / Tank",
                    reactor.get("clearance_T"),
                    "C/T — dimensionless",
                    3,
                )

            with p12:

                engineering_kpi(
                    "Mixing Regime",
                    reactor.get(
                        "mixing_regime",
                        "—",
                    ),
                    "flow regime",
                )

            st.divider()

            # -------------------------------------------------
            # FULL PARAMETER TABLE
            # -------------------------------------------------

            st.markdown(
                "#### Detailed Engineering Parameters"
            )

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
                        str(
                            reactor["number_impellers"]
                        ),
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
                        str(
                            reactor["number_baffles"]
                        ),
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
# SCALE-UP TAB
# =========================================================

with tab_scaleup:

    st.markdown(
        "## 📈 Scale-Up Analysis"
    )

    if len(reactors) < 2:

        st.info(
            "Select a multi-reactor study mode to perform scale-up analysis."
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

                scale_ratio = (
                    target["working_volume"]
                    / base["working_volume"]
                    if base["working_volume"] > 0
                    else 0
                )

                engineering_kpi(
                    "Volume Scale Ratio",
                    scale_ratio,
                    "×",
                    2,
                )

            with c4:

                diameter_ratio = (
                    target["tank_diameter_m"]
                    / base["tank_diameter_m"]
                    if base["tank_diameter_m"] > 0
                    else 0
                )

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

            r1, r2, r3, r4 = st.columns(4)

            with r1:

                engineering_kpi(
                    "Scale-Up Criterion",
                    scaleup_basis,
                    "criterion",
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
                    "W/m³",
                    2,
                )

            if scale_result.get("message"):

                st.info(
                    scale_result["message"]
                )


# =========================================================
# VALIDATION TAB
# =========================================================

with tab_validation:

    st.markdown(
        "## ✅ Engineering Validation"
    )

    if overall_status == "PASS":

        st.success(
            "Overall screening status: PASS"
        )

    elif overall_status == "REVIEW":

        st.warning(
            "Overall screening status: REVIEW"
        )

    else:

        st.error(
            "Overall screening status: FAIL"
        )

    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        validation = reactor.get(
            "validation",
            {},
        )

        with st.container(border=True):

            c1, c2, c3 = st.columns(3)

            with c1:

                engineering_kpi(
                    "Validation Status",
                    validation.get(
                        "overall",
                        "REVIEW",
                    ),
                    "screening",
                )

            with c2:

                engineering_kpi(
                    "Failures",
                    validation.get(
                        "failures",
                        0,
                    ),
                    "count",
                    0,
                )

            with c3:

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
                            c["severity"]
                            for c in checks
                        ],
                        "Engineering Check": [
                            c["message"]
                            for c in checks
                        ],
                    }
                )

                st.dataframe(
                    validation_table,
                    use_container_width=True,
                    hide_index=True,
                )


# =========================================================
# 3D TAB
# =========================================================

with tab_3d:

    st.markdown(
        "## 🧊 3D Reactor Visualization"
    )

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
            "Tank Diameter",
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
            "Impeller Diameter",
            selected["impeller_diameter_m"],
            "m",
            3,
        )

    with c4:

        engineering_kpi(
            "Agitator Speed",
            selected["rpm"],
            "RPM",
            1,
        )

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

    st.markdown(
        "## 💡 Engineering Insights"
    )

    st.info(
        f"**{process_type}:** "
        f"{get_process_guidance(process_type)}"
    )

    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        with st.container(border=True):

            dt = reactor.get("D_T")
            re = reactor.get("Re")
            fill = calculate_fill_percent(
                reactor["working_volume"],
                reactor["vessel_volume"],
            )

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

            if process_type in [
                "Solid-Liquid",
                "Gas-Liquid-Solid",
                "Crystallization",
            ]:

                st.info(
                    "For solids-containing systems, validate Njs using "
                    "an appropriate solids-suspension correlation or pilot data."
                )

            if process_type in [
                "Gas-Liquid",
                "Gas-Liquid-Solid",
            ]:

                st.info(
                    "For gas-liquid systems, validate gas dispersion, "
                    "flooding and KLa using appropriate correlations/test data."
                )

            if process_type == "High-Viscosity":

                st.info(
                    "For high-viscosity service, verify torque, motor sizing, "
                    "gearbox limitations and laminar power correlation."
                )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "⚠️ Preliminary engineering screening tool. "
    "Validate Np/Nq, Njs, KLa, blend time, flooding, vessel geometry "
    "and mechanical design against applicable literature, vendor data, "
    "pilot trials and site engineering standards before final design."
)
