import math
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up & Mixing Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# IMPORTS
# ============================================================

try:
    from calculations.engine import calculate_reactor
except Exception as e:
    st.error(f"Unable to load calculations/engine.py: {e}")
    st.stop()


try:
    from libraries.agitator_geometry import AGITATORS
except Exception as e:
    st.error(f"Unable to load libraries/agitator_geometry.py: {e}")
    st.stop()


try:
    from visualization.reactor_3d import create_reactor_animation
except Exception as e:
    st.error(f"Unable to load visualization/reactor_3d.py: {e}")
    st.stop()


# Optional modules
try:
    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )
except Exception:

    REACTOR_HEADS = {
        "Flat": {},
        "2:1 Ellipsoidal": {},
        "Torispherical": {},
    }

    def calculate_total_volume(
        diameter_m,
        straight_height_m,
        bottom_type=None,
        top_type=None,
    ):
        """
        Fallback vessel volume calculation.
        """

        D = float(diameter_m)
        H = float(straight_height_m)

        cylindrical_volume = (
            math.pi / 4.0 * D**2 * H
        )

        # Approximate heads
        head_volume = 0.0

        if bottom_type and "ellipsoidal" in str(bottom_type).lower():
            head_volume += math.pi * D**3 / 24.0

        if top_type and "ellipsoidal" in str(top_type).lower():
            head_volume += math.pi * D**3 / 24.0

        return cylindrical_volume + head_volume

    def liquid_height_from_volume(
        volume_m3,
        diameter_m,
        straight_height_m,
        bottom_type=None,
        top_type=None,
    ):
        """
        Fallback approximation.
        """

        D = float(diameter_m)
        H = float(straight_height_m)
        V = float(volume_m3)

        area = math.pi * D**2 / 4.0

        if area <= 0:
            return 0.0

        return min(H, max(0.0, V / area))


try:
    from calculations.scaleup import calculate_scaleup
except Exception:
    calculate_scaleup = None


try:
    from calculations.validation import validate_reactor
except Exception:
    validate_reactor = None


try:
    from reporting.report_generator import (
        create_word_report,
        create_excel_report,
    )
