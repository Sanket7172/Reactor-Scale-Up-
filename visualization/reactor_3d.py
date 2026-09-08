import math
import numpy as np
import plotly.graph_objects as go


# ============================================================
# CONSTANTS
# ============================================================

G = 9.81


# ============================================================
# SAFE HELPERS
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


def _first_value(data, keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data and data[key] is not None:
            return data[key]

    return default


def _clamp(value, low, high):
    return max(low, min(high, value))


# ============================================================
# IMPELLER NORMALIZATION
# ============================================================

def _normalize_impellers(
    impellers=None,
    D=1.0,
    tank_diameter_m=None,
    impeller_diameter_m=None,
    impeller_clearance_m=0.4,
    agitator="Rushton Turbine",
    number_impellers=1,
):
    """
    Convert all supported impeller input formats into:

    [
        {
            "position": "...",
            "agitator_type": "...",
            "diameter_m": ...,
            "elevation_m": ...
        }
    ]
    """

    if impellers is None:
        impellers = []

    normalized = []

    # --------------------------------------------------------
    # Existing list
    # --------------------------------------------------------

    if isinstance(impellers, list) and len(impellers) > 0:

        for i, imp in enumerate(impellers):

            if not isinstance(imp, dict):
                continue

            agitator_name = _first_value(
                imp,
                [
                    "agitator_type",
                    "agitator",
                    "type",
                    "name",
                ],
                agitator,
            )

            diameter = _first_value(
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
                diameter = _safe_float(
                    tank_diameter_m,
                    _safe_float(D, 2.0)
                ) * 0.5

            elevation = _first_value(
                imp,
                [
                    "elevation_m",
                    "elevation",
                    "bottom_clearance_m",
                    "clearance_m",
                ],
                impeller_clearance_m,
            )

            position = _first_value(
                imp,
                [
                    "position",
                    "location",
                ],
                ["Bottom", "Middle", "Top"][
                    min(i, 2)
                ],
            )

            normalized.append(
                {
                    "position": str(position),
                    "agitator_type": str(
                        agitator_name
                    ),
                    "diameter_m": _safe_float(
                        diameter,
                        0.5
                    ),
                    "elevation_m": _safe_float(
                        elevation,
                        0.4
                    ),
                }
            )

    # --------------------------------------------------------
    # Legacy single-impeller inputs
    # --------------------------------------------------------

    if not normalized:

        tank_D = _safe_float(
            tank_diameter_m,
            _safe_float(D, 2.0)
        )

        imp_D = _safe_float(
            impeller_diameter_m,
            tank_D * 0.5
        )

        nimp = max(
            1,
            _safe_int(
                number_impellers,
                1
            )
        )

        positions = [
            "Bottom",
            "Middle",
            "Top"
        ]

        for i in range(nimp):

            if nimp == 1:
                elevation = _safe_float(
                    impeller_clearance_m,
                    0.4
                )

            else:
                elevation = (
                    _safe_float(
                        impeller_clearance_m,
                        0.4
                    )
                    +
                    i * imp_D
                )

            normalized.append(
                {
                    "position": positions[
                        min(i, 2)
                    ],
                    "agitator_type": str(
                        agitator
                    ),
                    "diameter_m": imp_D,
                    "elevation_m": elevation,
                }
            )

    return normalized


# ============================================================
# VESSEL GEOMETRY
# ============================================================

def _head_depth(
    diameter,
    head_type
):
    """
    Approximate internal head depth for visualization.
    """

    head_type = str(
        head_type or ""
    ).lower()

    if "2:1" in head_type:
        return 0.25 * diameter

    if "ellipsoidal" in head_type:
        return 0.25 * diameter

    if "torispherical" in head_type:
        return 0.10 * diameter

    if "flat" in head_type:
        return 0.0

    return 0.10 * diameter


def _create_vessel_geometry(
    tank_diameter_m,
    straight_height_m,
    bottom_type,
    top_type,
):
    radius = tank_diameter_m / 2.0

    bottom_depth = _head_depth(
        tank_diameter_m,
        bottom_type
    )

    top_depth = _head_depth(
        tank_diameter_m,
        top_type
    )

    straight_bottom = bottom_depth

    straight_top = (
        bottom_depth +
        straight_height_m
    )

    total_height = (
        straight_height_m +
        bottom_depth +
        top_depth
    )

    return {
        "radius": radius,
        "diameter": tank_diameter_m,
        "bottom_depth": bottom_depth,
        "top_depth": top_depth,
        "straight_bottom": straight_bottom,
        "straight_top": straight_top,
        "total_height": total_height,
    }


# ============================================================
# VESSEL SURFACE
# ============================================================

def _cylinder_surface(
    radius,
    z_bottom,
    z_top,
    n_theta=60,
    n_z=20,
):
    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        n_theta
    )

    z = np.linspace(
        z_bottom,
        z_top,
        n_z
    )

    T, Z = np.meshgrid(
        theta,
        z
    )

    X = radius * np.cos(T)
    Y = radius * np.sin(T)

    return X, Y, Z


def _head_surface(
    radius,
    z_base,
    depth,
    top=True,
    n_theta=60,
    n_phi=20,
):
    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        n_theta
    )

    phi = np.linspace(
        0.0,
        np.pi / 2.0,
        n_phi
    )

    T, P = np.meshgrid(
        theta,
        phi
    )

    X = radius * np.sin(P) * np.cos(T)
    Y = radius * np.sin(P) * np.sin(T)

    if top:
        Z = (
            z_base +
            depth * np.cos(P)
        )
    else:
        Z = (
            z_base -
            depth * np.cos(P)
        )

    return X, Y, Z


