# 📈 Revenue Forecasting with Time Series Analysis

> **Predicting next-quarter revenue using Prophet and ARIMA models**

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)]()
[![Prophet](https://img.shields.io/badge/Prophet-0066CC?style=flat)]()
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)]()

---

## 📌 Problem Statement

Finance and operations teams struggled with manual, spreadsheet-based revenue projections that were often inaccurate and couldn't account for seasonality or growth trends.

**Goal:** Build an automated revenue forecasting model that predicts the next 90 days of revenue with confidence intervals, enabling better resource planning and goal-setting.

---

## 📊 Dataset

- **Source:** Anonymized monthly and weekly revenue records (36 months)
- **Frequency:** Weekly aggregates · 156 data points
- **Key Features:** Revenue, promotional periods, seasonal patterns, trend breaks

---

## 🛠️ Tools & Technologies

| Tool | Purpose |
|------|---------|
| Python (Pandas, NumPy) | Data preparation |
| Facebook Prophet | Primary forecasting model |
| Statsmodels (ARIMA) | Benchmark comparison model |
| Plotly | Interactive forecast visualizations |
| Scikit-learn | Error metrics (RMSE, MAPE) |

---

## 🔍 Process

### 1. Time Series Decomposition
- Separated trend, seasonality, and residual components
- Identified yearly and weekly seasonal patterns
- Flagged anomaly weeks (promotions, external events)

### 2. Model Selection
Evaluated three approaches:
- **ARIMA(2,1,2)** — Classical statistical model
- **Facebook Prophet** — Handles seasonality + holidays natively
- **Linear Trend Baseline** — For comparison

### 3. Cross-Validation
Used Prophet's built-in `cross_validation()` with rolling 12-week windows to assess out-of-sample accuracy.

### 4. Forecast & Confidence Intervals
Generated 90-day forecast with 80% and 95% prediction intervals.

---

## 📈 Model Performance

| Model | MAPE | RMSE | MAE |
|-------|------|------|-----|
| Linear Baseline | 18.4% | $42,300 | $31,100 |
| ARIMA(2,1,2) | 11.2% | $28,700 | $21,500 |
| **Prophet (Selected)** | **7.8%** | **$19,400** | **$15,200** |

**Prophet outperformed ARIMA by 30% on MAPE** — primarily due to better handling of weekly seasonality.

---

## 📊 Forecast Insights

- **Q1 Projection:** $2.84M (±$180K at 80% confidence)
- **Peak Revenue Period:** October–November (holiday lift of +34%)
- **Growth Trend:** +12.3% YoY compound
- **Identified Risk:** February historically underperforms by 18% — enable proactive pipeline building

---

## 💼 Business Impact

- Finance team reduced forecast prep time from **3 days to 2 hours**
- Model accuracy of **7.8% MAPE** vs. previous manual method of 22% MAPE
- Enabled operations to **pre-allocate staffing** 6 weeks in advance based on revenue signals
- Q3 forecast was within **4.2% of actual results** — highest accuracy ever achieved

---

## 📁 Files

```
revenue-forecasting/
├── README.md
├── revenue_forecast.ipynb    # Full forecasting notebook
└── forecast_utils.py         # Helper functions for model evaluation
```

---

## 🔗 Related Skills Demonstrated
`Time Series Analysis` · `Prophet` · `ARIMA` · `Cross-Validation` · `Forecasting` · `Plotly Visualization` · `Business Planning`
