import streamlit as st
import pandas as pd

from calculations.engine import (
    calculate_train,
    zwietering_njs,
)

from calculations.scaleup import scale_rpm

from calculations.validation import (
    validate_design,
    recommendations,
)

from libraries.agitator_geometry import AGITATORS

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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="⚗️",
    layout="wide",
)


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 24px 28px;
        border-radius: 18px;
        background: linear-gradient(
            135deg,
            #111b33,
            #203a63
        );
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(20,35,65,0.12);
    }

    .hero h1 {
        margin: 0;
        font-size: 30px;
    }

    .hero p {
        margin: 7px 0 0 0;
        opacity: 0.88;
    }

    .kpi {
        background: white;
        border: 1px solid #e2e7ef;
        border-radius: 14px;
        padding: 14px;
        min-height: 82px;
        box-shadow: 0 3px 12px rgba(20,35,65,0.04);
    }

    .kpi small {
        color: #6b778c;
    }

    .kpi b {
        display: block;
        font-size: 22px;
        color: #17233c;
        margin-top: 4px;
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
        <h1>⚗️ Reactor Scale-Up Engineering Studio</h1>
        <p>
            Process requirement → mixing mechanism → agitator train →
            reactor geometry → scale-up → validation → recommendation
        </p>
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
        "Process requirement",
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

    basis = st.selectbox(
        "Scale-up basis",
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

    st.caption(
        "Screening tool. Final design should be validated "
        "against pilot data, vendor curves and detailed "
        "process/mechanical design."
    )


# ============================================================
# BASIC DESIGN INPUTS
# ============================================================

V_col, T_col, H_col, RHO_col = st.columns(4)

with V_col:

    workV = st.number_input(
        "Working volume (m³)",
        min_value=0.1,
        max_value=5000.0,
        value=3.0,
        step=0.1,
    )

with T_col:

    tankD = st.number_input(
        "Tank ID (m)",
        min_value=0.2,
        max_value=20.0,
        value=1.5,
        step=0.01,
    )

with H_col:

    straightH = st.number_input(
        "Straight side (m)",
        min_value=0.2,
        max_value=30.0,
        value=2.0,
        step=0.01,
    )

with RHO_col:

    density = st.number_input(
        "Density (kg/m³)",
        min_value=1.0,
        max_value=5000.0,
        value=1000.0,
        step=1.0,
    )


# ============================================================
# FLUID / REACTOR INPUTS
# ============================================================

A_col, B_col, C_col, D_col = st.columns(4)

with A_col:

    visc_cp = st.number_input(
        "Viscosity (cP)",
        min_value=0.1,
        max_value=1_000_000.0,
        value=10.0,
        step=0.1,
    )

with B_col:

    bottom = st.selectbox(
        "Bottom head",
        [
            "Flat Bottom",
            "2:1 Ellipsoidal",
            "10% Torispherical",
            "6% Torispherical",
            "Hemispherical",
            "Conical",
        ],
    )

with C_col:

    top = st.selectbox(
        "Top head",
        [
            "Flat Bottom",
            "2:1 Ellipsoidal",
            "10% Torispherical",
            "6% Torispherical",
            "Hemispherical",
            "Conical",
        ],
    )

with D_col:

    baffles = st.number_input(
        "Baffles",
        min_value=0,
        max_value=12,
        value=4,
        step=1,
    )


# ============================================================
# REACTOR GEOMETRY
# ============================================================

totalV = calculate_total_volume(
    tankD,
    straightH,
    bottom,
    top,
)


# Prevent impossible numerical input from breaking
# the liquid-height calculation.
effective_workV = min(
    float(workV),
    float(totalV) if totalV > 0 else float(workV),
)


liquidH = liquid_height_from_volume(
    effective_workV,
    tankD,
    straightH,
    bottom,
    top,
)


fill = (
    100.0 * workV / totalV
    if totalV > 0
    else 0.0
)


st.subheader("Reactor Geometry")

st.info(
    f"Capacity: **{totalV:.3f} m³**  |  "
    f"Liquid height: **{liquidH:.3f} m**  |  "
    f"Fill: **{fill:.1f}%**"
)


if workV > totalV:

    st.warning(
        "Working volume exceeds calculated reactor capacity. "
        "The 3D visualization is limited to vessel geometry, "
        "while the reported fill percentage remains based on "
        "the entered working volume."
    )


# ============================================================
# AGITATOR TRAIN
# ============================================================

st.subheader("Independent Agitator Train")

nstages = st.number_input(
    "Independent agitator stages",
    min_value=1,
    max_value=3,
    value=2,
    step=1,
)

nstages = int(nstages)

stages = []

cols = st.columns(nstages)


for i, col in enumerate(cols, 1):

    with col:

        st.markdown(f"### Stage {i}")

        name = st.selectbox(
            "Agitator",
            list(AGITATORS.keys()),
            index=min(i - 1, len(AGITATORS) - 1),
            key=f"ag_{i}",
        )

        spec = AGITATORS[name]

        ratio = st.number_input(
            "Impeller D/T",
            min_value=0.10,
            max_value=0.95,
            value=float(spec["D_T"]),
            step=0.01,
            key=f"dt_{i}",
        )

        default_rpm = (
            40.0
            if name in ["Anchor", "Helical Ribbon"]
            else 120.0
        )

        rpm = st.number_input(
            "RPM",
            min_value=1.0,
            max_value=1500.0,
            value=default_rpm,
            step=1.0,
            key=f"rpm_{i}",
        )

        nimp = st.number_input(
            "Impellers in stage",
            min_value=1,
            max_value=6,
            value=1,
            step=1,
            key=f"ni_{i}",
        )

        elev = st.number_input(
            "Elevation from bottom (m)",
            min_value=0.0,
            max_value=max(straightH, 0.1),
            value=min(
                0.35 * straightH,
                straightH,
            ),
            step=0.01,
            key=f"el_{i}",
        )

        clr = st.number_input(
            "Bottom clearance (m)",
            min_value=0.01,
            max_value=max(tankD, 0.2),
            value=max(
                0.15 * tankD,
                0.02,
            ),
            step=0.01,
            key=f"cl_{i}",
        )

        st.caption(
            f"Np = {spec['Np'] if spec['Np'] is not None else 'Vendor'} | "
            f"Nq = {spec['Nq'] if spec['Nq'] is not None else 'Vendor'} | "
            f"{spec['flow']}"
        )

        stages.append(
            {
                "agitator": name,
                "Np": spec["Np"],
                "Nq": spec["Nq"],
                "impeller_diameter_m": tankD * ratio,
                "rpm": rpm,
                "number_impellers": int(nimp),
                "elevation_m": elev,
                "clearance_m": clr,
                "density_kg_m3": density,
                "viscosity_pa_s": visc_cp / 1000.0,
            }
        )


# ============================================================
# CALCULATIONS
# ============================================================

results, train = calculate_train(
    stages,
    workV,
)


# ============================================================
# Njs
# ============================================================

if (
    "Solid" in process_type
    or "Crystallization" in process_type
):

    A_col, B_col, C_col, D_col = st.columns(4)

    with A_col:

        solids = st.number_input(
            "Solids wt%",
            min_value=0.0,
            max_value=80.0,
            value=10.0,
            step=0.5,
        )

    with B_col:

        dp = st.number_input(
            "Particle d50 (mm)",
            min_value=0.001,
            max_value=20.0,
            value=0.5,
            step=0.01,
        )

    with C_col:

        solidrho = st.number_input(
            "Solid density (kg/m³)",
            min_value=1.0,
            max_value=10000.0,
            value=1500.0,
            step=10.0,
        )

    with D_col:

        S = st.number_input(
            "Njs S constant",
            min_value=0.1,
            max_value=20.0,
            value=5.0,
            step=0.1,
        )

    for x in results:

        x["Njs_s_inv"] = zwietering_njs(
            x,
            solids,
            dp / 1000.0,
            solidrho,
            density,
            S,
        )

else:

    for x in results:
        x["Njs_s_inv"] = None


# ============================================================
# VALIDATION
# ============================================================

geom = {
    "tank_diameter_m": tankD,
    "working_volume_m3": workV,
    "total_volume_m3": totalV,
    "liquid_height_m": liquidH,
    "baffles": baffles,
    "froude": (
        max(
            [x.get("Fr", 0.0) for x in results]
        )
        if results
        else 0.0
    ),
}


checks = validate_design(
    geom,
    results,
)


recs = recommendations(
    process_type,
    train,
)


# ============================================================
# KPI CALCULATIONS
# ============================================================

passed = sum(
    1
    for x in checks
    if len(x) >= 2 and x[1]
)

total_checks = len(checks)


validation_text = (
    f"{passed}/{total_checks} PASS"
    if total_checks
    else "N/A"
)


kpis = [
    (
        "Working Volume",
        f"{workV:.2f} m³",
    ),
    (
        "Fill",
        f"{fill:.1f}%",
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
        f"{train['Q_per_volume_1_s']:.4f} s⁻¹",
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
        validation_text,
    ),
]


# ============================================================
# KPI DISPLAY
# ============================================================

for j in range(0, len(kpis), 4):

    cs = st.columns(4)

    for cc, (lab, val) in zip(
        cs,
        kpis[j:j + 4],
    ):

        cc.markdown(
            f"""
            <div class="kpi">
                <small>{lab}</small>
                <b>{val}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.divider()


# ============================================================
# MAIN TABS
# ============================================================

t1, t2, t3, t4, t5 = st.tabs(
    [
        "Performance",
        "Scale-Up",
        "Validation",
        "3D Mixing",
        "Engineering Report",
    ]
)


# ============================================================
# PERFORMANCE
# ============================================================

with t1:

    st.subheader(
        "Agitator Stage Performance"
    )

    rows = []

    for i, x in enumerate(results):

        njs = x.get("Njs_s_inv")

        n_over_njs = (
            (x["rpm"] / 60.0) / njs
            if njs and njs > 0
            else None
        )

        rows.append(
            {
                "Stage": i + 1,
                "Agitator": x["agitator"],
                "D (m)": x["impeller_diameter_m"],
                "RPM": x["rpm"],
                "Re": x.get("Re"),
                "Fr": x.get("Fr"),
                "Tip speed (m/s)": x.get(
                    "tip_speed_m_s",
                    x.get("tip_speed"),
                ),
                "Power (kW)": x.get("power_kw"),
                "Q (m³/h)": x.get("Q_m3_h"),
                "Torque (N·m)": x.get(
                    "torque_Nm",
                    x.get("torque_nm"),
                ),
                "Njs (s⁻¹)": njs,
                "N/Njs": n_over_njs,
            }
        )

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# SCALE-UP
# ============================================================

with t2:

    st.subheader(
        "Reference → Target Scale-Up"
    )

    a, b = st.columns(2)

    with a:

        rv = st.number_input(
            "Reference volume (m³)",
            min_value=0.01,
            max_value=5000.0,
            value=max(workV / 10.0, 0.1),
            step=0.1,
        )

        rd = st.number_input(
            "Reference impeller D (m)",
            min_value=0.01,
            max_value=10.0,
            value=max(
                results[0]["impeller_diameter_m"] * 0.7,
                0.05,
            ),
            step=0.01,
        )

        rr = st.number_input(
            "Reference RPM",
            min_value=1.0,
            max_value=1500.0,
            value=float(results[0]["rpm"]),
            step=1.0,
        )

    with b:

        td = st.number_input(
            "Target impeller D (m)",
            min_value=0.01,
            max_value=10.0,
            value=float(
                results[0]["impeller_diameter_m"]
            ),
            step=0.01,
        )

        sr = scale_rpm(
            {
                "rpm": rr,
                "impeller_diameter_m": rd,
                "volume_m3": rv,
            },
            {
                "impeller_diameter_m": td,
                "volume_m3": workV,
            },
            basis,
        )

        st.success(
            f"Calculated target RPM: **{sr:.1f} rpm**"
        )

        st.caption(
            "Starting-point criterion only. "
            "Check geometry, P/V, Q/V, N/Njs, "
            "blend time and heat transfer."
        )


# ============================================================
# VALIDATION
# ============================================================

with t3:

    st.subheader(
        "Engineering Validation"
    )

    for item in checks:

        if len(item) >= 3:

            name, ok, message = item[:3]

            if ok:

                st.success(
                    f"PASS — {name}: {message}"
                )

            else:

                st.warning(
                    f"REVIEW — {name}: {message}"
                )

    st.subheader(
        "Engineering Recommendations"
    )

    for r in recs:

        st.info(r)


# ============================================================
# 3D MIXING
# ============================================================

with t4:

    st.subheader(
        "3D Reactor & Mixing Visualization"
    )

    st.caption(
        "Interactive engineering visualization showing "
        "reactor geometry, liquid volume, baffles, shaft, "
        "independent agitator stages and conceptual flow paths."
    )

    try:

        fig = create_reactor_figure(
            tankD,
            straightH,
            liquidH,
            results,
            baffles,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

        st.info(
            "⚠️ CFD-inspired visualization only. "
            "The displayed flow paths are conceptual and "
            "are not calculated CFD velocity or turbulence fields."
        )

    except Exception as exc:

        st.error(
            "3D visualization could not be generated."
        )

        st.exception(exc)


# ============================================================
# ENGINEERING REPORT
# ============================================================

with t5:

    st.subheader(
        "Engineering Report"
    )

    report_data = {
        "process_type": process_type,
        "geometry": geom,
        "stages": results,
        "train": train,
        "checks": checks,
        "recommendations": recs,
    }

    try:

        pdf = build_pdf(
            report_data
        )

        st.download_button(
            "Download Engineering PDF",
            pdf,
            "reactor_scaleup_engineering_report.pdf",
            "application/pdf",
            use_container_width=True,
        )

    except Exception as exc:

        st.error(
            "Engineering report could not be generated."
        )

        st.exception(exc)
