# 🚀 GitHub Portfolio Setup Guide
### How to Upload Everything to GitHub — Step by Step

---

## 📦 What's In This Folder

```
Portfolio/
├── README.md                           ← Main profile README (goes in a SPECIAL repo)
├── GITHUB_SETUP_GUIDE.md             ← This file
├── projects/
│   ├── sales-performance-analysis/    ← Project 1 (SQL + Python + Power BI)
│   ├── customer-segmentation/         ← Project 2 (ML + K-Means)
│   ├── revenue-forecasting/           ← Project 3 (Prophet Forecasting)
│   ├── etl-data-pipeline/             ← Project 4 (Python ETL)
│   └── ab-testing-analysis/            ← Project 5 (Stats + A/B Testing)
├── dermamind-ai/                      ← DermaMind AI project page
├── labs/
│   ├── sql/                           ← SQL window functions, CTEs, funnels
│   └── python/                        ← Python EDA, ML, cleaning
└── resume/                             ← Resume folder (add your PDF here)
```

---

## 🔧 STEP 1: Create Your Profile README Repository

GitHub has a **special secret repo** — if you create a repo with the EXACT same name as your username, the README.md in it becomes your profile page.

1. Go to: https://github.com/new
2. Repository name: **`allenday28`** (must match your username exactly)
3. Check ✅ "Public"
4. Check ✅ "Add a README file"
5. Click **Create repository**
6. Click the pencil edit icon on the README
7. **Delete all the default text** and paste in the contents of the `README.md` file from this folder
8. Click **Commit changes**

---

## 🔧 STEP 2: Update Your Allen-Day-Portfolio Repository

Upload all project files to your existing `Allen-Day-Portfolio` repo.

### Option A: Upload via GitHub Web (Easiest)

1. Go to: https://github.com/allenday28/Allen-Day-Portfolio
2. Click **Add file** → **Upload files**
3. Drag and drop the entire `projects/` folder
4. Add commit message: `"Add: Complete portfolio project suite"`
5. Click **Commit changes**
6. Repeat for `labs/`, `dermamind-ai/`, `resume/`

### Option B: Command Line (If you have Git installed)

```bash
# Clone your repo
git clone https://github.com/allenday28/Allen-Day-Portfolio.git
cd Allen-Day-Portfolio

# Copy all files from the Portfolio folder
cp -r /path/to/Portfolio/projects .
cp -r /path/to/Portfolio/labs .
cp -r /path/to/Portfolio/dermamind-ai .
cp -r /path/to/Portfolio/resume .

# Add the main README
cp /path/to/Portfolio/README.md README.md

# Commit and push
git add .
git commit -m "Add: Complete recruiter-ready data science portfolio"
git push origin main
```

---

## 🔧 STEP 3: Pin Your Best Repos

1. Go to your profile: https://github.com/allenday28
2. Click **Customize your pins**
3. Pin these repos:
   - `Allen-Day-Portfolio`
   - `allenday28` (your profile README repo)

---

## 🔧 STEP 4: Update Your GitHub Profile Bio

1. Go to: https://github.com/settings/profile
2. **Name:** Allen Day
3. **Bio:** `Data Scientist & Analyst | MS Data Science | Python · SQL · ML · Power BI | Creator of DermaMind AI | Open to opportunities`
4. **Location:** Orange County, CA
5. **Website:** `https://personal-analysis-skincare.deploypad.app`
6. **LinkedIn:** Add your LinkedIn URL
7. Click **Save profile**

---

## 🔧 STEP 5: Add Your Resume PDF

1. Place your resume file in the `resume/` folder
2. Name it: `Allen_Day_Resume.pdf`
3. Upload to GitHub inside the `Allen-Day-Portfolio/resume/` folder

---

## ✅ Final Checklist

- [ ] Created `allenday28/allenday28` profile README repo
- [ ] Pasted profile README content (badges, bio, skills table, project table)
- [ ] Uploaded all 5 projects to `Allen-Day-Portfolio`
- [ ] Uploaded DermaMind AI project page
- [ ] Uploaded SQL and Python labs
- [ ] Added resume PDF to `resume/` folder
- [ ] Pinned repos on profile page
- [ ] Updated GitHub bio and website link
- [ ] Verified all links work (DermaMind AI link, LinkedIn link)

---

## 💡 Pro Tips

**Keep contributing.** Even small commits keep your contribution graph green. Set a goal of committing something every week.

**Add actual notebooks.** Once you do coursework in Jupyter, export the `.ipynb` files and add them to the matching project folders.

**Link your GitHub on LinkedIn.** Add your GitHub URL to your LinkedIn profile in the "Contact info" section.

**Update as you grow.** Every new school project, lab, or analysis should become a commit. Your portfolio is a living document.

---

## 📬 Questions?

This portfolio was built to target **Data Analyst**, **Data Scientist**, and **Business Intelligence** roles. If you need help customizing any project or adding new work, reach out!
