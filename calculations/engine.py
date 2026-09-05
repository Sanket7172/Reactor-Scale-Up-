import math


def calculate_reactor(data):

    rho = data["density"]
    mu = data["viscosity"] / 1000.0
    rpm = data["rpm"]
    D = data["impeller_diameter"] / 1000.0
    V = data["working_volume"]

    agitator = data["agitator_type"]

    # ---------------------------------------------
    # RPM
    # ---------------------------------------------

    N = rpm / 60.0

    # ---------------------------------------------
    # TIP SPEED
    # ---------------------------------------------

    tip_speed = math.pi * D * N

    # ---------------------------------------------
    # REYNOLDS NUMBER
    # ---------------------------------------------

    reynolds = (
        rho * N * D**2 / mu
        if mu > 0
        else 0
    )

    # ---------------------------------------------
    # Np
    # ---------------------------------------------

    NP_VALUES = {
        "Rushton Turbine": 5.0,
        "Pitched Blade Turbine": 1.5,
        "Hydrofoil": 0.35,
        "Marine Propeller": 0.5,
        "Anchor": 2.0,
        "Helical Ribbon": 1.0,
        "RCI": None,
    }

    Np = NP_VALUES.get(agitator)

    if Np is not None:

        power_per_impeller = (
            Np *
            rho *
            N**3 *
            D**5
        )

        total_power = (
            power_per_impeller *
            data["number_impellers"]
        )

        power_kw = total_power / 1000.0

    else:

        power_kw = float("nan")


    # ---------------------------------------------
    # POWER / VOLUME
    # ---------------------------------------------

    if V > 0 and not math.isnan(power_kw):

        power_per_volume = power_kw / V

    else:

        power_per_volume = float("nan")


    # ---------------------------------------------
    # TORQUE
    # ---------------------------------------------

    if N > 0 and not math.isnan(power_kw):

        torque = (
            power_kw * 1000 /
            (2 * math.pi * N)
        )

    else:

        torque = float("nan")


    # ---------------------------------------------
    # LIQUID HEIGHT
    # ---------------------------------------------

    # Detailed geometry calculation is handled
    # by reactor_geometry.py in the full version.

    liquid_height = data["working_volume"] ** (1/3) * 1000


    return {

        "liquid_height": liquid_height,

        "tip_speed": tip_speed,

        "reynolds_number": reynolds,

        "power_kw": power_kw,

        "power_per_volume": power_per_volume,

        "torque_nm": torque,

    }
