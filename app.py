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
    """
    Dynamically load a Python module from a file path.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            "Required file not found:\n"
            f"{file_path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        str(file_path),
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            "Unable to create module specification for:\n"
            f"{file_path}"
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

    from visualization.reactor_3d import (
        create_reactor_animation,
    )

except Exception as exc:

    st.error("Unable to load visualization.reactor_3d")
    st.exception(exc)
    st.stop()


# ============================================================
# REPORTING MODULE
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

    create_word_report = (
        report_generator.create_word_report
    )

    create_excel_report = (
        report_generator.create_excel_report
    )

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
    """
    <style>

    .stApp {
        background: #f4f7fb;
    }

    .block-container {
        max-width: 1550px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #12344d !important;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d9e2ec;
        padding: 14px;
        border-radius: 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #486581 !important;
        font-weight: 700;
    }

    div[data-testid="stMetricValue"] {
        color: #102a43 !important;
        font-weight: 800;
    }

    button {
        border-radius: 9px !important;
    }

    .section-box {
        background: white;
        border: 1px solid #d9e2ec;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def fmt(value, decimals=3):
    """
    Safely format numerical values.
    """

    if value is None:
        return "—"

    try:
        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):
        return str(value)


def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:

        number = float(value)

        if number != number:
            return default

        return number

    except (TypeError, ValueError):
        return default


def status_icon(status):
    """
    Return status indicator.
    """

    text = str(status).upper()

    if text == "PASS":
        return "🟢"

    if text == "FAIL":
        return "🔴"

    if text in ["WARNING", "WARN"]:
        return "🟠"

    return "🟠"


def kpi(label, value, unit="", decimals=3):
    """
    Display Streamlit KPI metric.
    """

    if value is None:
        display = "—"

    elif isinstance(value, str):
        display = value

    else:
        display = fmt(
            value,
            decimals,
        )

    if unit:
        label = f"{label} ({unit})"

    st.metric(
        label=label,
        value=display,
    )


def get_value(
    data,
    *keys,
    default=None,
):
    """
    Return first available value from a dictionary.
    """

    if not isinstance(data, dict):
        return default

    for key in keys:

        if (
            key in data
            and data[key] is not None
        ):

            return data[key]

    return default


# ============================================================
# IMPORTANT:
# STREAMLIT / PYARROW DATAFRAME SAFETY
# ============================================================

def safe_dataframe(df):
    """
    Convert mixed-type pandas DataFrames into
    Streamlit/PyArrow-compatible DataFrames.

    This specifically prevents errors such as:

        ArrowTypeError:
        Expected bytes, got a 'int' object

    caused by mixed object columns such as Result.
    """

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame()

    out = df.copy()

    for column in out.columns:

        try:

            dtype_name = str(out[column].dtype)

            if dtype_name == "object":

                out[column] = (
                    out[column]
                    .fillna("")
                    .astype(str)
                )

        except Exception:

            # Absolute fallback for problematic columns
            try:
                out[column] = out[column].apply(
                    lambda x: "" if x is None else str(x)
                )
            except Exception:
                pass

    return out


def display_dataframe(
    df,
    hide_index=True,
):
    """
    Centralized DataFrame display function.

    Every DataFrame displayed by this application
    passes through safe_dataframe().
    """

    safe_df = safe_dataframe(df)

    st.dataframe(
        safe_df,
        width="stretch",
        hide_index=hide_index,
    )


# ============================================================
# POSITION CONFIGURATION
# ============================================================

POSITION_OPTIONS = [
    "Bottom",
    "Middle",
    "Top",
]


POSITION_ORDER = {
    "Bottom": 1,
    "Middle": 2,
    "Top": 3,
}


# ============================================================
# AUTOMATIC IMPELLER ELEVATION
# ============================================================

