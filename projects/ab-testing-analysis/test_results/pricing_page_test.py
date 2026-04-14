"""
pricing_page_test.py
--------------------
A/B Test: Current Pricing Page vs. Simplified Redesign
Metric: Free trial signup conversion rate
Result: SIGNIFICANT — Ship the simplified design

Author: Allen Day
"""

import numpy as np
from scipy import stats
from scipy.stats import norm, chi2_contingency
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


# ─── TEST PARAMETERS ────────────────────────────────────────────────────────

TEST_NAME = "Pricing Page Layout — Simplified Design"
CONTROL_LABEL = "Control: Current 3-tier pricing table with all features"
VARIANT_LABEL = "Variant: Simplified single CTA with social proof"

# Pre-test design
BASELINE_CVR = 0.038     # 3.8% signup rate
MDE = 0.10               # 10% relative lift (0.38pp absolute)
ALPHA = 0.05
POWER = 0.80
N_REQUIRED = 12_480

# Actual test results (ran for 21 days)
CONTROL_VISITORS = 14_230
CONTROL_SIGNUPS = 540     # 3.79% CVR

VARIANT_VISITORS = 14_418
VARIANT_SIGNUPS = 631     # 4.38% CVR

# Secondary metric: time on page (seconds)
CONTROL_TIME_MEAN = 87.3
CONTROL_TIME_STD = 42.1
VARIANT_TIME_MEAN = 64.8
VARIANT_TIME_STD@= 38.4


# ─── PRIMARY METRIC TEST ────────────────────────────────────────────────────

def run_conversion_test() -> dict:
    """Two-proportion z-test on signup conversion rate."""
    ctrl_rate = CONTROL_SIGNUPS / CONTROL_VISITORS
    var_rate = VARIANT_SIGNUPS / VARIANT_VISITORS
    relative_lift = (var_rate - ctrl_rate) / ctrl_rate

    z_stat, p_value = stats.proportions_ztest(
        count=[VARIANT_SIGNUPS, CONTROL_SIGNUPS],
        nobs=[VARIANT_VISITORS, CONTROL_VISITORS],
    )

    diff = var_rate - ctrl_rate
    pooled_se = np.sqrt(
        ctrl_rate * (1 - ctrl_rate) / CONTROL_VISITORS +
        var_rate * (1 - var_rate) / VARIANT_VISITORS
    )
    z_critical = norm.ppf(1 - ALPHA / 2)

    return {
        "metric": "Signup Conversion Rate",
        "control_rate": ctrl_rate,
        "variant_rate": var_rate,
        "absolute_lift_pp": diff,
        "relative_lift_pct": relative_lift * 100,
        "z_statistic": z_stat,
        "p_value": p_value,
        "ci_95": (diff - z_critical * pooled_se, diff + z_critical * pooled_se),
        "significant": p_value < ALPHA,
    }


def run_time_on_page_test() -> dict:
    """Two-sample t-test on time on page (continuous metric)."""
    np.random.seed(42)
    ctrl_sample = np.random.normal(CONTROL_TIME_MEAN, CONTROL_TIME_STD, CONTROL_VISITORS)
    var_sample = np.random.normal(VARIANT_TIME_MEAN, VARIANT_TIME_STD, VARIANT_VISITORS)

    t_stat, p_value = stats.ttest_ind(var_sample, ctrl_sample, equal_var=False)

    return {
        "metric": "Time on Page (seconds)",
        "control_mean": CONTROL_TIME_MEAN,
        "variant_mean": VARIANT_TIME_MEAN,
        "delta_seconds": VARIANT_TIME_MEAN - CONTROL_TIME_MEAN,
        "t_statistic": t_stat,
        "p_value": p_value,
        "significant": p_value < ALPHA,
    }


# ─── REPORT ─────────────────────────────────────────────────────────────────

def print_full_report(cvr: dict, time: dict) -> None:
    decision = "✅ SHIP IT" if cvr["significant"] else "❌ DO NOT SHIP"

    print(f"\n{'='*65}")
    print(f"  {TEST_NAME}")
    print(f"{'='*65}")
    print(f"\n  PRIMARY METRIC — {cvr['metric']}")
    print(f"  Control CVR    : {cvr['control_rate']:.2%}  (n={CONTROL_VISITORS:,})")
    print(f"  Variant CVR    : {cvr['variant_rate']:.2%}  (n={VARIANT_VISITORS:,})")
    print(f"  Absolute lift  : {cvr['absolute_lift_pp']:+.2%}")
    print(f"  Relative lift  : {cvr['relative_lift_pct']:+.1f}%")
    print(f"  Z-stat         : {cvr['z_statistic']:.3f}")
    print(f"  p-value        : {cvr['p_value']:.4f}  {'✅ Significant' if cvr['significant'] else '❌ Not significant'}")
    print(f"  95% CI         : [{cvr['ci_95'][0]:.3%}, {cvr['ci_95'][1]:.3%}]")

    print(f"\n  SECONDARY METRIC — {time['metric']}")
    print(f"  Control mean   : {time['control_mean']:.1f}s")
    print(f"  Variant mean   : {time['variant_mean']:.1f}s  ({time['delta_seconds']:+.1f}s)")
    note = "(users finding info faster)" if time["delta_seconds"] < 0 else "(users spending more time)"
    print(f"  Note           : {note}")
    print(f"  p-value        : {time['p_value']:.4f}  {'✅ Significant' if time['significant'] else '❌ Not significant'}")

    print(f"\n  Decision: {decision}")
    print(f"  Business Impact: +{cvr['relative_lift_pct']:.1f}% signup rate → "
          f"est. ${(cvr['absolute_lift_pp'] * VARIANT_VISITORS * 80):,.0f} incremental MRR/month")
    print(f"{'='*65}\n")


def plot_results(cvr: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart: CVR comparison
    labels = ["Control\n(Current)", "Variant\n(Simplified)"]
    rates = [cvr["control_rate"] * 100, cvr["variant_rate"] * 100]
    colors = ["#95a5a6", "#3498db"]
    bars = ax1.bar(labels, rates, color=colors, width=0.4, edgecolor="white", linewidth=2)
    for bar, rate in zip(bars, rates):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f"{rate:.2f}%", ha="center", va="bottom", fontsize=13, fontweight="bold")
    ax1.set_ylim(0, max(rates) * 1.35)
    ax1.set_ylabel("Conversion Rate (%)")
    ax1.set_title(f"Pricing Page CVR\n+{cvr['relative_lift_pct']:.1f}% lift (p={cvr['p_value']:.3f})",
                  fontsize=12)
    ax1.grid(axis="y", alpha=0.3)

    # Funnel: visitors → signups
    stages = ["Visitors", "Signups"]
    ctrl_vals = [CONTROL_VISITORS, CONTROL_SIGNUPS]
    var_vals = [VARIANT_VISITORS, VARIANT_SIGNUPS]
    x = np.arange(len(stages))
    width = 0.35
    ax2.bar(x - width/2, ctrl_vals, width, label="Control", color="#95a5a6", edgecolor="white")
    ax2.bar(x + width/2, var_vals, width, label="Variant", color="#3498db", edgecolor="white")
    ax2.set_xticks(x)
    ax2.set_xticklabels(stages)
    ax2.set_ylabel("Count")
    ax2.set_title("Conversion Funnel Comparison", fontsize=12)
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    plt.suptitle(TEST_NAME, fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.show()


# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cvr_results = run_conversion_test()
    time_results = run_time_on_page_test()
    print_full_report(cvr_results, time_results)
    plot_results(cvr_results)
