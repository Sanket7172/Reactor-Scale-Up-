import math

import numpy as np
import plotly.graph_objects as go


# ============================================================
# SAFE HELPERS
# ============================================================

def _safe_float(value, default=0.0):

    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


# ============================================================
# COORDINATE ROTATION
# ============================================================

def _rotate_xy(
    x,
    y,
    angle,
):
    ca = math.cos(angle)
    sa = math.sin(angle)

    return (
        x * ca - y * sa,
        x * sa + y * ca,
    )


# ============================================================
# CYLINDER
# ============================================================

def _cylinder_surface(
    radius,
    z_bottom,
    z_top,
    n=40,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        n,
    )

    z = np.array(
        [
            z_bottom,
            z_top,
        ]
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z,
    )

    x = radius * np.cos(
        theta_grid
    )

    y = radius * np.sin(
        theta_grid
    )

    return x, y, z_grid


# ============================================================
# VESSEL HEAD
# ============================================================

def _ellipsoidal_head(
    radius,
    center_z,
    depth,
    top=True,
    n_theta=50,
    n_phi=20,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        n_theta,
    )

    phi = np.linspace(
        0,
        math.pi / 2,
        n_phi,
    )

    theta_grid, phi_grid = np.meshgrid(
        theta,
        phi,
    )

    x = radius * np.sin(
        phi_grid
    ) * np.cos(
        theta_grid
    )

    y = radius * np.sin(
        phi_grid
    ) * np.sin(
        theta_grid
    )

    if top:

        z = (
            center_z
            + depth * np.cos(
                phi_grid
            )
        )

    else:

        z = (
            center_z
            - depth * np.cos(
                phi_grid
            )
        )

    return x, y, z


# ============================================================
# TORISPHERICAL-STYLE APPROXIMATION
# ============================================================

def _torispherical_head(
    radius,
    center_z,
    depth,
    top=True,
    n_theta=50,
    n_phi=20,
):

    theta = np.linspace(
        0,
        2 * math.pi,
        n_theta,
    )

    phi = np.linspace(
        0,
        math.pi / 2,
        n_phi,
    )

    theta_grid, phi_grid = np.meshgrid(
        theta,
        phi,
    )

    # Smooth approximation for visualization
    radial = radius * np.sin(
        phi_grid
    )

    x = radial * np.cos(
        theta_grid
    )

    y = radial * np.sin(
        theta_grid
    )

    profile = (
        0.72
        + 0.28
        * np.cos(phi_grid)
    )

    if top:

        z = (
            center_z
            + depth * profile
            * np.cos(phi_grid)
        )

    else:

        z = (
            center_z
            - depth * profile
            * np.cos(phi_grid)
        )

    return x, y, z


# ============================================================
# ADD VESSEL
# ============================================================

def _add_vessel(
    fig,
    D,
    straight_height,
    bottom_type,
    top_type,
    opacity=0.22,
):

    radius = D / 2.0

    # --------------------------------------------------------
    # CYLINDRICAL SHELL
    # --------------------------------------------------------

    x, y, z = _cylinder_surface(
        radius,
        0.0,
        straight_height,
        60,
    )

    fig.add_surface(
        x=x,
        y=y,
        z=z,
        opacity=opacity,
        showscale=False,
        hoverinfo="skip",
        name="Reactor Shell",
    )

    # --------------------------------------------------------
    # HEAD DEPTH
    # --------------------------------------------------------

    bottom_name = str(
        bottom_type
    ).lower()

    top_name = str(
        top_type
    ).lower()

    if "ellipsoidal" in bottom_name:

        depth = radius / 2.0

        x, y, z = _ellipsoidal_head(
            radius,
            0.0,
            depth,
            top=False,
        )

        fig.add_surface(
            x=x,
            y=y,
            z=z,
            opacity=opacity,
            showscale=False,
            hoverinfo="skip",
            name="Bottom Head",
        )

    elif "torispherical" in bottom_name:

        depth = radius * 0.20

        x, y, z = _torispherical_head(
            radius,
            0.0,
            depth,
            top=False,
        )

        fig.add_surface(
            x=x,
            y=y,
            z=z,
            opacity=opacity,
            showscale=False,
            hoverinfo="skip",
            name="Bottom Head",
        )

    if "ellipsoidal" in top_name:

        depth = radius / 2.0

        x, y, z = _ellipsoidal_head(
            radius,
            straight_height,
            depth,
            top=True,
        )

        fig.add_surface(
            x=x,
            y=y,
            z=z,
            opacity=opacity,
            showscale=False,
            hoverinfo="skip",
            name="Top Head",
        )

    elif "torispherical" in top_name:

        depth = radius * 0.20

        x, y, z = _torispherical_head(
            radius,
            straight_height,
            depth,
            top=True,
        )

        fig.add_surface(
            x=x,
            y=y,
            z=z,
            opacity=opacity,
            showscale=False,
            hoverinfo="skip",
            name="Top Head",
        )


