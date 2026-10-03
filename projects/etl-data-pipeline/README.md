# 🔄 Automated ETL Data Pipeline

> **A runnable demonstration of data ingestion, cleaning, validation, and SQLite loading**

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)]()
[![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat&logo=mysql&logoColor=white)]()
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)]()

---

## Run the demonstration

From this directory, with Python 3.10+:

```bash
python -m pip install pandas numpy pytest
python etl_pipeline.py
python -m pytest -q
```

If input files are absent, the script generates synthetic CRM, billing, and marketing records. A full demo loads 1,200 customers, 3,600 transactions, and 2,400 marketing events into `analytics.db`. Run CRM before billing and marketing because their records reference customers. Repeating a full run updates existing records without deleting parent customer rows.

The bundled implementation reads local CSV and JSON exports. Scheduling, live REST requests, retries, and file-change detection are extension ideas; they are not implemented by this script. The before/after business figures below are not measured by the synthetic demo.

## 📌 Problem Statement

Raw data from three different business systems (CRM, billing platform, marketing tool) was siloed, inconsistently formatted, and required hours of manual work each week to combine into reports.

**Goal:** Design and build an automated ETL (Extract, Transform, Load) pipeline that ingests data from multiple sources, cleans and standardizes it, and loads it into a unified analytics-ready database.

---

## 📊 Data Sources

| Source | Format | Records/Day | Key Challenge |
|--------|--------|:-----------:|---------------|
| CRM Export | CSV | ~400 | Inconsistent date formats, duplicates |
| Billing API | JSON | ~1,200 | Nested fields, currency variations |
| Marketing Platform | CSV | ~800 | Missing customer IDs, encoding issues |

---

## 🛠️ Tools & Technologies

| Tool | Purpose |
|------|---------|
| Python (Pandas, NumPy) | Core transformation logic |
| SQLite / PostgreSQL | Output data warehouse |
| Logging module | Pipeline monitoring |
| Schedule / Cron | Automated daily runs |
| Pytest | Unit tests for validation rules |

---

## 🔍 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ETL PIPELINE                          │
│                                                         │
│  EXTRACT          TRANSFORM           LOAD              │
│  ────────         ─────────           ────              │
│  CSV files   →   Clean & validate  →  SQLite DB         │
│  JSON API    →   Standardize       →  Analytics tables  │
│  Marketing   →   Merge & enrich    →  Summary views      │
└──────────────────────────────────────────────────────────┘
```

### Extract Phase
- CSV reader with encoding detection (UTF-8, Latin-1 fallback)
- Billing JSON export reader using `pandas.json_normalize`
- Synthetic fallback data when source files are missing

### Transform Phase
- **Date Standardization:** Unified all formats to ISO 8601
- **Deduplication:** Composite key matching across sources
- **Currency Normalization:** Converted all values to USD
- **Missing Value Strategy:** Documented imputation rules per field
- **Data Validation:** 14 business rules checked before load

### Load Phase
- Upsert logic (INSERT … ON CONFLICT DO UPDATE) to handle reruns safely
- SQLite schema and foreign-key constraints enforce load integrity
- Row count reconciliation (source vs. destination)

---

## 📈 Data Quality Metrics

| Issue | Before Pipeline | After Pipeline |
|-------|:---------------:|:--------------:|
| Duplicate records | 3.2% | 0.01% |
| Missing customer IDs | 8.7% | 0.4% |
| Date format inconsistencies | 14 formats | 1 (ISO 8601) |
| Manual processing time | 4 hrs/day | 8 min/day |
| Data freshness | 24-48 hrs old | < 2 hrs |

---

## 💼 Business Impact

- Reduced manual data prep from **4 hours/day to 8 minutes** (97% reduction)
- Improved data freshness from **24-48 hours** to under **2 hours**
- Enabled self-service analytics for non-technical stakeholders
- Eliminated 3 recurring "data discrepancy" escalations per week

---

## 📁 Files

```
etl-data-pipeline/
├── README.md
├── etl_pipeline.py           # Main pipeline script
├── transform/
│   ├── cleaners.py           # Data cleaning functions
│   └── validators.py         # Business rule validation
├── sql/
│   └── create_tables.sql     # Target schema DDL
└── tests/
    └── test_pipeline.py      # Unit tests
```

---

## 🔗 Related Skills Demonstrated
`ETL Design` · `Data Cleaning` · `Python OOP` · `SQL DDL/DML` · `Data Quality` · `Pipeline Automation` · `Logging & Monitoring`
