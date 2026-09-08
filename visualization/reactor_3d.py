# visualization/reactor_3d.py

import math
import numpy as np
import plotly.graph_objects as go


# ============================================================
# CONSTANTS
# ============================================================

G = 9.81


# ============================================================
# SAFE CONVERSION FUNCTIONS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _clamp(value, low, high):
    return max(low, min(high, value))


def _get_value(data, keys, default=None):

    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data:
            value = data[key]

            if value is not None:
                return value

    return default


# ============================================================
# IMPELLER NORMALIZATION
# ============================================================

def _normalize_impellers(
    impellers=None,
    tank_diameter_m=2.0,
    impeller_diameter_m=None,
    impeller_clearance_m=0.4,
    agitator="Rushton Turbine",
    number_impellers=1,
):

    normalized = []

    # --------------------------------------------------------
    # User supplied impeller arrangement
    # --------------------------------------------------------

    if isinstance(impellers, list):

        for i, imp in enumerate(impellers):

            if not isinstance(imp, dict):
                continue

            imp_type = _get_value(
                imp,
                [
                    "agitator_type",
                    "agitator",
                    "type",
                    "name",
                ],
                agitator,
            )

            diameter = _get_value(
                imp,
                [
                    "diameter_m",
                    "impeller_diameter_m",
                    "D",
                    "diameter",
                ],
                impeller_diameter_m,
            )

            if diameter is None:
                diameter = (
                    tank_diameter_m *
                    0.5
                )

            elevation = _get_value(
                imp,
                [
                    "elevation_m",
                    "elevation",
                    "bottom_clearance_m",
                    "clearance_m",
                ],
                None,
            )

            if elevation is None:
                elevation = (
                    impeller_clearance_m +
                    i *
                    0.90 *
                    float(diameter)
                )

            position = _get_value(
                imp,
                [
                    "position",
                    "location",
                ],
                [
                    "Bottom",
                    "Middle",
                    "Top",
                ][
                    min(i, 2)
                ],
            )

            normalized.append(
                {
                    "position": str(position),
                    "agitator_type": str(imp_type),
                    "diameter_m": _safe_float(
                        diameter,
                        tank_diameter_m * 0.5,
                    ),
                    "elevation_m": _safe_float(
                        elevation,
                        0.4,
                    ),
                }
            )

    # --------------------------------------------------------
    # Legacy single / multiple impeller input
    # --------------------------------------------------------

    if not normalized:

        nimp = max(
            1,
            _safe_int(
                number_impellers,
                1,
            ),
        )

        diameter = _safe_float(
            impeller_diameter_m,
            tank_diameter_m * 0.5,
        )

        positions = [
            "Bottom",
            "Middle",
            "Top",
        ]

        for i in range(nimp):

            elevation = (
                impeller_clearance_m +
                i *
                0.90 *
                diameter
            )

            normalized.append(
                {
                    "position": positions[
                        min(i, 2)
                    ],
                    "agitator_type": str(
                        agitator
                    ),
                    "diameter_m": diameter,
                    "elevation_m": elevation,
                }
            )

    return normalized


# ============================================================
# HEAD GEOMETRY
# ============================================================

def _head_depth(
    diameter,
    head_type,
):

    text = str(
        head_type or ""
    ).lower()

    if "2:1" in text:
        return 0.25 * diameter

    if "ellipsoidal" in text:
        return 0.25 * diameter

    if "torispherical" in text:
        return 0.10 * diameter

    if "flat" in text:
        return 0.0

    return 0.10 * diameter


# ============================================================
# VESSEL GEOMETRY
# ============================================================

def _vessel_geometry(
    tank_diameter_m,
    straight_height_m,
    bottom_type,
    top_type,
):

    D = _safe_float(
        tank_diameter_m,
        2.0,
    )

    H = _safe_float(
        straight_height_m,
        3.0,
    )

    radius = D / 2.0

    bottom_depth = _head_depth(
        D,
        bottom_type,
    )

    top_depth = _head_depth(
        D,
        top_type,
    )

    straight_bottom = (
        bottom_depth
    )

    straight_top = (
        bottom_depth +
        H
    )

    total_height = (
        bottom_depth +
        H +
        top_depth
    )

    cross_section_area = (
        math.pi *
        radius ** 2
    )

    # Approximate head volume
    bottom_volume = (
        0.50 *
        cross_section_area *
        bottom_depth
    )

    top_volume = (
        0.50 *
        cross_section_area *
        top_depth
    )

    cylinder_volume = (
        cross_section_area *
        H
    )

    total_volume = (
        bottom_volume +
        cylinder_volume +
        top_volume
    )

    return {
        "diameter": D,
        "radius": radius,
        "straight_height": H,
        "bottom_depth": bottom_depth,
        "top_depth": top_depth,
        "straight_bottom": straight_bottom,
        "straight_top": straight_top,
        "total_height": total_height,
        "area": cross_section_area,
        "vessel_volume_m3": total_volume,
    }


# ============================================================
# LIQUID LEVEL CALCULATION
# ============================================================

