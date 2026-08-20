# Weekly Radar

The weekly executive summary. One page, ten questions, five minutes to read, every claim checkable.

Generated: Monday 07:00 local (configurable) → `knowledge/radar/<ISO-week>.md`, plus optional email/webhook.

---

## 1. Design constraints

1. **Fixed structure.** The same ten sections every week, in the same order. Users learn where to look; a variable report is a report that gets skimmed.
2. **Length cap.** ≤900 words in the main body. Detail lives in linked insight files. If a section has nothing worth saying, it says "nothing this week" — padding is a failure.
3. **Every claim carries evidence.** Counts, windows, and links inline. No claim appears in the radar that isn't traceable to a stored insight.
4. **Uncertainty is visible.** Confidence bands and caveats are in the body, not a footnote.
5. **Trusted-only by default.** `candidate` insights may appear but are marked `[candidate]`. `Rejected` never appears.
6. **The report includes what NOT to do.** A recommendation system without a stop list generates infinite work.

---

## 2. Required sections

| # | Section | Content | Source |
|---|---|---|---|
| 1 | What changed this week | 3–5 deltas vs last week: new pains, trend shifts, new gaps, source health | all |
| 2 | What people are complaining about | Top 3 pains by severity × frequency, with change | `audience-pains.md` |
| 3 | What people are asking | Top 3 questions by urgency, with answer-rate | `hot-questions.md` |
| 4 | What's accelerating | Topics classified `emerging`/`rising` with `significance: high` only | `emerging-topics.md` |
| 5 | What language they're using | 5–8 verbatim phrases, new ones marked | `audience-language.md` |
| 6 | Why they don't buy | Top 2 objections + underlying concern | `objections.md` |
| 7 | What competitors are doing | Notable coverage moves, with data-quality caveat | `competitors.md` |
| 8 | What competitors are missing | Top 2–3 gaps with both-sided evidence | `competitor-gaps.md` |
| 9 | What to create next | Ranked top 5 opportunities | `content-opportunities.md` |
| 10 | What NOT to create | Saturated topics, low-relevance gaps, blocked items, with reasons | scoring vetoes |
| — | System health (footer) | Collection rate, items, relevance rate, cost, review queue, caveats | metrics |

---

## 3. Generation workflow

```text
Monday 06:00 UTC
  1. verify the week's collection is complete (window_completeness ≥ 0.8, else annotate)
  2. run aggregation: frequencies, trends, gaps, opportunity scoring
  3. select: top-N per section by section-specific ranking
  4. diversify: max 2 items per topic cluster across sections 2–4 and 9
  5. compose: Radar Agent writes prose from structured inputs ONLY (no free recall)
  6. validate: every claim maps to an insight id; every URL resolves; word count ≤900
  7. write knowledge/radar/<week>.md, update knowledge/index.md, notify
```

**Hard rule for the Radar Agent:** it may only use numbers and statements present in its structured input. Any figure it cannot source is omitted. A validation pass rejects the draft if it contains a numeral not present in the input payload — a cheap, effective anti-hallucination check.

If inputs are incomplete, the radar is still produced, with a visible banner naming what's missing. A missing radar is worse than a caveated one.

---

## 4. Example output

````markdown
# Audience Radar — Week 34 (2026-08-10 → 2026-08-16)
Audience: Busy knowledge workers seeking calmer routines
812 items collected · 241 relevant (29.7%) · 9 sources · 3 platforms · cost this week: US$1.84

---

