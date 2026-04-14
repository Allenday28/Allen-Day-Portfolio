# 🐍 Python Labs — Data Science Fundamentals

> Practical, annotated Python examples covering the core skills used daily in data science and analytics roles.

---

## Lab Index

| # | Topic | Libraries |
|---|-------|---------|
| 01 | [Data Cleaning Workflow](#01-data-cleaning-workflow) | Pandas, NumPy |
| 02 | [Exploratory Data Analysis](#02-exploratory-data-analysis) | Pandas, Matplotlib, Seaborn |
| 03 | [Feature Engineering](#03-feature-engineering) | Pandas, Scikit-learn |
| 04 | [Classification Model](#04-classification-model) | Scikit-learn, Pandas |
| 05 | [Data Visualization Gallery](#05-visualization-gallery) | Matplotlib, Seaborn, Plotly |

---

## 01. Data Cleaning Workflow

```python
import pandas as pd
import numpy as np

# ── Load & Inspect ──────────────────────────────────────────
df = pd.read_csv('raw_data.csv')

print(f"Shape: {df.shape}")
print(f"\nMissing values:\n{df.isnull().sum()}")
print(f"\nDuplicates: {df.duplicated().sum()}")
print(f"\nData types:\n{df.dtypes}")

# ── Step 1: Handle Missing Values ────────────────────────────
# Strategy: document and apply rules per column
missing_strategy = {
    'age':         'median',
    'income':      'median',
    'city':        'mode',
    'email':       'drop_row',
    'signup_date': 'drop_row'
}

for col, strategy in missing_strategy.items():
    if col not in df.columns:
        continue
    if strategy == 'median':
        df[col] = df[col].fillna(df[col].median())
    elif strategy == 'mode':
        df[col] = df[col].fillna(df[col].mode()[0])
    elif strategy == 'drop_row':
        df = df.dropna(subset=[col])

# ── Step 2: Remove Duplicates ────────────────────────────────
original_count = len(df)
df = df.drop_duplicates(subset=['customer_id'], keep='last')
print(f"Removed {original_count - len(df)} duplicates")

# ── Step 3: Standardize Text Fields ─────────────────────────
text_cols = ['city', 'state', 'product_category']
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].str.strip().str.title()

# ── Step 4: Fix Date Formats ─────────────────────────────────
df['signup_date'] = pd.to_datetime(df['signup_date'], errors='coerce')
df['signup_year']  = df['signup_date'].dt.year
df['signup_month'] = df['signup_date'].dt.month

# ── Step 5: Outlier Detection (IQR Method) ───────────────────
def remove_outliers_iqr(df, col, multiplier=1.5):
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    before = len(df)
    df_clean = df[(df[col] >= lower) & (df[col] <= upper)]
    print(f"  {col}: removed {before - len(df_clean)} outliers")
    return df_clean

df = remove_outliers_iqr(df, 'income')

print(f"\nFinal clean dataset shape: {df.shape}")
df.to_csv('clean_data.csv', index=False)
print("Saved to clean_data.csv")
```

---

## 02. Exploratory Data Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('clean_data.csv')

# ── Summary Statistics ────────────────────────────────────────
print(df.describe(include='all').T)

# ── Distribution Plots ────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
numerical_cols = df.select_dtypes(include='number').columns[:6]

for ax, col in zip(axes.flat, numerical_cols):
    ax.hist(df[col].dropna(), bins=30, color='steelblue', edgecolor='white', alpha=0.8)
    ax.axvline(df[col].mean(), color='red', linestyle='--', label=f'Mean: {df[col].mean():.1f}')
    ax.set_title(f'Distribution: {col}')
    ax.legend()

plt.suptitle('Feature Distributions', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('distributions.png', dpi=150, bbox_inches='tight')

# ── Correlation Heatmap ───────────────────────────────────────
plt.figure(figsize=(10, 8))
corr_matrix = df.select_dtypes(include='number').corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # Hide upper triangle
sns.heatmap(
    corr_matrix,
    mask=mask,
    annot=True, fmt='.2f',
    cmap='RdYlGn', center=0,
    vmin=-1, vmax=1,
    linewidths=0.5
)
plt.title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=150)
```

---

## 03. Feature Engineering

```python
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

df = pd.read_csv('clean_data.csv')

# ── Derived Features ──────────────────────────────────────────
df['account_age_days']   = (pd.Timestamp.now() - df['signup_date']).dt.days
df['revenue_per_order']  = df['total_revenue'] / df['order_count'].replace(0, np.nan)
df['is_high_value']      = (df['total_revenue'] > df['total_revenue'].quantile(0.75)).astype(int)

# ── Binning ───────────────────────────────────────────────────
df['age_group'] = pd.cut(df['age'],
    bins=[0, 25, 35, 50, 65, 100],
    labels=['Under 25', '25-34', '35-49', '50-64', '65+']
)

df['revenue_tier'] = pd.qcut(df['total_revenue'], q=4,
    labels=['Bronze', 'Silver', 'Gold', 'Platinum']
)

# ── Encoding ──────────────────────────────────────────────────
# One-hot encode low-cardinality categoricals
df = pd.get_dummies(df, columns=['region', 'product_category'], drop_first=True)

# Label encode ordinal features
le = LabelEncoder()
df['revenue_tier_encoded'] = le.fit_transform(df['revenue_tier'].astype(str))

# ── Scaling ───────────────────────────────────────────────────
scale_cols = ['age', 'income', 'total_revenue', 'order_count', 'account_age_days']
scaler = StandardScaler()
df[[f'{c}_scaled' for c in scale_cols]] = scaler.fit_transform(df[scale_cols])

print(f"Feature engineered dataset: {df.shape}")
print(df.head(3))
```

---

## 04. Classification Model

```python
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('clean_data.csv')

# ── Define Features & Target ──────────────────────────────────
feature_cols = ['age', 'income', 'order_count', 'account_age_days', 'revenue_per_order']
X = df[feature_cols].fillna(df[feature_cols].median())
y = df['is_churned']  # Binary target: 1 = churned, 0 = retained

# ── Train / Test Split ────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {X_train.shape}, Test: {X_test.shape}")

# ── Train Random Forest ───────────────────────────────────────
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_split=10,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────
y_pred = model.predict(X_test)
print("\n=== Classification Report ===")
print(classification_report(y_test, y_pred))

# Cross-validation AUC
cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
print(f"Cross-Val AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# ── Feature Importance ────────────────────────────────────────
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=True)

plt.figure(figsize=(8, 5))
plt.barh(importance_df['feature'], importance_df['importance'], color='steelblue')
plt.title('Feature Importance — Random Forest', fontweight='bold')
plt.xlabel('Importance Score')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=150)
print("Feature importance chart saved.")
```