def _liquid_level_from_volume(
    working_volume_m3,
    geometry,
):

    V = _safe_float(
        working_volume_m3,
        0.0,
    )

    area = geometry["area"]

    bottom_depth = geometry[
        "bottom_depth"
    ]

    straight_height = geometry[
        "straight_height"
    ]

    top_depth = geometry[
        "top_depth"
    ]

    bottom_volume = (
        0.50 *
        area *
        bottom_depth
    )

    straight_volume = (
        area *
        straight_height
    )

    top_volume = (
        0.50 *
        area *
        top_depth
    )

    vessel_volume = (
        bottom_volume +
        straight_volume +
        top_volume
    )

    V = _clamp(
        V,
        0.0,
        vessel_volume,
    )

    # Bottom head
    if V <= bottom_volume:

        if bottom_volume <= 0:
            return 0.0

        fraction = (
            V /
            bottom_volume
        )

        return (
            bottom_depth *
            fraction
        )

    # Straight section
    if V <= (
        bottom_volume +
        straight_volume
    ):

        remaining = (
            V -
            bottom_volume
        )

        return (
            bottom_depth +
            remaining /
            max(area, 1e-12)
        )

    # Top head
    remaining = (
        V -
        bottom_volume -
        straight_volume
    )

    if top_volume <= 0:
        return geometry[
            "straight_top"
        ]

    fraction = (
        remaining /
        top_volume
    )

    return _clamp(
        geometry["straight_top"] +
        fraction *
        top_depth,
        0.0,
        geometry["total_height"],
    )


# ============================================================
# VESSEL CYLINDER
# ============================================================

def _cylinder_surface(
    radius,
    z_bottom,
    z_top,
    theta_points=70,
    z_points=25,
):

    theta = np.linspace(
        0,
        2 * np.pi,
        theta_points,
    )

    z = np.linspace(
        z_bottom,
        z_top,
        z_points,
    )

    T, Z = np.meshgrid(
        theta,
        z,
    )

    X = (
        radius *
        np.cos(T)
    )

    Y = (
        radius *
        np.sin(T)
    )

    return X, Y, Z


# ============================================================
# HEAD SURFACE
# ============================================================

def _head_surface(
    radius,
    z_base,
    depth,
    top=True,
    theta_points=70,
    phi_points=25,
):

    if depth <= 0:
        return (
            np.empty((0, 0)),
            np.empty((0, 0)),
            np.empty((0, 0)),
        )

    theta = np.linspace(
        0,
        2 * np.pi,
        theta_points,
    )

    phi = np.linspace(
        0,
        np.pi / 2,
        phi_points,
    )

    T, P = np.meshgrid(
        theta,
        phi,
    )

    X = (
        radius *
        np.sin(P) *
        np.cos(T)
    )

    Y = (
        radius *
        np.sin(P) *
        np.sin(T)
    )

    if top:

        Z = (
            z_base +
            depth *
            np.cos(P)
        )

    else:

        Z = (
            z_base -
            depth *
            np.cos(P)
        )

    return X, Y, Z


# ============================================================
# REACTOR SHELL
# ============================================================

def _add_vessel_shell(
    fig,
    geometry,
):

    radius = geometry[
        "radius"
    ]

    # Straight shell
    X, Y, Z = _cylinder_surface(
        radius,
        geometry["straight_bottom"],
        geometry["straight_top"],
    )

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.16,
            showscale=False,
            name="Reactor Shell",
            hoverinfo="skip",
        )
    )

    # Bottom head
    if geometry["bottom_depth"] > 0:

        X, Y, Z = _head_surface(
            radius,
            geometry["straight_bottom"],
            geometry["bottom_depth"],
            top=False,
        )

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                opacity=0.16,
                showscale=False,
                name="Bottom Head",
                hoverinfo="skip",
            )
        )

    # Top head
    if geometry["top_depth"] > 0:

        X, Y, Z = _head_surface(
            radius,
            geometry["straight_top"],
            geometry["top_depth"],
            top=True,
        )

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                opacity=0.16,
                showscale=False,
                name="Top Head",
                hoverinfo="skip",
            )
        )


# ============================================================
# LIQUID SURFACE
# ============================================================

def _liquid_surface(
    radius,
    liquid_level,
    vortex_depth=0.0,
    resolution=70,
):

    r = np.linspace(
        0,
        radius * 0.995,
        resolution,
    )

    theta = np.linspace(
        0,
        2 * np.pi,
        resolution,
    )

    R, T = np.meshgrid(
        r,
        theta,
    )

    X = (
        R *
        np.cos(T)
    )

    Y = (
        R *
        np.sin(T)
    )

    radial_factor = (
        1 -
        (
            R /
            max(radius, 1e-12)
        ) ** 2
    )

    Z = (
        liquid_level -
        vortex_depth *
        radial_factor
    )

    return X, Y, Z


# ============================================================
# BAFFLES
# ============================================================

def _add_baffles(
    fig,
    radius,
    z_bottom,
    z_top,
    number_baffles=4,
):

    number_baffles = max(
        0,
        _safe_int(
            number_baffles,
            4,
        ),
    )

    if number_baffles == 0:
        return

    radial_position = (
        radius *
        0.91
    )

    width = max(
        radius * 0.08,
        0.03,
    )

    for i in range(
        number_baffles
    ):

        angle = (
            2 *
            np.pi *
            i /
            number_baffles
        )

        cx = (
            radial_position *
            np.cos(angle)
        )

        cy = (
            radial_position *
            np.sin(angle)
        )

        tx = -np.sin(angle)
        ty = np.cos(angle)

        x1 = (
            cx +
            width / 2 *
            tx
        )

        y1 = (
            cy +
            width / 2 *
            ty
        )

        x2 = (
            cx -
            width / 2 *
            tx
        )

        y2 = (
            cy -
            width / 2 *
            ty
        )

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x1,
                    x2,
                    x2,
                    x1,
                    x1,
                ],
                y=[
                    y1,
                    y2,
                    y2,
                    y1,
                    y1,
                ],
                z=[
                    z_bottom,
                    z_bottom,
                    z_top,
                    z_top,
                    z_bottom,
                ],
                mode="lines",
                line=dict(
                    width=8,
                ),
                name="Baffle",
                showlegend=(
                    i == 0
                ),
                hoverinfo="skip",
            )
        )


