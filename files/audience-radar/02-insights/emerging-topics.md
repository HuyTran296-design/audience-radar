# Emerging Topics & Trend Detection

Trend detection is where audience-intelligence tools most often lie. Volume gets reported as momentum, small numbers get reported as breakouts, and week-to-week noise gets reported as a signal. This document defines rules strict enough that the system usually says "stable" — which is the truth most weeks.

**Core principle: high volume alone is not a trend.** A topic with 8 mentions growing 300% across 3 platforms matters more than one with 200 flat mentions. But 1 mention becoming 4 is not a 300% trend — it is noise, and the system must say so.

---

## 1. Time windows (canonical)

| Window | Definition |
|---|---|
| `current` (T0) | Last 7 complete days, ISO week boundaries, UTC |
| `previous` (T-1) | The 7 days before that |
| `prior_month` | T-2 to T-5 (4 weeks) |
| `baseline` | Trailing 90 days excluding T0, expressed as a weekly mean and standard deviation |
| `history` | All data, used for seasonality once ≥1 year exists |

Rules:
- Windows must be **equal length and aligned**. Comparing a 9-day window against a 7-day one is a bug, not an approximation.
- **No trend classification before 28 days of collection.** Until then everything is `insufficient_baseline` and the radar says "baseline building — week N of 4".
- Partial windows (a source added mid-window, an outage) set `window_completeness < 1.0`; below 0.8 the topic is `data_incomplete` and excluded from trend claims.

---

## 2. Schema

```yaml
id: topic_01J8S7Y1B3D5F8H0
slug: notification-fatigue
type: topic
label: "Notification fatigue and cue habituation"
description: "Conversations about alerts losing effect, being dismissed reflexively, or being disabled."

# --- measurement ---
current_frequency: 34                 # distinct-author-weighted, T0
previous_frequency: 21                # T-1
baseline_weekly_mean: 18.4            # 90d
baseline_weekly_stdev: 5.1
historical_frequency:                 # last 8 aligned weeks, oldest → newest
  [12, 15, 14, 19, 17, 22, 21, 34]

growth_rate: 0.62                     # (T0 − T-1) / max(T-1, floor)
velocity: 13.0                        # absolute change per week (T0 − T-1)
acceleration: 6.0                     # velocity(T0) − velocity(T-1)
z_score: 3.06                         # (T0 − baseline_mean) / baseline_stdev
share_of_voice: 0.11                  # T0 topic frequency / all relevant items T0
share_change: +0.04

# --- classification ---
trend: rising                         # emerging | rising | stable | declining | saturated | insufficient_baseline | data_incomplete
trend_confidence: 0.78
significance: high                    # low | medium | high  (§5)
sustained_weeks: 3                    # consecutive weeks above baseline+1σ

# --- distribution ---
platforms: {reddit: 22, youtube: 11, forum: 1}
platform_spread: 3
platform_led_by: reddit
cross_platform_lag_days: 4            # first seen on reddit, then youtube
audience_segments: [routine_rebuilder, adhd_adjacent]
distinct_authors: 29
author_concentration: 0.21            # top-3 authors' share of mentions; >0.5 = concentration flag

# --- context ---
related_topics: [topic_habit_streaks, topic_digital_minimalism]
related_pain_points: [pain_01J8K2M4P7QRXV3B]
related_questions: [q_01J8M3P0RQ2V7XB4]
first_detected: 2026-06-09
last_updated: 2026-08-17
external_trigger: null                # detected co-occurring event, if any (e.g. a viral post)
external_trigger_confidence: null

# --- four-way separation ---
observed_fact: "34 distinct-author-weighted mentions in T0 vs 21 in T-1 and a 90-day weekly mean of 18.4 (z=3.06), across 3 platforms, sustained 3 weeks."
ai_interpretation: "Growth is broad rather than driven by one thread; author concentration is low (0.21)."
hypothesis: "Interest may be seasonal (return-to-office period) — insufficient history to test."
recommended_action: "Treat as a live topic for this month's content; re-evaluate in 2 weeks for saturation."

status: trusted
```

---

## 3. Classification rules

Evaluated **in order**; the first matching rule wins. All conditions in a rule must hold.

```text
RULE 0 — insufficient_baseline
  IF days_of_data < 28 OR window_completeness < 0.8
  THEN insufficient_baseline   (no trend claim may be made)

RULE 1 — emerging
  IF first_detected within last 21 days
  AND current_frequency >= 5           (absolute floor — no exceptions)
  AND distinct_authors >= 4
  AND platform_spread >= 2
  AND growth_rate >= 1.0               (at least doubling)
  THEN emerging

RULE 2 — rising
  IF current_frequency >= 8
  AND distinct_authors >= 6
  AND growth_rate >= 0.35
  AND z_score >= 1.5
  AND acceleration >= 0                (not already decelerating)
  THEN rising

RULE 3 — declining
  IF growth_rate <= -0.30
  AND z_score <= -1.0
  AND sustained_weeks_below_baseline >= 2
  THEN declining

RULE 4 — saturated
  IF current_frequency >= baseline_weekly_mean
  AND |growth_rate| < 0.15 for >= 4 consecutive weeks
  AND market_coverage >= 70            (from competitors.md §5)
  THEN saturated

RULE 5 — stable
  ELSE stable
```

