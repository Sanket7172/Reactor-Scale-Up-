# ============================================================
# visualization/reactor_3d.py
# Advanced 3D Reactor Mixing Visualization
#
# Includes:
#   - Parametric reactor geometry
#   - Multiple impellers
#   - 3D circulation field
#   - Streamlines
#   - Vortex/free-surface depression
#   - Animated tracer particles
#   - Impeller rotation indication
#
# NOTE:
# This is a parametric engineering visualization, NOT CFD.
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
        value = float(value)
        if not np.isfinite(value):
            return float(default)
        return value
    except Exception:
        return float(default)


def _safe_int(value, default=1):
    try:
        return int(value)
    except Exception:
        return int(default)


def _clamp(value, low, high):
    return max(low, min(high, value))


def _rotate_xy(x, y, angle):
    """Rotate XY coordinates around reactor shaft."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    ca = math.cos(angle)
    sa = math.sin(angle)

    xr = x * ca - y * sa
    yr = x * sa + y * ca

    return xr, yr


# ============================================================
# IMPELLER FLOW CHARACTERISTICS
# ============================================================

def _impeller_flow_characteristics(agitator):
    """
    Returns approximate normalized flow characteristics.

    axial:
        axial pumping tendency

    radial:
        radial pumping tendency

    swirl:
        tangential flow tendency

    circulation:
        strength of bulk circulation

    These are visualization coefficients only.
    """

    name = str(agitator).lower()

    if "anchor" in name:
        return {
            "axial": 0.30,
            "radial": 0.45,
            "swirl": 0.80,
            "circulation": 0.55,
        }

    if "rushton" in name:
        return {
            "axial": 0.15,
            "radial": 1.00,
            "swirl": 0.75,
            "circulation": 0.65,
        }

    if "pitched" in name or "pbt" in name:
        return {
            "axial": 0.85,
            "radial": 0.55,
            "swirl": 0.65,
            "circulation": 0.90,
        }

    if "hydrofoil" in name:
        return {
            "axial": 1.00,
            "radial": 0.25,
            "swirl": 0.35,
            "circulation": 1.00,
        }

    if "marine" in name:
        return {
            "axial": 0.95,
            "radial": 0.30,
            "swirl": 0.55,
            "circulation": 0.95,
        }

    if "helical" in name or "ribbon" in name:
        return {
            "axial": 0.75,
            "radial": 0.40,
            "swirl": 0.90,
            "circulation": 0.85,
        }

    if "rci" in name:
        return {
            "axial": 0.35,
            "radial": 0.90,
            "swirl": 0.65,
            "circulation": 0.70,
        }

    return {
        "axial": 0.70,
        "radial": 0.50,
        "swirl": 0.55,
        "circulation": 0.80,
    }


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
    """Create rectangular solid."""

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

    x = (
        vertices[:, 0] * ca
        - vertices[:, 1] * sa
    )

    y = (
        vertices[:, 0] * sa
        + vertices[:, 1] * ca
    )

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
    """Add shaded 3D solid."""

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
    """Generate cylindrical solid."""

    theta = np.linspace(
        0,
        2 * math.pi,
        segments,
        endpoint=False,
    )

    xb = (
        center_x
        + radius * np.cos(theta)
    )

    yb = (
        center_y
        + radius * np.sin(theta)
    )

    xt = (
        center_x
        + radius * np.cos(theta)
    )

    yt = (
        center_y
        + radius * np.sin(theta)
    )

    x = np.concatenate(
        [
            xb,
            xt,
            [center_x],
            [center_x],
        ]
    )

    y = np.concatenate(
        [
            yb,
            yt,
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

    for n in range(segments):

        n2 = (n + 1) % segments

        faces.append(
            (n, n2, segments + n)
        )

        faces.append(
            (
                n2,
                segments + n2,
                segments + n,
            )
        )

    bottom_center = 2 * segments
    top_center = 2 * segments + 1

    for n in range(segments):

        n2 = (n + 1) % segments

        faces.append(
            (
                bottom_center,
                n2,
                n,
            )
        )

        faces.append(
            (
                top_center,
                segments + n,
                segments + n2,
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

def _anchor_geometry(D, z, thickness=None):

    radius = D / 2.0

    if thickness is None:
        thickness = max(
            0.025 * D,
            0.025,
        )

    parts = []

    # Horizontal lower arm
    parts.append(
        _box_mesh(
            0,
            0,
            z,
            radius * 1.75,
            thickness,
            thickness,
        )
    )

    # Vertical legs
    leg_height = max(
        D * 0.55,
        0.15,
    )

    leg_offset = radius * 0.82

    for direction in [-1, 1]:

        parts.append(
            _box_mesh(
                direction * leg_offset,
                0,
                z + leg_height / 2.0,
                thickness,
                thickness,
                leg_height,
            )
        )

    # Cross arm
    parts.append(
        _box_mesh(
            0,
            0,
            z + leg_height,
            radius * 1.65,
            thickness,
            thickness,
            angle=math.pi / 2,
        )
    )

    return parts


def _rushton_geometry(D, z, blades=6):

    radius = D / 2.0

    parts = []

    disk_radius = radius * 0.38
    disk_thickness = max(
        0.035 * D,
        0.02,
    )

    parts.append(
        _cylinder_mesh(
            disk_radius,
            z - disk_thickness / 2,
            z + disk_thickness / 2,
            segments=40,
        )
    )

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
            2 * math.pi * n / blades
        )

        cx = (
            radius
            * 0.62
            * math.cos(angle)
        )

        cy = (
            radius
            * 0.62
            * math.sin(angle)
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


def _pbt_geometry(D, z, blades=4):

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

    parts.append(
        _cylinder_mesh(
            hub_radius,
            z - hub_height / 2,
            z + hub_height / 2,
            segments=32,
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
            2 * math.pi * n / blades
        )

        cx = (
            radius
            * 0.50
            * math.cos(angle)
        )

        cy = (
            radius
            * 0.50
            * math.sin(angle)
        )

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

        # Correct local pitch transformation
        local_x = px - cx
        local_y = py - cy
        local_z = pz - z

        cp = math.cos(pitch_angle)
        sp = math.sin(pitch_angle)

        pitched_x = (
            local_x * cp
            - local_z * sp
        )

        pitched_z = (
            local_x * sp
            + local_z * cp
        )

        px = pitched_x + cx
        py = local_y + cy
        pz = pitched_z + z

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


def _hydrofoil_geometry(D, z, blades=3):

    radius = D / 2.0

    parts = []

    hub_radius = D * 0.12
    hub_height = D * 0.18

    parts.append(
        _cylinder_mesh(
            hub_radius,
            z - hub_height / 2,
            z + hub_height / 2,
            segments=32,
        )
    )

    for n in range(blades):

        angle = (
            2 * math.pi * n / blades
        )

        r1 = radius * 0.18
        r2 = radius * 0.90

        width1 = D * 0.12
        width2 = D * 0.06

        vertices = np.array(
            [
                [r1, -width1 / 2, -0.025 * D],
                [r2, -width2 / 2, -0.015 * D],
                [r2,  width2 / 2,  0.015 * D],
                [r1,  width1 / 2,  0.025 * D],
            ],
            dtype=float,
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

        zz = vertices[:, 2] + z

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
                zz,
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

    radius = D / 2.0

    parts = []

    hub_radius = D * 0.13
    hub_height = D * 0.30

    parts.append(
        _cylinder_mesh(
            hub_radius,
            z - hub_height / 2,
            z + hub_height / 2,
            segments=32,
        )
    )

    for n in range(blades):

        angle = (
            2 * math.pi * n / blades
        )

        r1 = radius * 0.18
        r2 = radius * 0.92

        w1 = D * 0.14
        w2 = D * 0.045

        vertices = np.array(
            [
                [r1, -w1 / 2, -D * 0.04],
                [r2, -w2 / 2,  D * 0.04],
                [r2,  w2 / 2, -D * 0.04],
                [r1,  w1 / 2,  D * 0.04],
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

        zz = vertices[:, 2] + z

        parts.append(
            (
                xx,
                yy,
                zz,
                [0, 0],
                [1, 2],
                [2, 3],
            )
        )

    return parts


def _helical_ribbon_geometry(D, z):

    radius = D / 2.0 * 0.88
    height = D * 0.85

    turns = 1.15
    n = 100

    theta = np.linspace(
        0,
        2 * math.pi * turns,
        n,
    )

    zz = (
        z
        - height / 2
        + height
        * np.linspace(0, 1, n)
    )

    width = D * 0.08

    x1 = radius * np.cos(theta)
    y1 = radius * np.sin(theta)

    x2 = (
        radius - width
    ) * np.cos(theta)

    y2 = (
        radius - width
    ) * np.sin(theta)

    x = np.concatenate([x1, x2])
    y = np.concatenate([y1, y2])
    z_all = np.concatenate([zz, zz])

    faces = []

    for idx in range(n - 1):

        faces.append(
            (
                idx,
                idx + 1,
                n + idx + 1,
            )
        )

        faces.append(
            (
                idx,
                n + idx + 1,
                n + idx,
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


def _rci_geometry(D, z, blades=2):

    radius = D / 2.0

    parts = []

    hub_radius = D * 0.13
    hub_height = D * 0.20

    parts.append(
        _cylinder_mesh(
            hub_radius,
            z - hub_height / 2,
            z + hub_height / 2,
            segments=32,
        )
    )

    for n in range(blades):

        angle = (
            2 * math.pi * n / blades
        )

        theta = np.linspace(
            -math.pi / 3,
            math.pi / 3,
            30,
        )

        r = radius * (
            0.25
            + 0.65
            * (1 - np.cos(theta))
            / 2
        )

        x = r * np.cos(
            theta + angle
        )

        y = r * np.sin(
            theta + angle
        )

        width = D * 0.06

        x2 = (
            r - width
        ) * np.cos(
            theta + angle
        )

        y2 = (
            r - width
        ) * np.sin(
            theta + angle
        )

        z1 = (
            z
            + 0.025
            * D
            * np.sin(theta)
        )

        z2 = (
            z
            - 0.025
            * D
            * np.sin(theta)
        )

        xx = np.concatenate([x, x2])
        yy = np.concatenate([y, y2])
        zz = np.concatenate([z1, z2])

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
                zz,
                [f[0] for f in faces],
                [f[1] for f in faces],
                [f[2] for f in faces],
            )
        )

    return parts


# ============================================================
# IMPELLER FACTORY
# ============================================================

def _create_impeller_geometry(
    agitator,
    D,
    z,
):
    """Select physical impeller geometry."""

    name = str(agitator).strip().lower()

    if "anchor" in name:
        return _anchor_geometry(D, z)

    if "rushton" in name:
        return _rushton_geometry(
            D,
            z,
            blades=6,
        )

    if "pitched" in name or "pbt" in name:
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

    if "helical" in name or "ribbon" in name:
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

    return _pbt_geometry(
        D,
        z,
        blades=4,
    )


# ============================================================
# ADD IMPELLER
# ============================================================

def _add_impeller(
    fig,
    impeller,
    index,
):

    agitator = impeller.get(
        "agitator",
        "Pitched Blade Turbine",
    )

    D = _safe_float(
        impeller.get(
            "impeller_diameter_m",
            impeller.get("D", 1.0),
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
                f"Impeller {index + 1}"
                f" – {agitator}"
            ),
            opacity=0.95,
            showlegend=pidx == 0,
            color="#AEB8BF",
        )


# ============================================================
# BAFFLES
# ============================================================

def _add_baffles(
    fig,
    D,
    liquid_z,
    number_baffles,
    baffle_width=None,
):

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
        radius
        - baffle_thickness * 2
    )

    for idx in range(
        int(number_baffles)
    ):

        angle = (
            2 * math.pi
            * idx
            / number_baffles
        )

        cx = (
            baffle_radius
            * math.cos(angle)
        )

        cy = (
            baffle_radius
            * math.sin(angle)
        )

        x, y, z, i, j, k = _box_mesh(
            cx,
            cy,
            liquid_z / 2,
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
            opacity=0.72,
            showlegend=idx == 0,
            color="#6F777D",
        )


# ============================================================
# VORTEX / LIQUID SURFACE
# ============================================================

def _calculate_vortex_depth(
    D,
    liquid_z,
    rpm,
    impellers,
    user_vortex_depth=0.0,
):
    """
    Estimate visualization vortex depth.

    This is NOT a CFD/free-surface calculation.

    The model increases vortex depth with:
        - RPM
        - impeller diameter
        - liquid height
        - impeller count
        - tangential flow tendency
    """

    if liquid_z <= 0:
        return 0.0

    if user_vortex_depth > 0:
        return min(
            user_vortex_depth,
            liquid_z * 0.45,
        )

    if not impellers:
        return 0.0

    max_D = 0.0
    swirl_sum = 0.0

    for imp in impellers:

        d = _safe_float(
            imp.get(
                "impeller_diameter_m",
                imp.get("D", D * 0.4),
            ),
            D * 0.4,
        )

        max_D = max(
            max_D,
            d,
        )

        characteristics = (
            _impeller_flow_characteristics(
                imp.get(
                    "agitator",
                    "PBT",
                )
            )
        )

        swirl_sum += (
            characteristics["swirl"]
            * characteristics["circulation"]
        )

    swirl_avg = (
        swirl_sum
        / max(len(impellers), 1)
    )

    rpm_factor = _clamp(
        rpm / 180.0,
        0.0,
        2.0,
    )

    diameter_factor = _clamp(
        max_D / max(D, 0.001),
        0.05,
        1.0,
    )

    count_factor = _clamp(
        0.75
        + 0.12 * len(impellers),
        0.75,
        1.20,
    )

    # Empirical visualization coefficient
    depth = (
        0.025
        * liquid_z
        * rpm_factor
        * diameter_factor
        * swirl_avg
        * count_factor
    )

    return _clamp(
        depth,
        0.0,
        liquid_z * 0.32,
    )


def _vortex_surface(
    radius,
    liquid_z,
    vortex_depth,
    n_radial=24,
    n_theta=64,
    phase=0.0,
):
    """
    Create a 3D free surface with center depression.
    """

    r = np.linspace(
        0.0,
        radius * 0.995,
        n_radial,
    )

    theta = np.linspace(
        0.0,
        2 * math.pi,
        n_theta,
    )

    R, TH = np.meshgrid(
        r,
        theta,
    )

    normalized_r = (
        R / max(radius, 1e-9)
    )

    # Strongest depression at shaft
    depression = (
        vortex_depth
        * np.power(
            1.0 - normalized_r ** 2,
            1.55,
        )
    )

    # Small wave disturbance
    ripple = (
        0.012
        * max(radius, 0.1)
        * np.sin(
            3.0 * TH
            - phase
        )
        * np.power(
            normalized_r,
            1.5,
        )
    )

    Z = (
        liquid_z
        - depression
        + ripple
    )

    X = R * np.cos(TH)
    Y = R * np.sin(TH)

    return X, Y, Z


def _add_liquid(
    fig,
    D,
    straight_height,
    bottom_type,
    top_type,
    liquid_height,
    z_profile,
    r_profile,
    vortex_depth=0.0,
):
    """
    Add liquid body and vortex surface.
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
        90,
    )

    liquid_radius = radius_at_height(
        liquid_z,
        D,
        straight_height,
        bottom_type,
        top_type,
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
            RL
            * np.cos(THL)
        )

        YL = (
            RL
            * np.sin(THL)
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
                opacity=0.105,
                showscale=False,
                name="Liquid",
                hoverinfo="skip",
                lighting=dict(
                    ambient=0.50,
                    diffuse=0.70,
                    specular=0.30,
                    roughness=0.45,
                ),
            )
        )

    # --------------------------------------------------------
    # VORTEX SURFACE
    # --------------------------------------------------------

    VX, VY, VZ = _vortex_surface(
        liquid_radius,
        liquid_z,
        vortex_depth,
        n_radial=28,
        n_theta=90,
    )

    fig.add_trace(
        go.Surface(
            x=VX,
            y=VY,
            z=VZ,
            surfacecolor=VZ,
            colorscale=[
                [0.0, "#197F96"],
                [0.45, "#2C9FB3"],
                [1.0, "#69C5D0"],
            ],
            opacity=0.38,
            showscale=False,
            name="Vortex Surface",
            hovertemplate=(
                "Vortex surface"
                "<br>Elevation = %{z:.2f} m"
                "<extra></extra>"
            ),
            lighting=dict(
                ambient=0.55,
                diffuse=0.75,
                specular=0.45,
                roughness=0.25,
            ),
        )
    )

    # Liquid level ring
    ring_theta = np.linspace(
        0,
        2 * math.pi,
        120,
    )

    ring_x = (
        liquid_radius
        * np.cos(ring_theta)
    )

    ring_y = (
        liquid_radius
        * np.sin(ring_theta)
    )

    ring_z = np.full_like(
        ring_x,
        liquid_z,
    )

    fig.add_trace(
        go.Scatter3d(
            x=ring_x,
            y=ring_y,
            z=ring_z,
            mode="lines",
            name="Liquid Level",
            line=dict(
                width=4,
                color="#2C9FB3",
            ),
            hovertemplate=(
                f"Liquid Level = "
                f"{liquid_z:.2f} m"
                "<extra></extra>"
            ),
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

    if shaft_diameter is None:
        shaft_diameter = max(
            D * 0.055,
            0.035,
        )

    _add_cylinder(
        fig,
        radius=shaft_diameter / 2,
        z_bottom=0.0,
        z_top=total_height,
        name="Agitator Shaft",
        color="#626A70",
        opacity=0.92,
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
    opacity=0.24,
):

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
        R
        * np.cos(TH)
    )

    Y = (
        R
        * np.sin(TH)
    )

    fig.add_trace(
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            opacity=opacity,
            showscale=False,
            name="Reactor Vessel",
            hovertemplate=(
                "Reactor Vessel"
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
# NOZZLES
# ============================================================

def _add_top_nozzle(
    fig,
    D,
    total_height,
):

    nozzle_diameter = D * 0.16
    nozzle_height = D * 0.18

    _add_cylinder(
        fig,
        radius=nozzle_diameter / 2,
        z_bottom=total_height,
        z_top=(
            total_height
            + nozzle_height
        ),
        name="Top Nozzle",
        color="#69747A",
        opacity=0.90,
        segments=32,
        showlegend=True,
    )


def _add_bottom_outlet(
    fig,
    D,
    bottom_z=0.0,
):

    nozzle_diameter = D * 0.12
    nozzle_length = D * 0.18

    theta = np.linspace(
        0,
        2 * math.pi,
        32,
    )

    radius = nozzle_diameter / 2

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)

    z1 = np.full_like(
        x,
        bottom_z - nozzle_length,
    )

    z2 = np.full_like(
        x,
        bottom_z,
    )

    xx = np.concatenate([x, x])
    yy = np.concatenate([y, y])
    zz = np.concatenate([z1, z2])

    faces = []

    for i in range(len(theta)):

        j = (i + 1) % len(theta)

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
# DIMENSIONS
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
):

    fig.add_trace(
        go.Scatter3d(
            x=[x1, x2],
            y=[y1, y2],
            z=[z1, z2],
            mode="lines",
            line=dict(
                width=3,
                dash="dash",
            ),
            name=text,
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[(x1 + x2) / 2],
            y=[(y1 + y2) / 2],
            z=[(z1 + z2) / 2],
            mode="text",
            text=[text],
            textfont=dict(size=11),
            showlegend=False,
            hoverinfo="skip",
        )
    )


def _add_reactor_dimensions(
    fig,
    D,
    total_height,
):

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
# IMPELLER ELEVATION LABELS
# ============================================================

def _add_impeller_elevation_markers(
    fig,
    D,
    impellers,
):

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
# FLOW FIELD
# ============================================================

def _flow_velocity(
    x,
    y,
    z,
    D,
    liquid_z,
    impellers,
    rpm,
    number_baffles=4,
):
    """
    Parametric stirred-tank velocity field.

    Cylindrical coordinates:
        r     = radial position
        theta = azimuth
        z     = elevation

    The field combines:
        - impeller radial pumping
        - axial circulation
        - tangential swirl
        - vertical recirculation
        - wall damping
        - baffle damping

    This is intended for visualization, not CFD prediction.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)

    r = np.sqrt(
        x * x + y * y
    )

    r_safe = np.maximum(
        r,
        D * 0.015,
    )

    theta = np.arctan2(
        y,
        x,
    )

    H = max(
        liquid_z,
        D * 0.1,
    )

    # --------------------------------------------------------
    # Overall scale
    # --------------------------------------------------------

    rpm_factor = _clamp(
        rpm / 120.0,
        0.15,
        3.0,
    )

    velocity_scale = (
        0.16
        * D
        * rpm_factor
    )

    u_r = np.zeros_like(x)
    u_theta = np.zeros_like(x)
    u_z = np.zeros_like(x)

    # --------------------------------------------------------
    # Each impeller contributes to local flow
    # --------------------------------------------------------

    for impeller in impellers:

        imp_D = _safe_float(
            impeller.get(
                "impeller_diameter_m",
                impeller.get(
                    "D",
                    D * 0.4,
                ),
            ),
            D * 0.4,
        )

        imp_z = _safe_float(
            impeller.get(
                "elevation_from_bottom_m",
                impeller.get(
                    "elevation_m",
                    H * 0.5,
                ),
            ),
            H * 0.5,
        )

        agitator = impeller.get(
            "agitator",
            "PBT",
        )

        characteristics = (
            _impeller_flow_characteristics(
                agitator
            )
        )

        axial = characteristics["axial"]
        radial = characteristics["radial"]
        swirl = characteristics["swirl"]
        circulation = characteristics["circulation"]

        # ----------------------------------------------------
        # Impeller influence zone
        # ----------------------------------------------------

        influence_radius = (
            max(
                imp_D * 1.35,
                D * 0.20,
            )
        )

        influence_height = (
            max(
                imp_D * 1.05,
                H * 0.15,
            )
        )

        radial_distance = (
            r / max(
                imp_D / 2,
                0.001,
            )
        )

        vertical_distance = (
            (z - imp_z)
            / influence_height
        )

        radial_weight = np.exp(
            -(
                radial_distance
                / 2.2
            ) ** 4
        )

        vertical_weight = np.exp(
            -(
                vertical_distance
                / 1.5
            ) ** 2
        )

        weight = (
            radial_weight
            * vertical_weight
        )

        # ----------------------------------------------------
        # Radial pumping
        # ----------------------------------------------------

        radial_profile = (
            np.tanh(
                (r - imp_D * 0.12)
                / max(
                    imp_D * 0.18,
                    0.001,
                )
            )
        )

        u_r += (
            velocity_scale
            * radial
            * circulation
            * weight
            * radial_profile
        )

        # ----------------------------------------------------
        # Tangential rotation
        # ----------------------------------------------------

        swirl_profile = np.exp(
            -(
                r
                / max(
                    imp_D * 1.15,
                    0.001,
                )
            ) ** 2
        )

        u_theta += (
            velocity_scale
            * swirl
            * weight
            * swirl_profile
        )

        # ----------------------------------------------------
        # Axial pumping
        # ----------------------------------------------------

        direction = (
            1.0
            if imp_z < H * 0.55
            else -1.0
        )

        # Hydrofoil / PBT generally stronger axial flow
        axial_shape = np.sin(
            math.pi
            * _clamp(
                z / H,
                0.0,
                1.0,
            )
        )

        u_z += (
            velocity_scale
            * axial
            * circulation
            * weight
            * direction
            * axial_shape
        )

        # ----------------------------------------------------
        # Global circulation loop
        # ----------------------------------------------------

        distance_from_impeller = (
            (z - imp_z)
            / max(H, 0.001)
        )

        loop = np.sin(
            math.pi
            * _clamp(
                z / H,
                0.0,
                1.0,
            )
        )

        u_z += (
            velocity_scale
            * 0.30
            * circulation
            * loop
            * np.exp(
                -(
                    r
                    / max(
                        D * 0.42,
                        0.001,
                    )
                ) ** 2
            )
        )

    # --------------------------------------------------------
    # Wall damping
    # --------------------------------------------------------

    wall_ratio = (
        r / max(D / 2, 0.001)
    )

    wall_damping = np.clip(
        1.0
        - 0.55
        * np.maximum(
            wall_ratio - 0.70,
            0.0,
        ) / 0.30,
        0.25,
        1.0,
    )

    u_r *= wall_damping
    u_theta *= wall_damping
    u_z *= wall_damping

    # --------------------------------------------------------
    # Baffle effect
    # --------------------------------------------------------

    if number_baffles > 0:

        baffle_phase = (
            number_baffles
            * theta
        )

        baffle_damping = (
            0.78
            + 0.22
            * np.abs(
                np.sin(
                    baffle_phase / 2
                )
            )
        )

        u_theta *= baffle_damping

    # --------------------------------------------------------
    # Convert cylindrical -> Cartesian
    # --------------------------------------------------------

    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    u_x = (
        u_r * cos_t
        - u_theta * sin_t
    )

    u_y = (
        u_r * sin_t
        + u_theta * cos_t
    )

    # --------------------------------------------------------
    # Keep flow inside reactor
    # --------------------------------------------------------

    near_wall = (
        wall_ratio > 0.92
    )

    u_x = np.where(
        near_wall,
        u_x * 0.35,
        u_x,
    )

    u_y = np.where(
        near_wall,
        u_y * 0.35,
        u_y,
    )

    return u_x, u_y, u_z


# ============================================================
# STREAMLINE INTEGRATION
# ============================================================

def _integrate_streamline(
    seed,
    D,
    liquid_z,
    impellers,
    rpm,
    number_baffles,
    steps=90,
    dt=0.055,
):
    """
    Integrate a streamline through the parametric velocity field.
    """

    point = np.asarray(
        seed,
        dtype=float,
    )

    points = [point.copy()]

    radius_limit = D * 0.47

    for _ in range(steps):

        x, y, z = point

        r = math.sqrt(
            x * x + y * y
        )

        if r >= radius_limit:
            break

        if z <= 0.03:
            break

        if z >= liquid_z - 0.03:
            break

        ux, uy, uz = _flow_velocity(
            np.array([x]),
            np.array([y]),
            np.array([z]),
            D,
            liquid_z,
            impellers,
            rpm,
            number_baffles,
        )

        velocity = np.array(
            [
                ux[0],
                uy[0],
                uz[0],
            ]
        )

        speed = np.linalg.norm(
            velocity
        )

        if speed < 1e-8:
            break

        # Normalize to prevent numerical explosion
        direction = (
            velocity
            / speed
        )

        point = (
            point
            + direction * D * dt
        )

        # Reflect gently from boundaries
        new_r = math.sqrt(
            point[0] ** 2
            + point[1] ** 2
        )

        if new_r > radius_limit:

            factor = (
                radius_limit
                / max(
                    new_r,
                    1e-9,
                )
            )

            point[0] *= factor
            point[1] *= factor

        point[2] = _clamp(
            point[2],
            0.04,
            liquid_z - 0.04,
        )

        points.append(
            point.copy()
        )

    if len(points) < 4:
        return None

    return np.asarray(points)


def _generate_streamlines(
    D,
    liquid_z,
    impellers,
    rpm,
    number_baffles,
):
    """
    Generate multiple 3D circulation streamlines.
    """

    if liquid_z <= 0 or not impellers:
        return []

    seeds = []

    # Several radial rings
    seed_radii = [
        D * 0.10,
        D * 0.18,
        D * 0.27,
        D * 0.35,
    ]

    seed_heights = np.linspace(
        max(
            0.08,
            liquid_z * 0.12,
        ),
        min(
            liquid_z * 0.88,
            liquid_z,
        ),
        5,
    )

    n_angles = 8

    for rr in seed_radii:

        for zz in seed_heights:

            for j in range(
                n_angles
            ):

                angle = (
                    2
                    * math.pi
                    * j
                    / n_angles
                )

                seeds.append(
                    (
                        rr * math.cos(angle),
                        rr * math.sin(angle),
                        zz,
                    )
                )

    streamlines = []

    for seed in seeds:

        line = _integrate_streamline(
            seed,
            D,
            liquid_z,
            impellers,
            rpm,
            number_baffles,
            steps=70,
            dt=0.065,
        )

        if line is not None:

            # Avoid excessive number of lines
            if len(streamlines) < 70:
                streamlines.append(
                    line
                )

    return streamlines


def _add_streamlines(
    fig,
    streamlines,
):
    """
    Add 3D circulation streamlines.
    """

    if not streamlines:
        return

    for idx, line in enumerate(
        streamlines
    ):

        # Add a small arrow-like marker at the end
        x = line[:, 0]
        y = line[:, 1]
        z = line[:, 2]

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                name=(
                    "3D Flow Streamlines"
                    if idx == 0
                    else "Flow"
                ),
                showlegend=idx == 0,
                line=dict(
                    width=2.2,
                    color="#E88935",
                ),
                opacity=0.70,
                hoverinfo="skip",
            )
        )


# ============================================================
# FLOW DIRECTION VECTORS
# ============================================================

def _add_flow_vectors(
    fig,
    D,
    liquid_z,
    impellers,
    rpm,
    number_baffles,
):
    """
    Add selected 3D velocity direction arrows.
    """

    if liquid_z <= 0:
        return

    radial_positions = [
        D * 0.16,
        D * 0.28,
        D * 0.38,
    ]

    heights = np.linspace(
        liquid_z * 0.18,
        liquid_z * 0.82,
        4,
    )

    angles = np.linspace(
        0,
        2 * math.pi,
        8,
        endpoint=False,
    )

    for rr in radial_positions:

        for zz in heights:

            for angle in angles:

                x = rr * math.cos(angle)
                y = rr * math.sin(angle)

                ux, uy, uz = _flow_velocity(
                    np.array([x]),
                    np.array([y]),
                    np.array([zz]),
                    D,
                    liquid_z,
                    impellers,
                    rpm,
                    number_baffles,
                )

                vx = ux[0]
                vy = uy[0]
                vz = uz[0]

                mag = math.sqrt(
                    vx * vx
                    + vy * vy
                    + vz * vz
                )

                if mag < 1e-8:
                    continue

                scale = (
                    D * 0.10
                    / max(
                        mag,
                        1e-8,
                    )
                )

                # Keep vector length reasonable
                scale = _clamp(
                    scale,
                    0.025,
                    0.18,
                )

                x2 = x + vx * scale
                y2 = y + vy * scale
                z2 = _clamp(
                    zz + vz * scale,
                    0.02,
                    liquid_z - 0.02,
                )

                fig.add_trace(
                    go.Scatter3d(
                        x=[x, x2],
                        y=[y, y2],
                        z=[zz, z2],
                        mode="lines",
                        line=dict(
                            width=2,
                            color="#C95E28",
                        ),
                        name="Flow Direction",
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )


# ============================================================
# VORTEX CENTERLINE
# ============================================================

def _add_vortex_core(
    fig,
    D,
    liquid_z,
    vortex_depth,
):
    """
    Add visible vortex core around shaft.
    """

    if vortex_depth <= 0:
        return

    theta = np.linspace(
        0,
        2 * math.pi * 2.5,
        180,
    )

    radius = (
        D * 0.035
        + D * 0.018
        * np.sin(theta * 2)
    )

    z = (
        liquid_z
        - vortex_depth
        + 0.02
        * D
        * np.sin(theta)
    )

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            name="Vortex Core",
            line=dict(
                width=5,
                color="#126B7A",
            ),
            opacity=0.80,
            hovertemplate=(
                "Vortex Core"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# MIXING TRACERS
# ============================================================

def _initialize_tracers(
    D,
    liquid_z,
    n_particles=220,
):
    """
    Generate initial tracer particles.
    """

    rng = np.random.default_rng(
        42
    )

    particle_r = (
        np.sqrt(
            rng.random(
                n_particles
            )
        )
        * D
        * 0.40
    )

    particle_angle = (
        rng.random(
            n_particles
        )
        * 2
        * math.pi
    )

    particle_z = (
        0.05
        + rng.random(
            n_particles
        )
        * max(
            liquid_z - 0.10,
            0.05,
        )
    )

    px = (
        particle_r
        * np.cos(
            particle_angle
        )
    )

    py = (
        particle_r
        * np.sin(
            particle_angle
        )

    return (
        px,
        py,
        particle_z,
    )


def _advance_particles(
    px,
    py,
    pz,
    D,
    liquid_z,
    impellers,
    rpm,
    number_baffles,
    dt=0.20,
):
    """
    Advance particles using the parametric flow field.
    """

    ux, uy, uz = _flow_velocity(
        px,
        py,
        pz,
        D,
        liquid_z,
        impellers,
        rpm,
        number_baffles,
    )

    # --------------------------------------------------------
    # Normalize excessive velocity
    # --------------------------------------------------------

    speed = np.sqrt(
        ux ** 2
        + uy ** 2
        + uz ** 2
    )

    max_speed = max(
        D * 0.70,
        0.1,
    )

    scale = np.minimum(
        1.0,
        max_speed
        / np.maximum(
            speed,
            1e-9,
        ),
    )

    ux *= scale
    uy *= scale
    uz *= scale

    new_x = (
        px
        + ux * dt
    )

    new_y = (
        py
        + uy * dt
    )

    new_z = (
        pz
        + uz * dt
    )

    # --------------------------------------------------------
    # Keep particles inside vessel
    # --------------------------------------------------------

    radius_limit = (
        D * 0.445
    )

    radial_distance = np.sqrt(
        new_x ** 2
        + new_y ** 2
    )

    outside = (
        radial_distance
        > radius_limit
    )

    factor = (
        radius_limit
        / np.maximum(
            radial_distance[outside],
            1e-9,
        )
    )

    new_x[outside] *= factor
    new_y[outside] *= factor

    # Bottom/top reflection
    bottom = new_z < 0.04
    top = new_z > liquid_z - 0.04

    new_z[bottom] = (
        0.08
        + (
            0.04
            - new_z[bottom]
        )
    )

    new_z[top] = (
        liquid_z
        - 0.08
        - (
            new_z[top]
            - liquid_z
            + 0.04
        )
    )

    new_z = np.clip(
        new_z,
        0.04,
        max(
            liquid_z - 0.04,
            0.05,
        ),
    )

    return (
        new_x,
        new_y,
        new_z,
    )


def _add_mixing_tracers(
    fig,
    D,
    liquid_z,
    impellers,
    rpm,
    number_baffles,
    frames_count=48,
):
    """
    Add animated particles following flow field.
    """

    if liquid_z <= 0:
        return

    px, py, pz = _initialize_tracers(
        D,
        liquid_z,
        n_particles=220,
    )

    particle_trace = len(
        fig.data
    )

    fig.add_trace(
        go.Scatter3d(
            x=px,
            y=py,
            z=pz,
            mode="markers",
            name="Moving Tracer Particles",
            marker=dict(
                size=3.2,
                opacity=0.78,
                color="#F28E3B",
            ),
            hovertemplate=(
                "Mixing tracer"
                "<extra></extra>"
            ),
        )
    )

    frames = []

    current_x = px.copy()
    current_y = py.copy()
    current_z = pz.copy()

    nframes = max(
        1,
        int(frames_count),
    )

    for frame_idx in range(
        nframes
    ):

        current_x, current_y, current_z = (
            _advance_particles(
                current_x,
                current_y,
                current_z,
                D,
                liquid_z,
                impellers,
                rpm,
                number_baffles,
                dt=0.22,
            )
        )

        frames.append(
            go.Frame(
                name=f"mix_{frame_idx}",
                data=[
                    go.Scatter3d(
                        x=current_x,
                        y=current_y,
                        z=current_z,
                        mode="markers",
                        marker=dict(
                            size=3.2,
                            opacity=0.78,
                            color="#F28E3B",
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
# ROTATING IMPELLER INDICATORS
# ============================================================

def _add_rotation_rings(
    fig,
    impellers,
):

    for idx, impeller in enumerate(
        impellers
    ):

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

        radius = (
            D * 0.56
        )

        theta = np.linspace(
            0,
            2 * math.pi,
            80,
        )

        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.full_like(
                    x,
                    z,
                ),
                mode="lines",
                name=(
                    f"Rotation Zone "
                    f"{idx + 1}"
                ),
                line=dict(
                    width=2,
                    dash="dot",
                ),
                opacity=0.35,
                showlegend=False,
                hoverinfo="skip",
            )
        )


# ============================================================
# FLOW LEGEND / ENGINEERING INFO
# ============================================================

def _add_flow_legend(
    fig,
    vortex_depth,
    impellers,
    rpm,
):

    fig.add_trace(
        go.Scatter3d(
            x=[None],
            y=[None],
            z=[None],
            mode="lines",
            line=dict(
                width=4,
                color="#E88935",
            ),
            name="Circulation Streamlines",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[None],
            y=[None],
            z=[None],
            mode="markers",
            marker=dict(
                size=6,
                color="#F28E3B",
            ),
            name="Moving Tracers",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[None],
            y=[None],
            z=[None],
            mode="lines",
            line=dict(
                width=5,
                color="#126B7A",
            ),
            name="Vortex Core",
            showlegend=True,
        )
    )


# ============================================================
# MAIN FUNCTION
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
    frames_count=48,

    # Multi-impeller input
    impellers=None,

    # Display controls
    show_dimensions=True,
    show_nozzles=True,
    show_tracers=True,
    vessel_opacity=0.20,
    show_baffles=True,

    # NEW FLOW CONTROLS
    show_streamlines=True,
    show_flow_vectors=False,
    show_vortex=True,
):
    """
    Advanced interactive 3D reactor mixing visualization.

    Parameters
    ----------
    D:
        Reactor internal diameter [m]

    straight_height:
        Straight-side height [m]

    liquid_height:
        Liquid height [m]

    rpm:
        Agitator speed [RPM]

    impellers:
        List of dictionaries:

        [
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
            {
                "position": "Top",
                "agitator": "Rushton Turbine",
                "impeller_diameter_m": 1.00,
                "elevation_from_bottom_m": 2.40,
            },
        ]

    IMPORTANT:
    The flow field is a parametric engineering visualization,
    not a CFD solution.
    """

    # ========================================================
    # SAFE INPUTS
    # ========================================================

    D = max(
        _safe_float(D, 1.0),
        0.10,
    )

    straight_height = max(
        _safe_float(
            straight_height,
            2.0,
        ),
        0.10,
    )

    liquid_height = max(
        _safe_float(
            liquid_height,
            0.0,
        ),
        0.0,
    )

    rpm = max(
        _safe_float(
            rpm,
            120.0,
        ),
        0.0,
    )

    number_baffles = max(
        _safe_int(
            number_baffles,
            4,
        ),
        0,
    )

    frames_count = max(
        _safe_int(
            frames_count,
            48,
        ),
        8,
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
        z_profile[-1],
        1.0,
    )

    # ========================================================
    # NORMALIZE IMPELLERS
    # ========================================================

    normalized_impellers = []

    if impellers:

        for item in impellers:

            normalized_impellers.append(
                {
                    "position": item.get(
                        "position",
                        "Auto",
                    ),
                    "agitator": item.get(
                        "agitator",
                        agitator,
                    ),
                    "impeller_diameter_m":
                        max(
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
                            0.05,
                        ),
                    "elevation_from_bottom_m":
                        _safe_float(
                            item.get(
                                "elevation_from_bottom_m",
                                item.get(
                                    "elevation_m",
                                    0.5,
                                ),
                            ),
                            0.5,
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

        if nimp == 1:

            positions = [
                min(
                    liquid_height * 0.25,
                    liquid_height,
                )
            ]

        else:

            positions = np.linspace(
                liquid_height * 0.20,
                liquid_height * 0.80,
                nimp,
            )

        normalized_impellers = []

        for z_imp in positions:

            normalized_impellers.append(
                {
                    "position": "Auto",
                    "agitator": agitator,
                    "impeller_diameter_m":
                        max(
                            _safe_float(
                                impeller_diameter,
                                D * 0.4,
                            ),
                            0.05,
                        ),
                    "elevation_from_bottom_m":
                        _safe_float(
                            z_imp,
                            0.5,
                        ),
                }
            )

    # ========================================================
    # FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # VESSEL
    # ========================================================

    _add_vessel(
        fig,
        z_profile,
        r_profile,
        opacity=vessel_opacity,
    )

    # ========================================================
    # VORTEX DEPTH
    # ========================================================

    calculated_vortex_depth = (
        _calculate_vortex_depth(
            D,
            liquid_height,
            rpm,
            normalized_impellers,
            user_vortex_depth=
                _safe_float(
                    vortex_depth,
                    0.0,
                ),
        )
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
        vortex_depth=(
            calculated_vortex_depth
            if show_vortex
            else 0.0
        ),
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
    # IMPELLERS
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
    # ROTATION ZONES
    # ========================================================

    _add_rotation_rings(
        fig,
        normalized_impellers,
    )

    # ========================================================
    # ELEVATION LABELS
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
    # STREAMLINES
    # ========================================================

    streamlines = []

    if show_streamlines:

        streamlines = _generate_streamlines(
            D,
            liquid_z,
            normalized_impellers,
            rpm,
            number_baffles,
        )

        _add_streamlines(
            fig,
            streamlines,
        )

    # ========================================================
    # FLOW VECTORS
    # ========================================================

    if show_flow_vectors:

        _add_flow_vectors(
            fig,
            D,
            liquid_z,
            normalized_impellers,
            rpm,
            number_baffles,
        )

    # ========================================================
    # VORTEX CORE
    # ========================================================

    if show_vortex:

        _add_vortex_core(
            fig,
            D,
            liquid_z,
            calculated_vortex_depth,
        )

    # ========================================================
    # TRACERS
    # ========================================================

    if show_tracers:

        _add_mixing_tracers(
            fig,
            D,
            liquid_z,
            normalized_impellers,
            rpm,
            number_baffles,
            frames_count=frames_count,
        )

    # ========================================================
    # FLOW LEGEND
    # ========================================================

    if (
        show_streamlines
        or show_tracers
        or show_vortex
    ):

        _add_flow_legend(
            fig,
            calculated_vortex_depth,
            normalized_impellers,
            rpm,
        )

    # ========================================================
    # ANIMATION CONTROLS
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
                            "label":
                                "▶ Start Mixing",
                            "method":
                                "animate",
                            "args": [
                                None,
                                {
                                    "frame": {
                                        "duration":
                                            80,
                                        "redraw":
                                            True,
                                    },
                                    "transition": {
                                        "duration":
                                            0,
                                    },
                                    "fromcurrent":
                                        True,
                                },
                            ],
                        },
                        {
                            "label":
                                "⏸ Pause",
                            "method":
                                "animate",
                            "args": [
                                [None],
                                {
                                    "frame": {
                                        "duration":
                                            0,
                                        "redraw":
                                            False,
                                    },
                                    "mode":
                                        "immediate",
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

    impeller_names = ", ".join(
        [
            str(
                item.get(
                    "agitator",
                    "Impeller",
                )
            )
            for item in normalized_impellers
        ]
    )

    if not impeller_names:
        impeller_names = str(
            agitator
        )

    title_text = (
        "3D Reactor Mixing & Flow Model"
        f"<br><sup>"
        f"ID = {D:.2f} m | "
        f"Liquid Height = {liquid_z:.2f} m | "
        f"RPM = {rpm:.0f} | "
        f"Impellers = {len(normalized_impellers)}"
        f"</sup>"
    )

    # ========================================================
    # ENGINEERING ANNOTATION
    # ========================================================

    fig.add_annotation(
        text=(
            f"<b>Mixing Visualization</b><br>"
            f"Vortex depth ≈ "
            f"{calculated_vortex_depth:.3f} m<br>"
            f"Impeller system: "
            f"{impeller_names}<br>"
            f"<i>Parametric flow model – "
            f"not CFD</i>"
        ),
        x=0.985,
        y=0.025,
        xref="paper",
        yref="paper",
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        align="right",
        bgcolor=(
            "rgba(255,255,255,0.82)"
        ),
        bordercolor="#B8C4CC",
        borderwidth=1,
        font=dict(
            size=11,
        ),
    )

    # ========================================================
    # FINAL LAYOUT
    # ========================================================

    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor="center",
        ),

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
                    total_height
                    / max(
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

        height=800,

        margin=dict(
            l=0,
            r=0,
            t=85,
            b=0,
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            bgcolor=(
                "rgba(255,255,255,0.78)"
            ),
        ),

        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",

        scene_dragmode="orbit",

        # Performance
        uirevision="reactor_mixing_model",
    )

    return fig


# ============================================================
# SIMPLE 3D FUNCTION
# ============================================================

def create_reactor_3d(**kwargs):

    return create_reactor_animation(
        **kwargs
    )
