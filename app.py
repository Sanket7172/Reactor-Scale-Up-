import streamlit as st

from calculations.engine import calculate_reactor

from libraries.agitator_geometry import AGITATORS

from libraries.reactor_geometry import (
    REACTOR_HEADS,
    calculate_total_volume,
    liquid_height_from_volume,
)

from visualization.reactor_3d import (
    create_reactor_animation,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# TITLE
# =========================================================

st.title(
    "🏭 Reactor Scale-Up Engineering Dashboard"
)

st.caption(
    "Process Engineering • Mixing • Agitation • "
    "Scale-Up • Reactor Geometry • 3D Mixing Visualization"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📋 Project")

project_name = st.sidebar.text_input(
    "Project Name",
    value="Reactor Scale-Up Study",
)

engineer = st.sidebar.text_input(
    "Prepared By",
    value="",
)


# =========================================================
# STUDY MODE
# =========================================================

st.sidebar.header("📊 Study Mode")

study_mode = st.sidebar.selectbox(
    "Select Study",
    [
        "Single Reactor",
        "Lab vs Pilot",
        "Pilot vs Commercial",
        "Lab vs Commercial",
        "Lab vs Pilot vs Commercial",
    ],
)


# =========================================================
# SELECT REACTORS
# =========================================================

if study_mode == "Single Reactor":

    selected_reactors = [
        "Reactor"
    ]

elif study_mode == "Lab vs Pilot":

    selected_reactors = [
        "Lab",
        "Pilot",
    ]

elif study_mode == "Pilot vs Commercial":

    selected_reactors = [
        "Pilot",
        "Commercial",
    ]

elif study_mode == "Lab vs Commercial":

    selected_reactors = [
        "Lab",
        "Commercial",
    ]

else:

    selected_reactors = [
        "Lab",
        "Pilot",
        "Commercial",
    ]


# =========================================================
# PROCESS INFORMATION
# =========================================================

st.header("1. Process Information")

reaction_type = st.selectbox(
    "Reaction / Process Type",
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
        "Other",
    ],
)


# =========================================================
# SCALE-UP BASIS
# =========================================================

scale_up_basis = st.selectbox(
    "Scale-Up Basis",
    [
        "Constant P/V",
        "Constant Tip Speed",
        "Constant RPM",
        "Constant Froude Number",
        "Constant Reynolds Number",
        "Constant N/Njs",
        "Constant Pumping / Volume",
        "Constant KLa",
        "User Defined",
    ],
)


# =========================================================
# REACTOR DATA STORAGE
# =========================================================

reactors = {}


# =========================================================
# REACTOR INPUTS
# =========================================================

for reactor_name in selected_reactors:

    st.header(
        f"2. {reactor_name} Reactor"
    )

    with st.expander(
        f"{reactor_name} Reactor Configuration",
        expanded=True,
    ):

        # =================================================
        # GEOMETRY
        # =================================================

        st.subheader("🏭 Reactor Geometry")

        col1, col2, col3 = st.columns(3)

        with col1:

            working_volume = st.number_input(
                f"{reactor_name} Operating Liquid Volume (m³)",
                min_value=0.001,
                max_value=5000.0,
                value=1.0,
                step=0.1,
                key=f"{reactor_name}_volume",
            )

            tank_id = st.number_input(
                f"{reactor_name} Tank ID (mm)",
                min_value=100.0,
                max_value=20000.0,
                value=1200.0,
                step=10.0,
                key=f"{reactor_name}_id",
            )

            straight_height = st.number_input(
                f"{reactor_name} Straight Side Height (mm)",
                min_value=100.0,
                max_value=30000.0,
                value=1500.0,
                step=10.0,
                key=f"{reactor_name}_straight_height",
            )

        with col2:

            bottom_type = st.selectbox(
                f"{reactor_name} Bottom Geometry",
                list(REACTOR_HEADS.keys()),
                key=f"{reactor_name}_bottom",
            )

            top_type = st.selectbox(
                f"{reactor_name} Top Geometry",
                list(REACTOR_HEADS.keys()),
                key=f"{reactor_name}_top",
            )

        with col3:

            liquid_density = st.number_input(
                f"{reactor_name} Liquid Density (kg/m³)",
                min_value=1.0,
                max_value=5000.0,
                value=1000.0,
                step=10.0,
                key=f"{reactor_name}_density",
            )

            viscosity = st.number_input(
                f"{reactor_name} Viscosity (mPa·s)",
                min_value=0.01,
                max_value=100000.0,
                value=1.0,
                step=0.1,
                key=f"{reactor_name}_viscosity",
            )

            surface_tension = st.number_input(
                f"{reactor_name} Surface Tension (mN/m)",
                min_value=0.1,
                max_value=2000.0,
                value=72.0,
                step=0.1,
                key=f"{reactor_name}_surface_tension",
            )

        # =================================================
        # UNIT CONVERSION
        # =================================================

        tank_id_m = tank_id / 1000.0

        straight_height_m = (
            straight_height / 1000.0
        )

        surface_tension_n_m = (
            surface_tension / 1000.0
        )

        viscosity_pa_s = (
            viscosity / 1000.0
        )

        # =================================================
        # CALCULATE VESSEL VOLUME
        # =================================================

        vessel_volume = calculate_total_volume(
            D=tank_id_m,
            straight_height=straight_height_m,
            bottom_type=bottom_type,
            top_type=top_type,
        )

        # =================================================
        # AUTOMATIC LIQUID LEVEL
        # =================================================

        liquid_height_m, calculated_total_volume = (
            liquid_height_from_volume(
                working_volume=working_volume,
                D=tank_id_m,
                straight_height=straight_height_m,
                bottom_type=bottom_type,
                top_type=top_type,
            )
        )

        liquid_height_mm = (
            liquid_height_m * 1000.0
        )

        fill_percentage = (
            working_volume
            / vessel_volume
            * 100.0
            if vessel_volume > 0
            else 0.0
        )

        # =================================================
        # VOLUME VALIDATION
        # =================================================

        if working_volume > vessel_volume:

            st.error(
                f"❌ Operating volume "
                f"{working_volume:.2f} m³ exceeds the "
                f"calculated vessel volume "
                f"{vessel_volume:.2f} m³."
            )

            working_volume = vessel_volume

            liquid_height_m, calculated_total_volume = (
                liquid_height_from_volume(
                    working_volume=working_volume,
                    D=tank_id_m,
                    straight_height=straight_height_m,
                    bottom_type=bottom_type,
                    top_type=top_type,
                )
            )

            liquid_height_mm = (
                liquid_height_m * 1000.0
            )

            fill_percentage = 100.0

        # =================================================
        # SHOW AUTOMATIC LIQUID LEVEL
        # =================================================

        st.markdown(
            "### 💧 Calculated Operating Liquid Level"
        )

        g1, g2, g3, g4 = st.columns(4)

        g1.metric(
            "Vessel Volume",
            f"{vessel_volume:.2f} m³",
        )

        g2.metric(
            "Operating Volume",
            f"{working_volume:.2f} m³",
        )

        g3.metric(
            "Liquid Level",
            f"{liquid_height_mm:.0f} mm",
        )

        g4.metric(
            "Fill %",
            f"{fill_percentage:.1f}%",
        )

        st.info(
            "Liquid height is automatically calculated from "
            "operating liquid volume and reactor geometry. "
            "Manual liquid-height entry is not required."
        )

        # =================================================
        # AGITATOR
        # =================================================

        st.subheader("⚙️ Agitation System")

        agitator_type = st.selectbox(
            "Agitator Type",
            list(AGITATORS.keys()),
            key=f"{reactor_name}_agitator",
        )

        agitator_info = AGITATORS[
            agitator_type
        ]

        st.caption(
            f"Flow pattern: "
            f"{agitator_info.get('flow', 'N/A')} | "
            f"{agitator_info.get('description', '')}"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            default_impeller = (
                tank_id
                * agitator_info.get(
                    "default_diameter_ratio",
                    0.35,
                )
            )

            impeller_diameter = st.number_input(
                "Impeller Diameter (mm)",
                min_value=10.0,
                max_value=15000.0,
                value=float(
                    round(
                        default_impeller,
                        1,
                    )
                ),
                step=10.0,
                key=f"{reactor_name}_impeller_d",
            )

        with c2:

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{reactor_name}_impellers",
            )

        with c3:

            baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{reactor_name}_baffles",
            )

        with c4:

            rpm = st.number_input(
                "Agitator Speed (RPM)",
                min_value=0.1,
                max_value=1000.0,
                value=100.0,
                step=1.0,
                key=f"{reactor_name}_rpm",
            )

        # =================================================
        # UNIT CONVERSION
        # =================================================

        impeller_diameter_m = (
            impeller_diameter / 1000.0
        )

        # =================================================
        # ENGINEERING CALCULATION
        # =================================================

        reactor_results = calculate_reactor(
            volume_m3=working_volume,
            tank_diameter_m=tank_id_m,
            liquid_height_m=liquid_height_m,
            density_kg_m3=liquid_density,
            viscosity_pa_s=viscosity_pa_s,
            surface_tension_n_m=surface_tension_n_m,
            rpm=rpm,
            impeller_diameter_m=impeller_diameter_m,
            number_impellers=int(number_impellers),
            agitator=agitator_type,
        )

        # =================================================
        # VORTEX ESTIMATION
        # =================================================

        froude = reactor_results.get(
            "Fr",
            0.0,
        )

        if baffles == 0:

            baffle_factor = 1.0

        elif baffles == 2:

            baffle_factor = 0.55

        elif baffles == 4:

            baffle_factor = 0.25

        else:

            baffle_factor = 0.15

        vortex_depth_m = (
            0.08
            * impeller_diameter_m
            * froude ** 0.5
            * baffle_factor
        )

        vortex_depth_m = min(
            vortex_depth_m,
            0.35 * liquid_height_m,
        )

        vortex_percent = (
            vortex_depth_m
            / liquid_height_m
            * 100.0
            if liquid_height_m > 0
            else 0.0
        )

        if baffles == 0 and froude > 0.1:

            vortex_status = (
                "Strong vortex tendency"
            )

        elif vortex_percent > 8:

            vortex_status = (
                "Moderate vortex"
            )

        elif vortex_percent > 3:

            vortex_status = (
                "Low vortex"
            )

        else:

            vortex_status = (
                "Vortex suppressed"
            )

        # =================================================
        # STORE DATA
        # =================================================

        reactor_data = {

            "name": reactor_name,

            "working_volume": working_volume,

            "tank_id": tank_id,

            "tank_id_m": tank_id_m,

            "straight_height": straight_height,

            "straight_height_m": straight_height_m,

            "bottom_type": bottom_type,

            "top_type": top_type,

            "vessel_volume": vessel_volume,

            "liquid_height": liquid_height_mm,

            "liquid_height_m": liquid_height_m,

            "fill_percentage": fill_percentage,

            "density": liquid_density,

            "viscosity": viscosity,

            "viscosity_pa_s": viscosity_pa_s,

            "surface_tension": surface_tension,

            "surface_tension_n_m": surface_tension_n_m,

            "rpm": rpm,

            "agitator_type": agitator_type,

            "impeller_diameter": impeller_diameter,

            "impeller_diameter_m": impeller_diameter_m,

            "number_impellers": int(
                number_impellers
            ),

            "baffles": int(baffles),

            "reaction_type": reaction_type,

            "scale_up_basis": scale_up_basis,

            "vortex_depth": vortex_depth_m,

            "vortex_percent": vortex_percent,

            "vortex_status": vortex_status,
        }

        reactor_data.update(
            reactor_results
        )

        reactors[
            reactor_name
        ] = reactor_data