Applied after classification:

- **Small-N guard.** If `current_frequency < 5` or `distinct_authors < 4`, the topic cannot be `emerging` or `rising`; it becomes `stable` with `note: below_detection_floor`. Percentages on tiny bases are never displayed.
- **Concentration guard.** If `author_concentration > 0.5`, downgrade one level and set `note: driven_by_few_authors`.
- **Single-thread guard.** If ≥60% of mentions come from one conversation, downgrade one level and set `note: single_thread_event`.
- **Spike guard.** If T0 is >4σ above baseline and `sustained_weeks == 1`, classify as `rising` but set `volatility: spike` — one big thread is not a trend until it repeats.
- **Confidence cap.** `trend_confidence ≤ 0.6` whenever any guard fires.

---

## 4. Trend Score (0–100)

For use in opportunity scoring (`scoring-system.md §10`):

```text
trend_score = clamp(0, 100,
      35 × normalized_growth       # min(1, growth_rate / 1.0)
    + 25 × normalized_z            # min(1, max(0, z_score) / 3.0)
    + 20 × normalized_acceleration # min(1, max(0, acceleration) / (0.5 × baseline_mean))
    + 10 × platform_spread_factor  # min(1, (platform_spread − 1) / 2)
    + 10 × sustain_factor          # min(1, sustained_weeks / 3)
)
× confidence_multiplier            # 1.0 no guards · 0.75 one guard · 0.5 two or more
```

Bands: `0–24` flat · `25–49` mild · `50–74` real momentum · `75–100` strong.

`saturated` topics are capped at 40 regardless of arithmetic — momentum with no room is not an opportunity.

---

## 5. Significance

Significance answers "should a human look at this?", combining statistical strength with business relevance:

```text
significance_score = 0.40 × trend_score
                   + 0.35 × business_relevance    # from scoring-system.md §5
                   + 0.25 × novelty               # is this new to our knowledge base?
```

`high` ≥65 · `medium` 40–64 · `low` <40. Only `high` topics appear in the radar's "what's accelerating" section; the rest go to an appendix.

---

## 6. Topic identity & stability

Topics are clusters, and clusters drift. Stability rules:

1. A topic ID is created once and reused as long as its centroid stays within cosine 0.85 of the original.
2. Weekly re-clustering **matches to existing topics first**, then creates new ones. A renamed label does not create a new ID.
3. Splits: if a topic's internal cohesion drops below 0.6, propose a split to human review. Never split automatically — trend history would break.
4. Merges: same rules as `audience-pains.md §6` (auto ≥0.88, review 0.80–0.88).
5. Every ID change records `supersedes`/`superseded_by` so historical trends remain reconstructible.

**A trend computed across an unstable cluster is fiction.** This is why clustering stability is a Phase-2 exit criterion and trend features are data-gated.

---

## 7. Seasonality & external triggers

- With <1 year of data the system does **not** attempt seasonal adjustment. It flags known-calendar effects (new year, September, holidays) as `possible_seasonal: true` when a topic spikes in those periods and adds the caveat to the report.
- **External trigger detection:** if ≥40% of T0 mentions cluster within 48 hours and reference a common URL or named event, set `external_trigger` with evidence. A single viral post creates a spike that decays; labelling it prevents the user from building a content plan on a dead trend.
- Where a trigger is detected, `recommended_action` explicitly notes the expected decay and suggests waiting one window before committing.

---

## 8. Worked example — the two-topic contrast

| | Topic A | Topic B |
|---|---|---|
| Label | "meditation app pricing" | "streak anxiety" |
| T0 frequency | 96 | 11 |
| T-1 | 92 | 3 |
| Baseline mean | 94.2 | 2.6 |
| Growth rate | +0.04 | +2.67 |
| z-score | 0.15 | 3.9 |
| Distinct authors | 71 | 9 |
| Platform spread | 3 | 2 |
| Sustained weeks | — | 2 |
| Author concentration | 0.06 | 0.28 |
| **Classification** | **stable** | **emerging** |
| Trend score | 12 | 78 |
| Market coverage | 84 | 11 |
| Significance | low | high |

Topic A is nine times larger and worth far less: everyone already covers it and nothing is changing. Topic B clears every floor (≥5 mentions, ≥4 authors, ≥2 platforms, doubling, sustained twice) with low concentration, and nobody is covering it.

**What the report must say about Topic B:** *"Emerging: 'streak anxiety' — 9 distinct authors, 11 mentions this week vs 3 last week (90-day weekly mean 2.6). Small base; confidence 0.62. Worth one piece, not a campaign."*

That last sentence is the difference between an intelligence system and a hype machine.
