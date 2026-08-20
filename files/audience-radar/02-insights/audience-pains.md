# Audience Pain Points

A **pain point** is a recurring problem, friction, or frustration expressed by the target audience, supported by evidence from multiple independent sources.

A pain point is *not*: a single complaint, a feature request (that is a `desired_outcome`), a question (see `hot-questions.md`), or a purchase objection (see `objections.md`). One conversation can contribute to several of these; they are separate records with separate lifecycles.

Storage: `knowledge/insights/pains/<pain_id>.md` (front-matter YAML + human notes) and the `PainPoint` table (`04-system/data-model.md`).

---

## 1. Canonical schema

```yaml
id: pain_01J8K2M4P7QRXV3B          # prefixed ULID, immutable
slug: reminders-are-easy-to-ignore  # stable, human-readable, unique
title: "Reminder apps become invisible after a few days"
category: habit_formation           # see §2
type: pain_point

description: >
  Users report that notification-based reminders stop working within days:
  they dismiss reflexively, stop noticing, or disable them. The failure is
  described as automatic rather than deliberate — not a motivation problem.

# --- measurement ---
frequency: 27                       # distinct conversations in the measurement window
frequency_distinct_authors: 21      # THE number that matters (see §3)
frequency_window: last_30_days
frequency_change: +0.42             # vs previous equivalent window, ratio
frequency_previous: 19
trend: rising                       # emerging | rising | stable | declining | saturated
trend_confidence: 0.71

confidence: 0.84                    # 0.00–1.00, see scoring-system.md §9
severity: high                      # low | moderate | high | critical  (§4)
severity_score: 72                  # 0–100

# --- audience ---
affected_audience:
  segments: [routine_rebuilder, adhd_adjacent]
  segment_confidence: 0.62
  description: "Lapsed app users who have already tried 2+ reminder tools."
  estimated_share: partial          # unknown | niche | partial | majority (qualitative, never a %)

# --- evidence ---
source_count: 27
distinct_authors: 21
platforms:
  reddit: 19
  youtube: 7
  rss: 1
platform_spread: 3                  # distinct platforms; 1 = single-platform caution flag
first_detected: 2026-06-14
last_detected: 2026-08-16
detection_span_days: 63

representative_quotes:              # ≤3, each ≤15 words, verbatim, attributed
  - text: "I just swipe them away without even reading anymore"
    evidence_id: ev_01J8K3...
    platform: reddit
    collected_at: 2026-08-02T09:14:00Z
  - text: "the notification became wallpaper"
    evidence_id: ev_01J8K9...
    platform: youtube
    collected_at: 2026-07-28T16:40:00Z

paraphrased_examples:               # preferred over quotes; unlimited
  - "Describes dismissing reminders reflexively within the first week."
  - "Says the alert stopped registering as information and became background noise."
  - "Turned notifications off after a stressful week and never turned them back on."

evidence:                           # full evidence chain, required
  - evidence_id: ev_01J8K3...
    platform: reddit
    source_id: reddit_mindfulness
    conversation_id: conv_01J8...
    url: "https://www.reddit.com/r/Mindfulness/comments/xxxxxx/"
    collected_at: 2026-08-02T09:14:00Z
    author_hash: a3f9c1e2
    relevance_score: 78
    contribution: primary           # primary | supporting | contradicting

contradicting_evidence:             # REQUIRED field; empty list is an explicit claim
  - evidence_id: ev_01J8L1...
    note: "User reports reminders working well after switching to a distinct sound."

# --- relationships ---
related_topics: [topic_notification_fatigue, topic_habit_streaks]
related_questions: [q_how_to_make_reminders_stick]
related_objections: [obj_another_app_i_will_ignore]
related_products: [prod_variable_cue_scheduling]
related_pains: [pain_01J8...]       # sibling pains in the same cluster family
cluster_id: clu_habit_cue_decay

# --- the four-way separation (mandatory) ---
observed_fact: >
  21 distinct authors across 3 platforms described reminders losing effect within
  roughly 3–10 days, in 27 conversations collected between 2026-06-14 and 2026-08-16.
ai_interpretation: >
  The described mechanism is habituation to an unchanging cue rather than declining
  motivation; users report the dismissal as automatic and pre-conscious.
hypothesis: >
  Cues that vary (sound, timing, or phrasing) may retain attention longer. Not tested
  by any evidence in this dataset.
recommended_action: >
  Content: address the habituation mechanism directly using the audience's own framing
  ("it became wallpaper"). Product: investigate cue variation — but see product-opportunities.md
  thresholds before treating this as validated demand.

# --- lifecycle ---
status: trusted                     # detected|analyzed|candidate|reviewed|trusted|archived|rejected
reviewed_by: human
reviewed_at: 2026-08-17T08:20:00Z
review_notes: "Merged with pain_01J7ZZ (duplicate phrasing). Severity raised from moderate."
version: 3
supersedes: null
created_at: 2026-06-14T11:02:00Z
updated_at: 2026-08-17T08:20:00Z
```

---

## 2. Category taxonomy

Categories are configurable per audience (`config/taxonomy.yaml`); these are the defaults. Multi-label is allowed; the first is primary.

`onboarding` · `habit_formation` · `time_cost` · `cognitive_load` · `trust` · `price_value` · `technical_friction` · `results_uncertainty` · `social_context` · `tool_overwhelm` · `privacy` · `accessibility` · `motivation` · `switching_cost` · `support` · `other`

`other` above 15% of pains for two consecutive weeks is a signal the taxonomy needs extending — reported automatically.

---

## 3. Frequency: how it is counted

Naive mention counting rewards loud individuals and cross-posts. The canonical count is **distinct-author-weighted**:

