# ============================================================
# REACTOR SCALE-UP ENGINEERING STUDIO
# ============================================================

from pathlib import Path
import sys
import importlib.util
import inspect
import re

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
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# APPLICATION VERSION
# ============================================================

APP_VERSION = "2.0.0"


# ============================================================
# SAFE MODULE LOADER
# ============================================================

def load_module(module_name, file_path):
    """
    Load a Python module directly from an absolute file path.
    """

    file_path = Path(file_path)

    if not file_path.exists():

        st.error(
            f"Required Python file was not found:\n\n"
            f"{file_path}"
        )

        st.stop()

    try:

        spec = importlib.util.spec_from_file_location(
            module_name,
            str(file_path)
        )

        if spec is None or spec.loader is None:

            raise ImportError(
                f"Unable to create module specification for "
                f"{file_path}"
            )

        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

        return module

    except Exception as exc:

        st.error(
            f"Unable to load module:\n\n"
            f"{file_path}"
        )

        st.code(
            f"{type(exc).__name__}: {exc}"
        )

        st.stop()


# ============================================================
# IMPORT HELPER
# ============================================================

def import_project_module(module_name, relative_file):
    """
    Import project module using its exact file path.
    """

    module_path = BASE_DIR / relative_file

    return load_module(
        module_name,
        module_path
    )


# ============================================================
# LOAD REPORT GENERATOR
# ============================================================

REPORTING_DIR = BASE_DIR / "reporting"
REPORTING_FILE = REPORTING_DIR / "report_generator.py"

if not REPORTING_DIR.exists():

    st.error(
        "The 'reporting' folder was not found."
    )

    st.code(
        str(REPORTING_DIR)
    )

    st.stop()


if not REPORTING_FILE.exists():

    st.error(
        "The report_generator.py file was not found."
    )

    st.code(
        str(REPORTING_FILE)
    )

    st.stop()


report_generator = load_module(
    "reactor_scaleup_report_generator",
    REPORTING_FILE
)


if not hasattr(
    report_generator,
    "create_word_report"
):

    st.error(
        "report_generator.py does not contain "
        "create_word_report()."
    )

    st.stop()


if not hasattr(
    report_generator,
    "create_excel_report"
):

    st.error(
        "report_generator.py does not contain "
        "create_excel_report()."
    )

    st.stop()


create_word_report = (
    report_generator.create_word_report
)

create_excel_report = (
    report_generator.create_excel_report
)


# ============================================================
# LOAD CALCULATION ENGINE
# ============================================================

try:

    engine_module = import_project_module(
        "reactor_scaleup_engine",
        Path("calculations") / "engine.py"
    )

    if not hasattr(
        engine_module,
        "calculate_reactor"
    ):

        raise AttributeError(
            "calculations/engine.py does not contain "
            "calculate_reactor()."
        )

    calculate_reactor = (
        engine_module.calculate_reactor
    )

except Exception as exc:

    st.error(
        "Unable to load calculations/engine.py"
    )

    st.code(
        f"{type(exc).__name__}: {exc}"
    )

    st.stop()


# ============================================================
# LOAD SCALE-UP ENGINE
# ============================================================

try:

    scaleup_module = import_project_module(
        "reactor_scaleup_scaleup",
        Path("calculations") / "scaleup.py"
    )

    if not hasattr(
        scaleup_module,
        "calculate_scaleup"
    ):

        raise AttributeError(
            "calculations/scaleup.py does not contain "
            "calculate_scaleup()."
        )

    calculate_scaleup = (
        scaleup_module.calculate_scaleup
    )

except Exception as exc:

    st.error(
        "Unable to load calculations/scaleup.py"
    )

    st.code(
        f"{type(exc).__name__}: {exc}"
    )

    st.stop()


# ============================================================
# LOAD VALIDATION ENGINE
# ============================================================

try:

    validation_module = import_project_module(
        "reactor_scaleup_validation",
        Path("calculations") / "validation.py"
    )

    if not hasattr(
        validation_module,
        "validate_reactor"
    ):

        raise AttributeError(
            "calculations/validation.py does not contain "
            "validate_reactor()."
        )

    validate_reactor = (
        validation_module.validate_reactor
    )

except Exception as exc:

    st.error(
        "Unable to load calculations/validation.py"
    )

    st.code(
        f"{type(exc).__name__}: {exc}"
    )

    st.stop()


# ============================================================
# LOAD AGITATOR LIBRARY
# ============================================================

try:

    agitator_module = import_project_module(
        "reactor_scaleup_agitators",
        Path("libraries") / "agitator_geometry.py"
    )

    if not hasattr(
        agitator_module,
        "AGITATORS"
    ):

        raise AttributeError(
            "libraries/agitator_geometry.py does not contain "
            "AGITATORS."
        )

    AGITATORS = agitator_module.AGITATORS

except Exception as exc:

    st.error(
        "Unable to load libraries/agitator_geometry.py"
    )

    st.code(
        f"{type(exc).__name__}: {exc}"
    )

    st.stop()


# ============================================================
# LOAD REACTOR GEOMETRY
# ============================================================

try:

    geometry_module = import_project_module(
        "reactor_scaleup_geometry",
        Path("libraries") / "reactor_geometry.py"
    )

    required_geometry_functions = [
        "calculate_total_volume",
        "liquid_height_from_volume",
    ]

    for function_name in required_geometry_functions:

        if not hasattr(
            geometry_module,
            function_name
        ):

            raise AttributeError(
                f"reactor_geometry.py does not contain "
                f"{function_name}()."
            )

    if not hasattr(
        geometry_module,
        "REACTOR_HEADS"
    ):

        raise AttributeError(
            "reactor_geometry.py does not contain "
            "REACTOR_HEADS."
        )

    REACTOR_HEADS = geometry_module.REACTOR_HEADS

    calculate_total_volume = (
        geometry_module.calculate_total_volume
    )

    liquid_height_from_volume = (
        geometry_module.liquid_height_from_volume
    )

except Exception as exc:

    st.error(
        "Unable to load libraries/reactor_geometry.py"
    )

    st.code(
        f"{type(exc).__name__}: {exc}"
    )

    st.stop()


