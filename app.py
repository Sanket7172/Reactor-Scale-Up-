import math
import pandas as pd
import streamlit as st

from calculations.engine import calculate_reactor, scaleup_rpm
from calculations.validation import validate_reactor, recommendations
from libraries.agitator_geometry import AGITATORS
from libraries.reactor_geometry import (
    REACTOR_HEADS,
    calculate_total_volume,
    liquid_height_from_volume,
)
from visualization.reactor_3d import create_reactor_animation


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
# UI STYLE
# ============================================================

st.markdown(
    """
<style>

/* ============================================================
   GLOBAL
============================================================ */

.stApp {
    background: #07111c;
}

.block-container {
    max-width: 1650px;
    padding-top: 1.0rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: #eef6fb !important;
}

p, label {
    color: #a9bdcb !important;
}

[data-testid="stSidebar"] {
    background: #06101a;
    border-right: 1px solid #193447;
}


/* ============================================================
   TOP HEADER
============================================================ */

.dashboard-header {
    background: linear-gradient(
        135deg,
        #0b1c2c 0%,
        #102c40 55%,
        #0b1b29 100%
    );

    border: 1px solid #21445b;
    border-radius: 18px;

    padding: 24px 28px;

    margin-bottom: 18px;

    box-shadow:
        0 12px 35px rgba(0, 0, 0, 0.22);
}

.dashboard-title {
    font-size: 2.2rem;
    font-weight: 850;
    color: #f4f9fc;
    letter-spacing: -0.035em;
}

.dashboard-subtitle {
    margin-top: 5px;
    color: #8fa8b9;
    font-size: 0.92rem;
}


/* ============================================================
   NAVIGATION
============================================================ */

div[data-baseweb="tab-list"] {
    background: #0a1825;
    border: 1px solid #1b374b;
    padding: 5px;
    border-radius: 12px;
}

button[data-baseweb="tab"] {
    color: #8da6b6 !important;
    font-weight: 700 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #12364b !important;
    color: #ffffff !important;
    border-radius: 8px;
}


/* ============================================================
   CARDS
============================================================ */

.metric-card {
    background: linear-gradient(
        145deg,
        #0e2132,
        #0a1927
    );

    border: 1px solid #1e3b50;

    border-radius: 14px;

    padding: 15px 16px;

    min-height: 112px;

    margin-bottom: 10px;

    box-shadow:
        0 8px 25px rgba(0, 0, 0, 0.18);
}

.metric-card:hover {
    border-color: #2c617c;
}

.metric-title {
    color: #7894a7;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.075em;
}

.metric-value {
    color: #f4f8fb;
    font-size: 1.45rem;
    font-weight: 850;
    margin-top: 8px;
    line-height: 1.15;
}

.metric-unit {
    color: #718b9e;
    font-size: 0.75rem;
    margin-top: 5px;
}


/* ============================================================
   ENGINEERING PANEL
============================================================ */

.engineering-panel {
    background: #0b1b29;

    border: 1px solid #1c3a4f;

    border-radius: 14px;

    padding: 17px 20px;

    margin: 12px 0 18px 0;
}

.panel-title {
    color: #dcecf5;

    font-size: 0.88rem;

    font-weight: 820;

    text-transform: uppercase;

    letter-spacing: 0.055em;
}

.panel-text {
    color: #8fa8b8;

    font-size: 0.84rem;

    line-height: 1.55;

    margin-top: 7px;
}


/* ============================================================
   STATUS
============================================================ */

.status-ready {
    display: inline-block;

    padding: 5px 12px;

    border-radius: 100px;

    background: #103826;

    border: 1px solid #287b50;

    color: #57df91;

    font-size: 0.70rem;

    font-weight: 850;
}

.status-review {
    display: inline-block;

    padding: 5px 12px;

    border-radius: 100px;

    background: #382e12;

    border: 1px solid #806621;

    color: #f1c75b;

    font-size: 0.70rem;

    font-weight: 850;
}

.status-risk {
    display: inline-block;

    padding: 5px 12px;

    border-radius: 100px;

    background: #3b1719;

    border: 1px solid #84343a;

    color: #ff7c82;

    font-size: 0.70rem;

    font-weight: 850;
}


/* ============================================================
   INPUTS
============================================================ */

div[data-baseweb="input"] > div {
    background: #0b1b29 !important;

    border-color: #29485c !important;

    border-radius: 8px !important;
}

div[data-baseweb="select"] > div {
    background: #0b1b29 !important;

    border-color: #29485c !important;

    border-radius: 8px !important;
}

input {
    color: #f0f6fa !important;
}

div[data-baseweb="select"] span {
    color: #e7f0f5 !important;
}


/* ============================================================
   BUTTONS
============================================================ */

.stButton > button {
    background: linear-gradient(
        135deg,
        #10405a,
        #12516e
    );

    color: white !important;

    border: 1px solid #28647f;

    border-radius: 9px;

    font-weight: 750;
}

.stButton > button:hover {
    border-color: #45c8f0;
}


/* ============================================================
   DATAFRAME
============================================================ */

[data-testid="stDataFrame"] {
    border: 1px solid #1d394d;
    border-radius: 10px;
}


/* ============================================================
   EXPANDER
============================================================ */

[data-testid="stExpander"] {
    background: #091925;

    border: 1px solid #1b384c !important;

    border-radius: 12px !important;
}


/* ============================================================
   DIVIDER
============================================================ */

hr {
    border-color: #183447 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="dashboard-header">
    <div class="dashboard-title">
        ⚗️ Reactor Scale-Up Engineering Studio
    </div>

    <div class="dashboard-subtitle">
        Reactor geometry • Mixing • Agitation • P/V • Q/V • Scale-Up • Validation • 3D
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# CONSTANTS
# ============================================================

PROCESS_TYPES = [
    "General Mixing",
    "Liquid-Liquid",
    "Solid-Liquid",
    "Gas-Liquid",
    "Gas-Liquid-Solid",
    "Crystallization",
    "Precipitation",
    "Dissolution",
    "Extraction",
    "Neutralization",
    "High-Viscosity",
    "Other",
]

SCALEUP_BASES = [
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

STUDY_MODES = [
    "Single Reactor",
    "Lab vs Pilot",
    "Pilot vs Commercial",
    "Lab vs Commercial",
    "Lab vs Pilot vs Commercial",
]

PROCESS_GUIDANCE = {
    "General Mixing": (
        "P/V + Q/V + blend performance",
        "Tip speed, Re, D/T, H/T and turnover"
    ),

    "Liquid-Liquid": (
        "Q/V + blend / dispersion performance",
        "P/V, tip speed, Re, phase ratio and droplet size"
    ),

    "Solid-Liquid": (
        "N/Njs + suspension",
        "P/V, Q/V, clearance and solids loading"
    ),

    "Gas-Liquid": (
        "Gas dispersion + kLa",
        "P/V, gas velocity, tip speed and flooding"
    ),

    "Gas-Liquid-Solid": (
        "N/Njs + gas dispersion",
        "P/V, Q/V, gas velocity and kLa"
    ),

    "Crystallization": (
        "Suspension + controlled shear",
        "P/V, tip speed, Re and crystal quality"
    ),

    "High-Viscosity": (
        "Torque + P/V",
        "Re, tip speed, shaft load and heat transfer"
    ),
}


# ============================================================
# HELPERS
# ============================================================

def metric_card(title, value, unit="", decimals=2):
    if value is None:
        text = "N/A"

    elif isinstance(value, str):
        text = value

    else:
        try:
            text = f"{float(value):,.{decimals}f}"
        except Exception:
            text = str(value)

    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-title">{title}</div>
    <div class="metric-value">{text}</div>
    <div class="metric-unit">{unit}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def section_title(title, description=None):
    st.markdown(
        f"### {title}"
    )

    if description:
        st.caption(description)


def validation_status(data):
    checks = data.get("validation_checks", [])

    if not checks:
        return "REVIEW"

    failed = [
        item for item in checks
        if len(item) >= 2 and not item[1]
    ]

    if failed:
        return "REVIEW"

    return "READY"


def status_display(status):

    if status == "READY":

        st.markdown(
            '<span class="status-ready">● READY</span>',
            unsafe_allow_html=True,
        )

    elif status == "RISK":

        st.markdown(
            '<span class="status-risk">● RISK</span>',
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            '<span class="status-review">● REVIEW</span>',
            unsafe_allow_html=True,
        )


def safe(value, decimals=2):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return str(value)


def add_derived_values(data):
    """
    Makes critical engineering KPIs explicit.

    P/V:
        P/V = Power / Working Volume

    Q/V:
        Q/V = Pumping Capacity / Working Volume

    Tip speed:
        u_tip = pi * D * N

    Torque:
        T = P / (2*pi*N)
    """

    volume = data.get("working_volume")

    power_w = data.get("power_w")

    rpm = data.get("rpm")

    impeller_D = data.get(
        "impeller_diameter_m"
    )

    pumping = data.get(
        "pumping_m3_h"
    )

    # --------------------------------------------------------
    # P/V
    # --------------------------------------------------------

    if power_w is not None and volume and volume > 0:

        data["power_volume"] = (
            power_w / volume
        )

        data["power_volume_kw_m3"] = (
            power_w / volume / 1000.0
        )

    # --------------------------------------------------------
    # Q/V
    # --------------------------------------------------------

    if pumping is not None and volume and volume > 0:

        data["qv_1_h"] = (
            pumping / volume
        )

        if data["qv_1_h"] > 0:

            data["turnover_time_min"] = (
                60.0 / data["qv_1_h"]
            )

    # --------------------------------------------------------
    # TIP SPEED
    # --------------------------------------------------------

    if rpm and impeller_D:

        N = rpm / 60.0

        data["tip_speed"] = (
            math.pi *
            impeller_D *
            N
        )

    # --------------------------------------------------------
    # TORQUE
    # --------------------------------------------------------

    if power_w is not None and rpm and rpm > 0:

        N = rpm / 60.0

        data["torque_nm"] = (
            power_w /
            (2.0 * math.pi * N)
        )

    # --------------------------------------------------------
    # D/T
    # --------------------------------------------------------

    if data.get("tank_diameter_m"):

        data["D_T"] = (
            impeller_D /
            data["tank_diameter_m"]
        )

    # --------------------------------------------------------
    # H/T
    # --------------------------------------------------------

    if data.get("tank_diameter_m"):

        data["H_T"] = (
            data["liquid_height_m"] /
            data["tank_diameter_m"]
        )

    # --------------------------------------------------------
    # C/T
    # --------------------------------------------------------

    if data.get("tank_diameter_m"):

        data["clearance_T"] = (
            data["clearance_m"] /
            data["tank_diameter_m"]
        )

    return data


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## ⚗️ Study Control"
    )

    project = st.text_input(
        "Project / Study",
        "Reactor Scale-Up Study",
    )

    engineer = st.text_input(
        "Prepared By",
        "",
    )

    study_mode = st.selectbox(
        "Study Mode",
        STUDY_MODES,
    )

    process_type = st.selectbox(
        "Process Type",
        PROCESS_TYPES,
    )

    basis = st.selectbox(
        "Scale-Up Basis",
        SCALEUP_BASES,
        index=0,
    )

    st.divider()

    primary, secondary = PROCESS_GUIDANCE.get(
        process_type,
        (
            "Process-specific engineering basis",
            "Validate against pilot/vendor data",
        ),
    )

    st.markdown(
        "### Scale-Up Focus"
    )

    st.caption(
        f"**Primary**  \n{primary}"
    )

    st.caption(
        f"**Secondary**  \n{secondary}"
    )

    st.divider()

    st.caption(
        "Preliminary engineering screening tool. "
        "Final equipment design requires validated correlations, "
        "pilot data, vendor information and mechanical design review."
    )


# ============================================================
# REACTOR CONFIGURATION
# ============================================================

reactor_map = {
    "Single Reactor": [
        "Reactor"
    ],

    "Lab vs Pilot": [
        "Lab",
        "Pilot"
    ],

    "Pilot vs Commercial": [
        "Pilot",
        "Commercial"
    ],

    "Lab vs Commercial": [
        "Lab",
        "Commercial"
    ],

    "Lab vs Pilot vs Commercial": [
        "Lab",
        "Pilot",
        "Commercial"
    ],
}

reactor_names = reactor_map[
    study_mode
]


# ============================================================
# DESIGN INPUTS
# ============================================================

st.markdown(
    "## 1. Reactor Design Basis"
)

st.caption(
    "Define vessel geometry, fluid properties and agitation system. "
    "The dashboard calculates liquid level and engineering KPIs automatically."
)


reactors = {}


for name in reactor_names:

    with st.expander(
        f"⚗️ {name} Reactor",
        expanded=True,
    ):

        # ====================================================
        # FLUID
        # ====================================================

        section_title(
            "Process & Fluid Properties",
            "Fundamental properties used in mixing calculations.",
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            V = st.number_input(
                "Working Volume [m³]",
                min_value=0.001,
                max_value=5000.0,
                value=10.0 if name != "Lab" else 1.0,
                step=0.1,
                key=f"{name}_V",
            )

        with c2:

            rho = st.number_input(
                "Density [kg/m³]",
                min_value=0.1,
                max_value=5000.0,
                value=1000.0,
                step=10.0,
                key=f"{name}_rho",
            )

        with c3:

            mu_cP = st.number_input(
                "Viscosity [mPa·s]",
                min_value=0.001,
                max_value=100000.0,
                value=1.0,
                step=0.1,
                key=f"{name}_mu",
            )

        with c4:

            sigma_mNm = st.number_input(
                "Surface Tension [mN/m]",
                min_value=0.001,
                max_value=2000.0,
                value=72.0,
                step=0.1,
                key=f"{name}_sigma",
            )

        mu = mu_cP / 1000.0

        sigma = sigma_mNm / 1000.0


        # ====================================================
        # GEOMETRY
        # ====================================================

        section_title(
            "Vessel Geometry",
            "Tank dimensions and head configuration.",
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            Tmm = st.number_input(
                "Tank ID [mm]",
                min_value=100.0,
                max_value=20000.0,
                value=2000.0,
                step=10.0,
                key=f"{name}_T",
            )

        with c2:

            Hmm = st.number_input(
                "Straight Side Height [mm]",
                min_value=100.0,
                max_value=30000.0,
                value=2500.0,
                step=10.0,
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

        T = Tmm / 1000.0

        H = Hmm / 1000.0


        # ====================================================
        # VESSEL VOLUME
        # ====================================================

        try:

            # IMPORTANT:
            # Positional arguments intentionally used here.
            # This is compatible with the current
            # reactor_geometry.py function.

            vessel_volume = calculate_total_volume(
                T,
                H,
                bottom,
                top,
            )

        except Exception as exc:

            st.error(
                "Unable to calculate vessel volume."
            )

            st.code(
                str(exc)
            )

            st.stop()


        if V > vessel_volume:

            st.error(
                f"Working volume {V:.3f} m³ exceeds "
                f"calculated vessel volume "
                f"{vessel_volume:.3f} m³."
            )

            working_volume = (
                vessel_volume * 0.999
            )

        else:

            working_volume = V


        # ====================================================
        # LIQUID LEVEL
        # ====================================================

        try:

            liquid_height, _ = (
                liquid_height_from_volume(
                    working_volume,
                    T,
                    H,
                    bottom,
                    top,
                )
            )

        except Exception as exc:

            st.error(
                "Unable to calculate liquid level."
            )

            st.code(
                str(exc)
            )

            st.stop()


        fill_percent = (
            100.0 *
            working_volume /
            vessel_volume
            if vessel_volume > 0
            else 0.0
        )


        # ====================================================
        # GEOMETRY SNAPSHOT
        # ====================================================

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
                "Liquid Level",
                liquid_height * 1000.0,
                "mm",
                0,
            )

        with c3:

            metric_card(
                "Operating Fill",
                fill_percent,
                "%",
                1,
            )

        with c4:

            metric_card(
                "H/T",
                liquid_height / T
                if T > 0
                else None,
                "dimensionless",
                3,
            )


        # ====================================================
        # AGITATOR
        # ====================================================

        section_title(
            "Agitation System",
            "Impeller selection and operating speed.",
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            agitator = st.selectbox(
                "Impeller Type",
                list(AGITATORS.keys()),
                key=f"{name}_agitator",
            )

        agitator_data = AGITATORS[
            agitator
        ]

        default_ratio = agitator_data.get(
            "default_diameter_ratio",
            0.35,
        )

        default_Dmm = (
            Tmm *
            default_ratio
        )

        with c2:

            Dmm = st.number_input(
                "Impeller Diameter [mm]",
                min_value=10.0,
                max_value=15000.0,
                value=float(
                    round(
                        default_Dmm,
                        1,
                    )
                ),
                step=10.0,
                key=f"{name}_D",
            )

        with c3:

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{name}_nimp",
            )

        with c4:

            rpm = st.number_input(
                "Agitator Speed [RPM]",
                min_value=0.1,
                max_value=2000.0,
                value=100.0,
                step=1.0,
                key=f"{name}_rpm",
            )

        D = Dmm / 1000.0


        # ====================================================
        # INTERNALS
        # ====================================================

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{name}_baffles",
            )

        with c2:

            clearance_mm = st.number_input(
                "Bottom Clearance [mm]",
                min_value=1.0,
                max_value=10000.0,
                value=max(
                    25.0,
                    Dmm * 0.20,
                ),
                step=5.0,
                key=f"{name}_clearance",
            )

        with c3:

            if process_type in (
                "Gas-Liquid",
                "Gas-Liquid-Solid",
            ):

                gas_rate = st.number_input(
                    "Gas Rate [Nm³/h]",
                    min_value=0.0,
                    max_value=100000.0,
                    value=0.0,
                    step=10.0,
                    key=f"{name}_gas",
                )

            else:

                gas_rate = 0.0

        with c4:

            if process_type in (
                "Solid-Liquid",
                "Gas-Liquid-Solid",
                "Crystallization",
                "Precipitation",
                "Dissolution",
            ):

                solids_pct = st.number_input(
                    "Solids Loading [wt%]",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.5,
                    key=f"{name}_solids",
                )

            else:

                solids_pct = 0.0

        clearance = (
            clearance_mm / 1000.0
        )


        # ====================================================
        # CALCULATION
        # ====================================================

        try:

            result = calculate_reactor(
                working_volume,
                T,
                liquid_height,
                rho,
                mu,
                sigma,
                rpm,
                D,
                int(number_impellers),
                agitator,
                clearance,
            )

        except Exception as exc:

            st.error(
                f"Reactor calculation failed for {name}."
            )

            st.exception(exc)

            st.stop()


        # ====================================================
        # ENGINEERING DATA MODEL
        # ====================================================

        data = {
            "name": name,

            "working_volume": working_volume,

            "tank_id_mm": Tmm,
            "tank_diameter_m": T,

            "straight_height_mm": Hmm,
            "straight_height_m": H,

            "bottom_type": bottom,
            "top_type": top,

            "vessel_volume": vessel_volume,

            "liquid_height_m": liquid_height,

            "liquid_height_mm":
                liquid_height * 1000.0,

            "fill_percentage":
                fill_percent,

            "density_kg_m3":
                rho,

            "viscosity_pa_s":
                mu,

            "viscosity_cP":
                mu_cP,

            "surface_tension_n_m":
                sigma,

            "surface_tension_mN_m":
                sigma_mNm,

            "rpm":
                rpm,

            "agitator_type":
                agitator,

            "impeller_diameter_m":
                D,

            "impeller_diameter_mm":
                Dmm,

            "number_impellers":
                int(number_impellers),

            "baffles":
                int(baffles),

            "clearance_m":
                clearance,

            "gas_rate_nm3_h":
                gas_rate,

            "solids_wt_pct":
                solids_pct,

            "process_type":
                process_type,

            "scale_up_basis":
                basis,
        }

        data.update(result)

        data = add_derived_values(
            data
        )


        # ====================================================
        # VALIDATION
        # ====================================================

        try:

            validation_data = {
                "fill_percentage":
                    data["fill_percentage"],

                "D_T":
                    data["D_T"],

                "H_T":
                    data["H_T"],

                "baffles":
                    data["baffles"],

                "clearance_T":
                    data.get(
                        "clearance_T"
                    ),

                "number_impellers":
                    data["number_impellers"],

                "mixing_regime":
                    data["mixing_regime"],

                "Fr":
                    data["Fr"],

                "Re":
                    data["Re"],

                "agitator_type":
                    data["agitator_type"],
            }

            checks = validate_reactor(
                validation_data
            )

        except Exception as exc:

            checks = []

            data["validation_error"] = str(
                exc
            )

        data[
            "validation_checks"
        ] = checks

        reactors[name] = data

        st.caption(
            f"{agitator_data.get('description', '')}"
        )

        if agitator_data.get("np") is None:

            st.warning(
                "This impeller has no generic Np/Nq data. "
                "Power and pumping calculations require validated "
                "vendor or literature performance data."
            )


# ============================================================
# ENGINEERING OVERVIEW
# ============================================================

st.divider()

st.markdown(
    "## 2. Engineering Performance"
)

st.caption(
    "Primary mixing KPIs calculated from vessel geometry, fluid properties, "
    "impeller geometry and operating speed."
)


for name, data in reactors.items():

    status = validation_status(
        data
    )

    c1, c2 = st.columns(
        [5, 1]
    )

    with c1:

        st.markdown(
            f"### {name}"
        )

    with c2:

        status_display(
            status
        )


    # ========================================================
    # PRIMARY KPIs
    # ========================================================

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:

        metric_card(
            "P / V",
            data.get(
                "power_volume"
            ),
            "W/m³",
            1,
        )

    with c2:

        metric_card(
            "P / V",
            data.get(
                "power_volume_kw_m3"
            ),
            "kW/m³",
            3,
        )

    with c3:

        metric_card(
            "Shaft Power",
            data.get(
                "power_kw"
            ),
            "kW",
            2,
        )

    with c4:

        metric_card(
            "Q / V",
            data.get(
                "qv_1_h"
            ),
            "h⁻¹",
            2,
        )

    with c5:

        metric_card(
            "Tip Speed",
            data.get(
                "tip_speed"
            ),
            "m/s",
            2,
        )

    with c6:

        metric_card(
            "Reynolds",
            data.get(
                "Re"
            ),
            "dimensionless",
            0,
        )


    # ========================================================
    # SECONDARY KPIs
    # ========================================================

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:

        metric_card(
            "Torque",
            data.get(
                "torque_nm"
            ),
            "N·m",
            1,
        )

    with c2:

        metric_card(
            "Froude",
            data.get(
                "Fr"
            ),
            "dimensionless",
            4,
        )

    with c3:

        metric_card(
            "D / T",
            data.get(
                "D_T"
            ),
            "dimensionless",
            3,
        )

    with c4:

        metric_card(
            "H / T",
            data.get(
                "H_T"
            ),
            "dimensionless",
            3,
        )

    with c5:

        metric_card(
            "C / T",
            data.get(
                "clearance_T"
            ),
            "dimensionless",
            3,
        )

    with c6:

        metric_card(
            "Turnover",
            data.get(
                "turnover_time_min"
            ),
            "min",
            1,
        )


    # ========================================================
    # ENGINEERING INTERPRETATION
    # ========================================================

    primary, secondary = PROCESS_GUIDANCE.get(
        process_type,
        PROCESS_GUIDANCE["General Mixing"],
    )

    st.markdown(
        f"""
<div class="engineering-panel">

<div class="panel-title">
Engineering Interpretation
</div>

<div class="panel-text">

<b>Primary scale-up focus:</b>
{primary}

<br><br>

<b>Secondary checks:</b>
{secondary}

<br><br>

<b>Current P/V:</b>
{safe(data.get("power_volume"), 1)} W/m³
&nbsp;&nbsp;|
&nbsp;&nbsp;
{safe(data.get("power_volume_kw_m3"), 3)} kW/m³

<br>

<b>Flow regime:</b>
{data.get("mixing_regime", "N/A")}

</div>

</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# DETAILED PARAMETERS
# ============================================================

with st.expander(
    "Detailed Engineering Data",
    expanded=False,
):

    rows = []

    parameter_list = [
        (
            "Working Volume",
            data.get("working_volume"),
            "m³",
        )
        for data in reactors.values()
    ]

    detailed_rows = []

    for name, data in reactors.items():

        detailed_rows.extend(
            [
                [
                    name,
                    "Working Volume",
                    data.get(
                        "working_volume"
                    ),
                    "m³",
                ],

                [
                    name,
                    "Vessel Volume",
                    data.get(
                        "vessel_volume"
                    ),
                    "m³",
                ],

                [
                    name,
                    "Liquid Height",
                    data.get(
                        "liquid_height_m"
                    ),
                    "m",
                ],

                [
                    name,
                    "Tank Diameter",
                    data.get(
                        "tank_diameter_m"
                    ),
                    "m",
                ],

                [
                    name,
                    "Impeller Diameter",
                    data.get(
                        "impeller_diameter_m"
                    ),
                    "m",
                ],

                [
                    name,
                    "RPM",
                    data.get(
                        "rpm"
                    ),
                    "RPM",
                ],

                [
                    name,
                    "Power",
                    data.get(
                        "power_kw"
                    ),
                    "kW",
                ],

                [
                    name,
                    "P/V",
                    data.get(
                        "power_volume"
                    ),
                    "W/m³",
                ],

                [
                    name,
                    "Q/V",
                    data.get(
                        "qv_1_h"
                    ),
                    "h⁻¹",
                ],

                [
                    name,
                    "Turnover Time",
                    data.get(
                        "turnover_time_min"
                    ),
                    "min",
                ],

                [
                    name,
                    "Tip Speed",
                    data.get(
                        "tip_speed"
                    ),
                    "m/s",
                ],

                [
                    name,
                    "Torque",
                    data.get(
                        "torque_nm"
                    ),
                    "N·m",
                ],

                [
                    name,
                    "Reynolds Number",
                    data.get(
                        "Re"
                    ),
                    "-",
                ],

                [
                    name,
                    "Froude Number",
                    data.get(
                        "Fr"
                    ),
                    "-",
                ],

                [
                    name,
                    "D/T",
                    data.get(
                        "D_T"
                    ),
                    "-",
                ],

                [
                    name,
                    "H/T",
                    data.get(
                        "H_T"
                    ),
                    "-",
                ],

                [
                    name,
                    "C/T",
                    data.get(
                        "clearance_T"
                    ),
                    "-",
                ],
            ]
        )

    detail_df = pd.DataFrame(
        detailed_rows,
        columns=[
            "Reactor",
            "Parameter",
            "Value",
            "Unit",
        ],
    )

    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# SCALE-UP
# ============================================================

st.divider()

st.markdown(
    "## 3. Scale-Up Engineering"
)

st.caption(
    "Reference-to-target similarity analysis. "
    "Use process-specific criteria and validate against pilot performance."
)


if len(reactors) >= 2:

    reference_name = reactor_names[0]

    reference = reactors[
        reference_name
    ]

    st.markdown(
        f"### {reference_name} → Target"
    )


    for target_name in reactor_names[1:]:

        target = reactors[
            target_name
        ]

        # ----------------------------------------------------
        # SCALE RATIOS
        # ----------------------------------------------------

        volume_ratio = (
            target["working_volume"]
            /
            reference["working_volume"]
        )

        diameter_ratio = (
            target["tank_diameter_m"]
            /
            reference["tank_diameter_m"]
        )

        impeller_ratio = (
            target["impeller_diameter_m"]
            /
            reference["impeller_diameter_m"]
        )

        pv_ratio = None

        if (
            reference.get("power_volume")
            and
            target.get("power_volume")
        ):

            pv_ratio = (
                target["power_volume"]
                /
                reference["power_volume"]
            )

        qv_ratio = None

        if (
            reference.get("qv_1_h")
            and
            target.get("qv_1_h")
        ):

            qv_ratio = (
                target["qv_1_h"]
                /
                reference["qv_1_h"]
            )

        tip_ratio = None

        if (
            reference.get("tip_speed")
            and
            target.get("tip_speed")
        ):

            tip_ratio = (
                target["tip_speed"]
                /
                reference["tip_speed"]
            )


        # ----------------------------------------------------
        # SCALE SNAPSHOT
        # ----------------------------------------------------

        st.markdown(
            f"#### {reference_name} → {target_name}"
        )

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
                "Tank Scale",
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


        # ----------------------------------------------------
        # SCALE-UP RPM
        # ----------------------------------------------------

        calculated_rpm = scaleup_rpm(
            reference,
            target,
            basis,
        )

        if calculated_rpm is None:

            st.warning(
                f"{basis} does not have a generic RPM "
                "relationship in the current calculation engine. "
                "Use validated process/vendor correlations."
            )

        else:

            st.markdown(
                "#### Calculated Scale-Up Target"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                metric_card(
                    "Calculated Target RPM",
                    calculated_rpm,
                    "RPM",
                    1,
                )

            with c2:

                target_tip = (
                    math.pi *
                    target["impeller_diameter_m"] *
                    calculated_rpm /
                    60.0
                )

                metric_card(
                    "Target Tip Speed",
                    target_tip,
                    "m/s",
                    2,
                )

            with c3:

                metric_card(
                    "Selected Basis",
                    basis,
                    "",
                    2,
                )


        # ----------------------------------------------------
        # ENGINEERING COMPARISON
        # ----------------------------------------------------

        comparison_rows = [
            [
                "Working Volume",
                "m³",
                reference["working_volume"],
                target["working_volume"],
                volume_ratio,
            ],

            [
                "Tank Diameter",
                "m",
                reference["tank_diameter_m"],
                target["tank_diameter_m"],
                diameter_ratio,
            ],

            [
                "Impeller Diameter",
                "m",
                reference["impeller_diameter_m"],
                target["impeller_diameter_m"],
                impeller_ratio,
            ],

            [
                "RPM",
                "RPM",
                reference["rpm"],
                target["rpm"],
                target["rpm"] /
                reference["rpm"],
            ],

            [
                "Power",
                "kW",
                reference.get("power_kw"),
                target.get("power_kw"),
                (
                    target["power_kw"] /
                    reference["power_kw"]
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
                "Reynolds",
                "-",
                reference.get("Re"),
                target.get("Re"),
                (
                    target["Re"] /
                    reference["Re"]
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
                    target["D_T"] /
                    reference["D_T"]
                    if reference.get("D_T")
                    else None
                ),
            ],
        ]

        comparison_df = pd.DataFrame(
            comparison_rows,
            columns=[
                "Engineering Parameter",
                "Unit",
                reference_name,
                target_name,
                "Target / Reference",
            ],
        )

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
        )


        # ----------------------------------------------------
        # P/V INTERPRETATION
        # ----------------------------------------------------

        if pv_ratio is not None:

            deviation = (
                (pv_ratio - 1.0) *
                100.0
            )

            if abs(deviation) <= 5:

                st.success(
                    f"P/V similarity is close: "
                    f"{pv_ratio:.3f}× reference "
                    f"({deviation:+.1f}%)."
                )

            elif abs(deviation) <= 20:

                st.warning(
                    f"P/V differs by "
                    f"{deviation:+.1f}% from reference. "
                    "Review against actual process performance."
                )

            else:

                st.error(
                    f"Large P/V deviation: "
                    f"{deviation:+.1f}%. "
                    "Do not assume equivalent mixing performance."
                )


else:

    st.info(
        "Select a comparison mode with two or more reactors "
        "to activate the scale-up analysis."
    )


# ============================================================
# PROCESS-SPECIFIC ENGINEERING
# ============================================================

st.divider()

st.markdown(
    "## 4. Process-Specific Engineering Review"
)

if process_type in (
    "Solid-Liquid",
    "Gas-Liquid-Solid",
    "Crystallization",
    "Precipitation",
    "Dissolution",
):

    st.info(
        "For solids service, the critical engineering question is not "
        "simply P/V. Suspension velocity, Njs, solids loading, particle "
        "properties, impeller type and clearance must be considered."
    )


if process_type in (
    "Gas-Liquid",
    "Gas-Liquid-Solid",
):

    st.info(
        "For gas-liquid service, P/V alone is insufficient. "
        "Gas rate, superficial gas velocity, sparger design, flooding/loading "
        "and validated kLa correlations must be checked."
    )


if process_type in (
    "Liquid-Liquid",
    "Extraction",
):

    st.info(
        "For liquid-liquid service, circulation and P/V should be supplemented "
        "by dispersion quality, droplet size, phase ratio and mass-transfer validation."
    )


if process_type == "High-Viscosity":

    st.info(
        "For high-viscosity service, torque and mechanical loading become "
        "critical. Generic turbulent-flow Np correlations may not be applicable."
    )


# ============================================================
# VALIDATION
# ============================================================

st.divider()

st.markdown(
    "## 5. Engineering Validation"
)

st.caption(
    "Screening checks. These are not substitutes for detailed mechanical or process design."
)


for name, data in reactors.items():

    with st.expander(
        f"🔎 {name} — Design Review",
        expanded=False,
    ):

        checks = data.get(
            "validation_checks",
            [],
        )

        if not checks:

            st.warning(
                "Validation results are unavailable."
            )

        else:

            validation_rows = []

            for item in checks:

                if len(item) >= 3:

                    label = item[0]

                    passed = item[1]

                    message = item[2]

                    validation_rows.append(
                        [
                            label,
                            "PASS"
                            if passed
                            else "REVIEW",
                            message,
                        ]
                    )

            validation_df = pd.DataFrame(
                validation_rows,
                columns=[
                    "Engineering Check",
                    "Status",
                    "Comment",
                ],
            )

            st.dataframe(
                validation_df,
                use_container_width=True,
                hide_index=True,
            )


        recs = recommendations(
            data,
            process_type,
            basis,
        )

        if recs:

            st.markdown(
                "### Engineering Recommendations"
            )

            for rec in recs:

                st.info(
                    f"💡 {rec}"
                )


# ============================================================
# 3D REACTOR
# ============================================================

st.divider()

st.markdown(
    "## 6. 3D Reactor & Mixing Visualization"
)

st.caption(
    "Interactive reactor geometry and conceptual mixing visualization. "
    "The particle/flow visualization is not CFD."
)


for name, data in reactors.items():

    with st.expander(
        f"🌊 {name} — {data['agitator_type']}",
        expanded=(name == reactor_names[0]),
    ):

        try:

            fig = create_reactor_animation(
                D=data[
                    "tank_diameter_m"
                ],

                straight_height=data[
                    "straight_height_m"
                ],

                bottom_type=data[
                    "bottom_type"
                ],

                top_type=data[
                    "top_type"
                ],

                liquid_height=data[
                    "liquid_height_m"
                ],

                agitator=data[
                    "agitator_type"
                ],

                impeller_diameter=data[
                    "impeller_diameter_m"
                ],

                number_impellers=data[
                    "number_impellers"
                ],

                rpm=data[
                    "rpm"
                ],

                number_baffles=data[
                    "baffles"
                ],

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
                "3D reactor visualization failed."
            )

            st.exception(
                exc
            )


# ============================================================
# ENGINEERING BASIS / LIMITATIONS
# ============================================================

st.divider()

st.markdown(
    "## Engineering Basis & Limitations"
)

st.markdown(
    """
**P/V**

\[
P/V = P/V_{working}
\]

where shaft power is calculated from the selected impeller power number,
fluid density, speed and impeller diameter.

**Pumping / Volume**

\[
Q/V
\]

is calculated from the impeller pumping number and represents a circulation
intensity indicator. It should not be interpreted as actual blend time.

**Tip Speed**

\[
u_{tip} = \pi DN
\]

**Reynolds Number**

\[
Re = \\frac{\\rho ND^2}{\\mu}
\]

**Torque**

\[
T = \\frac{P}{2\\pi N}
\]

**Important:** Np, Nq, Njs, kLa, blend time, flooding, gas dispersion,
shaft mechanical design and final equipment suitability require
validated correlations, pilot data or vendor data where applicable.
"""
)

st.caption(
    f"Project: {project}  |  "
    f"Prepared By: {engineer or '—'}  |  "
    f"Process: {process_type}  |  "
    f"Scale-Up Basis: {basis}"
)
