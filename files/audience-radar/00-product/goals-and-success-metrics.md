# Goals & Success Metrics

All metrics below are computed by the system about itself and written to `knowledge/metrics/<period>.md`. Every metric has: definition, formula, measurement window, MVP target, and a stated failure threshold. Where a metric requires human judgement (e.g. false positives), the measurement method is a **sampled audit**, and the sample size is specified.

**Measurement calendar**
- Weekly window: Monday 00:00:00 UTC → Sunday 23:59:59 UTC (ISO week).
- Monthly window: calendar month, UTC.
- Baseline: trailing 90 days, recomputed weekly.

---

## 1. Product metrics

### 1.1 Sources monitored
- **Definition:** count of sources with `enabled: true` that completed ≥1 successful collection in the window.
- **Formula:** `COUNT(DISTINCT source_id WHERE last_success_at within window)`
- **MVP target:** ≥8 active sources; ≥3 platforms represented.
- **Failure threshold:** any source with 0 successes for 7 consecutive days must raise a `source_stale` warning in the radar.

### 1.2 Conversations collected
- **Definition:** new normalized `Conversation` + `Comment` records created in the window (post-dedup).
- **MVP target:** 500–3,000 items/week. This is a *health band*, not a goal to maximise — above 5,000/week the relevance gate should tighten, not the LLM budget widen.
- **Failure threshold:** <100/week (sources too narrow or collection broken).

### 1.3 Relevant conversations
- **Definition:** items with `relevance_score ≥ 50` after the full gate.
- **Formula:** `relevant / collected`
- **MVP target:** relevance rate **20–45%**.
  - Below 20% → sources or keywords are wrong (fix config, not the model).
  - Above 60% → the gate is probably too loose or the sources too narrow; audit for false positives.

### 1.4 Insight extraction rate
- **Definition:** share of relevant items that yielded ≥1 structured insight (pain / question / objection / desire / phrase).
- **MVP target:** ≥60% of relevant items produce ≥1 insight; ≥25% produce a pain or question specifically.
- **Failure threshold:** <35% suggests the extraction prompt or the relevance definition is misaligned.

### 1.5 Duplicate rate
- **Definition:** items rejected by dedup / total items fetched.
- **Layers reported separately:** exact-hash, near-duplicate (simhash), semantic (cosine ≥0.93).
- **MVP target:** report only, no target. Expect 10–35% (cross-posting, quote-tweets, re-fetch overlap).
- **Failure threshold:** >55% → collection windows overlap too much; fix cursors.

### 1.6 False positive rate (relevance)
- **Definition:** share of items marked relevant that a human audit judges irrelevant.
- **Method:** weekly stratified sample of **30 items** (10 from each score band 50–64 / 65–79 / 80–100).
- **MVP target:** ≤20% overall; ≤10% in the 80–100 band.
- **Failure threshold:** >30% overall → tighten thresholds before adding sources.

### 1.7 Insight precision (audit)
- **Definition:** share of `candidate` insights a human accepts without material correction.
- **Method:** measured directly from review-queue actions (`promoted` / `edited` / `rejected`).
- **MVP target:** ≥70% promoted-or-edited, ≤30% rejected by week 4; ≥80% by week 12.
- **Note:** rejection is not failure — an un-used rejection button *is* failure. Track review-queue engagement separately (§1.10).

### 1.8 Insight confidence distribution
- **Definition:** histogram of `confidence` across trusted insights.
- **MVP target:** median ≥0.65; ≤15% of *reported* insights below 0.50 (those appear only under "Watchlist").
- **Anti-goal:** confidence inflation. If >50% of insights score ≥0.9, treat as a calibration bug and audit against evidence counts.

### 1.9 Emerging topic detection
- **Definition:** topics classified `emerging` or `rising` in the window that a human marks "genuinely new / useful".
- **MVP target:** 1–5 per week flagged; ≥50% judged useful.
- **Failure threshold:** 0 for 3 consecutive weeks (detector too strict or baseline too wide) or >12/week (noise).

### 1.10 Review-queue engagement
- **Definition:** share of candidates that received a human decision within 14 days.
- **MVP target:** ≥60%. Below 30% the human-in-the-loop design is not working and the queue must be shortened, not the reports lengthened.

### 1.11 Evidence integrity (hard gate, not a KPI)
- **Definition:** share of insights whose every evidence URL resolves and whose `source_id` exists in storage.
- **Target:** **100%.** Any insight failing this is quarantined automatically and excluded from reports. This is a correctness invariant, tested in CI.

---

## 2. Content metrics

These measure whether the intelligence changes what gets made. They require the user (or Content Engine) to report back; MVP captures them via a single CLI command (`radar outcome`).

### 2.1 Opportunities generated
- **Definition:** distinct `Opportunity` records created in the window with `opportunity_score ≥ 50`.
- **MVP target:** 5–15 per week. Above 20 the ranking has stopped being a decision aid.

### 2.2 Opportunity acceptance rate
- **Formula:** `accepted / presented` (top 10 presented in the radar).
- **MVP target:** ≥30% of the weekly top-5 accepted into a backlog.
- **Failure threshold:** <10% over 4 weeks → scoring weights are wrong for this user; recalibrate business-relevance weighting.