# ============================================================
# LIQUID LEVEL
# ============================================================

def _calculate_liquid_level(
    working_volume_m3,
    geometry,
):
    """
    Approximate liquid height from bottom of vessel.

    For engineering visualization only.
    """

    radius = geometry["radius"]

    area = (
        np.pi *
        radius ** 2
    )

    bottom_depth = geometry[
        "bottom_depth"
    ]

    straight_height = (
        geometry["straight_top"] -
        geometry["straight_bottom"]
    )

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
        _safe_float(
            working_volume_m3,
            straight_volume
        ),
        0.001,
        max(
            vessel_volume * 0.999,
            0.002
        )
    )

    if V <= bottom_volume:

        fraction = V / max(
            bottom_volume,
            1e-9
        )

        return (
            bottom_depth *
            fraction
        )

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
            remaining / area
        )

    remaining = (
        V -
        bottom_volume -
        straight_volume
    )

    fraction = remaining / max(
        top_volume,
        1e-9
    )

    return _clamp(
        geometry["straight_top"] +
        fraction * top_depth,
        0.001,
        geometry["total_height"] * 0.999
    )


# ============================================================
# LIQUID SURFACE + VORTEX
# ============================================================

def _create_liquid_surface(
    radius,
    liquid_level,
    vortex_depth,
    n=70,
):
    r = np.linspace(
        0.0,
        radius * 0.995,
        n
    )

    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        n
    )

    R, T = np.meshgrid(
        r,
        theta
    )

    X = R * np.cos(T)
    Y = R * np.sin(T)

    normalized_r = (
        R /
        max(radius, 1e-9)
    )

    Z = (
        liquid_level -
        vortex_depth *
        (
            1.0 -
            normalized_r ** 2
        )
    )

    return X, Y, Z


# ============================================================
# BAFFLES
# ============================================================

def _create_baffles(
    radius,
    z_bottom,
    z_top,
    number_baffles,
):
    traces = []

    number_baffles = max(
        0,
        _safe_int(
            number_baffles,
            4
        )
    )

    width = max(
        radius * 0.08,
        0.04
    )

    radial = (
        radius * 0.92
    )

    for i in range(
        number_baffles
    ):

        angle = (
            2.0 *
            np.pi *
            i /
            max(number_baffles, 1)
        )

        cx = (
            radial *
            np.cos(angle)
        )

        cy = (
            radial *
            np.sin(angle)
        )

        tx = -np.sin(angle)
        ty = np.cos(angle)

        x1 = cx + tx * width / 2
        y1 = cy + ty * width / 2

        x2 = cx - tx * width / 2
        y2 = cy - ty * width / 2

        traces.append(
            go.Scatter3d(
                x=[
                    x1,
                    x2,
                    x2,
                    x1,
                    x1
                ],
                y=[
                    y1,
                    y2,
                    y2,
                    y1,
                    y1
                ],
                z=[
                    z_bottom,
                    z_bottom,
                    z_top,
                    z_top,
                    z_bottom
                ],
                mode="lines",
                line=dict(
                    width=7
                ),
                name=f"Baffle {i + 1}",
                showlegend=False,
                hoverinfo="skip"
            )
        )

    return traces


# ============================================================
# SHAFT
# ============================================================

