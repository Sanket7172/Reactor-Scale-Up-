# ============================================================
# visualization/reactor_3d.py
# Professional Parametric 3D Reactor Visualization
# ============================================================

import math
import numpy as np
import plotly.graph_objects as go

from libraries.reactor_geometry import (
    profile,
    radius_at_height,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value, default=1):
    try:
        return int(value)
    except Exception:
        return int(default)


def _rotate_xy(x, y, angle):
    """Rotate XY coordinates around the reactor shaft."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    ca = math.cos(angle)
    sa = math.sin(angle)

    xr = x * ca - y * sa
    yr = x * sa + y * ca

    return xr, yr


# ============================================================
# MESH HELPER
# ============================================================

def _box_mesh(
    cx,
    cy,
    cz,
    length_x,
    width_y,
    height_z,
    angle=0.0,
):
    """
    Creates a rectangular solid and returns vertices/faces.
    """

    lx = length_x / 2.0
    wy = width_y / 2.0
    hz = height_z / 2.0

    vertices = np.array(
        [
            [-lx, -wy, -hz],
            [ lx, -wy, -hz],
            [ lx,  wy, -hz],
            [-lx,  wy, -hz],
            [-lx, -wy,  hz],
            [ lx, -wy,  hz],
            [ lx,  wy,  hz],
            [-lx,  wy,  hz],
        ],
        dtype=float,
    )

    ca = math.cos(angle)
    sa = math.sin(angle)

    x = vertices[:, 0] * ca - vertices[:, 1] * sa
    y = vertices[:, 0] * sa + vertices[:, 1] * ca

    x += cx
    y += cy
    z = vertices[:, 2] + cz

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

    i = [f[0] for f in faces]
    j = [f[1] for f in faces]
    k = [f[2] for f in faces]

    return x, y, z, i, j, k


def _add_mesh(
    fig,
    x,
    y,
    z,
    i,
    j,
    k,
    name,
    opacity=1.0,
    showlegend=True,
    color="#B8C4CC",
):
    """
    Add shaded 3D solid.
    """

    fig.add_trace(
        go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            color=color,
            opacity=opacity,
            flatshading=False,
            lighting=dict(
                ambient=0.35,
                diffuse=0.75,
                specular=0.65,
                roughness=0.35,
                fresnel=0.20,
            ),
            lightposition=dict(
                x=100,
                y=100,
                z=200,
            ),
            name=name,
            showlegend=showlegend,
            hovertemplate=(
                f"{name}"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# CYLINDER
# ============================================================

def _cylinder_mesh(
    radius,
    z_bottom,
    z_top,
    segments=48,
    center_x=0.0,
    center_y=0.0,
):
    """
    Generate cylindrical surface with top and bottom caps.
    """

    theta = np.linspace(
        0,
        2 * math.pi,
        segments,
        endpoint=False,
    )

    x_bottom = (
        center_x +
        radius * np.cos(theta)
    )

    y_bottom = (
        center_y +
        radius * np.sin(theta)
    )

    x_top = (
        center_x +
        radius * np.cos(theta)
    )

    y_top = (
        center_y +
        radius * np.sin(theta)
    )

    x = np.concatenate(
        [
            x_bottom,
            x_top,
            [center_x],
            [center_x],
        ]
    )

    y = np.concatenate(
        [
            y_bottom,
            y_top,
            [center_y],
            [center_y],
        ]
    )

    z = np.concatenate(
        [
            np.full(segments, z_bottom),
            np.full(segments, z_top),
            [z_bottom],
            [z_top],
        ]
    )

    faces = []

    # Side wall
    for n in range(segments):

        n2 = (n + 1) % segments

        faces.append(
            (
                n,
                n2,
                segments + n
            )
        )

        faces.append(
            (
                n2,
                segments + n2,
                segments + n
            )
        )

    bottom_center = 2 * segments
    top_center = 2 * segments + 1

    # Bottom cap
    for n in range(segments):

        n2 = (n + 1) % segments

        faces.append(
            (
                bottom_center,
                n2,
                n
            )
        )

    # Top cap
    for n in range(segments):

        n2 = (n + 1) % segments

        faces.append(
            (
                top_center,
                segments + n,
                segments + n2
            )
        )

    i = [f[0] for f in faces]
    j = [f[1] for f in faces]
    k = [f[2] for f in faces]

    return x, y, z, i, j, k


def _add_cylinder(
    fig,
    radius,
    z_bottom,
    z_top,
    name,
    color="#777F86",
    opacity=1.0,
    segments=48,
    showlegend=True,
):

    x, y, z, i, j, k = _cylinder_mesh(
        radius,
        z_bottom,
        z_top,
        segments=segments,
    )

    _add_mesh(
        fig,
        x,
        y,
        z,
        i,
        j,
        k,
        name=name,
        opacity=opacity,
        showlegend=showlegend,
        color=color,
    )


# ============================================================
# IMPELLER GEOMETRY
# ============================================================

def _anchor_geometry(
    D,
    z,
    thickness=None,
):
    """
    3D Anchor impeller.
    """

    radius = D / 2.0

    if thickness is None:
        thickness = max(
            0.025 * D,
            0.025,
        )

    parts = []

    # Bottom horizontal arm
    arm_length = radius * 1.80

    parts.append(
        _box_mesh(
            0,
            0,
            z,
            arm_length,
            thickness,
            thickness,
        )
    )

    # Vertical anchor legs
    leg_height = max(
        D * 0.55,
        0.15,
    )

    leg_offset = radius * 0.82

    parts.append(
        _box_mesh(
            leg_offset,
            0,
            z + leg_height / 2.0,
            thickness,
            thickness,
            leg_height,
        )
    )

    parts.append(
        _box_mesh(
            -leg_offset,
            0,
            z + leg_height / 2.0,
            thickness,
            thickness,
            leg_height,
        )
    )

    # Rotate/replicate visual cross arms
    return parts


def _rushton_geometry(
    D,
    z,
    blades=6,
):
    """
    3D Rushton turbine:
    central disk + six radial blades.
    """

    radius = D / 2.0

    parts = []

    # Disk
    disk_radius = radius * 0.38
    disk_thickness = max(
        0.035 * D,
        0.02,
    )

    x, y, zz, i, j, k = _cylinder_mesh(
        disk_radius,
        z - disk_thickness / 2,
        z + disk_thickness / 2,
        segments=40,
    )

    parts.append(
        (
            x,
            y,
            zz,
            i,
            j,
            k
        )
    )

    # Blades
    blade_length = radius * 0.52
    blade_width = max(
        D * 0.10,
        0.035,
    )
    blade_height = max(
        D * 0.10,
        0.025,
    )

    for n in range(blades):

        angle = (
            2 *
            math.pi *
            n /
            blades
        )

        cx = (
            radius *
            0.62 *
            math.cos(angle)
        )

        cy = (
            radius *
            0.62 *
            math.sin(angle)
        )

        parts.append(
            _box_mesh(
                cx,
                cy,
                z,
                blade_length,
                blade_width,
                blade_height,
                angle=angle,
            )
        )

    return parts


def _pbt_geometry(
    D,
    z,
    blades=4,
):
    """
    3D pitched blade turbine.
    """

    radius = D / 2.0

    parts = []

    hub_radius = max(
        D * 0.12,
        0.04,
    )

    hub_height = max(
        D * 0.18,
        0.05,
    )

    x, y, zz, i, j, k = _cylinder_mesh(
        hub_radius,
        z - hub_height / 2,
        z + hub_height / 2,
        segments=32,
    )

    parts.append(
        (
            x,
            y,
            zz,
            i,
            j,
            k
        )
    )

    blade_length = radius * 0.70
    blade_width = max(
        D * 0.13,
        0.05,
    )
    blade_height = max(
        D * 0.055,
        0.025,
    )

    pitch_angle = math.radians(25)

    for n in range(blades):

        angle = (
            2 *
            math.pi *
            n /
            blades
        )

        cx = (
            radius *
            0.50 *
            math.cos(angle)
        )

        cy = (
            radius *
            0.50 *
            math.sin(angle)
        )

        # Blade as rectangular solid with inclination
        part = _box_mesh(
            cx,
            cy,
            z,
            blade_length,
            blade_width,
            blade_height,
            angle=angle,
        )

        px, py, pz, pi, pj, pk = part

        # Apply pitch around radial direction
        local_x = (
            px * math.cos(pitch_angle)
            - pz * math.sin(pitch_angle)
        )

        local_z = (
            px * math.sin(pitch_angle)
            + pz * math.cos(pitch_angle)
        )

        px = local_x
        pz = local_z + z

        # Remove double z translation caused by box helper
        pz = pz - z + z

        parts.append(
            (
                px,
                py,
                pz,
                pi,
                pj,
                pk,
            )
        )

    return parts


def _hydrofoil_geometry(
    D,
    z,
    blades=3,
):
    """
    Approximate hydrofoil impeller using tapered swept blades.
    """

    radius = D / 2.0

    parts = []

    hub_radius = D * 0.12
    hub_height = D * 0.18

    x, y, zz, i, j, k = _cylinder_mesh(
        hub_radius,
        z - hub_height / 2,
        z + hub_height / 2,
        segments=32,
    )

    parts.append(
        (
            x,
            y,
            zz,
            i,
            j,
            k,
        )
    )

    for n in range(blades):

        angle = (
            2 *
            math.pi *
            n /
            blades
        )

        r1 = radius * 0.18
        r2 = radius * 0.90

        width1 = D * 0.12
        width2 = D * 0.06

        x1 = r1
        x2 = r2

        vertices = np.array(
            [
                [x1, -width1 / 2, -0.02 * D],
                [x2, -width2 / 2, -0.02 * D],
                [x2,  width2 / 2,  0.02 * D],
                [x1,  width1 / 2,  0.02 * D],
            ]
        )

        ca = math.cos(angle)
        sa = math.sin(angle)

        xx = (
            vertices[:, 0] * ca
            - vertices[:, 1] * sa
        )

        yy = (
            vertices[:, 0] * sa
            + vertices[:, 1] * ca
        )

        zzv = vertices[:, 2] + z

        faces = [
            (0, 1, 2),
            (0, 2, 3),
            (2, 1, 0),
            (3, 2, 0),
        ]

        parts.append(
            (
                xx,
                yy,
                zzv,
                [f[0] for f in faces],
                [f[1] for f in faces],
                [f[2] for f in faces],
            )
        )

    return parts


def _marine_propeller_geometry(
    D,
    z,
    blades=3,
):
    """
    Approximate marine propeller.
    """

    radius = D / 2.0

    parts = []

    hub_radius = D * 0.13
    hub_height = D * 0.30

    x, y, zz, i, j, k = _cylinder_mesh(
        hub_radius,
        z - hub_height / 2,
        z + hub_height / 2,
        segments=32,
    )

    parts.append(
        (
            x,
            y,
            zz,
            i,
            j,
            k,
        )
    )

    for n in range(blades):

        angle = (
            2 *
            math.pi *
            n /
            blades
        )

        r_inner = radius * 0.18
        r_outer = radius * 0.92

        width_inner = D * 0.14
        width_outer = D * 0.045

        points = []

        for r, width, zz_offset in [
            (r_inner, width_inner, -D * 0.04),
            (r_outer, width_outer, D * 0.04),
            (r_outer, width_outer, -D * 0.04),
            (r_inner, width_inner, D * 0.04),
        ]:

            local_x = r
            local_y = width / 2

            xx = (
                local_x * math.cos(angle)
                - local_y * math.sin(angle)
            )

            yy = (
                local_x * math.sin(angle)
                + local_y * math.cos(angle)
            )

            points.append(
                [
                    xx,
                    yy,
                    z + zz_offset,
                ]
            )

        points = np.asarray(points)

        faces = [
            (0, 1, 2),
            (0, 2, 3),
        ]

        parts.append(
            (
                points[:, 0],
                points[:, 1],
                points[:, 2],
                [0, 0],
                [1, 2],
                [2, 3],
            )
        )

    return parts


def _helical_ribbon_geometry(
    D,
    z,
):
    """
    Approximate helical ribbon.
    """

    radius = D / 2.0 * 0.88

    height = D * 0.85

    turns = 1.15

    n = 80

    theta = np.linspace(
        0,
        2 * math.pi * turns,
        n,
    )

    zz = (
        z -
        height / 2
        +
        height *
        np.linspace(0, 1, n)
    )

    width = D * 0.08

    x1 = radius * np.cos(theta)
    y1 = radius * np.sin(theta)

    x2 = (
        (radius - width)
        * np.cos(theta)
    )

    y2 = (
        (radius - width)
        * np.sin(theta)
    )

    x = np.concatenate(
        [x1, x2]
    )

    y = np.concatenate(
        [y1, y2]
    )

    z_all = np.concatenate(
        [zz, zz]
    )

    faces = []

    for nidx in range(n - 1):

        faces.append(
            (
                nidx,
                nidx + 1,
                n + nidx + 1,
            )
        )

        faces.append(
            (
                nidx,
                n + nidx + 1,
                n + nidx,
            )
        )

    return [
        (
            x,
            y,
            z_all,
            [f[0] for f in faces],
            [f[1] for f in faces],
            [f[2] for f in faces],
        )
    ]


def _rci_geometry(
    D,
    z,
    blades=2,
):
    """
    Approximate RCI / radial curved impeller.
    """

    radius = D / 2.0

    parts = []

    hub_radius = D * 0.13
    hub_height = D * 0.20

    x, y, zz, i, j, k = _cylinder_mesh(
        hub_radius,
        z - hub_height / 2,
        z + hub_height / 2,
        segments=32,
    )

    parts.append(
        (
            x,
            y,
            zz,
            i,
            j,
            k,
        )
    )

    for n in range(blades):

        angle = (
            2 *
            math.pi *
            n /
            blades
        )

        theta = np.linspace(
            -math.pi / 3,
            math.pi / 3,
            25,
        )

        r = (
            radius *
            (
                0.25 +
                0.65 *
                (
                    1 -
                    np.cos(theta)
                ) /
                2
            )
        )

        x = r * np.cos(
            theta + angle
        )

        y = r * np.sin(
            theta + angle
        )

        width = D * 0.06

        x2 = (
            (r - width)
            * np.cos(theta + angle)
        )

        y2 = (
            (r - width)
            * np.sin(theta + angle)
        )

        z1 = (
            z +
            0.025 *
            D *
            np.sin(theta)
        )

        z2 = (
            z -
            0.025 *
            D *
            np.sin(theta)
        )

        xx = np.concatenate(
            [x, x2]
        )

        yy = np.concatenate(
            [y, y2]
        )

        zzv = np.concatenate(
            [z1, z2]
        )

        faces = []

        nn = len(theta)

        for q in range(nn - 1):

            faces.append(
                (
                    q,
                    q + 1,
                    nn + q + 1,
                )
            )

            faces.append(
                (
                    q,
                    nn + q + 1,
                    nn + q,
                )
            )

        parts.append(
            (
                xx,
                yy,
                zzv,
                [f[0] for f in faces],
                [f[1] for f in faces],
                [f[2] for f in faces],
            )
        )

    return parts


# ============================================================
# IMPeller FACTORY
# ============================================================

def _create_impeller_geometry(
    agitator,
    D,
    z,
):
    """
    Select the appropriate physical impeller geometry.
    """

    agitator = str(
        agitator
    ).strip()

    name = agitator.lower()

    if "anchor" in name:

        return _anchor_geometry(
            D,
            z,
        )

    if "rushton" in name:

        return _rushton_geometry(
            D,
            z,
            blades=6,
        )

    if (
        "pitched" in name
        or "pbt" in name
    ):

        return _pbt_geometry(
            D,
            z,
            blades=4,
        )

    if "hydrofoil" in name:

        return _hydrofoil_geometry(
            D,
            z,
            blades=3,
        )

    if "marine" in name:

        return _marine_propeller_geometry(
            D,
            z,
            blades=3,
        )

    if (
        "helical" in name
        or "ribbon" in name
    ):

        return _helical_ribbon_geometry(
            D,
            z,
        )

    if "rci" in name:

        return _rci_geometry(
            D,
            z,
            blades=2,
        )

    # Default to PBT
    return _pbt_geometry(
        D,
        z,
        blades=4,
    )


# ============================================================
# ADD IMPELLER TO FIGURE
# ============================================================

def _add_impeller(
    fig,
    impeller,
    index,
):
    """
    Add one complete impeller assembly.
    """

    agitator = impeller.get(
        "agitator",
        "Pitched Blade Turbine",
    )

    D = _safe_float(
        impeller.get(
            "impeller_diameter_m",
            impeller.get(
                "D",
                1.0,
            ),
        ),
        1.0,
    )

    z = _safe_float(
        impeller.get(
            "elevation_from_bottom_m",
            impeller.get(
                "elevation_m",
                0.5,
            ),
        ),
        0.5,
    )

    parts = _create_impeller_geometry(
        agitator,
        D,
        z,
    )

    for pidx, part in enumerate(parts):

        x, y, zz, i, j, k = part

        _add_mesh(
            fig,
            x,
            y,
            zz,
            i,
            j,
            k,
            name=(
                f"Impeller {index + 1} "
                f"– {agitator}"
            ),
            opacity=0.95,
            showlegend=pidx == 0,
            color="#AEB8BF",
        )


# ============================================================
# BAFFLE
# ============================================================

def _add_baffles(
    fig,
    D,
    liquid_z,
    number_baffles,
    baffle_width=None,
):
    """
    Create actual rectangular vertical baffle plates.
    """

    if number_baffles <= 0:
        return

    if baffle_width is None:
        baffle_width = D * 0.06

    baffle_thickness = max(
        D * 0.015,
        0.015,
    )

    radius = D / 2.0

    baffle_radius = (
        radius -
        baffle_thickness * 2
    )

    for idx in range(
        int(number_baffles)
    ):

        angle = (
            2 *
            math.pi *
            idx /
            number_baffles
        )

        cx = (
            baffle_radius *
            math.cos(angle)
        )

        cy = (
            baffle_radius *
            math.sin(angle)
        )

        # Long plate tangent to vessel wall
        x, y, z, i, j, k = _box_mesh(
            cx,
            cy,
            liquid_z / 2.0,
            baffle_thickness,
            baffle_width,
            liquid_z,
            angle=angle,
        )

        _add_mesh(
            fig,
            x,
            y,
            z,
            i,
            j,
            k,
            name="Baffle",
            opacity=0.80,
            showlegend=idx == 0,
            color="#6F777D",
        )


# ============================================================
# LIQUID
# ============================================================

def _add_liquid(
    fig,
    D,
    straight_height,
    bottom_type,
    top_type,
    liquid_height,
    z_profile,
    r_profile,
):
    """
    Create liquid body and liquid surface.
    """

    liquid_z = max(
        0.0,
        min(
            _safe_float(liquid_height),
            _safe_float(z_profile[-1]),
        ),
    )

    if liquid_z <= 0:
        return liquid_z

    theta = np.linspace(
        0,
        2 * math.pi,
        80,
    )

    liquid_radius = radius_at_height(
        liquid_z,
        D,
        straight_height,
        bottom_type,
        top_type,
    )

    # --------------------------------------------------------
    # Liquid surface
    # --------------------------------------------------------

    liquid_x = (
        liquid_radius *
        np.cos(theta)
    )

    liquid_y = (
        liquid_radius *
        np.sin(theta)
    )

    fig.add_trace(
        go.Scatter3d(
            x=liquid_x,
            y=liquid_y,
            z=np.full_like(
                liquid_x,
                liquid_z,
            ),
            mode="lines",
            name="Liquid Surface",
            line=dict(
                width=5,
                color="#2C9FB3",
            ),
            showlegend=True,
            hovertemplate=(
                f"Liquid level = "
                f"{liquid_z:.2f} m"
                "<extra></extra>"
            ),
        )
    )

    # --------------------------------------------------------
    # Liquid body
    # --------------------------------------------------------

    mask = (
        z_profile <= liquid_z
    )

    zl = z_profile[mask]
    rl = r_profile[mask]

    if len(zl) >= 2:

        ZL, THL = np.meshgrid(
            zl,
            theta,
        )

        RL = np.tile(
            rl,
            (len(theta), 1),
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
                surfacecolor=np.ones_like(ZL),
                colorscale=[
                    [0, "#4BAFC1"],
                    [1, "#4BAFC1"],
                ],
                opacity=0.16,
                showscale=False,
                name="Liquid",
                hoverinfo="skip",
                lighting=dict(
                    ambient=0.45,
                    diffuse=0.65,
                    specular=0.25,
                    roughness=0.5,
                ),
            )
        )

        # Liquid top surface
        surface_x = (
            liquid_radius *
            np.cos(theta)
        )

        surface_y = (
            liquid_radius *
            np.sin(theta)
        )

        fig.add_trace(
            go.Mesh3d(
                x=np.concatenate(
                    [
                        surface_x,
                        [0],
                    ]
                ),
                y=np.concatenate(
                    [
                        surface_y,
                        [0],
                    ]
                ),
                z=np.concatenate(
                    [
                        np.full_like(
                            surface_x,
                            liquid_z,
                        ),
                        [liquid_z],
                    ]
                ),
                alphahull=0,
                opacity=0.08,
                color="#45B7C7",
                name="Liquid Surface",
                showlegend=False,
            )
        )

    return liquid_z


# ============================================================
# SHAFT
# ============================================================

def _add_shaft(
    fig,
    D,
    total_height,
    shaft_diameter=None,
):
    """
    Actual cylindrical agitator shaft.
    """

    if shaft_diameter is None:

        shaft_diameter = max(
            D * 0.055,
            0.035,
        )

    _add_cylinder(
        fig,
        radius=shaft_diameter / 2.0,
        z_bottom=0.0,
        z_top=total_height,
        name="Agitator Shaft",
        color="#626A70",
        opacity=0.95,
        segments=32,
        showlegend=True,
    )


# ============================================================
# VESSEL
# ============================================================

def _add_vessel(
    fig,
    z_profile,
    r_profile,
):
    """
    Add realistic shaded vessel shell.
    """

    theta = np.linspace(
        0,
        2 * math.pi,
        100,
    )

    Z, TH = np.meshgrid(
        z_profile,
        theta,
    )

    R = np.tile(
        r_profile,
        (len(theta), 1),
    )

    X = (
        R *
        np.cos(TH)
    )

    Y = (
        R *
        np.sin(TH)
    )

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=0.24,
            showscale=False,
            name="Reactor Vessel",
            hovertemplate=(
                "Reactor vessel"
                "<extra></extra>"
            ),
            colorscale=[
                [0.0, "#7D8B94"],
                [0.5, "#C7D0D5"],
                [1.0, "#66747D"],
            ],
            surfacecolor=np.tile(
                np.linspace(
                    0,
                    1,
                    len(z_profile),
                ),
                (len(theta), 1),
            ),
            lighting=dict(
                ambient=0.28,
                diffuse=0.75,
                specular=0.75,
                roughness=0.28,
                fresnel=0.35,
            ),
            lightposition=dict(
                x=200,
                y=100,
                z=300,
            ),
        )
    )


# ============================================================
# NOZZLE
# ============================================================

def _add_top_nozzle(
    fig,
    D,
    total_height,
):
    """
    Add a simple top-mounted nozzle.
    """

    nozzle_diameter = D * 0.16
    nozzle_height = D * 0.18

    _add_cylinder(
        fig,
        radius=nozzle_diameter / 2.0,
        z_bottom=total_height,
        z_top=total_height + nozzle_height,
        name="Top Nozzle",
        color="#69747A",
        opacity=0.90,
        segments=32,
        showlegend=True,
    )


# ============================================================
# OUTLET NOZZLE
# ============================================================

def _add_bottom_outlet(
    fig,
    D,
    bottom_z=0.0,
):
    """
    Add a bottom outlet nozzle.
    """

    nozzle_diameter = D * 0.12
    nozzle_length = D * 0.18

    theta = np.linspace(
        0,
        2 * math.pi,
        32,
    )

    radius = nozzle_diameter / 2.0

    x = (
        radius *
        np.cos(theta)
    )

    y = (
        radius *
        np.sin(theta)
    )

    z1 = np.full_like(
        x,
        bottom_z - nozzle_length,
    )

    z2 = np.full_like(
        x,
        bottom_z,
    )

    # Create side surface
    xx = np.concatenate(
        [x, x]
    )

    yy = np.concatenate(
        [y, y]
    )

    zz = np.concatenate(
        [z1, z2]
    )

    faces = []

    for i in range(
        len(theta)
    ):

        j = (
            i + 1
        ) % len(theta)

        faces.append(
            (
                i,
                j,
                len(theta) + j,
            )
        )

        faces.append(
            (
                i,
                len(theta) + j,
                len(theta) + i,
            )
        )

    _add_mesh(
        fig,
        xx,
        yy,
        zz,
        [f[0] for f in faces],
        [f[1] for f in faces],
        [f[2] for f in faces],
        name="Bottom Outlet",
        opacity=0.90,
        showlegend=True,
        color="#68747B",
    )


# ============================================================
# DIMENSION HELPERS
# ============================================================

def _add_dimension(
    fig,
    x1,
    y1,
    z1,
    x2,
    y2,
    z2,
    text,
    color="#333333",
):
    """
    Add dimension line + annotation.
    """

    fig.add_trace(
        go.Scatter3d(
            x=[x1, x2],
            y=[y1, y2],
            z=[z1, z2],
            mode="lines",
            line=dict(
                width=3,
                color=color,
                dash="dash",
            ),
            name=text,
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[
                (x1 + x2) / 2
            ],
            y=[
                (y1 + y2) / 2
            ],
            z=[
                (z1 + z2) / 2
            ],
            mode="text",
            text=[text],
            textfont=dict(
                size=11,
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )


# ============================================================
# REACTOR DIMENSIONS
# ============================================================

def _add_reactor_dimensions(
    fig,
    D,
    total_height,
):
    """
    Add overall diameter and height.
    """

    # Diameter
    _add_dimension(
        fig,
        -D / 2,
        0,
        0,
        D / 2,
        0,
        0,
        f"ID = {D:.2f} m",
    )

    # Height
    offset = D * 0.72

    _add_dimension(
        fig,
        offset,
        0,
        0,
        offset,
        0,
        total_height,
        f"H = {total_height:.2f} m",
    )


# ============================================================
# IMPELLER ELEVATION MARKERS
# ============================================================

def _add_impeller_elevation_markers(
    fig,
    D,
    impellers,
):
    """
    Add elevation labels for individual impellers.
    """

    for idx, impeller in enumerate(
        impellers
    ):

        z = _safe_float(
            impeller.get(
                "elevation_from_bottom_m",
                impeller.get(
                    "elevation_m",
                    0.0,
                ),
            )
        )

        agitator = impeller.get(
            "agitator",
            "Impeller",
        )

        x = D * 0.60

        fig.add_trace(
            go.Scatter3d(
                x=[x],
                y=[0],
                z=[z],
                mode="text",
                text=[
                    f"{idx + 1}: "
                    f"{agitator}<br>"
                    f"EL = {z:.2f} m"
                ],
                textfont=dict(
                    size=10,
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# MIXING TRACERS
# ============================================================

def _add_mixing_tracers(
    fig,
    D,
    liquid_z,
    frames_count=36,
):
    """
    Add animated tracer particles.
    """

    if liquid_z <= 0:
        return

    rng = np.random.default_rng(
        42
    )

    n_particles = 180

    liquid_radius = D / 2.0

    particle_r = (
        np.sqrt(
            rng.random(
                n_particles
            )
        )
        *
        liquid_radius
        *
        0.82
    )

    particle_angle = (
        rng.random(
            n_particles
        )
        *
        2 *
        math.pi
    )

    particle_z = (
        rng.random(
            n_particles
        )
        *
        liquid_z
    )

    px = (
        particle_r *
        np.cos(
            particle_angle
        )
    )

    py = (
        particle_r *
        np.sin(
            particle_angle
        )
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
                size=2.8,
                opacity=0.65,
                color="#E07A3F",
            ),
        )
    )

    frames = []

    nframes = max(
        1,
        int(frames_count),
    )

    for frame_idx in range(
        nframes
    ):

        rotation = (
            2 *
            math.pi *
            frame_idx /
            nframes
        )

        # Add slight axial circulation
        angle = (
            particle_angle +
            rotation
        )

        radial_factor = (
            1.0 +
            0.08 *
            np.sin(
                particle_z /
                max(
                    liquid_z,
                    0.001,
                )
                *
                4 *
                math.pi
                +
                rotation
            )
        )

        radius_frame = (
            particle_r *
            radial_factor
        )

        fx = (
            radius_frame *
            np.cos(angle)
        )

        fy = (
            radius_frame *
            np.sin(angle)
        )

        fz = (
            particle_z
            +
            0.035 *
            D
            *
            np.sin(
                particle_angle *
                2
                +
                rotation
            )
        )

        fz = np.clip(
            fz,
            0,
            liquid_z,
        )

        frames.append(
            go.Frame(
                name=str(
                    frame_idx
                ),
                data=[
                    go.Scatter3d(
                        x=fx,
                        y=fy,
                        z=fz,
                        mode="markers",
                        marker=dict(
                            size=2.8,
                            opacity=0.65,
                            color="#E07A3F",
                        ),
                    )
                ],
                traces=[
                    particle_trace
                ],
            )
        )

    fig.frames = frames


# ============================================================
# MAIN REACTOR 3D FUNCTION
# ============================================================

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

    # --------------------------------------------------------
    # NEW MULTI-IMPELLER INPUT
    # --------------------------------------------------------

    impellers=None,

    # --------------------------------------------------------
    # OPTIONAL DISPLAY CONTROLS
    # --------------------------------------------------------

    show_dimensions=True,
    show_nozzles=True,
    show_tracers=True,
    vessel_opacity=0.24,
    show_baffles=True,
):
    """
    Create professional interactive 3D reactor visualization.

    Backward compatible with the old single-impeller interface.

    New format:

    impellers = [
        {
            "position": "Bottom",
            "agitator": "Anchor",
            "impeller_diameter_m": 1.60,
            "elevation_from_bottom_m": 0.30,
        },
        {
            "position": "Middle",
            "agitator": "Pitched Blade Turbine",
            "impeller_diameter_m": 1.20,
            "elevation_from_bottom_m": 1.40,
        },
    ]
    """

    D = _safe_float(
        D,
        1.0,
    )

    straight_height = _safe_float(
        straight_height,
        2.0,
    )

    liquid_height = _safe_float(
        liquid_height,
        0.0,
    )

    rpm = _safe_float(
        rpm,
        120.0,
    )

    number_baffles = _safe_int(
        number_baffles,
        4,
    )

    # ========================================================
    # REACTOR PROFILE
    # ========================================================

    z_profile, r_profile = profile(
        D,
        straight_height,
        bottom_type,
        top_type,
        n_points=300,
    )

    total_height = _safe_float(
        z_profile[-1]
    )

    # ========================================================
    # CREATE FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # VESSEL
    # ========================================================

    _add_vessel(
        fig,
        z_profile,
        r_profile,
    )

    # ========================================================
    # LIQUID
    # ========================================================

    liquid_z = _add_liquid(
        fig,
        D,
        straight_height,
        bottom_type,
        top_type,
        liquid_height,
        z_profile,
        r_profile,
    )

    # ========================================================
    # SHAFT
    # ========================================================

    _add_shaft(
        fig,
        D,
        total_height,
    )

    # ========================================================
    # BAFFLES
    # ========================================================

    if show_baffles:

        _add_baffles(
            fig,
            D,
            liquid_z,
            number_baffles,
        )

    # ========================================================
    # IMPELLER CONFIGURATION
    # ========================================================

    if impellers:

        normalized_impellers = []

        for item in impellers:

            normalized_impellers.append(
                {
                    "position": item.get(
                        "position",
                        "",
                    ),
                    "agitator": item.get(
                        "agitator",
                        agitator,
                    ),
                    "impeller_diameter_m":
                        _safe_float(
                            item.get(
                                "impeller_diameter_m",
                                item.get(
                                    "D",
                                    impeller_diameter,
                                ),
                            ),
                            impeller_diameter,
                        ),
                    "elevation_from_bottom_m":
                        _safe_float(
                            item.get(
                                "elevation_from_bottom_m",
                                item.get(
                                    "elevation_m",
                                    0.0,
                                ),
                            ),
                            0.0,
                        ),
                }
            )

    else:

        nimp = max(
            1,
            _safe_int(
                number_impellers,
                1,
            ),
        )

        # ----------------------------------------------------
        # Legacy positioning
        # ----------------------------------------------------

        if nimp == 1:

            positions = [
                min(
                    liquid_z * 0.25,
                    liquid_z,
                )
            ]

        else:

            positions = np.linspace(
                liquid_z * 0.20,
                liquid_z * 0.80,
                nimp,
            )

        normalized_impellers = []

        for z_imp in positions:

            normalized_impellers.append(
                {
                    "position": "Auto",
                    "agitator": agitator,
                    "impeller_diameter_m":
                        _safe_float(
                            impeller_diameter,
                            1.0,
                        ),
                    "elevation_from_bottom_m":
                        _safe_float(
                            z_imp
                        ),
                }
            )

    # ========================================================
    # ADD EACH REAL IMPELLER
    # ========================================================

    for idx, impeller in enumerate(
        normalized_impellers
    ):

        _add_impeller(
            fig,
            impeller,
            idx,
        )

    # ========================================================
    # IMPELLER ELEVATION LABELS
    # ========================================================

    if show_dimensions:

        _add_impeller_elevation_markers(
            fig,
            D,
            normalized_impellers,
        )

    # ========================================================
    # NOZZLES
    # ========================================================

    if show_nozzles:

        _add_top_nozzle(
            fig,
            D,
            total_height,
        )

        _add_bottom_outlet(
            fig,
            D,
            bottom_z=0.0,
        )

    # ========================================================
    # DIMENSIONS
    # ========================================================

    if show_dimensions:

        _add_reactor_dimensions(
            fig,
            D,
            total_height,
        )

    # ========================================================
    # MIXING TRACERS
    # ========================================================

    if show_tracers:

        _add_mixing_tracers(
            fig,
            D,
            liquid_z,
            frames_count=frames_count,
        )

    # ========================================================
    # CONTROL BUTTONS
    # ========================================================

    if show_tracers:

        fig.update_layout(
            updatemenus=[
                {
                    "type": "buttons",
                    "direction": "left",
                    "showactive": True,
                    "x": 0.02,
                    "y": 0.02,
                    "xanchor": "left",
                    "yanchor": "bottom",
                    "buttons": [
                        {
                            "label": "▶ Start Mixing",
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
                                    "mode": "immediate",
                                },
                            ],
                        },
                    ],
                }
            ]
        )

    # ========================================================
    # TITLE
    # ========================================================

    if normalized_impellers:

        impeller_names = ", ".join(
            [
                str(
                    x.get(
                        "agitator",
                        "Impeller",
                    )
                )
                for x in normalized_impellers
            ]
        )

    else:

        impeller_names = str(
            agitator
        )

    fig.update_layout(
        title=dict(
            text=(
                "3D Reactor Equipment Model"
                f"<br><sup>"
                f"ID = {D:.2f} m | "
                f"Liquid Height = {liquid_z:.2f} m | "
                f"{rpm:.0f} RPM"
                f"</sup>"
            ),
            x=0.5,
            xanchor="center",
        ),

        # ====================================================
        # 3D SCENE
        # ====================================================

        scene=dict(

            xaxis=dict(
                title="X (m)",
                showbackground=True,
                backgroundcolor="#F4F6F7",
                gridcolor="#D5DADD",
                zerolinecolor="#AAB2B7",
            ),

            yaxis=dict(
                title="Y (m)",
                showbackground=True,
                backgroundcolor="#F4F6F7",
                gridcolor="#D5DADD",
                zerolinecolor="#AAB2B7",
            ),

            zaxis=dict(
                title="Elevation (m)",
                showbackground=True,
                backgroundcolor="#F4F6F7",
                gridcolor="#D5DADD",
                zerolinecolor="#AAB2B7",
            ),

            aspectmode="manual",

            aspectratio=dict(
                x=1,
                y=1,
                z=max(
                    1.15,
                    total_height /
                    max(
                        D,
                        0.1,
                    ),
                ),
            ),

            camera=dict(
                eye=dict(
                    x=1.65,
                    y=1.65,
                    z=1.15,
                ),
                center=dict(
                    x=0,
                    y=0,
                    z=0,
                ),
            ),
        ),

        # ====================================================
        # SIZE
        # ====================================================

        height=760,

        margin=dict(
            l=0,
            r=0,
            t=80,
            b=0,
        ),

        # ====================================================
        # LEGEND
        # ====================================================

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0.75)",
        ),

        # ====================================================
        # HOVER
        # ====================================================

        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
        ),

        # ====================================================
        # PAPER
        # ====================================================

        paper_bgcolor="white",
        plot_bgcolor="white",

        # ====================================================
        # DRAG MODE
        # ====================================================

        scene_dragmode="orbit",
    )

    return fig


# ============================================================
# SIMPLE 3D FUNCTION
# ============================================================

def create_reactor_3d(**kwargs):

    return create_reactor_animation(
        **kwargs
    )