# ============================================================
# SHAFT
# ============================================================

def _add_shaft(
    fig,
    radius,
    z_bottom,
    z_top,
):

    shaft_radius = max(
        radius * 0.05,
        0.025,
    )

    theta = np.linspace(
        0,
        2 * np.pi,
        30,
    )

    z = np.linspace(
        z_bottom,
        z_top,
        30,
    )

    T, Z = np.meshgrid(
        theta,
        z,
    )

    X = (
        shaft_radius *
        np.cos(T)
    )

    Y = (
        shaft_radius *
        np.sin(T)
    )

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.65,
            showscale=False,
            name="Agitator Shaft",
            hoverinfo="skip",
        )
    )


# ============================================================
# IMPELLER VISUALIZATION
# ============================================================

def _impeller_trace(
    impeller_type,
    diameter,
    elevation,
):

    traces = []

    D = max(
        _safe_float(
            diameter,
            1.0,
        ),
        0.02,
    )

    R = D / 2

    name = str(
        impeller_type
    )

    text = name.lower()

    # --------------------------------------------------------
    # RUSHTON
    # --------------------------------------------------------

    if "rushton" in text:

        blades = 6

        for i in range(blades):

            angle = (
                2 *
                np.pi *
                i /
                blades
            )

            hub_r = (
                0.12 *
                R
            )

            x0 = (
                hub_r *
                np.cos(angle)
            )

            y0 = (
                hub_r *
                np.sin(angle)
            )

            x1 = (
                0.90 *
                R *
                np.cos(angle)
            )

            y1 = (
                0.90 *
                R *
                np.sin(angle)
            )

            tangential = (
                angle +
                np.pi / 2
            )

            width = (
                0.12 *
                D
            )

            xa = (
                x1 +
                width *
                np.cos(tangential)
            )

            ya = (
                y1 +
                width *
                np.sin(tangential)
            )

            xb = (
                x1 -
                width *
                np.cos(tangential)
            )

            yb = (
                y1 -
                width *
                np.sin(tangential)
            )

            traces.append(
                go.Scatter3d(
                    x=[
                        x0,
                        xa,
                        xb,
                        x0,
                    ],
                    y=[
                        y0,
                        ya,
                        yb,
                        y0,
                    ],
                    z=[
                        elevation,
                        elevation,
                        elevation,
                        elevation,
                    ],
                    mode="lines",
                    line=dict(
                        width=12,
                    ),
                    name=name,
                    showlegend=(
                        i == 0
                    ),
                    hoverinfo="skip",
                )
            )

    # --------------------------------------------------------
    # PBT
    # --------------------------------------------------------

    elif (
        "pitched" in text or
        "pbt" in text
    ):

        blades = 4

        for i in range(blades):

            angle = (
                2 *
                np.pi *
                i /
                blades
            )

            r = np.linspace(
                0.10 * R,
                0.92 * R,
                30,
            )

            x = (
                r *
                np.cos(angle)
            )

            y = (
                r *
                np.sin(angle)
            )

            z = (
                elevation +
                0.12 *
                D *
                r /
                max(R, 1e-12)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=12,
                    ),
                    name=name,
                    showlegend=(
                        i == 0
                    ),
                    hoverinfo="skip",
                )
            )

    # --------------------------------------------------------
    # HYDROFOIL
    # --------------------------------------------------------

    elif "hydrofoil" in text:

        blades = 3

        for i in range(blades):

            angle = (
                2 *
                np.pi *
                i /
                blades
            )

            r = np.linspace(
                0.10 * R,
                0.95 * R,
                35,
            )

            x = (
                r *
                np.cos(angle)
            )

            y = (
                r *
                np.sin(angle)
            )

            z = (
                elevation +
                0.05 *
                D *
                r /
                max(R, 1e-12)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=12,
                    ),
                    name=name,
                    showlegend=(
                        i == 0
                    ),
                    hoverinfo="skip",
                )
            )

    # --------------------------------------------------------
    # MARINE PROPELLER
    # --------------------------------------------------------

    elif (
        "marine" in text or
        "propeller" in text
    ):

        blades = 3

        for i in range(blades):

            base = (
                2 *
                np.pi *
                i /
                blades
            )

            r = np.linspace(
                0.10 * R,
                0.96 * R,
                40,
            )

            angle = (
                base +
                0.40 *
                r /
                max(R, 1e-12)
            )

            x = (
                r *
                np.cos(angle)
            )

            y = (
                r *
                np.sin(angle)
            )

            z = (
                elevation +
                0.10 *
                D *
                r /
                max(R, 1e-12)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=11,
                    ),
                    name=name,
                    showlegend=(
                        i == 0
                    ),
                    hoverinfo="skip",
                )
            )

    # --------------------------------------------------------
    # ANCHOR
    # --------------------------------------------------------

    elif "anchor" in text:

        theta = np.linspace(
            0,
            2 * np.pi,
            150,
        )

        x = (
            0.90 *
            R *
            np.cos(theta)
        )

        y = (
            0.90 *
            R *
            np.sin(theta)
        )

        z = np.full_like(
            theta,
            elevation,
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=13,
                ),
                name=name,
                showlegend=True,
                hoverinfo="skip",
            )
        )

    # --------------------------------------------------------
    # HELICAL RIBBON
    # --------------------------------------------------------

    elif "helical" in text:

        theta = np.linspace(
            0,
            4 * np.pi,
            220,
        )

        x = (
            0.90 *
            R *
            np.cos(theta)
        )

        y = (
            0.90 *
            R *
            np.sin(theta)
        )

        z = (
            elevation -
            0.30 * D +
            0.60 *
            D *
            theta /
            (4 * np.pi)
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=10,
                ),
                name=name,
                showlegend=True,
                hoverinfo="skip",
            )
        )

    # --------------------------------------------------------
    # RCI / GENERIC
    # --------------------------------------------------------

    else:

        theta = np.linspace(
            0,
            2 * np.pi,
            120,
        )

        x = (
            R *
            np.cos(theta)
        )

        y = (
            R *
            np.sin(theta)
        )

        z = np.full_like(
            theta,
            elevation,
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=10,
                ),
                name=name,
                showlegend=True,
                hoverinfo="skip",
            )
        )

    return traces