def _create_shaft(
    shaft_radius,
    z_bottom,
    z_top,
):
    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        30
    )

    z = np.linspace(
        z_bottom,
        z_top,
        25
    )

    T, Z = np.meshgrid(
        theta,
        z
    )

    X = (
        shaft_radius *
        np.cos(T)
    )

    Y = (
        shaft_radius *
        np.sin(T)
    )

    return go.Surface(
        x=X,
        y=Y,
        z=Z,
        opacity=0.75,
        showscale=False,
        hoverinfo="skip",
        name="Shaft"
    )


# ============================================================
# IMPELLER GEOMETRY
# ============================================================

def _create_impeller(
    agitator_type,
    diameter,
    elevation,
    angle=0.0,
):
    """
    Parametric engineering visualization
    of common agitator geometries.
    """

    traces = []

    name = str(
        agitator_type
    )

    lower_name = name.lower()

    R = diameter / 2.0

    # --------------------------------------------------------
    # RUSHTON
    # --------------------------------------------------------

    if "rushton" in lower_name:

        blades = 6

        hub_r = (
            0.15 * R
        )

        for i in range(blades):

            a = (
                angle +
                2.0 *
                np.pi *
                i /
                blades
            )

            x0 = (
                hub_r *
                np.cos(a)
            )

            y0 = (
                hub_r *
                np.sin(a)
            )

            x1 = (
                0.92 *
                R *
                np.cos(a)
            )

            y1 = (
                0.92 *
                R *
                np.sin(a)
            )

            tangent = (
                a +
                np.pi / 2.0
            )

            blade_width = (
                0.13 *
                diameter
            )

            xa = (
                x1 +
                blade_width *
                np.cos(tangent)
            )

            ya = (
                y1 +
                blade_width *
                np.sin(tangent)
            )

            xb = (
                x1 -
                blade_width *
                np.cos(tangent)
            )

            yb = (
                y1 -
                blade_width *
                np.sin(tangent)
            )

            traces.append(
                go.Scatter3d(
                    x=[
                        x0,
                        xa,
                        xb,
                        x0
                    ],
                    y=[
                        y0,
                        ya,
                        yb,
                        y0
                    ],
                    z=[
                        elevation,
                        elevation,
                        elevation,
                        elevation
                    ],
                    mode="lines",
                    line=dict(
                        width=10
                    ),
                    name=name,
                    showlegend=False,
                    hoverinfo="skip"
                )
            )

    # --------------------------------------------------------
    # PBT
    # --------------------------------------------------------

    elif (
        "pitched" in lower_name or
        "pbt" in lower_name
    ):

        blades = 4

        for i in range(blades):

            a = (
                angle +
                2.0 *
                np.pi *
                i /
                blades
            )

            r = np.linspace(
                0.15 * R,
                0.95 * R,
                25
            )

            x = (
                r *
                np.cos(a)
            )

            y = (
                r *
                np.sin(a)
            )

            z = (
                elevation +
                0.15 *
                diameter *
                r /
                max(R, 1e-9)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=10
                    ),
                    name=name,
                    showlegend=False,
                    hoverinfo="skip"
                )
            )

    # --------------------------------------------------------
    # HYDROFOIL
    # --------------------------------------------------------

    elif "hydrofoil" in lower_name:

        blades = 3

        for i in range(blades):

            a = (
                angle +
                2.0 *
                np.pi *
                i /
                blades
            )

            r = np.linspace(
                0.12 * R,
                0.95 * R,
                30
            )

            x = (
                r *
                np.cos(a)
            )

            y = (
                r *
                np.sin(a)
            )

            z = (
                elevation +
                0.08 *
                diameter *
                r /
                max(R, 1e-9)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=12
                    ),
                    name=name,
                    showlegend=False,
                    hoverinfo="skip"
                )
            )

    # --------------------------------------------------------
    # MARINE PROPELLER
    # --------------------------------------------------------

    elif (
        "marine" in lower_name or
        "propeller" in lower_name
    ):

        blades = 3

        for i in range(blades):

            a0 = (
                angle +
                2.0 *
                np.pi *
                i /
                blades
            )

            r = np.linspace(
                0.10 * R,
                0.98 * R,
                40
            )

            a = (
                a0 +
                0.45 *
                r /
                max(R, 1e-9)
            )

            x = (
                r *
                np.cos(a)
            )

            y = (
                r *
                np.sin(a)
            )

            z = (
                elevation +
                0.10 *
                diameter *
                r /
                max(R, 1e-9)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=10
                    ),
                    name=name,
                    showlegend=False,
                    hoverinfo="skip"
                )
            )

    # --------------------------------------------------------
    # ANCHOR
    # --------------------------------------------------------

    elif "anchor" in lower_name:

        theta = np.linspace(
            0.0,
            2.0 * np.pi,
            100
        )

        theta = (
            theta +
            angle
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
            elevation
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=11
                ),
                name=name,
                showlegend=False,
                hoverinfo="skip"
            )
        )

    # --------------------------------------------------------
    # HELICAL RIBBON
    # --------------------------------------------------------

    elif "helical" in lower_name:

        theta = np.linspace(
            0.0,
            4.0 * np.pi,
            180
        )

        theta = (
            theta +
            angle
        )

        x = (
            0.92 *
            R *
            np.cos(theta)
        )

        y = (
            0.92 *
            R *
            np.sin(theta)
        )

        z = (
            elevation -
            0.30 * diameter +
            0.60 *
            diameter *
            theta /
            (4.0 * np.pi)
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=9
                ),
                name=name,
                showlegend=False,
                hoverinfo="skip"
            )
        )

    # --------------------------------------------------------
    # RCI / GENERIC
    # --------------------------------------------------------

    else:

        theta = np.linspace(
            0.0,
            2.0 * np.pi,
            100
        )

        theta = (
            theta +
            angle
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
            elevation
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=9
                ),
                name=name,
                showlegend=False,
                hoverinfo="skip"
            )
        )

    return traces


