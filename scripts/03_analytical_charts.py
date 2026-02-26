#!/usr/bin/env python3
"""
03_analytical_charts.py
=======================
Analytical chart generation for the Water Value Database –
Data in Brief article.

Generates publication-quality charts that complement (not duplicate)
the companion article (article.txt):

    Chart 1: Year × Method Stacked Bar (differentiates from companion Fig 3a)
    Chart 2: Geographic Distribution (horizontal bar)
    Chart 3: Water Value Data Points by Year × Purpose (NEW)
    Chart 4: Country × Purpose Heatmap (NEW)
    Chart 5: Classification Category × Method cross-tabulation (heatmap)

All charts are saved as PNG (300 dpi) and PDF.

Usage
-----
    python 03_analytical_charts.py

Inputs
------
    output/water_value_database.db  (from 02_derived_variables.py)

Outputs
-------
    output/figures_tables/fig_year_method_stacked.{png,pdf}
    output/figures_tables/fig_geographic_distribution.{png,pdf}
    output/figures_tables/fig_wv_datapoints_by_year.{png,pdf}
    output/figures_tables/fig_continent_purpose_heatmap.{png,pdf}
    output/figures_tables/fig_category_method_heatmap.{png,pdf}
    output/figures_tables/fig_analytical_charts_captions.txt

Author : [Author team]
Task   : Blueprint 2, Tasks B2-T09 through B2-T12
"""

import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DATA_DIR = Path("./data")
FIGURES_DIR = Path("./figures")
SQLITE_PATH = DATA_DIR / "water_value_database.db"
TABLES_DIR = Path("./tables")

# Consistent color palette
STEEL_BLUE = "#4682B4"
LIGHT_STEEL = "#B0C4DE"

# Method_clean display order (manuscript order)
METHOD_ORDER = ["LP", "MILP", "SDP", "SDDP", "Econ-Engi", "Other", "Not available"]

# Method colors — qualitative palette aligned with manuscript order
METHOD_COLORS = {
    "LP":            "#1f77b4",  # blue
    "MILP":          "#ff7f0e",  # orange
    "SDP":           "#2ca02c",  # green
    "SDDP":          "#d62728",  # red
    "Econ-Engi":     "#9467bd",  # purple
    "Other":         "#8c564b",  # brown
    "Not available": "#c7c7c7",  # light gray
}

# Purpose colors
PURPOSE_COLORS = {
    "Hydropower":      "#1f77b4",
    "Agriculture":     "#2ca02c",
    "Urban/Municipal": "#ff7f0e",
    "Environmental":   "#17becf",
    "Mixed":           "#9467bd",
    "Industrial":      "#8c564b",
    "Social/Economic": "#e377c2",
}

# Classification category order
CATEGORY_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H", "R"]

_report_lines: list[str] = []
_captions: list[str] = []


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
# 1. Load data
# ──────────────────────────────────────────────

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load classification and water_values tables from SQLite."""
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {SQLITE_PATH}\n"
            f"Run 01_data_preparation.py and 02_derived_variables.py first."
        )

    conn = sqlite3.connect(str(SQLITE_PATH))
    df_class = pd.read_sql("SELECT * FROM classification", conn)
    df_wv = pd.read_sql("SELECT * FROM water_values", conn)
    conn.close()

    _print(f"  ✓ Loaded classification:  {len(df_class):,} rows × {df_class.shape[1]} cols")
    _print(f"  ✓ Loaded water_values:    {len(df_wv):,} rows × {df_wv.shape[1]} cols")

    return df_class, df_wv


# ──────────────────────────────────────────────
# 2. Set consistent style
# ──────────────────────────────────────────────

def set_style() -> None:
    """Set consistent matplotlib style for all charts."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
        "axes.grid": False,
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "savefig.edgecolor": "none",
    })


def _save_figure(fig: plt.Figure, name: str) -> None:
    """Save figure as PNG and PDF."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    png_path = FIGURES_DIR / f"{name}.png"
    pdf_path = FIGURES_DIR / f"{name}.pdf"

    fig.savefig(str(png_path), dpi=300, bbox_inches="tight")
    fig.savefig(str(pdf_path), bbox_inches="tight")
    plt.close(fig)

    size_png = png_path.stat().st_size / 1024
    size_pdf = pdf_path.stat().st_size / 1024
    _print(f"  ✓ {png_path.name:45s}  ({size_png:.1f} KB)")
    _print(f"  ✓ {pdf_path.name:45s}  ({size_pdf:.1f} KB)")


def _remove_top_right_spines(ax: plt.Axes) -> None:
    """Remove top and right spines for cleaner look."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ──────────────────────────────────────────────
