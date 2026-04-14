"""
power_analysis.py
-----------------
Pre-test sample size and power calculations for A/B experiments.

Usage:
    python power_analysis.py --baseline 0.05 --mde 0.20 --alpha 0.05 --power 0.80

Author: Allen Day
"""

import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.power import TTestIndPower, NormalIndPower


# ─── SAMPLE SIZE CALCULATORS ────────────────────────────────────────────────

def sample_size_proportions(baseline_rate: float,
                            min_detectable_effect: float,
                            alpha: float = 0.05,
                            power: float = 0.80) -> dict:
    """
    Calculate required sample size per variant for a two-proportion z-test.

    Parameters
    ----------
    baseline_rate : current conversion/success rate (0–1)
    min_detectable_effect : relative lift you want to detect (e.g., 0.10 = 10%)
    alpha : significance level (Type I error rate)
    power : desired statistical power (1 - Type II error rate)

    Returns
    -------
    dict with n_per_variant, total_n, variant_rate, effect_size
    """
    variant_rate = baseline_rate * (1 + min_detectable_effect)

    # Cohen's h effect size for proportions
    h = 2 * (math.asin(math.sqrt(variant_rate)) - math.asin(math.sqrt(baseline_rate)))
    effect_size = abs(h)

    analysis = NormalIndPower()
    n = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        alternative="two-sided",
    )
    n = math.ceil(n)

    return {
        "baseline_rate": baseline_rate,
        "variant_rate": round(variant_rate, 4),
        "min_detectable_effect_pct": round(min_detectable_effect * 100, 1),
        "effect_size_h": round(effect_size, 4),
        "alpha": alpha,
        "power": power,
        "n_per_variant": n,
        "total_n": n * 2,
    }


def sample_size_means(baseline_mean: float,
                      baseline_std: float,
                      min_detectable_delta: float,
                      alpha: float = 0.05,
                      power: float = 0.80) -> dict:
    """
    Calculate required sample size for a two-sample t-test (continuous metric).

    Parameters
    ----------
    baseline_mean : current mean value
    baseline_std : standard deviation of the metric
    min_detectable_delta : absolute change you want to detect
    """
    effect_size = min_detectable_delta / baseline_std

    analysis = TTestIndPower()
    n = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        alternative="two-sided",
    )
    n = math.ceil(n)

    return {
        "baseline_mean": baseline_mean,
        "baseline_std": baseline_std,
        "min_detectable_delta": min_detectable_delta,
        "effect_size_d": round(effect_size, 4),
        "alpha": alpha,
        "power": power,
        "n_per_variant": n,
        "total_n": n * 2,
    }


# ─── RUNTIME CALCULATOR ─────────────────────────────────────────────────────

def estimate_runtime(n_per_variant: int,
                     daily_traffic: int,
                     traffic_split: float = 0.5) -> dict:
    """
    Estimate how many days the test needs to run.

    Parameters
    ----------
    n_per_variant : required sample size per arm
    daily_traffic : total daily visitors/sessions exposed to the test
    traffic_split : fraction of traffic sent to each variant (default 50/50)
    """
    daily_per_variant = daily_traffic * traffic_split
    days_needed = math.ceil(n_per_variant / daily_per_variant)

    return {
        "n_per_variant": n_per_variant,
        "daily_traffic": daily_traffic,
        "traffic_split_pct": round(traffic_split * 100),
        "days_needed": days_needed,
        "weeks_needed": round(days_needed / 7, 1),
    }


# ─── SENSITIVITY ANALYSIS ───────────────────────────────────────────────────

def sensitivity_table(baseline_rate: float,
                      mde_range: list[float] = None,
                      alpha: float = 0.05,
                      power: float = 0.80) -> None:
    """
    Print a table of required sample sizes for different MDE values.
    """
    mde_range = mde_range or [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

    print(f"\n── Sample Size Sensitivity (baseline={baseline_rate:.1%}, "
          f"α={alpha}, power={power}) ─────────────────")
    print(f"{'MDE':>8}  {'Variant Rate':>14}  {'n/variant':>10}  {'Total n':>10}  {'Est. Days (1K/day)':>20}")
    print("-" * 70)

    for mde in mde_range:
        result = sample_size_proportions(baseline_rate, mde, alpha, power)
        runtime = estimate_runtime(result["n_per_variant"], daily_traffic=1000)
        print(f"  {mde:>6.0%}  {result['variant_rate']:>14.2%}  "
              f"{result['n_per_variant']:>10,}  {result['total_n']:>10,}  "
              f"{runtime['days_needed']:>20,}")


def plot_sample_size_curve(baseline_rate: float,
                           mde_range: list[float] = None,
                           alpha: float = 0.05,
                           power: float = 0.80) -> None:
    """Plot required n per variant vs. MDE."""
    mde_range = mde_range or np.linspace(0.03, 0.60, 50)

    ns = [
        sample_size_proportions(baseline_rate, mde, alpha, power)["n_per_variant"]
        for mde in mde_range
    ]

    plt.figure(figsize=(10, 5))
    plt.plot([m * 100 for m in mde_range], ns, color="#3498db", linewidth=2.5)
    plt.fill_between([m * 100 for m in mde_range], ns, alpha=0.1, color="#3498db")
    plt.axvline(10, color="#e74c3c", linestyle="--", alpha=0.7, label="MDE = 10%")
    plt.axvline(20, color="#2ecc71", linestyle="--", alpha=0.7, label="MDE = 20%")
    plt.title(f"Required Sample Size vs. Min Detectable Effect\n"
              f"(baseline={baseline_rate:.0%}, α={alpha}, power={power:.0%})",
              fontsize=13, fontweight="bold")
    plt.xlabel("Min Detectable Effect (%)")
    plt.ylabel("Sample Size per Variant")
    plt.yscale("log")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


# ─── PRETTY PRINT ────────────────────────────────────────────────────────────

def print_result(result: dict, label: str = "Power Analysis") -> None:
    print(f"\n── {label} ─────────────────────────────────────────")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"  {k:<32}: {v:.4f}")
        else:
            print(f"  {k:<32}: {v:,}" if isinstance(v, int) else f"  {k:<32}: {v}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A/B Test sample size calculator")
    parser.add_argument("--baseline", type=float, default=0.05, help="Baseline conversion rate")
    parser.add_argument("--mde", type=float, default=0.20, help="Min detectable effect (relative)")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--power", type=float, default=0.80, help="Desired power")
    parser.add_argument("--daily-traffic", type=int, default=5000, help="Daily exposed users")
    parser.add_argument("--sensitivity", action="store_true", help="Show sensitivity table")
    args = parser.parse_args()

    result = sample_size_proportions(args.baseline, args.mde, args.alpha, args.power)
    print_result(result, label="Sample Size Calculation")

    runtime = estimate_runtime(result["n_per_variant"], args.daily_traffic)
    print_result(runtime, label="Runtime Estimate")

    if args.sensitivity:
        sensitivity_table(args.baseline, alpha=args.alpha, power=args.power)
