import math
import numpy as np
import plotly.graph_objects as go

from libraries.reactor_geometry import (
    profile,
    radius_at_height,
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
    # Rushton Turbine
    # -----------------------------------------------------

    if agitator == "Rushton Turbine":

        disk_r = radius * 0.75

        # Disk
        disk_points = 50

        for i in range(disk_points):

            angle = (
                2.0 *
                math.pi *
                i /
                (disk_points - 1)
            )

            x.append(
                disk_r *
                math.cos(angle)
            )

            y.append(
                disk_r *
                math.sin(angle)
            )

            zz.append(z)

        x.append(None)
        y.append(None)
        zz.append(None)

        # Blades
        for i in range(blades):

            angle = (
                2.0 *
                math.pi *
                i /
                blades
            )

            x.extend([
                radius * 0.20 * math.cos(angle),
                radius * 0.95 * math.cos(angle),
                None,
            ])

            y.extend([
                radius * 0.20 * math.sin(angle),
                radius * 0.95 * math.sin(angle),
                None,
            ])

            zz.extend([
                z,
                z,
                None,
            ])

    # -----------------------------------------------------
    # Pitched Blade Turbine
    # -----------------------------------------------------

    elif agitator == "Pitched Blade Turbine":

        for i in range(blades):

            angle = (
                2.0 *
                math.pi *
                i /
                blades
            )

            x1 = (
                radius *
                0.12 *
                math.cos(angle)
            )

            y1 = (
                radius *
                0.12 *
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
    # Hydrofoil
    # -----------------------------------------------------

    elif agitator == "Hydrofoil":

        for i in range(blades):

            angle = (
                2.0 *
                math.pi *
                i /
                blades
            )

            # Root
            x.extend([
                radius * 0.10 * math.cos(angle),
                radius * math.cos(angle),
                None,
            ])

            y.extend([
                radius * 0.10 * math.sin(angle),
                radius * math.sin(angle),
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
                2.0 *
                math.pi *
                i /
                blades
            )

            x.extend([
                0.0,
                radius *
                math.cos(angle),
                None,
            ])

            y.extend([
                0.0,
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

        points = 80

        for i in range(points):

            angle = (
                2.0 *
                math.pi *
                i /
                (points - 1)
            )

            x.append(
                radius *
                0.88 *
                math.cos(angle)
            )

            y.append(
                radius *
                0.88 *
                math.sin(angle)
            )

            zz.append(z)

        x.append(None)
        y.append(None)
        zz.append(None)

        # Vertical section
        x.extend([
            -radius * 0.88,
            -radius * 0.88,
            None,
        ])

        y.extend([
            0.0,
            0.0,
            None,
        ])

        zz.extend([
            z,
            z + D * 0.45,
            None,
        ])

    # -----------------------------------------------------
    # Helical Ribbon
    # -----------------------------------------------------

    elif agitator == "Helical Ribbon":

        points = 160

        for i in range(points):

            angle = (
                4.0 *
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
                2.0 *
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
# CREATE REACTOR ANIMATION
# =========================================================

def create_reactor_animation(
    D=None,
    straight_height=None,
    bottom_type="Flat Bottom",
    top_type="Flat Bottom",
    liquid_height=None,
    impeller_diameter=None,
    impeller_clearance=0.10,
    number_impellers=1,
    agitator="Pitched Blade Turbine",
    number_baffles=4,
    rpm=120,
    frames_count=36,

    # -----------------------------------------------------
    # Additional compatibility arguments
    # -----------------------------------------------------

    tank_id_m=None,
    tank_height_m=None,
    liquid_level_m=None,
    impeller_diameter_m=None,
    impeller_clearance_m=None,
    n_impellers=None,
    n_baffles=None,

    **kwargs,
):

    # =====================================================
    # ARGUMENT COMPATIBILITY
    # =====================================================

    if D is None:
        D = tank_id_m

    if straight_height is None:
        straight_height = tank_height_m

    if liquid_height is None:
        liquid_height = liquid_level_m

    if impeller_diameter is None:
        impeller_diameter = impeller_diameter_m

    if impeller_clearance_m is not None:
        impeller_clearance = impeller_clearance_m

    if n_impellers is not None:
        number_impellers = n_impellers

    if n_baffles is not None:
        number_baffles = n_baffles

    # =====================================================
    # SAFETY DEFAULTS
    # =====================================================

    if D is None:
        D = 2.0

    if straight_height is None:
        straight_height = 2.5

    if liquid_height is None:
        liquid_height = straight_height * 0.70

    if impeller_diameter is None:
        impeller_diameter = D * 0.40

    if impeller_clearance is None:
        impeller_clearance = D * 0.10

    if number_impellers is None:
        number_impellers = 1

    if number_baffles is None:
        number_baffles = 4

    if frames_count is None:
        frames_count = 36

    frames_count = max(
        1,
        int(frames_count)
    )

    # =====================================================
    # VESSEL PROFILE
    # =====================================================

    z_profile, r_profile = profile(
        D,
        straight_height,
        bottom_type,
        top_type,
        n_points=220,
    )

    theta = np.linspace(
        0.0,
        2.0 * math.pi,
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
    # REACTOR VESSEL
    # =====================================================

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.22,
            showscale=False,
            name="Reactor Vessel",
            hovertemplate=(
                "Reactor Vessel"
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
        0.0,
        2.0 * math.pi,
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
            line=dict(
                width=5
            ),
        )
    )

    # =====================================================
    # LIQUID BODY
    # =====================================================

    liquid_mask = (
        z_profile <= liquid_z
    )

    zl = z_profile[
        liquid_mask
    ]

    rl = r_profile[
        liquid_mask
    ]

    if len(zl) >= 2:

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
                opacity=0.10,
                showscale=False,
                name="Liquid",
                hoverinfo="skip",
            )
        )

    # =====================================================
    # SHAFT
    # =====================================================

    shaft_z = np.linspace(
        0.0,
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
            line=dict(
                width=8
            ),
        )
    )

    # =====================================================
    # BAFFLES
    # =====================================================

    if int(number_baffles) > 0:

        baffle_count = int(
            number_baffles
        )

        baffle_r = (
            D / 2.0 -
            D * 0.05
        )

        for i in range(
            baffle_count
        ):

            angle = (
                2.0 *
                math.pi *
                i /
                baffle_count
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
                    x=[
                        bx,
                        bx
                    ],
                    y=[
                        by,
                        by
                    ],
                    z=[
                        0.0,
                        liquid_z
                    ],
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
    # IMPELLER BLADE COUNT
    # =====================================================

    blade_library = {

        "Rushton Turbine": 6,

        "Pitched Blade Turbine": 4,

        "Hydrofoil": 3,

        "Marine Propeller": 3,

        "Anchor": 2,

        "Helical Ribbon": 1,

        "RCI": 2,
    }

    blades = blade_library.get(
        agitator,
        4
    )

    # =====================================================
    # IMPELLER POSITIONS
    # =====================================================

    nimp = max(
        1,
        int(number_impellers)
    )

    clearance = max(
        0.0,
        float(impeller_clearance)
    )

    usable_height = max(
        liquid_z -
        clearance -
        0.15 * D,
        0.20 * D
    )

    if nimp == 1:

        positions = [
            clearance
        ]

    else:

        positions = []

        for i in range(nimp):

            frac = (
                i /
                (nimp - 1)
            )

            positions.append(
                clearance +
                frac *
                usable_height
            )

    # =====================================================
    # DRAW IMPELLERS
    # =====================================================

    for idx, z_imp in enumerate(
        positions
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

    rng = np.random.default_rng(
        42
    )

    n_particles = 100

    particle_z = (
        rng.random(
            n_particles
        )
        *
        max(
            liquid_z,
            0.05
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
            liquid_radius * 0.82,
            D * 0.03
        )
    )

    particle_angle = (
        rng.random(
            n_particles
        )
        *
        2.0 *
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

    particle_trace_index = (
        len(fig.data)
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
                opacity=0.60,
            ),
        )
    )

    # =====================================================
    # ANIMATION FRAMES
    # =====================================================

    frames = []

    for frame_no in range(
        frames_count
    ):

        rotation = (
            2.0 *
            math.pi *
            frame_no /
            frames_count
        )

        # Add a slight vertical circulation
        # for visual representation
        vertical_shift = (
            0.04 *
            D *
            math.sin(
                rotation * 2.0
            )
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

        fz = (
            particle_z +
            vertical_shift *
            np.sin(
                particle_angle * 2.0
            )
        )

        fz = np.clip(
            fz,
            0.0,
            liquid_z
        )

        frames.append(
            go.Frame(
                name=str(frame_no),

                data=[
                    go.Scatter3d(
                        x=fx,
                        y=fy,
                        z=fz,
                        mode="markers",
                        marker=dict(
                            size=3,
                            opacity=0.60,
                        ),
                    )
                ],

                traces=[
                    particle_trace_index
                ],
            )
        )

    fig.frames = frames

    # =====================================================
    # ANIMATION CONTROL
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
                                    "duration": 0
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
                                "transition": {
                                    "duration": 0
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

    total_height = (
        z_profile[-1]
    )

    fig.update_layout(

        title=(
            f"3D Reactor | "
            f"{agitator} | "
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
                    1.2,
                    total_height / max(D, 0.1)
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
