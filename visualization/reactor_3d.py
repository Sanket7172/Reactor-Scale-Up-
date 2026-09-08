# visualization/reactor_3d.py

import math
import numpy as np
import plotly.graph_objects as go


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))


def _get_value(obj, *keys, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        for key in keys:
            if key in obj:
                return obj[key]

    for key in keys:
        if hasattr(obj, key):
            return getattr(obj, key)

    return default


# ============================================================
# FEATURE LIST
# ============================================================

VISUALIZATION_FEATURES = [
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


# ============================================================
# IMPeller NORMALIZATION
# ============================================================

def _normalize_impellers(
    impellers=None,
    agitator=None,
    impeller_diameter_m=None,
    impeller_clearance_m=None,
    number_impellers=1,
    liquid_height_m=1.0,
):
    """
    Normalize impeller data into one consistent structure.

    Output:
    [
        {
            "position": "Bottom",
            "type": "Rushton Turbine",
            "diameter_m": 1.0,
            "elevation_m": 0.4
        }
    ]
    """

    result = []

    if isinstance(impellers, list):

        for i, item in enumerate(impellers):

            if not isinstance(item, dict):
                continue

            impeller_type = (
                item.get("agitator_type")
                or item.get("type")
                or item.get("agitator")
                or agitator
                or "Rushton Turbine"
            )

            diameter = _safe_float(
                item.get("diameter_m"),
                _safe_float(
                    item.get("D"),
                    _safe_float(
                        impeller_diameter_m,
                        0.0
                    )
                )
            )

            elevation = item.get("elevation_m")

            if elevation is None:
                elevation = item.get(
                    "bottom_clearance_m"
                )

            if elevation is None:
                elevation = (
                    liquid_height_m
                    * (i + 1)
                    / (len(impellers) + 1)
                )

            result.append(
                {
                    "position": item.get(
                        "position",
                        f"Impeller {i + 1}"
                    ),
                    "type": impeller_type,
                    "diameter_m": diameter,
                    "elevation_m": _safe_float(
                        elevation,
                        0.0
                    ),
                }
            )

    if result:
        return result

    n = max(
        1,
        _safe_int(
            number_impellers,
            1
        )
    )

    diameter = _safe_float(
        impeller_diameter_m,
        0.0
    )

    clearance = _safe_float(
        impeller_clearance_m,
        0.4
    )

    for i in range(n):

        if n == 1:
            elevation = clearance
        else:
            available_height = max(
                liquid_height_m - 2.0 * clearance,
                0.0
            )

            elevation = (
                clearance
                + i
                * available_height
                / max(n - 1, 1)
            )

        result.append(
            {
                "position": (
                    "Bottom"
                    if i == 0
                    else f"Impeller {i + 1}"
                ),
                "type": (
                    agitator
                    or "Rushton Turbine"
                ),
                "diameter_m": diameter,
                "elevation_m": elevation,
            }
        )

    return result


# ============================================================
# HEAD DEPTH
# ============================================================

def _head_depth(
    diameter_m,
    head_type
):
    text = str(
        head_type or ""
    ).lower()

    if "flat" in text:
        return 0.0

    if (
        "2:1" in text
        or "ellipsoid" in text
    ):
        return diameter_m / 4.0

    if "toris" in text:
        return 0.10 * diameter_m

    return 0.10 * diameter_m


# ============================================================
# VESSEL GEOMETRY
# ============================================================

def _create_geometry(
    diameter_m,
    straight_height_m,
    bottom_type,
    top_type,
):
    D = max(
        _safe_float(
            diameter_m,
            2.0
        ),
        0.1
    )

    H = max(
        _safe_float(
            straight_height_m,
            3.0
        ),
        0.1
    )

    R = D / 2.0

    bottom_depth = _head_depth(
        D,
        bottom_type
    )

    top_depth = _head_depth(
        D,
        top_type
    )

    z_bottom = 0.0

    z_bottom_tangent = (
        bottom_depth
    )

    z_top_tangent = (
        bottom_depth
        + H
    )

    z_top = (
        z_top_tangent
        + top_depth
    )

    return {
        "D": D,
        "R": R,
        "straight_height": H,
        "bottom_depth": bottom_depth,
        "top_depth": top_depth,
        "z_bottom": z_bottom,
        "z_bottom_tangent": z_bottom_tangent,
        "z_top_tangent": z_top_tangent,
        "z_top": z_top,
    }


# ============================================================
# CYLINDRICAL SHELL
# ============================================================

def _cylinder_surface(
    radius,
    z0,
    z1,
    n_theta=80,
    n_z=30,
):
    theta = np.linspace(
        0.0,
        2.0 * math.pi,
        n_theta
    )

    z = np.linspace(
        z0,
        z1,
        n_z
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    x = (
        radius
        * np.cos(theta_grid)
    )

    y = (
        radius
        * np.sin(theta_grid)
    )

    return x, y, z_grid


# ============================================================
# 2:1 ELLIPSOID HEAD
# ============================================================

def _ellipsoidal_head(
    radius,
    tangent_z,
    depth,
    orientation="bottom",
    n_theta=80,
    n_phi=30,
):
    theta = np.linspace(
        0.0,
        2.0 * math.pi,
        n_theta
    )

    phi = np.linspace(
        0.0,
        math.pi / 2.0,
        n_phi
    )

    theta_grid, phi_grid = np.meshgrid(
        theta,
        phi
    )

    x = (
        radius
        * np.sin(phi_grid)
        * np.cos(theta_grid)
    )

    y = (
        radius
        * np.sin(phi_grid)
        * np.sin(theta_grid)
    )

    if orientation == "bottom":

        z = (
            tangent_z
            - depth
            * np.cos(phi_grid)
        )

    else:

        z = (
            tangent_z
            + depth
            * np.cos(phi_grid)
        )

    return x, y, z


# ============================================================
# TORISPHERICAL-LIKE HEAD
# ============================================================

def _torispherical_head(
    radius,
    tangent_z,
    depth,
    orientation="bottom",
    n_theta=80,
    n_phi=30,
):
    theta = np.linspace(
        0.0,
        2.0 * math.pi,
        n_theta
    )

    phi = np.linspace(
        0.0,
        math.pi / 2.0,
        n_phi
    )

    theta_grid, phi_grid = np.meshgrid(
        theta,
        phi
    )

    x = (
        radius
        * np.sin(phi_grid)
        * np.cos(theta_grid)
    )

    y = (
        radius
        * np.sin(phi_grid)
        * np.sin(theta_grid)
    )

    # Smooth approximation for visualization.
    profile = (
        0.5
        * (
            1.0
            - np.cos(phi_grid)
        )
    )

    if orientation == "bottom":

        z = (
            tangent_z
            - depth * profile
        )

    else:

        z = (
            tangent_z
            + depth * profile
        )

    return x, y, z


# ============================================================
# ADD VESSEL
# ============================================================

def _add_vessel(
    fig,
    geometry,
    bottom_type,
    top_type,
):
    D = geometry["D"]
    R = geometry["R"]

    # --------------------------------------------------------
    # CYLINDRICAL SHELL
    # --------------------------------------------------------

    x, y, z = _cylinder_surface(
        R,
        geometry["z_bottom_tangent"],
        geometry["z_top_tangent"],
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.18,
            showscale=False,
            hoverinfo="skip",
            name="Reactor Shell",
        )
    )

    # --------------------------------------------------------
    # BOTTOM HEAD
    # --------------------------------------------------------

    if (
        "2:1" in str(
            bottom_type
        ).lower()
        or "ellipsoid" in str(
            bottom_type
        ).lower()
    ):

        x, y, z = _ellipsoidal_head(
            R,
            geometry[
                "z_bottom_tangent"
            ],
            geometry[
                "bottom_depth"
            ],
            "bottom",
        )

    else:

        x, y, z = _torispherical_head(
            R,
            geometry[
                "z_bottom_tangent"
            ],
            geometry[
                "bottom_depth"
            ],
            "bottom",
        )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.18,
            showscale=False,
            hoverinfo="skip",
            name="Bottom Head",
        )
    )

    # --------------------------------------------------------
    # TOP HEAD
    # --------------------------------------------------------

    if (
        "2:1" in str(
            top_type
        ).lower()
        or "ellipsoid" in str(
            top_type
        ).lower()
    ):

        x, y, z = _ellipsoidal_head(
            R,
            geometry[
                "z_top_tangent"
            ],
            geometry[
                "top_depth"
            ],
            "top",
        )

    else:

        x, y, z = _torispherical_head(
            R,
            geometry[
                "z_top_tangent"
            ],
            geometry[
                "top_depth"
            ],
            "top",
        )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.18,
            showscale=False,
            hoverinfo="skip",
            name="Top Head",
        )
    )


