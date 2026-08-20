# Competitor Gaps

A **gap** is a measured difference between what the audience demands and what the market supplies:

```text
        Audience demand                      Competitor coverage
 (pains, questions, topics, trends)   vs   (content, answers, offers)
                        ↓
                    GAP or NO GAP
```

Both sides must be measured. A "gap" derived only from demand data is a guess, and a "gap" derived only from competitor data is a content-calendar diff. This document defines how the two sides are joined, scored, and — most importantly — how the system avoids claiming absence of coverage it never actually looked for.

---

## 1. Gap types

| Type | Definition | Value | Risk |
|---|---|---|---|
| `silent` | Real demand, **zero** observed coverage across all competitors | Highest | Most likely to be a measurement artifact |
| `shallow` | Coverage exists but is thin, generic, or introductory relative to demand depth | High | Genuine and safe — the usual best bet |
| `stale` | Coverage exists but is ≥180 days old while demand is rising | High | Timing-dependent |
| `poorly_received` | Coverage exists and the audience responds badly (low engagement, critical comments) | High | Requires `data_quality: good` |
| `unanswered_question` | A specific recurring question none of them answers directly | High | Easiest to act on, easiest to verify |
| `format_gap` | Topic covered, but not in the format the audience asks for | Medium | Often the cheapest win |
| `segment_gap` | Covered for a different segment than the one asking | Medium | Requires reliable segment inference |
| `language_gap` | Covered in the market's language but not the audience's framing | Medium | Feeds directly from `audience-language.md` |
| `product_gap` | Demand for a capability nobody ships | Highest business value | Requires product-opportunity evidence thresholds |
| `deliberately_unserved` | Demand exists, nobody serves it, and business relevance is low | Negative | The trap this taxonomy exists to name |

`deliberately_unserved` is a first-class outcome. Sometimes an empty space is empty because it is worthless, and a system that can't say so will send its user into it.

---

## 2. Schema

```yaml
id: gap_01J8T9C4E6G8J1L3
type: competitor_gap
gap_type: unanswered_question
slug: minimal-app-without-library

topic: topic_tool_overwhelm
title: "Nobody answers: 'is there a mindfulness app without a whole library?'"

# --- demand side ---
audience_demand:
  demand_score: 74                  # 0–100, §3
  frequency: 9
  distinct_authors: 9
  trend: rising
  trend_score: 66
  intent: comparison
  intent_score: 85
  platforms: {reddit: 7, youtube: 2}
  platform_spread: 2
  evidence:
    - evidence_id: ev_01J8T1...
      url: "https://www.reddit.com/r/Mindfulness/comments/xxxxxx/"
      collected_at: 2026-08-09T12:00:00Z
      exact_phrasing: "anything minimal? every app is a whole library"
  source_insights:
    pains: [pain_01J8QZ...]
    questions: [q_01J8P2...]
    objections: [obj_01J8N5T2WQ4ZK9P1]

# --- supply side ---
competitor_coverage:
  market_coverage: 12               # 0–100, weighted max, competitors.md §5
  coverage_by_competitor:
    comp_example_calm:    {coverage_score: 8,  items_on_topic: 1, last_seen: 2025-11-02, depth: shallow, data_quality: good}
    comp_example_timer:   {coverage_score: 0,  items_on_topic: 0, last_seen: null,       depth: null,    data_quality: partial}
    comp_example_creator: {coverage_score: 22, items_on_topic: 3, last_seen: 2026-06-14, depth: shallow, data_quality: good}
  competitors_checked: [comp_example_calm, comp_example_timer, comp_example_creator]
  competitors_uncheckable: [comp_example_timer]     # surfaces unavailable → limits the claim
  items_examined: 214
  window: 2026-05-20 .. 2026-08-17
  coverage_evidence:
    - competitor: comp_example_calm
      url: "https://www.example-calm.com/blog/why-a-library-helps"
      note: "Argues the opposite position; does not address minimal alternatives."

# --- the diff ---
unanswered_questions: [q_01J8P2...]
underserved_audience: "Lapsed users choosing tools, who name library size as the reason for churn."
content_gap: "No direct comparison content framed around minimalism as the selection criterion."
product_gap: "Positioning space: the anti-library. Product implication only, not validated demand."

# --- scoring ---
opportunity_score: 81               # §4
score_components:
  demand: 74
  coverage_inverse: 88
  business_relevance: 92
  trend: 66
  addressability: 85
  evidence_quality: 70
confidence: 0.69
confidence_caps_applied: [partial_competitor_coverage]

# --- action ---
recommended_action: >
  Create a comparison piece using the audience's own selection criterion (library size as a cost,
  not a benefit). Verify manually that no major competitor published on this in the last 90 days
  before making any "nobody offers this" claim in public copy.
recommended_format: [article, short_video]
claims_requiring_verification:
  - "That no competitor offers a minimal alternative — verified only within collected data."

# --- four-way separation ---
observed_fact: >
  9 distinct authors asked for minimal alternatives in 21 days. Across 214 competitor items
  collected since 2026-05-20 from 3 competitors (1 with partial data), no item addresses the
  question directly; one argues the opposite position.
ai_interpretation: "The selection criterion in this audience has inverted — library size reads as cost."
hypothesis: "Positioning explicitly against library size would capture this demand."
recommendation: "Publish the comparison piece; hold the positioning claim until manual verification."

status: candidate
created_at: 2026-08-17T00:00:00Z
```

