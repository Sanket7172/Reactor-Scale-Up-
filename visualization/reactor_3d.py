import math

import numpy as np
import plotly.graph_objects as go

from libraries.reactor_geometry import (
    profile,
    radius_at_height,
    head_depth,
)


# =========================================================
# VESSEL SURFACE
# =========================================================

def create_vessel_surface(
    D,
    straight_height,
    bottom_type,
    top_type,
    n_theta=60,
):
    """
    Create a 3D reactor vessel surface.

    All dimensions are in metres.
    """

    z_profile, r_profile = profile(
        D=D,
        straight_height=straight_height,
        bottom_type=bottom_type,
        top_type=top_type,
    )

    theta = np.linspace(
        0,
        2 * math.pi,
        n_theta
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z_profile
    )

    radius_grid = np.repeat(
        r_profile[:, np.newaxis],
        n_theta,
        axis=1
    )

    x = (
        radius_grid *
        np.cos(theta_grid)
    )

    y = (
        radius_grid *
        np.sin(theta_grid)
    )

    z = z_grid

    return x, y, z


# =========================================================
# VESSEL
# =========================================================

def add_vessel(
    fig,
    D,
    straight_height,
    bottom_type,
    top_type,
):
    """
    Add reactor vessel surface to Plotly figure.
    """

    x, y, z = create_vessel_surface(
        D=D,
        straight_height=straight_height,
        bottom_type=bottom_type,
        top_type=top_type,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.22,
            showscale=False,
            name="Reactor Vessel",
            hoverinfo="skip",
        )
    )


# =========================================================
# LIQUID SURFACE
# =========================================================

def add_liquid(
    fig,
    D,
    liquid_height,
):
    """
    Add liquid surface.

    Dimensions in metres.
    """

    radius = radius_at_height(
        z=liquid_height,
        D=D,
        straight_height=0.000001,
        bottom_type="Flat Bottom",
        top_type="Flat Bottom",
    )

    # For normal cylindrical liquid region,
    # use vessel radius if calculated radius is invalid.
    if radius <= 0:
        radius = D / 2.0

    theta = np.linspace(
        0,
        2 * math.pi,
        60
    )

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = np.full_like(
        theta,
        liquid_height
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            name="Liquid Level",
            line=dict(
                width=4
            ),
            hoverinfo="skip",
        )
    )


# =========================================================
# BAFFLES
# =========================================================