# ============================================================
# LOAD 3D VISUALIZATION
# ============================================================

try:

    visualization_module = import_project_module(
        "reactor_scaleup_3d",
        Path("visualization") / "reactor_3d.py"
    )

    if not hasattr(
        visualization_module,
        "create_reactor_animation"
    ):

        raise AttributeError(
            "reactor_3d.py does not contain "
            "create_reactor_animation()."
        )

    create_reactor_animation = (
        visualization_module.create_reactor_animation
    )

except Exception as exc:

    st.error(
        "Unable to load visualization/reactor_3d.py"
    )

    st.code(
        f"{type(exc).__name__}: {exc}"
    )

    st.stop()


# ============================================================
# CSS
# ============================================================

CSS = (
    "<style>"
    ".stApp {"
    "background:#f4f7fb;"
    "}"
    ".block-container {"
    "max-width:1550px;"
    "padding-top:1rem;"
    "padding-bottom:2rem;"
    "}"
    "h1,h2,h3 {"
    "color:#12344d !important;"
    "}"
    "[data-testid='stSidebar'] {"
    "background:#ffffff;"
    "}"
    "div[data-testid='stMetric'] {"
    "background:#ffffff;"
    "border:1px solid #d9e2ec;"
    "padding:14px;"
    "border-radius:12px;"
    "}"
    "div[data-testid='stMetricLabel'] {"
    "color:#486581 !important;"
    "font-weight:700;"
    "}"
    "div[data-testid='stMetricValue'] {"
    "color:#102a43 !important;"
    "font-weight:800;"
    "}"
    "button {"
    "border-radius:9px !important;"
    "}"
    ".section-box {"
    "background:white;"
    "border:1px solid #d9e2ec;"
    "border-radius:14px;"
    "padding:18px;"
    "margin-bottom:15px;"
    "}"
    ".small-note {"
    "color:#627d98;"
    "font-size:0.85rem;"
    "}"
    "</style>"
)

st.markdown(
    CSS,
    unsafe_allow_html=True
)


# ============================================================
# GENERIC HELPERS
# ============================================================

def fmt(value, decimals=3):

    if value is None:
        return "—"

    try:

        if pd.isna(value):
            return "—"

    except Exception:
        pass

    try:

        return f"{float(value):,.{decimals}f}"

    except (
        TypeError,
        ValueError
    ):

        return str(value)


def status_icon(status):

    status = str(status).upper()

    if status == "PASS":
        return "🟢"

    if status == "FAIL":
        return "🔴"

    return "🟠"


def kpi(
    label,
    value,
    unit="",
    decimals=3
):

    if value is None:

        display = "—"

    elif isinstance(
        value,
        str
    ):

        display = value

    else:

        display = fmt(
            value,
            decimals
        )

    st.metric(
        label=label,
        value=display,
        delta=unit if unit else None
    )


def clean_filename(name):

    name = str(name)

    name = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        name
    )

    return name[:100]


def get_value(
    data,
    *keys,
    default=None
):

    if not isinstance(
        data,
        dict
    ):

        return default

    for key in keys:

        value = data.get(key)

        if value is not None:

            return value

    return default


def numeric_value(
    data,
    *keys,
    default=None
):

    value = get_value(
        data,
        *keys,
        default=default
    )

    try:

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# COMPATIBLE FUNCTION CALLER
# ============================================================

def call_compatible(
    function,
    kwargs,
    positional_variants=None
):
    """
    Call a project function while tolerating small differences
    in argument names between module versions.
    """

    positional_variants = (
        positional_variants or []
    )

    try:

        signature = inspect.signature(
            function
        )

        parameters = signature.parameters

        accepts_kwargs = any(
            parameter.kind
            == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )

        if accepts_kwargs:

            return function(
                **kwargs
            )

        filtered_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in parameters
        }

        required_missing = []

        for parameter in parameters.values():

            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD
            ):

                if (
                    parameter.default
                    is inspect.Parameter.empty
                    and parameter.name
                    not in filtered_kwargs
                ):

                    required_missing.append(
                        parameter.name
                    )

        if not required_missing:

            return function(
                **filtered_kwargs
            )

    except Exception:
        pass

    last_error = None

    for args in positional_variants:

        try:

            return function(
                *args
            )

        except Exception as exc:

            last_error = exc

    if last_error is not None:

        raise last_error

    return function(
        **kwargs
    )


# ============================================================
# PROCESS GUIDANCE
# ============================================================

def process_guidance(
    process_type
):

    guidance = {

        "Liquid-Liquid":
            "Primary focus: blend time, circulation, P/V, tip speed and impeller selection.",

        "Solid-Liquid":
            "Primary focus: Njs, solids suspension, clearance, P/V and circulation.",

        "Gas-Liquid":
            "Primary focus: gas dispersion, P/V, tip speed, gas holdup, bubble contact time and kLa.",

        "Gas-Liquid-Solid":
            "Primary focus: gas dispersion, solids suspension, Njs, gas holdup, kLa and P/V.",

        "Crystallization":
            "Primary focus: suspension, circulation, shear, P/V and crystal quality.",

        "High-Viscosity":
            "Primary focus: torque, laminar power, close-clearance impeller and gearbox loading.",

        "General Mixing":
            "Primary focus: P/V, tip speed, Reynolds number, pumping and geometry ratios.",
    }

    return guidance.get(
        process_type,
        guidance["General Mixing"]
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "# ⚗️ Reactor Studio"
    )

    st.caption(
        "Process Engineering Scale-Up Platform"
    )

    st.divider()

    st.markdown(
        "### 📁 Project"
    )

    project_name = st.text_input(
        "Project Name",
        value="Reactor Scale-Up Study"
    )

    prepared_by = st.text_input(
        "Prepared By",
        value="Process Engineering"
    )

    st.divider()

    st.markdown(
        "### ⚙️ Study"
    )

    study_mode = st.selectbox(
        "Study Mode",
        [
            "Single Reactor",
            "Lab vs Pilot",
            "Pilot vs Commercial",
            "Lab vs Commercial",
            "Lab vs Pilot vs Commercial",
        ]
    )

    process_type = st.selectbox(
        "Reaction / Process Type",
        [
            "Liquid-Liquid",
            "Solid-Liquid",
            "Gas-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
            "High-Viscosity",
            "General Mixing",
        ]
    )

    scaleup_basis = st.selectbox(
        "Primary Scale-Up Basis",
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
        ]
    )

    st.divider()

    st.markdown(
        "### 🎯 Engineering Focus"
    )

    st.info(
        process_guidance(
            process_type
        )
    )

    st.caption(
        f"Application version: {APP_VERSION}"
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
        "Pilot"
    ]

