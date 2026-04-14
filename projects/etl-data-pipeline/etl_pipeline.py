"""
etl_pipeline.py
---------------
Main ETL pipeline: Extract → Transform → Load

Ingests data from three sources (CRM CSV, Billing API JSON, Marketing CSV),
cleans and validates it, then loads into a SQLite analytics warehouse.

Usage:
    python etl_pipeline.py --run-date 2024-01-15
    python etl_pipeline.py --source crm_csv

Author: Allen Day
"""

import argparse
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

from transform.cleaners import (
    standardize_dates, normalize_currency,
    deduplicate, handle_missing_values,
    normalize_channel, clean_email, clean_text_columns,
)
from transform.validators import (
    validate, TRANSACTION_RULES, CUSTOMER_RULES, MARKETING_RULES,
)

# ─── LOGGING ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("etl")

# ─── CONFIG ─────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "analytics.db"
SCHEMA_PATH = BASE_DIR / "sql" / "create_tables.sql"
DATA_DIR = BASE_DIR / "data"  # place source files here


# ─── DATABASE SETUP ─────────────────────────────────────────────────────────

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create DB and apply schema if not already present."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    if SCHEMA_PATH.exists():
        ddl = SCHEMA_PATH.read_text()
        conn.executescript(ddl)
        conn.commit()
        logger.info("Schema applied ✅")
    return conn


# ─── EXTRACT ────────────────────────────────────────────────────────────────

def extract_crm_csv(path: Path) -> pd.DataFrame:
    """Read CRM export CSV. Handles encoding variations."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path, encoding=encoding, low_memory=False)
            logger.info(f"CRM CSV: {len(df):,} rows extracted (encoding={encoding})")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode file: {path}")


def extract_billing_api(path: Path) -> pd.DataFrame:
    """Parse nested JSON from billing API export."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    records = raw.get("transactions", raw) if isinstance(raw, dict) else raw
    df = pd.json_normalize(records)
    logger.info(f"Billing API: {len(df):,} rows extracted")
    return df


def extract_marketing_csv(path: Path) -> pd.DataFrame:
    """Read marketing platform CSV export."""
    df = pd.read_csv(path, low_memory=False)
    logger.info(f"Marketing CSV: {len(df):,} rows extracted")
    return df


def _simulate_data(source: str) -> pd.DataFrame:
    """Generate synthetic data for demonstration when real files aren't present."""
    np.random.seed(42)
    n = 1200

    if source == "crm":
        return pd.DataFrame({
            "customer_id": [f"C{i:05d}" for i in range(n)],
            "email": [f"user{i}@example.com" for i in range(n)],
            "full_name": [f"Customer {i}" for i in range(n)],
            "region": np.random.choice(["West", "East", "Central", "South"], n),
            "signup_date": pd.date_range("2021-01-01", periods=n, freq="6H").strftime("%Y-%m-%d"),
            "source_system": "crm",
        })

    elif source == "billing":
        cust_ids = [f"C{np.random.randint(0, n):05d}" for _ in range(n * 3)]
        return pd.DataFrame({
            "transaction_id": [f"T{i:07d}" for i in range(n * 3)],
            "customer_id": cust_ids,
            "amount": np.abs(np.random.lognormal(4.8, 1.1, n * 3)).round(2),
            "currency": np.random.choice(["USD", "EUR", "GBP", "CAD"], n * 3,
                                          p=[0.70, 0.15, 0.10, 0.05]),
            "transaction_date": pd.date_range("2022-01-01", periods=n * 3, freq="2H").strftime("%Y-%m-%d"),
            "product_sku": np.random.choice(["SKU-001", "SKU-002", "SKU-003", "SKU-004"], n * 3),
            "payment_method": np.random.choice(["card", "ach", "paypal"], n * 3),
            "status": np.random.choice(["completed", "completed", "completed",
                                         "refunded", "failed"], n * 3),
        })

    elif source == "marketing":
        cust_ids = [f"C{np.random.randint(0, n):05d}" for _ in range(n * 2)]
        return pd.DataFrame({
            "event_id": [f"E{i:07d}" for i in range(n * 2)],
            "customer_id": cust_ids,
            "campaign_id": np.random.choice(["CAMP-01", "CAMP-02", "CAMP-03"], n * 2),
            "campaign_name": np.random.choice(["Q1 Email Blast", "Retargeting", "Summer Sale"], n * 2),
            "channel": np.random.choice(["email", "paid social", "organic search",
                                          "referral program"], n * 2),
            "event_type": np.random.choice(["open", "click", "convert"], n * 2,
                                            p=[0.5, 0.35, 0.15]),
            "event_date": pd.date_range("2022-01-01", periods=n * 2, freq="1H").strftime("%Y-%m-%d"),
            "revenue_attr": np.where(np.random.random(n * 2) > 0.85,
                                      np.abs(np.random.normal(150, 50, n * 2)), 0).round(2),
        })

    raise ValueError(f"Unknown source: {source}")


# ─── TRANSFORM ──────────────────────────────────────────────────────────────

