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

All scripts are located in the `scripts/` directory. The scripts read from the SQLite database in `data/` and regenerate all summary tables and figures.

| Script | Description |
|--------|-------------|
| `01_summary_tables.py` | Generates summary statistics tables: papers by classification category, method type, study region/country, publication year range, and water value summary statistics by purpose. Exports as CSV and formatted text to `tables/`. |
| `02_completeness_heatmap.py` | Calculates column-level data completeness for all three files and generates an annotated heatmap visualization (RdYlGn colormap). Exports to `figures/`. |
| `03_analytical_charts.py` | Generates publication-quality analytical figures: year × method stacked bar with trendlines, geographic distribution, water value data points by year × purpose, continent × purpose heatmap, and classification category × method heatmap. Exports to `figures/`. |
| `04_run_pipeline.py` | Runs all analysis scripts in sequence and verifies that all expected outputs are generated. |

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
uv run python scripts/01_summary_tables.py
uv run python scripts/02_completeness_heatmap.py
uv run python scripts/03_analytical_charts.py
```

Without uv: You can also use pip directly:
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install .
python scripts/04_run_pipeline.py
```

All scripts read from data/water_value_database.db and write outputs to figures/ and tables/.


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


### Tables

All summary tables are located in the `tables/` directory.

| Table File | Description |
| :--- | :--- |
| `table_1_classification.csv` | **Papers by classification category** (A–H, R). |
| `table_2_methods.csv` | **Papers by method type** (Method_clean). |
| `table_3_regions.csv` | **Papers by study region/country.** |
| `table_4_years.csv` | **Papers by publication year range.** |
| `table_5_wv_summary.csv` | **Water value summary statistics.** |
| `table_6_wv_purpose.csv` | **Water values by purpose/sector.** |
| `all_tables_formatted.txt` | **All tables combined** in formatted text. |

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

### Contact
For questions about this dataset, please open an issue in this repository or contact the corresponding author at mpavicevic@anl.gov. 
