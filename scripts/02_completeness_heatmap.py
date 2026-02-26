#!/usr/bin/env python3
"""
02_completeness_heatmap.py
==========================
Data completeness heatmap generation for the Water Value Database –
Data in Brief article.

Creates a stacked heatmap figure showing the percentage of non-null
values for each column across all three dataset files. This provides
readers with an immediate visual understanding of dataset quality.

Usage
-----
    python 02_completeness_heatmap.py

Inputs
------
    output/water_value_database.db  (from 02_derived_variables.py)

Outputs
-------
    output/figures_tables/fig_completeness_heatmap.png  (300 dpi)
    output/figures_tables/fig_completeness_heatmap.pdf
    output/figures_tables/fig_completeness_heatmap_caption.txt

Author : [Author team]
Task   : Blueprint 2, Task B2-T08
"""

import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import BoundaryNorm
from matplotlib.cm import ScalarMappable

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DATA_DIR = Path("./data")
FIGURES_DIR = Path("./figures")
SQLITE_PATH = DATA_DIR / "water_value_database.db"
TABLES_DIR = Path("./tables")

# Columns to EXCLUDE from the heatmap — derived variables that are
# always 100% complete by construction and would clutter the figure.
# We show only the ORIGINAL data columns.
DERIVED_COLS_CLASSIFICATION = {
    "Year_numeric", "Decade", "Has_water_value",
    "Method_clean", "Method_category", "Method_detail",
    "Study_region_clean", "Study_region_continent",
}

DERIVED_COLS_WATERVALUE = {
    "Country_clean", "Purpose_clean", "Continent",
    "Method_clean", "Method_category", "Method_detail",
    "units_clean",
}

_report_lines: list[str] = []


def _print(msg: str = "") -> None:
    """Print to console AND capture in report buffer."""
    print(msg)
    _report_lines.append(msg)


def _sep(title: str, char: str = "═", width: int = 72) -> None:
    _print(f"\n{char * width}")
    _print(f"  {title}")
    _print(f"{char * width}\n")


def _subsep(title: str, char: str = "─", width: int = 60) -> None:
    _print(f"\n  {char * width}")
    _print(f"  {title}")
    _print(f"  {char * width}\n")


# ──────────────────────────────────────────────
# 1. Load from SQLite
# ──────────────────────────────────────────────

def load_data() -> dict[str, pd.DataFrame]:
    """Load all three tables from SQLite."""
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {SQLITE_PATH}\n"
            f"Run 01_data_preparation.py and 02_derived_variables.py first."
        )

    conn = sqlite3.connect(str(SQLITE_PATH))
    dfs = {
        "01_Screening": pd.read_sql("SELECT * FROM screening", conn),
        "02_Classification": pd.read_sql("SELECT * FROM classification", conn),
        "03_WaterValue": pd.read_sql("SELECT * FROM water_values", conn),
    }
    conn.close()

    for name, df in dfs.items():
        _print(f"  ✓ Loaded {name:20s}  ({len(df):,} rows × {df.shape[1]} cols)")

    return dfs


# ──────────────────────────────────────────────
# 2. Calculate completeness
# ──────────────────────────────────────────────