except Exception:
    create_word_report = None
    create_excel_report = None


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.1rem;
    }

    .subtitle {
        color: #666666;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 650;
        margin-top: 0.8rem;
        margin-bottom: 0.5rem;
    }

    .metric-card {
        border: 1px solid #DDDDDD;
        border-radius: 10px;
        padding: 12px;
        background: #FAFAFA;
        margin-bottom: 8px;
    }

    .status-ok {
        color: #17823B;
        font-weight: 700;
    }

    .status-warning {
        color: #B26A00;
        font-weight: 700;
    }

    .status-error {
        color: #B42318;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.strip()

        return float(value)

    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fmt(value, digits=3):
    if value is None:
        return "—"

    try:
        value = float(value)

        if not math.isfinite(value):
            return "—"

        return f"{value:,.{digits}f}"

    except (TypeError, ValueError):
        return str(value)


def safe_dataframe(df):
    """
    Prevent Streamlit/PyArrow errors caused by mixed
    object columns.
    """

    if df is None:
        return pd.DataFrame()

    out = df.copy()

    for col in out.columns:

        if str(out[col].dtype) == "object":
            out[col] = out[col].astype("string")

    return out


def get_value(data, *keys, default=None):

    for key in keys:

        if isinstance(data, dict) and key in data:

            value = data[key]

            if value is not None:
                return value

    return default


# ============================================================
# AGITATOR HELPERS
# ============================================================

def get_agitator_names():

    if not isinstance(AGITATORS, dict):
        return []

    return list(AGITATORS.keys())


def get_agitator_data(name):

    if not isinstance(AGITATORS, dict):
        return {}

    data = AGITATORS.get(name, {})

    if isinstance(data, dict):
        return data

    return {}


def get_agitator_np(name):

    data = get_agitator_data(name)

    value = data.get("np")

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_agitator_nq(name):

    data = get_agitator_data(name)

    value = data.get("nq")

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# IMPeller ELEVATION
# ============================================================

POSITION_OPTIONS = [
    "Bottom",
    "Middle",
    "Top",
]


def calculate_impeller_elevations(
    impellers,
    liquid_height_m,
    tank_diameter_m,
):
    """
    Converts user selected positions into actual elevations
    from vessel bottom.

    Bottom:
        user-defined clearance

    Middle:
        approximately 50% of liquid height

    Top:
        approximately 75% of liquid height
    """

    if not impellers:
        return []

    result = []

    H = max(
        safe_float(liquid_height_m, 0.0),
        0.0,
    )

    T = max(
        safe_float(tank_diameter_m, 0.0),
        0.0,
    )

    for item in impellers:

        data = dict(item)

        position = str(
            data.get("position", "Bottom")
        )

        clearance = safe_float(
            data.get("bottom_clearance_m"),
            0.20 * T if T > 0 else 0.3,
        )

        if position == "Bottom":

            elevation = clearance

        elif position == "Middle":

            elevation = max(
                clearance,
                0.50 * H,
            )

        elif position == "Top":

            elevation = max(
                clearance,
                0.75 * H,
            )

        else:

            elevation = clearance

        elevation = min(
            elevation,
            max(H - 0.05, 0.05),
        )

        data["elevation_m"] = elevation

        # Alias for 3D module
        data["bottom_clearance_m"] = clearance

        result.append(data)

    # Sort from bottom to top
    result.sort(
        key=lambda x: safe_float(
            x.get("elevation_m"),
            0.0,
        )
    )

    return result


# ============================================================
# VALIDATE IMPELLER ARRANGEMENT
# ============================================================

def validate_impeller_configuration(
    impellers,
    liquid_height_m,
    tank_diameter_m,
):

    messages = []

    if not impellers:

        messages.append(
            (
                "ERROR",
                "At least one impeller is required.",
            )
        )

        return messages

    elevations = []

    for i, imp in enumerate(impellers, 1):

        D = safe_float(
            imp.get("diameter_m"),
            0.0,
        )

        elevation = safe_float(
            imp.get("elevation_m"),
            0.0,
        )

        clearance = safe_float(
            imp.get("bottom_clearance_m"),
            0.0,
        )

        if D <= 0:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: diameter must be > 0.",
                )
            )

        if elevation < 0:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: elevation cannot be negative.",
                )
            )

        if clearance < 0:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: clearance cannot be negative.",
                )
            )

        elevations.append(elevation)

    # Duplicate elevation check
    rounded = [
        round(x, 4)
        for x in elevations
    ]

    if len(rounded) != len(set(rounded)):

        messages.append(
            (
                "WARNING",
                "Two or more impellers have the same elevation.",
            )
        )

    H = safe_float(
        liquid_height_m,
        0.0,
    )

    for i, elevation in enumerate(elevations, 1):

        if H > 0 and elevation >= H:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: elevation is above liquid level.",
                )
            )

    if not messages:

        messages.append(
            (
                "OK",
                "Impeller arrangement is internally consistent.",
            )
        )

    return messages


# ============================================================
# REACTOR INPUT PANEL
# ============================================================

