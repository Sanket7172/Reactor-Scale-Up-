"""
Agitator reference database.

IMPORTANT:
Np/Nq are screening/reference values.
For final design, replace them with geometry-specific
vendor/literature/test data.
"""

AGITATORS = {

    "Pitched Blade Turbine 45° Down": {
        "description": "45° pitched-blade turbine, downward pumping",
        "flow": "Mixed / Axial",
        "direction": "Down-pumping",
        "blades": 4,
        "blade_angle_deg": 45,
        "D_T": 0.40,
        "Np": 1.30,
        "Nq": 0.85,
        "Kblend": 5.0,
        "application": "General blending, liquid-liquid, solids suspension",
        "viscosity": "Low-Medium",
        "gas_liquid": "Good",
        "solid_liquid": "Good",
        "description_short": "Versatile mixed-flow impeller",
    },

    "Hydrofoil": {
        "description": "High-efficiency axial-flow hydrofoil",
        "flow": "Axial",
        "direction": "Down-pumping",
        "blades": 3,
        "blade_angle_deg": 20,
        "D_T": 0.40,
        "Np": 0.30,
        "Nq": 0.65,
        "Kblend": 4.5,
        "application": "Bulk circulation, blending, solids suspension",
        "viscosity": "Low-Medium",
        "gas_liquid": "Good",
        "solid_liquid": "Excellent",
        "description_short": "High pumping / low power",
    },

    "Rushton Turbine": {
        "description": "Six-blade radial-flow disk turbine",
        "flow": "Radial",
        "direction": "Radial",
        "blades": 6,
        "blade_angle_deg": 90,
        "D_T": 0.33,
        "Np": 5.0,
        "Nq": 0.75,
        "Kblend": 6.0,
        "application": "Gas dispersion, high shear dispersion",
        "viscosity": "Low",
        "gas_liquid": "Excellent",
        "solid_liquid": "Moderate",
        "description_short": "High radial shear / gas dispersion",
    },

    "Marine Propeller": {
        "description": "Three-blade marine propeller",
        "flow": "Axial",
        "direction": "Axial",
        "blades": 3,
        "blade_angle_deg": 20,
        "D_T": 0.35,
        "Np": 0.50,
        "Nq": 0.60,
        "Kblend": 4.0,
        "application": "Low-viscosity circulation and blending",
        "viscosity": "Low",
        "gas_liquid": "Good",
        "solid_liquid": "Moderate",
        "description_short": "Efficient axial circulation",
    },

    "Anchor": {
        "description": "Close-clearance anchor agitator",
        "flow": "Tangential",
        "direction": "Tangential",
        "blades": 2,
        "blade_angle_deg": 0,
        "D_T": 0.85,
        "Np": 2.0,
        "Nq": 0.30,
        "Kblend": 8.0,
        "application": "High-viscosity mixing and wall heat transfer",
        "viscosity": "Medium-High",
        "gas_liquid": "Poor",
        "solid_liquid": "Moderate",
        "description_short": "Close-clearance viscous mixing",
    },

    "Helical Ribbon": {
        "description": "Close-clearance helical ribbon",
        "flow": "Axial / Tangential",
        "direction": "Axial",
        "blades": 1,
        "blade_angle_deg": 0,
        "D_T": 0.90,
        "Np": 1.0,
        "Nq": 0.25,
        "Kblend": 10.0,
        "application": "Very high viscosity systems",
        "viscosity": "High-Very High",
        "gas_liquid": "Poor",
        "solid_liquid": "Moderate",
        "description_short": "Very high viscosity mixing",
    },

    "RCI / Retreat Curve Impeller": {
        "description": "Retreat curve impeller / RCI",
        "flow": "Axial / Mixed",
        "direction": "Down-pumping",
        "blades": 3,
        "blade_angle_deg": 30,
        "D_T": 0.45,
        "Np": None,
        "Nq": None,
        "Kblend": None,
        "application": "Specialized mixing service",
        "viscosity": "Low-Medium",
        "gas_liquid": "Good",
        "solid_liquid": "Good",
        "description_short": "Vendor/literature data required",
    },
}


def get_agitator(name):
    """Return agitator specification."""
    return AGITATORS.get(name, {})


def agitator_names():
    return list(AGITATORS.keys())
