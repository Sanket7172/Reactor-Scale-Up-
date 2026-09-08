import math
import numpy as np
import plotly.graph_objects as go


# ============================================================
# CONSTANTS
# ============================================================

G = 9.81


# ============================================================
# SAFE HELPERS
# ============================================================

def _f(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _i(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))


# ============================================================
# REACTOR GEOMETRY
# ============================================================

def _cylinder_surface(radius, z_bottom, z_top, nr=36, nz=16):

    theta = np.linspace(0, 2 * np.pi, nr)
    z = np.linspace(z_bottom, z_top, nz)

    T, Z = np.meshgrid(theta, z)

    X = radius * np.cos(T)
    Y = radius * np.sin(T)

    return X, Y, Z


def _ellipsoidal_head(radius, z_center, depth, top=True,
                      nr=36, ntheta=16):

    theta = np.linspace(0, 2 * np.pi, nr)
    phi = np.linspace(0, np.pi / 2, ntheta)

    T, P = np.meshgrid(theta, phi)

    X = radius * np.sin(P) * np.cos(T)
    Y = radius * np.sin(P) * np.sin(T)

    if top:
        Z = z_center + depth * np.cos(P)
    else:
        Z = z_center - depth * np.cos(P)

    return X, Y, Z


def _torispherical_head(radius, z_base, depth,
                        top=True, nr=36, ntheta=16):

    theta = np.linspace(0, 2 * np.pi, nr)
    phi = np.linspace(0, np.pi / 2, ntheta)

    T, P = np.meshgrid(theta, phi)

    # Engineering visualization approximation
    radial = radius * np.sin(P)

    X = radial * np.cos(T)
    Y = radial * np.sin(T)

    if top:
        Z = z_base + depth * np.sin(P)
    else:
        Z = z_base - depth * np.sin(P)

    return X, Y, Z


# ============================================================
# VESSEL
# ============================================================

def _create_vessel(
    tank_diameter,
    straight_height,
    bottom_type,
    top_type
):

    R = tank_diameter / 2.0

    bottom_depth = tank_diameter * (
        0.25 if "Ellipsoidal" in str(bottom_type) else
        0.10 if "Torispherical" in str(bottom_type) else
        0.0
    )

    top_depth = tank_diameter * (
        0.25 if "Ellipsoidal" in str(top_type) else
        0.10 if "Torispherical" in str(top_type) else
        0.0
    )

    z_bottom = 0.0
    z_straight_bottom = bottom_depth
    z_straight_top = bottom_depth + straight_height
    z_top = z_straight_top + top_depth

    surfaces = []

    # Straight shell
    X, Y, Z = _cylinder_surface(
        R,
        z_straight_bottom,
        z_straight_top
    )

    surfaces.append((X, Y, Z))

    # Bottom head
    if bottom_depth > 0:

        if "Ellipsoidal" in str(bottom_type):

            X, Y, Z = _ellipsoidal_head(
                R,
                z_straight_bottom,
                bottom_depth,
                top=True
            )

        else:

            X, Y, Z = _torispherical_head(
                R,
                z_straight_bottom,
                bottom_depth,
                top=False
            )

        surfaces.append((X, Y, Z))

    # Top head
    if top_depth > 0:

        if "Ellipsoidal" in str(top_type):

            X, Y, Z = _ellipsoidal_head(
                R,
                z_straight_top,
                top_depth,
                top=False
            )

        else:

            X, Y, Z = _torispherical_head(
                R,
                z_straight_top,
                top_depth,
                top=True
            )

        surfaces.append((X, Y, Z))

    geometry = {
        "radius": R,
        "bottom_depth": bottom_depth,
        "top_depth": top_depth,
        "straight_bottom": z_straight_bottom,
        "straight_top": z_straight_top,
        "total_height": z_top,
        "surfaces": surfaces
    }

    return geometry


# ============================================================
# LIQUID LEVEL
# ============================================================

