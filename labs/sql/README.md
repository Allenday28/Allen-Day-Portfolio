# 📊 SQL Labs — Core Analytics Patterns

> Clean, practical SQL examples covering real-world analytics use cases.
> Each query is production-quality and annotated for clarity.

---

## Lab Index

| # | Topic | Concepts |
|---|-------|---------|
| 01 | [Window Functions](#01-window-functions) | ROW_NUMBER, RANK, LAG, LEAD, running totals |
| 02 | [CTEs & Subqueries](#02-ctes--subqueries) | WITH clauses, nested logic, readability |
| 03 | [Aggregations & GROUPING](#03-aggregations) | GROUP BY, HAVING, ROLLUP, CUBE |
| 04 | [Customer Cohort Analysis](#04-cohort-analysis) | DATE_TRUNC, DATEDIFF, retention logic |
| 05 | [Funnel Analysis](#05-funnel-analysis) | Conditional aggregation, conversion rates |

---

## 01. Window Functions

```sql
-- ============================================================
-- Running revenue total + month-over-month growth
-- ============================================================
SELECT
    transaction_month,
    monthly_revenue,
    SUM(monthly_revenue)
        OVER (ORDER BY transaction_month)                       AS cumulative_revenue,
    LAG(monthly_revenue, 1)
        OVER (ORDER BY transaction_month)                       AS prior_month_revenue,
    ROUND(
        100.0 * (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY transaction_month))
        / NULLIF(LAG(monthly_revenue, 1) OVER (ORDER BY transaction_month), 0),
        1
    )                                                           AS mom_growth_pct,
    -- Rank months by revenue (1 = highest)
    RANK() OVER (ORDER BY monthly_revenue DESC)                 AS revenue_rank
FROM (
    SELECT
        DATE_TRUNC('month', transaction_date)   AS transaction_month,
        SUM(amount)                             AS monthly_revenue
    FROM transactions
    WHERE status = 'completed'
    GROUP BY 1
) monthly
ORDER BY transaction_month;
```

---

## 02. CTEs & Subqueries

```sql
-- ============================================================
-- Identify customers who upgraded plans (used CTE chain)
-- ============================================================
WITH first_plan AS (
    SELECT
        customer_id,
        plan_name                                     AS initial_plan,
        MIN(start_date)                               AS first_start
    FROM subscriptions
    GROUP BY customer_id, plan_name
    QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY MIN(start_date)) = 1
),
latest_plan AS (
    SELECT
        customer_id,
        plan_name                                     AS current_plan,
        MAX(start_date)                               AS latest_start
    FROM subscriptions
    GROUP BY customer_id, plan_name
    QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY MAX(start_date) DESC) = 1
),
plan_changes AS (
    SELECT
        f.customer_id,
        f.initial_plan,
        l.current_plan,
        f.first_start,
        l.latest_start,
        DATEDIFF('day', f.first_start, l.latest_start)  AS days_to_upgrade
    FROM first_plan f
    JOIN latest_plan l USING (customer_id)
    WHERE f.initial_plan != l.current_plan
)
SELECT
    initial_plan,
    current_plan,
    COUNT(*)                                    AS upgrade_count,
    ROUND(AVG(days_to_upgrade), 0)              AS avg_days_to_upgrade
FROM plan_changes
GROUP BY 1, 2
ORDER BY upgrade_count DESC;
```

---

## 03. Aggregations

```sql
-- ============================================================
-- Revenue summary with ROLLUP (subtotals + grand total)
-- ============================================================
SELECT
    COALESCE(region, 'ALL REGIONS')      AS region,
    COALESCE(channel, 'ALL CHANNELS')    AS channel,
    COUNT(DISTINCT customer_id)          AS unique_customers,
    COUNT(deal_id)                       AS deals_closed,
    SUM(revenue)                         AS total_revenue,
    ROUND(AVG(revenue), 0)               AS avg_deal_size,
    -- Percentage of grand total (using window function)
    ROUND(
        100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (),
        1
    )                                    AS pct_of_total
FROM sales_deals
WHERE stage = 'Closed Won'
  AND EXTRACT(YEAR FROM close_date) = 2024
GROUP BY ROLLUP(region, channel)
HAVING SUM(revenue) > 10000
ORDER BY
    GROUPING(region),
    GROUPING(channel),
    total_revenue DESC;
```

---

## 04. Cohort Analysis

```sql
-- ============================================================
-- Monthly cohort retention analysis
-- Shows % of customers retained N months after first purchase
-- ============================================================
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(order_date))    AS cohort_month
    FROM orders
    GROUP BY customer_id
),
customer_activity AS (
    SELECT
        o.customer_id,
        c.cohort_month,
        DATE_TRUNC('month', o.order_date)       AS activity_month,
        DATEDIFF(
            'month',
            c.cohort_month,
            DATE_TRUNC('month', o.order_date)
        )                                       AS months_since_cohort
    FROM orders o
    JOIN cohorts c USING (customer_id)
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    cs.cohort_size,
    ca.months_since_cohort,
    COUNT(DISTINCT ca.customer_id)              AS retained_customers,
    ROUND(
        100.0 * COUNT(DISTINCT ca.customer_id) / cs.cohort_size,
        1
    )                                           AS retention_rate_pct
FROM customer_activity ca
JOIN cohort_sizes cs USING (cohort_month)
GROUP BY ca.cohort_month, cs.cohort_size, ca.months_since_cohort
ORDER BY ca.cohort_month, ca.months_since_cohort;
```

---

## 05. Funnel Analysis

```sql
-- ============================================================
-- Marketing funnel: impression → click → signup → purchase
-- ============================================================
SELECT
    campaign_id,
    campaign_name,
    -- Step counts
    COUNT(DISTINCT CASE WHEN event_type = 'impression' THEN user_id END)  AS impressions,
    COUNT(DISTINCT CASE WHEN event_type = 'click'      THEN user_id END)  AS clicks,
    COUNT(DISTINCT CASE WHEN event_type = 'signup'     THEN user_id END)  AS signups,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase'   THEN user_id END)  AS purchases,
    -- Conversion rates
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'click' THEN user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'impression' THEN user_id END), 0),
        2
    )                                                                       AS ctr_pct,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'signup' THEN user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'click' THEN user_id END), 0),
        2
    )                                                                       AS click_to_signup_pct,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'impression' THEN user_id END), 0),
        2
    )                                                                       AS overall_conversion_pct
FROM marketing_events
JOIN campaigns USING (campaign_id)
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY campaign_id, campaign_name
ORDER BY overall_conversion_pct DESC;
```
