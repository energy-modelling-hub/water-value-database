#!/usr/bin/env python3
"""
01_summary_tables.py
====================
Summary statistics table generation for the Water Value Database –
Data in Brief article.

Generates six publication-ready summary tables from the reconciled and
standardized database:

    Table 1: Papers by Classification Category
    Table 2: Papers by Method Type (Method_clean)
    Table 3: Papers by Study Region / Country
    Table 4: Papers by Publication Year Range
    Table 5: Water Value Summary Statistics
    Table 6: Water Values by Purpose

All tables are exported as:
    - Individual CSV files  (for GitHub/Zenodo repository)
    - A single formatted text file (for manuscript insertion)

Usage
-----
    python 01_summary_tables.py

Inputs
------
    output/water_value_database.db  (from 02_derived_variables.py)

Outputs
-------
    output/figures_tables/table_1_classification.csv
    output/figures_tables/table_2_methods.csv
    output/figures_tables/table_3_regions.csv
    output/figures_tables/table_4_years.csv
    output/figures_tables/table_5_wv_summary.csv
    output/figures_tables/table_6_wv_purpose.csv
    output/figures_tables/all_tables_formatted.txt

Author : [Author team]
Task   : Blueprint 2, Tasks B2-T04 through B2-T07
"""

import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from fontTools.ufoLib import DATA_DIRNAME

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DATA_DIR = Path("./data")
FIGURES_DIR = Path("./figures")
SQLITE_PATH = DATA_DIR / "water_value_database.db"
TABLES_DIR = Path("./tables")

