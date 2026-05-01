"""
Final super_digest.json for week 2026-05-01:
includes competitors, regulatory, cross_signals, voc, fog (empty),
health_score (current week), history (9-week trend), and the new
review HTML that incorporates the score and VOC.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO / "scripts"))
from health_score import compute_score

GENERATED_AT = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

current = json.load(open(REPO / "docs" / "data" / "super_digest.json"))
voc = json.load(open(REPO / "docs" / "data" / "voc_current_week.json"))
hist = json.load(open(REPO / "docs" / "data" / "history.json"))

# Recompute current-week score with VOC included
sc = compute_score(
    competitors=current["competitors"],
    regulatory=current["regulatory"],
    cross_signals=current.get("cross_signals", []),
    voc_summary={"intuit_vs_peer_sentiment_delta": voc["summary"]["intuit_vs_peer_sentiment_delta"]},
    intuit_moves=[],
    fog=[],
    week_end=current["week_end"],
)

# Find prior week from history.json
prior = next((w for w in reversed(hist["weeks"]) if w["week_end"] != current["week_end"]), None)
delta = round(sc["score"] - prior["score"], 1) if prior else 0.0

# Review HTML — product-team focus.
# Top section: ≤4 bullets the product team should act on this week.
# Collapsible "More context" section: secondary signals (marketing moves,
# adjacent peers, quiet markets) that round out the picture but aren't
# the priority for product planning.
review_html = (
    "<p><strong>Health Score: " + f"{sc['score']:.1f} / 10" + "</strong> "
    + (f"({'▼' if delta < 0 else '▲'} {abs(delta):.1f} vs last week — " if delta != 0 else "(flat — ")
    + "Sage Tier-1 M&amp;A, 8 regulatory deadlines in the 90-day hot zone, and a UK cross-signal stacking competitor + regulator on the same accountant base).</p>"
    "<p><strong>For the product team this week:</strong></p>"
    "<ul>"
    "<li><strong>Italy SDI v1.9.1 ships 15 May — 14 days out.</strong> Confirm QBO compliance backlog is on track for VAT-group and sports-worker updates. This is the closest hard deadline in any priority market.</li>"
    "<li><strong>Sage acquired Doyen AI — implementation speed becomes a competitive feature.</strong> Sage is now positioned to compress Intacct / Sage 200 go-lives from weeks to days in the same UK/EU/NA mid-market QBO Advanced is climbing into. Pressure-test our onboarding/data-migration narrative against this thesis before next QBR.</li>"
    "<li><strong>Canada paper drop-box closure (30 Apr) creates an immediate accountant-led migration moment.</strong> Every Canadian SMB without a digital workflow is now forced into one — short window to capture them. Worth a fast assist-channel push.</li>"
    "<li><strong>VOC: Intuit 4.4★ vs peer-set avg 4.43★ on Trustpilot UK.</strong> Negative themes clustering on 2026 price increases (UK charity 70% YoY) and the mandatory July payroll-tax-filing change. Sage and FreeAgent both 4.6★ — support reputation is the gap.</li>"
    "</ul>"
    "<details class=\"more-context\">"
    "<summary>More context — secondary signals &amp; quiet markets</summary>"
    "<ul>"
    "<li><strong>Vertex restructuring (9% headcount) toward agentic tax.</strong> Confirms the AI-as-packaging trend Sage's Doyen deal embodies. Avalara and Sovos likely to follow within the quarter.</li>"
    "<li><strong>Airwallex × Arsenal campaign (Spike Lee–directed, 2-min film).</strong> Largest brand spend in Airwallex's history, running through the PL run-in and 2026 World Cup. UK/EU B2B-tooling overlap with QBO Money/Bill Pay — track for share-of-voice impact, not immediate product action.</li>"
    "<li><strong>Other e-invoicing dates on the horizon:</strong> Australia Peppol target (1 Jul), France PDP→PA pilot (1 Sep), Spain AEAT draft (1 Oct). Five priority markets need product-side action this calendar year — sequence them now even though only Italy is &lt;30 days.</li>"
    "<li><strong>Cross-signals — UK is the loudest market this week.</strong> Sage M&amp;A and Airwallex Arsenal lead in UK alongside the UK confirming its 2029 B2B/B2G e-invoicing mandate. Three forces pulling on the same accountant base; second-order effect on partner attention.</li>"
    "<li><strong>Quiet markets:</strong> Germany and Spain saw regulatory motion only — no competitor moves. Watch DATEV and Holvi/Qonto for response in coming weeks.</li>"
    "</ul>"
    "</details>"
)

# Compose final payload
final = {
    "generated_at": GENERATED_AT,
    "week_start": current["week_start"],
    "week_end": current["week_end"],
    "review": review_html,
    "competitors": current["competitors"],
    "regulatory": current["regulatory"],
    "cross_signals": current.get("cross_signals", []),
    "voc": voc,
    "feet_on_the_ground": [],
    "intuit_moves": [],
    "health_score": {
        "score": sc["score"],
        "delta_vs_last_week": delta,
        "components": sc["components"],
        "explainers": sc["explainers"],
        "why_it_moved": "Score moved because: " + "; ".join(sc["explainers"]) if sc["explainers"] else "Quiet week — score holds at neutral baseline.",
        "scale_min": 0,
        "scale_max": 10,
        "neutral_baseline": 5.0,
        "config_version": "1.0.0",
    },
    "history": hist["weeks"],
    "kpis": {
        "competitor_signals": len(current["competitors"]),
        "tier1_signals": sum(1 for c in current["competitors"] if c.get("tier") == "t1"),
        "regulatory_changes": len(current["regulatory"]),
        "urgent_mandates": sum(1 for r in current["regulatory"] if r.get("urgent")),
        "active_markets": current["kpis"]["active_markets"],
        "cross_signals": current["kpis"]["cross_signals"],
    },
}

with open(REPO / "docs" / "data" / "super_digest.json", "w") as f:
    json.dump(final, f, indent=2, ensure_ascii=False)
with open(REPO / "docs" / "data" / "history" / f"super_digest_{current['week_end']}.json", "w") as f:
    json.dump(final, f, indent=2, ensure_ascii=False)

print("Wrote final super_digest.json")
print(f"  health score: {sc['score']:.1f} / 10  (delta {delta:+.1f})")
print(f"  history weeks: {len(final['history'])}")
print(f"  voc themes: {len(voc['themes'])}")
print(f"  voc platforms: {len(voc['ratings_by_platform'])}")
print(f"  voc overall: Intuit {voc['summary']['intuit_overall_stars']}★ vs peer-avg {voc['summary']['peer_set_avg_stars']}★ ({voc['summary']['intuit_vs_peer_sentiment_delta']:+.2f})")
