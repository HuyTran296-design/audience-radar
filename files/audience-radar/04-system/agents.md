# AI Agents

Nine agents. "Agent" here means **a bounded task with a fixed input contract, a strict output schema, and explicit failure behaviour** — not an autonomous loop. Autonomy is deliberately minimal: agents do not choose their own tools, do not decide what to collect, and cannot promote their own outputs to `trusted`.

**Universal rules (apply to every agent, stated once):**

1. **Evidence or abstain.** Any claim in the output must be supported by an input item ID. An agent that cannot support a claim must omit it, not soften it.
2. **Four-way labelling.** Every substantive output separates `observed_fact`, `ai_interpretation`, `hypothesis`, `recommendation`.
3. **Strict JSON.** Output validates against the schema or is retried once, then quarantined. Never partially parsed.
4. **No invented identifiers.** Every referenced ID must exist in the input payload. Validated post-hoc; hallucinated IDs are the primary automated hallucination check.
5. **No numbers from the model.** Counts, frequencies, and scores are computed in code from stored data. Agents receive numbers; they do not produce them.
6. **Abstention is success.** `insufficient_evidence` is a valid, expected, unpenalised output.
7. **Prompt versioning.** Every prompt has a version; outputs record it; a bump invalidates the analysis cache for affected items.
8. **No PII, no clinical inference.** Extractors drop names, employers, locations, health disclosures. No agent may infer or state a diagnosis, condition, or clinical claim about anyone.

---

## 1. Collector Agent

**Purpose:** plan and coordinate collection runs. Mostly deterministic code; the "agent" surface is small and that is intentional.

- **Input:** enabled sources, cursors, quota ledger, priorities, last-run outcomes.
- **Output:** an ordered execution plan `[{source_id, window, max_items, quota_estimate}]`.
- **Decision rules:**
  - Order by `priority` (critical → low), then by staleness.
  - Allocate constrained quota (YouTube) proportionally to priority; never exceed 90% of daily quota, reserving 10% for manual runs.
  - Skip sources with `consecutive_failures ≥ 3` (auto-disabled) and sources whose credentials are missing.
  - Backfill windows never exceed `backfill_days` or platform limits.
- **Confidence:** n/a (deterministic).
- **Failure:** partial plans are valid; a source that cannot be planned is recorded `skipped` with a reason, never silently dropped.
- **Hallucination prevention:** no LLM in the default path. An optional LLM assist for *query suggestion* is advisory only and writes to a suggestions file a human must approve.

---

## 2. Relevance Agent

**Purpose:** decide whether an item is about this audience's world. Only adjudicates the grey zone; stages 1 and 2 are free.

- **Input:** audience profile (description, goals, not-our-audience list), source context, item text (truncated to 1,500 chars), preliminary embedding score.
- **Output:**
```json
{"content_id":"...","relevant":true,"score":72,"reason":"Describes abandoning a reminder app after three days","primary_signal":"habit_abandonment","not_audience_match":false}
```
- **System instruction (abridged):**
  > You judge whether a conversation is relevant to a defined audience. You are given the audience description, what is explicitly *not* this audience, and one item. Score 0–100 for how likely this item reflects that audience discussing their own experience, questions, or decisions in this domain. Relevance is about the *speaker and their situation*, not topic keywords. Marketing posts, giveaways, bot content, and creator self-promotion are not relevant regardless of topic. If the item is ambiguous, score it in the middle and say why in one sentence. Do not explain your reasoning at length.
- **Decision rules:** ≥70 relevant · 40–69 grey (this agent decides) · <40 rejected before the agent ever sees it. `not_our_audience` matches are hard rejects.
- **Confidence:** implicit in the score; scores 45–55 are logged for review sampling.
- **Failure:** on error, default to **reject** with `stage: error` — a false negative costs one item; a false positive costs money and pollutes insights.
- **Hallucination prevention:** output is a score plus a one-sentence reason grounded in the item; the reason is stored and sampled in the weekly audit.

---

## 3. Insight Agent

**Purpose:** extract structured insights from a single item. The highest-volume agent, hence the cheap tier.

- **Input:** item text, audience profile, taxonomy lists (categories, intents, objection types), `content_id`.
- **Output:**
```json
{
  "content_id": "cnt_...",
  "pains": [{"statement":"...","category":"habit_formation","severity_hint":"high","exact_phrasing":"...","confidence":0.8}],
  "questions": [{"question":"...","normalized":"...","intent":"implementation","is_rhetorical":false,"confidence":0.75}],
  "objections": [{"objection":"...","type":"implementation","stated_concern":"...","raised_at_stage":"consideration","confidence":0.7}],
  "desired_outcomes": [{"statement":"...","exact_phrasing":"...","confidence":0.6}],
  "phrases": [{"text":"notification wallpaper","category":"metaphor","context":"..."}],
  "segments": [{"segment":"routine_rebuilder","confidence":0.6}],
  "insufficient_signal": false
}
```
- **System instruction (abridged):**
  > Extract only what this person actually said. Every `exact_phrasing` must appear verbatim in the input, be 15 words or fewer, and contain no names, employers, locations, or health disclosures. Do not infer motives. Do not merge separate points. If the item contains no clear pain, question, or objection, return `insufficient_signal: true` — that is a correct answer, and most items should produce little. Never invent a plausible-sounding complaint that the text does not support.
