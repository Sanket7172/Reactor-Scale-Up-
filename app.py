import sys
import importlib.util
from pathlib import Path

import pandas as pd
import streamlit as st


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


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
# MODULE LOADER
# =========================================================

def load_module(module_name, file_path):
    """
    Dynamically load a Python module from a file path.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        str(file_path)
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to load module: {module_name}"
        )

    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module

    spec.loader.exec_module(module)

    return module


# =========================================================
# CORE CALCULATION MODULES
# =========================================================

try:

    from calculations.engine import calculate_reactor

except Exception as e:

    st.error(
        f"Unable to load calculations.engine:\n\n{e}"
    )

    st.stop()


try:

    from calculations.scaleup import calculate_scaleup

except Exception as e:

    st.error(
        f"Unable to load calculations.scaleup:\n\n{e}"
    )

    st.stop()


try:

    from calculations.validation import validate_reactor

except Exception as e:

    st.error(
        f"Unable to load calculations.validation:\n\n{e}"
    )

    st.stop()


# =========================================================
# LIBRARIES
# =========================================================

try:

    from libraries.agitator_geometry import AGITATORS

except Exception as e:

    st.error(
        f"Unable to load libraries.agitator_geometry:\n\n{e}"
    )

    st.stop()


try:

    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )

except Exception as e:

    st.error(
        f"Unable to load libraries.reactor_geometry:\n\n{e}"
    )

    st.stop()


# =========================================================
# LOAD 3D MODULE DYNAMICALLY
# =========================================================

REACTOR_3D_MODULE = None
REACTOR_3D_ERROR = None

try:

    reactor_3d_path = BASE_DIR / "visualization" / "reactor_3d.py"

    REACTOR_3D_MODULE = load_module(
        "reactor_3d_dynamic",
        reactor_3d_path
    )

except Exception as e:

    REACTOR_3D_ERROR = e


# =========================================================
# LOAD REPORTING MODULE DYNAMICALLY
# =========================================================

REPORT_MODULE = None
REPORT_ERROR = None

try:

    report_path = BASE_DIR / "reporting" / "report_generator.py"

    REPORT_MODULE = load_module(
        "report_generator_dynamic",
        report_path
    )

except Exception as e:

    REPORT_ERROR = e


# =========================================================
# REPORT FUNCTIONS
# =========================================================

create_word_report = None
create_excel_report = None

if REPORT_MODULE is not None:

    create_word_report = getattr(
        REPORT_MODULE,
        "create_word_report",
        None
    )

    create_excel_report = getattr(
        REPORT_MODULE,
        "create_excel_report",
        None
    )


# =========================================================
# 3D FUNCTION
# =========================================================

create_reactor_animation = None

if REACTOR_3D_MODULE is not None:

    create_reactor_animation = getattr(
        REACTOR_3D_MODULE,
        "create_reactor_animation",
        None
    )


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 650;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    .small-note {
        font-size: 0.85rem;
        color: #666;
    }

    .kpi-box {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 12px;
        background: #fafafa;
        text-align: center;
    }

    .kpi-title {
        font-size: 0.85rem;
        color: #666;
    }

    .kpi-value {
        font-size: 1.35rem;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# GENERAL HELPERS
# =========================================================

def fmt(value, digits=3):

    if value is None:
        return "—"

    try:
        return f"{float(value):.{digits}f}"

    except Exception:
        return str(value)


def safe_float(value, default=0.0):

    try:
        return float(value)

    except Exception:
        return default


def status_icon(status):

    status = str(status).lower()

    if status in ["pass", "passed", "ok", "valid", "yes"]:
        return "✅"

    if status in ["warning", "warn"]:
        return "⚠️"

    if status in ["fail", "failed", "error", "invalid", "no"]:
        return "❌"

    return "ℹ️"


def kpi(title, value):

    st.markdown(
        f"""
        <div class="kpi-box">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_value(data, key, default=None):

    if data is None:
        return default

    if isinstance(data, dict):
        return data.get(key, default)

    try:
        return getattr(data, key)

    except Exception:
        return default


# =========================================================
# IMPORTANT:
# STREAMLIT / PYARROW SAFE DATAFRAME
# =========================================================

