import streamlit as st
import math

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# OPTIONAL PROJECT MODULES
# ============================================================

try:
    from calculations.engine import calculate_reactor
except Exception:
    calculate_reactor = None

try:
    from calculations.scaleup import calculate_scaleup
except Exception:
    calculate_scaleup = None

try:
    from calculations.validation import validate_reactor
except Exception:
    validate_reactor = None

try:
    from libraries.agitator_geometry import AGITATORS
except Exception:
    AGITATORS = {
        "Rushton Turbine": {"Np": 5.0, "Nq": 0.75},
        "Pitched Blade Turbine": {"Np": 1.3, "Nq": 0.75},
        "Hydrofoil": {"Np": 0.35, "Nq": 0.65},
        "Anchor": {"Np": 0.5, "Nq": 0.5},
    }

try:
    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )
except Exception:
    REACTOR_HEADS = {
        "2:1 Ellipsoidal": {},
        "Torispherical": {},
        "Flat Bottom": {},
    }

    def calculate_total_volume(diameter, straight_height, bottom_type, top_type):
        return math.pi * diameter**2 / 4 * straight_height

    def liquid_height_from_volume(
        volume,
        diameter,
        straight_height,
        bottom_type,
        top_type,
    ):
        area = math.pi * diameter**2 / 4

        if area <= 0:
            return 0.0

        return min(volume / area, straight_height)

try:
    from visualization.reactor_3d import create_reactor_animation
except Exception:
    create_reactor_animation = None


# ============================================================
# MODERN CSS
# ============================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 5%, rgba(59,130,246,0.10), transparent 25%),
        radial-gradient(circle at 90% 10%, rgba(139,92,246,0.10), transparent 25%),
        #f5f7fb;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #0f172a 0%,
        #172554 55%,
        #1e1b4b 100%
    );
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

.sidebar-title {
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 2px;
}

.sidebar-subtitle {
    font-size: 12px;
    color: #cbd5e1 !important;
    margin-bottom: 25px;
}

/* Hero */

.hero {
    background:
        linear-gradient(
            135deg,
            #0f172a 0%,
            #1e3a8a 48%,
            #6d28d9 100%
        );
    padding: 30px 34px;
    border-radius: 24px;
    color: white;
    margin-bottom: 24px;
    box-shadow: 0 14px 40px rgba(15,23,42,0.18);
}

.hero-title {
    font-size: 34px;
    font-weight: 850;
    margin: 0;
}

.hero-subtitle {
    margin-top: 8px;
    color: #dbeafe;
    font-size: 15px;
}

.status {
    display: inline-block;
    margin-top: 18px;
    padding: 7px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.20);
    font-size: 12px;
    font-weight: 700;
}

/* Section */

.section-title {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    margin-top: 20px;
    margin-bottom: 14px;
}

/* KPI cards */

.kpi-card {
    padding: 20px;
    border-radius: 18px;
    background: white;
    border: 1px solid #e5e7eb;
    box-shadow: 0 7px 24px rgba(15,23,42,0.06);
    min-height: 120px;
}

.kpi-label {
    font-size: 12px;
    color: #64748b;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.kpi-value {
    font-size: 27px;
    font-weight: 850;
    color: #0f172a;
    margin-top: 7px;
}

.kpi-blue {
    border-top: 5px solid #2563eb;
}

.kpi-purple {
    border-top: 5px solid #7c3aed;
}

.kpi-green {
    border-top: 5px solid #059669;
}

.kpi-orange {
    border-top: 5px solid #ea580c;
}

.kpi-red {
    border-top: 5px solid #dc2626;
}

/* Reactor cards */

.reactor-card {
    background: white;
    border-radius: 20px;
    border: 1px solid #e5e7eb;
    padding: 22px;
    box-shadow: 0 8px 28px rgba(15,23,42,0.06);
    margin-bottom: 18px;
}

.reactor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.reactor-name {
    font-size: 21px;
    font-weight: 800;
    color: #0f172a;
}