---

## 3. Demand score

```text
demand_score = 0.30 × frequency_score        # distinct-author-weighted, log-scaled
             + 0.25 × pain_severity_or_intent  # max(pain severity_score, intent_score)
             + 0.25 × trend_score
             + 0.20 × platform_spread_factor   # 100 × min(1, (spread − 1) / 2)
```

Floors: a gap cannot be created below `distinct_authors ≥ 5` and `demand_score ≥ 45`. Below that it is a note, not a gap.

---

## 4. Gap opportunity score

```text
raw = 0.28 × demand_score
    + 0.24 × (100 − market_coverage)
    + 0.22 × business_relevance
    + 0.14 × trend_score
    + 0.12 × addressability

opportunity_score = round( raw × evidence_multiplier × coverage_reliability )
```

Where:

| Multiplier | Value | When |
|---|---|---|
| `evidence_multiplier` | 1.00 | ≥8 distinct authors, ≥2 platforms |
| | 0.85 | 5–7 distinct authors or single platform |
| | 0.70 | any small-N or single-thread guard fired |
| `coverage_reliability` | 1.00 | all competitors `data_quality: good`, ≥100 items examined |
| | 0.85 | one competitor `partial` |
| | 0.70 | any competitor `unavailable`, or <50 items examined |
| | 0.55 | competitor data older than 60 days |

Bands: `0–39` ignore · `40–59` watchlist · `60–74` worth doing · `75–100` priority.

**Business relevance is the veto.** If `business_relevance < 30`, the gap is reclassified `deliberately_unserved` regardless of score and reported under "what NOT to create".

---

## 5. The absence problem (the hard part)

Claiming "nobody covers this" requires proving a negative from incomplete data. The system handles it with four mechanisms:

1. **Scoped claims only.** Every absence statement is scoped to what was examined: *"no coverage found in 214 items from 3 competitors collected since 2026-05-20"*. Never *"no one covers this"*.
2. **Uncheckable surfaces are named.** `competitors_uncheckable[]` appears in the report. If a competitor's blog has no feed, that is stated, not silently treated as zero.
3. **Confidence caps.** Any `unavailable` surface caps gap confidence at 0.65; two or more caps it at 0.55, which keeps it out of "priority".
4. **Manual verification flag.** `silent` and `unanswered_question` gaps always carry `claims_requiring_verification`, and the Content Engine may not publish an absence claim until a human clears it. One search takes thirty seconds; a wrong public claim costs more.

Additional guard: a `silent` gap where `items_examined < 50` for the relevant competitor set is downgraded to `insufficient_coverage_data` and reported as "unknown", not as a gap.

---

## 6. Detection workflow

```text
weekly, after clustering and trend detection:

for each topic with demand_score >= 45:
    supply = coverage_map[topic]                      # from competitors.md
    if supply.market_coverage == 0 and supply.items_examined >= 50:  → silent
    elif topic has questions with no direct/partial competitor answer: → unanswered_question
    elif supply.depth == shallow and demand depth == high:            → shallow
    elif supply.last_seen older than 180d and trend in (rising, emerging): → stale
    elif supply.performance_index < 25 and data_quality == good:      → poorly_received
    elif requested_format not in supply.formats:                      → format_gap
    elif supply.segment != demand.segment:                            → segment_gap
    else: no gap

then:
    score → apply multipliers → apply business_relevance veto → dedup against open gaps → queue for review
```

Gaps are deduped against the previous 8 weeks: an existing gap is updated (frequency, evidence, score history), never duplicated. A gap that has been acted on is marked `addressed_by: <content_id>` and moves to `archived` after 60 days without new demand.

---

## 7. Reporting rules

1. Every gap shows **both** sides: demand evidence and coverage evidence. A gap with one side missing is not reported.
2. Coverage claims carry the examination window and item count.
3. `confidence_caps_applied[]` is always visible — the reason a score was held down is as informative as the score.
4. Competitor names appear in internal reports; in any externally-facing export, comparative claims are stripped unless `data_quality: good` on both sides and a human has cleared them.
5. `deliberately_unserved` items appear in the radar's "what NOT to create" section, with the reason.
