AGITATORS = {

    "Rushton Turbine": {
        "description": "Six-blade radial-flow disc turbine",
        "flow_type": "Radial",
        "np": 5.0,
        "nq": 0.75,
        "recommended_d_t": (0.30, 0.50),
        "gas_dispersion": True,
    },

    "Pitched Blade Turbine 45": {
        "description": "Four/six-blade pitched blade turbine",
        "flow_type": "Mixed",
        "np": 1.27,
        "nq": 0.79,
        "recommended_d_t": (0.30, 0.60),
        "gas_dispersion": True,
    },

    "Hydrofoil": {
        "description": "High-efficiency axial-flow hydrofoil",
        "flow_type": "Axial",
        "np": 0.30,
        "nq": 0.55,
        "recommended_d_t": (0.30, 0.60),
        "gas_dispersion": False,
    },

    "Marine Propeller": {
        "description": "Axial-flow marine propeller",
        "flow_type": "Axial",
        "np": 0.35,
        "nq": 0.55,
        "recommended_d_t": (0.30, 0.50),
        "gas_dispersion": False,
    },

    "Anchor": {
        "description": "Close-clearance anchor agitator",
        "flow_type": "Tangential",
        "np": 1.50,
        "nq": 0.20,
        "recommended_d_t": (0.80, 0.95),
        "gas_dispersion": False,
    },

    "Helical Ribbon": {
        "description": "Close-clearance helical ribbon",
        "flow_type": "Axial / Helical",
        "np": 2.50,
        "nq": 0.30,
        "recommended_d_t": (0.80, 0.95),
        "gas_dispersion": False,
    },

    "RCI": {
        "description": "Radial circulation impeller",
        "flow_type": "Radial",
        "np": 4.50,
        "nq": 0.70,
        "recommended_d_t": (0.30, 0.60),
        "gas_dispersion": True,
    },
}