elif study_mode == "Pilot vs Commercial":

    reactor_names = [
        "Pilot",
        "Commercial"
    ]

elif study_mode == "Lab vs Commercial":

    reactor_names = [
        "Lab",
        "Commercial"
    ]

else:

    reactor_names = [
        "Lab",
        "Pilot",
        "Commercial"
    ]


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚗️ Reactor Scale-Up Engineering Studio"
)

st.caption(
    f"{project_name}  •  "
    f"{process_type}  •  "
    f"{study_mode}"
)

st.divider()


# ============================================================
# REACTOR INPUT PANEL
# ============================================================

def reactor_input_panel(name):

    st.markdown(
        f"## ⚗️ {name} Reactor"
    )

    with st.container(
        border=True
    ):

        # ====================================================
        # PROCESS CONDITIONS
        # ====================================================

        st.markdown(
            "### 1. Process Conditions"
        )

        c1, c2, c3, c4 = st.columns(4)

        default_volume = {

            "Lab": 1.0,
            "Pilot": 10.0,
            "Commercial": 50.0,
            "Reactor": 10.0,

        }.get(
            name,
            10.0
        )

        with c1:

            working_volume = st.number_input(
                "Working Volume",
                min_value=0.001,
                value=default_volume,
                step=0.5,
                key=f"{name}_volume"
            )

            st.caption(
                "Unit: m³"
            )

        with c2:

            density = st.number_input(
                "Liquid Density",
                min_value=0.001,
                value=1000.0,
                step=10.0,
                key=f"{name}_density"
            )

            st.caption(
                "Unit: kg/m³"
            )

        with c3:

            viscosity_mpas = st.number_input(
                "Viscosity",
                min_value=0.001,
                value=1.0,
                step=0.1,
                key=f"{name}_viscosity"
            )

            st.caption(
                "Unit: mPa·s"
            )

        with c4:

            surface_tension = st.number_input(
                "Surface Tension",
                min_value=0.001,
                value=0.072,
                step=0.001,
                key=f"{name}_surface"
            )

            st.caption(
                "Unit: N/m"
            )

        viscosity_pa_s = (
            viscosity_mpas / 1000.0
        )

        # ====================================================
        # GEOMETRY
        # ====================================================

        st.markdown(
            "### 2. Reactor Geometry"
        )

        c1, c2, c3, c4 = st.columns(4)

        default_diameter = {

            "Lab": 1.0,
            "Pilot": 2.0,
            "Commercial": 3.0,
            "Reactor": 2.0,

        }.get(
            name,
            2.0
        )

        default_straight = {

            "Lab": 1.5,
            "Pilot": 2.5,
            "Commercial": 4.0,
            "Reactor": 2.5,

        }.get(
            name,
            2.5
        )

        with c1:

            tank_diameter = st.number_input(
                "Tank Internal Diameter",
                min_value=0.05,
                value=default_diameter,
                step=0.05,
                key=f"{name}_diameter"
            )

            st.caption(
                "Unit: m"
            )

        with c2:

            straight_height = st.number_input(
                "Straight Side Height",
                min_value=0.05,
                value=default_straight,
                step=0.05,
                key=f"{name}_straight"
            )

            st.caption(
                "Unit: m"
            )

        head_options = list(
            REACTOR_HEADS.keys()
        )

        if not head_options:

            st.error(
                "REACTOR_HEADS is empty."
            )

            st.stop()

        with c3:

            bottom_type = st.selectbox(
                "Bottom Head",
                head_options,
                index=min(
                    1,
                    len(head_options) - 1
                ),
                key=f"{name}_bottom"
            )

        with c4:

            top_type = st.selectbox(
                "Top Head",
                head_options,
                index=min(
                    1,
                    len(head_options) - 1
                ),
                key=f"{name}_top"
            )

        # ====================================================
        # VESSEL VOLUME
        # ====================================================

        try:

            vessel_volume = calculate_total_volume(
                D=tank_diameter,
                straight_height=straight_height,
                bottom_type=bottom_type,
                top_type=top_type
            )

            vessel_volume = float(
                vessel_volume
            )

        except Exception as exc:

            st.error(
                f"Vessel volume calculation failed: "
                f"{type(exc).__name__}: {exc}"
            )

            vessel_volume = 0.0

        # ====================================================
        # LIQUID HEIGHT
        # ====================================================

        try:

            liquid_height_result = (
                liquid_height_from_volume(
                    working_volume=working_volume,
                    D=tank_diameter,
                    straight_height=straight_height,
                    bottom_type=bottom_type,
                    top_type=top_type
                )
            )

            if isinstance(
                liquid_height_result,
                tuple
            ):

                liquid_height = float(
                    liquid_height_result[0]
                )

            else:

                liquid_height = float(
                    liquid_height_result
                )

        except Exception as exc:

            st.error(
                f"Liquid height calculation failed: "
                f"{type(exc).__name__}: {exc}"
            )

            liquid_height = 0.0

        # ====================================================
        # FILL %
        # ====================================================

        fill_percent = (

            working_volume
            / vessel_volume
            * 100.0

            if vessel_volume > 0

            else 0.0
        )

        g1, g2, g3 = st.columns(3)

        with g1:

            kpi(
                "Vessel Capacity",
                vessel_volume,
                "m³",
                3
            )

        with g2:

            kpi(
                "Liquid Height",
                liquid_height,
                "m",
                3
            )

        with g3:

            kpi(
                "Operating Fill",
                fill_percent,
                "%",
                1
            )

        st.progress(
            min(
                max(
                    fill_percent / 100.0,
                    0.0
                ),
                1.0
            )
        )

        if fill_percent > 100:

            st.error(
                "Working volume exceeds vessel capacity."
            )

        elif fill_percent > 90:

            st.warning(
                "Operating fill is high. Review required headspace."
            )

        # ====================================================
        # AGITATION
        # ====================================================

        st.markdown(
            "### 3. Agitation System"
        )

        agitator_options = list(
            AGITATORS.keys()
        )

        if not agitator_options:

            st.error(
                "AGITATORS library is empty."
            )

            st.stop()

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            agitator = st.selectbox(
                "Agitator Type",
                agitator_options,
                index=min(
                    1,
                    len(agitator_options) - 1
                ),
                key=f"{name}_agitator"
            )

        agitator_data = AGITATORS.get(
            agitator,
            {}
        )

        if not isinstance(
            agitator_data,
            dict
        ):

            agitator_data = {}

        default_ratio = agitator_data.get(
            "default_diameter_ratio",
            0.40
        )

        try:

            default_ratio = float(
                default_ratio
            )

        except Exception:

            default_ratio = 0.40

        default_impeller = max(
            0.02,
            round(
                tank_diameter
                * default_ratio,
                3
            )
        )

        with c2:

            impeller_diameter = st.number_input(
                "Impeller Diameter",
                min_value=0.02,
                value=default_impeller,
                step=0.01,
                key=f"{name}_impeller"
            )

            st.caption(
                "Unit: m"
            )

        with c3:

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{name}_nimp"
            )

        with c4:

            rpm = st.number_input(
                "Agitator Speed",
                min_value=0.1,
                value=150.0,
                step=5.0,
                key=f"{name}_rpm"
            )

            st.caption(
                "Unit: RPM"
            )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            number_baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{name}_baffles"
            )

        with c2:

            clearance = st.number_input(
                "Impeller Bottom Clearance",
                min_value=0.0,
                value=max(
                    0.05,
                    tank_diameter * 0.20
                ),
                step=0.01,
                key=f"{name}_clearance"
            )

            st.caption(
                "Unit: m"
            )

        with c3:

            kpi(
                "D/T",
                (
                    impeller_diameter
                    / tank_diameter
                    if tank_diameter > 0
                    else None
                ),
                "-",
                3
            )

        with c4:

            flow_description = (
                agitator_data.get(
                    "flow",
                    "Unknown"
                )
            )

            st.info(
                f"{agitator}: "
                f"{flow_description} flow"
            )

        # ====================================================
        # GAS PARAMETERS
        # ====================================================

        gas_flow = 0.0
        gas_density = 1.2
        gas_viscosity = 1.8e-5
        gas_diffusivity = 2e-9
        bubble_diameter = 3.0
        gas_holdup = 0.05

        if process_type in [
            "Gas-Liquid",
            "Gas-Liquid-Solid"
        ]:

            st.markdown(
                "### 4. Gas-Liquid Mass Transfer"
            )

            st.info(
                "Gas-liquid calculations are preliminary "
                "screening estimates. Final kLa should be "
                "validated using appropriate correlations, "
                "pilot data or vendor data."
            )

            g1, g2, g3, g4 = st.columns(4)

            with g1:

                gas_flow = st.number_input(
                    "Gas Flow",
                    min_value=0.0,
                    value=5.0,
                    step=0.5,
                    key=f"{name}_gasflow"
                )

                st.caption(
                    "Unit: m³/h"
                )

            with g2:

                bubble_diameter = st.number_input(
                    "Bubble Diameter",
                    min_value=0.1,
                    value=3.0,
                    step=0.1,
                    key=f"{name}_bubble"
                )

                st.caption(
                    "Unit: mm"
                )

            with g3:

                gas_holdup_percent = st.number_input(
                    "Gas Holdup",
                    min_value=0.1,
                    max_value=50.0,
                    value=5.0,
                    step=0.5,
                    key=f"{name}_holdup"
                )

                gas_holdup = (
                    gas_holdup_percent
                    / 100.0
                )

                st.caption(
                    "Unit: %"
                )

            with g4:

                gas_density = st.number_input(
                    "Gas Density",
                    min_value=0.001,
                    value=1.2,
                    step=0.1,
                    key=f"{name}_gasdensity"
                )

                st.caption(
                    "Unit: kg/m³"
                )

            g1, g2 = st.columns(2)

            with g1:

                gas_viscosity = st.number_input(
                    "Gas Viscosity",
                    min_value=1e-7,
                    value=1.8e-5,
                    format="%.2e",
                    key=f"{name}_gasviscosity"
                )

                st.caption(
                    "Unit: Pa·s"
                )

            with g2:

                gas_diffusivity = st.number_input(
                    "Gas-Liquid Diffusivity",
                    min_value=1e-12,
                    value=2e-9,
                    format="%.2e",
                    key=f"{name}_diffusivity"
                )

                st.caption(
                    "Unit: m²/s"
                )

        # ====================================================
        # CALCULATE REACTOR
        # ====================================================

        reactor_kwargs = {

            "volume_m3":
                working_volume,

            "working_volume_m3":
                working_volume,

            "tank_diameter_m":
                tank_diameter,

            "D":
                tank_diameter,

            "liquid_height_m":
                liquid_height,

            "density_kg_m3":
                density,

            "density":
                density,

            "viscosity_pa_s":
                viscosity_pa_s,

            "viscosity":
                viscosity_pa_s,

            "surface_tension_n_m":
                surface_tension,

            "surface_tension":
                surface_tension,

            "rpm":
                rpm,

            "speed_rpm":
                rpm,

            "N":
                rpm,

            "impeller_diameter_m":
                impeller_diameter,

            "Di":
                impeller_diameter,

            "number_impellers":
                number_impellers,

            "agitator":
                agitator,

            "impeller_clearance_m":
                clearance,

            "clearance_m":
                clearance,

            "number_baffles":
                number_baffles,

            "gas_flow_m3_h":
                gas_flow,

            "gas_density_kg_m3":
                gas_density,

            "gas_viscosity_pa_s":
                gas_viscosity,

            "gas_diffusivity_m2_s":
                gas_diffusivity,

            "bubble_diameter_mm":
                bubble_diameter,

            "gas_holdup_fraction":
                gas_holdup,
        }

        try:

            result = call_compatible(
                calculate_reactor,
                reactor_kwargs,
                positional_variants=[
                    (
                        working_volume,
                        tank_diameter,
                        liquid_height,
                        density,
                        viscosity_pa_s,
                        surface_tension,
                        rpm,
                        impeller_diameter,
                        number_impellers,
                        agitator,
                        clearance,
                        gas_flow,
                        gas_density,
                        gas_viscosity,
                        gas_diffusivity,
                        bubble_diameter,
                        gas_holdup,
                    )
                ]
            )

            if result is None:

                result = {}

            if not isinstance(
                result,
                dict
            ):

                result = {}

        except Exception as exc:

            st.error(
                f"Calculation error for {name}"
            )

            st.code(
                f"{type(exc).__name__}: {exc}"
            )

            result = {}

        # ====================================================
        # ADD INPUT DATA
        # ====================================================

        result.update({

            "name":
                name,

            "working_volume":
                working_volume,

            "working_volume_m3":
                working_volume,

            "vessel_volume":
                vessel_volume,

            "vessel_volume_m3":
                vessel_volume,

            "tank_diameter_m":
                tank_diameter,

            "D":
                tank_diameter,

            "straight_height_m":
                straight_height,

            "bottom_type":
                bottom_type,

            "top_type":
                top_type,

            "liquid_height_m":
                liquid_height,

            "density":
                density,

            "density_kg_m3":
                density,

            "viscosity_pa_s":
                viscosity_pa_s,

            "surface_tension_n_m":
                surface_tension,

            "rpm":
                rpm,

            "impeller_diameter_m":
                impeller_diameter,

            "number_impellers":
                number_impellers,

            "agitator":
                agitator,

            "number_baffles":
                number_baffles,

            "impeller_clearance_m":
                clearance,

            "gas_flow_m3_h":
                gas_flow,

            "gas_density_kg_m3":
                gas_density,

            "gas_viscosity_pa_s":
                gas_viscosity,

            "gas_diffusivity_m2_s":
                gas_diffusivity,

            "bubble_diameter_mm":
                bubble_diameter,

            "gas_holdup_fraction":
                gas_holdup,
        })

        # ====================================================
        # NORMALIZE COMMON OUTPUT NAMES
        # ====================================================

        if result.get(
            "power_volume_kw_m3"
        ) is None:

            power_w = result.get(
                "power_volume_w_m3"
            )

            if power_w is not None:

                result[
                    "power_volume_kw_m3"
                ] = (
                    float(power_w) / 1000.0
                )

        if result.get(
            "power_volume_w_m3"
        ) is None:

            power_kw = result.get(
                "power_volume_kw_m3"
            )

            if power_kw is not None:

                result[
                    "power_volume_w_m3"
                ] = (
                    float(power_kw) * 1000.0
                )

        if result.get(
            "Re"
        ) is None:

            result["Re"] = result.get(
                "reynolds_number"
            )

        if result.get(
            "Fr"
        ) is None:

            result["Fr"] = result.get(
                "froude_number"
            )

        if result.get(
            "tip_speed"
        ) is None:

            result["tip_speed"] = result.get(
                "tip_speed_m_s"
            )

        if result.get(
            "pumping_m3_h"
        ) is None:

            result["pumping_m3_h"] = result.get(
                "pumping_capacity_m3_h"
            )

        if result.get(
            "qv_1_h"
        ) is None:

            result["qv_1_h"] = result.get(
                "turnover_1_h"
            )

        # ====================================================
        # VALIDATION
        # ====================================================

        validation_kwargs = {

            "volume_m3":
                working_volume,

            "working_volume_m3":
                working_volume,

            "vessel_volume_m3":
                vessel_volume,

            "tank_diameter_m":
                tank_diameter,

            "D":
                tank_diameter,

            "straight_height_m":
                straight_height,

            "liquid_height_m":
                liquid_height,

            "impeller_diameter_m":
                impeller_diameter,

            "Di":
                impeller_diameter,

            "number_impellers":
                number_impellers,

            "number_baffles":
                number_baffles,

            "rpm":
                rpm,

            "agitator":
                agitator,

            "density_kg_m3":
                density,

            "viscosity_pa_s":
                viscosity_pa_s,

            "power_volume_kw_m3":
                result.get(
                    "power_volume_kw_m3"
                ),

            "gas_flow_m3_h":
                gas_flow,

            "kLa_1_h":
                result.get(
                    "kLa_1_h"
                ),
        }

        try:

            validation = call_compatible(
                validate_reactor,
                validation_kwargs,
                positional_variants=[]
            )

            if not isinstance(
                validation,
                dict
            ):

                validation = {
                    "overall": "REVIEW",
                    "failures": 0,
                    "warnings": 1,
                    "checks": [
                        {
                            "severity": "WARNING",
                            "message":
                                "Validation returned a non-dictionary result."
                        }
                    ]
                }

        except Exception as exc:

            validation = {

                "overall":
                    "REVIEW",

                "failures":
                    0,

                "warnings":
                    1,

                "checks": [

                    {

                        "severity":
                            "WARNING",

                        "message":
                            "Validation could not be completed: "
                            f"{type(exc).__name__}: {exc}",

                    }

                ],

            }

        result[
            "validation"
        ] = validation

        return result