def safe_dataframe(df):

    """
    Makes DataFrames safe for Streamlit / PyArrow.

    Mixed object columns such as:

        Result = [True, "PASS", 10, "Warning"]

    can cause:

        pyarrow.lib.ArrowTypeError

    Therefore object columns are converted to pandas
    string dtype.
    """

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    out = df.copy()

    for column in out.columns:

        if str(out[column].dtype) == "object":

            out[column] = out[column].astype("string")

    return out


# =========================================================
# IMPeller POSITION OPTIONS
# =========================================================

POSITION_OPTIONS = [
    "Bottom",
    "Middle",
    "Top",
]


# =========================================================
# IMPeller ELEVATION CALCULATION
# =========================================================

def calculate_impeller_elevations(
    number_impellers,
    liquid_height,
    bottom_clearance,
):

    number_impellers = int(number_impellers)

    liquid_height = safe_float(
        liquid_height,
        0.0
    )

    bottom_clearance = safe_float(
        bottom_clearance,
        0.30
    )

    if number_impellers <= 1:

        return [
            {
                "position": "Bottom",
                "elevation_m": bottom_clearance,
            }
        ]

    if number_impellers == 2:

        available_height = max(
            liquid_height - bottom_clearance,
            0.0
        )

        return [
            {
                "position": "Bottom",
                "elevation_m": bottom_clearance,
            },
            {
                "position": "Top",
                "elevation_m": (
                    bottom_clearance
                    + available_height * 0.55
                ),
            },
        ]

    available_height = max(
        liquid_height - bottom_clearance,
        0.0
    )

    return [
        {
            "position": "Bottom",
            "elevation_m": bottom_clearance,
        },
        {
            "position": "Middle",
            "elevation_m": (
                bottom_clearance
                + available_height * 0.50
            ),
        },
        {
            "position": "Top",
            "elevation_m": (
                bottom_clearance
                + available_height * 0.85
            ),
        },
    ]


# =========================================================
# VALIDATE IMPELLER CONFIGURATION
# =========================================================

def validate_impeller_configuration(
    impellers,
    liquid_height,
):

    errors = []
    warnings = []

    if not impellers:

        errors.append(
            "At least one impeller is required."
        )

        return errors, warnings

    positions = []

    elevations = []

    for i, impeller in enumerate(impellers, start=1):

        position = str(
            impeller.get(
                "position",
                ""
            )
        )

        diameter = safe_float(
            impeller.get(
                "diameter_m",
                impeller.get(
                    "D",
                    0
                )
            ),
            0
        )

        elevation = safe_float(
            impeller.get(
                "elevation_m",
                0
            ),
            0
        )

        if position in positions:

            errors.append(
                f"Impeller {i}: duplicate position '{position}'."
            )

        positions.append(position)

        if diameter <= 0:

            errors.append(
                f"Impeller {i}: diameter must be > 0 m."
            )

        if elevation < 0:

            errors.append(
                f"Impeller {i}: elevation cannot be negative."
            )

        if elevation > liquid_height:

            errors.append(
                f"Impeller {i}: elevation exceeds liquid height."
            )

        elevations.append(elevation)

        if position == "Bottom":

            clearance = safe_float(
                impeller.get(
                    "bottom_clearance_m",
                    0
                ),
                0
            )

            if clearance <= 0:

                warnings.append(
                    f"Impeller {i}: bottom clearance is not defined."
                )

    if len(elevations) > 1:

        if elevations != sorted(elevations):

            errors.append(
                "Impeller elevations must increase from bottom to top."
            )

    return errors, warnings


# =========================================================
# PROCESS TYPES
# =========================================================

PROCESS_TYPES = [
    "Liquid-Liquid",
    "Solid-Liquid",
    "Gas-Liquid",
    "Three-Phase",
]


# =========================================================
# SCALE-UP BASES
# =========================================================

SCALEUP_BASES = [
    "Constant P/V",
    "Constant Tip Speed",
    "Constant RPM",
    "Constant Froude Number",
]


# =========================================================
# REACTOR INPUT PANEL
# =========================================================

