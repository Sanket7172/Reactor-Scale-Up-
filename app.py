# ============================================================
# REACTOR SCALE-UP ENGINEERING STUDIO
# Professional Process Engineering Dashboard
# ============================================================

import sys
import importlib.util
from pathlib import Path

import streamlit as st
import pandas as pd


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
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# CUSTOM MODULE LOADER
# ============================================================

def load_module(module_name, file_path):
    """
    Load a Python module directly from a file path.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            "Required file not found:\n\n"
            f"{file_path}\n\n"
            "Please check that the file exists in the GitHub repository."
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        str(file_path),
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to create module specification for:\n{file_path}"
        )

    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module

    spec.loader.exec_module(module)

    return module


# ============================================================
# LOAD CALCULATION MODULES
# ============================================================

try:

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

except Exception as exc:

    st.error("Unable to load one or more calculation modules.")

    st.exception(exc)

    st.stop()


# ============================================================
# LOAD REPORTING MODULE
# ============================================================

REPORTING_FILE = (
    BASE_DIR
    / "reporting"
    / "report_generator.py"
)

try:

    report_generator = load_module(
        "reporting_report_generator",
        REPORTING_FILE,
    )

    create_word_report = report_generator.create_word_report

    create_excel_report = report_generator.create_excel_report

except Exception as exc:

    st.error("Unable to load reporting/report_generator.py")

    st.exception(exc)

    st.info(
        "Expected file location:\n\n"
        f"{REPORTING_FILE}"
    )

    st.stop()


# ============================================================
# PAGE STYLING
# ============================================================

st.markdown(
    "<style>"
    ".stApp { background: #f4f7fb; }"
    ".block-container { "
    "max-width: 1550px; "
    "padding-top: 1rem; "
    "padding-bottom: 2rem; "
    "}"
    "h1, h2, h3 { color: #12344d !important; }"
    "[data-testid='stSidebar'] { background: #ffffff; }"
    "div[data-testid='stMetric'] { "
    "background: #ffffff; "
    "border: 1px solid #d9e2ec; "
    "padding: 14px; "
    "border-radius: 12px; "
    "}"
    "div[data-testid='stMetricLabel'] { "
    "color: #486581 !important; "
    "font-weight: 700; "
    "}"
    "div[data-testid='stMetricValue'] { "
    "color: #102a43 !important; "
    "font-weight: 800; "
    "}"
    "button { border-radius: 9px !important; }"
    ".section-box { "
    "background: white; "
    "border: 1px solid #d9e2ec; "
    "border-radius: 14px; "
    "padding: 18px; "
    "margin-bottom: 15px; "
    "}"
    ".small-note { "
    "color: #627d98; "
    "font-size: 0.85rem; "
    "}"
    "</style>",
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def fmt(value, decimals=3):

    if value is None:
        return "—"

    try:
        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):
        return str(value)


def status_icon(status):

    if status == "PASS":
        return "🟢"

    if status == "FAIL":
        return "🔴"

    return "🟠"


def kpi(label, value, unit="", decimals=3):

    label_text = f"{label} ({unit})" if unit else label

    if value is None:
        display = "—"

    elif isinstance(value, str):
        display = value

    else:
        display = fmt(value, decimals)

    st.metric(
        label=label_text,
        value=display,
    )


def safe_float(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def get_result(result, *keys, default=None):

    if not isinstance(result, dict):
        return default

    for key in keys:

        if key in result:
            return result[key]

    return default


# ============================================================
# SESSION STATE
# ============================================================

if "reactors" not in st.session_state:
    st.session_state.reactors = []

if "scaleup_result" not in st.session_state:
    st.session_state.scaleup_result = None

if "calculated" not in st.session_state:
    st.session_state.calculated = False


# ============================================================
# HEADER
# ============================================================

st.title("⚗️ Reactor Scale-Up Engineering Studio")

st.caption(
    "Process Engineering • Mixing • Agitation • Scale-Up • "
    "Gas-Liquid Analysis • Validation"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Project Configuration")

    project_name = st.text_input(
        "Project Name",
        value="Reactor Scale-Up Study",
    )

    prepared_by = st.text_input(
        "Prepared By",
        value="Process Engineering",
    )

    st.divider()

    process_type = st.selectbox(
        "Process Type",
        [
            "Liquid-Liquid",
            "Solid-Liquid",
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ],
    )

    study_mode = st.selectbox(
        "Study Mode",
        [
            "Single Reactor Analysis",
            "Reactor Scale-Up",
        ],
    )

    scaleup_basis = st.selectbox(
        "Scale-Up Basis",
        [
            "Constant P/V",
            "Constant Tip Speed",
            "Constant RPM",
            "Constant Mixing Time",
        ],
    )

    st.divider()

    st.info(
        "Use the engineering inputs for the reactor, "
        "agitator and process fluid. The dashboard calculates "
        "mixing and scale-up parameters."
    )


# ============================================================
# NUMBER OF REACTORS
# ============================================================

if study_mode == "Single Reactor Analysis":

    number_reactors = 1

else:

    number_reactors = 2


# ============================================================
# REACTOR INPUT SECTION
# ============================================================

st.header("1. Reactor & Process Inputs")


reactors = []


for reactor_index in range(number_reactors):

    if number_reactors == 1:

        reactor_title = "Reactor"

    else:

        reactor_title = f"Reactor {reactor_index + 1}"

    with st.expander(
        reactor_title,
        expanded=True,
    ):

        col1, col2, col3 = st.columns(3)

        # ----------------------------------------------------
        # PROCESS DATA
        # ----------------------------------------------------

        with col1:

            st.subheader("Process Data")

            working_volume = st.number_input(
                "Working Volume (m³)",
                min_value=0.01,
                value=5.00 if reactor_index == 0 else 10.00,
                step=0.10,
                key=f"working_volume_{reactor_index}",
            )

            density = st.number_input(
                "Liquid Density (kg/m³)",
                min_value=1.0,
                value=1000.0,
                step=10.0,
                key=f"density_{reactor_index}",
            )

            viscosity_pa_s = st.number_input(
                "Viscosity (Pa·s)",
                min_value=0.000001,
                value=0.001,
                format="%.6f",
                key=f"viscosity_{reactor_index}",
            )

            surface_tension = st.number_input(
                "Surface Tension (N/m)",
                min_value=0.0001,
                value=0.072,
                format="%.5f",
                key=f"surface_tension_{reactor_index}",
            )

        # ----------------------------------------------------
        # VESSEL GEOMETRY
        # ----------------------------------------------------

        with col2:

            st.subheader("Vessel Geometry")

            tank_diameter = st.number_input(
                "Tank Diameter (m)",
                min_value=0.10,
                value=2.00 if reactor_index == 0 else 2.50,
                step=0.05,
                key=f"tank_diameter_{reactor_index}",
            )

            straight_height = st.number_input(
                "Straight Side Height (m)",
                min_value=0.10,
                value=2.50 if reactor_index == 0 else 3.00,
                step=0.05,
                key=f"straight_height_{reactor_index}",
            )

            bottom_options = list(REACTOR_HEADS.keys())

            bottom_type = st.selectbox(
                "Bottom Head",
                bottom_options,
                key=f"bottom_type_{reactor_index}",
            )

            top_type = st.selectbox(
                "Top Head",
                bottom_options,
                key=f"top_type_{reactor_index}",
            )

            try:

                vessel_volume = calculate_total_volume(
                    tank_diameter,
                    straight_height,
                    bottom_type,
                    top_type,
                )

            except TypeError:

                try:

                    vessel_volume = calculate_total_volume(
                        D=tank_diameter,
                        straight_height=straight_height,
                        bottom_type=bottom_type,
                        top_type=top_type,
                    )

                except Exception:

                    vessel_volume = None

            if vessel_volume is not None:

                st.info(
                    f"Calculated Vessel Volume: "
                    f"{fmt(vessel_volume, 3)} m³"
                )

                try:

                    liquid_height = liquid_height_from_volume(
                        working_volume,
                        tank_diameter,
                        straight_height,
                        bottom_type,
                    )

                except TypeError:

                    try:

                        liquid_height = liquid_height_from_volume(
                            volume_m3=working_volume,
                            tank_diameter_m=tank_diameter,
                            straight_height_m=straight_height,
                            bottom_type=bottom_type,
                        )

                    except Exception:

                        liquid_height = working_volume / (
                            3.141592653589793
                            * tank_diameter**2
                            / 4
                        )

            else:

                liquid_height = working_volume / (
                    3.141592653589793
                    * tank_diameter**2
                    / 4
                )

            st.info(
                f"Estimated Liquid Height: "
                f"{fmt(liquid_height, 3)} m"
            )

        # ----------------------------------------------------
        # AGITATION
        # ----------------------------------------------------

        with col3:

            st.subheader("Agitation")

            agitator_names = list(AGITATORS.keys())

            agitator = st.selectbox(
                "Agitator",
                agitator_names,
                key=f"agitator_{reactor_index}",
            )

            agitator_data = AGITATORS.get(
                agitator,
                {},
            )

            default_impeller = safe_float(
                agitator_data.get(
                    "impeller_diameter_m",
                    0.7,
                ),
                0.7,
            )

            impeller_diameter = st.number_input(
                "Impeller Diameter (m)",
                min_value=0.05,
                value=default_impeller,
                step=0.01,
                key=f"impeller_diameter_{reactor_index}",
            )

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"number_impellers_{reactor_index}",
            )

            rpm = st.number_input(
                "Agitator Speed (RPM)",
                min_value=1.0,
                max_value=1000.0,
                value=120.0,
                step=5.0,
                key=f"rpm_{reactor_index}",
            )

            number_baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"number_baffles_{reactor_index}",
            )

            clearance = st.number_input(
                "Impeller Clearance (m)",
                min_value=0.01,
                value=0.30,
                step=0.01,
                key=f"clearance_{reactor_index}",
            )

        # ----------------------------------------------------
        # GAS INPUTS
        # ----------------------------------------------------

        gas_flow = 0.0
        gas_density = 1.2
        gas_viscosity = 1.8e-5
        gas_diffusivity = 2.0e-5
        bubble_diameter = 3.0
        gas_holdup = 0.05

        if process_type in [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ]:

            st.subheader("Gas-Liquid Parameters")

            g1, g2, g3 = st.columns(3)

            with g1:

                gas_flow = st.number_input(
                    "Gas Flow (m³/h)",
                    min_value=0.0,
                    value=10.0,
                    step=1.0,
                    key=f"gas_flow_{reactor_index}",
                )

                gas_density = st.number_input(
                    "Gas Density (kg/m³)",
                    min_value=0.01,
                    value=1.2,
                    step=0.1,
                    key=f"gas_density_{reactor_index}",
                )

            with g2:

                gas_viscosity = st.number_input(
                    "Gas Viscosity (Pa·s)",
                    min_value=1e-8,
                    value=1.8e-5,
                    format="%.8f",
                    key=f"gas_viscosity_{reactor_index}",
                )

                gas_diffusivity = st.number_input(
                    "Gas Diffusivity (m²/s)",
                    min_value=1e-9,
                    value=2.0e-5,
                    format="%.8f",
                    key=f"gas_diffusivity_{reactor_index}",
                )

            with g3:

                bubble_diameter = st.number_input(
                    "Bubble Diameter (mm)",
                    min_value=0.1,
                    value=3.0,
                    step=0.1,
                    key=f"bubble_diameter_{reactor_index}",
                )

                gas_holdup = st.number_input(
                    "Gas Holdup",
                    min_value=0.0,
                    max_value=0.99,
                    value=0.05,
                    step=0.01,
                    key=f"gas_holdup_{reactor_index}",
                )

        # ----------------------------------------------------
        # STORE INPUTS
        # ----------------------------------------------------

        reactors.append(
            {
                "name": reactor_title,

                "working_volume_m3": working_volume,

                "vessel_volume_m3": vessel_volume,

                "tank_diameter_m": tank_diameter,

                "straight_height_m": straight_height,

                "liquid_height_m": liquid_height,

                "bottom_type": bottom_type,

                "top_type": top_type,

                "density_kg_m3": density,

                "viscosity_pa_s": viscosity_pa_s,

                "surface_tension_n_m": surface_tension,

                "agitator": agitator,

                "impeller_diameter_m": impeller_diameter,

                "number_impellers": number_impellers,

                "rpm": rpm,

                "number_baffles": number_baffles,

                "impeller_clearance_m": clearance,

                "gas_flow_m3_h": gas_flow,

                "gas_density_kg_m3": gas_density,

                "gas_viscosity_pa_s": gas_viscosity,

                "gas_diffusivity_m2_s": gas_diffusivity,

                "bubble_diameter_mm": bubble_diameter,

                "gas_holdup_fraction": gas_holdup,
            }
        )


# ============================================================
# CALCULATE BUTTON
# ============================================================

st.divider()

calculate_button = st.button(
    "🚀 Run Engineering Calculations",
    type="primary",
    use_container_width=True,
)


# ============================================================
# CALCULATION ENGINE
# ============================================================

if calculate_button:

    calculated_reactors = []

    calculation_failed = False

    for reactor in reactors:

        try:

            result = calculate_reactor(
                volume_m3=reactor["working_volume_m3"],
                tank_diameter_m=reactor["tank_diameter_m"],
                liquid_height_m=reactor["liquid_height_m"],
                density_kg_m3=reactor["density_kg_m3"],
                viscosity_pa_s=reactor["viscosity_pa_s"],
                surface_tension_n_m=reactor[
                    "surface_tension_n_m"
                ],
                rpm=reactor["rpm"],
                impeller_diameter_m=reactor[
                    "impeller_diameter_m"
                ],
                number_impellers=reactor[
                    "number_impellers"
                ],
                agitator=reactor["agitator"],
                impeller_clearance_m=reactor[
                    "impeller_clearance_m"
                ],
                gas_flow_m3_h=reactor[
                    "gas_flow_m3_h"
                ],
                gas_density_kg_m3=reactor[
                    "gas_density_kg_m3"
                ],
                gas_viscosity_pa_s=reactor[
                    "gas_viscosity_pa_s"
                ],
                gas_diffusivity_m2_s=reactor[
                    "gas_diffusivity_m2_s"
                ],
                bubble_diameter_mm=reactor[
                    "bubble_diameter_mm"
                ],
                gas_holdup_fraction=reactor[
                    "gas_holdup_fraction"
                ],
            )

        except Exception as exc:

            st.error(
                f"Calculation failed for "
                f"{reactor['name']}."
            )

            st.exception(exc)

            calculation_failed = True

            continue

        if not isinstance(result, dict):

            st.error(
                f"Calculation engine returned an invalid "
                f"result for {reactor['name']}."
            )

            calculation_failed = True

            continue

        # ----------------------------------------------------
        # ADD INPUT DATA TO RESULT
        # ----------------------------------------------------

        result.update(reactor)

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        try:

            validation_result = validate_reactor(
                volume_m3=reactor[
                    "working_volume_m3"
                ],
                vessel_volume_m3=reactor[
                    "vessel_volume_m3"
                ],
                tank_diameter_m=reactor[
                    "tank_diameter_m"
                ],
                straight_height_m=reactor[
                    "straight_height_m"
                ],
                liquid_height_m=reactor[
                    "liquid_height_m"
                ],
                impeller_diameter_m=reactor[
                    "impeller_diameter_m"
                ],
                number_impellers=reactor[
                    "number_impellers"
                ],
                number_baffles=reactor[
                    "number_baffles"
                ],
                rpm=reactor["rpm"],
                agitator=reactor["agitator"],
                density_kg_m3=reactor[
                    "density_kg_m3"
                ],
                viscosity_pa_s=reactor[
                    "viscosity_pa_s"
                ],
                power_volume_kw_m3=result.get(
                    "power_volume_kw_m3"
                ),
                gas_flow_m3_h=reactor[
                    "gas_flow_m3_h"
                ],
                kLa_1_h=result.get("kLa_1_h"),
            )

            result["validation"] = validation_result

        except Exception as exc:

            result["validation"] = {
                "overall_status": "WARNING",
                "error": str(exc),
            }

        calculated_reactors.append(result)

    # --------------------------------------------------------
    # STORE RESULTS
    # --------------------------------------------------------

    if not calculation_failed and calculated_reactors:

        st.session_state.reactors = calculated_reactors

        st.session_state.calculated = True

        st.session_state.scaleup_result = None

        # ----------------------------------------------------
        # SCALE-UP
        # ----------------------------------------------------

        if len(calculated_reactors) >= 2:

            base = calculated_reactors[0]

            target = calculated_reactors[1]

            try:

                scale_result = calculate_scaleup(
                    base=base,
                    target=target,
                    basis=scaleup_basis,
                )

            except TypeError:

                try:

                    scale_result = calculate_scaleup(
                        base,
                        target,
                        scaleup_basis,
                    )

                except Exception as exc:

                    scale_result = {
                        "status": "ERROR",
                        "error": str(exc),
                    }

            except Exception as exc:

                scale_result = {
                    "status": "ERROR",
                    "error": str(exc),
                }

            st.session_state.scaleup_result = (
                scale_result
            )

        st.success(
            "Engineering calculations completed successfully."
        )


# ============================================================
# DISPLAY ONLY AFTER CALCULATION
# ============================================================

if st.session_state.calculated:

    reactors = st.session_state.reactors

    scaleup_result = st.session_state.scaleup_result

    # ========================================================
    # TABS
    # ========================================================

    tab_performance, tab_gas, tab_scaleup, tab_validation, tab_3d, tab_reports = st.tabs(
        [
            "📊 Performance",
            "🫧 Gas-Liquid",
            "📐 Scale-Up",
            "✅ Validation",
            "🧊 3D Reactor",
            "📄 Reports",
        ]
    )


    # ========================================================
    # PERFORMANCE TAB
    # ========================================================

    with tab_performance:

        st.header("Reactor Performance")

        for reactor in reactors:

            st.subheader(
                reactor.get(
                    "name",
                    "Reactor",
                )
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Working Volume",
                    get_result(
                        reactor,
                        "working_volume_m3",
                    ),
                    "m³",
                )

            with c2:

                kpi(
                    "Tank Diameter",
                    get_result(
                        reactor,
                        "tank_diameter_m",
                    ),
                    "m",
                )

            with c3:

                kpi(
                    "Liquid Height",
                    get_result(
                        reactor,
                        "liquid_height_m",
                    ),
                    "m",
                )

            with c4:

                kpi(
                    "Agitator Speed",
                    get_result(
                        reactor,
                        "rpm",
                    ),
                    "RPM",
                )

            st.markdown("### Mixing Performance")

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Power",
                    get_result(
                        reactor,
                        "power_kw",
                        "power",
                    ),
                    "kW",
                )

            with c2:

                kpi(
                    "Power / Volume",
                    get_result(
                        reactor,
                        "power_volume_kw_m3",
                    ),
                    "kW/m³",
                )

            with c3:

                kpi(
                    "Tip Speed",
                    get_result(
                        reactor,
                        "tip_speed_m_s",
                    ),
                    "m/s",
                )

            with c4:

                kpi(
                    "Reynolds Number",
                    get_result(
                        reactor,
                        "reynolds_number",
                    ),
                    "",
                    0,
                )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Froude Number",
                    get_result(
                        reactor,
                        "froude_number",
                    ),
                    "",
                    4,
                )

            with c2:

                kpi(
                    "Pumping Capacity",
                    get_result(
                        reactor,
                        "pumping_capacity_m3_h",
                    ),
                    "m³/h",
                )

            with c3:

                kpi(
                    "Turnover Time",
                    get_result(
                        reactor,
                        "turnover_time_min",
                    ),
                    "min",
                )

            with c4:

                kpi(
                    "Impeller Diameter",
                    get_result(
                        reactor,
                        "impeller_diameter_m",
                    ),
                    "m",
                )

            st.divider()


    # ========================================================
    # GAS-LIQUID TAB
    # ========================================================

    with tab_gas:

        st.header("Gas-Liquid Performance")

        if reactors[0].get("gas_flow_m3_h", 0) <= 0:

            st.info(
                "Gas flow is zero. Gas-liquid calculations "
                "will become active when a gas flow is entered."
            )

        for reactor in reactors:

            st.subheader(
                reactor.get(
                    "name",
                    "Reactor",
                )
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Gas Flow",
                    get_result(
                        reactor,
                        "gas_flow_m3_h",
                    ),
                    "m³/h",
                )

            with c2:

                kpi(
                    "Superficial Gas Velocity",
                    get_result(
                        reactor,
                        "superficial_gas_velocity_m_s",
                    ),
                    "m/s",
                )

            with c3:

                kpi(
                    "Gas Holdup",
                    get_result(
                        reactor,
                        "gas_holdup_fraction",
                    ),
                    "fraction",
                    4,
                )

            with c4:

                kpi(
                    "Bubble Diameter",
                    get_result(
                        reactor,
                        "bubble_diameter_mm",
                    ),
                    "mm",
                )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Bubble Rise Velocity",
                    get_result(
                        reactor,
                        "bubble_rise_velocity_m_s",
                    ),
                    "m/s",
                )

            with c2:

                kpi(
                    "Bubble Reynolds",
                    get_result(
                        reactor,
                        "bubble_reynolds_number",
                    ),
                    "",
                    0,
                )

            with c3:

                kpi(
                    "Schmidt Number",
                    get_result(
                        reactor,
                        "schmidt_number",
                    ),
                    "",
                    2,
                )

            with c4:

                kpi(
                    "Sherwood Number",
                    get_result(
                        reactor,
                        "sherwood_number",
                    ),
                    "",
                    2,
                )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Mass Transfer Coefficient",
                    get_result(
                        reactor,
                        "kL_m_s",
                    ),
                    "m/s",
                    6,
                )

            with c2:

                kpi(
                    "Interfacial Area",
                    get_result(
                        reactor,
                        "interfacial_area_m2_m3",
                    ),
                    "m²/m³",
                )

            with c3:

                kpi(
                    "kLa",
                    get_result(
                        reactor,
                        "kLa_1_h",
                    ),
                    "1/h",
                )

            with c4:

                kpi(
                    "Volumetric Transfer Rate",
                    get_result(
                        reactor,
                        "qv_1_s",
                    ),
                    "1/s",
                    5,
                )

            st.divider()


    # ========================================================
    # SCALE-UP TAB
    # ========================================================

    with tab_scaleup:

        st.header("Reactor Scale-Up Analysis")

        if len(reactors) < 2:

            st.info(
                "Scale-up analysis requires two reactors."
            )

        elif scaleup_result is None:

            st.warning(
                "Scale-up calculation is not available."
            )

        elif isinstance(scaleup_result, dict):

            st.subheader(
                f"Scale-Up Basis: {scaleup_basis}"
            )

            # ------------------------------------------------
            # SHOW SCALE-UP RESULT
            # ------------------------------------------------

            scale_df = pd.DataFrame(
                [
                    {
                        "Parameter": key,
                        "Value": value,
                    }
                    for key, value in scaleup_result.items()
                    if not isinstance(
                        value,
                        (dict, list, tuple),
                    )
                ]
            )

            if not scale_df.empty:

                st.dataframe(
                    scale_df,
                    use_container_width=True,
                    hide_index=True,
                )

            # ------------------------------------------------
            # BASE / TARGET COMPARISON
            # ------------------------------------------------

            st.subheader("Base vs Target Reactor")

            comparison_rows = []

            parameters = [
                (
                    "Working Volume",
                    "working_volume_m3",
                    "m³",
                ),
                (
                    "Tank Diameter",
                    "tank_diameter_m",
                    "m",
                ),
                (
                    "Liquid Height",
                    "liquid_height_m",
                    "m",
                ),
                (
                    "Impeller Diameter",
                    "impeller_diameter_m",
                    "m",
                ),
                (
                    "RPM",
                    "rpm",
                    "RPM",
                ),
                (
                    "Power",
                    "power_kw",
                    "kW",
                ),
                (
                    "P/V",
                    "power_volume_kw_m3",
                    "kW/m³",
                ),
                (
                    "Tip Speed",
                    "tip_speed_m_s",
                    "m/s",
                ),
                (
                    "Reynolds Number",
                    "reynolds_number",
                    "",
                ),
                (
                    "Turnover Time",
                    "turnover_time_min",
                    "min",
                ),
            ]

            for label, key, unit in parameters:

                comparison_rows.append(
                    {
                        "Parameter": label,
                        "Base Reactor": get_result(
                            reactors[0],
                            key,
                        ),
                        "Target Reactor": get_result(
                            reactors[1],
                            key,
                        ),
                        "Unit": unit,
                    }
                )

            comparison_df = pd.DataFrame(
                comparison_rows
            )

            st.dataframe(
                comparison_df,
                use_container_width=True,
                hide_index=True,
            )


    # ========================================================
    # VALIDATION TAB
    # ========================================================

    with tab_validation:

        st.header("Engineering Validation")

        for reactor in reactors:

            st.subheader(
                reactor.get(
                    "name",
                    "Reactor",
                )
            )

            validation = reactor.get(
                "validation",
                {},
            )

            if not isinstance(validation, dict):

                st.warning(
                    "Validation result is not available."
                )

                continue

            overall_status = validation.get(
                "overall_status",
                validation.get(
                    "status",
                    "WARNING",
                ),
            )

            st.markdown(
                f"### Overall Status: "
                f"{status_icon(overall_status)} "
                f"{overall_status}"
            )

            validation_rows = []

            for key, value in validation.items():

                if isinstance(value, dict):

                    validation_rows.append(
                        {
                            "Check": key,
                            "Status": value.get(
                                "status",
                                value.get(
                                    "result",
                                    "—",
                                ),
                            ),
                            "Value": value.get(
                                "value",
                                "—",
                            ),
                            "Message": value.get(
                                "message",
                                value.get(
                                    "reason",
                                    "",
                                ),
                            ),
                        }
                    )

                elif key not in [
                    "overall_status",
                    "status",
                ]:

                    validation_rows.append(
                        {
                            "Check": key,
                            "Status": "INFO",
                            "Value": value,
                            "Message": "",
                        }
                    )

            if validation_rows:

                validation_df = pd.DataFrame(
                    validation_rows
                )

                st.dataframe(
                    validation_df,
                    use_container_width=True,
                    hide_index=True,
                )

            st.divider()


    # ========================================================
    # 3D REACTOR TAB
    # ========================================================

    with tab_3d:

        st.header("3D Reactor Visualization")

        reactor_names = [
            r.get(
                "name",
                f"Reactor {i + 1}",
            )
            for i, r in enumerate(reactors)
        ]

        selected_name = st.selectbox(
            "Select Reactor",
            reactor_names,
        )

        selected = next(
            (
                r
                for r in reactors
                if r.get("name") == selected_name
            ),
            reactors[0],
        )

        try:

            fig = create_reactor_animation(
                D=selected.get(
                    "tank_diameter_m"
                ),
                straight_height=selected.get(
                    "straight_height_m"
                ),
                bottom_type=selected.get(
                    "bottom_type"
                ),
                top_type=selected.get(
                    "top_type"
                ),
                liquid_height=selected.get(
                    "liquid_height_m"
                ),
                agitator=selected.get(
                    "agitator"
                ),
                impeller_diameter=selected.get(
                    "impeller_diameter_m"
                ),
                number_impellers=selected.get(
                    "number_impellers"
                ),
                rpm=selected.get(
                    "rpm"
                ),
                number_baffles=selected.get(
                    "number_baffles"
                ),
                frames_count=36,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        except Exception as exc:

            st.error(
                "Unable to generate the 3D reactor visualization."
            )

            st.exception(exc)


    # ========================================================
    # REPORTS TAB
    # ========================================================

    with tab_reports:

        st.header("Engineering Reports")

        st.write(
            "Generate downloadable engineering reports "
            "containing reactor inputs, calculated parameters, "
            "scale-up results and validation."
        )

        report_col1, report_col2 = st.columns(2)

        # ----------------------------------------------------
        # WORD REPORT
        # ----------------------------------------------------

        with report_col1:

            st.subheader("Microsoft Word Report")

            if st.button(
                "📄 Generate Word Report",
                use_container_width=True,
            ):

                try:

                    word_file = create_word_report(
                        project_name=project_name,
                        prepared_by=prepared_by,
                        process_type=process_type,
                        study_mode=study_mode,
                        scaleup_basis=scaleup_basis,
                        reactors=reactors,
                        scaleup_result=(
                            scaleup_result
                            if len(reactors) >= 2
                            else None
                        ),
                    )

                    st.download_button(
                        label="⬇️ Download Word Report",
                        data=word_file.getvalue(),
                        file_name=(
                            "reactor_scaleup_report.docx"
                        ),
                        mime=(
                            "application/vnd.openxmlformats-"
                            "officedocument.wordprocessingml.document"
                        ),
                        use_container_width=True,
                    )

                except Exception as exc:

                    st.error(
                        "Unable to generate Word report."
                    )

                    st.exception(exc)

        # ----------------------------------------------------
        # EXCEL REPORT
        # ----------------------------------------------------

        with report_col2:

            st.subheader("Microsoft Excel Report")

            if st.button(
                "📊 Generate Excel Report",
                use_container_width=True,
            ):

                try:

                    excel_file = create_excel_report(
                        project_name=project_name,
                        prepared_by=prepared_by,
                        process_type=process_type,
                        study_mode=study_mode,
                        scaleup_basis=scaleup_basis,
                        reactors=reactors,
                        scaleup_result=(
                            scaleup_result
                            if len(reactors) >= 2
                            else None
                        ),
                    )

                    st.download_button(
                        label="⬇️ Download Excel Report",
                        data=excel_file.getvalue(),
                        file_name=(
                            "reactor_scaleup_report.xlsx"
                        ),
                        mime=(
                            "application/vnd.openxmlformats-"
                            "officedocument.spreadsheetml.sheet"
                        ),
                        use_container_width=True,
                    )

                except Exception as exc:

                    st.error(
                        "Unable to generate Excel report."
                    )

                    st.exception(exc)


# ============================================================
# ENGINEERING DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "Engineering Disclaimer: This dashboard is intended for "
    "engineering calculation, preliminary design and scale-up "
    "assessment. Final equipment design, mechanical integrity, "
    "process safety and plant implementation must be verified "
    "against applicable design codes, vendor data, process "
    "conditions and project-specific engineering standards."
)
