```python
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
    page_title="Reactor Scale-Up Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# MODERN UI CSS
# =========================================================

st.markdown(
    """
<style>

/* =========================================================
   GLOBAL
   ========================================================= */

.stApp {
    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(99,102,241,0.08),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 5%,
            rgba(6,182,212,0.08),
            transparent 25%
        ),
        #f5f7fb;
}

.block-container {
    max-width: 1550px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

html,
body,
[class*="css"] {
    font-family:
        "Inter",
        "Segoe UI",
        Arial,
        sans-serif;
}


/* =========================================================
   REMOVE DEFAULT STREAMLIT DECORATION
   ========================================================= */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #111827 0%,
            #172554 100%
        );

    border-right: none;
}

[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

[data-testid="stSidebar"] hr {
    border-top: 1px solid rgba(255,255,255,0.12);
}

[data-testid="stSidebar"] input {
    background: rgba(255,255,255,0.08) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: white !important;
}


/* =========================================================
   TITLES
   ========================================================= */

h1 {
    color: #111827 !important;
    font-weight: 800 !important;
}

h2 {
    color: #111827 !important;
    font-weight: 800 !important;
}

h3 {
    color: #1f2937 !important;
    font-weight: 750 !important;
}

h4 {
    color: #374151 !important;
}


/* =========================================================
   INPUTS
   ========================================================= */

div[data-baseweb="input"] {
    background: white !important;
    border: 1px solid #dbe2ea !important;
    border-radius: 10px !important;
}

div[data-baseweb="input"]:focus-within {
    border: 2px solid #6366f1 !important;
}

input {
    color: #111827 !important;
    font-weight: 600 !important;
    background: white !important;
}


/* =========================================================
   SELECTBOX
   ========================================================= */

div[data-baseweb="select"] > div {
    background: white !important;
    border: 1px solid #dbe2ea !important;
    border-radius: 10px !important;
    min-height: 42px;
}

div[data-baseweb="select"] * {
    color: #111827 !important;
}


/* =========================================================
   LABELS
   ========================================================= */

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p {
    color: #374151 !important;
    font-weight: 650 !important;
}


/* =========================================================
   HERO
   ========================================================= */

.hero {
    position: relative;

    background:
        linear-gradient(
            135deg,
            #312e81 0%,
            #4f46e5 45%,
            #0891b2 100%
        );

    border-radius: 24px;

    padding: 28px 32px;

    margin-bottom: 22px;

    overflow: hidden;

    box-shadow:
        0 18px 45px rgba(49,46,129,0.20);
}

.hero:after {
    content: "";
    position: absolute;

    width: 260px;
    height: 260px;

    right: -70px;
    top: -100px;

    border-radius: 50%;

    background: rgba(255,255,255,0.10);
}

.hero-title {
    color: white;

    font-size: 2rem;

    font-weight: 850;

    letter-spacing: -0.7px;
}

.hero-subtitle {
    color: rgba(255,255,255,0.82);

    margin-top: 6px;

    font-size: 0.92rem;
}


/* =========================================================
   KPI CARDS
   ========================================================= */

.kpi-card {
    position: relative;

    background: white;

    border-radius: 18px;

    padding: 18px;

    min-height: 120px;

    border: 1px solid #e5e7eb;

    box-shadow:
        0 8px 25px rgba(15,23,42,0.06);

    overflow: hidden;
}

.kpi-card:before {
    content: "";

    position: absolute;

    left: 0;
    top: 0;

    width: 5px;
    height: 100%;

    background: #6366f1;
}

.kpi-blue:before {
    background: linear-gradient(
        180deg,
        #3b82f6,
        #06b6d4
    );
}

.kpi-purple:before {
    background: linear-gradient(
        180deg,
        #8b5cf6,
        #6366f1
    );
}

.kpi-green:before {
    background: linear-gradient(
        180deg,
        #10b981,
        #22c55e
    );
}

.kpi-orange:before {
    background: linear-gradient(
        180deg,
        #f59e0b,
        #f97316
    );
}

.kpi-red:before {
    background: linear-gradient(
        180deg,
        #ef4444,
        #f43f5e
    );
}

.kpi-label {
    color: #64748b;

    font-size: 0.78rem;

    font-weight: 700;

    text-transform: uppercase;

    letter-spacing: 0.5px;
}

.kpi-value {
    color: #111827;

    font-size: 1.65rem;

    font-weight: 850;

    margin-top: 9px;

    line-height: 1.1;

    overflow-wrap: anywhere;
}

.kpi-unit {
    color: #94a3b8;

    font-size: 0.78rem;

    font-weight: 600;

    margin-top: 6px;
}


/* =========================================================
   SECTION
   ========================================================= */

.section-title {
    display: flex;

    align-items: center;

    gap: 10px;

    color: #111827;

    font-size: 1.25rem;

    font-weight: 800;

    margin-top: 22px;

    margin-bottom: 12px;
}

.section-dot {
    width: 9px;
    height: 9px;

    border-radius: 50%;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #06b6d4
        );
}


/* =========================================================
   REACTOR CARD
   ========================================================= */

.reactor-card {
    background: white;

    border-radius: 20px;

    border: 1px solid #e5e7eb;

    padding: 20px;

    margin-bottom: 16px;

    box-shadow:
        0 10px 28px rgba(15,23,42,0.055);
}

.reactor-card-header {
    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 16px;
}

.reactor-title {
    color: #111827;

    font-size: 1.12rem;

    font-weight: 800;
}

.reactor-subtitle {
    color: #94a3b8;

    font-size: 0.78rem;

    margin-top: 3px;
}


/* =========================================================
   STATUS
   ========================================================= */

.status {
    display: inline-block;

    padding: 6px 12px;

    border-radius: 999px;

    font-size: 0.72rem;

    font-weight: 800;

    letter-spacing: 0.5px;
}

.status-pass {
    color: #047857;

    background: #d1fae5;
}

.status-review {
    color: #b45309;

    background: #fef3c7;
}

.status-fail {
    color: #b91c1c;

    background: #fee2e2;
}


/* =========================================================
   EXPANDERS
   ========================================================= */

[data-testid="stExpander"] {
    background: white;

    border: 1px solid #e5e7eb !important;

    border-radius: 12px !important;

    margin-bottom: 10px;
}

[data-testid="stExpander"] summary {
    color: #374151 !important;

    font-weight: 700 !important;
}


/* =========================================================
   TABS
   ========================================================= */

div[data-baseweb="tab-list"] {
    background: white;

    padding: 6px;

    border-radius: 14px;

    border: 1px solid #e5e7eb;

    gap: 5px;

    margin-bottom: 20px;
}

button[data-baseweb="tab"] {
    border-radius: 10px !important;

    color: #64748b !important;

    font-weight: 700 !important;

    padding: 8px 14px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background:
        linear-gradient(
            135deg,
            #4f46e5,
            #0891b2
        ) !important;

    color: white !important;
}


/* =========================================================
   BUTTONS
   ========================================================= */

.stButton > button {
    border-radius: 10px;

    border: none;

    background:
        linear-gradient(
            135deg,
            #4f46e5,
            #6366f1
        );

    color: white !important;

    font-weight: 700;

    min-height: 42px;

    box-shadow:
        0 5px 14px rgba(79,70,229,0.20);
}


/* =========================================================
   INFO / WARNING
   ========================================================= */

[data-testid="stAlert"] {
    border-radius: 12px !important;
}


/* =========================================================
   TABLE
   ========================================================= */

[data-testid="stDataFrame"] {
    border-radius: 12px;

    border: 1px solid #e5e7eb;
}


/* =========================================================
   METRIC COMPARISON
   ========================================================= */

.compare-card {
    background: white;

    border-radius: 18px;

    padding: 20px;

    border: 1px solid #e5e7eb;

    box-shadow:
        0 8px 25px rgba(15,23,42,0.05);
}

.compare-arrow {
    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 2rem;

    font-weight: 800;

    color: #6366f1;

    height: 100%;
}


/* =========================================================
   INSIGHT CARD
   ========================================================= */

.insight-card {
    background: white;

    border-radius: 15px;

    padding: 17px;

    border: 1px solid #e5e7eb;

    margin-bottom: 12px;

    box-shadow:
        0 6px 20px rgba(15,23,42,0.04);
}

.insight-title {
    font-weight: 800;

    color: #1f2937;

    margin-bottom: 5px;
}

.insight-text {
    color: #64748b;

    font-size: 0.87rem;

    line-height: 1.5;
}


/* =========================================================
   PROGRESS
   ========================================================= */

div[data-testid="stProgressBar"] {
    margin-top: 8px;
}


/* =========================================================
   FOOTER
   ========================================================= */

.footer {
    text-align: center;

    color: #94a3b8;

    font-size: 0.75rem;

    padding-top: 15px;
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


def kpi(title, value, unit="", decimals=2, color="blue"):

    if value is None:

        display_value = "—"

    elif isinstance(value, str):

        display_value = value

    else:

        display_value = fmt_number(
            value,
            decimals,
        )

    st.markdown(
        f"""
        <div class="kpi-card kpi-{color}">
            <div class="kpi-label">
                {title}
            </div>

            <div class="kpi-value">
                {display_value}
            </div>

            <div class="kpi-unit">
                {unit}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def fill_percent(volume, capacity):

    if capacity <= 0:
        return 0

    return volume / capacity * 100


def get_status(validation):

    if not validation:
        return "REVIEW"

    return validation.get(
        "overall",
        "REVIEW",
    )


def status_badge(status):

    if status == "PASS":

        return """
        <span class="status status-pass">
        ✓ PASS
        </span>
        """

    if status == "FAIL":

        return """
        <span class="status status-fail">
        ✕ FAIL
        </span>
        """

    return """
    <span class="status status-review">
    ! REVIEW
    </span>
    """


def guidance(process_type):

    values = {

        "Liquid-Liquid":
            "Blend time, circulation, P/V, tip speed and impeller selection.",

        "Solid-Liquid":
            "Njs, solids suspension, off-bottom clearance and P/V.",

        "Gas-Liquid":
            "Gas dispersion, flooding, P/V, tip speed and KLa.",

        "Gas-Liquid-Solid":
            "Gas dispersion, Njs, solids suspension, P/V and KLa.",

        "Crystallization":
            "Suspension, circulation, shear and crystal quality.",

        "High-Viscosity":
            "Torque, laminar mixing, power and close-clearance impellers.",

        "General Mixing":
            "P/V, tip speed, Reynolds number, Froude number and pumping.",
    }

    return values.get(
        process_type,
        values["General Mixing"],
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size:1.35rem;
            font-weight:850;
            color:white;
            margin-bottom:3px;
        ">
        ⚗️ Reactor Studio
        </div>

        <div style="
            font-size:0.75rem;
            color:#94a3b8;
            margin-bottom:15px;
        ">
        Engineering Scale-Up Platform
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### 📁 Project")

    project_name = st.text_input(
        "Project",
        "Reactor Scale-Up Study",
    )

    prepared_by = st.text_input(
        "Prepared By",
        "Process Engineering",
    )

    st.divider()

    st.markdown("### ⚙️ Study")

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

    st.markdown("### 🎯 Focus")

    st.caption(
        "Primary engineering parameters"
    )

    focus = [
        "P/V",
        "Tip Speed",
        "Power",
        "Reynolds Number",
        "Q/V",
    ]

    if process_type in [
        "Solid-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
    ]:

        focus.insert(
            2,
            "Njs",
        )

    if process_type in [
        "Gas-Liquid",
        "Gas-Liquid-Solid",
    ]:

        focus.append(
            "KLa"
        )

    for item in focus:

        st.checkbox(
            item,
            value=True,
            disabled=True,
        )


# =========================================================
# REACTOR NAMES
# =========================================================

if study_mode == "Single Reactor":

    reactor_names = ["Reactor"]

elif study_mode == "Lab vs Pilot":

    reactor_names = [
        "Lab",
        "Pilot",
    ]

elif study_mode == "Pilot vs Commercial":

    reactor_names = [
        "Pilot",
        "Commercial",
    ]

elif study_mode == "Lab vs Commercial":

    reactor_names = [
        "Lab",
        "Commercial",
    ]

else:

    reactor_names = [
        "Lab",
        "Pilot",
        "Commercial",
    ]


# =========================================================
# HERO
# =========================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="hero-title">
            ⚗️ Reactor Scale-Up Studio
        </div>

        <div class="hero-subtitle">
            Professional Process Engineering & Mixing Analysis
            &nbsp; • &nbsp;
            {project_name}
            &nbsp; • &nbsp;
            {process_type}
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# REACTOR INPUT
# =========================================================

def reactor_input(name):

    volume_default = (
        1.0
        if name == "Lab"
        else 10.0
        if name == "Pilot"
        else 50.0
    )

    diameter_default = (
        1.0
        if name == "Lab"
        else 2.0
        if name == "Pilot"
        else 3.0
    )

    height_default = (
        1.5
        if name == "Lab"
        else 2.5
        if name == "Pilot"
        else 4.0
    )

    # -----------------------------------------------------
    # GEOMETRY
    # -----------------------------------------------------

    with st.expander(
        f"🏭 {name} Reactor — Vessel Configuration",
        expanded=True,
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            working_volume = st.number_input(
                "Working Volume (m³)",
                min_value=0.001,
                value=volume_default,
                step=0.5,
                format="%.3f",
                key=f"{name}_working_volume",
            )

        with c2:

            tank_diameter = st.number_input(
                "Tank ID (m)",
                min_value=0.05,
                value=diameter_default,
                step=0.05,
                format="%.3f",
                key=f"{name}_diameter",
            )

        with c3:

            straight_height = st.number_input(
                "Straight Height (m)",
                min_value=0.05,
                value=height_default,
                step=0.05,
                format="%.3f",
                key=f"{name}_height",
            )

        with c4:

            density = st.number_input(
                "Density (kg/m³)",
                min_value=0.001,
                value=1000.0,
                step=10.0,
                format="%.1f",
                key=f"{name}_density",
            )

        g1, g2 = st.columns(2)

        with g1:

            bottom_type = st.selectbox(
                "Bottom Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{name}_bottom",
            )

        with g2:

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

        fill = fill_percent(
            working_volume,
            vessel_volume,
        )

        k1, k2, k3 = st.columns(3)

        with k1:

            kpi(
                "Vessel Capacity",
                vessel_volume,
                "m³",
                3,
                "blue",
            )

        with k2:

            kpi(
                "Liquid Height",
                liquid_height,
                "m",
                3,
                "purple",
            )

        with k3:

            kpi(
                "Operating Fill",
                fill,
                "%",
                1,
                "green"
                if fill <= 90
                else "orange",
            )

        st.progress(
            min(
                max(fill / 100, 0),
                1,
            )
        )

        if fill > 100:

            st.error(
                "Working volume exceeds vessel capacity."
            )

        elif fill > 90:

            st.warning(
                "High operating fill — review headspace."
            )

    # -----------------------------------------------------
    # PROCESS
    # -----------------------------------------------------

    with st.expander(
        "🧪 Process Properties",
        expanded=False,
    ):

        c1, c2, c3 = st.columns(3)

        with c1:

            viscosity_mpas = st.number_input(
                "Viscosity (mPa·s)",
                min_value=0.001,
                value=1.0,
                step=0.1,
                format="%.3f",
                key=f"{name}_viscosity",
            )

        with c2:

            surface_tension = st.number_input(
                "Surface Tension (N/m)",
                min_value=0.001,
                value=0.072,
                step=0.001,
                format="%.4f",
                key=f"{name}_surface_tension",
            )

        with c3:

            st.markdown(
                f"""
                <div style="
                    padding:12px;
                    background:#f8fafc;
                    border-radius:10px;
                    margin-top:26px;
                    color:#64748b;
                    font-size:0.82rem;
                ">
                <b>Process focus</b><br>
                {guidance(process_type)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        viscosity_pa_s = (
            viscosity_mpas / 1000
        )

    # -----------------------------------------------------
    # AGITATION
    # -----------------------------------------------------

    with st.expander(
        "⚙️ Agitation System",
        expanded=True,
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            agitator = st.selectbox(
                "Agitator",
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
                "Impeller Diameter (m)",
                min_value=0.02,
                value=default_impeller,
                step=0.01,
                format="%.3f",
                key=f"{name}_impeller",
            )

        with c3:

            number_impellers = st.number_input(
                "Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{name}_impellers",
            )

        with c4:

            rpm = st.number_input(
                "Speed (RPM)",
                min_value=0.1,
                value=150.0,
                step=5.0,
                format="%.1f",
                key=f"{name}_rpm",
            )

        a1, a2, a3, a4 = st.columns(4)

        with a1:

            kpi(
                "Flow Pattern",
                agitator_data.get(
                    "flow",
                    "—",
                ),
                "",
                color="blue",
            )

        with a2:

            kpi(
                "Blade Count",
                agitator_data.get(
                    "blades",
                    "—",
                ),
                "count",
                0,
                "purple",
            )

        with a3:

            kpi(
                "Power Number",
                agitator_data.get("np"),
                "Np",
                3,
                "orange",
            )

        with a4:

            kpi(
                "Pumping Number",
                agitator_data.get("nq"),
                "Nq",
                3,
                "green",
            )

        st.caption(
            agitator_data.get(
                "description",
                "",
            )
        )

    # -----------------------------------------------------
    # INTERNALS
    # -----------------------------------------------------

    with st.expander(
        "🔧 Internal Arrangement",
        expanded=False,
    ):

        c1, c2, c3 = st.columns(3)

        with c1:

            number_baffles = st.number_input(
                "Baffles",
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

    # -----------------------------------------------------
    # CALCULATE
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
                "pumping_per_volume": result.get(
                    "qv_1_h"
                ),
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
    tab_dashboard,
    tab_setup,
    tab_performance,
    tab_scaleup,
    tab_validation,
    tab_3d,
    tab_insights,
) = st.tabs(
    [
        "🏠 Dashboard",
        "📐 Setup",
        "📊 Performance",
        "📈 Scale-Up",
        "✓ Validation",
        "🧊 3D Reactor",
        "💡 Insights",
    ]
)


# =========================================================
# SETUP
# =========================================================

with tab_setup:

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        'Reactor Configuration'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Configure the vessel, process properties and agitation system."
    )

    reactors = []

    for name in reactor_names:

        reactors.append(
            reactor_input(name)
        )


# =========================================================
# STATUS
# =========================================================

statuses = [
    get_status(
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
# DASHBOARD HOME
# =========================================================

with tab_dashboard:

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        'Engineering Overview'
        '</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # TOP KPIs
    # -----------------------------------------------------

    total_volume = sum(
        r["working_volume"]
        for r in reactors
    )

    avg_pv = None

    pv_values = [
        r.get("power_volume")
        for r in reactors
        if r.get("power_volume") is not None
    ]

    if pv_values:

        avg_pv = sum(pv_values) / len(pv_values)

    k1, k2, k3, k4 = st.columns(4)

    with k1:

        kpi(
            "Reactors",
            len(reactors),
            "in study",
            0,
            "blue",
        )

    with k2:

        kpi(
            "Total Working Volume",
            total_volume,
            "m³",
            2,
            "purple",
        )

    with k3:

        kpi(
            "Average P/V",
            avg_pv,
            "kW/m³",
            4,
            "orange",
        )

    with k4:

        kpi(
            "Engineering Status",
            overall_status,
            "screening",
            color=(
                "green"
                if overall_status == "PASS"
                else "orange"
                if overall_status == "REVIEW"
                else "red"
            ),
        )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    st.markdown("")

    if overall_status == "PASS":

        st.success(
            "✓ Engineering screening completed successfully."
        )

    elif overall_status == "REVIEW":

        st.warning(
            "! Engineering review required for one or more checks."
        )

    else:

        st.error(
            "✕ Engineering validation indicates one or more failures."
        )

    # -----------------------------------------------------
    # REACTOR CARDS
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        'Reactor Overview'
        '</div>',
        unsafe_allow_html=True,
    )

    overview_columns = st.columns(
        len(reactors)
    )

    for col, reactor in zip(
        overview_columns,
        reactors,
    ):

        with col:

            status = get_status(
                reactor["validation"]
            )

            st.markdown(
                f"""
                <div class="reactor-card">

                    <div class="reactor-card-header">

                        <div>
                            <div class="reactor-title">
                                ⚗️ {reactor["name"]}
                            </div>

                            <div class="reactor-subtitle">
                                Reactor configuration
                            </div>
                        </div>

                        {status_badge(status)}

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            a, b = st.columns(2)

            with a:

                kpi(
                    "Volume",
                    reactor["working_volume"],
                    "m³",
                    2,
                    "blue",
                )

            with b:

                kpi(
                    "Speed",
                    reactor["rpm"],
                    "RPM",
                    0,
                    "purple",
                )

            a, b = st.columns(2)

            with a:

                kpi(
                    "Power",
                    reactor.get("power_kw"),
                    "kW",
                    2,
                    "orange",
                )

            with b:

                kpi(
                    "P/V",
                    reactor.get("power_volume"),
                    "kW/m³",
                    4,
                    "green",
                )


# =========================================================
# PERFORMANCE
# =========================================================

with tab_performance:

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        'Mixing Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        f"🎯 **{process_type}:** {guidance(process_type)}"
    )

    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            kpi(
                "Agitator Power",
                reactor.get("power_kw"),
                "kW",
                2,
                "blue",
            )

        with p2:

            kpi(
                "Power / Volume",
                reactor.get("power_volume"),
                "kW/m³",
                4,
                "purple",
            )

        with p3:

            kpi(
                "Tip Speed",
                reactor.get("tip_speed"),
                "m/s",
                2,
                "orange",
            )

        with p4:

            kpi(
                "Reynolds Number",
                reactor.get("Re"),
                "dimensionless",
                0,
                "green",
            )

        st.markdown("")

        p5, p6, p7, p8 = st.columns(4)

        with p5:

            kpi(
                "Froude Number",
                reactor.get("Fr"),
                "dimensionless",
                4,
                "blue",
            )

        with p6:

            kpi(
                "Pumping Capacity",
                reactor.get("pumping_m3_h"),
                "m³/h",
                2,
                "purple",
            )

        with p7:

            kpi(
                "Q / V",
                reactor.get("qv_1_h"),
                "1/h",
                3,
                "orange",
            )

        with p8:

            kpi(
                "Turnover Time",
                reactor.get("turnover_time_min"),
                "min",
                2,
                "green",
            )

        with st.expander(
            f"View detailed parameters — {reactor['name']}"
        ):

            table = pd.DataFrame(
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
                        "Bottom Head",
                        "Top Head",
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
                }
            )

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# SCALE-UP
# =========================================================

with tab_scaleup:

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        'Scale-Up Analysis'
        '</div>',
        unsafe_allow_html=True,
    )

    if len(reactors) < 2:

        st.info(
            "Select a multi-reactor study mode to activate scale-up analysis."
        )

    else:

        base = reactors[0]
        target = reactors[1]

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

        st.markdown(
            f"""
            <div class="compare-card">

                <div style="
                    font-size:0.78rem;
                    color:#64748b;
                    font-weight:700;
                    text-transform:uppercase;
                ">
                Scale-Up Path
                </div>

                <div style="
                    font-size:1.5rem;
                    font-weight:850;
                    color:#111827;
                    margin-top:5px;
                ">
                {base["name"]}
                &nbsp; → &nbsp;
                {target["name"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("")

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            kpi(
                "Base Volume",
                base["working_volume"],
                "m³",
                3,
                "blue",
            )

        with c2:

            kpi(
                "Target Volume",
                target["working_volume"],
                "m³",
                3,
                "purple",
            )

        with c3:

            kpi(
                "Volume Scale",
                scale_ratio,
                "×",
                2,
                "orange",
            )

        with c4:

            kpi(
                "Diameter Scale",
                diameter_ratio,
                "×",
                2,
                "green",
            )

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

        st.markdown(
            "### Target Operating Conditions"
        )

        r1, r2, r3, r4 = st.columns(4)

        with r1:

            kpi(
                "Scale-Up Basis",
                scaleup_basis,
                "",
                color="blue",
            )

        with r2:

            kpi(
                "Target RPM",
                scale_result.get(
                    "target_rpm"
                ),
                "RPM",
                1,
                "purple",
            )

        with r3:

            kpi(
                "Target Tip Speed",
                scale_result.get(
                    "target_tip_speed"
                ),
                "m/s",
                2,
                "orange",
            )

        with r4:

            kpi(
                "Target P/V",
                scale_result.get(
                    "target_power_volume"
                ),
                "kW/m³",
                4,
                "green",
            )

        if scale_result.get("message"):

            st.info(
                scale_result["message"]
            )


# =========================================================
# VALIDATION
# =========================================================

with tab_validation:

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        'Engineering Validation'
        '</div>',
        unsafe_allow_html=True,
    )

    if overall_status == "PASS":

        st.success(
            "✓ Overall engineering screening: PASS"
        )

    elif overall_status == "REVIEW":

        st.warning(
            "! Overall engineering screening: REVIEW"
        )

    else:

        st.error(
            "✕ Overall engineering screening: FAIL"
        )

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

            kpi(
                "Status",
                validation.get(
                    "overall",
                    "REVIEW",
                ),
                "",
                color=(
                    "green"
                    if validation.get("overall") == "PASS"
                    else "orange"
                    if validation.get("overall") == "REVIEW"
                    else "red"
                ),
            )

        with v2:

            kpi(
                "Failures",
                validation.get(
                    "failures",
                    0,
                ),
                "count",
                0,
                "red",
            )

        with v3:

            kpi(
                "Warnings",
                validation.get(
                    "warnings",
                    0,
                ),
                "count",
                0,
                "orange",
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


# =========================================================
# 3D
# =========================================================

with tab_3d:

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        '3D Reactor Visualization'
        '</div>',
        unsafe_allow_html=True,
    )

    selected_name = st.selectbox(
        "Select Reactor",
        [
            r["name"]
            for r in reactors
        ],
        key="selected_3d_reactor",
    )

    selected = next(
        r
        for r in reactors
        if r["name"] == selected_name
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        kpi(
            "Tank Diameter",
            selected["tank_diameter_m"],
            "m",
            3,
            "blue",
        )

    with c2:

        kpi(
            "Liquid Height",
            selected["liquid_height_m"],
            "m",
            3,
            "purple",
        )

    with c3:

        kpi(
            "Impeller Diameter",
            selected["impeller_diameter_m"],
            "m",
            3,
            "orange",
        )

    with c4:

        kpi(
            "Agitator Speed",
            selected["rpm"],
            "RPM",
            1,
            "green",
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
# INSIGHTS
# =========================================================

with tab_insights:

    st.markdown(
        '<div class="section-title">'
        '<span class="section-dot"></span>'
        'Engineering Insights'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        f"🎯 **Process focus:** {guidance(process_type)}"
    )

    for reactor in reactors:

        dt = reactor.get("D_T")
        re = reactor.get("Re")

        fill = fill_percent(
            reactor["working_volume"],
            reactor["vessel_volume"],
        )

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        # -------------------------------------------------
        # D/T
        # -------------------------------------------------

        if dt is not None:

            if dt < 0.20:

                st.warning(
                    "⚠️ Impeller diameter is relatively small. "
                    "Review circulation and blend performance."
                )

            elif dt > 0.60:

                st.warning(
                    "⚠️ Large impeller/tank ratio. Review power, "
                    "torque and mechanical loading."
                )

            else:

                st.success(
                    "✓ Impeller/tank ratio is within the screening range."
                )

        # -------------------------------------------------
        # RE
        # -------------------------------------------------

        if re is not None:

            if re < 10:

                st.warning(
                    "⚠️ Laminar regime indicated. "
                    "Verify the applicable power correlation."
                )

            elif re < 10000:

                st.warning(
                    "⚠️ Transitional regime. "
                    "Correlation selection requires attention."
                )

            else:

                st.success(
                    "✓ Turbulent mixing regime indicated."
                )

        # -------------------------------------------------
        # FILL
        # -------------------------------------------------

        if fill > 90:

            st.warning(
                "⚠️ High operating fill. Confirm required headspace."
            )

        elif fill < 25:

            st.warning(
                "⚠️ Low operating fill. Confirm impeller immersion."
            )

        else:

            st.success(
                "✓ Operating fill is within the screening range."
            )

        # -------------------------------------------------
        # PROCESS SPECIFIC
        # -------------------------------------------------

        if process_type in [
            "Solid-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
        ]:

            st.info(
                "🧪 Solids service: validate Njs, off-bottom suspension "
                "and solids distribution using appropriate correlations "
                "or pilot data."
            )

        if process_type in [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ]:

            st.info(
                "💨 Gas-liquid service: validate gas dispersion, flooding, "
                "gas holdup and KLa using suitable correlations or test data."
            )

        if process_type == "High-Viscosity":

            st.info(
                "⚙️ High-viscosity service: verify torque, motor sizing, "
                "gearbox limits and laminar power correlation."
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        Reactor Scale-Up Engineering Studio
        &nbsp; • &nbsp;
        Preliminary Engineering Screening Tool
        <br>
        Validate correlations, vendor data, pilot trials and
        mechanical design before final equipment design.
    </div>
    """,
    unsafe_allow_html=True,
)
```
