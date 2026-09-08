import math
import uuid

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

from libraries.agitator_geometry import (
    AGITATORS,
)

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

    /* =====================================================
       GLOBAL
       ===================================================== */

    .stApp {
        background: #f5f7fa;
    }

    .block-container {
        max-width: 1650px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }


    /* =====================================================
       SIDEBAR
       ===================================================== */

    [data-testid="stSidebar"] {
        background: #111827;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }


    /* =====================================================
       MAIN HEADER
       ===================================================== */

    .app-header {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #1e3a5f 55%,
            #315b7d 100%
        );

        padding: 28px 32px;
        border-radius: 18px;

        color: white;

        margin-bottom: 22px;

        box-shadow:
            0 8px 24px rgba(15, 23, 42, 0.14);
    }

    .app-header-title {
        font-size: 31px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.4px;
    }

    .app-header-subtitle {
        margin-top: 7px;
        font-size: 14px;
        color: #dbe7f5;
        line-height: 1.5;
    }


    /* =====================================================
       SECTION HEADER
       ===================================================== */

    .section-header {
        font-size: 21px;
        font-weight: 800;
        color: #172033;

        margin-top: 18px;
        margin-bottom: 12px;
    }

    .subsection-header {
        font-size: 16px;
        font-weight: 750;
        color: #243247;

        margin-top: 12px;
        margin-bottom: 8px;
    }


    /* =====================================================
       CONFIGURATION CARD
       ===================================================== */

    .config-card {
        background: white;

        border: 1px solid #dce3ec;
        border-radius: 15px;

        padding: 18px 20px;

        margin-bottom: 20px;

        box-shadow:
            0 3px 12px rgba(15, 23, 42, 0.045);
    }


    /* =====================================================
       METRIC CARDS
       ===================================================== */

    .metric-card {
        background: white;

        border: 1px solid #dce3ec;
        border-radius: 14px;

        padding: 15px 17px;

        min-height: 102px;

        box-shadow:
            0 3px 10px rgba(15, 23, 42, 0.04);
    }

    .metric-label {
        font-size: 11px;
        color: #64748b;

        font-weight: 700;

        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .metric-value {
        font-size: 23px;

        color: #172033;

        font-weight: 800;

        margin-top: 6px;
    }

    .metric-unit {
        font-size: 11px;
        color: #64748b;

        margin-top: 2px;
    }


    /* =====================================================
       ENGINEERING INFO
       ===================================================== */

    .engineering-note {
        background: #fff8e7;

        border: 1px solid #f1dfac;
        border-left: 4px solid #d49b21;

        border-radius: 10px;

        padding: 12px 15px;

        color: #604d17;

        font-size: 13px;

        line-height: 1.55;
    }

    .info-note {
        background: #eff6ff;

        border: 1px solid #cfe1f7;
        border-left: 4px solid #3b82f6;

        border-radius: 10px;

        padding: 12px 15px;

        color: #24466e;

        font-size: 13px;

        line-height: 1.55;
    }


    /* =====================================================
       AGITATOR CARD
       ===================================================== */

    .agitator-card {
        background: #ffffff;

        border: 1px solid #d9e1eb;

        border-radius: 14px;

        padding: 13px 15px;

        margin-bottom: 8px;

        box-shadow:
            0 2px 8px rgba(15, 23, 42, 0.035);
    }

    .agitator-stage-title {
        font-size: 16px;
        font-weight: 800;
        color: #1e293b;
    }

    .agitator-stage-subtitle {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
    }


    /* =====================================================
       STATUS
       ===================================================== */

    .status-pass {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #047857;

        border-radius: 10px;
        padding: 10px 14px;

        font-weight: 750;
    }

    .status-review {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #a16207;

        border-radius: 10px;
        padding: 10px 14px;

        font-weight: 750;
    }

    .status-fail {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #b91c1c;

        border-radius: 10px;
        padding: 10px 14px;

        font-weight: 750;
    }


    /* =====================================================
       SMALL TEXT
       ===================================================== */

    .small-muted {
        font-size: 12px;
        color: #64748b;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# APPLICATION HEADER
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
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_ratio(numerator, denominator):
    """Safe division."""
    try:
        if denominator is None or abs(float(denominator)) < 1e-12:
            return None
        return float(numerator) / float(denominator)
    except Exception:
        return None


def fmt(value, decimals=2):
    """Engineering-friendly formatting."""
    if value is None:
        return "N/A"

    try:
        if isinstance(value, float) and math.isnan(value):
            return "N/A"

        return f"{float(value):,.{decimals}f}"

    except Exception:
        return str(value)


def create_stage_id():
    """Create persistent unique ID for an agitator stage."""
    return uuid.uuid4().hex[:8]


# ============================================================
# STUDY CONFIGURATION
# ============================================================

if "project_name" not in st.session_state:
    st.session_state.project_name = "Reactor Scale-Up Study"

if "study_mode" not in st.session_state:
    st.session_state.study_mode = "Single Reactor"

if "process_type" not in st.session_state:
    st.session_state.process_type = "General Mixing"

if "scaleup_basis" not in st.session_state:
    st.session_state.scaleup_basis = "Constant P/V"


st.markdown(
    '<div class="section-header">01 · Study Configuration</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        project_name = st.text_input(
            "Project / Study Name",
            key="project_name",
            help="Engineering study or project identification.",
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

    with c4:

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


# ============================================================
# ENGINEERING FOCUS
# ============================================================

focus_parameters = [
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
    focus_parameters.append("N/Njs")

if process_type in [
    "Gas-Liquid",
    "Gas-Liquid-Solid",
]:
    focus_parameters.append("kLa")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚗️ Engineering Studio")

    st.caption(
        "Reactor mixing and scale-up screening"
    )

    st.divider()

    st.markdown("### Current Study")

    st.write(
        f"**Project:** {project_name}"
    )

    st.write(
        f"**Mode:** {study_mode}"
    )

    st.write(
        f"**Process:** {process_type}"
    )

    st.write(
        f"**Scale-Up:** {scaleup_basis}"
    )

    st.divider()

    st.markdown("### Engineering Focus")

    for item in focus_parameters:

        st.markdown(
            f"✓ {item}"
        )

    st.divider()

    st.caption(
        "Preliminary engineering screening tool. "
        "Final equipment selection requires validated "
        "process, mechanical and vendor data."
    )


# ============================================================
# REACTOR NAMES
# ============================================================

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


# ============================================================
# SESSION STATE — AGITATOR STAGE MANAGEMENT
# ============================================================

for reactor_name in reactor_names:

    state_key = (
        f"stage_ids_{reactor_name}"
    )

    if state_key not in st.session_state:

        st.session_state[state_key] = [
            create_stage_id(),
            create_stage_id(),
        ]


# Remove session state for reactors no longer active

for key in list(st.session_state.keys()):

    if key.startswith("stage_ids_"):

        reactor_name = key.replace(
            "stage_ids_",
            "",
        )

        if reactor_name not in reactor_names:

            del st.session_state[key]


# ============================================================
# DEFAULT AGITATOR HELPERS
# ============================================================

agitator_names = list(
    AGITATORS.keys()
)


def get_agitator_default(index):

    if not agitator_names:
        return None

    return agitator_names[
        min(
            index,
            len(agitator_names) - 1,
        )
    ]


def get_stage_key(
    reactor_name,
    stage_id,
    parameter,
):

    return (
        f"{reactor_name}_"
        f"stage_{stage_id}_"
        f"{parameter}"
    )


# ============================================================
# REACTOR INPUT PANEL
# ============================================================

def reactor_input_panel(name):

    st.markdown(
        f'<div class="section-header">02 · {name} Reactor Definition</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):

        # ====================================================
        # PROCESS CONDITIONS
        # ====================================================

        st.markdown(
            '<div class="subsection-header">'
            'Process Conditions'
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


        # ====================================================
        # REACTOR GEOMETRY
        # ====================================================

        st.markdown(
            '<div class="subsection-header">'
            'Vessel Geometry'
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

        head_options = [
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
                head_options,
                index=1,
                key=f"{name}_bottom",
            )

        with c4:

            top_type = st.selectbox(
                "Top Head",
                head_options,
                index=1,
                key=f"{name}_top",
            )


        # ====================================================
        # GEOMETRY CALCULATIONS
        # ====================================================

        total_volume = calculate_total_volume(
            tank_D,
            straight_H,
            bottom_type,
            top_type,
        )

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

        fill = calculate_fill_percent(
            working_volume,
            total_volume,
        )

        ht_ratio = safe_ratio(
            liquid_height,
            tank_D,
        )


        # ====================================================
        # GEOMETRY KPI
        # ====================================================

        k1, k2, k3, k4 = st.columns(4)

        with k1:

            st.metric(
                "Calculated Vessel Volume",
                f"{total_volume:.2f} m³",
            )

        with k2:

            st.metric(
                "Liquid Height",
                f"{liquid_height:.2f} m",
            )

        with k3:

            st.metric(
                "Operating Fill",
                f"{fill:.1f} %",
            )

        with k4:

            st.metric(
                "H/T",
                (
                    f"{ht_ratio:.2f}"
                    if ht_ratio is not None
                    else "N/A"
                ),
            )

        if working_volume > total_volume:

            st.error(
                "Working volume exceeds calculated vessel capacity. "
                "Please review reactor geometry."
            )


        # ====================================================
        # VESSEL INTERNALS
        # ====================================================

        st.markdown(
            '<div class="subsection-header">'
            'Vessel Internals'
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


        # ====================================================
        # AGITATOR TRAIN
        # ====================================================

        st.markdown(
            '<div class="subsection-header">'
            'Agitator Train'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="info-note">
            Each impeller is treated as an independent stage.
            Use <b>Add Agitator Stage</b> to create another impeller
            and <b>Remove</b> to delete an existing stage.
            Stage settings are retained when the train is modified.
            </div>
            """,
            unsafe_allow_html=True,
        )

        stage_state_key = (
            f"stage_ids_{name}"
        )

        stage_ids = st.session_state[
            stage_state_key
        ]


        # ----------------------------------------------------
        # ADD / REMOVE CONTROLS
        # ----------------------------------------------------

        add_col, spacer, count_col = st.columns(
            [1.5, 5, 1.5]
        )

        with add_col:

            if st.button(
                "＋ Add Agitator Stage",
                key=f"{name}_add_stage",
                use_container_width=True,
            ):

                if len(stage_ids) < 8:

                    stage_ids.append(
                        create_stage_id()
                    )

                    st.session_state[
                        stage_state_key
                    ] = stage_ids

                    st.rerun()

                else:

                    st.warning(
                        "Maximum 8 agitator stages allowed."
                    )

        with count_col:

            st.metric(
                "Stages",
                len(stage_ids),
            )


        # ----------------------------------------------------
        # STAGE CONFIGURATION
        # ----------------------------------------------------

        stages = []

        for stage_index, stage_id in enumerate(
            stage_ids
        ):

            default_agitator = (
                get_agitator_default(
                    stage_index
                )
            )

            default_spec = (
                AGITATORS[
                    default_agitator
                ]
                if default_agitator
                else {}
            )


            with st.expander(
                f"Stage {stage_index + 1}  ·  "
                f"{default_agitator or 'Agitator'}",
                expanded=True,
            ):

                # --------------------------------------------
                # STAGE HEADER
                # --------------------------------------------

                header_col, remove_col = st.columns(
                    [8, 1]
                )

                with header_col:

                    st.markdown(
                        f"""
                        <div class="agitator-stage-title">
                            Agitator Stage {stage_index + 1}
                        </div>

                        <div class="agitator-stage-subtitle">
                            Independent impeller configuration
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with remove_col:

                    if st.button(
                        "✕",
                        key=f"{name}_remove_{stage_id}",
                        help="Remove this agitator stage",
                        use_container_width=True,
                    ):

                        if len(stage_ids) > 1:

                            stage_ids.remove(
                                stage_id
                            )

                            st.session_state[
                                stage_state_key
                            ] = stage_ids

                            st.rerun()

                        else:

                            st.warning(
                                "At least one agitator stage is required."
                            )


                # --------------------------------------------
                # BASIC AGITATOR PARAMETERS
                # --------------------------------------------

                c1, c2, c3, c4 = st.columns(4)

                with c1:

                    agitator_name = st.selectbox(
                        "Agitator Type",
                        agitator_names,
                        index=(
                            agitator_names.index(
                                default_agitator
                            )
                            if default_agitator
                            in agitator_names
                            else 0
                        ),
                        key=get_stage_key(
                            name,
                            stage_id,
                            "agitator",
                        ),
                    )

                spec = AGITATORS[
                    agitator_name
                ]

                with c2:

                    ratio = st.number_input(
                        "D/T Ratio",
                        min_value=0.05,
                        max_value=0.95,
                        value=float(
                            spec.get(
                                "D_T",
                                0.35,
                            )
                        ),
                        step=0.01,
                        key=get_stage_key(
                            name,
                            stage_id,
                            "DT",
                        ),
                    )

                with c3:

                    rpm = st.number_input(
                        "Operating RPM",
                        min_value=0.1,
                        max_value=1500.0,
                        value=115.0,
                        step=1.0,
                        key=get_stage_key(
                            name,
                            stage_id,
                            "rpm",
                        ),
                    )

                with c4:

                    blades = st.number_input(
                        "Number of Blades",
                        min_value=1,
                        max_value=20,
                        value=int(
                            spec.get(
                                "blades",
                                4,
                            )
                        ),
                        step=1,
                        key=get_stage_key(
                            name,
                            stage_id,
                            "blades",
                        ),
                    )


                # --------------------------------------------
                # IMPELLER POSITION
                # --------------------------------------------

                st.markdown(
                    "**Impeller Position & Geometry**"
                )

                c1, c2, c3 = st.columns(3)

                impeller_D = (
                    tank_D * ratio
                )

                with c1:

                    st.number_input(
                        "Calculated Impeller Diameter (m)",
                        value=float(
                            impeller_D
                        ),
                        disabled=True,
                        key=get_stage_key(
                            name,
                            stage_id,
                            "diameter_display",
                        ),
                    )

                with c2:

                    clearance = st.number_input(
                        "Bottom Clearance C (m)",
                        min_value=0.001,
                        max_value=max(
                            tank_D,
                            0.1,
                        ),
                        value=max(
                            0.15 * tank_D,
                            0.02,
                        ),
                        step=0.01,
                        key=get_stage_key(
                            name,
                            stage_id,
                            "clearance",
                        ),
                    )

                with c3:

                    default_elevation = min(
                        straight_H
                        * (
                            0.25
                            + stage_index
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
                        value=float(
                            default_elevation
                        ),
                        step=0.01,
                        key=get_stage_key(
                            name,
                            stage_id,
                            "elevation",
                        ),
                    )


                # --------------------------------------------
                # POWER / FLOW PARAMETERS
                # --------------------------------------------

                st.markdown(
                    "**Hydrodynamic Correlation**"
                )

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.write(
                        f"**Np:** "
                        f"{fmt(spec.get('Np'), 4)}"
                    )

                    st.write(
                        f"**Nq:** "
                        f"{fmt(spec.get('Nq'), 4)}"
                    )

                with c2:

                    use_override = st.checkbox(
                        "Override Np / Nq",
                        value=False,
                        key=get_stage_key(
                            name,
                            stage_id,
                            "override",
                        ),
                    )

                np_value = spec.get(
                    "Np"
                )

                nq_value = spec.get(
                    "Nq"
                )

                if use_override:

                    with c2:

                        np_value = st.number_input(
                            "Power Number Np",
                            min_value=0.001,
                            max_value=50.0,
                            value=float(
                                spec.get(
                                    "Np"
                                    or 1.0
                                )
                            ),
                            step=0.05,
                            key=get_stage_key(
                                name,
                                stage_id,
                                "Np",
                            ),
                        )

                    with c3:

                        nq_value = st.number_input(
                            "Flow Number Nq",
                            min_value=0.001,
                            max_value=10.0,
                            value=float(
                                spec.get(
                                    "Nq"
                                    or 0.5
                                )
                            ),
                            step=0.05,
                            key=get_stage_key(
                                name,
                                stage_id,
                                "Nq",
                            ),
                        )

                else:

                    with c3:

                        st.write(
                            f"**Correlation:** "
                            f"Np = {fmt(np_value, 4)}  |  "
                            f"Nq = {fmt(nq_value, 4)}"
                        )


                if np_value is None:

                    st.warning(
                        "Np is unavailable for this agitator. "
                        "Enter validated vendor/literature data."
                    )

                if nq_value is None:

                    st.warning(
                        "Nq is unavailable for this agitator. "
                        "Enter validated vendor/literature data."
                    )


                # --------------------------------------------
                # DESCRIPTION
                # --------------------------------------------

                description = spec.get(
                    "description_short",
                    "",
                )

                if description:

                    st.caption(
                        description
                    )


                # --------------------------------------------
                # APPEND STAGE
                # --------------------------------------------

                stages.append(
                    {
                        "stage": stage_index + 1,

                        "agitator":
                            agitator_name,

                        "Np":
                            np_value,

                        "Nq":
                            nq_value,

                        "impeller_diameter_m":
                            impeller_D,

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


        # ====================================================
        # SOLIDS SUSPENSION
        # ====================================================

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

            st.markdown(
                '<div class="subsection-header">'
                'Solids Suspension Basis'
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


        # ====================================================
        # RETURN
        # ====================================================

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


# ============================================================
# COLLECT REACTOR DATA
# ============================================================

reactors = []

for reactor_name in reactor_names:

    reactor = reactor_input_panel(
        reactor_name
    )

    reactors.append(
        reactor
    )


# ============================================================
# CALCULATE ALL REACTORS
# ============================================================

for reactor in reactors:

    try:

        results, train = calculate_train(
            reactor["stages"],
            reactor["working_volume_m3"],
        )

    except Exception as exc:

        st.error(
            f"Calculation error for "
            f"{reactor['name']} reactor: {exc}"
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


    # ========================================================
    # NJS
    # ========================================================

    if process_type in [
        "Solid-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
    ]:

        solids = reactor[
            "solids"
        ]

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
                    solids["S"],
                )

            except Exception:

                njs = None


            stage["njs_rpm"] = njs

            if njs and njs > 0:

                stage["Njs_RPM"] = njs

                stage["N_over_Njs"] = (
                    stage["rpm"]
                    / njs
                )

            else:

                stage["N_over_Njs"] = None


    reactor["results"] = results

    reactor["train"] = train


    # ========================================================
    # GEOMETRY DICTIONARY
    # ========================================================

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


    # ========================================================
    # VALIDATION
    # ========================================================

    try:

        reactor["checks"] = validate_design(
            geometry,
            results,
            process_type,
        )

    except Exception as exc:

        reactor["checks"] = [
            {
                "severity":
                    "REVIEW",

                "message":
                    f"Validation calculation error: {exc}",
            }
        ]


    try:

        reactor["status"] = overall_status(
            reactor["checks"]
        )

    except Exception:

        reactor["status"] = "REVIEW"


    try:

        reactor["recommendations"] = recommendations(
            process_type,
            train,
        )

    except Exception as exc:

        reactor["recommendations"] = [
            f"Recommendation engine unavailable: {exc}"
        ]


# ============================================================
# ACTIVE REACTOR
# ============================================================

active_reactor = reactors[-1]

active_train = active_reactor[
    "train"
]

active_status = active_reactor[
    "status"
]


# ============================================================
# ENGINEERING KPI OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-header">'
    '03 · Engineering Performance Overview'
    '</div>',
    unsafe_allow_html=True,
)

kpis = [

    (
        "Working Volume",
        fmt(
            active_reactor[
                "working_volume_m3"
            ],
            2,
        ),
        "m³",
    ),

    (
        "Operating Fill",
        fmt(
            active_reactor[
                "fill_percent"
            ],
            1,
        ),
        "%",
    ),

    (
        "Shaft Power",
        fmt(
            active_train.get(
                "total_power_kw"
            ),
            2,
        ),
        "kW",
    ),

    (
        "Power Density",
        fmt(
            active_train.get(
                "P_per_V_kW_m3"
            ),
            3,
        ),
        "kW/m³",
    ),

    (
        "Total Q",
        fmt(
            active_train.get(
                "total_Q_m3_h"
            ),
            1,
        ),
        "m³/h",
    ),

    (
        "Q/V",
        fmt(
            active_train.get(
                "Q_per_volume_1_s"
            ),
            4,
        ),
        "s⁻¹",
    ),

    (
        "Maximum Re",
        (
            f"{active_train.get('maximum_reynolds'):,.0f}"
            if active_train.get(
                "maximum_reynolds"
            )
            else "N/A"
        ),
        "",
    ),

    (
        "Design Status",
        str(active_status),
        "screening",
    ),
]


kpi_columns = st.columns(
    len(kpis)
)

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
            <div class="metric-card">

                <div class="metric-label">
                    {label}
                </div>

                <div class="metric-value">
                    {value}
                </div>

                <div class="metric-unit">
                    {unit}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN TABS
# ============================================================

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
        "Mixing Performance",
        "Scale-Up",
        "Validation",
        "3D Mixing",
        "Engineering Report",
    ]
)


# ============================================================
# DESIGN BASIS
# ============================================================

with tab_basis:

    st.markdown(
        "## Process & Scale-Up Design Basis"
    )

    guidance = {

        "General Mixing":
            "Primary: Q/V and blend time. Secondary: P/V and Reynolds number.",

        "Liquid-Liquid":
            "Prioritize bulk circulation, phase contact, dispersion and blend time.",

        "Solid-Liquid":
            "Primary criterion: N/Njs. Secondary: P/V, Q/V and impeller clearance.",

        "Gas-Liquid":
            "Prioritize gas dispersion, gas-liquid contacting and kLa.",

        "Gas-Liquid-Solid":
            "Solids suspension and gas dispersion must be evaluated simultaneously.",

        "Crystallization":
            "Balance suspension quality, circulation, shear and crystal attrition.",

        "High-Viscosity":
            "Prioritize torque, P/V, Reynolds number and mechanical loading.",

        "Heat-Controlled Reaction":
            "Mixing performance and heat-transfer capacity must both be demonstrated.",
    }

    scaleup_description = {

        "Constant P/V":
            "Maintains power density and is widely used when energy intensity is the governing similarity parameter.",

        "Constant Tip Speed":
            "Maintains impeller peripheral velocity and can be useful where local shear is important.",

        "Constant Q/V":
            "Maintains circulation or turnover intensity.",

        "Constant RPM":
            "Provides direct mechanical speed comparison but is not generally a universal mixing similarity criterion.",

        "Constant Froude Number":
            "Maintains inertial/gravity similarity.",

        "Constant Reynolds Number":
            "Maintains viscous/inertial similarity.",
    }

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            "### Process Requirement"
        )

        st.info(
            guidance[
                process_type
            ]
        )

    with c2:

        st.markdown(
            "### Primary Scale-Up Criterion"
        )

        st.info(
            scaleup_description[
                scaleup_basis
            ]
        )


    st.markdown(
        "### Engineering Governance"
    )

    st.markdown(
        """
        <div class="engineering-note">

        <b>Engineering principle:</b>

        RPM alone should not be treated as a universal scale-up
        criterion. The selected scale-up basis should be reconciled
        against functional performance including P/V, Q/V, tip speed,
        Reynolds number, solids suspension, gas dispersion, blend time,
        heat transfer and mechanical loading.

        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        "### Study Scope"
    )

    scope_df = pd.DataFrame(
        {
            "Parameter": [
                "Project",
                "Study Mode",
                "Process Requirement",
                "Primary Scale-Up Basis",
                "Engineering Focus",
            ],

            "Selected Value": [
                project_name,
                study_mode,
                process_type,
                scaleup_basis,
                ", ".join(
                    focus_parameters
                ),
            ],
        }
    )

    st.dataframe(
        scope_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# REACTOR GEOMETRY TAB
# ============================================================

with tab_geometry:

    st.markdown(
        "## Reactor Geometry Comparison"
    )

    geometry_rows = []

    for reactor in reactors:

        geometry_rows.append(
            {
                "Reactor":
                    reactor["name"],

                "Working Volume (m³)":
                    reactor[
                        "working_volume_m3"
                    ],

                "Vessel Volume (m³)":
                    reactor[
                        "total_volume_m3"
                    ],

                "Tank ID (m)":
                    reactor[
                        "tank_diameter_m"
                    ],

                "Straight Side (m)":
                    reactor[
                        "straight_height_m"
                    ],

                "Liquid Height (m)":
                    reactor[
                        "liquid_height_m"
                    ],

                "Fill (%)":
                    reactor[
                        "fill_percent"
                    ],

                "H/T":
                    safe_ratio(
                        reactor[
                            "liquid_height_m"
                        ],
                        reactor[
                            "tank_diameter_m"
                        ],
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
        use_container_width=True,
        hide_index=True,
    )


    st.markdown(
        "### Geometry Review"
    )

    for reactor in reactors:

        with st.container(border=True):

            st.markdown(
                f"### ⚗️ {reactor['name']} Reactor"
            )

            c1, c2, c3, c4, c5 = st.columns(5)

            with c1:

                st.metric(
                    "Tank Diameter",
                    f"{reactor['tank_diameter_m']:.3f} m",
                )

            with c2:

                st.metric(
                    "Straight Side",
                    f"{reactor['straight_height_m']:.3f} m",
                )

            with c3:

                st.metric(
                    "Liquid Height",
                    f"{reactor['liquid_height_m']:.3f} m",
                )

            with c4:

                st.metric(
                    "Vessel Volume",
                    f"{reactor['total_volume_m3']:.2f} m³",
                )

            with c5:

                st.metric(
                    "Fill",
                    f"{reactor['fill_percent']:.1f} %",
                )


# ============================================================
# AGITATOR TRAIN TAB
# ============================================================

with tab_agitator:

    st.markdown(
        "## Independent Agitator Train"
    )

    st.markdown(
        """
        <div class="info-note">

        <b>Train philosophy:</b>
        Each impeller is independently configured for type,
        D/T ratio, RPM, elevation, clearance and hydrodynamic
        correlation. This allows multi-impeller reactors to be
        evaluated without forcing all impellers to use the same
        operating parameters.

        </div>
        """,
        unsafe_allow_html=True,
    )


    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        rows = []

        for stage in reactor[
            "results"
        ]:

            njs = stage.get(
                "njs_rpm"
            )

            n_over_njs = (
                stage.get(
                    "N_over_Njs"
                )
            )

            rows.append(
                {
                    "Stage":
                        stage.get(
                            "stage"
                        ),

                    "Agitator":
                        stage.get(
                            "agitator"
                        ),

                    "D (m)":
                        stage.get(
                            "impeller_diameter_m"
                        ),

                    "D/T":
                        stage.get(
                            "D_T"
                        ),

                    "RPM":
                        stage.get(
                            "rpm"
                        ),

                    "Clearance (m)":
                        stage.get(
                            "clearance_m"
                        ),

                    "Elevation (m)":
                        stage.get(
                            "elevation_m"
                        ),

                    "Blades":
                        stage.get(
                            "blades"
                        ),

                    "Np":
                        stage.get(
                            "Np"
                        ),

                    "Nq":
                        stage.get(
                            "Nq"
                        ),

                    "Re":
                        stage.get(
                            "Re"
                        ),

                    "Power (kW)":
                        stage.get(
                            "power_kw"
                        ),

                    "Power (HP)":
                        stage.get(
                            "power_hp"
                        ),

                    "Q (m³/h)":
                        stage.get(
                            "Q_m3_h"
                        ),

                    "P/V":
                        stage.get(
                            "power_per_volume_kw_m3"
                        ),

                    "Tip Speed (m/s)":
                        stage.get(
                            "tip_speed_m_s"
                        ),

                    "Torque (N·m)":
                        stage.get(
                            "torque_Nm"
                        ),

                    "Njs (RPM)":
                        njs,

                    "N/Njs":
                        n_over_njs,
                }
            )


        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.warning(
                "No agitator calculation results available."
            )


# ============================================================
# PERFORMANCE TAB
# ============================================================

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

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        with c1:

            st.metric(
                "Total Power",
                f"{fmt(train.get('total_power_kw'), 2)} kW",
            )

        with c2:

            st.metric(
                "P/V",
                f"{fmt(train.get('P_per_V_kW_m3'), 3)} kW/m³",
            )

        with c3:

            st.metric(
                "Total Q",
                f"{fmt(train.get('total_Q_m3_h'), 1)} m³/h",
            )

        with c4:

            st.metric(
                "Q/V",
                f"{fmt(train.get('Q_per_volume_1_s'), 4)} s⁻¹",
            )

        with c5:

            turnover = train.get(
                "turnover_time_min"
            )

            st.metric(
                "Turnover Time",
                (
                    f"{turnover:.3f} min"
                    if turnover
                    else "N/A"
                ),
            )

        with c6:

            st.metric(
                "Total Torque",
                f"{fmt(train.get('total_torque_Nm'), 1)} N·m",
            )


        performance_rows = []

        for stage in reactor[
            "results"
        ]:

            performance_rows.append(
                {
                    "Stage":
                        stage.get("stage"),

                    "Agitator":
                        stage.get("agitator"),

                    "Regime":
                        stage.get(
                            "mixing_regime"
                        ),

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

                    "Q (m³/h)":
                        stage.get(
                            "Q_m3_h"
                        ),

                    "Torque (N·m)":
                        stage.get(
                            "torque_Nm"
                        ),
                }
            )


        if performance_rows:

            st.dataframe(
                pd.DataFrame(
                    performance_rows
                ),
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# SCALE-UP TAB
# ============================================================

with tab_scaleup:

    st.markdown(
        "## Reactor Scale-Up Evaluation"
    )

    if len(reactors) < 2:

        st.info(
            "Select a comparison study mode in Study Configuration "
            "to activate the scale-up evaluation."
        )

    else:

        reference = reactors[0]

        target = reactors[-1]

        st.markdown(
            f"### {reference['name']} → {target['name']}"
        )

        volume_factor = safe_ratio(
            target[
                "working_volume_m3"
            ],
            reference[
                "working_volume_m3"
            ],
        )

        diameter_ratio = safe_ratio(
            target[
                "tank_diameter_m"
            ],
            reference[
                "tank_diameter_m"
            ],
        )

        pv_ratio = safe_ratio(
            target["train"].get(
                "P_per_V_kW_m3"
            ),
            reference["train"].get(
                "P_per_V_kW_m3"
            ),
        )

        qv_ratio = safe_ratio(
            target["train"].get(
                "Q_per_volume_1_s"
            ),
            reference["train"].get(
                "Q_per_volume_1_s"
            ),
        )


        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "Volume Scale Factor",
                (
                    f"{volume_factor:.2f}"
                    if volume_factor
                    is not None
                    else "N/A"
                ),
            )

        with c2:

            st.metric(
                "Tank Diameter Ratio",
                (
                    f"{diameter_ratio:.2f}"
                    if diameter_ratio
                    is not None
                    else "N/A"
                ),
            )

        with c3:

            st.metric(
                "P/V Ratio",
                (
                    f"{pv_ratio:.3f}"
                    if pv_ratio
                    is not None
                    else "N/A"
                ),
            )

        with c4:

            st.metric(
                "Q/V Ratio",
                (
                    f"{qv_ratio:.3f}"
                    if qv_ratio
                    is not None
                    else "N/A"
                ),
            )


        # ====================================================
        # SCALE-UP CALCULATION
        # ====================================================

        st.markdown(
            "### Primary Criterion Calculation"
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
                    ref_stage.get(
                        "rpm"
                    ),

                "impeller_diameter_m":
                    ref_stage.get(
                        "impeller_diameter_m"
                    ),

                "volume_m3":
                    reference[
                        "working_volume_m3"
                    ],
            }


            target_basis = {

                "impeller_diameter_m":
                    target_stage.get(
                        "impeller_diameter_m"
                    ),

                "volume_m3":
                    target[
                        "working_volume_m3"
                    ],
            }


            try:

                scale_result = calculate_scaleup(
                    reference_basis,
                    target_basis,
                    scaleup_basis,
                )

                target_rpm = scale_result.get(
                    "target_rpm"
                )

                target_tip = scale_result.get(
                    "target_tip_speed"
                )

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.metric(
                        "Scale-Up Criterion",
                        scaleup_basis,
                    )

                with c2:

                    st.metric(
                        "Calculated Target RPM",
                        (
                            f"{target_rpm:.1f} RPM"
                            if target_rpm
                            is not None
                            else "N/A"
                        ),
                    )

                with c3:

                    st.metric(
                        "Corresponding Tip Speed",
                        (
                            f"{target_tip:.2f} m/s"
                            if target_tip
                            is not None
                            else "N/A"
                        ),
                    )


            except Exception as exc:

                st.error(
                    f"Scale-up calculation error: {exc}"
                )


        else:

            st.warning(
                "Reference or target agitator results are unavailable."
            )


        # ====================================================
        # COMPARISON TABLE
        # ====================================================

        st.markdown(
            "### Reference vs Target Comparison"
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
                    reference["train"].get(
                        "total_power_kw"
                    ),

                target["name"]:
                    target["train"].get(
                        "total_power_kw"
                    ),
            },

            {
                "Parameter":
                    "P/V",

                "Unit":
                    "kW/m³",

                reference["name"]:
                    reference["train"].get(
                        "P_per_V_kW_m3"
                    ),

                target["name"]:
                    target["train"].get(
                        "P_per_V_kW_m3"
                    ),
            },

            {
                "Parameter":
                    "Total Q",

                "Unit":
                    "m³/h",

                reference["name"]:
                    reference["train"].get(
                        "total_Q_m3_h"
                    ),

                target["name"]:
                    target["train"].get(
                        "total_Q_m3_h"
                    ),
            },

            {
                "Parameter":
                    "Q/V",

                "Unit":
                    "s⁻¹",

                reference["name"]:
                    reference["train"].get(
                        "Q_per_volume_1_s"
                    ),

                target["name"]:
                    target["train"].get(
                        "Q_per_volume_1_s"
                    ),
            },

            {
                "Parameter":
                    "Average Tip Speed",

                "Unit":
                    "m/s",

                reference["name"]:
                    reference["train"].get(
                        "average_tip_speed_m_s"
                    ),

                target["name"]:
                    target["train"].get(
                        "average_tip_speed_m_s"
                    ),
            },

            {
                "Parameter":
                    "Maximum Re",

                "Unit":
                    "-",

                reference["name"]:
                    reference["train"].get(
                        "maximum_reynolds"
                    ),

                target["name"]:
                    target["train"].get(
                        "maximum_reynolds"
                    ),
            },
        ]


        st.dataframe(
            pd.DataFrame(
                comparison_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


        st.markdown(
            """
            <div class="engineering-note">

            <b>Scale-up governance:</b>
            Calculated target RPM is a starting-point engineering
            value. Final selection should reconcile P/V, Q/V,
            tip speed, Reynolds number, N/Njs, blend time,
            gas dispersion, heat-transfer requirements,
            motor/gearbox torque and vendor recommendations.

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# VALIDATION TAB
# ============================================================

with tab_validation:

    st.markdown(
        "## Engineering Validation"
    )

    if active_status == "PASS":

        st.markdown(
            '<div class="status-pass">'
            '✓ Overall Screening Status: PASS'
            '</div>',
            unsafe_allow_html=True,
        )

    elif active_status == "REVIEW":

        st.markdown(
            '<div class="status-review">'
            '⚠ Overall Screening Status: REVIEW'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            '<div class="status-fail">'
            '✕ Overall Screening Status: FAIL'
            '</div>',
            unsafe_allow_html=True,
        )


    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        checks = reactor[
            "checks"
        ]

        status_counts = {

            "PASS":
                sum(
                    x.get("severity")
                    == "PASS"
                    for x in checks
                ),

            "REVIEW":
                sum(
                    x.get("severity")
                    == "REVIEW"
                    for x in checks
                ),

            "FAIL":
                sum(
                    x.get("severity")
                    == "FAIL"
                    for x in checks
                ),
        }


        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "PASS",
                status_counts[
                    "PASS"
                ],
            )

        with c2:

            st.metric(
                "REVIEW",
                status_counts[
                    "REVIEW"
                ],
            )

        with c3:

            st.metric(
                "FAIL",
                status_counts[
                    "FAIL"
                ],
            )


        validation_df = pd.DataFrame(
            [
                {
                    "Status":
                        x.get(
                            "severity"
                        ),

                    "Engineering Check":
                        x.get(
                            "message"
                        ),
                }

                for x in checks
            ]
        )


        if not validation_df.empty:

            st.dataframe(
                validation_df,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# 3D VISUALIZATION TAB
# ============================================================

with tab_3d:

    st.markdown(
        "## 3D Reactor & Mixing Visualization"
    )

    selected_name = st.selectbox(
        "Select Reactor",
        [
            x["name"]
            for x in reactors
        ],
        key="selected_3d_reactor",
    )


    selected = next(
        x
        for x in reactors
        if x["name"]
        == selected_name
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
            use_container_width=True,
            config={
                "displayModeBar":
                    True,

                "scrollZoom":
                    True,

                "displaylogo":
                    False,
            },
        )


    except Exception as exc:

        st.error(
            f"3D visualization error: {exc}"
        )


    st.markdown(
        """
        <div class="info-note">

        <b>Visualization scope:</b>
        The 3D model represents vessel geometry, heads,
        liquid level, baffles, impeller arrangement and
        conceptual mixing/circulation features.

        It is not a CFD solution and does not represent
        validated velocity, pressure, turbulence,
        species-concentration or temperature fields.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# ENGINEERING REPORT TAB
# ============================================================

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

            label=
                "📄 Download Engineering PDF",

            data=
                pdf_bytes,

            file_name=
                "reactor_scaleup_engineering_report.pdf",

            mime=
                "application/pdf",

            use_container_width=
                True,
        )


    except Exception as exc:

        st.error(
            f"Unable to generate engineering report: {exc}"
        )


    st.markdown(
        "### Engineering Recommendation"
    )


    for item in selected[
        "recommendations"
    ]:

        st.info(
            item
        )


# ============================================================
# FINAL DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "Preliminary engineering screening tool. "
    "Np/Nq values are representative unless overridden "
    "with validated vendor or literature data. Njs, blend "
    "time, kLa and heat-transfer calculations require "
    "system-specific validation. Final equipment selection "
    "must include vendor data, pilot/plant validation, "
    "mechanical design, process safety and applicable "
    "engineering standards."
)
