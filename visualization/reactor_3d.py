"""
3D Reactor Visualization
Reactor Scale-Up Engineering Studio

This module provides a CFD-inspired engineering visualization.
It is NOT a CFD solver and does not calculate actual velocity,
pressure, turbulence, concentration or species fields.
"""

import math
from typing import Any, Dict, List

import numpy as np
import plotly.graph_objects as go


# ============================================================
# BASIC GEOMETRY HELPERS
# ============================================================

def _cylinder_surface(
    radius: float,
    z_bottom: float,
    z_top: float,
    n_theta: int = 60,
    n_z: int = 20,
):
    theta = np.linspace(0.0, 2.0 * math.pi, n_theta)
    z = np.linspace(z_bottom, z_top, n_z)

    tt, zz = np.meshgrid(theta, z)

    x = radius * np.cos(tt)
    y = radius * np.sin(tt)

    return x, y, zz


def _disk_surface(
    radius: float,
    z: float,
    n_theta: int = 60,
    n_r: int = 12,
):
    theta = np.linspace(0.0, 2.0 * math.pi, n_theta)
    r = np.linspace(0.0, radius, n_r)

    tt, rr = np.meshgrid(theta, r)

    x = rr * np.cos(tt)
    y = rr * np.sin(tt)
    zz = np.full_like(x, z)

    return x, y, zz


def _ellipsoidal_bottom(
    radius: float,
    depth: float,
    z_center: float,
    n_theta: int = 60,
    n_phi: int = 20,
):
    """
    Lower half of a 2:1-type ellipsoidal head approximation.
    """
    theta = np.linspace(0.0, 2.0 * math.pi, n_theta)
    phi = np.linspace(math.pi / 2.0, math.pi, n_phi)

    tt, pp = np.meshgrid(theta, phi)

    x = radius * np.sin(pp) * np.cos(tt)
    y = radius * np.sin(pp) * np.sin(tt)
    z = z_center + depth * np.cos(pp)

    return x, y, z


def _ellipsoidal_top(
    radius: float,
    depth: float,
    z_center: float,
    n_theta: int = 60,
    n_phi: int = 20,
):
    """
    Upper ellipsoidal head approximation.
    """
    theta = np.linspace(0.0, 2.0 * math.pi, n_theta)
    phi = np.linspace(0.0, math.pi / 2.0, n_phi)

    tt, pp = np.meshgrid(theta, phi)

    x = radius * np.sin(pp) * np.cos(tt)
    y = radius * np.sin(pp) * np.sin(tt)
    z = z_center + depth * np.cos(pp)

    return x, y, z


# ============================================================
# VESSEL
# ============================================================

def _add_vessel(
    fig: go.Figure,
    diameter: float,
    straight_height: float,
):
    radius = diameter / 2.0

    # --------------------------------------------------------
    # Main shell
    # --------------------------------------------------------

    x, y, z = _cylinder_surface(
        radius,
        0.0,
        straight_height,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.22,
            showscale=False,
            hoverinfo="skip",
            name="Reactor shell",
        )
    )

    # --------------------------------------------------------
    # Bottom head
    # --------------------------------------------------------

    bottom_depth = 0.25 * diameter

    xb, yb, zb = _ellipsoidal_bottom(
        radius,
        bottom_depth,
        0.0,
    )

    fig.add_trace(
        go.Surface(
            x=xb,
            y=yb,
            z=zb,
            opacity=0.24,
            showscale=False,
            hoverinfo="skip",
            name="Bottom head",
        )
    )

    # --------------------------------------------------------
    # Top head
    # --------------------------------------------------------

    top_depth = 0.25 * diameter

    xt, yt, zt = _ellipsoidal_top(
        radius,
        top_depth,
        straight_height,
    )

    fig.add_trace(
        go.Surface(
            x=xt,
            y=yt,
            z=zt,
            opacity=0.24,
            showscale=False,
            hoverinfo="skip",
            name="Top head",
        )
    )

    # --------------------------------------------------------
    # Bottom ring
    # --------------------------------------------------------

    theta = np.linspace(0, 2 * math.pi, 100)

    fig.add_trace(
        go.Scatter3d(
            x=radius * np.cos(theta),
            y=radius * np.sin(theta),
            z=np.zeros_like(theta),
            mode="lines",
            line=dict(width=4),
            name="Bottom tangent line",
            hoverinfo="skip",
        )
    )

    # --------------------------------------------------------
    # Top ring
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter3d(
            x=radius * np.cos(theta),
            y=radius * np.sin(theta),
            z=np.full_like(theta, straight_height),
            mode="lines",
            line=dict(width=4),
            name="Top tangent line",
            hoverinfo="skip",
        )
    )


