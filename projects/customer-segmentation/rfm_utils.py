"""
rfm_utils.py
------------
Reusable helper functions for RFM (Recency, Frequency, Monetary) analysis
and K-Means customer segmentation.

Author: Allen Day
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")


# ─── RFM COMPUTATION ────────────────────────────────────────────────────────

def compute_rfm(df: pd.DataFrame,
                customer_col: str = "customer_id",
                date_col: str = "transaction_date",
                value_col: str = "order_value",
                snapshot_date=None) -> pd.DataFrame:
    """
    Compute RFM scores for each customer.

    Parameters
    ----------
    df : DataFrame with transaction records
    customer_col : column name for customer identifier
    date_col : column name for transaction date
    value_col : column name for transaction value
    snapshot_date : reference date for recency (defaults to max date + 1 day)

    Returns
    -------
    DataFrame with columns: customer_id, Recency, Frequency, Monetary
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    if snapshot_date is None:
        snapshot_date = df[date_col].max() + timedelta(days=1)

    rfm = df.groupby(customer_col).agg(
        Recency=(date_col, lambda x: (snapshot_date - x.max()).days),
        Frequency=(date_col, "count"),
        Monetary=(value_col, "sum"),
    ).reset_index()

    rfm.rename(columns={customer_col: "customer_id"}, inplace=True)
    return rfm


def rfm_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """Print descriptive stats for RFM features."""
    print("── RFM Feature Summary ─────────────────────────────")
    print(rfm[["Recency", "Frequency", "Monetary"]].describe().round(2))
    return rfm[["Recency", "Frequency", "Monetary"]].describe()


# ─── SCALING ────────────────────────────────────────────────────────────────

def scale_rfm(rfm: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    """
    Standardize RFM features using StandardScaler.

    Returns
    -------
    scaled_array : numpy array of scaled features
    scaler : fitted StandardScaler (for inverse_transform if needed)
    """
    scaler = StandardScaler()
    features = ["Recency", "Frequency", "Monetary"]
    scaled = scaler.fit_transform(rfm[features])
    return scaled, scaler


# ─── OPTIMAL K SELECTION ────────────────────────────────────────────────────

def elbow_and_silhouette(scaled: np.ndarray,
                         k_range: range = range(2, 11)) -> dict:
    """
    Compute inertia (elbow) and silhouette scores for a range of k values.

    Returns
    -------
    dict with keys 'inertia', 'silhouette', 'k_values'
    """
    inertias, silhouettes = [], []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(scaled, labels))

    return {"k_values": list(k_range),
            "inertia": inertias,
            "silhouette": silhouettes}


def plot_elbow_silhouette(scores: dict, figsize: tuple = (12, 4)) -> None:
    """Plot elbow curve and silhouette scores side-by-side."""
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    axes[0].plot(scores["k_values"], scores["inertia"], "bo-", linewidth=2)
    axes[0].set_title("Elbow Method — Inertia vs K")
    axes[0].set_xlabel("Number of Clusters (k)")
    axes[0].set_ylabel("Inertia")
    axes[0].grid(alpha=0.3)

    axes[1].plot(scores["k_values"], scores["silhouette"], "go-", linewidth=2)
    axes[1].set_title("Silhouette Score vs K")
    axes[1].set_xlabel("Number of Clusters (k)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()
    print(f"Best k by silhouette: {scores['k_values'][np.argmax(scores['silhouette'])]}")


# ─── CLUSTERING ─────────────────────────────────────────────────────────────

SEGMENT_LABELS = {
    0: "💎 Champions",
    1: "🌱 At-Risk",
    2: "🚀 Promising",
    3: "😴 Dormant",
}


def fit_kmeans(rfm: pd.DataFrame,
               scaled: np.ndarray,
               k: int = 4,
               segment_map: dict = None) -> pd.DataFrame:
    """
    Fit K-Means and assign segment labels to customers.

    Returns
    -------
    rfm DataFrame with added 'Cluster' and 'Segment' columns
    """
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    rfm = rfm.copy()
    rfm["Cluster"] = km.fit_predict(scaled)

    # Remap clusters by descending Monetary value (most valuable = 0)
    cluster_means = rfm.groupby("Cluster")["Monetary"].mean().sort_values(ascending=False)
    rank_map = {old: new for new, old in enumerate(cluster_means.index)}
    rfm["Cluster"] = rfm["Cluster"].map(rank_map)

    labels = segment_map or SEGMENT_LABELS
    rfm["Segment"] = rfm["Cluster"].map(labels)

    return rfm


# ─── PROFILING & VISUALIZATION ──────────────────────────────────────────────

def profile_segments(rfm: pd.DataFrame) -> pd.DataFrame:
    """Return mean RFM values and customer count per segment."""
    profile = (
        rfm.groupby("Segment")
        .agg(
            Customers=("customer_id", "count"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean"),
            Avg_Monetary=("Monetary", "mean"),
        )
        .round(1)
        .sort_values("Avg_Monetary", ascending=False)
    )
    profile["Pct_Customers"] = (profile["Customers"] / profile["Customers"].sum() * 100).round(1)
    print(profile)
    return profile


def plot_rfm_heatmap(rfm: pd.DataFrame) -> None:
    """Plot heatmap of mean RFM values per segment."""
    pivot = rfm.groupby("Segment")[["Recency", "Frequency", "Monetary"]].mean()
    # Normalize for visual comparison
    pivot_norm = (pivot - pivot.min()) / (pivot.max() - pivot.min())

    plt.figure(figsize=(8, 4))
    sns.heatmap(pivot_norm, annot=pivot.round(0), fmt="g",
                cmap="YlOrRd", linewidths=0.5)
    plt.title("RFM Heatmap by Segment (normalized)")
    plt.tight_layout()
    plt.show()


def plot_segment_distribution(rfm: pd.DataFrame) -> None:
    """Bar chart of customer count per segment."""
    counts = rfm["Segment"].value_counts()
    colors = ["#FFD700", "#FF6B6B", "#4ECDC4", "#95A5A6"]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 50, str(val),
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_title("Customer Count by Segment", fontsize=14, fontweight="bold")
    ax.set_ylabel("Number of Customers")
    ax.set_xlabel("Segment")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()
