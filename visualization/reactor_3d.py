import math
import numpy as np
import plotly.graph_objects as go

from libraries.reactor_geometry import (
    profile,
    radius_at_height,
    head_depth,
)


# =========================================================
# IMPeller geometry
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

        x.extend([
            -disk_r,
            disk_r,
            None,
        ])

        y.extend([
            0,
            0,
            None,
        ])

        zz.extend([
            z,
            z,
            None,
        ])

        for i in range(blades):

            angle = (
                2 *
                math.pi *
                i /
                blades
            )

            x.extend([
                0,
                radius,
                None,
            ])

            y.extend([
                0,
                0,
                None,
            ])

            zz.extend([
                z,
                z,
                None,
            ])

    # -----------------------------------------------------
    # Pitched Blade / Hydrofoil
    # -----------------------------------------------------

    elif agitator in [
        "Pitched Blade Turbine",
        "Hydrofoil",
    ]:

        for i in range(blades):

            angle = (
                2 *
                math.pi *
                i /
                blades
            )

            x1 = (
                radius *
                0.10 *
                math.cos(angle)
            )

            y1 = (
                radius *
                0.10 *
                math.sin(angle)
            )

            x2 = (
                radius *
                math.cos(angle)
            )

            y2 = (
                radius *
                math.sin(angle)
            )

            x.extend([
                x1,
                x2,
                None,
            ])

            y.extend([
                y1,
                y2,
                None,
            ])

            zz.extend([
                z,
                z,
                None,
            ])

    # -----------------------------------------------------
    # Marine Propeller
    # -----------------------------------------------------

    elif agitator == "Marine Propeller":

        for i in range(blades):

            angle = (
                2 *
                math.pi *
                i /
                blades
            )

            x.extend([
                0,
                radius *
                math.cos(angle),
                None,
            ])

            y.extend([
                0,
                radius *
                math.sin(angle),
                None,
            ])

            zz.extend([
                z,
                z,
                None,
            ])

    # -----------------------------------------------------
    # Anchor
    # -----------------------------------------------------

    elif agitator == "Anchor":

        points = 50

        for i in range(points):

            angle = (
                2 *
                math.pi *
                i /
                (points - 1)
            )

            x.append(
                radius *
                0.90 *
                math.cos(angle)
            )

            y.append(
                radius *
                0.90 *
                math.sin(angle)
            )

            zz.append(z)

        x.append(None)
        y.append(None)
        zz.append(None)

        x.extend([
            -radius * 0.90,
            -radius * 0.90,
            None,
        ])

        y.extend([
            0,
            0,
            None,
        ])

        zz.extend([
            z,
            z + D * 0.40,
            None,
        ])

    # -----------------------------------------------------
    # Helical Ribbon
    # -----------------------------------------------------

    elif agitator == "Helical Ribbon":

        points = 120

        for i in range(points):

            angle = (
                4 *
                math.pi *
                i /
                (points - 1)
            )

            x.append(
                radius *
                0.90 *
                math.cos(angle)
            )

            y.append(
                radius *
                0.90 *
                math.sin(angle)
            )

            zz.append(
                z -
                D * 0.35 +
                D * 0.70 *
                i /
                (points - 1)
            )

    # -----------------------------------------------------
    # RCI
    # -----------------------------------------------------

    elif agitator == "RCI":

        for i in range(blades):

            angle = (
                2 *
                math.pi *
                i /
                blades
            )

            x.extend([
                radius * 0.15 *
                math.cos(angle),

                radius *
                math.cos(angle),

                None,
            ])

            y.extend([
                radius * 0.15 *
                math.sin(angle),

                radius *
                math.sin(angle),

                None,
            ])

            zz.extend([
                z,
                z,
                None,
            ])

    return x, y, zz


# =========================================================
# 3D REACTOR
# =========================================================

