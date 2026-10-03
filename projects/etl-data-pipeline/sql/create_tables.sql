-- ============================================================
-- Analytics Data Warehouse — DDL
-- Author: Allen Day
-- Description: Target schema for the ETL pipeline output
-- ============================================================

-- ── Customers (unified) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id     TEXT        PRIMARY KEY,
    email           TEXT        UNIQUE,
    full_name       TEXT,
    region          TEXT,
    signup_date     DATE,
    source_system   TEXT,   -- 'crm' | 'billing' | 'marketing'
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ── Transactions (from billing API) ──────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id  TEXT        PRIMARY KEY,
    customer_id     TEXT        REFERENCES dim_customers(customer_id),
    amount_usd      NUMERIC(12,2)   NOT NULL,
    currency_orig   TEXT,
    fx_rate         NUMERIC(10,6),
    transaction_date DATE        NOT NULL,
    product_sku     TEXT,
    payment_method  TEXT,
    status          TEXT,           -- 'completed' | 'refunded' | 'failed'
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ── Marketing events (from marketing platform) ───────────────
CREATE TABLE IF NOT EXISTS fact_marketing_events (
    event_id        TEXT        PRIMARY KEY,
    customer_id     TEXT        REFERENCES dim_customers(customer_id),
    campaign_id     TEXT,
    campaign_name   TEXT,
    channel         TEXT,           -- 'email' | 'paid_social' | 'organic'
    event_type      TEXT,           -- 'open' | 'click' | 'convert'
    event_date      DATE        NOT NULL,
    revenue_attr    NUMERIC(12,2),
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ── Pipeline run log ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS etl_run_log (
    run_id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    run_timestamp   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    source          TEXT,       -- 'crm_csv' | 'billing_api' | 'marketing_csv'
    rows_extracted  INTEGER,
    rows_loaded     INTEGER,
    rows_rejected   INTEGER,
    status          TEXT,       -- 'success' | 'partial' | 'rejected'
    error_message   TEXT
);

-- ── Materialized summary view ─────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_customer_revenue_summary AS
SELECT
    c.customer_id,
    c.email,
    c.region,
    c.source_system,
    COUNT(DISTINCT t.transaction_id)                AS total_transactions,
    SUM(t.amount_usd)                               AS lifetime_value,
    MAX(t.transaction_date)                         AS last_purchase_date,
    julianday('now') - julianday(MAX(t.transaction_date)) AS days_since_purchase,
    AVG(t.amount_usd)                               AS avg_order_value
FROM dim_customers c
LEFT JOIN fact_transactions t
       ON c.customer_id = t.customer_id
      AND t.status = 'completed'
GROUP BY c.customer_id, c.email, c.region, c.source_system;
