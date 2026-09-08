"""
Professional interactive reactor visualization.

The visualization represents:
- reactor shell
- top/bottom heads
- liquid volume
- baffles
- shaft
- independent agitators
- conceptual mixing paths

It is NOT a CFD solver.
"""


import math

import numpy as np
import plotly.graph_objects as go


def _cylinder(
    radius,
    z0,
    z1,
    ntheta=70,
):
    theta = np.linspace(
        0,
        2 * math.pi,
        ntheta,
    )

    z = np.linspace(
        z0,
        z1,
        20,
    )

    tt, zz = np.meshgrid(
        theta,
        z,
    )

    x = radius * np.cos(tt)
    y = radius * np.sin(tt)

    return x, y, zz


def _disk(
    radius,
    z,
    ntheta=70,
):
    theta = np.linspace(
        0,
        2 * math.pi,
        ntheta,
    )

    r = np.linspace(
        0,
        radius,
        20,
    )

    tt, rr = np.meshgrid(
        theta,
        r,
    )

    x = rr * np.cos(tt)
    y = rr * np.sin(tt)
    zz = np.full_like(
        x,
        z,
    )

    return x, y, zz


def _add_reactor_shell(
    fig,
    D,
    H,
):
    R = D / 2.0

    x, y, z = _cylinder(
        R,
        0,
        H,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.16,
            showscale=False,
            hoverinfo="skip",
            name="Reactor shell",
        )
    )

    theta = np.linspace(
        0,
        2 * math.pi,
        100,
    )

    fig.add_trace(
        go.Scatter3d(
            x=R * np.cos(theta),
            y=R * np.sin(theta),
            z=np.zeros_like(theta),
            mode="lines",
            line=dict(width=5),
            hoverinfo="skip",
            showlegend=False,
        )
    )

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
            hoverinfo="skip",
            showlegend=False,
        )
    )


def _add_liquid(
    fig,
    D,
    liquid_height,
    H,
):
    R = D / 2.0

    liquid_height = min(
        max(
            float(liquid_height),
            0.05,
        ),
        H,
    )

    liquid_R = R * 0.94

    x, y, z = _cylinder(
        liquid_R,
        0.02,
        liquid_height,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.28,
            showscale=False,
            hoverinfo="skip",
            name="Liquid",
        )
    )

    x, y, z = _disk(
        liquid_R,
        liquid_height,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.42,
            showscale=False,
            hoverinfo="skip",
            name="Liquid surface",
        )
    )


def _add_baffles(
    fig,
    D,
    H,
    number_baffles,
):
    if number_baffles <= 0:
        return

    R = D / 2.0

    width = max(
        D * 0.055,
        0.025,
    )

    thickness = max(
        D * 0.012,
        0.006,
    )

    z0 = H * 0.08
    z1 = H * 0.92

    for i in range(
        int(number_baffles)
    ):

        angle = (
            2
            * math.pi
            * i
            / number_baffles
        )

        radial_x = math.cos(angle)
        radial_y = math.sin(angle)

        tangent_x = -math.sin(angle)
        tangent_y = math.cos(angle)

        r = (
            R
            - width * 0.45
        )

        cx = r * radial_x
        cy = r * radial_y

        w = width / 2.0

        x1 = cx - tangent_x * w
        y1 = cy - tangent_y * w

        x2 = cx + tangent_x * w
        y2 = cy + tangent_y * w

        vertices = [
            (x1, y1, z0),
            (x2, y2, z0),
            (
                x2 + radial_x * thickness,
                y2 + radial_y * thickness,
                z0,
            ),
            (
                x1 + radial_x * thickness,
                y1 + radial_y * thickness,
                z0,
            ),
            (x1, y1, z1),
            (x2, y2, z1),
            (
                x2 + radial_x * thickness,
                y2 + radial_y * thickness,
                z1,
            ),
            (
                x1 + radial_x * thickness,
                y1 + radial_y * thickness,
                z1,
            ),
        ]

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

        fig.add_trace(
            go.Mesh3d(
                x=vx,
                y=vy,
                z=vz,
                i=[f[0] for f in faces],
                j=[f[1] for f in faces],
                k=[f[2] for f in faces],
                opacity=0.72,
                name=f"Baffle {i + 1}",
                hoverinfo="skip",
                showlegend=False,
            )
        )


def _add_shaft(
    fig,
    D,
    H,
):
    z = np.linspace(
        -0.1 * D,
        H + 0.2 * D,
        100,
    )

    fig.add_trace(
        go.Scatter3d(
            x=np.zeros_like(z),
            y=np.zeros_like(z),
            z=z,
            mode="lines",
            line=dict(width=8),
            name="Agitator shaft",
            hoverinfo="skip",
        )
    )


def _add_anchor(
    fig,
    z,
    D,
    agitator,
):
    R = D / 2.0

    theta = np.linspace(
        0,
        2 * math.pi,
        100,
    )

    x = R * 0.42 * np.cos(theta)
    y = R * 0.42 * np.sin(theta)

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=np.full_like(
                theta,
                z,
            ),
            mode="lines",
            line=dict(width=8),
            name=agitator,
            hovertemplate=(
                f"{agitator}<br>"
                f"Diameter = {D:.3f} m"
                "<extra></extra>"
            ),
        )
    )


def _add_ribbon(
    fig,
    z,
    D,
    agitator,
):
    R = D / 2.0

    theta = np.linspace(
        0,
        4 * math.pi,
        220,
    )

    x = R * 0.43 * np.cos(theta)
    y = R * 0.43 * np.sin(theta)

    zz = (
        z
        + 0.18 * D
        * (
            theta / theta.max()
            - 0.5
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=zz,
            mode="lines",
            line=dict(width=7),
            name=agitator,
            hovertemplate=(
                f"{agitator}<br>"
                f"Diameter = {D:.3f} m"
                "<extra></extra>"
            ),
        )
    )


