# visualization/reactor_3d.py

import math
import numpy as np
import plotly.graph_objects as go


# ============================================================
# BASIC HELPERS
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


def _get(data, *keys, default=None):
    if data is None:
        return default

    for key in keys:
        if isinstance(data, dict) and key in data:
            return data[key]

        if hasattr(data, key):
            return getattr(data, key)

    return default


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
    Converts all possible impeller input formats into:

    [
        {
            "position": ...,
            "type": ...,
            "diameter_m": ...,
            "elevation_m": ...
        }
    ]
    """

    normalized = []

    if isinstance(impellers, list) and len(impellers) > 0:

        for i, item in enumerate(impellers):

            if not isinstance(item, dict):
                continue

            imp_type = (
                item.get("agitator_type")
                or item.get("type")
                or item.get("agitator")
                or agitator
                or "Rushton Turbine"
            )

            diameter = _safe_float(
                item.get("diameter_m")
                or item.get("D")
                or impeller_diameter_m,
                0.0,
            )

            elevation = item.get("elevation_m")

            if elevation is None:
                elevation = item.get("bottom_clearance_m")

            if elevation is None:
                elevation = (
                    (i + 1)
                    * liquid_height_m
                    / (len(impellers) + 1)
                )

            normalized.append(
                {
                    "position": item.get(
                        "position",
                        f"Impeller {i + 1}"
                    ),
                    "type": imp_type,
                    "diameter_m": diameter,
                    "elevation_m": _safe_float(
                        elevation,
                        0.0
                    ),
                }
            )

    if not normalized:

        n = max(1, _safe_int(number_impellers, 1))

        D = _safe_float(
            impeller_diameter_m,
            0.0
        )

        clearance = _safe_float(
            impeller_clearance_m,
            0.4
        )

        for i in range(n):

            elevation = clearance

            if n > 1:
                elevation = (
                    clearance
                    + i
                    * (
                        max(
                            liquid_height_m
                            - 2.0 * clearance,
                            0.0
                        )
                        / max(n - 1, 1)
                    )
                )

            normalized.append(
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
                    "diameter_m": D,
                    "elevation_m": elevation,
                }
            )

    return normalized


# ============================================================
# HEAD GEOMETRY
# ============================================================

def _head_depth(diameter_m, head_type):

    D = diameter_m

    text = str(
        head_type or ""
    ).lower()

    if "2:1" in text or "ellipsoid" in text:
        return D / 4.0

    if "toris" in text:
        return 0.10 * D

    if "flat" in text:
        return 0.0

    return 0.10 * D


# ============================================================
# VESSEL GEOMETRY
# ============================================================

def _create_vessel_geometry(
    diameter_m,
    straight_height_m,
    bottom_type,
    top_type,
):
    D = diameter_m
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
    z_bottom_tangent = bottom_depth
    z_top_tangent = (
        bottom_depth
        + straight_height_m
    )
    z_top = (
        z_top_tangent
        + top_depth
    )

    return {
        "D": D,
        "R": R,
        "bottom_depth": bottom_depth,
        "top_depth": top_depth,
        "z_bottom": z_bottom,
        "z_bottom_tangent": z_bottom_tangent,
        "z_top_tangent": z_top_tangent,
        "z_top": z_top,
    }


# ============================================================
# CYLINDER SURFACE
# ============================================================

def _cylinder_surface(
    radius,
    z0,
    z1,
    resolution=80,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        resolution
    )

    z = np.linspace(
        z0,
        z1,
        30
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    x = radius * np.cos(theta_grid)
    y = radius * np.sin(theta_grid)

    return x, y, z_grid


# ============================================================
# ELLIPSOID HEAD
# ============================================================

def _ellipsoidal_head(
    radius,
    z_center,
    depth,
    orientation="bottom",
    resolution=80,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        resolution
    )

    phi = np.linspace(
        0,
        math.pi / 2.0,
        25
    )

    theta_grid, phi_grid = np.meshgrid(
        theta,
        phi
    )

    x = radius * np.sin(phi_grid) * np.cos(theta_grid)
    y = radius * np.sin(phi_grid) * np.sin(theta_grid)

    if orientation == "bottom":

        z = (
            z_center
            - depth * np.cos(phi_grid)
        )

    else:

        z = (
            z_center
            + depth * np.cos(phi_grid)
        )

    return x, y, z


# ============================================================
# TORISPHERICAL-LIKE HEAD
# ============================================================

def _torispherical_head(
    radius,
    z_center,
    depth,
    orientation="bottom",
    resolution=80,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        resolution
    )

    phi = np.linspace(
        0,
        math.pi / 2.0,
        25
    )

    theta_grid, phi_grid = np.meshgrid(
        theta,
        phi
    )

    # Smooth engineering visualization
    # approximating a torispherical profile.
    radial_factor = np.sin(phi_grid)

    x = (
        radius
        * radial_factor
        * np.cos(theta_grid)
    )

    y = (
        radius
        * radial_factor
        * np.sin(theta_grid)
    )

    profile = (
        0.5
        - 0.5 * np.cos(phi_grid)
    )

    if orientation == "bottom":

        z = (
            z_center
            - depth * profile
        )

    else:

        z = (
            z_center
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

    zb = geometry["z_bottom_tangent"]
    zt = geometry["z_top_tangent"]

    # --------------------------------------------------------
    # CYLINDRICAL SHELL
    # --------------------------------------------------------

    x, y, z = _cylinder_surface(
        R,
        zb,
        zt
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            showscale=False,
            opacity=0.22,
            hoverinfo="skip",
            name="Reactor Shell",
        )
    )

    # --------------------------------------------------------
    # BOTTOM HEAD
    # --------------------------------------------------------

    if "2:1" in str(bottom_type).lower() or \
       "ellipsoid" in str(bottom_type).lower():

        x, y, z = _ellipsoidal_head(
            R,
            zb,
            geometry["bottom_depth"],
            "bottom"
        )

    else:

        x, y, z = _torispherical_head(
            R,
            zb,
            geometry["bottom_depth"],
            "bottom"
        )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            showscale=False,
            opacity=0.22,
            hoverinfo="skip",
            name="Bottom Head",
        )
    )

    # --------------------------------------------------------
    # TOP HEAD
    # --------------------------------------------------------

    if "2:1" in str(top_type).lower() or \
       "ellipsoid" in str(top_type).lower():

        x, y, z = _ellipsoidal_head(
            R,
            zt,
            geometry["top_depth"],
            "top"
        )

    else:

        x, y, z = _torispherical_head(
            R,
            zt,
            geometry["top_depth"],
            "top"
        )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            showscale=False,
            opacity=0.22,
            hoverinfo="skip",
            name="Top Head",
        )
    )


# ============================================================
# LIQUID HEIGHT
# ============================================================

def _calculate_liquid_height(
    volume_m3,
    geometry,
):

    V = _safe_float(
        volume_m3,
        0.0
    )

    D = geometry["D"]
    R = geometry["R"]

    bottom_depth = geometry[
        "bottom_depth"
    ]

    straight_height = (
        geometry["z_top_tangent"]
        - geometry["z_bottom_tangent"]
    )

    top_depth = geometry[
        "top_depth"
    ]

    cylinder_area = math.pi * R**2

    # Approximate head volumes.
    bottom_volume = (
        math.pi
        * D**3
        / 24.0
        if bottom_depth > 0
        else 0.0
    )

    top_volume = (
        math.pi
        * D**3
        / 24.0
        if top_depth > 0
        else 0.0
    )

    if V <= 0:
        return geometry["z_bottom_tangent"]

    if V <= bottom_volume and bottom_depth > 0:

        fraction = _clamp(
            V / bottom_volume,
            0.0,
            1.0
        )

        return (
            geometry["z_bottom"]
            + fraction * bottom_depth
        )

    V_remaining = max(
        V - bottom_volume,
        0.0
    )

    cylinder_volume = (
        cylinder_area
        * straight_height
    )

    if V_remaining <= cylinder_volume:

        h = (
            V_remaining
            / cylinder_area
        )

        return (
            geometry["z_bottom_tangent"]
            + h
        )

    V_after_cylinder = (
        V_remaining
        - cylinder_volume
    )

    if top_volume > 0:

        fraction = _clamp(
            V_after_cylinder
            / top_volume,
            0.0,
            1.0
        )

        return (
            geometry["z_top_tangent"]
            + fraction * top_depth
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
    vortex=False,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        100
    )

    r = np.linspace(
        0,
        radius * 0.985,
        40
    )

    rr, tt = np.meshgrid(
        r,
        theta
    )

    x = rr * np.cos(tt)
    y = rr * np.sin(tt)

    if vortex and vortex_depth > 0:

        normalized_r = rr / radius

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
            showscale=False,
            opacity=0.60,
            hovertemplate=(
                "Liquid surface"
                "<br>X=%{x:.2f} m"
                "<br>Y=%{y:.2f} m"
                "<br>Z=%{z:.2f} m"
                "<extra></extra>"
            ),
            name="Liquid Level",
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

    if n <= 0:
        return

    theta_values = np.linspace(
        0,
        2 * math.pi,
        n,
        endpoint=False
    )

    width = max(
        0.06,
        radius * 0.08
    )

    for theta in theta_values:

        ux = math.cos(theta)
        uy = math.sin(theta)

        tx = -uy
        ty = ux

        z = np.linspace(
            z_bottom,
            z_top,
            20
        )

        center_r = radius * 0.92

        x1 = (
            center_r * ux
            + width * tx
        )

        y1 = (
            center_r * uy
            + width * ty
        )

        x2 = (
            center_r * ux
            - width * tx
        )

        y2 = (
            center_r * uy
            - width * ty
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
                    z[0],
                    z[0],
                    z[-1],
                    z[-1],
                    z[0],
                ],
                mode="lines",
                line=dict(
                    width=7
                ),
                hoverinfo="skip",
                name=f"Baffle {int(theta_values.tolist().index(theta)) + 1}",
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
        0.015,
        radius * 0.025
    )

    theta = np.linspace(
        0,
        2 * math.pi,
        30
    )

    z = np.linspace(
        z_bottom,
        z_top,
        40
    )

    tt, zz = np.meshgrid(
        theta,
        z
    )

    x = (
        shaft_radius
        * np.cos(tt)
    )

    y = (
        shaft_radius
        * np.sin(tt)
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=zz,
            showscale=False,
            opacity=0.95,
            hoverinfo="skip",
            name="Shaft",
        )
    )


# ============================================================
# IMPELLER
# ============================================================

def _add_rushton(
    fig,
    D,
    z,
):

    R = D / 2.0

    # Hub
    theta = np.linspace(
        0,
        2 * math.pi,
        40
    )

    hub_r = D * 0.13

    fig.add_trace(
        go.Scatter3d(
            x=hub_r * np.cos(theta),
            y=hub_r * np.sin(theta),
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

    # Six blades
    n_blades = 6

    for i in range(n_blades):

        a = (
            2
            * math.pi
            * i
            / n_blades
        )

        r1 = D * 0.14
        r2 = R * 0.92

        x1 = r1 * math.cos(a)
        y1 = r1 * math.sin(a)

        x2 = r2 * math.cos(a)
        y2 = r2 * math.sin(a)

        # blade width in tangential direction
        tx = -math.sin(a)
        ty = math.cos(a)

        width = D * 0.045

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

        zs = [
            z,
            z,
            z,
            z,
            z,
        ]

        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="lines",
                line=dict(
                    width=8
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )


def _add_pbt(
    fig,
    D,
    z,
):

    R = D / 2.0

    theta = np.linspace(
        0,
        2 * math.pi,
        80
    )

    for blade in range(4):

        a = (
            2
            * math.pi
            * blade
            / 4.0
        )

        r = np.linspace(
            D * 0.15,
            R * 0.95,
            30
        )

        # Slight pitch representation
        local_angle = (
            a
            + 0.25
            * (r / max(R, 1e-9))
        )

        x = r * np.cos(
            local_angle
        )

        y = r * np.sin(
            local_angle
        )

        zz = (
            z
            + 0.10 * D
            * (
                r / max(R, 1e-9)
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


def _add_hydrofoil(
    fig,
    D,
    z,
):

    R = D / 2.0

    for blade in range(3):

        a = (
            2
            * math.pi
            * blade
            / 3.0
        )

        r = np.linspace(
            D * 0.12,
            R * 0.95,
            50
        )

        sweep = (
            a
            + 0.55
            * (
                r / max(R, 1e-9)
            )
        )

        x = r * np.cos(sweep)
        y = r * np.sin(sweep)

        zz = (
            z
            + 0.05
            * D
            * (
                r / max(R, 1e-9)
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


def _add_marine(
    fig,
    D,
    z,
):

    R = D / 2.0

    for blade in range(3):

        a = (
            2
            * math.pi
            * blade
            / 3.0
        )

        t = np.linspace(
            -0.8,
            0.8,
            50
        )

        r = (
            D * 0.15
            + (
                R * 0.8
            )
            * (
                t + 1.0
            )
            / 2.0
        )

        angle = (
            a
            + 0.55 * t
        )

        x = r * np.cos(angle)
        y = r * np.sin(angle)

        zz = (
            z
            + 0.06
            * D
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


def _add_anchor(
    fig,
    D,
    z,
    vessel_radius,
):

    outer = min(
        D / 2.0,
        vessel_radius * 0.90
    )

    theta = np.linspace(
        0,
        2 * math.pi,
        100
    )

    x = outer * np.cos(theta)
    y = outer * np.sin(theta)

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


def _add_helical_ribbon(
    fig,
    D,
    z,
    vessel_radius,
):

    r = min(
        D / 2.0,
        vessel_radius * 0.90
    )

    theta = np.linspace(
        0,
        4 * math.pi,
        180
    )

    height = max(
        D * 0.8,
        0.5
    )

    x = r * np.cos(theta)
    y = r * np.sin(theta)

    zz = (
        z
        + height
        * (
            theta
            / max(
                theta[-1],
                1e-9
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


def _add_generic_impeller(
    fig,
    D,
    z,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        100
    )

    r = D / 2.0

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


def _add_impeller(
    fig,
    impeller,
    vessel_radius,
):

    D = _safe_float(
        impeller.get("diameter_m"),
        vessel_radius
    )

    z = _safe_float(
        impeller.get("elevation_m"),
        0.5
    )

    imp_type = str(
        impeller.get(
            "type",
            "Rushton Turbine"
        )
    ).lower()

    if "rushton" in imp_type:

        _add_rushton(
            fig,
            D,
            z
        )

    elif (
        "pitched" in imp_type
        or "pbt" in imp_type
    ):

        _add_pbt(
            fig,
            D,
            z
        )

    elif "hydrofoil" in imp_type:

        _add_hydrofoil(
            fig,
            D,
            z
        )

    elif (
        "marine" in imp_type
        or "propeller" in imp_type
    ):

        _add_marine(
            fig,
            D,
            z
        )

    elif "anchor" in imp_type:

        _add_anchor(
            fig,
            D,
            z,
            vessel_radius
        )

    elif "helical" in imp_type:

        _add_helical_ribbon(
            fig,
            D,
            z,
            vessel_radius
        )

    else:

        _add_generic_impeller(
            fig,
            D,
            z
        )


# ============================================================
# FLOW FIELD
# ============================================================

def _calculate_flow_field(
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
    density,
    viscosity,
):

    n = 13

    x = np.linspace(
        -radius * 0.85,
        radius * 0.85,
        n
    )

    y = np.linspace(
        -radius * 0.85,
        radius * 0.85,
        n
    )

    z = np.linspace(
        liquid_bottom,
        liquid_top,
        9
    )

    X, Y, Z = np.meshgrid(
        x,
        y,
        z,
        indexing="xy"
    )

    radial = np.sqrt(
        X**2 + Y**2
    )

    inside = (
        radial
        <= radius * 0.90
    )

    # Dimensionless screening velocity
    N = max(
        rpm / 60.0,
        0.01
    )

    characteristic = (
        N
        * radius
    )

    # Rotational component
    swirl = (
        0.55
        * characteristic
        * np.exp(
            -(
                radial
                / max(radius, 1e-9)
            )**2
        )
    )

    # Radial circulation
    radial_velocity = (
        0.35
        * characteristic
        * np.sin(
            math.pi
            * (
                Z
                - liquid_bottom
            )
            / max(
                liquid_top
                - liquid_bottom,
                1e-9
            )
        )
        * (
            1.0
            - radial
            / max(radius, 1e-9)
        )
    )

    # Axial circulation
    axial_velocity = (
        0.45
        * characteristic
        * np.cos(
            math.pi
            * (
                Z
                - liquid_bottom
            )
            / max(
                liquid_top
                - liquid_bottom,
                1e-9
            )
        )
        * np.exp(
            -(
                radial
                / max(radius, 1e-9)
            )**2
        )
    )

    safe_radial = np.maximum(
        radial,
        1e-8
    )

    U = (
        -swirl
        * Y
        / safe_radial
        + radial_velocity
        * X
        / safe_radial
    )

    V = (
        swirl
        * X
        / safe_radial
        + radial_velocity
        * Y
        / safe_radial
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

    return X, Y, Z, U, V, W, speed


# ============================================================
# VELOCITY PROFILE
# ============================================================

def _add_velocity_profile(
    fig,
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
    density,
    viscosity,
):

    (
        X,
        Y,
        Z,
        U,
        V,
        W,
        speed,
    ) = _calculate_flow_field(
        radius,
        liquid_bottom,
        liquid_top,
        rpm,
        density,
        viscosity,
    )

    mask = (
        np.isfinite(speed)
        & (
            speed
            > np.nanpercentile(
                speed,
                20
            )
        )
    )

    x = X[mask]
    y = Y[mask]
    z = Z[mask]
    s = speed[mask]

    if len(x) > 600:

        indices = np.linspace(
            0,
            len(x) - 1,
            600
        ).astype(int)

        x = x[indices]
        y = y[indices]
        z = z[indices]
        s = s[indices]

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
# FLOW PROFILE / STREAMLINES
# ============================================================

def _add_flow_profile(
    fig,
    radius,
    liquid_bottom,
    liquid_top,
    rpm,
):

    n_lines = 18

    N = max(
        rpm / 60.0,
        0.01
    )

    height = (
        liquid_top
        - liquid_bottom
    )

    for i in range(
        n_lines
    ):

        theta = (
            2
            * math.pi
            * i
            / n_lines
        )

        r = radius * (
            0.18
            + 0.68
            * (
                i
                / max(
                    n_lines - 1,
                    1
                )
            )
        )

        t = np.linspace(
            0,
            2 * math.pi,
            120
        )

        z = (
            liquid_bottom
            + 0.5 * height
            + 0.38
            * height
            * np.sin(t)
        )

        radial = (
            r
            * (
                0.75
                + 0.15
                * np.cos(t)
            )
        )

        angle = (
            theta
            + 1.2 * t
        )

        x = (
            radial
            * np.cos(angle)
        )

        y = (
            radial
            * np.sin(angle)
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
    rpm,
    radius,
    liquid_height,
):

    N = rpm / 60.0

    Fr = (
        N**2
        * radius
        / 9.81
    )

    depth = (
        0.35
        * radius
        * Fr
    )

    return _clamp(
        depth,
        0.0,
        0.35 * liquid_height
    )


def _add_vortex(
    fig,
    radius,
    liquid_z,
    rpm,
    liquid_height,
):

    depth = _calculate_vortex_depth(
        rpm,
        radius,
        liquid_height
    )

    _add_liquid_surface(
        fig,
        radius,
        liquid_z,
        vortex_depth=depth,
        vortex=True
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
):

    (
        X,
        Y,
        Z,
        U,
        V,
        W,
        speed,
    ) = _calculate_flow_field(
        radius,
        liquid_bottom,
        liquid_top,
        rpm,
        1000.0,
        0.001,
    )

    finite_speed = speed[
        np.isfinite(speed)
    ]

    if len(finite_speed) == 0:
        return

    threshold = np.nanpercentile(
        finite_speed,
        20
    )

    mask = (
        np.isfinite(speed)
        & (speed <= threshold)
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
    frames=30,
):

    rng = np.random.default_rng(
        42
    )

    n_particles = 120

    r = (
        radius
        * np.sqrt(
            rng.random(
                n_particles
            )
        )
        * 0.88
    )

    theta = (
        rng.random(
            n_particles
        )
        * 2
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

    data_frames = []

    N = max(
        rpm / 60.0,
        0.01
    )

    for frame in range(
        frames
    ):

        time = (
            frame
            / max(
                frames - 1,
                1
            )
        )

        angle = (
            2
            * math.pi
            * N
            * time
            * 3.0
        )

        x = (
            x0
            * np.cos(angle)
            - y0
            * np.sin(angle)
        )

        y = (
            x0
            * np.sin(angle)
            + y0
            * np.cos(angle)
        )

        # axial circulation
        z = (
            z0
            + 0.18
            * (
                liquid_top
                - liquid_bottom
            )
            * np.sin(
                angle
                + z0
            )
        )

        z = np.clip(
            z,
            liquid_bottom,
            liquid_top
        )

        data_frames.append(
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
                        name="Particles",
                    )
                ],
                name=str(frame),
            )
        )

    # Initial particle trace
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

    fig.frames = data_frames

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.05,
                y=0.05,
                buttons=[
                    dict(
                        label="▶ Play Mixing",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {
                                    "duration": 80,
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


# ============================================================
# GAS BUBBLES
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
        10
    )

    n = int(
        _clamp(
            40
            + gas_flow * 8,
            40,
            300
        )
    )

    r = (
        radius
        * np.sqrt(
            rng.random(n)
        )
        * 0.70
    )

    theta = (
        rng.random(n)
        * 2
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
        + rng.random(n)
        * (
            liquid_top
            - liquid_bottom
        )
    )

    bubble_size = _clamp(
        _safe_float(
            bubble_diameter_mm,
            3.0
        ) * 1.8,
        3,
        12
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=bubble_size,
                opacity=0.65,
                symbol="circle",
            ),
            name="Gas Bubbles",
            hovertemplate=(
                "Gas bubble"
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

    # Diameter
    fig.add_trace(
        go.Scatter3d(
            x=[
                -R,
                R,
            ],
            y=[
                -R * 1.12,
                -R * 1.12,
            ],
            z=[
                liquid_z,
                liquid_z,
            ],
            mode="lines+text",
            text=[
                "",
                f"D = {2 * R:.2f} m",
            ],
            textposition="top center",
            line=dict(
                width=4
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Height
    fig.add_trace(
        go.Scatter3d(
            x=[
                R * 1.15,
                R * 1.15,
            ],
            y=[
                0,
                0,
            ],
            z=[
                geometry["z_bottom"],
                geometry["z_top"],
            ],
            mode="lines+text",
            text=[
                "",
                f"H = {geometry['z_top'] - geometry['z_bottom']:.2f} m",
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
# MAIN 3D FUNCTION
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
    # BACKWARD COMPATIBILITY
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
    # GEOMETRY
    # ========================================================

    geometry = _create_vessel_geometry(
        tank_diameter_m,
        straight_height_m,
        bottom_type,
        top_type,
    )

    if liquid_height_m is None:

        liquid_z = _calculate_liquid_height(
            volume_m3,
            geometry
        )

    else:

        liquid_height_input = _safe_float(
            liquid_height_m,
            straight_height_m
        )

        # Support both:
        # total height and straight-side height.
        liquid_z = (
            geometry["z_bottom"]
            + liquid_height_input
        )

        liquid_z = _clamp(
            liquid_z,
            geometry["z_bottom"],
            geometry["z_top"]
        )

    liquid_bottom = geometry[
        "z_bottom"
    ]

    liquid_height_actual = max(
        liquid_z - liquid_bottom,
        0.05
    )

    # ========================================================
    # IMPELLERS
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
                liquid_height_actual
            ),
        )
    )

    # ========================================================
    # FEATURE SELECTION
    # ========================================================

    all_features = [
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

    # Select All support
    normalized_selection = [
        str(x).strip()
        for x in selected_features
    ]

    if (
        "Select All"
        in normalized_selection
        or "All"
        in normalized_selection
    ):

        normalized_selection = all_features

    # ========================================================
    # CREATE FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # 1. REACTOR GEOMETRY
    # ========================================================

    if "Reactor Geometry" in normalized_selection:

        _add_vessel(
            fig,
            geometry,
            bottom_type,
            top_type,
        )

    # ========================================================
    # 2. LIQUID LEVEL
    # ========================================================

    if "Liquid Level" in normalized_selection:

        _add_liquid_surface(
            fig,
            geometry["R"],
            liquid_z
        )

    # ========================================================
    # 3. SHAFT + IMPELLERS
    # ========================================================

    if (
        "Impeller & Shaft"
        in normalized_selection
    ):

        _add_shaft(
            fig,
            geometry["R"],
            geometry["z_bottom"],
            liquid_z + geometry["top_depth"]
        )

        for impeller in normalized_impellers:

            _add_impeller(
                fig,
                impeller,
                geometry["R"]
            )

    # ========================================================
    # 4. BAFFLES
    # ========================================================

    if "Baffles" in normalized_selection:

        _add_baffles(
            fig,
            geometry["R"],
            liquid_bottom,
            liquid_z,
            number_baffles,
        )

    # ========================================================
    # 5. VORTEX
    # ========================================================

    if "Vortex Formation" in normalized_selection:

        _add_vortex(
            fig,
            geometry["R"],
            liquid_z,
            rpm,
            liquid_height_actual,
        )

    # ========================================================
    # 6. VELOCITY PROFILE
    # ========================================================

    if "Velocity Profile" in normalized_selection:

        _add_velocity_profile(
            fig,
            geometry["R"],
            liquid_bottom,
            liquid_z,
            rpm,
            density_kg_m3,
            viscosity_pa_s,
        )

    # ========================================================
    # 7. FLOW PROFILE
    # ========================================================

    if "Flow Profile" in normalized_selection:

        _add_flow_profile(
            fig,
            geometry["R"],
            liquid_bottom,
            liquid_z,
            rpm,
        )

    # ========================================================
    # 8. DEAD ZONES
    # ========================================================

    if "Dead Zone Analysis" in normalized_selection:

        _add_dead_zones(
            fig,
            geometry["R"],
            liquid_bottom,
            liquid_z,
            rpm,
        )

    # ========================================================
    # 9. PARTICLES
    # ========================================================

    if "Mixing Particles" in normalized_selection:

        _add_particles(
            fig,
            geometry["R"],
            liquid_bottom,
            liquid_z,
            rpm,
            frames=40,
        )

    # ========================================================
    # 10. GAS-LIQUID
    # ========================================================

    if "Gas-Liquid Bubbles" in normalized_selection:

        _add_gas_bubbles(
            fig,
            geometry["R"],
            liquid_bottom,
            liquid_z,
            gas_flow_m3_h,
            bubble_diameter_mm,
        )

    # ========================================================
    # 11. DIMENSIONS
    # ========================================================

    if "Dimensions" in normalized_selection:

        _add_dimensions(
            fig,
            geometry,
            liquid_z
        )

    # ========================================================
    # CAMERA / LAYOUT
    # ========================================================

    total_height = (
        geometry["z_top"]
        - geometry["z_bottom"]
    )

    camera_eye = dict(
        x=1.65,
        y=1.65,
        z=1.15,
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
                backgroundcolor="rgba(240,240,240,0.4)",
                gridcolor="lightgray",
            ),

            yaxis=dict(
                title="Y (m)",
                showbackground=True,
                backgroundcolor="rgba(240,240,240,0.4)",
                gridcolor="lightgray",
            ),

            zaxis=dict(
                title="Z (m)",
                showbackground=True,
                backgroundcolor="rgba(240,240,240,0.4)",
                gridcolor="lightgray",
                range=[
                    geometry["z_bottom"]
                    - 0.15 * total_height,
                    geometry["z_top"]
                    + 0.15 * total_height,
                ],
            ),

            aspectmode="manual",

            aspectratio=dict(
                x=1,
                y=1,
                z=max(
                    1.4,
                    total_height
                    / max(
                        tank_diameter_m,
                        1e-9
                    )
                ),
            ),

            camera=dict(
                eye=camera_eye
            ),
        ),

        margin=dict(
            l=0,
            r=0,
            t=55,
            b=0,
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="center",
            x=0.5,
        ),

        hovermode="closest",
    )

    # ========================================================
    # ENGINEERING ANNOTATION
    # ========================================================

    selected_text = ", ".join(
        normalized_selection
    )

    fig.add_annotation(
        text=(
            f"<b>Selected:</b> {selected_text}"
            f"<br>"
            f"D = {tank_diameter_m:.2f} m"
            f" | "
            f"Liquid level = "
            f"{liquid_z - geometry['z_bottom']:.2f} m"
            f" | "
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
# SIMPLE ALIAS
# ============================================================

def create_reactor_3d(**kwargs):
    return create_reactor_animation(
        **kwargs
    )
