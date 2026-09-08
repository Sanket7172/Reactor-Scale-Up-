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
# PROJECT IMPORTS
# ============================================================

try:
    from calculations.engine import calculate_reactor
except Exception as exc:
    st.error(f"Unable to import calculations.engine: {exc}")
    st.stop()

try:
    from calculations.validation import validate_reactor, recommendations
except Exception:
    validate_reactor = None
    recommendations = None

try:
    from libraries.agitator_geometry import AGITATORS
except Exception as exc:
    st.error(f"Unable to import agitator library: {exc}")
    st.stop()

try:
    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )
except Exception as exc:
    st.error(f"Unable to import reactor geometry library: {exc}")
    st.stop()

try:
    from visualization.reactor_3d import create_reactor_animation
except Exception:
    create_reactor_animation = None


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
# MODERN UI CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 15% 5%,
                rgba(59,130,246,0.08),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 20%,
                rgba(14,165,233,0.06),
                transparent 25%
            ),
            #07111f;
        color: #e5edf7;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: #091524;
        border-right: 1px solid rgba(148,163,184,0.12);
    }

    [data-testid="stSidebar"] * {
        color: #dbe7f5;
    }

    /* Main width */

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* ======================================================
       TYPOGRAPHY
       ====================================================== */

    h1 {
        color: #f8fafc !important;
        font-size: 2.15rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.035em;
    }

    h2 {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    h3 {
        color: #e2e8f0 !important;
        font-weight: 650 !important;
    }

    p {
        color: #94a3b8;
    }

    /* ======================================================
       METRIC CARDS
       ====================================================== */

    [data-testid="stMetric"] {
        background: rgba(15, 29, 47, 0.88);
        border: 1px solid rgba(148,163,184,0.13);
        border-radius: 14px;
        padding: 15px 17px;
        min-height: 118px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.14);
    }

    [data-testid="stMetricLabel"] {
        color: #8fa4bb !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 1.65rem !important;
        font-weight: 750 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.76rem !important;
    }

    /* ======================================================
       INPUTS
       ====================================================== */

    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"],
    .stMultiSelect div[data-baseweb="select"] {
        background-color: #0d1b2b !important;
        border-color: rgba(148,163,184,0.18) !important;
    }

    .stNumberInput input,
    .stTextInput input {
        color: #f8fafc !important;
    }

    label {
        color: #b7c5d6 !important;
        font-weight: 550 !important;
    }

    /* ======================================================
       BUTTONS
       ====================================================== */

    .stButton > button {
        width: 100%;
        border-radius: 9px;
        border: 1px solid rgba(96,165,250,0.25);
        background: #13263d;
        color: #e8f1fb;
        font-weight: 650;
        transition: 0.2s ease;
    }

    .stButton > button:hover {
        border-color: rgba(96,165,250,0.55);
        background: #18314f;
    }

    /* ======================================================
       TABS
       ====================================================== */

    button[data-baseweb="tab"] {
        color: #8fa4bb !important;
        font-weight: 650 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #f8fafc !important;
    }

    /* ======================================================
       DATAFRAME
       ====================================================== */

    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ======================================================
       EXPANDER
       ====================================================== */

    [data-testid="stExpander"] {
        background: rgba(13,27,43,0.75);
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 12px;
    }

    /* ======================================================
       DIVIDER
       ====================================================== */

    hr {
        border-color: rgba(148,163,184,0.12) !important;
    }

    /* ======================================================
       SMALL ENGINEERING LABEL
       ====================================================== */

    .engineering-label {
        color: #60a5fa;
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .engineering-subtitle {
        color: #91a4b9;
        font-size: 0.92rem;
        margin-bottom: 18px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ENGINEERING SCALE-UP FUNCTIONS
# ============================================================

def local_scaleup_rpm(reference, target, basis):
    """
    Calculate target RPM using the selected scale-up criterion.

    Engineering basis:
        Tip speed:
            N ∝ 1/D

        Constant RPM:
            N = constant

        Froude:
            Fr = N²D/g
            N ∝ D^(-0.5)

        P/V:
            P/V ∝ N³D⁵/V
            N ∝ (V/D⁵)^(1/3)

        Q/V:
            Q/V ∝ ND³/V
            N ∝ V/D³

        Reynolds:
            Re ∝ ND²
            N ∝ 1/D²

    Returns:
        target RPM or None.
    """

    try:
        nr = float(reference["rpm"])
        dr = float(reference["impeller_diameter_m"])
        vr = float(reference["volume_m3"])

        dt = float(target["impeller_diameter_m"])
        vt = float(target["volume_m3"])

        if min(nr, dr, vr, dt, vt) <= 0:
            return None

        basis = str(basis).strip().lower()

        if basis == "constant tip speed":
            return nr * dr / dt

        if basis == "constant rpm":
            return nr

        if basis == "constant froude number":
            return nr * math.sqrt(dr / dt)

        if basis == "constant p/v":
            return nr * (
                ((dr ** 5) / vr) /
                ((dt ** 5) / vt)
            ) ** (1.0 / 3.0)

        if basis in (
            "constant q/v",
            "constant pumping / volume",
            "constant pumping/volume",
        ):
            return nr * (
                ((dr ** 3) / vr) /
                ((dt ** 3) / vt)
            )

        if basis == "constant reynolds number":
            return nr * (dr / dt) ** 2

        return None

    except Exception:
        return None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def fmt(value, digits=2, unit=""):
    if value is None:
        return "—"

    try:
        return f"{float(value):,.{digits}f}{unit}"
    except Exception:
        return "—"


def add_derived_values(result, geometry):
    """
    Ensure important engineering quantities are available even if
    the underlying engine version uses slightly different names.
    """

    data = dict(result)

    volume = safe_float(geometry.get("working_volume_m3"))
    diameter = safe_float(geometry.get("tank_diameter_m"))
    impeller = safe_float(geometry.get("impeller_diameter_m"))
    rpm = safe_float(geometry.get("rpm"))

    power_w = safe_float(
        data.get(
            "power_w",
            safe_float(data.get("power_kw")) * 1000
        )
    )

    q_m3_h = safe_float(data.get("pumping_m3_h"))

    if volume > 0 and power_w > 0:
        data["power_volume"] = power_w / volume
        data["pv_kw_m3"] = power_w / 1000 / volume
    else:
        data["power_volume"] = None
        data["pv_kw_m3"] = None

    if volume > 0 and q_m3_h > 0:
        data["qv_1_h"] = q_m3_h / volume
        data["turnover_time_min"] = 60.0 / data["qv_1_h"]
    else:
        data["qv_1_h"] = None
        data["turnover_time_min"] = None

    if rpm > 0 and impeller > 0:
        n = rpm / 60.0
        data["tip_speed"] = math.pi * impeller * n

    if rpm > 0 and impeller > 0 and power_w > 0:
        n = rpm / 60.0
        data["torque_nm"] = power_w / (2.0 * math.pi * n)

    if diameter > 0 and impeller > 0:
        data["impeller_D_T"] = impeller / diameter

    return data


def process_basis(process_type):
    basis = {
        "Liquid–Liquid": {
            "primary": "Q/V and blend-time behaviour",
            "secondary": "P/V, tip speed and Reynolds number",
            "note": "Use circulation intensity and experimentally validated blend time as the main scale-up indicators.",
        },
        "Solid–Liquid": {
            "primary": "N/Njs",
            "secondary": "P/V, Q/V and clearance",
            "note": "Suspension quality should be verified experimentally or using a validated Njs correlation.",
        },
        "Gas–Liquid": {
            "primary": "kLa / gas dispersion",
            "secondary": "P/V, superficial gas velocity and tip speed",
            "note": "kLa is system-specific and should not be treated as a universal geometric scale-up law.",
        },
        "Gas–Liquid–Solid": {
            "primary": "N/Njs + gas dispersion",
            "secondary": "kLa, P/V and Q/V",
            "note": "Maintain solids suspension and gas dispersion simultaneously.",
        },
        "Crystallization": {
            "primary": "Suspension + controlled shear",
            "secondary": "P/V, tip speed and Reynolds number",
            "note": "Crystal morphology and attrition can make simple P/V scaling insufficient.",
        },
        "High Viscosity": {
            "primary": "Torque + P/V",
            "secondary": "Reynolds number and tip speed",
            "note": "Power and torque capability become important design constraints.",
        },
        "Heat-Controlled Reaction": {
            "primary": "Heat-transfer capacity + mixing",
            "secondary": "P/V and circulation",
            "note": "Agitation cannot compensate for inadequate heat-transfer area or utility conditions.",
        },
        "General Blending": {
            "primary": "Blend time / Q/V",
            "secondary": "P/V and Reynolds number",
            "note": "Validate blend time using representative physical properties and geometry.",
        },
    }

    return basis.get(
        process_type,
        {
            "primary": "Process-specific criterion",
            "secondary": "P/V, Q/V and Re",
            "note": "Define the governing scale-up criterion from process development data.",
        },
    )


def calculate_geometry(
    tank_diameter_mm,
    straight_height_mm,
    bottom_type,
    top_type,
    working_volume_m3,
):
    """
    Uses the actual reactor geometry module with positional
    arguments to avoid keyword/signature compatibility issues.
    """

    diameter_m = tank_diameter_mm / 1000.0
    straight_m = straight_height_mm / 1000.0

    total_volume = calculate_total_volume(
        diameter_m,
        straight_m,
        bottom_type,
        top_type,
    )

    liquid_height, _ = liquid_height_from_volume(
        working_volume_m3,
        diameter_m,
        straight_m,
        bottom_type,
        top_type,
    )

    return {
        "tank_diameter_m": diameter_m,
        "straight_height_m": straight_m,
        "total_volume_m3": total_volume,
        "working_volume_m3": working_volume_m3,
        "liquid_height_m": liquid_height,
        "fill_percent": (
            working_volume_m3 / total_volume * 100
            if total_volume > 0
            else 0
        ),
    }


def run_reactor_calculation(
    geometry,
    density,
    viscosity,
    surface_tension,
    rpm,
    impeller_diameter,
    number_impellers,
    agitator,
    clearance,
):
    """
    Calls the existing calculation engine using its known
    positional signature.
    """

    result = calculate_reactor(
        geometry["working_volume_m3"],
        geometry["tank_diameter_m"],
        geometry["liquid_height_m"],
        density,
        viscosity,
        surface_tension,
        rpm,
        impeller_diameter,
        number_impellers,
        agitator,
        clearance,
    )

    return add_derived_values(
        result,
        {
            **geometry,
            "impeller_diameter_m": impeller_diameter,
            "rpm": rpm,
        },
    )


def validation_summary(data):
    if validate_reactor is None:
        return []

    try:
        return validate_reactor(data)
    except Exception:
        return []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚗️ Reactor Studio")
    st.caption("Process Engineering • Mixing • Scale-Up")

    st.divider()

    st.markdown("### Study")

    project_name = st.text_input(
        "Project / Batch",
        value="Reactor Scale-Up Study",
    )

    engineer_name = st.text_input(
        "Engineer",
        value="Process Engineering",
    )

    study_mode = st.selectbox(
        "Analysis mode",
        [
            "Single Reactor",
            "Reference → Target",
            "Multi-Reactor Comparison",
        ],
    )

    process_type = st.selectbox(
        "Process type",
        [
            "General Blending",
            "Liquid–Liquid",
            "Solid–Liquid",
            "Gas–Liquid",
            "Gas–Liquid–Solid",
            "Crystallization",
            "High Viscosity",
            "Heat-Controlled Reaction",
        ],
    )

    st.divider()

    st.markdown("### Scale-Up Criterion")

    scale_basis = st.selectbox(
        "Primary basis",
        [
            "Constant P/V",
            "Constant Q/V",
            "Constant Tip Speed",
            "Constant Froude Number",
            "Constant RPM",
            "Constant Reynolds Number",
        ],
    )

    st.divider()

    st.caption("Engineering screening tool")
    st.caption("Validate final design against process data, vendor data and plant trials.")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="engineering-label">PROCESS ENGINEERING / MIXING / SCALE-UP</div>',
    unsafe_allow_html=True,
)

st.title("Reactor Scale-Up Engineering Studio")

st.markdown(
    """
    A structured engineering workspace for reactor geometry,
    agitator selection, mixing performance and scale-up evaluation.
    """
)

st.caption(
    f"Project: **{project_name}**  •  Process: **{process_type}**  •  "
    f"Scale-up basis: **{scale_basis}**"
)

st.divider()


# ============================================================
# PROCESS BASIS
# ============================================================

basis_info = process_basis(process_type)

b1, b2, b3 = st.columns(3)

with b1:
    st.metric(
        "Primary engineering criterion",
        basis_info["primary"],
    )

with b2:
    st.metric(
        "Secondary indicators",
        basis_info["secondary"],
    )

with b3:
    st.metric(
        "Selected scale-up basis",
        scale_basis,
    )

st.info(basis_info["note"])


# ============================================================
# REACTOR INPUT FUNCTION
# ============================================================

def reactor_input(label, defaults=None):

    defaults = defaults or {}

    st.markdown(f"### {label}")

    tab_geometry, tab_fluid, tab_agitation = st.tabs(
        [
            "Reactor Geometry",
            "Fluid / Process",
            "Agitation",
        ]
    )

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    with tab_geometry:

        c1, c2, c3 = st.columns(3)

        with c1:
            working_volume = st.number_input(
                "Working volume (m³)",
                min_value=0.01,
                value=float(defaults.get("working_volume_m3", 1.0)),
                step=0.1,
                key=f"{label}_working_volume",
            )

        with c2:
            tank_diameter_mm = st.number_input(
                "Tank ID (mm)",
                min_value=100.0,
                value=float(defaults.get("tank_diameter_mm", 1000.0)),
                step=50.0,
                key=f"{label}_diameter",
            )

        with c3:
            straight_height_mm = st.number_input(
                "Straight side (mm)",
                min_value=100.0,
                value=float(defaults.get("straight_height_mm", 1500.0)),
                step=50.0,
                key=f"{label}_straight",
            )

        c4, c5 = st.columns(2)

        bottom_options = list(REACTOR_HEADS.keys())

        with c4:
            bottom_type = st.selectbox(
                "Bottom head",
                bottom_options,
                index=(
                    bottom_options.index(
                        defaults.get(
                            "bottom_type",
                            "2:1 Ellipsoidal",
                        )
                    )
                    if defaults.get(
                        "bottom_type",
                        "2:1 Ellipsoidal",
                    )
                    in bottom_options
                    else 1
                ),
                key=f"{label}_bottom",
            )

        with c5:
            top_type = st.selectbox(
                "Top head",
                bottom_options,
                index=(
                    bottom_options.index(
                        defaults.get(
                            "top_type",
                            "2:1 Ellipsoidal",
                        )
                    )
                    if defaults.get(
                        "top_type",
                        "2:1 Ellipsoidal",
                    )
                    in bottom_options
                    else 1
                ),
                key=f"{label}_top",
            )

    # --------------------------------------------------------
    # FLUID
    # --------------------------------------------------------

    with tab_fluid:

        c1, c2, c3 = st.columns(3)

        with c1:
            density = st.number_input(
                "Density (kg/m³)",
                min_value=1.0,
                value=float(defaults.get("density", 1000.0)),
                step=10.0,
                key=f"{label}_density",
            )

        with c2:
            viscosity_cP = st.number_input(
                "Viscosity (cP)",
                min_value=0.01,
                value=float(defaults.get("viscosity_cP", 1.0)),
                step=0.5,
                key=f"{label}_viscosity",
            )

        with c3:
            surface_tension = st.number_input(
                "Surface tension (N/m)",
                min_value=0.001,
                value=float(defaults.get("surface_tension", 0.072)),
                step=0.001,
                format="%.4f",
                key=f"{label}_surface",
            )

        viscosity_pa_s = viscosity_cP / 1000.0

        st.caption(
            f"Internal viscosity used for Reynolds calculation: "
            f"{viscosity_pa_s:.5f} Pa·s"
        )

    # --------------------------------------------------------
    # AGITATION
    # --------------------------------------------------------

    with tab_agitation:

        agitator_names = list(AGITATORS.keys())

        c1, c2 = st.columns(2)

        with c1:
            agitator = st.selectbox(
                "Agitator",
                agitator_names,
                index=(
                    agitator_names.index(
                        defaults.get(
                            "agitator",
                            agitator_names[0],
                        )
                    )
                    if defaults.get(
                        "agitator",
                        agitator_names[0],
                    ) in agitator_names
                    else 0
                ),
                key=f"{label}_agitator",
            )

        with c2:
            rpm = st.number_input(
                "Operating speed (RPM)",
                min_value=1.0,
                value=float(defaults.get("rpm", 100.0)),
                step=5.0,
                key=f"{label}_rpm",
            )

        agitator_data = AGITATORS[agitator]

        c3, c4, c5 = st.columns(3)

        with c3:
            default_ratio = float(
                agitator_data.get("D_T", 0.4)
            )

            impeller_ratio = st.number_input(
                "Impeller D/T",
                min_value=0.05,
                max_value=0.95,
                value=float(
                    defaults.get(
                        "impeller_D_T",
                        default_ratio,
                    )
                ),
                step=0.01,
                key=f"{label}_impeller_ratio",
            )

        with c4:
            number_impellers = st.number_input(
                "Number of impellers",
                min_value=1,
                max_value=8,
                value=int(
                    defaults.get(
                        "number_impellers",
                        1,
                    )
                ),
                step=1,
                key=f"{label}_number_impellers",
            )

        with c5:
            clearance_ratio = st.number_input(
                "Clearance C/T",
                min_value=0.02,
                max_value=0.70,
                value=float(
                    defaults.get(
                        "clearance_T",
                        0.10,
                    )
                ),
                step=0.01,
                key=f"{label}_clearance",
            )

        tank_diameter_m_temp = tank_diameter_mm / 1000.0

        impeller_diameter = (
            tank_diameter_m_temp * impeller_ratio
        )

        clearance_m = (
            tank_diameter_m_temp * clearance_ratio
        )

        st.caption(
            f"Impeller diameter: **{impeller_diameter:.3f} m**  •  "
            f"Clearance: **{clearance_m:.3f} m**  •  "
            f"Agitator type: **{agitator_data.get('flow', 'N/A')}**"
        )

    # --------------------------------------------------------
    # GEOMETRY CALCULATION
    # --------------------------------------------------------

    try:

        geometry = calculate_geometry(
            tank_diameter_mm,
            straight_height_mm,
            bottom_type,
            top_type,
            working_volume,
        )

    except Exception as exc:

        st.error(
            f"Reactor geometry calculation failed for {label}: {exc}"
        )

        st.stop()

    # --------------------------------------------------------
    # ENGINE CALCULATION
    # --------------------------------------------------------

    try:

        result = run_reactor_calculation(
            geometry,
            density,
            viscosity_pa_s,
            surface_tension,
            rpm,
            impeller_diameter,
            number_impellers,
            agitator,
            clearance_m,
        )

    except Exception as exc:

        st.error(
            f"Mixing calculation failed for {label}: {exc}"
        )

        st.stop()

    # --------------------------------------------------------
    # PACKAGE DATA
    # --------------------------------------------------------

    result["reactor_name"] = label
    result["rpm"] = rpm
    result["agitator"] = agitator
    result["number_impellers"] = number_impellers
    result["impeller_diameter_m"] = impeller_diameter
    result["clearance_m"] = clearance_m
    result["clearance_T"] = clearance_ratio

    result["tank_diameter_m"] = tank_diameter_m_temp
    result["straight_height_m"] = straight_height_mm / 1000.0
    result["working_volume_m3"] = working_volume
    result["total_volume_m3"] = geometry["total_volume_m3"]
    result["liquid_height_m"] = geometry["liquid_height_m"]
    result["fill_percent"] = geometry["fill_percent"]

    result["bottom_type"] = bottom_type
    result["top_type"] = top_type

    result["density_kg_m3"] = density
    result["viscosity_pa_s"] = viscosity_pa_s
    result["viscosity_cP"] = viscosity_cP
    result["surface_tension_n_m"] = surface_tension

    result["process_type"] = process_type
    result["scale_basis"] = scale_basis

    return result


# ============================================================
# CREATE REACTOR DATA
# ============================================================

if study_mode == "Single Reactor":

    reactors = {}

    reactors["Reactor"] = reactor_input(
        "Reactor",
        {
            "working_volume_m3": 5.0,
            "tank_diameter_mm": 1800.0,
            "straight_height_mm": 2500.0,
            "bottom_type": "2:1 Ellipsoidal",
            "top_type": "2:1 Ellipsoidal",
            "density": 1000.0,
            "viscosity_cP": 1.0,
            "surface_tension": 0.072,
            "agitator": list(AGITATORS.keys())[0],
            "rpm": 100.0,
            "impeller_D_T": 0.40,
            "number_impellers": 1,
            "clearance_T": 0.10,
        },
    )

elif study_mode == "Reference → Target":

    reactors = {}

    reactors["Reference"] = reactor_input(
        "Reference Reactor",
        {
            "working_volume_m3": 1.0,
            "tank_diameter_mm": 1000.0,
            "straight_height_mm": 1500.0,
            "bottom_type": "2:1 Ellipsoidal",
            "top_type": "2:1 Ellipsoidal",
            "density": 1000.0,
            "viscosity_cP": 1.0,
            "surface_tension": 0.072,
            "agitator": list(AGITATORS.keys())[0],
            "rpm": 150.0,
            "impeller_D_T": 0.40,
            "number_impellers": 1,
            "clearance_T": 0.10,
        },
    )

    reactors["Target"] = reactor_input(
        "Target Reactor",
        {
            "working_volume_m3": 10.0,
            "tank_diameter_mm": 2000.0,
            "straight_height_mm": 3000.0,
            "bottom_type": "2:1 Ellipsoidal",
            "top_type": "2:1 Ellipsoidal",
            "density": 1000.0,
            "viscosity_cP": 1.0,
            "surface_tension": 0.072,
            "agitator": list(AGITATORS.keys())[0],
            "rpm": 100.0,
            "impeller_D_T": 0.40,
            "number_impellers": 1,
            "clearance_T": 0.10,
        },
    )

else:

    reactors = {}

    reactor_names = [
        "Lab",
        "Pilot",
        "Commercial",
    ]

    defaults = [
        {
            "working_volume_m3": 0.5,
            "tank_diameter_mm": 800.0,
            "straight_height_mm": 1200.0,
        },
        {
            "working_volume_m3": 5.0,
            "tank_diameter_mm": 1600.0,
            "straight_height_mm": 2200.0,
        },
        {
            "working_volume_m3": 20.0,
            "tank_diameter_mm": 2400.0,
            "straight_height_mm": 3500.0,
        },
    ]

    for name, default in zip(reactor_names, defaults):

        base = {
            "bottom_type": "2:1 Ellipsoidal",
            "top_type": "2:1 Ellipsoidal",
            "density": 1000.0,
            "viscosity_cP": 1.0,
            "surface_tension": 0.072,
            "agitator": list(AGITATORS.keys())[0],
            "rpm": 100.0,
            "impeller_D_T": 0.40,
            "number_impellers": 1,
            "clearance_T": 0.10,
        }

        base.update(default)

        reactors[name] = reactor_input(
            name,
            base,
        )


# ============================================================
# SELECT DISPLAY REACTOR
# ============================================================

if study_mode == "Single Reactor":

    selected_name = "Reactor"

elif study_mode == "Reference → Target":

    selected_name = st.radio(
        "Displayed reactor",
        list(reactors.keys()),
        horizontal=True,
    )

else:

    selected_name = st.selectbox(
        "Displayed reactor",
        list(reactors.keys()),
    )

selected = reactors[selected_name]


# ============================================================
# ENGINEERING DASHBOARD
# ============================================================

st.divider()

st.markdown(
    '<div class="engineering-label">LIVE ENGINEERING PERFORMANCE</div>',
    unsafe_allow_html=True,
)

st.header(f"{selected_name} Performance")


# ============================================================
# PRIMARY KPI ROW
# ============================================================

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric(
        "P / V",
        fmt(
            selected.get("power_volume"),
            1,
            " W/m³",
        ),
    )

with k2:
    st.metric(
        "P / V",
        fmt(
            selected.get("pv_kw_m3"),
            3,
            " kW/m³",
        ),
    )

with k3:
    st.metric(
        "Shaft Power",
        fmt(
            selected.get("power_kw"),
            3,
            " kW",
        ),
    )

with k4:
    st.metric(
        "Q / V",
        fmt(
            selected.get("qv_1_h"),
            2,
            " 1/h",
        ),
    )

with k5:
    st.metric(
        "Tip Speed",
        fmt(
            selected.get("tip_speed"),
            2,
            " m/s",
        ),
    )

with k6:
    st.metric(
        "Reynolds",
        f"{safe_float(selected.get('Re')):,.0f}"
        if selected.get("Re") is not None
        else "—",
    )


# ============================================================
# SECONDARY KPI ROW
# ============================================================

st.markdown("#### Mechanical / Hydrodynamic Indicators")

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric(
        "Torque",
        fmt(
            selected.get("torque_nm"),
            1,
            " N·m",
        ),
    )

with k2:
    st.metric(
        "Froude",
        fmt(
            selected.get("Fr"),
            4,
        ),
    )

with k3:
    st.metric(
        "Impeller D/T",
        fmt(
            selected.get("impeller_D_T"),
            3,
        ),
    )

with k4:
    st.metric(
        "Tank H/T",
        fmt(
            selected.get("H_T"),
            2,
        ),
    )

with k5:
    st.metric(
        "Clearance C/T",
        fmt(
            selected.get("clearance_T"),
            2,
        ),
    )

with k6:
    st.metric(
        "Turnover",
        fmt(
            selected.get("turnover_time_min"),
            1,
            " min",
        ),
    )


# ============================================================
# MAIN ANALYSIS TABS
# ============================================================

tab_overview, tab_scaleup, tab_validation, tab_visual, tab_data = st.tabs(
    [
        "Engineering Overview",
        "Scale-Up",
        "Validation",
        "3D Reactor",
        "Engineering Data",
    ]
)


# ============================================================
# ENGINEERING OVERVIEW
# ============================================================

with tab_overview:

    left, right = st.columns([1.05, 1])

    with left:

        st.subheader("Reactor Geometry")

        geometry_df = pd.DataFrame(
            [
                [
                    "Working Volume",
                    fmt(selected["working_volume_m3"], 3, " m³"),
                ],
                [
                    "Total Volume",
                    fmt(selected["total_volume_m3"], 3, " m³"),
                ],
                [
                    "Fill",
                    fmt(selected["fill_percent"], 1, " %"),
                ],
                [
                    "Tank ID",
                    fmt(selected["tank_diameter_m"], 3, " m"),
                ],
                [
                    "Straight Side",
                    fmt(selected["straight_height_m"], 3, " m"),
                ],
                [
                    "Liquid Height",
                    fmt(selected["liquid_height_m"], 3, " m"),
                ],
                [
                    "Bottom",
                    selected["bottom_type"],
                ],
                [
                    "Top",
                    selected["top_type"],
                ],
            ],
            columns=["Parameter", "Value"],
        )

        st.dataframe(
            geometry_df,
            use_container_width=True,
            hide_index=True,
        )

    with right:

        st.subheader("Agitation System")

        agitation_df = pd.DataFrame(
            [
                [
                    "Agitator",
                    selected["agitator"],
                ],
                [
                    "Flow Pattern",
                    AGITATORS[selected["agitator"]].get(
                        "flow",
                        "N/A",
                    ),
                ],
                [
                    "Operating RPM",
                    fmt(selected["rpm"], 1, " rpm"),
                ],
                [
                    "Impeller Diameter",
                    fmt(
                        selected["impeller_diameter_m"],
                        3,
                        " m",
                    ),
                ],
                [
                    "Number of Impellers",
                    str(selected["number_impellers"]),
                ],
                [
                    "Clearance",
                    fmt(
                        selected["clearance_m"],
                        3,
                        " m",
                    ),
                ],
                [
                    "Power Number",
                    fmt(
                        selected.get("Np"),
                        3,
                    ),
                ],
                [
                    "Pumping Number",
                    fmt(
                        selected.get("Nq"),
                        3,
                    ),
                ],
            ],
            columns=["Parameter", "Value"],
        )

        st.dataframe(
            agitation_df,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Mixing Regime")

    regime = selected.get(
        "mixing_regime",
        "Not available",
    )

    if regime == "Turbulent":
        st.success(
            f"Mixing regime: **{regime}**"
        )
    elif regime == "Transitional":
        st.warning(
            f"Mixing regime: **{regime}**"
        )
    elif regime == "Laminar":
        st.warning(
            f"Mixing regime: **{regime}**"
        )
    else:
        st.info(
            f"Mixing regime: **{regime}**"
        )

    st.subheader("Engineering Interpretation")

    if process_type in [
        "Liquid–Liquid",
        "General Blending",
    ]:

        st.write(
            f"""
            The selected configuration should be evaluated primarily
            through circulation intensity and experimentally validated
            blend time. Current Q/V is
            **{fmt(selected.get("qv_1_h"), 2, " 1/h")}**
            and P/V is
            **{fmt(selected.get("power_volume"), 1, " W/m³")}**.
            """
        )

    elif process_type == "Solid–Liquid":

        st.write(
            """
            Suspension quality is the governing consideration.
            P/V alone should not be used as proof of adequate suspension.
            A validated Njs correlation or plant observation should be
            used to establish the minimum suspension speed.
            """
        )

    elif process_type in [
        "Gas–Liquid",
        "Gas–Liquid–Solid",
    ]:

        st.write(
            """
            Gas dispersion and mass transfer should govern the final
            scale-up decision. P/V and tip speed are useful screening
            parameters but kLa must be validated experimentally.
            """
        )

    elif process_type == "High Viscosity":

        st.write(
            f"""
            Torque and power loading become critical. Current estimated
            shaft torque is
            **{fmt(selected.get("torque_nm"), 1, " N·m")}**.
            Check gearbox, shaft and mechanical seal loading at the
            selected operating condition.
            """
        )

    elif process_type == "Heat-Controlled Reaction":

        st.write(
            """
            Mixing performance should be evaluated together with heat
            transfer capacity. Adequate P/V does not guarantee adequate
            heat removal. Verify U, available area, utility temperature
            and process ΔT separately.
            """
        )

    else:

        st.write(
            """
            Use the calculated hydrodynamic parameters as engineering
            screening indicators and correlate them with actual process
            performance before finalizing scale-up.
            """
        )


# ============================================================
# SCALE-UP
# ============================================================

with tab_scaleup:

    st.subheader("Scale-Up Engineering")

    if len(reactors) < 2:

        st.info(
            "Select Reference → Target or Multi-Reactor Comparison "
            "to perform a scale-up analysis."
        )

    else:

        names = list(reactors.keys())

        if "Reference" in reactors and "Target" in reactors:

            reference_name = "Reference"
            target_name = "Target"

        else:

            reference_name = st.selectbox(
                "Reference reactor",
                names,
                key="scale_reference",
            )

            target_options = [
                n for n in names
                if n != reference_name
            ]

            target_name = st.selectbox(
                "Target reactor",
                target_options,
                key="scale_target",
            )

        reference = reactors[reference_name]
        target = reactors[target_name]

        st.markdown("#### Scale-Up Summary")

        s1, s2, s3, s4 = st.columns(4)

        volume_ratio = (
            target["working_volume_m3"]
            / reference["working_volume_m3"]
            if reference["working_volume_m3"] > 0
            else None
        )

        tank_ratio = (
            target["tank_diameter_m"]
            / reference["tank_diameter_m"]
            if reference["tank_diameter_m"] > 0
            else None
        )

        impeller_ratio = (
            target["impeller_diameter_m"]
            / reference["impeller_diameter_m"]
            if reference["impeller_diameter_m"] > 0
            else None
        )

        with s1:
            st.metric(
                "Volume Scale",
                fmt(volume_ratio, 2, " ×"),
            )

        with s2:
            st.metric(
                "Tank Diameter",
                fmt(tank_ratio, 2, " ×"),
            )

        with s3:
            st.metric(
                "Impeller Diameter",
                fmt(impeller_ratio, 2, " ×"),
            )

        with s4:
            st.metric(
                "Selected Basis",
                scale_basis,
            )

        st.divider()

        # ----------------------------------------------------
        # CALCULATED RPM
        # ----------------------------------------------------

        calculated_rpm = local_scaleup_rpm(
            reference,
            target,
            scale_basis,
        )

        st.markdown("#### Calculated Target Operating Speed")

        if calculated_rpm is None:

            st.warning(
                f"No direct universal RPM equation is implemented "
                f"for **{scale_basis}**."
            )

        else:

            r1, r2, r3 = st.columns(3)

            with r1:
                st.metric(
                    "Reference RPM",
                    fmt(reference["rpm"], 1, " rpm"),
                )

            with r2:
                st.metric(
                    "Calculated Target RPM",
                    fmt(calculated_rpm, 1, " rpm"),
                )

            with r3:
                rpm_change = (
                    (
                        calculated_rpm
                        / reference["rpm"]
                        - 1
                    )
                    * 100
                    if reference["rpm"] > 0
                    else 0
                )

                st.metric(
                    "RPM Change",
                    f"{rpm_change:+.1f} %",
                )

        st.divider()

        # ----------------------------------------------------
        # PERFORMANCE COMPARISON
        # ----------------------------------------------------

        st.markdown("#### Reference vs Target Performance")

        comparison = pd.DataFrame(
            [
                [
                    "Working Volume",
                    fmt(
                        reference["working_volume_m3"],
                        3,
                        " m³",
                    ),
                    fmt(
                        target["working_volume_m3"],
                        3,
                        " m³",
                    ),
                ],
                [
                    "Tank ID",
                    fmt(
                        reference["tank_diameter_m"],
                        3,
                        " m",
                    ),
                    fmt(
                        target["tank_diameter_m"],
                        3,
                        " m",
                    ),
                ],
                [
                    "Impeller Diameter",
                    fmt(
                        reference["impeller_diameter_m"],
                        3,
                        " m",
                    ),
                    fmt(
                        target["impeller_diameter_m"],
                        3,
                        " m",
                    ),
                ],
                [
                    "RPM",
                    fmt(reference["rpm"], 1, " rpm"),
                    fmt(target["rpm"], 1, " rpm"),
                ],
                [
                    "Tip Speed",
                    fmt(
                        reference.get("tip_speed"),
                        2,
                        " m/s",
                    ),
                    fmt(
                        target.get("tip_speed"),
                        2,
                        " m/s",
                    ),
                ],
                [
                    "P/V",
                    fmt(
                        reference.get("power_volume"),
                        1,
                        " W/m³",
                    ),
                    fmt(
                        target.get("power_volume"),
                        1,
                        " W/m³",
                    ),
                ],
                [
                    "Q/V",
                    fmt(
                        reference.get("qv_1_h"),
                        2,
                        " 1/h",
                    ),
                    fmt(
                        target.get("qv_1_h"),
                        2,
                        " 1/h",
                    ),
                ],
                [
                    "Reynolds",
                    (
                        f"{safe_float(reference.get('Re')):,.0f}"
                        if reference.get("Re") is not None
                        else "—"
                    ),
                    (
                        f"{safe_float(target.get('Re')):,.0f}"
                        if target.get("Re") is not None
                        else "—"
                    ),
                ],
                [
                    "Torque",
                    fmt(
                        reference.get("torque_nm"),
                        1,
                        " N·m",
                    ),
                    fmt(
                        target.get("torque_nm"),
                        1,
                        " N·m",
                    ),
                ],
            ],
            columns=[
                "Parameter",
                reference_name,
                target_name,
            ],
        )

        st.dataframe(
            comparison,
            use_container_width=True,
            hide_index=True,
        )

        # ----------------------------------------------------
        # SCALE-UP DEVIATION
        # ----------------------------------------------------

        st.markdown("#### Scale-Up Deviation")

        d1, d2, d3 = st.columns(3)

        ref_pv = reference.get("power_volume")
        tar_pv = target.get("power_volume")

        ref_qv = reference.get("qv_1_h")
        tar_qv = target.get("qv_1_h")

        ref_tip = reference.get("tip_speed")
        tar_tip = target.get("tip_speed")

        pv_dev = (
            (tar_pv / ref_pv - 1) * 100
            if ref_pv and tar_pv and ref_pv > 0
            else None
        )

        qv_dev = (
            (tar_qv / ref_qv - 1) * 100
            if ref_qv and tar_qv and ref_qv > 0
            else None
        )

        tip_dev = (
            (tar_tip / ref_tip - 1) * 100
            if ref_tip and tar_tip and ref_tip > 0
            else None
        )

        with d1:
            st.metric(
                "P/V Deviation",
                fmt(pv_dev, 1, " %"),
            )

        with d2:
            st.metric(
                "Q/V Deviation",
                fmt(qv_dev, 1, " %"),
            )

        with d3:
            st.metric(
                "Tip-Speed Deviation",
                fmt(tip_dev, 1, " %"),
            )

        st.info(
            """
            A low deviation from the selected scale-up criterion is
            desirable, but it is not by itself proof of process equivalence.
            Confirm mixing performance using process-specific validation data.
            """
        )


# ============================================================
# VALIDATION
# ============================================================

with tab_validation:

    st.subheader("Engineering Validation")

    validation_data = {
        **selected,
        "D_T": (
            selected["tank_diameter_m"] /
            selected["tank_diameter_m"]
        ),
        "C_T": selected.get("clearance_T"),
    }

    checks = validation_summary(validation_data)

    if not checks:

        st.info(
            "No validation checks were returned by the current validation module."
        )

    else:

        passed = 0
        failed = 0

        rows = []

        for item in checks:

            try:
                name, ok, message = item
            except Exception:
                continue

            if ok:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "REVIEW"

            rows.append(
                [
                    status,
                    name,
                    message,
                ]
            )

        if failed == 0:
            st.success(
                f"Engineering screening status: READY — {passed} checks passed."
            )
        else:
            st.warning(
                f"Engineering screening status: REVIEW — "
                f"{passed} passed, {failed} require review."
            )

        validation_df = pd.DataFrame(
            rows,
            columns=[
                "Status",
                "Check",
                "Engineering Comment",
            ],
        )

        st.dataframe(
            validation_df,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Design Review Notes")

    notes = []

    fill = selected.get("fill_percent")

    if fill is not None:

        if 20 <= fill <= 85:
            notes.append(
                "Working fill is within the current screening window."
            )
        else:
            notes.append(
                "Working fill should be reviewed against vessel geometry and process requirements."
            )

    dt = (
        selected["tank_diameter_m"]
        if selected["tank_diameter_m"] > 0
        else 1
    )

    impeller_dt = (
        selected["impeller_diameter_m"] / dt
    )

    if 0.20 <= impeller_dt <= 0.90:
        notes.append(
            "Impeller-to-tank diameter ratio is within a practical screening range."
        )
    else:
        notes.append(
            "Impeller-to-tank diameter ratio requires engineering review."
        )

    if selected.get("mixing_regime") == "Laminar":
        notes.append(
            "Laminar operation requires an agitator and geometry specifically suited to viscous mixing."
        )

    if selected.get("torque_nm"):
        notes.append(
            f"Estimated shaft torque is {selected['torque_nm']:.1f} N·m; "
            "mechanical drive sizing should be checked separately."
        )

    for note in notes:
        st.write(f"• {note}")


# ============================================================
# 3D VISUALIZATION
# ============================================================

with tab_visual:

    st.subheader("3D Reactor Visualization")

    if create_reactor_animation is None:

        st.warning(
            "The 3D visualization module could not be imported."
        )

    else:

        st.caption(
            "Conceptual engineering visualization — not CFD."
        )

        try:

            fig = create_reactor_animation(
                selected["tank_diameter_m"],
                selected["straight_height_m"],
                selected["bottom_type"],
                selected["top_type"],
                selected["liquid_height_m"],
                selected["agitator"],
                selected["impeller_diameter_m"],
                selected["number_impellers"],
                selected["rpm"],
                4,
                0.0,
                36,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        except Exception as exc:

            st.error(
                f"3D visualization could not be generated: {exc}"
            )

            st.info(
                "The calculation dashboard remains fully functional."
            )


# ============================================================
# ENGINEERING DATA
# ============================================================

with tab_data:

    st.subheader("Engineering Data")

    engineering_rows = [
        ("Project", project_name),
        ("Process Type", process_type),
        ("Scale-Up Basis", scale_basis),
        ("Reactor", selected_name),

        ("Working Volume", fmt(selected.get("working_volume_m3"), 3, " m³")),
        ("Total Volume", fmt(selected.get("total_volume_m3"), 3, " m³")),
        ("Fill", fmt(selected.get("fill_percent"), 1, " %")),

        ("Tank Diameter", fmt(selected.get("tank_diameter_m"), 3, " m")),
        ("Straight Height", fmt(selected.get("straight_height_m"), 3, " m")),
        ("Liquid Height", fmt(selected.get("liquid_height_m"), 3, " m")),

        ("Bottom Head", selected.get("bottom_type")),
        ("Top Head", selected.get("top_type")),

        ("Agitator", selected.get("agitator")),
        ("Number of Impellers", selected.get("number_impellers")),
        ("Impeller Diameter", fmt(selected.get("impeller_diameter_m"), 3, " m")),
        ("Impeller D/T", fmt(selected.get("impeller_D_T"), 3)),

        ("RPM", fmt(selected.get("rpm"), 1, " rpm")),
        ("Tip Speed", fmt(selected.get("tip_speed"), 3, " m/s")),

        ("Density", fmt(selected.get("density_kg_m3"), 1, " kg/m³")),
        ("Viscosity", fmt(selected.get("viscosity_pa_s"), 5, " Pa·s")),
        ("Surface Tension", fmt(selected.get("surface_tension_n_m"), 4, " N/m")),

        ("Reynolds Number", (
            f"{safe_float(selected.get('Re')):,.0f}"
            if selected.get("Re") is not None
            else "—"
        )),

        ("Froude Number", fmt(selected.get("Fr"), 5)),

        ("Power Number", fmt(selected.get("Np"), 3)),
        ("Pumping Number", fmt(selected.get("Nq"), 3)),

        ("Shaft Power", fmt(selected.get("power_kw"), 3, " kW")),
        ("P/V", fmt(selected.get("power_volume"), 2, " W/m³")),
        ("P/V", fmt(selected.get("pv_kw_m3"), 4, " kW/m³")),

        ("Pumping Rate", fmt(selected.get("pumping_m3_h"), 2, " m³/h")),
        ("Q/V", fmt(selected.get("qv_1_h"), 3, " 1/h")),
        ("Turnover Time", fmt(selected.get("turnover_time_min"), 2, " min")),

        ("Torque", fmt(selected.get("torque_nm"), 2, " N·m")),
        ("Mixing Regime", selected.get("mixing_regime")),
    ]

    data_df = pd.DataFrame(
        engineering_rows,
        columns=[
            "Engineering Parameter",
            "Value",
        ],
    )

    st.dataframe(
        data_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download Engineering Data CSV",
        data=data_df.to_csv(index=False).encode("utf-8"),
        file_name="reactor_engineering_data.csv",
        mime="text/csv",
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Reactor Scale-Up Engineering Studio • "
    "Engineering screening calculations only • "
    "Final design requires process validation, mechanical design review "
    "and vendor/plant confirmation."
)
