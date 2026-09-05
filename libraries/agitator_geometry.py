AGITATORS = {

    "Rushton Turbine": {
        "description": "Radial-flow disk turbine",
        "blades": 6,
        "flow": "Radial",
        "np": 5.0,
        "nq": 0.75,
        "default_diameter_ratio": 0.33,
        "recommended_for": [
            "Gas-Liquid",
            "Gas-Liquid-Solid",
            "Dispersion",
        ],
    },

    "Pitched Blade Turbine": {
        "description": "Four-blade pitched turbine",
        "blades": 4,
        "flow": "Mixed",
        "np": 1.5,
        "nq": 0.75,
        "default_diameter_ratio": 0.40,
        "recommended_for": [
            "Liquid-Liquid",
            "Solid-Liquid",
            "Crystallization",
        ],
    },

    "Hydrofoil": {
        "description": "High-efficiency axial-flow impeller",
        "blades": 3,
        "flow": "Axial",
        "np": 0.35,
        "nq": 0.70,
        "default_diameter_ratio": 0.45,
        "recommended_for": [
            "Liquid-Liquid",
            "Solid-Liquid",
            "Low-viscosity blending",
        ],
    },

    "Marine Propeller": {
        "description": "Axial-flow propeller",
        "blades": 3,
        "flow": "Axial",
        "np": 0.50,
        "nq": 0.60,
        "default_diameter_ratio": 0.40,
        "recommended_for": [
            "Liquid-Liquid",
            "Low-viscosity liquids",
        ],
    },

    "Anchor": {
        "description": "Close-clearance low-speed impeller",
        "blades": 2,
        "flow": "Tangential",
        "np": 2.0,
        "nq": 0.30,
        "default_diameter_ratio": 0.85,
        "recommended_for": [
            "High viscosity",
            "Laminar mixing",
            "Heat-transfer service",
        ],
    },

    "Helical Ribbon": {
        "description": "Close-clearance helical ribbon",
        "blades": 1,
        "flow": "Axial/Tangential",
        "np": 1.0,
        "nq": 0.25,
        "default_diameter_ratio": 0.90,
        "recommended_for": [
            "High viscosity",
            "Non-Newtonian systems",
        ],
    },

    "RCI": {
        "description": "Retreating Curve Impeller",
        "blades": 2,
        "flow": "Axial/Mixed",
        "np": None,
        "nq": None,
        "default_diameter_ratio": 0.40,
        "recommended_for": [
            "High-efficiency mixing",
        ],
        "note": (
            "Use validated manufacturer/literature/test "
            "Np and Nq data."
        ),
    },
}