def calculate_completeness(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Calculate column-level completeness (% non-null) for each file.

    Returns a dict mapping file name to a single-row DataFrame with
    column names as columns and completeness percentages as values.

    Excludes derived columns to show only original data quality.
    """
    _subsep("Calculating Completeness")

    completeness = {}

    exclude_map = {
        "01_Screening": set(),
        "02_Classification": DERIVED_COLS_CLASSIFICATION,
        "03_WaterValue": DERIVED_COLS_WATERVALUE,
    }

    for name, df in dfs.items():
        exclude = exclude_map.get(name, set())
        cols = [c for c in df.columns if c not in exclude]
        df_filtered = df[cols]

        pct = ((1 - df_filtered.isna().mean()) * 100).round(0).astype(int)
        completeness[name] = pct

        _print(f"\n  {name} ({len(cols)} original columns):")
        for col in cols:
            val = pct[col]
            icon = "✓" if val == 100 else "⚠" if val >= 50 else "✗"
            _print(f"    {icon} {col:40s}  {val:>3}%")

    return completeness


# ──────────────────────────────────────────────
# 3. Create heatmap figure
# ──────────────────────────────────────────────

def create_heatmap(
    completeness: dict[str, pd.Series],
    output_dir: Path,
) -> None:
    """
    Create a stacked heatmap figure with three subplots (one per CSV file).

    Each subplot shows a single-row heatmap with completeness percentages
    annotated in each cell.

    Color scale: RdYlGn (Red=0%, Yellow=50%, Green=100%)
    """
    _subsep("Creating Heatmap Figure")

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Set up matplotlib style ──
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
    })

    # ── Determine subplot sizes ──
    # Each subplot height is fixed; width scales with number of columns
    file_names = list(completeness.keys())
    n_cols_per_file = [len(completeness[name]) for name in file_names]
    max_cols = max(n_cols_per_file)

    # Figure dimensions
    fig_width = max(12, max_cols * 0.55)
    subplot_height = 1.2
    title_space = 1.0
    bottom_space = 2.5  # space for rotated labels on bottom subplot
    spacing = 0.8
    fig_height = (
        title_space
        + len(file_names) * subplot_height
        + (len(file_names) - 1) * spacing
        + bottom_space
    )

    fig, axes = plt.subplots(
        nrows=len(file_names),
        ncols=1,
        figsize=(fig_width, fig_height),
        gridspec_kw={"hspace": spacing / subplot_height},
    )

    if len(file_names) == 1:
        axes = [axes]

    # ── Color map ──
    cmap = plt.cm.RdYlGn
    boundaries = [0, 25, 50, 75, 90, 95, 100.01]
    norm = BoundaryNorm(boundaries, cmap.N)

    for idx, (name, ax) in enumerate(zip(file_names, axes)):
        pct = completeness[name]
        cols = list(pct.index)
        values = pct.values.reshape(1, -1).astype(float)

        # Draw heatmap
        im = ax.imshow(
            values,
            cmap=cmap,
            norm=norm,
            aspect="auto",
        )

        # ── Annotations ──
        for j, val in enumerate(values[0]):
            # Choose text color based on background brightness
            text_color = "white" if val < 40 else "black"
            ax.text(
                j, 0, f"{int(val)}",
                ha="center", va="center",
                fontsize=10, fontweight="bold",
                color=text_color,
            )

        # ── Axis formatting ──
        ax.set_yticks([0])
        ax.set_yticklabels([name], fontsize=9, fontweight="bold")
        ax.set_xticks(range(len(cols)))

        # Only show x-axis labels on the bottom subplot
        if idx == len(file_names) - 1:
            ax.set_xticklabels(
                cols,
                rotation=45,
                ha="right",
                fontsize=9,
            )
        else:
            ax.set_xticklabels(
                cols,
                rotation=45,
                ha="right",
                fontsize=9,
            )

        # Cell borders
        ax.set_xlim(-0.5, len(cols) - 0.5)
        ax.set_ylim(-0.5, 0.5)

        # Grid lines between cells
        for j in range(len(cols) + 1):
            ax.axvline(j - 0.5, color="white", linewidth=0.5)
        ax.axhline(-0.5, color="white", linewidth=0.5)
        ax.axhline(0.5, color="white", linewidth=0.5)

        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.tick_params(
            left=False, bottom=False,
            labelbottom=True,
        )

    # ── Shared colorbar ──
    fig.subplots_adjust(right=0.88, top=0.92, bottom=0.18)

    cbar_ax = fig.add_axes([0.90, 0.25, 0.015, 0.55])
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label("Completeness (%)", fontsize=9)
    cbar.set_ticks([0, 25, 50, 75, 100])
    cbar.ax.tick_params(labelsize=8)

    # ── Title ──
    fig.suptitle(
        "Data Completeness Across Dataset Files",
        fontsize=13,
        fontweight="bold",
        y=0.97,
    )
    fig.text(
        0.44, 0.935,
        "(Percentage of non-null values per column — original data columns only)",
        ha="center",
        fontsize=9,
        fontstyle="italic",
        color="gray",
    )

    # ── Save ──
    png_path = output_dir / "fig_completeness_heatmap.png"
    pdf_path = output_dir / "fig_completeness_heatmap.pdf"

    fig.savefig(str(png_path), dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    fig.savefig(str(pdf_path), bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)

    size_png = png_path.stat().st_size / 1024
    size_pdf = pdf_path.stat().st_size / 1024
    _print(f"  ✓ {png_path.name}  ({size_png:.1f} KB)")
    _print(f"  ✓ {pdf_path.name}  ({size_pdf:.1f} KB)")


# ──────────────────────────────────────────────
# 4. Generate caption
# ──────────────────────────────────────────────

def generate_caption(
    completeness: dict[str, pd.Series],
    output_dir: Path,
) -> None:
    """Generate and save the figure caption."""
    _subsep("Generating Caption")

    # Calculate study region completeness for caption
    class_pct = completeness.get("02_Classification", pd.Series())
    study_region_pct = class_pct.get("Study region", 0)

    caption = (
        "Figure X. Data completeness heatmap showing the percentage of "
        "non-null values for each original data column across the three "
        "dataset files. Green indicates complete or near-complete data "
        "(≥90%), yellow indicates partial completeness (50–89%), and red "
        "indicates significant gaps (<50%). Only original data columns "
        "are shown; derived variables (e.g., Country_clean, Method_clean, "
        "Continent) created during standardization are excluded as they "
        "are 100% complete by construction. The 'Study region' column in "
        f"02_Classification shows {study_region_pct:.0f}% completeness, "
        "reflecting that many papers do not explicitly specify a geographic "
        "study area. Columns such as 'Notes' and 'Sub_state' have "
        "intentionally low completeness as they are optional fields. "
        "The WV_min, WV_median, and WV_max columns in 03_WaterValue show "
        "0% completeness as the unit conversion pipeline is pending "
        "completion by a collaborator."
    )

    caption_path = output_dir / "fig_completeness_heatmap_caption.txt"
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption)

    _print(f"  ✓ Caption saved: {caption_path.name}")
    _print(f"\n  Caption text:")
    _print(f"  {caption}")


# ──────────────────────────────────────────────
# 5. Print completeness summary
# ──────────────────────────────────────────────

def print_completeness_summary(completeness: dict[str, pd.Series]) -> None:
    """Print a concise summary of completeness across all files."""
    _subsep("Completeness Summary")

    for name, pct in completeness.items():
        n_cols = len(pct)
        n_complete = (pct == 100).sum()
        n_partial = ((pct > 0) & (pct < 100)).sum()
        n_empty = (pct == 0).sum()
        avg_pct = pct.mean()

        _print(f"  {name}:")
        _print(f"    Columns: {n_cols}")
        _print(f"    100% complete:  {n_complete:>3} ({n_complete/n_cols*100:.0f}%)")
        _print(f"    Partial (1-99%): {n_partial:>2} ({n_partial/n_cols*100:.0f}%)")
        _print(f"    Empty (0%):     {n_empty:>3} ({n_empty/n_cols*100:.0f}%)")
        _print(f"    Average completeness: {avg_pct:.1f}%")
        _print("")


# ──────────────────────────────────────────────
# 6. Save report
# ──────────────────────────────────────────────

def save_report() -> None:
    """Save the full console output as a text report."""
    report_path = FIGURES_DIR / "completeness_heatmap_report.txt"
    header = (
        f"Water Value Database — Completeness Heatmap Report\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'=' * 72}\n\n"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(_report_lines))

    print(f"\n  ✓ Report saved: {report_path}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    """
    Full completeness heatmap pipeline:
    1. Load data from SQLite
    2. Calculate completeness percentages
    3. Create stacked heatmap figure
    4. Generate caption
    5. Print summary
    6. Save report
    """
    _sep("BLUEPRINT 2 — B2-T08: Data Completeness Heatmap")

    # 1. Load
    _subsep("Loading data")
    dfs = load_data()

    # 2. Calculate
    completeness = calculate_completeness(dfs)

    # 3. Create figure
    _sep("Creating Heatmap Figure")
    create_heatmap(completeness, FIGURES_DIR)

    # 4. Caption
    generate_caption(completeness, FIGURES_DIR)

    # 5. Summary
    print_completeness_summary(completeness)

    # 6. Report
    _sep("B2-T08 COMPLETE")
    _print("  Completeness heatmap generated.")
    _print(f"  Figure: {FIGURES_DIR}/fig_completeness_heatmap.png")
    _print(f"  Figure: {FIGURES_DIR}/fig_completeness_heatmap.pdf")
    _print(f"  Caption: {FIGURES_DIR}/fig_completeness_heatmap_caption.txt")
    _print("  Ready for B2-T09 (analytical charts).")

    save_report()


# ──────────────────────────────────────────────
# Module-level execution
# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()
