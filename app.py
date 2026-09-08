import copy
import math
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# APPLICATION PATH
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up & Mixing Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# IMPORT ENGINEERING MODULES
# ============================================================

try:

    from calculations.engine import (
        calculate_reactor,
    )

    from calculations.scaleup import (
        calculate_scaleup,
    )

    from calculations.validation import (
        validate_reactor,
    )

    from libraries.agitator_geometry import (
        AGITATORS,
    )

    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )

    from visualization.reactor_3d import (
        create_reactor_animation,
    )

    from reporting.report_generator import (
        create_word_report,
        create_excel_report,
    )

except Exception as e:

    st.error(
        "Application module loading failed."
    )

    st.code(
        f"{type(e).__name__}: {e}"
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "reactor_inputs" not in st.session_state:

    st.session_state[
        "reactor_inputs"
    ] = None


if "reactor_result" not in st.session_state:

    st.session_state[
        "reactor_result"
    ] = None


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.main-title {
    font-size: 2.25rem;
    font-weight: 700;
}

.subtitle {
    color: #666;
    font-size: 1rem;
    margin-bottom: 1rem;
}

.section-title {
    font-size: 1.35rem;
    font-weight: 650;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def sf(
    value,
    default=0.0,
):

    try:

        value = float(
            value
        )

        if not math.isfinite(
            value
        ):

            return default

        return value

    except (
        TypeError,
        ValueError,
    ):

        return default


def fmt(
    value,
    digits=3,
):

    if value is None:
        return "—"

    try:

        value = float(
            value
        )

        if not math.isfinite(
            value
        ):

            return "—"

        return f"{value:,.{digits}f}"

    except (
        TypeError,
        ValueError,
    ):

        return str(
            value
        )


def safe_dataframe(
    data,
):

    if isinstance(
        data,
        pd.DataFrame,
    ):

        df = data.copy()

    else:

        df = pd.DataFrame(
            data
        )

    for column in df.columns:

        if str(
            df[column].dtype
        ) == "object":

            df[column] = (
                df[column]
                .map(
                    lambda x:
                    "" if x is None
                    else str(x)
                )
                .astype("string")
            )

    return df


# ============================================================
# IMPeller HELPERS
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
        if isinstance(
            data,
            dict,
        )
    ]


def calculate_elevations(
    impellers,
    liquid_height,
    tank_diameter,
):

    H = sf(
        liquid_height
    )

    T = sf(
        tank_diameter
    )

    output = []

    for impeller in impellers:

        item = copy.deepcopy(
            impeller
        )

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

        item[
            "elevation_m"
        ] = elevation

        output.append(
            item
        )

    output.sort(
        key=lambda x: sf(
            x.get(
                "elevation_m"
            )
        )
    )

    return output


def validate_impellers(
    impellers,
    liquid_height,
    tank_diameter,
):

    messages = []

    H = sf(
        liquid_height
    )

    T = sf(
        tank_diameter
    )

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

        if D <= 0:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: diameter must be > 0.",
                )
            )

        if T > 0 and D >= T:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: diameter must be smaller than tank ID.",
                )
            )

        if elevation >= H:

            messages.append(
                (
                    "ERROR",
                    f"Impeller {i}: elevation is above liquid level.",
                )
            )

        elevations.append(
            elevation
        )

    if len(
        elevations
    ) != len(
        set(
            round(
                x,
                4,
            )
            for x in elevations
        )
    ):

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
# INPUT FORM
# ============================================================

