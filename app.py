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
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* ---------- MAIN PAGE ---------- */

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }


    /* ---------- HEADER ---------- */

    .dashboard-header {
        padding: 22px 28px;
        border-radius: 16px;
        margin-bottom: 24px;
        background: linear-gradient(
            135deg,
            #eef4ff 0%,
            #ffffff 60%,
            #f4f8ff 100%
        );
        border: 1px solid #d9e2f2;
    }

    .dashboard-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 5px;
        color: #172033;
    }

    .dashboard-subtitle {
        font-size: 1rem;
        color: #667085;
    }


    /* ---------- SECTION HEADER ---------- */

    .section-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #172033;
        margin-top: 20px;
        margin-bottom: 12px;
    }


    /* ---------- KPI CARD ---------- */

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e1e6ef;
        border-radius: 14px;
        padding: 18px 16px;
        min-height: 145px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.06);
        margin-bottom: 12px;
    }

    .kpi-label {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        color: #667085;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: clamp(1.45rem, 2.2vw, 2rem);
        line-height: 1.15;
        font-weight: 800;
        color: #101828;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .kpi-unit {
        font-size: 0.90rem;
        font-weight: 600;
        color: #667085;
        margin-top: 5px;
    }

    .kpi-note {
        font-size: 0.72rem;
        color: #98A2B3;
        margin-top: 8px;
    }


    /* ---------- OPERATING CARD ---------- */

    .operating-card {
        background: #ffffff;
        border: 1px solid #e1e6ef;
        border-radius: 14px;
        padding: 18px;
        margin-top: 8px;
        margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(16, 24, 40, 0.04);
    }

    .operating-title {
        font-size: 0.95rem;
        font-weight: 750;
        color: #344054;
        margin-bottom: 15px;
    }

    .operating-item {
        padding: 8px 4px;
    }

    .operating-label {
        font-size: 0.75rem;
        color: #667085;
        margin-bottom: 4px;
    }

    .operating-value {
        font-size: 1rem;
        font-weight: 700;
        color: #101828;
    }


    /* ---------- INFO BOX ---------- */

    .engineering-box {
        background: #f8fafc;
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        padding: 16px;
        margin-top: 10px;
        margin-bottom: 16px;
    }


    /* ---------- SIDEBAR ---------- */

    [data-testid="stSidebar"] {
        border-right: 1px solid #e4e7ec;
    }


    /* ---------- TABLE ---------- */

    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }


    /* ---------- MOBILE ---------- */

    @media (max-width: 900px) {

        .dashboard-title {
            font-size: 1.7rem;
        }

        .kpi-card {
            min-height: 125px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="dashboard-header">

        <div class="dashboard-title">
            🏭 Reactor Scale-Up Engineering Studio
        </div>

        <div class="dashboard-subtitle">
            Reactor geometry • Mixing • Agitation • Scale-up •
            Hydrodynamics • Engineering validation
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Study Configuration")

project_name = st.sidebar.text_input(
    "Project / Study Name",
    "Reactor Scale-Up Study",
)

prepared_by = st.sidebar.text_input(
    "Prepared By",
    "Process Engineering",
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
        "Use P/V, tip speed, Re, Fr and Q/V as initial screening parameters.",
}


with st.sidebar.expander("💡 Engineering Guidance"):

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
# REACTOR DEFINITION
# =========================================================

st.markdown(
    '<div class="section-title">1️⃣ Reactor Definition</div>',
    unsafe_allow_html=True,
)


for reactor_name in reactor_names:

    st.subheader(
        f"🏭 {reactor_name} Reactor"
    )

    # -----------------------------------------------------
    # PROCESS PARAMETERS
    # -----------------------------------------------------

    st.markdown("##### 🧪 Process Properties")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        working_volume = st.number_input(
            "Working Volume [m³]",
            min_value=0.01,
            value=1.0,
            step=0.10,
            key=f"{reactor_name}_volume",
        )

    with c2:

        density = st.number_input(
            "Density [kg/m³]",
            min_value=1.0,
            value=1000.0,
            step=10.0,
            key=f"{reactor_name}_density",
        )

    with c3:

        viscosity = st.number_input(
            "Viscosity [mPa·s]",
            min_value=0.01,
            value=1.0,
            step=0.1,
            key=f"{reactor_name}_viscosity",
        )

    with c4:

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

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        tank_id = st.number_input(
            "Tank ID [mm]",
            min_value=100.0,
            value=1000.0,
            step=50.0,
            key=f"{reactor_name}_tank_id",
        )

    with c2:

        straight_height = st.number_input(
            "Straight Height [mm]",
            min_value=100.0,
            value=1500.0,
            step=50.0,
            key=f"{reactor_name}_straight_height",
        )

    with c3:

        bottom_type = st.selectbox(
            "Bottom Head",
            list(REACTOR_HEADS.keys()),
            index=1,
            key=f"{reactor_name}_bottom",
        )

    with c4:

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

    c1, c2, c3, c4 = st.columns(4)

    with c1:

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

    default_impeller = (
        tank_id *
        default_ratio
    )

    with c2:

        impeller_diameter = st.number_input(
            "Impeller Diameter [mm]",
            min_value=20.0,
            value=float(default_impeller),
            step=10.0,
            key=f"{reactor_name}_impeller",
        )

    with c3:

        number_impellers = st.number_input(
            "Number of Impellers [-]",
            min_value=1,
            max_value=6,
            value=1,
            step=1,
            key=f"{reactor_name}_nimp",
        )

    with c4:

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

    c1, c2 = st.columns(4)

    with c1:

        baffles = st.number_input(
            "Baffles [-]",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
            key=f"{reactor_name}_baffles",
        )


    # =====================================================
    # UNIT CONVERSIONS
    # =====================================================

    D = tank_id / 1000.0
    H = straight_height / 1000.0
    Di = impeller_diameter / 1000.0

    mu = viscosity / 1000.0
    sigma = surface_tension / 1000.0


    # =====================================================
    # VESSEL VOLUME
    # =====================================================

    vessel_volume = calculate_total_volume(
        D=D,
        straight_height=H,
        bottom_type=bottom_type,
        top_type=top_type,
    )


    # =====================================================
    # LIQUID HEIGHT
    # =====================================================

    liquid_height, calculated_total_volume = (
        liquid_height_from_volume(
            working_volume=working_volume,
            D=D,
            straight_height=H,
            bottom_type=bottom_type,
            top_type=top_type,
        )
    )


    # =====================================================
    # GEOMETRY RATIOS
    # =====================================================

    fill_percent = (
        working_volume /
        vessel_volume *
        100.0
        if vessel_volume > 0
        else 0.0
    )

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


    # =====================================================
    # REACTOR CALCULATION
    # =====================================================

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

        st.error(
            f"Calculation error for {reactor_name}: {e}"
        )

        st.stop()


    # =====================================================
    # VALIDATION
    # =====================================================

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


    # =====================================================
    # VORTEX SCREENING
    # =====================================================

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


    # =====================================================
    # STORE
    # =====================================================

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


# =========================================================
# ENGINEERING KPI DASHBOARD
# =========================================================

st.markdown(
    '<div class="section-title">2️⃣ Engineering Performance</div>',
    unsafe_allow_html=True,
)

st.caption(
    "All displayed values include their engineering units."
)


for reactor_name in reactor_names:

    data = reactors[reactor_name]
    result = data["results"]

    st.subheader(
        f"📊 {reactor_name} — Mixing Performance"
    )


    # =====================================================
    # EXTRACT VALUES
    # =====================================================

    power_kw = result.get("power_kw")
    pv = result.get("power_volume")
    tip_speed = result.get("tip_speed", 0)
    reynolds = result.get("Re", 0)

    pumping = result.get("pumping_m3_h")
    turnover = result.get("turnover_time_min")

    froude = result.get("Fr", 0)
    torque = result.get("torque_nm")


    # =====================================================
    # FORMAT VALUES
    # =====================================================

    power_text = (
        f"{power_kw:,.2f}"
        if power_kw is not None
        else "N/A"
    )

    pv_text = (
        f"{pv:,.1f}"
        if pv is not None
        else "N/A"
    )

    tip_text = (
        f"{tip_speed:,.2f}"
    )

    re_text = (
        f"{reynolds:,.0f}"
    )

    pumping_text = (
        f"{pumping:,.2f}"
        if pumping is not None
        else "N/A"
    )

    turnover_text = (
        f"{turnover:,.2f}"
        if turnover is not None
        else "N/A"
    )

    froude_text = (
        f"{froude:,.4f}"
    )

    torque_text = (
        f"{torque:,.1f}"
        if torque is not None
        else "N/A"
    )


    # =====================================================
    # KPI ROW 1
    # =====================================================

    k1, k2, k3, k4 = st.columns(4)


    with k1:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    ⚡ Agitator Power
                </div>

                <div class="kpi-value">
                    {power_text}
                </div>

                <div class="kpi-unit">
                    kW
                </div>

                <div class="kpi-note">
                    Calculated shaft power
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with k2:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    🔋 Power / Volume
                </div>

                <div class="kpi-value">
                    {pv_text}
                </div>

                <div class="kpi-unit">
                    W/m³
                </div>

                <div class="kpi-note">
                    Mixing intensity
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with k3:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    🌀 Tip Speed
                </div>

                <div class="kpi-value">
                    {tip_text}
                </div>

                <div class="kpi-unit">
                    m/s
                </div>

                <div class="kpi-note">
                    π × Dᵢ × N
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with k4:

        if reynolds >= 10000:

            regime = "Turbulent"
            regime_icon = "🟢"

        elif reynolds >= 10:

            regime = "Transitional"
            regime_icon = "🟡"

        else:

            regime = "Laminar"
            regime_icon = "🔵"


        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    {regime_icon} Reynolds Number
                </div>

                <div class="kpi-value">
                    {re_text}
                </div>

                <div class="kpi-unit">
                    [-] dimensionless
                </div>

                <div class="kpi-note">
                    {regime} flow regime
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # KPI ROW 2
    # =====================================================

    k1, k2, k3, k4 = st.columns(4)


    with k1:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    💧 Pumping Capacity
                </div>

                <div class="kpi-value">
                    {pumping_text}
                </div>

                <div class="kpi-unit">
                    m³/h
                </div>

                <div class="kpi-note">
                    Impeller pumping rate
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with k2:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    🔄 Turnover Time
                </div>

                <div class="kpi-value">
                    {turnover_text}
                </div>

                <div class="kpi-unit">
                    min / turnover
                </div>

                <div class="kpi-note">
                    V / Q
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with k3:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    🌊 Froude Number
                </div>

                <div class="kpi-value">
                    {froude_text}
                </div>

                <div class="kpi-unit">
                    [-] dimensionless
                </div>

                <div class="kpi-note">
                    Inertial / gravity effects
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with k4:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    ⚙️ Agitator Torque
                </div>

                <div class="kpi-value">
                    {torque_text}
                </div>

                <div class="kpi-unit">
                    N·m
                </div>

                <div class="kpi-note">
                    P / (2πN)
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # OPERATING CONDITIONS
    # =====================================================

    st.markdown(
        """
        <div class="operating-card">

            <div class="operating-title">
                🔧 Operating & Geometry Conditions
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    o1, o2, o3, o4, o5, o6 = st.columns(6)


    with o1:

        st.metric(
            "Working Volume",
            f"{data['working_volume']:,.2f} m³",
        )


    with o2:

        st.metric(
            "Tank ID",
            f"{data['tank_id_m']:,.2f} m",
        )


    with o3:

        st.metric(
            "Liquid Height",
            f"{data['liquid_height_m']:,.2f} m",
        )


    with o4:

        st.metric(
            "Impeller Ø",
            f"{data['impeller_diameter_m']:,.3f} m",
        )


    with o5:

        st.metric(
            "Agitator Speed",
            f"{data['rpm']:,.0f} RPM",
        )


    with o6:

        st.metric(
            "Fill Level",
            f"{data['fill_percent']:,.1f} %",
        )


    # =====================================================
    # DETAILED PARAMETERS
    # =====================================================

    with st.expander(
        "📐 View Detailed Engineering Parameters",
        expanded=False,
    ):

        d1, d2, d3 = st.columns(3)


        with d1:

            st.markdown("#### 🌀 Mixing")

            st.write(
                f"**Agitator:** {data['agitator_type']}"
            )

            st.write(
                f"**Impellers:** "
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
                f"**Baffles:** "
                f"{data['baffles']} [-]"
            )


        with d2:

            st.markdown("#### ⚡ Power")

            st.write(
                f"**Power:** "
                f"{power_text} kW"
            )

            st.write(
                f"**Power / Volume:** "
                f"{pv_text} W/m³"
            )

            st.write(
                f"**Torque:** "
                f"{torque_text} N·m"
            )

            st.write(
                f"**Power Number, Np:** "
                f"{result.get('Np')} [-]"
            )


        with d3:

            st.markdown("#### 💧 Hydrodynamics")

            st.write(
                f"**Pumping Rate:** "
                f"{pumping_text} m³/h"
            )

            st.write(
                f"**Q/V:** "
                f"{result.get('qv_1_h', 0):,.2f} h⁻¹"
            )

            st.write(
                f"**Turnover Time:** "
                f"{turnover_text} min"
            )

            st.write(
                f"**Flow Number, Nq:** "
                f"{result.get('Nq')} [-]"
            )


# =========================================================
# GEOMETRY SUMMARY
# =========================================================

st.markdown(
    '<div class="section-title">3️⃣ Reactor Geometry Summary</div>',
    unsafe_allow_html=True,
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
    })


st.dataframe(
    pd.DataFrame(
        geometry_rows
    ),
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# SCALE-UP COMPARISON
# =========================================================

if len(reactor_names) >= 2:

    st.markdown(
        '<div class="section-title">4️⃣ Scale-Up Comparison</div>',
        unsafe_allow_html=True,
    )


    base_name = reactor_names[0]

    base_data = reactors[base_name]


    for target_name in reactor_names[1:]:

        target_data = reactors[target_name]


        base_result = base_data["results"]

        target_result = target_data["results"]


        base_for_scaleup = {

            "working_volume":
                base_data["working_volume"],

            "impeller_diameter_m":
                base_data["impeller_diameter_m"],

            "rpm":
                base_data["rpm"],

            "tip_speed":
                base_result.get(
                    "tip_speed"
                ),

            "power_volume":
                base_result.get(
                    "power_volume"
                ),

            "qv_1_h":
                base_result.get(
                    "qv_1_h"
                ),

            "pumping_m3_h":
                base_result.get(
                    "pumping_m3_h"
                ),

            "density":
                base_data["density"],

            "viscosity_pa_s":
                base_result.get(
                    "viscosity_pa_s"
                ),

            "Np":
                base_result.get(
                    "Np"
                ),

            "Nq":
                base_result.get(
                    "Nq"
                ),
        }


        target_for_scaleup = {

            "working_volume":
                target_data["working_volume"],

            "impeller_diameter_m":
                target_data["impeller_diameter_m"],

            "rpm":
                target_data["rpm"],

            "tip_speed":
                target_result.get(
                    "tip_speed"
                ),

            "power_volume":
                target_result.get(
                    "power_volume"
                ),

            "qv_1_h":
                target_result.get(
                    "qv_1_h"
                ),

            "pumping_m3_h":
                target_result.get(
                    "pumping_m3_h"
                ),

            "density":
                target_data["density"],

            "viscosity_pa_s":
                target_result.get(
                    "viscosity_pa_s"
                ),

            "Np":
                target_result.get(
                    "Np"
                ),

            "Nq":
                target_result.get(
                    "Nq"
                ),
        }


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


        st.subheader(
            f"📈 {base_name} → {target_name}"
        )


        s1, s2, s3 = st.columns(3)


        with s1:

            target_rpm = scaleup.get(
                "target_rpm"
            )

            if target_rpm is not None:

                st.metric(
                    "Calculated Target Speed",
                    f"{target_rpm:,.1f} RPM",
                )

            else:

                st.metric(
                    "Calculated Target Speed",
                    "N/A",
                )


        with s2:

            target_tip = scaleup.get(
                "target_tip_speed"
            )

            if target_tip is not None:

                st.metric(
                    "Target Tip Speed",
                    f"{target_tip:,.2f} m/s",
                )

            else:

                st.metric(
                    "Target Tip Speed",
                    "N/A",
                )


        with s3:

            st.metric(
                "Scale-Up Basis",
                scaleup_basis,
            )


        st.info(
            scaleup.get(
                "message",
                "Review scale-up result.",
            )
        )


# =========================================================
# VALIDATION
# =========================================================

st.markdown(
    '<div class="section-title">5️⃣ Engineering Validation</div>',
    unsafe_allow_html=True,
)


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    validation = data["validation"]


    st.subheader(
        f"🔍 {reactor_name}"
    )


    if validation["overall"] == "PASS":

        st.success(
            "🟢 Overall Status: PASS"
        )

    elif validation["overall"] == "REVIEW":

        st.warning(
            "🟡 Overall Status: REVIEW"
        )

    else:

        st.error(
            "🔴 Overall Status: FAIL"
        )


    validation_rows = []


    for check in validation["checks"]:

        validation_rows.append({

            "Status":
                check["severity"],

            "Engineering Check":
                check["message"],
        })


    st.dataframe(
        pd.DataFrame(
            validation_rows
        ),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 3D VISUALIZATION
# =========================================================

st.markdown(
    '<div class="section-title">6️⃣ 3D Reactor Visualization</div>',
    unsafe_allow_html=True,
)


selected_reactor = st.selectbox(
    "Select Reactor",
    reactor_names,
)


data = reactors[
    selected_reactor
]


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
# ENGINEERING INSIGHTS
# =========================================================

st.markdown(
    '<div class="section-title">7️⃣ Engineering Insights</div>',
    unsafe_allow_html=True,
)


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    result = data["results"]

    insights = []


    if data["fill_percent"] < 40:

        insights.append(
            "⚠️ Low operating fill. Review impeller coverage and circulation."
        )

    elif data["fill_percent"] > 85:

        insights.append(
            "⚠️ High operating fill. Review headspace and gas disengagement."
        )

    else:

        insights.append(
            "✅ Operating fill is within a commonly screened range."
        )


    if data["baffles"] < 4:

        insights.append(
            "⚠️ Fewer than four baffles selected. Review vortex suppression."
        )

    else:

        insights.append(
            "✅ Baffle configuration is suitable for preliminary vortex screening."
        )


    if data["Di_over_D"] < 0.20:

        insights.append(
            "⚠️ Small impeller/tank ratio. Check bulk circulation."
        )

    elif data["Di_over_D"] > 0.60:

        insights.append(
            "⚠️ Large impeller/tank ratio. Review power and mechanical loads."
        )

    else:

        insights.append(
            "✅ Impeller/tank diameter ratio is within the preliminary screening range."
        )


    if result.get("Re", 0) < 10:

        insights.append(
            "🔵 Laminar mixing regime."
        )

    elif result.get("Re", 0) < 10000:

        insights.append(
            "🟡 Transitional mixing regime."
        )

    else:

        insights.append(
            "🟢 Turbulent mixing regime."
        )


    if data["viscosity"] > 100:

        insights.append(
            "⚠️ High viscosity detected. Validate impeller selection and power correlation."
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
# ENGINEERING LIMITATIONS
# =========================================================

with st.expander(
    "⚠️ Engineering Limitations & Design Note"
):

    st.warning(
        """
        This dashboard is intended for preliminary engineering
        screening, comparison and reactor scale-up assessment.

        Before final equipment specification, validate:

        • Vendor-specific Np / Nq data
        • Njs and solids suspension correlations
        • Blend time
        • Gas dispersion / flooding
        • KLa
        • Shaft torque and mechanical loads
        • Motor sizing and service factor
        • Critical speed
        • Seal design
        • Pressure / vacuum design
        • Exact reactor-head geometry
        • Heat-transfer requirements
        • Pilot-scale experimental data

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
