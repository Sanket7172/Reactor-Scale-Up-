# visualization/reactor_3d.py

import numpy as np
import plotly.graph_objects as go

from libraries.reactor_geometry import (
    profile,
    radius_at_height,
    head_depth
)


def cylinder_mesh(
    radius,
    z1,
    z2,
    n=40
):

    theta = np.linspace(
        0,
        2*np.pi,
        n
    )

    z = np.array([z1, z2])

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    x = radius * np.cos(theta_grid)
    y = radius * np.sin(theta_grid)

    return x, y, z_grid


def create_vessel_surface(
    D,
    straight_height,
    bottom_type,
    top_type
):

    z, r = profile(
        D,
        straight_height,
        bottom_type,
        top_type,
        points=160
    )

    theta = np.linspace(
        0,
        2*np.pi,
        70
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    r_grid = np.repeat(
        r[:, None],
        len(theta),
        axis=1
    )

    x = r_grid * np.cos(theta_grid)
    y = r_grid * np.sin(theta_grid)

    return x, y, z_grid


def add_vessel(
    fig,
    D,
    straight_height,
    bottom_type,
    top_type
):

    x, y, z = create_vessel_surface(
        D,
        straight_height,
        bottom_type,
        top_type
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.20,
            showscale=False,
            name="Reactor Shell",
            hoverinfo="skip"
        )
    )


def add_baffles(
    fig,
    D,
    liquid_height,
    number_baffles
):

    if number_baffles <= 0:
        return

    R = D / 2

    theta_values = np.linspace(
        0,
        2*np.pi,
        number_baffles,
        endpoint=False
    )

    for theta in theta_values:

        x = np.array([
            R * np.cos(theta),
            R * 0.94 * np.cos(theta)
        ])

        y = np.array([
            R * np.sin(theta),
            R * 0.94 * np.sin(theta)
        ])

        z = np.array([
            liquid_height * 0.08,
            liquid_height * 0.95
        ])

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=12
                ),
                name="Baffle",
                showlegend=False
            )
        )


def add_shaft(
    fig,
    shaft_height,
    shaft_radius
):

    fig.add_trace(
        go.Scatter3d(
            x=[0, 0],
            y=[0, 0],
            z=[0, shaft_height],
            mode="lines",
            line=dict(
                width=10
            ),
            name="Shaft",
            showlegend=False
        )
    )


def impeller_geometry(
    agitator,
    D,
    z,
    angle
):

    R = D / 2

    traces = []

    # --------------------------------------------
    # RUSHTON
    # --------------------------------------------

    if agitator == "Rushton Turbine":

        hub_r = 0.12 * R

        theta = np.linspace(
            0,
            2*np.pi,
            40
        )

        traces.append(
            go.Scatter3d(
                x=hub_r*np.cos(theta),
                y=hub_r*np.sin(theta),
                z=np.ones_like(theta)*z,
                mode="lines",
                line=dict(width=6),
                showlegend=False
            )
        )

        blades = 6

        for i in range(blades):

            a = (
                2*np.pi*i/blades
                + angle
            )

            x = [
                hub_r*np.cos(a),
                R*np.cos(a)
            ]

            y = [
                hub_r*np.sin(a),
                R*np.sin(a)
            ]

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=[z, z],
                    mode="lines",
                    line=dict(width=14),
                    showlegend=False
                )
            )

    # --------------------------------------------
    # PITCHED BLADE
    # --------------------------------------------

    elif agitator == "Pitched Blade Turbine":

        blades = 4

        for i in range(blades):

            a = (
                2*np.pi*i/blades
                + angle
            )

            r1 = 0.20 * R
            r2 = R

            x = [
                r1*np.cos(a),
                r2*np.cos(a + 0.22)
            ]

            y = [
                r1*np.sin(a),
                r2*np.sin(a + 0.22)
            ]

            zvals = [
                z - 0.10*D,
                z + 0.10*D
            ]

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=zvals,
                    mode="lines",
                    line=dict(width=14),
                    showlegend=False
                )
            )

    # --------------------------------------------
    # HYDROFOIL
    # --------------------------------------------

    elif agitator == "Hydrofoil":

        blades = 3

        for i in range(blades):

            a = (
                2*np.pi*i/blades
                + angle
            )

            rr = np.linspace(
                0.15*R,
                R,
                25
            )

            x = rr*np.cos(a)

            y = rr*np.sin(a)

            zvals = (
                z
                + 0.12*D*np.sin(
                    (rr/R)*np.pi
                )
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=zvals,
                    mode="lines",
                    line=dict(width=15),
                    showlegend=False
                )
            )

    # --------------------------------------------
    # MARINE PROPELLER
    # --------------------------------------------

    elif agitator == "Marine Propeller":

        blades = 3

        for i in range(blades):

            a = (
                2*np.pi*i/blades
                + angle
            )

            rr = np.linspace(
                0.10*R,
                R,
                30
            )

            x = rr*np.cos(
                a + 0.4*rr/R
            )

            y = rr*np.sin(
                a + 0.4*rr/R
            )

            zvals = (
                z
                + 0.08*D*np.sin(
                    rr/R*np.pi
                )
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=zvals,
                    mode="lines",
                    line=dict(width=13),
                    showlegend=False
                )
            )

    # --------------------------------------------
    # ANCHOR
    # --------------------------------------------

    elif agitator == "Anchor":

        r = 0.88 * R

        theta = np.linspace(
            0,
            np.pi,
            50
        )

        x = r*np.cos(theta + angle)

        y = r*np.sin(theta + angle)

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.ones_like(x)*z,
                mode="lines",
                line=dict(width=14),
                showlegend=False
            )
        )

        for a in [
            angle,
            angle + np.pi
        ]:

            traces.append(
                go.Scatter3d(
                    x=[
                        r*np.cos(a),
                        r*np.cos(a)
                    ],
                    y=[
                        r*np.sin(a),
                        r*np.sin(a)
                    ],
                    z=[
                        z,
                        z + 0.65*D
                    ],
                    mode="lines",
                    line=dict(width=14),
                    showlegend=False
                )
            )

    # --------------------------------------------
    # HELICAL RIBBON
    # --------------------------------------------

    elif agitator == "Helical Ribbon":

        turns = 1.8

        theta = np.linspace(
            0,
            2*np.pi*turns,
            160
        )

        rr = 0.85 * R

        x = rr*np.cos(
            theta + angle
        )

        y = rr*np.sin(
            theta + angle
        )

        zvals = (
            z +
            0.50*D *
            theta /
            (2*np.pi*turns)
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=zvals,
                mode="lines",
                line=dict(width=16),
                showlegend=False
            )
        )

    # --------------------------------------------
    # RCI
    # --------------------------------------------

    elif agitator == "RCI":

        blades = 2

        for i in range(blades):

            base = (
                np.pi*i
                + angle
            )

            t = np.linspace(
                0,
                1,
                80
            )

            rr = (
                0.12*R
                + 0.88*R*t
            )

            curve = (
                0.35 *
                np.sin(
                    np.pi*t
                )
            )

            a = (
                base
                + curve
            )

            x = rr*np.cos(a)

            y = rr*np.sin(a)

            zvals = (
                z
                + 0.12*D*
                np.sin(
                    np.pi*t
                )
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=zvals,
                    mode="lines",
                    line=dict(width=16),
                    showlegend=False
                )
            )

    return traces