def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming customerr…")
    df = clean_text_columns(df, lower_cols=["email"], strip_cols=["full_name", "region"])
    df = standardize_dates(df, ["signup_date"])
    df = deduplicate(df, key_columns=["customer_id"])
    df = handle_missing_values(df)
    df["email"] = df.get("email", pd.Series()).apply(clean_email)
    return df


def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming transactions…")
    df = standardize_dates(df, ["transaction_date"])
    df = normalize_currency(df, amount_col="amount", currency_col="currency")
    df = deduplicate(df, key_columns=["transaction_id"])
    df = handle_missing_values(df)
    return df


def transform_marketing(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming marketing events…")
    df = standardize_dates(df, ["event_date"])
    df["channel"] = df["channel"].apply(normalize_channel)
    df = deduplicate(df, key_columns=["event_id"])
    df = handle_missing_values(df)
    return df


# ─── LOAD ────────────────────────────────────────────────────────────────────

def upsert(conn: sqlite3.Connection, df: pd.DataFrame,
           table: str, pk_col: str) -> int:
    """
    INSERT OR REPLACE rows into target table.
    Returns number of rows written.
    """
    if df.empty:
        return 0
    placeholders = ", ".join(["?"] * len(df.columns))
    cols = ", ".join(df.columns)
    sql = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
    conn.executemany(sql, df.values.tolist())
    conn.commit()
    logger.info(f"Loaded {len(df):,} rows → {table}")
    return len(df)


def log_run(conn: sqlite3.Connection, source: str,
            extracted: int, loaded: int, rejected: int,
            status: str, error: str = None) -> None:
    conn.execute(
        """INSERT INTO etl_run_log
               (source, rows_extracted, rows_loaded, rows_rejected, status, error_message)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (source, extracted, loaded, rejected, status, error),
    )
    conn.commit()


# ─── ORCHESTRATION ─────────────────────────────────────────────────────────

def run_pipeline(sources: list[str] = None) -> dict:
    """
    Run the full ETL pipeline for specified sources.

    Parameters
    ----------
    sources : list of source names ('crm', 'billing', 'marketing');
              defaults to all three

    Returns
    -------
    dict with run statistics
    """
    sources = sources or ["crm", "billing", "marketing"]
    conn = init_db()
    stats = {}
    start_time = time.time()

    logger.info("=" * 60)
    logger.info(f"ETL run started — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for source in sources:
        logger.info(f"\n── {source.upper()} ─────────────────────────────────")
        t0 = time.time()

        try:
            # EXTRACT
            crm_path = DATA_DIR / "crm_export.csv"
            if source == "crm":
                df_raw = extract_crm_csv(crm_path) if crm_path.exists() else _simulate_data("crm")
                df_clean = transform_customers(df_raw)
                result = validate(df_clean, CUSTOMER_RULES, label="customers")
                loaded = upsert(conn, result.passed, "dim_customers", "customer_id")
                table = "dim_customers"

            elif source == "billing":
                api_path = DATA_DIR / "billing_export.json"
                df_raw = extract_billing_api(api_path) if api_path.exists() else _simulate_data("billing")
                df_clean = transform_transactions(df_raw)
                result = validate(df_clean, TRANSACTION_RULES, label="transactions")
                loaded = upsert(conn, result.passed, "fact_transactions", "transaction_id")
                table = "fact_transactions"

            elif source == "marketing":
                mkt_path = DATA_DIR / "marketing_export.csv"
                df_raw = extract_marketing_csv(mkt_path) if mkt_path.exists() else _simulate_data("marketing")
                df_clean = transform_marketing(df_raw)
                result = validate(df_clean, MARKETING_RULES, label="marketing")
                loaded = upsert(conn, result.passed, "fact_marketing_events", "event_id")
                table = "fact_marketing_events"

            rejected = len(result.failed)
            log_run(conn, source, len(df_raw), loaded, rejected, "success")
            elapsed = round(time.time() - t0, 2)
            stats[source] = {"status": "success", "loaded": loaded,
                              "rejected": rejected, "seconds": elapsed}
            logger.info(f"✅ {source} complete in {elapsed}s")

        except Exception as e:
            logger.error(f"❌ {source} FAILED: {e}")
            log_run(conn, source, 0, 0, 0, "failed", str(e))
            stats[source] = {"status": "failed", "error": str(e)}

    total_elapsed = round(time.time() - start_time, 2)
    logger.info(f"\n{'='*60}")
    logger.info(f"Pipeline complete in {total_elapsed}s")
    conn.close()
    return stats


# ─── CLI ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ETL data pipeline")
    parser.add_argument("--source", nargs="+",
                        choices=["crm", "billing", "marketing"],
                        help="Which source(s) to run (default: all)")
    parser.add_argument("--run-date", help="Override run date (YYYY-MM-DD)")
    args = parser.parse_args()

    results = run_pipeline(sources=args.source)
    print("\n── Run Summary ─────────────────────────────────────")
    for src, info in results.items():
        status_icon = "✅" if info["status"] == "success" else "❌"
        if info["status"] == "success":
            print(f"  {status_icon} {src}: {info['loaded']:,} loaded, "
                  f"{info['rejected']} rejected ({info['seconds']}s)")
        else:
            print(f"  {status_icon} {src}: FAILED — {info.get('error')}")
