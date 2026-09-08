import math
from html import escape

import pandas as pd
import streamlit as st

from calculations.engine import calculate_reactor
from calculations.validation import validate_reactor

try:
    from calculations.scaleup import calculate_scaleup
except Exception:
    calculate_scaleup = None

from libraries.agitator_geometry import AGITATORS
from libraries.reactor_geometry import (
    REACTOR_HEADS,
    calculate_total_volume,
    liquid_height_from_volume,
)

try:
    from visualization.reactor_3d import create_reactor_animation
except Exception:
    create_reactor_animation = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ENGINEERING THEME
# ============================================================

st.markdown(
    """
<style>

:root {
    --bg: #07111f;
    --panel: #0d1b2a;
    --panel2: #102337;
    --border: #1f3a52;
    --text: #e8f0f7;
    --muted: #8fa7bb;
    --accent: #36c5f0;
    --accent2: #61dafb;
    --green: #35d07f;
    --amber: #f5b942;
    --red: #ff6b6b;
}

.stApp {
    background:
        radial-gradient(circle at 75% 5%, rgba(54,197,240,0.08), transparent 28%),
        radial-gradient(circle at 10% 20%, rgba(97,218,251,0.05), transparent 25%),
        var(--bg);
    color: var(--text);
}

.block-container {
    max-width: 1650px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

html, body, [class*="css"] {
    font-family:
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;
}

h1, h2, h3, h4 {
    color: var(--text) !important;
}

p, span, label {
    color: inherit;
}

/* ------------------------------------------------------------
   SIDEBAR
------------------------------------------------------------ */

[data-testid="stSidebar"] {
    background: #06101c;
    border-right: 1px solid #173149;
}

[data-testid="stSidebar"] * {
    color: #d9e7f1;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* ------------------------------------------------------------
   INPUTS
------------------------------------------------------------ */

div[data-baseweb="input"],
div[data-baseweb="select"] > div {
    background: #0c1c2c !important;
    border: 1px solid #28465e !important;
    border-radius: 9px !important;
}

input {
    color: #f4f8fb !important;
    background: transparent !important;
}

div[data-baseweb="select"] * {
    color: #f4f8fb !important;
}

[data-testid="stWidgetLabel"] p,
label {
    color: #b9cada !important;
    font-weight: 650 !important;
}

/* ------------------------------------------------------------
   BUTTONS
------------------------------------------------------------ */

.stButton > button {
    width: 100%;
    min-height: 44px;
    border-radius: 9px;
    border: 1px solid #2a5874;
    background: linear-gradient(135deg, #0e3148, #123e58);
    color: white !important;
    font-weight: 750;
}

.stButton > button:hover {
    border-color: var(--accent);
    color: white !important;
}

/* ------------------------------------------------------------
   TABS
------------------------------------------------------------ */

div[data-baseweb="tab-list"] {
    background: #0b1928;
    border: 1px solid #1d374d;
    border-radius: 12px;
    padding: 5px;
    gap: 5px;
}

button[data-baseweb="tab"] {
    color: #90a8ba !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #15384e !important;
    color: #ffffff !important;
}

/* ------------------------------------------------------------
   METRIC CARDS
------------------------------------------------------------ */

.engineering-card {
    background:
        linear-gradient(
            145deg,
            rgba(16,35,55,0.98),
            rgba(9,25,40,0.98)
        );
    border: 1px solid #1f4058;
    border-radius: 14px;
    padding: 16px 17px;
    min-height: 118px;
    box-shadow:
        0 10px 30px rgba(0,0,0,0.18),
        inset 0 1px 0 rgba(255,255,255,0.025);
    margin-bottom: 10px;
}

.engineering-card:hover {
    border-color: #2f6585;
}

.metric-label {
    color: #86a1b5;
    font-size: 0.78rem;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 9px;
}

.metric-value {
    color: #f5f9fc;
    font-size: 1.55rem;
    font-weight: 850;
    line-height: 1.1;
    overflow-wrap: anywhere;
}

.metric-unit {
    color: #6f8da3;
    font-size: 0.78rem;
    font-weight: 650;
    margin-top: 6px;
}

/* ------------------------------------------------------------
   HERO
------------------------------------------------------------ */

.hero {
    border: 1px solid #1e4057;
    border-radius: 20px;
    padding: 25px 28px;
    margin-bottom: 18px;
    background:
        linear-gradient(
            135deg,
            #0b1d2d 0%,
            #102d43 55%,
            #0a1b2b 100%
        );
    box-shadow: 0 15px 40px rgba(0,0,0,0.22);
}

.hero-title {
    font-size: 2.25rem;
    font-weight: 850;
    color: white;
    letter-spacing: -0.04em;
}

.hero-subtitle {
    color: #91aec1;
    margin-top: 5px;
    font-size: 0.98rem;
}

.hero-chip {
    display: inline-block;
    margin-top: 16px;
    margin-right: 7px;
    padding: 5px 10px;
    border-radius: 999px;
    background: #12364b;
    border: 1px solid #24566e;
    color: #9edff5;
    font-size: 0.72rem;
    font-weight: 750;
}

/* ------------------------------------------------------------
   SECTION
------------------------------------------------------------ */

.section-title {
    margin-top: 18px;
    margin-bottom: 9px;
    font-size: 1.08rem;
    font-weight: 820;
    color: #dceaf4;
}

.section-subtitle {
    color: #718ca1;
    font-size: 0.82rem;
    margin-bottom: 13px;
}

/* ------------------------------------------------------------
   ENGINEERING DECISION
------------------------------------------------------------ */

.decision {
    border: 1px solid #24516a;
    background:
        linear-gradient(
            135deg,
            rgba(15,48,67,0.85),
            rgba(11,30,46,0.92)
        );
    border-radius: 15px;
    padding: 18px 20px;
    margin: 10px 0 15px 0;
}

.decision-title {
    color: #8edcf4;
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-weight: 850;
}

.decision-main {
    color: #ffffff;
    font-size: 1.15rem;
    font-weight: 800;
    margin-top: 5px;
}

.decision-note {
    color: #8fa9ba;
    font-size: 0.82rem;
    margin-top: 7px;
}

/* ------------------------------------------------------------
   STATUS
------------------------------------------------------------ */

.status {
    display: inline-block;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: 0.73rem;
    font-weight: 850;
    letter-spacing: 0.05em;
}

.status-pass {
    background: rgba(53,208,127,0.13);
    color: #55e795;
    border: 1px solid rgba(53,208,127,0.35);
}

.status-review {
    background: rgba(245,185,66,0.12);
    color: #f8c95e;
    border: 1px solid rgba(245,185,66,0.35);
}

.status-fail {
    background: rgba(255,107,107,0.12);
    color: #ff8888;
    border: 1px solid rgba(255,107,107,0.35);
}

/* ------------------------------------------------------------
   TABLE
------------------------------------------------------------ */

[data-testid="stDataFrame"] {
    border: 1px solid #1c394f;
    border-radius: 12px;
}

/* ------------------------------------------------------------
   ALERTS
------------------------------------------------------------ */

[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ------------------------------------------------------------
   EXPANDER
------------------------------------------------------------ */

[data-testid="stExpander"] {
    border: 1px solid #1d394f !important;
    border-radius: 12px !important;
    background: rgba(10,27,43,0.55);
}

/* ------------------------------------------------------------
   DIVIDER
------------------------------------------------------------ */

hr {
    border-color: #173248 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# CONSTANTS / CONFIGURATION
# ============================================================

PROCESS_TYPES = [
    "General Mixing",
    "Liquid-Liquid",
    "Solid-Liquid",
    "Gas-Liquid",
    "Gas-Liquid-Solid",
    "Crystallization",
    "High-Viscosity",
]

SUPPORTED_SCALEUP_BASES = [
    "Constant P/V",
    "Constant Tip Speed",
    "Constant RPM",
]

PROCESS_GUIDANCE = {
    "General Mixing": {
        "primary": "P/V + Q/V + blend performance",
        "secondary": "Tip speed, Re, Fr, D/T, H/T",
    },
    "Liquid-Liquid": {
        "primary": "Q/V + blend time",
        "secondary": "P/V, tip speed, Re and dispersion",
    },
    "Solid-Liquid": {
        "primary": "N/Njs",
        "secondary": "P/V, Q/V, clearance and solids properties",
    },
    "Gas-Liquid": {
        "primary": "Gas dispersion + kLa",
        "secondary": "P/V, superficial gas velocity and tip speed",
    },
    "Gas-Liquid-Solid": {
        "primary": "N/Njs + gas dispersion",
        "secondary": "P/V, Q/V, Ug and kLa",
    },
    "Crystallization": {
        "primary": "Suspension + controlled shear",
        "secondary": "P/V, tip speed, Re and crystal quality",
    },
    "High-Viscosity": {
        "primary": "Torque + P/V",
        "secondary": "Re, tip speed and mechanical loading",
    },
}


# ============================================================
# HELPERS
# ============================================================

def fmt(value, decimals=2):
    if value is None:
        return "—"

    try:
        if isinstance(value, str):
            return value

        return f"{float(value):,.{decimals}f}"

    except Exception:
        return "—"


def first_value(data, keys, default=None):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]

    return default


def metric_card(label, value, unit="", decimals=2):
    if isinstance(value, str):
        display = escape(value)
    elif value is None:
        display = "—"
    else:
        display = fmt(value, decimals)

    st.markdown(
        f"""
        <div class="engineering-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{display}</div>
            <div class="metric-unit">{escape(unit)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_chip(status):
    status = str(status).upper()

    if status in ("PASS", "READY", "OK"):
        css = "status-pass"
        text = "READY"
    elif status in ("FAIL", "RISK", "ERROR"):
        css = "status-fail"
        text = "RISK"
    else:
        css = "status-review"
        text = "REVIEW"

    st.markdown(
        f'<span class="status {css}">{text}</span>',
        unsafe_allow_html=True,
    )


def get_validation_status(validation):
    if not validation:
        return "REVIEW"

    overall = str(validation.get("overall", "")).upper()

    if overall in ("PASS", "OK"):
        return "PASS"

    if overall in ("FAIL", "RISK", "ERROR"):
        return "FAIL"

    return "REVIEW"


def calculate_fill_percentage(volume, vessel_volume):
    if vessel_volume is None or vessel_volume <= 0:
        return 0.0

    return 100.0 * volume / vessel_volume


def calculate_derived_metrics(result):
    """
    Recalculate important engineering KPIs from fundamental quantities
    when possible.

    This deliberately makes P/V visible even if a future calculation
    engine changes its dictionary key.
    """

    volume = first_value(
        result,
        ["working_volume", "volume_m3", "volume"],
    )

    power_w = first_value(
        result,
        ["power_w"],
    )

    power_kw = first_value(
        result,
        ["power_kw"],
    )

    if power_w is None and power_kw is not None:
        power_w = float(power_kw) * 1000.0

    if power_w is not None and volume and volume > 0:
        pv_w_m3 = power_w / volume
        result["power_volume"] = pv_w_m3
        result["power_per_volume"] = pv_w_m3
        result["power_volume_kw_m3"] = pv_w_m3 / 1000.0

    elif power_kw is not None and volume and volume > 0:
        pv_kw_m3 = float(power_kw) / volume
        result["power_volume_kw_m3"] = pv_kw_m3
        result["power_volume"] = pv_kw_m3 * 1000.0
        result["power_per_volume"] = pv_kw_m3 * 1000.0

    # Q/V
    q_m3_h = first_value(
        result,
        ["pumping_m3_h", "pumping_capacity_m3_h"],
    )

    if q_m3_h is not None and volume and volume > 0:
        result["qv_1_h"] = float(q_m3_h) / volume

        if result["qv_1_h"] > 0:
            result["turnover_time_min"] = 60.0 / result["qv_1_h"]

    # Tip speed
    D = first_value(
        result,
        ["impeller_diameter_m"],
    )

    rpm = first_value(
        result,
        ["rpm"],
    )

    if D and rpm:
        N = float(rpm) / 60.0

        result["tip_speed"] = math.pi * D * N

        if volume:
            result["Fr"] = N**2 * D / 9.81

    # Torque
    if power_w is not None and rpm and rpm > 0:
        N = float(rpm) / 60.0

        result["torque_nm"] = power_w / (2.0 * math.pi * N)

    return result


def engineering_regime(re):
    if re is None:
        return "—"

    if re < 10:
        return "Laminar"

    if re < 10000:
        return "Transitional"

    return "Turbulent"


def get_njs_ratio(result):
    njs = first_value(
        result,
        [
            "njs_rpm",
            "Njs",
            "system_njs_rpm",
            "njs",
        ],
    )

    rpm = first_value(result, ["rpm"])

    if njs and rpm and float(njs) > 0:
        return float(rpm) / float(njs)

    return None


def engineering_decision(process_type, result):
    guidance = PROCESS_GUIDANCE.get(
        process_type,
        PROCESS_GUIDANCE["General Mixing"],
    )

    pv = first_value(
        result,
        ["power_volume"],
    )

    qv = first_value(
        result,
        ["qv_1_h"],
    )

    re = first_value(
        result,
        ["Re", "reynolds_number"],
    )

    decision = guidance["primary"]

    notes = [
        f"Primary criterion: {guidance['primary']}.",
        f"Secondary checks: {guidance['secondary']}.",
    ]

    if pv is not None:
        notes.append(
            f"P/V = {fmt(pv, 1)} W/m³ "
            f"({fmt(pv / 1000.0, 3)} kW/m³)."
        )

    if qv is not None:
        notes.append(
            f"Q/V = {fmt(qv, 2)} h⁻¹."
        )

    if re is not None:
        notes.append(
            f"Re = {re:.2e} "
            f"({engineering_regime(re)} regime)."
        )

    return decision, " ".join(notes)


def validate_and_summarize(result):
    try:
        checks = validate_reactor(result)
    except Exception as exc:
        return "REVIEW", [], [f"Validation calculation unavailable: {exc}"]

    failures = []
    warnings = []

    for item in checks:
        if len(item) < 3:
            continue

        name, ok, message = item

        if ok:
            continue

        warnings.append(
            f"{name}: {message}"
        )

    if failures:
        return "FAIL", checks, failures + warnings

    if warnings:
        return "REVIEW", checks, warnings

    return "PASS", checks, []


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="hero">
    <div class="hero-title">⚗️ Reactor Scale-Up Engineering Studio</div>
    <div class="hero-subtitle">
        Engineering-first reactor design, mixing analysis, similarity scaling,
        validation and 3D process visualization.
    </div>

    <span class="hero-chip">REACTOR GEOMETRY</span>
    <span class="hero-chip">AGITATION</span>
    <span class="hero-chip">P/V</span>
    <span class="hero-chip">Q/V</span>
    <span class="hero-chip">SCALE-UP</span>
    <span class="hero-chip">VALIDATION</span>
    <span class="hero-chip">3D</span>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚗️ Engineering Studio")

    st.caption(
        "Reactor scale-up & mixing engineering"
    )

    st.divider()

    project_name = st.text_input(
        "Project",
        "Reactor Scale-Up Study",
    )

    prepared_by = st.text_input(
        "Prepared By",
        "Process Engineering",
    )

    study_mode = st.selectbox(
        "Study Configuration",
        [
            "Single Reactor",
            "Lab vs Pilot",
            "Pilot vs Commercial",
            "Lab vs Commercial",
            "Lab vs Pilot vs Commercial",
        ],
    )

    process_type = st.selectbox(
        "Process Type",
        PROCESS_TYPES,
    )

    st.divider()

    st.markdown("### Engineering Basis")

    st.info(
        f"**Primary:** "
        f"{PROCESS_GUIDANCE[process_type]['primary']}\n\n"
        f"**Secondary:** "
        f"{PROCESS_GUIDANCE[process_type]['secondary']}"
    )

    st.caption(
        "Scale-up is not based on RPM alone. "
        "Use process-specific similarity criteria and validate against "
        "pilot data/vendor correlations."
    )


# ============================================================
# REACTOR NAMES
# ============================================================

MODE_REACTORS = {
    "Single Reactor": ["Reactor"],
    "Lab vs Pilot": ["Lab", "Pilot"],
    "Pilot vs Commercial": ["Pilot", "Commercial"],
    "Lab vs Commercial": ["Lab", "Commercial"],
    "Lab vs Pilot vs Commercial": [
        "Lab",
        "Pilot",
        "Commercial",
    ],
}

reactor_names = MODE_REACTORS[study_mode]


# ============================================================
# MAIN NAVIGATION
# ============================================================

navigation = st.radio(
    "Engineering Workspace",
    [
        "Design Basis",
        "Mixing Engineering",
        "Scale-Up",
        "Validation",
        "3D Reactor",
    ],
    horizontal=True,
    label_visibility="collapsed",
)


# ============================================================
# REACTOR INPUT
# ============================================================

def reactor_input(name):

    defaults = {
        "Lab": {
            "volume": 1.0,
            "diameter": 1.0,
            "height": 1.5,
            "rpm": 150.0,
        },
        "Pilot": {
            "volume": 10.0,
            "diameter": 2.0,
            "height": 2.5,
            "rpm": 120.0,
        },
        "Commercial": {
            "volume": 50.0,
            "diameter": 3.0,
            "height": 4.0,
            "rpm": 90.0,
        },
        "Reactor": {
            "volume": 10.0,
            "diameter": 2.0,
            "height": 2.5,
            "rpm": 100.0,
        },
    }

    d = defaults.get(
        name,
        defaults["Reactor"],
    )

    with st.container():

        st.markdown(
            f"### 🏭 {name} Reactor"
        )

        # ----------------------------------------------------
        # PROCESS
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Process & Fluid Properties</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-subtitle">'
            'Fundamental process inputs used by the mixing correlations.'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            V = st.number_input(
                "Working Volume",
                min_value=0.001,
                max_value=5000.0,
                value=float(d["volume"]),
                step=0.1,
                format="%.3f",
                key=f"{name}_V",
            )

        with c2:
            rho = st.number_input(
                "Liquid Density",
                min_value=0.1,
                max_value=5000.0,
                value=1000.0,
                step=10.0,
                format="%.1f",
                key=f"{name}_rho",
            )

        with c3:
            mu_cP = st.number_input(
                "Viscosity",
                min_value=0.001,
                max_value=100000.0,
                value=1.0,
                step=0.1,
                format="%.3f",
                key=f"{name}_mu",
            )

        with c4:
            sigma_mNm = st.number_input(
                "Surface Tension",
                min_value=0.001,
                max_value=2000.0,
                value=72.0,
                step=0.1,
                format="%.3f",
                key=f"{name}_sigma",
            )

        mu = mu_cP / 1000.0
        sigma = sigma_mNm / 1000.0

        # ----------------------------------------------------
        # VESSEL GEOMETRY
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Vessel Geometry</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            T = st.number_input(
                "Tank ID",
                min_value=0.05,
                max_value=30.0,
                value=float(d["diameter"]),
                step=0.05,
                format="%.3f",
                key=f"{name}_T",
            )

        with c2:
            H = st.number_input(
                "Straight Side Height",
                min_value=0.05,
                max_value=30.0,
                value=float(d["height"]),
                step=0.05,
                format="%.3f",
                key=f"{name}_H",
            )

        with c3:
            bottom = st.selectbox(
                "Bottom Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{name}_bottom",
            )

        with c4:
            top = st.selectbox(
                "Top Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{name}_top",
            )

        vessel_volume = calculate_total_volume(
            D=T,
            straight_height=H,
            bottom_type=bottom,
            top_type=top,
        )

        if V > vessel_volume:

            st.error(
                f"Working volume {V:.3f} m³ exceeds vessel capacity "
                f"{vessel_volume:.3f} m³."
            )

            valid_volume = max(
                0.001,
                vessel_volume * 0.999,
            )

        else:
            valid_volume = V

        liquid_height, _ = liquid_height_from_volume(
            working_volume=valid_volume,
            D=T,
            straight_height=H,
            bottom_type=bottom,
            top_type=top,
        )

        fill = calculate_fill_percentage(
            valid_volume,
            vessel_volume,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            metric_card(
                "Vessel Capacity",
                vessel_volume,
                "m³",
                3,
            )

        with c2:
            metric_card(
                "Liquid Height",
                liquid_height,
                "m",
                3,
            )

        with c3:
            metric_card(
                "Operating Fill",
                fill,
                "%",
                1,
            )

        with c4:
            metric_card(
                "H/T",
                liquid_height / T if T > 0 else None,
                "dimensionless",
                3,
            )

        # ----------------------------------------------------
        # AGITATION
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Agitation System</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            agitator = st.selectbox(
                "Impeller Type",
                list(AGITATORS.keys()),
                index=1 if len(AGITATORS) > 1 else 0,
                key=f"{name}_agitator",
            )

        agitator_data = AGITATORS.get(
            agitator,
            {},
        )

        default_ratio = agitator_data.get(
            "default_diameter_ratio",
            0.33,
        )

        default_D = max(
            0.02,
            round(T * default_ratio, 3),
        )

        with c2:
            D = st.number_input(
                "Impeller Diameter",
                min_value=0.02,
                max_value=15.0,
                value=float(default_D),
                step=0.01,
                format="%.3f",
                key=f"{name}_D",
            )

        with c3:
            rpm = st.number_input(
                "Agitator Speed",
                min_value=0.1,
                max_value=2000.0,
                value=float(d["rpm"]),
                step=1.0,
                format="%.1f",
                key=f"{name}_rpm",
            )

        with c4:
            nimp = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{name}_nimp",
            )

        # ----------------------------------------------------
        # INTERNALS
        # ----------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            baffles = st.number_input(
                "Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{name}_baffles",
            )

        with c2:
            clearance = st.number_input(
                "Bottom Clearance",
                min_value=0.0,
                max_value=10.0,
                value=max(
                    0.05,
                    D * 0.20,
                ),
                step=0.01,
                format="%.3f",
                key=f"{name}_clearance",
            )

        gas_flow = 0.0

        if process_type in (
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ):

            with c3:
                gas_flow = st.number_input(
                    "Gas Flow",
                    min_value=0.0,
                    max_value=100000.0,
                    value=0.0,
                    step=10.0,
                    key=f"{name}_gas",
                )

        try:

            result = calculate_reactor(
                volume_m3=valid_volume,
                tank_diameter_m=T,
                liquid_height_m=liquid_height,
                density_kg_m3=rho,
                viscosity_pa_s=mu,
                surface_tension_n_m=sigma,
                rpm=rpm,
                impeller_diameter_m=D,
                number_impellers=int(nimp),
                agitator=agitator,
                impeller_clearance_m=clearance,
                gas_flow_m3_h=gas_flow,
                bubble_diameter_mm=1.0,
                gas_holdup_fraction=0.05,
            )

        except TypeError:

            # Compatibility with older calculation.engine versions.

            result = calculate_reactor(
                volume_m3=valid_volume,
                tank_diameter_m=T,
                liquid_height_m=liquid_height,
                density_kg_m3=rho,
                viscosity_pa_s=mu,
                surface_tension_n_m=sigma,
                rpm=rpm,
                impeller_diameter_m=D,
                number_impellers=int(nimp),
                agitator=agitator,
                impeller_clearance_m=clearance,
            )

        result.update(
            {
                "name": name,
                "working_volume": valid_volume,
                "vessel_volume": vessel_volume,
                "tank_diameter_m": T,
                "straight_height_m": H,
                "bottom_type": bottom,
                "top_type": top,
                "liquid_height_m": liquid_height,
                "fill_percentage": fill,
                "density": rho,
                "density_kg_m3": rho,
                "viscosity_pa_s": mu,
                "viscosity_mpa_s": mu_cP,
                "surface_tension_n_m": sigma,
                "surface_tension_mn_m": sigma_mNm,
                "rpm": rpm,
                "impeller_diameter_m": D,
                "number_impellers": int(nimp),
                "agitator": agitator,
                "agitator_type": agitator,
                "number_baffles": int(baffles),
                "baffles": int(baffles),
                "impeller_clearance_m": clearance,
                "clearance_m": clearance,
                "gas_flow_m3_h": gas_flow,
                "process_type": process_type,
            }
        )

        result = calculate_derived_metrics(result)

        # Validation
        validation = {}

        try:

            validation_input = dict(result)

            validation_input["fill_percentage"] = fill
            validation_input["D_T"] = (
                D / T if T > 0 else 0
            )
            validation_input["H_T"] = (
                liquid_height / T
                if T > 0
                else 0
            )
            validation_input["clearance_T"] = (
                clearance / T
                if T > 0
                else None
            )
            validation_input["Fr"] = first_value(
                result,
                ["Fr"],
                0.0,
            )
            validation_input["mixing_regime"] = first_value(
                result,
                ["mixing_regime"],
                engineering_regime(
                    first_value(result, ["Re"])
                ),
            )
            validation_input["agitator_type"] = agitator

            validation = validate_reactor(
                validation_input
            )

            result["validation"] = {
                "checks": validation,
                "overall": (
                    "PASS"
                    if all(x[1] for x in validation)
                    else "REVIEW"
                ),
                "failures": sum(
                    1 for x in validation if not x[1]
                ),
                "warnings": 0,
            }

        except Exception:
            result["validation"] = {
                "checks": [],
                "overall": "REVIEW",
                "failures": 0,
                "warnings": 0,
            }

        return result


# ============================================================
# DESIGN BASIS
# ============================================================

if navigation == "Design Basis":

    st.markdown(
        "## Design Basis"
    )

    st.caption(
        "Define the physical system first. "
        "The dashboard then converts the inputs into mixing and scale-up KPIs."
    )

    reactors = {}

    for name in reactor_names:

        with st.expander(
            f"⚗️ {name} — Reactor Design Basis",
            expanded=True,
        ):

            reactors[name] = reactor_input(name)

    st.session_state["reactors"] = reactors
    st.session_state["project_name"] = project_name
    st.session_state["prepared_by"] = prepared_by
    st.session_state["process_type"] = process_type

    st.success(
        "Design basis calculated. Open **Mixing Engineering** to review the engineering KPIs."
    )


# ============================================================
# LOAD RESULTS
# ============================================================

reactors = st.session_state.get(
    "reactors",
    {},
)

if not reactors:

    if navigation != "Design Basis":

        st.info(
            "Start from **Design Basis** and enter the reactor geometry, "
            "fluid properties and agitator configuration."
        )

    st.stop()


# ============================================================
# MIXING ENGINEERING
# ============================================================

if navigation == "Mixing Engineering":

    st.markdown(
        "## Mixing Engineering"
    )

    st.caption(
        "Primary engineering parameters governing reactor circulation, "
        "energy density, hydrodynamics and mechanical loading."
    )

    for name, result in reactors.items():

        status = get_validation_status(
            result.get("validation")
        )

        left, right = st.columns([5, 1])

        with left:

            st.markdown(
                f"### {name}"
            )

        with right:

            status_chip(status)

        # ----------------------------------------------------
        # PRIMARY ENGINEERING KPIs
        # ----------------------------------------------------

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        with c1:
            metric_card(
                "Power / Volume",
                result.get("power_volume"),
                "W/m³",
                1,
            )

        with c2:
            metric_card(
                "P/V",
                (
                    result.get("power_volume") / 1000.0
                    if result.get("power_volume") is not None
                    else None
                ),
                "kW/m³",
                3,
            )

        with c3:
            metric_card(
                "Agitator Power",
                result.get("power_kw"),
                "kW",
                2,
            )

        with c4:
            metric_card(
                "Pumping Capacity",
                result.get("pumping_m3_h"),
                "m³/h",
                1,
            )

        with c5:
            metric_card(
                "Q / V",
                result.get("qv_1_h"),
                "h⁻¹",
                2,
            )

        with c6:
            metric_card(
                "Tip Speed",
                result.get("tip_speed"),
                "m/s",
                2,
            )

        # ----------------------------------------------------
        # HYDRODYNAMIC KPIs
        # ----------------------------------------------------

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        with c1:
            metric_card(
                "Reynolds Number",
                result.get("Re"),
                "dimensionless",
                0,
            )

        with c2:
            metric_card(
                "Froude Number",
                result.get("Fr"),
                "dimensionless",
                4,
            )

        with c3:
            metric_card(
                "Torque",
                result.get("torque_nm"),
                "N·m",
                1,
            )

        with c4:
            metric_card(
                "D / T",
                result.get("D_T"),
                "dimensionless",
                3,
            )

        with c5:
            metric_card(
                "H / T",
                result.get("H_T"),
                "dimensionless",
                3,
            )

        with c6:
            metric_card(
                "C / T",
                result.get("clearance_T"),
                "dimensionless",
                3,
            )

        st.markdown(
            '<div class="decision">',
            unsafe_allow_html=True,
        )

        decision, note = engineering_decision(
            process_type,
            result,
        )

        st.markdown(
            f"""
            <div class="decision-title">
                Engineering Focus
            </div>

            <div class="decision-main">
                {escape(decision)}
            </div>

            <div class="decision-note">
                {escape(note)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # ENGINEERING PARAMETER TABLE
        # ----------------------------------------------------

        with st.expander(
            f"Detailed Engineering Parameters — {name}",
            expanded=False,
        ):

            rows = [
                ["Working Volume", result.get("working_volume"), "m³"],
                ["Vessel Volume", result.get("vessel_volume"), "m³"],
                ["Liquid Height", result.get("liquid_height_m"), "m"],
                ["Tank ID", result.get("tank_diameter_m"), "m"],
                ["Straight Height", result.get("straight_height_m"), "m"],
                ["Impeller Diameter", result.get("impeller_diameter_m"), "m"],
                ["Agitator Speed", result.get("rpm"), "RPM"],
                ["Number of Impellers", result.get("number_impellers"), "-"],
                ["Number of Baffles", result.get("number_baffles"), "-"],
                ["Density", result.get("density_kg_m3"), "kg/m³"],
                ["Viscosity", result.get("viscosity_pa_s"), "Pa·s"],
                ["Surface Tension", result.get("surface_tension_n_m"), "N/m"],
                ["Power", result.get("power_kw"), "kW"],
                ["Power / Volume", result.get("power_volume"), "W/m³"],
                [
                    "Power / Volume",
                    (
                        result.get("power_volume") / 1000.0
                        if result.get("power_volume") is not None
                        else None
                    ),
                    "kW/m³",
                ],
                ["Pumping Capacity", result.get("pumping_m3_h"), "m³/h"],
                ["Q / V", result.get("qv_1_h"), "h⁻¹"],
                ["Turnover Time", result.get("turnover_time_min"), "min"],
                ["Tip Speed", result.get("tip_speed"), "m/s"],
                ["Torque", result.get("torque_nm"), "N·m"],
                ["Reynolds Number", result.get("Re"), "-"],
                ["Froude Number", result.get("Fr"), "-"],
                ["D/T", result.get("D_T"), "-"],
                ["H/T", result.get("H_T"), "-"],
                ["C/T", result.get("clearance_T"), "-"],
            ]

            table = pd.DataFrame(
                rows,
                columns=[
                    "Engineering Parameter",
                    "Value",
                    "Unit",
                ],
            )

            table["Value"] = table["Value"].apply(
                lambda x: fmt(x, 4)
                if isinstance(x, (float, int))
                else x
            )

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# SCALE-UP
# ============================================================

if navigation == "Scale-Up":

    st.markdown(
        "## Scale-Up Engineering"
    )

    st.caption(
        "Compare reference and target reactors using physically meaningful "
        "similarity criteria. RPM alone is not treated as a scale-up basis."
    )

    if len(reactors) < 2:

        st.info(
            "Select a multi-reactor study configuration "
            "such as Lab vs Pilot or Pilot vs Commercial."
        )

    else:

        reference_name = reactor_names[0]
        target_names = reactor_names[1:]

        reference = reactors[reference_name]

        st.markdown(
            f"### {reference_name} → Target"
        )

        # ----------------------------------------------------
        # SCALE-UP BASIS
        # ----------------------------------------------------

        basis = st.selectbox(
            "Primary Scale-Up Criterion",
            SUPPORTED_SCALEUP_BASES,
            help=(
                "These criteria are available in the current scale-up "
                "calculation engine."
            ),
        )

        guidance = PROCESS_GUIDANCE[process_type]

        st.markdown(
            f"""
            <div class="decision">
                <div class="decision-title">
                    Process-Specific Scale-Up Logic
                </div>

                <div class="decision-main">
                    Recommended focus: {escape(guidance["primary"])}
                </div>

                <div class="decision-note">
                    Secondary checks: {escape(guidance["secondary"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # REFERENCE KPI
        # ----------------------------------------------------

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        with c1:
            metric_card(
                "Reference Volume",
                reference.get("working_volume"),
                "m³",
                3,
            )

        with c2:
            metric_card(
                "Reference P/V",
                reference.get("power_volume"),
                "W/m³",
                1,
            )

        with c3:
            metric_card(
                "Reference Q/V",
                reference.get("qv_1_h"),
                "h⁻¹",
                2,
            )

        with c4:
            metric_card(
                "Reference Tip Speed",
                reference.get("tip_speed"),
                "m/s",
                2,
            )

        with c5:
            metric_card(
                "Reference RPM",
                reference.get("rpm"),
                "RPM",
                1,
            )

        with c6:
            metric_card(
                "Reference D/T",
                reference.get("D_T"),
                "-",
                3,
            )

        # ----------------------------------------------------
        # TARGETS
        # ----------------------------------------------------

        for target_name in target_names:

            target = reactors[target_name]

            st.markdown(
                f"### {reference_name} → {target_name}"
            )

            volume_ratio = (
                target["working_volume"]
                / reference["working_volume"]
                if reference["working_volume"] > 0
                else None
            )

            diameter_ratio = (
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

            pv_ratio = None

            if (
                reference.get("power_volume") is not None
                and target.get("power_volume") is not None
                and reference["power_volume"] != 0
            ):

                pv_ratio = (
                    target["power_volume"]
                    / reference["power_volume"]
                )

            qv_ratio = None

            if (
                reference.get("qv_1_h") is not None
                and target.get("qv_1_h") is not None
                and reference["qv_1_h"] != 0
            ):

                qv_ratio = (
                    target["qv_1_h"]
                    / reference["qv_1_h"]
                )

            tip_ratio = None

            if (
                reference.get("tip_speed") is not None
                and target.get("tip_speed") is not None
                and reference["tip_speed"] != 0
            ):

                tip_ratio = (
                    target["tip_speed"]
                    / reference["tip_speed"]
                )

            # ------------------------------------------------
            # SCALE RATIOS
            # ------------------------------------------------

            c1, c2, c3, c4, c5, c6 = st.columns(6)

            with c1:
                metric_card(
                    "Volume Scale",
                    volume_ratio,
                    "×",
                    2,
                )

            with c2:
                metric_card(
                    "Tank Diameter Scale",
                    diameter_ratio,
                    "×",
                    2,
                )

            with c3:
                metric_card(
                    "Impeller Scale",
                    impeller_ratio,
                    "×",
                    2,
                )

            with c4:
                metric_card(
                    "P/V Ratio",
                    pv_ratio,
                    "Target / Reference",
                    3,
                )

            with c5:
                metric_card(
                    "Q/V Ratio",
                    qv_ratio,
                    "Target / Reference",
                    3,
                )

            with c6:
                metric_card(
                    "Tip Speed Ratio",
                    tip_ratio,
                    "Target / Reference",
                    3,
                )

            # ------------------------------------------------
            # CALCULATED SCALE-UP TARGET
            # ------------------------------------------------

            scale_result = {}

            if calculate_scaleup is not None:

                try:

                    scale_result = calculate_scaleup(
                        reference_volume=reference[
                            "working_volume"
                        ],
                        target_volume=target[
                            "working_volume"
                        ],
                        basis=basis,
                        reference_diameter=reference[
                            "tank_diameter_m"
                        ],
                        reference_rpm=reference[
                            "rpm"
                        ],
                        reference_power_per_volume=(
                            reference.get(
                                "power_volume_kw_m3"
                            )
                            if reference.get(
                                "power_volume_kw_m3"
                            ) is not None
                            else (
                                reference.get(
                                    "power_volume",
                                    0,
                                )
                                / 1000.0
                            )
                        ),
                        reference_tip_speed=reference.get(
                            "tip_speed"
                        ),
                    )

                except Exception as exc:

                    scale_result = {
                        "message": str(exc)
                    }

            else:

                scale_result = {
                    "message":
                        "Scale-up module is not available."
                }

            target_rpm = first_value(
                scale_result,
                ["target_rpm"],
            )

            target_tip = first_value(
                scale_result,
                ["target_tip_speed"],
            )

            target_pv = first_value(
                scale_result,
                [
                    "target_power_volume",
                    "target_power_per_volume",
                ],
            )

            target_qv = first_value(
                scale_result,
                [
                    "target_qv",
                    "target_qv_1_h",
                ],
            )

            st.markdown(
                "#### Calculated Scale-Up Target"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                metric_card(
                    "Target RPM",
                    target_rpm,
                    "RPM",
                    1,
                )

            with c2:
                metric_card(
                    "Target Tip Speed",
                    target_tip,
                    "m/s",
                    2,
                )

            with c3:
                metric_card(
                    "Target P/V",
                    target_pv,
                    "engine result",
                    3,
                )

            with c4:
                metric_card(
                    "Target Q/V",
                    target_qv,
                    "engine result",
                    3,
                )

            if scale_result.get("message"):

                st.warning(
                    scale_result["message"]
                )

            # ------------------------------------------------
            # ENGINEERING COMPARISON TABLE
            # ------------------------------------------------

            comparison = pd.DataFrame(
                [
                    [
                        "Working Volume",
                        "m³",
                        reference.get("working_volume"),
                        target.get("working_volume"),
                        volume_ratio,
                    ],
                    [
                        "Tank Diameter",
                        "m",
                        reference.get("tank_diameter_m"),
                        target.get("tank_diameter_m"),
                        diameter_ratio,
                    ],
                    [
                        "Impeller Diameter",
                        "m",
                        reference.get("impeller_diameter_m"),
                        target.get("impeller_diameter_m"),
                        impeller_ratio,
                    ],
                    [
                        "RPM",
                        "RPM",
                        reference.get("rpm"),
                        target.get("rpm"),
                        (
                            target.get("rpm")
                            / reference.get("rpm")
                            if reference.get("rpm")
                            else None
                        ),
                    ],
                    [
                        "Power",
                        "kW",
                        reference.get("power_kw"),
                        target.get("power_kw"),
                        (
                            target.get("power_kw")
                            / reference.get("power_kw")
                            if reference.get("power_kw")
                            else None
                        ),
                    ],
                    [
                        "P/V",
                        "W/m³",
                        reference.get("power_volume"),
                        target.get("power_volume"),
                        pv_ratio,
                    ],
                    [
                        "Q/V",
                        "h⁻¹",
                        reference.get("qv_1_h"),
                        target.get("qv_1_h"),
                        qv_ratio,
                    ],
                    [
                        "Tip Speed",
                        "m/s",
                        reference.get("tip_speed"),
                        target.get("tip_speed"),
                        tip_ratio,
                    ],
                    [
                        "Reynolds Number",
                        "-",
                        reference.get("Re"),
                        target.get("Re"),
                        (
                            target.get("Re")
                            / reference.get("Re")
                            if reference.get("Re")
                            else None
                        ),
                    ],
                    [
                        "D/T",
                        "-",
                        reference.get("D_T"),
                        target.get("D_T"),
                        (
                            target.get("D_T")
                            / reference.get("D_T")
                            if reference.get("D_T")
                            else None
                        ),
                    ],
                ],
                columns=[
                    "Parameter",
                    "Unit",
                    reference_name,
                    target_name,
                    "Target / Reference",
                ],
            )

            st.dataframe(
                comparison,
                use_container_width=True,
                hide_index=True,
            )

            # ------------------------------------------------
            # P/V INTERPRETATION
            # ------------------------------------------------

            if pv_ratio is not None:

                if abs(pv_ratio - 1.0) <= 0.05:

                    st.success(
                        f"P/V similarity: target is "
                        f"{pv_ratio:.3f}× reference. "
                        f"The two reactors are close on an energy-density basis."
                    )

                elif pv_ratio < 0.8 or pv_ratio > 1.2:

                    st.warning(
                        f"P/V deviation: target/reference = "
                        f"{pv_ratio:.3f}. "
                        f"Review whether this deviation is acceptable for "
                        f"the process-specific scale-up objective."
                    )

                else:

                    st.info(
                        f"P/V deviation: target/reference = "
                        f"{pv_ratio:.3f}. "
                        f"Review against pilot performance and process requirements."
                    )


# ============================================================
# VALIDATION
# ============================================================

if navigation == "Validation":

    st.markdown(
        "## Engineering Validation"
    )

    st.caption(
        "Screening checks for vessel geometry, operating fill, "
        "impeller arrangement, baffles and hydrodynamic consistency."
    )

    for name, result in reactors.items():

        validation = result.get(
            "validation",
            {},
        )

        status = get_validation_status(
            validation
        )

        c1, c2, c3 = st.columns([2, 1, 1])

        with c1:
            st.markdown(
                f"### {name}"
            )

        with c2:
            status_chip(status)

        with c3:
            metric_card(
                "Fill",
                result.get("fill_percentage"),
                "%",
                1,
            )

        checks = validation.get(
            "checks",
            [],
        )

        if checks:

            table = pd.DataFrame(
                [
                    [
                        x[0],
                        "PASS" if x[1] else "REVIEW",
                        x[2],
                    ]
                    for x in checks
                ],
                columns=[
                    "Engineering Check",
                    "Status",
                    "Comment",
                ],
            )

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
            )

        # ----------------------------------------------------
        # QUICK ENGINEERING CHECKS
        # ----------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        re = result.get("Re")
        dt = result.get("D_T")
        ht = result.get("H_T")
        ct = result.get("clearance_T")

        with c1:

            if dt is not None:

                if 0.20 <= dt <= 0.90:

                    st.success(
                        f"D/T = {dt:.3f} — within screening range."
                    )

                else:

                    st.warning(
                        f"D/T = {dt:.3f} — review impeller/tank geometry."
                    )

        with c2:

            if ht is not None:

                if ht >= 0.50:

                    st.success(
                        f"H/T = {ht:.3f} — liquid aspect ratio acceptable for screening."
                    )

                else:

                    st.warning(
                        f"H/T = {ht:.3f} — review axial coverage."
                    )

        with c3:

            if ct is not None:

                if 0.05 <= ct <= 0.50:

                    st.success(
                        f"C/T = {ct:.3f} — clearance within screening range."
                    )

                else:

                    st.warning(
                        f"C/T = {ct:.3f} — review impeller clearance."
                    )

        with c4:

            if re is not None:

                st.info(
                    f"Re = {re:.2e} — {engineering_regime(re)}."
                )

        # ----------------------------------------------------
        # PROCESS-SPECIFIC
        # ----------------------------------------------------

        if process_type in (
            "Solid-Liquid",
            "Gas-Liquid-Solid",
            "Crystallization",
        ):

            njs_ratio = get_njs_ratio(
                result
            )

            if njs_ratio is None:

                st.warning(
                    "N/Njs is not available from the current reactor "
                    "calculation result. For solids service, add a validated "
                    "Njs correlation using particle size, solids loading, "
                    "density difference and impeller geometry."
                )

            else:

                metric_card(
                    "N / Njs",
                    njs_ratio,
                    "suspension margin",
                    2,
                )

        if process_type in (
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ):

            st.info(
                "Gas-liquid scale-up requires validated gas dispersion, "
                "flooding/loading and kLa correlations. P/V alone should "
                "not be treated as a complete gas-transfer criterion."
            )


# ============================================================
# 3D REACTOR
# ============================================================

if navigation == "3D Reactor":

    st.markdown(
        "## 3D Reactor & Mixing Visualization"
    )

    st.caption(
        "Interactive engineering visualization of vessel geometry, "
        "liquid level, shaft, impeller and internal arrangement."
    )

    if create_reactor_animation is None:

        st.error(
            "3D visualization module could not be imported."
        )

    else:

        for index, (name, result) in enumerate(
            reactors.items()
        ):

            st.markdown(
                f"### {name}"
            )

            selected_features = st.multiselect(
                "Visualization Features",
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
                    "Baffles",
                    "Mixing Particles",
                ],
                key=f"{name}_features",
            )

            try:

                fig = create_reactor_animation(
                    volume_m3=result.get(
                        "working_volume"
                    ),
                    tank_diameter_m=result.get(
                        "tank_diameter_m"
                    ),
                    straight_height_m=result.get(
                        "straight_height_m"
                    ),
                    liquid_height_m=result.get(
                        "liquid_height_m"
                    ),
                    rpm=result.get(
                        "rpm"
                    ),
                    impellers=[],
                    bottom_type=result.get(
                        "bottom_type"
                    ),
                    top_type=result.get(
                        "top_type"
                    ),
                    number_baffles=result.get(
                        "number_baffles",
                        4,
                    ),
                    density_kg_m3=result.get(
                        "density_kg_m3"
                    ),
                    viscosity_pa_s=result.get(
                        "viscosity_pa_s"
                    ),
                    gas_flow_m3_h=result.get(
                        "gas_flow_m3_h",
                        0.0,
                    ),
                    bubble_diameter_mm=1.0,
                    selected_features=selected_features,
                    D=result.get(
                        "tank_diameter_m"
                    ),
                    H=result.get(
                        "straight_height_m"
                    ),
                    volume=result.get(
                        "working_volume"
                    ),
                    liquid_level=result.get(
                        "liquid_height_m"
                    ),
                    agitator=result.get(
                        "agitator"
                    ),
                    impeller_diameter_m=result.get(
                        "impeller_diameter_m"
                    ),
                    number_impellers=result.get(
                        "number_impellers",
                        1,
                    ),
                    impeller_clearance_m=result.get(
                        "impeller_clearance_m"
                    ),
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={
                        "displaylogo": False,
                        "responsive": True,
                        "scrollZoom": True,
                    },
                )

            except TypeError:

                # Compatibility with simpler reactor_3d implementations.

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
                        agitator=result.get(
                            "agitator"
                        ),
                        impeller_diameter=result.get(
                            "impeller_diameter_m"
                        ),
                        number_impellers=result.get(
                            "number_impellers",
                            1,
                        ),
                        rpm=result.get(
                            "rpm"
                        ),
                        number_baffles=result.get(
                            "number_baffles",
                            4,
                        ),
                        vortex_depth=0.0,
                        frames_count=36,
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        config={
                            "displaylogo": False,
                            "responsive": True,
                            "scrollZoom": True,
                        },
                    )

                except Exception as exc:

                    st.error(
                        f"3D visualization error: {exc}"
                    )

            except Exception as exc:

                st.error(
                    f"3D visualization error: {exc}"
                )

            # KPI strip under visualization

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                metric_card(
                    "P/V",
                    result.get("power_volume"),
                    "W/m³",
                    1,
                )

            with c2:
                metric_card(
                    "Tip Speed",
                    result.get("tip_speed"),
                    "m/s",
                    2,
                )

            with c3:
                metric_card(
                    "Q/V",
                    result.get("qv_1_h"),
                    "h⁻¹",
                    2,
                )

            with c4:
                metric_card(
                    "Re",
                    result.get("Re"),
                    "-",
                    0,
                )


# ============================================================
# ENGINEERING FOOTER
# ============================================================

st.divider()

st.caption(
    "Engineering screening tool — P/V is calculated from shaft power / "
    "working volume; Q/V from pumping capacity / working volume; "
    "Re from ρND²/μ; tip speed from πDN. "
    "Validate Np/Nq, Njs, kLa, blend time, flooding, mechanical loading "
    "and final vessel design against applicable literature, pilot data, "
    "vendor information and site engineering standards."
)

st.caption(
    f"Project: {project_name}  |  "
    f"Prepared by: {prepared_by}  |  "
    f"Process: {process_type}"
)
