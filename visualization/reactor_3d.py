# ============================================================
# 3D REACTOR VISUALIZATION
# ============================================================

import numpy as np
import plotly.graph_objects as go


def create_reactor_3d(
    reactor,
    result,
    reaction_type="Liquid-Liquid",
):

    fig = go.Figure()

    D = (
        reactor["tank_id"]
        / 1000.0
    )

    R = D / 2.0

    H = (
        reactor["straight_side_height"]
        / 1000.0
    )

    liquid_height = (
        result["liquid_height"]
        / 1000.0
    )

    bottom_type = reactor[
        "bottom_type"
    ]

    top_type = reactor[
        "top_type"
    ]

    # --------------------------------------------------------
    # SIMPLE VESSEL HEIGHT
    # --------------------------------------------------------

    bottom_depth = (
        0.25 * D
        if bottom_type
        == "2:1 Ellipsoidal"
        else 0.10 * D
    )

    top_depth = (
        0.25 * D
        if top_type
        == "2:1 Ellipsoidal"
        else 0.10 * D
    )

    total_height = (
        bottom_depth
        + H
        + top_depth
    )

    # --------------------------------------------------------
    # VESSEL WALL
    # --------------------------------------------------------

    theta = np.linspace(
        0,
        2 * np.pi,
        60,
    )

    z = np.linspace(
        0,
        total_height,
        40,
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z,
    )

    radius_grid = np.full_like(
        z_grid,
        R,
    )

    # Bottom reduction
    bottom_mask = (
        z_grid
        < bottom_depth
    )

    radius_grid[
        bottom_mask
    ] = (
        R
        * np.sqrt(
            np.clip(
                2
                * z_grid[
                    bottom_mask
                ]
                / bottom_depth
                - (
                    z_grid[
                        bottom_mask
                    ]
                    / bottom_depth
                ) ** 2,
                0,
                1,
            )
        )
    )

    # Top reduction
    top_start = (
        bottom_depth
        + H
    )

    top_mask = (
        z_grid
        > top_start
    )

    ratio = np.zeros_like(
        z_grid[
            top_mask
        ]
    )

    if top_depth > 0:

        ratio = (
            z_grid[
                top_mask
            ]
            - top_start
        ) / top_depth

    radius_grid[
        top_mask
    ] = (
        R
        * np.sqrt(
            np.clip(
                2 * ratio
                - ratio**2,
                0,
                1,
            )
        )
    )

    X = (
        radius_grid
        * np.cos(theta_grid)
    )

    Y = (
        radius_grid
        * np.sin(theta_grid)
    )

    Z = z_grid

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.22,
            showscale=False,
            name="Reactor",
        )
    )

    # --------------------------------------------------------
    # LIQUID
    # --------------------------------------------------------

    liquid_r = R * 0.98

    liquid_x = (
        liquid_r
        * np.cos(theta)
    )

    liquid_y = (
        liquid_r
        * np.sin(theta)
    )

    liquid_z = np.full_like(
        theta,
        liquid_height,
    )

    fig.add_trace(
        go.Scatter3d(
            x=liquid_x,
            y=liquid_y,
            z=liquid_z,
            mode="lines",
            line=dict(
                width=5,
            ),
            name="Liquid Level",
        )
    )

    # --------------------------------------------------------
    # SHAFT
    # --------------------------------------------------------

    shaft_r = max(
        D * 0.015,
        0.02,
    )

    shaft_theta = np.linspace(
        0,
        2 * np.pi,
        20,
    )

    shaft_z = np.linspace(
        0,
        total_height,
        20,
    )

    shaft_theta_grid, shaft_z_grid = np.meshgrid(
        shaft_theta,
        shaft_z,
    )

    shaft_x = (
        shaft_r
        * np.cos(
            shaft_theta_grid
        )
    )

    shaft_y = (
        shaft_r
        * np.sin(
            shaft_theta_grid
        )
    )

    fig.add_trace(
        go.Surface(
            x=shaft_x,
            y=shaft_y,
            z=shaft_z_grid,
            opacity=0.9,
            showscale=False,
            name="Shaft",
        )
    )

    # --------------------------------------------------------
    # BAFFLES
    # --------------------------------------------------------

    baffles = int(
        reactor.get(
            "baffles",
            4,
        )
    )

    baffle_width = (
        reactor.get(
            "baffle_width",
            D * 1000 * 0.1,
        )
        / 1000.0
    )

    baffle_height = min(
        H,
        liquid_height,
    )

    for i in range(baffles):

        angle = (
            2
            * np.pi
            * i
            / max(
                baffles,
                1,
            )
        )

        x = np.array(
            [
                R * np.cos(angle),
                R * np.cos(angle),
            ]
        )

        y = np.array(
            [
                R * np.sin(angle),
                R * np.sin(angle),
            ]
        )

        z = np.array(
            [
                bottom_depth,
                bottom_depth
                + baffle_height,
            ]
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=8,
                ),
                showlegend=False,
            )
        )

    # --------------------------------------------------------
    # IMPELLERS
    # --------------------------------------------------------

    impeller_d = (
        reactor[
            "impeller_diameter"
        ]
        / 1000.0
    )

    number_impellers = int(
        reactor[
            "number_of_impellers"
        ]
    )

    clearance = (
        reactor[
            "impeller_clearance"
        ]
        / 1000.0
    )

    available_height = max(
        liquid_height
        - clearance,
        0.2,
    )

    if number_impellers == 1:

        elevations = [
            clearance
            + 0.35
            * available_height
        ]

    else:

        elevations = np.linspace(
            clearance
            + 0.20
            * available_height,
            clearance
            + 0.80
            * available_height,
            number_impellers,
        )

    for elevation in elevations:

        _add_impeller(
            fig,
            reactor[
                "impeller_type"
            ],
            impeller_d,
            elevation,
        )

    # --------------------------------------------------------
    # GAS SPARGER
    # --------------------------------------------------------

    if (
        reaction_type
        in [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
        ]
        and reactor.get(
            "gas_flow",
            0,
        )
        > 0
    ):

        sparger_r = (
            impeller_d
            * 0.65
        )

        sparger_x = (
            sparger_r
            * np.cos(theta)
        )

        sparger_y = (
            sparger_r
            * np.sin(theta)
        )

        sparger_z = np.full_like(
            theta,
            clearance * 0.6,
        )

        fig.add_trace(
            go.Scatter3d(
                x=sparger_x,
                y=sparger_y,
                z=sparger_z,
                mode="lines",
                line=dict(
                    width=6,
                ),
                name="Gas Sparger",
            )
        )

    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    fig.update_layout(
        title=(
            f"{reactor['impeller_type']} — "
            f"{reactor['bottom_type']} Bottom / "
            f"{reactor['top_type']} Top"
        ),

        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Height (m)",
            aspectmode="data",
        ),

        margin=dict(
            l=0,
            r=0,
            t=50,
            b=0,
        ),

        height=700,
    )

    return fig


