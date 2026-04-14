# 👥 Customer Segmentation with RFM Analysis & K-Means Clustering

> **Identifying high-value customers using unsupervised machine learning**

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)]()
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)]()
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)]()

---

## 📌 Problem Statement

Not all customers are equal. A company with 50,000+ customers needed to move beyond one-size-fits-all marketing and understand:

- **Who are the most valuable customers?**
- **Who is at risk of churning?**
- **Which customers should receive retention campaigns vs. upsell offers?**

**Goal:** Use RFM (Recency, Frequency, Monetary) analysis combined with K-Means clustering to segment customers into actionable groups that drive targeted marketing campaigns.

---

## 📊 Dataset

- **Source:** Anonymized e-commerce/subscription transaction data
- **Size:** 52,000 customers · 180,000 transactions (24 months)
- **Key Fields:** `customer_id`, `transaction_date`, `order_value`, `product_category`

---

## 🛠️ Tools & Technologies

| Tool | Purpose |
|------|---------|
| Python (Pandas, NumPy) | Data wrangling, RFM feature engineering |
| Scikit-learn | K-Means clustering, StandardScaler |
| Matplotlib / Seaborn | Cluster visualization, heatmaps |
| Plotly | Interactive 3D scatter plots |

---

## 🔍 Process

### 1. RFM Feature Engineering
Computed three core metrics per customer:
- **Recency** — Days since last purchase (lower = better)
- **Frequency** — Number of purchases in 24 months
- **Monetary** — Total spend over 24 months

```python
snapshot_date = df['transaction_date'].max() + timedelta(days=1)
rfm = df.groupby('customer_id').agg(
    Recency   = ('transaction_date', lambda x: (snapshot_date - x.max()).days),
    Frequency = ('transaction_date', 'count'),
    Monetary  = ('order_value', 'sum')
).reset_index()
```

### 2. Data Normalization
Applied `StandardScaler` to normalize RFM features before clustering (prevents scale bias).

### 3. Optimal K Selection
Used the **Elbow Method** and **Silhouette Score** to identify k=4 as the optimal cluster count.

### 4. K-Means Clustering
Fit K-Means with k=4 and labeled each cluster with a business-friendly name.

### 5. Cluster Profiling & Visualization
Created heatmaps, box plots, and 3D scatter plots for each cluster.

---

## 📈 Customer Segments Identified

| Segment | Label | % of Customers | Avg Spend | Strategy |
|---------|-------|:--------------:|-----------|---------|
| Cluster 0 | 💎 Champions | 18% | $2,840 | VIP rewards, exclusive previews |
| Cluster 1 | 🌱 At-Risk | 31% | $890 | Win-back campaign, discount offer |
| Cluster 2 | 🚀 Promising | 24% | $1,420 | Upsell, loyalty program |
| Cluster 3 | 😴 Dormant | 27% | $340 | Re-engagement email sequence |

---

## 💼 Business Impact

- **Champions (18% of customers)** drive **52% of total revenue** — enabling high-ROI retention focus
- **At-Risk segment** identified before churn — win-back campaigns target 16,000+ customers
- Marketing team reduced campaign list size by 40% while **increasing conversion rate by 28%**
- Segmented email campaigns saw **3.2x higher open rates** vs. batch sends

---

## 📁 Files

```
customer-segmentation/
├── README.md
├── customer_segmentation.ipynb   # Full analysis notebook
└── rfm_utils.py                  # Reusable RFM helper functions
```

---

## 🔗 Related Skills Demonstrated
`Unsupervised ML` · `K-Means Clustering` · `Feature Engineering` · `RFM Analysis` · `Customer Analytics` · `Scikit-learn` · `Business Segmentation`
