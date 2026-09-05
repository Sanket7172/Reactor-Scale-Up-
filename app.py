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
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# IMPORTANT:
# No HTML is used for KPI rendering.
# Streamlit native components are used instead.
# =========================================================

st.markdown(
    """
    <style>

    /* Main application width */
    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    /* Main title */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    /* Section spacing */
    h2, h3 {
        margin-top: 1rem;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    [data-testid="stMetricLabel"] {
        font-weight: 700;
    }

    [data-testid="stMetricValue"] {
        font-weight: 800;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 10px;
    }

    /* Horizontal separator */
    hr {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.title("🏭 Reactor Scale-Up Engineering Studio")

st.caption(
    "Reactor geometry • Mixing • Agitation • Scale-up • "
    "Hydrodynamics • Engineering validation"
)

st.divider()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Study Configuration")

project_name = st.sidebar.text_input(
    "Project / Study Name",
    value="Reactor Scale-Up Study",
)

prepared_by = st.sidebar.text_input(
    "Prepared By",
    value="Process Engineering",
)

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


# =========================================================
# PROCESS GUIDANCE
# =========================================================

PROCESS_GUIDANCE = {

    "Liquid-Liquid":
        "Focus on blending, circulation and phase dispersion.",

    "Solid-Liquid":
        "Focus on solids suspension, Njs and circulation.",

    "Gas-Liquid":
        "Focus on gas dispersion, P/V, tip speed and KLa.",

    "Gas-Liquid-Solid":
        "Consider gas dispersion and solids suspension together.",

    "Crystallization":
        "Consider suspension, shear, heat transfer and crystal quality.",

    "Precipitation":
        "Consider mixing intensity, local supersaturation and micromixing.",

    "Dissolution":
        "Focus on solids suspension, wetting and circulation.",

    "Extraction":
        "Focus on dispersion, interfacial area and coalescence.",

    "Neutralization":
        "Focus on blending, heat release and addition-point mixing.",

    "General Mixing":
        "Use P/V, tip speed, Re, Fr and Q/V for initial screening.",
}


with st.sidebar.expander("💡 Engineering Guidance", expanded=True):

    st.info(
        PROCESS_GUIDANCE.get(
            process_type,
            "Use validated engineering correlations.",
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

    reactor_names = ["Lab", "Pilot", "Commercial"]


# =========================================================
# STORAGE
# =========================================================

reactors = {}


# =========================================================
# SECTION 1
# REACTOR DEFINITION
# =========================================================

st.header("1️⃣ Reactor Definition")

st.caption(
    "Define vessel geometry, process properties and agitation configuration."
)


# =========================================================
# REACTOR INPUT LOOP
# =========================================================

for reactor_name in reactor_names:

    st.subheader(f"🏭 {reactor_name} Reactor")

    # -----------------------------------------------------
    # PROCESS PROPERTIES
    # -----------------------------------------------------

    st.markdown("##### 🧪 Process Properties")

    p1, p2, p3, p4 = st.columns(4)

    with p1:

        working_volume = st.number_input(
            "Working Volume [m³]",
            min_value=0.01,
            value=1.00,
            step=0.10,
            key=f"{reactor_name}_volume",
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


    # -----------------------------------------------------
    # VESSEL GEOMETRY
    # -----------------------------------------------------

    st.markdown("##### 📐 Vessel Geometry")

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


    # -----------------------------------------------------
    # AGITATION
    # -----------------------------------------------------

    st.markdown("##### 🌀 Agitation")

    a1, a2, a3, a4 = st.columns(4)

    with a1:

        agitator_type = st.selectbox(
            "Agitator Type",
            list(AGITATORS.keys()),
            index=1,
            key=f"{reactor_name}_agitator",
        )

    agitator_info = AGITATORS[agitator_type]

    default_ratio = agitator_info.get(
        "default_diameter_ratio",
        0.40,
    )

    default_impeller = tank_id * default_ratio

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
            "Number of Impellers [-]",
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


    # -----------------------------------------------------
    # BAFFLES
    # -----------------------------------------------------

    st.markdown("##### 🧱 Baffles")

    b1, b2, b3, b4 = st.columns(4)

    with b1:

        baffles = st.number_input(
            "Number of Baffles [-]",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
            key=f"{reactor_name}_baffles",
        )

    with b2:

        baffle_note = st.selectbox(
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

        st.metric(
            "Impeller / Tank",
            f"{(impeller_diameter / tank_id):.3f}",
        )

    with b4:

        st.metric(
            "No. of Impellers",
            f"{int(number_impellers)}",
        )


    # -----------------------------------------------------
    # UNIT CONVERSION
    # -----------------------------------------------------

    D = tank_id / 1000.0

    H = straight_height / 1000.0

    Di = impeller_diameter / 1000.0

    mu = viscosity / 1000.0

    sigma = surface_tension / 1000.0


    # -----------------------------------------------------
    # VESSEL VOLUME
    # -----------------------------------------------------

    vessel_volume = calculate_total_volume(
        D=D,
        straight_height=H,
        bottom_type=bottom_type,
        top_type=top_type,
    )


    # -----------------------------------------------------
    # LIQUID HEIGHT
    # -----------------------------------------------------

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

    except Exception as e:

        st.error(
            f"Liquid-height calculation error for "
            f"{reactor_name}: {e}"
        )

        liquid_height = 0.0
        calculated_total_volume = vessel_volume


    # -----------------------------------------------------
    # RATIOS
    # -----------------------------------------------------

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
        working_volume / vessel_volume * 100.0
        if vessel_volume > 0
        else 0.0
    )


    # -----------------------------------------------------
    # REACTOR CALCULATION
    # -----------------------------------------------------

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

            number_impellers=int(number_impellers),

            agitator=agitator_type,

        )

    except Exception as e:

        st.error(
            f"Calculation error for "
            f"{reactor_name}: {e}"
        )

        # Safe fallback instead of stopping the entire application.
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


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    try:

        validation = validate_reactor(

            volume_m3=working_volume,

            vessel_volume_m3=vessel_volume,

            tank_diameter_m=D,

            straight_height_m=H,

            liquid_height_m=liquid_height,

            impeller_diameter_m=Di,

            number_impellers=int(number_impellers),

            number_baffles=int(baffles),

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
                    "message": f"Validation calculation error: {e}",
                }
            ],
        }


    # -----------------------------------------------------
    # VORTEX SCREENING
    # -----------------------------------------------------

    if baffles == 0:

        vortex_depth = 0.10 * liquid_height

    elif baffles < 4:

        vortex_depth = 0.05 * liquid_height

    else:

        vortex_depth = 0.01 * liquid_height


    # -----------------------------------------------------
    # SAVE DATA
    # -----------------------------------------------------

    reactors[reactor_name] = {

        "working_volume": working_volume,

        "density": density,

        "viscosity": viscosity,

        "surface_tension": surface_tension,

        "tank_id_m": D,

        "straight_height_m": H,

        "bottom_type": bottom_type,

        "top_type": top_type,

        "agitator_type": agitator_type,

        "impeller_diameter_m": Di,

        "number_impellers": int(number_impellers),

        "rpm": rpm,

        "baffles": int(baffles),

        "baffle_config": baffle_note,

        "vessel_volume_m3": vessel_volume,

        "liquid_height_m": liquid_height,

        "fill_percent": fill_percent,

        "H_over_D": H_over_D,

        "Di_over_D": Di_over_D,

        "vortex_depth": vortex_depth,

        "results": results,

        "validation": validation,
    }

    st.divider()


# =========================================================
# SECTION 2
# ENGINEERING PERFORMANCE
# =========================================================

st.header("2️⃣ Engineering Performance")

st.caption(
    "Primary mixing, hydrodynamic and agitator performance indicators."
)


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    result = data["results"]

    st.subheader(
        f"📊 {reactor_name} — Mixing Performance"
    )


    # -----------------------------------------------------
    # GET RESULTS
    # -----------------------------------------------------

    power_kw = result.get("power_kw")

    pv = result.get("power_volume")

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


    # -----------------------------------------------------
    # MIXING REGIME
    # -----------------------------------------------------

    if reynolds >= 10000:

        regime = "Turbulent"
        regime_icon = "🟢"

    elif reynolds >= 10:

        regime = "Transitional"
        regime_icon = "🟡"

    else:

        regime = "Laminar"
        regime_icon = "🔵"


    # -----------------------------------------------------
    # FORMAT
    # -----------------------------------------------------

    power_text = (
        f"{power_kw:,.2f} kW"
        if power_kw is not None
        else "N/A"
    )

    pv_text = (
        f"{pv:,.1f} W/m³"
        if pv is not None
        else "N/A"
    )

    tip_text = (
        f"{tip_speed:,.2f} m/s"
    )

    re_text = (
        f"{reynolds:,.0f}"
    )

    pumping_text = (
        f"{pumping:,.2f} m³/h"
        if pumping is not None
        else "N/A"
    )

    turnover_text = (
        f"{turnover:,.2f} min"
        if turnover is not None
        else "N/A"
    )

    froude_text = (
        f"{froude:,.4f}"
    )

    torque_text = (
        f"{torque:,.1f} N·m"
        if torque is not None
        else "N/A"
    )


    # =====================================================
    # KPI ROW 1
    # =====================================================

    k1, k2, k3, k4 = st.columns(
        4,
        gap="medium",
    )

    with k1:

        st.metric(
            label="⚡ Agitator Power",
            value=power_text,
            help="Calculated agitator shaft power.",
        )

    with k2:

        st.metric(
            label="🔋 Power / Volume",
            value=pv_text,
            help="Mixing power intensity.",
        )

    with k3:

        st.metric(
            label="🌀 Impeller Tip Speed",
            value=tip_text,
            help="π × impeller diameter × rotational speed.",
        )

    with k4:

        st.metric(
            label=f"{regime_icon} Reynolds Number",
            value=re_text,
            help=f"Estimated mixing regime: {regime}.",
        )


    # =====================================================
    # KPI ROW 2
    # =====================================================

    k1, k2, k3, k4 = st.columns(
        4,
        gap="medium",
    )

    with k1:

        st.metric(
            label="💧 Pumping Capacity",
            value=pumping_text,
            help="Estimated impeller pumping capacity.",
        )

    with k2:

        st.metric(
            label="🔄 Vessel Turnover",
            value=turnover_text,
            help="Approximate working-volume turnover time.",
        )

    with k3:

        st.metric(
            label="🌊 Froude Number",
            value=froude_text,
            help="Ratio representing inertial versus gravitational effects.",
        )

    with k4:

        st.metric(
            label="⚙️ Agitator Torque",
            value=torque_text,
            help="Calculated agitator torque.",
        )


    # =====================================================
    # OPERATING CONDITIONS
    # =====================================================

    st.markdown("##### 🔧 Operating Conditions")

    o1, o2, o3, o4 = st.columns(4)

    with o1:

        st.metric(
            "Working Volume",
            f"{data['working_volume']:,.2f} m³",
        )

    with o2:

        st.metric(
            "Vessel Volume",
            f"{data['vessel_volume_m3']:,.2f} m³",
        )

    with o3:

        st.metric(
            "Operating Fill",
            f"{data['fill_percent']:,.1f} %",
        )

    with o4:

        st.metric(
            "Liquid Height",
            f"{data['liquid_height_m']:,.2f} m",
        )


    # =====================================================
    # DETAILED PARAMETERS
    # =====================================================

    with st.expander(
        "📐 Detailed Engineering Parameters",
        expanded=False,
    ):

        d1, d2, d3 = st.columns(3)

        with d1:

            st.markdown("#### 🌀 Mixing")

            st.write(
                f"**Agitator:** "
                f"{data['agitator_type']}"
            )

            st.write(
                f"**Flow Pattern:** "
                f"{AGITATORS[data['agitator_type']].get('flow', 'N/A')}"
            )

            st.write(
                f"**Number of Impellers:** "
                f"{data['number_impellers']} [-]"
            )

            st.write(
                f"**Impeller / Tank:** "
                f"{data['Di_over_D']:.3f} [-]"
            )

            st.write(
                f"**Liquid Height / Tank ID:** "
                f"{data['H_over_D']:.2f} [-]"
            )

            st.write(
                f"**Number of Baffles:** "
                f"{data['baffles']} [-]"
            )

        with d2:

            st.markdown("#### ⚡ Power")

            st.write(
                f"**Power:** "
                f"{power_text}"
            )

            st.write(
                f"**Power / Volume:** "
                f"{pv_text}"
            )

            st.write(
                f"**Torque:** "
                f"{torque_text}"
            )

            np_value = result.get("Np")

            st.write(
                "**Power Number (Np):** "
                f"{np_value if np_value is not None else 'N/A'} [-]"
            )

        with d3:

            st.markdown("#### 💧 Hydrodynamics")

            st.write(
                f"**Pumping Rate:** "
                f"{pumping_text}"
            )

            st.write(
                f"**Q/V:** "
                f"{result.get('qv_1_h', 0):,.2f} h⁻¹"
            )

            st.write(
                f"**Turnover:** "
                f"{turnover_text}"
            )

            nq_value = result.get("Nq")

            st.write(
                "**Flow Number (Nq):** "
                f"{nq_value if nq_value is not None else 'N/A'} [-]"
            )

    st.divider()


# =========================================================
# SECTION 3
# GEOMETRY SUMMARY
# =========================================================

st.header("3️⃣ Reactor Geometry Summary")

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

        "RPM [min⁻¹]":
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
    pd.DataFrame(geometry_rows),
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# SECTION 4
# SCALE-UP COMPARISON
# =========================================================

if len(reactor_names) >= 2:

    st.header("4️⃣ Scale-Up Comparison")

    st.caption(
        "Screening-level comparison between base and target reactor."
    )

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
                base_result.get("viscosity_pa_s"),

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
                target_result.get("viscosity_pa_s"),

            "Np":
                target_result.get("Np"),

            "Nq":
                target_result.get("Nq"),
        }


        try:

            scaleup = calculate_scaleup(

                base=base_for_scaleup,

                target=target_for_scaleup,

                basis=scaleup_basis,

            )

        except Exception as e:

            st.error(
                f"Scale-up calculation error "
                f"({base_name} → {target_name}): {e}"
            )

            continue


        st.subheader(
            f"📈 {base_name} → {target_name}"
        )


        s1, s2, s3 = st.columns(3)

        with s1:

            target_rpm = scaleup.get(
                "target_rpm"
            )

            st.metric(
                "Target Agitator Speed",
                (
                    f"{target_rpm:,.1f} RPM"
                    if target_rpm is not None
                    else "N/A"
                ),
            )

        with s2:

            target_tip = scaleup.get(
                "target_tip_speed"
            )

            st.metric(
                "Target Tip Speed",
                (
                    f"{target_tip:,.2f} m/s"
                    if target_tip is not None
                    else "N/A"
                ),
            )

        with s3:

            st.metric(
                "Scale-Up Basis",
                scaleup_basis,
            )


        message = scaleup.get(
            "message",
            "Review scale-up result.",
        )

        st.info(message)


# =========================================================
# SECTION 5
# ENGINEERING VALIDATION
# =========================================================

st.header("5️⃣ Engineering Validation")


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    validation = data["validation"]

    st.subheader(
        f"🔍 {reactor_name}"
    )


    overall = validation.get(
        "overall",
        "REVIEW",
    )


    if overall == "PASS":

        st.success(
            "🟢 Overall Status: PASS"
        )

    elif overall == "REVIEW":

        st.warning(
            "🟡 Overall Status: REVIEW"
        )

    else:

        st.error(
            "🔴 Overall Status: FAIL"
        )


    validation_rows = []


    for check in validation.get(
        "checks",
        [],
    ):

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
            pd.DataFrame(validation_rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No validation checks returned."
        )


# =========================================================
# SECTION 6
# 3D VISUALIZATION
# =========================================================

st.header("6️⃣ 3D Reactor Visualization")

st.caption(
    "Interactive reactor geometry and agitator visualization."
)


selected_reactor = st.selectbox(
    "Select Reactor for 3D View",
    reactor_names,
)


data = reactors[selected_reactor]


try:

    fig = create_reactor_animation(

        D=data["tank_id_m"],

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
# SECTION 7
# ENGINEERING INSIGHTS
# =========================================================

st.header("7️⃣ Engineering Insights")


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    result = data["results"]

    insights = []


    # -----------------------------------------------------
    # FILL
    # -----------------------------------------------------

    if data["fill_percent"] < 40:

        insights.append(
            "⚠️ Low operating fill. "
            "Review impeller coverage, liquid circulation and headspace."
        )

    elif data["fill_percent"] > 85:

        insights.append(
            "⚠️ High operating fill. "
            "Review headspace, gas disengagement and expansion allowance."
        )

    else:

        insights.append(
            "✅ Operating fill is within the preliminary screening range."
        )


    # -----------------------------------------------------
    # BAFFLES
    # -----------------------------------------------------

    if data["baffles"] < 4:

        insights.append(
            "⚠️ Fewer than four baffles selected. "
            "Review vortex suppression."
        )

    else:

        insights.append(
            "✅ Baffle count is suitable for preliminary screening."
        )


    # -----------------------------------------------------
    # IMPELLER RATIO
    # -----------------------------------------------------

    if data["Di_over_D"] < 0.20:

        insights.append(
            "⚠️ Small impeller/tank ratio. "
            "Check bulk circulation and dead zones."
        )

    elif data["Di_over_D"] > 0.60:

        insights.append(
            "⚠️ Large impeller/tank ratio. "
            "Review power, torque and mechanical loads."
        )

    else:

        insights.append(
            "✅ Impeller/tank ratio is within the preliminary screening range."
        )


    # -----------------------------------------------------
    # REYNOLDS
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # VISCOSITY
    # -----------------------------------------------------

    if data["viscosity"] > 100:

        insights.append(
            "⚠️ High viscosity detected. "
            "Validate impeller selection, Np and power correlation."
        )


    with st.expander(
        f"💡 {reactor_name} Engineering Assessment",
        expanded=True,
    ):

        for insight in insights:

            st.write(insight)


# =========================================================
# ENGINEERING LIMITATIONS
# =========================================================

with st.expander(
    "⚠️ Engineering Limitations & Design Note"
):

    st.warning(
        """
This dashboard is intended for preliminary engineering screening
and reactor scale-up assessment.

Before final equipment specification, validate:

• Vendor-specific Np / Nq data
• Njs / solids suspension correlations
• Blend time
• Gas dispersion and flooding
• KLa
• Shaft torque and mechanical loads
• Motor sizing and service factor
• Critical speed
• Seal design
• Pressure / vacuum design
• Exact reactor-head geometry
• Heat-transfer requirements
• Pilot-scale experimental data
• Process-specific mixing requirements

Final equipment design should use validated engineering
correlations, vendor data and process-specific test results.
"""
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    f"Project: {project_name}  |  "
    f"Prepared by: {prepared_by}  |  "
    f"Reactor Scale-Up Engineering Studio"
)

st.caption(
    "Preliminary engineering screening tool — "
    "not a substitute for detailed equipment design."
)