def reactor_input_panel():

    st.markdown(
        '<div class="section-title">1. Reactor & Process Inputs</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        working_volume = st.number_input(
            "Working Volume (m³)",
            min_value=0.01,
            value=10.0,
            step=0.5,
        )

        density = st.number_input(
            "Liquid Density (kg/m³)",
            min_value=0.1,
            value=1000.0,
            step=10.0,
        )

        viscosity_cp = st.number_input(
            "Viscosity (cP)",
            min_value=0.001,
            value=1.0,
            step=0.1,
        )

    with col2:

        tank_diameter = st.number_input(
            "Tank ID (m)",
            min_value=0.1,
            value=2.0,
            step=0.05,
        )

        straight_height = st.number_input(
            "Straight Side Height (m)",
            min_value=0.1,
            value=3.0,
            step=0.1,
        )

        surface_tension = st.number_input(
            "Surface Tension (mN/m)",
            min_value=0.1,
            value=30.0,
            step=1.0,
        )

    with col3:

        rpm = st.number_input(
            "Agitator Speed (RPM)",
            min_value=0.1,
            value=100.0,
            step=5.0,
        )

        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=3,
            value=1,
            step=1,
        )

        number_baffles = st.number_input(
            "Number of Baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
        )

    st.markdown(
        '<div class="section-title">2. Vessel Geometry</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    head_names = list(REACTOR_HEADS.keys())

    if not head_names:
        head_names = [
            "Flat",
            "2:1 Ellipsoidal",
            "Torispherical",
        ]

    with col1:

        bottom_type = st.selectbox(
            "Bottom Head",
            head_names,
            index=(
                head_names.index("2:1 Ellipsoidal")
                if "2:1 Ellipsoidal" in head_names
                else 0
            ),
        )

    with col2:

        top_type = st.selectbox(
            "Top Head",
            head_names,
            index=(
                head_names.index("2:1 Ellipsoidal")
                if "2:1 Ellipsoidal" in head_names
                else 0
            ),
        )

    with col3:

        calculate_geometry = st.checkbox(
            "Calculate vessel geometry",
            value=True,
        )

    # --------------------------------------------------------
    # VESSEL VOLUME
    # --------------------------------------------------------

    vessel_volume = None

    if calculate_geometry:

        try:

            vessel_volume = calculate_total_volume(
                diameter_m=tank_diameter,
                straight_height_m=straight_height,
                bottom_type=bottom_type,
                top_type=top_type,
            )

        except Exception:

            try:

                vessel_volume = calculate_total_volume(
                    tank_diameter,
                    straight_height,
                    bottom_type,
                    top_type,
                )

            except Exception:

                vessel_volume = (
                    math.pi
                    / 4.0
                    * tank_diameter**2
                    * straight_height
                )

    if vessel_volume:

        st.info(
            f"Estimated vessel volume: "
            f"**{fmt(vessel_volume, 2)} m³**"
        )

    # --------------------------------------------------------
    # LIQUID HEIGHT
    # --------------------------------------------------------

    try:

        liquid_height = liquid_height_from_volume(
            volume_m3=working_volume,
            diameter_m=tank_diameter,
            straight_height_m=straight_height,
            bottom_type=bottom_type,
            top_type=top_type,
        )

    except Exception:

        liquid_height = min(
            straight_height,
            working_volume
            / (
                math.pi
                / 4.0
                * tank_diameter**2
            ),
        )

    liquid_height = max(
        0.05,
        safe_float(
            liquid_height,
            straight_height * 0.7,
        ),
    )

    st.info(
        f"Calculated liquid height: "
        f"**{fmt(liquid_height, 2)} m**"
    )

    # ========================================================
    # AGITATION
    # ========================================================

    st.markdown(
        '<div class="section-title">3. Multi-Impeller Agitation</div>',
        unsafe_allow_html=True,
    )

    agitator_names = get_agitator_names()

    if not agitator_names:

        st.error(
            "No agitators found in AGITATORS database."
        )

        st.stop()

    impellers = []

    for i in range(int(number_impellers)):

        st.markdown(
            f"**Impeller {i + 1}**"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            position = st.selectbox(
                "Position",
                POSITION_OPTIONS,
                index=min(i, 2),
                key=f"position_{i}",
            )

        with c2:

            agitator = st.selectbox(
                "Agitator Type",
                agitator_names,
                key=f"agitator_{i}",
            )

        with c3:

            default_D = 0.5 * tank_diameter

            D = st.number_input(
                "Impeller Diameter (m)",
                min_value=0.01,
                value=float(
                    max(0.05, default_D)
                ),
                step=0.05,
                key=f"impeller_diameter_{i}",
            )

        with c4:

            clearance_default = (
                0.20 * tank_diameter
            )

            clearance = st.number_input(
                "Bottom Clearance (m)",
                min_value=0.0,
                value=float(
                    max(
                        0.05,
                        clearance_default,
                    )
                ),
                step=0.05,
                key=f"clearance_{i}",
            )

        impellers.append(
            {
                "position": position,
                "agitator_type": agitator,
                "type": agitator,
                "diameter_m": D,
                "D": D,
                "bottom_clearance_m": clearance,
            }
        )

    # --------------------------------------------------------
    # ACTUAL ELEVATIONS
    # --------------------------------------------------------

    impellers = calculate_impeller_elevations(
        impellers,
        liquid_height,
        tank_diameter,
    )

    arrangement_messages = validate_impeller_configuration(
        impellers,
        liquid_height,
        tank_diameter,
    )

    for level, message in arrangement_messages:

        if level == "ERROR":
            st.error(message)

        elif level == "WARNING":
            st.warning(message)

        else:
            st.success(message)

    # --------------------------------------------------------
    # GAS LIQUID
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">4. Gas–Liquid Inputs</div>',
        unsafe_allow_html=True,
    )

    gas_active = st.checkbox(
        "Enable Gas–Liquid Calculation",
        value=False,
    )

    if gas_active:

        c1, c2, c3 = st.columns(3)

        with c1:

            gas_flow = st.number_input(
                "Gas Flow (m³/h)",
                min_value=0.001,
                value=10.0,
                step=1.0,
            )

        with c2:

            bubble_diameter = st.number_input(
                "Bubble Diameter (mm)",
                min_value=0.1,
                value=3.0,
                step=0.5,
            )

        with c3:

            gas_holdup = st.number_input(
                "Gas Holdup Fraction",
                min_value=0.001,
                max_value=0.50,
                value=0.05,
                step=0.01,
            )

    else:

        gas_flow = 0.0
        bubble_diameter = 3.0
        gas_holdup = 0.05

    # ========================================================
    # RETURN INPUTS
    # ========================================================

    return {
        "working_volume_m3": working_volume,
        "volume_m3": working_volume,
        "tank_diameter_m": tank_diameter,
        "diameter_m": tank_diameter,
        "straight_height_m": straight_height,
        "liquid_height_m": liquid_height,
        "density_kg_m3": density,
        "viscosity_cp": viscosity_cp,
        "viscosity_pa_s": viscosity_cp * 0.001,
        "surface_tension_mN_m": surface_tension,
        "surface_tension_n_m": surface_tension * 0.001,
        "rpm": rpm,
        "number_impellers": int(number_impellers),
        "number_baffles": int(number_baffles),
        "bottom_type": bottom_type,
        "top_type": top_type,
        "vessel_volume_m3": vessel_volume,
        "impellers": impellers,
        "agitator": impellers[0]["agitator_type"],
        "impeller_diameter_m": impellers[0]["diameter_m"],
        "impeller_clearance_m": impellers[0]["bottom_clearance_m"],
        "gas_flow_m3_h": gas_flow,
        "bubble_diameter_mm": bubble_diameter,
        "gas_holdup_fraction": gas_holdup,
    }


# ============================================================
# CALCULATION ADAPTER
# ============================================================

def calculate_reactor_case(inputs):

    volume_m3 = safe_float(
        inputs.get("working_volume_m3"),
        0.0,
    )

    tank_diameter_m = safe_float(
        inputs.get("tank_diameter_m"),
        0.0,
    )

    liquid_height_m = safe_float(
        inputs.get("liquid_height_m"),
        0.0,
    )

    density_kg_m3 = safe_float(
        inputs.get("density_kg_m3"),
        1000.0,
    )

    viscosity_pa_s = safe_float(
        inputs.get("viscosity_pa_s"),
        0.001,
    )

    surface_tension_n_m = safe_float(
        inputs.get("surface_tension_n_m"),
        0.03,
    )

    rpm = safe_float(
        inputs.get("rpm"),
        100.0,
    )

    impellers = inputs.get(
        "impellers",
        [],
    )

    if not impellers:

        raise ValueError(
            "No impeller configuration found."
        )

    primary_impeller = impellers[0]

    agitator = primary_impeller.get(
        "agitator_type",
        primary_impeller.get(
            "type"
        ),
    )

    if not agitator:

        raise ValueError(
            "Agitator type is not defined."
        )

    impeller_diameter_m = safe_float(
        primary_impeller.get(
            "diameter_m",
            primary_impeller.get("D"),
        ),
        0.0,
    )

    number_impellers = safe_int(
        inputs.get(
            "number_impellers",
            len(impellers),
        ),
        len(impellers),
    )

    clearance = primary_impeller.get(
        "bottom_clearance_m"
    )

    if clearance is None:

        clearance = inputs.get(
            "impeller_clearance_m"
        )

    clearance = safe_float(
        clearance,
        0.20 * tank_diameter_m,
    )

    if volume_m3 <= 0:
        raise ValueError(
            "Working volume must be greater than zero."
        )

    if tank_diameter_m <= 0:
        raise ValueError(
            "Tank diameter must be greater than zero."
        )

    if liquid_height_m <= 0:
        raise ValueError(
            "Liquid height must be greater than zero."
        )

    if density_kg_m3 <= 0:
        raise ValueError(
            "Density must be greater than zero."
        )

    if viscosity_pa_s <= 0:
        raise ValueError(
            "Viscosity must be greater than zero."
        )

    if rpm <= 0:
        raise ValueError(
            "RPM must be greater than zero."
        )

    if impeller_diameter_m <= 0:
        raise ValueError(
            "Impeller diameter must be greater than zero."
        )

    # --------------------------------------------------------
    # CALL ENGINE
    # --------------------------------------------------------

    result = calculate_reactor(

        volume_m3=volume_m3,

        tank_diameter_m=tank_diameter_m,

        liquid_height_m=liquid_height_m,

        density_kg_m3=density_kg_m3,

        viscosity_pa_s=viscosity_pa_s,

        surface_tension_n_m=surface_tension_n_m,

        rpm=rpm,

        impeller_diameter_m=impeller_diameter_m,

        number_impellers=number_impellers,

        agitator=agitator,

        impeller_clearance_m=clearance,

        gas_flow_m3_h=safe_float(
            inputs.get(
                "gas_flow_m3_h"
            ),
            0.0,
        ),

        bubble_diameter_mm=safe_float(
            inputs.get(
                "bubble_diameter_mm"
            ),
            3.0,
        ),

        gas_holdup_fraction=safe_float(
            inputs.get(
                "gas_holdup_fraction"
            ),
            0.05,
        ),
    )

    # --------------------------------------------------------
    # ADD UI / GEOMETRY DATA
    # --------------------------------------------------------

    result["straight_height_m"] = safe_float(
        inputs.get("straight_height_m"),
        0.0,
    )

    result["bottom_type"] = inputs.get(
        "bottom_type"
    )

    result["top_type"] = inputs.get(
        "top_type"
    )

    result["number_baffles"] = safe_int(
        inputs.get("number_baffles"),
        4,
    )

    result["impellers"] = impellers

    result["vessel_volume_m3"] = inputs.get(
        "vessel_volume_m3"
    )

    return result


# ============================================================
# PERFORMANCE TAB
# ============================================================

def show_performance(result):

    st.subheader("Reactor Mixing Performance")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Reynolds Number",
            fmt(
                result.get("Re"),
                0,
            ),
        )

    with c2:
        st.metric(
            "Tip Speed",
            f"{fmt(result.get('tip_speed'), 2)} m/s",
        )

    with c3:
        st.metric(
            "Power",
            f"{fmt(result.get('power_kw'), 2)} kW",
        )

    with c4:
        st.metric(
            "Specific Power",
            f"{fmt(result.get('power_volume_kw_m3'), 3)} kW/m³",
        )

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Pumping Capacity",
            f"{fmt(result.get('pumping_m3_h'), 2)} m³/h",
        )

    with c2:

        st.metric(
            "Turnover Time",
            f"{fmt(result.get('turnover_time_min'), 2)} min",
        )

    with c3:

        st.metric(
            "Torque",
            f"{fmt(result.get('torque_nm'), 1)} N·m",
        )

    with c4:

        st.metric(
            "Mixing Regime",
            str(
                result.get(
                    "mixing_regime",
                    "—",
                )
            ),
        )

    st.subheader("Engineering Parameters")

    performance_data = {

        "Parameter": [
            "Working Volume",
            "Tank Diameter",
            "Liquid Height",
            "D/T",
            "H/T",
            "RPM",
            "Impeller Diameter",
            "Impeller Count",
            "Reynolds Number",
            "Froude Number",
            "Tip Speed",
            "Power",
            "Power / Volume",
            "Torque",
            "Pumping Capacity",
            "Pumping / Volume",
            "Turnover Time",
            "Mixing Regime",
        ],

        "Value": [

            fmt(result.get("volume_m3"), 3),

            fmt(
                result.get("tank_diameter_m"),
                3,
            ),

            fmt(
                result.get("liquid_height_m"),
                3,
            ),

            fmt(result.get("D_T"), 3),

            fmt(result.get("H_T"), 3),

            fmt(result.get("rpm"), 1),

            fmt(
                result.get("impeller_diameter_m"),
                3,
            ),

            result.get(
                "number_impellers",
                "—",
            ),

            fmt(
                result.get("reynolds_number"),
                0,
            ),

            fmt(
                result.get("froude_number"),
                4,
            ),

            f"{fmt(result.get('tip_speed'), 3)} m/s",

            f"{fmt(result.get('power_kw'), 3)} kW",

            f"{fmt(result.get('power_volume_kw_m3'), 4)} kW/m³",

            f"{fmt(result.get('torque_nm'), 2)} N·m",

            f"{fmt(result.get('pumping_m3_h'), 2)} m³/h",

            f"{fmt(result.get('pumping_per_volume'), 3)} 1/h",

            f"{fmt(result.get('turnover_time_min'), 2)} min",

            result.get(
                "mixing_regime",
                "—",
            ),
        ],
    }

    df = safe_dataframe(
        pd.DataFrame(performance_data)
    )

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# IMPELLER TAB
# ============================================================

