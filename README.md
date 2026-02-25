# Water Value Database: A Systematic Review Dataset

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![DOI](https://img.shields.io/badge/DOI-PLACEHOLDER-blue.svg)](https://doi.org/PLACEHOLDER)

## Description

The Water Value Database is a systematically curated dataset of economic water valuations extracted from 276 peer-reviewed studies identified through a PRISMA 2020-compliant systematic literature review. The database contains 461 numerical water value data points spanning multiple decades, countries, water-use sectors, and estimation methods, with standardized unit conversions enabling direct cross-study comparison.

**Companion article:** [PLACEHOLDER — title, authors, journal, DOI]

---

## Dataset Files

All data files are located in the `data/` directory.

### CSV Files

| File | Rows | Description |
|------|------|-------------|
| `01_Screening_clean.csv` | 656 | Complete PRISMA search trail from four academic databases (Scopus, IEEE Xplore, ASCE Library, Web of Science). Contains all search results with screening decisions, exclusion reasons, and derived inclusion/exclusion flags. All records retained — included and excluded — to ensure full reproducibility of the screening process. |
| `02_Classification_clean.csv` | 276 | Metadata for the 276 included papers. Contains thematic classification (categories A–H, R), methodological approach, study region, and systematically extracted problem statements, research gaps, and contributions. Serves as the authority file and single source of truth for paper-level metadata. |
| `03_WaterValue_clean.csv` | 461 | Numerical water value data points extracted from included papers. Contains raw values as reported in source papers, a single multiplicative conversion factor (combining volume standardization, currency conversion, and CPI adjustment), and converted values in standardized units. Includes geographic, sectoral, and methodological metadata for each data point. |

### Database Files

| File | Description |
|------|-------------|
| `water_value_database.db` | SQLite database containing all three tables (`screening`, `classification`, `water_values`) with indexes on key columns. Suitable for programmatic access and SQL queries. |
| `water_value_database.xlsx` | Excel workbook with three sheets (one per CSV file). Suitable for manual inspection and filtering. |

---

## Python Scripts

All scripts are located in the `scripts/` directory. The pipeline reads from the raw CSV files in `data/`, processes and reconciles the data, and produces all derived outputs.

| Script | Description |
|--------|-------------|
| `01_data_preparation.py` | Loads all three raw CSVs, cleans artifacts, reconciles cross-file relationships, renames columns to professional standards, anonymizes screener identifiers, adds derived columns (`Final_Decision`, `Exclusion_Stage`), and exports the SQLite database, Excel workbook, and clean CSVs. |
| `02_derived_variables.py` | Standardizes column values and creates derived analytical variables: `Year_numeric`, `Decade`, `Has_water_value`, three-level method hierarchy (`Method_clean`, `Method_category`, `Method_detail`), ISO-aligned geographic names (`Study_region_clean`, `Country_clean`, `Continent`), standardized purposes (`Purpose_clean`), and standardized units (`units_clean`). |
| `02_summary_tables.py` | Generates summary statistics tables: papers by classification category, method type, study region/country, publication year range, and water value summary statistics by purpose. Exports as CSV and formatted text. |
| `03_completeness_heatmap.py` | Calculates column-level data completeness for all three files and generates an annotated heatmap visualization (RdYlGn colormap). |
| `04_analytical_charts.py` | Generates publication-quality analytical figures: publication year distribution, geographic distribution, method distribution (donut chart), water value range by purpose (box plot, log scale), and classification category × method cross-tabulation heatmap. |
| `05_overlap_check.py` | Compares generated figures and tables against the companion article to flag any duplicate visualizations or content overlap. |
| `06_run_pipeline.py` | Runs all scripts in sequence and verifies that all expected outputs are generated. |

### How to Run

**Prerequisites:** Python 3.9+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates .venv automatically)
uv sync

