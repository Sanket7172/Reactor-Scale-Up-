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
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* Main page */

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }


    /* Header */

    .main-header {
        background: linear-gradient(
            135deg,
            #eef4ff,
            #ffffff
        );

        border: 1px solid #d9e2f2;

        border-radius: 16px;

        padding: 24px 28px;

        margin-bottom: 24px;
    }

    .main-header h1 {
        font-size: 2.15rem;
        font-weight: 800;
        margin: 0;
        color: #172033;
    }

    .main-header p {
        color: #667085;
        margin-top: 8px;
        font-size: 0.98rem;
    }


    /* Section */

    .section-header {
        font-size: 1.35rem;
        font-weight: 750;
        color: #172033;

        margin-top: 25px;
        margin-bottom: 15px;
    }


    /* KPI cards */

    .kpi-card {
        background: #ffffff;

        border: 1px solid #e1e6ef;

        border-radius: 14px;

        padding: 18px;

        min-height: 145px;

        margin-bottom: 15px;

        box-shadow:
            0 3px 12px
            rgba(16, 24, 40, 0.06);
    }


    .kpi-label {
        font-size: 0.76rem;

        font-weight: 700;

        letter-spacing: 0.04em;

        color: #667085;

        text-transform: uppercase;

        margin-bottom: 10px;
    }


    .kpi-value {
        font-size: 1.85rem;

        line-height: 1.15;

        font-weight: 800;

        color: #101828;

        overflow-wrap: anywhere;
    }


    .kpi-unit {
        font-size: 0.90rem;

        font-weight: 650;

        color: #475467;

        margin-top: 5px;
    }


    .kpi-note {
        font-size: 0.72rem;

        color: #98A2B3;

        margin-top: 8px;
    }


    /* Info cards */

    .info-card {
        background: #ffffff;

        border: 1px solid #e1e6ef;

        border-radius: 14px;

        padding: 18px;

        margin-bottom: 15px;

        box-shadow:
            0 2px 8px
            rgba(16, 24, 40, 0.04);
    }


    /* Mobile */

    @media (max-width: 900px) {

        .main-header h1 {
            font-size: 1.65rem;
        }

        .kpi-value {
            font-size: 1.45rem;
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
    <div class="main-header">
    """,
    unsafe_allow_html=True,
)

st.title("🏭 Reactor Scale-Up Engineering Studio")

st.caption(
    "Reactor geometry • Mixing • Agitation • Scale-up • "
    "Hydrodynamics • Engineering validation"
)

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


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
# STORAGE
# =========================================================

reactors = {}


# =========================================================
# REACTOR DEFINITION
# =========================================================

st.markdown(
    '<div class="section-header">1️⃣ Reactor Definition</div>',
    unsafe_allow_html=True,
)


for reactor_name in reactor_names:

    st.subheader(
        f"🏭 {reactor_name} Reactor"
    )


    # =====================================================
    # PROCESS PROPERTIES
    # =====================================================

    st.markdown(
        "##### 🧪 Process Properties"
    )

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


    # =====================================================
    # VESSEL GEOMETRY
    # =====================================================

    st.markdown(
        "##### 📐 Vessel Geometry"
    )

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


    # =====================================================
    # AGITATION
    # =====================================================

    st.markdown(
        "##### 🌀 Agitation"
    )

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
        tank_id *
        default_ratio
    )


    with a2:

        impeller_diameter = st.number_input(
            "Impeller Diameter [mm]",
            min_value=20.0,
            value=float(
                default_impeller
            ),
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


    # =====================================================
    # BAFFLES
    # =====================================================

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


    # =====================================================
    # UNIT CONVERSION
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
    # RATIOS
    # =====================================================

    if D > 0:

        H_over_D = (
            liquid_height / D
        )

        Di_over_D = (
            Di / D
        )

    else:

        H_over_D = 0

        Di_over_D = 0


    if vessel_volume > 0:

        fill_percent = (
            working_volume /
            vessel_volume *
            100
        )

    else:

        fill_percent = 0


    # =====================================================
    # CALCULATE REACTOR
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
            f"Calculation error for "
            f"{reactor_name}: {e}"
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
    # SAVE REACTOR DATA
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
# ENGINEERING PERFORMANCE
# =========================================================

st.markdown(
    '<div class="section-header">'
    '2️⃣ Engineering Performance'
    '</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Primary mixing and hydrodynamic performance indicators"
)


for reactor_name in reactor_names:

    data = reactors[
        reactor_name
    ]

    result = data[
        "results"
    ]


    st.subheader(
        f"📊 {reactor_name} — Mixing Performance"
    )


    # =====================================================
    # VALUES
    # =====================================================

    power_kw = result.get(
        "power_kw"
    )

    pv = result.get(
        "power_volume"
    )

    tip_speed = result.get(
        "tip_speed",
        0,
    )

    reynolds = result.get(
        "Re",
        0,
    )

    pumping = result.get(
        "pumping_m3_h"
    )

    turnover = result.get(
        "turnover_time_min"
    )

    froude = result.get(
        "Fr",
        0,
    )

    torque = result.get(
        "torque_nm"
    )


    # =====================================================
    # REGIME
    # =====================================================

    if reynolds >= 10000:

        regime = "Turbulent"
        regime_icon = "🟢"

    elif reynolds >= 10:

        regime = "Transitional"
        regime_icon = "🟡"

    else:

        regime = "Laminar"
        regime_icon = "🔵"


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

    k1, k2, k3, k4 = st.columns(
        4,
        gap="medium",
    )


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
                    🌀 Impeller Tip Speed
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
                    {regime} mixing regime
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # KPI ROW 2
    # =====================================================

    k1, k2, k3, k4 = st.columns(
        4,
        gap="medium",
    )


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
                    🔄 Vessel Turnover
                </div>

                <div class="kpi-value">
                    {turnover_text}
                </div>

                <div class="kpi-unit">
                    min / turnover
                </div>

                <div class="kpi-note">
                    Working volume / pumping rate
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
                    Calculated mixing torque
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # OPERATING CONDITIONS
    # =====================================================

    st.markdown(
        "##### 🔧 Operating Conditions"
    )


    o1, o2, o3 = st.columns(
        3,
        gap="medium",
    )


    with o1:

        st.metric(
            "Working Volume",
            f"{data['working_volume']:,.2f} m³",
        )

        st.metric(
            "Tank ID",
            f"{data['tank_id_m']:,.2f} m",
        )


    with o2:

        st.metric(
            "Liquid Height",
            f"{data['liquid_height_m']:,.2f} m",
        )

        st.metric(
            "Impeller Diameter",
            f"{data['impeller_diameter_m']:,.3f} m",
        )


    with o3:

        st.metric(
            "Agitator Speed",
            f"{data['rpm']:,.0f} RPM",
        )

        st.metric(
            "Operating Fill",
            f"{data['fill_percent']:,.1f} %",
        )


    # =====================================================
    # DETAILED PARAMETERS
    # =====================================================

    with st.expander(
        "📐 Detailed Engineering Parameters"
    ):

        d1, d2, d3 = st.columns(
            3,
            gap="large",
        )


        with d1:

            st.markdown(
                "#### 🌀 Mixing"
            )

            st.write(
                f"**Agitator:** "
                f"{data['agitator_type']}"
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

            st.markdown(
                "#### ⚡ Power"
            )

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
                f"**Power Number (Np):** "
                f"{result.get('Np')} [-]"
            )


        with d3:

            st.markdown(
                "#### 💧 Hydrodynamics"
            )

            st.write(
                f"**Pumping Rate:** "
                f"{pumping_text} m³/h"
            )

            st.write(
                f"**Q/V:** "
                f"{result.get('qv_1_h', 0):,.2f} h⁻¹"
            )

            st.write(
                f"**Turnover:** "
                f"{turnover_text} min"
            )

            st.write(
                f"**Flow Number (Nq):** "
                f"{result.get('Nq')} [-]"
            )


# =========================================================
# GEOMETRY SUMMARY
# =========================================================

st.markdown(
    '<div class="section-header">'
    '3️⃣ Reactor Geometry Summary'
    '</div>',
    unsafe_allow_html=True,
)


geometry_rows = []


for reactor_name in reactor_names:

    data = reactors[
        reactor_name
    ]


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
# SCALE-UP
# =========================================================

if len(reactor_names) >= 2:

    st.markdown(
        '<div class="section-header">'
        '4️⃣ Scale-Up Comparison'
        '</div>',
        unsafe_allow_html=True,
    )


    base_name = reactor_names[0]

    base_data = reactors[
        base_name
    ]


    for target_name in reactor_names[1:]:

        target_data = reactors[
            target_name
        ]


        base_result = base_data[
            "results"
        ]

        target_result = target_data[
            "results"
        ]


        base_for_scaleup = {

            "working_volume":
                base_data[
                    "working_volume"
                ],

            "impeller_diameter_m":
                base_data[
                    "impeller_diameter_m"
                ],

            "rpm":
                base_data[
                    "rpm"
                ],

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
                base_data[
                    "density"
                ],

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
                target_data[
                    "working_volume"
                ],

            "impeller_diameter_m":
                target_data[
                    "impeller_diameter_m"
                ],

            "rpm":
                target_data[
                    "rpm"
                ],

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
                target_data[
                    "density"
                ],

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

                base=
                    base_for_scaleup,

                target=
                    target_for_scaleup,

                basis=
                    scaleup_basis,
            )


        except Exception as e:

            st.error(
                f"Scale-up calculation error: {e}"
            )

            continue


        st.subheader(
            f"📈 {base_name} → {target_name}"
        )


        s1, s2, s3 = st.columns(
            3,
            gap="medium",
        )


        with s1:

            target_rpm = scaleup.get(
                "target_rpm"
            )

            if target_rpm is not None:

                st.metric(
                    "Target Agitator Speed",
                    f"{target_rpm:,.1f} RPM",
                )

            else:

                st.metric(
                    "Target Agitator Speed",
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
    '<div class="section-header">'
    '5️⃣ Engineering Validation'
    '</div>',
    unsafe_allow_html=True,
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


    if validation[
        "overall"
    ] == "PASS":

        st.success(
            "🟢 Overall Status: PASS"
        )

    elif validation[
        "overall"
    ] == "REVIEW":

        st.warning(
            "🟡 Overall Status: REVIEW"
        )

    else:

        st.error(
            "🔴 Overall Status: FAIL"
        )


    validation_rows = []


    for check in validation[
        "checks"
    ]:

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
    '<div class="section-header">'
    '6️⃣ 3D Reactor Visualization'
    '</div>',
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
# ENGINEERING INSIGHTS
# =========================================================

st.markdown(
    '<div class="section-header">'
    '7️⃣ Engineering Insights'
    '</div>',
    unsafe_allow_html=True,
)


for reactor_name in reactor_names:

    data = reactors[
        reactor_name
    ]

    result = data[
        "results"
    ]


    insights = []


    if data[
        "fill_percent"
    ] < 40:

        insights.append(
            "⚠️ Low operating fill. "
            "Review impeller coverage and circulation."
        )

    elif data[
        "fill_percent"
    ] > 85:

        insights.append(
            "⚠️ High operating fill. "
            "Review headspace and gas disengagement."
        )

    else:

        insights.append(
            "✅ Operating fill is within the preliminary screening range."
        )


    if data[
        "baffles"
    ] < 4:

        insights.append(
            "⚠️ Fewer than four baffles selected. "
            "Review vortex suppression."
        )

    else:

        insights.append(
            "✅ Baffle configuration is suitable for preliminary screening."
        )


    if data[
        "Di_over_D"
    ] < 0.20:

        insights.append(
            "⚠️ Small impeller/tank ratio. "
            "Check bulk circulation."
        )

    elif data[
        "Di_over_D"
    ] > 0.60:

        insights.append(
            "⚠️ Large impeller/tank ratio. "
            "Review power and mechanical loads."
        )

    else:

        insights.append(
            "✅ Impeller/tank ratio is within the preliminary screening range."
        )


    if result.get(
        "Re",
        0
    ) < 10:

        insights.append(
            "🔵 Laminar mixing regime."
        )

    elif result.get(
        "Re",
        0
    ) < 10000:

        insights.append(
            "🟡 Transitional mixing regime."
        )

    else:

        insights.append(
            "🟢 Turbulent mixing regime."
        )


    if data[
        "viscosity"
    ] > 100:

        insights.append(
            "⚠️ High viscosity detected. "
            "Validate impeller selection and power correlation."
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
        screening and reactor scale-up assessment.

        Validate the following before final equipment specification:

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
