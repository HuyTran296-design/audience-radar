# Hot Questions

A **question** is something the audience repeatedly asks. Questions are the highest-conversion content input in the system: they arrive pre-formed as titles, they carry explicit intent, and their frequency is directly measurable.

Storage: `knowledge/insights/questions/<question_id>.md` + `Question` table.

---

## 1. Canonical schema

```yaml
id: q_01J8M3P0RQ2V7XB4
slug: how-to-make-reminders-stick
type: question

question: "How do I get reminders to actually work for more than a week?"   # best representative phrasing, verbatim where possible
normalized_question: "How can notification reminders remain effective over time?"
question_variants:                    # other phrasings that clustered here (verbatim, ≤12 words each)
  - "why do I stop noticing my reminders"
  - "any way to stop ignoring notifications"
  - "reminders stopped working after 3 days??"

# --- measurement ---
frequency: 18
frequency_distinct_authors: 16
frequency_window: last_30_days
frequency_change: +0.29
trend: rising
first_asked: 2026-06-20
last_asked: 2026-08-16
answered_in_thread_rate: 0.28         # share of instances that got a substantive reply

# --- classification ---
intent: implementation                # see §2
intent_confidence: 0.79
secondary_intent: troubleshooting
audience_segment: [routine_rebuilder, adhd_adjacent]
segment_confidence: 0.61
urgency: medium                       # low | medium | high  (§4)
urgency_score: 58
confidence: 0.81

# --- distribution ---
platform_distribution:
  reddit: 12
  youtube: 5
  forum: 1
platform_spread: 3
source_ids: [reddit_mindfulness, reddit_getdisciplined, yt_calm_productivity_channels]

# --- evidence ---
source_count: 18
evidence:
  - evidence_id: ev_01J8M4...
    platform: reddit
    source_id: reddit_mindfulness
    url: "https://www.reddit.com/r/Mindfulness/comments/xxxxxx/"
    collected_at: 2026-08-11T07:22:00Z
    exact_phrasing: "why do I stop noticing my reminders"
    upvotes: 34
    reply_count: 6
    got_useful_answer: false

# --- relationships ---
related_pain_points: [pain_01J8K2M4P7QRXV3B]
related_objections: [obj_another_app_i_will_ignore]
related_topics: [topic_notification_fatigue]
competitor_coverage:
  answered_by: []                     # competitor ids with direct/partial answers
  best_existing_answer: null
  coverage_quality: none              # none | tangential | partial | direct | saturated
  checked_at: 2026-08-17

# --- content planning ---
content_potential: 84                 # 0–100, see §5
business_potential: 71
suggested_formats:
  - format: short_video
    platform: [youtube_shorts, tiktok, reels]
    rationale: "Mechanism is explainable in 40s; the 'wallpaper' framing is a visual hook."
  - format: article
    platform: [blog, newsletter]
    rationale: "Ranks for a real query; supports the app-comparison follow-up."
suggested_hooks:                      # written FROM audience language, not marketing language
  - "Your reminders didn't stop working. You stopped seeing them."
  - "Three days is the average lifespan of a notification."
  - "The reason you swipe it away before you read it"
suggested_angle: >
  Explain habituation as a mechanism, not a willpower failure. Lead with the audience's
  own description ("it became wallpaper"), then the fix.
cta_idea: "Try one change: make the cue different tomorrow than it was today."
do_not_say:                           # guardrails inherited from brand config
  - "any clinical or medical claim about attention or ADHD"
  - "promises that this removes the need for notifications"

# --- four-way separation ---
observed_fact: "16 distinct authors asked a version of this question in 30 days across 3 platforms; 72% of instances received no substantive answer."
ai_interpretation: "Demand is for a mechanism explanation, not a tool recommendation — most phrasings ask 'why', not 'which app'."
hypothesis: "A mechanism-first piece will outperform a listicle of reminder apps."
recommended_action: "Create the mechanism explainer first; the app comparison is a weaker second piece."

# --- lifecycle ---
status: trusted
confidence_factors: [high_author_count, multi_platform, consistent_phrasing, low_answer_rate]
created_at: 2026-06-20T09:00:00Z
updated_at: 2026-08-17T08:30:00Z
version: 2
```

---

## 2. Intent taxonomy

Exactly one primary intent; an optional secondary. Classification is made by the Insight Agent against this rubric and is a required field.

| Intent | Definition | Typical markers | Content implication |
|---|---|---|---|
| `informational` | Wants to understand a concept | "what is", "why does", "how does … work" | Explainer, mechanism piece |
| `commercial` | Evaluating whether to buy a category | "is X worth it", "does anyone pay for" | Value/positioning content |
| `comparison` | Choosing between named options | "X vs Y", "which one should I", "alternatives to" | Comparison, honest tradeoffs |
| `troubleshooting` | Something is broken now | "not working", "stopped", "keeps failing" | Fix content, support docs |
| `educational` | Wants to learn a skill over time | "how do I get better at", "beginner", "where to start" | Series, course, guide |
| `opinion` | Wants judgement or social validation | "thoughts on", "am I the only one", "is it normal" | Community, POV content |
| `purchase_intent` | Ready to transact | "worth the money", "discount", "which plan", "about to buy" | Landing page, offer, objection handling |
| `implementation` | Wants to apply a known solution | "how do I set up", "what's your routine", "how to actually" | Tutorial, template, checklist |

