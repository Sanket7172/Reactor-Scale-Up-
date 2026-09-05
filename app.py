import math
import streamlit as st
import pandas as pd

from calculations.engine import calculate_reactor
from calculations.validation import validate_reactor

from libraries.agitator_geometry import AGITATORS
from libraries.reactor_geometry import (
    REACTOR_HEADS,
    calculate_total_volume,
    liquid_height_from_volume,
)

from visualization.reactor_3d import create_reactor_animation


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Studio",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* -----------------------------------------------------
       MAIN APPLICATION
       ----------------------------------------------------- */

    .main {
        background:
        radial-gradient(
            circle at top right,
            rgba(70,120,180,0.08),
            transparent 35%
        );
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }


    /* -----------------------------------------------------
       HERO CONTAINER
       ----------------------------------------------------- */

    .hero-box {
        padding: 28px 32px;
        border-radius: 22px;
        margin-bottom: 25px;

        background:
        linear-gradient(
            135deg,
            rgba(30,60,90,0.96),
            rgba(20,30,45,0.98)
        );

        color: white;

        box-shadow:
        0 12px 35px rgba(0,0,0,0.18);
    }


    /* -----------------------------------------------------
       KPI CARDS
       ----------------------------------------------------- */

    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.06);
        border: 1px solid rgba(128,128,128,0.18);
        padding: 12px;
        border-radius: 12px;
    }


    /* -----------------------------------------------------
       ENGINEERING STATUS
       ----------------------------------------------------- */

    .good {
        border-left: 5px solid #2e8b57;
        padding: 10px 15px;
        background: rgba(46,139,87,0.08);
        border-radius: 8px;
    }

    .warning {
        border-left: 5px solid #e0a800;
        padding: 10px 15px;
        background: rgba(224,168,0,0.08);
        border-radius: 8px;
    }

    .danger {
        border-left: 5px solid #d9534f;
        padding: 10px 15px;
        background: rgba(217,83,79,0.08);
        border-radius: 8px;
    }


    /* -----------------------------------------------------
       SIDEBAR
       ----------------------------------------------------- */

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.15);
    }


    /* -----------------------------------------------------
       DATAFRAME
       ----------------------------------------------------- */

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }


    /* -----------------------------------------------------
       BUTTONS
       ----------------------------------------------------- */

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }


    /* -----------------------------------------------------
       EXPANDERS
       ----------------------------------------------------- */

    details {
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero-box">
    """,
    unsafe_allow_html=True,
)

st.title("🏭 Reactor Scale-Up Engineering Studio")

st.markdown(
    "**Professional screening platform for reactor geometry, "
    "mixing, agitation, scale-up similarity and engineering validation.**"
)

st.caption(
    "Lab → Pilot → Commercial  |  "
    "Mixing • Geometry • Scale-Up • Mechanical Screening"
)

st.markdown(
    """
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Study Controls")

project_name = st.sidebar.text_input(
    "Project",
    "Reactor Scale-Up Study",
)

prepared_by = st.sidebar.text_input(
    "Prepared By",
    "",
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

process_type = st.sidebar.selectbox(
    "Process Type",
    [
        "Liquid-Liquid",
        "Solid-Liquid",
        "Gas-Liquid",
        "Gas-Liquid-Solid",
        "Crystallization",
        "Precipitation",
        "Dissolution",
        "Extraction",
        "Neutralization",
        "Other",
    ],
)

scaleup_basis = st.sidebar.selectbox(
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
    ],
)


# =========================================================
# REACTOR SELECTION
# =========================================================

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


# =========================================================
# PROCESS GUIDANCE
# =========================================================

PROCESS_GUIDANCE = {

    "Liquid-Liquid": [
        "Blend time",
        "Tip speed",
        "P/V",
        "Reynolds number",
        "Pumping / volume",
    ],

    "Solid-Liquid": [
        "Njs",
        "P/V",
        "Tip speed",
        "Solids suspension",
        "Pumping / volume",
    ],

    "Gas-Liquid": [
        "P/V",
        "Tip speed",
        "Gas dispersion",
        "KLa",
        "Superficial gas velocity",
    ],

    "Gas-Liquid-Solid": [
        "Njs",
        "P/V",
        "Gas dispersion",
        "KLa",
        "Solids suspension",
    ],

    "Crystallization": [
        "Tip speed",
        "P/V",
        "Suspension",
        "Blend time",
        "Shear sensitivity",
    ],

    "Precipitation": [
        "P/V",
        "Blend time",
        "Tip speed",
        "Micromixing",
    ],

    "Dissolution": [
        "P/V",
        "Tip speed",
        "Pumping",
        "Blend time",
    ],

    "Extraction": [
        "P/V",
        "Tip speed",
        "Dispersion",
        "Blend time",
    ],

    "Neutralization": [
        "P/V",
        "Blend time",
        "Micromixing",
        "Tip speed",
    ],

    "Other": [
        "P/V",
        "Tip speed",
        "Reynolds",
        "Blend time",
    ],
}


# =========================================================
# PROCESS ENGINEERING GUIDANCE
# =========================================================

with st.expander(
    "🧠 Process Engineering Guidance",
    expanded=True,
):

    g1, g2 = st.columns([1, 2])

    with g1:

        st.write(
            f"**Process:** `{process_type}`"
        )

        st.write(
            f"**Scale-up basis:** `{scaleup_basis}`"
        )

    with g2:

        parameters = PROCESS_GUIDANCE.get(
            process_type,
            [],
        )

        st.write(
            "**Recommended engineering parameters:** "
            + " • ".join(parameters)
        )


# =========================================================
# REACTOR DATA
# =========================================================

reactors = {}


# =========================================================
# REACTOR DEFINITION
# =========================================================

st.subheader("📐 Reactor Definition")


# =========================================================
# INPUTS FOR EACH REACTOR
# =========================================================

for reactor_name in reactor_names:

    with st.expander(
        f"🏭 {reactor_name} Reactor",
        expanded=True,
    ):

        col1, col2, col3 = st.columns(3)


        # =================================================
        # PROCESS / VOLUME
        # =================================================

        with col1:

            st.markdown("### Process / Fluid")

            working_volume = st.number_input(
                "Operating Liquid Volume [m³]",
                min_value=0.001,
                max_value=5000.0,
                value=1.0,
                step=0.1,
                key=f"{reactor_name}_volume",
            )

            density = st.number_input(
                "Liquid Density [kg/m³]",
                min_value=1.0,
                max_value=5000.0,
                value=1000.0,
                step=10.0,
                key=f"{reactor_name}_density",
            )

            viscosity = st.number_input(
                "Viscosity [mPa·s]",
                min_value=0.01,
                max_value=100000.0,
                value=1.0,
                step=0.1,
                key=f"{reactor_name}_viscosity",
            )

            surface_tension = st.number_input(
                "Surface Tension [mN/m]",
                min_value=0.1,
                max_value=2000.0,
                value=72.0,
                step=0.1,
                key=f"{reactor_name}_surface",
            )


        # =================================================
        # GEOMETRY
        # =================================================

        with col2:

            st.markdown("### Vessel Geometry")

            tank_id = st.number_input(
                "Tank Internal Diameter [mm]",
                min_value=100.0,
                max_value=20000.0,
                value=1200.0,
                step=10.0,
                key=f"{reactor_name}_tank_id",
            )

            straight_height = st.number_input(
                "Straight Side Height [mm]",
                min_value=100.0,
                max_value=30000.0,
                value=1500.0,
                step=10.0,
                key=f"{reactor_name}_straight",
            )

            bottom_type = st.selectbox(
                "Bottom Head",
                list(REACTOR_HEADS.keys()),
                index=1,
                key=f"{reactor_name}_bottom",
            )

            top_type = st.selectbox(
                "Top Head",
                list(REACTOR_HEADS.keys()),
                index=0,
                key=f"{reactor_name}_top",
            )


        # =================================================
        # AGITATION
        # =================================================

        with col3:

            st.markdown("### Agitation")

            agitator_type = st.selectbox(
                "Impeller Type",
                list(AGITATORS.keys()),
                key=f"{reactor_name}_agitator",
            )

            agitator_info = AGITATORS[
                agitator_type
            ]

            default_ratio = agitator_info.get(
                "default_diameter_ratio",
                0.35,
            )

            default_impeller = (
                tank_id *
                default_ratio
            )

            impeller_diameter = st.number_input(
                "Impeller Diameter [mm]",
                min_value=10.0,
                max_value=15000.0,
                value=float(
                    round(
                        default_impeller,
                        1,
                    )
                ),
                step=10.0,
                key=f"{reactor_name}_impeller",
            )

            number_impellers = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"{reactor_name}_number_impellers",
            )

            rpm = st.number_input(
                "Agitator Speed [RPM]",
                min_value=0.1,
                max_value=1000.0,
                value=100.0,
                step=1.0,
                key=f"{reactor_name}_rpm",
            )

            baffles = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=4,
                step=1,
                key=f"{reactor_name}_baffles",
            )


        # =================================================
        # UNIT CONVERSION
        # =================================================

        D = tank_id / 1000.0

        H = straight_height / 1000.0

        Di = impeller_diameter / 1000.0

        mu = viscosity / 1000.0

        sigma = surface_tension / 1000.0


        # =================================================
        # VESSEL VOLUME
        # =================================================

        vessel_volume = calculate_total_volume(
            D=D,
            straight_height=H,
            bottom_type=bottom_type,
            top_type=top_type,
        )


        # =================================================
        # LIQUID LEVEL
        # =================================================

        if working_volume <= vessel_volume:

            liquid_height, _ = (
                liquid_height_from_volume(
                    working_volume=working_volume,
                    D=D,
                    straight_height=H,
                    bottom_type=bottom_type,
                    top_type=top_type,
                )
            )

        else:

            liquid_height = 0.0


        # =================================================
        # FILL PERCENTAGE
        # =================================================

        if vessel_volume > 0:

            fill_percent = (
                working_volume /
                vessel_volume *
                100
            )

        else:

            fill_percent = 0.0


        # =================================================
        # BASIC GEOMETRIC RATIOS
        # =================================================

        H_over_D = (
            H / D
            if D > 0
            else 0.0
        )

        Di_over_D = (
            Di / D
            if D > 0
            else 0.0
        )

        liquid_over_D = (
            liquid_height / D
            if D > 0
            else 0.0
        )


        # =================================================
        # ENGINE CALCULATION
        # =================================================

        if working_volume <= vessel_volume:

            try:

                results = calculate_reactor(
                    volume_m3=working_volume,
                    tank_diameter_m=D,
                    liquid_height_m=liquid_height,
                    density_kg_m3=density,
                    viscosity_pa_s=mu,
                    surface_tension_n_m=sigma,
                    rpm=rpm,
                    impeller_diameter_m=Di,
                    number_impellers=int(
                        number_impellers
                    ),
                    agitator=agitator_type,
                    impeller_clearance_m=None,
                )

            except Exception as exc:

                st.error(
                    f"Calculation error for {reactor_name}: {exc}"
                )

                results = {}

        else:

            results = {}

            st.error(
                "Operating volume exceeds calculated vessel volume."
            )


        # =================================================
        # VALIDATION
        # =================================================

        validation = validate_reactor(
            volume_m3=working_volume,
            vessel_volume_m3=vessel_volume,
            tank_diameter_m=D,
            straight_height_m=H,
            liquid_height_m=liquid_height,
            impeller_diameter_m=Di,
            number_impellers=int(number_impellers),
            number_baffles=int(baffles),
            rpm=rpm,
            agitator=agitator_type,
            density_kg_m3=density,
            viscosity_pa_s=mu,
        )


        # =================================================
        # VORTEX SCREENING
        # =================================================

        Fr = results.get(
            "Fr",
            0.0,
        )

        if baffles == 0:

            baffle_factor = 1.0

        elif baffles == 2:

            baffle_factor = 0.55

        elif baffles == 4:

            baffle_factor = 0.25

        else:

            baffle_factor = 0.15


        vortex_depth = (
            0.08 *
            Di *
            math.sqrt(
                max(
                    Fr,
                    0.0,
                )
            ) *
            baffle_factor
        )


        if liquid_height > 0:

            vortex_depth = min(
                vortex_depth,
                0.35 * liquid_height,
            )

        else:

            vortex_depth = 0.0


        if liquid_height > 0:

            vortex_percent = (
                vortex_depth /
                liquid_height *
                100
            )

        else:

            vortex_percent = 0.0


        if baffles == 0 and Fr > 0.1:

            vortex_status = "High vortex tendency"

        elif vortex_percent > 8:

            vortex_status = "Moderate vortex"

        elif vortex_percent > 3:

            vortex_status = "Low vortex"

        else:

            vortex_status = "Vortex suppressed"


        # =================================================
        # STORE DATA
        # =================================================

        reactor_data = {

            "name": reactor_name,

            "working_volume": working_volume,

            "vessel_volume": vessel_volume,

            "tank_id": tank_id,

            "tank_id_m": D,

            "straight_height": straight_height,

            "straight_height_m": H,

            "bottom_type": bottom_type,

            "top_type": top_type,

            "liquid_height_m": liquid_height,

            "liquid_height": liquid_height * 1000,

            "fill_percentage": fill_percent,

            "density": density,

            "viscosity": viscosity,

            "viscosity_pa_s": mu,

            "surface_tension": surface_tension,

            "surface_tension_n_m": sigma,

            "agitator_type": agitator_type,

            "impeller_diameter": impeller_diameter,

            "impeller_diameter_m": Di,

            "number_impellers": int(
                number_impellers
            ),

            "baffles": int(
                baffles
            ),

            "rpm": rpm,

            "reaction_type": process_type,

            "scale_up_basis": scaleup_basis,

            "H_over_D": H_over_D,

            "Di_over_D": Di_over_D,

            "liquid_over_D": liquid_over_D,

            "vortex_depth": vortex_depth,

            "vortex_percent": vortex_percent,

            "vortex_status": vortex_status,

            "validation": validation,
        }


        reactor_data.update(
            results
        )


        reactors[
            reactor_name
        ] = reactor_data