# ============================================================
# LIQUID
# ============================================================

def _add_liquid(
    fig,
    D,
    liquid_height,
    opacity=0.30,
):

    radius = D / 2.0

    theta = np.linspace(
        0,
        2 * math.pi,
        60,
    )

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = np.full_like(
        theta,
        liquid_height,
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            name="Liquid Level",
            line=dict(
                width=4,
            ),
            hoverinfo="skip",
        )
    )

    # Filled liquid cylinder
    z_values = np.linspace(
        0,
        liquid_height,
        12,
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z_values,
    )

    x_grid = radius * np.cos(
        theta_grid
    )

    y_grid = radius * np.sin(
        theta_grid
    )

    fig.add_surface(
        x=x_grid,
        y=y_grid,
        z=z_grid,
        opacity=opacity,
        showscale=False,
        hoverinfo="skip",
        name="Liquid",
    )


# ============================================================
# SHAFT
# ============================================================

def _add_shaft(
    fig,
    D,
    height,
):

    shaft_radius = max(
        0.025 * D,
        0.025,
    )

    theta = np.linspace(
        0,
        2 * math.pi,
        30,
    )

    z = np.linspace(
        -0.1 * D,
        height + 0.25 * D,
        20,
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z,
    )

    x = shaft_radius * np.cos(
        theta_grid
    )

    y = shaft_radius * np.sin(
        theta_grid
    )

    fig.add_surface(
        x=x,
        y=y,
        z=z_grid,
        showscale=False,
        opacity=0.95,
        hoverinfo="skip",
        name="Shaft",
    )


# ============================================================
# BAFFLES
# ============================================================

