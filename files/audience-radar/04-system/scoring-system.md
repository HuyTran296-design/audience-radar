# Scoring System

**This file is canonical.** Where any other document shows a formula, threshold, or band, the version here governs.

## 0. Principles

1. **All scores are integers 0–100**, reported in bands. Two-decimal precision on an LLM-derived estimate is a lie about accuracy.
2. **Confidence is 0.00–1.00**, separate from every other score, and never blended into them silently.
3. **Scoring is pure code.** No scoring function calls an LLM. LLMs supply rubric-anchored *component ratings* (0–100) as inputs; composition, weighting, and thresholds are deterministic and unit-tested.
4. **Every score is explainable.** Every stored score carries its component breakdown. A score without components is a bug.
5. **Evidence weakness reduces scores multiplicatively**, never additively — weak evidence should suppress a strong topic, not merely nudge it.
6. **Floors before formulas.** Below the evidence floor, no score is produced at all.

**Universal bands**

| Band | Range |
|---|---|
| low | 0–24 |
| moderate | 25–49 |
| high | 50–74 |
| critical / exceptional | 75–100 |

**Confidence bands:** `low <0.50` · `medium 0.50–0.74` · `high ≥0.75`.

**Rounding:** compute in float, round half-up to integer at the end. Never round intermediate components.

---

## 1. Shared helpers

```python
def clamp(x, lo=0, hi=100): return max(lo, min(hi, x))

def log_scale(n, saturation):
    """0–100, saturating. The 4th occurrence matters far more than the 40th."""
    if n <= 0: return 0
    return 100 * min(1.0, math.log1p(n) / math.log1p(saturation))

def band(score):
    return ("low" if score < 25 else "moderate" if score < 50
            else "high" if score < 75 else "critical")
```

---

## 2. Relevance Score

**Range** 0–100. **Purpose:** should this item enter the intelligence pipeline?

Three stages; the first decisive stage wins.

### Stage 1 — rules (free)
Immediate reject (score 0, `stage: rules`) if any:
- matches `exclusion_keywords` / `exclusion_patterns`
- <15 words after cleaning
- bot/automod signature, or `author.is_likely_bot`
- older than `max_age_days`
- matches an `audience.not_our_audience` term
- authored by a tracked creator/competitor (→ competitor pipeline instead)

### Stage 2 — embedding (≈free)
```text
embedding_score = 100 × (
      0.55 × cos(item, audience_profile_embedding)
    + 0.30 × max over target_topics of cos(item, topic_embedding)
    + 0.15 × source_prior
)
source_prior: critical 1.0 · high 0.85 · medium 0.7 · low 0.55

+5  if it contains a first-person problem marker ("I can't", "my", "keeps happening")
+5  if it contains a question directed at others
−10 if it is promotional (link-heavy, CTA-heavy, giveaway markers)
```
Cosine is rescaled from its practical range (0.15–0.85) to 0–1 before weighting; raw cosine compresses everything into 0.3–0.6 and destroys resolution.

Routing: `≥70` accept · `<40` reject · `40–69` → stage 3.

### Stage 3 — Relevance Agent (cheap LLM, batched)
Returns 0–100. Final score = `round(0.4 × embedding_score + 0.6 × llm_score)`.

**Threshold:** `min_relevance_score` per source (default 50).
**Human review:** weekly stratified audit of 30 items across bands. False positives >30% → raise thresholds before touching prompts.

---

## 3. Pain Score

**Range** 0–100. Composed of severity and prevalence, kept separate because they answer different questions.

```text
severity_score = 0.35 × impact              # LLM rubric 0–100
               + 0.25 × emotional_intensity # lexical, computed in code
               + 0.20 × persistence         # recurring vs one-off (rubric)
               + 0.20 × workaround_cost     # effort spent working around it (rubric)
```

**Impact rubric (anchored — the anchors are what keep this stable across items):**
| Score | Anchor |
|---|---|
| 90–100 | Causes abandonment of the category entirely |
| 70–89 | Blocks the primary goal; user gives up on the attempt |
| 50–69 | Significant friction; needs a workaround every time |
| 30–49 | Noticeable annoyance, tolerated |
| 10–29 | Minor, mentioned in passing |
| 0–9 | Not really a problem |

**Emotional intensity (code, not sentiment analysis):**
```text
intensity = clamp(
    12 × count(intensity_markers)      # "really", "so", "constantly", "every single"
  + 18 × count(frustration_markers)    # "hate", "sick of", "gave up", "why does"
  +  8 × count(emphasis)               # caps runs, repeated punctuation
  + 25 × has_abandonment_language      # "deleted it", "stopped using", "not worth"
)
```
Markers are stored as evidence — the phrases that produced the score are inspectable.