# ============================================================
# FLOW FIELD MODEL
# ============================================================

def _flow_field(
    radius,
    liquid_level,
    impellers,
    rpm,
    radial_points=14,
    angular_points=24,
    vertical_points=12,
):

    if not impellers:
        return []

    omega = (
        2 *
        np.pi *
        rpm /
        60
    )

    field = []

    for impeller in impellers:

        D = _safe_float(
            impeller.get(
                "diameter_m",
                radius,
            ),
            radius,
        )

        elevation = _safe_float(
            impeller.get(
                "elevation_m",
                liquid_level * 0.3,
            ),
            liquid_level * 0.3,
        )

        Ri = D / 2

        for iz in range(
            vertical_points
        ):

            z = (
                0.05 *
                liquid_level +
                (
                    0.90 *
                    liquid_level
                ) *
                iz /
                max(
                    vertical_points - 1,
                    1,
                )
            )

            for ir in range(
                1,
                radial_points
            ):

                r = (
                    radius *
                    ir /
                    radial_points
                )

                for ia in range(
                    angular_points
                ):

                    theta = (
                        2 *
                        np.pi *
                        ia /
                        angular_points
                    )

                    dz = (
                        z -
                        elevation
                    )

                    axial_influence = np.exp(
                        -abs(dz) /
                        max(
                            1.5 * D,
                            1e-6,
                        )
                    )

                    radial_influence = np.exp(
                        -abs(
                            r -
                            Ri
                        ) /
                        max(
                            0.50 *
                            radius,
                            1e-6,
                        )
                    )

                    influence = (
                        axial_influence *
                        radial_influence
                    )

                    # Tangential velocity
                    vtheta = (
                        omega *
                        r *
                        0.55 *
                        influence
                    )

                    # Radial velocity
                    vr = (
                        omega *
                        Ri *
                        0.30 *
                        influence *
                        (
                            1 -
                            r /
                            max(
                                radius,
                                1e-12,
                            )
                        )
                    )

                    # Axial circulation
                    vz = (
                        omega *
                        Ri *
                        0.20 *
                        influence
                    )

                    if z > elevation:
                        vz *= -1

                    # Wall return
                    if r > (
                        0.70 *
                        radius
                    ):

                        vr *= -1.30
                        vz *= 1.30

                    erx = np.cos(theta)
                    ery = np.sin(theta)

                    etx = -np.sin(theta)
                    ety = np.cos(theta)

                    vx = (
                        vr * erx +
                        vtheta * etx
                    )

                    vy = (
                        vr * ery +
                        vtheta * ety
                    )

                    speed = math.sqrt(
                        vx ** 2 +
                        vy ** 2 +
                        vz ** 2
                    )

                    field.append(
                        {
                            "x":
                                r *
                                np.cos(theta),
                            "y":
                                r *
                                np.sin(theta),
                            "z":
                                z,
                            "vx": vx,
                            "vy": vy,
                            "vz": vz,
                            "speed":
                                speed,
                        }
                    )

    return field


# ============================================================
# FLOW STREAMLINES
# ============================================================

