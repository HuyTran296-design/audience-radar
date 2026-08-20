# Product Opportunities

Content opportunities are cheap to act on and cheap to be wrong about. Product opportunities are not: they consume roadmap, money, and months. This document therefore sets **hard evidence thresholds enforced in code**, not guidance.

The rule the system exists to enforce: **the system may never say "people want this" on the strength of a few posts.**

---

## 1. Opportunity classes

| Class | Definition | Typical cost to act | Evidence bar |
|---|---|---|---|
| `content_opportunity` | Make something that explains, entertains, or persuades | hours | Low (see `content-opportunities.md`) |
| `feature_opportunity` | Change or add to an existing product | days–weeks | High |
| `product_opportunity` | Build a new product | months | Very high |
| `service_opportunity` | Offer human-delivered work | days | Medium |
| `offer_opportunity` | Repackage, reprice, or rebundle what exists | hours–days | Medium |

Misclassification is the most common error: a `feature_opportunity` dressed as a `product_opportunity` inflates perceived risk; an `offer_opportunity` dressed as a `feature_opportunity` sends engineering after a pricing problem. The classifier must justify its choice in `classification_rationale`.

---

## 2. Evidence thresholds (hard gates)

No record of a given class may reach `candidate` unless **all** conditions hold.

| Requirement | content | offer | service | feature | product |
|---|---|---|---|---|---|
| Distinct conversations | ≥3 | ≥8 | ≥8 | ≥12 | ≥20 |
| **Distinct authors** | ≥3 | ≥6 | ≥6 | ≥8 | ≥15 |
| Distinct platforms | ≥1 | ≥2 | ≥2 | ≥2 | ≥3 |
| Time span of evidence | ≥7 d | ≥14 d | ≥14 d | ≥21 d | ≥45 d |
| Author concentration | <0.60 | <0.50 | <0.50 | <0.40 | <0.35 |
| Single-thread share | <0.70 | <0.50 | <0.50 | <0.40 | <0.30 |
| Insight confidence | ≥0.50 | ≥0.60 | ≥0.60 | ≥0.65 | ≥0.70 |
| Willingness-to-pay signals | — | ≥2 | ≥2 | ≥3 | ≥5 |
| Substitute analysis present | — | ✅ | ✅ | ✅ | ✅ |
| Human review before `trusted` | ✅ | ✅ | ✅ | ✅ | ✅ + second reviewer |

Notes:
- **Time span matters as much as count.** 20 conversations in 48 hours is one event; 20 across 45 days is a pattern. This is why `detection_span_days` is a gate and not a nice-to-have.
- **Willingness-to-pay signals** are statements about money or effort: current spend, refusal to pay, workaround cost, "I'd pay for", "I already pay for X but". Each is stored as evidence with the exact phrasing.
- **Substitute analysis** is mandatory above content class: what are they using instead *right now*? If the answer is "nothing", the problem may not be painful enough to act on — the most useful and most ignored signal in demand discovery.

Below threshold, the record still exists — as `signal`, visible in an appendix, accumulating evidence. Signals that cross a threshold are promoted automatically to `candidate` and surface in the radar. This is the mechanism that lets weak ideas mature honestly instead of being either discarded or overclaimed.

---

## 3. Schema