# 3. Chart 1: Year × Method Stacked Bar
# ──────────────────────────────────────────────

def create_year_method_stacked(df: pd.DataFrame) -> None:
    """
    Chart 1: Stacked bar chart showing number of papers per year,
    stacked by Method_clean, with 3-year and 5-year moving average
    trendlines overlaid.

    Differentiates from companion Figure 3a which stacks by
    Classification category (A-H, R).
    """
    _subsep("Chart 1: Year × Method Stacked Bar + Trendlines")

    # Prepare cross-tabulation: Year × Method_clean
    year_method = pd.crosstab(df["Year_numeric"], df["Method_clean"])

    # Ensure all methods are present and in order
    for method in METHOD_ORDER:
        if method not in year_method.columns:
            year_method[method] = 0
    year_method = year_method[METHOD_ORDER]

    # Determine display range — start from first year with ≥2 papers
    # in a 3-year window
    year_totals = year_method.sum(axis=1)
    year_min = int(year_totals.index.min())
    year_max = int(year_totals.index.max())

    start_year = year_min
    for yr in range(year_min, year_max):
        window = year_totals.loc[
            (year_totals.index >= yr) & (year_totals.index <= yr + 2)
        ].sum()
        if window >= 2:
            start_year = yr
            break

    year_method = year_method.loc[year_method.index >= start_year]

    # Fill missing years with 0
    all_years = range(start_year, year_max + 1)
    year_method = year_method.reindex(all_years, fill_value=0)

    # Compute annual totals and moving averages
    annual_totals = year_method.sum(axis=1)
    ma_3yr = annual_totals.rolling(window=3, center=True, min_periods=2).mean()
    ma_5yr = annual_totals.rolling(window=5, center=True, min_periods=3).mean()

    _print(f"  Year range displayed: {start_year}–{year_max}")
    _print(f"  Total papers: {year_method.sum().sum()}")
    _print(f"  Method breakdown:")
    for method in METHOD_ORDER:
        count = year_method[method].sum()
        _print(f"    {method:20s}  {count:>4}")
    _print(f"\n  Trendlines:")
    _print(f"    3-year MA range: {ma_3yr.min():.1f} – {ma_3yr.max():.1f}")
    _print(f"    5-year MA range: {ma_5yr.min():.1f} – {ma_5yr.max():.1f}")
    peak_3yr = ma_3yr.idxmax()
    peak_5yr = ma_5yr.idxmax()
    _print(f"    3-year MA peak:  {peak_3yr} ({ma_3yr.loc[peak_3yr]:.1f} papers/yr)")
    _print(f"    5-year MA peak:  {peak_5yr} ({ma_5yr.loc[peak_5yr]:.1f} papers/yr)")

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 5))

    # Stacked bar chart
    bottom = np.zeros(len(year_method))
    for method in METHOD_ORDER:
        values = year_method[method].values.astype(float)
        color = METHOD_COLORS.get(method, "#999999")
        ax.bar(
            year_method.index,
            values,
            bottom=bottom,
            color=color,
            edgecolor="white",
            linewidth=0.3,
            width=0.8,
            label=method,
            zorder=2,
        )
        bottom += values

    # Overlay trendlines
    ax.plot(
        ma_3yr.index,
        ma_3yr.values,
        color="#222222",
        linewidth=1.8,
        linestyle="-",
        label="3-year moving avg.",
        zorder=4,
        alpha=0.85,
    )
    ax.plot(
        ma_5yr.index,
        ma_5yr.values,
        color="#222222",
        linewidth=1.8,
        linestyle="--",
        label="5-year moving avg.",
        zorder=4,
        alpha=0.85,
    )

    # Formatting
    ax.set_xlabel("Publication Year")
    ax.set_ylabel("Number of Papers")
    _remove_top_right_spines(ax)

    # Y-axis grid
    ax.yaxis.grid(True, alpha=0.3, linestyle="-", zorder=0)
    ax.set_axisbelow(True)

    # X-axis ticks — every 5 years
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(1))

    # Y-axis integer ticks
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    # Legend — separate method entries from trendline entries
    # using two-column layout with trendlines in their own row
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        fontsize=8,
        loc="upper left",
        framealpha=0.9,
        ncol=3,
        title="Method / Trend",
        title_fontsize=9,
        columnspacing=1.5,
    )

    plt.tight_layout()
    _save_figure(fig, "fig_year_method_stacked")

    # Caption
    caption = (
        f"Figure X. Distribution of the {len(df)} classified papers by "
        f"publication year ({start_year}–{year_max}), stacked by "
        f"optimization/analysis method (Method_clean). Solid and dashed "
        f"black lines show 3-year and 5-year centered moving averages of "
        f"total annual publications, respectively. The 5-year moving "
        f"average peaks at {ma_5yr.loc[peak_5yr]:.1f} papers per year "
        f"around {peak_5yr}. This figure complements Figure 3a in the "
        f"companion article [REF-companion], which stacks the same "
        f"temporal distribution by classification category (A–H, R). "
        f"The methodological stacking reveals the temporal evolution of "
        f"analytical approaches, including the early dominance of LP "
        f"methods and the subsequent adoption of stochastic approaches "
        f"(SDP, SDDP). Method abbreviations: LP = Linear Programming, "
        f"MILP = Mixed-Integer Linear Programming, SDP = Stochastic "
        f"Dynamic Programming, SDDP = Stochastic Dual Dynamic "
        f"Programming, Econ-Engi = Economic-Engineering approach."
    )
    _captions.append(("fig_year_method_stacked", caption))
    _print(f"\n  Caption: {caption[:80]}...")