def _streamlines(
    radius,
    liquid_level,
    impellers,
    rpm,
    number_lines=24,
):

    if not impellers:
        return []

    omega = (
        2 *
        np.pi *
        rpm /
        60
    )

    traces = []

    for line in range(
        number_lines
    ):

        theta = (
            2 *
            np.pi *
            line /
            number_lines
        )

        r = (
            radius *
            (
                0.10 +
                0.80 *
                (
                    line %
                    10
                ) /
                10
            )
        )

        z = (
            liquid_level *
            (
                0.10 +
                0.80 *
                (
                    line %
                    8
                ) /
                8
            )
        )

        xs = []
        ys = []
        zs = []

        for _ in range(140):

            nearest = min(
                impellers,
                key=lambda imp:
                abs(
                    z -
                    _safe_float(
                        imp.get(
                            "elevation_m",
                            liquid_level / 2,
                        ),
                        liquid_level / 2,
                    )
                ),
            )

            D = _safe_float(
                nearest.get(
                    "diameter_m",
                    radius,
                ),
                radius,
            )

            elevation = _safe_float(
                nearest.get(
                    "elevation_m",
                    liquid_level / 2,
                ),
                liquid_level / 2,
            )

            Ri = D / 2

            influence = np.exp(
                -abs(
                    z -
                    elevation
                ) /
                max(
                    D * 1.5,
                    1e-6,
                )
            )

            vtheta = (
                omega *
                r *
                0.45 *
                influence
            )

            vr = (
                omega *
                Ri *
                0.20 *
                influence
            )

            vz = (
                omega *
                Ri *
                0.15 *
                influence
            )

            if z > elevation:
                vz *= -1

            if r > (
                0.72 *
                radius
            ):

                vr *= -1.35
                vz *= 1.25

            dt = 0.010

            r += (
                vr *
                dt
            )

            z += (
                vz *
                dt
            )

            theta += (
                vtheta /
                max(r, 0.02) *
                dt
            )

            r = _clamp(
                r,
                radius * 0.08,
                radius * 0.94,
            )

            z = _clamp(
                z,
                0.03,
                liquid_level - 0.03,
            )

            xs.append(
                r *
                np.cos(theta)
            )

            ys.append(
                r *
                np.sin(theta)
            )

            zs.append(z)

        traces.append(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="lines",
                line=dict(
                    width=4,
                ),
                opacity=0.65,
                name="Flow Path",
                showlegend=(
                    line == 0
                ),
                hoverinfo="skip",
            )
        )

    return traces


# ============================================================
# PARTICLES
# ============================================================

def _particles(
    radius,
    liquid_level,
    count=300,
):

    rng = np.random.default_rng(
        42
    )

    r = (
        radius *
        np.sqrt(
            rng.random(
                count
            )
        ) *
        0.90
    )

    theta = (
        2 *
        np.pi *
        rng.random(
            count
        )
    )

    z = (
        0.04 *
        liquid_level +
        0.92 *
        liquid_level *
        rng.random(
            count
        )
    )

    x = (
        r *
        np.cos(theta)
    )

    y = (
        r *
        np.sin(theta)
    )

    return x, y, z


# ============================================================
# DEAD ZONE DETECTION
# ============================================================

def _dead_zone_field(
    flow,
    speed_limit_fraction=0.15,
):

    if not flow:
        return []

    speeds = np.array(
        [
            p["speed"]
            for p in flow
        ]
    )

    max_speed = max(
        float(
            np.max(speeds)
        ),
        1e-12,
    )

    threshold = (
        max_speed *
        speed_limit_fraction
    )

    dead = [
        p
        for p in flow
        if p["speed"] <= threshold
    ]

    return dead


# ============================================================
# VELOCITY PROFILE
# ============================================================

def _add_velocity_profile(
    fig,
    flow,
):

    if not flow:
        return

    # Limit point count
    maximum = 2500

    if len(flow) > maximum:

        indexes = np.linspace(
            0,
            len(flow) - 1,
            maximum,
        ).astype(int)

        flow = [
            flow[i]
            for i in indexes
        ]

    x = np.array(
        [
            p["x"]
            for p in flow
        ]
    )

    y = np.array(
        [
            p["y"]
            for p in flow
        ]
    )

    z = np.array(
        [
            p["z"]
            for p in flow
        ]
    )

    speed = np.array(
        [
            p["speed"]
            for p in flow
        ]
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=3.5,
                color=speed,
                colorscale="Turbo",
                opacity=0.80,
                colorbar=dict(
                    title="Velocity<br>m/s"
                ),
            ),
            name="Velocity Profile",
            hovertemplate=(
                "Velocity = "
                "%{marker.color:.3f} m/s"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# DEAD ZONE PROFILE
# ============================================================

def _add_dead_zone_profile(
    fig,
    flow,
):

    dead = _dead_zone_field(
        flow,
        0.15,
    )

    if not dead:
        return

    x = np.array(
        [
            p["x"]
            for p in dead
        ]
    )

    y = np.array(
        [
            p["y"]
            for p in dead
        ]
    )

    z = np.array(
        [
            p["z"]
            for p in dead
        ]
    )

    speed = np.array(
        [
            p["speed"]
            for p in dead
        ]
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=5,
                color=speed,
                colorscale="Viridis",
                opacity=0.85,
                colorbar=dict(
                    title="Low Velocity<br>m/s"
                ),
            ),
            name="Potential Dead Zones",
            hovertemplate=(
                "Velocity = "
                "%{marker.color:.3f} m/s"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# FLOW VECTOR PROFILE
# ============================================================

def _add_flow_vectors(
    fig,
    flow,
):

    if not flow:
        return

    maximum = 350

    if len(flow) > maximum:

        indexes = np.linspace(
            0,
            len(flow) - 1,
            maximum,
        ).astype(int)

        flow = [
            flow[i]
            for i in indexes
        ]

    for p in flow:

        scale = 0.10

        x0 = p["x"]
        y0 = p["y"]
        z0 = p["z"]

        x1 = (
            x0 +
            p["vx"] *
            scale
        )

        y1 = (
            y0 +
            p["vy"] *
            scale
        )

        z1 = (
            z0 +
            p["vz"] *
            scale
        )

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x0,
                    x1,
                ],
                y=[
                    y0,
                    y1,
                ],
                z=[
                    z0,
                    z1,
                ],
                mode="lines",
                line=dict(
                    width=3,
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# DIMENSIONS
# ============================================================

def _add_dimensions(
    fig,
    geometry,
    liquid_level,
):

    radius = geometry[
        "radius"
    ]

    top = geometry[
        "straight_top"
    ]

    # Tank diameter
    fig.add_trace(
        go.Scatter3d(
            x=[
                -radius,
                radius,
            ],
            y=[
                0,
                0,
            ],
            z=[
                top,
                top,
            ],
            mode="lines+text",
            text=[
                "",
                f"ID = {geometry['diameter']:.2f} m",
            ],
            textposition="top center",
            line=dict(
                width=5,
            ),
            name="Tank Diameter",
        )
    )

    # Liquid level
    fig.add_trace(
        go.Scatter3d(
            x=[
                -radius * 0.98,
                radius * 0.98,
            ],
            y=[
                0,
                0,
            ],
            z=[
                liquid_level,
                liquid_level,
            ],
            mode="lines+text",
            text=[
                "",
                f"Liquid Level = {liquid_level:.2f} m",
            ],
            textposition="middle right",
            line=dict(
                width=5,
                dash="dash",
            ),
            name="Liquid Level",
        )
    )


# ============================================================
# VORTEX
# ============================================================

def _vortex_depth(
    liquid_level,
    rpm,
    tank_diameter,
):

    N = (
        rpm /
        60.0
    )

    Fr = (
        N ** 2 *
        tank_diameter /
        G
    )

    depth = (
        liquid_level *
        0.05 *
        math.sqrt(
            max(
                Fr,
                0,
            )
        )
    )

    return _clamp(
        depth,
        0,
        liquid_level * 0.30,
    )


# ============================================================
# VORTEX VISUALIZATION
# ============================================================

def _add_vortex(
    fig,
    radius,
    liquid_level,
    vortex_depth,
):

    X, Y, Z = _liquid_surface(
        radius,
        liquid_level,
        vortex_depth,
    )

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.65,
            showscale=False,
            name="Vortex Surface",
            hovertemplate=(
                "Vortex Surface"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            ),
        )
    )

    # Center depth indicator
    fig.add_trace(
        go.Scatter3d(
            x=[
                0,
                0,
            ],
            y=[
                0,
                0,
            ],
            z=[
                liquid_level,
                liquid_level -
                vortex_depth,
            ],
            mode="lines+text",
            text=[
                "",
                f"Vortex Depth ≈ {vortex_depth:.3f} m",
            ],
            textposition="middle right",
            line=dict(
                width=6,
                dash="dot",
            ),
            name="Vortex Depth",
        )
    )