- **Decision rules:** one item may produce multiple insight types; a statement can be both a pain and an objection only if it explicitly does both work. Rhetorical questions are marked, never counted as demand. Creator/marketing content is flagged, not extracted as audience signal.
- **Confidence requirements:** per-extraction confidence 0–1; anything <0.4 is dropped at ingestion.
- **Failure:** JSON invalid → one repair retry → quarantine with `error`. Quarantined items are counted and reported; they are never silently skipped.
- **Hallucination prevention:** **verbatim verification** — every `exact_phrasing` is string-matched against the source text in code. Non-matching extractions are discarded and logged. This single check eliminates the most damaging failure mode (fabricated quotes).

---

## 4. Clustering Agent

**Purpose:** group items and insights expressing the same underlying thing, so "I can't decide which app", "too many apps", and "how do I choose" become one topic.

- **Input:** embeddings (computed in code), candidate pairs/groups from HDBSCAN, existing topic centroids and labels.
- **Output:** cluster assignments, proposed labels/descriptions, merge/split proposals with reasons.
```json
{"cluster_id":"clu_...","label":"Tool selection fatigue","description":"...","merge_with":"clu_...","merge_reason":"Both describe difficulty choosing among equivalent tools","confidence":0.82,"same_underlying_problem":true}
```
- **Decision rules:**
  - Mechanical assignment first (cosine ≥0.86 to a centroid). The LLM only adjudicates the 0.78–0.88 band.
  - Auto-merge ≥0.88 with a positive adjudication; 0.80–0.88 goes to human review; <0.80 never merges.
  - Match to existing topics **before** creating new ones — cluster ID stability is what makes trends real.
  - Cohesion <0.6 → propose a split; never split automatically.
- **Confidence:** merges below 0.75 confidence are proposals, not actions.
- **Failure:** on adjudication failure, do not merge. The safe default is more clusters, not fewer — over-merging destroys trend history irreversibly, over-splitting is visible and fixable.
- **Hallucination prevention:** the agent may only choose among supplied cluster IDs; labels must be derived from the supplied member items.

---

## 5. Trend Agent

**Purpose:** interpret and explain momentum. **It does not compute it** — every number comes from `scoring/trend.py`.

- **Input:** computed time series, growth/velocity/acceleration/z-score, guard flags, platform distribution, author concentration, classification from the rule engine.
- **Output:** narrative explanation, external-trigger assessment, significance rationale, caveats.
- **System instruction (abridged):**
  > You are given a completed statistical classification. Do not recompute, dispute, or restate the numbers differently. Explain in two sentences what changed and what would make it credible or not. If guards fired, say plainly why the reader should be cautious. Never describe a topic as a trend if the classification says `stable` or `insufficient_baseline`.
- **Decision rules:** guards fired → the caveat is mandatory and appears first. External trigger detected → the expected-decay note is mandatory.
- **Confidence:** inherited from the rule engine; the agent may lower it with a reason, never raise it.
- **Failure:** on failure, emit the numbers with a templated sentence. A trend section without prose is fine; a trend section with invented prose is not.
- **Hallucination prevention:** the numeric-validation pass rejects any numeral absent from the input payload.

---

## 6. Competitor Agent

**Purpose:** characterize what a competitor covers, how deeply, how recently, and how it lands.

- **Input:** competitor content items (title, summary, format, date, engagement, topic assignment), competitor config, audience topic list.
- **Output:** per-topic coverage characterization, depth rating, promoted offers, positioning language, `data_quality` assessment.
- **Decision rules:**
  - Depth is rated against *that competitor's own* catalogue, never across competitors (different formats, different norms).
  - Engagement is only interpretable with `data_quality: good`; otherwise it is reported as unavailable.
  - Absence of observed coverage is reported as *"not found in N items examined since <date>"* — never as "does not cover".
- **Confidence:** capped at 0.7 when any monitored surface is uncollectable.
- **Failure:** missing surfaces reduce `data_quality`; the agent must never fill a coverage gap with inference.
- **Hallucination prevention:** no competitor claim without a URL in the input. Competitor text is summarized, never reproduced beyond a ≤15-word attributed phrase.

---

## 7. Gap Agent

**Purpose:** diff audience demand against competitor supply and classify the gap type.