def calculate_impeller_elevations(
    impellers,
    liquid_height_m,
    tank_diameter_m,
):
    """
    Calculate impeller elevation from vessel bottom.

    Rules:

    Bottom:
        Elevation = Bottom Clearance

    Middle:
        Elevation = midpoint between lower and upper
        mixing boundaries

    Top:
        Elevation = Liquid Height - Top Clearance

    If all three are present:

        Bottom = C

        Middle = H / 2

        Top = H - C_top

    The final elevations are checked against
    the liquid height.
    """

    if not impellers:
        return []

    H = max(
        safe_float(
            liquid_height_m,
            0.0,
        ),
        0.001,
    )

    T = max(
        safe_float(
            tank_diameter_m,
            0.0,
        ),
        0.001,
    )

    result = [
        dict(item)
        for item in impellers
    ]

    # --------------------------------------------------------
    # Identify positions
    # --------------------------------------------------------

    bottom = next(
        (
            item
            for item in result
            if item.get("position") == "Bottom"
        ),
        None,
    )

    middle = next(
        (
            item
            for item in result
            if item.get("position") == "Middle"
        ),
        None,
    )

    top = next(
        (
            item
            for item in result
            if item.get("position") == "Top"
        ),
        None,
    )

    # --------------------------------------------------------
    # Bottom boundary
    # --------------------------------------------------------

    if bottom is not None:

        clearance = safe_float(
            bottom.get(
                "bottom_clearance_m"
            ),
            T * 0.20,
        )

        clearance = max(
            clearance,
            0.01,
        )

        bottom[
            "elevation_from_bottom_m"
        ] = clearance

        lower_boundary = clearance

    else:

        lower_boundary = max(
            0.10 * T,
            0.05,
        )

    # --------------------------------------------------------
    # Upper boundary
    # --------------------------------------------------------

    if top is not None:

        top_diameter = safe_float(
            top.get(
                "impeller_diameter_m"
            ),
            T * 0.40,
        )

        upper_clearance = max(
            0.20 * T,
            0.25 * top_diameter,
        )

        upper_boundary = (
            H - upper_clearance
        )

    else:

        upper_boundary = (
            H
            - max(
                0.10 * T,
                0.10,
            )
        )

    # --------------------------------------------------------
    # Prevent invalid mixing zone
    # --------------------------------------------------------

    if upper_boundary <= lower_boundary:

        upper_boundary = (
            lower_boundary
            + max(
                0.30 * T,
                0.50 * T,
            )
        )

    # --------------------------------------------------------
    # Top impeller
    # --------------------------------------------------------

    if top is not None:

        top[
            "elevation_from_bottom_m"
        ] = upper_boundary

    # --------------------------------------------------------
    # Middle impeller
    # --------------------------------------------------------

    if middle is not None:

        middle[
            "elevation_from_bottom_m"
        ] = (
            lower_boundary
            + (
                upper_boundary
                - lower_boundary
            ) / 2.0
        )

    # --------------------------------------------------------
    # Only middle impeller
    # --------------------------------------------------------

    if (
        middle is not None
        and bottom is None
        and top is None
    ):

        middle[
            "elevation_from_bottom_m"
        ] = H / 2.0

    # --------------------------------------------------------
    # Clamp all elevations
    # --------------------------------------------------------

    for impeller in result:

        diameter = safe_float(
            impeller.get(
                "impeller_diameter_m"
            ),
            T * 0.40,
        )

        z = safe_float(
            impeller.get(
                "elevation_from_bottom_m"
            ),
            H / 2.0,
        )

        minimum_elevation = max(
            0.01,
            0.05 * diameter,
        )

        maximum_elevation = H - max(
            0.05,
            0.15 * diameter,
        )

        if maximum_elevation <= minimum_elevation:
            maximum_elevation = H * 0.95

        z = max(
            minimum_elevation,
            min(
                z,
                maximum_elevation,
            ),
        )

        impeller[
            "elevation_from_bottom_m"
        ] = z

        # Compatibility alias
        impeller[
            "elevation_m"
        ] = z

    # --------------------------------------------------------
    # Sort physically from bottom to top
    # --------------------------------------------------------

    result.sort(
        key=lambda x: safe_float(
            x.get(
                "elevation_from_bottom_m"
            )
        )
    )

    return result


# ============================================================
# IMPELLER VALIDATION
# ============================================================

