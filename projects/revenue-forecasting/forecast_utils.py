"""
forecast_utils.py
-----------------
Helper functions for revenue time-series forecasting.
Supports Facebook Prophet and ARIMA benchmark comparisons.

Author: Allen Day
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings

warnings.filterwarnings("ignore")


# ─── DATA PREPARATION ───────────────────────────────────────────────────────

def prepare_prophet_df(df: pd.DataFrame,
                       date_col: str = "date",
                       revenue_col: str = "revenue") -> pd.DataFrame:
    """
    Rename columns to Prophet's required format: ds (date) and y (target).

    Parameters
    ----------
    df : DataFrame with date and revenue columns
    date_col : name of the date column
    revenue_col : name of the revenue column

    Returns
    -------
    DataFrame with columns 'ds' and 'y'
    """
    prophet_df = df[[date_col, revenue_col]].copy()
    prophet_df.columns = ["ds", "y"]
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    prophet_df = prophet_df.sort_values("ds").reset_index(drop=True)
    return prophet_df


def train_test_split_ts(df: pd.DataFrame,
                        test_weeks: int = 13) -> tuple:
    """
    Split a time series DataFrame into train and test sets.

    Returns
    -------
    (train_df, test_df)
    """
    cutoff = df["ds"].max() - pd.Timedelta(weeks=test_weeks)
    train = df[df["ds"] <= cutoff].copy()
    test = df[df["ds"] > cutoff].copy()
    print(f"Train: {len(train)} rows | Test: {len(test)} rows | Cutoff: {cutoff.date()}")
    return train, test


# ─── METRICS ────────────────────────────────────────────────────────────────

def evaluate_forecast(actual: pd.Series,
                      predicted: pd.Series,
                      model_name: str = "Model") -> dict:
    """
    Compute MAPE, RMSE, and MAE for a forecast.

    Returns
    -------
    dict with metric values
    """
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mae = mean_absolute_error(actual, predicted)

    results = {"Model": model_name, "MAPE": round(mape, 2),
               "RMSE": round(rmse, 0), "MAE": round(mae, 0)}
    print(f"  {model_name} → MAPE: {mape:.1f}% | RMSE: ${rmse:,.0f} | MAE: ${mae:,.0f}")
    return results


def compare_models(results_list: list[dict]) -> pd.DataFrame:
    """Display a ranked comparison table of model performance."""
    df = pd.DataFrame(results_list).sort_values("MAPE")
    df["RMSE"] = df["RMSE"].apply(lambda x: f"${x:,.0f}")
    df["MAE"] = df["MAE"].apply(lambda x: f"${x:,.0f}")
    df["MAPE"] = df["MAPE"].apply(lambda x: f"{x:.1f}%")
    print("\n── Model Comparison ─────────────────────────────────")
    print(df.to_string(index=False))
    return df


# ─── PLOTTING ───────────────────────────────────────────────────────────────

def plot_forecast(train: pd.DataFrame,
                  forecast: pd.DataFrame,
                  test: pd.DataFrame = None,
                  title: str = "Revenue Forecast",
                  ci_lower_col: str = "yhat_lower",
                  ci_upper_col: str = "yhat_upper") -> None:
    """
    Plot historical revenue, forecast, and optional actuals.

    Parameters
    ----------
    train : historical data with columns 'ds' and 'y'
    forecast : Prophet forecast DataFrame (must have 'ds', 'yhat',
               'yhat_lower', 'yhat_upper')
    test : optional held-out actuals
    title : chart title
    """
    fig, ax = plt.subplots(figsize=(14, 5))

    # Historical
    ax.plot(train["ds"], train["y"], color="#2c3e50",
            linewidth=2, label="Historical Revenue")

    # Forecast
    future_mask = forecast["ds"] > train["ds"].max()
    ax.plot(forecast.loc[future_mask, "ds"],
            forecast.loc[future_mask, "yhat"],
            color="#3498db", linewidth=2.5, linestyle="--",
            label="Forecast")

    # Confidence interval
    if ci_lower_col in forecast.columns and ci_upper_col in forecast.columns:
        ax.fill_between(forecast.loc[future_mask, "ds"],
                        forecast.loc[future_mask, ci_lower_col],
                        forecast.loc[future_mask, ci_upper_col],
                        alpha=0.2, color="#3498db", label="80% CI")

    # Actuals (test set)
    if test is not None:
        ax.plot(test["ds"], test["y"], "o-", color="#e74c3c",
                linewidth=1.5, markersize=4, label="Actual (held-out)")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=30)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K")
    )
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_components(model, forecast: pd.DataFrame) -> None:
    """Plot Prophet trend + seasonality components."""
    model.plot_components(forecast)
    plt.suptitle("Forecast Components: Trend & Seasonality", y=1.02)
    plt.tight_layout()
    plt.show()


# ─── SUMMARY STATS ──────────────────────────────────────────────────────────

def forecast_summary(forecast: pd.DataFrame,
                     horizon_weeks: int = 13) -> None:
    """Print key numbers for the forecast horizon."""
    future = forecast.tail(horizon_weeks)
    total = future["yhat"].sum()
    lower = future["yhat_lower"].sum()
    upper = future["yhat_upper"].sum()
    weekly_avg = future["yhat"].mean()

    print(f"\n── {horizon_weeks}-Week Forecast Summary ─────────────────────")
    print(f"  Total projected revenue : ${total:,.0f}")
    print(f"  80% confidence range    : ${lower:,.0f} – ${upper:,.0f}")
    print(f"  Average weekly revenue  : ${weekly_avg:,.0f}")
    peak_week = future.loc[future["yhat"].idxmax(), "ds"]
    print(f"  Peak week               : {peak_week.strftime('%b %d, %Y')}")
