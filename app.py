import streamlit as st
import math


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up Studio",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SAFE IMPORTS
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
        "Pitched Blade Turbine": {"Np": 1.30, "Nq": 0.75},
        "Hydrofoil": {"Np": 0.35, "Nq": 0.65},
        "Anchor": {"Np": 0.50, "Nq": 0.50},
    }

try:
    from libraries.reactor_geometry import REACTOR_HEADS
except Exception:
    REACTOR_HEADS = {
        "2:1 Ellipsoidal": {},
        "Torispherical": {},
        "Flat Bottom": {},
    }

try:
    from visualization.reactor_3d import create_reactor_animation
except Exception:
    create_reactor_animation = None


# ============================================================
# MODERN STREAMLIT STYLE
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   GLOBAL
   ========================================================== */

.stApp {
    background: #f4f7fb;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}


/* ==========================================================
   SIDEBAR
   ========================================================== */

section[data-testid="stSidebar"] {
    background: #0b1220;
}

section[data-testid="stSidebar"] > div {
    background: #0b1220;
}

section[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

.sidebar-brand {
    font-size: 24px;
    font-weight: 800;
    color: white;
    letter-spacing: 0.5px;
    margin-bottom: 3px;
}

.sidebar-subtitle {
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.5;
    margin-bottom: 20px;
}

.sidebar-section {
    font-size: 11px;
    font-weight: 800;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 18px;
    margin-bottom: 8px;
}


/* ==========================================================
   MAIN HEADER
   ========================================================== */

.main-header {
    background: linear-gradient(
        135deg,
        #0f172a 0%,
        #172554 55%,
        #075985 100%
    );

    border-radius: 18px;
    padding: 26px 30px;
    margin-bottom: 20px;
    border: 1px solid #1e3a8a;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15);
}

.main-header-title {
    color: white;
    font-size: 30px;
    font-weight: 800;
    letter-spacing: 0.2px;
}

.main-header-subtitle {
    color: #bfdbfe;
    font-size: 14px;
    margin-top: 7px;
}

.header-status {
    color: #86efac;
    font-size: 11px;
    font-weight: 800;
    margin-top: 14px;
    letter-spacing: 0.5px;
}


/* ==========================================================
   KPI
   ========================================================== */

.kpi-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
    padding: 17px;
    min-height: 108px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
}

.kpi-blue {
    border-left: 5px solid #2563eb;
}

.kpi-cyan {
    border-left: 5px solid #0891b2;
}

.kpi-green {
    border-left: 5px solid #059669;
}

.kpi-orange {
    border-left: 5px solid #ea580c;
}

.kpi-purple {
    border-left: 5px solid #7c3aed;
}

.kpi-red {
    border-left: 5px solid #dc2626;
}

.kpi-label {
    color: #64748b;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

.kpi-value {
    color: #0f172a;
    font-size: 25px;
    font-weight: 800;
    margin-top: 8px;
}

.kpi-unit {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
}


/* ==========================================================
   SECTION
   ========================================================== */

.section-heading {
    color: #0f172a;
    font-size: 20px;
    font-weight: 800;
    margin-top: 18px;
    margin-bottom: 12px;
}


/* ==========================================================
   ENGINEERING CARD
   ========================================================== */

.engineering-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 3px 14px rgba(15, 23, 42, 0.04);
}

.card-heading {
    color: #0f172a;
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 12px;
}


/* ==========================================================
   STATUS
   ========================================================== */

.status-pass {
    color: #047857;
    background: #d1fae5;
    border: 1px solid #a7f3d0;
    border-radius: 20px;
    padding: 5px 11px;
    font-size: 11px;
    font-weight: 800;
}

.status-review {
    color: #a16207;
    background: #fef3c7;
    border: 1px solid #fde68a;
    border-radius: 20px;
    padding: 5px 11px;
    font-size: 11px;
    font-weight: 800;
}

.status-fail {
    color: #b91c1c;
    background: #fee2e2;
    border: 1px solid #fecaca;
    border-radius: 20px;
    padding: 5px 11px;
    font-size: 11px;
    font-weight: 800;
}


/* ==========================================================
   BUTTON
   ========================================================== */

.stButton > button {
    border-radius: 10px;
    font-weight: 800;
    min-height: 42px;
}


/* ==========================================================
   FOOTER
   ========================================================== */

.engineering-footer {
    background: #0f172a;
    color: #94a3b8;
    border-radius: 14px;
    padding: 16px;
    text-align: center;
    font-size: 10px;
    margin-top: 30px;
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
        '<div class="sidebar-brand">REACTOR STUDIO</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-subtitle">
        Process Engineering<br>
        Mixing | Agitation | Scale-Up
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section">Project</div>',
        unsafe_allow_html=True,
    )

    project_name = st.text_input(
        "Project",
        value="Reactor Scale-Up Study",
        label_visibility="collapsed",
    )

    prepared_by = st.text_input(
        "Prepared By",
        value="Process Engineering",
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="sidebar-section">Study Configuration</div>',
        unsafe_allow_html=True,
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
            "Solid Suspension",
            "Gas Dispersion",
            "Heat Transfer",
            "Scale-Up",
            "Geometry",
        ],
        default=[
            "Power / Volume",
            "Tip Speed",
            "Mixing",
        ],
    )

    st.divider()

    st.caption("Engineering Scale-Up Tool")
    st.caption("Preliminary design and analysis")


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">

        <div class="main-header-title">
            REACTOR SCALE-UP ENGINEERING STUDIO
        </div>

        <div class="main-header-subtitle">
            Mixing, agitation, reactor geometry and scale-up analysis
        </div>

        <div class="header-status">
            SYSTEM READY
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PROJECT STATUS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("PROJECT", project_name)