# =========================================================
# ENGINEERING RESULTS
# =========================================================

st.header(
    "3. 📊 Engineering Results"
)


for name, data in reactors.items():

    st.subheader(
        f"{name} Reactor"
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    # -----------------------------------------------------
    # LIQUID HEIGHT
    # -----------------------------------------------------

    with c1:

        st.metric(
            "Liquid Level",
            f"{data['liquid_height']:.0f} mm",
        )

    # -----------------------------------------------------
    # TIP SPEED
    # -----------------------------------------------------

    with c2:

        st.metric(
            "Tip Speed",
            f"{data['tip_speed']:.2f} m/s",
        )

    # -----------------------------------------------------
    # POWER
    # -----------------------------------------------------

    with c3:

        power = data.get(
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

    with c4:

        power_volume = data.get(
            "power_volume"
        )

        if power_volume is not None:

            st.metric(
                "P/V",
                f"{power_volume:.1f} W/m³",
            )

        else:

            st.metric(
                "P/V",
                "N/A",
            )

    # -----------------------------------------------------
    # REYNOLDS
    # -----------------------------------------------------

    with c5:

        st.metric(
            "Reynolds Number",
            f"{data['Re']:.2e}",
        )

    # =====================================================
    # SECOND ROW
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        pumping = data.get(
            "pumping_m3_h"
        )

        if pumping is not None:

            st.metric(
                "Pumping Capacity",
                f"{pumping:.1f} m³/h",
            )

        else:

            st.metric(
                "Pumping Capacity",
                "N/A",
            )

    with c2:

        turnover = data.get(
            "turnover_time_min"
        )

        if turnover is not None:

            st.metric(
                "Turnover Time",
                f"{turnover:.1f} min",
            )

        else:

            st.metric(
                "Turnover Time",
                "N/A",
            )

    with c3:

        st.metric(
            "Froude Number",
            f"{data['Fr']:.4f}",
        )

    with c4:

        st.metric(
            "Vortex Depth",
            f"{data['vortex_depth']:.3f} m",
        )

    with c5:

        st.metric(
            "Vortex",
            data["vortex_status"],
        )

    # =====================================================
    # RCI WARNING
    # =====================================================

    if data["agitator_type"] == "RCI":

        st.warning(
            "RCI selected. Universal Np/Nq values are not "
            "assumed because RCI performance depends on the "
            "specific blade geometry and manufacturer. "
            "Use validated vendor/literature/test data."
        )


# =========================================================
# 3D VISUALIZATION
# =========================================================

st.header(
    "4. 🏭 3D Reactor & Animated Mixing"
)

st.info(
    "The 3D model uses the selected reactor diameter, "
    "straight-side height, bottom head, top head and "
    "calculated operating liquid level. Press ▶ Play "
    "inside the Plotly viewer to animate agitation and "
    "mixing."
)


for name, data in reactors.items():

    st.subheader(
        f"🌊 {name} — {data['agitator_type']}"
    )

    # =====================================================
    # CREATE ANIMATION
    # =====================================================

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

    st.caption(
        f"Operating liquid level: "
        f"{data['liquid_height']:.0f} mm | "
        f"Vortex depth: "
        f"{data['vortex_depth']:.3f} m | "
        f"Flow pattern: "
        f"{AGITATORS[data['agitator_type']]['flow']}"
    )


# =========================================================
# ENGINEERING NOTES
# =========================================================

st.header(
    "5. ⚠️ Engineering Notes"
)

st.markdown(
    """
    **3D mixing visualization:** conceptual engineering
    visualization based on selected impeller, RPM, reactor
    geometry, liquid level and baffle configuration.

    **It is not CFD.** Actual velocity distribution,
    turbulence, power number, Njs, KLa, gas dispersion and
    blend time should be validated using appropriate
    correlations, vendor data, pilot testing or CFD.

    **RCI:** Np/Nq should be supplied from validated
    manufacturer/literature/test data for the specific
    impeller geometry.
    """
)
