"""
test_pipeline.py
----------------
Unit tests for the ETL pipeline's cleaning and validation logic.

Run with:  pytest tests/test_pipeline.py -v

Author: Allen Day
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Allow imports from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.cleaners import (
    parse_date, standardize_dates, normalize_currency,
    deduplicate, normalize_channel, clean_email,
)
from transform.validators import (
    rule_not_null, rule_positive_amount, rule_date_range,
    rule_known_status, rule_no_duplicate_id, validate,
    TRANSACTION_RULES,
)


# ─── FIXTURES ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        "transaction_id": ["T001", "T002", "T003", "T004"],
        "customer_id":    ["C001", "C002", "C003", "C004"],
        "amount_usd":     [100.0, 250.0, -50.0, 0.0],
        "currency":       ["USD", "USD", "USD", "USD"],
        "transaction_date": ["2023-06-01", "2023-07-15", "2023-08-01", "2023-09-01"],
        "status":         ["completed", "completed", "completed", "completed"],
    })


@pytest.fixture
def sample_customers():
    return pd.DataFrame({
        "customer_id": ["C001", "C002", "C003"],
        "email":       ["alice@example.com", "bob@example.com", None],
        "full_name":   ["Alice A", "Bob B", "Carol C"],
        "region":      ["West", "East", "Central"],
        "signup_date": ["2022-01-01", "2022-03-15", "2022-06-30"],
        "source_system": ["crm", "crm", "crm"],
    })


# ─── DATE PARSING ────────────────────────────────────────────────────────────

class TestParseDateFormats:
    def test_iso_format(self):
        assert parse_date("2023-06-15") == "2023-06-15"

    def test_us_slash_format(self):
        assert parse_date("06/15/2023") == "2023-06-15"

    def test_dmy_format(self):
        assert parse_date("15-06-2023") == "2023-06-15"

    def test_long_month_format(self):
        assert parse_date("June 15, 2023") == "2023-06-15"

    def test_compact_numeric(self):
        assert parse_date("20230615") == "2023-06-15"

    def test_invalid_returns_none(self):
        assert parse_date("not a date") is None

    def test_null_returns_none(self):
        assert parse_date(None) is None
        assert parse_date("") is None

    def test_standardize_column(self, sample_customers):
        df = standardize_dates(sample_customers, ["signup_date"])
        assert df["signup_date"].iloc[0] == "2022-01-01"


# ─── CURRENCY NORMALIZATION ──────────────────────────────────────────────────

class TestCurrencyNormalization:
    def test_usd_unchanged(self):
        df = pd.DataFrame({"amount": [100.0], "currency": ["USD"]})
        result = normalize_currency(df)
        assert result["amount_usd"].iloc[0] == 100.0
        assert result["fx_rate"].iloc[0] == 1.0

    def test_eur_converted(self):
        df = pd.DataFrame({"amount": [100.0], "currency": ["EUR"]})
        result = normalize_currency(df)
        assert result["amount_usd"].iloc[0] == pytest.approx(109.0, rel=0.01)

    def test_unknown_currency_uses_1(self):
        df = pd.DataFrame({"amount": [50.0], "currency": ["XYZ"]})
        result = normalize_currency(df)
        assert result["fx_rate"].iloc[0] == 1.0

    def test_case_insensitive(self):
        df = pd.DataFrame({"amount": [100.0], "currency": ["usd"]})
        result = normalize_currency(df)
        assert result["amount_usd"].iloc[0] == 100.0


# ─── DEDUPLICATION ──────────────────────────────────────────────────────────

class TestDeduplication:
    def test_removes_exact_duplicates(self):
        df = pd.DataFrame({
            "id": ["A", "A", "B"],
            "value": [1, 2, 3],
        })
        result = deduplicate(df, key_columns=["id"], keep="last")
        assert len(result) == 2

    def test_no_duplicates_unchanged(self):
        df = pd.DataFrame({"id": ["A", "B", "C"], "val": [1, 2, 3]})
        result = deduplicate(df, key_columns=["id"])
        assert len(result) == 3


# ─── CHANNEL NORMALIZATION ───────────────────────────────────────────────────

class TestChannelNormalization:
    def test_alias_mapping(self):
        assert normalize_channel("email marketing") == "email"
        assert normalize_channel("paid social") == "paid_social"
        assert normalize_channel("organic search") == "organic"

    def test_passthrough_unknown(self):
        assert normalize_channel("podcast") == "podcast"

    def test_null_returns_unknown(self):
        assert normalize_channel(None) == "unknown"


# ─── EMAIL CLEANING ──────────────────────────────────────────────────────────

class TestEmailCleaning:
    def test_valid_email_lowercased(self):
        assert clean_email("Alice@Example.COM") == "alice@example.com"

    def test_invalid_email_returns_none(self):
        assert clean_email("not-an-email") is None
        assert clean_email("missing@domain") is None

    def test_null_returns_none(self):
        assert clean_email(None) is None


# ─── VALIDATION RULES ────────────────────────────────────────────────────────

class TestValidationRules:
    def test_not_null_passes_complete_rows(self, sample_transactions):
        mask = rule_not_null(sample_transactions, ["transaction_id", "customer_id"])
        assert mask.all()

    def test_not_null_fails_missing(self):
        df = pd.DataFrame({"a": ["x", None, "z"], "b": [1, 2, 3]})
        mask = rule_not_null(df, ["a"])
        assert mask.sum() == 2

    def test_positive_amount_fails_zero_and_negative(self, sample_transactions):
        mask = rule_positive_amount(sample_transactions, "amount_usd")
        # T003 (-50) and T004 (0) should fail
        assert mask.sum() == 2

    def test_known_status_fails_unexpected(self):
        df = pd.DataFrame({"status": ["completed", "pending", "mystery"]})
        mask = rule_known_status(df)
        # 'mystery' not in allowed set
        assert mask.sum() == 2

    def test_no_duplicate_id_flags_second(self):
        df = pd.DataFrame({"transaction_id": ["T001", "T001", "T002"]})
        mask = rule_no_duplicate_id(df, "transaction_id")
        assert mask.sum() == 2  # first T001 and T002 pass

    def test_date_range_rejects_future(self):
        df = pd.DataFrame({
            "transaction_date": ["2020-01-01", "2099-12-31", "2023-06-01"]
        })
        mask = rule_date_range(df, "transaction_date")
        assert mask.sum() == 2  # 2099 should fail


# ─── END-TO-END VALIDATION ───────────────────────────────────────────────────

class TestValidationPipeline:
    def test_all_good_data_passes(self, sample_transactions):
        # Only T001 and T002 have positive amounts
        good_df = sample_transactions[sample_transactions["amount_usd"] > 0].copy()
        result = validate(good_df, TRANSACTION_RULES, label="test")
        assert len(result.failed) == 0
        assert result.pass_rate == 100.0

    def test_bad_data_quarantined(self, sample_transactions):
        result = validate(sample_transactions, TRANSACTION_RULES, label="test")
        # T003 and T004 have non-positive amounts → should fail
        assert len(result.failed) >= 2
        assert len(result.passed) + len(result.failed) == len(sample_transactions)