# ============================================================
# PHYSICS-INFORMED FLOW FIELD
# ============================================================

def _calculate_flow_field(
    radius,
    z_bottom,
    liquid_level,
    impellers,
    rpm,
    radial_points=10,
    theta_points=20,
    vertical_points=8,
):
    """
    Physics-informed flow visualization.

    Components:
        Vt = tangential velocity
        Vr = radial velocity
        Vz = axial circulation velocity

    This is NOT a Navier-Stokes CFD solution.
    """

    omega = (
        2.0 *
        np.pi *
        rpm /
        60.0
    )

    result = []

    for impeller in impellers:

        D = _safe_float(
            impeller.get(
                "diameter_m",
                radius
            ),
            radius
        )

        zi = _safe_float(
            impeller.get(
                "elevation_m",
                z_bottom
            ),
            z_bottom
        )

        Ri = D / 2.0

        for iz in range(
            vertical_points
        ):

            z = (
                z_bottom +
                (
                    liquid_level -
                    z_bottom
                ) *
                iz /
                max(
                    vertical_points - 1,
                    1
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

                for it in range(
                    theta_points
                ):

                    theta = (
                        2.0 *
                        np.pi *
                        it /
                        theta_points
                    )

                    dz = (
                        z -
                        zi
                    )

                    vertical_influence = np.exp(
                        -abs(dz) /
                        max(
                            1.2 * D,
                            1e-6
                        )
                    )

                    radial_influence = np.exp(
                        -abs(
                            r -
                            Ri
                        ) /
                        max(
                            0.45 * radius,
                            1e-6
                        )
                    )

                    influence = (
                        vertical_influence *
                        radial_influence
                    )

                    # ------------------------------------------------
                    # Tangential component
                    # ------------------------------------------------

                    v_theta = (
                        omega *
                        r *
                        0.60 *
                        influence
                    )

                    # ------------------------------------------------
                    # Radial discharge
                    # ------------------------------------------------

                    v_r = (
                        omega *
                        Ri *
                        0.32 *
                        influence *
                        (
                            1.0 -
                            r /
                            max(
                                radius,
                                1e-9
                            )
                        )
                    )

                    # ------------------------------------------------
                    # Axial circulation
                    # ------------------------------------------------

                    v_z = (
                        omega *
                        Ri *
                        0.20 *
                        influence
                    )

                    if z > zi:
                        v_z *= -1.0

                    # Wall return
                    if r > (
                        0.70 *
                        radius
                    ):

                        v_r *= -1.25
                        v_z *= 1.35

                    erx = np.cos(theta)
                    ery = np.sin(theta)

                    etx = -np.sin(theta)
                    ety = np.cos(theta)

                    vx = (
                        v_r * erx +
                        v_theta * etx
                    )

                    vy = (
                        v_r * ery +
                        v_theta * ety
                    )

                    speed = math.sqrt(
                        vx ** 2 +
                        vy ** 2 +
                        v_z ** 2
                    )

                    x = (
                        r *
                        np.cos(theta)
                    )

                    y = (
                        r *
                        np.sin(theta)
                    )

                    result.append(
                        {
                            "x": x,
                            "y": y,
                            "z": z,
                            "vx": vx,
                            "vy": vy,
                            "vz": v_z,
                            "speed": speed,
                        }
                    )

    return result


# ============================================================
# FLOW STREAMLINES
# ============================================================

def _create_streamlines(
    radius,
    z_bottom,
    liquid_level,
    impellers,
    rpm,
    count=24,
):
    traces = []

    omega = (
        2.0 *
        np.pi *
        rpm /
        60.0
    )

    if not impellers:
        impellers = [
            {
                "diameter_m": radius,
                "elevation_m": (
                    z_bottom +
                    liquid_level
                ) / 2.0
            }
        ]

    for line_number in range(
        count
    ):

        theta = (
            2.0 *
            np.pi *
            line_number /
            count
        )

        r = (
            radius *
            (
                0.15 +
                0.72 *
                (
                    (
                        line_number %
                        10
                    ) /
                    10.0
                )
            )
        )

        z = (
            z_bottom +
            (
                liquid_level -
                z_bottom
            ) *
            (
                0.10 +
                0.80 *
                (
                    (
                        line_number * 7 %
                        10
                    ) /
                    10.0
                )
            )
        )

        xs = []
        ys = []
        zs = []

        for _ in range(130):

            distances = [
                abs(
                    z -
                    _safe_float(
                        imp.get(
                            "elevation_m",
                            z_bottom
                        ),
                        z_bottom
                    )
                )
                for imp in impellers
            ]

            nearest = impellers[
                int(
                    np.argmin(
                        distances
                    )
                )
            ]

            imp_D = _safe_float(
                nearest.get(
                    "diameter_m",
                    radius
                ),
                radius
            )

            imp_z = _safe_float(
                nearest.get(
                    "elevation_m",
                    z_bottom
                ),
                z_bottom
            )

            imp_R = (
                imp_D /
                2.0
            )

            influence = np.exp(
                -abs(
                    z -
                    imp_z
                ) /
                max(
                    imp_D * 1.5,
                    1e-6
                )
            )

            vtheta = (
                omega *
                r *
                0.50 *
                influence
            )

            vr = (
                omega *
                imp_R *
                0.22 *
                influence
            )

            vz = (
                omega *
                imp_R *
                0.18 *
                influence
            )

            if z > imp_z:
                vz *= -1.0

            if r > (
                0.72 *
                radius
            ):

                vr *= -1.35
                vz *= 1.25

            dt = 0.012

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
                max(
                    r,
                    0.03
                ) *
                dt
            )

            r = _clamp(
                r,
                radius * 0.08,
                radius * 0.94
            )

            z = _clamp(
                z,
                z_bottom + 0.03,
                liquid_level - 0.03
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
                    width=3
                ),
                opacity=0.45,
                name="Flow path",
                showlegend=False,
                hoverinfo="skip"
            )
        )

    return traces


