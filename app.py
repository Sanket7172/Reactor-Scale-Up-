import pandas as pd
import streamlit as st

from calculations.engine import (
    calculate_train,
    zwietering_njs,
)

from calculations.scaleup import (
    calculate_scaleup,
)

from calculations.validation import (
    validate_design,
    overall_status,
    recommendations,
)

from libraries.agitator_geometry import AGITATORS

from libraries.reactor_geometry import (
    calculate_total_volume,
    liquid_height_from_volume,
    calculate_fill_percent,
)

from visualization.reactor_3d import (
    create_reactor_figure,
)

from reporting.report_generator import (
    build_pdf,
)


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
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 10% 0%,
                rgba(30, 64, 175, 0.08),
                transparent 30%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(14, 116, 144, 0.07),
                transparent 30%
            ),
            #f6f8fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    .app-header {
        padding: 1.25rem 1.5rem;
        border-radius: 18px;
        margin-bottom: 1.2rem;
        background:
            linear-gradient(
                135deg,
                #0f172a 0%,
                #172554 55%,
                #164e63 100%
            );
        color: white;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.16);
    }

    .app-header-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
    }

    .app-header-subtitle {
        font-size: 0.95rem;
        opacity: 0.86;
        line-height: 1.5;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 750;
        color: #0f172a;
        margin-top: 0.4rem;
        margin-bottom: 0.65rem;
    }

    .section-subtitle {
        font-size: 0.86rem;
        color: #64748b;
        margin-bottom: 0.9rem;
    }

    .kpi-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        min-height: 120px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }

    .kpi-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 650;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .kpi-value {
        color: #0f172a;
        font-size: 1.65rem;
        font-weight: 800;
        margin-top: 0.2rem;
        line-height: 1.2;
    }

    .kpi-unit {
        color: #64748b;
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }

    .status-pass {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        font-weight: 750;
        font-size: 0.8rem;
    }

    .status-fail {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: #fee2e2;
        color: #991b1b;
        font-weight: 750;
        font-size: 0.8rem;
    }

    .status-warning {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: #fef3c7;
        color: #92400e;
        font-weight: 750;
        font-size: 0.8rem;
    }

    .engineering-note {
        background: #eff6ff;
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.8rem 0;
        color: #1e3a8a;
        font-size: 0.86rem;
    }

    .engineering-error {
        background: #fef2f2;
        border-left: 4px solid #dc2626;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.8rem 0;
        color: #7f1d1d;
        font-size: 0.86rem;
    }

    .engineering-warning {
        background: #fffbeb;
        border-left: 4px solid #d97706;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.8rem 0;
        color: #78350f;
        font-size: 0.86rem;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.75rem;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        background: white;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <div class="app-header-title">
            ⚗️ Reactor Scale-Up Engineering Studio
        </div>
        <div class="app-header-subtitle">
            Integrated reactor geometry, agitator-train design,
            mixing performance, scale-up evaluation,
            engineering validation and 3D reactor visualization.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def get_train_value(train, *keys, default=None):
    if not isinstance(train, dict):
        return default

    for key in keys:
        if key in train and train[key] is not None:
            return train[key]

    return default


def get_qv_s(train, working_volume):
    """
    Returns Q/V in s^-1.

    Priority:
    1. Q_per_volume_1_s
    2. Q_per_volume_h converted to s^-1
    3. total_Q_m3_h / working_volume / 3600
    """

    if not isinstance(train, dict):
        return 0.0

    qv_s = train.get("Q_per_volume_1_s")

    if qv_s is not None:
        return safe_float(qv_s, 0.0)

    qv_h = train.get("Q_per_volume_h")

    if qv_h is not None:
        return safe_float(qv_h, 0.0) / 3600.0

    total_q = safe_float(
        train.get("total_Q_m3_h"),
        0.0,
    )

    volume = safe_float(
        working_volume,
        0.0,
    )

    if volume > 0:
        return total_q / volume / 3600.0

    return 0.0


def get_qv_h(train, working_volume):
    return get_qv_s(train, working_volume) * 3600.0


def initialize_agitators(name):
    key = f"agitators_{name}"

    if key not in st.session_state:
        st.session_state[key] = [0]

    return st.session_state[key]


def add_agitator(name):
    key = f"agitators_{name}"

    if key not in st.session_state:
        st.session_state[key] = [0]

    next_id = (
        max(st.session_state[key]) + 1
        if st.session_state[key]
        else 0
    )

    st.session_state[key].append(next_id)


def remove_agitator(name, stage_id):
    key = f"agitators_{name}"

    if key not in st.session_state:
        return

    if len(st.session_state[key]) <= 1:
        return

    if stage_id in st.session_state[key]:
        st.session_state[key].remove(stage_id)


def format_value(value, digits=2):
    if value is None:
        return "—"

    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def status_class(status):
    text = str(status).upper()

    if "PASS" in text:
        return "status-pass"

    if "FAIL" in text:
        return "status-fail"

    return "status-warning"


# ============================================================
# SESSION STATE
# ============================================================

if "reactors" not in st.session_state:
    st.session_state.reactors = {}

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Design Basis"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## Study Configuration")

    project_name = st.text_input(
        "Project Name",
        value="Reactor Scale-Up Study",
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
            "General Mixing",
            "Liquid-Liquid",
            "Solid-Liquid",
            "Gas-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
            "High-Viscosity",
            "Heat-Controlled Reaction",
        ],
    )

    scaleup_basis = st.selectbox(
        "Scale-Up Basis",
        [
            "Constant P/V",
            "Constant Tip Speed",
            "Constant Q/V",
            "Constant RPM",
            "Constant Froude Number",
            "Constant Reynolds Number",
        ],
    )

    st.markdown("---")

    st.markdown("### Engineering Focus")

    focus_metrics = st.multiselect(
        "Select engineering metrics",
        [
            "P/V",
            "Q/V",
            "Tip Speed",
            "Reynolds Number",
            "Power",
            "Torque",
            "N/Njs",
            "kLa",
        ],
        default=[
            "P/V",
            "Q/V",
            "Tip Speed",
            "Reynolds Number",
            "Power",
            "Torque",
        ],
    )

    st.markdown("---")

    st.markdown(
        """
        <div class="engineering-note">
            <b>Engineering basis</b><br>
            Use scale-up criteria according to the controlling
            physical phenomenon. RPM alone should not normally
            be treated as a universal scale-up criterion.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# REACTOR MODES
# ============================================================

reactor_modes = {
    "Single Reactor": ["Reactor"],
    "Lab vs Pilot": ["Lab", "Pilot"],
    "Pilot vs Commercial": ["Pilot", "Commercial"],
    "Lab vs Commercial": ["Lab", "Commercial"],
    "Lab vs Pilot vs Commercial": [
        "Lab",
        "Pilot",
        "Commercial",
    ],
}

reactor_names = reactor_modes.get(
    study_mode,
    ["Reactor"],
)


# ============================================================
# REACTOR INPUT PANEL
# ============================================================

def reactor_input_panel(name):

    st.markdown(
        f'<div class="section-title">⚗️ {name} Reactor Design Basis</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Define process conditions, reactor geometry, baffles and agitator train.'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # PROCESS CONDITIONS
    # --------------------------------------------------------

    with st.expander("Process Conditions", expanded=True):

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            working_volume = st.number_input(
                "Working Volume (m³)",
                min_value=0.001,
                value=3.0,
                step=0.1,
                key=f"{name}_working_volume",
            )

        with c2:
            density = st.number_input(
                "Density (kg/m³)",
                min_value=1.0,
                value=1000.0,
                step=10.0,
                key=f"{name}_density",
            )

        with c3:
            viscosity = st.number_input(
                "Viscosity (Pa·s)",
                min_value=0.000001,
                value=0.001,
                format="%.6f",
                key=f"{name}_viscosity",
            )

        with c4:
            surface_tension = st.number_input(
                "Surface Tension (N/m)",
                min_value=0.0001,
                value=0.072,
                format="%.4f",
                key=f"{name}_surface_tension",
            )

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    with st.expander("Reactor Geometry", expanded=True):

        g1, g2, g3, g4 = st.columns(4)

        with g1:
            tank_diameter = st.number_input(
                "Tank ID (m)",
                min_value=0.05,
                value=2.0,
                step=0.05,
                key=f"{name}_tank_diameter",
            )

        with g2:
            straight_height = st.number_input(
                "Straight Side (m)",
                min_value=0.05,
                value=2.5,
                step=0.05,
                key=f"{name}_straight_height",
            )

        with g3:
            bottom_type = st.selectbox(
                "Bottom Head",
                [
                    "Flat",
                    "2:1 Ellipsoidal",
                    "Torispherical",
                ],
                key=f"{name}_bottom_type",
            )

        with g4:
            top_type = st.selectbox(
                "Top Head",
                [
                    "Flat",
                    "2:1 Ellipsoidal",
                    "Torispherical",
                ],
                key=f"{name}_top_type",
            )

        try:
            total_volume = calculate_total_volume(
                tank_diameter,
                straight_height,
                bottom_type=bottom_type,
                top_type=top_type,
            )
        except TypeError:
            try:
                total_volume = calculate_total_volume(
                    tank_diameter,
                    straight_height,
                    bottom_type,
                    top_type,
                )
            except Exception:
                total_volume = 0.0
        except Exception:
            total_volume = 0.0

        total_volume = safe_float(
            total_volume,
            0.0,
        )

        try:
            liquid_height = liquid_height_from_volume(
                working_volume,
                tank_diameter,
                straight_height,
                bottom_type=bottom_type,
            )
        except TypeError:
            try:
                liquid_height = liquid_height_from_volume(
                    working_volume,
                    tank_diameter,
                    straight_height,
                    bottom_type,
                )
            except Exception:
                liquid_height = straight_height
        except Exception:
            liquid_height = straight_height

        liquid_height = safe_float(
            liquid_height,
            straight_height,
        )

        try:
            fill_percent = calculate_fill_percent(
                working_volume,
                total_volume,
            )
        except Exception:
            if total_volume > 0:
                fill_percent = (
                    working_volume / total_volume
                ) * 100.0
            else:
                fill_percent = 0.0

        fill_percent = safe_float(
            fill_percent,
            0.0,
        )

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric(
                "Calculated Vessel Capacity",
                f"{total_volume:.2f} m³",
            )

        with m2:
            st.metric(
                "Calculated Liquid Height",
                f"{liquid_height:.2f} m",
            )

        with m3:
            st.metric(
                "Operating Fill",
                f"{fill_percent:.1f}%",
            )

        if total_volume > 0 and working_volume > total_volume:

            st.markdown(
                f"""
                <div class="engineering-error">
                    <b>ENGINEERING DESIGN ERROR</b><br>
                    Working volume ({working_volume:.2f} m³)
                    exceeds calculated vessel capacity
                    ({total_volume:.2f} m³).
                    Current operating fill is
                    <b>{fill_percent:.1f}%</b>.
                    Increase reactor dimensions or reduce
                    the specified working volume.
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif fill_percent > 85:

            st.markdown(
                f"""
                <div class="engineering-warning">
                    <b>High Operating Fill</b><br>
                    Operating fill is {fill_percent:.1f}%.
                    Verify freeboard, gas disengagement,
                    foaming allowance and process safety requirements.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # BAFFLES
    # --------------------------------------------------------

    with st.expander("Baffles"):

        b1, b2 = st.columns(2)

        with b1:
            baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{name}_baffles",
            )

        with b2:
            baffle_width_ratio = st.number_input(
                "Baffle Width / Tank Diameter",
                min_value=0.0,
                max_value=0.30,
                value=0.10,
                step=0.01,
                key=f"{name}_baffle_ratio",
            )

    # --------------------------------------------------------
    # AGITATOR TRAIN
    # --------------------------------------------------------

    with st.expander(
        "Agitator Train",
        expanded=True,
    ):

        agitator_ids = initialize_agitators(name)

        top_add_col, top_info_col = st.columns(
            [1, 4]
        )

        with top_add_col:
            if st.button(
                "＋ Add Agitator",
                key=f"{name}_add_agitator",
                width="stretch",
            ):
                add_agitator(name)
                st.rerun()

        with top_info_col:
            st.caption(
                f"{len(agitator_ids)} agitator stage(s) configured."
            )

        stages = []

        for index, stage_id in enumerate(
            list(agitator_ids)
        ):

            stage_key = f"{name}_stage_{stage_id}"

            st.markdown(
                f"**Stage {index + 1}**"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                agitator_options = list(
                    AGITATORS.keys()
                )

                agitator_type = st.selectbox(
                    "Agitator Type",
                    agitator_options,
                    key=f"{stage_key}_type",
                )

            with c2:
                d_t = st.number_input(
                    "D/T Ratio",
                    min_value=0.05,
                    max_value=0.95,
                    value=0.40,
                    step=0.01,
                    key=f"{stage_key}_dt",
                )

            with c3:
                rpm = st.number_input(
                    "RPM",
                    min_value=0.1,
                    max_value=2000.0,
                    value=120.0,
                    step=1.0,
                    key=f"{stage_key}_rpm",
                )

            with c4:
                number_impellers = st.number_input(
                    "No. of Impellers",
                    min_value=1,
                    max_value=10,
                    value=1,
                    step=1,
                    key=f"{stage_key}_nimp",
                )

            c5, c6, c7, c8 = st.columns(4)

            with c5:
                blades = st.number_input(
                    "Blades",
                    min_value=2,
                    max_value=12,
                    value=4,
                    step=1,
                    key=f"{stage_key}_blades",
                )

            with c6:
                clearance = st.number_input(
                    "Clearance (m)",
                    min_value=0.0,
                    value=0.25,
                    step=0.01,
                    key=f"{stage_key}_clearance",
                )

            with c7:
                elevation = st.number_input(
                    "Elevation (m)",
                    min_value=0.0,
                    value=0.50,
                    step=0.05,
                    key=f"{stage_key}_elevation",
                )

            with c8:
                remove_clicked = st.button(
                    "Remove",
                    key=f"{stage_key}_remove",
                    width="stretch",
                )

            agitator_data = AGITATORS.get(
                agitator_type,
                {},
            )

            default_np = safe_float(
                agitator_data.get("Np", 1.0),
                1.0,
            )

            default_nq = safe_float(
                agitator_data.get("Nq", 0.5),
                0.5,
            )

            c9, c10 = st.columns(2)

            with c9:
                np_value = st.number_input(
                    "Power Number, Np",
                    min_value=0.0,
                    value=default_np,
                    step=0.05,
                    key=f"{stage_key}_np",
                )

            with c10:
                nq_value = st.number_input(
                    "Pumping Number, Nq",
                    min_value=0.0,
                    value=default_nq,
                    step=0.05,
                    key=f"{stage_key}_nq",
                )

            impeller_diameter = (
                d_t * tank_diameter
            )

            stages.append(
                {
                    "stage": index + 1,
                    "agitator": agitator_type,
                    "Np": np_value,
                    "Nq": nq_value,
                    "impeller_diameter_m": impeller_diameter,
                    "D_T": d_t,
                    "rpm": rpm,
                    "number_impellers": number_impellers,
                    "elevation_m": elevation,
                    "clearance_m": clearance,
                    "blades": blades,
                    "density_kg_m3": density,
                    "viscosity_pa_s": viscosity,
                    "tank_diameter_m": tank_diameter,
                    "liquid_height_m": liquid_height,
                    "working_volume_m3": working_volume,
                    "surface_tension_N_m": surface_tension,
                }
            )

            if remove_clicked:
                remove_agitator(
                    name,
                    stage_id,
                )
                st.rerun()

            if index < len(agitator_ids) - 1:
                st.markdown("---")

    # --------------------------------------------------------
    # SOLIDS
    # --------------------------------------------------------

    solids = {
        "solids_wt_percent": 0.0,
        "particle_diameter_m": 0.0,
        "solid_density_kg_m3": 0.0,
        "S": 7.0,
    }

    if process_type in [
        "Solid-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
    ]:

        with st.expander(
            "Solid Suspension / NJS",
            expanded=True,
        ):

            s1, s2, s3, s4 = st.columns(4)

            with s1:
                solids_wt = st.number_input(
                    "Solids Concentration (wt%)",
                    min_value=0.01,
                    max_value=80.0,
                    value=10.0,
                    step=0.5,
                    key=f"{name}_solids_wt",
                )

            with s2:
                particle_d50_mm = st.number_input(
                    "Particle d50 (mm)",
                    min_value=0.001,
                    value=0.5,
                    step=0.01,
                    format="%.3f",
                    key=f"{name}_particle_d50",
                )

            with s3:
                solid_density = st.number_input(
                    "Solid Density (kg/m³)",
                    min_value=10.0,
                    value=2500.0,
                    step=10.0,
                    key=f"{name}_solid_density",
                )

            with s4:
                zwietering_s = st.number_input(
                    "Zwietering S",
                    min_value=0.1,
                    value=7.0,
                    step=0.1,
                    key=f"{name}_zwietering_s",
                )

            solids = {
                "solids_wt_percent": solids_wt,
                "particle_diameter_m": particle_d50_mm / 1000.0,
                "solid_density_kg_m3": solid_density,
                "S": zwietering_s,
            }

    # --------------------------------------------------------
    # CALCULATIONS
    # --------------------------------------------------------

    geometry = {
        "working_volume_m3": working_volume,
        "tank_diameter_m": tank_diameter,
        "straight_height_m": straight_height,
        "bottom_type": bottom_type,
        "top_type": top_type,
        "total_volume_m3": total_volume,
        "liquid_height_m": liquid_height,
        "fill_percent": fill_percent,
        "baffles": baffles,
        "baffle_width_ratio": baffle_width_ratio,
        "density_kg_m3": density,
        "viscosity_pa_s": viscosity,
        "surface_tension_N_m": surface_tension,
    }

    try:

        calculation_output = calculate_train(
            stages,
            working_volume,
        )

        if (
            isinstance(calculation_output, tuple)
            and len(calculation_output) >= 2
        ):
            results = calculation_output[0]
            train = calculation_output[1]
        else:
            results = calculation_output
            train = {}

        if not isinstance(results, list):
            results = []

        if not isinstance(train, dict):
            train = {}

    except Exception as exc:

        st.error(
            f"Reactor calculation failed for {name}: {exc}"
        )

        results = []

        train = {
            "total_power_kw": 0.0,
            "P_per_V_kW_m3": 0.0,
            "total_Q_m3_h": 0.0,
            "Q_per_volume_1_s": 0.0,
            "maximum_reynolds": None,
            "average_tip_speed_m_s": 0.0,
            "turnover_time_min": None,
            "total_torque_Nm": 0.0,
        }

    # --------------------------------------------------------
    # SOLIDS NJS
    # --------------------------------------------------------

    if (
        process_type
        in [
            "Solid-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
        ]
        and stages
    ):

        updated_results = []

        for stage, result in zip(
            stages,
            results,
        ):

            try:

                njs_rpm = zwietering_njs(
                    stage,
                    solids["solids_wt_percent"],
                    solids["particle_diameter_m"],
                    solids["solid_density_kg_m3"],
                    density,
                    solids["S"],
                )

                rpm_value = safe_float(
                    stage.get("rpm"),
                    0.0,
                )

                if njs_rpm and njs_rpm > 0:
                    n_over_njs = (
                        rpm_value / njs_rpm
                    )
                else:
                    n_over_njs = None

                if isinstance(result, dict):
                    result = dict(result)
                    result["njs_rpm"] = njs_rpm
                    result["N_over_Njs"] = n_over_njs

            except Exception:
                pass

            updated_results.append(result)

        results = updated_results

    # --------------------------------------------------------
    # ENGINEERING VALIDATION
    # --------------------------------------------------------

    checks = []

    try:

        validation_geometry = dict(geometry)

        validation_geometry["working_volume_m3"] = (
            working_volume
        )

        validation_geometry["total_volume_m3"] = (
            total_volume
        )

        validation_geometry["fill_percent"] = (
            fill_percent
        )

        checks = validate_design(
            validation_geometry,
            results,
            process_type,
        )

        if checks is None:
            checks = []

    except Exception as exc:

        checks = [
            {
                "check": "Validation execution",
                "status": "WARNING",
                "message": str(exc),
            }
        ]

    # Explicit vessel-capacity validation.
    if (
        total_volume > 0
        and working_volume > total_volume
    ):

        checks.append(
            {
                "check": "Working volume vs vessel capacity",
                "status": "FAIL",
                "message": (
                    f"Working volume {working_volume:.2f} m³ "
                    f"exceeds vessel capacity "
                    f"{total_volume:.2f} m³."
                ),
            }
        )

    try:
        overall = overall_status(checks)
    except Exception:
        overall = "FAIL" if any(
            isinstance(c, dict)
            and str(c.get("status", "")).upper()
            == "FAIL"
            for c in checks
        ) else "PASS"

    try:
        recs = recommendations(
            process_type,
            train,
        )

        if recs is None:
            recs = []

    except Exception:
        recs = []

    return {
        "name": name,
        "geometry": geometry,
        "stages": stages,
        "results": results,
        "train": train,
        "solids": solids,
        "checks": checks,
        "overall_status": overall,
        "recommendations": recs,
    }


# ============================================================
# BUILD REACTORS
# ============================================================

reactor_outputs = {}

for reactor_name in reactor_names:

    reactor_outputs[reactor_name] = reactor_input_panel(
        reactor_name
    )


# ============================================================
# ACTIVE REACTOR
# ============================================================

active_reactor_name = reactor_names[-1]

active_reactor = reactor_outputs[
    active_reactor_name
]

active_geometry = active_reactor["geometry"]
active_train = active_reactor["train"]
active_results = active_reactor["results"]

working_volume = safe_float(
    active_geometry.get(
        "working_volume_m3"
    ),
    0.0,
)

fill_percent = safe_float(
    active_geometry.get(
        "fill_percent"
    ),
    0.0,
)

shaft_power = safe_float(
    get_train_value(
        active_train,
        "total_power_kw",
        "shaft_power_kw",
        "power_kw",
        default=0.0,
    ),
    0.0,
)

p_per_v = safe_float(
    get_train_value(
        active_train,
        "P_per_V_kW_m3",
        "power_per_volume_kw_m3",
        "P_V_kW_m3",
        default=(
            shaft_power / working_volume
            if working_volume > 0
            else 0.0
        ),
    ),
    0.0,
)

total_q = safe_float(
    get_train_value(
        active_train,
        "total_Q_m3_h",
        "Q_total_m3_h",
        default=0.0,
    ),
    0.0,
)

qv_h = get_qv_h(
    active_train,
    working_volume,
)

qv_s = get_qv_s(
    active_train,
    working_volume,
)

maximum_re = get_train_value(
    active_train,
    "maximum_reynolds",
    "max_reynolds",
    "Re_max",
)

average_tip_speed = safe_float(
    get_train_value(
        active_train,
        "average_tip_speed_m_s",
        "tip_speed_m_s",
        default=0.0,
    ),
    0.0,
)

total_torque = safe_float(
    get_train_value(
        active_train,
        "total_torque_Nm",
        "torque_Nm",
        default=0.0,
    ),
    0.0,
)

turnover_time = get_train_value(
    active_train,
    "turnover_time_min",
    "turnover_time_minutes",
)

overall_status_value = active_reactor[
    "overall_status"
]


# ============================================================
# KPI OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">Engineering Performance Overview</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
k5, k6, k7, k8 = st.columns(4)

with k1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Working Volume</div>
            <div class="kpi-value">{working_volume:.2f}</div>
            <div class="kpi-unit">m³</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Operating Fill</div>
            <div class="kpi-value">{fill_percent:.1f}</div>
            <div class="kpi-unit">%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Shaft Power</div>
            <div class="kpi-value">{shaft_power:.2f}</div>
            <div class="kpi-unit">kW</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Power / Volume</div>
            <div class="kpi-value">{p_per_v:.3f}</div>
            <div class="kpi-unit">kW/m³</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k5:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Pumping</div>
            <div class="kpi-value">{total_q:.1f}</div>
            <div class="kpi-unit">m³/h</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k6:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Q / V</div>
            <div class="kpi-value">{qv_h:.2f}</div>
            <div class="kpi-unit">h⁻¹ &nbsp;|&nbsp; {qv_s:.4f} s⁻¹</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k7:

    re_text = (
        "—"
        if maximum_re is None
        else format_value(
            maximum_re,
            0,
        )
    )

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Maximum Reynolds Number</div>
            <div class="kpi-value">{re_text}</div>
            <div class="kpi-unit">dimensionless</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k8:

    status_text = str(
        overall_status_value
    ).upper()

    status_css = status_class(
        status_text
    )

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Engineering Status</div>
            <div class="kpi-value">
                <span class="{status_css}">
                    {status_text}
                </span>
            </div>
            <div class="kpi-unit">
                Based on current validation checks
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TABS
# ============================================================

tabs = st.tabs(
    [
        "Design Basis",
        "Reactor Geometry",
        "Agitator Train",
        "Performance",
        "Scale-Up",
        "Validation",
        "3D Mixing",
        "Engineering Report",
    ]
)


# ============================================================
# TAB 1 — DESIGN BASIS
# ============================================================

with tabs[0]:

    st.markdown(
        '<div class="section-title">Design Basis</div>',
        unsafe_allow_html=True,
    )

    basis_data = []

    for reactor_name, reactor in reactor_outputs.items():

        geometry = reactor["geometry"]
        train = reactor["train"]

        basis_data.append(
            {
                "Reactor": reactor_name,
                "Working Volume (m³)": safe_float(
                    geometry.get(
                        "working_volume_m3"
                    )
                ),
                "Tank ID (m)": safe_float(
                    geometry.get(
                        "tank_diameter_m"
                    )
                ),
                "Straight Side (m)": safe_float(
                    geometry.get(
                        "straight_height_m"
                    )
                ),
                "Calculated Capacity (m³)": safe_float(
                    geometry.get(
                        "total_volume_m3"
                    )
                ),
                "Fill (%)": safe_float(
                    geometry.get(
                        "fill_percent"
                    )
                ),
                "Power (kW)": safe_float(
                    get_train_value(
                        train,
                        "total_power_kw",
                        default=0.0,
                    )
                ),
                "P/V (kW/m³)": safe_float(
                    get_train_value(
                        train,
                        "P_per_V_kW_m3",
                        default=0.0,
                    )
                ),
                "Q (m³/h)": safe_float(
                    get_train_value(
                        train,
                        "total_Q_m3_h",
                        default=0.0,
                    )
                ),
                "Status": reactor[
                    "overall_status"
                ],
            }
        )

    if basis_data:

        df_basis = pd.DataFrame(
            basis_data
        )

        st.dataframe(
            df_basis,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# TAB 2 — REACTOR GEOMETRY
# ============================================================

with tabs[1]:

    st.markdown(
        '<div class="section-title">Reactor Geometry Comparison</div>',
        unsafe_allow_html=True,
    )

    geometry_rows = []

    for reactor_name, reactor in reactor_outputs.items():

        geometry = reactor["geometry"]

        geometry_rows.append(
            {
                "Reactor": reactor_name,
                "Tank ID (m)": geometry.get(
                    "tank_diameter_m"
                ),
                "Straight Side (m)": geometry.get(
                    "straight_height_m"
                ),
                "Bottom Head": geometry.get(
                    "bottom_type"
                ),
                "Top Head": geometry.get(
                    "top_type"
                ),
                "Vessel Capacity (m³)": geometry.get(
                    "total_volume_m3"
                ),
                "Working Volume (m³)": geometry.get(
                    "working_volume_m3"
                ),
                "Liquid Height (m)": geometry.get(
                    "liquid_height_m"
                ),
                "Fill (%)": geometry.get(
                    "fill_percent"
                ),
                "Baffles": geometry.get(
                    "baffles"
                ),
                "Baffle Width / T": geometry.get(
                    "baffle_width_ratio"
                ),
            }
        )

    if geometry_rows:

        st.dataframe(
            pd.DataFrame(
                geometry_rows
            ),
            width="stretch",
            hide_index=True,
        )

    st.markdown(
        """
        <div class="engineering-note">
            <b>Geometry check:</b>
            Operating fill must remain below calculated vessel capacity.
            Freeboard requirements should additionally consider foaming,
            gas disengagement, vapor space and process-specific constraints.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TAB 3 — AGITATOR TRAIN
# ============================================================

with tabs[2]:

    st.markdown(
        '<div class="section-title">Agitator Train Summary</div>',
        unsafe_allow_html=True,
    )

    for reactor_name, reactor in reactor_outputs.items():

        st.markdown(
            f"### {reactor_name}"
        )

        stage_rows = []

        for stage, result in zip(
            reactor["stages"],
            reactor["results"],
        ):

            result_dict = (
                result
                if isinstance(result, dict)
                else {}
            )

            stage_rows.append(
                {
                    "Stage": stage.get(
                        "stage"
                    ),
                    "Agitator": stage.get(
                        "agitator"
                    ),
                    "D/T": stage.get(
                        "D_T"
                    ),
                    "Impeller D (m)": stage.get(
                        "impeller_diameter_m"
                    ),
                    "RPM": stage.get(
                        "rpm"
                    ),
                    "Impellers": stage.get(
                        "number_impellers"
                    ),
                    "Np": stage.get(
                        "Np"
                    ),
                    "Nq": stage.get(
                        "Nq"
                    ),
                    "Power (kW)": result_dict.get(
                        "power_kw"
                    ),
                    "Q (m³/h)": result_dict.get(
                        "flow_m3_h"
                    ),
                    "Re": result_dict.get(
                        "reynolds"
                    ),
                    "Tip Speed (m/s)": result_dict.get(
                        "tip_speed_m_s"
                    ),
                    "NJS (RPM)": result_dict.get(
                        "njs_rpm"
                    ),
                    "N/NJS": result_dict.get(
                        "N_over_Njs"
                    ),
                }
            )

        if stage_rows:

            st.dataframe(
                pd.DataFrame(
                    stage_rows
                ),
                width="stretch",
                hide_index=True,
            )

        else:

            st.info(
                "No agitator calculation results are available."
            )


# ============================================================
# TAB 4 — PERFORMANCE
# ============================================================

with tabs[3]:

    st.markdown(
        '<div class="section-title">Mixing Performance</div>',
        unsafe_allow_html=True,
    )

    p1, p2, p3 = st.columns(3)

    with p1:
        st.metric(
            "Shaft Power",
            f"{shaft_power:.3f} kW",
        )

    with p2:
        st.metric(
            "P/V",
            f"{p_per_v:.4f} kW/m³",
        )

    with p3:
        st.metric(
            "Q/V",
            f"{qv_h:.2f} h⁻¹",
        )

    p4, p5, p6 = st.columns(3)

    with p4:
        st.metric(
            "Q/V",
            f"{qv_s:.5f} s⁻¹",
        )

    with p5:
        st.metric(
            "Average Tip Speed",
            f"{average_tip_speed:.2f} m/s",
        )

    with p6:
        st.metric(
            "Total Torque",
            f"{total_torque:.1f} N·m",
        )

    if turnover_time is not None:

        st.metric(
            "Estimated Turnover Time",
            f"{safe_float(turnover_time):.2f} min",
        )

    if active_results:

        st.markdown(
            "### Stage-Level Performance"
        )

        performance_rows = []

        for result in active_results:

            if not isinstance(result, dict):
                continue

            performance_rows.append(
                {
                    "Stage": result.get(
                        "stage"
                    ),
                    "Power (kW)": result.get(
                        "power_kw"
                    ),
                    "Flow (m³/h)": result.get(
                        "flow_m3_h"
                    ),
                    "P/V (kW/m³)": result.get(
                        "power_per_volume_kw_m3"
                    ),
                    "Reynolds": result.get(
                        "reynolds"
                    ),
                    "Tip Speed (m/s)": result.get(
                        "tip_speed_m_s"
                    ),
                    "Torque (N·m)": result.get(
                        "torque_Nm"
                    ),
                    "NJS (RPM)": result.get(
                        "njs_rpm"
                    ),
                    "N/NJS": result.get(
                        "N_over_Njs"
                    ),
                }
            )

        if performance_rows:

            st.dataframe(
                pd.DataFrame(
                    performance_rows
                ),
                width="stretch",
                hide_index=True,
            )


# ============================================================
# TAB 5 — SCALE-UP
# ============================================================

with tabs[4]:

    st.markdown(
        '<div class="section-title">Scale-Up Evaluation</div>',
        unsafe_allow_html=True,
    )

    if len(reactor_names) >= 2:

        reference_name = reactor_names[0]
        target_name = reactor_names[-1]

        reference = reactor_outputs[
            reference_name
        ]

        target = reactor_outputs[
            target_name
        ]

        reference_stage = (
            reference["stages"][0]
            if reference["stages"]
            else {}
        )

        target_stage = (
            target["stages"][0]
            if target["stages"]
            else {}
        )

        reference_basis = {
            "working_volume_m3": reference[
                "geometry"
            ].get(
                "working_volume_m3"
            ),
            "tank_diameter_m": reference[
                "geometry"
            ].get(
                "tank_diameter_m"
            ),
            "rpm": reference_stage.get(
                "rpm"
            ),
            "impeller_diameter_m": reference_stage.get(
                "impeller_diameter_m"
            ),
            "density_kg_m3": reference[
                "geometry"
            ].get(
                "density_kg_m3"
            ),
            "viscosity_pa_s": reference[
                "geometry"
            ].get(
                "viscosity_pa_s"
            ),
        }

        target_basis = {
            "working_volume_m3": target[
                "geometry"
            ].get(
                "working_volume_m3"
            ),
            "tank_diameter_m": target[
                "geometry"
            ].get(
                "tank_diameter_m"
            ),
            "rpm": target_stage.get(
                "rpm"
            ),
            "impeller_diameter_m": target_stage.get(
                "impeller_diameter_m"
            ),
            "density_kg_m3": target[
                "geometry"
            ].get(
                "density_kg_m3"
            ),
            "viscosity_pa_s": target[
                "geometry"
            ].get(
                "viscosity_pa_s"
            ),
        }

        try:

            scaleup_result = calculate_scaleup(
                reference_basis,
                target_basis,
                scaleup_basis,
            )

        except Exception as exc:

            scaleup_result = {
                "error": str(exc)
            }

        st.markdown(
            f"""
            <div class="engineering-note">
                <b>Scale-Up Basis:</b> {scaleup_basis}<br>
                Reference: <b>{reference_name}</b><br>
                Target: <b>{target_name}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if isinstance(
            scaleup_result,
            dict,
        ):

            if "error" in scaleup_result:

                st.error(
                    f"Scale-up calculation failed: "
                    f"{scaleup_result['error']}"
                )

            else:

                scaleup_rows = []

                for key, value in scaleup_result.items():

                    if isinstance(
                        value,
                        (int, float),
                    ):

                        scaleup_rows.append(
                            {
                                "Parameter": key,
                                "Value": value,
                            }
                        )

                if scaleup_rows:

                    st.dataframe(
                        pd.DataFrame(
                            scaleup_rows
                        ),
                        width="stretch",
                        hide_index=True,
                    )

                else:

                    st.json(
                        scaleup_result
                    )

    else:

        st.info(
            "Select a comparative study mode to perform scale-up evaluation."
        )


# ============================================================
# TAB 6 — VALIDATION
# ============================================================

with tabs[5]:

    st.markdown(
        '<div class="section-title">Engineering Validation</div>',
        unsafe_allow_html=True,
    )

    validation_rows = []

    for check in active_reactor[
        "checks"
    ]:

        if isinstance(check, dict):

            validation_rows.append(
                {
                    "Check": check.get(
                        "check",
                        check.get(
                            "name",
                            "Validation Check",
                        ),
                    ),
                    "Status": check.get(
                        "status",
                        "WARNING",
                    ),
                    "Message": check.get(
                        "message",
                        check.get(
                            "reason",
                            "",
                        ),
                    ),
                }
            )

        else:

            validation_rows.append(
                {
                    "Check": str(check),
                    "Status": "INFO",
                    "Message": "",
                }
            )

    if validation_rows:

        validation_df = pd.DataFrame(
            validation_rows
        )

        st.dataframe(
            validation_df,
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No validation checks were returned."
        )

    st.markdown(
        "### Engineering Recommendations"
    )

    if active_reactor[
        "recommendations"
    ]:

        for recommendation in active_reactor[
            "recommendations"
        ]:

            st.markdown(
                f"- {recommendation}"
            )

    else:

        st.info(
            "No additional recommendations were returned."
        )

    if (
        active_geometry["working_volume_m3"]
        > active_geometry["total_volume_m3"]
        and active_geometry["total_volume_m3"] > 0
    ):

        st.markdown(
            """
            <div class="engineering-error">
                <b>Critical:</b>
                The specified working volume is greater than
                the calculated vessel capacity. This design
                should not be considered acceptable until the
                geometry or working volume is corrected.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# TAB 7 — 3D MIXING
# ============================================================

with tabs[6]:

    st.markdown(
        '<div class="section-title">3D Reactor & Mixing Visualization</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="engineering-note">
            The 3D visualization is intended for engineering
            communication and qualitative assessment. It should
            not be interpreted as CFD or as a substitute for
            detailed mechanical/vendor drawings.
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:

        fig = create_reactor_figure(
            tank_diameter_m=active_geometry[
                "tank_diameter_m"
            ],
            straight_height_m=active_geometry[
                "straight_height_m"
            ],
            liquid_height_m=active_geometry[
                "liquid_height_m"
            ],
            results=active_results,
            baffles=active_geometry[
                "baffles"
            ],
            bottom_type=active_geometry[
                "bottom_type"
            ],
            top_type=active_geometry[
                "top_type"
            ],
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

    except Exception as exc:

        st.error(
            "3D reactor visualization could not be generated."
        )

        st.exception(exc)


# ============================================================
# TAB 8 — ENGINEERING REPORT
# ============================================================

with tabs[7]:

    st.markdown(
        '<div class="section-title">Engineering Report</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Generate an engineering summary containing the
        design basis, reactor geometry, agitator train,
        mixing performance, scale-up information and
        validation status.
        """
    )

    report_data = {
        "project_name": project_name,
        "study_mode": study_mode,
        "process_type": process_type,
        "scaleup_basis": scaleup_basis,
        "reactors": reactor_outputs,
        "focus_metrics": focus_metrics,
    }

    try:

        pdf_bytes = build_pdf(
            report_data
        )

        if pdf_bytes:

            st.download_button(
                label="⬇️ Download Engineering Report",
                data=pdf_bytes,
                file_name=(
                    f"{project_name.replace(' ', '_')}"
                    "_reactor_scaleup_report.pdf"
                ),
                mime="application/pdf",
                width="stretch",
            )

        else:

            st.warning(
                "The report generator returned no PDF data."
            )

    except Exception as exc:

        st.error(
            "Engineering report could not be generated."
        )

        st.exception(exc)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    "---"
)

st.caption(
    "Reactor Scale-Up Engineering Studio | "
    "Engineering decision-support tool | "
    "Validate final equipment design against process data, "
    "mechanical design requirements, vendor data and process safety requirements."
)