def _estimate_liquid_level(
    working_volume,
    tank_diameter,
    straight_height,
    bottom_type,
    top_type
):

    R = tank_diameter / 2.0

    bottom_depth = tank_diameter * (
        0.25 if "Ellipsoidal" in str(bottom_type) else
        0.10 if "Torispherical" in str(bottom_type) else
        0.0
    )

    top_depth = tank_diameter * (
        0.25 if "Ellipsoidal" in str(top_type) else
        0.10 if "Torispherical" in str(top_type) else
        0.0
    )

    area = math.pi * R ** 2

    bottom_head_volume = (
        area * bottom_depth * 0.50
    )

    cylinder_volume = area * straight_height

    top_head_volume = (
        area * top_depth * 0.50
    )

    total_volume = (
        bottom_head_volume +
        cylinder_volume +
        top_head_volume
    )

    working_volume = _clamp(
        working_volume,
        0.0,
        total_volume * 0.999
    )

    if working_volume <= bottom_head_volume:

        fraction = (
            working_volume /
            max(bottom_head_volume, 1e-9)
        )

        return bottom_depth * fraction

    remaining = working_volume - bottom_head_volume

    if remaining <= cylinder_volume:

        return bottom_depth + remaining / area

    remaining -= cylinder_volume

    fraction = remaining / max(top_head_volume, 1e-9)

    return (
        bottom_depth +
        straight_height +
        top_depth * fraction
    )


# ============================================================
# LIQUID SURFACE
# ============================================================

def _create_liquid_surface(
    radius,
    liquid_level,
    vortex_depth=0.0,
    nr=70
):

    r = np.linspace(0, radius * 0.995, nr)
    theta = np.linspace(0, 2 * np.pi, nr)

    R, T = np.meshgrid(r, theta)

    X = R * np.cos(T)
    Y = R * np.sin(T)

    normalized = R / max(radius, 1e-9)

    # Parabolic vortex
    Z = (
        liquid_level -
        vortex_depth *
        (1.0 - normalized ** 2)
    )

    return X, Y, Z


# ============================================================
# BAFFLES
# ============================================================

def _create_baffles(
    radius,
    z_bottom,
    z_top,
    number_baffles=4,
    width=None
):

    if width is None:
        width = radius * 0.08

    baffle_thickness = max(radius * 0.025, 0.02)

    traces = []

    for i in range(number_baffles):

        angle = (
            2.0 *
            np.pi *
            i /
            number_baffles
        )

        radial = radius * 0.92

        x0 = radial * np.cos(angle)
        y0 = radial * np.sin(angle)

        tangent_x = -np.sin(angle)
        tangent_y = np.cos(angle)

        half_w = width / 2

        x1 = x0 + tangent_x * half_w
        y1 = y0 + tangent_y * half_w

        x2 = x0 - tangent_x * half_w
        y2 = y0 - tangent_y * half_w

        traces.append(
            go.Scatter3d(
                x=[x1, x2, x2, x1, x1],
                y=[y1, y2, y2, y1, y1],
                z=[
                    z_bottom,
                    z_bottom,
                    z_top,
                    z_top,
                    z_bottom
                ],
                mode="lines",
                line=dict(
                    width=6
                ),
                name=f"Baffle {i + 1}",
                showlegend=False
            )
        )

    return traces


# ============================================================
# SHAFT
# ============================================================

def _create_shaft(
    shaft_radius,
    z_bottom,
    z_top
):

    theta = np.linspace(0, 2 * np.pi, 30)
    z = np.linspace(z_bottom, z_top, 20)

    T, Z = np.meshgrid(theta, z)

    X = shaft_radius * np.cos(T)
    Y = shaft_radius * np.sin(T)

    return go.Surface(
        x=X,
        y=Y,
        z=Z,
        opacity=0.8,
        showscale=False,
        hoverinfo="skip",
        name="Agitator Shaft"
    )


# ============================================================
# IMPELLER
# ============================================================

