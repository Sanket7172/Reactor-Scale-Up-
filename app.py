import streamlit as st
import pandas as pd

from calculations.engine import (
    calculate_train,
    zwietering_njs,
)

from calculations.scaleup import (
    scale_rpm,
)

from calculations.validation import (
    validate_design,
    recommendations,
)

from libraries.agitator_geometry import (
    AGITATORS,
)

from libraries.reactor_geometry import (
    calculate_total_volume,
    liquid_height_from_volume,
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
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f4f6fa;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: linear-gradient(
            135deg,
            #101b35 0%,
            #203b68 100%
        );

        border-radius: 18px;

        padding: 25px 30px;

        margin-bottom: 20px;

        color: white;

        box-shadow:
            0 8px 30px
            rgba(16, 27, 53, 0.16);
    }

    .hero-title {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .hero-subtitle {
        font-size: 14px;
        opacity: 0.85;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #18243c;
        margin-top: 12px;
        margin-bottom: 10px;
    }

    .kpi-card {
        background: white;

        border: 1px solid #e1e6ef;

        border-radius: 14px;

        padding: 15px;

        min-height: 90px;

        box-shadow:
            0 4px 14px
            rgba(20, 30, 50, 0.05);
    }

    .kpi-label {
        font-size: 12px;
        color: #69758a;
    }

    .kpi-value {
        font-size: 22px;
        font-weight: 700;
        color: #18243c;
        margin-top: 4px;
    }

    .small-note {
        font-size: 12px;
        color: #69758a;
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
    <div class="hero">

        <div class="hero-title">
            ⚗️ Reactor Scale-Up Engineering Studio
        </div>

        <div class="hero-subtitle">
            Process requirement → mixing mechanism → reactor geometry
            → independent agitator train → scale-up → validation
            → engineering recommendation
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Study Configuration")

    process_type = st.selectbox(
        "Process Requirement",
        [
            "General blending",
            "Liquid–Liquid",
            "Solid–Liquid",
            "Gas–Liquid",
            "Gas–Liquid–Solid",
            "Crystallization",
            "High viscosity",
            "Heat-controlled reaction",
        ],
    )

    scale_basis = st.selectbox(
        "Scale-Up Basis",
        [
            "Constant Tip Speed",
            "Constant P/V",
            "Constant Q/V",
            "Constant Froude",
            "Constant Reynolds",
            "Constant RPM",
        ],
    )

    st.divider()

    st.subheader("Study Objective")

    objective = st.multiselect(
        "Primary objectives",
        [
            "Blending",
            "Suspension",
            "Gas Dispersion",
            "Heat Transfer",
            "Mass Transfer",
            "Reaction Mixing",
            "Scale-Up",
        ],
        default=[
            "Blending",
            "Scale-Up",
        ],
    )

    st.divider()

    st.caption(
        "Preliminary engineering screening tool. "
        "Final equipment design requires validation "
        "against pilot data, vendor data and detailed "
        "mechanical/process design."
    )


# ============================================================
# DESIGN BASIS
# ============================================================

st.markdown(
    '<div class="section-title">1. Design Basis</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)

with c1:

    working_volume = st.number_input(
        "Working Volume (m³)",
        min_value=0.1,
        max_value=5000.0,
        value=3.0,
        step=0.1,
    )

with c2:

    density = st.number_input(
        "Liquid Density (kg/m³)",
        min_value=1.0,
        max_value=5000.0,
        value=1000.0,
        step=1.0,
    )

with c3:

    viscosity_cp = st.number_input(
        "Viscosity (cP)",
        min_value=0.1,
        max_value=1_000_000.0,
        value=10.0,
        step=0.1,
    )

with c4:

    surface_tension = st.number_input(
        "Surface Tension (mN/m)",
        min_value=0.1,
        max_value=200.0,
        value=30.0,
        step=0.1,
    )


# ============================================================
# REACTOR GEOMETRY
# ============================================================

st.markdown(
    '<div class="section-title">2. Reactor Geometry</div>',
    unsafe_allow_html=True,
)

g1, g2, g3, g4 = st.columns(4)

with g1:

    tank_diameter = st.number_input(
        "Tank ID (m)",
        min_value=0.2,
        max_value=20.0,
        value=1.50,
        step=0.01,
    )

with g2:

    straight_height = st.number_input(
        "Straight Side Height (m)",
        min_value=0.2,
        max_value=30.0,
        value=2.00,
        step=0.01,
    )

with g3:

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
    )

with g4:

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
    )


b1, b2, b3, b4 = st.columns(4)

with b1:

    number_baffles = st.number_input(
        "Number of Baffles",
        min_value=0,
        max_value=12,
        value=4,
        step=1,
    )

with b2:

    baffle_width_ratio = st.number_input(
        "Baffle Width / T",
        min_value=0.01,
        max_value=0.20,
        value=0.10,
        step=0.01,
    )

with b3:

    design_pressure = st.number_input(
        "Design Pressure (bar g)",
        min_value=-1.0,
        max_value=100.0,
        value=3.0,
        step=0.1,
    )

with b4:

    design_temperature = st.number_input(
        "Design Temperature (°C)",
        min_value=-50.0,
        max_value=500.0,
        value=100.0,
        step=1.0,
    )


# ============================================================
# GEOMETRY CALCULATION
# ============================================================

total_volume = calculate_total_volume(
    tank_diameter,
    straight_height,
    bottom_type,
    top_type,
)

liquid_height = liquid_height_from_volume(
    min(
        working_volume,
        total_volume,
    ),
    tank_diameter,
    straight_height,
    bottom_type,
    top_type,
)

fill_percent = (
    working_volume
    / total_volume
    * 100.0
    if total_volume > 0
    else 0.0
)


if working_volume > total_volume:

    st.warning(
        "Working volume exceeds the calculated vessel capacity."
    )


# ============================================================
# GEOMETRY SUMMARY
# ============================================================

g1, g2, g3, g4 = st.columns(4)

g1.metric(
    "Calculated Capacity",
    f"{total_volume:.2f} m³",
)

g2.metric(
    "Liquid Height",
    f"{liquid_height:.2f} m",
)

g3.metric(
    "Fill",
    f"{fill_percent:.1f} %",
)

g4.metric(
    "H/T",
    (
        f"{liquid_height / tank_diameter:.2f}"
        if tank_diameter > 0
        else "N/A"
    ),
)


# ============================================================
# AGITATOR TRAIN
# ============================================================

st.markdown(
    '<div class="section-title">3. Independent Agitator Train</div>',
    unsafe_allow_html=True,
)

number_stages = st.number_input(
    "Number of Independent Agitator Stages",
    min_value=1,
    max_value=3,
    value=2,
    step=1,
)

number_stages = int(number_stages)

stage_columns = st.columns(
    number_stages
)

stages = []


for stage_index, col in enumerate(
    stage_columns,
    1,
):

    with col:

        st.markdown(
            f"### Stage {stage_index}"
        )

        agitator_name = st.selectbox(
            "Agitator Type",
            list(AGITATORS.keys()),
            key=f"agitator_{stage_index}",
        )

        spec = AGITATORS[
            agitator_name
        ]

        dt_ratio = st.number_input(
            "Impeller D/T",
            min_value=0.10,
            max_value=0.95,
            value=float(
                spec["D_T"]
            ),
            step=0.01,
            key=f"dt_{stage_index}",
        )

        default_rpm = (
            40.0
            if agitator_name
            in [
                "Anchor",
                "Helical Ribbon",
            ]
            else 120.0
        )

        rpm = st.number_input(
            "Operating RPM",
            min_value=1.0,
            max_value=1500.0,
            value=default_rpm,
            step=1.0,
            key=f"rpm_{stage_index}",
        )

        impeller_count = st.number_input(
            "Impellers in Stage",
            min_value=1,
            max_value=6,
            value=1,
            step=1,
            key=f"impellers_{stage_index}",
        )

        elevation = st.number_input(
            "Impeller Elevation (m)",
            min_value=0.0,
            max_value=max(
                straight_height,
                0.1,
            ),
            value=min(
                straight_height * 0.35,
                straight_height,
            ),
            step=0.01,
            key=f"elevation_{stage_index}",
        )

        clearance = st.number_input(
            "Bottom Clearance (m)",
            min_value=0.01,
            max_value=max(
                tank_diameter,
                0.2,
            ),
            value=max(
                tank_diameter * 0.15,
                0.02,
            ),
            step=0.01,
            key=f"clearance_{stage_index}",
        )

        st.caption(
            f"Np = "
            f"{spec['Np'] if spec['Np'] is not None else 'Vendor'}"
            f" | Nq = "
            f"{spec['Nq'] if spec['Nq'] is not None else 'Vendor'}"
            f" | Flow = {spec['flow']}"
        )

        stages.append(
            {
                "agitator": agitator_name,
                "Np": spec["Np"],
                "Nq": spec["Nq"],
                "flow": spec["flow"],
                "impeller_diameter_m":
                    tank_diameter * dt_ratio,
                "rpm": rpm,
                "number_impellers":
                    int(impeller_count),
                "elevation_m": elevation,
                "clearance_m": clearance,
                "density_kg_m3": density,
                "viscosity_pa_s":
                    viscosity_cp / 1000.0,
                "tank_diameter_m":
                    tank_diameter,
            }
        )


# ============================================================
# CALCULATE TRAIN
# ============================================================

results, train = calculate_train(
    stages,
    working_volume,
)


# ============================================================
# SOLIDS / NJS
# ============================================================

if process_type in [
    "Solid–Liquid",
    "Gas–Liquid–Solid",
    "Crystallization",
]:

    st.markdown(
        '<div class="section-title">4. Solid Suspension Basis</div>',
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:

        solids_wt = st.number_input(
            "Solids Concentration (wt%)",
            min_value=0.0,
            max_value=80.0,
            value=10.0,
            step=0.5,
        )

    with s2:

        particle_size_mm = st.number_input(
            "Particle d50 (mm)",
            min_value=0.001,
            max_value=20.0,
            value=0.50,
            step=0.01,
        )

    with s3:

        solid_density = st.number_input(
            "Solid Density (kg/m³)",
            min_value=1.0,
            max_value=10000.0,
            value=1500.0,
            step=10.0,
        )

    with s4:

        S_constant = st.number_input(
            "Njs S Constant",
            min_value=0.1,
            max_value=20.0,
            value=5.0,
            step=0.1,
        )

    for result in results:

        result["Njs_s_inv"] = zwietering_njs(
            result,
            solids_wt,
            particle_size_mm / 1000.0,
            solid_density,
            density,
            S_constant,
        )

else:

    for result in results:
        result["Njs_s_inv"] = None


# ============================================================
# ADD N/NJS
# ============================================================

for result in results:

    njs = result.get(
        "Njs_s_inv"
    )

    if njs and njs > 0:

        result["N_over_Njs"] = (
            result["N_s_inv"]
            / njs
        )

    else:

        result["N_over_Njs"] = None


# ============================================================
# VALIDATION
# ============================================================

geometry = {
    "tank_diameter_m":
        tank_diameter,

    "working_volume_m3":
        working_volume,

    "total_volume_m3":
        total_volume,

    "liquid_height_m":
        liquid_height,

    "baffles":
        number_baffles,

    "froude":
        max(
            [
                x.get(
                    "Fr",
                    0.0,
                )
                for x in results
            ],
            default=0.0,
        ),
}


checks = validate_design(
    geometry,
    results,
)


recommendation_list = recommendations(
    process_type,
    train,
)


# ============================================================
# KPI STRIP
# ============================================================

st.markdown(
    '<div class="section-title">Engineering Performance Summary</div>',
    unsafe_allow_html=True,
)

kpis = [
    (
        "Working Volume",
        f"{working_volume:.2f} m³",
    ),

    (
        "Fill",
        f"{fill_percent:.1f} %",
    ),

    (
        "Total Power",
        f"{train['total_power_kw']:.2f} kW",
    ),

    (
        "P/V",
        f"{train['power_per_volume_W_m3']:.1f} W/m³",
    ),

    (
        "Total Q",
        f"{train['total_Q_m3_h']:.1f} m³/h",
    ),

    (
        "Q/V",
        f"{train['Q_per_volume_h']:.2f} h⁻¹",
    ),

    (
        "Turnover",
        (
            f"{train['turnover_time_min']:.1f} min"
            if train["turnover_time_min"]
            else "N/A"
        ),
    ),

    (
        "Validation",
        f"{sum(x[1] for x in checks)}/{len(checks)} PASS",
    ),
]


for start in range(
    0,
    len(kpis),
    4,
):

    cols = st.columns(4)

    for col, (
        label,
        value,
    ) in zip(
        cols,
        kpis[start:start + 4],
    ):

        col.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    {label}
                </div>

                <div class="kpi-value">
                    {value}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# APPLICATION TABS
# ============================================================

tabs = st.tabs(
    [
        "Design Basis",
        "Reactor Geometry",
        "Agitator Train",
        "Performance",
        "Scale-Up",
        "Suspension / Njs",
        "Gas-Liquid",
        "Heat Transfer",
        "Validation",
        "3D Mixing",
        "Engineering Report",
    ]
)


# ============================================================
# TAB 1
# ============================================================

with tabs[0]:

    st.subheader(
        "Process Design Basis"
    )

    st.write(
        "The application evaluates the reactor from the process "
        "requirement through preliminary mixing and scale-up criteria."
    )

    basis_table = pd.DataFrame(
        [
            [
                "Process Requirement",
                process_type,
            ],

            [
                "Scale-Up Criterion",
                scale_basis,
            ],

            [
                "Design Objective",
                ", ".join(objective)
                if objective
                else "Not specified",
            ],

            [
                "Working Volume",
                f"{working_volume:.3f} m³",
            ],

            [
                "Density",
                f"{density:.1f} kg/m³",
            ],

            [
                "Viscosity",
                f"{viscosity_cp:.2f} cP",
            ],

            [
                "Surface Tension",
                f"{surface_tension:.2f} mN/m",
            ],
        ],
        columns=[
            "Parameter",
            "Value",
        ],
    )

    st.dataframe(
        basis_table,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 2
# ============================================================

with tabs[1]:

    st.subheader(
        "Reactor Geometry"
    )

    geometry_table = pd.DataFrame(
        [
            [
                "Tank ID",
                tank_diameter,
                "m",
            ],

            [
                "Straight Side",
                straight_height,
                "m",
            ],

            [
                "Calculated Capacity",
                total_volume,
                "m³",
            ],

            [
                "Working Volume",
                working_volume,
                "m³",
            ],

            [
                "Liquid Height",
                liquid_height,
                "m",
            ],

            [
                "Fill",
                fill_percent,
                "%",
            ],

            [
                "H/T",
                liquid_height / tank_diameter,
                "-",
            ],

            [
                "Baffles",
                number_baffles,
                "Nos.",
            ],
        ],
        columns=[
            "Parameter",
            "Value",
            "Unit",
        ],
    )

    st.dataframe(
        geometry_table,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 3
# ============================================================

with tabs[2]:

    st.subheader(
        "Independent Agitator Train"
    )

    train_table = pd.DataFrame(
        [
            {
                "Stage":
                    i + 1,

                "Agitator":
                    x["agitator"],

                "Impeller D (m)":
                    x["impeller_diameter_m"],

                "D/T":
                    x["D_T"],

                "RPM":
                    x["rpm"],

                "Elevation (m)":
                    x["elevation_m"],

                "Clearance (m)":
                    x["clearance_m"],

                "Np":
                    x["Np"],

                "Nq":
                    x["Nq"],

                "Flow":
                    x["flow"],
            }

            for i, x
            in enumerate(results)
        ]
    )

    st.dataframe(
        train_table,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 4
# ============================================================

with tabs[3]:

    st.subheader(
        "Mixing Performance"
    )

    performance_table = pd.DataFrame(
        [
            {
                "Stage":
                    i + 1,

                "Agitator":
                    x["agitator"],

                "RPM":
                    x["rpm"],

                "Re":
                    x["Re"],

                "Fr":
                    x["Fr"],

                "Regime":
                    x["mixing_regime"],

                "Tip Speed (m/s)":
                    x["tip_speed_m_s"],

                "Power (kW)":
                    x["power_kw"],

                "Q (m³/h)":
                    x["Q_m3_h"],

                "Torque (N·m)":
                    x["torque_Nm"],

                "Njs (s⁻¹)":
                    x["Njs_s_inv"],

                "N/Njs":
                    x["N_over_Njs"],
            }

            for i, x
            in enumerate(results)
        ]
    )

    st.dataframe(
        performance_table,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    p1, p2, p3, p4 = st.columns(4)

    p1.metric(
        "Total Power",
        f"{train['total_power_kw']:.2f} kW",
    )

    p2.metric(
        "P/V",
        f"{train['power_per_volume_W_m3']:.1f} W/m³",
    )

    p3.metric(
        "Total Q",
        f"{train['total_Q_m3_h']:.1f} m³/h",
    )

    p4.metric(
        "Turnover",
        (
            f"{train['turnover_time_min']:.1f} min"
            if train["turnover_time_min"]
            else "N/A"
        ),
    )


# ============================================================
# TAB 5
# ============================================================

with tabs[4]:

    st.subheader(
        "Reference → Target Scale-Up"
    )

    st.write(
        "The calculated RPM is a starting-point scale-up value. "
        "The final criterion must be selected according to the "
        "actual process objective and validated against pilot data."
    )

    s1, s2 = st.columns(2)

    with s1:

        reference_volume = st.number_input(
            "Reference Volume (m³)",
            min_value=0.01,
            max_value=5000.0,
            value=max(
                working_volume / 10.0,
                0.1,
            ),
        )

        reference_impeller_D = st.number_input(
            "Reference Impeller D (m)",
            min_value=0.01,
            max_value=10.0,
            value=max(
                results[0]["impeller_diameter_m"]
                * 0.70,
                0.05,
            ),
        )

        reference_rpm = st.number_input(
            "Reference RPM",
            min_value=1.0,
            max_value=1500.0,
            value=float(
                results[0]["rpm"]
            ),
        )

    with s2:

        target_impeller_D = st.number_input(
            "Target Impeller D (m)",
            min_value=0.01,
            max_value=10.0,
            value=float(
                results[0]["impeller_diameter_m"]
            ),
        )

        target_rpm = scale_rpm(
            {
                "rpm":
                    reference_rpm,

                "impeller_diameter_m":
                    reference_impeller_D,

                "volume_m3":
                    reference_volume,
            },

            {
                "impeller_diameter_m":
                    target_impeller_D,

                "volume_m3":
                    working_volume,
            },

            scale_basis,
        )

        st.metric(
            "Calculated Target RPM",
            f"{target_rpm:.1f} rpm",
        )


# ============================================================
# TAB 6
# ============================================================

with tabs[5]:

    st.subheader(
        "Solid Suspension / Njs"
    )

    if process_type not in [
        "Solid–Liquid",
        "Gas–Liquid–Solid",
        "Crystallization",
    ]:

        st.info(
            "Njs analysis becomes active for Solid–Liquid, "
            "Gas–Liquid–Solid and Crystallization studies."
        )

    else:

        njs_table = pd.DataFrame(
            [
                {
                    "Stage":
                        i + 1,

                    "Agitator":
                        x["agitator"],

                    "Njs (s⁻¹)":
                        x["Njs_s_inv"],

                    "Operating N":
                        x["N_s_inv"],

                    "N/Njs":
                        x["N_over_Njs"],
                }

                for i, x
                in enumerate(results)
            ]
        )

        st.dataframe(
            njs_table,
            use_container_width=True,
            hide_index=True,
        )

        st.warning(
            "Njs is a screening estimate. "
            "Use actual suspension tests or validated "
            "system-specific correlations for final design."
        )


# ============================================================
# TAB 7
# ============================================================

with tabs[6]:

    st.subheader(
        "Gas–Liquid Screening"
    )

    st.info(
        "Gas-liquid design requires process-specific "
        "gas flow, sparger geometry, gas holdup, kLa "
        "and mass-transfer data."
    )

    gl1, gl2, gl3, gl4 = st.columns(4)

    with gl1:

        gas_flow = st.number_input(
            "Gas Flow (Nm³/h)",
            min_value=0.0,
            max_value=100000.0,
            value=0.0,
        )

    with gl2:

        sparger_area = st.number_input(
            "Sparger Area (m²)",
            min_value=0.0001,
            max_value=100.0,
            value=0.01,
        )

    with gl3:

        estimated_ug = (
            gas_flow
            / 3600.0
            / sparger_area
            if sparger_area > 0
            else 0.0
        )

        st.metric(
            "Screening Gas Velocity",
            f"{estimated_ug:.3f} m/s",
        )

    with gl4:

        st.metric(
            "P/V",
            f"{train['power_per_volume_W_m3']:.1f} W/m³",
        )

    st.caption(
        "kLa should be calculated from a validated empirical "
        "correlation or experimental data for the actual system."
    )


# ============================================================
# TAB 8
# ============================================================

with tabs[7]:

    st.subheader(
        "Heat Transfer Screening"
    )

    h1, h2, h3, h4 = st.columns(4)

    with h1:

        heat_transfer_U = st.number_input(
            "U (W/m²·K)",
            min_value=1.0,
            max_value=10000.0,
            value=500.0,
        )

    with h2:

        heat_transfer_A = st.number_input(
            "Heat Transfer Area (m²)",
            min_value=0.1,
            max_value=5000.0,
            value=10.0,
        )

    with h3:

        delta_T = st.number_input(
            "Effective ΔT (K)",
            min_value=0.1,
            max_value=300.0,
            value=20.0,
        )

    with h4:

        heat_duty_kw = (
            heat_transfer_U
            * heat_transfer_A
            * delta_T
            / 1000.0
        )

        st.metric(
            "Heat Duty",
            f"{heat_duty_kw:.2f} kW",
        )

    st.caption(
        "Heat-transfer capacity depends on U, area, "
        "temperature driving force, fouling and actual "
        "mixing-side heat-transfer coefficient."
    )


# ============================================================
# TAB 9
# ============================================================

with tabs[8]:

    st.subheader(
        "Engineering Validation"
    )

    passed = 0

    for item in checks:

        name, status, message = item

        if status:

            passed += 1

            st.success(
                f"PASS — {name}: {message}"
            )

        else:

            st.warning(
                f"REVIEW — {name}: {message}"
            )

    st.divider()

    st.subheader(
        "Engineering Recommendation"
    )

    for item in recommendation_list:

        st.info(item)

    st.metric(
        "Validation Result",
        f"{passed}/{len(checks)} PASS",
    )


# ============================================================
# TAB 10
# ============================================================

with tabs[9]:

    st.subheader(
        "3D Reactor & Mixing Visualization"
    )

    st.caption(
        "The model shows reactor geometry, liquid level, "
        "baffles, shaft, independent agitators and "
        "conceptual flow paths."
    )

    try:

        figure = create_reactor_figure(
            tank_diameter,
            straight_height,
            liquid_height,
            results,
            number_baffles,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

        st.info(
            "This is a CFD-inspired visualization. "
            "It is not a CFD velocity, turbulence, "
            "species or pressure solution."
        )

    except Exception as error:

        st.error(
            "3D visualization error."
        )

        st.exception(error)


# ============================================================
# TAB 11
# ============================================================

with tabs[10]:

    st.subheader(
        "Engineering Report"
    )

    report_data = {

        "process_type":
            process_type,

        "geometry":
            geometry,

        "stages":
            results,

        "train":
            train,

        "checks":
            checks,

        "recommendations":
            recommendation_list,
    }

    try:

        pdf_data = build_pdf(
            report_data
        )

        st.download_button(
            label="Download Engineering Report",
            data=pdf_data,
            file_name=(
                "reactor_scaleup_engineering_report.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as error:

        st.error(
            "PDF generation error."
        )

        st.exception(error)
