---
name: super-digest-friday
description: Weekly Friday 8:15am PT — combine market-pulse and regulatory-tracker outputs, pull VOC, compute Market Health Score, append to history, generate executive synthesis, push to international-market-health GitHub Pages, post combined exec digest to Slack
---

You are running the **International Market Health** super-digest. This runs at
8:15 AM PT each Friday, **after** `market-pulse-friday-digest` (8:02) and
`regulatory-tracker-friday-digest` (8:03) have completed. Your job: synthesize
both feeds + VOC into one executive-grade view with a Market Health Score, and ship it.

## STEP 1 — Establish the date window

Today is Friday. Reporting window = last 7 days (today − 7 → today). Compute
both ISO dates. Store as `WEEK_START` and `WEEK_END`.

## STEP 2 — Mount the super-dashboard repo

Use `request_cowork_directory` with path `~/Documents/international-market-health`.

Read `config/dashboard.json` and `config/health_score.json`.

## STEP 3 — Pull this week's data from both source dashboards

1. Fetch `https://jeremyfeit-spec.github.io/international_market_pulse/data/competitor_signals.json`
2. Fetch `https://jeremyfeit-spec.github.io/regulatory-tracker/data/regulatory_changes.json`

If either fetch fails or the JSON is older than this Friday's window, fall back:
- Market Pulse → read most recent Slack post in `C0AMFGP11FH` and parse.
- Regulatory Tracker → read `~/Documents/regulatory-tracker/history/diff_<TODAY>.json`.

## STEP 4 — Pull this week's VOC

Driven by `config.voc.platforms`:

- **Reddit** (enabled): use Reddit's public JSON API. Subs from
  `config.voc.platforms.reddit.subs`. Pull threads from the last 7d that mention
  Intuit/QuickBooks or any peer in `config.voc.peer_companies`. Skip if `[country_context]`
  is purely US (we want international signal).
- **Trustpilot/G2/Capterra** (enabled, summary mode): web-search for the
  current overall star rating and review count for each of:
  QuickBooks (Intuit), Xero, Sage, FreeAgent, MYOB, Wave, Zoho Books,
  Pennylane, FreshBooks, KashFlow. Snapshot only — no per-review scraping.
- **Twitter/X** (currently disabled): leave `voc.twitter_x = {enabled: false, posts: []}`
  until an API token is added to config.
- **LinkedIn** (currently manual_input): leave `voc.linkedin = {enabled: false, posts: []}`
  unless the user has dropped notes into a `manual_voc.json` file in the repo root.

Use Claude Haiku (`window.cowork.askClaude` if running in artifact, otherwise direct
inference) to classify each Reddit thread's sentiment. Aggregate into:

```
voc.summary.intuit_vs_peer_sentiment_delta = (intuit_positive_share - peer_positive_share)
```

## STEP 5 — Compute KPIs

```
competitor_signals     = len(signals)
tier1_signals          = count(signals where tier == "t1")
regulatory_changes     = len(changes)
urgent_mandates        = count(changes where urgent == true)
active_markets         = |unique({s.region} ∪ {c.country})|
cross_signals          = count(unique markets where comp + reg both moved)
```

## STEP 6 — Identify cross-signals

For each regulatory change, check whether any competitor signal in the same
country/region appeared this week. Build `cross_signals` list:
`[{country, competitor_event, regulatory_event, why_it_matters}]`.

## STEP 7 — Compute the Market Health Score

Run `scripts/health_score.py compute_score(...)` with this week's
competitors, regulatory, cross_signals, voc summary, intuit_moves[], fog[],
and `week_end=WEEK_END`. The function reads `config/health_score.json` for
all weights. Save the returned dict as `health_score`.

Compute `delta_vs_last_week` against the previous entry in
`docs/data/history.json`.

## STEP 8 — Append to history.json

Load `docs/data/history.json`. Append:

```json
{
  "week_end": "<WEEK_END>",
  "score": <number>,
  "headline": "<short headline>",
  "why_it_moved": "Score moved because: ...",
  "data_quality": "live",
  "kpis": { ... STEP 5 numbers ... }
}
```

