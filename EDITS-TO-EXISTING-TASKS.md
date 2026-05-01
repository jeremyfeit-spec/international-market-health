# One-time edits to your two existing Friday tasks

The super-dashboard pulls from two JSON files that don't yet exist on your
source dashboards. Add the steps below to each existing scheduled task — once
those land, super-digest-friday becomes fully self-driving every Friday.

You can apply these in two ways:
1. Open each task's `SKILL.md` and edit it directly (path shown in `list_scheduled_tasks`).
2. Or just say to me "apply the super-dashboard edits to my existing tasks" and I'll do it.

---

## A) `market-pulse-friday-digest` — add a STEP 6.5 (serialize JSON) and update STEP 6 footer

**Add a new STEP 6.5 between current STEP 6 and STEP 7:**

```markdown
### STEP 6.5 — Serialize the digest as JSON for the super-dashboard

Before posting to Slack, also serialize the same set of selected signals to
`~/Documents/international_market_pulse/docs/data/competitor_signals.json` so
the super-dashboard can pull them.

Schema:

{
  "generated_at": "<UTC ISO now>",
  "week_start":   "<START_DATE>",
  "week_end":     "<END_DATE>",
  "signals": [
    {
      "company":       "<Company name>",
      "region":        "<EU | UK | APAC | LatAm | Middle East | Global>",
      "tier":          "<t1 | t2 | t3>",   // map :red_circle:→t1, :large_green_circle:→t2, :large_yellow_circle:→t3
      "signal_type":   "<funding | acquisition | product launch | partnership | leadership | regulatory approval | market entry | other>",
      "headline":      "<short headline if separate from company>",
      "summary":       "<one-sentence factual summary, same as Slack post>",
      "source_url":    "<URL>",
      "source_label":  "<TechCrunch | FT | Reuters | etc.>",
      "date":          "<YYYY-MM-DD>"
    }
  ]
}

After writing the JSON:

cd ~/Documents/international_market_pulse
git add docs/data/competitor_signals.json
git commit -m "weekly signals <END_DATE>" && git push || true
```

**And update the Slack footer in STEP 6:** add a third line to the bottom of
the digest just above the feedback line:

```
:globe_with_meridians: Super dashboard: <https://jeremyfeit-spec.github.io/international-market-health/>
```

So the footer block becomes:

```
*[N] signals · All from [START_DATE] – [END_DATE] · Next digest Fri [NEXT_FRIDAY_DATE], 8am PT*
:bar_chart: Dashboard: <https://jeremyfeit-spec.github.io/international_market_pulse/>
:globe_with_meridians: Super dashboard: <https://jeremyfeit-spec.github.io/international-market-health/>
:speech_balloon: Reply with feedback — what should we add, drop, or track differently?
```

---

## B) `regulatory-tracker-friday-digest` — add a serialize step and update Slack footer

**Add a new step between "Update last_synced" and "Rebuild dashboard data + push to GitHub":**

```markdown
### Serialize the week's diff as JSON for the super-dashboard

Write `~/Documents/regulatory-tracker/docs/data/regulatory_changes.json`:

{
  "generated_at": "<UTC ISO now>",
  "week_start":   "<TODAY - 7d>",
  "week_end":     "<TODAY>",
  "changes": [
    {
      "country":        "<Country name>",
      "iso":            "<ISO2>",
      "region":         "<EU | UK | APAC | LatAm | Middle East | Africa | Global>",
      "topic":          "<Tax Filing | VAT/GST | E-Invoicing | Payroll | Local GAAP | Banking & Payments>",
      "title":          "<entry.title>",
      "summary":        "<entry.summary>",
      "status":         "<live | upcoming | in_progress | monitoring | repealed>",
      "effective_date": "<YYYY-MM-DD or 'TBD' or 'YYYY-Qn'>",
      "source_url":     "<entry.source>",
      "urgent":         <true if country ∈ {GB,DE,FR,ES,IT,CA,MX,BR,IN,AU,SG,ZA} AND status==upcoming AND effective_date within 12mo, else false>
    }
  ]
}

The set is the union of `new_changes` and `updated_changes` for this week.
This file is included in the same `docs/` git push that already happens in the
next step — no extra push needed.
```

**Update the Slack footer:** add a single line right above the dashboard
footer in the message body:

```
:globe_with_meridians: Super dashboard (combined view): https://jeremyfeit-spec.github.io/international-market-health/
```

---

## C) Push the new repo

```bash
cd /sessions/eager-sweet-turing/mnt/outputs/international-market-health
git init -b main
git add .
git commit -m "init super dashboard"

# Create empty repo on GitHub: https://github.com/new
#   Name: international-market-health
#   Public, no README/license/gitignore

git remote add origin git@github.com:jeremyfeit-spec/international-market-health.git
git push -u origin main

# Settings → Pages → Source: Deploy from branch → Branch: main / docs
```

After GitHub Pages enables (1–2 min), the dashboard is live at:
`https://jeremyfeit-spec.github.io/international-market-health/`

Until the first Friday run (or until you complete edits A and B), the page
shows the seed message + falls back to live-pulling from the source dashboards
where it can.

---

## Timeline summary

| Friday step  | What happens                                                              |
|--------------|---------------------------------------------------------------------------|
| 8:02 AM PT   | `market-pulse-friday-digest` runs → posts to #competitor channel + writes `competitor_signals.json` |
| 8:03 AM PT   | `regulatory-tracker-friday-digest` runs → posts to #regulatory channel + writes `regulatory_changes.json` |
| 8:21 AM PT   | `super-digest-friday` runs → reads both JSONs → AI synthesis → writes `super_digest.json` → DMs you the exec digest |
