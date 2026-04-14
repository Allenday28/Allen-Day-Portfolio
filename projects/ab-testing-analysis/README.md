# 🧪 A/B Testing Framework for Marketing Campaign Optimization

> **Applying statistical rigor to measure what actually moves the needle**

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)]()
[![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?style=flat&logo=scipy&logoColor=white)]()
[![Statsmodels](https://img.shields.io/badge/Statsmodels-4B8BBE?style=flat)]()

---

## 📌 Problem Statement

A marketing team was running campaigns based on intuition and gut feel, with no statistical validation of whether changes actually improved results — or just looked good in a small sample.

**Goal:** Build a reusable A/B testing framework to evaluate campaign changes with proper statistical controls, calculate required sample sizes upfront, and deliver clear go/no-go recommendations.

---

## 📊 Test Scenarios Analyzed

| Test | Control | Variant | Metric |
|------|---------|---------|--------|
| Email Subject Line | Generic subject | Personalized subject | Open rate |
| CTA Button Color | Blue button | Orange button | Click-through rate |
| Pricing Page Layout | Current design | Simplified design | Conversion rate |
| Discount Offer | 10% off | Free shipping | Revenue per visitor |

---

## 🛠️ Tools & Technologies

| Tool | Purpose |
|------|---------|
| Python (Pandas, NumPy) | Data preparation |
| SciPy (stats) | Two-proportion z-test, t-test |
| Statsmodels | Power analysis, sample size calculation |
| Matplotlib / Seaborn | Test result visualizations |

---

## 🔍 Statistical Framework

### Pre-Test: Power Analysis
Before running any test, calculated required sample size:
```python
from statsmodels.stats.power import TTestIndPower

analysis = TTestIndPower()
sample_size = analysis.solve_power(
    effect_size=0.2,    # Minimum detectable effect
    alpha=0.05,         # Significance threshold
    power=0.80          # 80% power
)
```

### During Test: Continuous Monitoring
- Checked for novelty effects (first-week inflation)
- Monitored for sample ratio mismatch (traffic split validation)
- Daily tracking of running p-value (without peeking-bias decisions)

### Post-Test: Statistical Significance Testing
Used two-proportion z-test for conversion metrics:
```python
from scipy import stats

z_stat, p_value = stats.proportions_ztest(
    count=[variant_conversions, control_conversions],
    nobs=[variant_n, control_n]
)
```

### Decision Framework
| p-value | Decision |
|---------|---------|
| < 0.01 | Strong evidence — ship it |
| 0.01 – 0.05 | Significant — ship with monitoring |
| 0.05 – 0.10 | Marginal — extend test |
| > 0.10 | No evidence — do not ship |

---

## 📈 Test Results Summary

| Test | Result | Lift | p-value | Decision |
|------|--------|------|---------|---------|
| Email Subject | Significant ✅ | +22.4% open rate | 0.002 | **Ship** |
| CTA Button | Not Significant ❌ | +1.8% CTR | 0.31 | **Do not ship** |
| Pricing Page | Significant ✅ | +14.7% conversions | 0.018 | **Ship** |
| Discount Offer | Significant ✅ | Free shipping +8.2% revenue | 0.041 | **Ship** |

---

## 💼 Business Impact

- Personalized email subjects drove **+22.4% open rate lift** → ~$84K incremental monthly revenue
- Prevented rollout of a "blue vs. orange" button change that would have wasted $12K in dev time
- Pricing page redesign improved conversion by **14.7%** → highest-impact test of the year
- Framework adopted by marketing team — **reduced decision cycles from 3 weeks to 8 days**

---

## 📁 Files

```
ab-testing-analysis/
├── README.md
├── ab_testing_framework.ipynb    # Complete analysis & framework
├── power_analysis.py             # Pre-test sample size calculator
└── test_results/
    ├── email_subject_test.py
    └── pricing_page_test.py
```

---

## 🔗 Related Skills Demonstrated
`A/B Testing` · `Hypothesis Testing` · `Statistical Significance` · `Power Analysis` · `SciPy` · `Marketing Analytics` · `Decision Science`