def _impeller_trace(
    impeller_type,
    D,
    z,
    rotation_angle=0.0
):

    R = D / 2.0

    impeller_type = str(
        impeller_type
    ).lower()

    traces = []

    # --------------------------------------------------------
    # RUSHTON
    # --------------------------------------------------------

    if "rushton" in impeller_type:

        n_blades = 6

        hub_r = R * 0.16

        for i in range(n_blades):

            a = (
                2 * np.pi * i / n_blades +
                rotation_angle
            )

            x0 = hub_r * np.cos(a)
            y0 = hub_r * np.sin(a)

            x1 = R * 0.88 * np.cos(a)
            y1 = R * 0.88 * np.sin(a)

            tangent = a + np.pi / 2

            blade_width = R * 0.16

            xa = x1 + blade_width * np.cos(tangent)
            ya = y1 + blade_width * np.sin(tangent)

            xb = x1 - blade_width * np.cos(tangent)
            yb = y1 - blade_width * np.sin(tangent)

            traces.append(
                go.Scatter3d(
                    x=[x0, xa, xb, x0],
                    y=[y0, ya, yb, y0],
                    z=[z, z, z, z],
                    mode="lines",
                    line=dict(width=9),
                    name="Rushton",
                    showlegend=False
                )
            )

    # --------------------------------------------------------
    # PBT
    # --------------------------------------------------------

    elif (
        "pitched" in impeller_type or
        "pbt" in impeller_type
    ):

        n_blades = 4

        for i in range(n_blades):

            a = (
                2 * np.pi * i / n_blades +
                rotation_angle
            )

            r_values = np.linspace(
                R * 0.15,
                R * 0.95,
                10
            )

            x = r_values * np.cos(a)
            y = r_values * np.sin(a)

            blade_pitch = (
                0.18 * D *
                (r_values / R)
            )

            z_values = z + blade_pitch

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z_values,
                    mode="lines",
                    line=dict(width=10),
                    name="PBT",
                    showlegend=False
                )
            )

    # --------------------------------------------------------
    # HYDROFOIL
    # --------------------------------------------------------

    elif "hydrofoil" in impeller_type:

        n_blades = 3

        for i in range(n_blades):

            a = (
                2 * np.pi * i / n_blades +
                rotation_angle
            )

            r_values = np.linspace(
                R * 0.15,
                R * 0.95,
                18
            )

            x = r_values * np.cos(a)
            y = r_values * np.sin(a)

            z_values = (
                z +
                0.10 * D *
                (r_values / R)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z_values,
                    mode="lines",
                    line=dict(width=12),
                    name="Hydrofoil",
                    showlegend=False
                )
            )

    # --------------------------------------------------------
    # MARINE PROPELLER
    # --------------------------------------------------------

    elif (
        "marine" in impeller_type or
        "propeller" in impeller_type
    ):

        n_blades = 3

        for i in range(n_blades):

            a0 = (
                2 * np.pi * i / n_blades +
                rotation_angle
            )

            r_values = np.linspace(
                R * 0.12,
                R,
                30
            )

            a = (
                a0 +
                0.45 *
                (r_values / R)
            )

            x = r_values * np.cos(a)
            y = r_values * np.sin(a)

            z_values = (
                z +
                0.12 *
                D *
                (r_values / R)
            )

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z_values,
                    mode="lines",
                    line=dict(width=10),
                    name="Marine Propeller",
                    showlegend=False
                )
            )

    # --------------------------------------------------------
    # ANCHOR
    # --------------------------------------------------------

    elif "anchor" in impeller_type:

        theta = np.linspace(
            0,
            2 * np.pi,
            100
        )

        x = R * np.cos(
            theta +
            rotation_angle
        )

        y = R * np.sin(
            theta +
            rotation_angle
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.full_like(x, z),
                mode="lines",
                line=dict(width=10),
                name="Anchor",
                showlegend=False
            )
        )

        # Vertical legs

        for side in [-1, 1]:

            a = (
                rotation_angle +
                side * np.pi / 2
            )

            x = [
                R * np.cos(a),
                R * np.cos(a)
            ]

            y = [
                R * np.sin(a),
                R * np.sin(a)
            ]

            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=[
                        z - D * 0.25,
                        z + D * 0.25
                    ],
                    mode="lines",
                    line=dict(width=9),
                    showlegend=False
                )
            )

    # --------------------------------------------------------
    # HELICAL RIBBON
    # --------------------------------------------------------

    elif "helical" in impeller_type:

        theta = np.linspace(
            0,
            4 * np.pi,
            160
        )

        x = R * np.cos(
            theta +
            rotation_angle
        )

        y = R * np.sin(
            theta +
            rotation_angle
        )

        z_values = (
            z +
            0.40 * D *
            theta /
            (4 * np.pi)
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=z_values,
                mode="lines",
                line=dict(width=10),
                name="Helical Ribbon",
                showlegend=False
            )
        )

    # --------------------------------------------------------
    # RCI / GENERIC
    # --------------------------------------------------------

    else:

        theta = np.linspace(
            0,
            2 * np.pi,
            100
        )

        x = R * np.cos(
            theta +
            rotation_angle
        )

        y = R * np.sin(
            theta +
            rotation_angle
        )

        traces.append(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.full_like(x, z),
                mode="lines",
                line=dict(width=9),
                name=str(impeller_type),
                showlegend=False
            )
        )

    return traces


