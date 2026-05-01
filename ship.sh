#!/bin/bash
# Ship the weekly super-digest. Safe to run multiple times.
set -e
cd "$(dirname "$0")"

# Clear stale sandbox locks (these can survive when Cowork's sandbox runs git)
rm -f .git/index.lock .git/HEAD.lock .git/objects/maintenance.lock 2>/dev/null || true

git add config docs scripts super-digest-friday-SKILL.md ship.sh
git commit -m "Add Market Health Score (0-10 rule-based), VOC bucket (Trustpilot ratings snapshot + 7 themes), 9-week backfill (2026-03-06 to 2026-04-24) with reconstructed competitor + regulatory signals, Chart.js sparkline, Feet-on-the-Ground scaffold; update SKILL.md and Slack message format"
git push
echo ""
echo "Done. GitHub Pages will rebuild in ~30-90 seconds."
echo "Refresh: https://jeremyfeit-spec.github.io/international-market-health/"
