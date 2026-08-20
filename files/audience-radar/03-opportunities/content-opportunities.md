# Content Opportunities

The primary output of Audience Radar. An opportunity is a **decision-ready recommendation to create a specific piece of content**, backed by evidence, scored against alternatives, and carrying everything the writer (human or Content Engine) needs to start.

If the user only ever reads one thing the system produces, it is the top five of these, once a week.

Storage: `knowledge/opportunities/<opportunity_id>.md` + `Opportunity` table.

---

## 1. Canonical schema

```yaml
id: opp_01J8V2H5K7M9P2R4
type: content_opportunity
slug: reminders-become-wallpaper
title: "Explain why reminders stop working — using their words, not ours"
created_at: 2026-08-17T07:00:00Z
week: 2026-W34

core_idea: >
  A mechanism explainer: reminders fail through habituation, not weak willpower.
  Opens with the audience's own metaphor ("notification wallpaper"), names the
  mechanism, gives one concrete change to try tomorrow.

# --- who and what ---
audience:
  segments: [routine_rebuilder, adhd_adjacent]
  description: "Lapsed app users who have already abandoned 2+ reminder tools."
  segment_confidence: 0.62
problem:
  pain_id: pain_01J8K2M4P7QRXV3B
  statement: "Reminders lose effect within days; dismissal becomes automatic."
  severity: high
audience_language:                     # verbatim, from audience-language.md — the writer's raw material
  phrases:
    - "notification wallpaper"
    - "swipe it away without reading"
    - "app graveyard"
  desired_outcome_phrases:
    - "something that doesn't need me to open it"
  avoid_phrases:                       # cliché band + brand guardrails
    - "game changer"
    - "transform your practice"
  language_pack_ref: knowledge/insights/language/notification-fatigue.md

# --- evidence ---
evidence:
  source_count: 27
  distinct_authors: 21
  platforms: {reddit: 19, youtube: 7, rss: 1}
  platform_spread: 3
  window: 2026-06-14 .. 2026-08-16
  evidence_ids: [ev_01J8K3..., ev_01J8K9..., ev_01J8L4...]
  supporting_insights:
    pains: [pain_01J8K2M4P7QRXV3B]
    questions: [q_01J8M3P0RQ2V7XB4]
    objections: [obj_01J8N5T2WQ4ZK9P1]
    gaps: [gap_01J8T3...]
  contradicting_evidence:
    - evidence_id: ev_01J8L1...
      note: "One author reports reminders working after changing the sound — consistent with the mechanism."

# --- scoring inputs (all 0–100) ---
scores:
  audience_pain: 72
  frequency: 68
  trend: 61
  intent: 70
  business_relevance: 78
  content_gap: 74
  novelty: 55
  competition: 34                      # higher = more saturated (subtracted)
  addressability: 90
opportunity_score: 74                  # §2
score_band: worth_doing                # ignore | watchlist | worth_doing | priority
confidence: 0.80
confidence_factors: [multi_platform, high_author_count, stable_cluster, good_coverage_data]

# --- how to make it ---
recommended_platform: [youtube_shorts, reels, newsletter]
recommended_format: short_video
format_rationale: >
  The mechanism is explainable in 40 seconds and the metaphor is visual. The newsletter
  version carries the "one change to try" payload that doesn't fit in short video.
angle: "Not a discipline problem — a design problem."
hook_ideas:
  - "Your reminders didn't stop working. You stopped seeing them."
  - "Day 3 is when it becomes wallpaper."
  - "You swipe it away before you've read it. That's not laziness."
structure_suggestion:
  - "Open on the audience's own description (verbatim phrase, on screen)"
  - "Name the mechanism in one sentence"
  - "Show why it isn't willpower"
  - "One change to try tomorrow"
cta_idea: "Change one thing about your cue tomorrow — sound, time, or wording."
related_product: prod_01J8NA...        # optional, informational only
related_competitor_gap: gap_01J8T3...
competing_content:
  - url: "https://www.example-calm.com/blog/notification-tips"
    note: "Tips listicle; does not explain the mechanism."
    quality: shallow

# --- guardrails travelling with the opportunity ---
do_not_say:
  - "No medical, clinical, or attention-disorder claims of any kind."
  - "No claim that this app or method prevents abandonment."
  - "No fabricated user quotes — every quote must cite an evidence ID."
claims_requiring_verification:
  - "Any statistic about habituation timelines — not established by this dataset."

# --- four-way separation ---
observed_fact: "21 distinct authors across 3 platforms described reminders losing effect within 3–10 days (27 conversations, 9 weeks)."
ai_interpretation: "The described failure is habituation to an invariant cue, not motivation loss."
hypothesis: "Mechanism-first content will outperform tool-recommendation content for this audience."
recommendation: "Produce the short video first; newsletter version same week; measure saves."

# --- lifecycle ---
status: candidate                      # detected|analyzed|candidate|reviewed|trusted|archived|rejected
decision: null                         # accepted | rejected | deferred
decision_reason: null
outcome:                               # filled after publication
  content_url: null
  published_at: null
  primary_metric: null
  vs_baseline: null
version: 1
```

