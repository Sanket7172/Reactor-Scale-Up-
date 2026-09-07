# ============================================================
# REACTOR SCALE-UP ENGINEERING STUDIO
# Streamlit Application
# ============================================================

import sys
import importlib.util
from pathlib import Path

import streamlit as st
import pandas as pd


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


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
# MODULE LOADER
# ============================================================

def load_module(module_name, file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found:\n{file_path}"
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
# REQUIRED PROJECT MODULES
# ============================================================

try:
    from calculations.engine import calculate_reactor
except Exception as exc:
    st.error("Unable to load calculations.engine")
    st.exception(exc)
    st.stop()


try:
    from calculations.scaleup import calculate_scaleup
except Exception as exc:
    st.error("Unable to load calculations.scaleup")
    st.exception(exc)
    st.stop()


try:
    from calculations.validation import validate_reactor
except Exception as exc:
    st.error("Unable to load calculations.validation")
    st.exception(exc)
    st.stop()


try:
    from libraries.agitator_geometry import AGITATORS
except Exception as exc:
    st.error("Unable to load libraries.agitator_geometry")
    st.exception(exc)
    st.stop()


try:
    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )
except Exception as exc:
    st.error("Unable to load libraries.reactor_geometry")
    st.exception(exc)
    st.stop()


try:
    from visualization.reactor_3d import create_reactor_animation
except Exception as exc:
    st.error("Unable to load visualization.reactor_3d")
    st.exception(exc)
    st.stop()


# ============================================================
# REPORTING MODULE
# ============================================================
#
# IMPORTANT:
# We deliberately DO NOT use:
#
# from reporting.report_generator import ...
#
# The module is loaded directly from its file so that the
# application does not depend on Python package discovery.
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
    st.error(
        "Unable to load reporting/report_generator.py"
    )
    st.exception(exc)
    st.stop()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    "<style>"
    ".stApp {"
    "background: #f4f7fb;"
    "}"
    ".block-container {"
    "max-width: 1550px;"
    "padding-top: 1rem;"
    "padding-bottom: 2rem;"
    "}"
    "h1, h2, h3 {"
    "color: #12344d !important;"
    "}"
    "[data-testid='stSidebar'] {"
    "background: #ffffff;"
    "}"
    "div[data-testid='stMetric'] {"
    "background: #ffffff;"
    "border: 1px solid #d9e2ec;"
    "padding: 14px;"
    "border-radius: 12px;"
    "}"
    "div[data-testid='stMetricLabel'] {"
    "color: #486581 !important;"
    "font-weight: 700;"
    "}"
    "div[data-testid='stMetricValue'] {"
    "color: #102a43 !important;"
    "font-weight: 800;"
    "}"
    "button {"
    "border-radius: 9px !important;"
    "}"
    ".section-box {"
    "background: white;"
    "border: 1px solid #d9e2ec;"
    "border-radius: 14px;"
    "padding: 18px;"
    "margin-bottom: 15px;"
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
    if str(status).upper() == "PASS":
        return "🟢"

    if str(status).upper() == "FAIL":
        return "🔴"

    return "🟠"


def kpi(label, value, unit="", decimals=3):
    if value is None:
        display = "—"

    elif isinstance(value, str):
        display = value

    else:
        display = fmt(value, decimals)

    if unit:
        label = f"{label} ({unit})"

    st.metric(
        label=label,
        value=display,
    )