with c2:
    st.metric("PROCESS", process_type)

with c3:
    st.metric("STUDY", study_mode)

with c4:
    st.metric("BASIS", scaleup_basis)


# ============================================================
# TABS
# ============================================================

tab_dashboard, tab_setup, tab_performance, tab_scaleup, tab_validation, tab_3d, tab_insights = st.tabs(
    [
        "Dashboard",
        "Reactor Setup",
        "Performance",
        "Scale-Up",
        "Validation",
        "3D Reactor",
        "Insights",
    ]
)


# ============================================================
# REACTOR SETUP TAB
# ============================================================

with tab_setup:

    st.markdown(
        '<div class="section-heading">Reactor & Process Configuration</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    with col1:

        st.markdown(
            """
            <div class="engineering-card">
                <div class="card-heading">
                    Process Conditions
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        volume_m3 = st.number_input(
            "Working Volume (m³)",
            min_value=0.01,
            value=5.00,
            step=0.10,
        )

        density = st.number_input(
            "Density (kg/m³)",
            min_value=1.0,
            value=1000.0,
            step=10.0,
        )

        viscosity_mpas = st.number_input(
            "Viscosity (mPa·s)",
            min_value=0.01,
            value=1.00,
            step=0.10,
        )

        surface_tension_mnm = st.number_input(
            "Surface Tension (mN/m)",
            min_value=0.01,
            value=30.0,
            step=1.0,
        )

    # --------------------------------------------------------
    # VESSEL
    # --------------------------------------------------------

    with col2:

        st.markdown(
            """
            <div class="engineering-card">
                <div class="card-heading">
                    Vessel Geometry
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tank_diameter = st.number_input(
            "Tank Diameter (m)",
            min_value=0.10,
            value=2.00,
            step=0.05,
        )

        straight_height = st.number_input(
            "Straight Side Height (m)",
            min_value=0.10,
            value=2.50,
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

    # --------------------------------------------------------
    # AGITATION
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">Agitation System</div>',
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns(3)

    with a1:

        agitator = st.selectbox(
            "Agitator",
            list(AGITATORS.keys()),
        )

    with a2:

        rpm = st.number_input(
            "Speed (RPM)",
            min_value=0.1,
            value=120.0,
            step=1.0,
        )

    with a3:

        impeller_diameter = st.number_input(
            "Impeller Diameter (m)",
            min_value=0.05,
            value=0.70,
            step=0.01,
        )

    a4, a5, a6 = st.columns(3)

    with a4:

        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
        )

    with a5:

        number_baffles = st.number_input(
            "Number of Baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
        )

    with a6:

        impeller_clearance = st.number_input(
            "Impeller Clearance (m)",
            min_value=0.01,
            value=0.25,
            step=0.01,
        )

    st.write("")

    calculate_button = st.button(
        "CALCULATE PERFORMANCE",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# FALLBACK ENGINEERING CALCULATION
# ============================================================

def fallback_calculation():

    # --------------------------------------------------------
    # UNIT CONVERSIONS
    # --------------------------------------------------------

    rho = density

    # mPa.s -> Pa.s

    mu = viscosity_mpas / 1000.0

    # RPM -> s^-1

    N = rpm / 60.0

    D = impeller_diameter

    if rho <= 0:
        rho = 1000.0

    if mu <= 0:
        mu = 0.001

    if N <= 0:
        N = 0.001

    # --------------------------------------------------------
    # AGITATOR CONSTANTS
    # --------------------------------------------------------

    agitator_data = AGITATORS.get(
        agitator,
        {},
    )

    try:
        Np = float(
            agitator_data.get(
                "Np",
                1.0,
            )
        )
    except Exception:
        Np = 1.0

    try:
        Nq = float(
            agitator_data.get(
                "Nq",
                0.7,
            )
        )
    except Exception:
        Nq = 0.7

    # --------------------------------------------------------
    # POWER
    #
    # P = Np x rho x N^3 x D^5
    #
    # Result = W
    # --------------------------------------------------------

    power_w = (
        Np
        * rho
        * N**3
        * D**5
        * number_impellers
    )

    power_kw = power_w / 1000.0

    # --------------------------------------------------------
    # P/V
    #
    # First calculate W/m3
    # Then convert to kW/m3
    # --------------------------------------------------------

    if volume_m3 > 0:

        pv_w_m3 = power_w / volume_m3

    else:

        pv_w_m3 = 0.0

    pv_kw_m3 = pv_w_m3 / 1000.0

    # --------------------------------------------------------
    # TIP SPEED
    # --------------------------------------------------------

    tip_speed = math.pi * D * N

    # --------------------------------------------------------
    # REYNOLDS NUMBER
    # --------------------------------------------------------

    reynolds = (
        rho
        * N
        * D**2
        / mu
    )

    # --------------------------------------------------------
    # FROUDE NUMBER
    # --------------------------------------------------------

    froude = (
        N**2
        * D
        / 9.81
    )

    # --------------------------------------------------------
    # PUMPING
    # --------------------------------------------------------

    pumping_m3_s = (
        Nq
        * N
        * D**3
        * number_impellers
    )

    pumping_m3_h = pumping_m3_s * 3600.0

    # --------------------------------------------------------
    # Q/V
    # --------------------------------------------------------

    if volume_m3 > 0:

        qv = pumping_m3_h / volume_m3

    else:

        qv = 0.0

    # --------------------------------------------------------
    # TURNOVER TIME
    # --------------------------------------------------------

    if qv > 0:

        turnover_time_min = 60.0 / qv

    else:

        turnover_time_min = 0.0

    # --------------------------------------------------------
    # VESSEL
    # --------------------------------------------------------

    cross_section = (
        math.pi
        * tank_diameter**2
        / 4.0
    )

    straight_volume = (
        cross_section
        * straight_height
    )

    if cross_section > 0:

        liquid_height = (
            volume_m3
            / cross_section
        )

    else:

        liquid_height = 0.0

    if straight_volume > 0:

        fill_percent = (
            volume_m3
            / straight_volume
            * 100.0
        )

    else:

        fill_percent = 0.0

    # --------------------------------------------------------
    # RATIOS
    # --------------------------------------------------------

    if tank_diameter > 0:

        d_t = (
            impeller_diameter
            / tank_diameter
        )

        h_t = (
            liquid_height
            / tank_diameter
        )

        c_t = (
            impeller_clearance
            / tank_diameter
        )

    else:

        d_t = 0.0
        h_t = 0.0
        c_t = 0.0

    # --------------------------------------------------------
    # MIXING REGIME
    # --------------------------------------------------------

    if reynolds < 10:

        mixing_regime = "Laminar"

    elif reynolds < 10000:

        mixing_regime = "Transitional"

    else:

        mixing_regime = "Turbulent"

    # --------------------------------------------------------
    # FLOW PATTERN
    # --------------------------------------------------------

    if Nq >= 0.65:

        flow_pattern = "Axial"

    else:

        flow_pattern = "Radial"

    return {
        "power_w": power_w,
        "power_kw": power_kw,

        "power_volume": pv_w_m3,
        "power_volume_w_m3": pv_w_m3,
        "power_volume_kw_m3": pv_kw_m3,

        "tip_speed": tip_speed,

        "reynolds": reynolds,
        "reynolds_number": reynolds,

        "froude": froude,
        "froude_number": froude,

        "pumping_capacity": pumping_m3_h,
        "pumping_rate": pumping_m3_h,

        "qv": qv,

        "turnover_time": turnover_time_min,

        "liquid_height": liquid_height,

        "fill_percent": fill_percent,

        "tank_volume": straight_volume,

        "np": Np,
        "nq": Nq,

        "d_t": d_t,
        "h_t": h_t,
        "c_t": c_t,

        "mixing_regime": mixing_regime,
        "flow_pattern": flow_pattern,
    }


# ============================================================
# CALCULATION BUTTON
# ============================================================

if calculate_button:

    with st.spinner("Calculating reactor performance..."):

        try:

            if calculate_reactor is not None:

                try:

                    results = calculate_reactor(
                        volume_m3=volume_m3,
                        tank_diameter_m=tank_diameter,
                        liquid_height_m=0.0,
                        density_kg_m3=density,
                        viscosity_pa_s=viscosity_mpas / 1000.0,
                        surface_tension_n_m=surface_tension_mnm / 1000.0,
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

    st.success("Reactor performance calculated successfully.")


# ============================================================
# RESULT HELPER
# ============================================================

results = st.session_state.results


def get_result(keys, default=0.0):

    if not results:
        return default

    for key in keys:

        if key in results:

            try:
                return float(results[key])
            except Exception:
                return results[key]

    return default


# ============================================================
# P/V CONVERSION
# ============================================================

def get_pv_kw_m3():

    # Prefer explicit kW/m3 result.

    value = get_result(
        [
            "power_volume_kw_m3",
            "pv_kw_m3",
        ],
        None,
    )

    if value is not None:

        return float(value)

    # Otherwise convert W/m3 to kW/m3.

    value = get_result(
        [
            "power_volume_w_m3",
            "power_volume",
            "pv_w_m3",
        ],
        0.0,
    )

    return float(value) / 1000.0


# ============================================================
# DASHBOARD TAB
# ============================================================

with tab_dashboard:

    st.markdown(
        '<div class="section-heading">Engineering Dashboard</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info(
            "Configure the reactor in the Reactor Setup tab and "
            "click CALCULATE PERFORMANCE."
        )

    else:

        power_kw = get_result(
            [
                "power_kw",
                "power",
            ],
            0.0,
        )

        pv_kw_m3 = get_pv_kw_m3()

        tip_speed = get_result(
            [
                "tip_speed",
                "tip_speed_m_s",
            ],
            0.0,
        )

        reynolds = get_result(
            [
                "reynolds_number",
                "reynolds",
            ],
            0.0,
        )

        k1, k2, k3, k4 = st.columns(4)

        with k1:

            st.markdown(
                f"""
                <div class="kpi-card kpi-blue">

                    <div class="kpi-label">
                        Agitator Power
                    </div>

                    <div class="kpi-value">
                        {power_kw:.2f}
                    </div>

                    <div class="kpi-unit">
                        kW
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with k2:

            st.markdown(
                f"""
                <div class="kpi-card kpi-purple">

                    <div class="kpi-label">
                        Power / Volume
                    </div>

                    <div class="kpi-value">
                        {pv_kw_m3:.4f}
                    </div>

                    <div class="kpi-unit">
                        kW/m³
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with k3:

            st.markdown(
                f"""
                <div class="kpi-card kpi-green">

                    <div class="kpi-label">
                        Tip Speed
                    </div>

                    <div class="kpi-value">
                        {tip_speed:.2f}
                    </div>

                    <div class="kpi-unit">
                        m/s
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with k4:

            st.markdown(
                f"""
                <div class="kpi-card kpi-orange">

                    <div class="kpi-label">
                        Reynolds Number
                    </div>

                    <div class="kpi-value">
                        {reynolds:,.0f}
                    </div>

                    <div class="kpi-unit">
                        dimensionless
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        k5, k6, k7, k8 = st.columns(4)

        with k5:

            st.metric(
                "Liquid Height",
                f"{get_result(['liquid_height']):.2f} m",
            )

        with k6:

            st.metric(
                "Fill Level",
                f"{get_result(['fill_percent']):.1f} %",
            )

        with k7:

            st.metric(
                "Q/V",
                f"{get_result(['qv']):.2f} 1/h",
            )

        with k8:

            st.metric(
                "Turnover",
                f"{get_result(['turnover_time']):.2f} min",
            )

        st.markdown(
            '<div class="section-heading">Reactor Overview</div>',
            unsafe_allow_html=True,
        )

        r1, r2 = st.columns(2)

        with r1:

            st.markdown(
                f"""
                <div class="engineering-card">

                    <div class="card-heading">
                        Vessel
                    </div>

                    <b>Working Volume</b><br>
                    {volume_m3:.2f} m³

                    <br><br>

                    <b>Tank Diameter</b><br>
                    {tank_diameter:.2f} m

                    <br><br>

                    <b>Straight Height</b><br>
                    {straight_height:.2f} m

                    <br><br>

                    <b>Liquid Height</b><br>
                    {get_result(['liquid_height']):.2f} m

                </div>
                """,
                unsafe_allow_html=True,
            )

        with r2:

            flow_pattern = results.get(
                "flow_pattern",
                "Not available",
            )

            mixing_regime = results.get(
                "mixing_regime",
                "Not available",
            )

            st.markdown(
                f"""
                <div class="engineering-card">

                    <div class="card-heading">
                        Agitation
                    </div>

                    <b>Agitator</b><br>
                    {agitator}

                    <br><br>

                    <b>Speed</b><br>
                    {rpm:.1f} RPM

                    <br><br>

                    <b>Impeller Diameter</b><br>
                    {impeller_diameter:.2f} m

                    <br><br>

                    <b>Flow Pattern</b><br>
                    {flow_pattern}

                    <br><br>

                    <b>Mixing Regime</b><br>
                    {mixing_regime}

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# PERFORMANCE TAB
# ============================================================

with tab_performance:

    st.markdown(
        '<div class="section-heading">Mixing Performance</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info("Calculate the reactor first.")

    else:

        p1, p2, p3 = st.columns(3)

        with p1:

            st.metric(
                "Power",
                f"{get_result(['power_kw', 'power']):.2f} kW",
            )

            st.metric(
                "Tip Speed",
                f"{get_result(['tip_speed']):.2f} m/s",
            )

        with p2:

            st.metric(
                "P/V",
                f"{get_pv_kw_m3():.4f} kW/m³",
            )

            st.metric(
                "Reynolds",
                f"{get_result(['reynolds_number', 'reynolds']):,.0f}",
            )

        with p3:

            st.metric(
                "Froude",
                f"{get_result(['froude_number', 'froude']):.4f}",
            )

            st.metric(
                "Pumping",
                f"{get_result(['pumping_capacity', 'pumping_rate']):.2f} m³/h",
            )

        st.markdown(
            '<div class="section-heading">Geometry Ratios</div>',
            unsafe_allow_html=True,
        )

        g1, g2, g3, g4 = st.columns(4)

        with g1:
            st.metric(
                "D/T",
                f"{get_result(['d_t']):.3f}",
            )

        with g2:
            st.metric(
                "H/T",
                f"{get_result(['h_t']):.3f}",
            )

        with g3:
            st.metric(
                "C/T",
                f"{get_result(['c_t']):.3f}",
            )

        with g4:
            st.metric(
                "Impellers",
                str(number_impellers),
            )

        re_value = get_result(
            [
                "reynolds_number",
                "reynolds",
            ],
            0,
        )

        if re_value < 10:

            st.warning(
                "LAMINAR MIXING REGIME"
            )

        elif re_value < 10000:

            st.warning(
                "TRANSITIONAL MIXING REGIME"
            )

        else:

            st.success(
                "TURBULENT MIXING REGIME"
            )


# ============================================================
# SCALE-UP TAB
# ============================================================

with tab_scaleup:

    st.markdown(
        '<div class="section-heading">Scale-Up Strategy</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="engineering-card">

            <div class="card-heading">
                Selected Scale-Up Basis
            </div>

            <div style="
                font-size:22px;
                font-weight:800;
                color:#1d4ed8;
                margin-bottom:10px;
            ">
                {scaleup_basis}
            </div>

            Process:
            <b>{process_type}</b>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if study_mode == "Single Reactor":

        st.info(
            "Select Lab vs Pilot, Pilot vs Commercial, "
            "Lab vs Commercial, or Lab vs Pilot vs Commercial "
            "for multi-scale analysis."
        )

    elif scaleup_basis == "Constant P/V":

        st.success(
            "Constant P/V selected. Target scale should maintain "
            "the specified volumetric power input."
        )

    elif scaleup_basis == "Constant Tip Speed":

        st.info(
            "Constant Tip Speed selected. Target scale should maintain "
            "impeller peripheral velocity."
        )

    elif scaleup_basis == "Constant RPM":

        st.warning(
            "Constant RPM selected. Verify resulting P/V, tip speed "
            "and pumping capacity at target scale."
        )

    else:

        st.info(
            "Scale-up basis selected: "
            + scaleup_basis
        )


# ============================================================
# VALIDATION TAB
# ============================================================

with tab_validation:

    st.markdown(
        '<div class="section-heading">Engineering Validation</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info("Calculate the reactor first.")

    else:

        validation_messages = []

        if tank_diameter <= 0:

            validation_messages.append(
                (
                    "FAIL",
                    "Tank diameter must be greater than zero.",
                )
            )

        if impeller_diameter >= tank_diameter:

            validation_messages.append(
                (
                    "FAIL",
                    "Impeller diameter must be smaller than tank diameter.",
                )
            )

        if get_result(["fill_percent"]) > 100:

            validation_messages.append(
                (
                    "FAIL",
                    "Working volume exceeds calculated vessel straight-side volume.",
                )
            )

        if number_baffles < 4 and process_type != "High-Viscosity":

            validation_messages.append(
                (
                    "REVIEW",
                    "Less than four baffles selected. Check vortexing.",
                )
            )

        if rpm <= 0:

            validation_messages.append(
                (
                    "FAIL",
                    "Agitator speed must be greater than zero.",
                )
            )

        if get_result(["d_t"]) < 0.20:

            validation_messages.append(
                (
                    "REVIEW",
                    "D/T is relatively low. Verify bulk circulation.",
                )
            )

        if not validation_messages:

            validation_messages.append(
                (
                    "PASS",
                    "Basic dashboard engineering checks passed.",
                )
            )

        for status, message in validation_messages:

            if status == "PASS":

                st.success(
                    "PASS - " + message
                )

            elif status == "REVIEW":

                st.warning(
                    "REVIEW - " + message
                )

            else:

                st.error(
                    "FAIL - " + message
                )

        st.markdown(
            '<div class="section-heading">Input Summary</div>',
            unsafe_allow_html=True,
        )

        validation_table = {
            "Parameter": [
                "Working Volume",
                "Tank Diameter",
                "Straight Height",
                "Impeller Diameter",
                "RPM",
                "Impellers",
                "Baffles",
                "Fill %",
                "D/T",
            ],
            "Value": [
                f"{volume_m3:.2f} m³",
                f"{tank_diameter:.2f} m",
                f"{straight_height:.2f} m",
                f"{impeller_diameter:.2f} m",
                f"{rpm:.1f}",
                str(number_impellers),
                str(number_baffles),
                f"{get_result(['fill_percent']):.1f} %",
                f"{get_result(['d_t']):.3f}",
            ],
        }

        st.dataframe(
            validation_table,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 3D REACTOR TAB
# ============================================================

with tab_3d:

    st.markdown(
        '<div class="section-heading">3D Reactor</div>',
        unsafe_allow_html=True,
    )

    if create_reactor_animation is None:

        st.info(
            "3D visualization module is not available."
        )

    elif not st.session_state.calculated:

        st.info(
            "Calculate the reactor first."
        )

    else:

        try:

            liquid_height_3d = get_result(
                [
                    "liquid_height",
                    "liquid_height_m",
                ],
                volume_m3,
            )

            try:

                figure = create_reactor_animation(
                    D=tank_diameter,
                    straight_height=straight_height,
                    bottom_type=bottom_type,
                    top_type=top_type,
                    liquid_height=liquid_height_3d,
                    agitator=agitator,
                    impeller_diameter=impeller_diameter,
                    number_impellers=number_impellers,
                    rpm=rpm,
                    number_baffles=number_baffles,
                    vortex_depth=0.0,
                    frames_count=30,
                )

                st.plotly_chart(
                    figure,
                    use_container_width=True,
                )

            except TypeError:

                st.warning(
                    "The existing reactor_3d.py function signature "
                    "does not match this app version."
                )

        except Exception as error:

            st.error(
                "3D visualization error: "
                + str(error)
            )


# ============================================================
# INSIGHTS TAB
# ============================================================

with tab_insights:

    st.markdown(
        '<div class="section-heading">Engineering Insights</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info(
            "Calculate the reactor first."
        )

    else:

        pv = get_pv_kw_m3()

        re_value = get_result(
            [
                "reynolds_number",
                "reynolds",
            ],
            0,
        )

        tip = get_result(
            [
                "tip_speed",
            ],
            0,
        )

        qv = get_result(
            [
                "qv",
            ],
            0,
        )

        d_t = get_result(
            [
                "d_t",
            ],
            0,
        )

        st.markdown(
            f"""
            <div class="engineering-card">

                <div class="card-heading">
                    Power Density
                </div>

                Calculated P/V:
                <b>{pv:.4f} kW/m³</b>

                <br><br>

                Compare this value with the process-specific
                mixing requirement and validated scale-up basis.

            </div>
            """,
            unsafe_allow_html=True,
        )

        if re_value >= 10000:

            st.success(
                "The calculated Reynolds number indicates turbulent mixing."
            )

        elif re_value >= 10:

            st.warning(
                "The reactor is in the transitional mixing regime."
            )

        else:

            st.warning(
                "The reactor is in the laminar mixing regime."
            )

        if tip > 10:

            st.warning(
                "Tip speed is relatively high. Review shear sensitivity "
                "and mechanical limitations."
            )

        else:

            st.info(
                f"Calculated tip speed: {tip:.2f} m/s."
            )

        if qv > 0:

            st.info(
                f"Estimated circulation rate: {qv:.2f} vessel volumes/hour."
            )

        if d_t < 0.20:

            st.warning(
                f"D/T = {d_t:.3f}. Verify bulk circulation and mixing coverage."
            )

        else:

            st.success(
                f"D/T = {d_t:.3f}."
            )

        if number_baffles < 4:

            st.warning(
                "Review baffle arrangement for vortex suppression."
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="engineering-footer">

        Reactor Scale-Up Engineering Studio

        <br><br>

        Preliminary engineering analysis only.
        Final equipment design shall be verified using validated
        correlations, process data, vendor information and applicable
        engineering standards.

    </div>
    """,
    unsafe_allow_html=True,
)