# =========================================================
# DASHBOARD KPI
# =========================================================

st.subheader(
    "📊 Engineering Performance Dashboard"
)


for name, data in reactors.items():

    st.markdown(
        f"### 🏭 {name}"
    )


    # =====================================================
    # FIRST KPI ROW
    # =====================================================

    c1, c2, c3, c4, c5, c6 = st.columns(6)


    with c1:

        st.metric(
            "Operating Volume",
            f"{data['working_volume']:.2f} m³",
        )


    with c2:

        st.metric(
            "Liquid Level",
            f"{data['liquid_height']:.0f} mm",
        )


    with c3:

        power = data.get(
            "power_kw"
        )

        st.metric(
            "Power",
            f"{power:.2f} kW"
            if power is not None
            else "N/A",
        )


    with c4:

        pv = data.get(
            "power_volume"
        )

        st.metric(
            "P/V",
            f"{pv:.1f} W/m³"
            if pv is not None
            else "N/A",
        )


    with c5:

        tip_speed = data.get(
            "tip_speed"
        )

        st.metric(
            "Tip Speed",
            f"{tip_speed:.2f} m/s"
            if tip_speed is not None
            else "N/A",
        )


    with c6:

        reynolds = data.get(
            "Re"
        )

        st.metric(
            "Reynolds",
            f"{reynolds:.2e}"
            if reynolds is not None
            else "N/A",
        )


    # =====================================================
    # SECOND KPI ROW
    # =====================================================

    c1, c2, c3, c4, c5, c6 = st.columns(6)


    with c1:

        froude = data.get(
            "Fr"
        )

        st.metric(
            "Froude",
            f"{froude:.4f}"
            if froude is not None
            else "N/A",
        )


    with c2:

        q = data.get(
            "pumping_m3_h"
        )

        st.metric(
            "Pumping",
            f"{q:.1f} m³/h"
            if q is not None
            else "N/A",
        )


    with c3:

        turnover = data.get(
            "turnover_time_min"
        )

        st.metric(
            "Turnover",
            f"{turnover:.1f} min"
            if turnover is not None
            else "N/A",
        )


    with c4:

        st.metric(
            "D/T",
            f"{data['Di_over_D']:.3f}",
        )


    with c5:

        st.metric(
            "H/T",
            f"{data['straight_height_m'] / data['tank_id_m']:.2f}",
        )


    with c6:

        st.metric(
            "Fill",
            f"{data['fill_percentage']:.1f}%",
        )