def create_particles(
    D,
    liquid_height,
    agitator,
    frame,
    number_particles=350,
    vortex_depth=0.0
):

    rng = np.random.default_rng(42)

    R = D / 2

    r = np.sqrt(
        rng.random(number_particles)
    ) * R * 0.90

    theta0 = (
        rng.random(number_particles)
        * 2*np.pi
    )

    z0 = (
        rng.random(number_particles)
        * liquid_height
        * 0.92
    )

    # Animation angle
    phase = frame * 0.20

    # Flow intensity
    flow_strength = {

        "Rushton Turbine": 0.80,
        "Pitched Blade Turbine": 0.90,
        "Hydrofoil": 1.00,
        "Marine Propeller": 0.95,
        "Anchor": 0.35,
        "Helical Ribbon": 0.45,
        "RCI": 0.75

    }.get(
        agitator,
        0.70
    )

    theta = (
        theta0
        + phase
        * (
            0.5
            + r/R
        )
        * flow_strength
    )

    # ------------------------------------------
    # RADIAL / AXIAL FLOW MODEL
    # ------------------------------------------

    if agitator == "Rushton Turbine":

        z = (
            z0
            + 0.12*liquid_height *
            np.sin(
                theta*2 + phase
            )
        )

        rr = (
            r
            + 0.08*R *
            np.sin(
                phase + theta
            )
        )

    elif agitator in [
        "Pitched Blade Turbine",
        "Hydrofoil",
        "Marine Propeller",
        "RCI"
    ]:

        z = (
            z0
            + 0.22 *
            liquid_height *
            np.sin(
                theta + phase
            )
        )

        rr = (
            r
            + 0.05*R *
            np.sin(
                phase*2 + theta
            )
        )

    else:

        z = (
            z0
            + 0.08 *
            liquid_height *
            np.sin(
                theta*3 + phase
            )
        )

        rr = r

    z = np.clip(
        z,
        0.03*liquid_height,
        liquid_height*0.96
    )

    # ------------------------------------------
    # VORTEX EFFECT
    # ------------------------------------------

    vortex_factor = (
        1 -
        (r/R)**2
    )

    z = (
        z
        - vortex_depth *
        vortex_factor
    )

    z = np.clip(
        z,
        0.02*liquid_height,
        liquid_height
    )

    x = rr*np.cos(theta)

    y = rr*np.sin(theta)

    return x, y, z


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
    vortex_depth,
    frames_count=36
):

    fig = go.Figure()

    # ------------------------------------------
    # VESSEL
    # ------------------------------------------

    add_vessel(
        fig,
        D,
        straight_height,
        bottom_type,
        top_type
    )

    total_height = (
        head_depth(D, bottom_type)
        + straight_height
        + head_depth(D, top_type)
    )

    # ------------------------------------------
    # LIQUID SURFACE
    # ------------------------------------------

    theta = np.linspace(
        0,
        2*np.pi,
        80
    )

    r = D/2

    rr, tt = np.meshgrid(
        np.linspace(0, r, 35),
        theta
    )

    # Central vortex depression
    zsurf = (
        liquid_height
        - vortex_depth *
        (
            1 -
            (rr/r)**2
        )
    )

    xs = rr*np.cos(tt)
    ys = rr*np.sin(tt)

    fig.add_trace(
        go.Surface(
            x=xs,
            y=ys,
            z=zsurf,
            opacity=0.58,
            showscale=False,
            name="Operating Liquid"
        )
    )

    # ------------------------------------------
    # BAFFLES
    # ------------------------------------------

    add_baffles(
        fig,
        D,
        liquid_height,
        number_baffles
    )

    # ------------------------------------------
    # SHAFT
    # ------------------------------------------

    shaft_top = total_height + 0.30*D

    add_shaft(
        fig,
        shaft_top,
        0.04*D
    )

    # ------------------------------------------
    # INITIAL IMPELLERS
    # ------------------------------------------

    impeller_zs = np.linspace(
        max(
            0.15*liquid_height,
            liquid_height*0.15
        ),
        max(
            0.15*liquid_height,
            liquid_height*0.15
        ) +
        max(
            0,
            number_impellers-1
        ) *
        0.25*liquid_height,
        number_impellers
    )

    for z_imp in impeller_zs:

        for trace in impeller_geometry(
            agitator,
            impeller_diameter,
            z_imp,
            0
        ):

            fig.add_trace(trace)

    # ------------------------------------------
    # PARTICLES
    # ------------------------------------------

    px, py, pz = create_particles(
        D,
        liquid_height,
        agitator,
        0,
        vortex_depth=vortex_depth
    )

    fig.add_trace(
        go.Scatter3d(
            x=px,
            y=py,
            z=pz,
            mode="markers",
            marker=dict(
                size=2,
                opacity=0.65
            ),
            name="Mixing Flow"
        )
    )

    # ------------------------------------------
    # ANIMATION FRAMES
    # ------------------------------------------

    frames = []

    for frame_no in range(frames_count):

        angle = (
            2*np.pi *
            frame_no /
            frames_count
        )

        frame_traces = []

        # Liquid surface vortex animation
        zsurf_frame = (
            liquid_height
            - vortex_depth *
            (
                1 -
                (rr/r)**2
            )
            * (
                0.95
                + 0.05 *
                np.sin(
                    angle
                )
            )
        )

        frame_traces.append(
            go.Surface(
                x=xs,
                y=ys,
                z=zsurf_frame,
                opacity=0.58,
                showscale=False
            )
        )

        # Impellers
        for z_imp in impeller_zs:

            frame_traces.extend(
                impeller_geometry(
                    agitator,
                    impeller_diameter,
                    z_imp,
                    angle
                )
            )

        # Mixing particles
        px, py, pz = create_particles(
            D,
            liquid_height,
            agitator,
            frame_no,
            vortex_depth=vortex_depth
        )

        frame_traces.append(
            go.Scatter3d(
                x=px,
                y=py,
                z=pz,
                mode="markers",
                marker=dict(
                    size=2,
                    opacity=0.65
                )
            )
        )

        # Only update liquid + impellers + particles.
        frames.append(
            go.Frame(
                data=frame_traces,
                name=f"frame{frame_no}"
            )
        )

    fig.frames = frames

    # ------------------------------------------
    # PLAYBACK CONTROLS
    # ------------------------------------------

    fig.update_layout(

        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,

                "buttons": [

                    {
                        "label": "▶ Play",
                        "method": "animate",

                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": max(
                                        40,
                                        int(
                                            6000 /
                                            max(
                                                rpm,
                                                1
                                            )
                                        )
                                    ),
                                    "redraw": True
                                },

                                "transition": {
                                    "duration": 0
                                },

                                "fromcurrent": True
                            }
                        ]
                    },

                    {
                        "label": "⏸ Pause",
                        "method": "animate",

                        "args": [
                            [None],
                            {
                                "frame": {
                                    "duration": 0,
                                    "redraw": False
                                },

                                "transition": {
                                    "duration": 0
                                }
                            }
                        ]
                    }
                ]
            }
        ],

        scene=dict(

            aspectmode="data",

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

            camera=dict(
                eye=dict(
                    x=1.6,
                    y=1.6,
                    z=1.1
                )
            )
        ),

        height=720,

        margin=dict(
            l=0,
            r=0,
            t=30,
            b=0
        ),

        title=(
            "3D Reactor — "
            "Animated Mixing / Vortex Visualization"
        )
    )

    return fig
