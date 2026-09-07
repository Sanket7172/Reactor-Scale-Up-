import math
import numpy as np
import plotly.graph_objects as go

from libraries.reactor_geometry import (
    profile,
    radius_at_height,
)


# =========================================================
# IMPeller TRACE
# =========================================================

def _impeller_trace(
    D,
    z,
    agitator,
    blades,
):

    radius = D / 2.0

    x = []
    y = []
    zz = []

    # -----------------------------------------------------
    # Rushton
    # -----------------------------------------------------

    if agitator == "Rushton Turbine":

        disk_r = radius * 0.75

        theta = np.linspace(
            0,
            2 * math.pi,
            60
        )

        for angle in theta:

            x.append(
                disk_r *
                math.cos(angle)
            )

            y.append(
                disk_r *
                math.sin(angle)
            )

            zz.append(z)

        x += [None]
        y += [None]
        zz += [None]

        for i in range(blades):

            angle = (
                2 *
                math.pi *
                i /
                blades
            )

            x += [
                radius * 0.2 *
                math.cos(angle),

                radius * 0.95 *
                math.cos(angle),

                None
            ]

            y += [
                radius * 0.2 *
                math.sin(angle),

                radius * 0.95 *
                math.sin(angle),

                None
            ]

            zz += [
                z,
                z,
                None
            ]

    # -----------------------------------------------------
    # Generic radial/axial blade representation
    # -----------------------------------------------------

    else:

        for i in range(blades):

            angle = (
                2 *
                math.pi *
                i /
                blades
            )

            x += [
                radius * 0.12 *
                math.cos(angle),

                radius *
                math.cos(angle),

                None
            ]

            y += [
                radius * 0.12 *
                math.sin(angle),

                radius *
                math.sin(angle),

                None
            ]

            zz += [
                z,
                z,
                None
            ]

    return x, y, zz


# =========================================================
# CREATE 3D REACTOR
# =========================================================