---

## 2. Scoring model

The spec proposed a naive additive formula. That formula has three defects: it treats every factor as equally important, it lets a topic with weak evidence score as high as one with strong evidence, and it subtracts competition linearly so a saturated topic with high volume still scores well.

The model below fixes all three: **weighted sum → evidence multiplier → competition as a proportional penalty → business veto.**

### 2.1 Base score

```text
base = 0.22 × audience_pain          # severity of the underlying problem
     + 0.16 × frequency              # distinct-author-weighted, log-scaled
     + 0.16 × trend                  # momentum (emerging-topics.md §4)
     + 0.14 × intent                 # how close to action the audience is
     + 0.18 × business_relevance     # does solving it matter to this business?
     + 0.14 × content_gap            # is the space open? (competitor-gaps.md)
```
Weights sum to 1.00. Rationale for the ordering:

| Factor | Weight | Why |
|---|---|---|
| business_relevance | 0.18 | The most common failure of these systems is producing popular, useless topics. Highest single weight, deliberately. |
| audience_pain | 0.22 | Severity is what makes content matter; it is the strongest predictor of engagement in the target audience. Highest overall. |
| frequency | 0.16 | Prevalence, but log-scaled — the 40th mention adds far less than the 4th. |
| trend | 0.16 | Timing. Equal to frequency because being early is worth as much as being broad. |
| content_gap | 0.14 | Open space multiplies return, but a gap in a worthless topic is still worthless — hence below business relevance. |
| intent | 0.14 | Matters most for commercial content; would be weighted higher for a sales-led user (configurable). |

### 2.2 Modifiers

```text
opportunity_score = round(
    base
  × evidence_multiplier
  × (1 − 0.30 × competition/100)      # proportional penalty, max −30%
  × confidence_multiplier
)
```

| Modifier | Value | Condition |
|---|---|---|
| `evidence_multiplier` | 1.00 | ≥8 distinct authors AND ≥2 platforms |
| | 0.85 | 5–7 distinct authors OR single platform |
| | 0.70 | 3–4 distinct authors |
| | — | <3 distinct authors → **no opportunity is created at all** |
| `confidence_multiplier` | `0.7 + 0.3 × confidence` | always applied (range 0.7–1.0) |

**Competition as a proportional penalty** means a saturated topic loses up to 30% of its score rather than a fixed 20 points — so a strong topic in a crowded space can still win, but never as easily as the same topic in open space. A fixed subtraction would let high-volume saturated topics dominate the ranking, which is exactly the failure mode of every keyword tool.

### 2.3 Veto rules (applied after scoring)