# ============================================================
# VORTEX / FLOW MODEL
# ============================================================

def _create_flow_field(
    radius,
    z_bottom,
    liquid_level,
    impellers,
    rpm,
    n_radial=12,
    n_theta=24,
    n_z=9
):

    """

    Physics-informed mixing flow field.

    The field is constructed from:
        - tangential rotation
        - radial discharge
        - axial return flow
        - impeller circulation zones
        - wall return flow
        - free-surface vortex

    This is NOT a CFD/Navier-Stokes solution.
    """

    points = []

    omega = 2.0 * np.pi * rpm / 60.0

    for imp in impellers:

        D = _f(
            imp.get(
                "diameter_m",
                imp.get("D", radius)
            ),
            radius
        )

        z_imp = _f(
            imp.get(
                "elevation_m",
                imp.get(
                    "bottom_clearance_m",
                    z_bottom
                )
            ),
            z_bottom
        )

        impeller_radius = D / 2.0

        for iz in range(n_z):

            z = (
                z_bottom +
                (
                    liquid_level -
                    z_bottom
                ) *
                iz /
                max(n_z - 1, 1)
            )

            for ir in range(1, n_radial):

                r = (
                    radius *
                    ir /
                    n_radial
                )

                for it in range(n_theta):

                    theta = (
                        2 *
                        np.pi *
                        it /
                        n_theta
                    )

                    # Distance from impeller elevation
                    dz = z - z_imp

                    vertical_decay = np.exp(
                        -abs(dz) /
                        max(D * 1.2, 1e-6)
                    )

                    radial_decay = np.exp(
                        -abs(
                            r -
                            impeller_radius
                        ) /
                        max(
                            radius * 0.40,
                            1e-6
                        )
                    )

                    influence = (
                        vertical_decay *
                        radial_decay
                    )

                    # Tangential velocity
                    tangential = (
                        omega *
                        r *
                        0.65 *
                        influence
                    )

                    # Radial discharge
                    radial_velocity = (
                        omega *
                        impeller_radius *
                        0.30 *
                        influence *
                        (
                            1.0 -
                            r /
                            max(radius, 1e-6)
                        )
                    )

                    # Axial pumping
                    axial_velocity = (
                        omega *
                        impeller_radius *
                        0.22 *
                        influence
                    )

                    # Circulation direction
                    if z > z_imp:
                        axial_velocity *= -1.0

                    # Wall return
                    if r > radius * 0.72:

                        radial_velocity *= -1.2

                        axial_velocity *= 1.4

                    # Convert cylindrical to Cartesian
                    er_x = np.cos(theta)
                    er_y = np.sin(theta)

                    et_x = -np.sin(theta)
                    et_y = np.cos(theta)

                    vx = (
                        radial_velocity *
                        er_x +
                        tangential *
                        et_x
                    )

                    vy = (
                        radial_velocity *
                        er_y +
                        tangential *
                        et_y
                    )

                    vz = axial_velocity

                    x = r * np.cos(theta)
                    y = r * np.sin(theta)

                    speed = math.sqrt(
                        vx ** 2 +
                        vy ** 2 +
                        vz ** 2
                    )

                    points.append(
                        (
                            x,
                            y,
                            z,
                            vx,
                            vy,
                            vz,
                            speed
                        )
                    )

    return points