def show_impellers(result):

    st.subheader("Impeller Arrangement")

    impellers = result.get(
        "impellers",
        [],
    )

    if not impellers:

        st.warning(
            "No impeller data available."
        )

        return

    rows = []

    for i, imp in enumerate(
        impellers,
        1,
    ):

        agitator = imp.get(
            "agitator_type",
            "Unknown",
        )

        D = safe_float(
            imp.get("diameter_m"),
            0.0,
        )

        elevation = safe_float(
            imp.get("elevation_m"),
            0.0,
        )

        np_value = get_agitator_np(
            agitator
        )

        nq_value = get_agitator_nq(
            agitator
        )

        rows.append(
            {
                "Impeller": i,
                "Position": imp.get(
                    "position"
                ),
                "Agitator": agitator,
                "Diameter (m)": D,
                "D/T": (
                    D
                    / result["tank_diameter_m"]
                    if result["tank_diameter_m"] > 0
                    else None
                ),
                "Elevation from Bottom (m)": elevation,
                "Bottom Clearance (m)": safe_float(
                    imp.get(
                        "bottom_clearance_m"
                    ),
                    0.0,
                ),
                "Np": np_value,
                "Nq": nq_value,
            }
        )

    df = safe_dataframe(
        pd.DataFrame(rows)
    )

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )

    st.subheader(
        "Impeller Elevation Profile"
    )

    chart_df = pd.DataFrame(
        {
            "Impeller": [
                f"I-{i + 1}"
                for i in range(
                    len(impellers)
                )
            ],
            "Elevation": [
                safe_float(
                    imp.get(
                        "elevation_m"
                    ),
                    0.0,
                )
                for imp in impellers
            ],
        }
    )

    st.bar_chart(
        chart_df.set_index(
            "Impeller"
        )
    )