# Classification category names — from companion article (article.txt)
# Update these with exact names from your manuscript.
CATEGORY_NAMES = {
    "A": "Hydropower scheduling and water values",
    "B": "Stochastic programming for hydropower",
    "C": "Hydro-economic modelling",
    "D": "Irrigation and agricultural water value",
    "E": "Urban and municipal water value",
    "F": "Environmental and ecological water value",
    "G": "Multi-purpose reservoir operation",
    "H": "Water markets and pricing",
    "R": "Review / Other",
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
# 2. Table generators
# ──────────────────────────────────────────────

def generate_classification_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Table 1: Papers by Classification Category.

    Columns: Category, Category_Name, Count, Percentage
    Sorted by category letter (A–R).
    Includes TOTAL row.
    """
    _subsep("Table 1: Papers by Classification Category")

    n_total = len(df)
    counts = df["Classification"].value_counts().sort_index()

    rows = []
    for cat in sorted(counts.index):
        count = counts[cat]
        pct = count / n_total * 100
        name = CATEGORY_NAMES.get(cat, "[Category name — see article.txt]")
        rows.append({
            "Category": cat,
            "Category_Name": name,
            "Count": count,
            "Percentage": round(pct, 1),
        })

    # Total row
    rows.append({
        "Category": "Total",
        "Category_Name": "",
        "Count": n_total,
        "Percentage": 100.0,
    })

    table = pd.DataFrame(rows)

    # Print
    _print(f"  {'Category':<10s} {'Name':<50s} {'Count':>6s} {'%':>7s}")
    _print(f"  {'—'*10} {'—'*50} {'—'*6} {'—'*7}")
    for _, row in table.iterrows():
        _print(f"  {row['Category']:<10s} {row['Category_Name']:<50s} "
               f"{row['Count']:>6} {row['Percentage']:>6.1f}%")

    return table


def generate_method_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Table 2: Papers by Method Type (Method_clean).

    Columns: Method, Count, Percentage
    Sorted by count (descending).
    7 manuscript-aligned categories only.
    Includes TOTAL row.
    """
    _subsep("Table 2: Papers by Method Type")

    n_total = len(df)

    counts = df["Method_clean"].value_counts()

    rows = []
    for method, count in counts.items():
        pct = count / n_total * 100
        rows.append({
            "Method": method,
            "Count": count,
            "Percentage": round(pct, 1),
        })

    # Sort by count descending
    rows.sort(key=lambda x: x["Count"], reverse=True)

    # Total row
    rows.append({
        "Method": "Total",
        "Count": n_total,
        "Percentage": 100.0,
    })

    table = pd.DataFrame(rows)

    # Print
    _print(f"  {'Method':<20s} {'Count':>6s} {'%':>7s}")
    _print(f"  {'—'*20} {'—'*6} {'—'*7}")
    for _, row in table.iterrows():
        _print(f"  {row['Method']:<20s} {row['Count']:>6} {row['Percentage']:>6.1f}%")

    return table



def generate_region_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Table 3: Papers by Study Region / Country.

    Uses Study_region_clean (standardized) from classification.
    Countries with count < 3 grouped under "Other".

    Columns: Country_or_Region, Count, Percentage
    Sorted by count (descending).
    Includes TOTAL row.
    """
    _subsep("Table 3: Papers by Study Region / Country")

    n_total = len(df)

    # Use standardized column
    regions = df["Study_region_clean"].copy()

    # Count
    raw_counts = regions.value_counts()

    # Separate "Not specified" and "Synthetic/Theoretical" — always show
    always_show = {"Not specified", "Synthetic/Theoretical"}

    # Group countries with count < 3 into "Other" (excluding always-show)
    main_entries = {}
    other_count = 0
    n_other_entries = 0

    for region, count in raw_counts.items():
        if region in always_show:
            main_entries[region] = count
        elif count >= 3:
            main_entries[region] = count
        else:
            other_count += count
            n_other_entries += 1

    rows = []
    for region, count in main_entries.items():
        pct = count / n_total * 100
        rows.append({
            "Country_or_Region": region,
            "Count": count,
            "Percentage": round(pct, 1),
        })

    if other_count > 0:
        rows.append({
            "Country_or_Region": f"Other ({n_other_entries} countries/regions)",
            "Count": other_count,
            "Percentage": round(other_count / n_total * 100, 1),
        })

    # Sort by count descending
    rows.sort(key=lambda x: x["Count"], reverse=True)

    # Total row
    rows.append({
        "Country_or_Region": "Total",
        "Count": n_total,
        "Percentage": 100.0,
    })

    table = pd.DataFrame(rows)

    # Calculate % not specified for caption
    not_specified_count = raw_counts.get("Not specified", 0)
    not_specified_pct = not_specified_count / n_total * 100

    # Print
    _print(f"  {'Country/Region':<50s} {'Count':>6s} {'%':>7s}")
    _print(f"  {'—'*50} {'—'*6} {'—'*7}")
    for _, row in table.iterrows():
        _print(f"  {row['Country_or_Region']:<50s} "
               f"{row['Count']:>6} {row['Percentage']:>6.1f}%")

    _print(f"\n  Note: {not_specified_pct:.1f}% of papers did not specify a study region.")

    return table



def generate_year_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Table 4: Papers by Publication Year Range.

    Uses Decade derived variable (5-year bins).
    Columns: Year_Range, Count, Percentage
    Sorted chronologically.
    Includes TOTAL row and year statistics.
    """
    _subsep("Table 4: Papers by Publication Year Range")

    n_total = len(df)

    # Use Decade column (already created in derived variables)
    decade_order = ["Pre-2000", "2000–2004", "2005–2009",
                    "2010–2014", "2015–2019", "2020–2025"]

    decade_counts = df["Decade"].value_counts()

    rows = []
    for decade in decade_order:
        count = decade_counts.get(decade, 0)
        pct = count / n_total * 100
        rows.append({
            "Year_Range": decade,
            "Count": count,
            "Percentage": round(pct, 1),
        })

    # Total row
    rows.append({
        "Year_Range": "Total",
        "Count": n_total,
        "Percentage": 100.0,
    })

    table = pd.DataFrame(rows)

    # Print
    _print(f"  {'Year Range':<15s} {'Count':>6s} {'%':>7s}")
    _print(f"  {'—'*15} {'—'*6} {'—'*7}")
    for _, row in table.iterrows():
        _print(f"  {row['Year_Range']:<15s} {row['Count']:>6} {row['Percentage']:>6.1f}%")

    # Year statistics
    year_min = df["Year_numeric"].min()
    year_max = df["Year_numeric"].max()
    year_median = df["Year_numeric"].median()
    _print(f"\n  Earliest year: {year_min}")
    _print(f"  Latest year:   {year_max}")
    _print(f"  Median year:   {year_median:.0f}")

    return table


def generate_wv_summary_table(
    df_class: pd.DataFrame,
    df_wv: pd.DataFrame,
) -> pd.DataFrame:
    """
    Table 5: Water Value Summary Statistics.

    Two-column table (Statistic, Value) with key dataset metrics.
    """
    _subsep("Table 5: Water Value Summary Statistics")

    # Compute statistics
    n_papers_with_wv = df_wv["ID"].nunique()
    n_data_points = len(df_wv)
    n_countries = df_wv["Country_clean"].nunique()
    n_continents = df_wv["Continent"].nunique()
    n_methods_clean = df_wv["Method_clean"].nunique()
    n_methods_detail = df_wv["Method_detail"].nunique()
    n_purposes = df_wv["Purpose_clean"].nunique()
    n_units = df_wv["units_clean"].nunique()

    # Year range
    year_col = "Paper_year" if "Paper_year" in df_wv.columns else "Year"
    yr_min = int(df_wv[year_col].min())
    yr_max = int(df_wv[year_col].max())

    # Most common values
    most_common_purpose = df_wv["Purpose_clean"].mode().iloc[0]
    most_common_unit = df_wv["units_clean"].mode().iloc[0]
    most_common_country = df_wv["Country_clean"].mode().iloc[0]
    most_common_method = df_wv["Method_clean"].mode().iloc[0]

    # Data points per paper
    points_per_paper = df_wv.groupby("ID").size()
    avg_points = points_per_paper.mean()
    max_points = points_per_paper.max()
    max_paper_id = points_per_paper.idxmax()

    # WV_median_raw coverage
    n_median_filled = df_wv["WV_median_raw"].notna().sum()
    pct_median = n_median_filled / n_data_points * 100

    stats = [
        ("Total papers reporting numerical water values", f"{n_papers_with_wv}"),
        ("Total water value data points", f"{n_data_points}"),
        ("Countries represented", f"{n_countries}"),
        ("Continents represented", f"{n_continents}"),
        ("Method categories (manuscript-level)", f"{n_methods_clean}"),
        ("Method types (detailed)", f"{n_methods_detail}"),
        ("Purpose categories", f"{n_purposes}"),
        ("Unique unit types", f"{n_units}"),
        ("Publication year range", f"{yr_min}–{yr_max}"),
        ("Most common purpose", f"{most_common_purpose}"),
        ("Most common unit", f"{most_common_unit}"),
        ("Most common country", f"{most_common_country}"),
        ("Most common method", f"{most_common_method}"),
        ("Average data points per paper", f"{avg_points:.1f}"),
        ("Maximum data points (single paper)", f"{max_points} (ID: {max_paper_id})"),
        ("WV_median_raw completeness", f"{n_median_filled}/{n_data_points} ({pct_median:.1f}%)"),
    ]

    table = pd.DataFrame(stats, columns=["Statistic", "Value"])

    # Print
    _print(f"  {'Statistic':<50s} {'Value':<30s}")
    _print(f"  {'—'*50} {'—'*30}")
    for _, row in table.iterrows():
        _print(f"  {row['Statistic']:<50s} {row['Value']:<30s}")

    return table


def generate_wv_purpose_table(df_wv: pd.DataFrame) -> pd.DataFrame:
    """
    Table 6: Water Values by Purpose.

    Columns: Purpose, Data_Points_Count, Papers_Count, Countries_Count,
             Continents_Count
    Sorted by Data_Points_Count (descending).
    Includes TOTAL row.
    """
    _subsep("Table 6: Water Values by Purpose")

    n_total = len(df_wv)

    purpose_stats = (
        df_wv.groupby("Purpose_clean")
        .agg(
            Data_Points_Count=("ID", "size"),
            Papers_Count=("ID", "nunique"),
            Countries_Count=("Country_clean", "nunique"),
            Continents_Count=("Continent", "nunique"),
        )
        .reset_index()
        .rename(columns={"Purpose_clean": "Purpose"})
        .sort_values("Data_Points_Count", ascending=False)
    )

    purpose_stats["Pct_of_Data_Points"] = (
        purpose_stats["Data_Points_Count"] / n_total * 100
    ).round(1)

    # Total row
    total_row = pd.DataFrame([{
        "Purpose": "Total",
        "Data_Points_Count": n_total,
        "Papers_Count": df_wv["ID"].nunique(),
        "Countries_Count": df_wv["Country_clean"].nunique(),
        "Continents_Count": df_wv["Continent"].nunique(),
        "Pct_of_Data_Points": 100.0,
    }])

    table = pd.concat([purpose_stats, total_row], ignore_index=True)

    # Print
    _print(f"  {'Purpose':<20s} {'Points':>7s} {'%':>6s} {'Papers':>7s} "
           f"{'Countries':>10s} {'Continents':>11s}")
    _print(f"  {'—'*20} {'—'*7} {'—'*6} {'—'*7} {'—'*10} {'—'*11}")
    for _, row in table.iterrows():
        _print(f"  {row['Purpose']:<20s} {row['Data_Points_Count']:>7} "
               f"{row['Pct_of_Data_Points']:>5.1f}% {row['Papers_Count']:>7} "
               f"{row['Countries_Count']:>10} {row['Continents_Count']:>11}")

    return table


# ──────────────────────────────────────────────
# 3. Export tables
# ──────────────────────────────────────────────

def export_tables(tables: dict[str, pd.DataFrame]) -> None:
    """
    Export all tables as:
    - Individual CSV files
    - Single formatted text file with captions
    """
    _sep("Exporting Tables")

    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # ── CSV export ──
    _subsep("CSV Export")

    csv_names = {
        "table_1": "table_1_classification.csv",
        "table_2": "table_2_methods.csv",
        "table_3": "table_3_regions.csv",
        "table_4": "table_4_years.csv",
        "table_5": "table_5_wv_summary.csv",
        "table_6": "table_6_wv_purpose.csv",
    }

    for key, filename in csv_names.items():
        path = TABLES_DIR / filename
        tables[key].to_csv(path, index=False, encoding="utf-8-sig")
        size_kb = path.stat().st_size / 1024
        _print(f"  ✓ {filename:<35s}  ({size_kb:.1f} KB)")

    # ── Formatted text export ──
    _subsep("Formatted Text Export")

    captions = {
        "table_1": (
            "Table 1. Distribution of 277 classified papers across nine "
            "classification categories. Category definitions are provided "
            "in the companion article [REF-companion]."
        ),
        "table_2": (
            "Table 2. Distribution of optimization and analysis methods "
            "used across the 277 classified papers, grouped by manuscript-"
            "level method categories (Method_clean) and broad methodological "
            "approach (Method_category)."
        ),
        "table_3": (
            "Table 3. Geographic distribution of study regions across the "
            "277 classified papers. Countries or regions with fewer than 3 "
            "papers are grouped under 'Other'. Approximately {not_spec_pct}% "
            "of papers did not specify a study region."
        ),
        "table_4": (
            "Table 4. Temporal distribution of the 277 classified papers "
            "by publication year range."
        ),
        "table_5": (
            "Table 5. Summary statistics of the water value dataset "
            "extracted from papers reporting numerical water values."
        ),
        "table_6": (
            "Table 6. Distribution of water value data points by water use "
            "purpose, showing the number of data points, papers, countries, "
            "and continents represented for each purpose category."
        ),
    }

    # Calculate not-specified percentage for Table 3 caption
    t3 = tables["table_3"]
    not_spec_row = t3[t3["Country_or_Region"] == "Not specified"]
    if len(not_spec_row) > 0:
        not_spec_pct = f"{not_spec_row.iloc[0]['Percentage']:.1f}"
    else:
        not_spec_pct = "0.0"
    captions["table_3"] = captions["table_3"].format(not_spec_pct=not_spec_pct)

    # Write formatted text file
    txt_path = TABLES_DIR / "all_tables_formatted.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Water Value Database — Summary Tables\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 72}\n\n")

        for key in ["table_1", "table_2", "table_3",
                     "table_4", "table_5", "table_6"]:
            # Caption
            f.write(f"{captions[key]}\n\n")

            # Table content
            table_str = tables[key].to_string(index=False)
            f.write(f"{table_str}\n\n")

            f.write(f"{'─' * 72}\n\n")

    size_kb = txt_path.stat().st_size / 1024
    _print(f"  ✓ all_tables_formatted.txt  ({size_kb:.1f} KB)")
    _print(f"\n  All tables exported to: {TABLES_DIR}")