def validate_impeller_configuration(
    impellers,
    liquid_height_m,
    tank_diameter_m,
):

    errors = []
    warnings = []

    H = safe_float(
        liquid_height_m
    )

    T = safe_float(
        tank_diameter_m
    )

    # --------------------------------------------------------
    # General
    # --------------------------------------------------------

    if not impellers:

        errors.append(
            "At least one impeller is required."
        )

        return errors, warnings

    if len(impellers) > 3:

        errors.append(
            "Maximum three impellers are supported."
        )

    if H <= 0:

        errors.append(
            "Liquid height must be greater than zero."
        )

    if T <= 0:

        errors.append(
            "Tank diameter must be greater than zero."
        )

    # --------------------------------------------------------
    # Position duplication
    # --------------------------------------------------------

    positions = [
        item.get("position")
        for item in impellers
    ]

    valid_positions = [
        position
        for position in positions
        if position in POSITION_OPTIONS
    ]

    if len(valid_positions) != len(
        set(valid_positions)
    ):

        errors.append(
            "Each position can be used only once. "
            "Use Bottom, Middle and Top for up to "
            "three impellers."
        )

    # --------------------------------------------------------
    # Individual checks
    # --------------------------------------------------------

    for impeller in impellers:

        number = impeller.get(
            "number",
            "?",
        )

        position = impeller.get(
            "position"
        )

        agitator = impeller.get(
            "agitator_type",
            impeller.get(
                "agitator",
                "Unknown",
            ),
        )

        diameter = safe_float(
            impeller.get(
                "impeller_diameter_m"
            )
        )

        elevation = safe_float(
            impeller.get(
                "elevation_from_bottom_m"
            )
        )

        # ----------------------------------------------------
        # Agitator
        # ----------------------------------------------------

        if not agitator:

            errors.append(
                f"Impeller {number}: "
                "agitator type is not selected."
            )

        # ----------------------------------------------------
        # Diameter
        # ----------------------------------------------------

        if diameter <= 0:

            errors.append(
                f"Impeller {number}: "
                "impeller diameter must be greater than zero."
            )

        elif diameter >= T:

            errors.append(
                f"Impeller {number}: "
                f"D = {diameter:.3f} m is greater than or equal "
                f"to tank diameter = {T:.3f} m."
            )

        elif diameter / T > 0.80:

            warnings.append(
                f"Impeller {number}: "
                f"D/T = {diameter / T:.3f}. "
                "Review impeller/vessel geometry."
            )

        # ----------------------------------------------------
        # Elevation
        # ----------------------------------------------------

        if elevation <= 0:

            errors.append(
                f"Impeller {number}: "
                "elevation must be greater than zero."
            )

        if H > 0 and elevation >= H:

            errors.append(
                f"Impeller {number}: "
                f"elevation = {elevation:.3f} m is at or above "
                f"liquid height = {H:.3f} m."
            )

        # ----------------------------------------------------
        # Bottom clearance
        # ----------------------------------------------------

        if position == "Bottom":

            clearance = impeller.get(
                "bottom_clearance_m"
            )

            if clearance is None:

                errors.append(
                    f"Impeller {number}: "
                    "Bottom impeller requires bottom clearance."
                )

            else:

                clearance = safe_float(
                    clearance
                )

                if clearance <= 0:

                    errors.append(
                        f"Impeller {number}: "
                        "bottom clearance must be greater than zero."
                    )

                if H > 0 and clearance >= H:

                    errors.append(
                        f"Impeller {number}: "
                        "bottom clearance cannot be greater "
                        "than liquid height."
                    )

    # --------------------------------------------------------
    # Elevation ordering
    # --------------------------------------------------------

    sorted_impellers = sorted(
        impellers,
        key=lambda x: safe_float(
            x.get(
                "elevation_from_bottom_m"
            )
        ),
    )

    for index in range(
        1,
        len(sorted_impellers),
    ):

        z1 = safe_float(
            sorted_impellers[
                index - 1
            ].get(
                "elevation_from_bottom_m"
            )
        )

        z2 = safe_float(
            sorted_impellers[
                index
            ].get(
                "elevation_from_bottom_m"
            )
        )

        if z2 <= z1:

            errors.append(
                "Impeller elevations must increase "
                "from bottom to top."
            )

    # --------------------------------------------------------
    # Minimum separation warning
    # --------------------------------------------------------

    for index in range(
        1,
        len(sorted_impellers),
    ):

        lower = sorted_impellers[
            index - 1
        ]

        upper = sorted_impellers[
            index
        ]

        z1 = safe_float(
            lower.get(
                "elevation_from_bottom_m"
            )
        )

        z2 = safe_float(
            upper.get(
                "elevation_from_bottom_m"
            )
        )

        d1 = safe_float(
            lower.get(
                "impeller_diameter_m"
            )
        )

        d2 = safe_float(
            upper.get(
                "impeller_diameter_m"
            )
        )

        spacing = z2 - z1

        recommended_spacing = (
            0.50 * max(
                d1,
                d2,
            )
        )

        if (
            spacing > 0
            and spacing < recommended_spacing
        ):

            warnings.append(
                f"Impellers {lower.get('number', '?')} and "
                f"{upper.get('number', '?')} are closely spaced "
                f"({spacing:.3f} m). Review impeller interference "
                "and mixing interaction."
            )

    return errors, warnings


# ============================================================
# PROCESS TYPES
# ============================================================

PROCESS_TYPES = [
    "Liquid-Liquid",
    "Solid-Liquid",
    "Gas-Liquid",
    "Gas-Liquid-Solid",
]


# ============================================================
# SCALE-UP BASES
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