# ──────────────────────────────────────────────
# 4. Chart 2: Geographic Distribution
# ──────────────────────────────────────────────

def create_geographic_distribution(df: pd.DataFrame) -> None:
    """
    Chart 2: Horizontal bar chart showing papers per country/region.

    Uses Study_region_clean from classification table.
    Shows top 15 + "Other" + "Not specified".
    """
    _subsep("Chart 2: Geographic Distribution")

    n_total = len(df)

    # Count by standardized study region
    region_counts = df["Study_region_clean"].value_counts()

    # Separate "Not specified" and "Synthetic/Theoretical"
    special_categories = {"Not specified", "Synthetic/Theoretical"}
    special_counts = {k: v for k, v in region_counts.items() if k in special_categories}
    regular_counts = {k: v for k, v in region_counts.items() if k not in special_categories}

    # Top 15 regular countries
    regular_sorted = sorted(regular_counts.items(), key=lambda x: x[1], reverse=True)
    top_15 = regular_sorted[:15]
    other_count = sum(count for _, count in regular_sorted[15:])
    n_other = len(regular_sorted[15:])

    # Build display data (bottom to top for horizontal bar)
    display_data = []

    # Add special categories first (will appear at bottom)
    for cat in ["Not specified", "Synthetic/Theoretical"]:
        if cat in special_counts:
            display_data.append((cat, special_counts[cat]))

    # Add "Other" if any
    if other_count > 0:
        display_data.append((f"Other ({n_other} regions)", other_count))

    # Add top 15 in reverse order (so highest count is at top)
    for name, count in reversed(top_15):
        display_data.append((name, count))

    labels = [d[0] for d in display_data]
    counts = [d[1] for d in display_data]

    _print(f"  Showing {len(top_15)} countries + Other + special categories")
    _print(f"  'Not specified': {special_counts.get('Not specified', 0)} "
           f"({special_counts.get('Not specified', 0)/n_total*100:.1f}%)")

    # Create figure
    fig, ax = plt.subplots(figsize=(12, max(5, len(labels) * 0.3)))

    # Color: special categories in gray, regular in steel blue
    colors = []
    for label in labels:
        if label in special_categories or label.startswith("Other"):
            colors.append("#999999")
        else:
            colors.append(STEEL_BLUE)

    bars = ax.barh(
        range(len(labels)),
        counts,
        color=colors,
        edgecolor="white",
        linewidth=0.3,
        height=0.7,
        zorder=2,
    )

    # Count labels at end of each bar
    for i, (count, label) in enumerate(zip(counts, labels)):
        pct = count / n_total * 100
        ax.text(
            count + 0.5, i,
            f"{count} ({pct:.1f}%)",
            va="center", ha="left",
            fontsize=7, color="#333333",
        )

    # Formatting
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Number of Papers")
    _remove_top_right_spines(ax)

    # X-axis grid
    ax.xaxis.grid(True, alpha=0.3, linestyle="-", zorder=0)
    ax.set_axisbelow(True)

    # Extend x-axis to fit labels
    ax.set_xlim(0, max(counts) * 1.25)

    plt.tight_layout()
    _save_figure(fig, "fig_geographic_distribution")

    # Caption
    not_spec_pct = special_counts.get("Not specified", 0) / n_total * 100
    caption = (
        f"Figure X. Geographic distribution of study regions across the "
        f"{n_total} classified papers (top {len(top_15)} countries/regions "
        f"shown). Approximately {not_spec_pct:.1f}% of papers did not "
        f"specify a study region and are categorized as 'Not specified'. "
        f"Country names follow ISO 3166-1 conventions. "
        f"Gray bars indicate non-geographic categories."
    )
    _captions.append(("fig_geographic_distribution", caption))
    _print(f"\n  Caption: {caption[:80]}...")


