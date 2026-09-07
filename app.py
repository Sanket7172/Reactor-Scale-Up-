import streamlit as st
import math

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="R",
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
        "Anchor": {"Np": 0.5, "Nq": 0.50},
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
# CSS
# ============================================================

st.markdown(
    """
<style>

/* ---------- GLOBAL ---------- */

.stApp {
    background-color: #f4f7fb;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

h1, h2, h3, h4 {
    font-family: Arial, Helvetica, sans-serif;
    color: #111827;
}

p, label, div, span {
    font-family: Arial, Helvetica, sans-serif;
}


/* ---------- SIDEBAR ---------- */

section[data-testid="stSidebar"] {
    background-color: #111827;
}

section[data-testid="stSidebar"] > div {
    background-color: #111827;
}

section[data-testid="stSidebar"] * {
    color: #f9fafb;
}

.sidebar-brand {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 24px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 3px;
}

.sidebar-description {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 12px;
    color: #cbd5e1;
    line-height: 1.5;
    margin-bottom: 22px;
}


/* ---------- HERO ---------- */

.hero-box {
    background-color: #172554;
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 22px;
    border: 1px solid #1e40af;
}

.hero-title {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 31px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 8px;
}

.hero-text {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 15px;
    color: #dbeafe;
    line-height: 1.6;
}

.system-ready {
    display: inline-block;
    margin-top: 15px;
    padding: 6px 13px;
    border-radius: 20px;
    background-color: #064e3b;
    color: #d1fae5;
    border: 1px solid #10b981;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11px;
    font-weight: 700;
}


/* ---------- KPI CARDS ---------- */

.kpi {
    background-color: #ffffff;
    border-radius: 16px;
    padding: 18px;
    min-height: 112px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
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

.kpi-label {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.kpi-value {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 26px;
    font-weight: 800;
    color: #111827;
    margin-top: 7px;
}


/* ---------- CARDS ---------- */

.card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
}

.card-title {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 18px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 12px;
}

.section-title {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 21px;
    font-weight: 800;
    color: #111827;
    margin-top: 18px;
    margin-bottom: 15px;
}


/* ---------- STATUS ---------- */

.status-pass {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    background-color: #dcfce7;
    color: #166534;
    font-weight: 700;
    font-size: 12px;
}

.status-review {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    background-color: #fef3c7;
    color: #92400e;
    font-weight: 700;
    font-size: 12px;
}

.status-fail {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    background-color: #fee2e2;
    color: #991b1b;
    font-weight: 700;
    font-size: 12px;
}


/* ---------- BUTTON ---------- */

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
}


/* ---------- FOOTER ---------- */

.footer {
    background-color: #111827;
    color: #cbd5e1;
    padding: 18px;
    border-radius: 14px;
    text-align: center;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11px;
    margin-top: 30px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = {}

if "calculated" not in st.session_state:
    st.session_state.calculated = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            REACTOR STUDIO
        </div>

        <div class="sidebar-description">
            Process Engineering<br>
            Mixing & Scale-Up Analysis
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Project")

    project_name = st.text_input(
        "Project Name",
        "Reactor Scale-Up Study",
    )

    prepared_by = st.text_input(
        "Prepared By",
        "Process Engineering",
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

    st.markdown("### Engineering Focus")

    engineering_focus = st.multiselect(
        "Select Parameters",
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

    st.caption("Reactor Scale-Up Engineering Studio")
    st.caption("Preliminary engineering analysis tool")


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero-box">

        <div class="hero-title">
            REACTOR SCALE-UP ENGINEERING STUDIO
        </div>

        <div class="hero-text">
            Professional process engineering dashboard for reactor
            geometry, agitation, power, mixing and scale-up analysis.
        </div>

        <div class="system-ready">
            SYSTEM READY
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PROJECT SUMMARY
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("PROJECT", project_name)

with c2:
    st.metric("PROCESS", process_type)

with c3:
    st.metric("STUDY MODE", study_mode)

with c4:
    st.metric("SCALE-UP BASIS", scaleup_basis)


# ============================================================
# TABS
# ============================================================

(
    dashboard_tab,
    setup_tab,
    performance_tab,
    scaleup_tab,
    validation_tab,
    reactor3d_tab,
    insights_tab,
) = st.tabs(
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
# REACTOR SETUP
# ============================================================

with setup_tab:

    st.markdown(
        '<div class="section-title">Reactor & Process Configuration</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    # --------------------------------------------------------
    # PROCESS CONDITIONS
    # --------------------------------------------------------

    with left:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">
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
    # VESSEL GEOMETRY
    # --------------------------------------------------------

    with right:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">
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
    # AGITATOR
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Agitation System</div>',
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns(3)

    with a1:

        agitator = st.selectbox(
            "Agitator Type",
            list(AGITATORS.keys()),
        )

    with a2:

        rpm = st.number_input(
            "Agitator Speed (RPM)",
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

    b1, b2, b3 = st.columns(3)

    with b1:

        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
        )

    with b2:

        number_baffles = st.number_input(
            "Number of Baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
        )

    with b3:

        impeller_clearance = st.number_input(
            "Impeller Clearance (m)",
            min_value=0.01,
            value=0.25,
            step=0.01,
        )

    st.markdown("")

    calculate_button = st.button(
        "CALCULATE REACTOR PERFORMANCE",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# FALLBACK ENGINEERING CALCULATION
# ============================================================

def fallback_calculation():

    # --------------------------------------------------------
    # UNIT CONVERSION
    # --------------------------------------------------------

    rho = density

    # mPa.s -> Pa.s
    mu = viscosity_mpas / 1000.0

    # RPM -> revolutions/second
    N = rpm / 60.0

    D = impeller_diameter

    # mN/m -> N/m
    sigma = surface_tension_mnm / 1000.0

    if rho <= 0:
        rho = 1000.0

    if mu <= 0:
        mu = 0.001

    if N <= 0:
        N = 0.001

    # --------------------------------------------------------
    # AGITATOR DATA
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
    # P = W
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
    # power_w / volume = W/m3
    #
    # Convert W/m3 -> kW/m3
    # --------------------------------------------------------

    if volume_m3 > 0:

        pv_w_m3 = power_w / volume_m3

    else:

        pv_w_m3 = 0.0

    pv_kw_m3 = pv_w_m3 / 1000.0

    # --------------------------------------------------------
    # TIP SPEED
    #
    # Utip = pi x D x N
    # --------------------------------------------------------

    tip_speed = math.pi * D * N

    # --------------------------------------------------------
    # REYNOLDS NUMBER
    #
    # Re = rho x N x D² / mu
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
    #
    # Q = Nq x N x D³
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
    # VESSEL GEOMETRY
    # --------------------------------------------------------

    vessel_cross_section = (
        math.pi
        * tank_diameter**2
        / 4.0
    )

    vessel_straight_volume = (
        vessel_cross_section
        * straight_height
    )

    if vessel_cross_section > 0:

        liquid_height = (
            volume_m3
            / vessel_cross_section
        )

    else:

        liquid_height = 0.0

    if vessel_straight_volume > 0:

        fill_percent = (
            volume_m3
            / vessel_straight_volume
            * 100.0
        )

    else:

        fill_percent = 0.0

    # --------------------------------------------------------
    # GEOMETRIC RATIOS
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

        "tank_volume": vessel_straight_volume,

        "np": Np,
        "nq": Nq,

        "d_t": d_t,
        "h_t": h_t,
        "c_t": c_t,

        "mixing_regime": mixing_regime,
        "flow_pattern": flow_pattern,

        "surface_tension": sigma,
    }


# ============================================================
# CALCULATE
# ============================================================

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

    st.success("Calculation completed.")


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
# P/V HELPER
# ============================================================

def get_pv_kw_m3():

    # Prefer an already calculated kW/m3 value.

    value = get_result(
        [
            "power_volume_kw_m3",
            "pv_kw_m3",
        ],
        None,
    )

    if value is not None:

        return float(value)

    # Otherwise assume power_volume is W/m3
    # and convert it.

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
# DASHBOARD
# ============================================================

with dashboard_tab:

    st.markdown(
        '<div class="section-title">Engineering Dashboard</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info(
            "Go to Reactor Setup, enter the process and equipment parameters, "
            "then click CALCULATE REACTOR PERFORMANCE."
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

        fill_percent = get_result(
            [
                "fill_percent",
                "fill_percentage",
            ],
            0.0,
        )

        liquid_height = get_result(
            [
                "liquid_height",
                "liquid_height_m",
            ],
            0.0,
        )

        qv = get_result(
            [
                "qv",
            ],
            0.0,
        )

        turnover = get_result(
            [
                "turnover_time",
                "turnover_time_min",
            ],
            0.0,
        )

        # ----------------------------------------------------
        # KPI ROW
        # ----------------------------------------------------

        k1, k2, k3, k4 = st.columns(4)

        with k1:

            st.markdown(
                f"""
                <div class="kpi kpi-blue">
                    <div class="kpi-label">
                        Agitator Power
                    </div>

                    <div class="kpi-value">
                        {power_kw:.2f} kW
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k2:

            st.markdown(
                f"""
                <div class="kpi kpi-purple">
                    <div class="kpi-label">
                        Power / Volume
                    </div>

                    <div class="kpi-value">
                        {pv_kw_m3:.4f} kW/m³
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k3:

            st.markdown(
                f"""
                <div class="kpi kpi-green">
                    <div class="kpi-label">
                        Tip Speed
                    </div>

                    <div class="kpi-value">
                        {tip_speed:.2f} m/s
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k4:

            st.markdown(
                f"""
                <div class="kpi kpi-orange">
                    <div class="kpi-label">
                        Reynolds Number
                    </div>

                    <div class="kpi-value">
                        {reynolds:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("")

        # ----------------------------------------------------
        # SECOND KPI ROW
        # ----------------------------------------------------

        k5, k6, k7, k8 = st.columns(4)

        with k5:
            st.metric(
                "Liquid Height",
                f"{liquid_height:.2f} m",
            )

        with k6:
            st.metric(
                "Fill %",
                f"{fill_percent:.1f} %",
            )

        with k7:
            st.metric(
                "Q/V",
                f"{qv:.2f} 1/h",
            )

        with k8:
            st.metric(
                "Turnover Time",
                f"{turnover:.2f} min",
            )

        # ----------------------------------------------------
        # REACTOR SUMMARY
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Reactor Overview</div>',
            unsafe_allow_html=True,
        )

        r1, r2 = st.columns(2)

        with r1:

            st.markdown(
                f"""
                <div class="card">

                    <div class="card-title">
                        Vessel Configuration
                    </div>

                    <b>Working Volume:</b>
                    {volume_m3:.2f} m³
                    <br><br>

                    <b>Tank Diameter:</b>
                    {tank_diameter:.2f} m
                    <br><br>

                    <b>Straight Height:</b>
                    {straight_height:.2f} m
                    <br><br>

                    <b>Liquid Height:</b>
                    {liquid_height:.2f} m
                    <br><br>

                    <b>Fill:</b>
                    {fill_percent:.1f} %

                </div>
                """,
                unsafe_allow_html=True,
            )

        with r2:

            flow_pattern = results.get(
                "flow_pattern",
                "Not Available",
            )

            mixing_regime = results.get(
                "mixing_regime",
                "Not Available",
            )

            st.markdown(
                f"""
                <div class="card">

                    <div class="card-title">
                        Agitation Configuration
                    </div>

                    <b>Agitator:</b>
                    {agitator}
                    <br><br>

                    <b>Speed:</b>
                    {rpm:.1f} RPM
                    <br><br>

                    <b>Impeller Diameter:</b>
                    {impeller_diameter:.2f} m
                    <br><br>

                    <b>Impellers:</b>
                    {number_impellers}
                    <br><br>

                    <b>Flow Pattern:</b>
                    {flow_pattern}
                    <br><br>

                    <b>Mixing Regime:</b>
                    {mixing_regime}

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# PERFORMANCE
# ============================================================

with performance_tab:

    st.markdown(
        '<div class="section-title">Mixing Performance</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info("Run the reactor calculation first.")

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
                "Reynolds Number",
                f"{get_result(['reynolds_number', 'reynolds']):,.0f}",
            )

        with p3:

            st.metric(
                "Froude Number",
                f"{get_result(['froude_number', 'froude']):.4f}",
            )

            st.metric(
                "Pumping Rate",
                f"{get_result(['pumping_capacity', 'pumping_rate']):.2f} m³/h",
            )

        st.markdown(
            '<div class="section-title">Geometry Ratios</div>',
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

        st.markdown(
            '<div class="section-title">Mixing Regime</div>',
            unsafe_allow_html=True,
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
                "LAMINAR: Reynolds number is below 10."
            )

        elif re_value < 10000:

            st.warning(
                "TRANSITIONAL: Reynolds number is between 10 and 10,000."
            )

        else:

            st.success(
                "TURBULENT: Reynolds number is above 10,000."
            )


# ============================================================
# SCALE-UP
# ============================================================

with scaleup_tab:

    st.markdown(
        '<div class="section-title">Scale-Up Analysis</div>',
        unsafe_allow_html=True,
    )

    if study_mode == "Single Reactor":

        st.info(
            "Select a multi-scale study mode from the sidebar "
            "to perform Lab/Pilot/Commercial comparison."
        )

    else:

        st.markdown(
            f"""
            <div class="card">

                <div class="card-title">
                    Selected Scale-Up Basis
                </div>

                <div style="
                    font-size:25px;
                    font-weight:800;
                    color:#1d4ed8;
                    margin-bottom:10px;
                ">
                    {scaleup_basis}
                </div>

                <div>
                    Process type: <b>{process_type}</b>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if scaleup_basis == "Constant P/V":

            st.success(
                "Constant P/V basis selected. "
                "Maintain volumetric power input between scales."
            )

        elif scaleup_basis == "Constant Tip Speed":

            st.info(
                "Constant Tip Speed basis selected. "
                "Maintain impeller peripheral velocity."
            )

        elif scaleup_basis == "Constant RPM":

            st.warning(
                "Constant RPM selected. Check the resulting P/V, "
                "tip speed and pumping capacity carefully."
            )

        elif scaleup_basis == "Constant Froude Number":

            st.info(
                "Constant Froude Number basis selected."
            )

        elif scaleup_basis == "Constant Reynolds Number":

            st.info(
                "Constant Reynolds Number basis selected."
            )

        elif scaleup_basis == "Constant N/Njs":

            st.info(
                "Constant N/Njs basis selected for suspension-related analysis."
            )

        elif scaleup_basis == "Constant KLa":

            st.info(
                "Constant KLa basis selected for gas-liquid applications."
            )

        else:

            st.info(
                "Selected scale-up basis: "
                + scaleup_basis
            )


# ============================================================
# VALIDATION
# ============================================================

with validation_tab:

    st.markdown(
        '<div class="section-title">Engineering Validation</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info("Run the reactor calculation first.")

    else:

        validation_messages = []

        # ----------------------------------------------------
        # DIAMETER CHECK
        # ----------------------------------------------------

        if tank_diameter <= 0:

            validation_messages.append(
                (
                    "FAIL",
                    "Tank diameter must be greater than zero.",
                )
            )

        # ----------------------------------------------------
        # IMPELLER DIAMETER CHECK
        # ----------------------------------------------------

        if impeller_diameter >= tank_diameter:

            validation_messages.append(
                (
                    "FAIL",
                    "Impeller diameter is greater than or equal to tank diameter.",
                )
            )

        # ----------------------------------------------------
        # FILL CHECK
        # ----------------------------------------------------

        if fill_percent > 100:

            validation_messages.append(
                (
                    "FAIL",
                    "Working volume exceeds the calculated straight-side vessel volume.",
                )
            )

        # ----------------------------------------------------
        # BAFFLE CHECK
        # ----------------------------------------------------

        if (
            number_baffles < 4
            and process_type != "High-Viscosity"
        ):

            validation_messages.append(
                (
                    "REVIEW",
                    "Less than four baffles selected. Check vortexing and tangential flow.",
                )
            )

        # ----------------------------------------------------
        # RPM CHECK
        # ----------------------------------------------------

        if rpm <= 0:

            validation_messages.append(
                (
                    "FAIL",
                    "Agitator speed must be greater than zero.",
                )
            )

        # ----------------------------------------------------
        # D/T CHECK
        # ----------------------------------------------------

        d_t_value = get_result(
            ["d_t"],
            0,
        )

        if d_t_value < 0.20:

            validation_messages.append(
                (
                    "REVIEW",
                    "D/T is relatively low. Verify bulk circulation and mixing coverage.",
                )
            )

        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------

        if not validation_messages:

            validation_messages.append(
                (
                    "PASS",
                    "Basic dashboard engineering checks passed.",
                )
            )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # VALIDATION TABLE
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Input Validation Summary</div>',
            unsafe_allow_html=True,
        )

        validation_table = {
            "Parameter": [
                "Working Volume",
                "Tank Diameter",
                "Straight Height",
                "Impeller Diameter",
                "RPM",
                "Number of Impellers",
                "Number of Baffles",
                "Fill %",
                "D/T",
            ],
            "Value": [
                f"{volume_m3:.2f} m³",
                f"{tank_diameter:.2f} m",
                f"{straight_height:.2f} m",
                f"{impeller_diameter:.2f} m",
                f"{rpm:.1f}",
                f"{number_impellers}",
                f"{number_baffles}",
                f"{fill_percent:.1f} %",
                f"{d_t_value:.3f}",
            ],
        }

        st.dataframe(
            validation_table,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 3D REACTOR
# ============================================================

with reactor3d_tab:

    st.markdown(
        '<div class="section-title">3D Reactor Visualization</div>',
        unsafe_allow_html=True,
    )

    if create_reactor_animation is None:

        st.info(
            "The 3D visualization module is not available. "
            "Add visualization/reactor_3d.py to activate this section."
        )

    elif not st.session_state.calculated:

        st.info(
            "Run the reactor calculation first."
        )

    else:

        try:

            try:

                liquid_height_for_3d = get_result(
                    [
                        "liquid_height",
                        "liquid_height_m",
                    ],
                    volume_m3,
                )

                fig = create_reactor_animation(
                    D=tank_diameter,
                    straight_height=straight_height,
                    bottom_type=bottom_type,
                    top_type=top_type,
                    liquid_height=liquid_height_for_3d,
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
                    "The 3D module is available, but its function "
                    "parameters do not match this app version."
                )

        except Exception as error:

            st.error(
                "3D visualization error: "
                + str(error)
            )


# ============================================================
# INSIGHTS
# ============================================================

with insights_tab:

    st.markdown(
        '<div class="section-title">Engineering Insights</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.calculated:

        st.info(
            "Run the calculation to generate engineering insights."
        )

    else:

        pv_value = get_pv_kw_m3()

        re_value = get_result(
            [
                "reynolds_number",
                "reynolds",
            ],
            0,
        )

        tip_value = get_result(
            [
                "tip_speed",
            ],
            0,
        )

        qv_value = get_result(
            [
                "qv",
            ],
            0,
        )

        d_t_value = get_result(
            [
                "d_t",
            ],
            0,
        )

        insights = []

        # ----------------------------------------------------
        # P/V
        # ----------------------------------------------------

        insights.append(
            f"P/V is calculated as {pv_value:.4f} kW/m³. "
            "Compare this value against the process-specific mixing requirement."
        )

        # ----------------------------------------------------
        # REYNOLDS
        # ----------------------------------------------------

        if re_value >= 10000:

            insights.append(
                "The calculated Reynolds number indicates turbulent mixing."
            )

        elif re_value >= 10:

            insights.append(
                "The reactor is operating in the transitional mixing regime. "
                "Scale-up correlations should be applied carefully."
            )

        else:

            insights.append(
                "The reactor is operating in the laminar regime. "
                "Viscosity and impeller geometry will strongly influence mixing."
            )

        # ----------------------------------------------------
        # TIP SPEED
        # ----------------------------------------------------

        if tip_value > 10:

            insights.append(
                "Tip speed is relatively high. Review shear sensitivity, "
                "mechanical limitations and potential vortexing."
            )

        else:

            insights.append(
                f"Calculated tip speed is {tip_value:.2f} m/s."
            )

        # ----------------------------------------------------
        # Q/V
        # ----------------------------------------------------

        if qv_value > 0:

            insights.append(
                f"Estimated circulation is {qv_value:.2f} vessel volumes/hour."
            )

        # ----------------------------------------------------
        # D/T
        # ----------------------------------------------------

        if d_t_value < 0.20:

            insights.append(
                "D/T is relatively low. Verify that adequate bulk circulation "
                "is achieved throughout the vessel."
            )

        else:

            insights.append(
                f"Impeller-to-tank ratio D/T is {d_t_value:.3f}."
            )

        # ----------------------------------------------------
        # BAFFLES
        # ----------------------------------------------------

        if number_baffles < 4:

            insights.append(
                "Baffle arrangement should be reviewed for vortex suppression."
            )

        else:

            insights.append(
                f"{number_baffles} baffles are specified."
            )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        for index, insight in enumerate(insights, start=1):

            st.markdown(
                f"""
                <div class="card">

                    <div class="card-title">
                        Engineering Insight {index}
                    </div>

                    <div style="
                        font-size:14px;
                        color:#374151;
                        line-height:1.6;
                    ">
                        {insight}
                    </div>

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
        Reactor Scale-Up Engineering Studio
        <br>
        Preliminary engineering analysis tool.
        Final equipment design should be verified using validated
        correlations, vendor data, process requirements and applicable
        engineering standards.
    </div>
    """,
    unsafe_allow_html=True,
)
