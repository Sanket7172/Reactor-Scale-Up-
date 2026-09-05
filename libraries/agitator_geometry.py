AGITATORS = {

    "Rushton Turbine": {
        "description": "Radial-flow disk turbine",
        "blades": 6,
        "flow": "Radial",
        "np": 5.0,
        "nq": 0.75,
    },

    "Pitched Blade Turbine": {
        "description": "Axial/radial pitched blade turbine",
        "blades": 4,
        "flow": "Mixed",
        "np": 1.5,
        "nq": 0.75,
    },

    "Hydrofoil": {
        "description": "High-efficiency axial flow impeller",
        "blades": 3,
        "flow": "Axial",
        "np": 0.35,
        "nq": 0.70,
    },

    "Marine Propeller": {
        "description": "Axial-flow marine propeller",
        "blades": 3,
        "flow": "Axial",
        "np": 0.50,
        "nq": 0.60,
    },

    "Anchor": {
        "description": "Low-speed close-clearance impeller",
        "blades": 2,
        "flow": "Tangential",
        "np": 2.0,
        "nq": 0.30,
    },

    "Helical Ribbon": {
        "description": "Close-clearance helical ribbon",
        "blades": 1,
        "flow": "Axial/Tangential",
        "np": 1.0,
        "nq": 0.25,
    },

    "RCI": {
        "description": "Retreating Curve Impeller",
        "blades": 2,
        "flow": "Axial/Mixed",
        "np": None,
        "nq": None,
        "note": (
            "Np/Nq should be entered from validated "
            "vendor/literature data or test data."
        ),
    },
}