def reactor_input_panel():

    st.markdown(
        '<div class="section-title">Reactor & Process Inputs</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        reactor_name = st.text_input(
            "Reactor Name",
            value="R-101"
        )

        process_type = st.selectbox(
            "Process Type",
            PROCESS_TYPES
        )

        working_volume = st.number_input(
            "Working Volume (m³)",
            min_value=0.01,
            value=10.0,
            step=0.10
        )

        density = st.number_input(
            "Liquid Density (kg/m³)",
            min_value=0.1,
            value=1000.0,
            step=10.0
        )

    with col2:

        viscosity = st.number_input(
            "Viscosity (cP)",
            min_value=0.01,
            value=10.0,
            step=0.5
        )

        surface_tension = st.number_input(
            "Surface Tension (mN/m)",
            min_value=0.1,
            value=30.0,
            step=1.0
        )

        tank_diameter = st.number_input(
            "Tank Diameter (m)",
            min_value=0.10,
            value=2.10,
            step=0.05
        )

        straight_height = st.number_input(
            "Straight Side Height (m)",
            min_value=0.10,
            value=2.80,
            step=0.05
        )

    with col3:

        bottom_type = st.selectbox(
            "Bottom Head",
            list(REACTOR_HEADS.keys()),
            index=0
        )

        top_type = st.selectbox(
            "Top Head",
            list(REACTOR_HEADS.keys()),
            index=0
        )

        number_baffles = st.number_input(
            "Number of Baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1
        )

    # -----------------------------------------------------
    # VESSEL VOLUME
    # -----------------------------------------------------

    try:

        vessel_volume = calculate_total_volume(
            D=tank_diameter,
            straight_height=straight_height,
            bottom_type=bottom_type,
            top_type=top_type,
        )

    except TypeError:

        try:

            vessel_volume = calculate_total_volume(
                tank_diameter,
                straight_height,
                bottom_type,
                top_type,
            )

        except Exception:

            vessel_volume = None

    except Exception:

        vessel_volume = None

    # -----------------------------------------------------
    # LIQUID HEIGHT
    # -----------------------------------------------------

    try:

        liquid_height = liquid_height_from_volume(
            volume=working_volume,
            D=tank_diameter,
            bottom_type=bottom_type,
        )

    except TypeError:

        try:

            liquid_height = liquid_height_from_volume(
                working_volume,
                tank_diameter,
                bottom_type,
            )

        except Exception:

            liquid_height = straight_height

    except Exception:

        liquid_height = straight_height

    if liquid_height is None:

        liquid_height = straight_height

    liquid_height = min(
        safe_float(liquid_height, straight_height),
        straight_height
    )

    st.markdown(
        '<div class="section-title">Calculated Vessel Information</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi(
            "Total Vessel Volume",
            f"{fmt(vessel_volume)} m³"
        )

    with c2:
        kpi(
            "Working Volume",
            f"{fmt(working_volume)} m³"
        )

    with c3:
        kpi(
            "Liquid Height",
            f"{fmt(liquid_height)} m"
        )

    # =====================================================
    # AGITATION
    # =====================================================

    st.markdown(
        '<div class="section-title">Agitation Configuration</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    with c1:

        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=3,
            value=1,
            step=1
        )

    with c2:

        rpm = st.number_input(
            "Agitator Speed (RPM)",
            min_value=1.0,
            max_value=1000.0,
            value=120.0,
            step=5.0
        )

    # -----------------------------------------------------
    # AUTOMATIC ELEVATION
    # -----------------------------------------------------

    default_positions = calculate_impeller_elevations(
        number_impellers,
        liquid_height,
        0.30
    )

    impellers = []

    for i in range(int(number_impellers)):

        st.markdown(
            f"**Impeller {i + 1}**"
        )

        c1, c2, c3, c4 = st.columns(4)

        default_position = default_positions[i]["position"]

        with c1:

            position = st.selectbox(
                "Position",
                POSITION_OPTIONS,
                index=POSITION_OPTIONS.index(
                    default_position
                ),
                key=f"position_{i}"
            )

        with c2:

            agitator_type = st.selectbox(
                "Agitator Type",
                list(AGITATORS.keys()),
                key=f"agitator_{i}"
            )

        agitator_data = AGITATORS.get(
            agitator_type,
            {}
        )

        default_diameter = safe_float(
            agitator_data.get(
                "D",
                tank_diameter * 0.35
            ),
            tank_diameter * 0.35
        )

        with c3:

            diameter = st.number_input(
                "Impeller Diameter (m)",
                min_value=0.01,
                max_value=max(
                    tank_diameter * 0.95,
                    0.02
                ),
                value=min(
                    default_diameter,
                    tank_diameter * 0.90
                ),
                step=0.01,
                key=f"diameter_{i}"
            )

        with c4:

            if position == "Bottom":

                clearance = st.number_input(
                    "Bottom Clearance (m)",
                    min_value=0.01,
                    max_value=max(
                        liquid_height * 0.8,
                        0.02
                    ),
                    value=min(
                        0.30,
                        max(
                            liquid_height * 0.25,
                            0.02
                        )
                    ),
                    step=0.01,
                    key=f"clearance_{i}"
                )

                elevation = clearance

            else:

                clearance = None

                if position == "Middle":

                    elevation = liquid_height * 0.50

                else:

                    elevation = liquid_height * 0.85

                st.number_input(
                    "Elevation from Bottom (m)",
                    min_value=0.0,
                    value=float(elevation),
                    step=0.01,
                    key=f"elevation_display_{i}",
                    disabled=True
                )

        impeller_record = {

            "position": position,

            "agitator_type": agitator_type,

            "type": agitator_type,

            "diameter_m": float(diameter),

            "D": float(diameter),

            "bottom_clearance_m": (
                float(clearance)
                if clearance is not None
                else None
            ),

            "elevation_m": float(elevation),

            "elevation": float(elevation),

        }

        impellers.append(
            impeller_record
        )

    # -----------------------------------------------------
    # VALIDATE CONFIGURATION
    # -----------------------------------------------------

    impeller_errors, impeller_warnings = (
        validate_impeller_configuration(
            impellers,
            liquid_height
        )
    )

    if impeller_errors:

        for error in impeller_errors:

            st.error(
                f"Impeller configuration: {error}"
            )

    if impeller_warnings:

        for warning in impeller_warnings:

            st.warning(
                f"Impeller configuration: {warning}"
            )

    return {

        "reactor_name": reactor_name,

        "process_type": process_type,

        "working_volume_m3": working_volume,

        "density_kg_m3": density,

        "viscosity_cp": viscosity,

        "surface_tension_mN_m": surface_tension,

        "tank_diameter_m": tank_diameter,

        "straight_height_m": straight_height,

        "bottom_type": bottom_type,

        "top_type": top_type,

        "number_baffles": number_baffles,

        "vessel_volume_m3": vessel_volume,

        "liquid_height_m": liquid_height,

        "number_impellers": number_impellers,

        "rpm": rpm,

        "impellers": impellers,

        # Legacy compatibility
        "agitator_type": (
            impellers[0]["agitator_type"]
            if impellers
            else None
        ),

        "impeller_diameter_m": (
            impellers[0]["diameter_m"]
            if impellers
            else None
        ),

        "bottom_clearance_m": (
            impellers[0]["bottom_clearance_m"]
            if impellers
            else None
        ),

    }