# =========================================================
# SCALE-UP COMPARISON
# =========================================================

st.subheader(
    "📈 Scale-Up Similarity Analysis"
)


if len(reactors) >= 2:

    scaleup_rows = []


    for name, data in reactors.items():

        pumping = data.get(
            "pumping_m3_h"
        )

        working_volume = data[
            "working_volume"
        ]


        qv = (
            pumping / working_volume
            if pumping is not None
            and working_volume > 0
            else None
        )


        scaleup_rows.append(
            {
                "Reactor": name,

                "Volume [m³]":
                    data["working_volume"],

                "Diameter [m]":
                    data["tank_id_m"],

                "Impeller [m]":
                    data["impeller_diameter_m"],

                "RPM":
                    data["rpm"],

                "Tip Speed [m/s]":
                    data.get("tip_speed"),

                "Power [kW]":
                    data.get("power_kw"),

                "P/V [W/m³]":
                    data.get("power_volume"),

                "Re":
                    data.get("Re"),

                "Fr":
                    data.get("Fr"),

                "Q [m³/h]":
                    pumping,

                "Q/V [1/h]":
                    qv,
            }
        )


    df = pd.DataFrame(
        scaleup_rows
    )


    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


    # =====================================================
    # SCALE-UP RECOMMENDATION
    # =====================================================

    first_name = list(
        reactors.keys()
    )[0]

    base = reactors[
        first_name
    ]


    st.markdown(
        "#### 🎯 Selected Scale-Up Basis"
    )


    if scaleup_basis == "Constant P/V":

        target = base.get(
            "power_volume"
        )

        if target is not None:

            st.info(
                f"Recommended target P/V = "
                f"{target:.1f} W/m³ based on "
                f"{first_name}."
            )

        else:

            st.warning(
                "P/V is not available for the selected reactor."
            )


    elif scaleup_basis == "Constant Tip Speed":

        target = base.get(
            "tip_speed"
        )

        if target is not None:

            st.info(
                f"Recommended target tip speed = "
                f"{target:.2f} m/s based on "
                f"{first_name}."
            )


    elif scaleup_basis == "Constant RPM":

        st.info(
            f"Recommended target RPM = "
            f"{base['rpm']:.1f} RPM based on "
            f"{first_name}."
        )


    elif scaleup_basis == "Constant Froude Number":

        st.info(
            f"Recommended target Fr = "
            f"{base.get('Fr', 0):.4f}."
        )


    elif scaleup_basis == "Constant Reynolds Number":

        st.info(
            f"Recommended target Re = "
            f"{base.get('Re', 0):.2e}."
        )


    elif scaleup_basis == "Constant Pumping / Volume":

        pumping = base.get(
            "pumping_m3_h"
        )

        if pumping is not None:

            qv = (
                pumping /
                base["working_volume"]
            )

            st.info(
                f"Recommended Q/V = "
                f"{qv:.3f} 1/h."
            )

        else:

            st.warning(
                "Pumping calculation is not available."
            )


    elif scaleup_basis == "Constant N/Njs":

        st.warning(
            "Njs requires a validated solids-suspension "
            "correlation. Do not use a generic value without "
            "particle and fluid data."
        )


    elif scaleup_basis == "Constant KLa":

        st.warning(
            "KLa scale-up requires gas flow, sparger geometry, "
            "gas properties and a validated KLa correlation."
        )


    else:

        st.info(
            "User-defined scale-up basis selected. "
            "Use validated process-specific criteria."
        )