def reactor_input_panel(
    name,
    process_type,
):

    st.subheader(
        f"⚙️ {name} Reactor"
    )

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

    # ========================================================
    # PROCESS / VESSEL DATA
    # ========================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        working_volume = st.number_input(
            "Working volume (m³)",
            min_value=0.001,
            value=float(
                d["volume"]
            ),
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

        viscosity_pa_s = (
            viscosity_mpas / 1000.0
        )

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
            value=float(
                d["diameter"]
            ),
            step=0.05,
            key=f"{name}_diameter",
        )

        straight_height = st.number_input(
            "Straight side height (m)",
            min_value=0.05,
            value=float(
                d["height"]
            ),
            step=0.05,
            key=f"{name}_straight_height",
        )

        head_options = list(
            REACTOR_HEADS.keys()
        )

        if not head_options:

            st.error(
                "No reactor head geometry is available."
            )

            st.stop()

        bottom_type = st.selectbox(
            "Bottom head",
            head_options,
            key=f"{name}_bottom",
        )

        top_type = st.selectbox(
            "Top head",
            head_options,
            key=f"{name}_top",
        )

    with col3:

        try:

            vessel_volume = (
                calculate_total_volume(
                    D=tank_diameter,
                    straight_height=straight_height,
                    bottom_type=bottom_type,
                    top_type=top_type,
                )
            )

        except Exception as exc:

            vessel_volume = None

            st.warning(
                "Unable to calculate vessel volume "
                f"from the selected geometry: {exc}"
            )

        if vessel_volume is not None:

            st.metric(
                "Calculated vessel volume",
                f"{fmt(vessel_volume, 3)} m³",
            )

        try:

            liquid_height_result = (
                liquid_height_from_volume(
                    working_volume=working_volume,
                    D=tank_diameter,
                    straight_height=straight_height,
                    bottom_type=bottom_type,
                    top_type=top_type,
                )
            )

            if isinstance(
                liquid_height_result,
                tuple,
            ):

                liquid_height = safe_float(
                    liquid_height_result[0]
                )

            else:

                liquid_height = safe_float(
                    liquid_height_result
                )

        except Exception:

            liquid_height = 0.0

        st.metric(
            "Calculated liquid height",
            f"{fmt(liquid_height, 3)} m",
        )

    # ========================================================
    # AGITATION
    # ========================================================

    st.divider()

    st.markdown(
        "### ⚙️ Multi-Impeller Agitation"
    )

    st.caption(
        "Configure up to three independent impellers. "
        "Each impeller may have a different agitator type "
        "and diameter. Bottom, Middle and Top positions "
        "are automatically converted into elevations."
    )

    # --------------------------------------------------------
    # NUMBER OF IMPELLERS
    # --------------------------------------------------------

    number_impellers = st.number_input(
        "Number of Impellers",
        min_value=1,
        max_value=3,
        value=1,
        step=1,
        key=f"{name}_number_impellers",
    )

    st.info(
        "For three impellers, the recommended arrangement "
        "is Bottom + Middle + Top."
    )

    agitator_names = list(
        AGITATORS.keys()
    )

    if not agitator_names:

        st.error(
            "No agitator geometry is available in "
            "libraries.agitator_geometry."
        )

        st.stop()

    # --------------------------------------------------------
    # COMMON SHAFT SPEED
    # --------------------------------------------------------

    rpm = st.number_input(
        "Agitator Speed (RPM)",
        min_value=0.1,
        max_value=3000.0,
        value=150.0,
        step=5.0,
        key=f"{name}_rpm",
    )

    number_baffles = st.number_input(
        "Number of Baffles",
        min_value=0,
        max_value=12,
        value=4,
        step=1,
        key=f"{name}_baffles",
    )

    st.markdown(
        "#### Individual Impeller Configuration"
    )

    raw_impellers = []

    # ========================================================
    # INDIVIDUAL IMPELLERS
    # ========================================================

    for i in range(
        int(number_impellers)
    ):

        st.markdown(
            f"**Impeller {i + 1}**"
        )

        c1, c2, c3, c4 = st.columns(
            [1.2, 1.8, 1.2, 1.5]
        )

        # ----------------------------------------------------
        # POSITION
        # ----------------------------------------------------

        with c1:

            position = st.selectbox(
                "Position",
                POSITION_OPTIONS,
                index=min(
                    i,
                    len(POSITION_OPTIONS) - 1,
                ),
                key=(
                    f"{name}_"
                    f"impeller_{i}_position"
                ),
            )

        # ----------------------------------------------------
        # AGITATOR
        # ----------------------------------------------------

        with c2:

            agitator_type = st.selectbox(
                "Agitator Type",
                agitator_names,
                key=(
                    f"{name}_"
                    f"impeller_{i}_type"
                ),
            )

        agitator_data = AGITATORS.get(
            agitator_type,
            {},
        )

        if not isinstance(
            agitator_data,
            dict,
        ):

            agitator_data = {}

        default_ratio = safe_float(
            agitator_data.get(
                "default_diameter_ratio",
                0.40,
            ),
            0.40,
        )

        if default_ratio <= 0:
            default_ratio = 0.40

        default_diameter = (
            tank_diameter
            * default_ratio
        )

        # ----------------------------------------------------
        # DIAMETER
        # ----------------------------------------------------

        with c3:

            max_impeller_diameter = max(
                0.10,
                tank_diameter * 0.95,
            )

            default_diameter = min(
                max(
                    0.05,
                    default_diameter,
                ),
                max_impeller_diameter,
            )

            impeller_diameter = st.number_input(
                "D (m)",
                min_value=0.05,
                max_value=max_impeller_diameter,
                value=float(
                    default_diameter
                ),
                step=0.01,
                key=(
                    f"{name}_"
                    f"impeller_{i}_diameter"
                ),
            )

        # ----------------------------------------------------
        # BOTTOM CLEARANCE
        # ----------------------------------------------------

        with c4:

            if position == "Bottom":

                max_clearance = max(
                    0.10,
                    liquid_height * 0.50,
                )

                default_clearance = min(
                    max_clearance,
                    max(
                        0.05,
                        tank_diameter * 0.20,
                    ),
                )

                bottom_clearance = st.number_input(
                    "Bottom Clearance (m)",
                    min_value=0.01,
                    max_value=max_clearance,
                    value=float(
                        default_clearance
                    ),
                    step=0.01,
                    key=(
                        f"{name}_"
                        f"impeller_{i}_clearance"
                    ),
                )

            else:

                st.text_input(
                    "Bottom Clearance (m)",
                    value="—",
                    disabled=True,
                    key=(
                        f"{name}_"
                        f"impeller_{i}_clearance_display"
                    ),
                )

                bottom_clearance = None

        # ----------------------------------------------------
        # STORE CONFIGURATION
        # ----------------------------------------------------

        raw_impellers.append(
            {
                "number": i + 1,

                "position": position,

                "agitator": agitator_type,

                "agitator_type": agitator_type,

                "impeller_diameter_m": (
                    impeller_diameter
                ),

                "diameter_m": (
                    impeller_diameter
                ),

                "bottom_clearance_m": (
                    bottom_clearance
                ),

                "elevation_from_bottom_m": None,

                "elevation_m": None,

                "rpm": rpm,
            }
        )

        st.divider()

    # ========================================================
    # AUTOMATIC ELEVATION
    # ========================================================

    impellers = (
        calculate_impeller_elevations(
            impellers=raw_impellers,
            liquid_height_m=liquid_height,
            tank_diameter_m=tank_diameter,
        )
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    geometry_errors, geometry_warnings = (
        validate_impeller_configuration(
            impellers=impellers,
            liquid_height_m=liquid_height,
            tank_diameter_m=tank_diameter,
        )
    )

    # ========================================================
    # ARRANGEMENT TABLE
    # ========================================================

    st.markdown(
        "#### Calculated Impeller Arrangement"
    )

    arrangement_rows = []

    for impeller in impellers:

        clearance_value = impeller.get(
            "bottom_clearance_m"
        )

        arrangement_rows.append(
            {
                "#": impeller.get(
                    "number"
                ),

                "Position": impeller.get(
                    "position"
                ),

                "Agitator Type": impeller.get(
                    "agitator_type",
                    impeller.get(
                        "agitator",
                        "",
                    ),
                ),

                "D (m)": round(
                    safe_float(
                        impeller.get(
                            "impeller_diameter_m"
                        )
                    ),
                    3,
                ),

                "Bottom Clearance (m)": (
                    round(
                        safe_float(
                            clearance_value
                        ),
                        3,
                    )
                    if clearance_value is not None
                    else "—"
                ),

                "Elevation from Bottom (m)": round(
                    safe_float(
                        impeller.get(
                            "elevation_from_bottom_m"
                        )
                    ),
                    3,
                ),

                "RPM": rpm,
            }
        )

    arrangement_df = pd.DataFrame(
        arrangement_rows
    )

    display_dataframe(
        arrangement_df,
        hide_index=True,
    )

    # --------------------------------------------------------
    # VALIDATION MESSAGE
    # --------------------------------------------------------

    if geometry_errors:

        for error in geometry_errors:

            st.error(
                f"⚠️ {error}"
            )

    else:

        st.success(
            "✓ Impeller arrangement is geometrically consistent."
        )

    if geometry_warnings:

        for warning in geometry_warnings:

            st.warning(
                f"⚠️ {warning}"
            )

    # ========================================================
    # GAS PARAMETERS
    # ========================================================

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

        st.markdown(
            "### Gas-Liquid Parameters"
        )

        gas_col1, gas_col2, gas_col3 = (
            st.columns(3)
        )

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

    # ========================================================
    # PRIMARY IMPELLER
    # ========================================================

    primary_impeller = (
        impellers[0]
        if impellers
        else {}
    )

    # ========================================================
    # RETURN COMPLETE REACTOR DATA
    # ========================================================

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

        # ----------------------------------------------------
        # MULTI-IMPELLER
        # ----------------------------------------------------

        "impellers": impellers,

        "number_impellers": len(
            impellers
        ),

        # ----------------------------------------------------
        # LEGACY COMPATIBILITY
        # ----------------------------------------------------

        "agitator": primary_impeller.get(
            "agitator_type"
        ),

        "impeller_diameter_m": (
            primary_impeller.get(
                "impeller_diameter_m"
            )
        ),

        "impeller_clearance_m": (
            primary_impeller.get(
                "bottom_clearance_m"
            )
        ),

        "number_baffles": int(
            number_baffles
        ),

        # ----------------------------------------------------
        # GAS
        # ----------------------------------------------------

        "gas_flow_m3_h": gas_flow,

        "gas_density_kg_m3": gas_density,

        "gas_viscosity_pa_s": gas_viscosity,

        "gas_diffusivity_m2_s": gas_diffusivity,

        "bubble_diameter_mm": bubble_diameter,

        "gas_holdup_fraction": gas_holdup,

        # ----------------------------------------------------
        # GEOMETRY VALIDATION
        # ----------------------------------------------------

        "impeller_geometry_errors": (
            geometry_errors
        ),

        "impeller_geometry_warnings": (
            geometry_warnings
        ),
    }