### 2.3 Content created from insights
- **Definition:** published pieces whose `Opportunity` lineage is recorded.
- **MVP target:** ≥50% of the user's weekly output traceable to a radar opportunity by week 8.

### 2.4 Content performance (comparative)
- **Definition:** performance of radar-sourced content vs the user's trailing 8-week median on the same platform+format, using whatever primary metric the user nominates (saves, watch-through, CTR, signups).
- **MVP target:** radar-sourced content median ≥ baseline median. Uplift is a Phase-2 ambition, parity is the Phase-1 bar.
- **Honesty note:** n will be small for months. Report as "directional, n=X", never as a significant result. No statistical claim below n=10 per arm.

### 2.5 Insight-to-content conversion rate
- **Formula:** `content pieces published / trusted insights created` (window-lagged 2 weeks).
- **MVP target:** report only. Establishes the funnel shape: sources → relevant → insights → opportunities → published.

### 2.6 Language adoption
- **Definition:** share of published pieces that reuse ≥1 verbatim audience phrase from the language pack.
- **MVP target:** ≥60%. This is the cheapest, highest-leverage habit the product can create.

---

## 3. System metrics

### 3.1 Collection success rate
- **Formula:** `successful collection jobs / attempted` per source per window.
- **MVP target:** ≥95% overall; ≥90% per source.
- **Escalation:** 3 consecutive failures on one source → disable it automatically, log reason, report in radar.

### 3.2 Processing latency
- **Definition:** p50/p95 from `collected_at` to `analysis_completed_at`.
- **MVP target:** p95 ≤ 6 hours (daily batch); weekly radar produced within 90 minutes of the aggregation trigger.

### 3.3 API errors
- **Definition:** counts by class — `rate_limited`, `auth`, `not_found`, `server`, `parse`, `timeout`.
- **MVP target:** rate-limit hits are expected and fine if handled; **unhandled** errors ≤1% of requests. Any `auth` error pages the user immediately (token expiry is the most common real-world failure).

### 3.4 Cost per 1,000 conversations
- **Definition:** total LLM + embedding + infra cost / (collected items / 1000).
- **MVP target:** ≤ **US$2.00 per 1,000 collected items**; ≤ US$6.00 per 1,000 *relevant* items.
- **Hard cap:** monthly LLM spend cap enforced in code (default US$30). At 80% of cap → warn; at 100% → stop LLM calls, continue collection, mark the week's analysis `partial`.

### 3.5 AI token usage
- **Definition:** input/output tokens by agent and by model tier.
- **MVP target:** ≥70% of *calls* served by the cheap tier (relevance grey-zone + extraction on short items); ≤30% by the reasoning tier (clustering adjudication, gap analysis, radar synthesis).
- **Watch:** tokens per relevant item; a rise without a quality gain means prompt bloat.

### 3.6 Scheduled job success rate
- **Formula:** `jobs completed / jobs scheduled`, by job type (collection, analysis, aggregation, radar).
- **MVP target:** ≥98%; weekly radar **100%** — a missing radar is the one failure the user always notices. If inputs are incomplete, produce a radar that says so rather than producing nothing.

### 3.7 Storage growth
- **Definition:** DB size + knowledge dir size per 1,000 items.
- **MVP target:** ≤50 MB per 10,000 items with raw payloads compressed; raw payload retention 180 days (configurable), derived insights retained indefinitely.

---

## 4. MVP scorecard (single view)

| Metric | Target | Fail below/above |
|---|---|---|
| Active sources | ≥8, ≥3 platforms | <5 |
| Items collected / week | 500–3,000 | <100 |
| Relevance rate | 20–45% | <20% or >60% |
| Insight extraction rate | ≥60% of relevant | <35% |
| Relevance false positives (audited, n=30) | ≤20% | >30% |
| Candidate rejection rate | ≤30% by wk 4 | >45% |
| Review-queue engagement | ≥60% | <30% |
| Median insight confidence | ≥0.65 | <0.55 |
| Emerging topics flagged / week | 1–5 | 0 for 3 wks, or >12 |
| Evidence integrity | 100% | anything <100% |
| Opportunities (score ≥50) / week | 5–15 | 0, or >20 |
| Weekly top-5 acceptance | ≥30% | <10% over 4 wks |
| Collection success rate | ≥95% | <90% |
| p95 analysis latency | ≤6 h | >24 h |
| Cost / 1,000 collected | ≤US$2.00 | >US$4.00 |
| Weekly radar delivered | 100% | any miss |

---

## 5. North-star and guardrail

**North star:** *trusted insights that changed a decision* — weekly count of insights promoted to `trusted` **and** linked to a published piece or a backlog item.
MVP target: **≥3 per week by week 8.**

**Guardrail against the obvious failure mode:** the system can hit every volume metric while producing plausible nonsense. Therefore the north star is paired with a mandatory guardrail: **evidence integrity 100% and audited false-positive rate ≤20%.** If the guardrail fails, the north star is reported as invalid for that period.

## 6. Explicit anti-metrics

Do not optimise, and do not put on any dashboard:

- total posts collected (encourages noise)
- number of insights generated (encourages duplication and padding)
- average confidence score (trivially gamed by prompt wording)
- sentiment percentages (low information, high false authority)
- "AI insights per dollar" (rewards shallow extraction)
