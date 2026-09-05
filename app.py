import math
import streamlit as st
import pandas as pd

from calculations.engine import calculate_reactor
from calculations.scaleup import calculate_scaleup
from calculations.validation import validate_reactor

from libraries.agitator_geometry import AGITATORS
from libraries.reactor_geometry import (
    REACTOR_HEADS,
    calculate_total_volume,
    liquid_height_from_volume,
)

from visualization.reactor_3d import create_reactor_animation


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f5f7fa;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e3e7ed;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        text-align: center;
    }

    .section-card {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #e3e7ed;
        margin-bottom: 15px;
    }

    .small-text {
        color: #667085;
        font-size: 0.85rem;
    }

    .success-box {
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #b7dfc5;
        background: #f0fff4;
    }

    .warning-box {
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #f2cf75;
        background: #fffaf0;
    }

    .danger-box {
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #efb2b2;
        background: #fff5f5;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.title("🏭 Reactor Scale-Up Engineering Studio")

st.markdown(
    "**Professional screening platform for reactor geometry, "
    "mixing, agitation, scale-up similarity and engineering validation.**"
)

st.caption(
    "Lab → Pilot → Commercial  |  "
    "Mixing • Geometry • Scale-Up • Mechanical Screening"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Study Configuration")

project_name = st.sidebar.text_input(
    "Project / Study Name",
    value="Reactor Scale-Up Study",
)

prepared_by = st.sidebar.text_input(
    "Prepared By",
    value="Process Engineering",
)

study_mode = st.sidebar.selectbox(
    "Study Mode",
    [
        "Single Reactor",
        "Lab vs Pilot",
        "Pilot vs Commercial",
        "Lab vs Commercial",
        "Lab vs Pilot vs Commercial",
    ],
)

process_type = st.sidebar.selectbox(
    "Process / Reaction Type",
    [
        "Liquid-Liquid",
        "Solid-Liquid",
        "Gas-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
        "Precipitation",
        "Dissolution",
        "Extraction",
        "Neutralization",
        "General Mixing",
    ],
)

scaleup_basis = st.sidebar.selectbox(
    "Scale-Up Basis",
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


# =========================================================
# PROCESS GUIDANCE
# =========================================================

PROCESS_GUIDANCE = {

    "Liquid-Liquid":
        "Focus on blending, circulation, droplet dispersion and mixing time.",

    "Solid-Liquid":
        "Focus on solids suspension, Njs, just-suspended condition and circulation.",

    "Gas-Liquid":
        "Focus on gas dispersion, P/V, tip speed, flooding and KLa.",

    "Gas-Liquid-Solid":
        "Consider gas dispersion + solids suspension simultaneously.",

    "Crystallization":
        "Focus on suspension, supersaturation control, shear and heat transfer.",

    "Precipitation":
        "Consider mixing intensity, local supersaturation and micromixing.",

    "Dissolution":
        "Focus on solids suspension, wetting and liquid circulation.",

    "Extraction":
        "Focus on phase dispersion, interfacial area and coalescence.",

    "Neutralization":
        "Focus on blending, heat release, addition point and local concentration.",

    "General Mixing":
        "Use P/V, tip speed, Re, Fr and pumping/volume as initial screening criteria.",
}


with st.sidebar.expander("💡 Engineering Guidance"):

    st.info(
        PROCESS_GUIDANCE.get(
            process_type,
            "Use engineering judgement and validated correlations.",
        )
    )


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
# STORAGE
# =========================================================

reactors = {}


# =========================================================
# REACTOR INPUTS
# =========================================================

st.header("1️⃣ Reactor Definition")

for reactor_name in reactor_names:

    st.subheader(f"🔹 {reactor_name} Reactor")

    with st.container():

        col1, col2, col3 = st.columns(3)

        # -------------------------------------------------
        # PROCESS DATA
        # -------------------------------------------------

        with col1:

            working_volume = st.number_input(
                f"{reactor_name} Working Volume [m³]",
                min_value=0.01,
                value=1.00 if reactor_name == "Lab" else 5.00,
                step=0.10,
                key=f"{reactor_name}_volume",
            )

            density = st.number_input(
                f"{reactor_name} Density [kg/m³]",
                min_value=1.0,
                value=1000.0,
                step=10.0,
                key=f"{reactor_name}_density",
            )

            viscosity = st.number_input(
                f"{reactor_name} Viscosity [mPa·s]",
                min_value=0.01,
                value=1.0,
                step=0.1,
                key=f"{reactor_name}_viscosity",
            )

            surface_tension = st.number_input(
                f"{reactor_name} Surface Tension [mN/m]",
                min_value=0.01,
                value=30.0,
                step=1.0,
                key=f"{reactor_name}_surface_tension",
            )

        # -------------------------------------------------
        # VESSEL GEOMETRY
        # -------------------------------------------------

        with col2:

            tank_id = st.number_input(
                f"{reactor_name} Tank ID [mm]",
                min_value=100.0,
                value=1000.0 if reactor_name == "Lab" else 1800.0,
                step=50.0,
                key=f"{reactor_name}_tank_id",
            )

            straight_height = st.number_input(
                f"{reactor_name} Straight Height [mm]",
                min_value=100.0,
                value=1500.0,
                step=50.0,
                key=f"{reactor_name}_straight_height",
            )

            bottom_type = st.selectbox(
                f"{reactor_name} Bottom Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{reactor_name}_bottom",
            )

            top_type = st.selectbox(
                f"{reactor_name} Top Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{reactor_name}_top",
            )

        # -------------------------------------------------
        # AGITATION
        # -------------------------------------------------

        with col3:

            agitator_type = st.selectbox(
                f"{reactor_name} Agitator",
                list(AGITATORS.keys()),
                index=1,
                key=f"{reactor_name}_agitator",
            )

            agitator_info = AGITATORS[agitator_type]

            default_ratio = agitator_info.get(
                "default_diameter_ratio",
                0.40,
            )

            default_impeller_diameter = (
                tank_id *
                default_ratio
            )

            impeller_diameter = st.number_input(
                f"{reactor_name} Impeller Diameter [mm]",
                min_value=20.0,
                value=float(
                    default_impeller_diameter
                ),
                step=10.0,
                key=f"{reactor_name}_impeller",
            )

            number_impellers = st.number_input(
                f"{reactor_name} Number of Impellers",
                min_value=1,
                max_value=6,
                value=1,
                step=1,
                key=f"{reactor_name}_nimp",
            )

            rpm = st.number_input(
                f"{reactor_name} Agitator Speed [RPM]",
                min_value=1.0,
                value=120.0,
                step=5.0,
                key=f"{reactor_name}_rpm",
            )

            baffles = st.number_input(
                f"{reactor_name} Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{reactor_name}_baffles",
            )


    # =====================================================
    # UNIT CONVERSIONS
    # =====================================================

    D = tank_id / 1000.0

    H = straight_height / 1000.0

    Di = impeller_diameter / 1000.0

    mu = viscosity / 1000.0

    sigma = surface_tension / 1000.0


    # =====================================================
    # VESSEL VOLUME
    # =====================================================

    vessel_volume = calculate_total_volume(
        D=D,
        straight_height=H,
        bottom_type=bottom_type,
        top_type=top_type,
    )


    # =====================================================
    # LIQUID HEIGHT
    # =====================================================

    liquid_height, calculated_total_volume = (
        liquid_height_from_volume(
            working_volume=working_volume,
            D=D,
            straight_height=H,
            bottom_type=bottom_type,
            top_type=top_type,
        )
    )


    # =====================================================
    # GEOMETRY RATIOS
    # =====================================================

    fill_percent = (
        working_volume /
        vessel_volume *
        100.0
        if vessel_volume > 0
        else 0.0
    )

    H_over_D = (
        liquid_height / D
        if D > 0
        else 0.0
    )

    Di_over_D = (
        Di / D
        if D > 0
        else 0.0
    )


    # =====================================================
    # REACTOR CALCULATION
    # =====================================================

    try:

        results = calculate_reactor(

            volume_m3=working_volume,

            tank_diameter_m=D,

            liquid_height_m=liquid_height,

            density_kg_m3=density,

            viscosity_pa_s=mu,

            surface_tension_n_m=sigma,

            rpm=rpm,

            impeller_diameter_m=Di,

            number_impellers=int(
                number_impellers
            ),

            agitator=agitator_type,

        )

    except Exception as e:

        st.error(
            f"Calculation error for {reactor_name}: {e}"
        )

        st.stop()


    # =====================================================
    # VALIDATION
    # =====================================================

    validation = validate_reactor(

        volume_m3=working_volume,

        vessel_volume_m3=vessel_volume,

        tank_diameter_m=D,

        straight_height_m=H,

        liquid_height_m=liquid_height,

        impeller_diameter_m=Di,

        number_impellers=int(
            number_impellers
        ),

        number_baffles=int(
            baffles
        ),

        rpm=rpm,

        agitator=agitator_type,

        density_kg_m3=density,

        viscosity_pa_s=mu,

    )


    # =====================================================
    # VORTEX SCREENING
    # =====================================================

    vortex_depth = 0.0

    if baffles == 0:

        vortex_depth = (
            0.10 *
            liquid_height
        )

    elif baffles < 4:

        vortex_depth = (
            0.05 *
            liquid_height
        )

    else:

        vortex_depth = 0.01 * liquid_height


    # =====================================================
    # STORE DATA
    # =====================================================

    reactors[reactor_name] = {

        "working_volume": working_volume,

        "density": density,

        "viscosity": viscosity,

        "surface_tension": surface_tension,

        "tank_id_m": D,

        "straight_height_m": H,

        "bottom_type": bottom_type,

        "top_type": top_type,

        "agitator_type": agitator_type,

        "impeller_diameter_m": Di,

        "number_impellers": int(
            number_impellers
        ),

        "rpm": rpm,

        "baffles": int(
            baffles
        ),

        "vessel_volume_m3": vessel_volume,

        "liquid_height_m": liquid_height,

        "fill_percent": fill_percent,

        "H_over_D": H_over_D,

        "Di_over_D": Di_over_D,

        "vortex_depth": vortex_depth,

        "results": results,

        "validation": validation,

    }


# =========================================================
# KPI DASHBOARD
# =========================================================

st.header("2️⃣ Engineering KPI Dashboard")


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    result = data["results"]

    st.subheader(
        f"📊 {reactor_name} Reactor Performance"
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    # -----------------------------------------------------
    # POWER
    # -----------------------------------------------------

    with c1:

        power = result.get(
            "power_kw"
        )

        if power is not None:

            st.metric(
                "Power",
                f"{power:.2f} kW",
            )

        else:

            st.metric(
                "Power",
                "N/A",
            )


    # -----------------------------------------------------
    # P/V
    # -----------------------------------------------------

    with c2:

        pv = result.get(
            "power_volume"
        )

        if pv is not None:

            st.metric(
                "P/V",
                f"{pv:.1f} W/m³",
            )

        else:

            st.metric(
                "P/V",
                "N/A",
            )


    # -----------------------------------------------------
    # TIP SPEED
    # -----------------------------------------------------

    with c3:

        tip_speed = result.get(
            "tip_speed"
        )

        st.metric(
            "Tip Speed",
            f"{tip_speed:.2f} m/s",
        )


    # -----------------------------------------------------
    # REYNOLDS
    # -----------------------------------------------------

    with c4:

        reynolds = result.get(
            "Re"
        )

        st.metric(
            "Re",
            f"{reynolds:,.0f}",
        )


    # -----------------------------------------------------
    # FLOW
    # -----------------------------------------------------

    with c5:

        pumping = result.get(
            "pumping_m3_h"
        )

        if pumping is not None:

            st.metric(
                "Pumping",
                f"{pumping:.2f} m³/h",
            )

        else:

            st.metric(
                "Pumping",
                "N/A",
            )


    # -----------------------------------------------------
    # TURNOVER
    # -----------------------------------------------------

    with c6:

        turnover = result.get(
            "turnover_time_min"
        )

        if turnover is not None:

            st.metric(
                "Turnover",
                f"{turnover:.1f} min",
            )

        else:

            st.metric(
                "Turnover",
                "N/A",
            )


# =========================================================
# GEOMETRY SUMMARY
# =========================================================

st.header("3️⃣ Reactor Geometry Summary")


geometry_rows = []


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    geometry_rows.append({

        "Reactor":
            reactor_name,

        "Working Volume [m³]":
            round(
                data["working_volume"],
                3,
            ),

        "Total Vessel Volume [m³]":
            round(
                data["vessel_volume_m3"],
                3,
            ),

        "Fill [%]":
            round(
                data["fill_percent"],
                1,
            ),

        "Tank ID [m]":
            round(
                data["tank_id_m"],
                3,
            ),

        "Liquid Height [m]":
            round(
                data["liquid_height_m"],
                3,
            ),

        "H/T":
            round(
                data["H_over_D"],
                2,
            ),

        "Impeller/Tank":
            round(
                data["Di_over_D"],
                3,
            ),

        "Impeller [m]":
            round(
                data["impeller_diameter_m"],
                3,
            ),

        "Impellers":
            data["number_impellers"],

        "RPM":
            round(
                data["rpm"],
                1,
            ),

        "Agitator":
            data["agitator_type"],

    })


geometry_df = pd.DataFrame(
    geometry_rows
)

st.dataframe(
    geometry_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# SCALE-UP COMPARISON
# =========================================================

if len(reactor_names) >= 2:

    st.header("4️⃣ Scale-Up Comparison")

    base_name = reactor_names[0]

    target_names = reactor_names[1:]


    base_data = reactors[base_name]


    for target_name in target_names:

        target_data = reactors[target_name]

        base_result = base_data["results"]

        target_result = target_data["results"]


        base_for_scaleup = {

            "working_volume":
                base_data["working_volume"],

            "impeller_diameter_m":
                base_data["impeller_diameter_m"],

            "rpm":
                base_data["rpm"],

            "tip_speed":
                base_result.get(
                    "tip_speed"
                ),

            "power_volume":
                base_result.get(
                    "power_volume"
                ),

            "qv_1_h":
                base_result.get(
                    "qv_1_h"
                ),

            "pumping_m3_h":
                base_result.get(
                    "pumping_m3_h"
                ),

            "density":
                base_data["density"],

            "viscosity_pa_s":
                base_result.get(
                    "viscosity_pa_s"
                ),

            "Np":
                base_result.get(
                    "Np"
                ),

            "Nq":
                base_result.get(
                    "Nq"
                ),

        }


        target_for_scaleup = {

            "working_volume":
                target_data["working_volume"],

            "impeller_diameter_m":
                target_data["impeller_diameter_m"],

            "rpm":
                target_data["rpm"],

            "tip_speed":
                target_result.get(
                    "tip_speed"
                ),

            "power_volume":
                target_result.get(
                    "power_volume"
                ),

            "qv_1_h":
                target_result.get(
                    "qv_1_h"
                ),

            "pumping_m3_h":
                target_result.get(
                    "pumping_m3_h"
                ),

            "density":
                target_data["density"],

            "viscosity_pa_s":
                target_result.get(
                    "viscosity_pa_s"
                ),

            "Np":
                target_result.get(
                    "Np"
                ),

            "Nq":
                target_result.get(
                    "Nq"
                ),

        }


        scaleup = calculate_scaleup(

            base=base_for_scaleup,

            target=target_for_scaleup,

            basis=scaleup_basis,

        )


        st.subheader(
            f"{base_name} → {target_name}"
        )


        s1, s2, s3 = st.columns(3)


        with s1:

            target_rpm = scaleup.get(
                "target_rpm"
            )

            if target_rpm is not None:

                st.metric(
                    "Calculated Target RPM",
                    f"{target_rpm:.1f}",
                )

            else:

                st.metric(
                    "Calculated Target RPM",
                    "N/A",
                )


        with s2:

            target_tip = scaleup.get(
                "target_tip_speed"
            )

            if target_tip is not None:

                st.metric(
                    "Target Tip Speed",
                    f"{target_tip:.2f} m/s",
                )

            else:

                st.metric(
                    "Target Tip Speed",
                    "N/A",
                )


        with s3:

            st.metric(
                "Scale-Up Basis",
                scaleup_basis,
            )


        st.info(
            scaleup.get(
                "message",
                "Review scale-up result.",
            )
        )


# =========================================================
# VALIDATION
# =========================================================

st.header("5️⃣ Engineering Validation")


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    validation = data["validation"]


    st.subheader(
        f"🔍 {reactor_name} Validation"
    )


    if validation["overall"] == "PASS":

        st.success(
            f"Overall Status: PASS | "
            f"{validation['warnings']} warning(s)"
        )

    elif validation["overall"] == "REVIEW":

        st.warning(
            f"Overall Status: REVIEW | "
            f"{validation['warnings']} warning(s)"
        )

    else:

        st.error(
            f"Overall Status: FAIL | "
            f"{validation['failures']} failure(s)"
        )


    validation_rows = []


    for check in validation["checks"]:

        validation_rows.append({

            "Status":
                check["severity"],

            "Engineering Check":
                check["message"],

        })


    validation_df = pd.DataFrame(
        validation_rows
    )


    st.dataframe(
        validation_df,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 3D REACTOR VISUALIZATION
# =========================================================

st.header("6️⃣ 3D Reactor Visualization")


selected_reactor = st.selectbox(
    "Select Reactor for 3D Visualization",
    reactor_names,
)


data = reactors[
    selected_reactor
]


try:

    fig = create_reactor_animation(

        D=data["tank_id_m"],

        straight_height=data[
            "straight_height_m"
        ],

        bottom_type=data[
            "bottom_type"
        ],

        top_type=data[
            "top_type"
        ],

        liquid_height=data[
            "liquid_height_m"
        ],

        agitator=data[
            "agitator_type"
        ],

        impeller_diameter=data[
            "impeller_diameter_m"
        ],

        number_impellers=data[
            "number_impellers"
        ],

        rpm=data[
            "rpm"
        ],

        number_baffles=data[
            "baffles"
        ],

        vortex_depth=data[
            "vortex_depth"
        ],

        frames_count=36,

    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )

except Exception as e:

    st.error(
        f"3D visualization error: {e}"
    )


# =========================================================
# ENGINEERING INSIGHTS
# =========================================================

st.header("7️⃣ Engineering Insights")


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    result = data["results"]


    st.subheader(
        f"💡 {reactor_name}"
    )


    insights = []


    # -----------------------------------------------------
    # FILL
    # -----------------------------------------------------

    fill = data["fill_percent"]

    if fill < 40:

        insights.append(
            "⚠️ Low operating fill. "
            "Review impeller coverage, circulation and headspace."
        )

    elif fill > 85:

        insights.append(
            "⚠️ High operating fill. "
            "Review headspace, vortex and gas disengagement."
        )

    else:

        insights.append(
            "✅ Operating fill is within a commonly screened range."
        )


    # -----------------------------------------------------
    # BAFFLES
    # -----------------------------------------------------

    if data["baffles"] < 4:

        insights.append(
            "⚠️ Fewer than four baffles selected. "
            "Check vortexing and rotational flow."
        )

    else:

        insights.append(
            "✅ Four or more baffles selected for vortex suppression screening."
        )


    # -----------------------------------------------------
    # IMPeller ratio
    # -----------------------------------------------------

    ratio = data["Di_over_D"]

    if ratio < 0.20:

        insights.append(
            "⚠️ Small impeller relative to tank diameter. "
            "Check bulk circulation."
        )

    elif ratio > 0.60:

        insights.append(
            "⚠️ Large impeller relative to tank diameter. "
            "Review power, clearance and mechanical loads."
        )

    else:

        insights.append(
            "✅ Impeller/tank ratio is within a commonly screened range."
        )


    # -----------------------------------------------------
    # REYNOLDS
    # -----------------------------------------------------

    Re = result.get(
        "Re",
        0,
    )


    if Re < 10:

        insights.append(
            "🔵 Laminar mixing regime detected."
        )

    elif Re < 10000:

        insights.append(
            "🟡 Transitional mixing regime detected."
        )

    else:

        insights.append(
            "🟢 Turbulent mixing regime detected."
        )


    # -----------------------------------------------------
    # VISCOSITY
    # -----------------------------------------------------

    if data["viscosity"] > 100:

        insights.append(
            "⚠️ High viscosity system. "
            "Verify impeller selection and power correlation."
        )


    for insight in insights:

        st.write(
            insight
        )


# =========================================================
# STUDY SUMMARY
# =========================================================

st.header("8️⃣ Study Summary")


summary_rows = []


for reactor_name in reactor_names:

    data = reactors[reactor_name]

    result = data["results"]

    summary_rows.append({

        "Reactor":
            reactor_name,

        "Volume [m³]":
            round(
                data["working_volume"],
                3,
            ),

        "RPM":
            round(
                data["rpm"],
                1,
            ),

        "Impeller [m]":
            round(
                data["impeller_diameter_m"],
                3,
            ),

        "Tip Speed [m/s]":
            round(
                result.get(
                    "tip_speed",
                    0,
                ),
                2,
            ),

        "P/V [W/m³]":
            round(
                result.get(
                    "power_volume",
                    0,
                )
                or 0,
                2,
            ),

        "Re":
            round(
                result.get(
                    "Re",
                    0,
                ),
                0,
            ),

        "Pumping [m³/h]":
            round(
                result.get(
                    "pumping_m3_h",
                    0,
                )
                or 0,
                2,
            ),

        "Fill [%]":
            round(
                data["fill_percent"],
                1,
            ),

        "Validation":
            data["validation"][
                "overall"
            ],

    })


summary_df = pd.DataFrame(
    summary_rows
)


st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# LIMITATIONS
# =========================================================

with st.expander(
    "⚠️ Engineering Limitations / Important Note"
):

    st.warning(
        """
        This dashboard is intended for engineering screening,
        comparison and preliminary scale-up assessment.

        The following should be validated before final equipment
        design or commercial implementation:

        • Vendor-specific impeller Np/Nq data
        • Njs / solids suspension correlations
        • Blend time correlations
        • Gas dispersion and flooding limits
        • KLa correlations
        • Mechanical shaft and seal design
        • Motor sizing and service factor
        • Critical speed
        • Torque and shaft stress
        • Reactor pressure/vacuum design
        • Exact ASME / EN head geometry
        • Heat-transfer calculations
        • Process-specific pilot data

        Final design should be based on validated correlations,
        vendor data and plant/pilot test results.
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    f"Project: {project_name}  |  "
    f"Prepared by: {prepared_by}  |  "
    f"Reactor Scale-Up Engineering Studio"
)

st.caption(
    "Screening tool — engineering judgement and validated "
    "design methods are required for final equipment specification."
)