.reactor-tag {
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    background: #eff6ff;
    color: #1d4ed8;
}

/* Status */

.pass {
    color: #047857;
    background: #d1fae5;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 800;
}

.review {
    color: #b45309;
    background: #fef3c7;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 800;
}

.fail {
    color: #b91c1c;
    background: #fee2e2;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 800;
}

/* Buttons */

.stButton > button {
    border-radius: 12px;
    font-weight: 750;
    border: none;
    padding: 0.65rem 1.1rem;
}

/* Inputs */

div[data-baseweb="select"] > div,
.stNumberInput input,
.stTextInput input {
    border-radius: 10px !important;
}

/* Tabs */

button[data-baseweb="tab"] {
    font-weight: 700;
}

/* Footer */

.footer {
    margin-top: 40px;
    padding: 18px;
    border-radius: 16px;
    background: #0f172a;
    color: #cbd5e1;
    text-align: center;
    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "calculated" not in st.session_state:
    st.session_state.calculated = False

if "results" not in st.session_state:
    st.session_state.results = {}


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-title">⚗️ Reactor Studio</div>
        <div class="sidebar-subtitle">
        Process Engineering & Mixing Analysis
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Project")

    project_name = st.text_input(
        "Project Name",
        value="Reactor Scale-Up Study",
    )

    prepared_by = st.text_input(
        "Prepared By",
        value="Process Engineering",
    )

    st.markdown("### Study Configuration")

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

    engineering_focus = st.multiselect(
        "Engineering Focus",
        [
            "Power / Volume",
            "Tip Speed",
            "Mixing",
            "Suspension",
            "Gas Dispersion",
            "Heat Transfer",
            "Scale-Up",
            "Mechanical Geometry",
        ],
        default=[
            "Power / Volume",
            "Tip Speed",
            "Mixing",
        ],
    )

    st.divider()

    st.caption("Engineering calculation dashboard")
    st.caption("Use validated design data before final equipment selection.")


# ============================================================
# HERO
# ============================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">
            ⚗️ Reactor Scale-Up Engineering Studio
        </div>

        <div class="hero-subtitle">
            Professional process engineering dashboard for
            reactor geometry, agitation, power, mixing and scale-up analysis.
        </div>

        <div class="status">
            ● SYSTEM READY
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TOP PROJECT INFORMATION
# ============================================================

info1, info2, info3, info4 = st.columns(4)

with info1:
    st.metric("PROJECT", project_name)

with info2:
    st.metric("PROCESS", process_type)

with info3:
    st.metric("STUDY", study_mode)

with info4:
    st.metric("SCALE-UP BASIS", scaleup_basis)


# ============================================================
# TABS
# ============================================================

tab_dashboard, tab_setup, tab_performance, tab_scaleup, tab_validation, tab_3d, tab_insights = st.tabs(
    [
        "📊 Dashboard",
        "⚙️ Reactor Setup",
        "⚡ Performance",
        "📈 Scale-Up",
        "✅ Validation",
        "🧊 3D Reactor",
        "💡 Insights",
    ]
)


# ============================================================
# REACTOR SETUP
# ============================================================

with tab_setup:

    st.markdown(
        '<div class="section-title">⚙️ Reactor & Process Configuration</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.markdown("### 🧪 Process Conditions")

            volume_m3 = st.number_input(
                "Working Volume (m³)",
                min_value=0.01,
                value=5.0,
                step=0.1,
            )

            density = st.number_input(
                "Density (kg/m³)",
                min_value=1.0,
                value=1000.0,
                step=10.0,
            )

            viscosity = st.number_input(
                "Viscosity (mPa·s)",
                min_value=0.01,
                value=1.0,
                step=0.1,
            )

            surface_tension = st.number_input(
                "Surface Tension (mN/m)",
                min_value=0.01,
                value=30.0,
                step=1.0,
            )

    with col2:

        with st.container(border=True):

            st.markdown("### 🏭 Vessel Geometry")

            tank_diameter = st.number_input(
                "Tank Diameter (m)",
                min_value=0.10,
                value=2.0,
                step=0.05,
            )

            straight_height = st.number_input(
                "Straight Height (m)",
                min_value=0.10,
                value=2.5,
                step=0.05,
            )

            bottom_type = st.selectbox(
                "Bottom Head",
                list(REACTOR_HEADS.keys()),
            )

            top_type = st.selectbox(
                "Top Head",
                list(REACTOR_HEADS.keys()),
            )

    st.markdown(
        '<div class="section-title">⚙️ Agitation System</div>',
        unsafe_allow_html=True,
    )

    col3, col4, col5 = st.columns(3)

    with col3:

        agitator = st.selectbox(
            "Agitator Type",
            list(AGITATORS.keys()),
        )

    with col4:

        rpm = st.number_input(
            "Agitator Speed (RPM)",
            min_value=0.1,
            value=120.0,
            step=1.0,
        )

    with col5:

        impeller_diameter = st.number_input(
            "Impeller Diameter (m)",
            min_value=0.05,
            value=0.70,
            step=0.01,
        )

    col6, col7, col8 = st.columns(3)

    with col6:

        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
        )

    with col7:

        number_baffles = st.number_input(
            "Number of Baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
        )

    with col8:

        impeller_clearance = st.number_input(
            "Impeller Clearance (m)",
            min_value=0.01,
            value=0.25,
            step=0.01,
        )

    st.markdown("### 🚀 Calculate")

    calculate_button = st.button(
        "Calculate Reactor Performance",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# ENGINEERING CALCULATION
# ============================================================

def fallback_calculation():

    rho = density
    mu = viscosity / 1000.0
    N = rpm / 60.0
    D = impeller_diameter

    if rho <= 0:
        rho = 1000.0

    if mu <= 0:
        mu = 0.001

    reynolds = rho * N * D**2 / mu

    tip_speed = math.pi * D * N

    agitator_data = AGITATORS.get(
        agitator,
        {},
    )

    np_value = float(
        agitator_data.get(
            "Np",
            1.0,
        )
    )

    nq_value = float(
        agitator_data.get(
            "Nq",
            0.7,
        )
    )

    power_w = (
        np_value
        * rho
        * N**3
        * D**5
        * number_impellers
    )

    power_kw = power_w / 1000.0

    pv_w_m3 = (
        power_w / volume_m3
        if volume_m3 > 0
        else 0.0
    )

    pv_kw_m3 = pv_w_m3 / 1000.0

    pumping_m3_s = (
        nq_value
        * N
        * D**3
        * number_impellers
    )

    pumping_m3_h = pumping_m3_s * 3600.0

    qv = (
        pumping_m3_h / volume_m3
        if volume_m3 > 0
        else 0.0
    )

    turnover_time_min = (
        60.0 / qv
        if qv > 0
        else 0.0
    )

    froude = (
        N**2
        * D
        / 9.81
    )

    fill_area = (
        math.pi
        * tank_diameter**2
        / 4.0
    )

    liquid_height = (
        volume_m3 / fill_area
        if fill_area > 0
        else 0.0
    )

    tank_volume = (
        fill_area
        * straight_height
    )

    fill_percent = (
        100.0
        * volume_m3
        / tank_volume
        if tank_volume > 0
        else 0.0
    )

    d_t = (
        impeller_diameter / tank_diameter
        if tank_diameter > 0
        else 0.0
    )

    h_t = (
        liquid_height / tank_diameter
        if tank_diameter > 0
        else 0.0
    )

    c_t = (
        impeller_clearance / tank_diameter
        if tank_diameter > 0
        else 0.0
    )

    if reynolds < 10:
        regime = "Laminar"
    elif reynolds < 10000:
        regime = "Transitional"
    else:
        regime = "Turbulent"

    return {
        "power_w": power_w,
        "power_kw": power_kw,
        "power_volume": pv_w_m3,
        "power_volume_w_m3": pv_w_m3,
        "power_volume_kw_m3": pv_kw_m3,
        "tip_speed": tip_speed,
        "reynolds_number": reynolds,
        "reynolds": reynolds,
        "froude_number": froude,
        "froude": froude,
        "pumping_capacity": pumping_m3_h,
        "pumping_rate": pumping_m3_h,
        "qv": qv,
        "turnover_time": turnover_time_min,
        "liquid_height": liquid_height,
        "fill_percent": fill_percent,
        "tank_volume": tank_volume,
        "np": np_value,
        "nq": nq_value,
        "d_t": d_t,
        "h_t": h_t,
        "c_t": c_t,
        "mixing_regime": regime,
        "flow_pattern": "Axial" if nq_value > 0.65 else "Radial",
    }


if calculate_button:

    with st.spinner("Running engineering calculations..."):

        try:

            if calculate_reactor is not None:

                try:

                    results = calculate_reactor(
                        volume_m3=volume_m3,
                        tank_diameter_m=tank_diameter,
                        liquid_height_m=0.0,
                        density_kg_m3=density,
                        viscosity_pa_s=viscosity / 1000.0,
                        surface_tension_n_m=surface_tension / 1000.0,
                        rpm=rpm,
                        impeller_diameter_m=impeller_diameter,
                        number_impellers=number_impellers,
                        agitator=agitator,
                        impeller_clearance_m=impeller_clearance,
                    )

                except TypeError:

                    results = fallback_calculation()

            else:

                results = fallback_calculation()

        except Exception:

            results = fallback_calculation()

        st.session_state.results = results
        st.session_state.calculated = True

    st.success("Engineering calculation completed successfully.")


# ============================================================
# GET RESULTS
# ============================================================

results = st.session_state.results


def get_value(keys, default=0.0):

    if not results:
        return default

    for key in keys:

        if key in results:

            value = results[key]

            try:
                return float(value)
            except Exception:
                return value

    return default


# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:

    st.markdown(
        '<div class="section-title">📊 Engineering Dashboard</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info(
            "Enter the reactor parameters in the Reactor Setup tab and click "
            "'Calculate Reactor Performance'."
        )

    else:

        power_kw = get_value(
            ["power_kw", "power"],
            0.0,
        )

        pv_kw_m3 = get_value(
            [
                "power_volume_kw_m3",
                "pv_kw_m3",
            ],
            None,
        )

        if pv_kw_m3 is None:

            pv_w_m3 = get_value(
                [
                    "power_volume_w_m3",
                    "power_volume",
                    "pv_w_m3",
                ],
                0.0,
            )

            pv_kw_m3 = pv_w_m3 / 1000.0

        tip_speed = get_value(
            [
                "tip_speed",
                "tip_speed_m_s",
            ],
            0.0,
        )

        reynolds = get_value(
            [
                "reynolds_number",
                "reynolds",
            ],
            0.0,
        )

        fill_percent = get_value(
            [
                "fill_percent",
                "fill_percentage",
            ],
            0.0,
        )

        liquid_height = get_value(
            [
                "liquid_height",
                "liquid_height_m",
            ],
            0.0,
        )

        qv = get_value(
            [
                "qv",
                "pumping_per_volume",
            ],
            0.0,
        )

        turnover = get_value(
            [
                "turnover_time",
                "turnover_time_min",
            ],
            0.0,
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.markdown(
                f"""
                <div class="kpi-card kpi-blue">
                    <div class="kpi-label">Agitator Power</div>
                    <div class="kpi-value">{power_kw:.2f} kW</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            st.markdown(
                f"""
                <div class="kpi-card kpi-purple">
                    <div class="kpi-label">Power / Volume</div>
                    <div class="kpi-value">{pv_kw_m3:.4f} kW/m³</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:

            st.markdown(
                f"""
                <div class="kpi-card kpi-green">
                    <div class="kpi-label">Tip Speed</div>
                    <div class="kpi-value">{tip_speed:.2f} m/s</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col4:

            st.markdown(
                f"""
                <div class="kpi-card kpi-orange">
                    <div class="kpi-label">Reynolds Number</div>
                    <div class="kpi-value">{reynolds:,.0f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        col5, col6, col7, col8 = st.columns(4)

        with col5:

            st.metric(
                "Liquid Height",
                f"{liquid_height:.2f} m",
            )

        with col6:

            st.metric(
                "Fill %",
                f"{fill_percent:.1f} %",
            )

        with col7:

            st.metric(
                "Q/V",
                f"{qv:.2f} 1/h",
            )

        with col8:

            st.metric(
                "Turnover Time",
                f"{turnover:.2f} min",
            )

        st.markdown(
            '<div class="section-title">🏭 Reactor Overview</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"""
                <div class="reactor-card">

                    <div class="reactor-header">

                        <div class="reactor-name">
                            Reactor Configuration
                        </div>

                        <div class="reactor-tag">
                            {process_type}
                        </div>

                    </div>

                    <p><b>Working Volume:</b> {volume_m3:.2f} m³</p>
                    <p><b>Tank Diameter:</b> {tank_diameter:.2f} m</p>
                    <p><b>Liquid Height:</b> {liquid_height:.2f} m</p>
                    <p><b>Fill Level:</b> {fill_percent:.1f}%</p>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            flow_pattern = results.get(
                "flow_pattern",
                "Not specified",
            )

            mixing_regime = results.get(
                "mixing_regime",
                "Not specified",
            )

            st.markdown(
                f"""
                <div class="reactor-card">

                    <div class="reactor-header">

                        <div class="reactor-name">
                            Mixing System
                        </div>

                        <div class="reactor-tag">
                            {agitator}
                        </div>

                    </div>

                    <p><b>Speed:</b> {rpm:.1f} RPM</p>
                    <p><b>Impeller:</b> {impeller_diameter:.2f} m</p>
                    <p><b>Impellers:</b> {number_impellers}</p>
                    <p><b>Flow Pattern:</b> {flow_pattern}</p>
                    <p><b>Mixing Regime:</b> {mixing_regime}</p>

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# PERFORMANCE TAB
# ============================================================

with tab_performance:

    st.markdown(
        '<div class="section-title">⚡ Mixing Performance</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.warning("Run the reactor calculation first.")

    else:

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Power",
                f"{get_value(['power_kw', 'power']):.2f} kW",
            )

            st.metric(
                "Tip Speed",
                f"{get_value(['tip_speed']):.2f} m/s",
            )

        with col2:

            pv = get_value(
                [
                    "power_volume_kw_m3",
                    "pv_kw_m3",
                ],
                None,
            )

            if pv is None:

                pv = get_value(
                    [
                        "power_volume_w_m3",
                        "power_volume",
                    ],
                    0.0,
                ) / 1000.0

            st.metric(
                "P/V",
                f"{pv:.4f} kW/m³",
            )

            st.metric(
                "Reynolds Number",
                f"{get_value(['reynolds_number', 'reynolds']):,.0f}",
            )

        with col3:

            st.metric(
                "Froude Number",
                f"{get_value(['froude_number', 'froude']):.4f}",
            )

            st.metric(
                "Q/V",
                f"{get_value(['qv']):.3f} 1/h",
            )

        st.markdown(
            '<div class="section-title">📐 Geometry Ratios</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "D/T",
                f"{get_value(['d_t']):.3f}",
            )

        with c2:
            st.metric(
                "H/T",
                f"{get_value(['h_t']):.3f}",
            )

        with c3:
            st.metric(
                "C/T",
                f"{get_value(['c_t']):.3f}",
            )

        with c4:
            st.metric(
                "N Impellers",
                f"{number_impellers}",
            )

        st.markdown(
            '<div class="section-title">🔬 Engineering Interpretation</div>',
            unsafe_allow_html=True,
        )

        re_value = get_value(
            ["reynolds_number", "reynolds"],
            0,
        )

        if re_value < 10:

            st.warning(
                "The calculated Reynolds number indicates a laminar mixing regime."
            )

        elif re_value < 10000:

            st.warning(
                "The reactor is operating in the transitional mixing regime. "
                "Scale-up should be checked carefully."
            )

        else:

            st.success(
                "The calculated Reynolds number indicates turbulent mixing."
            )


# ============================================================
# SCALE-UP TAB
# ============================================================

with tab_scaleup:

    st.markdown(
        '<div class="section-title">📈 Scale-Up Analysis</div>',
        unsafe_allow_html=True,
    )

    if study_mode == "Single Reactor":

        st.info(
            "Select a Lab/Pilot/Commercial study mode from the sidebar "
            "to perform scale-up comparison."
        )

    else:

        st.markdown(
            """
            <div class="reactor-card">

            <div class="reactor-header">

                <div class="reactor-name">
                    Scale-Up Strategy
                </div>

                <div class="reactor-tag">
                    ENGINEERING BASIS
                </div>

            </div>

            <p>
            <b>Selected basis:</b>
            """
            + scaleup_basis
            + """
            </p>

            <p>
            The scale-up engine should compare geometry, agitation speed,
            power, P/V, tip speed, Reynolds number, pumping and other
            process-specific parameters.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Scale-Up Notes")

        if scaleup_basis == "Constant P/V":

            st.success(
                "Constant P/V selected. This basis maintains volumetric "
                "power input between scales."
            )

        elif scaleup_basis == "Constant Tip Speed":

            st.info(
                "Constant Tip Speed selected. This basis maintains "
                "impeller peripheral velocity."
            )

        elif scaleup_basis == "Constant RPM":

            st.info(
                "Constant RPM selected. Confirm that tip speed and P/V "
                "remain acceptable at the target scale."
            )

        else:

            st.info(
                f"{scaleup_basis} selected as the primary engineering basis."
            )


# ============================================================
# VALIDATION TAB
# ============================================================

with tab_validation:

    st.markdown(
        '<div class="section-title">✅ Engineering Validation</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info("Run the reactor calculation to activate validation.")

    else:

        validation_messages = []

        if tank_diameter <= 0:

            validation_messages.append(
                ("FAIL", "Tank diameter must be greater than zero.")
            )

        if impeller_diameter >= tank_diameter:

            validation_messages.append(
                (
                    "FAIL",
                    "Impeller diameter should be smaller than tank diameter.",
                )
            )

        if fill_percent > 100:

            validation_messages.append(
                (
                    "FAIL",
                    "Calculated liquid volume exceeds the available straight-side vessel volume.",
                )
            )

        if number_baffles < 4 and process_type != "High-Viscosity":

            validation_messages.append(
                (
                    "REVIEW",
                    "Less than four baffles are selected. Check vortexing and tangential flow.",
                )
            )

        if rpm <= 0:

            validation_messages.append(
                (
                    "FAIL",
                    "Agitator speed must be greater than zero.",
                )
            )

        if not validation_messages:

            validation_messages.append(
                (
                    "PASS",
                    "Basic dashboard-level engineering validation checks passed.",
                )
            )

        for status, message in validation_messages:

            if status == "PASS":

                st.success("PASS — " + message)

            elif status == "REVIEW":

                st.warning("REVIEW — " + message)

            else:

                st.error("FAIL — " + message)

        st.markdown("### Validation Summary")

        validation_data = {
            "Parameter": [
                "Working Volume",
                "Tank Diameter",
                "Impeller Diameter",
                "RPM",
                "Number of Impellers",
                "Number of Baffles",
                "Fill %",
            ],
            "Value": [
                f"{volume_m3:.2f} m³",
                f"{tank_diameter:.2f} m",
                f"{impeller_diameter:.2f} m",
                f"{rpm:.1f}",
                f"{number_impellers}",
                f"{number_baffles}",
                f"{fill_percent:.1f} %",
            ],
        }

        st.dataframe(
            validation_data,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 3D REACTOR TAB
# ============================================================

with tab_3d:

    st.markdown(
        '<div class="section-title">🧊 3D Reactor Visualization</div>',
        unsafe_allow_html=True,
    )

    if create_reactor_animation is None:

        st.info(
            "The 3D visualization module is not available. "
            "Add visualization/reactor_3d.py to activate this section."
        )

    else:

        try:

            if st.session_state.calculated:

                try:

                    fig = create_reactor_animation(
                        D=tank_diameter,
                        straight_height=straight_height,
                        bottom_type=bottom_type,
                        top_type=top_type,
                        liquid_height=get_value(
                            ["liquid_height"],
                            volume_m3,
                        ),
                        agitator=agitator,
                        impeller_diameter=impeller_diameter,
                        number_impellers=number_impellers,
                        rpm=rpm,
                        number_baffles=number_baffles,
                        vortex_depth=0.0,
                        frames_count=30,
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                    )

                except TypeError:

                    st.warning(
                        "The 3D module exists, but its function signature "
                        "does not match this dashboard version."
                    )

                except Exception as exc:

                    st.error(
                        f"3D visualization error: {exc}"
                    )

            else:

                st.info(
                    "Run the calculation first to generate the 3D reactor."
                )

        except Exception as exc:

            st.error(
                f"Unable to load 3D visualization: {exc}"
            )


# ============================================================
# INSIGHTS TAB
# ============================================================

with tab_insights:

    st.markdown(
        '<div class="section-title">💡 Engineering Insights</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info(
            "Run the calculation to generate engineering insights."
        )

    else:

        pv_value = get_value(
            [
                "power_volume_kw_m3",
                "pv_kw_m3",
            ],
            None,
        )

        if pv_value is None:

            pv_value = (
                get_value(
                    [
                        "power_volume_w_m3",
                        "power_volume",
                    ],
                    0.0,
                )
                / 1000.0
            )

        re_value = get_value(
            [
                "reynolds_number",
                "reynolds",
            ],
            0,
        )

        tip_value = get_value(
            [
                "tip_speed",
            ],
            0,
        )

        qv_value = get_value(
            [
                "qv",
            ],
            0,
        )

        insights = []

        if pv_value > 5:

            insights.append(
                "⚠️ P/V is relatively high. Check heat generation, shear sensitivity and motor loading."
            )

        elif pv_value > 0:

            insights.append(
                "✅ P/V has been calculated in kW/m³ and should be compared against the process-specific mixing requirement."
            )

        if re_value > 10000:

            insights.append(
                "✅ Mixing is in the turbulent regime based on the calculated Reynolds number."
            )

        elif re_value > 10:

            insights.append(
                "⚠️ Mixing is transitional. Scale-up correlations should be selected carefully."
            )

        else:

            insights.append(
                "⚠️ Mixing is laminar. Consider viscosity effects and impeller selection."
            )

        if tip_value > 10:

            insights.append(
                "⚠️ Tip speed is relatively high. Review shear-sensitive materials and mechanical limitations."
            )

        if qv_value > 0:

            insights.append(
                f"🔄 Estimated turnover rate is {qv_value:.2f} vessel volumes/hour."
            )

        if number_baffles < 4:

            insights.append(
                "⚠️ Baffle arrangement should be reviewed for vortex suppression."
            )

        if impeller_diameter / tank_diameter < 0.25:

            insights.append(
                "⚠️ D/T is relatively low. Check whether the selected impeller provides adequate bulk circulation."
            )

        for insight in insights:

            st.markdown(
                f"""
                <div class="reactor-card">
                    {insight}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        ⚠️ Engineering Tool — Results are intended for preliminary
        engineering analysis and scale-up screening.
        Final equipment design must be verified against validated
        correlations, vendor data, process requirements and applicable
        engineering standards.
        <br><br>
        Reactor Scale-Up Engineering Studio
    </div>
    """,
    unsafe_allow_html=True,
)