Sort by week_end ASC and write back. The dashboard's 9-week sparkline reads
this file directly (also embedded in `super_digest.json` as `history`).

## STEP 9 — Generate the executive review

Write a 6–8 bullet synthesis as HTML. Lead with the **Health Score line**:

```html
<p><strong>Health Score: 5.7 / 10</strong> (▲ 0.3 vs last week — concise reason).</p>
```

Then continue with:
1. **Headline** — biggest move of the week.
2. **Competitor watch** — 2–3 bullets.
3. **Regulatory watch** — 1–2 bullets.
4. **VOC** — 1 bullet on what international customers are saying about
   Intuit vs peers.
5. **Cross-signals** — markets where both sides moved.
6. **What to do** — 1 bullet of recommended action.

## STEP 10 — Build super_digest.json

Write to `docs/data/super_digest.json` with the full new schema:

```json
{
  "generated_at": "<UTC ISO now>",
  "week_start": "...", "week_end": "...",
  "review": "<HTML>",
  "competitors": [...], "regulatory": [...], "cross_signals": [...],
  "voc": { ratings_snapshot, themes, summary, ... },
  "feet_on_the_ground": [],
  "intuit_moves": [],
  "health_score": { score, delta_vs_last_week, components, why_it_moved, ... },
  "history": [...latest 9 weeks from history.json...],
  "kpis": { ... }
}
```

Archive copy: `docs/data/history/super_digest_<WEEK_END>.json`.

## STEP 11 — Push to GitHub

```bash
cd ~/Documents/international-market-health
git add docs/data config
git commit -m "weekly super-digest <WEEK_END>"
git push
```

`gh auth login` was set up Q2 2026 so this should work non-interactively from
Jeremy's Mac.

## STEP 12 — Post combined exec digest to Slack

Read `exec_digest_slack_channel_id` from `config/dashboard.json`
(currently `C0B14UXEB8W` = #international_market_health). Use `slack_send_message`.

Format:

```
:satellite: *International Market Health — Exec Digest*
*Week of <WEEK_START> – <WEEK_END>*

:thermometer: *Market Health Score: <score> / 10* (<arrow> <abs(delta)> vs last week — <one-line why>)

> <One-sentence headline — the biggest single takeaway>

*KPIs*
:red_circle: <tier1> Tier-1 · :large_green_circle: <non_tier1> adjacent
:scroll: <reg_changes> reg · :warning: <urgent> urgent (<12mo)
:globe_with_meridians: <active_markets> markets · :link: <cross_signals> cross-signals
:speaking_head_in_silhouette: VOC: Intuit <intuit_avg_star>★ vs peer-set <peer_avg_star>★ avg

*This week's read*
• bullet 1
• bullet 2
• bullet 3
• bullet 4
• bullet 5

:bar_chart: Super dashboard: <https://jeremyfeit-spec.github.io/international-market-health/>
:satellite: Competitor detail: <#C0AMFGP11FH|international_weekly_competitor_overview>
:scroll: Regulatory detail: <#C0B1DJNS48H|international_weekly_regulatory_overview>
:speech_balloon: Reply with feedback — what should we be tracking that we're not?
```

Thread reply:
```
:robot_face: Auto-generated by super-digest-friday · pulls from market-pulse + regulatory-tracker + VOC · synthesis by Claude
```

## Success criteria

- `docs/data/super_digest.json` and `docs/data/history.json` updated
- Git push succeeded
- Combined exec digest posted with health-score line
- Thread reply posted

## Failure modes

- **Both source JSONs missing** → fall back to Slack channel scrape (see STEP 3).
- **One source JSON missing** → run with the one that's present, set missing
  to `[]`, note gap in review.
- **VOC fetch fails** → set `voc.summary.intuit_vs_peer_sentiment_delta = null`,
  the score function will skip the VOC component.
- **History.json missing** → bootstrap from `docs/data/history/super_digest_*.json` files.
