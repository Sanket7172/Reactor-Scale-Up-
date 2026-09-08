import math
import numpy as np
import plotly.graph_objects as go


# ============================================================
# VISUALIZATION LAYERS
# ============================================================

VISUALIZATION_FEATURES = [
    "Reactor Geometry",
    "Liquid Level",
    "Impeller & Shaft",
    "Baffles",
    "Vortex Formation",
    "Velocity Profile",
    "Flow Profile",
    "Dead Zone Analysis",
    "Mixing Particles",
    "Gas-Liquid Bubbles",
    "Dimensions",
]


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))


def _get_value(dictionary, keys, default=None):
    if not isinstance(dictionary, dict):
        return default

    for key in keys:
        if key in dictionary:
            return dictionary[key]

    return default


# ============================================================
# IMPeller NORMALIZATION
# ============================================================

def _normalize_impellers(
    impellers=None,
    agitator=None,
    impeller_diameter_m=None,
    number_impellers=1,
    impeller_clearance_m=0.4,
    liquid_height_m=3.0,
):
    """
    Normalize all impeller input formats into a common structure.
    """

    normalized = []

    if isinstance(impellers, list) and impellers:

        for index, item in enumerate(impellers):

            if not isinstance(item, dict):
                continue

            position = item.get(
                "position",
                "Bottom" if index == 0 else "Middle",
            )

            agitator_type = item.get(
                "agitator_type",
                item.get(
                    "type",
                    agitator or "Rushton Turbine",
                ),
            )

            diameter = _safe_float(
                item.get(
                    "diameter_m",
                    item.get(
                        "D",
                        impeller_diameter_m or 1.0,
                    ),
                ),
                1.0,
            )

            clearance = _safe_float(
                item.get(
                    "bottom_clearance_m",
                    impeller_clearance_m,
                ),
                impeller_clearance_m,
            )

            elevation = item.get(
                "elevation_m",
                None,
            )

            if elevation is None:

                H = max(
                    0.10,
                    liquid_height_m,
                )

                if position == "Bottom":
                    elevation = clearance

                elif position == "Middle":
                    elevation = 0.50 * H

                else:
                    elevation = 0.75 * H

            normalized.append(
                {
                    "position": position,
                    "agitator_type": agitator_type,
                    "diameter_m": diameter,
                    "bottom_clearance_m": clearance,
                    "elevation_m": _safe_float(
                        elevation,
                        clearance,
                    ),
                }
            )

    else:

        count = max(
            1,
            _safe_int(
                number_impellers,
                1,
            ),
        )

        H = max(
            0.10,
            liquid_height_m,
        )

        D = _safe_float(
            impeller_diameter_m,
            1.0,
        )

        C = _safe_float(
            impeller_clearance_m,
            0.4,
        )

        for index in range(count):

            if index == 0:
                position = "Bottom"
                elevation = C

            elif index == 1:
                position = "Middle"
                elevation = 0.50 * H

            else:
                position = "Top"
                elevation = 0.75 * H

            normalized.append(
                {
                    "position": position,
                    "agitator_type": (
                        agitator or "Rushton Turbine"
                    ),
                    "diameter_m": D,
                    "bottom_clearance_m": C,
                    "elevation_m": elevation,
                }
            )

    normalized.sort(
        key=lambda x: x["elevation_m"]
    )

    return normalized


# ============================================================
# GEOMETRY
# ============================================================

def _head_depth(
    diameter,
    head_type,
):
    D = max(
        0.01,
        diameter,
    )

    text = str(
        head_type or ""
    ).lower()

    if "flat" in text:
        return 0.0

    if "ellipsoid" in text:
        return D / 4.0

    if "torispherical" in text:
        return 0.20 * D

    return 0.20 * D


def _cylinder_surface(
    radius,
    z0,
    z1,
    nr=40,
    nz=18,
):

    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        nr,
    )

    z = np.linspace(
        z0,
        z1,
        nz,
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


def _ellipsoidal_head(
    radius,
    z_center,
    depth,
    top=True,
    nr=40,
    nz=16,
):

    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        nr,
    )

    phi = np.linspace(
        0.0,
        np.pi / 2.0,
        nz,
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
            z_center
            + depth * np.cos(
                phi_grid
            )
        )

    else:

        z = (
            z_center
            - depth * np.cos(
                phi_grid
            )
        )

    return x, y, z


def _torispherical_head(
    radius,
    z_tangent,
    depth,
    top=True,
    nr=40,
    nz=18,
):
    """
    Smooth engineering approximation of a torispherical head.
    """

    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        nr,
    )

    u = np.linspace(
        0.0,
        1.0,
        nz,
    )

    theta_grid, u_grid = np.meshgrid(
        theta,
        u,
    )

    radial_factor = (
        np.sin(
            0.5 * np.pi * u_grid
        ) ** 0.92
    )

    x = (
        radius
        * radial_factor
        * np.cos(theta_grid)
    )

    y = (
        radius
        * radial_factor
        * np.sin(theta_grid)
    )

    depth_profile = (
        1.0
        - np.cos(
            0.5 * np.pi * u_grid
        )
    )

    z_offset = depth * depth_profile

    if top:

        z = z_tangent + z_offset

    else:

        z = z_tangent - z_offset

    return x, y, z


