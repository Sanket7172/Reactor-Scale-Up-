import math


def calculate_scaleup(
    base,
    target,
    basis,
):
    """
    Compare target reactor against base reactor
    using selected scale-up criterion.

    This function provides screening-level similarity.
    """

    result = {
        "basis": basis,
        "status": "REVIEW",
        "target_rpm": None,
        "target_tip_speed": None,
        "target_power_volume": None,
        "target_qv": None,
        "message": "",
    }

    Vb = base["working_volume"]
    Vt = target["working_volume"]

    Db = base["impeller_diameter_m"]
    Dt = target["impeller_diameter_m"]

    Nb = base["rpm"]
    Nt = target["rpm"]

    # -----------------------------------------------------
    # CONSTANT TIP SPEED
    # -----------------------------------------------------

    if basis == "Constant Tip Speed":

        target_rpm = (
            Nb *
            Db /
            Dt
        )

        result["target_rpm"] = target_rpm

        result["target_tip_speed"] = (
            base["tip_speed"]
        )

        result["message"] = (
            "RPM adjusted to maintain constant impeller tip speed."
        )

    # -----------------------------------------------------
    # CONSTANT P/V
    # -----------------------------------------------------

    elif basis == "Constant P/V":

        pv = base.get(
            "power_volume"
        )

        if pv is not None:

            result["target_power_volume"] = pv

            if (
                target.get("power_kw")
                is not None
            ):

                # Screening indication only.
                # Actual solution depends on Np and D.
                Np = target.get(
                    "Np"
                )

                rho = target.get(
                    "density",
                    1000
                )

                if (
                    Np is not None
                    and rho > 0
                ):

                    D = Dt

                    target_rpm = (
                        pv *
                        Vt *
                        1000.0 /
                        (
                            Np *
                            rho *
                            D ** 5
                        )
                    )

                    target_rpm = (
                        target_rpm ** (
                            1.0 / 3.0
                        )
                        * 60.0
                    )

                    result["target_rpm"] = (
                        target_rpm
                    )

            result["message"] = (
                "Target RPM estimated to maintain constant P/V."
            )

    # -----------------------------------------------------
    # CONSTANT RPM
    # -----------------------------------------------------

    elif basis == "Constant RPM":

        result["target_rpm"] = Nb

        result["message"] = (
            "Target RPM maintained equal to base reactor."
        )

    # -----------------------------------------------------
    # CONSTANT FROUDE
    # -----------------------------------------------------

    elif basis == "Constant Froude Number":

        Fr_base = base.get(
            "Fr"
        )

        if Fr_base is not None:

            target_rpm = (
                Nb *
                math.sqrt(
                    Db / Dt
                )
            )

            result["target_rpm"] = (
                target_rpm
            )

            result["message"] = (
                "RPM scaled approximately with D^-0.5 "
                "for constant Froude number."
            )

    # -----------------------------------------------------
    # CONSTANT REYNOLDS
    # -----------------------------------------------------

    elif basis == "Constant Reynolds Number":

        # Re = rho N D² / mu

        rho_b = base.get(
            "density",
            1000
        )

        rho_t = target.get(
            "density",
            rho_b
        )

        mu_b = base.get(
            "viscosity_pa_s",
            0.001
        )

        mu_t = target.get(
            "viscosity_pa_s",
            mu_b
        )

        if (
            rho_t > 0
            and mu_t > 0
        ):

            N_target = (
                rho_b /
                rho_t *
                mu_t /
                mu_b *
                Nb *
                (
                    Db /
                    Dt
                ) ** 2
            )

            result["target_rpm"] = (
                N_target
            )

            result["message"] = (
                "RPM estimated to maintain Reynolds similarity."
            )

    # -----------------------------------------------------
    # CONSTANT Q/V
    # -----------------------------------------------------

    elif basis == "Constant Pumping / Volume":

        qv = base.get(
            "pumping_per_volume"
        )

        result["target_qv"] = qv

        if qv:

            Nq = target.get(
                "Nq"
            )

            if Nq:

                rho = target.get(
                    "density",
                    1000
                )

                target_rpm = (
                    qv *
                    Vt /
                    (
                        Nq *
                        Dt ** 3 *
                        3600
                    )
                    * 60
                )

                result["target_rpm"] = (
                    target_rpm
                )

        result["message"] = (
            "Target RPM estimated from constant Q/V."
        )

    # -----------------------------------------------------
    # N/NJS
    # -----------------------------------------------------

    elif basis == "Constant N/Njs":

        result["message"] = (
            "Njs correlation required. "
            "Use validated solids-suspension correlation."
        )

    # -----------------------------------------------------
    # KLA
    # -----------------------------------------------------

    elif basis == "Constant KLa":

        result["message"] = (
            "KLa requires validated gas-liquid mass-transfer correlation."
        )

    # -----------------------------------------------------
    # USER DEFINED
    # -----------------------------------------------------

    else:

        result["message"] = (
            "User-defined scale-up criterion."
        )

    return result