def _add_baffles(
    fig,
    D,
    height,
    number_baffles=4,
):

    number_baffles = max(
        0,
        number_baffles,
    )

    if number_baffles <= 0:
        return

    radius = D / 2.0

    baffle_width = 0.08 * D
    baffle_thickness = 0.025 * D

    z1 = 0.08 * height
    z2 = 0.92 * height

    for i in range(number_baffles):

        angle = (
            2
            * math.pi
            * i
            / number_baffles
        )

        # radial position
        r = radius - baffle_width / 2.0

        cx = r * math.cos(angle)
        cy = r * math.sin(angle)

        # Tangential direction
        tx = -math.sin(angle)
        ty = math.cos(angle)

        # Four corners
        half_w = baffle_width / 2.0
        half_t = baffle_thickness / 2.0

        corners = []

        for dz in [z1, z2]:

            for a, b in [
                (-half_w, -half_t),
                (half_w, -half_t),
                (half_w, half_t),
                (-half_w, half_t),
            ]:

                x = (
                    cx
                    + tx * a
                    + math.cos(angle) * b
                )

                y = (
                    cy
                    + ty * a
                    + math.sin(angle) * b
                )

                corners.append(
                    (x, y, dz)
                )

        # bottom rectangle
        for j in range(4):

            p1 = corners[j]
            p2 = corners[
                (j + 1) % 4
            ]

            fig.add_trace(
                go.Scatter3d(
                    x=[
                        p1[0],
                        p2[0],
                    ],
                    y=[
                        p1[1],
                        p2[1],
                    ],
                    z=[
                        p1[2],
                        p2[2],
                    ],
                    mode="lines",
                    line=dict(
                        width=5,
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # vertical edges
        for j in range(4):

            p1 = corners[j]
            p2 = corners[j + 4]

            fig.add_trace(
                go.Scatter3d(
                    x=[
                        p1[0],
                        p2[0],
                    ],
                    y=[
                        p1[1],
                        p2[1],
                    ],
                    z=[
                        p1[2],
                        p2[2],
                    ],
                    mode="lines",
                    line=dict(
                        width=5,
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )


# ============================================================
# ANCHOR
# ============================================================

def _anchor_impeller(
    D,
    z,
    angle,
):

    radius = D / 2.0

    # Anchor arms
    theta = np.linspace(
        0,
        2 * math.pi,
        80,
    )

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)

    points = []

    for px, py in zip(x, y):

        rx, ry = _rotate_xy(
            px,
            py,
            angle,
        )

        points.append(
            (
                rx,
                ry,
                z,
            )
        )

    return points


# ============================================================
# RUSHTON
# ============================================================

def _rushton_impeller(
    D,
    z,
    angle,
):

    radius = D / 2.0

    points = []

    # six blades
    blades = 6

    hub_radius = 0.10 * D

    for i in range(blades):

        a = (
            angle
            + 2
            * math.pi
            * i
            / blades
        )

        a2 = a + math.radians(18)

        r1 = hub_radius
        r2 = radius

        p1 = (
            r1 * math.cos(a),
            r1 * math.sin(a),
            z,
        )

        p2 = (
            r2 * math.cos(a),
            r2 * math.sin(a),
            z,
        )

        p3 = (
            r2 * math.cos(a2),
            r2 * math.sin(a2),
            z,
        )

        points.extend(
            [
                p1,
                p2,
                p3,
                p1,
            ]
        )

    return points


# ============================================================
# PBT
# ============================================================

def _pbt_impeller(
    D,
    z,
    angle,
):

    radius = D / 2.0

    blades = 4

    points = []

    hub = 0.10 * D

    for i in range(blades):

        a = (
            angle
            + 2
            * math.pi
            * i
            / blades
        )

        # angled blade line
        r1 = hub
        r2 = radius

        x1 = r1 * math.cos(a)
        y1 = r1 * math.sin(a)

        x2 = r2 * math.cos(a)
        y2 = r2 * math.sin(a)

        points.extend(
            [
                (
                    x1,
                    y1,
                    z,
                ),
                (
                    x2,
                    y2,
                    z,
                ),
            ]
        )

    return points


# ============================================================
# HYDROFOIL
# ============================================================

def _hydrofoil_impeller(
    D,
    z,
    angle,
):

    radius = D / 2.0

    blades = 3

    points = []

    for i in range(blades):

        a = (
            angle
            + 2
            * math.pi
            * i
            / blades
        )

        r1 = 0.12 * D
        r2 = radius

        # curved blade approximation
        for frac in np.linspace(
            0,
            1,
            8,
        ):

            r = (
                r1
                + frac
                * (
                    r2
                    - r1
                )
            )

            local_angle = (
                a
                + math.radians(
                    20
                    * frac
                )
            )

            x = r * math.cos(
                local_angle
            )

            y = r * math.sin(
                local_angle
            )

            points.append(
                (
                    x,
                    y,
                    z,
                )
            )

    return points


# ============================================================
# MARINE PROPELLER
# ============================================================

def _marine_propeller(
    D,
    z,
    angle,
):

    radius = D / 2.0

    blades = 3

    points = []

    for i in range(blades):

        a = (
            angle
            + 2
            * math.pi
            * i
            / blades
        )

        for frac in np.linspace(
            0.1,
            1.0,
            12,
        ):

            r = (
                frac
                * radius
            )

            local_angle = (
                a
                + math.radians(
                    35
                    * (
                        1
                        - frac
                    )
                )
            )

            points.append(
                (
                    r * math.cos(
                        local_angle
                    ),
                    r * math.sin(
                        local_angle
                    ),
                    z,
                )
            )

    return points


# ============================================================
# HELICAL RIBBON
# ============================================================

def _helical_ribbon(
    D,
    z,
    angle,
):

    radius = D / 2.0

    points = []

    turns = 0.8

    theta = np.linspace(
        0,
        2 * math.pi * turns,
        100,
    )

    vertical_span = 0.35 * D

    for t in theta:

        local_angle = (
            angle + t
        )

        x = radius * math.cos(
            local_angle
        )

        y = radius * math.sin(
            local_angle
        )

        zz = (
            z
            - vertical_span / 2
            + vertical_span
            * t
            / (
                2
                * math.pi
                * turns
            )
        )

        points.append(
            (
                x,
                y,
                zz,
            )
        )

    return points


# ============================================================
# RCI
# ============================================================

def _rci_impeller(
    D,
    z,
    angle,
):

    radius = D / 2.0

    blades = 6

    points = []

    for i in range(blades):

        a = (
            angle
            + 2
            * math.pi
            * i
            / blades
        )

        r1 = 0.12 * D
        r2 = radius

        points.extend(
            [
                (
                    r1 * math.cos(a),
                    r1 * math.sin(a),
                    z,
                ),
                (
                    r2 * math.cos(a),
                    r2 * math.sin(a),
                    z,
                ),
            ]
        )

    return points


# ============================================================
# CREATE IMPELLER
# ============================================================

def _create_impeller_geometry(
    agitator_type,
    D,
    z,
    angle,
):

    name = str(
        agitator_type
    ).lower()

    if (
        "anchor"
        in name
    ):

        return _anchor_impeller(
            D,
            z,
            angle,
        )

    if (
        "rushton"
        in name
        or "disk"
        in name
    ):

        return _rushton_impeller(
            D,
            z,
            angle,
        )

    if (
        "pbt"
        in name
        or "pitched"
        in name
    ):

        return _pbt_impeller(
            D,
            z,
            angle,
        )

    if (
        "hydrofoil"
        in name
    ):

        return _hydrofoil_impeller(
            D,
            z,
            angle,
        )

    if (
        "marine"
        in name
        or "propeller"
        in name
    ):

        return _marine_propeller(
            D,
            z,
            angle,
        )

    if (
        "helical"
        in name
        or "ribbon"
        in name
    ):

        return _helical_ribbon(
            D,
            z,
            angle,
        )

    if (
        "rci"
        in name
    ):

        return _rci_impeller(
            D,
            z,
            angle,
        )

    # Default
    return _pbt_impeller(
        D,
        z,
        angle,
    )


# ============================================================
# ADD IMPELLER
# ============================================================

def _add_impeller(
    fig,
    impeller,
    angle=0.0,
    frame_name=None,
):

    D = _safe_float(
        impeller.get(
            "diameter_m",
            impeller.get("D"),
        ),
        0.5,
    )

    z = _safe_float(
        impeller.get(
            "elevation_m"
        ),
        0.5,
    )

    agitator = impeller.get(
        "agitator_type",
        impeller.get(
            "type",
            "PBT",
        ),
    )

    points = _create_impeller_geometry(
        agitator,
        D,
        z,
        angle,
    )

    if not points:
        return

    x = [
        p[0]
        for p in points
    ]

    y = [
        p[1]
        for p in points
    ]

    z_values = [
        p[2]
        for p in points
    ]

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z_values,
            mode="lines",
            line=dict(
                width=8,
            ),
            name=(
                f"{agitator} "
                f"Impeller"
            ),
            legendgroup=(
                f"impeller_{id(impeller)}"
            ),
            showlegend=(
                frame_name is None
            ),
            hovertemplate=(
                f"{agitator}<br>"
                f"D = {D:.3f} m"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# DIMENSION LINE
# ============================================================

def _add_dimension(
    fig,
    x1,
    y1,
    z1,
    x2,
    y2,
    z2,
    label,
):

    fig.add_trace(
        go.Scatter3d(
            x=[x1, x2],
            y=[y1, y2],
            z=[z1, z2],
            mode="lines+text",
            line=dict(
                width=3,
            ),
            text=[
                "",
                label,
            ],
            textposition="middle center",
            showlegend=False,
            hoverinfo="skip",
        )
    )


# ============================================================
# TOP NOZZLE
# ============================================================

def _add_top_nozzle(
    fig,
    D,
    height,
):

    radius = 0.10 * D

    theta = np.linspace(
        0,
        2 * math.pi,
        30,
    )

    z = np.array(
        [
            height,
            height + 0.25 * D,
        ]
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z,
    )

    x = radius * np.cos(
        theta_grid
    )

    y = radius * np.sin(
        theta_grid
    )

    fig.add_surface(
        x=x,
        y=y,
        z=z_grid,
        showscale=False,
        opacity=0.75,
        hoverinfo="skip",
        name="Top Nozzle",
    )


# ============================================================
# BOTTOM OUTLET
# ============================================================

def _add_bottom_outlet(
    fig,
    D,
):

    radius = 0.075 * D

    theta = np.linspace(
        0,
        2 * math.pi,
        30,
    )

    z = np.array(
        [
            -0.25 * D,
            0.0,
        ]
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z,
    )

    x = radius * np.cos(
        theta_grid
    )

    y = radius * np.sin(
        theta_grid
    )

    fig.add_surface(
        x=x,
        y=y,
        z=z_grid,
        showscale=False,
        opacity=0.80,
        hoverinfo="skip",
        name="Bottom Outlet",
    )


# ============================================================
# MIXING TRACERS
# ============================================================

def _create_tracers(
    D,
    liquid_height,
    count=80,
):

    radius = 0.40 * D

    rng = np.random.default_rng(
        42
    )

    theta = rng.uniform(
        0,
        2 * math.pi,
        count,
    )

    r = np.sqrt(
        rng.uniform(
            0,
            1,
            count,
        )
    ) * radius

    x = r * np.cos(theta)
    y = r * np.sin(theta)

    z = rng.uniform(
        0.05 * liquid_height,
        0.95 * liquid_height,
        count,
    )

    return x, y, z


# ============================================================
# MAIN 3D FUNCTION
# ============================================================

def create_reactor_animation(
    D,
    straight_height,
    bottom_type="2:1 Ellipsoidal",
    top_type="2:1 Ellipsoidal",
    liquid_height=None,
    impellers=None,
    rpm=100.0,
    number_baffles=4,
    frames_count=36,
    show_dimensions=True,
    show_nozzles=True,
    show_tracers=True,
    show_baffles=True,
    vessel_opacity=0.22,
):

    D = _safe_float(
        D,
        2.0,
    )

    straight_height = _safe_float(
        straight_height,
        3.0,
    )

    rpm = _safe_float(
        rpm,
        100.0,
    )

    number_baffles = _safe_int(
        number_baffles,
        4,
    )

    frames_count = max(
        12,
        _safe_int(
            frames_count,
            36,
        ),
    )

    if liquid_height is None:

        liquid_height = (
            0.70
            * straight_height
        )

    liquid_height = max(
        0.05,
        min(
            _safe_float(
                liquid_height,
                straight_height * 0.7,
            ),
            straight_height,
        ),
    )

    if not impellers:

        impellers = [
            {
                "position": "Bottom",
                "agitator_type": "PBT",
                "diameter_m": 0.5 * D,
                "bottom_clearance_m": 0.2 * D,
                "elevation_m": 0.2 * D,
            }
        ]

    # ========================================================
    # BASE FIGURE
    # ========================================================

    fig = go.Figure()

    # Vessel
    _add_vessel(
        fig,
        D,
        straight_height,
        bottom_type,
        top_type,
        opacity=vessel_opacity,
    )

    # Liquid
    _add_liquid(
        fig,
        D,
        liquid_height,
    )

    # Shaft
    _add_shaft(
        fig,
        D,
        straight_height,
    )

    # Baffles
    if show_baffles:

        _add_baffles(
            fig,
            D,
            straight_height,
            number_baffles,
        )

    # Nozzles
    if show_nozzles:

        _add_top_nozzle(
            fig,
            D,
            straight_height,
        )

        _add_bottom_outlet(
            fig,
            D,
        )

    # Dimensions
    if show_dimensions:

        _add_dimension(
            fig,
            D / 2.0 + 0.15 * D,
            0,
            0,
            D / 2.0 + 0.15 * D,
            0,
            straight_height,
            f"H = {straight_height:.2f} m",
        )

        _add_dimension(
            fig,
            -D / 2.0,
            -0.15 * D,
            0,
            D / 2.0,
            -0.15 * D,
            0,
            f"D = {D:.2f} m",
        )

        _add_dimension(
            fig,
            D / 2.0 + 0.30 * D,
            0,
            0,
            D / 2.0 + 0.30 * D,
            0,
            liquid_height,
            f"Liquid = {liquid_height:.2f} m",
        )

    # ========================================================
    # TRACERS
    # ========================================================

    tracer_x = None
    tracer_y = None
    tracer_z = None

    if show_tracers:

        tracer_x, tracer_y, tracer_z = (
            _create_tracers(
                D,
                liquid_height,
                count=70,
            )
        )

        fig.add_trace(
            go.Scatter3d(
                x=tracer_x,
                y=tracer_y,
                z=tracer_z,
                mode="markers",
                marker=dict(
                    size=3,
                ),
                name="Mixing Tracers",
            )
        )

    # ========================================================
    # INITIAL IMPELLERS
    # ========================================================

    for impeller in impellers:

        _add_impeller(
            fig,
            impeller,
            angle=0.0,
        )

    # ========================================================
    # ANIMATION FRAMES
    # ========================================================

    frames = []

    for frame_index in range(
        frames_count
    ):

        angle = (
            2
            * math.pi
            * frame_index
            / frames_count
        )

        # ----------------------------------------------------
        # Calculate total number of traces in static figure
        # ----------------------------------------------------

        frame_data = []

        # The order of dynamic traces must match the initial
        # traces that are replaced by the frame.
        #
        # We construct a complete frame with:
        # impellers + tracers.
        #

        for impeller in impellers:

            D_imp = _safe_float(
                impeller.get(
                    "diameter_m",
                    impeller.get("D"),
                ),
                0.5 * D,
            )

            z_imp = _safe_float(
                impeller.get(
                    "elevation_m"
                ),
                0.2 * D,
            )

            agitator = impeller.get(
                "agitator_type",
                impeller.get(
                    "type",
                    "PBT",
                ),
            )

            points = _create_impeller_geometry(
                agitator,
                D_imp,
                z_imp,
                angle,
            )

            x = [
                p[0]
                for p in points
            ]

            y = [
                p[1]
                for p in points
            ]

            z = [
                p[2]
                for p in points
            ]

            frame_data.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                )
            )

        # ----------------------------------------------------
        # TRACER ROTATION
        # ----------------------------------------------------

        if show_tracers:

            ca = math.cos(
                0.5 * angle
            )

            sa = math.sin(
                0.5 * angle
            )

            tx = (
                tracer_x * ca
                - tracer_y * sa
            )

            ty = (
                tracer_x * sa
                + tracer_y * ca
            )

            frame_data.append(
                go.Scatter3d(
                    x=tx,
                    y=ty,
                    z=tracer_z,
                    mode="markers",
                )
            )

        frames.append(
            go.Frame(
                data=frame_data,
                name=f"frame_{frame_index}",
            )
        )

    fig.frames = frames

    # ========================================================
    # ANIMATION CONTROL
    # ========================================================

    frame_duration = max(
        30,
        int(
            60000
            / max(
                rpm * frames_count,
                1,
            )
        ),
    )

    fig.update_layout(
        title=(
            "Interactive Reactor 3D Model"
        ),

        scene=dict(

            xaxis=dict(
                title="X (m)",
                showbackground=True,
                zeroline=False,
            ),

            yaxis=dict(
                title="Y (m)",
                showbackground=True,
                zeroline=False,
            ),

            zaxis=dict(
                title="Elevation (m)",
                showbackground=True,
                zeroline=False,
            ),

            aspectmode="data",

            camera=dict(
                eye=dict(
                    x=1.7,
                    y=1.7,
                    z=1.2,
                )
            ),
        ),

        height=750,

        margin=dict(
            l=0,
            r=0,
            t=50,
            b=0,
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),

        updatemenus=[
            {
                "type": "buttons",
                "showactive": True,
                "x": 0.05,
                "y": 0.02,
                "xanchor": "left",
                "yanchor": "bottom",
                "buttons": [

                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": frame_duration,
                                    "redraw": True,
                                },
                                "fromcurrent": True,
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
                            [
                                None
                            ],
                            {
                                "frame": {
                                    "duration": 0,
                                    "redraw": False,
                                },
                                "mode": "immediate",
                                "transition": {
                                    "duration": 0,
                                },
                            },
                        ],
                    },

                ],
            }
        ],

        sliders=[
            {
                "active": 0,
                "x": 0.25,
                "y": 0.02,
                "len": 0.65,
                "xanchor": "left",
                "yanchor": "bottom",
                "currentvalue": {
                    "prefix": "Rotation: ",
                },
                "steps": [

                    {
                        "label": str(i),
                        "method": "animate",
                        "args": [
                            [
                                f"frame_{i}"
                            ],
                            {
                                "mode": "immediate",
                                "frame": {
                                    "duration": 0,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 0,
                                },
                            },
                        ],
                    }

                    for i in range(
                        frames_count
                    )
                ],
            }
        ],
    )

    return fig


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def create_reactor_3d(**kwargs):

    return create_reactor_animation(
        **kwargs
    )