# ============================================================
# CREATE REACTOR RESULTS
# ============================================================

reactors = []

for name in reactor_names:

    reactor_result = reactor_input_panel(
        name
    )

    reactors.append(
        reactor_result
    )


# ============================================================
# OVERALL ENGINEERING STATUS
# ============================================================

statuses = []

for reactor in reactors:

    validation = reactor.get(
        "validation",
        {}
    )

    status = str(
        validation.get(
            "overall",
            "REVIEW"
        )
    ).upper()

    statuses.append(
        status
    )


if "FAIL" in statuses:

    overall_status = "FAIL"

elif "REVIEW" in statuses:

    overall_status = "REVIEW"

else:

    overall_status = "PASS"


# ============================================================
# DASHBOARD KPI
# ============================================================

st.divider()

st.markdown(
    "## 📊 Engineering Dashboard"
)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    kpi(
        "Reactors",
        len(reactors),
        "count",
        0
    )

with c2:

    total_volume = sum(
        numeric_value(
            reactor,
            "working_volume",
            "working_volume_m3",
            default=0.0
        )
        or 0.0
        for reactor in reactors
    )

    kpi(
        "Working Volume",
        total_volume,
        "m³",
        2
    )

with c3:

    pv_values = [

        numeric_value(
            reactor,
            "power_volume_kw_m3"
        )

        for reactor in reactors

        if numeric_value(
            reactor,
            "power_volume_kw_m3"
        ) is not None

    ]

    max_pv = (
        max(pv_values)
        if pv_values
        else None
    )

    kpi(
        "Maximum P/V",
        max_pv,
        "kW/m³",
        3
    )

