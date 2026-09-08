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


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f5f7fa;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    [data-testid="stSidebar"] * {
        color: #f3f4f6;
    }

    .app-header {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #1e3a5f 100%
        );
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 22px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
    }

    .app-header-title {
        color: white;
        font-size: 31px;
        font-weight: 750;
        line-height: 1.2;
        margin-bottom: 8px;
    }

    .app-header-subtitle {
        color: #dbe7f5;
        font-size: 14px;
        line-height: 1.6;
    }

    .section-header {
        font-size: 22px;
        font-weight: 700;
        color: #172033;
        margin-top: 18px;
        margin-bottom: 10px;
    }

    .subsection-header {
        font-size: 17px;
        font-weight: 700;
        color: #24344d;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    .kpi-card {
        background: white;
        border: 1px solid #dce3ec;
        border-radius: 12px;
        padding: 15px 16px;
        min-height: 98px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    .kpi-label {
        color: #64748b;
        font-size: 12px;
        font-weight: 650;
    }

    .kpi-value {
        color: #172033;
        font-size: 23px;
        font-weight: 750;
        margin-top: 5px;
    }

    .kpi-unit {
        color: #64748b;
        font-size: 11px;
        margin-top: 2px;
    }

    .engineering-note {
        background: white;
        border: 1px solid #dce3ec;
        border-radius: 12px;
        padding: 16px;
        margin-top: 10px;
        margin-bottom: 10px;
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
    <div class="app-header">
        <div class="app-header-title">
            Reactor Scale-Up Engineering Studio
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


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## Reactor Scale-Up")

    st.markdown("---")

    st.markdown(
        """
        **Study Configuration**

        Process and scale-up basis.

        **Reactor Design**

        Vessel geometry and internals.

        **Agitator Train**

        Independent impeller configuration.

        **Performance**

        Power, P/V, Q/V, Re and torque.

        **Scale-Up**

        Reactor comparison and scale-up.

        **Validation**

        Engineering screening checks.

        **3D Mixing**

        Reactor and agitator visualization.

        **Engineering Report**

        Preliminary engineering report.
        """
    )

    st.markdown("---")

    st.caption(
        "Preliminary engineering screening tool. "
        "Final equipment selection requires validated "
        "process, vendor and mechanical design data."
    )


# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        return float(value)

    except Exception:
        return default


def safe_int(value, default=1):
    try:
        if value is None:
            return default

        return int(value)

    except Exception:
        return default


def get_train_value(train, key, default=0.0):
    """
    Safely retrieve a calculated train parameter.
    """
    if not isinstance(train, dict):
        return default

    value = train.get(key, default)

    if value is None:
        return default

    return value


def get_qv_per_second(train, working_volume_m3):
    """
    Returns Q/V in s^-1.

    Supports multiple possible engine output names.
    """

    if not isinstance(train, dict):
        return 0.0

    # Preferred current engine key
    value = train.get("Q_per_volume_1_s")

    if value is not None:
        return safe_float(value, 0.0)

    # Alternative key if engine provides Q/V in h^-1
    value = train.get("Q_per_volume_h")

    if value is not None:
        qv_h = safe_float(value, 0.0)
        return qv_h / 3600.0

    # Derive directly from total flow
    total_q = safe_float(
        train.get("total_Q_m3_h"),
        0.0,
    )

    volume = safe_float(
        working_volume_m3,
        0.0,
    )

    if volume > 0:
        return total_q / volume / 3600.0

    return 0.0


def get_qv_per_hour(train, working_volume_m3):
    """
    Returns Q/V in h^-1.
    """

    qv_s = get_qv_per_second(
        train,
        working_volume_m3,
    )

    return qv_s * 3600.0


def initialize_agitators(reactor_name):

    key = f"{reactor_name}_agitator_ids"

    if key not in st.session_state:

        st.session_state[key] = [1, 2]


def add_agitator(reactor_name):

    key = f"{reactor_name}_agitator_ids"

    initialize_agitators(reactor_name)

    ids = st.session_state[key]

    new_id = max(ids) + 1 if ids else 1

    ids.append(new_id)


def remove_agitator(
    reactor_name,
    agitator_id,
):

    key = f"{reactor_name}_agitator_ids"

    initialize_agitators(reactor_name)

    ids = st.session_state[key]

    if len(ids) <= 1:
        return

    st.session_state[key] = [
        item
        for item in ids
        if item != agitator_id
    ]


def get_default_agitator_spec(agitator_name):

    try:

        spec = AGITATORS.get(
            agitator_name,
            {},
        )

        if isinstance(spec, dict):
            return spec

    except Exception:
        pass

    return {}


def get_stage_value(
    stage,
    key,
    default=None,
):

    if not isinstance(stage, dict):
        return default

    value = stage.get(
        key,
        default,
    )

    return value


# =========================================================
# STUDY CONFIGURATION
# =========================================================

st.markdown(
    '<div class="section-header">Study Configuration</div>',
    unsafe_allow_html=True,
)

with st.container():

    c1, c2, c3 = st.columns(3)

    with c1:

        project_name = st.text_input(
            "Project / Study Name",
            value="Reactor Scale-Up Study",
            key="project_name",
        )

    with c2:

        study_mode = st.selectbox(
            "Study Mode",
            [
                "Single Reactor",
                "Lab vs Pilot",
                "Pilot vs Commercial",
                "Lab vs Commercial",
                "Lab vs Pilot vs Commercial",
            ],
            key="study_mode",
        )

    with c3:

        process_type = st.selectbox(
            "Process Requirement",
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
            key="process_type",
        )

    c1, c2 = st.columns(2)

    with c1:

        scaleup_basis = st.selectbox(
            "Primary Scale-Up Basis",
            [
                "Constant P/V",
                "Constant Tip Speed",
                "Constant Q/V",
                "Constant RPM",
                "Constant Froude Number",
                "Constant Reynolds Number",
            ],
            key="scaleup_basis",
        )

    with c2:

        focus_items = [
            "P/V",
            "Q/V",
            "Tip Speed",
            "Reynolds Number",
            "Power",
            "Torque",
        ]

        if process_type in [
            "Solid-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
        ]:

            focus_items.append("N/Njs")

        if process_type in [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ]:

            focus_items.append("kLa")

        st.markdown("**Engineering Focus**")

        st.write(
            " • ".join(focus_items)
        )


# =========================================================
# DETERMINE REACTORS
# =========================================================

if study_mode == "Single Reactor":

    reactor_names = [
        "Reactor"
    ]

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
# REACTOR INPUT PANEL
# =========================================================

def reactor_input_panel(name):

    st.markdown(
        f'<div class="section-header">{name} Reactor</div>',
        unsafe_allow_html=True,
    )

    # =====================================================
    # PROCESS CONDITIONS
    # =====================================================

    with st.container():

        st.markdown(
            '<div class="subsection-header">'
            '1. Process Conditions'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            default_volume = (
                20.0
                if name == "Commercial"
                else 3.0
            )

            working_volume = st.number_input(
                "Working Volume (m³)",
                min_value=0.01,
                max_value=5000.0,
                value=default_volume,
                step=0.1,
                key=f"{name}_volume",
            )

        with c2:

            density = st.number_input(
                "Liquid Density (kg/m³)",
                min_value=1.0,
                max_value=5000.0,
                value=1000.0,
                step=10.0,
                key=f"{name}_density",
            )

        with c3:

            viscosity_cp = st.number_input(
                "Viscosity (cP)",
                min_value=0.01,
                max_value=1000000.0,
                value=1.0,
                step=0.1,
                key=f"{name}_viscosity",
            )

        with c4:

            surface_tension = st.number_input(
                "Surface Tension (mN/m)",
                min_value=0.1,
                max_value=500.0,
                value=72.0,
                step=0.5,
                key=f"{name}_surface_tension",
            )

    # =====================================================
    # REACTOR GEOMETRY
    # =====================================================

    with st.container():

        st.markdown(
            '<div class="subsection-header">'
            '2. Reactor Geometry'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            tank_D = st.number_input(
                "Tank ID (m)",
                min_value=0.1,
                max_value=20.0,
                value=(
                    2.2
                    if name == "Commercial"
                    else 1.0
                ),
                step=0.01,
                key=f"{name}_tank_D",
            )

        with c2:

            straight_H = st.number_input(
                "Straight Side (m)",
                min_value=0.1,
                max_value=30.0,
                value=(
                    3.0
                    if name == "Commercial"
                    else 2.0
                ),
                step=0.01,
                key=f"{name}_straight_H",
            )

        head_types = [
            "Flat Bottom",
            "2:1 Ellipsoidal",
            "10% Torispherical",
            "6% Torispherical",
            "Hemispherical",
            "Conical",
        ]

        with c3:

            bottom_type = st.selectbox(
                "Bottom Head",
                head_types,
                index=1,
                key=f"{name}_bottom",
            )

        with c4:

            top_type = st.selectbox(
                "Top Head",
                head_types,
                index=1,
                key=f"{name}_top",
            )

        try:

            total_volume = calculate_total_volume(
                tank_D,
                straight_H,
                bottom_type,
                top_type,
            )

        except Exception:

            total_volume = 0.0

        try:

            liquid_height = liquid_height_from_volume(
                working_volume,
                tank_D,
                straight_H,
                bottom_type,
                top_type,
            )

        except Exception:

            liquid_height = 0.0

        try:

            fill = calculate_fill_percent(
                working_volume,
                total_volume,
            )

        except Exception:

            fill = 0.0

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Vessel Volume",
            f"{total_volume:.2f} m³",
        )

        c2.metric(
            "Liquid Height",
            f"{liquid_height:.2f} m",
        )

        c3.metric(
            "Operating Fill",
            f"{fill:.1f} %",
        )

        H_T = (
            liquid_height / tank_D
            if tank_D > 0
            else 0.0
        )

        c4.metric(
            "H/T",
            f"{H_T:.2f}",
        )

        if (
            total_volume > 0
            and working_volume > total_volume
        ):

            st.error(
                "Working volume exceeds calculated vessel capacity."
            )

    # =====================================================
    # VESSEL INTERNALS
    # =====================================================

    with st.container():

        st.markdown(
            '<div class="subsection-header">'
            '3. Vessel Internals'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)

        with c1:

            baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{name}_baffles",
            )

        with c2:

            baffle_width_ratio = st.number_input(
                "Baffle Width / Tank D",
                min_value=0.0,
                max_value=0.20,
                value=0.10,
                step=0.005,
                key=f"{name}_baffle_width",
            )

    # =====================================================
    # AGITATOR TRAIN
    # =====================================================

    initialize_agitators(name)

    agitator_ids = st.session_state[
        f"{name}_agitator_ids"
    ]

    with st.container():

        st.markdown(
            '<div class="subsection-header">'
            '4. Agitator Train'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(
            [2, 2, 5]
        )

        with c1:

            st.button(
                "＋ Add Agitator",
                key=f"{name}_add_agitator",
                width="stretch",
                on_click=add_agitator,
                args=(name,),
            )

        with c2:

            if len(agitator_ids) > 1:

                st.button(
                    "− Remove Last",
                    key=f"{name}_remove_last",
                    width="stretch",
                    on_click=remove_agitator,
                    args=(
                        name,
                        agitator_ids[-1],
                    ),
                )

        with c3:

            st.write(
                f"Configured agitators: "
                f"**{len(agitator_ids)}**"
            )

        stages = []

        try:

            agitator_names = list(
                AGITATORS.keys()
            )

        except Exception:

            agitator_names = []

        if not agitator_names:

            st.error(
                "No agitators are defined in "
                "libraries/agitator_geometry.py."
            )

            return None

        default_agitator = agitator_names[0]

        for stage_number, agitator_id in enumerate(
            agitator_ids,
            start=1,
        ):

            st.markdown(
                f"#### Agitator {stage_number}"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                selected_agitator = st.selectbox(
                    "Agitator Type",
                    agitator_names,
                    index=0,
                    key=(
                        f"{name}_agitator_"
                        f"{agitator_id}"
                    ),
                )

            spec = get_default_agitator_spec(
                selected_agitator
            )

            with c2:

                default_ratio = safe_float(
                    spec.get(
                        "D_T",
                        0.40,
                    ),
                    0.40,
                )

                ratio = st.number_input(
                    "D/T Ratio",
                    min_value=0.05,
                    max_value=0.95,
                    value=default_ratio,
                    step=0.01,
                    key=(
                        f"{name}_DT_"
                        f"{agitator_id}"
                    ),
                )

            with c3:

                rpm = st.number_input(
                    "RPM",
                    min_value=0.1,
                    max_value=1500.0,
                    value=115.0,
                    step=1.0,
                    key=(
                        f"{name}_rpm_"
                        f"{agitator_id}"
                    ),
                )

            with c4:

                blades = st.number_input(
                    "Number of Blades",
                    min_value=1,
                    max_value=20,
                    value=safe_int(
                        spec.get(
                            "blades",
                            4,
                        ),
                        4,
                    ),
                    step=1,
                    key=(
                        f"{name}_blades_"
                        f"{agitator_id}"
                    ),
                )

            c1, c2, c3, c4 = st.columns(4)

            impeller_D = tank_D * ratio

            with c1:

                clearance_default = min(
                    0.15 * tank_D,
                    max(
                        tank_D * 0.5,
                        0.02,
                    ),
                )

                clearance = st.number_input(
                    "Bottom Clearance (m)",
                    min_value=0.001,
                    max_value=max(
                        tank_D,
                        0.1,
                    ),
                    value=min(
                        clearance_default,
                        tank_D,
                    ),
                    step=0.01,
                    key=(
                        f"{name}_clearance_"
                        f"{agitator_id}"
                    ),
                )

            with c2:

                elevation_default = min(
                    straight_H
                    * (
                        0.25
                        + (
                            stage_number - 1
                        )
                        * 0.25
                    ),
                    straight_H,
                )

                elevation = st.number_input(
                    "Elevation from Bottom (m)",
                    min_value=0.0,
                    max_value=max(
                        straight_H,
                        0.1,
                    ),
                    value=elevation_default,
                    step=0.01,
                    key=(
                        f"{name}_elevation_"
                        f"{agitator_id}"
                    ),
                )

            with c3:

                np_default = safe_float(
                    spec.get(
                        "Np",
                        1.0,
                    ),
                    1.0,
                )

                np_value = st.number_input(
                    "Power Number Np",
                    min_value=0.001,
                    max_value=50.0,
                    value=np_default,
                    step=0.05,
                    key=(
                        f"{name}_Np_"
                        f"{agitator_id}"
                    ),
                )

            with c4:

                nq_default = safe_float(
                    spec.get(
                        "Nq",
                        0.5,
                    ),
                    0.5,
                )

                nq_value = st.number_input(
                    "Flow Number Nq",
                    min_value=0.001,
                    max_value=10.0,
                    value=nq_default,
                    step=0.05,
                    key=(
                        f"{name}_Nq_"
                        f"{agitator_id}"
                    ),
                )

            st.caption(
                f"Impeller diameter: "
                f"{impeller_D:.3f} m"
            )

            c1, c2 = st.columns(
                [8, 1]
            )

            with c1:

                st.caption(
                    spec.get(
                        "description_short",
                        "Agitator geometry",
                    )
                )

            with c2:

                if len(agitator_ids) > 1:

                    st.button(
                        "✕",
                        key=(
                            f"{name}_delete_"
                            f"{agitator_id}"
                        ),
                        on_click=remove_agitator,
                        args=(
                            name,
                            agitator_id,
                        ),
                    )

            stages.append(
                {
                    "stage": stage_number,

                    "agitator":
                        selected_agitator,

                    "Np":
                        np_value,

                    "Nq":
                        nq_value,

                    "impeller_diameter_m":
                        impeller_D,

                    "D_T":
                        ratio,

                    "rpm":
                        rpm,

                    "number_impellers":
                        1,

                    "elevation_m":
                        elevation,

                    "clearance_m":
                        clearance,

                    "blades":
                        int(blades),

                    "density_kg_m3":
                        density,

                    "viscosity_pa_s":
                        viscosity_cp / 1000.0,

                    "tank_diameter_m":
                        tank_D,

                    "liquid_height_m":
                        liquid_height,

                    "working_volume_m3":
                        working_volume,
                }
            )

            st.divider()

    # =====================================================
    # SOLIDS
    # =====================================================

    solids_data = {
        "solids_wt_percent": 0.0,
        "particle_diameter_m": 0.0005,
        "solid_density_kg_m3": 1500.0,
        "S": 4.5,
    }

    if process_type in [
        "Solid-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
    ]:

        with st.container():

            st.markdown(
                '<div class="subsection-header">'
                '5. Solids Suspension Basis'
                '</div>',
                unsafe_allow_html=True,
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                solids_wt = st.number_input(
                    "Solids Loading (wt%)",
                    min_value=0.01,
                    max_value=90.0,
                    value=10.0,
                    step=0.5,
                    key=f"{name}_solids",
                )

            with c2:

                particle_d50_mm = st.number_input(
                    "Particle d50 (mm)",
                    min_value=0.001,
                    max_value=50.0,
                    value=0.5,
                    step=0.01,
                    key=f"{name}_particle",
                )

            with c3:

                solid_density = st.number_input(
                    "Solid Density (kg/m³)",
                    min_value=1.0,
                    max_value=20000.0,
                    value=1500.0,
                    step=10.0,
                    key=f"{name}_solid_density",
                )

            with c4:

                S_factor = st.number_input(
                    "Zwietering S",
                    min_value=0.1,
                    max_value=20.0,
                    value=4.5,
                    step=0.1,
                    key=f"{name}_S",
                )

            solids_data = {
                "solids_wt_percent":
                    solids_wt,

                "particle_diameter_m":
                    particle_d50_mm / 1000.0,

                "solid_density_kg_m3":
                    solid_density,

                "S":
                    S_factor,
            }

    return {
        "name":
            name,

        "working_volume_m3":
            working_volume,

        "density_kg_m3":
            density,

        "viscosity_cp":
            viscosity_cp,

        "viscosity_pa_s":
            viscosity_cp / 1000.0,

        "surface_tension_mN_m":
            surface_tension,

        "surface_tension_n_m":
            surface_tension / 1000.0,

        "tank_diameter_m":
            tank_D,

        "straight_height_m":
            straight_H,

        "bottom_type":
            bottom_type,

        "top_type":
            top_type,

        "total_volume_m3":
            total_volume,

        "liquid_height_m":
            liquid_height,

        "fill_percent":
            fill,

        "baffles":
            int(baffles),

        "baffle_width_ratio":
            baffle_width_ratio,

        "stages":
            stages,

        "solids":
            solids_data,
    }


# =========================================================
# COLLECT REACTOR DATA
# =========================================================

reactors = []

for reactor_name in reactor_names:

    reactor = reactor_input_panel(
        reactor_name
    )

    if reactor is not None:

        reactors.append(
            reactor
        )


# =========================================================
# CALCULATE ALL REACTORS
# =========================================================

for reactor in reactors:

    # -----------------------------------------------------
    # MAIN AGITATOR TRAIN CALCULATION
    # -----------------------------------------------------

    try:

        calculation_output = calculate_train(
            reactor["stages"],
            reactor["working_volume_m3"],
        )

        if (
            isinstance(
                calculation_output,
                tuple,
            )
            and len(calculation_output) >= 2
        ):

            results = calculation_output[0]
            train = calculation_output[1]

        else:

            results = []
            train = {}

        if not isinstance(results, list):
            results = list(results) if results else []

        if not isinstance(train, dict):
            train = {}

    except Exception as exc:

        st.error(
            f"{reactor['name']} calculation error: {exc}"
        )

        results = []

        train = {}

    # -----------------------------------------------------
    # ENSURE TRAIN OUTPUT KEYS EXIST
    # -----------------------------------------------------

    train.setdefault(
        "total_power_kw",
        0.0,
    )

    train.setdefault(
        "P_per_V_kW_m3",
        0.0,
    )

    train.setdefault(
        "total_Q_m3_h",
        0.0,
    )

    train.setdefault(
        "maximum_reynolds",
        None,
    )

    train.setdefault(
        "average_tip_speed_m_s",
        0.0,
    )

    train.setdefault(
        "turnover_time_min",
        None,
    )

    train.setdefault(
        "total_torque_Nm",
        0.0,
    )

    # -----------------------------------------------------
    # SAFE Q/V CALCULATION
    # -----------------------------------------------------

    qv_s = get_qv_per_second(
        train,
        reactor["working_volume_m3"],
    )

    train["Q_per_volume_1_s"] = qv_s

    train["Q_per_volume_h"] = qv_s * 3600.0

    # -----------------------------------------------------
    # NJS
    # -----------------------------------------------------

    if process_type in [
        "Solid-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
    ]:

        solids = reactor["solids"]

        for stage in results:

            try:

                njs = zwietering_njs(
                    stage,
                    solids[
                        "solids_wt_percent"
                    ],
                    solids[
                        "particle_diameter_m"
                    ],
                    solids[
                        "solid_density_kg_m3"
                    ],
                    reactor[
                        "density_kg_m3"
                    ],
                    solids[
                        "S"
                    ],
                )

            except Exception:

                njs = None

            stage["njs_rpm"] = njs

            if njs is not None and njs > 0:

                stage["N_over_Njs"] = (
                    safe_float(
                        stage.get(
                            "rpm",
                            0.0,
                        ),
                        0.0,
                    )
                    / njs
                )

            else:

                stage["N_over_Njs"] = None

    reactor["results"] = results

    reactor["train"] = train

    # =====================================================
    # GEOMETRY
    # =====================================================

    geometry = {
        "working_volume_m3":
            reactor[
                "working_volume_m3"
            ],

        "total_volume_m3":
            reactor[
                "total_volume_m3"
            ],

        "tank_diameter_m":
            reactor[
                "tank_diameter_m"
            ],

        "straight_height_m":
            reactor[
                "straight_height_m"
            ],

        "liquid_height_m":
            reactor[
                "liquid_height_m"
            ],

        "fill_percent":
            reactor[
                "fill_percent"
            ],

        "baffles":
            reactor[
                "baffles"
            ],
    }

    reactor["geometry"] = geometry

    # =====================================================
    # VALIDATION
    # =====================================================

    try:

        reactor["checks"] = validate_design(
            geometry,
            results,
            process_type,
        )

        if reactor["checks"] is None:
            reactor["checks"] = []

    except Exception as exc:

        reactor["checks"] = [
            {
                "severity": "REVIEW",
                "message":
                    f"Validation calculation error: {exc}",
            }
        ]

    try:

        reactor["status"] = overall_status(
            reactor["checks"]
        )

        if reactor["status"] is None:
            reactor["status"] = "REVIEW"

    except Exception:

        reactor["status"] = "REVIEW"

    try:

        reactor["recommendations"] = recommendations(
            process_type,
            train,
        )

        if reactor["recommendations"] is None:
            reactor["recommendations"] = []

    except Exception as exc:

        reactor["recommendations"] = [
            f"Recommendation engine error: {exc}"
        ]


# =========================================================
# STOP IF NO REACTOR
# =========================================================

if not reactors:

    st.error(
        "No reactor configuration is available."
    )

    st.stop()


# =========================================================
# ACTIVE REACTOR
# =========================================================

active_reactor = reactors[-1]

active_train = active_reactor[
    "train"
]

active_status = active_reactor[
    "status"
]


# =========================================================
# KPI OVERVIEW
# =========================================================

st.markdown(
    '<div class="section-header">'
    'Engineering Performance Overview'
    '</div>',
    unsafe_allow_html=True,
)

kpi_columns = st.columns(8)


def display_train_value(
    key,
    default=0.0,
):

    value = active_train.get(
        key,
        default,
    )

    if value is None:
        return default

    return value


kpis = [
    (
        "Working Volume",
        f"{safe_float(active_reactor['working_volume_m3']):.2f}",
        "m³",
    ),

    (
        "Operating Fill",
        f"{safe_float(active_reactor['fill_percent']):.1f}",
        "%",
    ),

    (
        "Shaft Power",
        f"{safe_float(display_train_value('total_power_kw')):.2f}",
        "kW",
    ),

    (
        "P/V",
        f"{safe_float(display_train_value('P_per_V_kW_m3')):.3f}",
        "kW/m³",
    ),

    (
        "Total Q",
        f"{safe_float(display_train_value('total_Q_m3_h')):.1f}",
        "m³/h",
    ),

    (
        "Q/V",
        f"{get_qv_per_second(active_train, active_reactor['working_volume_m3']):.4f}",
        "s⁻¹",
    ),

    (
        "Maximum Re",
        (
            f"{safe_float(display_train_value('maximum_reynolds'), 0):,.0f}"
            if display_train_value(
                "maximum_reynolds",
                None,
            ) is not None
            else "N/A"
        ),
        "",
    ),

    (
        "Status",
        str(active_status),
        "screening",
    ),
]


for col, (
    label,
    value,
    unit,
) in zip(
    kpi_columns,
    kpis,
):

    with col:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    {label}
                </div>

                <div class="kpi-value">
                    {value}
                </div>

                <div class="kpi-unit">
                    {unit}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# TABS
# =========================================================

(
    tab_basis,
    tab_geometry,
    tab_agitator,
    tab_performance,
    tab_scaleup,
    tab_validation,
    tab_3d,
    tab_report,
) = st.tabs(
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


# =========================================================
# DESIGN BASIS
# =========================================================

with tab_basis:

    st.markdown(
        "## Process & Scale-Up Design Basis"
    )

    guidance = {
        "General Mixing":
            "Primary focus is bulk circulation, Q/V and blend performance.",

        "Liquid-Liquid":
            "Review circulation, phase contact, dispersion and blend performance.",

        "Solid-Liquid":
            "Primary criterion is N/Njs, supported by P/V, Q/V and impeller clearance.",

        "Gas-Liquid":
            "Review gas dispersion, P/V, gas flow and mass-transfer requirements.",

        "Gas-Liquid-Solid":
            "Evaluate both solids suspension and gas dispersion.",

        "Crystallization":
            "Balance suspension, circulation, shear and crystal-growth requirements.",

        "High-Viscosity":
            "Prioritize torque, P/V, Reynolds number and mechanical loading.",

        "Heat-Controlled Reaction":
            "Mixing and heat-transfer requirements must both be demonstrated.",
    }

    scaleup_description = {
        "Constant P/V":
            "Maintains power density and is commonly used for mixing-intensity comparison.",

        "Constant Tip Speed":
            "Maintains impeller peripheral velocity and provides a useful shear-related comparison.",

        "Constant Q/V":
            "Maintains circulation or turnover intensity.",

        "Constant RPM":
            "Maintains rotational speed but is not a universal mixing similarity criterion.",

        "Constant Froude Number":
            "Maintains inertial/gravity similarity.",

        "Constant Reynolds Number":
            "Maintains viscous/inertial similarity.",
    }

    c1, c2 = st.columns(2)

    with c1:

        with st.container():

            st.markdown(
                "### Process Requirement"
            )

            st.info(
                guidance.get(
                    process_type,
                    "Review process-specific mixing requirements.",
                )
            )

    with c2:

        with st.container():

            st.markdown(
                "### Primary Scale-Up Criterion"
            )

            st.info(
                scaleup_description.get(
                    scaleup_basis,
                    "Review the selected scale-up basis.",
                )
            )

    with st.container():

        st.markdown(
            "### Engineering Principle"
        )

        st.warning(
            "RPM alone should not be treated as a universal "
            "scale-up criterion. Scale-up should reconcile "
            "P/V, Q/V, tip speed, Reynolds number, N/Njs, "
            "blend time, gas dispersion, mass transfer, "
            "heat transfer and mechanical requirements."
        )


# =========================================================
# GEOMETRY TAB
# =========================================================

with tab_geometry:

    st.markdown(
        "## Reactor Geometry"
    )

    geometry_rows = []

    for reactor in reactors:

        tank_diameter = safe_float(
            reactor["tank_diameter_m"],
            0.0,
        )

        liquid_height_value = safe_float(
            reactor["liquid_height_m"],
            0.0,
        )

        h_t = (
            liquid_height_value / tank_diameter
            if tank_diameter > 0
            else 0.0
        )

        geometry_rows.append(
            {
                "Reactor":
                    reactor["name"],

                "Working Volume (m³)":
                    round(
                        reactor[
                            "working_volume_m3"
                        ],
                        3,
                    ),

                "Vessel Volume (m³)":
                    round(
                        reactor[
                            "total_volume_m3"
                        ],
                        3,
                    ),

                "Tank ID (m)":
                    round(
                        reactor[
                            "tank_diameter_m"
                        ],
                        3,
                    ),

                "Straight Side (m)":
                    round(
                        reactor[
                            "straight_height_m"
                        ],
                        3,
                    ),

                "Liquid Height (m)":
                    round(
                        reactor[
                            "liquid_height_m"
                        ],
                        3,
                    ),

                "Fill (%)":
                    round(
                        reactor[
                            "fill_percent"
                        ],
                        1,
                    ),

                "H/T":
                    round(
                        h_t,
                        2,
                    ),

                "Baffles":
                    reactor[
                        "baffles"
                    ],
            }
        )

    st.dataframe(
        pd.DataFrame(
            geometry_rows
        ),
        width="stretch",
        hide_index=True,
    )


# =========================================================
# AGITATOR TAB
# =========================================================

with tab_agitator:

    st.markdown(
        "## Agitator Train Design"
    )

    for reactor in reactors:

        st.markdown(
            f"### {reactor['name']} Reactor"
        )

        rows = []

        for stage in reactor[
            "results"
        ]:

            rows.append(
                {
                    "Stage":
                        stage.get(
                            "stage",
                            "",
                        ),

                    "Agitator":
                        stage.get(
                            "agitator",
                            "",
                        ),

                    "D/T":
                        stage.get(
                            "D_T",
                            None,
                        ),

                    "Impeller D (m)":
                        stage.get(
                            "impeller_diameter_m",
                            None,
                        ),

                    "RPM":
                        stage.get(
                            "rpm",
                            None,
                        ),

                    "Clearance (m)":
                        stage.get(
                            "clearance_m",
                            None,
                        ),

                    "Elevation (m)":
                        stage.get(
                            "elevation_m",
                            None,
                        ),

                    "Blades":
                        stage.get(
                            "blades",
                            None,
                        ),

                    "Np":
                        stage.get(
                            "Np",
                            None,
                        ),

                    "Nq":
                        stage.get(
                            "Nq",
                            None,
                        ),

                    "Re":
                        stage.get(
                            "Re",
                            None,
                        ),

                    "Power (kW)":
                        stage.get(
                            "power_kw",
                            None,
                        ),

                    "Q (m³/h)":
                        stage.get(
                            "Q_m3_h",
                            None,
                        ),

                    "Tip Speed (m/s)":
                        stage.get(
                            "tip_speed_m_s",
                            None,
                        ),

                    "Torque (N·m)":
                        stage.get(
                            "torque_Nm",
                            None,
                        ),

                    "Njs (RPM)":
                        stage.get(
                            "njs_rpm",
                            None,
                        ),

                    "N/Njs":
                        stage.get(
                            "N_over_Njs",
                            None,
                        ),
                }
            )

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                width="stretch",
                hide_index=True,
            )

        else:

            st.warning(
                "No agitator calculation results are available."
            )


# =========================================================
# PERFORMANCE TAB
# =========================================================

with tab_performance:

    st.markdown(
        "## Mixing Performance"
    )

    for reactor in reactors:

        st.markdown(
            f"### {reactor['name']} Performance"
        )

        train = reactor[
            "train"
        ]

        qv_s = get_qv_per_second(
            train,
            reactor["working_volume_m3"],
        )

        qv_h = qv_s * 3600.0

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Power",
            f"{safe_float(train.get('total_power_kw')):.2f} kW",
        )

        c2.metric(
            "Power Density",
            f"{safe_float(train.get('P_per_V_kW_m3')):.3f} kW/m³",
        )

        c3.metric(
            "Total Flow",
            f"{safe_float(train.get('total_Q_m3_h')):.1f} m³/h",
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Q/V",
            f"{qv_s:.4f} s⁻¹",
        )

        c2.metric(
            "Q/V",
            f"{qv_h:.2f} h⁻¹",
        )

        turnover = train.get(
            "turnover_time_min"
        )

        if turnover is not None:

            turnover_text = (
                f"{safe_float(turnover):.3f} min"
            )

        elif qv_s > 0:

            turnover_text = (
                f"{1.0 / qv_s / 60.0:.3f} min"
            )

        else:

            turnover_text = "N/A"

        c3.metric(
            "Turnover Time",
            turnover_text,
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Torque",
            f"{safe_float(train.get('total_torque_Nm')):.1f} N·m",
        )

        maximum_re = train.get(
            "maximum_reynolds"
        )

        c2.metric(
            "Maximum Reynolds Number",
            (
                f"{safe_float(maximum_re):,.0f}"
                if maximum_re is not None
                else "N/A"
            ),
        )

        rows = []

        for stage in reactor[
            "results"
        ]:

            rows.append(
                {
                    "Stage":
                        stage.get("stage"),

                    "Agitator":
                        stage.get("agitator"),

                    "Re":
                        stage.get("Re"),

                    "Fr":
                        stage.get("Fr"),

                    "Tip Speed (m/s)":
                        stage.get(
                            "tip_speed_m_s"
                        ),

                    "Power (kW)":
                        stage.get(
                            "power_kw"
                        ),

                    "Flow (m³/h)":
                        stage.get(
                            "Q_m3_h"
                        ),

                    "Torque (N·m)":
                        stage.get(
                            "torque_Nm"
                        ),

                    "Njs (RPM)":
                        stage.get(
                            "njs_rpm"
                        ),

                    "N/Njs":
                        stage.get(
                            "N_over_Njs"
                        ),
                }
            )

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                width="stretch",
                hide_index=True,
            )


# =========================================================
# SCALE-UP TAB
# =========================================================

with tab_scaleup:

    st.markdown(
        "## Reactor Scale-Up Evaluation"
    )

    if len(reactors) < 2:

        st.info(
            "Select a comparison study mode to activate "
            "the scale-up evaluation."
        )

    else:

        reference = reactors[0]

        target = reactors[-1]

        reference_volume = safe_float(
            reference[
                "working_volume_m3"
            ]
        )

        target_volume = safe_float(
            target[
                "working_volume_m3"
            ]
        )

        volume_ratio = (
            target_volume / reference_volume
            if reference_volume > 0
            else 0.0
        )

        reference_diameter = safe_float(
            reference[
                "tank_diameter_m"
            ]
        )

        target_diameter = safe_float(
            target[
                "tank_diameter_m"
            ]
        )

        diameter_ratio = (
            target_diameter
            / reference_diameter
            if reference_diameter > 0
            else 0.0
        )

        reference_train = reference[
            "train"
        ]

        target_train = target[
            "train"
        ]

        reference_pv = safe_float(
            reference_train.get(
                "P_per_V_kW_m3"
            )
        )

        target_pv = safe_float(
            target_train.get(
                "P_per_V_kW_m3"
            )
        )

        reference_qv = get_qv_per_second(
            reference_train,
            reference_volume,
        )

        target_qv = get_qv_per_second(
            target_train,
            target_volume,
        )

        pv_ratio = (
            target_pv / reference_pv
            if reference_pv > 0
            else 0.0
        )

        qv_ratio = (
            target_qv / reference_qv
            if reference_qv > 0
            else 0.0
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Volume Scale Factor",
            f"{volume_ratio:.2f} ×",
        )

        c2.metric(
            "Tank Diameter Ratio",
            f"{diameter_ratio:.2f} ×",
        )

        c3.metric(
            "P/V Ratio",
            f"{pv_ratio:.3f}",
        )

        c4.metric(
            "Q/V Ratio",
            f"{qv_ratio:.3f}",
        )

        st.markdown(
            "### Primary Scale-Up Calculation"
        )

        if (
            reference["results"]
            and target["results"]
        ):

            ref_stage = reference[
                "results"
            ][0]

            target_stage = target[
                "results"
            ][0]

            reference_basis = {
                "rpm":
                    safe_float(
                        ref_stage.get(
                            "rpm",
                            0.0,
                        )
                    ),

                "impeller_diameter_m":
                    safe_float(
                        ref_stage.get(
                            "impeller_diameter_m",
                            0.0,
                        )
                    ),

                "volume_m3":
                    reference_volume,
            }

            target_basis = {
                "impeller_diameter_m":
                    safe_float(
                        target_stage.get(
                            "impeller_diameter_m",
                            0.0,
                        )
                    ),

                "volume_m3":
                    target_volume,
            }

            try:

                scale_result = calculate_scaleup(
                    reference_basis,
                    target_basis,
                    scaleup_basis,
                )

                if not isinstance(
                    scale_result,
                    dict,
                ):

                    scale_result = {}

                target_rpm = scale_result.get(
                    "target_rpm"
                )

                target_tip = scale_result.get(
                    "target_tip_speed"
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Scale-Up Basis",
                    scaleup_basis,
                )

                c2.metric(
                    "Calculated Target RPM",
                    (
                        f"{safe_float(target_rpm):.1f} RPM"
                        if target_rpm is not None
                        else "N/A"
                    ),
                )

                c3.metric(
                    "Target Tip Speed",
                    (
                        f"{safe_float(target_tip):.2f} m/s"
                        if target_tip is not None
                        else "N/A"
                    ),
                )

                if scale_result:

                    st.markdown(
                        "### Scale-Up Calculation Details"
                    )

                    scale_rows = []

                    for key, value in scale_result.items():

                        if isinstance(
                            value,
                            (int, float),
                        ):

                            scale_rows.append(
                                {
                                    "Parameter":
                                        str(key),

                                    "Calculated Value":
                                        value,
                                }
                            )

                    if scale_rows:

                        st.dataframe(
                            pd.DataFrame(
                                scale_rows
                            ),
                            width="stretch",
                            hide_index=True,
                        )

            except Exception as exc:

                st.error(
                    f"Scale-up calculation error: {exc}"
                )

        else:

            st.warning(
                "Both reactors require at least one "
                "calculated agitator stage."
            )

        comparison_rows = [
            {
                "Parameter":
                    "Working Volume",

                "Unit":
                    "m³",

                reference["name"]:
                    reference[
                        "working_volume_m3"
                    ],

                target["name"]:
                    target[
                        "working_volume_m3"
                    ],
            },

            {
                "Parameter":
                    "Tank Diameter",

                "Unit":
                    "m",

                reference["name"]:
                    reference[
                        "tank_diameter_m"
                    ],

                target["name"]:
                    target[
                        "tank_diameter_m"
                    ],
            },

            {
                "Parameter":
                    "Liquid Height",

                "Unit":
                    "m",

                reference["name"]:
                    reference[
                        "liquid_height_m"
                    ],

                target["name"]:
                    target[
                        "liquid_height_m"
                    ],
            },

            {
                "Parameter":
                    "Total Power",

                "Unit":
                    "kW",

                reference["name"]:
                    reference[
                        "train"
                    ].get(
                        "total_power_kw",
                        0.0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "total_power_kw",
                        0.0,
                    ),
            },

            {
                "Parameter":
                    "P/V",

                "Unit":
                    "kW/m³",

                reference["name"]:
                    reference[
                        "train"
                    ].get(
                        "P_per_V_kW_m3",
                        0.0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "P_per_V_kW_m3",
                        0.0,
                    ),
            },

            {
                "Parameter":
                    "Total Q",

                "Unit":
                    "m³/h",

                reference["name"]:
                    reference[
                        "train"
                    ].get(
                        "total_Q_m3_h",
                        0.0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "total_Q_m3_h",
                        0.0,
                    ),
            },

            {
                "Parameter":
                    "Q/V",

                "Unit":
                    "s⁻¹",

                reference["name"]:
                    reference_qv,

                target["name"]:
                    target_qv,
            },
        ]

        st.markdown(
            "### Reactor Comparison"
        )

        st.dataframe(
            pd.DataFrame(
                comparison_rows
            ),
            width="stretch",
            hide_index=True,
        )

        st.warning(
            "Scale-up RPM is a preliminary engineering "
            "starting point. Final selection should reconcile "
            "P/V, Q/V, tip speed, Reynolds number, N/Njs, "
            "blend time, gas dispersion, heat transfer and "
            "mechanical design."
        )


# =========================================================
# VALIDATION TAB
# =========================================================

with tab_validation:

    st.markdown(
        "## Engineering Validation"
    )

    if active_status == "PASS":

        st.success(
            "Overall screening status: PASS"
        )

    elif active_status == "REVIEW":

        st.warning(
            "Overall screening status: REVIEW"
        )

    else:

        st.error(
            "Overall screening status: FAIL"
        )

    for reactor in reactors:

        st.markdown(
            f"### {reactor['name']} Reactor"
        )

        checks = reactor[
            "checks"
        ]

        validation_rows = []

        for item in checks:

            if not isinstance(
                item,
                dict,
            ):
                continue

            validation_rows.append(
                {
                    "Status":
                        item.get(
                            "severity",
                            "REVIEW",
                        ),

                    "Engineering Check":
                        item.get(
                            "message",
                            "",
                        ),
                }
            )

        if validation_rows:

            st.dataframe(
                pd.DataFrame(
                    validation_rows
                ),
                width="stretch",
                hide_index=True,
            )

        else:

            st.info(
                "No validation checks were returned."
            )

        recommendations_list = reactor.get(
            "recommendations",
            [],
        )

        if recommendations_list:

            st.markdown(
                "#### Engineering Recommendations"
            )

            for item in recommendations_list:

                st.info(
                    str(item)
                )


# =========================================================
# 3D MIXING TAB
# =========================================================

with tab_3d:

    st.markdown(
        "## 3D Reactor & Mixing Visualization"
    )

    selected_name = st.selectbox(
        "Select Reactor",
        [
            reactor["name"]
            for reactor in reactors
        ],
        key="selected_3d_reactor",
    )

    selected = next(
        reactor
        for reactor in reactors
        if reactor["name"] == selected_name
    )

    try:

        fig = create_reactor_figure(
            tank_diameter_m=
                selected[
                    "tank_diameter_m"
                ],

            straight_height_m=
                selected[
                    "straight_height_m"
                ],

            liquid_height_m=
                selected[
                    "liquid_height_m"
                ],

            results=
                selected[
                    "results"
                ],

            baffles=
                selected[
                    "baffles"
                ],

            bottom_type=
                selected[
                    "bottom_type"
                ],

            top_type=
                selected[
                    "top_type"
                ],
        )

        st.plotly_chart(
            fig,
            width="stretch",
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

    st.info(
        "The 3D model represents vessel geometry, "
        "baffles and agitator arrangement. It is a "
        "conceptual engineering visualization and not "
        "a CFD solution."
    )


# =========================================================
# ENGINEERING REPORT
# =========================================================

with tab_report:

    st.markdown(
        "## Engineering Report"
    )

    selected = reactors[-1]

    report_data = {
        "project_name":
            project_name,

        "process_type":
            process_type,

        "study_mode":
            study_mode,

        "scaleup_basis":
            scaleup_basis,

        "geometry":
            selected[
                "geometry"
            ],

        "stages":
            selected[
                "results"
            ],

        "train":
            selected[
                "train"
            ],

        "checks":
            selected[
                "checks"
            ],

        "recommendations":
            selected[
                "recommendations"
            ],
    }

    try:

        pdf_bytes = build_pdf(
            report_data
        )

        st.download_button(
            "Download Engineering PDF",
            data=pdf_bytes,
            file_name=(
                "reactor_scaleup_"
                "engineering_report.pdf"
            ),
            mime="application/pdf",
            width="stretch",
        )

    except Exception as exc:

        st.error(
            f"Report generation error: {exc}"
        )

    st.markdown(
        "### Engineering Recommendation"
    )

    recommendations_list = selected.get(
        "recommendations",
        [],
    )

    if recommendations_list:

        for item in recommendations_list:

            st.info(
                str(item)
            )

    else:

        st.info(
            "No additional engineering recommendations "
            "were returned by the validation module."
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Preliminary engineering screening tool. "
    "Np/Nq values should be based on validated agitator "
    "geometry, vendor data or reliable literature. "
    "Njs, blend time, kLa and heat-transfer calculations "
    "require system-specific validation. Final equipment "
    "selection requires vendor confirmation, mechanical "
    "design and process safety review."
)
