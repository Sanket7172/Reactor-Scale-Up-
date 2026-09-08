```python
import math
import pandas as pd
import streamlit as st

# =========================================================
# APPLICATION MODULES
# =========================================================

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

    /* -----------------------------
       APPLICATION BACKGROUND
    ----------------------------- */

    .stApp {
        background-color: #f5f7fa;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    /* -----------------------------
       SIDEBAR
    ----------------------------- */

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    [data-testid="stSidebar"] * {
        color: #f3f4f6;
    }

    /* -----------------------------
       MAIN HEADER
    ----------------------------- */

    .app-header {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #1e3a5f 100%
        );

        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 22px;

        box-shadow:
            0 6px 18px rgba(15, 23, 42, 0.12);
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

    /* -----------------------------
       SECTION HEADERS
    ----------------------------- */

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

    /* -----------------------------
       CONFIGURATION CARD
    ----------------------------- */

    .config-card {
        background: white;
        border: 1px solid #dce3ec;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 18px;

        box-shadow:
            0 2px 8px rgba(15, 23, 42, 0.04);
    }

    /* -----------------------------
       KPI CARDS
    ----------------------------- */

    .kpi-card {
        background: white;
        border: 1px solid #dce3ec;
        border-radius: 12px;
        padding: 15px 16px;
        min-height: 98px;

        box-shadow:
            0 2px 8px rgba(15, 23, 42, 0.04);
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

    /* -----------------------------
       AGITATOR CARD
    ----------------------------- */

    .agitator-card {
        background: white;
        border: 1px solid #d7dee8;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;

        box-shadow:
            0 2px 7px rgba(15, 23, 42, 0.035);
    }

    .agitator-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e293b;
    }

    .agitator-description {
        color: #64748b;
        font-size: 12px;
    }

    /* -----------------------------
       ENGINEERING NOTE
    ----------------------------- */

    .engineering-note {
        background: #fff8e7;
        border: 1px solid #ead9a5;
        border-radius: 10px;
        padding: 13px 16px;
        color: #624d16;
        font-size: 13px;
        line-height: 1.55;
    }

    /* -----------------------------
       STATUS
    ----------------------------- */

    .status-pass {
        color: #166534;
        font-weight: 700;
    }

    .status-review {
        color: #92400e;
        font-weight: 700;
    }

    .status-fail {
        color: #991b1b;
        font-weight: 700;
    }

    /* -----------------------------
       BUTTONS
    ----------------------------- */

    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# APPLICATION HEADER
# =========================================================

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


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ⚗️ Engineering Studio")

    st.markdown("---")

    st.markdown("### Application Modules")

    st.markdown(
        """
        **Study Configuration**

        Define process and scale-up basis.

        **Reactor Design**

        Define vessel geometry and internals.

        **Agitator Train**

        Configure independent impellers.

        **Performance**

        Review P/V, Q/V, Re, torque and power.

        **Scale-Up**

        Compare laboratory, pilot and commercial systems.

        **Validation**

        Review engineering checks.

        **3D Mixing**

        Visualize reactor and agitator arrangement.

        **Engineering Report**

        Generate the preliminary engineering report.
        """
    )

    st.markdown("---")

    st.caption(
        "Preliminary engineering screening tool. "
        "Final equipment selection requires validated "
        "process, vendor and mechanical design data."
    )


# =========================================================
# STUDY CONFIGURATION
# =========================================================

st.markdown(
    '<div class="section-header">Study Configuration</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):

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

        st.markdown("**Engineering Focus**")

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

        st.write(" • ".join(focus_items))


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
# AGITATOR STATE MANAGEMENT
# =========================================================

def initialize_agitators(reactor_name):

    state_key = f"{reactor_name}_agitator_ids"

    if state_key not in st.session_state:

        st.session_state[state_key] = [
            1,
            2,
        ]


def add_agitator(reactor_name):

    state_key = f"{reactor_name}_agitator_ids"

    initialize_agitators(reactor_name)

    current_ids = st.session_state[state_key]

    new_id = (
        max(current_ids) + 1
        if current_ids
        else 1
    )

    st.session_state[state_key].append(
        new_id
    )


def remove_agitator(
    reactor_name,
    agitator_id,
):

    state_key = f"{reactor_name}_agitator_ids"

    initialize_agitators(reactor_name)

    current_ids = st.session_state[state_key]

    if len(current_ids) <= 1:
        return

    st.session_state[state_key] = [
        x
        for x in current_ids
        if x != agitator_id
    ]


# =========================================================
# SAFE AGITATOR VALUE HELPERS
# =========================================================

def safe_float(
    value,
    default=0.0,
):

    try:

        if value is None:
            return default

        return float(value)

    except Exception:

        return default


def safe_int(
    value,
    default=1,
):

    try:

        if value is None:
            return default

        return int(value)

    except Exception:

        return default


# =========================================================
# REACTOR INPUT PANEL
# =========================================================

def reactor_input_panel(name):

    st.markdown(
        f'<div class="section-header">⚗️ {name} Reactor</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # PROCESS CONDITIONS
    # -----------------------------------------------------

    with st.container(border=True):

        st.markdown(
            '<div class="subsection-header">1. Process Conditions</div>',
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

    # -----------------------------------------------------
    # REACTOR GEOMETRY
    # -----------------------------------------------------

    with st.container(border=True):

        st.markdown(
            '<div class="subsection-header">2. Reactor Geometry</div>',
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
            "Calculated Vessel Volume",
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

    # -----------------------------------------------------
    # VESSEL INTERNALS
    # -----------------------------------------------------

    with st.container(border=True):

        st.markdown(
            '<div class="subsection-header">3. Vessel Internals</div>',
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

    # -----------------------------------------------------
    # AGITATOR TRAIN
    # -----------------------------------------------------

    initialize_agitators(name)

    agitator_ids = st.session_state[
        f"{name}_agitator_ids"
    ]

    with st.container(border=True):

        st.markdown(
            '<div class="subsection-header">4. Agitator Train</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Each agitator is configured independently. "
            "Use Add Agitator / Remove to define the shaft arrangement."
        )

        # -----------------------------------------------
        # ADD / REMOVE
        # -----------------------------------------------

        c1, c2, c3 = st.columns(
            [2, 2, 6]
        )

        with c1:

            st.button(
                "＋ Add Agitator",
                key=f"{name}_add_agitator",
                use_container_width=True,
                on_click=add_agitator,
                args=(name,),
            )

        with c2:

            if len(agitator_ids) > 1:

                last_id = agitator_ids[-1]

                st.button(
                    "− Remove Last",
                    key=f"{name}_remove_last",
                    use_container_width=True,
                    on_click=remove_agitator,
                    args=(
                        name,
                        last_id,
                    ),
                )

        with c3:

            st.markdown(
                f"**Current agitators: {len(agitator_ids)}**"
            )

        stages = []

        # -----------------------------------------------
        # AGITATOR CARDS
        # -----------------------------------------------

        for stage_number, agitator_id in enumerate(
            agitator_ids,
            start=1,
        ):

            spec_default = list(
                AGITATORS.keys()
            )[0]

            with st.container(border=True):

                c1, c2 = st.columns(
                    [8, 1]
                )

                with c1:

                    st.markdown(
                        f"**Agitator {stage_number}**"
                    )

                with c2:

                    if len(agitator_ids) > 1:

                        st.button(
                            "✕",
                            key=(
                                f"{name}_remove_{agitator_id}"
                            ),
                            help=(
                                "Remove this agitator"
                            ),
                            on_click=remove_agitator,
                            args=(
                                name,
                                agitator_id,
                            ),
                        )

                # ---------------------------------------
                # AGITATOR TYPE
                # ---------------------------------------

                agitator_key = (
                    f"{name}_agitator_type_{agitator_id}"
                )

                if (
                    agitator_key
                    not in st.session_state
                ):

                    st.session_state[
                        agitator_key
                    ] = spec_default

                selected_agitator = st.selectbox(
                    "Agitator Type",
                    list(AGITATORS.keys()),
                    key=agitator_key,
                )

                spec = AGITATORS[
                    selected_agitator
                ]

                st.caption(
                    spec.get(
                        "description_short",
                        "Agitator geometry",
                    )
                )

                # ---------------------------------------
                # MAIN PARAMETERS
                # ---------------------------------------

                c1, c2, c3, c4 = st.columns(4)

                default_DT = safe_float(
                    spec.get(
                        "D_T",
                        0.4,
                    ),
                    0.4,
                )

                with c1:

                    ratio = st.number_input(
                        "D/T Ratio",
                        min_value=0.05,
                        max_value=0.95,
                        value=default_DT,
                        step=0.01,
                        key=(
                            f"{name}_DT_{agitator_id}"
                        ),
                    )

                with c2:

                    rpm = st.number_input(
                        "RPM",
                        min_value=0.1,
                        max_value=1500.0,
                        value=115.0,
                        step=1.0,
                        key=(
                            f"{name}_rpm_{agitator_id}"
                        ),
                    )

                with c3:

                    default_clearance = max(
                        0.15 * tank_D,
                        0.02,
                    )

                    clearance = st.number_input(
                        "Bottom Clearance (m)",
                        min_value=0.001,
                        max_value=max(
                            tank_D,
                            0.1,
                        ),
                        value=min(
                            default_clearance,
                            tank_D,
                        ),
                        step=0.01,
                        key=(
                            f"{name}_clearance_{agitator_id}"
                        ),
                    )

                with c4:

                    default_elevation = min(
                        straight_H
                        * (
                            0.25
                            + (
                                stage_number
                                - 1
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
                        value=default_elevation,
                        step=0.01,
                        key=(
                            f"{name}_elevation_{agitator_id}"
                        ),
                    )

                # ---------------------------------------
                # BLADES / Np / Nq
                # ---------------------------------------

                c1, c2, c3 = st.columns(3)

                with c1:

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
                            f"{name}_blades_{agitator_id}"
                        ),
                    )

                with c2:

                    np_available = spec.get(
                        "Np",
                        None,
                    )

                    if np_available is None:

                        np_value = st.number_input(
                            "Power Number Np",
                            min_value=0.001,
                            max_value=50.0,
                            value=1.0,
                            step=0.05,
                            key=(
                                f"{name}_Np_{agitator_id}"
                            ),
                        )

                    else:

                        np_value = st.number_input(
                            "Power Number Np",
                            min_value=0.001,
                            max_value=50.0,
                            value=safe_float(
                                np_available,
                                1.0,
                            ),
                            step=0.05,
                            key=(
                                f"{name}_Np_{agitator_id}"
                            ),
                        )

                with c3:

                    nq_available = spec.get(
                        "Nq",
                        None,
                    )

                    if nq_available is None:

                        nq_value = st.number_input(
                            "Flow Number Nq",
                            min_value=0.001,
                            max_value=10.0,
                            value=0.5,
                            step=0.05,
                            key=(
                                f"{name}_Nq_{agitator_id}"
                            ),
                        )

                    else:

                        nq_value = st.number_input(
                            "Flow Number Nq",
                            min_value=0.001,
                            max_value=10.0,
                            value=safe_float(
                                nq_available,
                                0.5,
                            ),
                            step=0.05,
                            key=(
                                f"{name}_Nq_{agitator_id}"
                            ),
                        )

                # ---------------------------------------
                # CALCULATED DIAMETER
                # ---------------------------------------

                impeller_D = tank_D * ratio

                st.info(
                    f"Impeller Diameter = "
                    f"{impeller_D:.3f} m "
                    f"(D/T = {ratio:.3f})"
                )

                # ---------------------------------------
                # STAGE DATA
                # ---------------------------------------

                stages.append(
                    {
                        "stage": stage_number,

                        "agitator": selected_agitator,

                        "Np": np_value,

                        "Nq": nq_value,

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

    # -----------------------------------------------------
    # SOLIDS
    # -----------------------------------------------------

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

        with st.container(border=True):

            st.markdown(
                '<div class="subsection-header">5. Solids Suspension Basis</div>',
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

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

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

    reactors.append(
        reactor
    )


# =========================================================
# CALCULATE REACTORS
# =========================================================

for reactor in reactors:

    try:

        results, train = calculate_train(
            reactor["stages"],
            reactor["working_volume_m3"],
        )

    except Exception as exc:

        st.error(
            f"{reactor['name']} reactor calculation error: {exc}"
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

    # -----------------------------------------------------
    # NJS CALCULATION
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

            if njs and njs > 0:

                stage["Njs_RPM"] = njs

                stage["N_over_Njs"] = (
                    stage["rpm"] / njs
                )

            else:

                stage["N_over_Njs"] = None

    reactor["results"] = results

    reactor["train"] = train

    # -----------------------------------------------------
    # GEOMETRY OBJECT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    try:

        reactor["checks"] = validate_design(
            geometry,
            results,
            process_type,
        )

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

    except Exception:

        reactor["status"] = "REVIEW"

    try:

        reactor["recommendations"] = recommendations(
            process_type,
            train,
        )

    except Exception as exc:

        reactor["recommendations"] = [
            f"Recommendation engine error: {exc}"
        ]


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
# ENGINEERING PERFORMANCE OVERVIEW
# =========================================================

st.markdown(
    '<div class="section-header">Engineering Performance Overview</div>',
    unsafe_allow_html=True,
)

kpi_columns = st.columns(8)


def train_value(
    key,
    default=0.0,
):

    value = active_train.get(
        key,
        default,
    )

    return value if value is not None else default


kpis = [
    (
        "Working Volume",
        f"{active_reactor['working_volume_m3']:.2f}",
        "m³",
    ),

    (
        "Operating Fill",
        f"{active_reactor['fill_percent']:.1f}",
        "%",
    ),

    (
        "Shaft Power",
        f"{train_value('total_power_kw'):.2f}",
        "kW",
    ),

    (
        "P/V",
        f"{train_value('P_per_V_kW_m3'):.3f}",
        "kW/m³",
    ),

    (
        "Total Q",
        f"{train_value('total_Q_m3_h'):.1f}",
        "m³/h",
    ),

    (
        "Q/V",
        f"{train_value('Q_per_volume_1_s'):.4f}",
        "s⁻¹",
    ),

    (
        "Maximum Re",
        (
            f"{train_value('maximum_reynolds'):,.0f}"
            if train_value(
                "maximum_reynolds",
                None,
            )
            else "N/A"
        ),
        "",
    ),

    (
        "Status",
        active_status,
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
            "Primary focus: circulation, Q/V and blend time. "
            "P/V and Reynolds number provide supporting criteria.",

        "Liquid-Liquid":
            "Prioritize bulk circulation, phase contact, "
            "dispersion and blend performance.",

        "Solid-Liquid":
            "Primary criterion is N/Njs. "
            "Also review P/V, Q/V, clearance and solids loading.",

        "Gas-Liquid":
            "Prioritize gas dispersion, P/V, gas flow and kLa.",

        "Gas-Liquid-Solid":
            "Simultaneously evaluate solids suspension and "
            "gas dispersion.",

        "Crystallization":
            "Balance suspension, circulation, shear and "
            "crystal-growth requirements.",

        "High-Viscosity":
            "Prioritize torque, P/V, Reynolds number and "
            "mechanical loading.",

        "Heat-Controlled Reaction":
            "Mixing performance and heat-transfer capacity "
            "must both be demonstrated.",
    }

    scaleup_description = {

        "Constant P/V":
            "Maintains power density and is widely used "
            "for mixing-intensity comparison.",

        "Constant Tip Speed":
            "Maintains impeller peripheral velocity and "
            "provides a useful shear-related comparison.",

        "Constant Q/V":
            "Maintains circulation or turnover intensity.",

        "Constant RPM":
            "Maintains mechanical operating speed but is "
            "not generally a universal mixing similarity criterion.",

        "Constant Froude Number":
            "Maintains inertial/gravity similarity.",

        "Constant Reynolds Number":
            "Maintains viscous/inertial similarity.",
    }

    c1, c2 = st.columns(2)

    with c1:

        with st.container(border=True):

            st.markdown(
                "### Process Requirement"
            )

            st.info(
                guidance[
                    process_type
                ]
            )

    with c2:

        with st.container(border=True):

            st.markdown(
                "### Primary Scale-Up Criterion"
            )

            st.info(
                scaleup_description[
                    scaleup_basis
                ]
            )

    with st.container(border=True):

        st.markdown(
            "### Engineering Governance"
        )

        st.markdown(
            """
            <div class="engineering-note">

            <b>Engineering principle:</b><br><br>

            RPM alone should not be treated as a universal
            scale-up criterion. Reactor scale-up should reconcile
            functional mixing requirements such as P/V, Q/V,
            impeller tip speed, Reynolds number, N/Njs,
            blend time, gas dispersion, mass transfer and
            heat-transfer performance.

            </div>
            """,
            unsafe_allow_html=True,
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
                        reactor[
                            "liquid_height_m"
                        ]
                        /
                        reactor[
                            "tank_diameter_m"
                        ]
                        if reactor[
                            "tank_diameter_m"
                        ] > 0
                        else 0,
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
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        "### Geometry Review"
    )

    for reactor in reactors:

        with st.container(border=True):

            st.markdown(
                f"**⚗️ {reactor['name']} Reactor**"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Tank Diameter",
                f"{reactor['tank_diameter_m']:.3f} m",
            )

            c2.metric(
                "Straight Side",
                f"{reactor['straight_height_m']:.3f} m",
            )

            c3.metric(
                "Liquid Height",
                f"{reactor['liquid_height_m']:.3f} m",
            )

            c4.metric(
                "Operating Fill",
                f"{reactor['fill_percent']:.1f} %",
            )


# =========================================================
# AGITATOR TAB
# =========================================================

with tab_agitator:

    st.markdown(
        "## Agitator Train Design"
    )

    st.info(
        "Agitators are configured in the Reactor Design section above. "
        "The table below shows the calculated engineering performance "
        "of each independent impeller."
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

                    "P/V":
                        stage.get(
                            "power_per_volume_kw_m3",
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
                        njs,

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
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.warning(
                "No agitator calculation results available."
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

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Power",
            f"{train.get('total_power_kw', 0):.2f} kW",
        )

        c2.metric(
            "P/V",
            f"{train.get('P_per_V_kW_m3', 0):.3f} kW/m³",
        )

        c3.metric(
            "Total Q",
            f"{train.get('total_Q_m3_h', 0):.1f} m³/h",
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Q/V",
            f"{train.get('Q_per_volume_1_s', 0):.4f} s⁻¹",
        )

        turnover = train.get(
            "turnover_time_min",
            None,
        )

        c2.metric(
            "Turnover Time",
            (
                f"{turnover:.3f} min"
                if turnover
                else "N/A"
            ),
        )

        c3.metric(
            "Total Torque",
            f"{train.get('total_torque_Nm', 0):.1f} N·m",
        )

        performance_rows = []

        for stage in reactor[
            "results"
        ]:

            performance_rows.append(
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

                    "Regime":
                        stage.get(
                            "mixing_regime",
                            "",
                        ),

                    "Re":
                        stage.get(
                            "Re",
                            None,
                        ),

                    "Fr":
                        stage.get(
                            "Fr",
                            None,
                        ),

                    "Tip Speed (m/s)":
                        stage.get(
                            "tip_speed_m_s",
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

                    "Torque (N·m)":
                        stage.get(
                            "torque_Nm",
                            None,
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


# =========================================================
# SCALE-UP TAB
# =========================================================

with tab_scaleup:

    st.markdown(
        "## Reactor Scale-Up Evaluation"
    )

    if len(reactors) < 2:

        st.info(
            "Select a comparison study mode above "
            "to activate scale-up evaluation."
        )

    else:

        reference = reactors[0]
        target = reactors[-1]

        st.markdown(
            f"### {reference['name']} → {target['name']}"
        )

        reference_volume = (
            reference[
                "working_volume_m3"
            ]
        )

        target_volume = (
            target[
                "working_volume_m3"
            ]
        )

        volume_ratio = (
            target_volume
            /
            reference_volume
            if reference_volume > 0
            else 0
        )

        diameter_ratio = (
            target[
                "tank_diameter_m"
            ]
            /
            reference[
                "tank_diameter_m"
            ]
            if reference[
                "tank_diameter_m"
            ] > 0
            else 0
        )

        reference_pv = (
            reference[
                "train"
            ].get(
                "P_per_V_kW_m3",
                0,
            )
        )

        target_pv = (
            target[
                "train"
            ].get(
                "P_per_V_kW_m3",
                0,
            )
        )

        reference_qv = (
            reference[
                "train"
            ].get(
                "Q_per_volume_1_s",
                0,
            )
        )

        target_qv = (
            target[
                "train"
            ].get(
                "Q_per_volume_1_s",
                0,
            )
        )

        pv_ratio = (
            target_pv / reference_pv
            if reference_pv > 0
            else 0
        )

        qv_ratio = (
            target_qv / reference_qv
            if reference_qv > 0
            else 0
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

        # -------------------------------------------------
        # SCALE-UP CALCULATION
        # -------------------------------------------------

        st.markdown(
            "### Primary Scale-Up Calculation"
        )

        if (
            reference.get("results")
            and target.get("results")
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
                        "rpm",
                        0,
                    ),

                "impeller_diameter_m":
                    ref_stage.get(
                        "impeller_diameter_m",
                        0,
                    ),

                "volume_m3":
                    reference[
                        "working_volume_m3"
                    ],
            }

            target_basis = {
                "impeller_diameter_m":
                    target_stage.get(
                        "impeller_diameter_m",
                        0,
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
                    "target_rpm",
                    None,
                )

                target_tip = scale_result.get(
                    "target_tip_speed",
                    None,
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Scale-Up Criterion",
                    scaleup_basis,
                )

                c2.metric(
                    "Calculated Target RPM",
                    (
                        f"{target_rpm:.1f} RPM"
                        if target_rpm is not None
                        else "N/A"
                    ),
                )

                c3.metric(
                    "Corresponding Tip Speed",
                    (
                        f"{target_tip:.2f} m/s"
                        if target_tip is not None
                        else "N/A"
                    ),
                )

            except Exception as exc:

                st.error(
                    f"Scale-up calculation error: {exc}"
                )

        else:

            st.warning(
                "Scale-up requires at least one calculated "
                "agitator stage in both reactors."
            )

        # -------------------------------------------------
        # COMPARISON
        # -------------------------------------------------

        st.markdown(
            "### Reactor Comparison"
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
                        0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "total_power_kw",
                        0,
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
                        0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "P_per_V_kW_m3",
                        0,
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
                        0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "total_Q_m3_h",
                        0,
                    ),
            },

            {
                "Parameter":
                    "Q/V",

                "Unit":
                    "s⁻¹",

                reference["name"]:
                    reference[
                        "train"
                    ].get(
                        "Q_per_volume_1_s",
                        0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "Q_per_volume_1_s",
                        0,
                    ),
            },

            {
                "Parameter":
                    "Average Tip Speed",

                "Unit":
                    "m/s",

                reference["name"]:
                    reference[
                        "train"
                    ].get(
                        "average_tip_speed_m_s",
                        0,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "average_tip_speed_m_s",
                        0,
                    ),
            },

            {
                "Parameter":
                    "Maximum Reynolds Number",

                "Unit":
                    "-",

                reference["name"]:
                    reference[
                        "train"
                    ].get(
                        "maximum_reynolds",
                        None,
                    ),

                target["name"]:
                    target[
                        "train"
                    ].get(
                        "maximum_reynolds",
                        None,
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

        st.warning(
            "Scale-up RPM is a preliminary engineering "
            "starting point. Final agitator selection should "
            "reconcile P/V, Q/V, tip speed, Reynolds number, "
            "N/Njs, blend time, gas dispersion, heat transfer "
            "and mechanical design requirements."
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
            f"### ⚗️ {reactor['name']}"
        )

        checks = reactor[
            "checks"
        ]

        status_counts = {
            "PASS":
                sum(
                    x.get(
                        "severity",
                        "",
                    ) == "PASS"
                    for x in checks
                ),

            "REVIEW":
                sum(
                    x.get(
                        "severity",
                        "",
                    ) == "REVIEW"
                    for x in checks
                ),

            "FAIL":
                sum(
                    x.get(
                        "severity",
                        "",
                    ) == "FAIL"
                    for x in checks
                ),
        }

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "PASS",
            status_counts["PASS"],
        )

        c2.metric(
            "REVIEW",
            status_counts["REVIEW"],
        )

        c3.metric(
            "FAIL",
            status_counts["FAIL"],
        )

        validation_rows = []

        for item in checks:

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
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# 3D VISUALIZATION
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
        if reactor["name"]
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
        "The 3D model is an engineering visualization of "
        "vessel geometry, impeller arrangement, baffles and "
        "conceptual mixing. It is not a CFD solution for "
        "velocity, pressure, turbulence or species concentration."
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
            label="📄 Download Engineering PDF",
            data=pdf_bytes,
            file_name=(
                "reactor_scaleup_engineering_report.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as exc:

        st.error(
            f"Report generation error: {exc}"
        )

    st.markdown(
        "### Engineering Recommendation"
    )

    for item in selected[
        "recommendations"
    ]:

        st.info(item)


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Preliminary engineering screening tool. "
    "Np/Nq values should be based on validated agitator "
    "geometry, vendor data or reliable literature correlations. "
    "Njs, blend time, kLa and heat-transfer calculations "
    "require system-specific validation. Final equipment "
    "selection must include vendor confirmation, mechanical "
    "design, process safety review and applicable engineering "
    "standards."
)
```