# ============================================================
# REACTOR CALCULATION
# ============================================================

def calculate_reactor_case(
    data,
    process_type,
):
    """
    Run reactor calculation.

    First attempts the new multi-impeller interface.

    If the current calculation engine does not yet support
    the impellers argument, automatically falls back to
    the legacy interface.
    """

    # ========================================================
    # COMMON PARAMETERS
    # ========================================================

    common = {

        "volume_m3": data[
            "working_volume_m3"
        ],

        "tank_diameter_m": data[
            "tank_diameter_m"
        ],

        "liquid_height_m": data[
            "liquid_height_m"
        ],

        "density_kg_m3": data[
            "density_kg_m3"
        ],

        "viscosity_pa_s": data[
            "viscosity_pa_s"
        ],

        "surface_tension_n_m": data[
            "surface_tension_n_m"
        ],

        "rpm": data[
            "rpm"
        ],

        "impeller_diameter_m": data[
            "impeller_diameter_m"
        ],

        "number_impellers": data[
            "number_impellers"
        ],

        "agitator": data[
            "agitator"
        ],

        "impeller_clearance_m": data[
            "impeller_clearance_m"
        ],

        "gas_flow_m3_h": data[
            "gas_flow_m3_h"
        ],

        "gas_density_kg_m3": data[
            "gas_density_kg_m3"
        ],

        "gas_viscosity_pa_s": data[
            "gas_viscosity_pa_s"
        ],

        "gas_diffusivity_m2_s": data[
            "gas_diffusivity_m2_s"
        ],

        "bubble_diameter_mm": data[
            "bubble_diameter_mm"
        ],

        "gas_holdup_fraction": data[
            "gas_holdup_fraction"
        ],
    }

    # ========================================================
    # TRY MULTI-IMPELLER ENGINE
    # ========================================================

    try:

        result = calculate_reactor(
            **common,
            impellers=data[
                "impellers"
            ],
        )

    except TypeError:

        # ====================================================
        # LEGACY ENGINE
        # ====================================================

        result = calculate_reactor(
            **common
        )

    # ========================================================
    # NORMALIZE RESULT
    # ========================================================

    if result is None:

        result = {}

    elif not isinstance(
        result,
        dict,
    ):

        try:

            result = dict(result)

        except Exception:

            result = {
                "calculation_result": result
            }

    # ========================================================
    # RETAIN ALL INPUT DATA
    # ========================================================

    # This ensures the downstream dashboard, validation,
    # visualization and reports always have the original
    # reactor configuration.

    result.update(data)

    result[
        "process_type"
    ] = process_type

    return result