- **Input:** topic with demand metrics, coverage map across all competitors, unanswered-question list, examination window and item counts, `data_quality` per competitor.
- **Output:** gap record per `02-insights/competitor-gaps.md`, including `gap_type`, both-sided evidence, `claims_requiring_verification`, and `confidence_caps_applied`.
- **Decision rules:**
  - No gap without **both** demand evidence (≥5 distinct authors, demand_score ≥45) and coverage evidence (≥50 items examined).
  - `silent` requires zero coverage across all `data_quality: good` competitors *and* ≥50 items examined.
  - `business_relevance < 30` → reclassify `deliberately_unserved`.
  - Every absence claim is scoped to the examination window and item count.
- **Confidence:** capped by `coverage_reliability` (`competitor-gaps.md §4`).
- **Failure:** insufficient coverage data → emit `insufficient_coverage_data`, not a gap. This is the correct output more often than not.
- **Hallucination prevention:** the agent cannot assert absence; the *code* computes absence from the coverage map, and the agent only explains it.

---

## 8. Opportunity Agent

**Purpose:** turn insights and gaps into a decision-ready recommendation someone could act on today.

- **Input:** pain/question/objection/gap records, language pack, competitor context, business config, computed component scores.
- **Output:** the `Opportunity` record — core idea, angle, hooks, structure, CTA, format, guardrails.
- **System instruction (abridged):**
  > Write hooks and angles using the supplied verbatim audience phrases. Do not invent quotes. Do not use phrases from the suppression list. Attach the guardrails supplied for this audience verbatim. If the evidence supports a topic but you cannot state a specific angle, say so — a vague opportunity is worse than none. You do not assign the score; it is computed. Your job is to make the recommendation concrete enough to start work from.
- **Decision rules:** floors from `content-opportunities.md §2` (≥3 distinct authors) and `product-opportunities.md §2` (class-specific thresholds) are enforced in code before the agent runs. Diversification (max 2 per cluster in a weekly top-5) is applied after.
- **Confidence:** inherited from source insights, capped at the minimum of contributing confidences.
- **Failure:** if no concrete angle can be produced, output `angle: null` with a reason; the record stays `candidate` and is reported under "watchlist".
- **Hallucination prevention:** hooks are checked against the suppression list and the cliché band; any hook resembling a quotation must map to an `AudiencePhrase` ID or it is stripped.

---

## 9. Radar Agent

**Purpose:** write the weekly report. Highest visibility, tightest leash.

- **Input:** fully assembled structured payload — selected insights, computed numbers, caveats, source health, cost. Nothing else.
- **Output:** the markdown report per `03-opportunities/weekly-radar.md §4`.
- **System instruction (abridged):**
  > Write the weekly radar from the supplied payload only. Every number in your output must appear in the payload. Every claim must reference an insight ID present in the payload. Use the fixed section order. Stay under 900 words. If a section has nothing, write "Nothing this week" — do not pad. Where caveats are supplied, include them in the body, not as a footnote. Do not add encouragement, speculation, or context you were not given.
- **Decision rules:** fixed structure; per-section caps; trusted-first with `[candidate]` marking; the "what NOT to create" section is mandatory and must be populated from veto data.
- **Confidence:** n/a — the report inherits per-item confidences and displays them.
- **Failure:** validation failure → one regeneration → fall back to templated tables without prose. A plain report always ships; an invented one never does.
- **Hallucination prevention:**
  1. **Numeric validation** — every numeral in the draft must exist in the payload.
  2. **ID validation** — every `[insight_id]` must exist.
  3. **Word cap** — enforced mechanically.
  4. **Quote validation** — every quoted phrase must match an `AudiencePhrase.exact_text`.

---

## 10. Cross-agent controls

| Control | Implementation |
|---|---|
| Cost attribution | Every call writes to `CostLedger` with agent, model, tokens, cache status |
| Prompt versioning | `prompts/<agent>.v<N>.md`; version recorded on every output row |
| Replay | Any agent can be re-run over stored inputs; outputs are new rows, never overwrites |
| Golden-set tests | 50 hand-labelled items per agent in CI; precision/recall must not regress |
| Escalation | Cheap-tier output with confidence <0.5 on a high-stakes field escalates once to the reasoning tier |
| Kill switch | `--no-llm` runs the entire pipeline on rules and embeddings only; degraded but functional |
| Audit sampling | 30 items/week sampled across agents for human audit; results feed calibration |

## 11. What no agent may do

- Promote anything to `trusted` (human-only).
- Write to raw or normalized tables.
- Compute a score, count, or frequency.
- Emit a quote that does not verbatim-match stored source text.
- Assert that something does not exist (only code, from coverage data, may assert scoped absence).
- Make medical, clinical, psychological-diagnostic, or legal claims about anyone.
- Decide to collect from a new source, or expand a collection scope.
- Modify its own prompt, thresholds, or budget.