def _add_vessel_shell(
    fig,
    diameter,
    straight_height,
    bottom_type,
    top_type,
):
    """
    Add realistic transparent reactor vessel.
    """

    D = max(
        0.10,
        diameter,
    )

    R = D / 2.0

    H = max(
        0.10,
        straight_height,
    )

    bottom_depth = _head_depth(
        D,
        bottom_type,
    )

    top_depth = _head_depth(
        D,
        top_type,
    )

    shell_bottom = bottom_depth

    shell_top = (
        bottom_depth
        + H
    )

    # --------------------------------------------------------
    # Cylindrical shell
    # --------------------------------------------------------

    x, y, z = _cylinder_surface(
        R,
        shell_bottom,
        shell_top,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.20,
            showscale=False,
            hoverinfo="skip",
            name="Reactor Shell",
        )
    )

    # --------------------------------------------------------
    # Bottom head
    # --------------------------------------------------------

    if "ellipsoid" in str(
        bottom_type
    ).lower():

        x, y, z = _ellipsoidal_head(
            R,
            shell_bottom,
            bottom_depth,
            top=False,
        )

    elif "torispherical" in str(
        bottom_type
    ).lower():

        x, y, z = _torispherical_head(
            R,
            shell_bottom,
            bottom_depth,
            top=False,
        )

    else:

        x, y, z = _cylinder_surface(
            R,
            0.0,
            0.001,
        )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.20,
            showscale=False,
            hoverinfo="skip",
            name="Bottom Head",
        )
    )

    # --------------------------------------------------------
    # Top head
    # --------------------------------------------------------

    if "ellipsoid" in str(
        top_type
    ).lower():

        x, y, z = _ellipsoidal_head(
            R,
            shell_top,
            top_depth,
            top=True,
        )

    elif "torispherical" in str(
        top_type
    ).lower():

        x, y, z = _torispherical_head(
            R,
            shell_top,
            top_depth,
            top=True,
        )

    else:

        x, y, z = _cylinder_surface(
            R,
            shell_top,
            shell_top + 0.001,
        )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.20,
            showscale=False,
            hoverinfo="skip",
            name="Top Head",
        )
    )

    # --------------------------------------------------------
    # Bottom tangent ring
    # --------------------------------------------------------

    theta = np.linspace(
        0,
        2 * np.pi,
        100,
    )

    fig.add_trace(
        go.Scatter3d(
            x=R * np.cos(theta),
            y=R * np.sin(theta),
            z=np.full_like(
                theta,
                shell_bottom,
            ),
            mode="lines",
            line=dict(
                width=5,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # --------------------------------------------------------
    # Top tangent ring
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter3d(
            x=R * np.cos(theta),
            y=R * np.sin(theta),
            z=np.full_like(
                theta,
                shell_top,
            ),
            mode="lines",
            line=dict(
                width=5,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    return {
        "radius": R,
        "shell_bottom": shell_bottom,
        "shell_top": shell_top,
        "bottom_depth": bottom_depth,
        "top_depth": top_depth,
        "total_height": (
            bottom_depth
            + H
            + top_depth
        ),
    }


# ============================================================
# LIQUID
# ============================================================

def _liquid_level_from_volume(
    volume_m3,
    diameter_m,
    straight_height_m,
    bottom_depth,
    top_depth,
):

    V = max(
        0.0,
        _safe_float(volume_m3),
    )

    D = max(
        0.10,
        _safe_float(diameter_m),
    )

    R = D / 2.0

    shell_area = (
        math.pi * R**2
    )

    if shell_area <= 0:
        return bottom_depth

    straight_capacity = (
        shell_area
        * straight_height_m
    )

    if V <= straight_capacity:

        return (
            bottom_depth
            + V / shell_area
        )

    remaining = (
        V
        - straight_capacity
    )

    additional = min(
        top_depth,
        remaining / shell_area,
    )

    return (
        bottom_depth
        + straight_height_m
        + additional
    )


def _add_liquid(
    fig,
    diameter,
    level,
    shell_bottom,
    shell_top,
    color_opacity=0.28,
):
    R = diameter / 2.0

    theta = np.linspace(
        0,
        2 * np.pi,
        80,
    )

    z = np.full_like(
        theta,
        level,
    )

    fig.add_trace(
        go.Mesh3d(
            x=[
                0,
                *(
                    R * np.cos(theta)
                ),
            ],
            y=[
                0,
                *(
                    R * np.sin(theta)
                ),
            ],
            z=[
                level,
                *z,
            ],
            opacity=color_opacity,
            alphahull=0,
            hoverinfo="skip",
            name="Liquid",
            showlegend=True,
        )
    )

    # Liquid surface ring

    fig.add_trace(
        go.Scatter3d(
            x=R * np.cos(theta),
            y=R * np.sin(theta),
            z=z,
            mode="lines",
            line=dict(
                width=4,
            ),
            name="Liquid Surface",
        )
    )


# ============================================================
# BAFFLES
# ============================================================

def _add_baffles(
    fig,
    diameter,
    shell_bottom,
    shell_top,
    number_baffles,
):

    count = max(
        0,
        _safe_int(
            number_baffles,
            4,
        ),
    )

    if count <= 0:
        return

    R = diameter / 2.0

    radial_angle = np.linspace(
        0,
        2 * np.pi,
        count,
        endpoint=False,
    )

    baffle_width = max(
        0.08 * diameter,
        0.10,
    )

    baffle_thickness = max(
        0.025 * diameter,
        0.025,
    )

    z0 = shell_bottom + 0.10 * (
        shell_top - shell_bottom
    )

    z1 = shell_bottom + 0.90 * (
        shell_top - shell_bottom
    )

    for i, angle in enumerate(
        radial_angle
    ):

        # Local rectangular baffle
        local_x = np.array(
            [
                R - baffle_thickness,
                R,
                R,
                R - baffle_thickness,
                R - baffle_thickness,
                R,
                R,
                R - baffle_thickness,
            ]
        )

        local_y = np.array(
            [
                -baffle_width / 2,
                -baffle_width / 2,
                baffle_width / 2,
                baffle_width / 2,
                -baffle_width / 2,
                -baffle_width / 2,
                baffle_width / 2,
                baffle_width / 2,
            ]
        )

        local_z = np.array(
            [
                z0,
                z0,
                z0,
                z0,
                z1,
                z1,
                z1,
                z1,
            ]
        )

        x = (
            local_x * np.cos(angle)
            - local_y * np.sin(angle)
        )

        y = (
            local_x * np.sin(angle)
            + local_y * np.cos(angle)
        )

        fig.add_trace(
            go.Mesh3d(
                x=x,
                y=y,
                z=local_z,
                i=[
                    0,
                    0,
                    4,
                    4,
                    0,
                    1,
                ],
                j=[
                    1,
                    2,
                    5,
                    6,
                    4,
                    5,
                ],
                k=[
                    2,
                    3,
                    6,
                    7,
                    5,
                    1,
                ],
                opacity=0.75,
                hoverinfo="skip",
                name=(
                    "Baffles"
                    if i == 0
                    else None
                ),
                showlegend=(i == 0),
            )
        )


# ============================================================
# CYLINDER
# ============================================================

def _add_cylinder(
    fig,
    radius,
    z0,
    z1,
    name,
    opacity=1.0,
    sides=48,
):

    x, y, z = _cylinder_surface(
        radius,
        z0,
        z1,
        nr=sides,
        nz=8,
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=opacity,
            showscale=False,
            hoverinfo="skip",
            name=name,
        )
    )


# ============================================================
# SHAFT
# ============================================================

def _add_shaft(
    fig,
    shaft_radius,
    z_bottom,
    z_top,
):

    _add_cylinder(
        fig,
        shaft_radius,
        z_bottom,
        z_top,
        "Shaft",
        opacity=0.95,
        sides=32,
    )


# ============================================================
# FLANGE
# ============================================================

def _add_flange(
    fig,
    radius,
    z,
    thickness,
):

    theta = np.linspace(
        0,
        2 * np.pi,
        80,
    )

    r_outer = radius
    r_inner = radius * 0.72

    for z_value in [
        z,
        z + thickness,
    ]:

        fig.add_trace(
            go.Scatter3d(
                x=r_outer * np.cos(theta),
                y=r_outer * np.sin(theta),
                z=np.full_like(
                    theta,
                    z_value,
                ),
                mode="lines",
                line=dict(
                    width=5,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter3d(
                x=r_inner * np.cos(theta),
                y=r_inner * np.sin(theta),
                z=np.full_like(
                    theta,
                    z_value,
                ),
                mode="lines",
                line=dict(
                    width=4,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )


# ============================================================
# MOTOR + GEARBOX
# ============================================================

def _add_drive(
    fig,
    reactor_radius,
    shell_top,
    total_height,
):

    # Gearbox

    gearbox_radius = 0.23 * reactor_radius

    gearbox_bottom = (
        shell_top
        + 0.08 * total_height
    )

    gearbox_top = (
        gearbox_bottom
        + 0.14 * total_height
    )

    _add_cylinder(
        fig,
        gearbox_radius,
        gearbox_bottom,
        gearbox_top,
        "Gearbox",
        opacity=0.95,
        sides=36,
    )

    # Motor

    motor_radius = (
        0.30 * reactor_radius
    )

    motor_bottom = (
        gearbox_top
        + 0.04 * total_height
    )

    motor_top = (
        motor_bottom
        + 0.22 * total_height
    )

    _add_cylinder(
        fig,
        motor_radius,
        motor_bottom,
        motor_top,
        "Drive Motor",
        opacity=0.95,
        sides=36,
    )

    # Motor top cap

    theta = np.linspace(
        0,
        2 * np.pi,
        60,
    )

    fig.add_trace(
        go.Scatter3d(
            x=motor_radius * np.cos(theta),
            y=motor_radius * np.sin(theta),
            z=np.full_like(
                theta,
                motor_top,
            ),
            mode="lines",
            line=dict(
                width=4,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Coupling

    coupling_bottom = (
        shell_top
        + 0.02 * total_height
    )

    coupling_top = (
        shell_top
        + 0.08 * total_height
    )

    _add_cylinder(
        fig,
        0.12 * reactor_radius,
        coupling_bottom,
        coupling_top,
        "Coupling",
        opacity=1.0,
        sides=32,
    )

    # Drive support plate

    plate_z = (
        shell_top
        + 0.015 * total_height
    )

    plate_radius = (
        0.48 * reactor_radius
    )

    fig.add_trace(
        go.Mesh3d(
            x=[
                -plate_radius,
                plate_radius,
                plate_radius,
                -plate_radius,
            ],
            y=[
                -plate_radius,
                -plate_radius,
                plate_radius,
                plate_radius,
            ],
            z=[
                plate_z,
                plate_z,
                plate_z,
                plate_z,
            ],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            opacity=0.9,
            hoverinfo="skip",
            name="Drive Support",
        )
    )


# ============================================================
# NOZZLES
# ============================================================

def _add_side_nozzle(
    fig,
    reactor_radius,
    z,
    angle,
    length,
    nozzle_radius,
    name,
):

    # Start close to vessel wall
    x0 = (
        reactor_radius
        * math.cos(angle)
    )

    y0 = (
        reactor_radius
        * math.sin(angle)
    )

    x1 = (
        (reactor_radius + length)
        * math.cos(angle)
    )

    y1 = (
        (reactor_radius + length)
        * math.sin(angle)
    )

    fig.add_trace(
        go.Scatter3d(
            x=[x0, x1],
            y=[y0, y1],
            z=[z, z],
            mode="lines",
            line=dict(
                width=16,
            ),
            name=name,
        )
    )

    # Nozzle end ring

    theta = np.linspace(
        0,
        2 * np.pi,
        40,
    )

    ux = math.cos(angle)
    uy = math.sin(angle)

    vx = -uy
    vy = ux

    cx = x1
    cy = y1

    ring_x = (
        cx
        + nozzle_radius
        * (
            vx * np.cos(theta)
        )
    )

    ring_y = (
        cy
        + nozzle_radius
        * (
            vy * np.cos(theta)
        )
    )

    ring_z = (
        z
        + nozzle_radius
        * np.sin(theta)
    )

    fig.add_trace(
        go.Scatter3d(
            x=ring_x,
            y=ring_y,
            z=ring_z,
            mode="lines",
            line=dict(
                width=5,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )


def _add_top_nozzles(
    fig,
    reactor_radius,
    shell_top,
    total_height,
):

    nozzle_z = (
        shell_top
        + 0.04 * total_height
    )

    # Main process nozzle

    _add_cylinder(
        fig,
        0.08 * reactor_radius,
        shell_top,
        nozzle_z + 0.10 * total_height,
        "Top Process Nozzle",
        opacity=0.95,
        sides=30,
    )

    # Small vent nozzle

    vent_x = (
        0.45 * reactor_radius
    )

    vent_y = 0.0

    r = 0.045 * reactor_radius

    z0 = shell_top

    z1 = (
        shell_top
        + 0.12 * total_height
    )

    theta = np.linspace(
        0,
        2 * np.pi,
        32,
    )

    fig.add_trace(
        go.Scatter3d(
            x=vent_x + r * np.cos(theta),
            y=vent_y + r * np.sin(theta),
            z=np.full_like(
                theta,
                z1,
            ),
            mode="lines",
            line=dict(
                width=5,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[
                vent_x,
                vent_x,
            ],
            y=[
                vent_y,
                vent_y,
            ],
            z=[
                z0,
                z1,
            ],
            mode="lines",
            line=dict(
                width=12,
            ),
            name="Vent Nozzle",
        )
    )


# ============================================================
# MANWAY
# ============================================================

def _add_manway(
    fig,
    reactor_radius,
    shell_top,
    total_height,
):

    angle = np.deg2rad(
        135
    )

    r = 0.18 * reactor_radius

    cx = (
        0.68
        * reactor_radius
        * math.cos(angle)
    )

    cy = (
        0.68
        * reactor_radius
        * math.sin(angle)
    )

    z = (
        shell_top
        + 0.04 * total_height
    )

    theta = np.linspace(
        0,
        2 * np.pi,
        60,
    )

    fig.add_trace(
        go.Scatter3d(
            x=cx + r * np.cos(theta),
            y=cy + r * np.sin(theta),
            z=np.full_like(
                theta,
                z,
            ),
            mode="lines",
            line=dict(
                width=10,
            ),
            name="Manway",
        )
    )


# ============================================================
# SUPPORT LEGS
# ============================================================

def _add_supports(
    fig,
    reactor_radius,
    shell_bottom,
    leg_height,
    count=4,
):

    count = max(
        3,
        _safe_int(
            count,
            4,
        ),
    )

    support_radius = (
        0.10 * reactor_radius
    )

    leg_top = shell_bottom

    leg_bottom = (
        shell_bottom
        - leg_height
    )

    support_circle = (
        0.72 * reactor_radius
    )

    for i in range(count):

        angle = (
            2
            * np.pi
            * i
            / count
        )

        x = (
            support_circle
            * np.cos(angle)
        )

        y = (
            support_circle
            * np.sin(angle)
        )

        _add_cylinder(
            fig,
            support_radius,
            leg_bottom,
            leg_top,
            "Support Legs" if i == 0 else None,
            opacity=0.95,
            sides=24,
        )

        # Foot plate

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x - 0.10 * reactor_radius,
                    x + 0.10 * reactor_radius,
                ],
                y=[
                    y,
                    y,
                ],
                z=[
                    leg_bottom,
                    leg_bottom,
                ],
                mode="lines",
                line=dict(
                    width=10,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )


# ============================================================
# IMPELLER GEOMETRIES
# ============================================================

def _add_rushton(
    fig,
    radius,
    z,
    shaft_radius,
    blades=6,
    rotation=0.0,
    name="Rushton Turbine",
):

    theta = np.linspace(
        0,
        2 * np.pi,
        80,
    )

    hub_radius = (
        2.2 * shaft_radius
    )

    # Hub

    _add_cylinder(
        fig,
        hub_radius,
        z - 0.035 * radius,
        z + 0.035 * radius,
        "Impeller Hub",
        opacity=0.95,
        sides=24,
    )

    # Disc

    r_disc = radius * 0.90

    fig.add_trace(
        go.Scatter3d(
            x=r_disc * np.cos(theta),
            y=r_disc * np.sin(theta),
            z=np.full_like(
                theta,
                z,
            ),
            mode="lines",
            line=dict(
                width=5,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Blades

    for b in range(blades):

        a = (
            rotation
            + 2
            * np.pi
            * b
            / blades
        )

        r1 = radius * 0.25
        r2 = radius * 0.95

        width = (
            0.08 * radius
        )

        ux = math.cos(a)
        uy = math.sin(a)

        vx = -uy
        vy = ux

        p1 = (
            r1 * ux,
            r1 * uy,
        )

        p2 = (
            r2 * ux,
            r2 * uy,
        )

        x = [
            p1[0] - width * vx,
            p2[0] - width * vx,
            p2[0] + width * vx,
            p1[0] + width * vx,
        ]

        y = [
            p1[1] - width * vy,
            p2[1] - width * vy,
            p2[1] + width * vy,
            p1[1] + width * vy,
        ]

        zz = [
            z,
            z,
            z,
            z,
        ]

        fig.add_trace(
            go.Mesh3d(
                x=x,
                y=y,
                z=zz,
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                opacity=0.95,
                hoverinfo="skip",
                name=(
                    name
                    if b == 0
                    else None
                ),
                showlegend=(b == 0),
            )
        )


def _add_pbt(
    fig,
    radius,
    z,
    shaft_radius,
    blades=4,
    rotation=0.0,
    name="Pitched Blade Turbine",
):

    hub_radius = (
        2.0 * shaft_radius
    )

    _add_cylinder(
        fig,
        hub_radius,
        z - 0.05 * radius,
        z + 0.05 * radius,
        "PBT Hub",
        opacity=0.95,
        sides=24,
    )

    for b in range(blades):

        a = (
            rotation
            + 2
            * np.pi
            * b
            / blades
        )

        r1 = 0.18 * radius
        r2 = 0.92 * radius

        width1 = 0.08 * radius
        width2 = 0.13 * radius

        ux = math.cos(a)
        uy = math.sin(a)

        vx = -uy
        vy = ux

        x = [
            r1 * ux - width1 * vx,
            r2 * ux - width2 * vx,
            r2 * ux + width2 * vx,
            r1 * ux + width1 * vx,
        ]

        y = [
            r1 * uy - width1 * vy,
            r2 * uy - width2 * vy,
            r2 * uy + width2 * vy,
            r1 * uy + width1 * vy,
        ]

        # Pitch is represented through blade height.

        z_values = [
            z - 0.05 * radius,
            z - 0.12 * radius,
            z + 0.12 * radius,
            z + 0.05 * radius,
        ]

        fig.add_trace(
            go.Mesh3d(
                x=x,
                y=y,
                z=z_values,
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                opacity=0.95,
                hoverinfo="skip",
                name=(
                    name
                    if b == 0
                    else None
                ),
                showlegend=(b == 0),
            )
        )


def _add_hydrofoil(
    fig,
    radius,
    z,
    shaft_radius,
    blades=3,
    rotation=0.0,
    name="Hydrofoil",
):

    hub_radius = (
        1.8 * shaft_radius
    )

    _add_cylinder(
        fig,
        hub_radius,
        z - 0.05 * radius,
        z + 0.05 * radius,
        "Hydrofoil Hub",
        opacity=0.95,
        sides=24,
    )

    for b in range(blades):

        a = (
            rotation
            + 2
            * np.pi
            * b
            / blades
        )

        r = np.linspace(
            0.18 * radius,
            0.95 * radius,
            18,
        )

        blade_width = (
            0.05 * radius
            + 0.10 * radius
            * (
                r / radius
            )
        )

        ux = math.cos(a)
        uy = math.sin(a)

        vx = -uy
        vy = ux

        x1 = (
            r * ux
            - blade_width * vx
        )

        y1 = (
            r * uy
            - blade_width * vy
        )

        x2 = (
            r * ux
            + blade_width * vx
        )

        y2 = (
            r * uy
            + blade_width * vy
        )

        z1 = (
            z
            - 0.05 * radius
            * r / radius
        )

        z2 = (
            z
            + 0.05 * radius
            * r / radius
        )

        fig.add_trace(
            go.Mesh3d(
                x=np.concatenate(
                    [x1, x2]
                ),
                y=np.concatenate(
                    [y1, y2]
                ),
                z=np.concatenate(
                    [z1, z2]
                ),
                i=list(
                    range(
                        len(r) - 1
                    )
                ),
                j=list(
                    range(
                        len(r) - 1
                    )
                ),
                k=[
                    len(r) + i
                    for i in range(
                        len(r) - 1
                    )
                ],
                opacity=0.95,
                hoverinfo="skip",
                name=(
                    name
                    if b == 0
                    else None
                ),
                showlegend=(b == 0),
            )
        )


def _add_marine_propeller(
    fig,
    radius,
    z,
    shaft_radius,
    blades=3,
    rotation=0.0,
    name="Marine Propeller",
):

    hub_radius = (
        2.0 * shaft_radius
    )

    _add_cylinder(
        fig,
        hub_radius,
        z - 0.07 * radius,
        z + 0.07 * radius,
        "Marine Propeller Hub",
        opacity=0.95,
        sides=24,
    )

    for b in range(blades):

        a = (
            rotation
            + 2
            * np.pi
            * b
            / blades
        )

        r = np.linspace(
            0.15 * radius,
            0.95 * radius,
            25,
        )

        width = (
            0.16
            * radius
            * (
                1
                - 0.65
                * r
                / radius
            )
        )

        ux = math.cos(a)
        uy = math.sin(a)

        vx = -uy
        vy = ux

        x = np.concatenate(
            [
                r * ux - width * vx,
                r * ux + width * vx,
            ]
        )

        y = np.concatenate(
            [
                r * uy - width * vy,
                r * uy + width * vy,
            ]
        )

        z1 = (
            z
            - 0.10
            * radius
            * r
            / radius
        )

        z2 = (
            z
            + 0.10
            * radius
            * r
            / radius
        )

        fig.add_trace(
            go.Mesh3d(
                x=x,
                y=y,
                z=np.concatenate(
                    [z1, z2]
                ),
                i=list(
                    range(
                        len(r) - 1
                    )
                ),
                j=[
                    len(r) + i
                    for i in range(
                        len(r) - 1
                    )
                ],
                k=[
                    len(r) + i + 1
                    for i in range(
                        len(r) - 1
                    )
                ],
                opacity=0.95,
                hoverinfo="skip",
                name=(
                    name
                    if b == 0
                    else None
                ),
                showlegend=(b == 0),
            )
        )


def _add_anchor(
    fig,
    radius,
    z,
    shaft_radius,
    name="Anchor",
):

    hub_radius = (
        2.0 * shaft_radius
    )

    _add_cylinder(
        fig,
        hub_radius,
        z - 0.05 * radius,
        z + 0.05 * radius,
        "Anchor Hub",
        opacity=0.95,
        sides=24,
    )

    theta = np.linspace(
        0,
        2 * np.pi,
        80,
    )

    # Anchor vertical arms

    r_anchor = (
        0.92 * radius
    )

    for angle in [
        0,
        np.pi,
    ]:

        x = np.array(
            [
                r_anchor * np.cos(angle),
                r_anchor * np.cos(angle),
            ]
        )

        y = np.array(
            [
                r_anchor * np.sin(angle),
                r_anchor * np.sin(angle),
            ]
        )

        z_values = np.array(
            [
                z - 0.45 * radius,
                z + 0.45 * radius,
            ]
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z_values,
                mode="lines",
                line=dict(
                    width=10,
                ),
                name=(
                    name
                    if angle == 0
                    else None
                ),
                showlegend=(
                    angle == 0
                ),
            )
        )

    # Horizontal anchor bridge

    fig.add_trace(
        go.Scatter3d(
            x=[
                -r_anchor,
                r_anchor,
            ],
            y=[
                0,
                0,
            ],
            z=[
                z - 0.45 * radius,
                z - 0.45 * radius,
            ],
            mode="lines",
            line=dict(
                width=10,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )


def _add_helical_ribbon(
    fig,
    radius,
    z,
    shaft_radius,
    name="Helical Ribbon",
):

    turns = 1.25

    theta = np.linspace(
        0,
        2 * np.pi * turns,
        180,
    )

    r = 0.90 * radius

    x = r * np.cos(theta)

    y = r * np.sin(theta)

    z_values = (
        z
        - 0.50 * radius
        + (
            theta
            / (
                2
                * np.pi
                * turns
            )
        )
        * radius
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z_values,
            mode="lines",
            line=dict(
                width=12,
            ),
            name=name,
        )
    )


def _add_generic_impeller(
    fig,
    radius,
    z,
    shaft_radius,
    rotation=0.0,
    name="Impeller",
):

    theta = np.linspace(
        0,
        2 * np.pi,
        6,
        endpoint=False,
    )

    for a in theta:

        angle = (
            a + rotation
        )

        x = [
            0,
            radius * math.cos(angle),
        ]

        y = [
            0,
            radius * math.sin(angle),
        ]

        z_values = [
            z,
            z,
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
                    name
                    if a == theta[0]
                    else None
                ),
                showlegend=(
                    a == theta[0]
                ),
            )
        )


def _add_impeller(
    fig,
    impeller,
    shaft_radius,
    rotation=0.0,
):

    D = max(
        0.05,
        _safe_float(
            impeller.get(
                "diameter_m"
            ),
            1.0,
        ),
    )

    radius = D / 2.0

    z = _safe_float(
        impeller.get(
            "elevation_m"
        ),
        0.5,
    )

    name = str(
        impeller.get(
            "agitator_type",
            "Impeller",
        )
    )

    lower = name.lower()

    if "rushton" in lower:

        _add_rushton(
            fig,
            radius,
            z,
            shaft_radius,
            rotation=rotation,
            name=name,
        )

    elif (
        "pitched" in lower
        or "pbt" in lower
    ):

        _add_pbt(
            fig,
            radius,
            z,
            shaft_radius,
            rotation=rotation,
            name=name,
        )

    elif "hydrofoil" in lower:

        _add_hydrofoil(
            fig,
            radius,
            z,
            shaft_radius,
            rotation=rotation,
            name=name,
        )

    elif (
        "marine" in lower
        or "propeller" in lower
    ):

        _add_marine_propeller(
            fig,
            radius,
            z,
            shaft_radius,
            rotation=rotation,
            name=name,
        )

    elif "anchor" in lower:

        _add_anchor(
            fig,
            radius,
            z,
            shaft_radius,
            name=name,
        )

    elif (
        "helical" in lower
        or "ribbon" in lower
    ):

        _add_helical_ribbon(
            fig,
            radius,
            z,
            shaft_radius,
            name=name,
        )

    else:

        _add_generic_impeller(
            fig,
            radius,
            z,
            shaft_radius,
            rotation=rotation,
            name=name,
        )


# ============================================================
# VORTEX
# ============================================================

def _add_vortex(
    fig,
    radius,
    liquid_level,
    rpm,
    strength=0.18,
):

    theta = np.linspace(
        0,
        2 * np.pi,
        100,
    )

    vortex_depth = (
        strength
        * radius
        * _clamp(
            rpm / 100.0,
            0.25,
            2.0,
        )
    )

    r = np.linspace(
        0.03 * radius,
        0.98 * radius,
        35,
    )

    theta_grid, r_grid = np.meshgrid(
        theta,
        r,
    )

    x = (
        r_grid
        * np.cos(theta_grid)
    )

    y = (
        r_grid
        * np.sin(theta_grid)
    )

    z = (
        liquid_level
        - vortex_depth
        * (
            1
            - r_grid / radius
        ) ** 2
    )

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            opacity=0.55,
            showscale=False,
            hoverinfo="skip",
            name="Vortex Surface",
        )
    )


# ============================================================
# VELOCITY PROFILE
# ============================================================

def _add_velocity_profile(
    fig,
    radius,
    shell_bottom,
    liquid_level,
    rpm,
):

    nr = 10
    nz = 8

    r_values = np.linspace(
        0.15 * radius,
        0.90 * radius,
        nr,
    )

    z_values = np.linspace(
        shell_bottom
        + 0.15
        * (
            liquid_level
            - shell_bottom
        ),
        liquid_level
        - 0.10
        * (
            liquid_level
            - shell_bottom
        ),
        nz,
    )

    R, Z = np.meshgrid(
        r_values,
        z_values,
    )

    omega = (
        2
        * np.pi
        * rpm
        / 60.0
    )

    velocity = (
        omega
        * R
        * np.exp(
            -0.65
            * (
                R / radius
            )
        )
    )

    theta = np.zeros_like(R)

    X = (
        R
        * np.cos(theta)
    )

    Y = (
        R
        * np.sin(theta)
    )

    U = np.zeros_like(R)

    V = velocity

    W = (
        0.12
        * velocity
    )

    fig.add_trace(
        go.Cone(
            x=X.flatten(),
            y=Y.flatten(),
            z=Z.flatten(),
            u=U.flatten(),
            v=V.flatten(),
            w=W.flatten(),
            sizemode="scaled",
            sizeref=0.45,
            anchor="tail",
            showscale=False,
            name="Velocity Profile",
        )
    )


# ============================================================
# FLOW PATHS
# ============================================================

def _add_flow_profile(
    fig,
    radius,
    liquid_level,
    shell_bottom,
    rpm,
):

    height = (
        liquid_level
        - shell_bottom
    )

    theta0 = np.linspace(
        0,
        2 * np.pi,
        12,
        endpoint=False,
    )

    for i, theta in enumerate(
        theta0
    ):

        t = np.linspace(
            0,
            2 * np.pi,
            90,
        )

        radial = (
            0.25
            * radius
            + 0.65
            * radius
            * (
                0.5
                + 0.5
                * np.sin(t)
            )
        )

        z = (
            shell_bottom
            + 0.15 * height
            + 0.70 * height
            * (
                0.5
                + 0.5
                * np.cos(t)
            )
        )

        phase = (
            theta
            + 0.35 * t
        )

        x = (
            radial
            * np.cos(phase)
        )

        y = (
            radial
            * np.sin(phase)
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=3,
                ),
                opacity=0.70,
                name=(
                    "Flow Paths"
                    if i == 0
                    else None
                ),
                showlegend=(
                    i == 0
                ),
                hoverinfo="skip",
            )
        )


# ============================================================
# DEAD ZONES
# ============================================================

def _add_dead_zones(
    fig,
    radius,
    shell_bottom,
    liquid_level,
):

    height = (
        liquid_level
        - shell_bottom
    )

    # Approximate lower corner zones

    for sign in [
        -1,
        1,
    ]:

        theta = (
            sign
            * np.pi
            / 4.0
        )

        center_r = (
            0.80 * radius
        )

        center_x = (
            center_r
            * math.cos(theta)
        )

        center_y = (
            center_r
            * math.sin(theta)
        )

        u = np.linspace(
            0,
            2 * np.pi,
            30,
        )

        v = np.linspace(
            0,
            np.pi,
            15,
        )

        uu, vv = np.meshgrid(
            u,
            v,
        )

        rr = (
            0.18 * radius
        )

        x = (
            center_x
            + rr
            * np.sin(vv)
            * np.cos(uu)
        )

        y = (
            center_y
            + rr
            * np.sin(vv)
            * np.sin(uu)
        )

        zc = (
            shell_bottom
            + 0.12 * height
        )

        z = (
            zc
            + 0.10
            * height
            * np.cos(vv)
        )

        fig.add_trace(
            go.Surface(
                x=x,
                y=y,
                z=z,
                opacity=0.30,
                showscale=False,
                hoverinfo="skip",
                name=(
                    "Approx. Dead Zone"
                    if sign == -1
                    else None
                ),
                showlegend=(
                    sign == -1
                ),
            )
        )


# ============================================================
# MIXING PARTICLES
# ============================================================

def _add_particles(
    fig,
    radius,
    shell_bottom,
    liquid_level,
    count=180,
):

    rng = np.random.default_rng(
        42
    )

    r = (
        radius
        * np.sqrt(
            rng.random(count)
        )
        * 0.88
    )

    theta = (
        2
        * np.pi
        * rng.random(count)
    )

    z = (
        shell_bottom
        + (
            liquid_level
            - shell_bottom
        )
        * rng.random(count)
    )

    x = (
        r
        * np.cos(theta)
    )

    y = (
        r
        * np.sin(theta)
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=3,
                opacity=0.75,
            ),
            name="Mixing Particles",
        )
    )


# ============================================================
# GAS BUBBLES
# ============================================================

def _add_gas_bubbles(
    fig,
    radius,
    shell_bottom,
    liquid_level,
    gas_flow_m3_h,
    bubble_diameter_mm,
):

    if gas_flow_m3_h <= 0:
        return

    rng = np.random.default_rng(
        7
    )

    count = int(
        _clamp(
            60
            + gas_flow_m3_h * 5,
            60,
            450,
        )
    )

    r = (
        0.18
        * radius
        * np.sqrt(
            rng.random(count)
        )
    )

    theta = (
        2
        * np.pi
        * rng.random(count)
    )

    z = (
        shell_bottom
        + (
            liquid_level
            - shell_bottom
        )
        * rng.random(count)
    )

    # Bubble rise spiral

    phase = (
        theta
        + 0.8
        * (
            z
            - shell_bottom
        )
        / max(
            0.01,
            liquid_level
            - shell_bottom,
        )
    )

    x = (
        r
        * np.cos(phase)
    )

    y = (
        r
        * np.sin(phase)
    )

    size = _clamp(
        3.0
        + 0.5
        * bubble_diameter_mm,
        3,
        10,
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=size,
                opacity=0.55,
                symbol="circle",
            ),
            name="Gas Bubbles",
        )
    )


# ============================================================
# DIMENSIONS
# ============================================================

def _add_dimension(
    fig,
    p1,
    p2,
    text,
):

    x = [
        p1[0],
        p2[0],
    ]

    y = [
        p1[1],
        p2[1],
    ]

    z = [
        p1[2],
        p2[2],
    ]

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines+text",
            text=[
                "",
                text,
            ],
            textposition="top center",
            line=dict(
                width=3,
                dash="dash",
            ),
            hoverinfo="skip",
            name=text,
        )
    )


def _add_dimensions(
    fig,
    diameter,
    total_height,
    liquid_level,
    shell_bottom,
):

    R = diameter / 2.0

    _add_dimension(
        fig,
        (-R * 1.20, 0, shell_bottom),
        (R * 1.20, 0, shell_bottom),
        f"ID = {diameter:.2f} m",
    )

    _add_dimension(
        fig,
        (
            R * 1.35,
            0,
            shell_bottom,
        ),
        (
            R * 1.35,
            0,
            shell_bottom + total_height,
        ),
        f"Overall H = {total_height:.2f} m",
    )

    _add_dimension(
        fig,
        (
            -R * 1.10,
            0,
            shell_bottom,
        ),
        (
            -R * 1.10,
            0,
            liquid_level,
        ),
        f"Liquid = {liquid_level - shell_bottom:.2f} m",
    )


# ============================================================
# EQUIPMENT MODE
# ============================================================

def _equipment_scene(
    fig,
    geometry,
    diameter,
    straight_height,
    bottom_type,
    top_type,
    liquid_level,
    impellers,
    rpm,
    number_baffles,
):

    R = geometry["radius"]

    shell_bottom = geometry[
        "shell_bottom"
    ]

    shell_top = geometry[
        "shell_top"
    ]

    total_height = geometry[
        "total_height"
    ]

    # Drive

    _add_drive(
        fig,
        R,
        shell_top,
        total_height,
    )

    # Shaft

    shaft_radius = max(
        0.025 * diameter,
        0.025,
    )

    _add_shaft(
        fig,
        shaft_radius,
        shell_bottom
        - 0.05 * total_height,
        shell_top
        + 0.25 * total_height,
    )

    # Flange

    _add_flange(
        fig,
        0.62 * R,
        shell_top,
        0.025 * total_height,
    )

    # Nozzles

    _add_top_nozzles(
        fig,
        R,
        shell_top,
        total_height,
    )

    _add_manway(
        fig,
        R,
        shell_top,
        total_height,
    )

    # Side nozzles

    _add_side_nozzle(
        fig,
        R,
        shell_bottom
        + 0.55
        * (
            shell_top
            - shell_bottom
        ),
        0.0,
        0.18 * diameter,
        0.06 * diameter,
        "Side Process Nozzle",
    )

    _add_side_nozzle(
        fig,
        R,
        shell_bottom
        + 0.30
        * (
            shell_top
            - shell_bottom
        ),
        np.pi,
        0.15 * diameter,
        0.05 * diameter,
        "Side Nozzle",
    )

    # Supports

    _add_supports(
        fig,
        R,
        shell_bottom,
        0.35 * total_height,
    )

    # Baffles

    _add_baffles(
        fig,
        diameter,
        shell_bottom,
        shell_top,
        number_baffles,
    )

    # Shaft and impellers

    rotation = 0.0

    for impeller in impellers:

        _add_impeller(
            fig,
            impeller,
            shaft_radius,
            rotation=rotation,
        )


# ============================================================
# MAIN 3D FUNCTION
# ============================================================

def create_reactor_animation(

    volume_m3=None,

    tank_diameter_m=None,

    straight_height_m=None,

    liquid_height_m=None,

    rpm=100.0,

    impellers=None,

    bottom_type="10% Torispherical",

    top_type="10% Torispherical",

    number_baffles=4,

    density_kg_m3=1000.0,

    viscosity_pa_s=0.001,

    gas_flow_m3_h=0.0,

    bubble_diameter_mm=3.0,

    selected_features=None,

    # --------------------------------------------------------
    # Legacy compatibility
    # --------------------------------------------------------

    D=None,

    H=None,

    volume=None,

    liquid_level=None,

    agitator=None,

    impeller_diameter_m=None,

    number_impellers=1,

    impeller_clearance_m=0.4,

    **kwargs,

):

    # ========================================================
    # INPUT NORMALIZATION
    # ========================================================

    if tank_diameter_m is None:
        tank_diameter_m = D

    if straight_height_m is None:
        straight_height_m = H

    if volume_m3 is None:
        volume_m3 = volume

    if liquid_height_m is None:
        liquid_height_m = liquid_level

    diameter = max(
        0.10,
        _safe_float(
            tank_diameter_m,
            2.0,
        ),
    )

    straight_height = max(
        0.10,
        _safe_float(
            straight_height_m,
            3.0,
        ),
    )

    volume_value = max(
        0.0,
        _safe_float(
            volume_m3,
            10.0,
        ),
    )

    rpm_value = max(
        0.0,
        _safe_float(
            rpm,
            100.0,
        ),
    )

    density = max(
        0.01,
        _safe_float(
            density_kg_m3,
            1000.0,
        ),
    )

    viscosity = max(
        1e-8,
        _safe_float(
            viscosity_pa_s,
            0.001,
        ),
    )

    gas_flow = max(
        0.0,
        _safe_float(
            gas_flow_m3_h,
            0.0,
        ),
    )

    bubble_size = max(
        0.1,
        _safe_float(
            bubble_diameter_mm,
            3.0,
        ),
    )

    # ========================================================
    # FEATURES
    # ========================================================

    if selected_features is None:

        selected = [
            "Reactor Geometry",
            "Liquid Level",
            "Impeller & Shaft",
            "Baffles",
        ]

    else:

        selected = list(
            selected_features
        )

    if (
        "Select All" in selected
        or "All" in selected
    ):

        selected = (
            VISUALIZATION_FEATURES.copy()
        )

    # ========================================================
    # GEOMETRY
    # ========================================================

    geometry = _add_vessel_shell(
        fig=go.Figure(),
        diameter=diameter,
        straight_height=straight_height,
        bottom_type=bottom_type,
        top_type=top_type,
    )

    # ========================================================
    # FIGURE
    # ========================================================

    fig = go.Figure()

    # Recreate vessel using same geometry
    geometry = _add_vessel_shell(
        fig,
        diameter,
        straight_height,
        bottom_type,
        top_type,
    )

    R = geometry["radius"]

    shell_bottom = geometry[
        "shell_bottom"
    ]

    shell_top = geometry[
        "shell_top"
    ]

    total_height = geometry[
        "total_height"
    ]

    # ========================================================
    # LIQUID LEVEL
    # ========================================================

    if liquid_height_m is not None:

        liquid_level_value = (
            shell_bottom
            + max(
                0.0,
                _safe_float(
                    liquid_height_m,
                    0.0,
                ),
            )
        )

    else:

        liquid_level_value = (
            _liquid_level_from_volume(
                volume_value,
                diameter,
                straight_height,
                geometry[
                    "bottom_depth"
                ],
                geometry[
                    "top_depth"
                ],
            )
        )

    liquid_level_value = _clamp(
        liquid_level_value,
        shell_bottom + 0.02,
        shell_top + geometry[
            "top_depth"
        ],
    )

    # ========================================================
    # NORMALIZE IMPELLERS
    # ========================================================

    impellers_normalized = (
        _normalize_impellers(
            impellers=impellers,
            agitator=agitator,
            impeller_diameter_m=(
                impeller_diameter_m
            ),
            number_impellers=(
                number_impellers
            ),
            impeller_clearance_m=(
                impeller_clearance_m
            ),
            liquid_height_m=(
                liquid_level_value
                - shell_bottom
            ),
        )
    )

    # ========================================================
    # GEOMETRY
    # ========================================================

    if "Reactor Geometry" in selected:

        _equipment_scene(
            fig,
            geometry,
            diameter,
            straight_height,
            bottom_type,
            top_type,
            liquid_level_value,
            impellers_normalized,
            rpm_value,
            number_baffles,
        )

    else:

        # If geometry is not selected, still show selected
        # internal components.

        shaft_radius = max(
            0.025 * diameter,
            0.025,
        )

        if "Impeller & Shaft" in selected:

            _add_shaft(
                fig,
                shaft_radius,
                shell_bottom,
                shell_top,
            )

            for impeller in (
                impellers_normalized
            ):

                _add_impeller(
                    fig,
                    impeller,
                    shaft_radius,
                )

        if "Baffles" in selected:

            _add_baffles(
                fig,
                diameter,
                shell_bottom,
                shell_top,
                number_baffles,
            )

    # ========================================================
    # LIQUID
    # ========================================================

    if "Liquid Level" in selected:

        _add_liquid(
            fig,
            diameter,
            liquid_level_value,
            shell_bottom,
            shell_top,
        )

    # ========================================================
    # IMPELLER & SHAFT
    # ========================================================

    if (
        "Impeller & Shaft" in selected
        and "Reactor Geometry" in selected
    ):

        # Already added by equipment scene.
        pass

    elif "Impeller & Shaft" in selected:

        shaft_radius = max(
            0.025 * diameter,
            0.025,
        )

        _add_shaft(
            fig,
            shaft_radius,
            shell_bottom,
            shell_top,
        )

        for impeller in (
            impellers_normalized
        ):

            _add_impeller(
                fig,
                impeller,
                shaft_radius,
            )

    # ========================================================
    # BAFFLES
    # ========================================================

    if (
        "Baffles" in selected
        and "Reactor Geometry" in selected
    ):

        # Already added.
        pass

    elif "Baffles" in selected:

        _add_baffles(
            fig,
            diameter,
            shell_bottom,
            shell_top,
            number_baffles,
        )

    # ========================================================
    # VORTEX
    # ========================================================

    if "Vortex Formation" in selected:

        _add_vortex(
            fig,
            R,
            liquid_level_value,
            rpm_value,
        )

    # ========================================================
    # VELOCITY
    # ========================================================

    if "Velocity Profile" in selected:

        _add_velocity_profile(
            fig,
            R,
            shell_bottom,
            liquid_level_value,
            rpm_value,
        )

    # ========================================================
    # FLOW
    # ========================================================

    if "Flow Profile" in selected:

        _add_flow_profile(
            fig,
            R,
            liquid_level_value,
            shell_bottom,
            rpm_value,
        )

    # ========================================================
    # DEAD ZONES
    # ========================================================

    if "Dead Zone Analysis" in selected:

        _add_dead_zones(
            fig,
            R,
            shell_bottom,
            liquid_level_value,
        )

    # ========================================================
    # PARTICLES
    # ========================================================

    if "Mixing Particles" in selected:

        _add_particles(
            fig,
            R,
            shell_bottom,
            liquid_level_value,
        )

    # ========================================================
    # GAS-LIQUID
    # ========================================================

    if "Gas-Liquid Bubbles" in selected:

        _add_gas_bubbles(
            fig,
            R,
            shell_bottom,
            liquid_level_value,
            gas_flow,
            bubble_size,
        )

    # ========================================================
    # DIMENSIONS
    # ========================================================

    if "Dimensions" in selected:

        _add_dimensions(
            fig,
            diameter,
            total_height,
            liquid_level_value,
            shell_bottom,
        )

    # ========================================================
    # PROFESSIONAL 3D CAMERA
    # ========================================================

    camera = dict(
        eye=dict(
            x=1.75,
            y=1.75,
            z=1.35,
        ),
        center=dict(
            x=0.0,
            y=0.0,
            z=0.15,
        ),
        up=dict(
            x=0,
            y=0,
            z=1,
        ),
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(

        title=dict(
            text=(
                "Advanced Reactor 3D Engineering Model"
            ),
            x=0.50,
            xanchor="center",
            font=dict(
                size=22,
            ),
        ),

        scene=dict(

            aspectmode="data",

            camera=camera,

            xaxis=dict(
                title="X (m)",
                showgrid=False,
                zeroline=False,
                showbackground=False,
            ),

            yaxis=dict(
                title="Y (m)",
                showgrid=False,
                zeroline=False,
                showbackground=False,
            ),

            zaxis=dict(
                title="Elevation (m)",
                showgrid=True,
                zeroline=False,
                showbackground=False,
            ),

            bgcolor="rgba(0,0,0,0)",

            dragmode="orbit",

        ),

        margin=dict(
            l=0,
            r=0,
            t=55,
            b=0,
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.50,
        ),

        hovermode="closest",

    )

    # ========================================================
    # ENGINEERING ANNOTATION
    # ========================================================

    fig.add_annotation(
        x=0.01,
        y=0.99,
        xref="paper",
        yref="paper",
        text=(
            f"ID: {diameter:.2f} m"
            f" | Straight Height: "
            f"{straight_height:.2f} m"
            f" | RPM: {rpm_value:.0f}"
            f" | Impellers: "
            f"{len(impellers_normalized)}"
        ),
        showarrow=False,
        align="left",
        font=dict(
            size=12,
        ),
    )

    return fig


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def create_reactor_3d(**kwargs):
    return create_reactor_animation(
        **kwargs
    )