# =========================================================
# REACTOR CALCULATION
# =========================================================

def calculate_reactor_case(inputs):

    """
    Calls the calculation engine.

    First attempts the new multi-impeller interface.
    Falls back to the legacy interface if required.
    """

    try:

        result = calculate_reactor(
            working_volume=inputs[
                "working_volume_m3"
            ],

            density=inputs[
                "density_kg_m3"
            ],

            viscosity=inputs[
                "viscosity_cp"
            ],

            surface_tension=inputs[
                "surface_tension_mN_m"
            ],

            tank_diameter=inputs[
                "tank_diameter_m"
            ],

            rpm=inputs[
                "rpm"
            ],

            impellers=inputs[
                "impellers"
            ],

            number_baffles=inputs[
                "number_baffles"
            ],

            process_type=inputs[
                "process_type"
            ],
        )

        return result

    except TypeError:

        # Legacy engine interface

        return calculate_reactor(

            working_volume=inputs[
                "working_volume_m3"
            ],

            density=inputs[
                "density_kg_m3"
            ],

            viscosity=inputs[
                "viscosity_cp"
            ],

            surface_tension=inputs[
                "surface_tension_mN_m"
            ],

            tank_diameter=inputs[
                "tank_diameter_m"
            ],

            rpm=inputs[
                "rpm"
            ],

            agitator_type=inputs[
                "agitator_type"
            ],

            impeller_diameter=inputs[
                "impeller_diameter_m"
            ],

            bottom_clearance=inputs[
                "bottom_clearance_m"
            ],

            number_baffles=inputs[
                "number_baffles"
            ],

            process_type=inputs[
                "process_type"
            ],
        )


