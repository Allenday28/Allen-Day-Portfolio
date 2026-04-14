"""
cleaners.py
-----------
Data cleaning and standardization functions for the ETL pipeline.
Applied during the Transform phase before loading to the warehouse.

Author: Allen Day
"""

import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger("etl.cleaners")


# ─── DATE STANDARDIZATION ───────────────────────────────────────────────────

DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%B %d, %Y",
    "%b %d %Y",
    "%Y%m%d",
]


def parse_date(value: str) -> str | None:
    """
    Try multiple date formats and return ISO 8601 string (YYYY-MM-DD).
    Returns None if parsing fails.
    """
    if pd.isna(value) or value == "":
        return None
    value = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    logger.warning(f"Could not parse date: '{value}'")
    return None


def standardize_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Apply parse_date to all specified columns."""
    df = df.copy()
    for col in columns:
        original_nulls = df[col].isna().sum()
        df[col] = df[col].apply(parse_date)
        new_nulls = df[col].isna().sum()
        failed = new_nulls - original_nulls
        if failed > 0:
            logger.warning(f"Column '{col}': {failed} dates could not be parsed")
    return df


# ─── CURRENCY NORMALIZATION ──────────────────────────────────────────────────

FX_RATES_TO_USD = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.27,
    "CAD": 0.74,
    "AUD": 0.65,
    "JPY": 0.0067,
}


def normalize_currency(df: pd.DataFrame,
                       amount_col: str = "amount",
                       currency_col: str = "currency") -> pd.DataFrame:
    """
    Add 'amount_usd' and 'fx_rate' columns by converting all amounts to USD.
    Unknown currencies are left as-is with fx_rate=1.0 and a warning.
    """
    df = df.copy()

    def to_usd(row):
        ccy = str(row[currency_col]).upper().strip()
        rate = FX_RATES_TO_USD.get(ccy)
        if rate is None:
            logger.warning(f"Unknown currency: '{ccy}' — using 1.0 rate")
            rate = 1.0
        return round(row[amount_col] * rate, 2), rate

    results = df.apply(to_usd, axis=1)
    df["amount_usd"] = [r[0] for r in results]
    df["fx_rate"] = [r[1] for r in results]
    return df


# ─── DEDUPLICATION ──────────────────────────────────────────────────────────

def deduplicate(df: pd.DataFrame,
                key_columns: list[str],
                keep: str = "last") -> pd.DataFrame:
    """
    Remove duplicate rows based on composite key columns.
    Logs how many duplicates were removed.
    """
    before = len(df)
    df = df.drop_duplicates(subset=key_columns, keep=keep)
    removed = before - len(df)
    if removed > 0:
        logger.info(f"Deduplication: removed {removed} rows on keys {key_columns}")
    return df


# ─── MISSING VALUE HANDLING ──────────────────────────────────────────────────

IMPUTATION_RULES = {
    # (column_name): ('strategy', fill_value_or_None)
    # strategy: 'drop', 'fill_constant', 'fill_median', 'fill_mode'
    "customer_id": ("drop", None),
    "transaction_date": ("drop", None),
    "amount": ("fill_median", None),
    "currency": ("fill_constant", "USD"),
    "channel": ("fill_constant", "unknown"),
    "campaign_name": ("fill_constant", "unattributed"),
}


def handle_missing_values(df: pd.DataFrame,
                          rules: dict = None) -> pd.DataFrame:
    """
    Apply imputation rules to handle missing values.
    Default rules can be overridden by passing a custom rules dict.
    """
    rules = rules or IMPUTATION_RULES
    df = df.copy()

    for col, (strategy, fill_val) in rules.items():
        if col not in df.columns:
            continue

        null_count = df[col].isna().sum()
        if null_count == 0:
            continue

        if strategy == "drop":
            df = df.dropna(subset=[col])
            logger.info(f"Dropped {null_count} rows with null '{col}'")

        elif strategy == "fill_constant":
            df[col] = df[col].fillna(fill_val)
            logger.info(f"Filled {null_count} nulls in '{col}' with '{fill_val}'")

        elif strategy == "fill_median":
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info(f"Filled {null_count} nulls in '{col}' with median {median_val:.2f}")

        elif strategy == "fill_mode":
            mode_val = df[col].mode()[0]
            df[col] = df[col].fillna(mode_val)
            logger.info(f"Filled {null_count} nulls in '{col}' with mode '{mode_val}'")

    return df


# ─── TEXT STANDARDIZATION ───────────────────────────────────────────────────

CHANNEL_ALIASES = {
    "email marketing": "email",
    "e-mail": "email",
    "paid social": "paid_social",
    "social media": "paid_social",
    "organic search": "organic",
    "seo": "organic",
    "referral program": "referral",
    "word of mouth": "referral",
    "cold outreach": "outbound",
    "cold email": "outbound",
}


def normalize_channel(value: str) -> str:
    """Standardize channel names to canonical values."""
    if pd.isna(value):
        return "unknown"
    clean = str(value).lower().strip()
    return CHANNEL_ALIASES.get(clean, clean)


def clean_email(value: str) -> str | None:
    """Lowercase and validate email addresses."""
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$"
    return value if re.match(pattern, value) else None


def clean_text_columns(df: pd.DataFrame,
                       lower_cols: list[str] = None,
                       strip_cols: list[str] = None) -> pd.DataFrame:
    """Lowercase and strip whitespace from specified columns."""
    df = df.copy()
    for col in (lower_cols or []):
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()
    for col in (strip_cols or []):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df