# ============================================================
# LIQUID LEVEL FROM WORKING VOLUME
# ============================================================

def _liquid_level_from_volume(
    volume_m3,
    geometry,
):
    V = max(
        _safe_float(
            volume_m3,
            0.0
        ),
        0.0
    )

    R = geometry["R"]
    D = geometry["D"]

    area = math.pi * R**2

    bottom_depth = geometry[
        "bottom_depth"
    ]

    straight_height = geometry[
        "straight_height"
    ]

    top_depth = geometry[
        "top_depth"
    ]

    # Approximate head volume.
    head_volume = (
        math.pi
        * D**3
        / 24.0
        if bottom_depth > 0
        else 0.0
    )

    if V <= head_volume and head_volume > 0:

        fraction = _clamp(
            V / head_volume,
            0.0,
            1.0
        )

        return (
            geometry["z_bottom"]
            + fraction
            * bottom_depth
        )

    V_remaining = max(
        V - head_volume,
        0.0
    )

    straight_volume = (
        area
        * straight_height
    )

    if V_remaining <= straight_volume:

        height = (
            V_remaining
            / max(area, 1e-12)
        )

        return (
            geometry[
                "z_bottom_tangent"
            ]
            + height
        )

    V_remaining -= straight_volume

    top_head_volume = (
        math.pi
        * D**3
        / 24.0
        if top_depth > 0
        else 0.0
    )

    if top_head_volume > 0:

        fraction = _clamp(
            V_remaining
            / top_head_volume,
            0.0,
            1.0
        )

        return (
            geometry[
                "z_top_tangent"
            ]
            + fraction
            * top_depth
        )

    return geometry["z_top"]