# ============================================================
# VALIDATION
# ============================================================

def validate_case(result):
    """
    Run compatibility-aware reactor validation.
    """

    # ========================================================
    # FIRST ATTEMPT: EXPLICIT ARGUMENT INTERFACE
    # ========================================================

    try:

        validation = validate_reactor(

            volume_m3=result[
                "working_volume_m3"
            ],

            vessel_volume_m3=result[
                "vessel_volume_m3"
            ],

            tank_diameter_m=result[
                "tank_diameter_m"
            ],

            straight_height_m=result[
                "straight_height_m"
            ],

            liquid_height_m=result[
                "liquid_height_m"
            ],

            impeller_diameter_m=result[
                "impeller_diameter_m"
            ],

            number_impellers=result[
                "number_impellers"
            ],

            number_baffles=result[
                "number_baffles"
            ],

            rpm=result[
                "rpm"
            ],

            agitator=result[
                "agitator"
            ],

            density_kg_m3=result[
                "density_kg_m3"
            ],

            viscosity_pa_s=result[
                "viscosity_pa_s"
            ],

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

        result[
            "validation"
        ] = validation

        return result

    except TypeError:

        pass

    except Exception as exc:

        result[
            "validation"
        ] = {
            "status": "ERROR",
            "message": str(exc),
        }

        return result

    # ========================================================
    # SECOND ATTEMPT: DICT INTERFACE
    # ========================================================

    try:

        result[
            "validation"
        ] = validate_reactor(
            result
        )

    except Exception as exc:

        result[
            "validation"
        ] = {
            "status": "ERROR",
            "message": str(exc),
        }

    return result


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "calculation_complete" not in st.session_state:

    st.session_state[
        "calculation_complete"
    ] = False


if "reactor_results" not in st.session_state:

    st.session_state[
        "reactor_results"
    ] = []


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⚗️ Reactor Scale-Up"
)

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

st.sidebar.markdown(
    "### Recommended Parameters"
)

for parameter in PROCESS_GUIDANCE.get(
    process_type,
    [],
):

    st.sidebar.write(
        f"• {parameter}"
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚗️ Reactor Scale-Up Engineering Studio"
)

st.caption(
    "Professional reactor geometry, multi-impeller "
    "agitation, mixing, gas-liquid and scale-up "
    "engineering dashboard"
)


# ============================================================
# REACTOR SELECTION
# ============================================================

if study_mode == "Single Reactor":

    reactor_names = [
        "Reactor"
    ]

elif study_mode == "Lab vs Pilot":

    reactor_names = [
        "Lab",
        "Pilot",
    ]

elif study_mode == "Pilot vs Commercial":

    reactor_names = [
        "Pilot",
        "Commercial",
    ]

elif study_mode == "Lab vs Commercial":

    reactor_names = [
        "Lab",
        "Commercial",
    ]

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

        reactor_inputs.append(
            data
        )


# ============================================================
# CALCULATE BUTTON
# ============================================================

st.divider()

calculate_button = st.button(
    "🚀 Run Engineering Calculation",
    type="primary",
    width="stretch",
)


# ============================================================
# CALCULATION
# ============================================================