else:

    st.info(
        "Select a comparison study mode to enable "
        "scale-up similarity analysis."
    )


# =========================================================
# ENGINEERING VALIDATION
# =========================================================

st.subheader(
    "🚦 Engineering Validation"
)


for name, data in reactors.items():

    st.markdown(
        f"#### {name}"
    )


    validation = data.get(
        "validation",
        {}
    )


    # =====================================================
    # OVERALL STATUS
    # =====================================================

    overall = validation.get(
        "overall",
        "REVIEW"
    )


    if overall == "PASS":

        st.success(
            "🟢 Overall Validation Status: PASS"
        )

    elif overall == "FAIL":

        st.error(
            "🔴 Overall Validation Status: FAIL"
        )

    else:

        st.warning(
            "🟡 Overall Validation Status: REVIEW"
        )


    # =====================================================
    # CHECKS
    # =====================================================

    for check in validation.get(
        "checks",
        []
    ):

        severity = check.get(
            "severity",
            "WARNING"
        )

        message = check.get(
            "message",
            ""
        )


        if severity == "PASS":

            st.success(
                f"✅ {message}"
            )


        elif severity == "WARNING":

            st.warning(
                f"⚠️ {message}"
            )


        else:

            st.error(
                f"❌ {message}"
            )


# =========================================================
# ENGINEERING INSIGHTS
# =========================================================