**Pain Score for ranking:**
```text
pain_score = round(0.6 × severity_score + 0.4 × frequency_score)
```

**Floor:** no PainPoint reaches `candidate` below 3 distinct authors and 2 platforms.
**Human review:** any `critical` severity, and any pain whose severity is `high`+ with confidence <0.6.

---

## 4. Frequency Score

**Range** 0–100. Measures prevalence, deliberately saturating.

```text
weighted_frequency = Σ over authors of min(contributions_by_author, 3)

frequency_score = round(
      0.60 × log_scale(distinct_authors, 25)
    + 0.25 × log_scale(weighted_frequency, 60)
    + 0.15 × platform_spread_factor            # 100 × min(1, (platforms − 1) / 2)
)
```

Why `distinct_authors` dominates: 30 comments from 3 people is a conversation; 30 comments from 30 people is a market. Saturation at 25 authors means the difference between 25 and 200 is small — by then the point is made.

| distinct_authors | 1 | 3 | 5 | 10 | 25 | 100 |
|---|---|---|---|---|---|---|
| log component | 21 | 43 | 55 | 74 | 100 | 100 |

**Floor:** <3 distinct authors → no score, no insight promotion.
**Guards:** `author_concentration > 0.5` → ×0.8. `single_thread_share > 0.6` → ×0.75.

---

## 5. Trend Score

Per `02-insights/emerging-topics.md §4`, restated as canonical:

```text
trend_score = clamp(
      35 × min(1, growth_rate / 1.0)
    + 25 × min(1, max(0, z_score) / 3.0)
    + 20 × min(1, max(0, acceleration) / max(1, 0.5 × baseline_mean))
    + 10 × min(1, (platform_spread − 1) / 2)
    + 10 × min(1, sustained_weeks / 3)
) × confidence_multiplier
```
`confidence_multiplier`: `1.0` no guards · `0.75` one guard · `0.5` two or more.
`saturated` topics are capped at 40. `insufficient_baseline` / `data_incomplete` produce no trend score at all (null, not zero — a null is honest, a zero is a claim).

**Human review:** every `emerging` classification, weekly. This is the classification most likely to be wrong and most likely to be acted on.

---

## 6. Intent Score

**Range** 0–100. How close is this person to acting?

```text
base by intent:
  purchase_intent 100 · comparison 85 · commercial 75 · implementation 70
  troubleshooting 65 · educational 50 · informational 40 · opinion 25

modifiers:
  +10  explicit timing ("this week", "today", "right now")
  +10  explicit budget/spend mention
  +5   names specific products (evaluation in progress)
  −10  hypothetical framing ("someday", "if I ever")
  −15  is_rhetorical

intent_score = clamp(base + modifiers) × intent_confidence_factor
intent_confidence_factor = 0.7 + 0.3 × intent_confidence
```

Aggregate for an insight: the **distinct-author-weighted mean** of contributing items' intent scores — one enthusiastic buyer must not lift the average of forty browsers.

---

## 7. Competition Score

**Range** 0–100, where **higher = more saturated = worse**.

```text
market_coverage = weighted_max over competitors of coverage_score
  weights: direct 1.0 · content_only 0.9 · aspirational 0.8 · adjacent 0.7 · substitute 0.5

coverage_score (per competitor, per topic) =
      0.35 × log_scale(items_on_topic, 8)
    + 0.25 × depth_percentile          # within that competitor's own catalogue
    + 0.25 × recency_component         # ≤30d:100 · ≤90d:70 · ≤180d:40 · ≤365d:10 · else 0
    + 0.15 × directness                # share of items where the topic is primary

competition_score = round(market_coverage × coverage_reliability_penalty)
coverage_reliability_penalty:
  1.00 all good, ≥100 items examined
  0.85 one competitor partial
  0.70 any unavailable, or <50 items examined
  0.55 competitor data >60 days old
```

The penalty direction is deliberate: **when coverage data is unreliable, competition is scored lower, which raises opportunity scores — so unreliability is separately punished via the opportunity-level `coverage_reliability` multiplier and a confidence cap.** Never let missing competitor data silently manufacture an opportunity.

---

## 8. Opportunity Score

**Range** 0–100. The system's headline number.