# ============================================================
# GAS-LIQUID TAB
# ============================================================

def show_gas_liquid(result):

    st.subheader(
        "Gas–Liquid Mass Transfer"
    )

    status = result.get(
        "gas_liquid_status",
        "NOT ACTIVE",
    )

    if status == "NOT ACTIVE":

        st.info(
            "Gas–liquid calculation is not active."
        )

        return

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Gas Flow",
            f"{fmt(result.get('gas_flow_m3_h'), 2)} m³/h",
        )

    with c2:

        st.metric(
            "Superficial Velocity",
            f"{fmt(result.get('gas_superficial_velocity_m_s'), 4)} m/s",
        )

    with c3:

        st.metric(
            "Bubble Diameter",
            f"{fmt(result.get('bubble_diameter_m'), 4)} m",
        )

    with c4:

        st.metric(
            "Gas Holdup",
            f"{fmt(result.get('gas_holdup_fraction'), 3)}",
        )

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Bubble Velocity",
            f"{fmt(result.get('bubble_rise_velocity_m_s'), 4)} m/s",
        )

    with c2:

        st.metric(
            "Residence Time",
            f"{fmt(result.get('bubble_residence_time_s'), 1)} s",
        )

    with c3:

        st.metric(
            "Bubble Reynolds",
            fmt(
                result.get(
                    "bubble_reynolds"
                ),
                1,
            ),
        )

    with c4:

        st.metric(
            "Schmidt Number",
            fmt(
                result.get(
                    "schmidt_number"
                ),
                1,
            ),
        )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Sherwood Number",
            fmt(
                result.get(
                    "sherwood_number"
                ),
                1,
            ),
        )

    with c2:

        st.metric(
            "kL",
            f"{fmt(result.get('kL_m_s'), 6)} m/s",
        )

    with c3:

        st.metric(
            "Interfacial Area",
            f"{fmt(result.get('interfacial_area_m2_m3'), 2)} m²/m³",
        )

    with c4:

        st.metric(
            "kLa",
            f"{fmt(result.get('kLa_1_h'), 2)} h⁻¹",
        )

    st.warning(
        "Gas–liquid values are screening-level estimates. "
        "Final kLa and mass-transfer design should use "
        "validated correlations and/or experimental data."
    )