# =========================================================
# VALIDATION
# =========================================================

def validate_case(inputs, result):

    try:

        return validate_reactor(
            inputs=inputs,
            result=result
        )

    except TypeError:

        try:

            return validate_reactor(
                result
            )

        except Exception as e:

            return {
                "error": str(e)
            }


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🏭 Reactor Scale-Up")

st.sidebar.markdown(
    "Professional reactor mixing and scale-up dashboard."
)

st.sidebar.markdown("---")

st.sidebar.subheader(
    "Reactor Selection"
)

reactor_selection = st.sidebar.selectbox(
    "Select Reactor",
    [
        "New Reactor"
    ]
)

st.sidebar.markdown("---")

st.sidebar.subheader(
    "Scale-Up Basis"
)

scaleup_basis = st.sidebar.selectbox(
    "Scale-Up Method",
    SCALEUP_BASES
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Engineering calculations are indicative and "
    "should be verified against plant/vendor data."
)


# =========================================================
# MAIN TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🏭 Reactor Scale-Up & Mixing Dashboard</div>',
    unsafe_allow_html=True
)

st.caption(
    "Reactor geometry • Agitation • Mixing • Scale-up • Validation • 3D visualization"
)


# =========================================================
# INPUTS
# =========================================================

inputs = reactor_input_panel()


# =========================================================
# CALCULATE BUTTON
# =========================================================

st.markdown("---")

calculate_button = st.button(
    "⚙️ Calculate Reactor",
    type="primary",
    width="stretch"
)


# =========================================================
# CALCULATION
# =========================================================

if calculate_button:

    try:

        if inputs["impellers"]:

            errors, warnings = (
                validate_impeller_configuration(
                    inputs["impellers"],
                    inputs["liquid_height_m"]
                )
            )

            if errors:

                st.error(
                    "Please correct the impeller configuration before calculation."
                )

                for error in errors:

                    st.error(error)

                st.stop()

        result = calculate_reactor_case(
            inputs
        )

        validation = validate_case(
            inputs,
            result
        )

        # -------------------------------------------------
        # STORE RESULTS
        # -------------------------------------------------

        st.session_state["reactor_inputs"] = inputs

        st.session_state["reactor_result"] = result

        st.session_state["reactor_validation"] = validation

        st.session_state["scaleup_basis"] = scaleup_basis

        st.success(
            "Reactor calculation completed successfully."
        )

    except Exception as e:

        st.error(
            "Reactor calculation failed."
        )

        st.exception(e)

        st.stop()


# =========================================================
# DISPLAY RESULTS
# =========================================================

if "reactor_result" not in st.session_state:

    st.info(
        "Enter the reactor parameters above and click "
        "'Calculate Reactor' to generate the engineering results."
    )

    st.stop()


inputs = st.session_state[
    "reactor_inputs"
]

result = st.session_state[
    "reactor_result"
]

validation = st.session_state[
    "reactor_validation"
]


# =========================================================
# RESULT TABS
# =========================================================

tabs = st.tabs(
    [
        "📊 Performance",
        "⚙️ Impeller Arrangement",
        "💨 Gas-Liquid",
        "📐 Scale-Up",
        "✅ Validation",
        "🧊 3D Reactor",
        "📄 Reports",
    ]
)


# =========================================================
# TAB 1 — PERFORMANCE
# =========================================================