```text
frequency               = distinct conversations containing ≥1 supporting item
frequency_distinct_authors = distinct author hashes (the headline number)
weighted_frequency      = Σ over authors of min(contributions_by_author, 3)
```

Rules:
1. An author contributes at most 3 to weighted frequency, no matter how many times they post.
2. Cross-posts of the same content by the same author count once (dedup already handles most).
3. A reply agreeing with an existing complaint counts (it is corroboration) but only via its own author.
4. Frequency is always reported with its window. A bare number is a reporting bug.
5. If `distinct_authors < 3`, the record cannot leave `candidate` status. Ever.

---

## 4. Severity

`severity_score` 0–100, derived, then banded.

```text
severity_score =
    0.35 × impact          # how much it blocks the audience's goal (LLM-rated 0–100, rubric-anchored)
  + 0.25 × emotional_intensity  # lexical intensity + explicit frustration markers
  + 0.20 × persistence     # is it described as recurring/unresolved vs one-off
  + 0.20 × workaround_cost # effort users report spending to work around it
```

| Band | Score | Meaning |
|---|---|---|
| low | 0–24 | Mild annoyance; mentioned in passing |
| moderate | 25–49 | Real friction, tolerated |
| high | 50–74 | Blocks the goal or causes abandonment |
| critical | 75–100 | Causes churn, refunds, or public warning-off |

**Emotional intensity is a lexical measure, not sentiment analysis.** It counts intensity markers, emphasis, profanity, and abandonment language present in the audience's own words — and stores the markers as evidence.

---

## 5. Lifecycle & state transitions

```text
detected ──► analyzed ──► candidate ──► reviewed ──► trusted ──► archived
                │             │            │            │
                └──► rejected ◄┴────────────┴────────────┘
```

| State | Entry condition | Who |
|---|---|---|
| `detected` | ≥1 item extracted a pain-shaped statement | Insight Agent |
| `analyzed` | Clustered, deduped, scored | Clustering + scoring |
| `candidate` | `distinct_authors ≥ 3` **and** `platform_spread ≥ 2` **and** `confidence ≥ 0.5` | System |
| `reviewed` | A human opened it and edited/confirmed fields | Human |
| `trusted` | Human promotion. **Only humans create this state.** | Human |
| `archived` | No new evidence for 90 days, or superseded by a merge | System (reversible) |
| `rejected` | Human rejection with a reason code | Human |

Rejection reason codes (fed back into relevance training): `not_our_audience` · `not_a_pain` · `duplicate` · `misinterpreted` · `insufficient_evidence` · `stale` · `off_topic_source`.

**Re-detection rule:** new evidence for an existing pain updates `frequency`, `last_detected`, and `evidence[]`, and increments `version`. It never creates a second record. Archived pains reopen to `candidate` (not straight to `trusted`) when new evidence arrives.

---

## 6. Merge rules

Two pains merge when:
- cosine similarity of their canonical descriptions ≥ **0.88**, **and**
- category matches or one is `other`, **and**
- a reasoning-tier adjudication returns `same_underlying_problem: true` with a stated reason.

Between **0.80–0.88** the merge is proposed to the human review queue, never automatic. Below 0.80, no merge.

All merges: record `supersedes`, keep both evidence sets, keep the higher severity, sum distinct authors (deduped by hash), and are reversible for 30 days.

---

## 7. Quote and copyright policy

- Verbatim quotes: **maximum 3 per pain, each ≤15 words**, exact, attributed to platform + URL + timestamp.
- Never stitch multiple short quotes from one source to reconstruct a passage.
- Prefer `paraphrased_examples` — they carry the same signal for content work and carry no reproduction risk.
- Never quote anything containing identifying personal detail (health status, employer, location, names). The extraction prompt strips these; a rule-based redactor is the backstop.
- Quotes are stored with `author_hash`, not usernames, in the insight layer. Usernames stay in the raw layer for traceability only.
- Where retention expires (180 days default), quotes are dropped and the paraphrase remains, with `evidence_expired: true` and confidence reduced by 0.1.

---

## 8. Worked example (compact record)

```yaml
id: pain_01J8Q7...
slug: five-minutes-is-still-too-long
title: "Even 'short' sessions feel too long during a workday"
category: [time_cost, cognitive_load]
frequency: 14
frequency_distinct_authors: 12
frequency_change: +0.17
trend: stable
confidence: 0.68
severity: moderate
severity_score: 46
platforms: {reddit: 9, youtube: 5}
platform_spread: 2
first_detected: 2026-07-02
last_detected: 2026-08-15
observed_fact: "12 distinct authors described 5–10 minute sessions as impractical mid-workday."
ai_interpretation: "The constraint described is interruption cost, not session length itself."
hypothesis: "Sub-60-second practices may fit the described constraint; untested here."
recommended_action: "Content: a piece built on the interruption-cost framing, using audience wording."
status: candidate
review_note: "Watch for confusion with pain_01J8K2 (reminder habituation) — distinct mechanism."
```

## 9. Anti-patterns (reject these in review)

| Anti-pattern | Why it's wrong |
|---|---|
| "Users want a better experience" | Not a pain — no mechanism, no evidence, unusable |
| A pain built from 2 posts by 1 author | Fails the `distinct_authors ≥ 3` gate |
| A pain whose evidence is all from one thread | Thread consensus ≠ audience prevalence; flag `single_thread: true` |
| Severity `critical` with confidence 0.4 | Confidence caps reported severity; never report a critical low-confidence pain above "watchlist" |
| Interpretation written into `description` | `description` states what was observed; mechanism belongs in `ai_interpretation` |
| A pain that is really an objection | Objections are purchase-blocking; route to `objections.md` |