## What changed this week
- **"Streak anxiety" crossed the detection floor** — 11 mentions from 9 authors (vs 3 last week, 90-day weekly mean 2.6). First `emerging` topic in 5 weeks. Small base; treat as one piece, not a theme. `[topic_streak_anxiety]`
- **Reminder habituation kept rising** for a third week (34 vs 21). No longer a spike. `[topic_notification_fatigue]`
- **New gap:** no competitor content addresses "minimal app without a library" across 214 items examined since 2026-05-20. `[gap_01J8T9]` *(one competitor's blog is uncollectable — see caveats)*
- **Source health:** `rss_example_forum` failed 4 consecutive runs (feed 404). Disabled automatically; 0 items lost elsewhere.

## What people are complaining about
1. **Reminders become invisible after a few days** — 21 authors, 27 conversations, 9 weeks, 3 platforms. Severity high (72), rising (+42%). *"notification wallpaper"* `[pain_01J8K2]`
2. **Even "short" sessions feel too long mid-workday** — 12 authors, stable. Severity moderate (46). The constraint described is interruption cost, not duration. `[pain_01J8Q7]` *[candidate]*
3. **Choosing between apps is exhausting** — 10 authors, +18%. Frames library size as a cost. `[pain_01J8R2]`

## What people are asking
1. **"How do I get reminders to actually work for more than a week?"** — 16 authors, urgency 58, **72% of instances got no substantive answer**. Intent: implementation. `[q_01J8M3]`
2. **"Is there a mindfulness app that doesn't have a whole library?"** — 9 authors, urgency 74, intent: comparison. `[q_01J8P2]`
3. **"What do you actually do when the bell goes off?"** — 7 authors, urgency 41, intent: implementation. New this week. `[q_01J8V9]` *[candidate]*

## What's accelerating
- **Streak anxiety** — emerging. 11 mentions / 9 authors, +267% vs last week, z=3.9, 2 platforms, sustained 2 weeks, low author concentration (0.28). Confidence 0.62 — small base. Market coverage 11.
- Nothing else met the significance bar this week.

## What language they're using
`"notification wallpaper"` (6 authors, metaphor) · `"app graveyard"` (4) · `"swipe it away without reading"` (5) · `"streak guilt"` (4, **new**) · `"something that doesn't need me to open it"` (5, desired outcome) · `"bloated"` (4, about competitors) · `"one tap and back to work"` (3).
Register: fatigue and resignation, mild self-blame. Almost no urgency or anger — **urgency-driven copy would misread this audience.**
→ Full pack: `knowledge/insights/language/notification-fatigue.md`

## Why they don't buy
1. **"I'd download it and forget about it like the last three"** — 19 authors, stable, blocking. Underlying: a prediction about themselves from prior failures, not skepticism about products (18 of 22 instances reference a past failed attempt). *Interpretation, confidence 0.66.* `[obj_01J8N5]`
2. **"Can't I just use my phone's alarm?"** — 8 authors, +25%. Necessity objection; the substitute is winning silently. `[obj_01J8P4]`

## What competitors are doing
- **Example Calm** published 4 items (2 sleep, 2 courses); nothing on reminder mechanics in 90 days. Engagement data `good`.
- **Example Focus Creator** posted on workday rituals; strongest comment engagement of the three, with 6 audience questions in comments — 4 unanswered.
- **Example Interval Timer**: no collectable content surface (`data_quality: partial`). Coverage claims involving them are limited accordingly.

## What competitors are missing
1. **Nobody answers the "minimal app" question** — demand 74 (9 authors, rising), market coverage 12 across 214 items examined. Gap score 81, confidence 0.69 (capped: one competitor partial). ⚠️ Verify manually before any public "nobody offers this" claim. `[gap_01J8T9]`
2. **Reminder mechanics explained anywhere** — one shallow tips listicle; no mechanism content. Gap score 68. `[gap_01J8U2]`

## What to create next
| # | Opportunity | Score | Format | Why now |
|---|---|---|---|---|
| 1 | "Your reminders didn't stop working — you stopped seeing them" | 74 | Short video + newsletter | Top pain, rising 3 weeks, no mechanism content exists `[opp_01J8V2]` |
| 2 | "The minimal app question" comparison | 71 | Article | Highest-intent question, open gap `[opp_01J8V5]` |
| 3 | "You're right, you probably will forget about it" | 66 | Short video | Directly answers the blocking objection `[opp_01J8V7]` |
| 4 | "Streak guilt" POV piece | 61 | Short video | Emerging language, uncontested `[opp_01J8V8]` *[candidate]* |
| 5 | "What to do in the ten seconds after the bell" | 58 | Carousel + short | Recurring implementation question `[opp_01J8W0]` |

## What NOT to create
- **"Best meditation apps 2026" listicles** — market coverage 84, trend flat, competition penalty maximal. Saturated.
- **Anything framed around discipline or motivation** — contradicts the dominant register and blames the audience for the thing they already fear (`obj_01J8N5`).
- **"Science of mindfulness" explainers** — demand 38, and the guardrails prohibit the health claims this format invites. Blocked.
- **A price-comparison piece** — pricing data for 2 of 3 competitors is >90 days old; any claim would be unverifiable this week.

---
### Caveats
- `comp_example_timer` has no collectable content surface; all coverage claims involving them are `partial`.
- `rss_example_forum` contributed 0 items (feed 404, auto-disabled) — forum-side signal is missing this week.
- "Streak anxiety" rests on 9 authors over 2 weeks. Directional only.

### Review queue: 11 items awaiting decision (4 pains, 3 questions, 4 opportunities) → `radar review`
### System: collection success 96% (24/25 jobs) · p95 analysis latency 3h12m · LLM spend MTD US$7.40 / US$30 cap
````

---

## 5. Section ranking rules

| Section | Ranked by | Cap |
|---|---|---|
| Complaints | `severity_score × 0.6 + frequency_score × 0.4` | 3 |
| Questions | `urgency_score`, tie-break `unanswered_rate` | 3 |
| Accelerating | `significance_score`, `high` only | 5 |
| Language | new phrases first, then `distinctiveness` | 8 |
| Objections | `objection_priority` | 2 |
| Competitor moves | recency × relevance to tracked topics | 3 |
| Gaps | `opportunity_score`, both-sided evidence required | 3 |
| Create next | `opportunity_score`, max 2 per cluster | 5 |
| Don't create | saturation, veto reason, or blocked status | 4 |

---

## 6. Monthly variant

Same structure, plus:
- 4-week trend lines for tracked topics
- Source review table: items, relevance rate, **trusted insights produced**, cost share → keep/tighten/cut recommendation
- Insight quality: candidates created, promoted, rejected, and rejection reason distribution
- Confidence calibration: stated confidence vs human accept rate
- Opportunity outcomes: what was published, how it performed vs baseline (labelled directional while n is small)
- Cost review and forecast

---

## 7. Failure handling

| Condition | Behaviour |
|---|---|
| Collection <80% complete | Publish with banner naming affected sources; suppress trend claims for those platforms |
| Zero new insights | Publish a short radar saying so plus source-health diagnosis. **Never fabricate content to fill sections.** |
| LLM cost cap reached | Publish from existing structured data without new synthesis; mark `partial` |
| Validation failure (unsourced numeral) | Regenerate once; if it fails again, publish the structured tables without narrative prose |
| Review queue >30 items | Add a prompt at the top; the queue, not the report, is the bottleneck |