```text
base = 0.22 × pain_score
     + 0.16 × frequency_score
     + 0.16 × trend_score            (0 if null)
     + 0.14 × intent_score
     + 0.18 × business_relevance
     + 0.14 × content_gap_score      (100 − competition_score)

opportunity_score = round(
      base
    × evidence_multiplier
    × (1 − 0.30 × competition_score / 100)
    × (0.7 + 0.3 × confidence)
)
```

| `evidence_multiplier` | Condition |
|---|---|
| 1.00 | ≥8 distinct authors AND ≥2 platforms |
| 0.85 | 5–7 distinct authors OR single platform |
| 0.70 | 3–4 distinct authors |
| — | <3 → no opportunity created |

**Business relevance (0–100)** — from `config/business.yaml`: what the user sells, to whom, what they will never sell. Computed as `100 × max cosine(topic, business_focus_embeddings)` rescaled, with human override per topic (overrides persist and are respected forever; this is where the user's judgement enters the ranking permanently).

**Vetoes (applied after scoring):**
1. `business_relevance < 30` → cap 39, route to "what NOT to create"
2. `confidence < 0.5` → cap 49, watchlist only
3. Guardrail conflict → `blocked: true`, excluded from export
4. Acted on within 60 days → suppressed unless `trend_score ≥ 70`

**Bands:** `0–39` ignore · `40–59` watchlist · `60–74` worth doing · `75–100` priority.

**Calibration note:** with the ×0.7–1.0 confidence multiplier and the competition penalty, scores above 85 should be rare — a few per quarter. If most weeks produce multiple 90s, the inputs are inflated and the components must be audited against the anchors.

---

## 9. Confidence Score

**Range** 0.00–1.00. How much should anyone believe this insight?

```text
confidence =
      0.25 × evidence_volume        # log_scale(distinct_authors, 20) / 100
    + 0.20 × platform_diversity     # 1 platform 0.4 · 2 → 0.75 · 3+ → 1.0
    + 0.20 × temporal_spread        # min(1, detection_span_days / 30)
    + 0.15 × extraction_agreement   # share of contributing items agreeing on the claim
    + 0.10 × source_quality         # mean relevance score of evidence / 100
    + 0.10 × (1 − author_concentration)

penalties (multiplicative):
  × 0.85  single-thread share > 0.5
  × 0.85  any contradicting evidence unresolved
  × 0.90  evidence_expired on >30% of evidence
  × 0.80  derived from partial/unavailable competitor data (gaps only)

caps:
  ≤ 0.80  for any inferred field (underlying concerns, motives)
  ≤ 0.60  when any trend guard fired
  ≤ 0.95  ever — the system is never more than 95% sure of anything it inferred
```

**Human review is REQUIRED when:**

| Condition | Why |
|---|---|
| confidence < 0.5 and the insight would be reported | Below the belief threshold |
| severity `critical` or opportunity band `priority` | High-consequence outputs |
| product/feature opportunity at any score | Expensive to be wrong |
| any `silent` competitor gap | Absence claims are the most falsifiable |
| a merge in the 0.80–0.88 similarity band | Irreversible damage to trend history |
| confidence ≥0.9 with <5 distinct authors | Almost certainly miscalibrated |
| an insight contradicting a trusted insight | Conflicts are shown, never auto-resolved |

---

## 10. Component summary

| Score | Range | Primary inputs | Floor | Review trigger |
|---|---|---|---|---|
| Relevance | 0–100 | rules, embeddings, LLM | — | weekly audit n=30 |
| Pain | 0–100 | severity × frequency | 3 authors, 2 platforms | critical severity |
| Frequency | 0–100 | distinct authors (log) | 3 authors | concentration >0.5 |
| Trend | 0–100 | growth, z, acceleration | 5 mentions, 4 authors | every `emerging` |
| Intent | 0–100 | intent class + modifiers | — | purchase_intent claims |
| Competition | 0–100 | competitor coverage | 50 items examined | data_quality < good |
| Opportunity | 0–100 | weighted composite | 3 authors | band `priority` |
| Confidence | 0.00–1.00 | evidence properties | — | <0.5 or ≥0.9 with thin evidence |

## 11. Avoiding fake precision

- Report bands in prose; keep integers in data.
- Never display a percentage on a base <5, in any output, ever.
- Always show the window with any frequency ("27 in 30 days", never "27").
- Show `n` alongside every rate.
- When a guard fires, say which one, in the report body.
- When confidence <0.5, the word "watchlist" replaces any recommendation verb.
- Never write "significant" unless a stated test was applied; the system applies none, so the word is banned from generated prose.