with tabs[0]:

    st.subheader(
        "Reactor Mixing Performance"
    )

    performance_rows = []

    if isinstance(result, dict):

        performance_keys = [
            (
                "Power",
                "power_kw"
            ),
            (
                "Power / Volume",
                "power_per_volume"
            ),
            (
                "Power Number",
                "power_number"
            ),
            (
                "Tip Speed",
                "tip_speed"
            ),
            (
                "Reynolds Number",
                "reynolds_number"
            ),
            (
                "Froude Number",
                "froude_number"
            ),
            (
                "Pumping Capacity",
                "pumping_capacity"
            ),
            (
                "Mixing Time",
                "mixing_time"
            ),
        ]

        for label, key in performance_keys:

            if key in result:

                performance_rows.append(
                    {
                        "Parameter": label,
                        "Value": result.get(key),
                    }
                )

    if performance_rows:

        performance_df = pd.DataFrame(
            performance_rows
        )

        st.dataframe(
            safe_dataframe(performance_df),
            width="stretch",
            hide_index=True,
        )

    else:

        if isinstance(result, dict):

            raw_rows = []

            for key, value in result.items():

                if not isinstance(
                    value,
                    (
                        dict,
                        list,
                        tuple
                    )
                ):

                    raw_rows.append(
                        {
                            "Parameter": key,
                            "Value": value,
                        }
                    )

            if raw_rows:

                st.dataframe(
                    safe_dataframe(
                        pd.DataFrame(raw_rows)
                    ),
                    width="stretch",
                    hide_index=True,
                )


# =========================================================
# TAB 2 — IMPELLER ARRANGEMENT
# =========================================================

with tabs[1]:

    st.subheader(
        "Impeller Arrangement"
    )

    arrangement_rows = []

    for i, impeller in enumerate(
        inputs.get(
            "impellers",
            []
        ),
        start=1
    ):

        arrangement_rows.append(
            {
                "Impeller": i,

                "Position": impeller.get(
                    "position"
                ),

                "Agitator Type": impeller.get(
                    "agitator_type"
                ),

                "Diameter (m)": impeller.get(
                    "diameter_m"
                ),

                "Bottom Clearance (m)": (
                    impeller.get(
                        "bottom_clearance_m"
                    )
                    if impeller.get(
                        "bottom_clearance_m"
                    ) is not None
                    else "—"
                ),

                "Elevation (m)": impeller.get(
                    "elevation_m"
                ),
            }
        )

    arrangement_df = pd.DataFrame(
        arrangement_rows
    )

    st.dataframe(
        safe_dataframe(arrangement_df),
        width="stretch",
        hide_index=True,
    )

    st.markdown(
        f"**Liquid Height:** "
        f"{fmt(inputs.get('liquid_height_m'))} m"
    )

    st.markdown(
        f"**Agitator Speed:** "
        f"{fmt(inputs.get('rpm'), 1)} RPM"
    )

    st.markdown(
        f"**Number of Baffles:** "
        f"{inputs.get('number_baffles')}"
    )


# =========================================================
# TAB 3 — GAS-LIQUID
# =========================================================

with tabs[2]:

    st.subheader(
        "Gas-Liquid Mixing"
    )

    gas_rows = []

    if isinstance(result, dict):

        gas_keys = [
            (
                "Gas Flow",
                "gas_flow"
            ),
            (
                "Superficial Gas Velocity",
                "superficial_gas_velocity"
            ),
            (
                "Gas Power",
                "gas_power"
            ),
            (
                "Gas Hold-Up",
                "gas_hold_up"
            ),
            (
                "kLa",
                "kla"
            ),
        ]

        for label, key in gas_keys:

            if key in result:

                gas_rows.append(
                    {
                        "Parameter": label,
                        "Value": result.get(key),
                    }
                )

    if gas_rows:

        gas_df = pd.DataFrame(
            gas_rows
        )

        st.dataframe(
            safe_dataframe(gas_df),
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "Gas-liquid specific calculations are not available "
            "for the current calculation engine."
        )


# =========================================================
# TAB 4 — SCALE-UP
# =========================================================