with c4:

    tip_values = [

        numeric_value(
            reactor,
            "tip_speed",
            "tip_speed_m_s"
        )

        for reactor in reactors

        if numeric_value(
            reactor,
            "tip_speed",
            "tip_speed_m_s"
        ) is not None

    ]

    max_tip = (
        max(tip_values)
        if tip_values
        else None
    )

    kpi(
        "Maximum Tip Speed",
        max_tip,
        "m/s",
        2
    )

with c5:

    st.metric(
        "Engineering Status",
        f"{status_icon(overall_status)} "
        f"{overall_status}"
    )


# ============================================================
# TABS
# ============================================================

(
    tab_results,
    tab_gas,
    tab_scaleup,
    tab_validation,
    tab_3d,
    tab_report,
) = st.tabs(
    [
        "📊 Performance",
        "🫧 Gas-Liquid",
        "📈 Scale-Up",
        "✅ Validation",
        "🧊 3D Reactor",
        "📄 Reports",
    ]
)


# ============================================================
# PERFORMANCE TAB
# ============================================================

with tab_results:

    st.markdown(
        "## Mixing & Agitation Performance"
    )

    for reactor in reactors:

        st.markdown(
            f"### ⚗️ "
            f"{reactor.get('name', 'Reactor')}"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            kpi(
                "Power",
                reactor.get(
                    "power_kw"
                ),
                "kW",
                2
            )

        with c2:

            kpi(
                "P/V",
                reactor.get(
                    "power_volume_kw_m3"
                ),
                "kW/m³",
                3
            )

        with c3:

            kpi(
                "Tip Speed",
                reactor.get(
                    "tip_speed"
                ),
                "m/s",
                2
            )

        with c4:

            kpi(
                "Reynolds Number",
                reactor.get(
                    "Re"
                ),
                "-",
                0
            )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            kpi(
                "Froude Number",
                reactor.get(
                    "Fr"
                ),
                "-",
                4
            )

        with c2:

            kpi(
                "Pumping",
                reactor.get(
                    "pumping_m3_h"
                ),
                "m³/h",
                2
            )

        with c3:

            kpi(
                "Q/V",
                reactor.get(
                    "qv_1_h"
                ),
                "1/h",
                3
            )

        with c4:

            kpi(
                "Turnover Time",
                reactor.get(
                    "turnover_time_min"
                ),
                "min",
                2
            )

        performance_rows = [

            {
                "Parameter": "Working Volume",
                "Value": fmt(
                    reactor.get(
                        "working_volume"
                    ),
                    3
                ),
                "Unit": "m³"
            },

            {
                "Parameter": "Vessel Capacity",
                "Value": fmt(
                    reactor.get(
                        "vessel_volume"
                    ),
                    3
                ),
                "Unit": "m³"
            },

            {
                "Parameter": "Tank Diameter",
                "Value": fmt(
                    reactor.get(
                        "tank_diameter_m"
                    ),
                    3
                ),
                "Unit": "m"
            },

            {
                "Parameter": "Straight Height",
                "Value": fmt(
                    reactor.get(
                        "straight_height_m"
                    ),
                    3
                ),
                "Unit": "m"
            },

            {
                "Parameter": "Liquid Height",
                "Value": fmt(
                    reactor.get(
                        "liquid_height_m"
                    ),
                    3
                ),
                "Unit": "m"
            },

            {
                "Parameter": "Impeller Diameter",
                "Value": fmt(
                    reactor.get(
                        "impeller_diameter_m"
                    ),
                    3
                ),
                "Unit": "m"
            },

            {
                "Parameter": "Number of Impellers",
                "Value": reactor.get(
                    "number_impellers"
                ),
                "Unit": "count"
            },

            {
                "Parameter": "Agitator Speed",
                "Value": fmt(
                    reactor.get(
                        "rpm"
                    ),
                    1
                ),
                "Unit": "RPM"
            },

            {
                "Parameter": "Power",
                "Value": fmt(
                    reactor.get(
                        "power_kw"
                    ),
                    3
                ),
                "Unit": "kW"
            },

            {
                "Parameter": "P/V",
                "Value": fmt(
                    reactor.get(
                        "power_volume_kw_m3"
                    ),
                    4
                ),
                "Unit": "kW/m³"
            },

            {
                "Parameter": "P/V",
                "Value": fmt(
                    reactor.get(
                        "power_volume_w_m3"
                    ),
                    2
                ),
                "Unit": "W/m³"
            },

            {
                "Parameter": "Tip Speed",
                "Value": fmt(
                    reactor.get(
                        "tip_speed"
                    ),
                    3
                ),
                "Unit": "m/s"
            },

            {
                "Parameter": "Reynolds Number",
                "Value": fmt(
                    reactor.get(
                        "Re"
                    ),
                    0
                ),
                "Unit": "-"
            },

            {
                "Parameter": "Froude Number",
                "Value": fmt(
                    reactor.get(
                        "Fr"
                    ),
                    5
                ),
                "Unit": "-"
            },

            {
                "Parameter": "Pumping Capacity",
                "Value": fmt(
                    reactor.get(
                        "pumping_m3_h"
                    ),
                    3
                ),
                "Unit": "m³/h"
            },

            {
                "Parameter": "Q/V",
                "Value": fmt(
                    reactor.get(
                        "qv_1_h"
                    ),
                    3
                ),
                "Unit": "1/h"
            },

            {
                "Parameter": "Turnover Time",
                "Value": fmt(
                    reactor.get(
                        "turnover_time_min"
                    ),
                    3
                ),
                "Unit": "min"
            },

        ]

        st.dataframe(
            pd.DataFrame(
                performance_rows
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# GAS-LIQUID TAB
# ============================================================

with tab_gas:

    st.markdown(
        "## 🫧 Gas-Liquid Mass Transfer"
    )

    if process_type not in [
        "Gas-Liquid",
        "Gas-Liquid-Solid"
    ]:

        st.info(
            "Gas-liquid calculations become active when "
            "Gas-Liquid or Gas-Liquid-Solid is selected."
        )

    else:

        st.warning(
            "kLa and bubble hydrodynamic values shown here "
            "are screening estimates. Final design should "
            "be validated using appropriate correlations, "
            "pilot data and/or vendor data."
        )

        for reactor in reactors:

            st.markdown(
                f"### "
                f"{reactor.get('name', 'Reactor')}"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Gas Flow",
                    reactor.get(
                        "gas_flow_m3_h"
                    ),
                    "m³/h",
                    2
                )

            with c2:

                kpi(
                    "Superficial Gas Velocity",
                    reactor.get(
                        "gas_superficial_velocity_m_s"
                    ),
                    "m/s",
                    4
                )

            with c3:

                holdup = reactor.get(
                    "gas_holdup_fraction"
                )

                kpi(
                    "Gas Holdup",
                    (
                        holdup * 100
                        if holdup is not None
                        else None
                    ),
                    "%",
                    2
                )

            with c4:

                bubble_m = reactor.get(
                    "bubble_diameter_m"
                )

                if bubble_m is None:

                    bubble_mm = reactor.get(
                        "bubble_diameter_mm"
                    )

                    if bubble_mm is not None:

                        bubble_m = (
                            bubble_mm / 1000.0
                        )

                kpi(
                    "Bubble Diameter",
                    bubble_m,
                    "m",
                    4
                )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Bubble Rise Velocity",
                    reactor.get(
                        "bubble_rise_velocity_m_s"
                    ),
                    "m/s",
                    4
                )

            with c2:

                kpi(
                    "Bubble Residence Time",
                    reactor.get(
                        "bubble_residence_time_min"
                    ),
                    "min",
                    2
                )

            with c3:

                kpi(
                    "Bubble Reynolds",
                    reactor.get(
                        "bubble_reynolds"
                    ),
                    "-",
                    0
                )

            with c4:

                kpi(
                    "Schmidt Number",
                    reactor.get(
                        "schmidt_number"
                    ),
                    "-",
                    0
                )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Sherwood Number",
                    reactor.get(
                        "sherwood_number"
                    ),
                    "-",
                    2
                )

            with c2:

                kpi(
                    "kL",
                    reactor.get(
                        "kL_m_s"
                    ),
                    "m/s",
                    6
                )

            with c3:

                kpi(
                    "Interfacial Area",
                    reactor.get(
                        "interfacial_area_m2_m3"
                    ),
                    "m²/m³",
                    2
                )

            with c4:

                kpi(
                    "kLa",
                    reactor.get(
                        "kLa_1_h"
                    ),
                    "1/h",
                    2
                )


# ============================================================
# SCALE-UP TAB
# ============================================================

scale_result = None

with tab_scaleup:

    st.markdown(
        "## 📈 Scale-Up Analysis"
    )

    if len(reactors) < 2:

        st.info(
            "Select a multi-reactor study mode."
        )

    else:

        base = reactors[0]
        target = reactors[1]

        scaleup_kwargs = {

            "base":
                base,

            "target":
                target,

            "basis":
                scaleup_basis,

            "scaleup_basis":
                scaleup_basis,

        }

        try:

            scale_result = call_compatible(
                calculate_scaleup,
                scaleup_kwargs,
                positional_variants=[
                    (
                        base,
                        target,
                        scaleup_basis
                    ),

                    (
                        base,
                        target
                    ),
                ]
            )

        except Exception as exc:

            st.error(
                "Scale-up calculation failed."
            )

            st.code(
                f"{type(exc).__name__}: {exc}"
            )

        if scale_result is not None:

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                kpi(
                    "Base Volume",
                    base.get(
                        "working_volume"
                    ),
                    "m³",
                    3
                )

            with c2:

                kpi(
                    "Target Volume",
                    target.get(
                        "working_volume"
                    ),
                    "m³",
                    3
                )

            with c3:

                base_volume = numeric_value(
                    base,
                    "working_volume",
                    "working_volume_m3"
                )

                target_volume = numeric_value(
                    target,
                    "working_volume",
                    "working_volume_m3"
                )

                volume_ratio = (

                    target_volume
                    / base_volume

                    if base_volume
                    and base_volume > 0

                    else None
                )

                kpi(
                    "Volume Ratio",
                    volume_ratio,
                    "×",
                    2
                )

            with c4:

                st.metric(
                    "Scale-Up Basis",
                    scaleup_basis
                )

            st.divider()

            if isinstance(
                scale_result,
                dict
            ):

                c1, c2, c3 = st.columns(3)

                with c1:

                    kpi(
                        "Target RPM",
                        scale_result.get(
                            "target_rpm"
                        ),
                        "RPM",
                        2
                    )

                with c2:

                    kpi(
                        "Target Tip Speed",
                        scale_result.get(
                            "target_tip_speed"
                        ),
                        "m/s",
                        3
                    )

                with c3:

                    kpi(
                        "Target P/V",
                        scale_result.get(
                            "target_power_volume_kw_m3"
                        ),
                        "kW/m³",
                        4
                    )

                st.markdown(
                    "### Scale-Up Calculation Details"
                )

                scale_rows = []

                for key, value in scale_result.items():

                    if not isinstance(
                        value,
                        (
                            dict,
                            list,
                            tuple
                        )
                    ):

                        scale_rows.append({

                            "Parameter":
                                key,

                            "Value":
                                value,

                        })

                if scale_rows:

                    st.dataframe(
                        pd.DataFrame(
                            scale_rows
                        ),
                        use_container_width=True,
                        hide_index=True
                    )

                message = scale_result.get(
                    "message"
                )

                if message:

                    st.info(
                        str(message)
                    )

            else:

                st.write(
                    scale_result
                )


# ============================================================
# VALIDATION TAB
# ============================================================

with tab_validation:

    st.markdown(
        "## ✅ Engineering Validation"
    )

    st.markdown(
        f"### Overall Status: "
        f"{status_icon(overall_status)} "
        f"{overall_status}"
    )

    for reactor in reactors:

        validation = reactor.get(
            "validation",
            {}
        )

        st.markdown(
            f"#### "
            f"{reactor.get('name', 'Reactor')}"
        )

        validation_status = str(
            validation.get(
                "overall",
                "REVIEW"
            )
        ).upper()

        st.write(
            f"Status: "
            f"{status_icon(validation_status)} "
            f"{validation_status}"
        )

        checks = validation.get(
            "checks",
            []
        )

        if checks:

            rows = []

            for check in checks:

                if not isinstance(
                    check,
                    dict
                ):

                    rows.append({

                        "Status":
                            "REVIEW",

                        "Engineering Check":
                            str(check),

                    })

                    continue

                rows.append({

                    "Status":
                        check.get(
                            "severity",
                            "REVIEW"
                        ),

                    "Engineering Check":
                        check.get(
                            "message",
                            ""
                        ),

                })

            if rows:

                st.dataframe(
                    pd.DataFrame(
                        rows
                    ),
                    use_container_width=True,
                    hide_index=True
                )

        else:

            failures = validation.get(
                "failures",
                0
            )

            warnings = validation.get(
                "warnings",
                0
            )

            c1, c2 = st.columns(2)

            with c1:

                st.metric(
                    "Failures",
                    failures
                )

            with c2:

                st.metric(
                    "Warnings",
                    warnings
                )


# ============================================================
# 3D REACTOR TAB
# ============================================================

with tab_3d:

    st.markdown(
        "## 🧊 3D Reactor Visualization"
    )

    selected_name = st.selectbox(
        "Select Reactor",
        [
            reactor.get(
                "name",
                "Reactor"
            )
            for reactor in reactors
        ],
        key="selected_3d_reactor"
    )

    selected = next(
        reactor
        for reactor in reactors
        if reactor.get(
            "name"
        ) == selected_name
    )

    visualization_kwargs = {

        "D":
            selected.get(
                "tank_diameter_m"
            ),

        "tank_diameter":
            selected.get(
                "tank_diameter_m"
            ),

        "straight_height":
            selected.get(
                "straight_height_m"
            ),

        "bottom_type":
            selected.get(
                "bottom_type"
            ),

        "top_type":
            selected.get(
                "top_type"
            ),

        "liquid_height":
            selected.get(
                "liquid_height_m"
            ),

        "agitator":
            selected.get(
                "agitator"
            ),

        "impeller_diameter":
            selected.get(
                "impeller_diameter_m"
            ),

        "number_impellers":
            selected.get(
                "number_impellers"
            ),

        "rpm":
            selected.get(
                "rpm"
            ),

        "number_baffles":
            selected.get(
                "number_baffles"
            ),

        "frames_count":
            36,
    }

    try:

        fig = call_compatible(
            create_reactor_animation,
            visualization_kwargs,
            positional_variants=[]
        )

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "displaylogo": False,
                }
            )

    except Exception as exc:

        st.error(
            "3D visualization could not be generated."
        )

        st.code(
            f"{type(exc).__name__}: {exc}"
        )

    st.caption(
        "Visualization only — this is not a CFD solution."
    )


