"""
validators.py
-------------
Business rule validation functions for the ETL pipeline.
All records failing validation are quarantined, not silently dropped.

Author: Allen Day
"""

import logging
import pandas as pd
from dataclasses import dataclass, field

logger = logging.getLogger("etl.validators")


@dataclass
class ValidationResult:
    """Container for validation outcome."""
    passed: pd.DataFrame
    failed: pd.DataFrame
    rules_triggered: dict = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        total = len(self.passed) + len(self.failed)
        return round(100 * len(self.passed) / total, 2) if total else 0.0

    def summary(self) -> None:
        total = len(self.passed) + len(self.failed)
        print(f"  Validation: {len(self.passed)}/{total} passed ({self.pass_rate}%)")
        for rule, count in self.rules_triggered.items():
            print(f"    ⚠️  {rule}: {count} violations")


# ─── INDIVIDUAL RULES ────────────────────────────────────────────────────────

def rule_not_null(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    """Fail rows where any required column is null."""
    mask = df[columns].notna().all(axis=1)
    violations = (~mask).sum()
    if violations:
        logger.warning(f"not_null [{columns}]: {violations} rows failed")
    return mask


def rule_positive_amount(df: pd.DataFrame,
                         col: str = "amount_usd") -> pd.Series:
    """Fail rows where amount is zero or negative."""
    mask = df[col] > 0
    violations = (~mask).sum()
    if violations:
        logger.warning(f"positive_amount [{col}]: {violations} rows failed")
    return mask


def rule_date_range(df: pd.DataFrame,
                    col: str = "transaction_date",
                    min_date: str = "2018-01-01",
                    max_date: str = None) -> pd.Series:
    """Fail rows where date is outside the acceptable range."""
    max_date = max_date or pd.Timestamp.today().strftime("%Y-%m-%d")
    dates = pd.to_datetime(df[col], errors="coerce")
    mask = (dates >= min_date) & (dates <= max_date)
    violations = (~mask).sum()
    if violations:
        logger.warning(f"date_range [{col}]: {violations} rows outside {min_date}–{max_date}")
    return mask


def rule_known_status(df: pd.DataFrame,
                      col: str = "status",
                      allowed: set = None) -> pd.Series:
    """Fail rows with unexpected status values."""
    allowed = allowed or {"completed", "refunded", "failed", "pending"}
    mask = df[col].isin(allowed)
    violations = (~mask).sum()
    if violations:
        unknown = df.loc[~mask, col].unique().tolist()
        logger.warning(f"known_status [{col}]: {violations} rows with values {unknown}")
    return mask


def rule_no_duplicate_id(df: pd.DataFrame,
                         id_col: str = "transaction_id") -> pd.Series:
    """Flag duplicate IDs — keep first occurrence, fail duplicates."""
    mask = ~df.duplicated(subset=[id_col], keep="first")
    violations = (~mask).sum()
    if violations:
        logger.warning(f"no_duplicate_id [{id_col}]: {violations} duplicate IDs found")
    return mask


def rule_amount_ceiling(df: pd.DataFrame,
                        col: str = "amount_usd",
                        ceiling: float = 100_000) -> pd.Series:
    """Flag suspiciously large transactions for manual review."""
    mask = df[col] <= ceiling
    violations = (~mask).sum()
    if violations:
        logger.warning(f"amount_ceiling [{col} > ${ceiling:,.0f}]: {violations} rows flagged")
    return mask


# ─── VALIDATION RUNNER ───────────────────────────────────────────────────────

TRANSACTION_RULES = [
    ("not_null",
     lambda df: rule_not_null(df, ["customer_id", "transaction_id", "transaction_date", "amount_usd"])),
    ("positive_amount",
     lambda df: rule_positive_amount(df, "amount_usd")),
    ("date_range",
     lambda df: rule_date_range(df, "transaction_date")),
    ("known_status",
     lambda df: rule_known_status(df, "status")),
    ("no_duplicate_id",
     lambda df: rule_no_duplicate_id(df, "transaction_id")),
    ("amount_ceiling",
     lambda df: rule_amount_ceiling(df, "amount_usd")),
]

CUSTOMER_RULES = [
    ("not_null",
     lambda df: rule_not_null(df, ["customer_id", "email"])),
]

MARKETING_RULES = [
    ("not_null",
     lambda df: rule_not_null(df, ["event_id", "event_date"])),
    ("date_range",
     lambda df: rule_date_range(df, "event_date")),
]


def validate(df: pd.DataFrame,
             rules: list = None,
             label: str = "dataset") -> ValidationResult:
    """
    Run a list of validation rules against a DataFrame.
    Returns a ValidationResult separating passing and failing rows.

    Parameters
    ----------
    df : input DataFrame
    rules : list of (rule_name, callable) tuples; each callable takes a
            DataFrame and returns a boolean Series
    label : dataset name for logging
    """
    rules = rules or TRANSACTION_RULES

    fail_mask = pd.Series(False, index=df.index)
    triggered = {}

    for rule_name, rule_fn in rules:
        passes = rule_fn(df)
        newly_failed = ~passes & ~fail_mask
        count = newly_failed.sum()
        if count > 0:
            triggered[rule_name] = int(count)
        fail_mask = fail_mask | ~passes

    passed_df = df[~fail_mask].reset_index(drop=True)
    failed_df = df[fail_mask].reset_index(drop=True)

    result = ValidationResult(passed=passed_df, failed=failed_df,
                              rules_triggered=triggered)
    print(f"\n── Validation [{label}] ─────────────────────────────")
    result.summary()
    return result
