#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Publish: judicial-transparency-indonesia-2023
# GitHub : git@github.com:bsdkijc-dev/judicial-transparency-indonesia-2023.git
# Kaggle : https://www.kaggle.com/datasets/judicialcollege/mahkamah-agung-ri-financial-reconciliation-2023
# ==============================================================================

REPO_NAME="judicial-transparency-indonesia-2023"
GITHUB_USER="bsdkijc-dev"

echo "[1/2] Initializing and pushing to GitHub (${GITHUB_USER}/${REPO_NAME}) via SSH..."
if [ ! -d ".git" ]; then
  git init
  git branch -M main
fi

git config user.name "Cecep Mustafa"
git config user.email "cecepmustafa97@gmail.com"

git add .
git commit -m "feat(fy2023): Mahkamah Agung RI FY 2023 Audited Financial Reconciliation (20 CSVs, 841 rows)" || true
git tag -a "v1.0.0-fy2023" -m "Audited LK MA RI FY 2023 Release" || true

git remote remove origin 2>/dev/null || true
git remote add origin "git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
git push -u origin main --follow-tags

echo "[2/2] Pushing dataset to Kaggle (judicialcollege/mahkamah-agung-ri-financial-reconciliation-2023)..."
chmod 600 ~/.kaggle/kaggle.json 2>/dev/null || true
if kaggle datasets status "judicialcollege/mahkamah-agung-ri-financial-reconciliation-2023" >/dev/null 2>&1; then
  kaggle datasets version -p . -m "Release v1.0.0: Audited LK MA RI FY 2023 Financial Reconciliation" -r zip
else
  kaggle datasets create -p . -r zip
fi

echo "[DONE] GitHub and Kaggle sync completed."