def add_baffles(
    fig,
    D,
    straight_height,
    liquid_height,
    number_baffles=4,
):
    """
    Add conceptual vertical baffles.
    """

    if number_baffles <= 0:
        return

    R = D / 2.0

    baffle_width = D * 0.08
    baffle_thickness = D * 0.015

    baffle_bottom = 0.0
    baffle_top = max(
        liquid_height,
        straight_height
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

        radial_x = math.cos(angle)
        radial_y = math.sin(angle)

        tangent_x = -math.sin(angle)
        tangent_y = math.cos(angle)

        center_x = (
            radial_x *
            (
                R -
                baffle_thickness
            )
        )

        center_y = (
            radial_y *
            (
                R -
                baffle_thickness
            )
        )

        corners = []

        for z in [
            baffle_bottom,
            baffle_top
        ]:

            for w in [
                -baffle_width / 2,
                baffle_width / 2
            ]:

                x = (
                    center_x +
                    tangent_x * w
                )

                y = (
                    center_y +
                    tangent_y * w
                )

                corners.append(
                    (x, y, z)
                )

        # Bottom edge
        fig.add_trace(
            go.Scatter3d(
                x=[
                    corners[0][0],
                    corners[1][0]
                ],
                y=[
                    corners[0][1],
                    corners[1][1]
                ],
                z=[
                    corners[0][2],
                    corners[1][2]
                ],
                mode="lines",
                line=dict(width=6),
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Top edge
        fig.add_trace(
            go.Scatter3d(
                x=[
                    corners[2][0],
                    corners[3][0]
                ],
                y=[
                    corners[2][1],
                    corners[3][1]
                ],
                z=[
                    corners[2][2],
                    corners[3][2]
                ],
                mode="lines",
                line=dict(width=6),
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Vertical edges
        for j in range(2):

            fig.add_trace(
                go.Scatter3d(
                    x=[
                        corners[j][0],
                        corners[j + 2][0]
                    ],
                    y=[
                        corners[j][1],
                        corners[j + 2][1]
                    ],
                    z=[
                        corners[j][2],
                        corners[j + 2][2]
                    ],
                    mode="lines",
                    line=dict(width=6),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )


# =========================================================
# SHAFT
# =========================================================

def add_shaft(
    fig,
    D,
    total_height,
):
    """
    Add vertical agitator shaft.
    """

    shaft_radius = max(
        D * 0.025,
        0.005
    )

    z = np.linspace(
        0,
        total_height,
        30
    )

    x = np.full_like(
        z,
        0.0
    )

    y = np.full_like(
        z,
        0.0
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            name="Agitator Shaft",
            line=dict(
                width=8
            ),
            hoverinfo="skip",
        )
    )


# =========================================================
# IMPELLER GEOMETRY
# =========================================================

def create_impeller(
    agitator,
    impeller_diameter,
    z_position,
):
    """
    Create conceptual impeller geometry.

    Dimensions in metres.
    """

    R = impeller_diameter / 2.0

    traces = []

    # -----------------------------------------------------
    # RUSHTON
    # -----------------------------------------------------

    if agitator == "Rushton Turbine":

        number_blades = 6

        for i in range(
            number_blades
        ):

            angle = (
                2 *
                math.pi *
                i /
                number_blades
            )

            x1 = 0
            y1 = 0

            x2 = (
                R *
                math.cos(angle)
            )

            y2 = (
                R *
                math.sin(angle)
            )

            traces.append(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        z_position,
                        z_position
                    ],
                    mode="lines",
                    line=dict(width=10),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # -----------------------------------------------------
    # PITCHED BLADE
    # -----------------------------------------------------

    elif agitator == "Pitched Blade Turbine":

        number_blades = 4

        for i in range(
            number_blades
        ):

            angle = (
                2 *
                math.pi *
                i /
                number_blades
            )

            x1 = (
                0.15 *
                R *
                math.cos(angle)
            )

            y1 = (
                0.15 *
                R *
                math.sin(angle)
            )

            x2 = (
                R *
                math.cos(angle)
            )

            y2 = (
                R *
                math.sin(angle)
            )

            traces.append(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        z_position,
                        z_position
                    ],
                    mode="lines",
                    line=dict(width=10),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # -----------------------------------------------------
    # HYDROFOIL
    # -----------------------------------------------------

    elif agitator == "Hydrofoil":

        number_blades = 3

        for i in range(
            number_blades
        ):

            angle = (
                2 *
                math.pi *
                i /
                number_blades
            )

            x1 = (
                0.10 *
                R *
                math.cos(angle)
            )

            y1 = (
                0.10 *
                R *
                math.sin(angle)
            )

            x2 = (
                R *
                math.cos(angle)
            )

            y2 = (
                R *
                math.sin(angle)
            )

            traces.append(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        z_position,
                        z_position
                    ],
                    mode="lines",
                    line=dict(width=10),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # -----------------------------------------------------
    # MARINE PROPELLER
    # -----------------------------------------------------

    elif agitator == "Marine Propeller":

        number_blades = 3

        for i in range(
            number_blades
        ):

            angle = (
                2 *
                math.pi *
                i /
                number_blades
            )

            x1 = (
                0.10 *
                R *
                math.cos(angle)
            )

            y1 = (
                0.10 *
                R *
                math.sin(angle)
            )

            x2 = (
                R *
                math.cos(angle)
            )

            y2 = (
                R *
                math.sin(angle)
            )

            traces.append(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        z_position,
                        z_position
                    ],
                    mode="lines",
                    line=dict(width=9),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # -----------------------------------------------------
    # ANCHOR
    # -----------------------------------------------------

    elif agitator == "Anchor":

        theta = np.linspace(
            0,
            2 * math.pi,
            100
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
            z_position
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(width=10),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # -----------------------------------------------------
    # HELICAL RIBBON
    # -----------------------------------------------------

    elif agitator == "Helical Ribbon":

        theta = np.linspace(
            0,
            2 * math.pi * 2,
            160
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
            z_position +
            0.10 *
            R *
            np.sin(theta)
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(width=8),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # -----------------------------------------------------
    # RCI
    # -----------------------------------------------------

    elif agitator == "RCI":

        number_blades = 2

        for i in range(
            number_blades
        ):

            angle = (
                2 *
                math.pi *
                i /
                number_blades
            )

            x1 = (
                -0.30 *
                R *
                math.cos(angle)
            )

            y1 = (
                -0.30 *
                R *
                math.sin(angle)
            )

            x2 = (
                R *
                math.cos(angle)
            )

            y2 = (
                R *
                math.sin(angle)
            )

            traces.append(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        z_position,
                        z_position
                    ],
                    mode="lines",
                    line=dict(width=10),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    return traces


# =========================================================
# PARTICLES
# =========================================================

def create_particles(
    D,
    liquid_height,
    number_particles=100,
):
    """
    Create conceptual mixing particles.

    This is visualization only.
    It is NOT CFD.
    """

    R = D / 2.0

    rng = np.random.default_rng(42)

    theta = rng.uniform(
        0,
        2 * math.pi,
        number_particles
    )

    radius = (
        np.sqrt(
            rng.uniform(
                0,
                1,
                number_particles
            )
        )
        *
        R *
        0.85
    )

    x = (
        radius *
        np.cos(theta)
    )

    y = (
        radius *
        np.sin(theta)
    )

    z = rng.uniform(
        0.05 *
        max(liquid_height, 0.01),

        0.95 *
        max(liquid_height, 0.01),

        number_particles
    )

    return x, y, z


# =========================================================
# MAIN REACTOR 3D FUNCTION
# =========================================================

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
    """
    Create interactive 3D reactor visualization.

    Parameters
    ----------
    D : float
        Reactor internal diameter in metres.

    straight_height : float
        Straight-side height in metres.

    bottom_type : str
        Reactor bottom geometry.

    top_type : str
        Reactor top geometry.

    liquid_height : float
        Liquid level in metres.

    agitator : str
        Agitator type.

    impeller_diameter : float
        Impeller diameter in metres.

    number_impellers : int
        Number of impellers.

    rpm : float
        Agitator speed.

    number_baffles : int
        Number of baffles.

    vortex_depth : float
        Conceptual vortex depth in metres.

    frames_count : int
        Number of animation frames.
    """

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if D <= 0:
        raise ValueError(
            "Reactor diameter must be greater than zero."
        )

    if straight_height <= 0:
        raise ValueError(
            "Straight height must be greater than zero."
        )

    if impeller_diameter <= 0:
        raise ValueError(
            "Impeller diameter must be greater than zero."
        )

    if number_impellers <= 0:
        number_impellers = 1

    if number_baffles < 0:
        number_baffles = 0

    # -----------------------------------------------------
    # TOTAL REACTOR HEIGHT
    # -----------------------------------------------------

    bottom_depth = head_depth(
        D,
        bottom_type
    )

    top_depth = head_depth(
        D,
        top_type
    )

    total_height = (
        bottom_depth +
        straight_height +
        top_depth
    )

    # Keep liquid height inside reactor
    liquid_height = max(
        0.0,
        min(
            liquid_height,
            total_height
        )
    )

    # -----------------------------------------------------
    # CREATE FIGURE
    # -----------------------------------------------------

    fig = go.Figure()

    # -----------------------------------------------------
    # VESSEL
    # -----------------------------------------------------

    add_vessel(
        fig=fig,
        D=D,
        straight_height=straight_height,
        bottom_type=bottom_type,
        top_type=top_type,
    )

    # -----------------------------------------------------
    # LIQUID
    # -----------------------------------------------------

    if liquid_height > 0:

        # Use simple cylindrical liquid surface.
        theta = np.linspace(
            0,
            2 * math.pi,
            80
        )

        liquid_radius = D / 2.0

        x = (
            liquid_radius *
            np.cos(theta)
        )

        y = (
            liquid_radius *
            np.sin(theta)
        )

        z = np.full_like(
            theta,
            liquid_height
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                name="Liquid Level",
                line=dict(
                    width=5
                ),
                hoverinfo="skip",
            )
        )

    # -----------------------------------------------------
    # BAFFLES
    # -----------------------------------------------------

    add_baffles(
        fig=fig,
        D=D,
        straight_height=straight_height,
        liquid_height=liquid_height,
        number_baffles=number_baffles,
    )

    # -----------------------------------------------------
    # SHAFT
    # -----------------------------------------------------

    add_shaft(
        fig=fig,
        D=D,
        total_height=total_height,
    )

    # -----------------------------------------------------
    # IMPELLERS
    # -----------------------------------------------------

    impeller_spacing = (
        liquid_height /
        max(
            number_impellers + 1,
            2
        )
    )

    impeller_traces = []

    for i in range(
        number_impellers
    ):

        z_position = (
            impeller_spacing *
            (i + 1)
        )

        traces = create_impeller(
            agitator=agitator,
            impeller_diameter=impeller_diameter,
            z_position=z_position,
        )

        for trace in traces:

            fig.add_trace(
                trace
            )

            impeller_traces.append(
                trace
            )

    # -----------------------------------------------------
    # PARTICLES
    # -----------------------------------------------------

    (
        particle_x,
        particle_y,
        particle_z
    ) = create_particles(
        D=D,
        liquid_height=liquid_height,
        number_particles=120,
    )

    fig.add_trace(
        go.Scatter3d(
            x=particle_x,
            y=particle_y,
            z=particle_z,
            mode="markers",
            marker=dict(
                size=3
            ),
            name="Mixing Particles",
            hoverinfo="skip",
        )
    )

    # -----------------------------------------------------
    # ANIMATION FRAMES
    # -----------------------------------------------------

    frames = []

    if frames_count < 1:
        frames_count = 1

    for frame_number in range(
        frames_count
    ):

        angle = (
            2 *
            math.pi *
            rpm /
            60.0 *
            (
                frame_number /
                frames_count
            )
        )

        frame_data = []

        for i in range(
            number_impellers
        ):

            z_position = (
                impeller_spacing *
                (i + 1)
            )

            traces = create_impeller(
                agitator=agitator,
                impeller_diameter=impeller_diameter,
                z_position=z_position,
            )

            for trace in traces:

                if hasattr(
                    trace,
                    "x"
                ) and trace.x is not None:

                    x_values = np.array(
                        trace.x,
                        dtype=float
                    )

                    y_values = np.array(
                        trace.y,
                        dtype=float
                    )

                    rotated_x = (
                        x_values *
                        math.cos(angle)
                        -
                        y_values *
                        math.sin(angle)
                    )

                    rotated_y = (
                        x_values *
                        math.sin(angle)
                        +
                        y_values *
                        math.cos(angle)
                    )

                    trace.x = rotated_x
                    trace.y = rotated_y

                frame_data.append(
                    trace
                )

        frames.append(
            go.Frame(
                data=frame_data,
                name=str(
                    frame_number
                )
            )
        )

    fig.frames = frames

    # -----------------------------------------------------
    # LAYOUT
    # -----------------------------------------------------

    max_radius = D / 2.0 * 1.25

    fig.update_layout(

        title={
            "text": (
                f"3D Reactor Visualization — "
                f"{agitator}"
            ),
            "x": 0.5,
        },

        scene=dict(

            xaxis=dict(
                title="X (m)",
                range=[
                    -max_radius,
                    max_radius
                ],
            ),

            yaxis=dict(
                title="Y (m)",
                range=[
                    -max_radius,
                    max_radius
                ],
            ),

            zaxis=dict(
                title="Height (m)",
                range=[
                    0,
                    total_height * 1.10
                ],
            ),

            aspectmode="manual",

            aspectratio=dict(
                x=1,
                y=1,
                z=max(
                    total_height / D,
                    1.0
                ),
            ),

            camera=dict(
                eye=dict(
                    x=1.6,
                    y=1.6,
                    z=1.2
                )
            ),
        ),

        height=700,

        margin=dict(
            l=0,
            r=0,
            t=50,
            b=0,
        ),

        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.05,
                y=1.05,
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {
                                    "duration": 80,
                                    "redraw": True,
                                },
                                "fromcurrent": True,
                            }
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
                            }
                        ],
                    ),
                ],
            )
        ],
    )

    return fig