# ──────────────────────────────────────────────
# 4. Save report
# ──────────────────────────────────────────────

def save_report() -> None:
    """Save the full console output as a text report."""
    report_path = FIGURES_DIR / "summary_tables_report.txt"
    header = (
        f"Water Value Database — Summary Tables Report\n"
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

def main() -> dict[str, pd.DataFrame]:
    """
    Full summary tables pipeline:
    1. Load data from SQLite
    2. Generate Table 1: Classification Category
    3. Generate Table 2: Method Type
    4. Generate Table 3: Study Region / Country
    5. Generate Table 4: Publication Year Range
    6. Generate Table 5: Water Value Summary Statistics
    7. Generate Table 6: Water Values by Purpose
    8. Export all tables (CSV + formatted text)
    9. Save report
    """
    _sep("BLUEPRINT 2 — B2-T04/T07: Summary Statistics Tables")

    # 1. Load
    _subsep("Loading data")
    df_class, df_wv = load_data()

    # 2–7. Generate tables
    _sep("Generating Summary Tables")

    tables = {}
    tables["table_1"] = generate_classification_table(df_class)
    tables["table_2"] = generate_method_table(df_class)
    tables["table_3"] = generate_region_table(df_class)
    tables["table_4"] = generate_year_table(df_class)
    tables["table_5"] = generate_wv_summary_table(df_class, df_wv)
    tables["table_6"] = generate_wv_purpose_table(df_wv)

    # 8. Export
    export_tables(tables)

    # 9. Report
    _sep("B2-T04/T07 COMPLETE")
    _print("  6 summary tables generated and exported.")
    _print(f"  CSV files:       {TABLES_DIR}/table_*.csv")
    _print(f"  Formatted text:  {TABLES_DIR}/all_tables_formatted.txt")
    _print("  Ready for B2-T08 (completeness heatmap).")

    save_report()

    return tables


# ──────────────────────────────────────────────
# Module-level execution
# ──────────────────────────────────────────────

if __name__ == "__main__":
    _tables = main()