if calculate_button:

    # --------------------------------------------------------
    # Validate geometry
    # --------------------------------------------------------

    invalid_geometry = False

    for data in reactor_inputs:

        errors = data.get(
            "impeller_geometry_errors",
            [],
        )

        if errors:

            invalid_geometry = True

            st.error(
                f"Geometry validation failed for "
                f"{data['name']}"
            )

            for error in errors:

                st.error(
                    f"• {error}"
                )

    if invalid_geometry:

        st.warning(
            "Correct the impeller geometry before "
            "running the engineering calculation."
        )

        st.stop()

    # --------------------------------------------------------
    # Run calculations
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Store results
    # --------------------------------------------------------

    st.session_state[
        "reactor_results"
    ] = calculated_results

    st.session_state[
        "calculation_complete"
    ] = True


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

st.header(
    "📊 Engineering Dashboard"
)

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
        "Number of Impellers",
        selected.get(
            "number_impellers"
        ),
        "",
        0,
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
        "Impeller Arrangement",
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

    st.subheader(
        "Mixing & Agitation Performance"
    )

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

                    "Value": reactor.get(
                        key
                    ),

                    "Unit": unit,
                }
            )

    performance_df = pd.DataFrame(
        rows
    )

    display_dataframe(
        performance_df,
        hide_index=True,
    )


# ============================================================
# IMPELLER ARRANGEMENT TAB
# ============================================================

with result_tabs[1]:

    st.subheader(
        "⚙️ Individual Impeller Arrangement"
    )

    st.caption(
        "Each impeller is independently defined. "
        "Elevation is calculated from the selected position "
        "and reactor geometry."
    )

    for reactor in reactors:

        st.markdown(
            f"### {reactor.get('name', 'Reactor')}"
        )

        impellers = reactor.get(
            "impellers",
            [],
        )

        if not impellers:

            st.info(
                "No impeller configuration available."
            )

            continue

        rows = []

        for impeller in impellers:

            clearance_value = impeller.get(
                "bottom_clearance_m"
            )

            rows.append(
                {
                    "#": impeller.get(
                        "number"
                    ),

                    "Position": impeller.get(
                        "position"
                    ),

                    "Agitator Type": impeller.get(
                        "agitator_type",
                        impeller.get(
                            "agitator",
                            "",
                        ),
                    ),

                    "D (m)": round(
                        safe_float(
                            impeller.get(
                                "impeller_diameter_m"
                            )
                        ),
                        3,
                    ),

                    "Bottom Clearance (m)": (
                        round(
                            safe_float(
                                clearance_value
                            ),
                            3,
                        )
                        if clearance_value is not None
                        else "—"
                    ),

                    "Elevation from Bottom (m)": round(
                        safe_float(
                            impeller.get(
                                "elevation_from_bottom_m"
                            )
                        ),
                        3,
                    ),

                    "RPM": impeller.get(
                        "rpm",
                        reactor.get(
                            "rpm"
                        ),
                    ),
                }
            )

        arrangement_df = pd.DataFrame(
            rows
        )

        display_dataframe(
            arrangement_df,
            hide_index=True,
        )


# ============================================================
# GAS-LIQUID TAB
# ============================================================

with result_tabs[2]:

    st.subheader(
        "Gas-Liquid Engineering"
    )

    if process_type not in [
        "Gas-Liquid",
        "Gas-Liquid-Solid",
    ]:

        st.info(
            "Gas-liquid calculations are not active "
            "for the selected process type."
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

                        "Value": reactor.get(
                            key
                        ),

                        "Unit": unit,
                    }
                )

        gas_df = pd.DataFrame(
            gas_rows
        )

        display_dataframe(
            gas_df,
            hide_index=True,
        )


# ============================================================
# SCALE-UP TAB
# ============================================================

with result_tabs[3]:

    st.subheader(
        "Reactor Scale-Up Analysis"
    )

    if scale_result is None:

        st.info(
            "Scale-up requires at least two reactors."
        )

    elif isinstance(
        scale_result,
        dict,
    ):

        scale_rows = []

        for key, value in scale_result.items():

            if isinstance(
                value,
                (dict, list, tuple),
            ):
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

            display_dataframe(
                scale_df,
                hide_index=True,
            )

        else:

            st.json(
                scale_result
            )

    else:

        st.write(
            scale_result
        )


# ============================================================
# VALIDATION TAB
# ============================================================