def get_value(data, *keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data and data[key] is not None:
            return data[key]

    return default


# ============================================================
# PROCESS TYPE
# ============================================================

PROCESS_TYPES = [
    "Liquid-Liquid",
    "Solid-Liquid",
    "Gas-Liquid",
    "Gas-Liquid-Solid",
]


# ============================================================
# SCALE-UP BASIS
# ============================================================

SCALEUP_BASES = [
    "P/V",
    "Tip Speed",
    "Impeller Speed",
    "Geometric Similarity",
]


# ============================================================
# PROCESS GUIDANCE
# ============================================================

PROCESS_GUIDANCE = {
    "Liquid-Liquid": [
        "P/V",
        "Tip Speed",
        "Blend Time",
        "Reynolds Number",
        "Impeller Speed",
    ],
    "Solid-Liquid": [
        "P/V",
        "Tip Speed",
        "Njs",
        "Suspension Quality",
        "Blend Time",
    ],
    "Gas-Liquid": [
        "P/V",
        "Gas Flow",
        "Gas Holdup",
        "kLa",
        "Superficial Gas Velocity",
    ],
    "Gas-Liquid-Solid": [
        "P/V",
        "Gas Flow",
        "Njs",
        "Gas Holdup",
        "kLa",
    ],
}


# ============================================================
# REACTOR INPUT PANEL
# ============================================================

def reactor_input_panel(name, process_type):

    st.subheader(f"⚙️ {name} Reactor")

    defaults = {
        "Lab": {
            "volume": 1.0,
            "diameter": 1.0,
            "height": 1.5,
        },
        "Pilot": {
            "volume": 10.0,
            "diameter": 2.0,
            "height": 2.5,
        },
        "Commercial": {
            "volume": 50.0,
            "diameter": 3.0,
            "height": 4.0,
        },
        "Reactor": {
            "volume": 10.0,
            "diameter": 2.0,
            "height": 2.5,
        },
    }

    d = defaults.get(
        name,
        defaults["Reactor"],
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        working_volume = st.number_input(
            "Working volume (m³)",
            min_value=0.001,
            value=float(d["volume"]),
            step=0.1,
            key=f"{name}_volume",
        )

        density = st.number_input(
            "Liquid density (kg/m³)",
            min_value=1.0,
            value=1000.0,
            step=10.0,
            key=f"{name}_density",
        )

        viscosity_mpas = st.number_input(
            "Viscosity (mPa·s)",
            min_value=0.001,
            value=1.0,
            step=0.1,
            key=f"{name}_viscosity",
        )

        viscosity_pa_s = viscosity_mpas / 1000.0

        surface_tension = st.number_input(
            "Surface tension (N/m)",
            min_value=0.0001,
            value=0.072,
            step=0.001,
            format="%.4f",
            key=f"{name}_surface_tension",
        )

    with col2:

        tank_diameter = st.number_input(
            "Tank diameter (m)",
            min_value=0.05,
            value=float(d["diameter"]),
            step=0.05,
            key=f"{name}_diameter",
        )

        straight_height = st.number_input(
            "Straight side height (m)",
            min_value=0.05,
            value=float(d["height"]),
            step=0.05,
            key=f"{name}_straight_height",
        )

        bottom_options = list(REACTOR_HEADS.keys())

        bottom_type = st.selectbox(
            "Bottom head",
            bottom_options,
            key=f"{name}_bottom",
        )

        top_type = st.selectbox(
            "Top head",
            bottom_options,
            key=f"{name}_top",
        )

    with col3:

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
            st.metric(
                "Calculated vessel volume",
                f"{fmt(vessel_volume, 3)} m³",
            )

        try:
            liquid_height, _ = liquid_height_from_volume(
                working_volume=working_volume,
                D=tank_diameter,
                straight_height=straight_height,
                bottom_type=bottom_type,
                top_type=top_type,
            )
        except Exception:
            liquid_height = 0.0

        st.metric(
            "Calculated liquid height",
            f"{fmt(liquid_height, 3)} m",
        )

    st.divider()

    st.markdown("### Agitation")

    ag_col1, ag_col2, ag_col3, ag_col4 = st.columns(4)

    agitator_names = list(AGITATORS.keys())

    with ag_col1:

        agitator = st.selectbox(
            "Agitator",
            agitator_names,
            key=f"{name}_agitator",
        )

    agitator_data = AGITATORS.get(
        agitator,
        {},
    )

    default_ratio = agitator_data.get(
        "default_diameter_ratio",
        0.40,
    )

    default_impeller_diameter = (
        tank_diameter * default_ratio
    )

    with ag_col2:

        impeller_diameter = st.number_input(
            "Impeller diameter (m)",
            min_value=0.01,
            value=float(default_impeller_diameter),
            step=0.01,
            key=f"{name}_impeller_diameter",
        )

    with ag_col3:

        number_impellers = st.number_input(
            "Number of impellers",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            key=f"{name}_number_impellers",
        )

        rpm = st.number_input(
            "Agitator speed (RPM)",
            min_value=0.1,
            max_value=3000.0,
            value=150.0,
            step=5.0,
            key=f"{name}_rpm",
        )

    with ag_col4:

        number_baffles = st.number_input(
            "Number of baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
            key=f"{name}_baffles",
        )

        clearance = st.number_input(
            "Impeller clearance (m)",
            min_value=0.001,
            value=max(
                0.05,
                tank_diameter * 0.20,
            ),
            step=0.01,
            key=f"{name}_clearance",
        )

    gas_flow = 0.0
    gas_density = 1.2
    gas_viscosity = 1.8e-5
    gas_diffusivity = 2e-9
    bubble_diameter = 3.0
    gas_holdup = 0.05

    if process_type in [
        "Gas-Liquid",
        "Gas-Liquid-Solid",
    ]:

        st.divider()
        st.markdown("### Gas-Liquid Parameters")

        gas_col1, gas_col2, gas_col3 = st.columns(3)

        with gas_col1:

            gas_flow = st.number_input(
                "Gas flow (m³/h)",
                min_value=0.0,
                value=5.0,
                step=0.5,
                key=f"{name}_gas_flow",
            )

            gas_density = st.number_input(
                "Gas density (kg/m³)",
                min_value=0.001,
                value=1.2,
                step=0.1,
                key=f"{name}_gas_density",
            )

        with gas_col2:

            gas_viscosity = st.number_input(
                "Gas viscosity (Pa·s)",
                min_value=1e-8,
                value=1.8e-5,
                format="%.2e",
                key=f"{name}_gas_viscosity",
            )

            gas_diffusivity = st.number_input(
                "Gas diffusivity (m²/s)",
                min_value=1e-12,
                value=2e-9,
                format="%.2e",
                key=f"{name}_gas_diffusivity",
            )

        with gas_col3:

            bubble_diameter = st.number_input(
                "Bubble diameter (mm)",
                min_value=0.01,
                value=3.0,
                step=0.1,
                key=f"{name}_bubble_diameter",
            )

            gas_holdup = st.number_input(
                "Gas holdup",
                min_value=0.0,
                max_value=0.95,
                value=0.05,
                step=0.01,
                key=f"{name}_gas_holdup",
            )

    return {
        "name": name,
        "working_volume": working_volume,
        "working_volume_m3": working_volume,
        "vessel_volume": vessel_volume,
        "vessel_volume_m3": vessel_volume,
        "tank_diameter_m": tank_diameter,
        "straight_height_m": straight_height,
        "bottom_type": bottom_type,
        "top_type": top_type,
        "liquid_height_m": liquid_height,
        "density": density,
        "density_kg_m3": density,
        "viscosity_pa_s": viscosity_pa_s,
        "surface_tension_n_m": surface_tension,
        "rpm": rpm,
        "impeller_diameter_m": impeller_diameter,
        "number_impellers": number_impellers,
        "agitator": agitator,
        "number_baffles": number_baffles,
        "impeller_clearance_m": clearance,
        "gas_flow_m3_h": gas_flow,
        "gas_density_kg_m3": gas_density,
        "gas_viscosity_pa_s": gas_viscosity,
        "gas_diffusivity_m2_s": gas_diffusivity,
        "bubble_diameter_mm": bubble_diameter,
        "gas_holdup_fraction": gas_holdup,
    }


# ============================================================
# REACTOR CALCULATION
# ============================================================

def calculate_reactor_case(data, process_type):

    result = calculate_reactor(
        volume_m3=data["working_volume_m3"],
        tank_diameter_m=data["tank_diameter_m"],
        liquid_height_m=data["liquid_height_m"],
        density_kg_m3=data["density_kg_m3"],
        viscosity_pa_s=data["viscosity_pa_s"],
        surface_tension_n_m=data["surface_tension_n_m"],
        rpm=data["rpm"],
        impeller_diameter_m=data["impeller_diameter_m"],
        number_impellers=data["number_impellers"],
        agitator=data["agitator"],
        impeller_clearance_m=data["impeller_clearance_m"],
        gas_flow_m3_h=data["gas_flow_m3_h"],
        gas_density_kg_m3=data["gas_density_kg_m3"],
        gas_viscosity_pa_s=data["gas_viscosity_pa_s"],
        gas_diffusivity_m2_s=data["gas_diffusivity_m2_s"],
        bubble_diameter_mm=data["bubble_diameter_mm"],
        gas_holdup_fraction=data["gas_holdup_fraction"],
    )

    if result is None:
        result = {}

    if not isinstance(result, dict):
        result = dict(result)

    result.update(data)

    result["process_type"] = process_type

    return result


# ============================================================
# VALIDATION
# ============================================================

def validate_case(result):

    try:

        validation = validate_reactor(
            volume_m3=result["working_volume_m3"],
            vessel_volume_m3=result["vessel_volume_m3"],
            tank_diameter_m=result["tank_diameter_m"],
            straight_height_m=result["straight_height_m"],
            liquid_height_m=result["liquid_height_m"],
            impeller_diameter_m=result["impeller_diameter_m"],
            number_impellers=result["number_impellers"],
            number_baffles=result["number_baffles"],
            rpm=result["rpm"],
            agitator=result["agitator"],
            density_kg_m3=result["density_kg_m3"],
            viscosity_pa_s=result["viscosity_pa_s"],
            power_volume_kw_m3=result.get(
                "power_volume_kw_m3"
            ),
            gas_flow_m3_h=result.get(
                "gas_flow_m3_h",
                0.0,
            ),
            kLa_1_h=result.get(
                "kLa_1_h"
            ),
        )

        result["validation"] = validation

    except TypeError:

        try:
            result["validation"] = validate_reactor(
                result
            )

        except Exception as exc:
            result["validation"] = {
                "status": "ERROR",
                "message": str(exc),
            }

    except Exception as exc:

        result["validation"] = {
            "status": "ERROR",
            "message": str(exc),
        }

    return result


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚗️ Reactor Scale-Up")

project_name = st.sidebar.text_input(
    "Project Name",
    "Reactor Scale-Up Study",
)

prepared_by = st.sidebar.text_input(
    "Prepared By",
    "Process Engineering",
)

process_type = st.sidebar.selectbox(
    "Process Type",
    PROCESS_TYPES,
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

scaleup_basis = st.sidebar.selectbox(
    "Scale-Up Basis",
    SCALEUP_BASES,
)

st.sidebar.divider()

st.sidebar.markdown("### Recommended Parameters")

for parameter in PROCESS_GUIDANCE.get(
    process_type,
    [],
):
    st.sidebar.write(f"• {parameter}")


# ============================================================
# HEADER
# ============================================================

st.title("⚗️ Reactor Scale-Up Engineering Studio")

st.caption(
    "Professional reactor geometry, agitation, mixing, "
    "gas-liquid and scale-up engineering dashboard"
)


# ============================================================
# REACTOR SELECTION
# ============================================================

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


# ============================================================
# INPUT TABS
# ============================================================

input_tabs = st.tabs(
    [
        f"⚙️ {name}"
        for name in reactor_names
    ]
)

reactor_inputs = []

for tab, name in zip(
    input_tabs,
    reactor_names,
):

    with tab:

        data = reactor_input_panel(
            name,
            process_type,
        )

        reactor_inputs.append(data)


# ============================================================
# CALCULATE BUTTON
# ============================================================

st.divider()

calculate_button = st.button(
    "🚀 Run Engineering Calculation",
    type="primary",
    use_container_width=True,
)


# ============================================================
# CALCULATION
# ============================================================

if calculate_button:

    calculated_results = []

    with st.spinner(
        "Running reactor engineering calculations..."
    ):

        for data in reactor_inputs:

            try:

                result = calculate_reactor_case(
                    data,
                    process_type,
                )

                result = validate_case(
                    result
                )

                calculated_results.append(
                    result
                )

            except Exception as exc:

                st.error(
                    f"Calculation failed for "
                    f"{data['name']}"
                )

                st.exception(exc)

                st.stop()

    st.session_state["reactor_results"] = (
        calculated_results
    )

    st.session_state["calculation_complete"] = True


# ============================================================
# DISPLAY RESULTS
# ============================================================

if not st.session_state.get(
    "calculation_complete",
    False,
):

    st.info(
        "Enter reactor parameters and click "
        "'Run Engineering Calculation'."
    )

    st.stop()


reactors = st.session_state.get(
    "reactor_results",
    [],
)

if not reactors:

    st.warning(
        "No reactor calculation results available."
    )

    st.stop()


# ============================================================
# SCALE-UP
# ============================================================

scale_result = None

if len(reactors) >= 2:

    base = reactors[0]
    target = reactors[-1]

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
                "message": str(exc),
            }

    except Exception as exc:

        scale_result = {
            "status": "ERROR",
            "message": str(exc),
        }


# ============================================================
# DASHBOARD KPI
# ============================================================

st.header("📊 Engineering Dashboard")

selected = reactors[-1]

c1, c2, c3, c4 = st.columns(4)

with c1:

    kpi(
        "Working Volume",
        selected.get(
            "working_volume_m3"
        ),
        "m³",
    )

with c2:

    kpi(
        "Liquid Height",
        selected.get(
            "liquid_height_m"
        ),
        "m",
    )

with c3:

    kpi(
        "Impeller Speed",
        selected.get(
            "rpm"
        ),
        "RPM",
    )

with c4:

    kpi(
        "Impeller Diameter",
        selected.get(
            "impeller_diameter_m"
        ),
        "m",
    )


c5, c6, c7, c8 = st.columns(4)

with c5:

    kpi(
        "Power",
        get_value(
            selected,
            "power_kw",
            "power",
        ),
        "kW",
    )

with c6:

    kpi(
        "P/V",
        get_value(
            selected,
            "power_volume_kw_m3",
            "power_volume",
        ),
        "kW/m³",
    )

with c7:

    kpi(
        "Tip Speed",
        get_value(
            selected,
            "tip_speed_m_s",
            "tip_speed",
        ),
        "m/s",
    )

with c8:

    kpi(
        "Reynolds Number",
        get_value(
            selected,
            "reynolds_number",
            "re",
        ),
        "",
    )


# ============================================================
# RESULT TABS
# ============================================================

result_tabs = st.tabs(
    [
        "Performance",
        "Gas-Liquid",
        "Scale-Up",
        "Validation",
        "3D Reactor",
        "Reports",
    ]
)


# ============================================================
# PERFORMANCE TAB
# ============================================================

with result_tabs[0]:

    st.subheader("Mixing & Agitation Performance")

    rows = []

    performance_fields = [
        (
            "Working Volume",
            "working_volume_m3",
            "m³",
        ),
        (
            "Vessel Volume",
            "vessel_volume_m3",
            "m³",
        ),
        (
            "Tank Diameter",
            "tank_diameter_m",
            "m",
        ),
        (
            "Straight Height",
            "straight_height_m",
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
            "Number of Impellers",
            "number_impellers",
            "-",
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
            "-",
        ),
        (
            "Froude Number",
            "froude_number",
            "-",
        ),
        (
            "Pumping Capacity",
            "pumping_capacity_m3_s",
            "m³/s",
        ),
        (
            "Q/V",
            "q_over_v_1_s",
            "1/s",
        ),
        (
            "Turnover Time",
            "turnover_time_s",
            "s",
        ),
    ]

    for reactor in reactors:

        for label, key, unit in performance_fields:

            rows.append(
                {
                    "Reactor": reactor.get(
                        "name",
                        "Reactor",
                    ),
                    "Parameter": label,
                    "Value": reactor.get(key),
                    "Unit": unit,
                }
            )

    performance_df = pd.DataFrame(rows)

    st.dataframe(
        performance_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# GAS-LIQUID TAB
# ============================================================

with result_tabs[1]:

    st.subheader(
        "Gas-Liquid Engineering"
    )

    if process_type not in [
        "Gas-Liquid",
        "Gas-Liquid-Solid",
    ]:

        st.info(
            "Gas-liquid calculations are not "
            "active for the selected process type."
        )

    else:

        gas_fields = [
            (
                "Gas Flow",
                "gas_flow_m3_h",
                "m³/h",
            ),
            (
                "Superficial Gas Velocity",
                "superficial_gas_velocity_m_s",
                "m/s",
            ),
            (
                "Gas Holdup",
                "gas_holdup_fraction",
                "-",
            ),
            (
                "Bubble Diameter",
                "bubble_diameter_mm",
                "mm",
            ),
            (
                "Bubble Rise Velocity",
                "bubble_rise_velocity_m_s",
                "m/s",
            ),
            (
                "Bubble Reynolds Number",
                "bubble_reynolds_number",
                "-",
            ),
            (
                "Schmidt Number",
                "schmidt_number",
                "-",
            ),
            (
                "Sherwood Number",
                "sherwood_number",
                "-",
            ),
            (
                "Liquid Mass Transfer Coefficient",
                "kL_m_s",
                "m/s",
            ),
            (
                "Interfacial Area",
                "interfacial_area_m2_m3",
                "m²/m³",
            ),
            (
                "kLa",
                "kLa_1_h",
                "1/h",
            ),
        ]

        gas_rows = []

        for reactor in reactors:

            for label, key, unit in gas_fields:

                gas_rows.append(
                    {
                        "Reactor": reactor.get(
                            "name",
                            "Reactor",
                        ),
                        "Parameter": label,
                        "Value": reactor.get(key),
                        "Unit": unit,
                    }
                )

        gas_df = pd.DataFrame(
            gas_rows
        )

        st.dataframe(
            gas_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# SCALE-UP TAB
# ============================================================

with result_tabs[2]:

    st.subheader(
        "Reactor Scale-Up Analysis"
    )

    if scale_result is None:

        st.info(
            "Scale-up requires at least two reactors."
        )

    elif isinstance(scale_result, dict):

        scale_rows = []

        for key, value in scale_result.items():

            if isinstance(value, (dict, list, tuple)):
                continue

            scale_rows.append(
                {
                    "Parameter": str(key),
                    "Value": value,
                }
            )

        if scale_rows:

            scale_df = pd.DataFrame(
                scale_rows
            )

            st.dataframe(
                scale_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.json(scale_result)

    else:

        st.write(scale_result)


# ============================================================
# VALIDATION TAB
# ============================================================

with result_tabs[3]:

    st.subheader(
        "Engineering Validation"
    )

    validation_rows = []

    for reactor in reactors:

        validation = reactor.get(
            "validation"
        )

        if isinstance(validation, dict):

            for key, value in validation.items():

                if isinstance(
                    value,
                    (dict, list, tuple),
                ):
                    continue

                status = ""

                if str(value).upper() in [
                    "PASS",
                    "FAIL",
                    "WARNING",
                    "WARN",
                ]:

                    status = status_icon(
                        str(value).upper()
                    )

                validation_rows.append(
                    {
                        "Reactor": reactor.get(
                            "name",
                            "Reactor",
                        ),
                        "Check": str(key),
                        "Result": value,
                        "Status": status,
                    }
                )

        else:

            validation_rows.append(
                {
                    "Reactor": reactor.get(
                        "name",
                        "Reactor",
                    ),
                    "Check": "Validation",
                    "Result": validation,
                    "Status": "",
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

    else:

        st.info(
            "No validation results returned."
        )


# ============================================================
# 3D REACTOR TAB
# ============================================================

with result_tabs[4]:

    st.subheader(
        "🧊 3D Reactor Visualization"
    )

    reactor_names_for_3d = [
        reactor.get(
            "name",
            "Reactor",
        )
        for reactor in reactors
    ]

    selected_3d_name = st.selectbox(
        "Select reactor",
        reactor_names_for_3d,
        key="selected_3d_reactor",
    )

    selected_3d = next(
        reactor
        for reactor in reactors
        if reactor.get(
            "name",
            "Reactor",
        )
        == selected_3d_name
    )

    try:

        fig = create_reactor_animation(
            D=selected_3d.get(
                "tank_diameter_m"
            ),
            straight_height=selected_3d.get(
                "straight_height_m"
            ),
            bottom_type=selected_3d.get(
                "bottom_type"
            ),
            top_type=selected_3d.get(
                "top_type"
            ),
            liquid_height=selected_3d.get(
                "liquid_height_m"
            ),
            agitator=selected_3d.get(
                "agitator"
            ),
            impeller_diameter=selected_3d.get(
                "impeller_diameter_m"
            ),
            number_impellers=selected_3d.get(
                "number_impellers"
            ),
            rpm=selected_3d.get(
                "rpm"
            ),
            number_baffles=selected_3d.get(
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
            "Unable to generate 3D reactor visualization."
        )

        st.exception(exc)


# ============================================================
# REPORTS TAB
# ============================================================

with result_tabs[5]:

    st.subheader(
        "📑 Engineering Reports"
    )

    st.write(
        "Generate Word and Excel engineering reports "
        "from the calculated reactor results."
    )

    report_col1, report_col2 = st.columns(2)

    with report_col1:

        try:

            word_file = create_word_report(
                project_name=project_name,
                prepared_by=prepared_by,
                process_type=process_type,
                study_mode=study_mode,
                scaleup_basis=scaleup_basis,
                reactors=reactors,
                scaleup_result=(
                    scale_result
                    if len(reactors) >= 2
                    else None
                ),
            )

            if hasattr(
                word_file,
                "getvalue",
            ):

                word_data = word_file.getvalue()

            else:

                word_data = word_file

            st.download_button(
                label="📄 Download Word Report",
                data=word_data,
                file_name=(
                    "reactor_scale_up_report.docx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                use_container_width=True,
            )

        except Exception as exc:

            st.error(
                "Word report generation failed."
            )

            st.exception(exc)

    with report_col2:

        try:

            excel_file = create_excel_report(
                project_name=project_name,
                prepared_by=prepared_by,
                process_type=process_type,
                study_mode=study_mode,
                scaleup_basis=scaleup_basis,
                reactors=reactors,
                scaleup_result=(
                    scale_result
                    if len(reactors) >= 2
                    else None
                ),
            )

            if hasattr(
                excel_file,
                "getvalue",
            ):

                excel_data = excel_file.getvalue()

            else:

                excel_data = excel_file

            st.download_button(
                label="📊 Download Excel Report",
                data=excel_data,
                file_name=(
                    "reactor_scale_up_report.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        except Exception as exc:

            st.error(
                "Excel report generation failed."
            )

            st.exception(exc)


# ============================================================
# ENGINEERING DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "Engineering note: This dashboard provides calculation "
    "and scale-up support. Final reactor design, mechanical "
    "design, agitator selection, motor sizing, pressure/vacuum "
    "rating, heat-transfer-area sizing, process safety and "
    "equipment specification must be verified by qualified "
    "engineering personnel and applicable design standards."
)