def reactor_inputs():

    st.markdown(
        '<div class="section-title">'
        "1. Reactor & Process"
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:

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

    with c2:

        tank_D = st.number_input(
            "Tank ID (m)",
            min_value=0.10,
            value=2.0,
            step=0.05,
        )

        straight_height = st.number_input(
            "Straight Side Height (m)",
            min_value=0.10,
            value=3.0,
            step=0.10,
        )

        surface_tension = st.number_input(
            "Surface Tension (mN/m)",
            min_value=0.1,
            value=30.0,
            step=1.0,
        )

    with c3:

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

    # ========================================================
    # VESSEL
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        "2. Vessel Geometry"
        "</div>",
        unsafe_allow_html=True,
    )

    head_names = list(
        REACTOR_HEADS.keys()
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        bottom_type = st.selectbox(
            "Bottom Head",
            head_names,
        )

    with c2:

        top_type = st.selectbox(
            "Top Head",
            head_names,
        )

    with c3:

        st.metric(
            "Working Volume",
            f"{fmt(working_volume, 2)} m³",
        )

    # Geometry

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

    if working_volume > vessel_volume:

        st.error(
            "Working volume is greater than estimated vessel volume."
        )

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
            working_volume
            / (
                math.pi
                * tank_D**2
                / 4.0
            ),
        )

    st.info(
        f"Estimated vessel volume: "
        f"**{fmt(vessel_volume, 2)} m³**  |  "
        f"Calculated liquid height: "
        f"**{fmt(liquid_height, 2)} m**"
    )

    # ========================================================
    # AGITATION
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        "3. Agitator Configuration"
        "</div>",
        unsafe_allow_html=True,
    )

    names = agitator_names()

    impellers = []

    for i in range(
        int(number_impellers)
    ):

        st.markdown(
            f"**Impeller {i + 1}**"
        )

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
                "Agitator",
                names,
                key=f"agitator_{i}",
            )

        with c3:

            default_D = min(
                0.50 * tank_D,
                0.90 * tank_D,
            )

            D = st.number_input(
                "Impeller Diameter (m)",
                min_value=0.01,
                max_value=max(
                    0.02,
                    0.95 * tank_D,
                ),
                value=max(
                    0.05,
                    default_D,
                ),
                step=0.05,
                key=f"D_{i}",
            )

        with c4:

            clearance = st.number_input(
                "Bottom Clearance (m)",
                min_value=0.0,
                max_value=max(
                    0.05,
                    liquid_height,
                ),
                value=min(
                    0.20 * tank_D,
                    max(
                        0.05,
                        liquid_height,
                    ),
                ),
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
    # GAS
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        "4. Gas–Liquid System"
        "</div>",
        unsafe_allow_html=True,
    )

    gas_active = st.checkbox(
        "Enable gas–liquid calculation",
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

    return {
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

        "impellers":
            impellers,

        "agitator":
            impellers[0][
                "agitator_type"
            ],

        "impeller_diameter_m":
            impellers[0][
                "diameter_m"
            ],

        "impeller_clearance_m":
            impellers[0][
                "bottom_clearance_m"
            ],

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

def run_calculation(
    inputs
):

    primary = inputs[
        "impellers"
    ][0]

    result = calculate_reactor(

        volume_m3=inputs[
            "working_volume_m3"
        ],

        tank_diameter_m=inputs[
            "tank_diameter_m"
        ],

        liquid_height_m=inputs[
            "liquid_height_m"
        ],

        density_kg_m3=inputs[
            "density_kg_m3"
        ],

        viscosity_pa_s=inputs[
            "viscosity_pa_s"
        ],

        surface_tension_n_m=inputs[
            "surface_tension_n_m"
        ],

        rpm=inputs[
            "rpm"
        ],

        impeller_diameter_m=primary[
            "diameter_m"
        ],

        number_impellers=inputs[
            "number_impellers"
        ],

        agitator=primary[
            "agitator_type"
        ],

        impeller_clearance_m=primary[
            "bottom_clearance_m"
        ],

        gas_flow_m3_h=inputs[
            "gas_flow_m3_h"
        ],

        bubble_diameter_mm=inputs[
            "bubble_diameter_mm"
        ],

        gas_holdup_fraction=inputs[
            "gas_holdup_fraction"
        ],
    )

    # Dashboard metadata

    result.update(
        {
            "straight_height_m":
                inputs[
                    "straight_height_m"
                ],

            "bottom_type":
                inputs[
                    "bottom_type"
                ],

            "top_type":
                inputs[
                    "top_type"
                ],

            "number_baffles":
                inputs[
                    "number_baffles"
                ],

            "vessel_volume_m3":
                inputs[
                    "vessel_volume_m3"
                ],

            "impellers":
                copy.deepcopy(
                    inputs[
                        "impellers"
                    ]
                ),
        }
    )

    return result


# ============================================================
# PERFORMANCE
# ============================================================

def performance_tab(
    result
):

    st.subheader(
        "Mixing Performance"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Reynolds Number",
            fmt(
                result.get(
                    "reynolds_number"
                ),
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

    data = [
        {
            "Parameter": "Working Volume",
            "Value": result.get(
                "volume_m3"
            ),
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
            "Parameter": "D/T",
            "Value": result.get(
                "D_T"
            ),
            "Unit": "-",
        },
        {
            "Parameter": "H/T",
            "Value": result.get(
                "H_T"
            ),
            "Unit": "-",
        },
        {
            "Parameter": "RPM",
            "Value": result.get(
                "rpm"
            ),
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


# ============================================================
# IMPELLER TAB
# ============================================================

def impeller_tab(
    result
):

    st.subheader(
        "Impeller Arrangement"
    )

    impellers = result.get(
        "impellers",
        []
    )

    rows = []

    tank_D = sf(
        result.get(
            "tank_diameter_m"
        )
    )

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
                    i,

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
                    D / tank_D
                    if tank_D > 0
                    else None,

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

    if rows:

        chart = pd.DataFrame(
            {
                "Impeller":
                    [
                        f"I-{i + 1}"
                        for i in range(
                            len(rows)
                        )
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

        st.subheader(
            "Impeller Elevation Profile"
        )

        st.bar_chart(
            chart.set_index(
                "Impeller"
            )
        )


# ============================================================
# GAS-LIQUID TAB
# ============================================================

def gas_liquid_tab(
    result
):

    st.subheader(
        "Gas–Liquid Mass Transfer"
    )

    status = result.get(
        "gas_liquid_status"
    )

    if status == "NOT ACTIVE":

        st.info(
            "Gas–liquid calculation is not active."
        )

        return

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

    rows = []

    for parameter, value, unit in data:

        rows.append(
            {
                "Parameter":
                    parameter,
                "Value":
                    value,
                "Unit":
                    unit,
            }
        )

    st.dataframe(
        safe_dataframe(rows),
        width="stretch",
        hide_index=True,
    )

    st.warning(
        "Gas–liquid calculations are screening-level "
        "estimates and require validation before final design."
    )


# ============================================================
# SCALE-UP TAB
# ============================================================

def scaleup_tab(
    result
):

    st.subheader(
        "Reactor Scale-Up"
    )

    c1, c2, c3 = st.columns(3)

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
            "Scale-Up Basis",
            [
                "Constant P/V",
                "Constant Tip Speed",
                "Constant RPM",
            ],
            key="scale_basis",
        )

    try:

        output = calculate_scaleup(
            reference_volume=V1,
            target_volume=V2,
            basis=basis,
            reference_diameter=(
                result.get(
                    "tank_diameter_m"
                )
            ),
            reference_rpm=(
                result.get(
                    "rpm"
                )
            ),
            reference_power_per_volume=(
                result.get(
                    "power_volume_kw_m3"
                )
            ),
            reference_tip_speed=(
                result.get(
                    "tip_speed"
                )
            ),
        )

        rows = [
            {
                "Parameter":
                    key,
                "Value":
                    value,
            }
            for key, value
            in output.items()
        ]

        st.dataframe(
            safe_dataframe(rows),
            width="stretch",
            hide_index=True,
        )

    except Exception as e:

        st.error(
            f"Scale-up calculation failed: "
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# VALIDATION TAB
# ============================================================

def validation_tab(
    result
):

    st.subheader(
        "Engineering Validation"
    )

    try:

        output = validate_reactor(
            result
        )

        st.dataframe(
            safe_dataframe(output),
            width="stretch",
            hide_index=True,
        )

    except Exception as e:

        st.error(
            f"Validation failed: "
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# 3D TAB
# ============================================================

def three_d_tab(
    result
):

    st.subheader(
        "3D Reactor Visualization"
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

            impellers=result.get(
                "impellers",
                [],
            ),

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
            "3D visualization failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# REPORT TAB
# ============================================================

def reports_tab(
    inputs,
    result
):

    st.subheader(
        "Engineering Reports"
    )

    c1, c2 = st.columns(2)

    with c1:

        try:

            word_file = create_word_report(
                inputs,
                result,
            )

            st.download_button(
                "Download Word Report",
                data=word_file.getvalue(),
                file_name=(
                    "reactor_scaleup_report.docx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                width="stretch",
            )

        except Exception as e:

            st.error(
                f"Word report failed: "
                f"{type(e).__name__}: {e}"
            )

    with c2:

        try:

            excel_file = create_excel_report(
                inputs,
                result,
            )

            st.download_button(
                "Download Excel Report",
                data=excel_file.getvalue(),
                file_name=(
                    "reactor_scaleup_report.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
            )

        except Exception as e:

            st.error(
                f"Excel report failed: "
                f"{type(e).__name__}: {e}"
            )

    st.divider()

    st.info(
        "The Excel report contains separate sheets for "
        "Summary, Inputs, Impellers, Performance, "
        "Gas-Liquid and Calculation Data."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🏭 Reactor Engineering"
    )

    st.caption(
        "Scale-Up & Mixing Dashboard"
    )

    st.divider()

    st.markdown(
        """
**Application Modules**

• Reactor geometry  
• Agitator selection  
• Mixing performance  
• Multi-impeller arrangement  
• Gas–liquid transfer  
• Scale-up  
• Engineering validation  
• 3D visualization  
• Word reporting  
• Excel reporting
"""
    )

    st.divider()

    st.caption(
        "Engineering screening tool. "
        "Final equipment design must be confirmed "
        "using validated correlations, vendor data, "
        "pilot/plant data and mechanical design checks."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    "🏭 Reactor Scale-Up & Mixing Dashboard"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Integrated process engineering tool for reactor "
    "geometry, agitator selection, mixing calculations, "
    "gas–liquid analysis, scale-up, validation, "
    "3D visualization and engineering reporting."
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# INPUTS
# ============================================================

inputs = reactor_inputs()


# ============================================================
# CALCULATE
# ============================================================

st.divider()

calculate = st.button(
    "▶ Calculate Reactor",
    type="primary",
    width="stretch",
)


if calculate:

    try:

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

        st.success(
            "Reactor calculation completed successfully."
        )

    except Exception as e:

        st.error(
            "Reactor calculation failed."
        )

        st.code(
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.get(
    "reactor_result"
)

stored_inputs = st.session_state.get(
    "reactor_inputs"
)


if result is None:

    st.info(
        "Enter the required reactor parameters "
        "and click Calculate Reactor."
    )

else:

    tabs = st.tabs(
        [
            "📊 Performance",
            "⚙️ Impellers",
            "🫧 Gas–Liquid",
            "📐 Scale-Up",
            "✅ Validation",
            "🧊 3D Reactor",
            "📄 Reports",
        ]
    )

    with tabs[0]:

        performance_tab(
            result
        )

    with tabs[1]:

        impeller_tab(
            result
        )

    with tabs[2]:

        gas_liquid_tab(
            result
        )

    with tabs[3]:

        scaleup_tab(
            result
        )

    with tabs[4]:

        validation_tab(
            result
        )

    with tabs[5]:

        three_d_tab(
            result
        )

    with tabs[6]:

        reports_tab(
            stored_inputs,
            result,
        )
