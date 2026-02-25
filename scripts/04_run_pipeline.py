#!/usr/bin/env python3
"""
04_run_pipeline.py
==================
Analysis pipeline runner for the Water Value Database.

Reads the clean SQLite database (data/water_value_database.db)
and regenerates all summary tables and figures.

Usage
-----
    python scripts/04_run_pipeline.py              # Run all steps
    python scripts/04_run_pipeline.py --step 1      # Summary tables only
    python scripts/04_run_pipeline.py --step 2      # Completeness heatmap only
    python scripts/04_run_pipeline.py --step 3      # Analytical charts only

Prerequisites
-------------
    uv sync                                         # Install dependencies
    # Or: pip install .

Notes
-----
    The pipeline expects data/water_value_database.db to exist.
    This file is included in the repository and contains all three
    tables (screening, classification, water_values) with derived
    columns already applied.

    Raw-to-clean processing scripts (data_preparation.py,
    derived_variables.py) are not included in this repository
    because only clean data is distributed. The processing
    methodology is documented in the companion Data in Brief
    article.

Author : [Author team]
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
DATA_DIR = REPO_ROOT / "data"
FIGURES_DIR = REPO_ROOT / "figures"

DB_PATH = DATA_DIR / "water_value_database.db"

# ──────────────────────────────────────────────
# Pipeline steps
# ──────────────────────────────────────────────

STEPS = [
    {
        "number": 1,
        "name": "Summary Tables",
        "script": "01_summary_tables.py",
        "description": (
            "Generate summary statistics tables "
            "(classification, methods, regions, years, water values)"
        ),
        "outputs": [
            FIGURES_DIR / "table_1_classification.csv",
            FIGURES_DIR / "table_2_methods.csv",
            FIGURES_DIR / "table_3_regions.csv",
            FIGURES_DIR / "table_4_years.csv",
            FIGURES_DIR / "table_5_wv_summary.csv",
            FIGURES_DIR / "table_6_wv_purpose.csv",
        ],
    },
    {
        "number": 2,
        "name": "Completeness Heatmap",
        "script": "02_completeness_heatmap.py",
        "description": "Generate data completeness heatmap figure",
        "outputs": [
            FIGURES_DIR / "fig_completeness_heatmap.png",
            FIGURES_DIR / "fig_completeness_heatmap.pdf",
        ],
    },
    {
        "number": 3,
        "name": "Analytical Charts",
        "script": "03_analytical_charts.py",
        "description": (
            "Generate analytical figures "
            "(year distribution, geographic, method, water value box plot, "
            "category-method heatmap)"
        ),
        "outputs": [
            FIGURES_DIR / "fig_year_method_stacked.png",
            FIGURES_DIR / "fig_geographic_distribution.png",
            FIGURES_DIR / "fig_wv_datapoints_by_year.png",
            FIGURES_DIR / "fig_continent_purpose_heatmap.png",
            FIGURES_DIR / "fig_category_method_heatmap.png",
        ],
    },
]


# ──────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────


def check_prerequisites() -> bool:
    """Verify the SQLite database exists before running."""
    if not DB_PATH.exists():
        print(f"  ✗ DATABASE NOT FOUND: {DB_PATH}")
        print()
        print("    The analysis pipeline requires data/water_value_database.db.")
        print("    This file should be included in the repository.")
        print("    If missing, re-download from the repository or Zenodo archive.")
        return False

    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"  ✓ Database found: {DB_PATH.name} ({size_mb:.1f} MB)")
    return True


def run_step(step: dict, python_cmd: str = sys.executable) -> bool:
    """Run a single pipeline step and verify outputs."""

    print(f"\n{'─' * 60}")
    print(f"  Step {step['number']}: {step['name']}")
    print(f"  Script: {step['script']}")
    print(f"  {step['description']}")
    print(f"{'─' * 60}\n")

    script_path = SCRIPTS_DIR / step["script"]
    if not script_path.exists():
        print(f"  ✗ SCRIPT NOT FOUND: {script_path}")
        return False

    # Run the script
    start_time = time.time()
    try:
        result = subprocess.run(
            [python_cmd, str(script_path)],
            capture_output=False,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(REPO_ROOT),  # Run from repo root
        )
    except subprocess.TimeoutExpired:
        print("\n  ✗ TIMEOUT: Script exceeded 5 minute limit")
        return False
    except Exception as e:
        print(f"\n  ✗ ERROR: {e}")
        return False

    elapsed = time.time() - start_time

    if result.returncode != 0:
        print(f"\n  ✗ FAILED: Exit code {result.returncode}")
        return False

    # Verify outputs exist
    missing_outputs = []
    for output_path in step["outputs"]:
        if not output_path.exists():
            missing_outputs.append(str(output_path))

    if missing_outputs:
        print("\n  ⚠ MISSING OUTPUTS:")
        for path in missing_outputs:
            print(f"    {path}")
        print(f"\n  ⚠ Step completed with warnings ({elapsed:.1f}s)")
        return True

    print(f"\n  ✓ Step {step['number']} completed successfully ({elapsed:.1f}s)")
    print(f"    All {len(step['outputs'])} expected outputs verified.")
    return True


def main():
    """Run the analysis pipeline."""

    print("\n" + "═" * 72)
    print("  WATER VALUE DATABASE — ANALYSIS PIPELINE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 72)

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Run the Water Value Database analysis pipeline"
    )
    parser.add_argument(
        "--step",
        type=int,
        default=0,
        help="Run only this step number (0 = all steps)",
    )
    args = parser.parse_args()

    # Check prerequisites
    print()
    if not check_prerequisites():
        sys.exit(1)

    # Determine which steps to run
    if args.step > 0:
        steps_to_run = [s for s in STEPS if s["number"] == args.step]
        if not steps_to_run:
            valid = [s["number"] for s in STEPS]
            print(f"\n  ✗ Invalid step number: {args.step}")
            print(f"  Valid steps: {valid}")
            sys.exit(1)
    else:
        steps_to_run = STEPS

    # Ensure output directory exists
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Run steps
    total_start = time.time()
    results = {}

    for step in steps_to_run:
        success = run_step(step)
        results[step["number"]] = success

        if not success and args.step == 0:
            print(f"\n  ✗ Pipeline halted at step {step['number']}")
            print("    Fix the error and re-run.")
            break

    # Summary
    total_elapsed = time.time() - total_start

    print("\n" + "═" * 72)
    print("  PIPELINE SUMMARY")
    print("═" * 72)
    print()

    for step in STEPS:
        if step["number"] in results:
            status = "✓ PASS" if results[step["number"]] else "✗ FAIL"
        else:
            status = "○ SKIP"
        print(f"  {status}  Step {step['number']}: {step['name']}")

    n_pass = sum(1 for v in results.values() if v)
    n_fail = sum(1 for v in results.values() if not v)
    n_skip = len(STEPS) - len(results)

    print()
    print(f"  Passed:  {n_pass}")
    print(f"  Failed:  {n_fail}")
    print(f"  Skipped: {n_skip}")
    print(f"  Total time: {total_elapsed:.1f}s")
    print()

    if n_fail == 0 and n_skip == 0:
        print("  ✓ ALL STEPS COMPLETED SUCCESSFULLY")
        print()
        print("  Input:")
        print(f"    Database:  {DB_PATH}")
        print()
        print("  Generated outputs:")
        print(f"    Tables:    {FIGURES_DIR}/table_*.csv")
        print(f"    Figures:   {FIGURES_DIR}/fig_*.png / .pdf")
    elif n_fail > 0:
        print("  ✗ PIPELINE INCOMPLETE — fix errors and re-run")
        sys.exit(1)

    print()
    print("═" * 72)
    print("  ANALYSIS PIPELINE COMPLETE")
    print("═" * 72)
    print()


if __name__ == "__main__":
    main()
