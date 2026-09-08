import math

import plotly.graph_objects as go


def _safe(value, default=0.0):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _cylinder_surface(
    radius,
    height,
    z0,
    segments=48,
):

    theta = [
        2.0 * math.pi * i / segments
        for i in range(segments + 1)
    ]

    x = []
    y = []
    z = []

    for zz in [z0, z0 + height]:

        for angle in theta:

            x.append(
                radius * math.cos(angle)
            )

            y.append(
                radius * math.sin(angle)
            )

            z.append(zz)

    i0 = 0
    i1 = segments + 1

    vertices_x = []
    vertices_y = []
    vertices_z = []

    for i in range(segments):

        j = i + 1

        vertices_x.extend(
            [
                x[i],
                x[j],
                x[i1 + j],
                x[i],
                x[i1 + j],
                x[i1 + i],
            ]
        )

        vertices_y.extend(
            [
                y[i],
                y[j],
                y[i1 + j],
                y[i],
                y[i1 + j],
                y[i1 + i],
            ]
        )

        vertices_z.extend(
            [
                z[i],
                z[j],
                z[i1 + j],
                z[i],
                z[i1 + j],
                z[i1 + i],
            ]
        )

    return (
        vertices_x,
        vertices_y,
        vertices_z,
    )


def _add_vessel(
    fig,
    D,
    straight_height,
    opacity=0.20,
):

    radius = D / 2.0

    x, y, z = _cylinder_surface(
        radius,
        straight_height,
        0.0,
    )

    fig.add_trace(
        go.Mesh3d(
            x=x,
            y=y,
            z=z,
            opacity=opacity,
            name="Reactor Shell",
            hoverinfo="skip",
        )
    )


def _add_liquid(
    fig,
    D,
    liquid_height,
):

    radius = D / 2.0

    theta = [
        2.0 * math.pi * i / 48
        for i in range(49)
    ]

    x = [
        radius * math.cos(t)
        for t in theta
    ]

    y = [
        radius * math.sin(t)
        for t in theta
    ]

    z = [
        liquid_height
        for _ in theta
    ]

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            name="Liquid Level",
        )
    )


def _add_shaft(
    fig,
    D,
    height,
):

    radius = max(
        0.025 * D,
        0.02,
    )

    theta = [
        2.0 * math.pi * i / 32
        for i in range(33)
    ]

    x = []
    y = []
    z = []

    for zz in [0.0, height]:

        for t in theta:

            x.append(
                radius * math.cos(t)
            )

            y.append(
                radius * math.sin(t)
            )

            z.append(zz)

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            name="Agitator Shaft",
        )
    )


def _add_impeller(
    fig,
    D,
    elevation,
    agitator,
    frame_angle=0.0,
):

    radius = D / 2.0

    agitator_lower = (
        str(agitator)
        .lower()
    )

    if "anchor" in agitator_lower:

        theta = [
            2.0 * math.pi * i / 64
            for i in range(65)
        ]

        x = [
            radius * math.cos(t + frame_angle)
            for t in theta
        ]

        y = [
            radius * math.sin(t + frame_angle)
            for t in theta
        ]

        z = [
            elevation
            for _ in theta
        ]

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                name=agitator,
            )
        )

        return

    if (
        "rushton" in agitator_lower
        or "rci" in agitator_lower
    ):

        blade_count = 6

    else:

        blade_count = 4

    # Hub
    hub_radius = max(
        0.10 * radius,
        0.025,
    )

    theta_hub = [
        2.0 * math.pi * i / 32
        for i in range(33)
    ]

    hx = [
        hub_radius
        * math.cos(
            t + frame_angle
        )
        for t in theta_hub
    ]

    hy = [
        hub_radius
        * math.sin(
            t + frame_angle
        )
        for t in theta_hub
    ]

    hz = [
        elevation
        for _ in theta_hub
    ]

    fig.add_trace(
        go.Scatter3d(
            x=hx,
            y=hy,
            z=hz,
            mode="lines",
            name=f"{agitator} hub",
            showlegend=False,
        )
    )

    for blade in range(
        blade_count
    ):

        angle = (
            2.0
            * math.pi
            * blade
            / blade_count
            + frame_angle
        )

        x1 = (
            hub_radius
            * math.cos(angle)
        )

        y1 = (
            hub_radius
            * math.sin(angle)
        )

        x2 = (
            radius
            * math.cos(angle)
        )

        y2 = (
            radius
            * math.sin(angle)
        )

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x1,
                    x2,
                ],
                y=[
                    y1,
                    y2,
                ],
                z=[
                    elevation,
                    elevation,
                ],
                mode="lines",
                name=(
                    agitator
                    if blade == 0
                    else None
                ),
                showlegend=(
                    blade == 0
                ),
            )
        )