```yaml
id: prod_01J8W3K5N7Q9S1U3
type: feature_opportunity
class_confidence: 0.74
classification_rationale: >
  Requested capability modifies an existing product surface (scheduling), does not
  require a new distribution or business model, and is described as a change to
  something users already have. Feature, not product.

title: "Cue variation to prevent reminder habituation"
slug: cue-variation
summary: >
  Recurring demand for reminders whose sound, timing, or wording changes so the cue
  stays noticeable beyond the first week.

# --- demand evidence ---
evidence_summary:
  distinct_conversations: 19
  distinct_authors: 16
  platforms: {reddit: 12, youtube: 6, forum: 1}
  platform_count: 3
  first_evidence: 2026-06-14
  last_evidence: 2026-08-16
  detection_span_days: 63
  author_concentration: 0.19
  single_thread_share: 0.21
  confidence: 0.72
thresholds_met:
  conversations: {required: 12, actual: 19, pass: true}
  authors: {required: 8, actual: 16, pass: true}
  platforms: {required: 2, actual: 3, pass: true}
  span_days: {required: 21, actual: 63, pass: true}
  concentration: {required: "<0.40", actual: 0.19, pass: true}
  wtp_signals: {required: 3, actual: 4, pass: true}
  confidence: {required: 0.65, actual: 0.72, pass: true}
gate_status: passed                    # passed | failed | signal_only

evidence:
  - evidence_id: ev_01J8K3...
    url: "https://www.reddit.com/r/Mindfulness/comments/xxxxxx/"
    collected_at: 2026-08-02T09:14:00Z
    exact_phrasing: "wish the sound changed so I'd actually notice it"
    signal_type: capability_request
  - evidence_id: ev_01J8W1...
    exact_phrasing: "I rotate three different alarm apps to keep noticing"
    signal_type: workaround
willingness_to_pay_signals:
  - type: current_spend
    detail: "Author reports paying for a timer app solely for varied alerts."
    evidence_id: ev_01J8W2...
  - type: workaround_cost
    detail: "Author maintains three apps to achieve the same effect."
    evidence_id: ev_01J8W1...
  - type: refusal
    detail: "Author says they would not pay a subscription for this alone."
    evidence_id: ev_01J8W4...
    direction: negative

# --- demand shape ---
underlying_job: "Stay noticeable to me for longer than a week."
current_substitutes:
  - substitute: "Multiple alarm/timer apps rotated manually"
    frequency: 7
    satisfaction: low
    switching_cost: low
  - substitute: "Turning reminders off entirely"
    frequency: 5
    satisfaction: none
    note: "Churn behaviour, not a substitute — the strongest evidence in this record."
audience_segments: [routine_rebuilder, adhd_adjacent]
segment_confidence: 0.60

# --- competitive context ---
competitor_coverage:
  shipping_this: []
  partially: [comp_example_timer]
  market_coverage: 18
  gap_ref: gap_01J8T7...
  data_quality: partial

# --- assessment ---
scores:
  demand_strength: 71
  evidence_quality: 78
  strategic_fit: 84
  differentiation: 66
  feasibility_hint: null                # NOT scored by this system — see §5
opportunity_score: 73
confidence: 0.72
risk_flags:
  - "One explicit refusal-to-pay signal; monetisation as a standalone feature is unsupported."
  - "Competitor data partial — 'nobody ships this' is not established."

# --- four-way separation ---
observed_fact: >
  16 distinct authors across 3 platforms over 63 days described wanting varied or changing
  reminder cues; 7 described manual workarounds; 4 gave willingness-to-pay signals, 1 negative.
ai_interpretation: >
  The demand is for sustained noticeability, not for variation per se. Variation is the
  audience's proposed solution, and their solution may not be the best one.
hypothesis: >
  Any mechanism that defeats habituation would satisfy this demand; variation is one candidate.
recommendation: >
  Treat as a validated problem, not a validated solution. Prototype against the job
  ("stay noticeable"), not the requested feature. Do not price it separately without new evidence.

status: candidate
review_required: true
reviewers_required: 1                  # 2 for product_opportunity class
created_at: 2026-08-17T00:00:00Z
```

---

## 4. Scoring

```text
opportunity_score = 0.30 × demand_strength
                  + 0.25 × evidence_quality
                  + 0.25 × strategic_fit
                  + 0.20 × differentiation
```

| Component | 0–100 definition |
|---|---|
| `demand_strength` | distinct authors (log-scaled) × severity × trend, normalized |
| `evidence_quality` | threshold headroom, platform spread, span, inverse concentration, confidence |
| `strategic_fit` | alignment with the user's stated business focus (`config/business.yaml`) — human-editable |
| `differentiation` | inverse of competitor coverage, adjusted by coverage data quality |

Bands: `<50` signal · `50–69` investigate · `70–84` strong candidate · `85+` rare; requires a second reviewer regardless of class.

**Feasibility is deliberately not scored.** The system has no knowledge of the team's stack, capacity, or constraints, and a fabricated feasibility score would be the most damaging number it could produce. `feasibility_hint` exists only as a human-entered field.

---

## 5. The "audience proposes solutions" trap

Audiences describe problems accurately and propose solutions unreliably. Every product opportunity therefore separates:

```text
underlying_job          ← what they are trying to accomplish     (high confidence)
requested_solution      ← what they asked for                    (evidence, but not a mandate)
recommended_direction   ← what the evidence actually supports    (explicit interpretation)
```

The `recommendation` field must address the job. Where the requested solution and the job diverge, the record must say so — as in the example above, where the job is "stay noticeable" and the requested feature is only one way to achieve it.

---

## 6. Negative evidence is evidence

Two categories are recorded with equal weight and appear in reports:

1. **Refusal signals** — explicit statements of unwillingness to pay, switch, or adopt. A `refusal` signal reduces `demand_strength` and is quoted in the record. Systems that only count enthusiasm produce roadmaps of things people like but won't buy.
2. **Satisfied-with-substitute signals** — evidence that current alternatives are good enough. If ≥30% of substitute evidence shows `satisfaction: high`, the record is flagged `weak_displacement` and capped at `investigate`.

---

## 7. Anti-patterns

| Anti-pattern | Guard |
|---|---|
| Two enthusiastic posts → "strong demand" | Hard thresholds; `signal_only` status |
| A single viral thread → "the market wants" | `single_thread_share` gate + external trigger detection |
| Feature requests treated as validated demand | `underlying_job` separation; `requested_solution` never becomes the recommendation |
| Competitor absence read as opportunity | `data_quality` gates from `competitor-gaps.md §5` |
| Confidence inflation over time as evidence accumulates from one source | Distinct-author and platform gates re-evaluated on every update, not just at creation |
| System proposing what the user already sells | `strategic_fit` check flags overlap with existing product config as `already_shipped` |
| Silent promotion of `signal` → `candidate` without review | Promotion is automatic, but `trusted` still requires a human; product class requires two |
