---
name: super-digest-friday
description: Weekly Friday 8:15am PT — combine market-pulse and regulatory-tracker outputs, generate executive synthesis, push to international-market-health GitHub Pages, post combined exec digest to Slack
---

You are running the **International Market Health** super-digest. This runs at
8:15 AM PT each Friday, **after** `market-pulse-friday-digest` (8:02) and
`regulatory-tracker-friday-digest` (8:03) have completed. Your job: synthesize
both feeds into one executive-grade view and ship it.

## STEP 1 — Establish the date window

Today is Friday. Reporting window = last 7 days (today − 7 → today). Compute
both ISO dates. Store as `WEEK_START` and `WEEK_END`.

## STEP 2 — Mount the super-dashboard repo

Use `request_cowork_directory` with path `~/Documents/international-market-health`.
This repo holds `docs/index.html` (the dashboard), `docs/data/super_digest.json`
(this week's payload), `docs/data/history/` (past weeks), and `config/dashboard.json`.

Read `config/dashboard.json` to load source URLs and the exec Slack channel ID.

## STEP 3 — Pull this week's data from both source dashboards

Both source jobs serialize their week's findings as JSON to GitHub Pages.

1. Fetch `https://jeremyfeit-spec.github.io/international_market_pulse/data/competitor_signals.json`
   - Expected shape: `{ generated_at, week_start, week_end, signals: [...] }`
   - Each signal: `{ company, region, tier, signal_type, headline, summary, source_url, source_label, date }`

2. Fetch `https://jeremyfeit-spec.github.io/regulatory-tracker/data/regulatory_changes.json`
   - Expected shape: `{ generated_at, changes: [...] }`
   - Each change: `{ country, iso, region, topic, title, summary, status, effective_date, source_url, urgent }`

If either fetch fails or the JSON is older than this Friday's window, re-read
the corresponding local data instead:
- Market Pulse: read the most recent Slack post in channel `C0AMFGP11FH` and
  parse the digest into the signal shape above.
- Regulatory Tracker: read `~/Documents/regulatory-tracker/history/diff_<TODAY>.json`
  and the affected `countries/<ISO>.json` files.

## STEP 4 — Compute KPIs

```
competitor_signals     = len(signals)
tier1_signals          = count(signals where tier == "t1")
regulatory_changes     = len(changes)
urgent_mandates        = count(changes where urgent == true)
active_markets         = |unique({s.region for s in signals} ∪ {c.country for c in changes})|
cross_signals          = count(changes where change.country or change.region appears in any signal.region/company)
```

## STEP 5 — Identify cross-signals (the "so what" magic)

For each regulatory change, check whether any competitor signal in the same
country/region appeared this week. Flag those as **cross-signals** — these are
the most strategically interesting items because something is happening on both
sides of the market in the same place.

Build a `cross_signals` list: `[{country, competitor_event, regulatory_event, why_it_matters}]`.

## STEP 6 — Generate the executive review

Write a 5–7 bullet synthesis. Tone: factual, sharp, internal-Intuit. No
marketing language. Each bullet ≤ 2 sentences. Lead with the highest-impact
items.

Structure:
1. **Headline** — the single biggest move of the week (competitor or regulator).
2. **Competitor watch** — top 2–3 competitor moves and what they signal about
   the market.
3. **Regulatory watch** — top 1–2 regulatory developments and what they force.
4. **Cross-signals** — any market where both sides moved this week.
5. **Quiet markets** — markets that were notably silent (only if relevant).
6. **What to do** — 1 bullet of recommended attention/action for the team.

Render as HTML (paragraphs + a single `<ul>` for the bullets) so the dashboard
can drop it straight into the page.

## STEP 7 — Build super_digest.json

Write to `docs/data/super_digest.json`:

```json
{
  "generated_at": "<UTC ISO now>",
  "week_start": "<WEEK_START>",
  "week_end": "<WEEK_END>",
  "review": "<HTML string from STEP 6>",
  "competitors": [<from STEP 3, pass-through>],
  "regulatory":  [<from STEP 3, pass-through>],
  "cross_signals": [<from STEP 5>],
  "kpis": { ... STEP 4 numbers ... }
}
```

Also archive a copy to `docs/data/history/super_digest_<WEEK_END>.json`.

## STEP 8 — Push to GitHub

```bash
cd ~/Documents/international-market-health
git add docs/data
git commit -m "weekly super-digest <WEEK_END>"
git push
```

If push fails (auth issue in sandbox), continue silently — note in final
report. Jeremy can push manually.

## STEP 9 — Post combined exec digest to Slack

Read the exec channel ID from `config/dashboard.json`
(`exec_digest_slack_channel_id`). Use Slack `slack_send_message`.

Format **exactly** like this:

```
:satellite: *International Market Health — Exec Digest*
*Week of <WEEK_START> – <WEEK_END>*

> <One-sentence headline — the biggest single takeaway of the week>

*KPIs*
:red_circle: <tier1_signals> Tier-1 competitor moves · :large_green_circle: <competitor_signals - tier1_signals> adjacent
:scroll: <regulatory_changes> regulatory changes · :warning: <urgent_mandates> urgent (<12mo)
:globe_with_meridians: <active_markets> markets active · :link: <cross_signals_count> cross-signals

*This week's read*
• <bullet 1 from review>
• <bullet 2 from review>
• <bullet 3 from review>
• <bullet 4 from review>
• <bullet 5 from review>

:bar_chart: Super dashboard: <https://jeremyfeit-spec.github.io/international-market-health/>
:satellite: Competitor detail: <#C0AMFGP11FH|international_weekly_competitor_overview>
:scroll: Regulatory detail: <#C0B1DJNS48H|international_weekly_regulatory_overview>
:speech_balloon: Reply with feedback — what should we be tracking that we're not?
```

**URL rule:** wrap bare URLs in angle brackets so Slack's parser terminates
links correctly. Never end a line with a bare URL when the next line starts
with `:`.

After posting, post a thread reply:

```
:robot_face: Auto-generated by super-digest-friday · pulls from market-pulse + regulatory-tracker · synthesis by Claude
```

## Success criteria

- `docs/data/super_digest.json` written with non-zero competitors+regs (or an
  explicit "quiet week" note if both sources came back empty)
- Git push succeeded (or noted as manual-push-needed)
- Combined exec digest posted to the configured Slack channel
- Thread reply posted
- All links in the Slack post resolve (test the dashboard URL)

## Failure modes

- **Both source JSONs missing** → wait 5 min and retry once. If still missing,
  post a Slack message saying "super-digest skipped — upstream feeds didn't
  publish; will retry next Friday" and stop.
- **One source JSON missing** → run with the one that's present, set the missing
  feed to `[]`, and note the gap in the exec review.
- **AI synthesis fails** → fall back to a templated review listing top items by
  category without commentary.