**Intent Score** (0–100) for prioritisation — see `scoring-system.md §6`:
`purchase_intent 100 · comparison 85 · commercial 75 · implementation 70 · troubleshooting 65 · educational 50 · informational 40 · opinion 25`, then modified by explicit-timing markers (+10 for "this week", "today") and by segment fit.

---

## 3. Normalization & clustering

Questions arrive in dozens of phrasings. The pipeline:

1. **Detect** — an item contains a question if it has interrogative structure, a question mark in a first-person context, or an implicit request ("looking for a way to…"). Rhetorical questions are excluded by the Insight Agent rubric (a required boolean `is_rhetorical`).
2. **Extract verbatim** — store the exact phrasing on the evidence record, always.
3. **Normalize** — canonical form: full sentence, second-person removed, entities preserved, slang preserved in `question_variants` but neutralized in `normalized_question`.
4. **Embed & cluster** — cosine ≥0.86 joins an existing question cluster; 0.78–0.86 goes to LLM adjudication; below 0.78 becomes a new cluster.
5. **Choose the representative** — the `question` field is the *most common real phrasing*, not the normalized one. Audiences search in their own words.

**Named entities split clusters.** "Which app should I use for reminders?" and "Should I use Example Calm or Example Timer?" are related but distinct: the second is `comparison`, has different content requirements, and must not be absorbed.

---

## 4. Urgency

```text
urgency_score =
    0.35 × recency_weight       # share of instances in the last 7 days vs 30
  + 0.30 × trend_velocity       # from emerging-topics.md
  + 0.20 × intent_score/100
  + 0.15 × unanswered_rate      # 1 − answered_in_thread_rate
```

| Band | Score | Meaning |
|---|---|---|
| low | 0–39 | Evergreen; schedule anytime |
| medium | 40–69 | This month |
| high | 70–100 | This week — demand is live and unmet |

`unanswered_rate` earns its weight: a frequently asked question that the community keeps answering well is a *worse* content opportunity than a less frequent one nobody answers.

---

## 5. Content potential

```text
content_potential =
    0.30 × frequency_score
  + 0.25 × intent_score
  + 0.20 × (100 − market_coverage)     # from competitors.md §5
  + 0.15 × urgency_score
  + 0.10 × format_fit                  # is it explainable in the user's native formats?
```

Reported in bands. Anything ≥70 is auto-nominated as a content opportunity candidate (`03-opportunities/content-opportunities.md`).

`business_potential` is scored separately (§ `scoring-system.md §5`) because a question can be extremely popular and commercially irrelevant. Both are shown; neither is hidden inside a single number.

---

## 6. Promotion thresholds

| To reach | Requires |
|---|---|
| `candidate` | ≥3 distinct authors, ≥2 platforms **or** ≥5 distinct authors on one platform, confidence ≥0.5 |
| appear in weekly radar | `candidate` + content_potential ≥60, or `trusted` at any score |
| exportable to Content Engine | `trusted` + evidence integrity 100% + `do_not_say` guardrails attached |

Single-platform questions are allowed at higher author counts because some questions genuinely live in one place (a subreddit's recurring thread). They carry `platform_spread: 1` and a visible caveat.

---

## 7. Worked example (compact)

```yaml
id: q_01J8P2...
question: "Is there a mindfulness app that doesn't have a whole library?"
normalized_question: "Are there minimal mindfulness apps without large content libraries?"
frequency: 9
frequency_distinct_authors: 9
intent: comparison
secondary_intent: commercial
urgency: high
urgency_score: 74
platform_distribution: {reddit: 7, youtube: 2}
competitor_coverage: {coverage_quality: tangential, answered_by: [], best_existing_answer: null}
content_potential: 88
business_potential: 92
observed_fact: "9 distinct authors in 21 days asked for minimal alternatives to library-based apps; no competitor content addresses this directly."
ai_interpretation: "The demand is anti-library, phrased as fatigue with choice rather than price."
hypothesis: "A positioning piece framed as 'the anti-library' would meet this demand precisely."
recommended_action: "High-priority comparison piece. Route to opportunity engine; verify competitor coverage manually before publishing a 'nobody offers this' claim."
status: candidate
```

## 8. Failure modes to guard against

1. **Rhetorical questions counted as demand** — "How hard is it to make a decent timer?" is a complaint. Required `is_rhetorical` flag.
2. **Title-question inflation** — YouTube titles are questions by convention. Questions extracted from *creator content* are marked `asked_by: creator` and excluded from audience frequency (they belong to competitor coverage).
3. **One thread, many replies** — a popular thread produces many similar questions from few people. Distinct-author counting handles it; `single_thread` flag makes it visible.
4. **Normalization eating the signal** — never let `normalized_question` replace `question`; the audience's phrasing *is* the deliverable.
5. **Stale questions** — questions with no instance in 60 days auto-archive; if they resurface they reopen as `candidate` with the prior history attached.
