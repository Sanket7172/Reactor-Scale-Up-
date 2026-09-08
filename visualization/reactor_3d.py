"""
3D engineering visualization.

This is NOT a CFD solver.
It visualizes vessel geometry, impeller train,
baffles and conceptual circulation paths.
"""

import math

import numpy as np
import plotly.graph_objects as go


def _add_cylinder(
    fig,
    radius,
    height,
    name,
):
    theta = np.linspace(
        0,
        2 * np.pi,
        80,
    )

    z = np.linspace(
        0,
        height,
        30,
    )

    T, Z = np.meshgrid(
        theta,
        z,
    )

    X = radius * np.cos(T)
    Y = radius * np.sin(T)

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.14,
            showscale=False,
            name=name,
            hoverinfo="skip",
        )
    )


def _add_baffles(
    fig,
    tank_radius,
    height,
    number_baffles,
):
    if number_baffles <= 0:
        return

    for angle in np.linspace(
        0,
        2 * np.pi,
        number_baffles,
        endpoint=False,
    ):
        rb = tank_radius * 0.94

        width = tank_radius * 0.045

        ux = math.cos(angle)
        uy = math.sin(angle)

        vx = -uy
        vy = ux

        x1 = rb * ux - width * vx
        y1 = rb * uy - width * vy

        x2 = rb * ux + width * vx
        y2 = rb * uy + width * vy

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
                    0,
                    0,
                    height,
                    height,
                ],
                opacity=0.55,
                showscale=False,
                hoverinfo="skip",
                name="Baffle",
                showlegend=False,
            )
        )


def _add_impeller(
    fig,
    stage,
    stage_number,
):
    D = float(
        stage.get(
            "impeller_diameter_m",
            0.4,
        )
    )

    z = float(
        stage.get(
            "elevation_m",
            0.5,
        )
    )

    name = stage.get(
        "agitator",
        "Impeller",
    )

    blades = int(
        stage.get(
            "blades",
            4,
        )
    )

    blades = max(
        min(blades, 12),
        2,
    )

    radius = D / 2.0

    # Shaft
    fig.add_trace(
        go.Scatter3d(
            x=[0, 0],
            y=[0, 0],
            z=[0, z],
            mode="lines",
            line=dict(width=8),
            name="Shaft",
            showlegend=False,
        )
    )

    if (
        "Anchor" in name
        or "Ribbon" in name
    ):
        theta = np.linspace(
            0,
            2 * np.pi,
            100,
        )

        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.full_like(
                    x,
                    z,
                ),
                mode="lines",
                line=dict(width=8),
                name=f"Stage {stage_number}: {name}",
            )
        )

        return

    for blade in range(blades):
        angle = (
            2
            * np.pi
            * blade
            / blades
        )

        x1 = 0.10 * D * math.cos(angle)
        y1 = 0.10 * D * math.sin(angle)

        x2 = radius * math.cos(angle)
        y2 = radius * math.sin(angle)

        fig.add_trace(
            go.Scatter3d(
                x=[x1, x2],
                y=[y1, y2],
                z=[z, z],
                mode="lines",
                line=dict(width=8),
                name=(
                    f"Stage {stage_number}: {name}"
                    if blade == 0
                    else None
                ),
                showlegend=blade == 0,
            )
        )


def _add_flow_path(
    fig,
    tank_radius,
    liquid_height,
    stage_number,
):
    t = np.linspace(
        0,
        2 * np.pi,
        180,
    )

    radius = tank_radius * 0.62

    x = radius * np.cos(t)

    y = radius * np.sin(t)

    z = (
        liquid_height * 0.5
        + liquid_height * 0.25
        * np.sin(
            2 * t
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            line=dict(
                width=4,
                dash="dash",
            ),
            opacity=0.55,
            name=(
                "Conceptual circulation path"
                if stage_number == 1
                else None
            ),
            showlegend=stage_number == 1,
        )
    )


def create_reactor_figure(
    tank_diameter_m,
    straight_height_m,
    liquid_height_m,
    results,
    baffles=4,
    bottom_type="Flat Bottom",
    top_type="Flat Bottom",
):
    D = max(
        float(tank_diameter_m),
        0.1,
    )

    H = max(
        float(straight_height_m),
        0.2,
    )

    R = D / 2.0

    liquid_H = min(
        max(
            float(liquid_height_m),
            0.0,
        ),
        H,
    )

    fig = go.Figure()

    # Vessel shell
    _add_cylinder(
        fig,
        R,
        H,
        "Vessel shell",
    )

    # Bottom ring
    theta = np.linspace(
        0,
        2 * np.pi,
        100,
    )

    fig.add_trace(
        go.Scatter3d(
            x=R * np.cos(theta),
            y=R * np.sin(theta),
            z=np.zeros_like(theta),
            mode="lines",
            line=dict(width=5),
            name="Vessel",
            showlegend=False,
        )
    )

    # Top ring
    fig.add_trace(
        go.Scatter3d(
            x=R * np.cos(theta),
            y=R * np.sin(theta),
            z=np.full_like(
                theta,
                H,
            ),
            mode="lines",
            line=dict(width=5),
            showlegend=False,
        )
    )

    # Liquid surface
    rr = np.linspace(
        0,
        R * 0.98,
        35,
    )

    tt = np.linspace(
        0,
        2 * np.pi,
        80,
    )

    RR, TT = np.meshgrid(
        rr,
        tt,
    )

    X = RR * np.cos(TT)
    Y = RR * np.sin(TT)
    Z = np.full_like(
        X,
        liquid_H,
    )

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.28,
            showscale=False,
            name="Liquid",
        )
    )

    # Baffles
    _add_baffles(
        fig,
        R,
        H,
        int(baffles),
    )

    # Impellers
    for i, stage in enumerate(
        results,
        start=1,
    ):
        _add_impeller(
            fig,
            stage,
            i,
        )

        _add_flow_path(
            fig,
            R,
            liquid_H,
            i,
        )

    fig.update_layout(
        height=720,
        margin=dict(
            l=0,
            r=0,
            t=25,
            b=0,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            aspectmode="manual",
            aspectratio=dict(
                x=1,
                y=1,
                z=max(H / D, 1.2),
            ),
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Height (m)",
            camera=dict(
                eye=dict(
                    x=1.55,
                    y=1.55,
                    z=1.10,
                )
            ),
        ),
        legend=dict(
            orientation="h",
            y=1.02,
        ),
    )

    return fig


def create_reactor_animation(
    D,
    straight_height,
    bottom_type,
    top_type,
    liquid_height,
    agitator,
    impeller_diameter,
    number_impellers,
    rpm,
    number_baffles,
    vortex_depth=0.0,
    frames_count=36,
):
    stage = {
        "agitator": agitator,
        "impeller_diameter_m": impeller_diameter,
        "rpm": rpm,
        "number_impellers": number_impellers,
        "elevation_m": straight_height * 0.35,
        "blades": 4,
    }

    return create_reactor_figure(
        tank_diameter_m=D,
        straight_height_m=straight_height,
        liquid_height_m=liquid_height,
        results=[stage],
        baffles=number_baffles,
        bottom_type=bottom_type,
        top_type=top_type,
    )
