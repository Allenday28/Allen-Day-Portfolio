#!/bin/bash
# ============================================================
# push_to_github.sh
# Initializes git and pushes the full portfolio to GitHub
# Run once from Terminal: bash ~/Documents/Claude/Projects/Portfolio/push_to_github.sh
# ============================================================

set -e  # Stop on any error

PORTFOLIO_DIR="$HOME/Documents/Claude/Projects/Portfolio"
REPO_URL="https://github.com/Allenday28/Allen-Day-Portfolio.git"

echo ""
echo "=============================================="
echo "  Allen Day Portfolio — GitHub Push Script"
echo "=============================================="
echo ""

# Move into portfolio folder
cd "$PORTFOLIO_DIR"
echo "📂 Working in: $PORTFOLIO_DIR"

# Initialize git if not already a repo
if [ ! -d ".git" ]; then
  echo "🔧 Initializing git repository..."
  git init
  git branch -M main
else
  echo "✅ Git repo already initialized"
fi

# Set git identity if not configured
if [ -z "$(git config user.name)" ]; then
  git config user.name "Allen Day"
fi
if [ -z "$(git config user.email)" ]; then
  git config user.email "allen.day24@gmail.com"
fi

# Set or update remote
if git remote get-url origin &>/dev/null; then
  echo "🔗 Updating remote origin → $REPO_URL"
  git remote set-url origin "$REPO_URL"
else
  echo "🔗 Adding remote origin → $REPO_URL"
  git remote add origin "$REPO_URL"
fi

# Create .gitignore
cat > .gitignore << 'EOF'
.DS_Store
__pycache__/
*.pyc
*.pyo
*.egg-info/
.env
.venv/
venv/
*.sqlite3
analytics.db
data/
push_to_github.sh
EOF

# Stage all files
echo ""
echo "📦 Staging all portfolio files..."
git add .
echo "$(git status --short | wc -l | tr -d ' ') files staged"

# Commit
echo ""
echo "💾 Committing..."
git commit -m "feat: Add complete data science portfolio suite

Projects:
- Sales Performance Analysis (SQL + Python + Power BI)
- Customer Segmentation (RFM + K-Means ML)
- Revenue Forecasting (Prophet + ARIMA)
- ETL Data Pipeline (Python + SQLite)
- A/B Testing Framework (SciPy + Statsmodels)
- DermaMind AI project page

Labs: SQL analytics patterns, Python data science fundamentals
Profile README: badges, skills table, project showcase" \
  --allow-empty

# Push (force to replace old files)
echo ""
echo "🚀 Pushing to GitHub (this may ask for your credentials)..."
echo ""
git push -u origin main --force

echo ""
echo "=============================================="
echo "  ✅ Portfolio pushed successfully!"
echo "  🔗 View at: https://github.com/Allenday28/Allen-Day-Portfolio"
echo "=============================================="
echo ""
echo "Next step: Create your profile README repo"
echo "  1. Go to https://github.com/new"
echo "  2. Name it exactly: allenday28"
echo "  3. Make it Public, add a README"
echo "  4. Paste the contents of README.md into it"
echo ""
