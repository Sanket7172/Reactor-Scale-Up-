import copy
import math
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# APPLICATION PATH
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
# ENGINEERING MODULES
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

    from reporting.report_generator import (
        create_word_report,
        create_excel_report,
    )

except Exception as e:

    st.error("Engineering module loading failed.")

    st.code(
        f"{type(e).__name__}: {e}"
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "reactor_inputs": None,
    "reactor_result": None,
    "calculation_complete": False,
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# MODERN ENGINEERING UI
# ============================================================

st.markdown(
    """
<style>

/* =========================================================
   GLOBAL
   ========================================================= */

.block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

[data-testid="stSidebar"] {
    border-right: 1px solid rgba(128,128,128,0.18);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

h1, h2, h3 {
    letter-spacing: -0.02em;
}

hr {
    margin: 1rem 0;
}


/* =========================================================
   HERO
   ========================================================= */

.hero {
    padding: 1.6rem 1.8rem;
    border-radius: 18px;
    margin-bottom: 1.2rem;
    background:
        linear-gradient(
            135deg,
            rgba(35, 45, 65, 0.95),
            rgba(18, 25, 40, 0.98)
        );
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 35px rgba(0,0,0,0.15);
}

.hero-kicker {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    opacity: 0.65;
    margin-bottom: 0.35rem;
}

.hero-title {
    font-size: 2.15rem;
    line-height: 1.1;
    font-weight: 800;
    margin: 0;
}

.hero-subtitle {
    font-size: 0.95rem;
    opacity: 0.72;
    margin-top: 0.55rem;
}


/* =========================================================
   ENGINEERING CARDS
   ========================================================= */

.engine-card {
    padding: 1rem 1.05rem;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,0.20);
    background: rgba(128,128,128,0.045);
    min-height: 95px;
}

.card-label {
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    opacity: 0.62;
}

.card-value {
    font-size: 1.45rem;
    font-weight: 750;
    margin-top: 0.22rem;
}

.card-unit {
    font-size: 0.75rem;
    opacity: 0.60;
}


/* =========================================================
   STATUS
   ========================================================= */

.status-ready {
    display: inline-block;
    padding: 0.32rem 0.75rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    background: rgba(40,167,69,0.15);
    border: 1px solid rgba(40,167,69,0.30);
}

.status-review {
    display: inline-block;
    padding: 0.32rem 0.75rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    background: rgba(255,193,7,0.15);
    border: 1px solid rgba(255,193,7,0.30);
}

.status-risk {
    display: inline-block;
    padding: 0.32rem 0.75rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    background: rgba(220,53,69,0.15);
    border: 1px solid rgba(220,53,69,0.30);
}


/* =========================================================
   SECTION HEADERS
   ========================================================= */

.section-kicker {
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0.55;
    margin-bottom: 0.1rem;
}

.section-title {
    font-size: 1.35rem;
    font-weight: 750;
    margin-bottom: 0.7rem;
}


/* =========================================================
   EMPTY STATE
   ========================================================= */

.empty-state {
    padding: 2.2rem;
    text-align: center;
    border: 1px dashed rgba(128,128,128,0.35);
    border-radius: 18px;
    margin-top: 1.5rem;
}

.empty-title {
    font-size: 1.35rem;
    font-weight: 750;
}

.empty-text {
    opacity: 0.65;
    max-width: 700px;
    margin: 0.5rem auto;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

.sidebar-brand {
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -0.01em;
}

.sidebar-caption {
    font-size: 0.72rem;
    opacity: 0.55;
    margin-top: -0.2rem;
}


/* =========================================================
   TABLE
   ========================================================= */

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}


/* =========================================================
   SMALL TEXT
   ========================================================= */

.engineering-note {
    font-size: 0.76rem;
    opacity: 0.58;
    line-height: 1.5;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def sf(value, default=0.0):

    try:

        if value is None:
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

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


def safe_dataframe(data):

    if data is None:
        return pd.DataFrame()

    if isinstance(data, pd.DataFrame):

        df = data.copy()

    else:

        try:
            df = pd.DataFrame(data)

        except Exception:
            return pd.DataFrame()

    for column in df.columns:

        if str(df[column].dtype) == "object":

            df[column] = (
                df[column]
                .map(
                    lambda x:
                    ""
                    if x is None
                    else str(x)
                )
                .astype("string")
            )

    return df


def metric_card(label, value, unit=""):

    st.markdown(
        f"""
        <div class="engine-card">
            <div class="card-label">{label}</div>
            <div class="card-value">{value}</div>
            <div class="card-unit">{unit}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(kicker, title):

    st.markdown(
        f"""
        <div class="section-kicker">{kicker}</div>
        <div class="section-title">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def get_value(result, *keys, default=None):

    for key in keys:

        if key in result and result[key] is not None:
            return result[key]

    return default


# ============================================================
# ENGINEERING STATUS
# ============================================================

def determine_status(result):

    if not result:
        return "NOT RUN"

    try:

        validation = validate_reactor(result)

        df = safe_dataframe(validation)

        if df.empty:
            return "READY"

        text = " ".join(
            df.astype(str)
            .fillna("")
            .values
            .flatten()
        ).upper()

        if "ERROR" in text or "FAIL" in text or "RISK" in text:
            return "RISK"

        if "WARNING" in text or "REVIEW" in text:
            return "REVIEW"

        return "READY"

    except Exception:

        return "REVIEW"


def status_badge(status):

    status = str(status).upper()

    if status == "READY":

        css = "status-ready"

    elif status == "RISK":

        css = "status-risk"

    else:

        css = "status-review"

    st.markdown(
        f'<span class="{css}">{status}</span>',
        unsafe_allow_html=True,
    )


# ============================================================
# SCALE-UP ENGINEERING LOGIC
# ============================================================

PROCESS_SCALEUP_LOGIC = {

    "Liquid–Liquid": {
        "primary": "Constant Q/V",
        "secondary": "P/V + Re + blend-time validation",
        "reason": "Liquid blending and circulation are usually governed by turnover and mixing time.",
    },

    "Solid–Liquid": {
        "primary": "Constant N/Njs",
        "secondary": "P/V + Q/V + impeller clearance",
        "reason": "Suspension quality should be maintained above the just-suspended condition.",
    },

    "Gas–Liquid": {
        "primary": "Constant kLa",
        "secondary": "P/V + superficial gas velocity + tip speed",
        "reason": "Gas dispersion and mass-transfer performance are normally the controlling criteria.",
    },

    "Gas–Liquid–Solid": {
        "primary": "N/Njs + kLa",
        "secondary": "P/V + gas velocity + circulation",
        "reason": "Both solids suspension and gas dispersion must be preserved.",
    },

    "Crystallization": {
        "primary": "N/Njs + controlled shear",
        "secondary": "P/V + tip speed + residence-time behaviour",
        "reason": "Suspension and local shear can strongly affect crystal growth and agglomeration.",
    },

    "High Viscosity": {
        "primary": "P/V + torque",
        "secondary": "Re + tip speed",
        "reason": "Power and shaft torque become important as viscous resistance increases.",
    },

    "Heat Transfer Controlled": {
        "primary": "Heat-transfer capacity",
        "secondary": "P/V + mixing + ΔT",
        "reason": "Scale-up must demonstrate adequate heat removal in addition to mixing similarity.",
    },

    "General Blending": {
        "primary": "Constant Q/V",
        "secondary": "P/V + Re",
        "reason": "Circulation and turnover are useful first-level indicators for blending.",
    },
}


def process_scaleup_recommendation(process_type):

    return PROCESS_SCALEUP_LOGIC.get(
        process_type,
        PROCESS_SCALEUP_LOGIC["General Blending"],
    )


# ============================================================
# IMPELLER CONFIGURATION
# ============================================================

POSITIONS = [
    "Bottom",
    "Middle",
    "Top",
]


def agitator_names():

    return [
        name
        for name, data in AGITATORS.items()
        if isinstance(data, dict)
    ]


# ============================================================
# IMPELLER ELEVATION
# ============================================================

def calculate_elevations(
    impellers,
    liquid_height,
    tank_diameter,
):

    H = sf(liquid_height, 0.10)
    T = sf(tank_diameter, 1.0)

    output = []

    for impeller in impellers:

        item = copy.deepcopy(impeller)

        position = item.get(
            "position",
            "Bottom",
        )

        clearance = max(
            0.0,
            sf(
                item.get(
                    "bottom_clearance_m"
                ),
                0.20 * T,
            ),
        )

        if position == "Bottom":

            elevation = clearance

        elif position == "Middle":

            elevation = 0.50 * H

        else:

            elevation = 0.75 * H

        elevation = min(
            elevation,
            max(
                0.05,
                H - 0.05,
            ),
        )

        item["elevation_m"] = elevation

        output.append(item)

    output.sort(
        key=lambda x:
        sf(x.get("elevation_m"))
    )

    return output


# ============================================================
# IMPELLER VALIDATION
# ============================================================

def validate_impellers(
    impellers,
    liquid_height,
    tank_diameter,
):

    messages = []

    H = sf(liquid_height)
    T = sf(tank_diameter)

    if not impellers:

        return [
            (
                "ERROR",
                "At least one impeller is required.",
            )
        ]

    elevations = []

    for i, impeller in enumerate(
        impellers,
        1,
    ):

        D = sf(
            impeller.get(
                "diameter_m"
            )
        )

        elevation = sf(
            impeller.get(
                "elevation_m"
            )
        )

        clearance = sf(
            impeller.get(
                "bottom_clearance_m"
            )
        )

        if D <= 0:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: diameter must be greater than zero.",
                )
            )

        if T > 0 and D >= T:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: diameter must be smaller than tank ID.",
                )
            )

        if H > 0 and elevation >= H:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: elevation is above liquid level.",
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

    rounded = [
        round(value, 4)
        for value in elevations
    ]

    if len(rounded) != len(set(rounded)):

        messages.append(
            (
                "WARNING",
                "Two or more impellers have identical elevations.",
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
# DESIGN INPUT PANEL
# ============================================================

def reactor_inputs():

    section_header(
        "01 / DESIGN BASIS",
        "Define the reactor and process",
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        process_type = st.selectbox(
            "Process Classification",
            [
                "General Blending",
                "Liquid–Liquid",
                "Solid–Liquid",
                "Gas–Liquid",
                "Gas–Liquid–Solid",
                "Crystallization",
                "High Viscosity",
                "Heat Transfer Controlled",
            ],
            key="process_type",
        )

        working_volume = st.number_input(
            "Working Volume",
            min_value=0.01,
            value=10.0,
            step=0.5,
            key="working_volume",
            help="Actual process working volume.",
        )

        density = st.number_input(
            "Liquid Density (kg/m³)",
            min_value=0.1,
            value=1000.0,
            step=10.0,
            key="density",
        )

    with c2:

        viscosity_cp = st.number_input(
            "Viscosity (cP)",
            min_value=0.001,
            value=1.0,
            step=0.1,
            key="viscosity_cp",
        )

        surface_tension = st.number_input(
            "Surface Tension (mN/m)",
            min_value=0.1,
            value=30.0,
            step=1.0,
            key="surface_tension",
        )

        rpm = st.number_input(
            "Agitator Speed (RPM)",
            min_value=0.1,
            value=100.0,
            step=5.0,
            key="rpm",
        )

    with c3:

        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=3,
            value=1,
            step=1,
            key="number_impellers",
        )

        number_baffles = st.number_input(
            "Number of Baffles",
            min_value=0,
            max_value=12,
            value=4,
            step=1,
            key="number_baffles",
        )

        st.markdown("**Recommended scale-up focus**")

        recommendation = process_scaleup_recommendation(
            process_type
        )

        st.info(
            f"**Primary:** {recommendation['primary']}\n\n"
            f"**Secondary:** {recommendation['secondary']}"
        )

    # ========================================================
    # VESSEL
    # ========================================================

    section_header(
        "02 / VESSEL GEOMETRY",
        "Define reactor geometry",
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        tank_D = st.number_input(
            "Tank ID (m)",
            min_value=0.10,
            value=2.0,
            step=0.05,
            key="tank_D",
        )

    with c2:

        straight_height = st.number_input(
            "Straight Side Height (m)",
            min_value=0.10,
            value=3.0,
            step=0.10,
            key="straight_height",
        )

    head_names = list(REACTOR_HEADS.keys())

    with c3:

        bottom_type = st.selectbox(
            "Bottom Head",
            head_names,
            key="bottom_type",
        )

    with c4:

        top_type = st.selectbox(
            "Top Head",
            head_names,
            key="top_type",
        )

    try:

        vessel_volume = calculate_total_volume(
            tank_D,
            straight_height,
            bottom_type,
            top_type,
        )

    except Exception as e:

        st.error(
            f"Geometry calculation failed: {e}"
        )

        vessel_volume = 0.0

    try:

        liquid_height = liquid_height_from_volume(
            working_volume,
            tank_D,
            straight_height,
            bottom_type,
            top_type,
        )

    except Exception:

        liquid_height = min(
            straight_height,
            working_volume /
            (
                math.pi
                * tank_D ** 2
                / 4.0
            ),
        )

    if vessel_volume > 0:

        fill_fraction = (
            working_volume /
            vessel_volume
        )

    else:

        fill_fraction = 0.0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Vessel Volume",
            fmt(vessel_volume, 2),
            "m³",
        )

    with c2:
        metric_card(
            "Working Volume",
            fmt(working_volume, 2),
            "m³",
        )

    with c3:
        metric_card(
            "Liquid Height",
            fmt(liquid_height, 2),
            "m",
        )

    with c4:
        metric_card(
            "Fill Fraction",
            f"{fill_fraction * 100:.1f}",
            "%",
        )

    if working_volume > vessel_volume:

        st.error(
            "Working volume exceeds calculated vessel volume. "
            "Correct the geometry before running the engineering calculation."
        )

    elif fill_fraction > 0.90:

        st.warning(
            "Working volume exceeds 90% of calculated vessel volume. "
            "Check freeboard and operating requirements."
        )

    # ========================================================
    # AGITATOR
    # ========================================================

    section_header(
        "03 / MIXING SYSTEM",
        "Configure impellers and shaft arrangement",
    )

    names = agitator_names()

    if not names:

        st.error(
            "No agitators found in agitator_geometry.py."
        )

        st.stop()

    impellers = []

    for i in range(int(number_impellers)):

        with st.expander(
            f"Impeller {i + 1}",
            expanded=True,
        ):

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                position = st.selectbox(
                    "Position",
                    POSITIONS,
                    index=min(
                        i,
                        len(POSITIONS) - 1,
                    ),
                    key=f"position_{i}",
                )

            with c2:

                agitator = st.selectbox(
                    "Agitator Type",
                    names,
                    key=f"agitator_{i}",
                )

            with c3:

                max_D = max(
                    0.02,
                    0.95 * tank_D,
                )

                default_D = min(
                    0.50 * tank_D,
                    max_D,
                )

                default_D = max(
                    0.05,
                    default_D,
                )

                D = st.number_input(
                    "Impeller Diameter (m)",
                    min_value=0.01,
                    max_value=max_D,
                    value=default_D,
                    step=0.05,
                    key=f"D_{i}",
                )

            with c4:

                max_clearance = max(
                    0.05,
                    liquid_height,
                )

                default_clearance = min(
                    0.20 * tank_D,
                    max_clearance,
                )

                clearance = st.number_input(
                    "Bottom Clearance (m)",
                    min_value=0.0,
                    max_value=max_clearance,
                    value=default_clearance,
                    step=0.05,
                    key=f"C_{i}",
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

    impellers = calculate_elevations(
        impellers,
        liquid_height,
        tank_D,
    )

    messages = validate_impellers(
        impellers,
        liquid_height,
        tank_D,
    )

    for level, message in messages:

        if level == "ERROR":
            st.error(message)

        elif level == "WARNING":
            st.warning(message)

        else:
            st.success(message)

    # ========================================================
    # GAS LIQUID
    # ========================================================

    section_header(
        "04 / OPTIONAL PHYSICS",
        "Gas–liquid system",
    )

    gas_active = st.checkbox(
        "Enable gas–liquid calculation",
        value=False,
        key="gas_active",
    )

    if gas_active:

        c1, c2, c3 = st.columns(3)

        with c1:

            gas_flow = st.number_input(
                "Gas Flow (m³/h)",
                min_value=0.001,
                value=10.0,
                step=1.0,
                key="gas_flow",
            )

        with c2:

            bubble_diameter = st.number_input(
                "Bubble Diameter (mm)",
                min_value=0.1,
                value=3.0,
                step=0.5,
                key="bubble_diameter",
            )

        with c3:

            gas_holdup = st.number_input(
                "Gas Holdup Fraction",
                min_value=0.001,
                max_value=0.50,
                value=0.05,
                step=0.01,
                key="gas_holdup",
            )

    else:

        gas_flow = 0.0
        bubble_diameter = 3.0
        gas_holdup = 0.05

    return {

        "process_type":
            process_type,

        "working_volume_m3":
            working_volume,

        "volume_m3":
            working_volume,

        "tank_diameter_m":
            tank_D,

        "diameter_m":
            tank_D,

        "straight_height_m":
            straight_height,

        "liquid_height_m":
            liquid_height,

        "density_kg_m3":
            density,

        "viscosity_cp":
            viscosity_cp,

        "viscosity_pa_s":
            viscosity_cp * 0.001,

        "surface_tension_mN_m":
            surface_tension,

        "surface_tension_n_m":
            surface_tension * 0.001,

        "rpm":
            rpm,

        "number_impellers":
            int(number_impellers),

        "number_baffles":
            int(number_baffles),

        "bottom_type":
            bottom_type,

        "top_type":
            top_type,

        "vessel_volume_m3":
            vessel_volume,

        "fill_fraction":
            fill_fraction,

        "impellers":
            impellers,

        "agitator":
            impellers[0]["agitator_type"],

        "impeller_diameter_m":
            impellers[0]["diameter_m"],

        "impeller_clearance_m":
            impellers[0]["bottom_clearance_m"],

        "gas_flow_m3_h":
            gas_flow,

        "bubble_diameter_mm":
            bubble_diameter,

        "gas_holdup_fraction":
            gas_holdup,
    }


# ============================================================
# ENGINE ADAPTER
# ============================================================

def run_calculation(inputs):

    primary = inputs["impellers"][0]

    result = calculate_reactor(

        volume_m3=inputs["working_volume_m3"],

        tank_diameter_m=inputs["tank_diameter_m"],

        liquid_height_m=inputs["liquid_height_m"],

        density_kg_m3=inputs["density_kg_m3"],

        viscosity_pa_s=inputs["viscosity_pa_s"],

        surface_tension_n_m=inputs["surface_tension_n_m"],

        rpm=inputs["rpm"],

        impeller_diameter_m=primary["diameter_m"],

        number_impellers=inputs["number_impellers"],

        agitator=primary["agitator_type"],

        impeller_clearance_m=primary["bottom_clearance_m"],

        gas_flow_m3_h=inputs["gas_flow_m3_h"],

        bubble_diameter_mm=inputs["bubble_diameter_mm"],

        gas_holdup_fraction=inputs["gas_holdup_fraction"],
    )

    result.update(
        {

            "process_type":
                inputs["process_type"],

            "rpm":
                inputs["rpm"],

            "straight_height_m":
                inputs["straight_height_m"],

            "bottom_type":
                inputs["bottom_type"],

            "top_type":
                inputs["top_type"],

            "number_baffles":
                inputs["number_baffles"],

            "vessel_volume_m3":
                inputs["vessel_volume_m3"],

            "fill_fraction":
                inputs["fill_fraction"],

            "impellers":
                copy.deepcopy(
                    inputs["impellers"]
                ),

            "working_volume_m3":
                inputs["working_volume_m3"],

            "viscosity_cp":
                inputs["viscosity_cp"],

            "surface_tension_mN_m":
                inputs["surface_tension_mN_m"],
        }
    )

    return result


# ============================================================
# OVERVIEW
# ============================================================

def overview_tab(result):

    section_header(
        "ENGINEERING OVERVIEW",
        "Scale-up design snapshot",
    )

    status = determine_status(result)

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        metric_card(
            "Working Volume",
            fmt(
                get_value(
                    result,
                    "working_volume_m3",
                    "volume_m3",
                ),
                2,
            ),
            "m³",
        )

    with c2:
        metric_card(
            "Tank ID",
            fmt(
                get_value(
                    result,
                    "tank_diameter_m",
                ),
                2,
            ),
            "m",
        )

    with c3:
        metric_card(
            "Agitator Speed",
            fmt(
                get_value(
                    result,
                    "rpm",
                ),
                0,
            ),
            "RPM",
        )

    with c4:
        metric_card(
            "Specific Power",
            fmt(
                get_value(
                    result,
                    "power_volume_kw_m3",
                ),
                3,
            ),
            "kW/m³",
        )

    with c5:

        st.markdown(
            '<div class="engine-card">'
            '<div class="card-label">ENGINEERING STATUS</div>',
            unsafe_allow_html=True,
        )

        status_badge(status)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    c1, c2 = st.columns([1.1, 1])

    with c1:

        st.markdown("### Design Basis")

        process_type = result.get(
            "process_type",
            "General Blending",
        )

        recommendation = process_scaleup_recommendation(
            process_type
        )

        st.markdown(
            f"""
**Process classification:** {process_type}

**Primary scale-up criterion:**  
### {recommendation['primary']}

**Secondary checks:**  
{recommendation['secondary']}

**Engineering rationale:**  
{recommendation['reason']}
"""
        )

    with c2:

        st.markdown("### Key Mixing Indicators")

        data = [

            {
                "Parameter": "Reynolds Number",
                "Value": get_value(
                    result,
                    "reynolds_number",
                ),
                "Unit": "-",
            },

            {
                "Parameter": "Tip Speed",
                "Value": get_value(
                    result,
                    "tip_speed",
                ),
                "Unit": "m/s",
            },

            {
                "Parameter": "Power",
                "Value": get_value(
                    result,
                    "power_kw",
                ),
                "Unit": "kW",
            },

            {
                "Parameter": "Pumping Capacity",
                "Value": get_value(
                    result,
                    "pumping_m3_h",
                ),
                "Unit": "m³/h",
            },

            {
                "Parameter": "Turnover Time",
                "Value": get_value(
                    result,
                    "turnover_time_min",
                ),
                "Unit": "min",
            },

            {
                "Parameter": "Torque",
                "Value": get_value(
                    result,
                    "torque_nm",
                ),
                "Unit": "N·m",
            },

        ]

        st.dataframe(
            safe_dataframe(data),
            width="stretch",
            hide_index=True,
        )

    st.divider()

    st.markdown("### Geometry Ratios")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "D/T",
            fmt(
                result.get("D_T"),
                3,
            ),
            "-",
        )

    with c2:
        metric_card(
            "H/T",
            fmt(
                result.get("H_T"),
                3,
            ),
            "-",
        )

    with c3:
        metric_card(
            "Liquid Height",
            fmt(
                result.get("liquid_height_m"),
                2,
            ),
            "m",
        )

    with c4:
        metric_card(
            "Froude Number",
            fmt(
                result.get("froude_number"),
                3,
            ),
            "-",
        )


# ============================================================
# MIXING TAB
# ============================================================

def mixing_tab(result):

    section_header(
        "MIXING ENGINEERING",
        "Agitator performance and circulation",
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Reynolds",
            fmt(
                result.get("reynolds_number"),
                0,
            ),
            "-",
        )

    with c2:
        metric_card(
            "Tip Speed",
            fmt(
                result.get("tip_speed"),
                2,
            ),
            "m/s",
        )

    with c3:
        metric_card(
            "Power",
            fmt(
                result.get("power_kw"),
                2,
            ),
            "kW",
        )

    with c4:
        metric_card(
            "P/V",
            fmt(
                result.get(
                    "power_volume_kw_m3"
                ),
                3,
            ),
            "kW/m³",
        )

    st.markdown("")

    c1, c2 = st.columns([1.2, 1])

    with c1:

        st.markdown("### Mixing Performance")

        data = [

            {
                "Parameter": "Working Volume",
                "Value": result.get("volume_m3"),
                "Unit": "m³",
            },

            {
                "Parameter": "Tank Diameter",
                "Value": result.get(
                    "tank_diameter_m"
                ),
                "Unit": "m",
            },

            {
                "Parameter": "Liquid Height",
                "Value": result.get(
                    "liquid_height_m"
                ),
                "Unit": "m",
            },

            {
                "Parameter": "RPM",
                "Value": result.get("rpm"),
                "Unit": "rpm",
            },

            {
                "Parameter": "Impeller Diameter",
                "Value": result.get(
                    "impeller_diameter_m"
                ),
                "Unit": "m",
            },

            {
                "Parameter": "Power",
                "Value": result.get(
                    "power_kw"
                ),
                "Unit": "kW",
            },

            {
                "Parameter": "Specific Power",
                "Value": result.get(
                    "power_volume_kw_m3"
                ),
                "Unit": "kW/m³",
            },

            {
                "Parameter": "Torque",
                "Value": result.get(
                    "torque_nm"
                ),
                "Unit": "N·m",
            },

            {
                "Parameter": "Pumping Capacity",
                "Value": result.get(
                    "pumping_m3_h"
                ),
                "Unit": "m³/h",
            },

            {
                "Parameter": "Turnover Time",
                "Value": result.get(
                    "turnover_time_min"
                ),
                "Unit": "min",
            },

            {
                "Parameter": "Froude Number",
                "Value": result.get(
                    "froude_number"
                ),
                "Unit": "-",
            },

            {
                "Parameter": "Mixing Regime",
                "Value": result.get(
                    "mixing_regime"
                ),
                "Unit": "-",
            },

        ]

        st.dataframe(
            safe_dataframe(data),
            width="stretch",
            hide_index=True,
        )

    with c2:

        st.markdown("### Engineering Interpretation")

        re_number = sf(
            result.get(
                "reynolds_number"
            )
        )

        if re_number < 10:

            regime = "Laminar / highly viscous"

        elif re_number < 10000:

            regime = "Transitional"

        else:

            regime = "Turbulent"

        st.info(
            f"""
**Mixing regime:** {regime}

**Calculated Re:** {fmt(re_number, 0)}

**Tip speed:** {fmt(result.get('tip_speed'), 2)} m/s

**P/V:** {fmt(result.get('power_volume_kw_m3'), 3)} kW/m³

**Turnover time:** {fmt(result.get('turnover_time_min'), 2)} min
"""
        )

        st.caption(
            "These indicators are engineering screening parameters. "
            "Final mixing performance should be validated against pilot "
            "data, vendor correlations, blend-time testing or CFD where justified."
        )

    st.divider()

    impeller_tab(result)


# ============================================================
# IMPELLER TAB
# ============================================================

def impeller_tab(result):

    st.markdown("### Impeller Arrangement")

    impellers = result.get(
        "impellers",
        [],
    )

    if not impellers:

        st.warning(
            "No impeller configuration available."
        )

        return

    tank_D = sf(
        result.get(
            "tank_diameter_m"
        )
    )

    rows = []

    for i, imp in enumerate(
        impellers,
        1,
    ):

        D = sf(
            imp.get(
                "diameter_m"
            )
        )

        agitator = imp.get(
            "agitator_type",
            "Unknown",
        )

        data = AGITATORS.get(
            agitator,
            {},
        )

        rows.append(
            {
                "Impeller":
                    f"I-{i}",

                "Position":
                    imp.get(
                        "position"
                    ),

                "Agitator":
                    agitator,

                "Flow Type":
                    data.get(
                        "flow_type",
                        "",
                    ),

                "Diameter (m)":
                    D,

                "D/T":
                    (
                        D / tank_D
                        if tank_D > 0
                        else None
                    ),

                "Elevation (m)":
                    imp.get(
                        "elevation_m"
                    ),

                "Clearance (m)":
                    imp.get(
                        "bottom_clearance_m"
                    ),

                "Np":
                    data.get(
                        "np"
                    ),

                "Nq":
                    data.get(
                        "nq"
                    ),
            }
        )

    st.dataframe(
        safe_dataframe(rows),
        width="stretch",
        hide_index=True,
    )

    chart = pd.DataFrame(
        {
            "Impeller":
                [
                    row["Impeller"]
                    for row in rows
                ],

            "Elevation":
                [
                    sf(
                        row[
                            "Elevation (m)"
                        ]
                    )
                    for row in rows
                ],
        }
    )

    st.markdown("### Impeller Elevation Profile")

    st.bar_chart(
        chart.set_index(
            "Impeller"
        )
    )


# ============================================================
# SCALE-UP TAB
# ============================================================

def scaleup_tab(result):

    section_header(
        "SCALE-UP ENGINEERING",
        "Reference → Target reactor evaluation",
    )

    process_type = result.get(
        "process_type",
        "General Blending",
    )

    recommendation = process_scaleup_recommendation(
        process_type
    )

    st.info(
        f"""
**Process:** {process_type}

**Recommended primary criterion:**  
### {recommendation['primary']}

**Secondary checks:** {recommendation['secondary']}

{recommendation['reason']}
"""
    )

    st.markdown("### Scale-Up Definition")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        V1 = st.number_input(
            "Reference Volume (m³)",
            min_value=0.01,
            value=1.0,
            step=0.1,
            key="scale_v1",
        )

    with c2:

        V2 = st.number_input(
            "Target Volume (m³)",
            min_value=0.01,
            value=float(
                result.get(
                    "volume_m3",
                    10.0,
                )
            ),
            step=0.5,
            key="scale_v2",
        )

    with c3:

        basis = st.selectbox(
            "Calculation Basis",
            [
                "Constant P/V",
                "Constant Tip Speed",
                "Constant RPM",
            ],
            key="scale_basis",
        )

    with c4:

        scale_ratio = (
            V2 / V1
            if V1 > 0
            else 0
        )

        metric_card(
            "Volume Scale Ratio",
            f"{scale_ratio:.2f}",
            "V₂ / V₁",
        )

    if V1 <= 0 or V2 <= 0:

        st.error(
            "Reference and target volumes must be greater than zero."
        )

        return

    st.divider()

    st.markdown("### Reference Design Basis")

    c1, c2, c3 = st.columns(3)

    with c1:

        ref_D = st.number_input(
            "Reference Impeller Diameter (m)",
            min_value=0.01,
            value=float(
                result.get(
                    "impeller_diameter_m",
                    0.5,
                )
            ),
            step=0.05,
            key="scale_ref_D",
        )

    with c2:

        ref_rpm = st.number_input(
            "Reference RPM",
            min_value=0.1,
            value=float(
                result.get(
                    "rpm",
                    100.0,
                )
            ),
            step=5.0,
            key="scale_ref_rpm",
        )

    with c3:

        ref_pv = st.number_input(
            "Reference P/V (kW/m³)",
            min_value=0.0001,
            value=max(
                0.0001,
                sf(
                    result.get(
                        "power_volume_kw_m3",
                        0.1,
                    )
                ),
            ),
            step=0.01,
            key="scale_ref_pv",
        )

    ref_tip = (
        math.pi
        * ref_D
        * ref_rpm
        / 60.0
    )

    metric_card(
        "Reference Tip Speed",
        fmt(ref_tip, 2),
        "m/s",
    )

    st.markdown("")

    try:

        output = calculate_scaleup(

            reference_volume=V1,

            target_volume=V2,

            basis=basis,

            reference_diameter=ref_D,

            reference_rpm=ref_rpm,

            reference_power_per_volume=ref_pv,

            reference_tip_speed=ref_tip,
        )

        if isinstance(
            output,
            dict,
        ):

            output_rows = [
                {
                    "Parameter":
                        key,

                    "Value":
                        value,
                }

                for key, value
                in output.items()
            ]

        else:

            output_rows = output

        st.markdown("### Scale-Up Calculation Result")

        st.dataframe(
            safe_dataframe(
                output_rows
            ),
            width="stretch",
            hide_index=True,
        )

    except Exception as e:

        st.error(
            "Scale-up calculation failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )

    st.divider()

    st.markdown("### Engineering Decision Framework")

    decision_data = [

        {
            "Check":
                "Primary scale-up criterion",

            "Recommendation":
                recommendation["primary"],

            "Purpose":
                "Preserve the dominant process requirement.",
        },

        {
            "Check":
                "Secondary criterion",

            "Recommendation":
                recommendation["secondary"],

            "Purpose":
                "Confirm that scale-up does not create unacceptable deviation.",
        },

        {
            "Check":
                "Volume ratio",

            "Recommendation":
                f"{scale_ratio:.2f}",

            "Purpose":
                "Quantify reference-to-target scale increase.",
        },

        {
            "Check":
                "Calculation basis",

            "Recommendation":
                basis,

            "Purpose":
                "Calculate target operating condition.",
        },

    ]

    st.dataframe(
        safe_dataframe(
            decision_data
        ),
        width="stretch",
        hide_index=True,
    )

    st.warning(
        "Scale-up basis must be selected from the process physics. "
        "Constant RPM should not be treated as a universal scale-up rule. "
        "Final selection should be supported by pilot data and validated correlations."
    )


# ============================================================
# GAS-LIQUID TAB
# ============================================================

def gas_liquid_tab(result):

    section_header(
        "GAS–LIQUID ENGINEERING",
        "Gas dispersion and mass-transfer screening",
    )

    if (
        result.get(
            "gas_liquid_status"
        )
        == "NOT ACTIVE"
    ):

        st.info(
            "Gas–liquid calculation is not active for this design."
        )

        return

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        metric_card(
            "Gas Flow",
            fmt(
                result.get(
                    "gas_flow_m3_h"
                ),
                2,
            ),
            "m³/h",
        )

    with c2:

        metric_card(
            "Superficial Velocity",
            fmt(
                result.get(
                    "gas_superficial_velocity_m_s"
                ),
                4,
            ),
            "m/s",
        )

    with c3:

        metric_card(
            "Gas Holdup",
            fmt(
                result.get(
                    "gas_holdup_fraction"
                ),
                3,
            ),
            "-",
        )

    with c4:

        metric_card(
            "kLa",
            fmt(
                result.get(
                    "kLa_1_h"
                ),
                2,
            ),
            "1/h",
        )

    data = [

        (
            "Gas Flow",
            result.get(
                "gas_flow_m3_h"
            ),
            "m³/h",
        ),

        (
            "Superficial Velocity",
            result.get(
                "gas_superficial_velocity_m_s"
            ),
            "m/s",
        ),

        (
            "Gas Holdup",
            result.get(
                "gas_holdup_fraction"
            ),
            "-",
        ),

        (
            "Bubble Diameter",
            result.get(
                "bubble_diameter_m"
            ),
            "m",
        ),

        (
            "Bubble Rise Velocity",
            result.get(
                "bubble_rise_velocity_m_s"
            ),
            "m/s",
        ),

        (
            "Bubble Residence Time",
            result.get(
                "bubble_residence_time_s"
            ),
            "s",
        ),

        (
            "Bubble Reynolds",
            result.get(
                "bubble_reynolds"
            ),
            "-",
        ),

        (
            "Schmidt Number",
            result.get(
                "schmidt_number"
            ),
            "-",
        ),

        (
            "Sherwood Number",
            result.get(
                "sherwood_number"
            ),
            "-",
        ),

        (
            "kL",
            result.get(
                "kL_m_s"
            ),
            "m/s",
        ),

        (
            "Interfacial Area",
            result.get(
                "interfacial_area_m2_m3"
            ),
            "m²/m³",
        ),

        (
            "kLa",
            result.get(
                "kLa_1_h"
            ),
            "1/h",
        ),
    ]

    rows = [

        {
            "Parameter":
                parameter,

            "Value":
                value,

            "Unit":
                unit,
        }

        for parameter, value, unit
        in data
    ]

    st.dataframe(
        safe_dataframe(rows),
        width="stretch",
        hide_index=True,
    )

    st.warning(
        "Gas–liquid calculations are screening-level estimates. "
        "kLa depends strongly on impeller geometry, gas rate, power input, "
        "physical properties and reactor configuration and should be validated "
        "using suitable experimental or vendor data."
    )


# ============================================================
# VALIDATION TAB
# ============================================================

def validation_tab(result):

    section_header(
        "ENGINEERING VALIDATION",
        "Design checks and engineering flags",
    )

    status = determine_status(result)

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            '<div class="engine-card">'
            '<div class="card-label">OVERALL STATUS</div>',
            unsafe_allow_html=True,
        )

        status_badge(status)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with c2:

        metric_card(
            "Working Volume",
            fmt(
                result.get(
                    "working_volume_m3"
                ),
                2,
            ),
            "m³",
        )

    with c3:

        metric_card(
            "Fill Fraction",
            f"{sf(result.get('fill_fraction')) * 100:.1f}",
            "%",
        )

    st.markdown("")

    try:

        output = validate_reactor(
            result
        )

        df = safe_dataframe(output)

        if df.empty:

            st.info(
                "Validation module returned no tabular checks."
            )

        else:

            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
            )

    except Exception as e:

        st.error(
            "Validation failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )

    st.divider()

    st.caption(
        "Validation is intended for engineering screening. "
        "Mechanical design, shaft critical speed, seals, bearings, "
        "stress calculations, nozzle loads, vibration and detailed "
        "equipment design require dedicated engineering checks."
    )


# ============================================================
# 3D REACTOR
# ============================================================

def three_d_tab(result):

    section_header(
        "3D ENGINEERING MODEL",
        "Interactive reactor and mixing visualization",
    )

    st.caption(
        "Use the 3D model to inspect vessel geometry, internals, "
        "impeller arrangement and physics-informed mixing layers."
    )

    view_mode = st.radio(
        "Visualization Mode",
        [
            "Equipment",
            "Cutaway",
            "Mixing",
            "Gas-Liquid",
            "Complete",
            "Custom",
        ],
        horizontal=True,
        key="reactor_3d_view_mode",
    )

    if view_mode == "Equipment":

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Dimensions",
        ]

    elif view_mode == "Cutaway":

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Dimensions",
        ]

    elif view_mode == "Mixing":

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Vortex Formation",
            "Velocity Profile",
            "Flow Profile",
            "Dead Zone Analysis",
            "Mixing Particles",
        ]

    elif view_mode == "Gas-Liquid":

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Gas-Liquid Bubbles",
            "Flow Profile",
        ]

    elif view_mode == "Complete":

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
            "Vortex Formation",
            "Velocity Profile",
            "Flow Profile",
            "Dead Zone Analysis",
            "Mixing Particles",
            "Gas-Liquid Bubbles",
            "Dimensions",
        ]

    else:

        selected_features = st.multiselect(
            "Visualization Layers",
            [
                "Reactor Geometry",
                "Liquid Level",
                "Impeller & Shaft",
                "Baffles",
                "Vortex Formation",
                "Velocity Profile",
                "Flow Profile",
                "Dead Zone Analysis",
                "Mixing Particles",
                "Gas-Liquid Bubbles",
                "Dimensions",
            ],
            default=[
                "Reactor Geometry",
                "Liquid Level",
                "Impeller & Shaft",
            ],
            key="custom_3d_features",
        )

    with st.expander(
        "3D Display Controls",
        expanded=False,
    ):

        c1, c2, c3 = st.columns(3)

        with c1:

            show_animation = st.checkbox(
                "Rotation animation",
                value=False,
                key="show_3d_animation",
            )

        with c2:

            transparent_shell = st.checkbox(
                "Transparent vessel",
                value=True,
                key="transparent_3d_shell",
            )

        with c3:

            engineering_axes = st.checkbox(
                "Engineering axes",
                value=True,
                key="engineering_3d_axes",
            )

    if not selected_features:

        st.warning(
            "Select at least one visualization layer."
        )

        return

    working_volume = sf(
        result.get(
            "working_volume_m3",
            result.get(
                "volume_m3",
                10.0,
            ),
        ),
        10.0,
    )

    tank_diameter = sf(
        result.get(
            "tank_diameter_m",
            2.0,
        ),
        2.0,
    )

    straight_height = sf(
        result.get(
            "straight_height_m",
            3.0,
        ),
        3.0,
    )

    liquid_height = result.get(
        "liquid_height_m",
        None,
    )

    rpm = sf(
        result.get(
            "rpm",
            100.0,
        ),
        100.0,
    )

    impellers = result.get(
        "impellers",
        [],
    )

    bottom_type = result.get(
        "bottom_type",
        "10% Torispherical",
    )

    top_type = result.get(
        "top_type",
        "10% Torispherical",
    )

    number_baffles = int(
        sf(
            result.get(
                "number_baffles",
                4,
            ),
            4,
        )
    )

    density = sf(
        result.get(
            "density_kg_m3",
            1000.0,
        ),
        1000.0,
    )

    viscosity = sf(
        result.get(
            "viscosity_pa_s",
            0.001,
        ),
        0.001,
    )

    gas_flow = sf(
        result.get(
            "gas_flow_m3_h",
            0.0,
        ),
        0.0,
    )

    bubble_diameter = sf(
        result.get(
            "bubble_diameter_mm",
            3.0,
        ),
        3.0,
    )

    primary = (
        impellers[0]
        if impellers
        else {}
    )

    agitator = primary.get(
        "agitator_type",
        result.get(
            "agitator",
            "Rushton Turbine",
        ),
    )

    impeller_D = sf(
        primary.get(
            "diameter_m",
            result.get(
                "impeller_diameter_m",
                tank_diameter * 0.5,
            ),
        ),
        tank_diameter * 0.5,
    )

    clearance = sf(
        primary.get(
            "bottom_clearance_m",
            result.get(
                "impeller_clearance_m",
                0.4,
            ),
        ),
        0.4,
    )

    try:

        fig = create_reactor_animation(

            volume_m3=working_volume,

            tank_diameter_m=tank_diameter,

            straight_height_m=straight_height,

            liquid_height_m=liquid_height,

            rpm=rpm,

            impellers=impellers,

            bottom_type=bottom_type,

            top_type=top_type,

            number_baffles=number_baffles,

            density_kg_m3=density,

            viscosity_pa_s=viscosity,

            gas_flow_m3_h=gas_flow,

            bubble_diameter_mm=bubble_diameter,

            selected_features=selected_features,

            D=tank_diameter,

            H=straight_height,

            volume=working_volume,

            liquid_level=liquid_height,

            agitator=agitator,

            impeller_diameter_m=impeller_D,

            number_impellers=len(
                impellers
            )
            if impellers
            else 1,

            impeller_clearance_m=clearance,
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
                "scrollZoom": True,
                "displayModeBar": True,
                "displayModeBarButtonsToAdd": [
                    "resetCameraDefault3d",
                    "resetCameraLastSave3d",
                ],
            },
        )

    except Exception as e:

        st.error(
            "3D reactor visualization failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )

    st.caption(
        "Visualization note: the 3D reactor is an engineering visualization "
        "and physics-informed screening layer. Velocity, vortex, dead-zone and "
        "particle representations are not validated CFD unless explicitly "
        "supported by a validated CFD workflow."
    )


# ============================================================
# REPORTS
# ============================================================

def reports_tab(
    inputs,
    result,
):

    section_header(
        "ENGINEERING REPORT",
        "Generate the scale-up design package",
    )

    if inputs is None or result is None:

        st.warning(
            "No completed engineering calculation is available."
        )

        return

    st.info(
        "Reports contain the current reactor design basis, "
        "calculation results, scale-up information and validation output."
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("### Word Engineering Report")

        try:

            word_file = create_word_report(
                inputs,
                result,
            )

            st.download_button(
                "Download Word Report",
                data=word_file.getvalue(),
                file_name="reactor_scaleup_engineering_report.docx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                width="stretch",
            )

        except Exception as e:

            st.error(
                "Word report generation failed."
            )

            st.code(
                f"{type(e).__name__}: {e}"
            )

    with c2:

        st.markdown("### Excel Engineering Workbook")

        try:

            excel_file = create_excel_report(
                inputs,
                result,
            )

            st.download_button(
                "Download Excel Report",
                data=excel_file.getvalue(),
                file_name="reactor_scaleup_engineering_report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
            )

        except Exception as e:

            st.error(
                "Excel report generation failed."
            )

            st.code(
                f"{type(e).__name__}: {e}"
            )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-brand">⚗️ REACTOR SCALE-UP</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-caption">'
        "Process & Mixing Engineering Studio"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Workspace")

    page = st.radio(
        "Engineering Workspace",
        [
            "Overview",
            "Mixing",
            "Scale-Up",
            "Gas–Liquid",
            "Validation",
            "3D Reactor",
            "Reports",
        ],
        label_visibility="collapsed",
        key="workspace_page",
    )

    st.divider()

    result_for_status = st.session_state.get(
        "reactor_result"
    )

    if result_for_status:

        st.markdown("### Design Status")

        status = determine_status(
            result_for_status
        )

        status_badge(status)

        st.markdown("")

        st.caption(
            f"Process: "
            f"{result_for_status.get('process_type', '—')}"
        )

        st.caption(
            f"Volume: "
            f"{fmt(result_for_status.get('volume_m3'), 2)} m³"
        )

    else:

        st.info(
            "No engineering calculation has been run yet."
        )

    st.divider()

    st.markdown("### Engineering Scope")

    st.caption(
        """
Reactor geometry

Agitator & mixing

Scale-up criteria

Solid suspension

Gas–liquid transfer

Engineering validation

3D reactor visualization
"""
    )

    st.divider()

    st.caption(
        "Screening tool. Final design requires validated "
        "correlations, pilot/plant data, vendor confirmation "
        "and mechanical design checks."
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
<div class="hero">

<div class="hero-kicker">
REACTOR ENGINEERING / SCALE-UP PLATFORM
</div>

<div class="hero-title">
Reactor Scale-Up Engineering Studio
</div>

<div class="hero-subtitle">
From process requirement → mixing mechanism → scale-up criterion
→ reactor geometry → agitator performance → engineering validation.
</div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DESIGN INPUTS
# ============================================================

with st.expander(
    "⚙️ Design Basis & Reactor Inputs",
    expanded=(
        st.session_state.get(
            "reactor_result"
        )
        is None
    ),
):

    inputs = reactor_inputs()

    st.divider()

    calculate = st.button(
        "▶  RUN ENGINEERING CALCULATION",
        type="primary",
        width="stretch",
    )

else_block = None


# ============================================================
# CALCULATION
# ============================================================

if calculate:

    calculation_errors = []

    if (
        inputs["working_volume_m3"]
        >
        inputs["vessel_volume_m3"]
    ):

        calculation_errors.append(
            "Working volume exceeds calculated vessel volume."
        )

    impeller_errors = [
        message
        for level, message
        in validate_impellers(
            inputs["impellers"],
            inputs["liquid_height_m"],
            inputs["tank_diameter_m"],
        )
        if level == "ERROR"
    ]

    calculation_errors.extend(
        impeller_errors
    )

    if calculation_errors:

        st.error(
            "Engineering calculation cannot proceed."
        )

        for message in calculation_errors:

            st.error(message)

    else:

        try:

            with st.spinner(
                "Running reactor engineering calculations..."
            ):

                result = run_calculation(
                    inputs
                )

            st.session_state[
                "reactor_inputs"
            ] = copy.deepcopy(
                inputs
            )

            st.session_state[
                "reactor_result"
            ] = copy.deepcopy(
                result
            )

            st.session_state[
                "calculation_complete"
            ] = True

            st.success(
                "Engineering calculation completed successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Reactor engineering calculation failed."
            )

            st.code(
                f"{type(e).__name__}: {e}"
            )


# ============================================================
# STORED RESULT
# ============================================================

result = st.session_state.get(
    "reactor_result"
)

stored_inputs = st.session_state.get(
    "reactor_inputs"
)


# ============================================================
# WORKSPACE
# ============================================================

if result is None:

    st.markdown(
        """
        <div class="empty-state">

        <div class="empty-title">
        Start a Reactor Scale-Up Study
        </div>

        <div class="empty-text">
        Define the process, vessel geometry and mixing system above.
        The platform will then evaluate reactor performance, scale-up
        criteria, mixing behaviour, gas–liquid performance and engineering
        validation.
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    if page == "Overview":

        overview_tab(result)

    elif page == "Mixing":

        mixing_tab(result)

    elif page == "Scale-Up":

        scaleup_tab(result)

    elif page == "Gas–Liquid":

        gas_liquid_tab(result)

    elif page == "Validation":

        validation_tab(result)

    elif page == "3D Reactor":

        three_d_tab(result)

    elif page == "Reports":

        reports_tab(
            stored_inputs,
            result,
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Reactor Scale-Up Engineering Studio • "
    "Engineering screening platform • "
    "Use validated process correlations and plant/pilot data "
    "for final scale-up decisions."
)