# ============================================================
# IMPELLER
# ============================================================

def _add_impeller(
    fig,
    impeller_type,
    diameter,
    elevation,
):

    radius = diameter / 2.0

    theta = np.linspace(
        0,
        2 * np.pi,
        100,
    )

    # --------------------------------------------------------
    # RUSHTON
    # --------------------------------------------------------

    if impeller_type == "Rushton Turbine":

        for i in range(6):

            angle = (
                2
                * np.pi
                * i
                / 6
            )

            x = [
                0,
                radius
                * np.cos(angle),
            ]

            y = [
                0,
                radius
                * np.sin(angle),
            ]

            z = [
                elevation,
                elevation,
            ]

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=8,
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # PBT
    # --------------------------------------------------------

    if impeller_type == "Pitched Blade Turbine":

        for i in range(4):

            angle = (
                2
                * np.pi
                * i
                / 4
            )

            x = [
                0.05
                * radius
                * np.cos(angle),
                radius
                * np.cos(angle),
            ]

            y = [
                0.05
                * radius
                * np.sin(angle),
                radius
                * np.sin(angle),
            ]

            z = [
                elevation,
                elevation
                + 0.12
                * radius,
            ]

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=10,
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # HYDROFOIL
    # --------------------------------------------------------

    if impeller_type == "Hydrofoil":

        for i in range(3):

            angle = (
                2
                * np.pi
                * i
                / 3
            )

            r = np.linspace(
                0.10 * radius,
                radius,
                20,
            )

            x = (
                r
                * np.cos(angle)
            )

            y = (
                r
                * np.sin(angle)
            )

            z = (
                elevation
                + 0.15
                * r
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=10,
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # MARINE PROPELLER
    # --------------------------------------------------------

    if impeller_type == "Marine Propeller":

        for i in range(3):

            angle = (
                2
                * np.pi
                * i
                / 3
            )

            r = np.linspace(
                0.1 * radius,
                radius,
                30,
            )

            twist = (
                0.6
                * r
                / radius
            )

            x = (
                r
                * np.cos(
                    angle
                    + twist
                )
            )

            y = (
                r
                * np.sin(
                    angle
                    + twist
                )
            )

            z = (
                elevation
                + 0.15
                * np.sin(
                    np.pi
                    * r
                    / radius
                )
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=10,
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # ANCHOR
    # --------------------------------------------------------

    if impeller_type == "Anchor":

        z_bottom = (
            elevation
            - 0.35
            * radius
        )

        x = (
            radius
            * np.cos(theta)
        )

        y = (
            radius
            * np.sin(theta)
        )

        z = np.full_like(
            theta,
            z_bottom,
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=8,
                ),
                showlegend=False,
            )
        )

        for angle in [
            0,
            np.pi,
        ]:

            fig.add_trace(
                go.Scatter3d(
                    x=[
                        radius
                        * np.cos(angle),
                        radius
                        * np.cos(angle),
                    ],
                    y=[
                        radius
                        * np.sin(angle),
                        radius
                        * np.sin(angle),
                    ],
                    z=[
                        z_bottom,
                        elevation
                        + 0.4
                        * radius,
                    ],
                    mode="lines",
                    line=dict(
                        width=8,
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # HELICAL RIBBON
    # --------------------------------------------------------

    if impeller_type == "Helical Ribbon":

        helix_z = np.linspace(
            elevation
            - radius,
            elevation
            + radius,
            200,
        )

        helix_theta = np.linspace(
            0,
            4 * np.pi,
            200,
        )

        helix_x = (
            radius
            * 0.85
            * np.cos(
                helix_theta
            )
        )

        helix_y = (
            radius
            * 0.85
            * np.sin(
                helix_theta
            )
        )

        fig.add_trace(
            go.Scatter3d(
                x=helix_x,
                y=helix_y,
                z=helix_z,
                mode="lines",
                line=dict(
                    width=8,
                ),
                showlegend=False,
            )
        )

        return

    # --------------------------------------------------------
    # RCI
    # --------------------------------------------------------

    if (
        impeller_type
        == "Retreating Curve Impeller (RCI)"
    ):

        for i in range(2):

            offset = (
                i
                * np.pi
            )

            t = np.linspace(
                -np.pi / 2,
                np.pi / 2,
                100,
            )

            r = (
                radius
                * (
                    0.25
                    + 0.75
                    * (
                        np.cos(t)
                        ** 0.65
                    )
                )
            )

            x = (
                r
                * np.cos(
                    t
                    + offset
                )
            )

            y = (
                r
                * np.sin(
                    t
                    + offset
                )
            )

            z = (
                elevation
                + 0.12
                * radius
                * np.sin(t)
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=10,
                    ),
                    showlegend=False,
                )
            )
