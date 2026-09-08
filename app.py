import math

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

from calculations.heat_transfer import (
    lmtd,
    heat_transfer_duty_kw,
    required_area_m2,
    heat_removal_margin,
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
# PAGE
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f4f7fb;
    }

    [data-testid="stSidebar"] {
        background: #101a2f;
    }

    [data-testid="stSidebar"] * {
        color: #eef3fa;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    .main-title {
        background: linear-gradient(
            135deg,
            #0d172b 0%,
            #1c355c 100%
        );
        padding: 28px 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 20px;
    }

    .main-title h1 {
        margin: 0;
        font-size: 32px;
        font-weight: 750;
    }

    .main-title p {
        margin: 7px 0 0 0;
        color: #cbd7e9;
        font-size: 15px;
    }

    .metric-card {
        background: white;
        border: 1px solid #e1e7f0;
        border-radius: 14px;
        padding: 15px;
        min-height: 100px;
        box-shadow: 0 2px 8px rgba(18, 31, 53, 0.04);
    }

    .metric-label {
        font-size: 12px;
        color: #718096;
        font-weight: 600;
    }

    .metric-value {
        font-size: 24px;
        color: #17233c;
        font-weight: 750;
        margin-top: 5px;
    }

    .metric-unit {
        font-size: 12px;
        color: #718096;
    }

    .section-title {
        font-size: 22px;
        font-weight: 750;
        color: #17233c;
        margin: 15px 0 10px 0;
    }

    .info-box {
        background: white;
        border-left: 4px solid #355c8a;
        border-radius: 10px;
        padding: 13px 16px;
        margin: 8px 0;
    }

    .engineering-note {
        background: #fff8e8;
        border: 1px solid #f1dfad;
        border-radius: 10px;
        padding: 12px 15px;
        color: #624d16;
        font-size: 13px;
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
    <div class="main-title">
        <h1>⚗️ Reactor Scale-Up Engineering Studio</h1>
        <p>
        Process requirement → mixing mechanism → reactor geometry →
        independent agitator train → scale-up → validation →
        engineering recommendation
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## Study Configuration")

    project_name = st.text_input(
        "Project / Study Name",
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
    )

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
    )

    st.divider()

    st.markdown("### Engineering Focus")

    focus = [
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
        focus.append("N/Njs")

    if process_type in [
        "Gas-Liquid",
        "Gas-Liquid-Solid",
    ]:
        focus.append("kLa")

    for item in focus:
        st.checkbox(
            item,
            value=True,
            disabled=True,
            key=f"focus_{item}",
        )

    st.divider()

    st.caption(
        "Preliminary engineering screening tool. "
        "Final equipment design requires validated data."
    )


# =========================================================
# REACTOR DEFINITIONS
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
# REACTOR INPUT FUNCTION
# =========================================================

def reactor_input_panel(name):

    st.markdown(
        f"### ⚗️ {name} Reactor"
    )

    with st.container(border=True):

        # -------------------------------------------------
        # PROCESS PROPERTIES
        # -------------------------------------------------

        st.markdown(
            "#### 1. Process Conditions"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            working_volume = st.number_input(
                "Working Volume (m³)",
                min_value=0.01,
                max_value=5000.0,
                value=20.0 if name == "Commercial" else 3.0,
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

        # -------------------------------------------------
        # REACTOR GEOMETRY
        # -------------------------------------------------

        st.markdown(
            "#### 2. Reactor Geometry"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            tank_D = st.number_input(
                "Tank ID (m)",
                min_value=0.1,
                max_value=20.0,
                value=2.2 if name == "Commercial" else 1.0,
                step=0.01,
                key=f"{name}_tank_D",
            )

        with c2:
            straight_H = st.number_input(
                "Straight Side (m)",
                min_value=0.1,
                max_value=30.0,
                value=3.0 if name == "Commercial" else 2.0,
                step=0.01,
                key=f"{name}_straight_H",
            )

        with c3:
            bottom_type = st.selectbox(
                "Bottom Head",
                [
                    "Flat Bottom",
                    "2:1 Ellipsoidal",
                    "10% Torispherical",
                    "6% Torispherical",
                    "Hemispherical",
                    "Conical",
                ],
                index=1,
                key=f"{name}_bottom",
            )

        with c4:
            top_type = st.selectbox(
                "Top Head",
                [
                    "Flat Bottom",
                    "2:1 Ellipsoidal",
                    "10% Torispherical",
                    "6% Torispherical",
                    "Hemispherical",
                    "Conical",
                ],
                index=1,
                key=f"{name}_top",
            )

        total_volume = calculate_total_volume(
            tank_D,
            straight_H,
            bottom_type,
            top_type,
        )

        liquid_height = liquid_height_from_volume(
            working_volume,
            tank_D,
            straight_H,
            bottom_type,
            top_type,
        )

        fill = calculate_fill_percent(
            working_volume,
            total_volume,
        )

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

        c4.metric(
            "H/T",
            f"{liquid_height / tank_D:.2f}",
        )

        if working_volume > total_volume:
            st.error(
                "Working volume exceeds calculated vessel capacity."
            )

        # -------------------------------------------------
        # INTERNALS
        # -------------------------------------------------

        st.markdown(
            "#### 3. Vessel Internals"
        )

        c1, c2 = st.columns(2)

        with c1:
            default_baffles = 4

            baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=default_baffles,
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

        # -------------------------------------------------
        # AGITATOR TRAIN
        # -------------------------------------------------

        st.markdown(
            "#### 4. Independent Agitator Train"
        )

        nstages = st.number_input(
            "Number of Independent Agitator Stages",
            min_value=1,
            max_value=3,
            value=2,
            step=1,
            key=f"{name}_nstages",
        )

        nstages = int(nstages)

        stages = []

        stage_cols = st.columns(
            nstages
        )

        for i in range(
            nstages
        ):

            with stage_cols[i]:

                st.markdown(
                    f"**Stage {i + 1}**"
                )

                agitator_name = st.selectbox(
                    "Agitator Type",
                    list(AGITATORS.keys()),
                    index=min(
                        i,
                        len(AGITATORS) - 1,
                    ),
                    key=f"{name}_agitator_{i}",
                )

                spec = AGITATORS[
                    agitator_name
                ]

                st.caption(
                    spec["description_short"]
                )

                ratio = st.number_input(
                    "D/T Ratio",
                    min_value=0.05,
                    max_value=0.95,
                    value=float(
                        spec["D_T"]
                    ),
                    step=0.01,
                    key=f"{name}_DT_{i}",
                )

                impeller_D = (
                    tank_D * ratio
                )

                rpm = st.number_input(
                    "RPM",
                    min_value=0.1,
                    max_value=1500.0,
                    value=115.0,
                    step=1.0,
                    key=f"{name}_rpm_{i}",
                )

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
                    key=f"{name}_clearance_{i}",
                )

                elevation = st.number_input(
                    "Elevation from Bottom (m)",
                    min_value=0.0,
                    max_value=max(
                        straight_H,
                        0.1,
                    ),
                    value=min(
                        straight_H * (
                            0.25
                            + i * 0.25
                        ),
                        straight_H,
                    ),
                    step=0.01,
                    key=f"{name}_elevation_{i}",
                )

                blades = st.number_input(
                    "Number of Blades",
                    min_value=1,
                    max_value=20,
                    value=int(
                        spec["blades"]
                    ),
                    step=1,
                    key=f"{name}_blades_{i}",
                )

                use_override = st.checkbox(
                    "Override Np / Nq",
                    value=False,
                    key=f"{name}_override_{i}",
                )

                if use_override:

                    np_value = st.number_input(
                        "Power Number Np",
                        min_value=0.001,
                        max_value=50.0,
                        value=float(
                            spec["Np"]
                            or 1.0
                        ),
                        step=0.05,
                        key=f"{name}_Np_{i}",
                    )

                    nq_value = st.number_input(
                        "Flow Number Nq",
                        min_value=0.001,
                        max_value=10.0,
                        value=float(
                            spec["Nq"]
                            or 0.5
                        ),
                        step=0.05,
                        key=f"{name}_Nq_{i}",
                    )

                else:
                    np_value = spec["Np"]
                    nq_value = spec["Nq"]

                if np_value is None:
                    st.warning(
                        "Np unavailable. "
                        "Enter validated vendor/literature data."
                    )

                if nq_value is None:
                    st.warning(
                        "Nq unavailable. "
                        "Enter validated vendor/literature data."
                    )

                stages.append(
                    {
                        "stage": i + 1,
                        "agitator": agitator_name,
                        "Np": np_value,
                        "Nq": nq_value,
                        "impeller_diameter_m": impeller_D,
                        "rpm": rpm,
                        "number_impellers": 1,
                        "elevation_m": elevation,
                        "clearance_m": clearance,
                        "blades": blades,
                        "density_kg_m3": density,
                        "viscosity_pa_s": viscosity_cp / 1000.0,
                        "tank_diameter_m": tank_D,
                        "liquid_height_m": liquid_height,
                        "working_volume_m3": working_volume,
                    }
                )

        # -------------------------------------------------
        # SOLIDS
        # -------------------------------------------------

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
                "#### 5. Solids Suspension Basis"
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
                "solids_wt_percent": solids_wt,
                "particle_diameter_m": particle_d50_mm / 1000.0,
                "solid_density_kg_m3": solid_density,
                "S": S_factor,
            }

        # -------------------------------------------------
        # RETURN
        # -------------------------------------------------

        return {
            "name": name,
            "working_volume_m3": working_volume,
            "density_kg_m3": density,
            "viscosity_cp": viscosity_cp,
            "viscosity_pa_s": viscosity_cp / 1000.0,
            "surface_tension_mN_m": surface_tension,
            "surface_tension_n_m": surface_tension / 1000.0,

            "tank_diameter_m": tank_D,
            "straight_height_m": straight_H,
            "bottom_type": bottom_type,
            "top_type": top_type,

            "total_volume_m3": total_volume,
            "liquid_height_m": liquid_height,
            "fill_percent": fill,

            "baffles": int(baffles),
            "baffle_width_ratio": baffle_width_ratio,

            "stages": stages,

            "solids": solids_data,
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
# CALCULATE ALL REACTORS
# =========================================================

for reactor in reactors:

    results, train = calculate_train(
        reactor["stages"],
        reactor["working_volume_m3"],
    )

    # Njs
    if process_type in [
        "Solid-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
    ]:

        solids = reactor["solids"]

        for stage in results:

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

            stage["njs_rpm"] = njs

            if njs:
                stage["Njs_RPM"] = njs

                stage["N_over_Njs"] = (
                    stage["rpm"]
                    / njs
                )

            else:
                stage["N_over_Njs"] = None

    reactor["results"] = results
    reactor["train"] = train

    geometry = {
        "working_volume_m3": reactor[
            "working_volume_m3"
        ],
        "total_volume_m3": reactor[
            "total_volume_m3"
        ],
        "tank_diameter_m": reactor[
            "tank_diameter_m"
        ],
        "straight_height_m": reactor[
            "straight_height_m"
        ],
        "liquid_height_m": reactor[
            "liquid_height_m"
        ],
        "fill_percent": reactor[
            "fill_percent"
        ],
        "baffles": reactor[
            "baffles"
        ],
    }

    reactor["geometry"] = geometry

    reactor["checks"] = validate_design(
        geometry,
        results,
        process_type,
    )

    reactor["status"] = overall_status(
        reactor["checks"]
    )

    reactor["recommendations"] = recommendations(
        process_type,
        train,
    )


# =========================================================
# GLOBAL KPI
# =========================================================

active_reactor = reactors[-1]

train = active_reactor["train"]

status = active_reactor["status"]


# =========================================================
# KPI HEADER
# =========================================================

st.markdown(
    '<div class="section-title">Engineering Performance Overview</div>',
    unsafe_allow_html=True,
)

kpi_columns = st.columns(8)

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
        f"{train['total_power_kw']:.2f}",
        "kW",
    ),
    (
        "P/V",
        f"{train['P_per_V_kW_m3']:.3f}",
        "kW/m³",
    ),
    (
        "Total Q",
        f"{train['total_Q_m3_h']:.1f}",
        "m³/h",
    ),
    (
        "Q/V",
        f"{train['Q_per_volume_1_s']:.4f}",
        "s⁻¹",
    ),
    (
        "Max Re",
        (
            f"{train['maximum_reynolds']:,.0f}"
            if train["maximum_reynolds"]
            else "N/A"
        ),
        "",
    ),
    (
        "Status",
        status,
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

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            "### Process Requirement"
        )

        guidance = {
            "General Mixing":
                "Primary: Q/V and blend time. Secondary: P/V and Re.",

            "Liquid-Liquid":
                "Prioritize bulk circulation, phase contact and blend time.",

            "Solid-Liquid":
                "Primary: N/Njs. Secondary: P/V, Q/V and clearance.",

            "Gas-Liquid":
                "Primary: gas dispersion and kLa. Secondary: P/V and gas velocity.",

            "Gas-Liquid-Solid":
                "Check solids suspension and gas dispersion simultaneously.",

            "Crystallization":
                "Balance suspension, circulation and shear.",

            "High-Viscosity":
                "Prioritize torque, P/V, Re and mechanical loading.",

            "Heat-Controlled Reaction":
                "Mixing and heat-transfer capacity must both be demonstrated.",
        }

        st.info(
            guidance[
                process_type
            ]
        )

    with c2:

        st.markdown(
            "### Primary Scale-Up Criterion"
        )

        scaleup_description = {
            "Constant P/V":
                "Maintains power density; useful for energy-intensity comparison.",

            "Constant Tip Speed":
                "Maintains impeller peripheral velocity / local shear proxy.",

            "Constant Q/V":
                "Maintains circulation / turnover intensity.",

            "Constant RPM":
                "Mechanical operating-speed comparison only; not generally a mixing similarity criterion.",

            "Constant Froude Number":
                "Maintains inertial/gravity similarity.",

            "Constant Reynolds Number":
                "Maintains viscous/inertial similarity.",
        }

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
        <b>Important:</b> RPM alone is not a valid universal scale-up
        criterion. Compare functional outcomes such as P/V, Q/V,
        blend time, solids suspension, gas dispersion, mass transfer
        and heat transfer.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# GEOMETRY
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
                    reactor[
                        "liquid_height_m"
                    ]
                    /
                    reactor[
                        "tank_diameter_m"
                    ],

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

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{reactor['name']} Reactor**"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Diameter",
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
                "Fill",
                f"{reactor['fill_percent']:.1f} %",
            )


# =========================================================
# AGITATOR TRAIN
# =========================================================

with tab_agitator:

    st.markdown(
        "## Independent Agitator Train"
    )

    for reactor in reactors:

        st.markdown(
            f"### ⚗️ {reactor['name']}"
        )

        rows = []

        for i, stage in enumerate(
            reactor["results"],
            start=1,
        ):

            njs = stage.get(
                "njs_rpm"
            )

            n_over_njs = (
                stage["rpm"] / njs
                if njs and njs > 0
                else None
            )

            rows.append(
                {
                    "Stage":
                        i,

                    "Agitator":
                        stage["agitator"],

                    "D (m)":
                        stage[
                            "impeller_diameter_m"
                        ],

                    "D/T":
                        stage["D_T"],

                    "RPM":
                        stage["rpm"],

                    "Clearance (m)":
                        stage[
                            "clearance_m"
                        ],

                    "Elevation (m)":
                        stage[
                            "elevation_m"
                        ],

                    "Blades":
                        stage[
                            "blades"
                        ],

                    "Np":
                        stage["Np"],

                    "Nq":
                        stage["Nq"],

                    "Re":
                        stage["Re"],

                    "Power (kW)":
                        stage["power_kw"],

                    "Power (HP)":
                        stage["power_hp"],

                    "Q (m³/h)":
                        stage["Q_m3_h"],

                    "P/V (kW/m³)":
                        stage[
                            "power_per_volume_kw_m3"
                        ],

                    "Tip Speed (m/s)":
                        stage[
                            "tip_speed_m_s"
                        ],

                    "Torque (N·m)":
                        stage[
                            "torque_Nm"
                        ],

                    "Njs (RPM)":
                        njs,

                    "N/Njs":
                        n_over_njs,
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# PERFORMANCE
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

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric(
            "Total Power",
            f"{train['total_power_kw']:.2f} kW",
        )

        c2.metric(
            "P/V",
            f"{train['P_per_V_kW_m3']:.3f} kW/m³",
        )

        c3.metric(
            "Total Q",
            f"{train['total_Q_m3_h']:.1f} m³/h",
        )

        c4.metric(
            "Q/V",
            f"{train['Q_per_volume_1_s']:.4f} s⁻¹",
        )

        c5.metric(
            "Turnover",
            (
                f"{train['turnover_time_min']:.3f} min"
                if train["turnover_time_min"]
                else "N/A"
            ),
        )

        c6.metric(
            "Total Torque",
            f"{train['total_torque_Nm']:.1f} N·m",
        )

        performance_rows = []

        for i, stage in enumerate(
            reactor["results"],
            start=1,
        ):

            performance_rows.append(
                {
                    "Stage": i,
                    "Agitator":
                        stage["agitator"],
                    "Regime":
                        stage["mixing_regime"],
                    "Re":
                        stage["Re"],
                    "Fr":
                        stage["Fr"],
                    "Tip Speed (m/s)":
                        stage["tip_speed_m_s"],
                    "Power (kW)":
                        stage["power_kw"],
                    "Q (m³/h)":
                        stage["Q_m3_h"],
                    "Torque (N·m)":
                        stage["torque_Nm"],
                }
            )

        st.dataframe(
            pd.DataFrame(
                performance_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# SCALE-UP
# =========================================================

with tab_scaleup:

    st.markdown(
        "## Pilot → Commercial Scale-Up"
    )

    if len(reactors) < 2:

        st.info(
            "Select a comparison study mode from the sidebar "
            "to activate pilot/commercial scale-up."
        )

    else:

        reference = reactors[0]
        target = reactors[-1]

        st.markdown(
            f"### {reference['name']} → {target['name']}"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Volume Scale Factor",
            (
                target[
                    "working_volume_m3"
                ]
                /
                reference[
                    "working_volume_m3"
                ]
            ),
        )

        c2.metric(
            "Tank Diameter Ratio",
            (
                target[
                    "tank_diameter_m"
                ]
                /
                reference[
                    "tank_diameter_m"
                ]
            ),
        )

        c3.metric(
            "P/V Ratio",
            (
                target["train"][
                    "P_per_V_kW_m3"
                ]
                /
                reference["train"][
                    "P_per_V_kW_m3"
                ]
                if reference["train"][
                    "P_per_V_kW_m3"
                ]
                > 0
                else float("nan")
            ),
        )

        c4.metric(
            "Q/V Ratio",
            (
                target["train"][
                    "Q_per_volume_1_s"
                ]
                /
                reference["train"][
                    "Q_per_volume_1_s"
                ]
                if reference["train"][
                    "Q_per_volume_1_s"
                ]
                > 0
                else float("nan")
            ),
        )

        st.markdown(
            "### Primary Criterion Calculation"
        )

        # Use first active impeller as the
        # reference scale-up impeller.
        ref_stage = reference[
            "results"
        ][0]

        target_stage = target[
            "results"
        ][0]

        reference_basis = {
            "rpm":
                ref_stage["rpm"],

            "impeller_diameter_m":
                ref_stage[
                    "impeller_diameter_m"
                ],

            "volume_m3":
                reference[
                    "working_volume_m3"
                ],
        }

        target_basis = {
            "impeller_diameter_m":
                target_stage[
                    "impeller_diameter_m"
                ],

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

            target_rpm = scale_result[
                "target_rpm"
            ]

            target_tip = scale_result[
                "target_tip_speed"
            ]

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Scale-Up Criterion",
                scaleup_basis,
            )

            c2.metric(
                "Calculated Target RPM",
                f"{target_rpm:.1f} RPM",
            )

            c3.metric(
                "Corresponding Tip Speed",
                f"{target_tip:.2f} m/s",
            )

        except Exception as exc:

            st.error(
                f"Scale-up calculation error: {exc}"
            )

        st.markdown(
            "### Pilot vs Target Comparison"
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
                    "P",
                "Unit":
                    "kW",
                reference["name"]:
                    reference["train"][
                        "total_power_kw"
                    ],
                target["name"]:
                    target["train"][
                        "total_power_kw"
                    ],
            },
            {
                "Parameter":
                    "P/V",
                "Unit":
                    "kW/m³",
                reference["name"]:
                    reference["train"][
                        "P_per_V_kW_m3"
                    ],
                target["name"]:
                    target["train"][
                        "P_per_V_kW_m3"
                    ],
            },
            {
                "Parameter":
                    "Q",
                "Unit":
                    "m³/h",
                reference["name"]:
                    reference["train"][
                        "total_Q_m3_h"
                    ],
                target["name"]:
                    target["train"][
                        "total_Q_m3_h"
                    ],
            },
            {
                "Parameter":
                    "Q/V",
                "Unit":
                    "s⁻¹",
                reference["name"]:
                    reference["train"][
                        "Q_per_volume_1_s"
                    ],
                target["name"]:
                    target["train"][
                        "Q_per_volume_1_s"
                    ],
            },
            {
                "Parameter":
                    "Average Tip Speed",
                "Unit":
                    "m/s",
                reference["name"]:
                    reference["train"][
                        "average_tip_speed_m_s"
                    ],
                target["name"]:
                    target["train"][
                        "average_tip_speed_m_s"
                    ],
            },
            {
                "Parameter":
                    "Maximum Re",
                "Unit":
                    "-",
                reference["name"]:
                    reference["train"][
                        "maximum_reynolds"
                    ],
                target["name"]:
                    target["train"][
                        "maximum_reynolds"
                    ],
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
            "Scale-up RPM is a starting-point engineering calculation. "
            "Final selection must reconcile P/V, Q/V, tip speed, Re, "
            "N/Njs, blend time, gas dispersion and heat-transfer "
            "requirements."
        )


# =========================================================
# VALIDATION
# =========================================================

with tab_validation:

    st.markdown(
        "## Engineering Validation"
    )

    if status == "PASS":
        st.success(
            "Overall screening status: PASS"
        )

    elif status == "REVIEW":
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
                    x["severity"] == "PASS"
                    for x in checks
                ),

            "REVIEW":
                sum(
                    x["severity"] == "REVIEW"
                    for x in checks
                ),

            "FAIL":
                sum(
                    x["severity"] == "FAIL"
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

        validation_df = pd.DataFrame(
            [
                {
                    "Status":
                        x["severity"],
                    "Engineering Check":
                        x["message"],
                }
                for x in checks
            ]
        )

        st.dataframe(
            validation_df,
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
            x["name"]
            for x in reactors
        ],
    )

    selected = next(
        x
        for x in reactors
        if x["name"] == selected_name
    )

    fig = create_reactor_figure(
        tank_diameter_m=selected[
            "tank_diameter_m"
        ],
        straight_height_m=selected[
            "straight_height_m"
        ],
        liquid_height_m=selected[
            "liquid_height_m"
        ],
        results=selected[
            "results"
        ],
        baffles=selected[
            "baffles"
        ],
        bottom_type=selected[
            "bottom_type"
        ],
        top_type=selected[
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

    st.info(
        "This 3D view is an engineering visualization of vessel "
        "geometry, impeller arrangement, baffles and conceptual "
        "circulation paths. It is NOT a CFD velocity, pressure, "
        "turbulence or species-concentration solution."
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
            selected["geometry"],

        "stages":
            selected["results"],

        "train":
            selected["train"],

        "checks":
            selected["checks"],

        "recommendations":
            selected["recommendations"],
    }

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

    st.markdown(
        "### Engineering Recommendation"
    )

    for item in selected[
        "recommendations"
    ]:
        st.info(item)


# =========================================================
# FINAL ENGINEERING DISCLAIMER
# =========================================================

st.divider()

st.caption(
    "Preliminary engineering screening tool. "
    "Np/Nq values are representative unless overridden with "
    "validated data. Njs, blend time, kLa and heat-transfer "
    "calculations require system-specific validation. "
    "Final equipment selection must include vendor data, "
    "pilot/plant validation, mechanical design, process safety "
    "and applicable engineering standards."
)