# ──────────────────────────────────────────────
# 5. Chart 3: WV Data Points by Year × Purpose
# ──────────────────────────────────────────────

def create_wv_datapoints_by_year(df_wv: pd.DataFrame) -> None:
    """
    Chart 3: Stacked bar chart showing number of water value data points
    per year, colored by Purpose_clean.

    This is a NEW figure not in the companion article — it shows
    data extraction density rather than paper counts.
    """
    _subsep("Chart 3: WV Data Points by Year × Purpose")

    # Use Paper_year for the year axis
    year_col = "Paper_year"

    # Cross-tabulation: Year × Purpose_clean
    year_purpose = pd.crosstab(df_wv[year_col], df_wv["Purpose_clean"])

    # Order purposes by total count (descending)
    purpose_order = year_purpose.sum().sort_values(ascending=False).index.tolist()
    year_purpose = year_purpose[purpose_order]

    # Fill missing years
    year_min = int(year_purpose.index.min())
    year_max = int(year_purpose.index.max())
    all_years = range(year_min, year_max + 1)
    year_purpose = year_purpose.reindex(all_years, fill_value=0)

    n_total = year_purpose.sum().sum()
    n_papers = df_wv["ID"].nunique()

    _print(f"  Year range: {year_min}–{year_max}")
    _print(f"  Total data points: {n_total}")
    _print(f"  Unique papers: {n_papers}")
    _print(f"  Purpose breakdown:")
    for purpose in purpose_order:
        count = year_purpose[purpose].sum()
        _print(f"    {purpose:20s}  {count:>4}  ({count/n_total*100:5.1f}%)")

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 5))

    # Stacked bar chart
    bottom = np.zeros(len(year_purpose))
    for purpose in purpose_order:
        values = year_purpose[purpose].values.astype(float)
        color = PURPOSE_COLORS.get(purpose, "#999999")
        ax.bar(
            year_purpose.index,
            values,
            bottom=bottom,
            color=color,
            edgecolor="white",
            linewidth=0.3,
            width=0.8,
            label=purpose,
            zorder=2,
        )
        bottom += values

    # Formatting
    ax.set_xlabel("Publication Year")
    ax.set_ylabel("Number of Water Value Data Points")
    _remove_top_right_spines(ax)

    # Y-axis grid
    ax.yaxis.grid(True, alpha=0.3, linestyle="-", zorder=0)
    ax.set_axisbelow(True)

    # X-axis ticks
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(1))

    # Y-axis integer ticks
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    # Legend
    ax.legend(
        fontsize=8,
        loc="upper left",
        framealpha=0.9,
        ncol=2,
        title="Purpose",
        title_fontsize=9,
    )

    plt.tight_layout()
    _save_figure(fig, "fig_wv_datapoints_by_year")

    # Caption
    caption = (
        f"Figure X. Distribution of {n_total} water value data points "
        f"by publication year ({year_min}–{year_max}), stacked by water "
        f"use purpose. Unlike the publication timeline in the companion "
        f"article [REF-companion], which counts papers, this figure shows "
        f"the number of individual water value observations extracted from "
        f"each paper, revealing the data extraction density across time. "
        f"A single paper may contribute multiple data points (average "
        f"{n_total/n_papers:.1f} per paper). The {n_total} data points "
        f"were extracted from {n_papers} papers reporting numerical "
        f"water values."
    )
    _captions.append(("fig_wv_datapoints_by_year", caption))
    _print(f"\n  Caption: {caption[:80]}...")


# ──────────────────────────────────────────────
# 6. Chart 4: Country × Purpose Heatmap
# ──────────────────────────────────────────────