# ============================================================
# LIQUID
# ============================================================

def _add_liquid(
    fig: go.Figure,
    diameter: float,
    liquid_height: float,
    straight_height: float,
):
    radius = diameter / 2.0

    liquid_height = max(
        0.05,
        min(float(liquid_height), float(straight_height)),
    )

    # Slightly smaller than vessel ID so liquid appears inside shell.
    liquid_radius = radius * 0.965

    # --------------------------------------------------------
    # Liquid body
    # --------------------------------------------------------

    x, y, z = _cylinder_surface(
        liquid_radius,
        0.03,
        liquid_height,
        n_theta=70,
        n_z=25,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.32,
            showscale=False,
            hoverinfo="skip",
            name="Liquid",
        )
    )

    # --------------------------------------------------------
    # Liquid surface
    # --------------------------------------------------------

    xs, ys, zs = _disk_surface(
        liquid_radius,
        liquid_height,
        n_theta=80,
        n_r=20,
    )

    fig.add_trace(
        go.Surface(
            x=xs,
            y=ys,
            z=zs,
            opacity=0.48,
            showscale=False,
            hoverinfo="skip",
            name="Liquid surface",
        )
    )

    # --------------------------------------------------------
    # Liquid level ring
    # --------------------------------------------------------

    theta = np.linspace(0, 2 * math.pi, 120)

    fig.add_trace(
        go.Scatter3d(
            x=liquid_radius * np.cos(theta),
            y=liquid_radius * np.sin(theta),
            z=np.full_like(theta, liquid_height),
            mode="lines",
            line=dict(width=5),
            name="Liquid level",
            hoverinfo="skip",
        )
    )


# ============================================================
# BAFFLES
# ============================================================

def _add_baffles(
    fig: go.Figure,
    diameter: float,
    straight_height: float,
    number_baffles: int,
):
    if number_baffles <= 0:
        return

    radius = diameter / 2.0
    baffle_width = max(diameter * 0.045, 0.025)
    baffle_thickness = max(diameter * 0.012, 0.008)

    z0 = straight_height * 0.08
    z1 = straight_height * 0.92

    for i in range(number_baffles):

        angle = 2.0 * math.pi * i / number_baffles

        # Radial position.
        r = radius - baffle_width / 2.0

        x0 = r * math.cos(angle)
        y0 = r * math.sin(angle)

        # Tangential vector.
        tx = -math.sin(angle)
        ty = math.cos(angle)

        half_width = baffle_width / 2.0

        x1 = x0 - tx * half_width
        y1 = y0 - ty * half_width

        x2 = x0 + tx * half_width
        y2 = y0 + ty * half_width

        # Small radial thickness.
        nx = math.cos(angle)
        ny = math.sin(angle)

        vertices = []

        for z in [z0, z1]:
            vertices.extend(
                [
                    [x1, y1, z],
                    [x2, y2, z],
                    [x2 + nx * baffle_thickness, y2 + ny * baffle_thickness, z],
                    [x1 + nx * baffle_thickness, y1 + ny * baffle_thickness, z],
                ]
            )

        vx = [v[0] for v in vertices]
        vy = [v[1] for v in vertices]
        vz = [v[2] for v in vertices]

        faces = [
            (0, 1, 2),
            (0, 2, 3),
            (4, 6, 5),
            (4, 7, 6),
            (0, 4, 5),
            (0, 5, 1),
            (1, 5, 6),
            (1, 6, 2),
            (2, 6, 7),
            (2, 7, 3),
            (3, 7, 4),
            (3, 4, 0),
        ]

        i_face = [f[0] for f in faces]
        j_face = [f[1] for f in faces]
        k_face = [f[2] for f in faces]

        fig.add_trace(
            go.Mesh3d(
                x=vx,
                y=vy,
                z=vz,
                i=i_face,
                j=j_face,
                k=k_face,
                opacity=0.75,
                name=f"Baffle {i + 1}",
                hoverinfo="skip",
            )
        )