# ============================================================
# PARTICLES
# ============================================================

def _create_particles(
    radius,
    z_bottom,
    liquid_level,
    count=350,
):
    rng = np.random.default_rng(42)

    r = (
        radius *
        np.sqrt(
            rng.random(count)
        ) *
        0.90
    )

    theta = (
        2.0 *
        np.pi *
        rng.random(count)
    )

    z = (
        z_bottom +
        (
            liquid_level -
            z_bottom
        ) *
        rng.random(count)
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
# GAS BUBBLES
# ============================================================

def _create_bubbles(
    radius,
    liquid_level,
    gas_flow_m3_h,
    bubble_diameter_mm,
    count=160,
):
    if gas_flow_m3_h <= 0:
        return None

    rng = np.random.default_rng(17)

    r = (
        radius *
        0.15 *
        np.sqrt(
            rng.random(count)
        )
    )

    theta = (
        2.0 *
        np.pi *
        rng.random(count)
    )

    x = (
        r *
        np.cos(theta)
    )

    y = (
        r *
        np.sin(theta)
    )

    z = (
        liquid_level *
        (
            0.05 +
            0.85 *
            rng.random(count)
        )
    )

    size = np.full(
        count,
        _clamp(
            bubble_diameter_mm * 1.8,
            3.0,
            12.0
        )
    )

    return x, y, z, size


# ============================================================
# MAIN REACTOR VISUALIZATION
# ============================================================

def create_reactor_animation(
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

    show_dimensions=True,
    show_flow_field=True,
    show_streamlines=True,
    show_particles=True,
    show_vortex=True,
    show_baffles=True,
    show_gas=False,

    frames=24,

    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================

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
    """
    Main 3D reactor mixing visualization.

    Supports both:

        tank_diameter_m
        straight_height_m
        volume_m3

    and legacy:

        D
        H
        volume

    inputs.

    The visualization is a physics-informed mixing model,
    NOT a true CFD/Navier-Stokes solver.
    """

    # ========================================================
    # INPUT MAPPING
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

    tank_diameter_m = _safe_float(
        tank_diameter_m,
        2.0
    )

    straight_height_m = _safe_float(
        straight_height_m,
        3.0
    )

    volume_m3 = _safe_float(
        volume_m3,
        10.0
    )

    rpm = _safe_float(
        rpm,
        100.0
    )

    tank_diameter_m = max(
        tank_diameter_m,
        0.10
    )

    straight_height_m = max(
        straight_height_m,
        0.10
    )

    rpm = max(
        rpm,
        0.0
    )

    # ========================================================
    # NORMALIZE IMPELLERS
    # ========================================================

    impellers = _normalize_impellers(
        impellers=impellers,
        D=tank_diameter_m,
        tank_diameter_m=tank_diameter_m,
        impeller_diameter_m=impeller_diameter_m,
        impeller_clearance_m=impeller_clearance_m,
        agitator=agitator,
        number_impellers=number_impellers,
    )

    # ========================================================
    # VESSEL
    # ========================================================

    geometry = _create_vessel_geometry(
        tank_diameter_m=tank_diameter_m,
        straight_height_m=straight_height_m,
        bottom_type=bottom_type,
        top_type=top_type,
    )

    radius = geometry["radius"]

    # ========================================================
    # LIQUID LEVEL
    # ========================================================

    if liquid_height_m is None:

        liquid_height = _calculate_liquid_level(
            volume_m3,
            geometry
        )

    else:

        liquid_height = _safe_float(
            liquid_height_m,
            _calculate_liquid_level(
                volume_m3,
                geometry
            )
        )

    liquid_height = _clamp(
        liquid_height,
        0.05,
        geometry["total_height"] * 0.99
    )

    # ========================================================
    # FROUDE NUMBER
    # ========================================================

    N = rpm / 60.0

    Fr = (
        N ** 2 *
        tank_diameter_m /
        G
    )

    # ========================================================
    # VORTEX
    # ========================================================

    if show_vortex:

        vortex_depth = _clamp(
            liquid_height *
            0.06 *
            math.sqrt(
                max(
                    Fr,
                    0.0
                )
            ),
            0.0,
            liquid_height * 0.25
        )

    else:

        vortex_depth = 0.0

    # ========================================================
    # FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # VESSEL
    # ========================================================

    X, Y, Z = _cylinder_surface(
        radius,
        geometry["straight_bottom"],
        geometry["straight_top"]
    )

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.15,
            showscale=False,
            hoverinfo="skip",
            name="Reactor Shell"
        )
    )

    # Bottom head
    if geometry["bottom_depth"] > 0:

        Xb, Yb, Zb = _head_surface(
            radius,
            geometry["straight_bottom"],
            geometry["bottom_depth"],
            top=False
        )

        fig.add_trace(
            go.Surface(
                x=Xb,
                y=Yb,
                z=Zb,
                opacity=0.15,
                showscale=False,
                hoverinfo="skip",
                name="Bottom Head"
            )
        )

    # Top head
    if geometry["top_depth"] > 0:

        Xt, Yt, Zt = _head_surface(
            radius,
            geometry["straight_top"],
            geometry["top_depth"],
            top=True
        )

        fig.add_trace(
            go.Surface(
                x=Xt,
                y=Yt,
                z=Zt,
                opacity=0.15,
                showscale=False,
                hoverinfo="skip",
                name="Top Head"
            )
        )

    # ========================================================
    # LIQUID
    # ========================================================

    Xl, Yl, Zl = _create_liquid_surface(
        radius,
        liquid_height,
        vortex_depth
    )

    fig.add_trace(
        go.Surface(
            x=Xl,
            y=Yl,
            z=Zl,
            opacity=0.48,
            showscale=False,
            name="Liquid Surface",
            hovertemplate=(
                "Liquid Surface"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            )
        )
    )

    # ========================================================
    # BAFFLES
    # ========================================================

    if show_baffles:

        baffles = _create_baffles(
            radius,
            geometry["straight_bottom"],
            min(
                liquid_height,
                geometry["straight_top"]
            ),
            number_baffles
        )

        for trace in baffles:
            fig.add_trace(trace)

    # ========================================================
    # SHAFT
    # ========================================================

    shaft_radius = max(
        tank_diameter_m * 0.025,
        0.02
    )

    fig.add_trace(
        _create_shaft(
            shaft_radius,
            geometry["straight_bottom"],
            geometry["straight_top"]
        )
    )

    # ========================================================
    # IMPELLERS
    # ========================================================

    for impeller in impellers:

        impeller_type = impeller[
            "agitator_type"
        ]

        impeller_D = _safe_float(
            impeller[
                "diameter_m"
            ],
            tank_diameter_m * 0.5
        )

        elevation = _safe_float(
            impeller[
                "elevation_m"
            ],
            0.4
        )

        traces = _create_impeller(
            impeller_type,
            impeller_D,
            elevation
        )

        for trace in traces:
            fig.add_trace(trace)

    # ========================================================
    # VELOCITY FIELD
    # ========================================================

    if show_flow_field:

        flow = _calculate_flow_field(
            radius,
            0.0,
            liquid_height,
            impellers,
            rpm
        )

        if flow:

            # Keep rendering reasonable
            max_points = 1800

            if len(flow) > max_points:

                indexes = np.linspace(
                    0,
                    len(flow) - 1,
                    max_points
                ).astype(int)

                flow = [
                    flow[i]
                    for i in indexes
                ]

            fx = np.array(
                [
                    p["x"]
                    for p in flow
                ]
            )

            fy = np.array(
                [
                    p["y"]
                    for p in flow
                ]
            )

            fz = np.array(
                [
                    p["z"]
                    for p in flow
                ]
            )

            fs = np.array(
                [
                    p["speed"]
                    for p in flow
                ]
            )

            fig.add_trace(
                go.Scatter3d(
                    x=fx,
                    y=fy,
                    z=fz,
                    mode="markers",
                    marker=dict(
                        size=3,
                        color=fs,
                        colorscale="Turbo",
                        opacity=0.70,
                        colorbar=dict(
                            title="Velocity<br>m/s"
                        )
                    ),
                    name="Velocity Field",
                    hovertemplate=(
                        "Velocity = "
                        "%{marker.color:.3f} m/s"
                        "<extra></extra>"
                    )
                )
            )

    # ========================================================
    # STREAMLINES
    # ========================================================

    if show_streamlines:

        streamlines = _create_streamlines(
            radius,
            0.0,
            liquid_height,
            impellers,
            rpm,
            count=26
        )

        for trace in streamlines:
            fig.add_trace(trace)

    # ========================================================
    # MIXING PARTICLES
    # ========================================================

    particle_index = None

    if show_particles:

        px, py, pz = _create_particles(
            radius,
            0.0,
            liquid_height,
            count=350
        )

        particle_index = len(
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
                    opacity=0.75
                ),
                name="Liquid Particles"
            )
        )

    # ========================================================
    # GAS BUBBLES
    # ========================================================

    if (
        show_gas and
        gas_flow_m3_h > 0
    ):

        bubble_data = _create_bubbles(
            radius,
            liquid_height,
            gas_flow_m3_h,
            bubble_diameter_mm
        )

        if bubble_data is not None:

            bx, by, bz, bs = (
                bubble_data
            )

            fig.add_trace(
                go.Scatter3d(
                    x=bx,
                    y=by,
                    z=bz,
                    mode="markers",
                    marker=dict(
                        size=bs,
                        opacity=0.60,
                        symbol="circle"
                    ),
                    name="Gas Bubbles"
                )
            )

    # ========================================================
    # DIMENSIONS
    # ========================================================

    if show_dimensions:

        # Diameter
        fig.add_trace(
            go.Scatter3d(
                x=[
                    -radius,
                    radius
                ],
                y=[
                    0,
                    0
                ],
                z=[
                    geometry[
                        "straight_top"
                    ],
                    geometry[
                        "straight_top"
                    ]
                ],
                mode="lines+text",
                text=[
                    "",
                    f"ID = {tank_diameter_m:.2f} m"
                ],
                textposition="top center",
                line=dict(
                    width=4
                ),
                name="Tank Diameter"
            )
        )

        # Liquid level
        fig.add_trace(
            go.Scatter3d(
                x=[
                    -radius * 0.98,
                    radius * 0.98
                ],
                y=[
                    0,
                    0
                ],
                z=[
                    liquid_height,
                    liquid_height
                ],
                mode="lines+text",
                text=[
                    "",
                    f"Liquid Level = {liquid_height:.2f} m"
                ],
                textposition="top center",
                line=dict(
                    width=5,
                    dash="dash"
                ),
                name="Liquid Level"
            )
        )

        # Vortex depth indicator
        if vortex_depth > 0:

            fig.add_trace(
                go.Scatter3d(
                    x=[
                        0,
                        0
                    ],
                    y=[
                        0,
                        0
                    ],
                    z=[
                        liquid_height,
                        liquid_height -
                        vortex_depth
                    ],
                    mode="lines+text",
                    text=[
                        "",
                        f"Vortex ≈ {vortex_depth:.2f} m"
                    ],
                    textposition="middle right",
                    line=dict(
                        width=4,
                        dash="dot"
                    ),
                    name="Vortex Depth"
                )
            )

    # ========================================================
    # ANIMATION
    # ========================================================

    animation_frames = []

    if particle_index is not None:

        px0, py0, pz0 = (
            _create_particles(
                radius,
                0.0,
                liquid_height,
                count=350
            )
        )

        r0 = np.sqrt(
            px0 ** 2 +
            py0 ** 2
        )

        theta0 = np.arctan2(
            py0,
            px0
        )

        for frame_number in range(
            max(
                1,
                frames
            )
        ):

            angle = (
                2.0 *
                np.pi *
                frame_number /
                max(
                    frames,
                    1
                )
            )

            rotation_factor = (
                0.25 +
                0.75 *
                (
                    1.0 -
                    r0 /
                    max(
                        radius,
                        1e-9
                    )
                )
            )

            theta_new = (
                theta0 +
                angle *
                rotation_factor
            )

            # Circulation oscillation
            z_new = (
                pz0 +
                0.06 *
                liquid_height *
                np.sin(
                    (
                        2.0 *
                        np.pi *
                        pz0 /
                        max(
                            liquid_height,
                            1e-9
                        )
                    ) +
                    angle
                )
            )

            z_new = np.clip(
                z_new,
                0.03,
                liquid_height - 0.03
            )

            x_new = (
                r0 *
                np.cos(theta_new)
            )

            y_new = (
                r0 *
                np.sin(theta_new)
            )

            animation_frames.append(
                go.Frame(
                    data=[
                        go.Scatter3d(
                            x=x_new,
                            y=y_new,
                            z=z_new
                        )
                    ],
                    traces=[
                        particle_index
                    ],
                    name=str(
                        frame_number
                    )
                )
            )

    fig.frames = animation_frames

    # ========================================================
    # PLAY BUTTON
    # ========================================================

    if animation_frames:

        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    x=0.02,
                    y=1.08,
                    buttons=[
                        dict(
                            label="▶ Play Mixing",
                            method="animate",
                            args=[
                                None,
                                {
                                    "frame": {
                                        "duration": 80,
                                        "redraw": True
                                    },
                                    "fromcurrent": True
                                }
                            ]
                        ),
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[
                                [None],
                                {
                                    "frame": {
                                        "duration": 0,
                                        "redraw": False
                                    }
                                }
                            ]
                        )
                    ]
                )
            ]
        )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(
        title=dict(
            text=(
                "3D Reactor Mixing Simulation"
                "<br>"
                f"<sup>"
                f"ID = {tank_diameter_m:.2f} m"
                f" | Liquid = {liquid_height:.2f} m"
                f" | RPM = {rpm:.0f}"
                f" | Re = Physics-informed"
                f"</sup>"
            ),
            x=0.5
        ),

        scene=dict(
            xaxis=dict(
                title="X (m)",
                showbackground=False
            ),
            yaxis=dict(
                title="Y (m)",
                showbackground=False
            ),
            zaxis=dict(
                title="Height (m)",
                showbackground=False
            ),
            aspectmode="data",
            camera=dict(
                eye=dict(
                    x=1.65,
                    y=1.65,
                    z=1.20
                )
            )
        ),

        height=760,

        margin=dict(
            l=0,
            r=0,
            t=90,
            b=0
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5
        )
    )

    return fig


# ============================================================
# BACKWARD COMPATIBILITY ALIAS
# ============================================================

def create_reactor_3d(**kwargs):
    return create_reactor_animation(
        **kwargs
    )