# ============================================================
# GAS BUBBLES
# ============================================================

def _add_gas_bubbles(
    fig,
    radius,
    liquid_level,
    gas_flow_m3_h,
    bubble_diameter_mm,
):

    if gas_flow_m3_h <= 0:
        return

    rng = np.random.default_rng(
        101
    )

    count = 180

    radial = (
        radius *
        0.20 *
        np.sqrt(
            rng.random(
                count
            )
        )
    )

    theta = (
        2 *
        np.pi *
        rng.random(
            count
        )
    )

    x = (
        radial *
        np.cos(theta)
    )

    y = (
        radial *
        np.sin(theta)
    )

    z = (
        liquid_level *
        (
            0.05 +
            0.85 *
            rng.random(
                count
            )
        )
    )

    size = np.full(
        count,
        _clamp(
            bubble_diameter_mm *
            1.5,
            3,
            12,
        ),
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=size,
                opacity=0.65,
            ),
            name="Gas Bubbles",
        )
    )


# ============================================================
# MAIN FUNCTION
# ============================================================

def create_reactor_animation(
    # --------------------------------------------------------
    # New interface
    # --------------------------------------------------------

    volume_m3=None,
    tank_diameter_m=None,
    straight_height_m=None,
    liquid_height_m=None,

    rpm=100.0,

    impellers=None,

    bottom_type="10% Torispherical",
    top_type="10% Torispherical",

    number_baffles=4,

    density_kg_m3=1000.0,
    viscosity_pa_s=0.001,

    gas_flow_m3_h=0.0,
    bubble_diameter_mm=3.0,
    gas_holdup_fraction=0.05,

    # --------------------------------------------------------
    # Visualization selection
    # --------------------------------------------------------

    display_mode="Reactor Geometry",

    show_liquid=True,
    show_vortex=False,
    show_velocity=False,
    show_flow=False,
    show_dead_zones=False,
    show_particles=False,
    show_gas=False,
    show_baffles=True,
    show_dimensions=True,

    # --------------------------------------------------------
    # Animation
    # --------------------------------------------------------

    animate=False,
    frames=30,

    # --------------------------------------------------------
    # Legacy interface
    # --------------------------------------------------------

    D=None,
    H=None,
    volume=None,
    liquid_level=None,

    agitator="Rushton Turbine",
    impeller_diameter_m=None,
    number_impellers=1,
    impeller_clearance_m=0.4,

    **kwargs,
):

    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================

    if tank_diameter_m is None:
        tank_diameter_m = D

    if tank_diameter_m is None:
        tank_diameter_m = 2.0

    if straight_height_m is None:
        straight_height_m = H

    if straight_height_m is None:
        straight_height_m = 3.0

    if volume_m3 is None:
        volume_m3 = volume

    if volume_m3 is None:
        volume_m3 = 10.0

    if liquid_height_m is None:
        liquid_height_m = liquid_level

    # ========================================================
    # SAFE VALUES
    # ========================================================

    tank_diameter_m = max(
        _safe_float(
            tank_diameter_m,
            2.0,
        ),
        0.10,
    )

    straight_height_m = max(
        _safe_float(
            straight_height_m,
            3.0,
        ),
        0.10,
    )

    volume_m3 = max(
        _safe_float(
            volume_m3,
            10.0,
        ),
        0.0,
    )

    rpm = max(
        _safe_float(
            rpm,
            100.0,
        ),
        0.0,
    )

    # ========================================================
    # GEOMETRY
    # ========================================================

    geometry = _vessel_geometry(
        tank_diameter_m,
        straight_height_m,
        bottom_type,
        top_type,
    )

    # ========================================================
    # LIQUID LEVEL
    # ========================================================

    if liquid_height_m is None:

        liquid_level = (
            _liquid_level_from_volume(
                volume_m3,
                geometry,
            )
        )

    else:

        liquid_level = _safe_float(
            liquid_height_m,
            _liquid_level_from_volume(
                volume_m3,
                geometry,
            ),
        )

    liquid_level = _clamp(
        liquid_level,
        0.02,
        geometry["total_height"] * 0.995,
    )

    # ========================================================
    # IMPELLERS
    # ========================================================

    impellers = _normalize_impellers(
        impellers=impellers,
        tank_diameter_m=tank_diameter_m,
        impeller_diameter_m=impeller_diameter_m,
        impeller_clearance_m=impeller_clearance_m,
        agitator=agitator,
        number_impellers=number_impellers,
    )

    # ========================================================
    # FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # MODE NORMALIZATION
    # ========================================================

    mode = str(
        display_mode or
        "Reactor Geometry"
    ).strip().lower()

    # --------------------------------------------------------
    # If explicit flags are supplied, respect them
    # --------------------------------------------------------

    if (
        mode == "liquid level"
    ):

        show_liquid = True
        show_vortex = False
        show_velocity = False
        show_flow = False
        show_dead_zones = False
        show_particles = False
        show_gas = False

    elif (
        mode == "vortex formation" or
        mode == "vortex"
    ):

        show_liquid = False
        show_vortex = True
        show_velocity = False
        show_flow = False
        show_dead_zones = False
        show_particles = False
        show_gas = False

    elif (
        mode == "velocity profile" or
        mode == "velocity"
    ):

        show_liquid = False
        show_vortex = False
        show_velocity = True
        show_flow = False
        show_dead_zones = False
        show_particles = False
        show_gas = False

    elif (
        mode == "flow profile" or
        mode == "flow"
    ):

        show_liquid = False
        show_vortex = False
        show_velocity = False
        show_flow = True
        show_dead_zones = False
        show_particles = False
        show_gas = False

    elif (
        mode == "dead zone analysis" or
        mode == "dead zones"
    ):

        show_liquid = False
        show_vortex = False
        show_velocity = False
        show_flow = False
        show_dead_zones = True
        show_particles = False
        show_gas = False

    elif (
        mode == "mixing particles" or
        mode == "particles"
    ):

        show_liquid = True
        show_vortex = False
        show_velocity = False
        show_flow = False
        show_dead_zones = False
        show_particles = True
        show_gas = False

    elif (
        mode == "gas-liquid"
    ):

        show_liquid = True
        show_vortex = False
        show_velocity = False
        show_flow = True
        show_dead_zones = False
        show_particles = False
        show_gas = True

    # ========================================================
    # REACTOR SHELL
    # ========================================================

    _add_vessel_shell(
        fig,
        geometry,
    )

    # ========================================================
    # BAFFLES
    # ========================================================

    if show_baffles:

        _add_baffles(
            fig,
            geometry["radius"],
            geometry["straight_bottom"],
            min(
                geometry["straight_top"],
                liquid_level,
            ),
            number_baffles,
        )

    # ========================================================
    # SHAFT
    # ========================================================

    _add_shaft(
        fig,
        geometry["radius"],
        geometry["straight_bottom"],
        geometry["straight_top"],
    )

    # ========================================================
    # IMPELLERS
    # ========================================================

    for impeller in impellers:

        traces = _impeller_trace(
            impeller[
                "agitator_type"
            ],
            impeller[
                "diameter_m"
            ],
            impeller[
                "elevation_m"
            ],
        )

        for trace in traces:
            fig.add_trace(trace)

    # ========================================================
    # LIQUID LEVEL
    # ========================================================

    if show_liquid:

        X, Y, Z = _liquid_surface(
            geometry["radius"],
            liquid_level,
            0.0,
        )

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                opacity=0.55,
                showscale=False,
                name="Liquid",
                hovertemplate=(
                    "Liquid Surface"
                    "<br>Z = %{z:.2f} m"
                    "<extra></extra>"
                ),
            )
        )

    # ========================================================
    # FLOW FIELD
    # ========================================================

    flow = []

    if (
        show_velocity or
        show_flow or
        show_dead_zones
    ):

        flow = _flow_field(
            geometry["radius"],
            liquid_level,
            impellers,
            rpm,
        )

    # ========================================================
    # VELOCITY PROFILE
    # ========================================================

    if show_velocity:

        _add_velocity_profile(
            fig,
            flow,
        )

    # ========================================================
    # FLOW PROFILE
    # ========================================================

    if show_flow:

        streamlines = _streamlines(
            geometry["radius"],
            liquid_level,
            impellers,
            rpm,
        )

        for trace in streamlines:
            fig.add_trace(trace)

        _add_flow_vectors(
            fig,
            flow,
        )

    # ========================================================
    # DEAD ZONES
    # ========================================================

    if show_dead_zones:

        _add_dead_zone_profile(
            fig,
            flow,
        )

    # ========================================================
    # VORTEX
    # ========================================================

    if show_vortex:

        depth = _vortex_depth(
            liquid_level,
            rpm,
            tank_diameter_m,
        )

        _add_vortex(
            fig,
            geometry["radius"],
            liquid_level,
            depth,
        )

    # ========================================================
    # PARTICLES
    # ========================================================

    particle_trace_index = None

    if show_particles:

        px, py, pz = _particles(
            geometry["radius"],
            liquid_level,
            400,
        )

        particle_trace_index = len(
            fig.data
        )

        fig.add_trace(
            go.Scatter3d(
                x=px,
                y=py,
                z=pz,
                mode="markers",
                marker=dict(
                    size=3,
                    opacity=0.75,
                ),
                name="Mixing Particles",
            )
        )

    # ========================================================
    # GAS
    # ========================================================

    if show_gas:

        _add_gas_bubbles(
            fig,
            geometry["radius"],
            liquid_level,
            gas_flow_m3_h,
            bubble_diameter_mm,
        )

    # ========================================================
    # DIMENSIONS
    # ========================================================

    if show_dimensions:

        _add_dimensions(
            fig,
            geometry,
            liquid_level,
        )

    # ========================================================
    # ANIMATION
    # ========================================================

    if (
        animate and
        particle_trace_index is not None
    ):

        px, py, pz = _particles(
            geometry["radius"],
            liquid_level,
            400,
        )

        r = np.sqrt(
            px ** 2 +
            py ** 2
        )

        theta = np.arctan2(
            py,
            px,
        )

        animation_frames = []

        total_frames = max(
            2,
            _safe_int(
                frames,
                30,
            ),
        )

        for i in range(
            total_frames
        ):

            angle = (
                2 *
                np.pi *
                i /
                total_frames
            )

            rotation = (
                0.20 +
                0.80 *
                (
                    1 -
                    r /
                    max(
                        geometry["radius"],
                        1e-12,
                    )
                )
            )

            new_theta = (
                theta +
                angle *
                rotation
            )

            new_z = (
                pz +
                0.05 *
                liquid_level *
                np.sin(
                    (
                        2 *
                        np.pi *
                        pz /
                        max(
                            liquid_level,
                            1e-12,
                        )
                    ) +
                    angle
                )
            )

            new_z = np.clip(
                new_z,
                0.02,
                liquid_level - 0.02,
            )

            new_x = (
                r *
                np.cos(
                    new_theta
                )
            )

            new_y = (
                r *
                np.sin(
                    new_theta
                )
            )

            animation_frames.append(
                go.Frame(
                    data=[
                        go.Scatter3d(
                            x=new_x,
                            y=new_y,
                            z=new_z,
                        )
                    ],
                    traces=[
                        particle_trace_index
                    ],
                    name=str(i),
                )
            )

        fig.frames = (
            animation_frames
        )

        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    x=0.02,
                    y=1.08,
                    buttons=[
                        dict(
                            label="▶ Start Mixing",
                            method="animate",
                            args=[
                                None,
                                {
                                    "frame": {
                                        "duration": 100,
                                        "redraw": True,
                                    },
                                    "fromcurrent": True,
                                },
                            ],
                        ),
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[
                                [None],
                                {
                                    "frame": {
                                        "duration": 0,
                                        "redraw": False,
                                    },
                                    "mode": "immediate",
                                },
                            ],
                        ),
                    ],
                )
            ]
        )

    # ========================================================
    # TITLE
    # ========================================================

    title_map = {
        "reactor geometry":
            "3D Reactor Geometry",

        "liquid level":
            "3D Liquid Level",

        "vortex formation":
            "3D Vortex Formation",

        "vortex":
            "3D Vortex Formation",

        "velocity profile":
            "3D Velocity Profile",

        "velocity":
            "3D Velocity Profile",

        "flow profile":
            "3D Flow Profile",

        "flow":
            "3D Flow Profile",

        "dead zone analysis":
            "3D Dead Zone Analysis",

        "dead zones":
            "3D Dead Zone Analysis",

        "mixing particles":
            "3D Mixing Particle Visualization",

        "particles":
            "3D Mixing Particle Visualization",

        "gas-liquid":
            "3D Gas–Liquid Mixing",
    }

    title = title_map.get(
        mode,
        "3D Reactor Visualization",
    )

    fig.update_layout(

        title=dict(
            text=(
                f"{title}"
                "<br>"
                f"<sup>"
                f"ID = {tank_diameter_m:.2f} m"
                f" | Liquid Level = "
                f"{liquid_level:.2f} m"
                f" | RPM = {rpm:.0f}"
                f"</sup>"
            ),
            x=0.5,
        ),

        scene=dict(

            xaxis=dict(
                title="X (m)",
                showbackground=False,
                zeroline=False,
            ),

            yaxis=dict(
                title="Y (m)",
                showbackground=False,
                zeroline=False,
            ),

            zaxis=dict(
                title="Height (m)",
                showbackground=False,
                zeroline=False,
            ),

            aspectmode="data",

            camera=dict(
                eye=dict(
                    x=1.55,
                    y=1.55,
                    z=1.20,
                ),
            ),
        ),

        height=760,

        margin=dict(
            l=0,
            r=0,
            t=90,
            b=0,
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5,
        ),
    )

    return fig


# ============================================================
# SIMPLE 3D ALIAS
# ============================================================

def create_reactor_3d(
    **kwargs
):

    return create_reactor_animation(
        **kwargs
    )