# ============================================================
# SHAFT
# ============================================================

def _add_shaft(
    fig: go.Figure,
    diameter: float,
    straight_height: float,
):
    radius = max(diameter * 0.025, 0.015)

    z = np.linspace(
        -0.05 * diameter,
        straight_height + 0.20 * diameter,
        100,
    )

    fig.add_trace(
        go.Scatter3d(
            x=np.full_like(z, 0.0),
            y=np.full_like(z, 0.0),
            z=z,
            mode="lines",
            line=dict(width=9),
            name="Agitator shaft",
            hoverinfo="skip",
        )
    )


# ============================================================
# IMPELLER
# ============================================================

def _add_impeller(
    fig: go.Figure,
    z_level: float,
    diameter: float,
    agitator: str,
    stage_number: int,
):
    r = diameter / 2.0

    agitator_lower = agitator.lower()

    # --------------------------------------------------------
    # Determine visual style
    # --------------------------------------------------------

    if "anchor" in agitator_lower:
        mode = "anchor"

    elif "ribbon" in agitator_lower:
        mode = "ribbon"

    elif "rushton" in agitator_lower:
        mode = "rushton"

    elif "pitched" in agitator_lower:
        mode = "pitched"

    elif "hydrofoil" in agitator_lower:
        mode = "hydrofoil"

    elif "marine" in agitator_lower:
        mode = "marine"

    else:
        mode = "generic"

    # --------------------------------------------------------
    # Anchor
    # --------------------------------------------------------

    if mode == "anchor":

        theta = np.linspace(0, 2 * math.pi, 100)

        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = np.full_like(theta, z_level)

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(width=8),
                name=f"Stage {stage_number} — {agitator}",
                hovertemplate=(
                    f"Stage {stage_number}<br>"
                    f"{agitator}<br>"
                    f"Diameter: {diameter:.3f} m"
                    "<extra></extra>"
                ),
            )
        )

        # Vertical anchor arms.
        for ang in np.linspace(0, 2 * math.pi, 9)[:-1]:

            x1 = r * math.cos(ang)
            y1 = r * math.sin(ang)

            fig.add_trace(
                go.Scatter3d(
                    x=[x1, x1],
                    y=[y1, y1],
                    z=[
                        z_level - 0.12 * diameter,
                        z_level + 0.12 * diameter,
                    ],
                    mode="lines",
                    line=dict(width=5),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        return

    # --------------------------------------------------------
    # Helical ribbon
    # --------------------------------------------------------

    if mode == "ribbon":

        theta = np.linspace(
            0,
            2.8 * math.pi,
            160,
        )

        x = r * np.cos(theta)
        y = r * np.sin(theta)

        z = (
            z_level
            + 0.18 * diameter
            * (theta / theta.max() - 0.5)
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(width=7),
                name=f"Stage {stage_number} — {agitator}",
                hovertemplate=(
                    f"Stage {stage_number}<br>"
                    f"{agitator}<br>"
                    f"Diameter: {diameter:.3f} m"
                    "<extra></extra>"
                ),
            )
        )

        return

    # --------------------------------------------------------
    # Rushton / pitched / hydrofoil / marine
    # --------------------------------------------------------

    n_blades = 6

    for i in range(n_blades):

        ang = 2 * math.pi * i / n_blades

        hub_r = 0.10 * r

        x0 = hub_r * math.cos(ang)
        y0 = hub_r * math.sin(ang)

        # Slight blade sweep.
        sweep = 0.12 if mode in ["pitched", "hydrofoil", "marine"] else 0.0

        ang2 = ang + sweep

        x1 = r * math.cos(ang2)
        y1 = r * math.sin(ang2)

        # Pitched blade has vertical offset.
        if mode in ["pitched", "hydrofoil", "marine"]:
            z0 = z_level - 0.025 * diameter
            z1 = z_level + 0.025 * diameter
        else:
            z0 = z_level
            z1 = z_level

        fig.add_trace(
            go.Scatter3d(
                x=[x0, x1],
                y=[y0, y1],
                z=[z0, z1],
                mode="lines",
                line=dict(width=9),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Hub.
    fig.add_trace(
        go.Scatter3d(
            x=[0],
            y=[0],
            z=[z_level],
            mode="markers",
            marker=dict(size=8),
            name=f"Stage {stage_number} — {agitator}",
            hovertemplate=(
                f"Stage {stage_number}<br>"
                f"{agitator}<br>"
                f"Diameter: {diameter:.3f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# FLOW VISUALIZATION
# ============================================================

def _add_flow_paths(
    fig: go.Figure,
    diameter: float,
    liquid_height: float,
    results: List[Dict[str, Any]],
):
    """
    Adds conceptual flow-path lines.

    These are visualization aids only.
    They are NOT CFD-calculated streamlines.
    """

    if liquid_height <= 0:
        return

    radius = diameter / 2.0

    for idx, result in enumerate(results):

        z0 = float(
            result.get(
                "elevation_m",
                liquid_height * (0.30 + 0.25 * idx),
            )
        )

        impeller_d = float(
            result.get(
                "impeller_diameter_m",
                diameter * 0.33,
            )
        )

        flow_type = str(
            result.get(
                "flow",
                "mixed",
            )
        ).lower()

        if "radial" in flow_type:

            theta = np.linspace(
                0,
                2 * math.pi,
                80,
            )

            rr = np.linspace(
                impeller_d * 0.45,
                radius * 0.88,
                80,
            )

            x = rr * np.cos(theta)
            y = rr * np.sin(theta)
            z = np.full_like(theta, z0)

        else:

            theta = np.linspace(
                0,
                2 * math.pi,
                100,
            )

            rr = impeller_d * 0.55

            x = rr * np.cos(theta)
            y = rr * np.sin(theta)

            z = (
                z0
                + 0.20 * liquid_height
                * np.sin(theta * 0.5)
            )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=2,
                    dash="dot",
                ),
                opacity=0.45,
                name=f"Conceptual flow path {idx + 1}",
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# MAIN FIGURE
# ============================================================

def create_reactor_figure(
    tank_diameter_m: float,
    straight_height_m: float,
    liquid_height_m: float,
    results: List[Dict[str, Any]],
    number_baffles: int = 4,
):
    """
    Create the main interactive 3D reactor visualization.

    Parameters
    ----------
    tank_diameter_m:
        Reactor internal diameter [m].

    straight_height_m:
        Straight-side height [m].

    liquid_height_m:
        Liquid height [m].

    results:
        Stage-by-stage agitator results from calculations.engine.

    number_baffles:
        Number of vessel baffles.

    Returns
    -------
    plotly.graph_objects.Figure
    """

    D = max(float(tank_diameter_m), 0.10)
    H = max(float(straight_height_m), 0.10)
    liquid_H = max(float(liquid_height_m), 0.0)

    if results is None:
        results = []

    fig = go.Figure()

    # --------------------------------------------------------
    # Reactor
    # --------------------------------------------------------

    _add_vessel(
        fig,
        D,
        H,
    )

    # --------------------------------------------------------
    # Liquid
    # --------------------------------------------------------

    _add_liquid(
        fig,
        D,
        liquid_H,
        H,
    )

    # --------------------------------------------------------
    # Baffles
    # --------------------------------------------------------

    _add_baffles(
        fig,
        D,
        H,
        int(number_baffles),
    )

    # --------------------------------------------------------
    # Shaft
    # --------------------------------------------------------

    _add_shaft(
        fig,
        D,
        H,
    )

    # --------------------------------------------------------
    # Independent agitator stages
    # --------------------------------------------------------

    for idx, result in enumerate(results):

        agitator = str(
            result.get(
                "agitator",
                f"Stage {idx + 1}",
            )
        )

        impeller_diameter = float(
            result.get(
                "impeller_diameter_m",
                D * 0.33,
            )
        )

        elevation = result.get(
            "elevation_m",
            None,
        )

        if elevation is None:
            if len(results) == 1:
                elevation = H * 0.50
            else:
                elevation = H * (
                    0.25
                    + 0.45 * idx / max(len(results) - 1, 1)
                )

        elevation = max(
            0.05,
            min(
                float(elevation),
                max(liquid_H - 0.05, 0.06),
            ),
        )

        _add_impeller(
            fig,
            elevation,
            impeller_diameter,
            agitator,
            idx + 1,
        )

    # --------------------------------------------------------
    # Conceptual flow paths
    # --------------------------------------------------------

    _add_flow_paths(
        fig,
        D,
        liquid_H,
        results,
    )

    # --------------------------------------------------------
    # Camera / layout
    # --------------------------------------------------------

    total_height = H * 1.55 + D * 0.5

    fig.update_layout(
        title=dict(
            text="3D Reactor & Mixing Visualization",
            x=0.02,
            xanchor="left",
        ),
        scene=dict(
            xaxis=dict(
                title="X (m)",
                showbackground=True,
                backgroundcolor="rgba(245,247,251,0.85)",
                gridcolor="rgba(120,130,150,0.25)",
            ),
            yaxis=dict(
                title="Y (m)",
                showbackground=True,
                backgroundcolor="rgba(245,247,251,0.85)",
                gridcolor="rgba(120,130,150,0.25)",
            ),
            zaxis=dict(
                title="Height (m)",
                showbackground=True,
                backgroundcolor="rgba(245,247,251,0.85)",
                gridcolor="rgba(120,130,150,0.25)",
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=1,
                y=1,
                z=max(total_height / D, 1.5),
            ),
            camera=dict(
                eye=dict(
                    x=1.65,
                    y=1.65,
                    z=1.15,
                )
            ),
        ),
        height=720,
        margin=dict(
            l=0,
            r=0,
            t=55,
            b=0,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="left",
            x=0.01,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def create_reactor_animation(
    D,
    straight_height,
    bottom_type=None,
    top_type=None,
    liquid_height=1.0,
    agitator="Pitched Blade Turbine",
    impeller_diameter=None,
    number_impellers=1,
    rpm=100,
    number_baffles=4,
    vortex_depth=0.0,
    frames_count=36,
):
    """
    Backward-compatible wrapper for the previous application.

    The current application uses create_reactor_figure().
    """

    D = float(D)
    straight_height = float(straight_height)

    if impeller_diameter is None:
        impeller_diameter = D * 0.33

    results = []

    for i in range(int(number_impellers)):

        if number_impellers <= 1:
            elevation = straight_height * 0.50
        else:
            elevation = straight_height * (
                0.25
                + 0.50 * i / max(number_impellers - 1, 1)
            )

        results.append(
            {
                "agitator": agitator,
                "impeller_diameter_m": impeller_diameter,
                "rpm": rpm,
                "elevation_m": elevation,
                "flow": "mixed",
            }
        )

    return create_reactor_figure(
        D,
        straight_height,
        liquid_height,
        results,
        number_baffles,
    )