# ============================================================
# VALIDATION TAB
# ============================================================

def show_validation(result):

    st.subheader(
        "Engineering Validation"
    )

    checks = []

    T = safe_float(
        result.get("tank_diameter_m"),
        0.0,
    )

    D = safe_float(
        result.get("impeller_diameter_m"),
        0.0,
    )

    H = safe_float(
        result.get("liquid_height_m"),
        0.0,
    )

    rpm = safe_float(
        result.get("rpm"),
        0.0,
    )

    # D/T
    D_T = (
        D / T
        if T > 0
        else 0
    )

    if 0.25 <= D_T <= 0.70:

        checks.append(
            {
                "Check": "Impeller D/T",
                "Result": "PASS",
                "Value": f"{D_T:.3f}",
                "Comment": "Within common preliminary range.",
            }
        )

    else:

        checks.append(
            {
                "Check": "Impeller D/T",
                "Result": "REVIEW",
                "Value": f"{D_T:.3f}",
                "Comment": "Review impeller diameter selection.",
            }
        )

    # H/T
    H_T = (
        H / T
        if T > 0
        else 0
    )

    checks.append(
        {
            "Check": "Liquid H/T",
            "Result": (
                "PASS"
                if H_T > 0
                else "ERROR"
            ),
            "Value": f"{H_T:.3f}",
            "Comment": "Check vessel aspect ratio.",
        }
    )

    # RPM
    checks.append(
        {
            "Check": "Agitator RPM",
            "Result": (
                "PASS"
                if rpm > 0
                else "ERROR"
            ),
            "Value": f"{rpm:.1f}",
            "Comment": "Operating speed entered.",
        }
    )

    # Power
    power = result.get(
        "power_kw"
    )

    checks.append(
        {
            "Check": "Power Calculation",
            "Result": (
                "PASS"
                if power is not None
                else "REVIEW"
            ),
            "Value": (
                f"{power:.3f} kW"
                if power is not None
                else "N/A"
            ),
            "Comment": "Requires valid Np in agitator database.",
        }
    )

    df = safe_dataframe(
        pd.DataFrame(checks)
    )

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )

    if validate_reactor is not None:

        try:

            validation_result = validate_reactor(
                result
            )

            st.subheader(
                "Validation Module Output"
            )

            if isinstance(
                validation_result,
                pd.DataFrame,
            ):

                st.dataframe(
                    safe_dataframe(
                        validation_result
                    ),
                    width="stretch",
                    hide_index=True,
                )

            elif isinstance(
                validation_result,
                dict,
            ):

                rows = []

                for key, value in validation_result.items():

                    rows.append(
                        {
                            "Parameter": key,
                            "Result": str(value),
                        }
                    )

                st.dataframe(
                    safe_dataframe(
                        pd.DataFrame(rows)
                    ),
                    width="stretch",
                    hide_index=True,
                )

            else:

                st.write(
                    validation_result
                )

        except Exception as e:

            st.warning(
                f"Validation module could not be executed: "
                f"{type(e).__name__}: {e}"
            )