with tabs[3]:

    st.subheader(
        "Reactor Scale-Up"
    )

    st.markdown(
        f"**Selected Basis:** `{scaleup_basis}`"
    )

    try:

        scaleup_result = calculate_scaleup(
            inputs=inputs,
            result=result,
            basis=scaleup_basis
        )

    except TypeError:

        try:

            scaleup_result = calculate_scaleup(
                inputs,
                result,
                scaleup_basis
            )

        except Exception as e:

            scaleup_result = {
                "error": str(e)
            }

    except Exception as e:

        scaleup_result = {
            "error": str(e)
        }

    if isinstance(
        scaleup_result,
        dict
    ):

        scaleup_rows = []

        for key, value in scaleup_result.items():

            if isinstance(
                value,
                (
                    dict,
                    list,
                    tuple
                )
            ):

                continue

            scaleup_rows.append(
                {
                    "Parameter": key,
                    "Value": value,
                }
            )

        if scaleup_rows:

            scaleup_df = pd.DataFrame(
                scaleup_rows
            )

            st.dataframe(
                safe_dataframe(scaleup_df),
                width="stretch",
                hide_index=True,
            )

        if "error" in scaleup_result:

            st.warning(
                scaleup_result["error"]
            )

    else:

        st.write(
            scaleup_result
        )


# =========================================================
# TAB 5 — VALIDATION
# =========================================================

with tabs[4]:

    st.subheader(
        "Engineering Validation"
    )

    validation_rows = []

    if isinstance(
        validation,
        dict
    ):

        for key, value in validation.items():

            if isinstance(
                value,
                list
            ):

                for item in value:

                    validation_rows.append(
                        {
                            "Check": key,
                            "Result": str(item),
                            "Status": "Information",
                        }
                    )

            else:

                validation_rows.append(
                    {
                        "Check": key,
                        "Result": str(value),
                        "Status": "Information",
                    }
                )

    elif isinstance(
        validation,
        list
    ):

        for item in validation:

            if isinstance(
                item,
                dict
            ):

                check = item.get(
                    "check",
                    item.get(
                        "parameter",
                        "Validation"
                    )
                )

                value = item.get(
                    "result",
                    item.get(
                        "value",
                        ""
                    )
                )

                status = item.get(
                    "status",
                    "Information"
                )

                validation_rows.append(
                    {
                        "Check": str(check),
                        "Result": str(value),
                        "Status": str(status),
                    }
                )

            else:

                validation_rows.append(
                    {
                        "Check": "Validation",
                        "Result": str(item),
                        "Status": "Information",
                    }
                )

    if validation_rows:

        validation_df = pd.DataFrame(
            validation_rows
        )

        st.dataframe(
            safe_dataframe(validation_df),
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No validation results returned."
        )


# =========================================================
# TAB 6 — 3D REACTOR
# =========================================================

with tabs[5]:

    st.subheader(
        "3D Reactor Visualization"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # DO NOT IMPORT reactor_3d AT APPLICATION STARTUP.
    # It has already been loaded dynamically above.
    # -----------------------------------------------------

    if REACTOR_3D_MODULE is None:

        st.error(
            "3D reactor module could not be loaded."
        )

        st.code(
            str(REACTOR_3D_ERROR)
        )

        st.info(
            "Check visualization/reactor_3d.py for the "
            "actual Python error. The rest of the dashboard "
            "remains available."
        )

    elif create_reactor_animation is None:

        st.error(
            "create_reactor_animation() was not found "
            "inside visualization/reactor_3d.py."
        )

    else:

        try:

            st.caption(
                "Parametric engineering visualization — "
                "not a CFD solution."
            )

            selected_3d = inputs

            # -------------------------------------------------
            # NEW MULTI-IMPELLER INTERFACE
            # -------------------------------------------------

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

                    impellers=selected_3d.get(
                        "impellers",
                        []
                    ),

                    rpm=selected_3d.get(
                        "rpm"
                    ),

                    number_baffles=selected_3d.get(
                        "number_baffles"
                    ),

                    frames_count=36,
                )

            except TypeError:

                # -------------------------------------------------
                # LEGACY REACTOR_3D INTERFACE
                # -------------------------------------------------

                first_impeller = (
                    selected_3d.get(
                        "impellers",
                        [{}]
                    )[0]
                    if selected_3d.get(
                        "impellers"
                    )
                    else {}
                )

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

                    agitator_type=first_impeller.get(
                        "agitator_type"
                    ),

                    impeller_diameter=first_impeller.get(
                        "diameter_m"
                    ),

                    rpm=selected_3d.get(
                        "rpm"
                    ),

                    number_baffles=selected_3d.get(
                        "number_baffles"
                    ),

                    frames_count=36,
                )

            if fig is not None:

                st.plotly_chart(
                    fig,
                    width="stretch",
                    config={
                        "displaylogo": False,
                        "responsive": True,
                    }
                )

            else:

                st.warning(
                    "The 3D visualization function returned no figure."
                )

        except Exception as e:

            st.error(
                "3D reactor visualization failed."
            )

            st.exception(e)


