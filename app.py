# ============================================================
# REACTOR SCALE-UP DASHBOARD
# Professional Process Engineering Dashboard
# ============================================================

import sys
from pathlib import Path

# ------------------------------------------------------------
# PROJECT ROOT / PYTHON PATH
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ------------------------------------------------------------
# STREAMLIT / CORE IMPORTS
# ------------------------------------------------------------

import streamlit as st
import pandas as pd


# ============================================================
# MODULE VALIDATION
# ============================================================

def check_required_modules():
    """
    Check that all project folders/files required by the
    dashboard are physically present in the deployed environment.
    """

    required_files = {
        "calculations/engine.py":
            BASE_DIR / "calculations" / "engine.py",

        "calculations/scaleup.py":
            BASE_DIR / "calculations" / "scaleup.py",

        "calculations/validation.py":
            BASE_DIR / "calculations" / "validation.py",

        "libraries/agitator_geometry.py":
            BASE_DIR / "libraries" / "agitator_geometry.py",

        "libraries/reactor_geometry.py":
            BASE_DIR / "libraries" / "reactor_geometry.py",

        "visualization/reactor_3d.py":
            BASE_DIR / "visualization" / "reactor_3d.py",

        "reporting/report_generator.py":
            BASE_DIR / "reporting" / "report_generator.py",
    }

    missing_files = []

    for display_name, file_path in required_files.items():
        if not file_path.is_file():
            missing_files.append(
                f"{display_name}  -->  {file_path}"
            )

    if missing_files:

        st.error("❌ Required project files are missing.")

        st.markdown(
            """
            ### Expected project structure

            ```
            reactor-scale-up-/
            │
            ├── app.py
            │
            ├── calculations/
            │   ├── __init__.py
            │   ├── engine.py
            │   ├── scaleup.py
            │   └── validation.py
            │
            ├── libraries/
            │   ├── __init__.py
            │   ├── agitator_geometry.py
            │   └── reactor_geometry.py
            │
            ├── visualization/
            │   ├── __init__.py
            │   └── reactor_3d.py
            │
            └── reporting/
                ├── __init__.py
                └── report_generator.py
            ```
            """
        )

        st.markdown("### Missing files detected:")

        for item in missing_files:
            st.code(item)

        st.stop()


# Run file validation before imports
check_required_modules()


# ============================================================
# PROJECT MODULE IMPORTS
# ============================================================

try:

    from calculations.engine import calculate_reactor

except Exception as e:

    st.error("❌ Error importing calculations.engine")

    st.code(
        f"""
{type(e).__name__}: {e}

Project root:
{BASE_DIR}

Engine path:
{BASE_DIR / "calculations" / "engine.py"}
"""
    )

    st.stop()


try:

    from calculations.scaleup import calculate_scaleup

except Exception as e:

    st.error("❌ Error importing calculations.scaleup")

    st.code(
        f"""
{type(e).__name__}: {e}

Scale-up path:
{BASE_DIR / "calculations" / "scaleup.py"}
"""
    )

    st.stop()


try:

    from calculations.validation import validate_reactor

except Exception as e:

    st.error("❌ Error importing calculations.validation")

    st.code(
        f"""
{type(e).__name__}: {e}

Validation path:
{BASE_DIR / "calculations" / "validation.py"}
"""
    )

    st.stop()


try:

    from libraries.agitator_geometry import AGITATORS

except Exception as e:

    st.error("❌ Error importing libraries.agitator_geometry")

    st.code(
        f"""
{type(e).__name__}: {e}

Agitator library:
{BASE_DIR / "libraries" / "agitator_geometry.py"}
"""
    )

    st.stop()


try:

    from libraries.reactor_geometry import (
        REACTOR_HEADS,
        calculate_total_volume,
        liquid_height_from_volume,
    )

except Exception as e:

    st.error("❌ Error importing libraries.reactor_geometry")

    st.code(
        f"""
{type(e).__name__}: {e}

Reactor geometry library:
{BASE_DIR / "libraries" / "reactor_geometry.py"}
"""
    )

    st.stop()


try:

    from visualization.reactor_3d import (
        create_reactor_animation
    )

except Exception as e:

    st.error("❌ Error importing visualization.reactor_3d")

    st.code(
        f"""
{type(e).__name__}: {e}

3D visualization:
{BASE_DIR / "visualization" / "reactor_3d.py"}
"""
    )

    st.stop()


# ============================================================
# REPORT GENERATOR IMPORT
# ============================================================

try:

    from reporting.report_generator import (
        create_word_report,
        create_excel_report,
    )

except Exception as e:

    st.error("❌ Error importing reporting.report_generator")

    st.markdown(
        """
        ### Check these items

        1. Folder must be named exactly:

        `reporting`

        2. File must be named exact