# ============================================================
# LIQUID SURFACE
# ============================================================

def _add_liquid_surface(
    fig,
    radius,
    liquid_z,
    vortex_depth=0.0,
):
    theta = np.linspace(
        0.0,
        2.0 * math.pi,
        100
    )

    radial = np.linspace(
        0.0,
        radius * 0.985,
        45
    )

    rr, tt = np.meshgrid(
        radial,
        theta
    )

    x = (
        rr
        * np.cos(tt)
    )

    y = (
        rr
        * np.sin(tt)
    )

    normalized_r = (
        rr
        / max(radius, 1e-12)
    )

    if vortex_depth > 0:

        z = (
            liquid_z
            - vortex_depth
            * (
                1.0
                - normalized_r**2
            )
        )

    else:

        z = np.full_like(
            x,
            liquid_z
        )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.58,
            showscale=False,
            name="Liquid Level",
            hovertemplate=(
                "Liquid Surface"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# BAFFLES
# ============================================================

def _add_baffles(
    fig,
    radius,
    z_bottom,
    z_top,
    number_baffles,
):
    n = max(
        0,
        _safe_int(
            number_baffles,
            4
        )
    )

    if n == 0:
        return

    baffle_width = max(
        radius * 0.07,
        0.05
    )

    baffle_r = radius * 0.94

    for i in range(n):

        theta = (
            2.0
            * math.pi
            * i
            / n
        )

        ux = math.cos(theta)
        uy = math.sin(theta)

        tx = -uy
        ty = ux

        r1 = baffle_r

        x1 = (
            r1 * ux
            + baffle_width * tx
        )

        y1 = (
            r1 * uy
            + baffle_width * ty
        )

        x2 = (
            r1 * ux
            - baffle_width * tx
        )

        y2 = (
            r1 * uy
            - baffle_width * ty
        )

        fig.add_trace(
            go.Mesh3d(
                x=[
                    x1,
                    x2,
                    x2,
                    x1,
                ],
                y=[
                    y1,
                    y2,
                    y2,
                    y1,
                ],
                z=[
                    z_bottom,
                    z_bottom,
                    z_top,
                    z_top,
                ],
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                opacity=0.55,
                name=f"Baffle {i + 1}",
                hoverinfo="skip",
                showlegend=False,
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
        radius * 0.025,
        0.015
    )

    theta = np.linspace(
        0.0,
        2.0 * math.pi,
        30
    )

    z = np.linspace(
        z_bottom,
        z_top,
        40
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    x = (
        shaft_radius
        * np.cos(theta_grid)
    )

    y = (
        shaft_radius
        * np.sin(theta_grid)
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z_grid,
            opacity=0.9,
            showscale=False,
            name="Shaft",
            hoverinfo="skip",
        )
    )


# ============================================================
# RUSHTON TURBINE
# ============================================================

def _add_rushton(
    fig,
    diameter,
    z,
):
    R = diameter / 2.0

    n_blades = 6

    for i in range(n_blades):

        angle = (
            2.0
            * math.pi
            * i
            / n_blades
        )

        r_inner = diameter * 0.14
        r_outer = R * 0.92

        x1 = (
            r_inner
            * math.cos(angle)
        )

        y1 = (
            r_inner
            * math.sin(angle)
        )

        x2 = (
            r_outer
            * math.cos(angle)
        )

        y2 = (
            r_outer
            * math.sin(angle)
        )

        tx = -math.sin(angle)
        ty = math.cos(angle)

        width = diameter * 0.045

        xs = [
            x1 + width * tx,
            x2 + width * tx,
            x2 - width * tx,
            x1 - width * tx,
            x1 + width * tx,
        ]

        ys = [
            y1 + width * ty,
            y2 + width * ty,
            y2 - width * ty,
            y1 - width * ty,
            y1 + width * ty,
        ]

        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=[
                    z,
                    z,
                    z,
                    z,
                    z,
                ],
                mode="lines",
                line=dict(
                    width=8
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# PBT
# ============================================================

def _add_pbt(
    fig,
    diameter,
    z,
):
    R = diameter / 2.0

    for i in range(4):

        base_angle = (
            2.0
            * math.pi
            * i
            / 4.0
        )

        r = np.linspace(
            diameter * 0.14,
            R * 0.95,
            50
        )

        angle = (
            base_angle
            + 0.28
            * (
                r
                / max(
                    R,
                    1e-12
                )
            )
        )

        x = (
            r
            * np.cos(angle)
        )

        y = (
            r
            * np.sin(angle)
        )

        zz = (
            z
            + 0.08
            * diameter
            * r
            / max(
                R,
                1e-12
            )
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=zz,
                mode="lines",
                line=dict(
                    width=8
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# HYDROFOIL
# ============================================================

def _add_hydrofoil(
    fig,
    diameter,
    z,
):
    R = diameter / 2.0

    for i in range(3):

        base_angle = (
            2.0
            * math.pi
            * i
            / 3.0
        )

        r = np.linspace(
            diameter * 0.12,
            R * 0.95,
            60
        )

        angle = (
            base_angle
            + 0.55
            * r
            / max(
                R,
                1e-12
            )
        )

        x = (
            r
            * np.cos(angle)
        )

        y = (
            r
            * np.sin(angle)
        )

        zz = (
            z
            + 0.04
            * diameter
            * r
            / max(
                R,
                1e-12
            )
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=zz,
                mode="lines",
                line=dict(
                    width=9
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# MARINE PROPELLER
# ============================================================

def _add_marine_propeller(
    fig,
    diameter,
    z,
):
    R = diameter / 2.0

    for i in range(3):

        base_angle = (
            2.0
            * math.pi
            * i
            / 3.0
        )

        t = np.linspace(
            -0.9,
            0.9,
            70
        )

        r = (
            diameter * 0.14
            + (
                R * 0.82
            )
            * (
                t + 0.9
            )
            / 1.8
        )

        angle = (
            base_angle
            + 0.55 * t
        )

        x = (
            r
            * np.cos(angle)
        )

        y = (
            r
            * np.sin(angle)
        )

        zz = (
            z
            + 0.06
            * diameter
            * np.sin(t)
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=zz,
                mode="lines",
                line=dict(
                    width=9
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# ANCHOR
# ============================================================

def _add_anchor(
    fig,
    diameter,
    z,
    vessel_radius,
):
    r = min(
        diameter / 2.0,
        vessel_radius * 0.90
    )

    theta = np.linspace(
        0.0,
        2.0 * math.pi,
        120
    )

    x = (
        r
        * np.cos(theta)
    )

    y = (
        r
        * np.sin(theta)
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=np.full_like(
                theta,
                z
            ),
            mode="lines",
            line=dict(
                width=10
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )


# ============================================================
# HELICAL RIBBON
# ============================================================

def _add_helical_ribbon(
    fig,
    diameter,
    z,
    vessel_radius,
):
    r = min(
        diameter / 2.0,
        vessel_radius * 0.90
    )

    theta = np.linspace(
        0.0,
        4.0 * math.pi,
        240
    )

    height = max(
        diameter,
        0.5
    )

    x = (
        r
        * np.cos(theta)
    )

    y = (
        r
        * np.sin(theta)
    )

    zz = (
        z
        + height
        * (
            theta
            / max(
                theta[-1],
                1e-12
            )
            - 0.5
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=zz,
            mode="lines",
            line=dict(
                width=10
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )


# ============================================================
# GENERIC IMPELLER
# ============================================================

def _add_generic_impeller(
    fig,
    diameter,
    z,
):
    theta = np.linspace(
        0.0,
        2.0 * math.pi,
        120
    )

    r = diameter / 2.0

    fig.add_trace(
        go.Scatter3d(
            x=r * np.cos(theta),
            y=r * np.sin(theta),
            z=np.full_like(
                theta,
                z
            ),
            mode="lines",
            line=dict(
                width=8
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )


# ============================================================
# ADD IMPeller
# ============================================================

def _add_impeller(
    fig,
    impeller,
    vessel_radius,
):
    diameter = _safe_float(
        impeller.get(
            "diameter_m"
        ),
        vessel_radius
    )

    diameter = min(
        max(
            diameter,
            0.05
        ),
        vessel_radius * 1.8
    )

    z = _safe_float(
        impeller.get(
            "elevation_m"
        ),
        0.5
    )

    impeller_type = str(
        impeller.get(
            "type",
            "Rushton Turbine"
        )
    ).lower()

    if "rushton" in impeller_type:

        _add_rushton(
            fig,
            diameter,
            z
        )

    elif (
        "pitched" in impeller_type
        or "pbt" in impeller_type
    ):

        _add_pbt(
            fig,
            diameter,
            z
        )

    elif "hydrofoil" in impeller_type:

        _add_hydrofoil(
            fig,
            diameter,
            z
        )

    elif (
        "marine" in impeller_type
        or "propeller" in impeller_type
    ):

        _add_marine_propeller(
            fig,
            diameter,
            z
        )

    elif "anchor" in impeller_type:

        _add_anchor(
            fig,
            diameter,
            z,
            vessel_radius
        )

    elif "helical" in impeller_type:

        _add_helical_ribbon(
            fig,
            diameter,
            z,
            vessel_radius
        )

    else:

        _add_generic_impeller(
            fig,
            diameter,
            z
        )


# ============================================================
# VELOCITY FIELD
# ============================================================

def _calculate_velocity_field(
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
    density_kg_m3,
    viscosity_pa_s,
):
    n_xy = 13
    n_z = 9

    x = np.linspace(
        -radius * 0.88,
        radius * 0.88,
        n_xy
    )

    y = np.linspace(
        -radius * 0.88,
        radius * 0.88,
        n_xy
    )

    z = np.linspace(
        liquid_bottom,
        liquid_top,
        n_z
    )

    X, Y, Z = np.meshgrid(
        x,
        y,
        z,
        indexing="xy"
    )

    radial = np.sqrt(
        X**2
        + Y**2
    )

    inside = (
        radial
        <= radius * 0.90
    )

    N = max(
        rpm / 60.0,
        0.01
    )

    characteristic_velocity = (
        N
        * radius
    )

    normalized_r = (
        radial
        / max(
            radius,
            1e-12
        )
    )

    normalized_z = (
        (
            Z
            - liquid_bottom
        )
        / max(
            liquid_top
            - liquid_bottom,
            1e-12
        )
    )

    swirl = (
        0.65
        * characteristic_velocity
        * np.exp(
            -1.7
            * normalized_r**2
        )
    )

    radial_velocity = (
        0.35
        * characteristic_velocity
        * (
            1.0
            - normalized_r
        )
        * np.sin(
            math.pi
            * normalized_z
        )
    )

    axial_velocity = (
        0.45
        * characteristic_velocity
        * np.cos(
            math.pi
            * normalized_z
        )
        * np.exp(
            -1.5
            * normalized_r**2
        )
    )

    safe_r = np.maximum(
        radial,
        1e-9
    )

    U = (
        -swirl
        * Y
        / safe_r
        + radial_velocity
        * X
        / safe_r
    )

    V = (
        swirl
        * X
        / safe_r
        + radial_velocity
        * Y
        / safe_r
    )

    W = axial_velocity

    U = np.where(
        inside,
        U,
        np.nan
    )

    V = np.where(
        inside,
        V,
        np.nan
    )

    W = np.where(
        inside,
        W,
        np.nan
    )

    speed = np.sqrt(
        U**2
        + V**2
        + W**2
    )

    return (
        X,
        Y,
        Z,
        U,
        V,
        W,
        speed,
    )


# ============================================================
# VELOCITY PROFILE
# ============================================================

def _add_velocity_profile(
    fig,
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
    density_kg_m3,
    viscosity_pa_s,
):
    (
        X,
        Y,
        Z,
        U,
        V,
        W,
        speed,
    ) = _calculate_velocity_field(
        radius,
        liquid_bottom,
        liquid_top,
        rpm,
        density_kg_m3,
        viscosity_pa_s,
    )

    mask = (
        np.isfinite(speed)
        & (
            speed > 0
        )
    )

    x = X[mask]
    y = Y[mask]
    z = Z[mask]
    s = speed[mask]

    if len(x) > 700:

        idx = np.linspace(
            0,
            len(x) - 1,
            700
        ).astype(int)

        x = x[idx]
        y = y[idx]
        z = z[idx]
        s = s[idx]

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=4,
                color=s,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(
                    title="Velocity<br>m/s"
                ),
            ),
            name="Velocity Profile",
            hovertemplate=(
                "Velocity = %{marker.color:.3f} m/s"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# FLOW PROFILE
# ============================================================

def _add_flow_profile(
    fig,
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
):
    number_lines = 20

    liquid_height = (
        liquid_top
        - liquid_bottom
    )

    for i in range(
        number_lines
    ):

        theta0 = (
            2.0
            * math.pi
            * i
            / number_lines
        )

        radial_position = (
            radius
            * (
                0.15
                + 0.70
                * i
                / max(
                    number_lines - 1,
                    1
                )
            )
        )

        t = np.linspace(
            0.0,
            2.0 * math.pi,
            160
        )

        radial = (
            radial_position
            * (
                0.78
                + 0.16
                * np.cos(t)
            )
        )

        angle = (
            theta0
            + 1.30 * t
        )

        x = (
            radial
            * np.cos(angle)
        )

        y = (
            radial
            * np.sin(angle)
        )

        z = (
            liquid_bottom
            + 0.50
            * liquid_height
            + 0.40
            * liquid_height
            * np.sin(t)
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=3
                ),
                opacity=0.65,
                showlegend=False,
                hoverinfo="skip",
                name="Flow Path",
            )
        )


# ============================================================
# VORTEX
# ============================================================

def _calculate_vortex_depth(
    radius,
    liquid_height,
    rpm,
):
    N = max(
        rpm / 60.0,
        0.0
    )

    Fr = (
        N**2
        * radius
        / 9.81
    )

    depth = (
        0.30
        * radius
        * Fr
    )

    return _clamp(
        depth,
        0.0,
        0.30
        * liquid_height
    )


# ============================================================
# DEAD ZONE
# ============================================================

def _add_dead_zones(
    fig,
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
    density_kg_m3,
    viscosity_pa_s,
):
    (
        X,
        Y,
        Z,
        U,
        V,
        W,
        speed,
    ) = _calculate_velocity_field(
        radius,
        liquid_bottom,
        liquid_top,
        rpm,
        density_kg_m3,
        viscosity_pa_s,
    )

    finite = speed[
        np.isfinite(speed)
    ]

    if finite.size == 0:
        return

    threshold = np.percentile(
        finite,
        20
    )

    mask = (
        np.isfinite(speed)
        & (
            speed <= threshold
        )
    )

    x = X[mask]
    y = Y[mask]
    z = Z[mask]

    if len(x) > 500:

        idx = np.linspace(
            0,
            len(x) - 1,
            500
        ).astype(int)

        x = x[idx]
        y = y[idx]
        z = z[idx]

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=5,
                symbol="circle",
                opacity=0.75,
            ),
            name="Potential Dead Zones",
            hovertemplate=(
                "Potential low-velocity zone"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# MIXING PARTICLES
# ============================================================

def _add_particles(
    fig,
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
):
    rng = np.random.default_rng(
        42
    )

    n_particles = 150

    r = (
        radius
        * np.sqrt(
            rng.random(
                n_particles
            )
        )
        * 0.86
    )

    theta = (
        rng.random(
            n_particles
        )
        * 2.0
        * math.pi
    )

    x0 = (
        r
        * np.cos(theta)
    )

    y0 = (
        r
        * np.sin(theta)
    )

    z0 = (
        liquid_bottom
        + rng.random(
            n_particles
        )
        * (
            liquid_top
            - liquid_bottom
        )
    )

    frames = []

    N = max(
        rpm / 60.0,
        0.01
    )

    number_frames = 50

    for frame_index in range(
        number_frames
    ):

        time = (
            frame_index
            / max(
                number_frames - 1,
                1
            )
        )

        rotation = (
            2.0
            * math.pi
            * N
            * time
            * 3.0
        )

        x = (
            x0
            * np.cos(rotation)
            - y0
            * np.sin(rotation)
        )

        y = (
            x0
            * np.sin(rotation)
            + y0
            * np.cos(rotation)
        )

        z = (
            z0
            + 0.15
            * (
                liquid_top
                - liquid_bottom
            )
            * np.sin(
                rotation
                + z0
            )
        )

        z = np.clip(
            z,
            liquid_bottom,
            liquid_top
        )

        frames.append(
            go.Frame(
                data=[
                    go.Scatter3d(
                        x=x,
                        y=y,
                        z=z,
                        mode="markers",
                        marker=dict(
                            size=4
                        ),
                        name="Mixing Particles",
                    )
                ],
                name=str(
                    frame_index
                ),
            )
        )

    fig.add_trace(
        go.Scatter3d(
            x=x0,
            y=y0,
            z=z0,
            mode="markers",
            marker=dict(
                size=4
            ),
            name="Mixing Particles",
        )
    )

    fig.frames = frames


# ============================================================
# GAS-LIQUID BUBBLES
# ============================================================

def _add_gas_bubbles(
    fig,
    radius,
    liquid_bottom,
    liquid_top,
    gas_flow_m3_h,
    bubble_diameter_mm,
):
    gas_flow = _safe_float(
        gas_flow_m3_h,
        0.0
    )

    if gas_flow <= 0:
        return

    rng = np.random.default_rng(
        15
    )

    number_bubbles = int(
        _clamp(
            40
            + 10
            * gas_flow,
            40,
            350
        )
    )

    r = (
        radius
        * np.sqrt(
            rng.random(
                number_bubbles
            )
        )
        * 0.70
    )

    theta = (
        rng.random(
            number_bubbles
        )
        * 2.0
        * math.pi
    )

    x = (
        r
        * np.cos(theta)
    )

    y = (
        r
        * np.sin(theta)
    )

    z = (
        liquid_bottom
        + rng.random(
            number_bubbles
        )
        * (
            liquid_top
            - liquid_bottom
        )
    )

    size = _clamp(
        _safe_float(
            bubble_diameter_mm,
            3.0
        ),
        2.0,
        10.0
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=size,
                opacity=0.70,
                symbol="circle",
            ),
            name="Gas Bubbles",
            hovertemplate=(
                "Gas Bubble"
                "<br>X = %{x:.2f} m"
                "<br>Y = %{y:.2f} m"
                "<br>Z = %{z:.2f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# DIMENSIONS
# ============================================================

def _add_dimensions(
    fig,
    geometry,
    liquid_z,
):
    R = geometry["R"]

    # --------------------------------------------------------
    # DIAMETER
    # --------------------------------------------------------

    dimension_y = -1.18 * R

    fig.add_trace(
        go.Scatter3d(
            x=[
                -R,
                R,
            ],
            y=[
                dimension_y,
                dimension_y,
            ],
            z=[
                liquid_z,
                liquid_z,
            ],
            mode="lines+text",
            text=[
                "",
                f"D = {2.0 * R:.2f} m",
            ],
            textposition="top center",
            line=dict(
                width=4
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # --------------------------------------------------------
    # TOTAL HEIGHT
    # --------------------------------------------------------

    dimension_x = 1.18 * R

    total_height = (
        geometry["z_top"]
        - geometry["z_bottom"]
    )

    fig.add_trace(
        go.Scatter3d(
            x=[
                dimension_x,
                dimension_x,
            ],
            y=[
                0.0,
                0.0,
            ],
            z=[
                geometry["z_bottom"],
                geometry["z_top"],
            ],
            mode="lines+text",
            text=[
                "",
                f"H = {total_height:.2f} m",
            ],
            textposition="middle right",
            line=dict(
                width=4
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )


# ============================================================
# MAIN FUNCTION
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
    selected_features=None,

    # --------------------------------------------------------
    # BACKWARD COMPATIBILITY WITH OLD APP
    # --------------------------------------------------------

    D=None,
    H=None,
    volume=None,
    liquid_level=None,
    agitator=None,
    impeller_diameter_m=None,
    number_impellers=1,
    impeller_clearance_m=None,

    **kwargs,
):

    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================

    if tank_diameter_m is None:
        tank_diameter_m = D

    if straight_height_m is None:
        straight_height_m = H

    if volume_m3 is None:
        volume_m3 = volume

    if liquid_height_m is None:
        liquid_height_m = liquid_level

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

    density_kg_m3 = _safe_float(
        density_kg_m3,
        1000.0
    )

    viscosity_pa_s = _safe_float(
        viscosity_pa_s,
        0.001
    )

    # ========================================================
    # CREATE GEOMETRY
    # ========================================================

    geometry = _create_geometry(
        tank_diameter_m,
        straight_height_m,
        bottom_type,
        top_type,
    )

    # ========================================================
    # LIQUID LEVEL
    # ========================================================

    if liquid_height_m is None:

        liquid_z = _liquid_level_from_volume(
            volume_m3,
            geometry,
        )

    else:

        requested_height = _safe_float(
            liquid_height_m,
            straight_height_m
        )

        liquid_z = (
            geometry["z_bottom"]
            + requested_height
        )

        liquid_z = _clamp(
            liquid_z,
            geometry["z_bottom"],
            geometry["z_top"],
        )

    actual_liquid_height = max(
        liquid_z
        - geometry["z_bottom"],
        0.05
    )

    # ========================================================
    # IMPellers
    # ========================================================

    normalized_impellers = (
        _normalize_impellers(
            impellers=impellers,
            agitator=agitator,
            impeller_diameter_m=(
                impeller_diameter_m
            ),
            impeller_clearance_m=(
                impeller_clearance_m
            ),
            number_impellers=(
                number_impellers
            ),
            liquid_height_m=(
                actual_liquid_height
            ),
        )
    )

    # ========================================================
    # SELECTION
    # ========================================================

    if selected_features is None:

        selected_features = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
        ]

    if isinstance(
        selected_features,
        str
    ):

        selected_features = [
            selected_features
        ]

    selected_features = [
        str(feature).strip()
        for feature in selected_features
    ]

    # Support "Select All"
    if (
        "Select All"
        in selected_features
        or "All"
        in selected_features
    ):

        selected_features = (
            VISUALIZATION_FEATURES.copy()
        )

    # ========================================================
    # CREATE FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # REACTOR GEOMETRY
    # ========================================================

    if "Reactor Geometry" in selected_features:

        _add_vessel(
            fig,
            geometry,
            bottom_type,
            top_type,
        )

    # ========================================================
    # LIQUID LEVEL
    # ========================================================

    if "Liquid Level" in selected_features:

        _add_liquid_surface(
            fig,
            geometry["R"],
            liquid_z,
            vortex_depth=0.0,
        )

    # ========================================================
    # IMPELLER + SHAFT
    # ========================================================

    if (
        "Impeller & Shaft"
        in selected_features
    ):

        _add_shaft(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z,
        )

        for impeller in normalized_impellers:

            _add_impeller(
                fig,
                impeller,
                geometry["R"],
            )

    # ========================================================
    # BAFFLES
    # ========================================================

    if "Baffles" in selected_features:

        _add_baffles(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z,
            number_baffles,
        )

    # ========================================================
    # VORTEX
    # ========================================================

    if "Vortex Formation" in selected_features:

        vortex_depth = (
            _calculate_vortex_depth(
                geometry["R"],
                actual_liquid_height,
                rpm,
            )
        )

        _add_liquid_surface(
            fig,
            geometry["R"],
            liquid_z,
            vortex_depth=vortex_depth,
        )

    # ========================================================
    # VELOCITY PROFILE
    # ========================================================

    if "Velocity Profile" in selected_features:

        _add_velocity_profile(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z,
            rpm,
            density_kg_m3,
            viscosity_pa_s,
        )

    # ========================================================
    # FLOW PROFILE
    # ========================================================

    if "Flow Profile" in selected_features:

        _add_flow_profile(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z,
            rpm,
        )

    # ========================================================
    # DEAD ZONES
    # ========================================================

    if "Dead Zone Analysis" in selected_features:

        _add_dead_zones(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z,
            rpm,
            density_kg_m3,
            viscosity_pa_s,
        )

    # ========================================================
    # PARTICLES
    # ========================================================

    if "Mixing Particles" in selected_features:

        _add_particles(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z,
            rpm,
        )

    # ========================================================
    # GAS BUBBLES
    # ========================================================

    if (
        "Gas-Liquid Bubbles"
        in selected_features
    ):

        _add_gas_bubbles(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z,
            gas_flow_m3_h,
            bubble_diameter_mm,
        )

    # ========================================================
    # DIMENSIONS
    # ========================================================

    if "Dimensions" in selected_features:

        _add_dimensions(
            fig,
            geometry,
            liquid_z,
        )

    # ========================================================
    # CAMERA / SCENE
    # ========================================================

    total_height = (
        geometry["z_top"]
        - geometry["z_bottom"]
    )

    diameter = geometry["D"]

    aspect_z = max(
        1.25,
        total_height
        / max(
            diameter,
            1e-12
        )
    )

    fig.update_layout(

        title=dict(
            text=(
                "3D Reactor Engineering Visualization"
            ),
            x=0.5,
            xanchor="center",
        ),

        scene=dict(

            xaxis=dict(
                title="X (m)",
                showbackground=True,
                backgroundcolor=(
                    "rgba(245,245,245,0.45)"
                ),
                gridcolor="lightgray",
                zeroline=True,
            ),

            yaxis=dict(
                title="Y (m)",
                showbackground=True,
                backgroundcolor=(
                    "rgba(245,245,245,0.45)"
                ),
                gridcolor="lightgray",
                zeroline=True,
            ),

            zaxis=dict(
                title="Z (m)",
                showbackground=True,
                backgroundcolor=(
                    "rgba(245,245,245,0.45)"
                ),
                gridcolor="lightgray",
                zeroline=True,
                range=[
                    geometry["z_bottom"]
                    - 0.10 * total_height,
                    geometry["z_top"]
                    + 0.10 * total_height,
                ],
            ),

            aspectmode="manual",

            aspectratio=dict(
                x=1.0,
                y=1.0,
                z=aspect_z,
            ),

            camera=dict(
                eye=dict(
                    x=1.55,
                    y=1.55,
                    z=1.10,
                ),
                center=dict(
                    x=0.0,
                    y=0.0,
                    z=0.0,
                ),
            ),
        ),

        margin=dict(
            l=0,
            r=0,
            t=60,
            b=0,
        ),

        hovermode="closest",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="center",
            x=0.5,
        ),
    )

    # ========================================================
    # INFORMATION ANNOTATION
    # ========================================================

    active_layers = ", ".join(
        selected_features
    )

    fig.add_annotation(
        text=(
            f"<b>Active Layers:</b> "
            f"{active_layers}"
            f"<br>"
            f"D = {diameter:.2f} m"
            f" &nbsp;|&nbsp; "
            f"Liquid Height = "
            f"{actual_liquid_height:.2f} m"
            f" &nbsp;|&nbsp; "
            f"RPM = {rpm:.0f}"
        ),
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.01,
        showarrow=False,
        align="left",
        font=dict(
            size=11
        ),
    )

    return fig


# ============================================================
# ALIAS
# ============================================================

def create_reactor_3d(**kwargs):
    return create_reactor_animation(
        **kwargs
    )