# =========================================================
# TAB 7 — REPORTS
# =========================================================

with tabs[6]:

    st.subheader(
        "Engineering Reports"
    )

    if REPORT_MODULE is None:

        st.error(
            "Reporting module could not be loaded."
        )

        st.code(
            str(REPORT_ERROR)
        )

    else:

        # -------------------------------------------------
        # WORD REPORT
        # -------------------------------------------------

        if create_word_report is not None:

            try:

                word_file = create_word_report(
                    inputs=inputs,
                    result=result,
                    validation=validation,
                )

                if word_file is not None:

                    st.download_button(
                        label="📄 Download Word Report",
                        data=word_file.getvalue()
                        if hasattr(
                            word_file,
                            "getvalue"
                        )
                        else word_file,
                        file_name=(
                            f"{inputs.get('reactor_name', 'reactor')}"
                            "_scale_up_report.docx"
                        ),
                        mime=(
                            "application/vnd.openxmlformats-officedocument"
                            ".wordprocessingml.document"
                        ),
                        width="stretch",
                    )

            except TypeError:

                try:

                    word_file = create_word_report(
                        inputs,
                        result,
                        validation,
                    )

                    if word_file is not None:

                        st.download_button(
                            label="📄 Download Word Report",
                            data=(
                                word_file.getvalue()
                                if hasattr(
                                    word_file,
                                    "getvalue"
                                )
                                else word_file
                            ),
                            file_name=(
                                f"{inputs.get('reactor_name', 'reactor')}"
                                "_scale_up_report.docx"
                            ),
                            mime=(
                                "application/vnd.openxmlformats-officedocument"
                                ".wordprocessingml.document"
                            ),
                            width="stretch",
                        )

                except Exception as e:

                    st.error(
                        f"Word report generation failed: {e}"
                    )

            except Exception as e:

                st.error(
                    f"Word report generation failed: {e}"
                )

        else:

            st.warning(
                "create_word_report() is not available."
            )

        # -------------------------------------------------
        # EXCEL REPORT
        # -------------------------------------------------

        if create_excel_report is not None:

            try:

                excel_file = create_excel_report(
                    inputs=inputs,
                    result=result,
                    validation=validation,
                )

                if excel_file is not None:

                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_file.getvalue()
                        if hasattr(
                            excel_file,
                            "getvalue"
                        )
                        else excel_file,
                        file_name=(
                            f"{inputs.get('reactor_name', 'reactor')}"
                            "_scale_up_report.xlsx"
                        ),
                        mime=(
                            "application/vnd.openxmlformats-officedocument"
                            ".spreadsheetml.sheet"
                        ),
                        width="stretch",
                    )

            except TypeError:

                try:

                    excel_file = create_excel_report(
                        inputs,
                        result,
                        validation,
                    )

                    if excel_file is not None:

                        st.download_button(
                            label="📊 Download Excel Report",
                            data=(
                                excel_file.getvalue()
                                if hasattr(
                                    excel_file,
                                    "getvalue"
                                )
                                else excel_file
                            ),
                            file_name=(
                                f"{inputs.get('reactor_name', 'reactor')}"
                                "_scale_up_report.xlsx"
                            ),
                            mime=(
                                "application/vnd.openxmlformats-officedocument"
                                ".spreadsheetml.sheet"
                            ),
                            width="stretch",
                        )

                except Exception as e:

                    st.error(
                        f"Excel report generation failed: {e}"
                    )

            except Exception as e:

                st.error(
                    f"Excel report generation failed: {e}"
                )

        else:

            st.warning(
                "create_excel_report() is not available."
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Reactor Scale-Up Dashboard | "
    "Process Engineering & Mixing Design"
)
