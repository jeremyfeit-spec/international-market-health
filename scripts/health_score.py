"""
Deterministic, auditable Market Health Score (0–10).

Run the same function for the current week and for each backfilled week.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import date

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "health_score.json"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def _bounded_sum(values: list[float], cap: float | None) -> float:
    """Sum values, then clamp the result to (cap, 0) for negatives or (0, cap) for positives."""
    total = sum(values)
    if cap is None:
        return total
    if cap < 0:
        return max(total, cap)
    return min(total, cap)


def compute_score(
    competitors: list[dict],
    regulatory: list[dict],
    cross_signals: list[dict],
    voc_summary: dict | None = None,
    intuit_moves: list[dict] | None = None,
    fog: list[dict] | None = None,
    week_end: str | None = None,
) -> dict:
    """
    Returns: {
      score: 5.7,
      components: {competitor_pressure: -0.6, regulatory_pressure: -0.6, ...},
      explainers: ["3 Tier-1 competitor moves in priority markets", ...],
      why_it_moved: ""  (filled in by caller from explainers)
    }
    """
    cfg = load_config()
    priority = set(cfg["priority_markets"])
    comp_w = cfg["components"]["competitor_pressure"]
    reg_w = cfg["components"]["regulatory_pressure"]
    cross_w = cfg["components"]["cross_signal_magnifier"]
    voc_w = cfg["components"]["voc_sentiment"]
    intuit_w = cfg["components"]["intuit_offensive_moves"]
    fog_w = cfg["components"]["feet_on_the_ground"]

    score = float(cfg["scale"]["neutral_baseline"])
    explainers: list[str] = []

    # --- Competitor pressure ---
    comp_values: list[float] = []
    tier1_priority = 0
    for s in competitors or []:
        tier = s.get("tier", "t3")
        # Region can be "UK / Global", "Global", "France" etc. We treat priority as "any priority country/region keyword present".
        region_blob = (s.get("region", "") or "").lower()
        is_priority = any(
            iso.lower() in region_blob
            or _country_for_iso(iso).lower() in region_blob
            for iso in priority
        ) or "global" in region_blob
        if tier == "t1":
            comp_values.append(comp_w["tier1_in_priority_market"] if is_priority else comp_w["non_priority_market"])
            if is_priority:
                tier1_priority += 1
        elif tier == "t2":
            comp_values.append(comp_w["tier2_in_priority_market"] if is_priority else comp_w["non_priority_market"])
        else:
            comp_values.append(comp_w["tier3_in_priority_market"] if is_priority else comp_w["non_priority_market"])
    comp_total = _bounded_sum(comp_values, comp_w["max_total"])
    score += comp_total
    if tier1_priority:
        explainers.append(f"{tier1_priority} Tier-1 competitor move{'s' if tier1_priority != 1 else ''} in priority markets")

    # --- Regulatory pressure ---
    reg_values: list[float] = []
    urgent_90 = 0
    for c in regulatory or []:
        if not c.get("urgent"):
            reg_values.append(reg_w["non_urgent"])
            continue
        eff = c.get("effective_date")
        if eff and week_end:
            days = (date.fromisoformat(eff) - date.fromisoformat(week_end)).days
            # "Hot zone" = recently went live (last 30d) OR going live within next 90d.
            if -30 <= days <= 90:
                reg_values.append(reg_w["urgent_within_90_days"])
                urgent_90 += 1
            elif -365 <= days <= 365:
                reg_values.append(reg_w["urgent_within_12_months"])
            else:
                reg_values.append(reg_w["non_urgent"])
        else:
            reg_values.append(reg_w["urgent_within_12_months"])
    reg_total = _bounded_sum(reg_values, reg_w["max_total"])
    score += reg_total
    if urgent_90:
        explainers.append(f"{urgent_90} regulatory deadline{'s' if urgent_90 != 1 else ''} within 90 days")

    # --- Cross-signal magnifier ---
    cross_unique_markets = len({cs.get("country") for cs in (cross_signals or []) if cs.get("country")})
    cross_total = _bounded_sum([cross_w["per_market"]] * cross_unique_markets, cross_w["max_total"])
    score += cross_total
    if cross_unique_markets:
        explainers.append(f"competitor + regulator both moved in {cross_unique_markets} market{'s' if cross_unique_markets != 1 else ''}")

    # --- VOC sentiment ---
    voc_total = 0.0
    if voc_summary and voc_summary.get("intuit_vs_peer_sentiment_delta") is not None:
        delta = voc_summary["intuit_vs_peer_sentiment_delta"]
        if delta >= 0.05:
            voc_total = voc_w["intuit_positive_above_peers"]
            explainers.append(f"VOC tilting Intuit-positive vs peers (+{delta:.2f})")
        elif delta <= -0.05:
            voc_total = voc_w["intuit_negative_above_peers"]
            explainers.append(f"VOC tilting Intuit-negative vs peers ({delta:+.2f})")
    score += voc_total

    # --- Intuit offensive moves ---
    intuit_values: list[float] = []
    for m in intuit_moves or []:
        if m.get("tier") == "t1":
            intuit_values.append(intuit_w["tier1_intuit_announcement"])
        elif m.get("tier") == "t2":
            intuit_values.append(intuit_w["tier2_intuit_announcement"])
    intuit_total = _bounded_sum(intuit_values, intuit_w["max_total"])
    if intuit_total:
        explainers.append(f"Intuit shipped/announced ({len(intuit_moves)} move{'s' if len(intuit_moves) != 1 else ''})")
    score += intuit_total

    # --- Feet on the ground ---
    fog_total = 0.0
    if fog:
        pos = sum(1 for f in fog if f.get("direction") == "positive")
        neg = sum(1 for f in fog if f.get("direction") == "negative")
        fog_total = _bounded_sum(
            [fog_w["positive_signal"]] * pos + [fog_w["negative_signal"]] * neg,
            None,
        )
        fog_total = max(fog_w["max_total_negative"], min(fog_w["max_total_positive"], fog_total))
        if fog_total:
            explainers.append(f"FOG net signal ({pos} positive / {neg} negative)")
    score += fog_total

    # Clamp + round
    score = max(0.0, min(10.0, score))
    score = round(score, 1)

    return {
        "score": score,
        "components": {
            "competitor_pressure": round(comp_total, 2),
            "regulatory_pressure": round(reg_total, 2),
            "cross_signal_magnifier": round(cross_total, 2),
            "voc_sentiment": round(voc_total, 2),
            "intuit_offensive_moves": round(intuit_total, 2),
            "feet_on_the_ground": round(fog_total, 2),
        },
        "explainers": explainers,
    }


_ISO_TO_COUNTRY = {
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "ES": "Spain",
    "IT": "Italy",
    "CA": "Canada",
    "MX": "Mexico",
    "BR": "Brazil",
    "IN": "India",
    "AU": "Australia",
    "SG": "Singapore",
    "ZA": "South Africa",
}


def _country_for_iso(iso: str) -> str:
    return _ISO_TO_COUNTRY.get(iso, iso)