def _add_standard_impeller(
    fig,
    z,
    D,
    agitator,
):
    R = D / 2.0

    lower = agitator.lower()

    if "rushton" in lower:
        blades = 6
    elif "marine" in lower:
        blades = 3
    else:
        blades = 4

    for i in range(blades):

        angle = (
            2
            * math.pi
            * i
            / blades
        )

        x0 = (
            0.08
            * R
            * math.cos(angle)
        )

        y0 = (
            0.08
            * R
            * math.sin(angle)
        )

        x1 = (
            0.95
            * R
            * math.cos(angle)
        )

        y1 = (
            0.95
            * R
            * math.sin(angle)
        )

        if (
            "pitched" in lower
            or "hydrofoil" in lower
            or "marine" in lower
        ):
            z0 = z - 0.025 * D
            z1 = z + 0.025 * D
        else:
            z0 = z
            z1 = z

        fig.add_trace(
            go.Scatter3d(
                x=[x0, x1],
                y=[y0, y1],
                z=[z0, z1],
                mode="lines",
                line=dict(width=9),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter3d(
            x=[0],
            y=[0],
            z=[z],
            mode="markers",
            marker=dict(size=9),
            name=agitator,
            hovertemplate=(
                f"{agitator}<br>"
                f"Diameter = {D:.3f} m"
                "<extra></extra>"
            ),
        )
    )


def _add_impeller(
    fig,
    z,
    D,
    agitator,
):
    name = agitator.lower()

    if "anchor" in name:

        _add_anchor(
            fig,
            z,
            D,
            agitator,
        )

    elif "ribbon" in name:

        _add_ribbon(
            fig,
            z,
            D,
            agitator,
        )

    else:

        _add_standard_impeller(
            fig,
            z,
            D,
            agitator,
        )


def _add_flow_paths(
    fig,
    D,
    liquid_height,
    results,
):
    if not results:
        return

    R = D / 2.0

    for i, result in enumerate(results):

        z = result.get(
            "elevation_m"
        )

        if z is None:

            z = (
                liquid_height
                * (
                    0.30
                    + 0.30 * i
                )
            )

        impeller_D = result.get(
            "impeller_diameter_m",
            D * 0.33,
        )

        flow = str(
            result.get(
                "flow",
                "Mixed",
            )
        ).lower()

        theta = np.linspace(
            0,
            2 * math.pi,
            100,
        )

        if "radial" in flow:

            rr = np.linspace(
                impeller_D * 0.45,
                R * 0.85,
                100,
            )

            x = (
                rr
                * np.cos(theta)
            )

            y = (
                rr
                * np.sin(theta)
            )

            zz = np.full_like(
                theta,
                z,
            )

        else:

            rr = impeller_D * 0.55

            x = (
                rr
                * np.cos(theta)
            )

            y = (
                rr
                * np.sin(theta)
            )

            zz = (
                z
                + 0.12
                * liquid_height
                * np.sin(theta)
            )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=zz,
                mode="lines",
                line=dict(
                    width=2,
                    dash="dot",
                ),
                opacity=0.45,
                hoverinfo="skip",
                showlegend=False,
            )
        )


def create_reactor_figure(
    tank_diameter_m,
    straight_height_m,
    liquid_height_m,
    results,
    number_baffles=4,
):
    """
    Main 3D visualization function.
    """

    D = max(
        float(tank_diameter_m),
        0.1,
    )

    H = max(
        float(straight_height_m),
        0.1,
    )

    liquid_height = min(
        max(
            float(liquid_height_m),
            0.05,
        ),
        H,
    )

    results = results or []

    fig = go.Figure()

    _add_reactor_shell(
        fig,
        D,
        H,
    )

    _add_liquid(
        fig,
        D,
        liquid_height,
        H,
    )

    _add_baffles(
        fig,
        D,
        H,
        number_baffles,
    )

    _add_shaft(
        fig,
        D,
        H,
    )

    for i, result in enumerate(results):

        agitator = result.get(
            "agitator",
            f"Stage {i + 1}",
        )

        impeller_D = float(
            result.get(
                "impeller_diameter_m",
                D * 0.33,
            )
        )

        elevation = result.get(
            "elevation_m"
        )

        if elevation is None:

            if len(results) == 1:

                elevation = (
                    liquid_height
                    * 0.50
                )

            else:

                elevation = (
                    liquid_height
                    * (
                        0.25
                        + 0.50
                        * i
                        / max(
                            len(results) - 1,
                            1,
                        )
                    )
                )

        elevation = min(
            max(
                float(elevation),
                0.05,
            ),
            max(
                liquid_height - 0.05,
                0.06,
            ),
        )

        _add_impeller(
            fig,
            elevation,
            impeller_D,
            agitator,
        )

    _add_flow_paths(
        fig,
        D,
        liquid_height,
        results,
    )

    fig.update_layout(
        title=dict(
            text="Reactor Geometry & Mixing Visualization",
            x=0.02,
        ),
        height=720,
        margin=dict(
            l=0,
            r=0,
            t=55,
            b=0,
        ),
        scene=dict(
            xaxis=dict(
                title="X (m)",
                showbackground=True,
            ),
            yaxis=dict(
                title="Y (m)",
                showbackground=True,
            ),
            zaxis=dict(
                title="Height (m)",
                showbackground=True,
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=1,
                y=1,
                z=max(
                    H / D,
                    1.5,
                ),
            ),
            camera=dict(
                eye=dict(
                    x=1.65,
                    y=1.65,
                    z=1.10,
                )
            ),
        ),
        legend=dict(
            orientation="h",
            y=0.01,
            x=0.01,
        ),
    )

    return fig