st.subheader(
    "💡 Engineering Insights"
)


for name, data in reactors.items():

    insights = []


    if data["fill_percentage"] < 30:

        insights.append(
            "Low operating fill may reduce effective mixing volume."
        )


    if data["fill_percentage"] > 85:

        insights.append(
            "High fill level may reduce available headspace."
        )


    if data["Di_over_D"] < 0.20:

        insights.append(
            "Impeller/Tank diameter ratio is relatively low; "
            "check bulk circulation."
        )


    if data["Di_over_D"] > 0.60:

        insights.append(
            "Large impeller relative to tank diameter; "
            "check mechanical loading and clearance."
        )


    if data["baffles"] == 0:

        insights.append(
            "No baffles selected. Evaluate vortexing and "
            "rotational bulk motion."
        )


    reynolds = data.get(
        "Re"
    )


    if reynolds is not None:

        if reynolds < 10:

            insights.append(
                "Flow is in a strongly viscous/laminar regime."
            )

        elif reynolds < 10000:

            insights.append(
                "Flow is transitional; verify the selected "
                "power-number correlation."
            )

        else:

            insights.append(
                "Flow is in the turbulent regime for screening."
            )


    if data["agitator_type"] == "RCI":

        insights.append(
            "RCI requires validated vendor/test Np and Nq data."
        )


    if not insights:

        insights.append(
            "No additional screening-level engineering "
            "observations were triggered."
        )


    for insight in insights:

        st.info(
            f"**{name}:** {insight}"
        )


