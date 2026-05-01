#!/bin/bash
# One-shot setup for international-market-health repo.
# Run this from INSIDE the international-market-health folder you unzipped.
set -e

cd "$(dirname "$0")"

# 1. Clean up the accidental home-folder git repo from earlier attempts
if [ -d "$HOME/.git" ]; then
  echo "→ Found a stray .git in your home folder from the earlier failed attempt. Removing it."
  rm -rf "$HOME/.git"
fi

# 2. Init local repo
echo "→ Initializing repo in $(pwd)"
rm -rf .git
git init -b main >/dev/null
git add .
git commit -m "init super dashboard" >/dev/null
echo "→ Local commit created"

# 3. Add remote (assumes the empty repo already exists on github.com)
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/jeremyfeit-spec/international-market-health.git

# 4. Push
echo "→ Pushing to GitHub…"
git push -u origin main

echo ""
echo "✅ Done. Next: enable GitHub Pages."
echo "   1. Open: https://github.com/jeremyfeit-spec/international-market-health/settings/pages"
echo "   2. Source = Deploy from a branch · Branch = main · Folder = /docs · Save"
echo "   3. Wait ~1 minute, then open:"
echo "      https://jeremyfeit-spec.github.io/international-market-health/"