# ============================================================
# FLOW STREAMLINES
# ============================================================

def _create_streamlines(
    radius,
    liquid_level,
    z_bottom,
    impellers,
    rpm,
    number_lines=28
):

    traces = []

    omega = (
        2 *
        np.pi *
        rpm /
        60.0
    )

    for line_no in range(number_lines):

        theta0 = (
            2 *
            np.pi *
            line_no /
            number_lines
        )

        r0 = (
            radius *
            (
                0.15 +
                0.70 *
                (
                    (line_no % 10) /
                    10.0
                )
            )
        )

        z0 = (
            z_bottom +
            (
                liquid_level -
                z_bottom
            ) *
            (
                0.15 +
                0.70 *
                (
                    ((line_no * 7) % 10) /
                    10.0
                )
            )
        )

        x_values = []
        y_values = []
        z_values = []

        r = r0
        theta = theta0
        z = z0

        for step in range(100):

            # nearest impeller
            if impellers:

                distances = [
                    abs(
                        z -
                        _f(
                            imp.get(
                                "elevation_m",
                                imp.get(
                                    "bottom_clearance_m",
                                    z_bottom
                                )
                            ),
                            z_bottom
                        )
                    )
                    for imp in impellers
                ]

                imp = impellers[
                    int(
                        np.argmin(
                            distances
                        )
                    )
                ]

                D = _f(
                    imp.get(
                        "diameter_m",
                        imp.get("D", radius)
                    ),
                    radius
                )

                zi = _f(
                    imp.get(
                        "elevation_m",
                        imp.get(
                            "bottom_clearance_m",
                            z_bottom
                        )
                    ),
                    z_bottom
                )

            else:

                D = radius
                zi = (
                    z_bottom +
                    liquid_level
                ) / 2

            Ri = D / 2

            influence = np.exp(
                -abs(z - zi) /
                max(D * 1.5, 1e-6)
            )

            tangential_velocity = (
                omega *
                r *
                0.55 *
                influence
            )

            radial_velocity = (
                omega *
                Ri *
                0.20 *
                influence
            )

            axial_velocity = (
                omega *
                Ri *
                0.18 *
                influence
            )

            if z > zi:
                axial_velocity *= -1

            if r > radius * 0.72:

                radial_velocity *= -1.4
                axial_velocity *= 1.2

            dt = 0.015

            dr = (
                radial_velocity *
                dt
            )

            dz = (
                axial_velocity *
                dt
            )

            dtheta = (
                tangential_velocity /
                max(r, 0.03) *
                dt
            )

            r += dr
            z += dz
            theta += dtheta

            # Wall boundary
            if r > radius * 0.94:
                r = radius * 0.94

            if r < radius * 0.08:
                r = radius * 0.08

            # Bottom boundary
            if z < z_bottom + 0.05:
                z = z_bottom + 0.05

            # Free surface
            if z > liquid_level - 0.03:
                z = liquid_level - 0.03

            x_values.append(
                r * np.cos(theta)
            )

            y_values.append(
                r * np.sin(theta)
            )

            z_values.append(z)

        traces.append(
            go.Scatter3d(
                x=x_values,
                y=y_values,
                z=z_values,
                mode="lines",
                line=dict(
                    width=3
                ),
                opacity=0.45,
                name="Flow path",
                showlegend=False
            )
        )

    return traces


# ============================================================
# PARTICLE SYSTEM
# ============================================================

