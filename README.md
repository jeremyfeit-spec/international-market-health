# International Market Health — Super Dashboard

Unified weekly view of (a) competitor moves and (b) regulatory developments
affecting Intuit's international accounting platform. Combines the two existing
Friday feeds into a single executive-friendly page.

**Live URL (after first push):** `https://jeremyfeit-spec.github.io/international-market-health/`

## What you see

1. **Executive review** — AI synthesis of the week's biggest moves and any
   cross-signals (e.g. competitor X just raised in market Y where regulator Z
   just shifted).
2. **KPI tiles** — competitor signals, Tier-1 hits, reg changes, urgent
   mandates, active markets, cross-signals.
3. **Side-by-side feeds** — competitor moves (Market Pulse) on the left,
   regulatory changes (Reg Tracker) on the right. Shared filters: search,
   region, urgency, tier.

## Data flow

```
Friday 8:00 AM PT  →  market-pulse-friday-digest      (existing)
Friday 8:00 AM PT  →  regulatory-tracker-friday-digest (existing)
Friday 8:15 AM PT  →  super-digest-friday              (new, runs after both)
                       ├─ pulls JSON from both source dashboards
                       ├─ generates AI executive review
                       ├─ writes docs/data/super_digest.json
                       ├─ git push origin main
                       └─ posts combined exec digest to Slack
```

## Setup

```bash
# 1. Initialize the new repo
cd international-market-health
git init
git add .
git commit -m "init super dashboard"

# 2. Create empty repo on GitHub (do not init with README)
#    https://github.com/new  →  international-market-health  (Public)

git remote add origin git@github.com:jeremyfeit-spec/international-market-health.git
git branch -M main
git push -u origin main

# 3. Enable GitHub Pages
#    Settings → Pages → Source: Deploy from branch → Branch: main / docs
```

## Wiring to existing dashboards

The super-dashboard expects each source dashboard to expose a small JSON file
the new Friday job can fetch. **One-time addition** to each existing dashboard:

- `international_market_pulse/docs/data/competitor_signals.json` →
  `{ generated_at, week_start, week_end, signals: [{company, region, tier, signal_type, summary, source_url, source_label, date, headline}] }`

- `regulatory-tracker/docs/data/regulatory_changes.json` →
  `{ generated_at, changes: [{country, iso, region, topic, title, summary, status, effective_date, source_url, urgent}] }`

Both existing Friday SKILL.md files already produce these fields internally; the
super-digest task adds a step at the end of each run to also serialize them.

## Files

- `docs/index.html` — the dashboard (single file, no build step)
- `docs/data/super_digest.json` — current week's synthesized payload
- `docs/data/history/` — past weeks' digests
- `config/` — channel IDs, sources, etc.
