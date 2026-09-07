import math


# =========================================================
# SCALE-UP ENGINE
# =========================================================

def calculate_scaleup(
    base,
    target,
    basis,
):
    """
    Preliminary reactor scale-up calculation.

    All equations are screening-level similarity equations.
    """

    result = {
        "basis": basis,
        "status": "REVIEW",
        "target_rpm": None,
        "target_tip_speed": None,
        "target_power_volume": None,
        "target_power_volume_kw_m3": None,
        "target_qv": None,
        "message": "",
    }

    Vb = float(
        base["working_volume"]
    )

    Vt = float(
        target["working_volume"]
    )

    Db = float(
        base["impeller_diameter_m"]
    )

    Dt = float(
        target["impeller_diameter_m"]
    )

    Nb = float(
        base["rpm"]
    )

    if Vb <= 0 or Vt <= 0:
        result["message"] = (
            "Working volumes must be greater than zero."
        )
        return result

    if Db <= 0 or Dt <= 0:
        result["message"] = (
            "Impeller diameters must be greater than zero."
        )
        return result

    # =====================================================
    # CONSTANT TIP SPEED
    # =====================================================

    if basis == "Constant Tip Speed":

        target_rpm = (
            Nb *
            Db /
            Dt
        )

        result["target_rpm"] = target_rpm

        result["target_tip_speed"] = (
            base.get("tip_speed")
        )

        result["message"] = (
            "Target RPM calculated for constant "
            "impeller tip speed."
        )

    # =====================================================
    # CONSTANT P/V
    # =====================================================

    elif basis == "Constant P/V":

        pv_w_m3 = base.get(
            "power_volume_w_m3"
        )

        if pv_w_m3 is None:
            pv_w_m3 = base.get(
                "power_volume"
            )

        Np = target.get("Np")

        rho = target.get(
            "density_kg_m3",
            target.get("density", 1000.0)
        )

        if (
            pv_w_m3 is not None
            and Np is not None
            and rho > 0
        ):

            # -------------------------------------------------
            # Correct equation:
            #
            # P/V = Np*rho*N^3*D^5 / V
            #
            # Therefore:
            #
            # N = [
            #       (P/V)*V /
            #       (Np*rho*D^5)
            #     ]^(1/3)
            #
            # -------------------------------------------------

            N_target_s = (
                (
                    pv_w_m3 *
                    Vt
                ) /
                (
                    Np *
                    rho *
                    Dt**5
                )
            ) ** (
                1.0 / 3.0
            )

            target_rpm = (
                N_target_s *
                60.0
            )

            result["target_rpm"] = (
                target_rpm
            )

            result["target_power_volume"] = (
                pv_w_m3
            )

            result["target_power_volume_kw_m3"] = (
                pv_w_m3 / 1000.0
            )

            result["message"] = (
                "Target RPM calculated to maintain "
                "constant P/V."
            )

    # =====================================================
    # CONSTANT RPM
    # =====================================================

    elif basis == "Constant RPM":

        result["target_rpm"] = Nb

        result["message"] = (
            "Target RPM maintained equal to "
            "the base reactor."
        )

    # =====================================================
    # CONSTANT FROUDE
    # =====================================================

    elif basis == "Constant Froude Number":

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
            "RPM scaled according to constant "
            "Froude number."
        )

    # =====================================================
    # CONSTANT REYNOLDS
    # =====================================================

    elif basis == "Constant Reynolds Number":

        rho_b = base.get(
            "density_kg_m3",
            base.get("density", 1000.0)
        )

        rho_t = target.get(
            "density_kg_m3",
            target.get("density", rho_b)
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
            and mu_b > 0
        ):

            N_target = (
                Nb *
                (
                    rho_b /
                    rho_t
                ) *
                (
                    mu_t /
                    mu_b
                ) *
                (
                    Db /
                    Dt
                )**2
            )

            result["target_rpm"] = (
                N_target
            )

            result["message"] = (
                "RPM calculated to maintain "
                "Reynolds-number similarity."
            )

    # =====================================================
    # CONSTANT Q/V
    # =====================================================

    elif basis == "Constant Pumping / Volume":

        qv = base.get(
            "qv_1_h"
        )

        Nq = target.get(
            "Nq"
        )

        if (
            qv is not None
            and Nq is not None
            and Nq > 0
        ):

            # Q/V = Nq*N*D^3 / V
            #
            # Q/V is in 1/s before conversion.
            #
            # Target RPM:

            N_target_s = (
                qv *
                Vt /
                (
                    Nq *
                    Dt**3 *
                    3600.0
                )
            )

            target_rpm = (
                N_target_s *
                60.0
            )

            result["target_rpm"] = (
                target_rpm
            )

            result["target_qv"] = qv

            result["message"] = (
                "Target RPM calculated to maintain "
                "constant pumping/volume."
            )

    # =====================================================
    # CONSTANT N/NJS
    # =====================================================

    elif basis == "Constant N/Njs":

        result["message"] = (
            "Njs requires solids concentration, "
            "particle size, particle density and a "
            "validated solids-suspension correlation."
        )

    # =====================================================
    # CONSTANT KLA
    # =====================================================

    elif basis == "Constant KLa":

        result["message"] = (
            "KLa scale-up requires a validated "
            "gas-liquid mass-transfer correlation "
            "and gas dispersion data."
        )

    # =====================================================
    # USER DEFINED
    # =====================================================

    else:

        result["message"] = (
            "User-defined scale-up criterion. "
            "Enter the required target criterion "
            "using validated engineering data."
        )

    # =====================================================
    # TARGET TIP SPEED
    # =====================================================

    if result["target_rpm"] is not None:

        result["target_tip_speed"] = (
            math.pi *
            Dt *
            result["target_rpm"] /
            60.0
        )

    return result