def _create_particles(
    radius,
    z_bottom,
    liquid_level,
    count=350
):

    rng = np.random.default_rng(42)

    r = (
        radius *
        np.sqrt(
            rng.random(count)
        ) *
        0.92
    )

    theta = (
        2 *
        np.pi *
        rng.random(count)
    )

    z = (
        z_bottom +
        (
            liquid_level -
            z_bottom
        ) *
        rng.random(count)
    )

    x = r * np.cos(theta)
    y = r * np.sin(theta)

    return x, y, z


# ============================================================
# GAS BUBBLES
# ============================================================

def _create_bubbles(
    radius,
    liquid_level,
    gas_flow_m3_h,
    bubble_diameter_mm,
    count=180
):

    if gas_flow_m3_h <= 0:
        return None

    rng = np.random.default_rng(21)

    bubble_r = (
        radius *
        0.12 *
        np.sqrt(
            rng.random(count)
        )
    )

    theta = (
        2 *
        np.pi *
        rng.random(count)
    )

    x = (
        bubble_r *
        np.cos(theta)
    )

    y = (
        bubble_r *
        np.sin(theta)
    )

    z = (
        0.10 *
        liquid_level +
        0.80 *
        liquid_level *
        rng.random(count)
    )

    sizes = np.full(
        count,
        max(
            2.0,
            min(
                14.0,
                bubble_diameter_mm * 2
            )
        )
    )

    return x, y, z, sizes


# ============================================================
# MAIN 3D FUNCTION
# ============================================================

