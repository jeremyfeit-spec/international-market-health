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
- `docs/data/voc_cache.json` — last successful scrape per (platform, company)
- `config/` — channel IDs, sources, scoring weights
- `scripts/voc_scraper.py` — best-effort live fetch from Trustpilot, ProductReview, G2, Capterra
- `scripts/build_voc.py` — turns the scraped cache into the VOC bucket
- `scripts/build_final_digest.py` — assembles `super_digest.json`
- `scripts/refresh_helper.py` — local HTTP server for the dashboard's "Refresh" button

## Refreshing VOC on demand

The dashboard has a **Refresh** button next to the Voice of Customer section.
Clicking it triggers a real scrape of Trustpilot/G2/Capterra/ProductReview
*on your Mac* (the GitHub Pages site can't scrape). To enable the button:

```bash
# Open a terminal on your Mac
cd ~/Documents/international-market-health
python3 scripts/refresh_helper.py
```

Leave that terminal running. Now click **Refresh** in the dashboard. The button
spins, you'll see live log output, and when it finishes the dashboard reloads
with the new numbers.

If the button reports "Cannot reach the refresh helper", the script isn't
running — start it as above and try again.

The helper listens on `localhost:7325` only — never exposed to the network.

## Auto-refresh (Friday cron)

The Friday `super-digest-friday` task automatically runs the same three-step
pipeline (`voc_scraper.py` → `build_voc.py` → `build_final_digest.py`) before
generating the weekly Slack digest. No manual action needed for the weekly
cycle.

## Scraper honesty

`voc_scraper.py` is a best-effort direct fetch — no paid scraping service. It
works reliably for Trustpilot and ProductReview.com.au. G2 and Capterra have
strong bot detection and may fail; when they do, the cache keeps the
last-successful value (with a `last_successful_at` timestamp so you can see
how stale it is) and the dashboard surfaces the staleness honestly via a pill
under the section title.
