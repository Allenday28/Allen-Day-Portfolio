"""
email_subject_test.py
---------------------
A/B Test: Generic vs. Personalized Email Subject Line
Metric: Open rate
Result: SIGNIFICANT — Ship personalized subject

Author: Allen Day
"""

import numpy as np
from scipy import stats
from scipy.stats import norm
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ─── TEST PARAMETERS ────────────────────────────────────────────────────────

TEST_NAME = "Email Subject Line Personalization"
CONTROL_LABEL = "Control: Generic subject line"
VARIANT_LABEL = "Variant: Personalized '[First Name], your pick of the week'"

# Pre-test power analysis
BASELINE_OPEN_RATE = 0.22    # 22% historical open rate
MDE = 0.15                   # 15% relative lift = 3.3pp
ALPHA = 0.05
POWER = 0.80
N_REQUIRED = 3_842           # computed via power_analysis.py

# Actual test results
CONTROL_SENT = 21_450
CONTROL_OPENS = 4_671        # 21.8% open rate

VARIANT_SENT = 21_537
VARIANT_OPENS = 5_727        # 26.6% open rate


# ─── ANALYSIS ───────────────────────────────────────────────────────────────

def run_test() -> dict:
    """Run two-proportion z-test and return full results dict."""
    ctrl_rate = CONTROL_OPENS / CONTROL_SENT
    var_rate = VARIANT_OPENS / VARIANT_SENT
    relative_lift = (var_rate - ctrl_rate) / ctrl_rate

    z_stat, p_value = stats.proportions_ztest(
        count=[VARIANT_OPENS, CONTROL_OPENS],
        nobs=[VARIANT_SENT, CONTROL_SENT],
    )

    # 95% confidence interval on the difference
    pooled_se = np.sqrt(
        ctrl_rate * (1 - ctrl_rate) / CONTROL_SENT +
        var_rate * (1 - var_rate) / VARIANT_SENT
    )
    diff = var_rate - ctrl_rate
    z_critical = norm.ppf(1 - ALPHA / 2)
    ci_low = diff - z_critical * pooled_se
    ci_high = diff + z_critical * pooled_se

    # Decision
    significant = p_value < ALPHA
    decision = "✅ SHIP IT" if significant else "❌ DO NOT SHIP"

    results = {
        "test_name": TEST_NAME,
        "control_rate": ctrl_rate,
        "variant_rate": var_rate,
        "absolute_lift_pp": diff,
        "relative_lift_pct": relative_lift * 100,
        "z_statistic": z_stat,
        "p_value": p_value,
        "ci_95": (ci_low, ci_high),
        "significant": significant,
        "decision": decision,
        "sample_ratio_ok": abs(VARIANT_SENT / CONTROL_SENT - 1) < 0.01,
    }
    return results


def print_results(r: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  {r['test_name']}")
    print(f"{'='*60}")
    print(f"  Control open rate  : {r['control_rate']:.2%}  (n={CONTROL_SENT:,})")
    print(f"  Variant open rate  : {r['variant_rate']:.2%}  (n={VARIANT_SENT:,})")
    print(f"  Absolute lift      : {r['absolute_lift_pp']:+.2%}")
    print(f"  Relative lift      : {r['relative_lift_pct']:+.1f}%")
    print(f"  Z-statistic        : {r['z_statistic']:.3f}")
    print(f"  p-value            : {r['p_value']:.4f}")
    print(f"  95% CI (diff)      : [{r['ci_95'][0]:.3%}, {r['ci_95'][1]:.3%}]")
    print(f"  Sample ratio check : {'✅ Pass' if r['sample_ratio_ok'] else '⚠️ Fail'}")
    print(f"\n  Decision: {r['decision']}")
    print(f"{'='*60}\n")


def plot_results(r: dict) -> None:
    """Bar chart comparing open rates with error bars."""
    rates = [r["control_rate"], r["variant_rate"]]
    labels = ["Control\n(Generic)", "Variant\n(Personalized)"]
    colors = ["#95a5a6", "#2ecc71"]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, [v * 100 for v in rates], color=colors,
                  width=0.4, edgecolor="white", linewidth=2)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{rate:.1%}", ha="center", va="bottom",
                fontsize=14, fontweight="bold")

    lift_pct = r["relative_lift_pct"]
    ax.annotate(f"+{lift_pct:.1f}% lift\np={r['p_value']:.4f}",
                xy=(1, r["variant_rate"] * 100),
                xytext=(1.3, r["variant_rate"] * 100 + 1.5),
                fontsize=12, color="#27ae60", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#27ae60"))

    ax.set_ylim(0, max(rates) * 100 * 1.3)
    ax.set_ylabel("Open Rate (%)")
    ax.set_title(f"Email Subject Test — Open Rate\n{r['decision']}", fontsize=13)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_test()
    print_results(results)
    plot_results(results)