def _add_baffles(
    fig,
    D,
    straight_height,
    number_baffles,
):

    if number_baffles <= 0:
        return

    radius = D / 2.0

    baffle_width = (
        0.08 * D
    )

    for i in range(
        number_baffles
    ):

        angle = (
            2.0
            * math.pi
            * i
            / number_baffles
        )

        x = (
            radius
            * math.cos(angle)
        )

        y = (
            radius
            * math.sin(angle)
        )

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x,
                    x,
                ],
                y=[
                    y,
                    y,
                ],
                z=[
                    0.0,
                    straight_height,
                ],
                mode="lines",
                name=(
                    "Baffles"
                    if i == 0
                    else None
                ),
                showlegend=(
                    i == 0
                ),
            )
        )


def create_reactor_animation(
    D,
    straight_height,
    bottom_type=None,
    top_type=None,
    liquid_height=None,
    impellers=None,
    rpm=0.0,
    number_baffles=4,
    frames_count=36,
    show_dimensions=True,
    show_nozzles=True,
    show_tracers=True,
    show_baffles=True,
    vessel_opacity=0.20,
):

    D = _safe(
        D,
        2.0,
    )

    straight_height = _safe(
        straight_height,
        3.0,
    )

    liquid_height = _safe(
        liquid_height,
        straight_height * 0.8,
    )

    rpm = _safe(
        rpm,
        0.0,
    )

    if not isinstance(
        impellers,
        list,
    ):

        impellers = []

    fig = go.Figure()

    _add_vessel(
        fig,
        D,
        straight_height,
        vessel_opacity,
    )

    _add_liquid(
        fig,
        D,
        liquid_height,
    )

    _add_shaft(
        fig,
        D,
        straight_height,
    )

    if show_baffles:

        _add_baffles(
            fig,
            D,
            straight_height,
            int(number_baffles),
        )

    for impeller in impellers:

        if not isinstance(
            impeller,
            dict,
        ):
            continue

        impeller_D = _safe(
            impeller.get(
                "diameter_m",
                impeller.get("D"),
            ),
            D * 0.5,
        )

        elevation = _safe(
            impeller.get(
                "elevation_m"
            ),
            liquid_height * 0.5,
        )

        agitator = impeller.get(
            "agitator_type",
            impeller.get(
                "type",
                "Impeller",
            ),
        )

        _add_impeller(
            fig,
            impeller_D,
            elevation,
            agitator,
        )

    # --------------------------------------------------------
    # Animation frames
    # --------------------------------------------------------

    frames = []

    for frame_index in range(
        max(
            1,
            int(frames_count),
        )
    ):

        angle = (
            2.0
            * math.pi
            * frame_index
            / max(
                1,
                int(frames_count),
            )
        )

        frame_traces = []

        for impeller in impellers:

            if not isinstance(
                impeller,
                dict,
            ):
                continue

            impeller_D = _safe(
                impeller.get(
                    "diameter_m",
                    impeller.get("D"),
                ),
                D * 0.5,
            )

            elevation = _safe(
                impeller.get(
                    "elevation_m"
                ),
                liquid_height * 0.5,
            )

            agitator = impeller.get(
                "agitator_type",
                impeller.get(
                    "type",
                    "Impeller",
                ),
            )

            radius = (
                impeller_D / 2.0
            )

            lower = str(
                agitator
            ).lower()

            blade_count = (
                6
                if (
                    "rushton" in lower
                    or "rci" in lower
                )
                else 4
            )

            for blade in range(
                blade_count
            ):

                blade_angle = (
                    angle
                    + 2.0
                    * math.pi
                    * blade
                    / blade_count
                )

                hub = (
                    radius * 0.10
                )

                frame_traces.append(
                    go.Scatter3d(
                        x=[
                            hub
                            * math.cos(
                                blade_angle
                            ),
                            radius
                            * math.cos(
                                blade_angle
                            ),
                        ],
                        y=[
                            hub
                            * math.sin(
                                blade_angle
                            ),
                            radius
                            * math.sin(
                                blade_angle
                            ),
                        ],
                        z=[
                            elevation,
                            elevation,
                        ],
                        mode="lines",
                        showlegend=False,
                    )
                )

        frames.append(
            go.Frame(
                data=frame_traces,
                name=str(frame_index),
            )
        )

    fig.frames = frames

    if frames:

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

    max_dimension = max(
        D,
        straight_height,
    )

    fig.update_layout(
        title="Reactor 3D Engineering Visualization",
        scene={
            "xaxis_title": "X (m)",
            "yaxis_title": "Y (m)",
            "zaxis_title": "Elevation (m)",
            "aspectmode": "manual",
            "aspectratio": {
                "x": 1,
                "y": 1,
                "z": max_dimension / D
                if D > 0
                else 1,
            },
        },
        height=720,
        margin={
            "l": 0,
            "r": 0,
            "t": 50,
            "b": 0,
        },
        showlegend=True,
    )

    return fig


def create_reactor_3d(**kwargs):

    return create_reactor_animation(
        **kwargs
    )