def create_reactor_animation(
    D,
    straight_height,
    bottom_type,
    top_type,
    liquid_height,
    agitator,
    impeller_diameter,
    number_impellers=1,
    rpm=120,
    number_baffles=4,
    vortex_depth=0.0,
    frames_count=36,
):

    z_profile, r_profile = profile(
        D,
        straight_height,
        bottom_type,
        top_type,
        n_points=240,
    )

    theta = np.linspace(
        0,
        2 * math.pi,
        80
    )

    Z, TH = np.meshgrid(
        z_profile,
        theta
    )

    R = np.tile(
        r_profile,
        (len(theta), 1)
    )

    X = (
        R *
        np.cos(TH)
    )

    Y = (
        R *
        np.sin(TH)
    )

    fig = go.Figure()

    # =====================================================
    # VESSEL
    # =====================================================

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.18,
            showscale=False,
            name="Vessel",
            hovertemplate=(
                "Reactor vessel"
                "<extra></extra>"
            ),
        )
    )

    # =====================================================
    # LIQUID
    # =====================================================

    liquid_z = max(
        0.0,
        min(
            float(liquid_height),
            float(z_profile[-1])
        )
    )

    liquid_radius = radius_at_height(
        liquid_z,
        D,
        straight_height,
        bottom_type,
        top_type,
    )

    liquid_theta = np.linspace(
        0,
        2 * math.pi,
        80
    )

    liquid_x = (
        liquid_radius *
        np.cos(liquid_theta)
    )

    liquid_y = (
        liquid_radius *
        np.sin(liquid_theta)
    )

    fig.add_trace(
        go.Scatter3d(
            x=liquid_x,
            y=liquid_y,
            z=np.full_like(
                liquid_x,
                liquid_z
            ),
            mode="lines",
            name="Liquid Level",
            line=dict(width=5),
        )
    )

    # =====================================================
    # LIQUID BODY
    # =====================================================

    mask = (
        z_profile <= liquid_z
    )

    zl = z_profile[mask]
    rl = r_profile[mask]

    if len(zl) >= 2:

        ZL, THL = np.meshgrid(
            zl,
            theta
        )

        RL = np.tile(
            rl,
            (len(theta), 1)
        )

        XL = (
            RL *
            np.cos(THL)
        )

        YL = (
            RL *
            np.sin(THL)
        )

        fig.add_trace(
            go.Surface(
                x=XL,
                y=YL,
                z=ZL,
                opacity=0.08,
                showscale=False,
                name="Liquid",
                hoverinfo="skip",
            )
        )

    # =====================================================
    # SHAFT
    # =====================================================

    shaft_z = np.linspace(
        0,
        z_profile[-1],
        100
    )

    fig.add_trace(
        go.Scatter3d(
            x=np.zeros_like(
                shaft_z
            ),
            y=np.zeros_like(
                shaft_z
            ),
            z=shaft_z,
            mode="lines",
            name="Shaft",
            line=dict(width=8),
        )
    )

    # =====================================================
    # BAFFLES
    # =====================================================

    if number_baffles > 0:

        baffle_r = (
            D / 2.0 -
            D * 0.04
        )

        for i in range(
            int(number_baffles)
        ):

            angle = (
                2 *
                math.pi *
                i /
                number_baffles
            )

            bx = (
                baffle_r *
                math.cos(angle)
            )

            by = (
                baffle_r *
                math.sin(angle)
            )

            fig.add_trace(
                go.Scatter3d(
                    x=[bx, bx],
                    y=[by, by],
                    z=[0, liquid_z],
                    mode="lines",
                    name="Baffle",
                    showlegend=i == 0,
                    line=dict(width=7),
                )
            )

    # =====================================================
    # IMPELLERS
    # =====================================================

    blade_count = {
        "Rushton Turbine": 6,
        "Pitched Blade Turbine": 4,
        "Hydrofoil": 3,
        "Marine Propeller": 3,
        "Anchor": 2,
        "Helical Ribbon": 1,
        "RCI": 2,
    }.get(
        agitator,
        4
    )

    nimp = max(
        1,
        int(number_impellers)
    )

    clearance = max(
        0.0,
        float(vortex_depth)
    )

    if nimp == 1:

        positions = [
            min(
                liquid_z * 0.25,
                liquid_z
            )
        ]

    else:

        positions = np.linspace(
            liquid_z * 0.20,
            liquid_z * 0.80,
            nimp
        )

    for i, z_imp in enumerate(
        positions
    ):

        ix, iy, iz = _impeller_trace(
            impeller_diameter,
            z_imp,
            agitator,
            blade_count,
        )

        fig.add_trace(
            go.Scatter3d(
                x=ix,
                y=iy,
                z=iz,
                mode="lines",
                name=f"Impeller {i + 1}",
                line=dict(width=6),
            )
        )

    # =====================================================
    # MIXING TRACERS
    # =====================================================

    rng = np.random.default_rng(
        42
    )

    n_particles = 120

    particle_r = (
        np.sqrt(
            rng.random(
                n_particles
            )
        ) *
        max(
            liquid_radius * 0.80,
            D * 0.03
        )
    )

    particle_angle = (
        rng.random(
            n_particles
        ) *
        2 *
        math.pi
    )

    particle_z = (
        rng.random(
            n_particles
        ) *
        liquid_z
    )

    px = (
        particle_r *
        np.cos(particle_angle)
    )

    py = (
        particle_r *
        np.sin(particle_angle)
    )

    particle_trace = len(
        fig.data
    )

    fig.add_trace(
        go.Scatter3d(
            x=px,
            y=py,
            z=particle_z,
            mode="markers",
            name="Mixing Tracers",
            marker=dict(
                size=3,
                opacity=0.55,
            ),
        )
    )

    # =====================================================
    # ANIMATION
    # =====================================================

    frames = []

    for i in range(
        max(1, int(frames_count))
    ):

        rotation = (
            2 *
            math.pi *
            i /
            max(1, frames_count)
        )

        angle = (
            particle_angle +
            rotation
        )

        fx = (
            particle_r *
            np.cos(angle)
        )

        fy = (
            particle_r *
            np.sin(angle)
        )

        fz = (
            particle_z +
            0.03 *
            D *
            np.sin(
                particle_angle * 2 +
                rotation
            )
        )

        fz = np.clip(
            fz,
            0,
            liquid_z
        )

        frames.append(
            go.Frame(
                name=str(i),
                data=[
                    go.Scatter3d(
                        x=fx,
                        y=fy,
                        z=fz,
                        mode="markers",
                        marker=dict(
                            size=3,
                            opacity=0.55,
                        ),
                    )
                ],
                traces=[
                    particle_trace
                ],
            )
        )

    fig.frames = frames

    # =====================================================
    # CONTROLS
    # =====================================================

    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0.02,
                "y": 0.02,
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": 100,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 0,
                                },
                            },
                        ],
                    },
                    {
                        "label": "⏸ Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {
                                    "duration": 0,
                                },
                            },
                        ],
                    },
                ],
            }
        ]
    )

    # =====================================================
    # LAYOUT
    # =====================================================

    total_height = z_profile[-1]

    fig.update_layout(

        title=(
            f"3D Reactor | "
            f"{agitator} | "
            f"{rpm:.0f} RPM"
        ),

        scene=dict(

            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Height (m)",

            aspectmode="manual",

            aspectratio=dict(
                x=1,
                y=1,
                z=max(
                    1.2,
                    total_height /
                    max(D, 0.1)
                ),
            ),

            camera=dict(
                eye=dict(
                    x=1.7,
                    y=1.7,
                    z=1.2,
                )
            ),
        ),

        height=680,

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
            x=0,
        ),
    )

    return fig


def create_reactor_3d(**kwargs):

    return create_reactor_animation(
        **kwargs
    )
