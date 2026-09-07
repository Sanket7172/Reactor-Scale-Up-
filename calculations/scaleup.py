import math


def calculate_scaleup(base, target, basis):

    result = {
        "basis": basis,
        "status": "REVIEW",
        "target_rpm": None,
        "target_tip_speed": None,
        "target_power_volume": None,
        "target_qv": None,
        "target_power_kw": None,
        "target_torque_nm": None,
        "message": "",
    }

    Vt = target["working_volume"]

    Db = base["impeller_diameter_m"]
    Dt = target["impeller_diameter_m"]

    Nb = base["rpm"]

    if Db <= 0 or Dt <= 0:
        result["message"] = "Invalid impeller diameter."
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
            "RPM adjusted to maintain constant impeller tip speed."
        )

    # =====================================================
    # CONSTANT P/V
    # =====================================================

    elif basis == "Constant P/V":

        pv_w_m3 = base.get(
            "power_volume_w_m3"
        )

        if pv_w_m3 is None:

            pv_kw_m3 = base.get(
                "power_volume_kw_m3"
            )

            if pv_kw_m3 is not None:
                pv_w_m3 = pv_kw_m3 * 1000.0

        Np = target.get("Np")
        rho = target.get(
            "density_kg_m3",
            target.get("density", 1000.0)
        )

        if (
            pv_w_m3 is not None
            and Np is not None
            and rho > 0
            and Vt > 0
        ):

            nimp = target.get(
                "number_impellers",
                1
            )

            N_target = (
                pv_w_m3 /
                (
                    Np *
                    rho *
                    Dt**5 *
                    nimp
                )
            ) ** (1.0 / 3.0)

            target_rpm = (
                N_target *
                60.0
            )

            result["target_rpm"] = target_rpm

            result["target_power_volume"] = (
                pv_w_m3 / 1000.0
            )

            result["message"] = (
                "Target RPM calculated to maintain constant P/V."
            )

        else:

            result["message"] = (
                "Insufficient target Np, density or P/V data."
            )

    # =====================================================
    # CONSTANT RPM
    # =====================================================

    elif basis == "Constant RPM":

        result["target_rpm"] = Nb

        result["message"] = (
            "Target RPM maintained equal to base reactor."
        )

    # =====================================================
    # CONSTANT FROUDE
    # =====================================================

    elif basis == "Constant Froude Number":

        target_rpm = (
            Nb *
            math.sqrt(
                Db /
                Dt
            )
        )

        result["target_rpm"] = target_rpm

        result["message"] = (
            "RPM scaled according to constant Froude similarity."
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
            and rho_b > 0
            and mu_b > 0
        ):

            N_target = (
                rho_b /
                rho_t
                *
                mu_t /
                mu_b
                *
                (Db / Dt) ** 2
                *
                Nb
            )

            result["target_rpm"] = N_target

            result["message"] = (
                "RPM calculated for constant Reynolds similarity."
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

        if qv is not None and Nq:

            nimp = target.get(
                "number_impellers",
                1
            )

            N_target = (
                qv *
                Vt /
                (
                    Nq *
                    Dt**3 *
                    nimp
                )
            )

            target_rpm = (
                N_target /
                60.0
            )

            result["target_rpm"] = target_rpm

            result["target_qv"] = qv

            result["message"] = (
                "RPM calculated to maintain constant Q/V."
            )

        else:

            result["message"] = (
                "Insufficient Q/V or Nq data."
            )

    # =====================================================
    # N/Njs
    # =====================================================

    elif basis == "Constant N/Njs":

        result["message"] = (
            "Requires solids properties and a validated Njs correlation."
        )

    # =====================================================
    # KLa
    # =====================================================

    elif basis == "Constant KLa":

        result["message"] = (
            "Requires validated gas-liquid mass-transfer correlation."
        )

    else:

        result["message"] = (
            "User-defined scale-up criterion."
        )

    return result