# =========================================================
# 3D VISUALIZATION
# =========================================================

st.subheader(
    "🌊 Interactive 3D Reactor Studio"
)


st.caption(
    "Conceptual engineering visualization — not CFD."
)


for name, data in reactors.items():

    with st.expander(
        f"🎛️ {name} — {data['agitator_type']}",
        expanded=True,
    ):

        try:

            fig = create_reactor_animation(

                D=data[
                    "tank_id_m"
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

                vortex_depth=data[
                    "vortex_depth"
                ],

                frames_count=36,
            )


            st.plotly_chart(
                fig,
                use_container_width=True,
            )


        except Exception as exc:

            st.error(
                f"3D visualization error for {name}: {exc}"
            )

            st.info(
                "The engineering calculations above can still "
                "be used independently of the 3D visualization."
            )


# =========================================================
# ENGINEERING BASIS & LIMITATIONS
# =========================================================

with st.expander(
    "⚠️ Engineering Basis & Limitations"
):

    st.markdown(
        """
        ### Calculation Philosophy

        This dashboard is intended for **engineering screening,
        comparison and scale-up studies**.

        It should not automatically be considered a final
        mechanical or process design calculation.

        ### Currently calculated

        - Reactor geometry
        - Operating liquid level
        - Fill percentage
        - Impeller/Tank diameter ratio
        - Tip speed
        - Reynolds number
        - Froude number
        - Power
        - Power/volume
        - Torque
        - Pumping capacity
        - Turnover time
        - Basic vortex tendency
        - Scale-up similarity indicators

        ### Requires validated process correlations

        - Njs
        - Blend time
        - KLa
        - Gas dispersion
        - Mass transfer
        - Micromixing
        - Crystal suspension
        - Solid-liquid suspension
        - Vendor-specific RCI performance

        ### Important

        Power numbers and pumping numbers are dependent on
        impeller geometry, Reynolds number, tank geometry,
        baffles, clearance and operating regime.

        Vendor data, pilot data, literature correlations or
        CFD should be used for final engineering design.

        ### Engineering Status

        Results from this dashboard should be treated as
        **screening-level engineering estimates** unless the
        underlying correlations and equipment-specific data
        have been validated for the actual system.
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    f"🏭 {project_name} | "
    f"Prepared by: {prepared_by or 'Process Engineering'} | "
    f"Reactor Scale-Up Engineering Studio"
)