# ============================================================
# SCALE-UP TAB
# ============================================================

def show_scaleup(result):

    st.subheader(
        "Reactor Scale-Up"
    )

    st.info(
        "Use the scale-up module for comparing "
        "geometrically similar systems and maintaining "
        "selected mixing criteria."
    )

    if calculate_scaleup is None:

        st.warning(
            "calculations/scaleup.py is not available."
        )

        return

    c1, c2, c3 = st.columns(3)

    with c1:

        reference_volume = st.number_input(
            "Reference Volume (m³)",
            min_value=0.01,
            value=1.0,
            step=0.1,
            key="scale_reference_volume",
        )

    with c2:

        target_volume = st.number_input(
            "Target Volume (m³)",
            min_value=0.01,
            value=float(
                result.get(
                    "volume_m3",
                    10.0,
                )
            ),
            step=0.5,
            key="scale_target_volume",
        )

    with c3:

        basis = st.selectbox(
            "Scale-Up Basis",
            [
                "Constant P/V",
                "Constant Tip Speed",
                "Constant RPM",
            ],
        )

    try:

        output = calculate_scaleup(
            reference_volume,
            target_volume,
            basis,
        )

    except TypeError:

        try:

            output = calculate_scaleup(
                reference_volume=reference_volume,
                target_volume=target_volume,
                basis=basis,
            )

        except Exception as e:

            st.warning(
                f"Scale-up module interface differs from dashboard: "
                f"{type(e).__name__}: {e}"
            )

            return

    except Exception as e:

        st.warning(
            f"Scale-up calculation failed: "
            f"{type(e).__name__}: {e}"
        )

        return

    if isinstance(output, dict):

        rows = [
            {
                "Parameter": key,
                "Value": str(value),
            }
            for key, value in output.items()
        ]

        st.dataframe(
            safe_dataframe(
                pd.DataFrame(rows)
            ),
            width="stretch",
            hide_index=True,
        )

    else:

        st.write(output)


# ============================================================
# 3D TAB
# ============================================================