with result_tabs[4]:

    st.subheader(
        "Engineering Validation"
    )

    validation_rows = []

    for reactor in reactors:

        reactor_name = reactor.get(
            "name",
            "Reactor",
        )

        # ----------------------------------------------------
        # Geometry errors
        # ----------------------------------------------------

        geometry_errors = reactor.get(
            "impeller_geometry_errors",
            [],
        )

        geometry_warnings = reactor.get(
            "impeller_geometry_warnings",
            [],
        )

        if not isinstance(
            geometry_errors,
            (list, tuple),
        ):

            geometry_errors = [
                str(geometry_errors)
            ]

        if not isinstance(
            geometry_warnings,
            (list, tuple),
        ):

            geometry_warnings = [
                str(geometry_warnings)
            ]

        for error in geometry_errors:

            validation_rows.append(
                {
                    "Reactor": reactor_name,

                    "Check": "Impeller Geometry",

                    "Result": str(error),

                    "Status": "🔴",
                }
            )

        for warning in geometry_warnings:

            validation_rows.append(
                {
                    "Reactor": reactor_name,

                    "Check": "Impeller Geometry",

                    "Result": str(warning),

                    "Status": "🟠",
                }
            )

        # ----------------------------------------------------
        # Engine validation
        # ----------------------------------------------------

        validation = reactor.get(
            "validation"
        )

        if isinstance(
            validation,
            dict,
        ):

            for key, value in validation.items():

                if isinstance(
                    value,
                    (dict, list, tuple),
                ):

                    continue

                text_value = str(value)

                status = ""

                upper_value = (
                    text_value.upper()
                )

                if upper_value in [
                    "PASS",
                    "FAIL",
                    "WARNING",
                    "WARN",
                ]:

                    status = status_icon(
                        upper_value
                    )

                validation_rows.append(
                    {
                        "Reactor": reactor_name,

                        "Check": str(key),

                        "Result": text_value,

                        "Status": status,
                    }
                )

        elif isinstance(
            validation,
            (list, tuple),
        ):

            for index, value in enumerate(
                validation,
                start=1,
            ):

                if isinstance(
                    value,
                    (dict, list, tuple),
                ):

                    value = str(value)

                validation_rows.append(
                    {
                        "Reactor": reactor_name,

                        "Check": (
                            f"Validation {index}"
                        ),

                        "Result": str(value),

                        "Status": "",
                    }
                )

        elif validation is not None:

            validation_rows.append(
                {
                    "Reactor": reactor_name,

                    "Check": "Validation",

                    "Result": str(validation),

                    "Status": "",
                }
            )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    if validation_rows:

        validation_df = pd.DataFrame(
            validation_rows
        )

        # Explicitly guarantee that Result is text.
        if "Result" in validation_df.columns:

            validation_df[
                "Result"
            ] = (
                validation_df[
                    "Result"
                ]
                .fillna("")
                .astype(str)
            )

        display_dataframe(
            validation_df,
            hide_index=True,
        )

    else:

        st.info(
            "No validation results returned."
        )


# ============================================================
# 3D REACTOR TAB
# ============================================================

with result_tabs[5]:

    st.subheader(
        "🧊 3D Reactor Visualization"
    )

    st.caption(
        "The 3D model uses the individual impeller "
        "configuration, calculated elevations, reactor "
        "geometry, RPM and baffle configuration."
    )

    reactor_names_for_3d = [
        reactor.get(
            "name",
            "Reactor",
        )
        for reactor in reactors
    ]

    if reactor_names_for_3d:

        selected_3d_name = st.selectbox(
            "Select reactor",
            reactor_names_for_3d,
            key="selected_3d_reactor",
        )

        selected_3d = next(
            (
                reactor
                for reactor in reactors
                if reactor.get(
                    "name",
                    "Reactor",
                )
                == selected_3d_name
            ),
            reactors[-1],
        )

        try:

            # =================================================
            # NEW MULTI-IMPELLER INTERFACE
            # =================================================

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
                        [],
                    ),

                    rpm=selected_3d.get(
                        "rpm"
                    ),

                    number_baffles=selected_3d.get(
                        "number_baffles",
                        4,
                    ),

                    frames_count=36,

                    show_dimensions=True,

                    show_nozzles=True,

                    show_tracers=True,

                    vessel_opacity=0.24,

                    show_baffles=True,
                )

            except TypeError:

                # =================================================
                # LEGACY 3D INTERFACE
                # =================================================

                configured_impellers = (
                    selected_3d.get(
                        "impellers",
                        [],
                    )
                )

                if configured_impellers:

                    primary_impeller = (
                        configured_impellers[0]
                    )

                else:

                    primary_impeller = {}

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

                    agitator=primary_impeller.get(
                        "agitator_type"
                    ),

                    impeller_diameter=primary_impeller.get(
                        "impeller_diameter_m"
                    ),

                    number_impellers=selected_3d.get(
                        "number_impellers",
                        1,
                    ),

                    rpm=selected_3d.get(
                        "rpm"
                    ),

                    number_baffles=selected_3d.get(
                        "number_baffles",
                        4,
                    ),

                    frames_count=36,
                )

            # -------------------------------------------------
            # Plotly chart
            # -------------------------------------------------

            st.plotly_chart(
                fig,
                width="stretch",
            )

        except Exception as exc:

            st.error(
                "Unable to generate 3D reactor visualization."
            )

            st.exception(exc)


# ============================================================
# REPORTS TAB
# ============================================================

with result_tabs[6]:

    st.subheader(
        "📑 Engineering Reports"
    )

    st.write(
        "Generate Word and Excel engineering reports "
        "from the calculated reactor results."
    )

    report_col1, report_col2 = (
        st.columns(2)
    )

    # ========================================================
    # WORD REPORT
    # ========================================================

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

                word_data = (
                    word_file.getvalue()
                )

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

                width="stretch",
            )

        except Exception as exc:

            st.error(
                "Word report generation failed."
            )

            st.exception(exc)

    # ========================================================
    # EXCEL REPORT
    # ========================================================

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

                excel_data = (
                    excel_file.getvalue()
                )

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

                width="stretch",
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