def create_continent_purpose_heatmap(df_wv: pd.DataFrame) -> None:
    """
    Chart 4: Annotated heatmap showing count of water value data points
    for each Continent × Purpose_clean combination.

    Shows geographic coverage gaps at the continental level.
    """
    _subsep("Chart 4: Continent × Purpose Heatmap")

    # Cross-tabulation
    crosstab = pd.crosstab(df_wv["Continent"], df_wv["Purpose_clean"])

    # Order purposes by total count (descending)
    purpose_order = crosstab.sum().sort_values(ascending=False).index.tolist()
    crosstab = crosstab[purpose_order]

    # Order continents by total count (descending)
    continent_order = crosstab.sum(axis=1).sort_values(ascending=False).index.tolist()
    crosstab = crosstab.reindex(continent_order)

    n_total = len(df_wv)
    n_continents = df_wv["Continent"].nunique()
    n_purposes = df_wv["Purpose_clean"].nunique()

    _print(f"  Cross-tabulation shape: {crosstab.shape}")
    _print(f"  Continents: {list(crosstab.index)}")
    _print(f"  Purposes: {list(crosstab.columns)}")
    _print(f"\n  Cross-tabulation:")
    _print(crosstab.to_string())

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 5))

    # Heatmap
    sns.heatmap(
        crosstab,
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={
            "label": "Number of Data Points",
            "shrink": 0.8,
        },
        ax=ax,
        annot_kws={"size": 10, "fontweight": "bold"},
        vmin=0,
    )

    # Formatting
    ax.set_xlabel("Water Use Purpose", fontsize=10)
    ax.set_ylabel("Continent", fontsize=10)

    ax.set_xticklabels(
        ax.get_xticklabels(),
        rotation=30,
        ha="right",
        fontsize=9,
    )
    ax.set_yticklabels(
        ax.get_yticklabels(),
        rotation=0,
        fontsize=9,
    )

    plt.tight_layout()
    _save_figure(fig, "fig_continent_purpose_heatmap")

    # Caption
    caption = (
        f"Figure X. Cross-tabulation of water value data points by "
        f"continent and water use purpose. Cell values indicate the "
        f"number of data points for each combination. Darker colors "
        f"indicate higher concentrations. The {n_total} data points "
        f"span {n_continents} continents and {n_purposes} purpose "
        f"categories. Continental assignments follow UN M49 macro-"
        f"geographical regions. Empty or low-value cells highlight "
        f"geographic and thematic coverage gaps in the water value "
        f"literature — for example, the concentration of urban/municipal "
        f"water values in North America and the limited coverage of "
        f"African and Oceanian water systems."
    )
    _captions.append(("fig_continent_purpose_heatmap", caption))
    _print(f"\n  Caption: {caption[:80]}...")



# ──────────────────────────────────────────────
# 7. Chart 5: Category × Method Heatmap
# ──────────────────────────────────────────────

def create_category_method_heatmap(df: pd.DataFrame) -> None:
    """
    Chart 5: Annotated heatmap showing count of papers for each
    combination of Classification category and Method_clean.
    """
    _subsep("Chart 5: Classification Category × Method Heatmap")

    # Create cross-tabulation
    crosstab = pd.crosstab(
        df["Classification"],
        df["Method_clean"],
    )

    # Reorder rows and columns
    row_order = [c for c in CATEGORY_ORDER if c in crosstab.index]
    col_order = [m for m in METHOD_ORDER if m in crosstab.columns]

    # Add any categories/methods not in predefined order
    for c in crosstab.index:
        if c not in row_order:
            row_order.append(c)
    for m in crosstab.columns:
        if m not in col_order:
            col_order.append(m)

    crosstab = crosstab.reindex(index=row_order, columns=col_order, fill_value=0)

    _print(f"  Cross-tabulation shape: {crosstab.shape}")
    _print(f"  Row categories: {list(crosstab.index)}")
    _print(f"  Column methods: {list(crosstab.columns)}")
    _print(f"\n  Cross-tabulation:")
    _print(crosstab.to_string())

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 5))

    # Heatmap
    sns.heatmap(
        crosstab,
        annot=True,
        fmt="d",
        cmap="Blues",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={
            "label": "Number of Papers",
            "shrink": 0.8,
        },
        ax=ax,
        annot_kws={"size": 10},
        vmin=0,
    )

    # Formatting
    ax.set_xlabel("Method", fontsize=10)
    ax.set_ylabel("Classification Category", fontsize=10)

    ax.set_xticklabels(
        ax.get_xticklabels(),
        rotation=45,
        ha="right",
        fontsize=9,
    )
    ax.set_yticklabels(
        ax.get_yticklabels(),
        rotation=0,
        fontsize=9,
    )

    plt.tight_layout()
    _save_figure(fig, "fig_category_method_heatmap")

    # Caption
    method_abbrevs = (
        "LP = Linear Programming, MILP = Mixed-Integer Linear Programming, "
        "SDP = Stochastic Dynamic Programming, SDDP = Stochastic Dual "
        "Dynamic Programming, Econ-Engi = Economic-Engineering approach."
    )
    caption = (
        f"Figure X. Cross-tabulation of classification categories and "
        f"optimization/analysis methods across the {len(df)} classified "
        f"papers. Cell values indicate the number of papers using each "
        f"method within each category. Darker colors indicate higher "
        f"concentrations. Category definitions are provided in the "
        f"companion article [REF-companion]. {method_abbrevs}"
    )
    _captions.append(("fig_category_method_heatmap", caption))
    _print(f"\n  Caption: {caption[:80]}...")


