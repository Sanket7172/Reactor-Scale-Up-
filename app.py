import streamlit as st

from calculations.engine import calculate_reactor
from libraries.agitator_geometry import AGITATORS
from libraries.reactor_geometry import REACTOR_HEADS
from visualization.reactor_3d import create_reactor_3d


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Reactor Scale-Up Dashboard",
    page_icon="🏭",
    layout="wide"
)


# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("🏭 Reactor Scale-Up Engineering Dashboard")

st.caption(
    "Process Engineering • Mixing • Agitation • Scale-Up • "
    "Reactor Geometry"
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.header("Project")

project_name = st.sidebar.text_input(
    "Project Name",
    value="Reactor Scale-Up Study"
)

engineer = st.sidebar.text_input(
    "Prepared By",
    value=""
)


# ---------------------------------------------------------
# STUDY MODE
# ---------------------------------------------------------

st.sidebar.header("Study Mode")

study_mode = st.sidebar.selectbox(
    "Select Study",
    [
        "Single Reactor",
        "Lab vs Pilot",
        "Pilot vs Commercial",
        "Lab vs Commercial",
        "Lab vs Pilot vs Commercial"
    ]
)


# ---------------------------------------------------------
# SELECT REACTORS
# ---------------------------------------------------------

if study_mode == "Single Reactor":
    selected_reactors = ["Reactor"]

elif study_mode == "Lab vs Pilot":
    selected_reactors = ["Lab", "Pilot"]

elif study_mode == "Pilot vs Commercial":
    selected_reactors = ["Pilot", "Commercial"]

elif study_mode == "Lab vs Commercial":
    selected_reactors = ["Lab", "Commercial"]

else:
    selected_reactors = [
        "Lab",
        "Pilot",
        "Commercial"
    ]


# ---------------------------------------------------------
# REACTION TYPE
# ---------------------------------------------------------

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
        "Other"
    ]
)


# ---------------------------------------------------------
# SCALE-UP CRITERION
# ---------------------------------------------------------

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
        "User Defined"
    ]
)


# ---------------------------------------------------------
# REACTOR INPUTS
# ---------------------------------------------------------

reactors = {}

for reactor_name in selected_reactors:

    st.header(f"2. {reactor_name} Reactor")

    with st.expander(
        f"{reactor_name} Reactor Configuration",
        expanded=True
    ):

        col1, col2, col3 = st.columns(3)

        with col1:

            working_volume = st.number_input(
                f"{reactor_name} Working Volume (m³)",
                min_value=0.001,
                value=1.0,
                key=f"{reactor_name}_volume"
            )

            tank_id = st.number_input(
                f"{reactor_name} Tank ID (mm)",
                min_value=100.0,
                value=1200.0,
                key=f"{reactor_name}_id"
            )

            straight_height = st.number_input(
                f"{reactor_name} Straight Side Height (mm)",
                min_value=100.0,
                value=1500.0,
                key=f"{reactor_name}_straight_height"
            )

        with col2:

            bottom_type = st.selectbox(
                f"{reactor_name} Bottom Geometry",
                list(REACTOR_HEADS.keys()),
                key=f"{reactor_name}_bottom"
            )

            top_type = st.selectbox(
                f"{reactor_name} Top Geometry",
                list(REACTOR_HEADS.keys()),
                key=f"{reactor_name}_top"
            )

            liquid_density = st.number_input(
                f"{reactor_name} Liquid Density (kg/m³)",
                min_value=1.0,
                value=1000.0,
                key=f"{reactor_name}_density"
            )

        with col3:

            viscosity = st.number_input(
                f"{reactor_name} Viscosity (mPa·s)",
                min_value=0.01,
                value=1.0,
                key=f"{reactor_name}_viscosity"
            )

            surface_tension = st.number_input(
                f"{reactor_name} Surface Tension (mN/m)",
                min_value=0.1,
                value=72.0,
                key=f"{reactor_name}_surface_tension"
            )

            rpm = st.number_input(
                f"{reactor_name} Agitator RPM",
                min_value=0.1,
                value=100.0,
                key=f"{reactor_name}_rpm"
            )


        # -------------------------------------------------
        # AGITATOR
        # -------------------------------------------------

        st.subheader("Agitator")

        agitator_type = st.selectbox(
            "Agitator Type",
            list(AGITATORS.keys()),
            key=f"{reactor_name}_agitator"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            impeller_diameter = st.number_input(
                "Impeller Diameter (mm)",
                min_value=10.0,
                value=400.0,
                key=f"{reactor_name}_impeller_d"
            )

        with c2:

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{reactor_name}_impellers"
            )

        with c3:

            baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{reactor_name}_baffles"
            )


        # -------------------------------------------------
        # CALCULATION
        # -------------------------------------------------

        reactor_data = {
            "name": reactor_name,
            "working_volume": working_volume,
            "tank_id": tank_id,
            "straight_height": straight_height,
            "bottom_type": bottom_type,
            "top_type": top_type,
            "density": liquid_density,
            "viscosity": viscosity,
            "surface_tension": surface_tension,
            "rpm": rpm,
            "agitator_type": agitator_type,
            "impeller_diameter": impeller_diameter,
            "number_impellers": number_impellers,
            "baffles": baffles,
            "reaction_type": reaction_type,
        }

        results = calculate_reactor(reactor_data)

        reactor_data.update(results)

        reactors[reactor_name] = reactor_data


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

st.header("3. Engineering Results")

for name, data in reactors.items():

    st.subheader(name)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Liquid Height",
            f"{data['liquid_height']:.0f} mm"
        )

    with c2:
        st.metric(
            "Tip Speed",
            f"{data['tip_speed']:.2f} m/s"
        )

    with c3:
        st.metric(
            "Power / Volume",
            f"{data['power_per_volume']:.3f} kW/m³"
        )

    with c4:
        st.metric(
            "Reynolds Number",
            f"{data['reynolds_number']:.0f}"
        )


# ---------------------------------------------------------
# 3D VISUALIZATION
# ---------------------------------------------------------

st.header("4. 3D Reactor Visualization")

for name, data in reactors.items():

    st.subheader(f"{name} Reactor")

    fig = create_reactor_3d(data)

    st.plotly_chart(
        fig,
        use_container_width=True
    )
