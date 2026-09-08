"""
Agitator engineering database.

Values are screening-level typical values.
Final design must use validated vendor/literature data.
"""

AGITATORS = {

    "Rushton Turbine": {
        "Np": 5.0,
        "Nq": 0.75,
        "D_T": 0.33,
        "flow": "Radial",
        "description": "High-shear radial-flow turbine; gas dispersion and gas-liquid service.",
    },

    "Pitched Blade Turbine": {
        "Np": 1.50,
        "Nq": 0.75,
        "D_T": 0.40,
        "flow": "Mixed",
        "description": "General-purpose mixed-flow agitator.",
    },

    "Hydrofoil": {
        "Np": 0.35,
        "Nq": 0.70,
        "D_T": 0.40,
        "flow": "Axial",
        "description": "High pumping / low power axial-flow impeller.",
    },

    "Marine Propeller": {
        "Np": 0.50,
        "Nq": 0.60,
        "D_T": 0.35,
        "flow": "Axial",
        "description": "Low-viscosity axial-flow application.",
    },

    "Anchor": {
        "Np": 2.00,
        "Nq": 0.30,
        "D_T": 0.85,
        "flow": "Tangential",
        "description": "High-viscosity and wall-sweeping service.",
    },

    "Helical Ribbon": {
        "Np": 1.00,
        "Nq": 0.25,
        "D_T": 0.90,
        "flow": "Axial/Tangential",
        "description": "Very high-viscosity mixing.",
    },

    "RCI": {
        "Np": None,
        "Nq": None,
        "D_T": 0.45,
        "flow": "Vendor-specific",
        "description": "Use validated vendor/literature performance data.",
    },
}