# Run the full pipeline
uv run python scripts/04_run_pipeline.py
```

Alternatively, run individual scripts in numbered order:
```bash
python scripts/01_data_preparation.py
python scripts/02_derived_variables.py
python scripts/01_summary_tables.py
python scripts/02_completeness_heatmap.py
python scripts/03_analytical_charts.py
python scripts/05_overlap_check.py
```

Note: Scripts 01 and 02_derived_variables must run before all others. The remaining scripts depend on the SQLite database produced by the first two scripts.

### Figures
All figures are located in the figures/ directory. Each figure is provided in both PNG (300 dpi) and PDF formats.

### List of Figures and Visualizations

| Figure ID | Description |
| :--- | :--- |
| **fig_database_schema** | **Database schema diagram** showing the structure and relationships between the three dataset files, including column names, data types, primary/foreign keys, and derived columns. |
| **fig_workflow_diagram** | **Six-stage data extraction and quality assurance workflow**, from literature search through final database assembly. Distinguishes stages documented in the companion article from stages documented in this dataset article. |
| **fig_completeness_heatmap** | **Column-level data completeness** across all three files, annotated with percentage values. Distinguishes intentional sparsity from data limitation gaps. |
| **fig_year_distribution** | **Distribution of included papers** by publication year. |
| **fig_geographic_distribution** | **Geographic distribution** of water value data points by country. |
| **fig_method_distribution** | **Distribution of estimation methods** across included papers (donut chart). |
| **fig_wv_boxplot** | **Water value ranges** by purpose/sector (box plot on logarithmic scale). |
| **fig_category_method_heatmap** | **Cross-tabulation** of classification categories and method types. |

---

### Citation

If you use this dataset, please cite:

**Dataset:**
> [PLACEHOLDER — Authors]. (2025). *Water Value Database: A Systematic Review Dataset (Version 1.0.0)* [Data set]. Zenodo. https://doi.org/PLACEHOLDER

**Companion article:**
> [PLACEHOLDER — full citation of companion article]


### License

This dataset is licensed under the **Creative Commons Attribution 4.0 International License (CC-BY 4.0)**.

**You are free to:**
* **Share** — copy and redistribute the material in any medium or format.
* **Adapt** — remix, transform, and build upon the material for any purpose, including commercially.

**Under the following terms:**
* **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made.

---

### Companion Article

This dataset accompanies the following research article:

> [PLACEHOLDER — title, authors, journal, DOI]

The companion article presents the **systematic review methodology**, **classification framework definitions**, and **analytical findings**. This repository provides the complete underlying data, processing scripts, and visualizations.

### Repository Structure

```bash
water-value-database/
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── data/
│   ├── 01_Screening_clean.csv
│   ├── 02_Classification_clean.csv
│   ├── 03_WaterValue_clean.csv
│   ├── water_value_database.db
│   └── water_value_database.xlsx
├── scripts/
│   ├── 01_summary_tables.py
│   ├── 02_completeness_heatmap.py
│   ├── 03_analytical_charts.py
│   └── 04_run_pipeline.py
├── figures/
│   ├── fig_category_method_heatmap.png
│   ├── fig_category_method_heatmap.pdf
│   ├── fig_completeness_heatmap.png
│   ├── fig_completeness_heatmap.pdf
│   ├── fig_continent_purpose_heatmap.png
│   ├── fig_continent_purpose_heatmap.pdf
│   ├── fig_geographic_distribution.png
│   ├── fig_geographic_distribution.pdf
│   ├── fig_wv_datapoints_by_year.png
│   ├── fig_wv_datapoints_by_year.pdf
│   ├── fig_year_method_stacked.png
│   ├── fig_year_method_stacked.pdf
│   ├── fig_analytical_charts_captions.txt
│   ├── fig_completeness_heatmap_caption.txt
│   ├── analytical_charts_report.txt
│   ├── completeness_heatmap_report.txt
│   └── summary_tables_report.txt
└── tables/
    ├── all_tables_formatted.txt
    ├── table_1_classification.csv
    ├── table_2_methods.csv
    ├── table_3_regions.csv
    ├── table_4_years.csv
    ├── table_5_wv_summary.csv
    └── table_6_wv_purpose.csv
```