def create_reactor_animation(
    D,
    straight_height,
    bottom_type,
    top_type,
    liquid_height,
    impeller_diameter,
    impeller_clearance,
    number_impellers,
    agitator,
    number_baffles,
    rpm,
):

    # =====================================================
    # VESSEL PROFILE
    # =====================================================

    z_profile, r_profile = profile(
        D,
        straight_height,
        bottom_type,
        top_type,
        n_points=180,
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

    X = R * np.cos(TH)
    Y = R * np.sin(TH)

    fig = go.Figure()

    # =====================================================
    # VESSEL
    # =====================================================

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.22,
            showscale=False,
            name="Reactor Vessel",
            hovertemplate="Reactor Vessel<extra></extra>",
        )
    )

    # =====================================================
    # LIQUID
    # =====================================================

    liquid_z = min(
        liquid_height,
        z_profile[-1]
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
        )
    )

    # =====================================================
    # LIQUID BODY
    # =====================================================

    liquid_profile_mask = (
        z_profile <= liquid_z
    )

    zl = z_profile[
        liquid_profile_mask
    ]

    rl = r_profile[
        liquid_profile_mask
    ]

    if len(zl) > 2:

        ZL, THL = np.meshgrid(
            zl,
            theta
        )

        RL = np.tile(
            rl,
            (len(theta), 1)
        )

        XL = RL * np.cos(THL)
        YL = RL * np.sin(THL)

        fig.add_trace(
            go.Surface(
                x=XL,
                y=YL,
                z=ZL,
                opacity=0.12,
                showscale=False,
                name="Liquid",
            )
        )

    # =====================================================
    # SHAFT
    # =====================================================

    shaft_radius = D * 0.015

    shaft_z = np.linspace(
        0,
        z_profile[-1],
        80
    )

    fig.add_trace(
        go.Scatter3d(
            x=np.full_like(
                shaft_z,
                0.0
            ),
            y=np.full_like(
                shaft_z,
                0.0
            ),
            z=shaft_z,
            mode="lines",
            name="Shaft",
            line=dict(
                width=8
            ),
        )
    )

    # =====================================================
    # BAFFLES
    # =====================================================

    if number_baffles > 0:

        baffle_width = D * 0.05

        baffle_height = (
            min(
                liquid_z,
                z_profile[-1]
            )
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

            r_baffle = (
                D / 2.0 -
                baffle_width
            )

            x = np.array([
                r_baffle *
                math.cos(angle),
                r_baffle *
                math.cos(angle),
            ])

            y = np.array([
                r_baffle *
                math.sin(angle),
                r_baffle *
                math.sin(angle),
            ])

            z = np.array([
                0,
                baffle_height,
            ])

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    name="Baffle",
                    showlegend=(
                        i == 0
                    ),
                    line=dict(
                        width=7
                    ),
                )
            )

    # =====================================================
    # IMPELLERS
    # =====================================================

    agitator_data = {
        "Rushton Turbine": 6,
        "Pitched Blade Turbine": 4,
        "Hydrofoil": 3,
        "Marine Propeller": 3,
        "Anchor": 2,
        "Helical Ribbon": 1,
        "RCI": 2,
    }

    blades = agitator_data.get(
        agitator,
        4
    )

    impeller_spacing = (
        max(
            liquid_z -
            impeller_clearance,
            0.20 * D
        )
    )

    impeller_z_positions = []

    if number_impellers == 1:

        impeller_z_positions = [
            impeller_clearance
        ]

    else:

        for i in range(
            int(number_impellers)
        ):

            frac = (
                i /
                (number_impellers - 1)
            )

            impeller_z_positions.append(
                impeller_clearance +
                frac *
                max(
                    liquid_z -
                    impeller_clearance -
                    0.15 * D,
                    0.2 * D
                )
            )

    for idx, z_imp in enumerate(
        impeller_z_positions
    ):

        ix, iy, iz = _impeller_trace(
            impeller_diameter,
            z_imp,
            agitator,
            blades,
        )

        fig.add_trace(
            go.Scatter3d(
                x=ix,
                y=iy,
                z=iz,
                mode="lines",
                name=(
                    f"Impeller {idx + 1}"
                ),
                line=dict(
                    width=6
                ),
            )
        )

    # =====================================================
    # MIXING PARTICLES
    # =====================================================

    rng = np.random.default_rng(42)

    n_particles = 90

    particle_z = (
        rng.random(
            n_particles
        ) *
        max(
            liquid_z,
            0.1
        )
    )

    particle_r = (
        np.sqrt(
            rng.random(
                n_particles
            )
        )
        *
        max(
            liquid_radius * 0.80,
            D * 0.05
        )
    )

    particle_angle = (
        rng.random(
            n_particles
        ) *
        2 *
        math.pi
    )

    particle_x = (
        particle_r *
        np.cos(particle_angle)
    )

    particle_y = (
        particle_r *
        np.sin(particle_angle)
    )

    fig.add_trace(
        go.Scatter3d(
            x=particle_x,
            y=particle_y,
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

    for frame_no in range(24):

        rotation = (
            2 *
            math.pi *
            frame_no /
            24.0
        )

        angle_frame = (
            particle_angle +
            rotation
        )

        fx = (
            particle_r *
            np.cos(angle_frame)
        )

        fy = (
            particle_r *
            np.sin(angle_frame)
        )

        frames.append(
            go.Frame(
                name=str(frame_no),
                data=[
                    go.Scatter3d(
                        x=fx,
                        y=fy,
                        z=particle_z,
                        mode="markers",
                        marker=dict(
                            size=3,
                            opacity=0.55,
                        ),
                    )
                ],
                traces=[
                    len(fig.data) - 1
                ],
            )
        )

    fig.frames = frames

    # =====================================================
    # ANIMATION CONTROLS
    # =====================================================

    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0.05,
                "y": 0.05,
                "buttons": [

                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": 80,
                                    "redraw": True,
                                },
                                "fromcurrent": True,
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
                                    "redraw": False,
                                },
                            },
                        ],
                    },
                ],
            }
        ]
    )

    # =====================================================
    # CAMERA / LAYOUT
    # =====================================================

    fig.update_layout(

        title=(
            f"3D Reactor — {agitator} | "
            f"{rpm:.0f} RPM"
        ),

        scene=dict(

            xaxis=dict(
                title="X (m)",
                showbackground=False,
            ),

            yaxis=dict(
                title="Y (m)",
                showbackground=False,
            ),

            zaxis=dict(
                title="Height (m)",
                showbackground=False,
            ),

            aspectmode="manual",

            aspectratio=dict(
                x=1,
                y=1,
                z=max(
                    1.4,
                    z_profile[-1] / D
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

        height=700,

        margin=dict(
            l=0,
            r=0,
            t=60,
            b=0,
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
        ),
    )

    return fig


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

def create_reactor_3d(**kwargs):

    return create_reactor_animation(
        **kwargs
    )
