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
# APPLICATION CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# PROFESSIONAL UI THEME
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL
       ===================================================== */

    .block-container {
        max-width: 1550px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    body {
        font-family: Inter, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
    }

    /* Remove excessive top spacing */
    [data-testid="stAppViewContainer"] {
        background: #f6f8fb;
    }

    /* =====================================================
       SIDEBAR
       ===================================================== */

    [data-testid="stSidebar"] {
        background: #101828;
        border-right: 1px solid #1d2939;
    }

    [data-testid="stSidebar"] * {
        color: #f2f4f7;
    }

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label {
        color: #d0d5dd !important;
        font-weight: 600;
    }

    [data-testid="stSidebar"] hr {
        border-color: #344054;
    }

    /* =====================================================
       TITLES
       ===================================================== */

    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.7px;
        color: #101828 !important;
    }

    h2 {
        font-weight: 750 !important;
        color: #101828 !important;
        margin-top: 1.5rem !important;
    }

    h3 {
        font-weight: 700 !important;
        color: #182230 !important;
    }

    /* =====================================================
       NATIVE METRIC CARDS
       ===================================================== */

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        padding: 18px 18px 16px 18px;
        min-height: 118px;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.045);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        font-weight: 650 !important;
        color: #667085 !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        color: #101828 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }

    /* =====================================================
       INPUTS
       ===================================================== */

    .stNumberInput input,
    .stTextInput input {
        border-radius: 8px !important;
    }

    .stSelectbox > div > div {
        border-radius: 8px !important;
    }

    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {
        border-radius: 8px;
        font-weight: 650;
        min-height: 40px;
    }

    /* =====================================================
       TABS
       ===================================================== */

    button[data-baseweb="tab"] {
        font-weight: 650;
        font-size: 0.92rem;
    }

    /* =====================================================
       EXPANDERS
       ===================================================== */

    [data-testid="stExpander"] {
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        background: #ffffff;
    }

    /* =====================================================
       ALERTS
       ===================================================== */

    .stAlert {
        border-radius: 10px;
    }

    /* =====================================================
       DATAFRAME
       ===================================================== */

    [data-testid="stDataFrame"] {
        border: 1px solid #e4e7ec;
        border-radius: 10px;
        overflow: hidden;
    }

    /* =====================================================
       DIVIDERS
       ===================================================== */

    hr {
        border-color: #e4e7ec;
        margin-top: 1.2rem;
        margin-bottom: 1.2rem;
    }

    /* =====================================================
       SMALL SCREEN
       ===================================================== */

    @media (max-width: 900px) {

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# APPLICATION HEADER
# =========================================================

st.title("🏭 Reactor Scale-Up Engineering Studio")

st.caption(
    "Process Engineering • Reactor Geometry • Mixing • Agitation • "
    "Hydrodynamics • Scale-Up • Validation"
)

st.divider()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("## 🏭 Engineering Studio")

st.sidebar.caption(
    "Reactor & Mixing Engineering Platform"
)

st.sidebar.divider()


project_name = st.sidebar.text_input(
    "Project / Study Name",
    value="Reactor Scale-Up Study",
)

prepared_by = st.sidebar.text_input(
    "Prepared By",
    value="Process Engineering",
)


st.sidebar.markdown("### 📊 Study Setup")


study_mode = st.sidebar.selectbox(
    "Study Mode",
    [
        "Single Reactor",
        "Lab vs Pilot",
        "Pilot vs Commercial",
        "Lab vs Commercial",
        "Lab vs Pilot vs Commercial",
    ],
)


process_type = st.sidebar.selectbox(
    "Process / Reaction Type",
    [
        "Liquid-Liquid",
        "Solid-Liquid",
        "Gas-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
        "Precipitation",
        "Dissolution",
        "Extraction",
        "Neutralization",
        "General Mixing",
    ],
)


scaleup_basis = st.sidebar.selectbox(
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


# =========================================================
# PROCESS GUIDANCE
# =========================================================

PROCESS_GUIDANCE = {

    "Liquid-Liquid":
        "Prioritize bulk blending, circulation, dispersion and phase contacting.",

    "Solid-Liquid":
        "Prioritize solids suspension, Njs, circulation and off-bottom suspension.",

    "Gas-Liquid":
        "Prioritize gas dispersion, P/V, tip speed, flooding and KLa.",

    "Gas-Liquid-Solid":
        "Evaluate gas dispersion and solids suspension simultaneously.",

    "Crystallization":
        "Consider suspension quality, shear, heat transfer and crystal morphology.",

    "Precipitation":
        "Pay particular attention to local supersaturation, micromixing and addition-point mixing.",

    "Dissolution":
        "Focus on solids suspension, wetting, circulation and dissolution kinetics.",

    "Extraction":
        "Focus on dispersion, interfacial area, phase ratio and coalescence.",

    "Neutralization":
        "Focus on blending, addition-point mixing and heat release.",

    "General Mixing":
        "Use P/V, tip speed, Reynolds number, Froude number and Q/V for preliminary screening.",
}


with st.sidebar.expander(
    "💡 Engineering Guidance",
    expanded=True,
):

    st.info(
        PROCESS_GUIDANCE.get(
            process_type,
            "Use validated process-specific engineering correlations.",
        )
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

    reactor_names = [
        "Lab",
        "Pilot",
        "Commercial",
    ]


# =========================================================
# STORAGE
# =========================================================

reactors = {}


# =========================================================
# MAIN NAVIGATION
# =========================================================

tab_setup, tab_performance, tab_scaleup, tab_geometry, tab_validation, tab_3d = st.tabs(
    [
        "⚙️ Reactor Setup",
        "📊 Performance",
        "📈 Scale-Up",
        "📐 Geometry",
        "✅ Validation",
        "🧊 3D Reactor",
    ]
)


# =========================================================
# TAB 1
# REACTOR SETUP
# =========================================================

with tab_setup:

    st.header("Reactor Configuration")

    st.caption(
        "Define process properties, vessel geometry and agitation system."
    )


    # =====================================================
    # REACTOR LOOP
    # =====================================================

    for reactor_name in reactor_names:

        with st.container():

            st.subheader(
                f"🏭 {reactor_name} Reactor"
            )


            # -------------------------------------------------
            # PROCESS
            # -------------------------------------------------

            st.markdown("#### 🧪 Process Properties")

            p1, p2, p3, p4 = st.columns(4)

            with p1:

                working_volume = st.number_input(
                    "Working Volume",
                    min_value=0.01,
                    value=1.00,
                    step=0.10,
                    format="%.2f",
                    key=f"{reactor_name}_volume",
                    help="Operating liquid volume.",
                )

            with p2:

                density = st.number_input(
                    "Density [kg/m³]",
                    min_value=1.0,
                    value=1000.0,
                    step=10.0,
                    key=f"{reactor_name}_density",
                )

            with p3:

                viscosity = st.number_input(
                    "Viscosity [mPa·s]",
                    min_value=0.01,
                    value=1.0,
                    step=0.1,
                    key=f"{reactor_name}_viscosity",
                )

            with p4:

                surface_tension = st.number_input(
                    "Surface Tension [mN/m]",
                    min_value=0.01,
                    value=30.0,
                    step=1.0,
                    key=f"{reactor_name}_surface_tension",
                )


            # -------------------------------------------------
            # GEOMETRY
            # -------------------------------------------------

            st.markdown("#### 📐 Vessel Geometry")

            g1, g2, g3, g4 = st.columns(4)

            with g1:

                tank_id = st.number_input(
                    "Tank ID [mm]",
                    min_value=100.0,
                    value=1000.0,
                    step=50.0,
                    key=f"{reactor_name}_tank_id",
                )

            with g2:

                straight_height = st.number_input(
                    "Straight Height [mm]",
                    min_value=100.0,
                    value=1500.0,
                    step=50.0,
                    key=f"{reactor_name}_height",
                )

            with g3:

                bottom_type = st.selectbox(
                    "Bottom Head",
                    list(REACTOR_HEADS.keys()),
                    index=1,
                    key=f"{reactor_name}_bottom",
                )

            with g4:

                top_type = st.selectbox(
                    "Top Head",
                    list(REACTOR_HEADS.keys()),
                    index=1,
                    key=f"{reactor_name}_top",
                )


            # -------------------------------------------------
            # AGITATION
            # -------------------------------------------------

            st.markdown("#### 🌀 Agitation System")

            a1, a2, a3, a4 = st.columns(4)

            with a1:

                agitator_type = st.selectbox(
                    "Agitator Type",
                    list(AGITATORS.keys()),
                    index=1,
                    key=f"{reactor_name}_agitator",
                )

            agitator_info = AGITATORS[
                agitator_type
            ]

            default_ratio = agitator_info.get(
                "default_diameter_ratio",
                0.40,
            )

            default_impeller = (
                tank_id * default_ratio
            )

            with a2:

                impeller_diameter = st.number_input(
                    "Impeller Diameter [mm]",
                    min_value=20.0,
                    value=float(default_impeller),
                    step=10.0,
                    key=f"{reactor_name}_impeller",
                )

            with a3:

                number_impellers = st.number_input(
                    "Number of Impellers",
                    min_value=1,
                    max_value=6,
                    value=1,
                    step=1,
                    key=f"{reactor_name}_nimp",
                )

            with a4:

                rpm = st.number_input(
                    "Agitator Speed [RPM]",
                    min_value=1.0,
                    value=120.0,
                    step=5.0,
                    key=f"{reactor_name}_rpm",
                )


            # -------------------------------------------------
            # BAFFLES
            # -------------------------------------------------

            st.markdown("#### 🧱 Baffle System")

            b1, b2, b3, b4 = st.columns(4)

            with b1:

                baffles = st.number_input(
                    "Number of Baffles",
                    min_value=0,
                    max_value=12,
                    value=4,
                    step=1,
                    key=f"{reactor_name}_baffles",
                )

            with b2:

                baffle_config = st.selectbox(
                    "Baffle Configuration",
                    [
                        "Standard",
                        "Partial Height",
                        "Full Height",
                        "Custom / Vendor Data",
                    ],
                    key=f"{reactor_name}_baffle_config",
                )

            with b3:

                Di_over_D_preview = (
                    impeller_diameter / tank_id
                    if tank_id > 0
                    else 0
                )

                st.metric(
                    "Impeller / Tank",
                    f"{Di_over_D_preview:.3f}",
                )

            with b4:

                st.metric(
                    "Impellers",
                    f"{int(number_impellers)}",
                )


            # -------------------------------------------------
            # CONVERSION
            # -------------------------------------------------

            D = tank_id / 1000.0

            H = straight_height / 1000.0

            Di = impeller_diameter / 1000.0

            mu = viscosity / 1000.0

            sigma = surface_tension / 1000.0


            # -------------------------------------------------
            # VESSEL CAPACITY
            # -------------------------------------------------

            try:

                vessel_volume = calculate_total_volume(
                    D=D,
                    straight_height=H,
                    bottom_type=bottom_type,
                    top_type=top_type,
                )

            except Exception:

                vessel_volume = 0.0


            # -------------------------------------------------
            # LIQUID HEIGHT
            # -------------------------------------------------

            try:

                liquid_height, calculated_total_volume = (
                    liquid_height_from_volume(
                        working_volume=working_volume,
                        D=D,
                        straight_height=H,
                        bottom_type=bottom_type,
                        top_type=top_type,
                    )
                )

            except Exception:

                liquid_height = 0.0

                calculated_total_volume = vessel_volume


            # -------------------------------------------------
            # RATIOS
            # -------------------------------------------------

            H_over_D = (
                liquid_height / D
                if D > 0
                else 0.0
            )

            Di_over_D = (
                Di / D
                if D > 0
                else 0.0
            )

            fill_percent = (
                working_volume / vessel_volume * 100
                if vessel_volume > 0
                else 0.0
            )


            # -------------------------------------------------
            # CALCULATIONS
            # -------------------------------------------------

            try:

                results = calculate_reactor(

                    volume_m3=working_volume,

                    tank_diameter_m=D,

                    liquid_height_m=liquid_height,

                    density_kg_m3=density,

                    viscosity_pa_s=mu,

                    surface_tension_n_m=sigma,

                    rpm=rpm,

                    impeller_diameter_m=Di,

                    number_impellers=int(
                        number_impellers
                    ),

                    agitator=agitator_type,

                )

            except Exception as e:

                results = {
                    "power_kw": None,
                    "power_volume": None,
                    "tip_speed": 0.0,
                    "Re": 0.0,
                    "Fr": 0.0,
                    "Np": None,
                    "Nq": None,
                    "torque_nm": None,
                    "pumping_m3_h": None,
                    "qv_1_h": None,
                    "turnover_time_min": None,
                    "viscosity_pa_s": mu,
                    "density_kg_m3": density,
                }

                st.error(
                    f"Calculation error for {reactor_name}: {e}"
                )


            # -------------------------------------------------
            # VALIDATION
            # -------------------------------------------------

            try:

                validation = validate_reactor(

                    volume_m3=working_volume,

                    vessel_volume_m3=vessel_volume,

                    tank_diameter_m=D,

                    straight_height_m=H,

                    liquid_height_m=liquid_height,

                    impeller_diameter_m=Di,

                    number_impellers=int(
                        number_impellers
                    ),

                    number_baffles=int(
                        baffles
                    ),

                    rpm=rpm,

                    agitator=agitator_type,

                    density_kg_m3=density,

                    viscosity_pa_s=mu,

                )

            except Exception as e:

                validation = {

                    "overall": "REVIEW",

                    "checks": [

                        {
                            "severity": "WARNING",
                            "message":
                                f"Validation error: {e}",
                        }

                    ],

                }


            # -------------------------------------------------
            # VORTEX SCREENING
            # -------------------------------------------------

            if baffles == 0:

                vortex_depth = (
                    0.10 *
                    liquid_height
                )

            elif baffles < 4:

                vortex_depth = (
                    0.05 *
                    liquid_height
                )

            else:

                vortex_depth = (
                    0.01 *
                    liquid_height
                )


            # -------------------------------------------------
            # SAVE
            # -------------------------------------------------

            reactors[reactor_name] = {

                "working_volume":
                    working_volume,

                "density":
                    density,

                "viscosity":
                    viscosity,

                "surface_tension":
                    surface_tension,

                "tank_id_m":
                    D,

                "straight_height_m":
                    H,

                "bottom_type":
                    bottom_type,

                "top_type":
                    top_type,

                "agitator_type":
                    agitator_type,

                "impeller_diameter_m":
                    Di,

                "number_impellers":
                    int(number_impellers),

                "rpm":
                    rpm,

                "baffles":
                    int(baffles),

                "baffle_config":
                    baffle_config,

                "vessel_volume_m3":
                    vessel_volume,

                "liquid_height_m":
                    liquid_height,

                "fill_percent":
                    fill_percent,

                "H_over_D":
                    H_over_D,

                "Di_over_D":
                    Di_over_D,

                "vortex_depth":
                    vortex_depth,

                "results":
                    results,

                "validation":
                    validation,
            }


            # -------------------------------------------------
            # QUICK CONFIGURATION SUMMARY
            # -------------------------------------------------

            st.markdown("##### 📌 Configuration Summary")

            q1, q2, q3, q4 = st.columns(4)

            with q1:

                st.metric(
                    "Vessel Capacity",
                    f"{vessel_volume:.2f} m³",
                )

            with q2:

                st.metric(
                    "Operating Fill",
                    f"{fill_percent:.1f} %",
                )

            with q3:

                st.metric(
                    "Liquid Height",
                    f"{liquid_height:.2f} m",
                )

            with q4:

                st.metric(
                    "H / D",
                    f"{H_over_D:.2f}",
                )

            st.divider()


# =========================================================
# TAB 2
# PERFORMANCE
# =========================================================

with tab_performance:

    st.header("📊 Mixing Performance")

    st.caption(
        "Calculated hydrodynamic and agitator performance indicators."
    )


    for reactor_name in reactor_names:

        data = reactors[reactor_name]

        result = data["results"]


        st.subheader(
            f"🏭 {reactor_name}"
        )


        power_kw = result.get(
            "power_kw"
        )

        pv = result.get(
            "power_volume"
        )

        tip_speed = result.get(
            "tip_speed",
            0.0,
        )

        reynolds = result.get(
            "Re",
            0.0,
        )

        pumping = result.get(
            "pumping_m3_h"
        )

        turnover = result.get(
            "turnover_time_min"
        )

        froude = result.get(
            "Fr",
            0.0,
        )

        torque = result.get(
            "torque_nm"
        )


        # -------------------------------------------------
        # REGIME
        # -------------------------------------------------

        if reynolds >= 10000:

            regime = "Turbulent"
            regime_icon = "🟢"

        elif reynolds >= 10:

            regime = "Transitional"
            regime_icon = "🟡"

        else:

            regime = "Laminar"
            regime_icon = "🔵"


        # -------------------------------------------------
        # KPI ROW
        # -------------------------------------------------

        k1, k2, k3, k4 = st.columns(4)

        with k1:

            st.metric(
                "⚡ Agitator Power",
                (
                    f"{power_kw:,.2f} kW"
                    if power_kw is not None
                    else "N/A"
                ),
                help="Calculated agitator shaft power.",
            )

        with k2:

            st.metric(
                "🔋 Power / Volume",
                (
                    f"{pv:,.1f} W/m³"
                    if pv is not None
                    else "N/A"
                ),
                help="Mixing power intensity.",
            )

        with k3:

            st.metric(
                "🌀 Tip Speed",
                f"{tip_speed:,.2f} m/s",
                help="Impeller peripheral velocity.",
            )

        with k4:

            st.metric(
                f"{regime_icon} Reynolds Number",
                f"{reynolds:,.0f}",
                help=f"Mixing regime: {regime}.",
            )


        k1, k2, k3, k4 = st.columns(4)

        with k1:

            st.metric(
                "💧 Pumping Capacity",
                (
                    f"{pumping:,.2f} m³/h"
                    if pumping is not None
                    else "N/A"
                ),
            )

        with k2:

            st.metric(
                "🔄 Vessel Turnover",
                (
                    f"{turnover:,.2f} min"
                    if turnover is not None
                    else "N/A"
                ),
            )

        with k3:

            st.metric(
                "🌊 Froude Number",
                f"{froude:,.4f}",
            )

        with k4:

            st.metric(
                "⚙️ Agitator Torque",
                (
                    f"{torque:,.1f} N·m"
                    if torque is not None
                    else "N/A"
                ),
            )


        # -------------------------------------------------
        # ENGINEERING SNAPSHOT
        # -------------------------------------------------

        st.markdown(
            "##### Engineering Snapshot"
        )

        snapshot = pd.DataFrame(
            [
                {
                    "Parameter":
                        "Working Volume",

                    "Value":
                        f"{data['working_volume']:.2f}",

                    "Unit":
                        "m³",
                },

                {
                    "Parameter":
                        "Tank ID",

                    "Value":
                        f"{data['tank_id_m']:.3f}",

                    "Unit":
                        "m",
                },

                {
                    "Parameter":
                        "Liquid Height",

                    "Value":
                        f"{data['liquid_height_m']:.3f}",

                    "Unit":
                        "m",
                },

                {
                    "Parameter":
                        "Impeller Diameter",

                    "Value":
                        f"{data['impeller_diameter_m']:.3f}",

                    "Unit":
                        "m",
                },

                {
                    "Parameter":
                        "Impeller / Tank",

                    "Value":
                        f"{data['Di_over_D']:.3f}",

                    "Unit":
                        "-",
                },

                {
                    "Parameter":
                        "H / D",

                    "Value":
                        f"{data['H_over_D']:.3f}",

                    "Unit":
                        "-",
                },

                {
                    "Parameter":
                        "Agitator Speed",

                    "Value":
                        f"{data['rpm']:.1f}",

                    "Unit":
                        "RPM",
                },

                {
                    "Parameter":
                        "Baffles",

                    "Value":
                        f"{data['baffles']}",

                    "Unit":
                        "-",
                },
            ]
        )

        st.dataframe(
            snapshot,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()


# =========================================================
# TAB 3
# SCALE-UP
# =========================================================

with tab_scaleup:

    st.header("📈 Reactor Scale-Up")

    st.caption(
        "Compare reactor configurations using the selected scale-up criterion."
    )


    if len(reactor_names) < 2:

        st.info(
            "Select a comparison study mode from the sidebar "
            "to activate scale-up analysis."
        )

    else:

        base_name = reactor_names[0]

        base_data = reactors[base_name]

        base_result = base_data["results"]


        for target_name in reactor_names[1:]:

            target_data = reactors[target_name]

            target_result = target_data["results"]


            base_for_scaleup = {

                "working_volume":
                    base_data["working_volume"],

                "impeller_diameter_m":
                    base_data["impeller_diameter_m"],

                "rpm":
                    base_data["rpm"],

                "tip_speed":
                    base_result.get("tip_speed"),

                "power_volume":
                    base_result.get("power_volume"),

                "qv_1_h":
                    base_result.get("qv_1_h"),

                "pumping_m3_h":
                    base_result.get("pumping_m3_h"),

                "density":
                    base_data["density"],

                "viscosity_pa_s":
                    base_result.get(
                        "viscosity_pa_s"
                    ),

                "Np":
                    base_result.get("Np"),

                "Nq":
                    base_result.get("Nq"),
            }


            target_for_scaleup = {

                "working_volume":
                    target_data["working_volume"],

                "impeller_diameter_m":
                    target_data["impeller_diameter_m"],

                "rpm":
                    target_data["rpm"],

                "tip_speed":
                    target_result.get("tip_speed"),

                "power_volume":
                    target_result.get("power_volume"),

                "qv_1_h":
                    target_result.get("qv_1_h"),

                "pumping_m3_h":
                    target_result.get("pumping_m3_h"),

                "density":
                    target_data["density"],

                "viscosity_pa_s":
                    target_result.get(
                        "viscosity_pa_s"
                    ),

                "Np":
                    target_result.get("Np"),

                "Nq":
                    target_result.get("Nq"),
            }


            st.subheader(
                f"{base_name}  →  {target_name}"
            )


            try:

                scaleup = calculate_scaleup(

                    base=base_for_scaleup,

                    target=target_for_scaleup,

                    basis=scaleup_basis,

                )

            except Exception as e:

                st.error(
                    f"Scale-up calculation error: {e}"
                )

                continue


            target_rpm = scaleup.get(
                "target_rpm"
            )

            target_tip = scaleup.get(
                "target_tip_speed"
            )

            target_pv = scaleup.get(
                "target_power_volume"
            )

            target_qv = scaleup.get(
                "target_qv"
            )


            c1, c2, c3, c4 = st.columns(4)

            with c1:

                st.metric(
                    "Target RPM",
                    (
                        f"{target_rpm:,.1f}"
                        if target_rpm is not None
                        else "N/A"
                    ),
                )

            with c2:

                st.metric(
                    "Target Tip Speed",
                    (
                        f"{target_tip:,.2f} m/s"
                        if target_tip is not None
                        else "N/A"
                    ),
                )

            with c3:

                st.metric(
                    "Target P/V",
                    (
                        f"{target_pv:,.1f} W/m³"
                        if target_pv is not None
                        else "N/A"
                    ),
                )

            with c4:

                st.metric(
                    "Target Q/V",
                    (
                        f"{target_qv:,.2f} h⁻¹"
                        if target_qv is not None
                        else "N/A"
                    ),
                )


            st.info(
                f"**Scale-Up Basis:** {scaleup_basis}\n\n"
                f"{scaleup.get('message', 'Review engineering result.')}"
            )


            # ---------------------------------------------
            # SCALE-UP COMPARISON TABLE
            # ---------------------------------------------

            comparison_rows = [

                {
                    "Parameter":
                        "Working Volume",

                    base_name:
                        f"{base_data['working_volume']:.2f} m³",

                    target_name:
                        f"{target_data['working_volume']:.2f} m³",
                },

                {
                    "Parameter":
                        "Tank ID",

                    base_name:
                        f"{base_data['tank_id_m']:.3f} m",

                    target_name:
                        f"{target_data['tank_id_m']:.3f} m",
                },

                {
                    "Parameter":
                        "Impeller Diameter",

                    base_name:
                        f"{base_data['impeller_diameter_m']:.3f} m",

                    target_name:
                        f"{target_data['impeller_diameter_m']:.3f} m",
                },

                {
                    "Parameter":
                        "RPM",

                    base_name:
                        f"{base_data['rpm']:.1f}",

                    target_name:
                        f"{target_data['rpm']:.1f}",
                },

                {
                    "Parameter":
                        "Tip Speed",

                    base_name:
                        f"{base_result.get('tip_speed', 0):.2f} m/s",

                    target_name:
                        f"{target_result.get('tip_speed', 0):.2f} m/s",
                },

                {
                    "Parameter":
                        "P/V",

                    base_name:
                        (
                            f"{base_result.get('power_volume', 0):.1f} W/m³"
                        ),

                    target_name:
                        (
                            f"{target_result.get('power_volume', 0):.1f} W/m³"
                        ),
                },

                {
                    "Parameter":
                        "Reynolds Number",

                    base_name:
                        f"{base_result.get('Re', 0):,.0f}",

                    target_name:
                        f"{target_result.get('Re', 0):,.0f}",
                },
            ]


            st.dataframe(
                pd.DataFrame(
                    comparison_rows
                ),
                use_container_width=True,
                hide_index=True,
            )


            st.divider()


# =========================================================
# TAB 4
# GEOMETRY
# =========================================================

with tab_geometry:

    st.header("📐 Reactor Geometry")

    st.caption(
        "Calculated vessel capacity, liquid level and geometry ratios."
    )


    geometry_rows = []


    for reactor_name in reactor_names:

        data = reactors[reactor_name]


        geometry_rows.append({

            "Reactor":
                reactor_name,

            "Working Volume [m³]":
                round(
                    data["working_volume"],
                    3,
                ),

            "Vessel Volume [m³]":
                round(
                    data["vessel_volume_m3"],
                    3,
                ),

            "Fill [%]":
                round(
                    data["fill_percent"],
                    1,
                ),

            "Tank ID [m]":
                round(
                    data["tank_id_m"],
                    3,
                ),

            "Straight Height [m]":
                round(
                    data["straight_height_m"],
                    3,
                ),

            "Liquid Height [m]":
                round(
                    data["liquid_height_m"],
                    3,
                ),

            "Impeller Ø [m]":
                round(
                    data["impeller_diameter_m"],
                    3,
                ),

            "Impeller/Tank [-]":
                round(
                    data["Di_over_D"],
                    3,
                ),

            "H/D [-]":
                round(
                    data["H_over_D"],
                    3,
                ),

            "RPM":
                round(
                    data["rpm"],
                    1,
                ),

            "Agitator":
                data["agitator_type"],

            "Bottom":
                data["bottom_type"],

            "Top":
                data["top_type"],
        })


    st.dataframe(
        pd.DataFrame(
            geometry_rows
        ),
        use_container_width=True,
        hide_index=True,
    )


    st.divider()


    # =====================================================
    # GEOMETRY KPI
    # =====================================================

    selected_geometry = st.selectbox(
        "Select Reactor for Geometry Review",
        reactor_names,
        key="geometry_reactor",
    )


    data = reactors[
        selected_geometry
    ]


    g1, g2, g3, g4 = st.columns(4)

    with g1:

        st.metric(
            "Vessel Capacity",
            f"{data['vessel_volume_m3']:.2f} m³",
        )

    with g2:

        st.metric(
            "Working Volume",
            f"{data['working_volume']:.2f} m³",
        )

    with g3:

        st.metric(
            "Liquid Height",
            f"{data['liquid_height_m']:.2f} m",
        )

    with g4:

        st.metric(
            "Operating Fill",
            f"{data['fill_percent']:.1f} %",
        )


    with st.expander(
        "🔍 Detailed Geometry Information",
        expanded=True,
    ):

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Tank ID:** "
                f"{data['tank_id_m']:.3f} m"
            )

            st.write(
                f"**Straight Height:** "
                f"{data['straight_height_m']:.3f} m"
            )

            st.write(
                f"**Bottom Head:** "
                f"{data['bottom_type']}"
            )

            st.write(
                f"**Top Head:** "
                f"{data['top_type']}"
            )

        with col2:

            st.write(
                f"**Liquid Height:** "
                f"{data['liquid_height_m']:.3f} m"
            )

            st.write(
                f"**H/D:** "
                f"{data['H_over_D']:.3f}"
            )

            st.write(
                f"**Impeller/Tank:** "
                f"{data['Di_over_D']:.3f}"
            )

            st.write(
                f"**Baffles:** "
                f"{data['baffles']}"
            )


# =========================================================
# TAB 5
# VALIDATION
# =========================================================

with tab_validation:

    st.header("✅ Engineering Validation")

    st.caption(
        "Automated preliminary screening checks."
    )


    for reactor_name in reactor_names:

        data = reactors[
            reactor_name
        ]

        validation = data[
            "validation"
        ]


        st.subheader(
            f"🔍 {reactor_name}"
        )


        overall = validation.get(
            "overall",
            "REVIEW",
        )


        if overall == "PASS":

            st.success(
                "🟢 ENGINEERING STATUS — PASS"
            )

        elif overall == "REVIEW":

            st.warning(
                "🟡 ENGINEERING STATUS — REVIEW"
            )

        else:

            st.error(
                "🔴 ENGINEERING STATUS — FAIL"
            )


        checks = validation.get(
            "checks",
            [],
        )


        pass_count = sum(
            1
            for check in checks
            if check.get("severity") == "PASS"
        )

        warning_count = sum(
            1
            for check in checks
            if check.get("severity") == "WARNING"
        )

        fail_count = sum(
            1
            for check in checks
            if check.get("severity") == "FAIL"
        )


        v1, v2, v3 = st.columns(3)

        with v1:

            st.metric(
                "Passed Checks",
                pass_count,
            )

        with v2:

            st.metric(
                "Warnings",
                warning_count,
            )

        with v3:

            st.metric(
                "Failures",
                fail_count,
            )


        validation_rows = []


        for check in checks:

            validation_rows.append({

                "Status":
                    check.get(
                        "severity",
                        "REVIEW",
                    ),

                "Engineering Check":
                    check.get(
                        "message",
                        "",
                    ),
            })


        if validation_rows:

            st.dataframe(
                pd.DataFrame(
                    validation_rows
                ),
                use_container_width=True,
                hide_index=True,
            )


        st.divider()


    # =====================================================
    # ENGINEERING INSIGHTS
    # =====================================================

    st.subheader(
        "💡 Engineering Assessment"
    )


    for reactor_name in reactor_names:

        data = reactors[
            reactor_name
        ]

        result = data[
            "results"
        ]


        insights = []


        # FILL

        if data["fill_percent"] < 40:

            insights.append(
                "⚠️ Low operating fill. "
                "Review impeller coverage, circulation and headspace."
            )

        elif data["fill_percent"] > 85:

            insights.append(
                "⚠️ High operating fill. "
                "Review headspace and gas disengagement."
            )

        else:

            insights.append(
                "✅ Operating fill is within the preliminary screening range."
            )


        # BAFFLES

        if data["baffles"] < 4:

            insights.append(
                "⚠️ Fewer than four baffles selected. "
                "Review vortex suppression."
            )

        else:

            insights.append(
                "✅ Baffle count is acceptable for preliminary screening."
            )


        # IMPELLER RATIO

        if data["Di_over_D"] < 0.20:

            insights.append(
                "⚠️ Low impeller/tank ratio. "
                "Review bulk circulation and potential dead zones."
            )

        elif data["Di_over_D"] > 0.60:

            insights.append(
                "⚠️ High impeller/tank ratio. "
                "Review power, torque and mechanical loading."
            )

        else:

            insights.append(
                "✅ Impeller/tank ratio is within the preliminary screening range."
            )


        # REYNOLDS

        re_value = result.get(
            "Re",
            0,
        )


        if re_value < 10:

            insights.append(
                "🔵 Laminar mixing regime."
            )

        elif re_value < 10000:

            insights.append(
                "🟡 Transitional mixing regime."
            )

        else:

            insights.append(
                "🟢 Turbulent mixing regime."
            )


        # VISCOSITY

        if data["viscosity"] > 100:

            insights.append(
                "⚠️ High viscosity detected. "
                "Validate agitator selection and Np correlation."
            )


        with st.expander(
            f"💡 {reactor_name} Engineering Assessment",
            expanded=True,
        ):

            for insight in insights:

                st.write(
                    insight
                )


# =========================================================
# TAB 6
# 3D VISUALIZATION
# =========================================================

with tab_3d:

    st.header("🧊 3D Reactor Visualization")

    st.caption(
        "Interactive reactor vessel, agitator and baffle visualization."
    )


    selected_reactor = st.selectbox(
        "Select Reactor",
        reactor_names,
        key="3d_reactor",
    )


    data = reactors[
        selected_reactor
    ]


    try:

        fig = create_reactor_animation(

            D=data[
                "tank_id_m"
            ],

            straight_height=data[
                "straight_height_m"
            ],

            bottom_type=data[
                "bottom_type"
            ],

            top_type=data[
                "top_type"
            ],

            liquid_height=data[
                "liquid_height_m"
            ],

            agitator=data[
                "agitator_type"
            ],

            impeller_diameter=data[
                "impeller_diameter_m"
            ],

            number_impellers=data[
                "number_impellers"
            ],

            rpm=data[
                "rpm"
            ],

            number_baffles=data[
                "baffles"
            ],

            vortex_depth=data[
                "vortex_depth"
            ],

            frames_count=36,

        )


        st.plotly_chart(
            fig,
            use_container_width=True,
        )


    except Exception as e:

        st.error(
            f"3D visualization error: {e}"
        )


# =========================================================
# GLOBAL ENGINEERING NOTE
# =========================================================

st.divider()

with st.expander(
    "⚠️ Engineering Basis, Assumptions & Limitations"
):

    st.warning(
        """
This application is intended for preliminary reactor mixing,
scale-up and process engineering screening.

The following items should be validated before final equipment
specification or procurement:

• Impeller-specific Np and Nq data
• Njs / minimum solids suspension speed
• Blend time
• Gas dispersion and flooding
• KLa / mass-transfer correlations
• Shaft torque and mechanical loads
• Motor sizing and service factor
• Critical speed
• Seal design
• Pressure / vacuum design
• Exact ASME / vendor vessel geometry
• Heat-transfer area and duty
• Process-specific rheology
• Pilot-scale experimental data
• CFD / vendor validation where required

Generic Np/Nq values and simplified geometry correlations should
be treated as preliminary screening assumptions.

Final equipment design must be based on validated correlations,
vendor data, mechanical design calculations and process-specific
experimental evidence.
"""
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

f1, f2, f3 = st.columns(3)

with f1:

    st.caption(
        f"📁 Project: {project_name}"
    )

with f2:

    st.caption(
        f"👤 Prepared by: {prepared_by}"
    )

with f3:

    st.caption(
        "🏭 Reactor Scale-Up Engineering Studio"
    )

st.caption(
    "Preliminary engineering screening tool • "
    "Process Engineering Application"
)