def show_3d(result):

    st.subheader(
        "3D Reactor Visualization"
    )

    st.caption(
        "Interactive engineering visualization of the "
        "selected reactor geometry and agitator arrangement."
    )

    impellers = result.get(
        "impellers",
        [],
    )

    try:

        fig = create_reactor_animation(

            D=result.get(
                "tank_diameter_m"
            ),

            straight_height=result.get(
                "straight_height_m"
            ),

            bottom_type=result.get(
                "bottom_type"
            ),

            top_type=result.get(
                "top_type"
            ),

            liquid_height=result.get(
                "liquid_height_m"
            ),

            impellers=impellers,

            rpm=result.get(
                "rpm"
            ),

            number_baffles=result.get(
                "number_baffles",
                4,
            ),

            frames_count=36,

            show_dimensions=True,

            show_nozzles=True,

            show_tracers=True,

            show_baffles=True,

        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "displaylogo": False,
                "scrollZoom": True,
            },
        )

    except Exception as e:

        st.error(
            "3D reactor visualization failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# REPORT TAB
# ============================================================

def show_reports(inputs, result):

    st.subheader(
        "Engineering Reports"
    )

    st.write(
        "Generate a calculation report using the current reactor case."
    )

    c1, c2 = st.columns(2)

    with c1:

        if create_word_report is None:

            st.warning(
                "Word report module is unavailable."
            )

        else:

            try:

                word_file = create_word_report(
                    inputs,
                    result,
                )

                st.download_button(
                    label="Download Word Report",
                    data=word_file.getvalue(),
                    file_name="reactor_scaleup_report.docx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                    width="stretch",
                )

            except Exception as e:

                st.error(
                    f"Word report generation failed: "
                    f"{type(e).__name__}: {e}"
                )

    with c2:

        if create_excel_report is None:

            st.warning(
                "Excel report module is unavailable."
            )

        else:

            try:

                excel_file = create_excel_report(
                    inputs,
                    result,
                )

                st.download_button(
                    label="Download Excel Report",
                    data=excel_file.getvalue(),
                    file_name="reactor_scaleup_report.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    width="stretch",
                )

            except Exception as e:

                st.error(
                    f"Excel report generation failed: "
                    f"{type(e).__name__}: {e}"
                )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🏭 Reactor Scale-Up"
    )

    st.caption(
        "Process Engineering Dashboard"
    )

    st.divider()

    st.markdown(
        """
        **Calculation Scope**

        • Reactor geometry  
        • Mixing performance  
        • Multi-impeller system  
        • Gas–liquid transfer  
        • Scale-up  
        • Validation  
        • 3D visualization  
        • Engineering reports
        """
    )

    st.divider()

    st.caption(
        "Screening-level engineering tool. "
        "Final equipment design requires validated "
        "correlations, vendor data and mechanical checks."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🏭 Reactor Scale-Up & Mixing Dashboard</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Process engineering tool for reactor geometry, "
    "agitator selection, mixing calculations, scale-up "
    "and 3D visualization."
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# INPUT PANEL
# ============================================================

inputs = reactor_input_panel()


# ============================================================
# CALCULATE
# ============================================================

st.divider()

calculate_clicked = st.button(
    "▶ Calculate Reactor",
    type="primary",
    width="stretch",
)


# ============================================================
# EXECUTE
# ============================================================

if calculate_clicked:

    try:

        result = calculate_reactor_case(
            inputs
        )

        st.session_state["reactor_inputs"] = inputs
        st.session_state["reactor_result"] = result

        st.success(
            "Reactor calculation completed successfully."
        )

    except Exception as e:

        st.error(
            "❌ Reactor calculation failed."
        )

        st.error(
            f"{type(e).__name__}: {e}"
        )

        st.info(
            "Check the reactor dimensions, liquid properties, "
            "RPM, impeller diameter and agitator database."
        )

        st.stop()


# ============================================================
# DISPLAY RESULTS
# ============================================================

if (
    "reactor_result"
    not in st.session_state
):

    st.info(
        "Enter the reactor and agitator parameters above, "
        "then click **Calculate Reactor**."
    )

else:

    result = st.session_state[
        "reactor_result"
    ]

    inputs = st.session_state[
        "reactor_inputs"
    ]

    tabs = st.tabs(
        [
            "📊 Performance",
            "⚙️ Impeller Arrangement",
            "🫧 Gas–Liquid",
            "📐 Scale-Up",
            "✅ Validation",
            "🧊 3D Reactor",
            "📄 Reports",
        ]
    )

    with tabs[0]:

        show_performance(
            result
        )

    with tabs[1]:

        show_impellers(
            result
        )

    with tabs[2]:

        show_gas_liquid(
            result
        )

    with tabs[3]:

        show_scaleup(
            result
        )

    with tabs[4]:

        show_validation(
            result
        )

    with tabs[5]:

        show_3d(
            result
        )

    with tabs[6]:

        show_reports(
            inputs,
            result,
        )