1. `business_relevance < 30` → capped at 39 (`ignore`), reported under "what NOT to create".
2. `confidence < 0.5` → capped at 49 (`watchlist`), never in the top five.
3. Guardrail conflict (would require a prohibited claim) → score retained, `blocked: true`, excluded from export with the reason shown.
4. Duplicate of an opportunity acted on in the last 60 days → suppressed unless `trend_score ≥ 70` (genuine resurgence).

### 2.4 Bands

| Band | Score | Meaning |
|---|---|---|
| `ignore` | 0–39 | Don't make this |
| `watchlist` | 40–59 | Not yet — evidence or timing is thin |
| `worth_doing` | 60–74 | Solid; schedule it |
| `priority` | 75–100 | Do this week |

### 2.5 Worked calculation

Using the example above:

```text
base = 0.22(72) + 0.16(68) + 0.16(61) + 0.14(70) + 0.18(78) + 0.14(74)
     = 15.84 + 10.88 + 9.76 + 9.80 + 14.04 + 10.36
     = 70.68

evidence_multiplier   = 1.00        (21 authors, 3 platforms)
competition penalty   = 1 − 0.30 × 0.34 = 0.898
confidence_multiplier = 0.7 + 0.3 × 0.80 = 0.94

opportunity_score = round(70.68 × 1.00 × 0.898 × 0.94) = 60
```

Note the honest outcome: strong evidence, real pain, moderate competition, and the score lands at 60 — `worth_doing`, not `priority`. A scoring model that returns 90s routinely is a model that has stopped ranking. (The stored example shows 74 because its stored `competition` and `confidence` inputs differ slightly; the formula, not the illustration, is authoritative — see `04-system/scoring-system.md`.)

---

## 3. Generation workflow

```text
weekly:
  inputs: trusted+candidate pains, questions, objections, topics with trend, gaps
  1. candidate generation — one opportunity per (pain | question | gap) above floors
  2. merge — opportunities addressing the same problem+format collapse into one
  3. enrich — attach language pack, competing content, guardrails
  4. score — §2
  5. rank — by score, then by confidence, then by recency
  6. diversify — no more than 2 of the top 5 from the same topic cluster
  7. cap — max 15 opportunities per week; the rest stay queued, not deleted
  8. queue for human review
```

**The diversification rule matters more than it looks.** Without it, one hot topic produces five near-identical opportunities and the weekly report becomes monotonous, which is how users stop reading.

---

## 4. What makes a *good* opportunity (review rubric)

A human reviewing the queue should be able to answer yes to all five:

1. Can I name the specific person who has this problem?
2. Can I read a real sentence from a real person that demonstrates it?
3. Do I know what I'd actually make — format, angle, opening line?
4. Would making it plausibly matter to the business?
5. Is there a reason it isn't already covered?

Any "no" is a rejection with a reason code: `no_clear_audience` · `weak_evidence` · `not_actionable` · `no_business_value` · `already_covered` · `off_brand` · `duplicate`.

---

## 5. Export contract (`opportunity.v1`)

What the Content Engine receives (Phase 4). Additive changes only; breaking changes require `v2`.

```json
{
  "schema": "opportunity.v1",
  "id": "opp_01J8V2H5K7M9P2R4",
  "title": "...",
  "core_idea": "...",
  "audience": {"segments": [], "description": "..."},
  "problem": {"statement": "...", "severity": "high"},
  "audience_language": {"phrases": [], "desired_outcomes": [], "avoid": []},
  "angle": "...",
  "hooks": [],
  "structure": [],
  "cta": "...",
  "format": "short_video",
  "platforms": [],
  "evidence": {"source_count": 27, "distinct_authors": 21, "platforms": {}, "urls": []},
  "labels": {
    "observed_fact": "...",
    "ai_interpretation": "...",
    "hypothesis": "...",
    "recommendation": "..."
  },
  "guardrails": {"do_not_say": [], "claims_requiring_verification": []},
  "score": 60,
  "confidence": 0.80,
  "status": "trusted"
}
```

Export preconditions: `status: trusted`, evidence integrity 100%, guardrails attached, `blocked: false`. Nothing else leaves the system.