# ============================================================
# REPORT TAB
# ============================================================

with tab_report:

    st.markdown(
        "## 📄 Engineering Reports"
    )

    st.info(
        "Generate professional Word and Excel engineering "
        "reports containing reactor inputs, calculated "
        "results, scale-up results and validation."
    )

    # ========================================================
    # WORD
    # ========================================================

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
            "getvalue"
        ):

            word_data = (
                word_file.getvalue()
            )

        else:

            word_data = word_file

        safe_project_name = clean_filename(
            project_name
        )

        st.download_button(

            label=
                "📄 Download Engineering Report — Word",

            data=
                word_data,

            file_name=
                f"{safe_project_name}"
                "_Reactor_ScaleUp_Report.docx",

            mime=
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document",

            use_container_width=True,

        )

    except Exception as exc:

        st.error(
            "Word report generation failed."
        )

        st.code(
            f"{type(exc).__name__}: {exc}"
        )


    # ========================================================
    # EXCEL
    # ========================================================

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
            "getvalue"
        ):

            excel_data = (
                excel_file.getvalue()
            )

        else:

            excel_data = excel_file

        safe_project_name = clean_filename(
            project_name
        )

        st.download_button(

            label=
                "📊 Download Calculation Workbook — Excel",

            data=
                excel_data,

            file_name=
                f"{safe_project_name}"
                "_Reactor_ScaleUp_Calculations.xlsx",

            mime=
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet",

            use_container_width=True,

        )

    except Exception as exc:

        st.error(
            "Excel report generation failed."
        )

        st.code(
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "⚠️ Engineering screening software. "
    "Validate agitator Np/Nq, Njs, blend time, gas flooding, "
    "kLa, bubble hydrodynamics, vessel geometry, shaft torque, "
    "gearbox, motor, mechanical design and process-specific "
    "correlations against applicable standards, vendor data "
    "and pilot/plant measurements before final design."
)