# ──────────────────────────────────────────────
# 8. Save captions
# ──────────────────────────────────────────────

def save_captions() -> None:
    """Save all figure captions to a single text file."""
    _subsep("Saving Captions")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    caption_path = FIGURES_DIR / "fig_analytical_charts_captions.txt"

    with open(caption_path, "w", encoding="utf-8") as f:
        f.write("Water Value Database — Analytical Chart Captions\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 72}\n\n")

        for fig_name, caption in _captions:
            f.write(f"[{fig_name}]\n")
            f.write(f"{caption}\n\n")
            f.write(f"{'─' * 72}\n\n")

    size_kb = caption_path.stat().st_size / 1024
    _print(f"  ✓ {caption_path.name}  ({size_kb:.1f} KB)")
    _print(f"  {len(_captions)} captions saved.")


# ──────────────────────────────────────────────
# 9. Save report
# ──────────────────────────────────────────────

def save_report() -> None:
    """Save the full console output as a text report."""
    report_path = FIGURES_DIR / "analytical_charts_report.txt"
    header = (
        f"Water Value Database — Analytical Charts Report\n"
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
    Full analytical charts pipeline:
    1. Load data from SQLite
    2. Set consistent style
    3. Chart 1: Year × Method stacked bar
    4. Chart 2: Geographic distribution
    5. Chart 3: WV data points by year × purpose
    6. Chart 4: Country × Purpose heatmap
    7. Chart 5: Category × Method heatmap
    8. Save captions
    9. Save report
    """
    _sep("BLUEPRINT 2 — B2-T09/T12: Analytical Charts")

    # 1. Load
    _subsep("Loading data")
    df_class, df_wv = load_data()

    # 2. Style
    set_style()

    # 3–7. Generate charts
    _sep("Generating Analytical Charts")

    create_year_method_stacked(df_class)
    create_geographic_distribution(df_class)
    create_wv_datapoints_by_year(df_wv)
    create_continent_purpose_heatmap(df_wv)
    create_category_method_heatmap(df_class)

    # 8. Captions
    _sep("Captions")
    save_captions()

    # 9. Report
    _sep("B2-T09/T12 COMPLETE")
    _print("  5 analytical charts generated.")
    _print(f"  Figures: {FIGURES_DIR}/fig_*.png and fig_*.pdf")
    _print(f"  Captions: {FIGURES_DIR}/fig_analytical_charts_captions.txt")
    _print("")
    _print("  Figures generated:")
    _print("    1. fig_year_method_stacked     — Year × Method (complements companion Fig 3a)")
    _print("    2. fig_geographic_distribution  — Study regions (no companion equivalent)")
    _print("    3. fig_wv_datapoints_by_year    — WV data density by year × purpose (NEW)")
    _print("    4. fig_continent_purpose_heatmap  — Country × Purpose coverage gaps (NEW)")
    _print("    5. fig_category_method_heatmap  — Category × Method cross-tab (no companion equivalent)")
    _print("")
    _print("  Deferred figures:")
    _print("    - Water value box plot by purpose (waiting for unit conversion)")
    _print("")
    _print("  Removed figures:")
    _print("    - Method distribution donut (duplicates companion Fig 3b)")
    _print("    - Year distribution simple bar (replaced by year × method stacked)")
    _print("")
    _print("  Ready for B2-T13 (overlap check and figure inventory).")

    save_report()


# ──────────────────────────────────────────────
# Module-level execution
# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()