def create_reactor_animation(
    volume_m3,
    tank_diameter_m,
    straight_height_m,
    liquid_height_m,
    rpm,
    impellers,
    bottom_type="10% Torispherical",
    top_type="10% Torispherical",
    number_baffles=4,
    density_kg_m3=1000.0,
    viscosity_pa_s=0.001,
    gas_flow_m3_h=0.0,
    bubble_diameter_mm=3.0,
    gas_holdup_fraction=0.05,
    show_dimensions=True,
    show_flow_field=True,
    show_streamlines=True,
    show_particles=True,
    show_vortex=True,
    show_baffles=True,
    show_gas=False,
    frames=24,
):

    # ========================================================
    # INPUTS
    # ========================================================

    D_tank = _f(tank_diameter_m, 2.0)
    H_straight = _f(straight_height_m, 3.0)
    H_liquid = _f(liquid_height_m, H_straight)

    rpm = _f(rpm, 100.0)

    radius = D_tank / 2.0

    impellers = (
        impellers
        if isinstance(impellers, list)
        else []
    )

    # ========================================================
    # VESSEL
    # ========================================================

    vessel = _create_vessel(
        D_tank,
        H_straight,
        bottom_type,
        top_type
    )

    z_bottom = 0.0

    # ========================================================
    # VORTEX
    # ========================================================

    # Engineering visualization estimate
    Fr = (
        (
            rpm / 60.0
        ) ** 2 *
        (
            D_tank
        ) /
        G
    )

    vortex_depth = 0.0

    if show_vortex:

        vortex_depth = _clamp(
            H_liquid *
            0.04 *
            math.sqrt(
                max(Fr, 0.0)
            ),
            0.0,
            H_liquid * 0.25
        )

    # ========================================================
    # FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # VESSEL SHELL
    # ========================================================

    for X, Y, Z in vessel["surfaces"]:

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                opacity=0.18,
                showscale=False,
                hoverinfo="skip",
                name="Reactor"
            )
        )

    # ========================================================
    # LIQUID
    # ========================================================

    Xl, Yl, Zl = _create_liquid_surface(
        radius,
        H_liquid,
        vortex_depth
    )

    fig.add_trace(
        go.Surface(
            x=Xl,
            y=Yl,
            z=Zl,
            opacity=0.48,
            showscale=False,
            hovertemplate=(
                "Liquid<br>"
                "X=%{x:.2f} m<br>"
                "Y=%{y:.2f} m<br>"
                "Z=%{z:.2f} m"
                "<extra></extra>"
            ),
            name="Liquid"
        )
    )

    # ========================================================
    # BAFFLES
    # ========================================================

    if show_baffles:

        baffle_traces = _create_baffles(
            radius,
            vessel["straight_bottom"],
            min(
                H_liquid,
                vessel["straight_top"]
            ),
            number_baffles
        )

        for trace in baffle_traces:
            fig.add_trace(trace)

    # ========================================================
    # SHAFT
    # ========================================================

    shaft_radius = max(
        D_tank * 0.025,
        0.025
    )

    fig.add_trace(
        _create_shaft(
            shaft_radius,
            vessel["straight_bottom"],
            vessel["total_height"]
        )
    )

    # ========================================================
    # IMPELLERS
    # ========================================================

    for imp in impellers:

        impeller_type = imp.get(
            "agitator_type",
            imp.get(
                "type",
                "Rushton Turbine"
            )
        )

        impeller_D = _f(
            imp.get(
                "diameter_m",
                imp.get(
                    "D",
                    D_tank * 0.5
                )
            ),
            D_tank * 0.5
        )

        elevation = _f(
            imp.get(
                "elevation_m",
                imp.get(
                    "bottom_clearance_m",
                    0.4
                )
            ),
            0.4
        )

        for trace in _impeller_trace(
            impeller_type,
            impeller_D,
            elevation
        ):
            fig.add_trace(trace)

    # ========================================================
    # FLOW FIELD
    # ========================================================

    flow_points = []

    if show_flow_field:

        flow_points = _create_flow_field(
            radius,
            z_bottom,
            H_liquid,
            impellers,
            rpm
        )

        # Thin down for rendering
        flow_points = flow_points[
            ::max(
                1,
                len(flow_points) // 1800
            )
        ]

        if flow_points:

            x = np.array(
                [p[0] for p in flow_points]
            )

            y = np.array(
                [p[1] for p in flow_points]
            )

            z = np.array(
                [p[2] for p in flow_points]
            )

            speed = np.array(
                [p[6] for p in flow_points]
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="markers",
                    marker=dict(
                        size=2.5,
                        color=speed,
                        colorscale="Turbo",
                        opacity=0.65,
                        colorbar=dict(
                            title="Velocity<br>m/s"
                        )
                    ),
                    name="Velocity Field",
                    hovertemplate=(
                        "Velocity = %{marker.color:.3f} m/s"
                        "<extra></extra>"
                    )
                )
            )

    # ========================================================
    # STREAMLINES
    # ========================================================

    if show_streamlines:

        streamlines = _create_streamlines(
            radius,
            H_liquid,
            z_bottom,
            impellers,
            rpm
        )

        for trace in streamlines:
            fig.add_trace(trace)

    # ========================================================
    # PARTICLES
    # ========================================================

    particle_trace_index = None

    if show_particles:

        px, py, pz = _create_particles(
            radius,
            z_bottom,
            H_liquid
        )

        particle_trace_index = len(
            fig.data
        )

        fig.add_trace(
            go.Scatter3d(
                x=px,
                y=py,
                z=pz,
                mode="markers",
                marker=dict(
                    size=3,
                    opacity=0.75
                ),
                name="Mixing Particles"
            )
        )

    # ========================================================
    # GAS BUBBLES
    # ========================================================

    if show_gas and gas_flow_m3_h > 0:

        bubble_data = _create_bubbles(
            radius,
            H_liquid,
            gas_flow_m3_h,
            bubble_diameter_mm
        )

        if bubble_data is not None:

            bx, by, bz, bs = bubble_data

            fig.add_trace(
                go.Scatter3d(
                    x=bx,
                    y=by,
                    z=bz,
                    mode="markers",
                    marker=dict(
                        size=bs,
                        opacity=0.60,
                        symbol="circle"
                    ),
                    name="Gas Bubbles"
                )
            )

    # ========================================================
    # DIMENSION LINES
    # ========================================================

    if show_dimensions:

        # Tank diameter
        fig.add_trace(
            go.Scatter3d(
                x=[
                    -radius,
                    radius
                ],
                y=[0, 0],
                z=[
                    vessel["straight_top"],
                    vessel["straight_top"]
                ],
                mode="lines+text",
                text=[
                    "",
                    f"ID = {D_tank:.2f} m"
                ],
                textposition="top center",
                line=dict(width=4),
                name="Tank Diameter"
            )
        )

        # Liquid level
        fig.add_trace(
            go.Scatter3d(
                x=[
                    -radius * 0.98,
                    radius * 0.98
                ],
                y=[0, 0],
                z=[
                    H_liquid,
                    H_liquid
                ],
                mode="lines+text",
                text=[
                    "",
                    f"Liquid Level = {H_liquid:.2f} m"
                ],
                textposition="top center",
                line=dict(
                    width=5,
                    dash="dash"
                ),
                name="Liquid Level"
            )
        )

    # ========================================================
    # ANIMATION
    # ========================================================

    animation_frames = []

    if particle_trace_index is not None:

        px0, py0, pz0 = _create_particles(
            radius,
            z_bottom,
            H_liquid
        )

        for frame_no in range(frames):

            angle = (
                2 *
                np.pi *
                frame_no /
                frames
            )

            # Particle circulation
            r = np.sqrt(
                px0 ** 2 +
                py0 ** 2
            )

            theta = np.arctan2(
                py0,
                px0
            )

            # Rotation rate decreases toward wall
            local_rotation = (
                angle *
                (
                    0.35 +
                    0.65 *
                    (
                        1 -
                        r /
                        max(radius, 1e-9)
                    )
                )
            )

            theta_new = (
                theta +
                local_rotation
            )

            # Axial circulation
            z_new = (
                pz0 +
                0.08 *
                H_liquid *
                np.sin(
                    2 *
                    np.pi *
                    pz0 /
                    max(H_liquid, 1e-9) +
                    angle
                )
            )

            z_new = np.clip(
                z_new,
                z_bottom + 0.03,
                H_liquid - 0.03
            )

            x_new = (
                r *
                np.cos(theta_new)
            )

            y_new = (
                r *
                np.sin(theta_new)
            )

            frame_data = [
                go.Scatter3d(
                    x=x_new,
                    y=y_new,
                    z=z_new
                )
            ]

            animation_frames.append(
                go.Frame(
                    data=frame_data,
                    traces=[particle_trace_index],
                    name=str(frame_no)
                )
            )

    fig.frames = animation_frames

    # ========================================================
    # PLAYBACK CONTROLS
    # ========================================================

    if animation_frames:

        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    x=0.02,
                    y=1.08,
                    buttons=[
                        dict(
                            label="▶ Play Mixing",
                            method="animate",
                            args=[
                                None,
                                {
                                    "frame": {
                                        "duration": 80,
                                        "redraw": True
                                    },
                                    "fromcurrent": True
                                }
                            ]
                        ),
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[
                                [None],
                                {
                                    "frame": {
                                        "duration": 0,
                                        "redraw": False
                                    }
                                }
                            ]
                        )
                    ]
                )
            ]
        )

    # ========================================================
    # CAMERA / LAYOUT
    # ========================================================

    fig.update_layout(
        title={
            "text": (
                "3D Reactor Mixing Simulation"
                "<br>"
                f"<sup>{D_tank:.2f} m ID | "
                f"{H_liquid:.2f} m Liquid Level | "
                f"{rpm:.0f} RPM</sup>"
            ),
            "x": 0.5
        },

        scene=dict(

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

            aspectmode="data",

            camera=dict(
                eye=dict(
                    x=1.7,
                    y=1.7,
                    z=1.2
                )
            )
        ),

        margin=dict(
            l=0,
            r=0,
            t=80,
            b=0
        ),

        height=760,

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5
        )
    )

    return fig


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def create_reactor_3d(**kwargs):

    return create_reactor_animation(
        **kwargs
    )
