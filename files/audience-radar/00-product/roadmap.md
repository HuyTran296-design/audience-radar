# Roadmap

Six phases. Each phase lists features, dependencies, risks, expected outcome, and **exit criteria** — objective, testable conditions that must hold before the next phase begins. Phases are sequential; parallel work inside a phase is fine.

Estimates assume one competent engineer plus an AI coding agent, part-time. They are planning aids, not commitments.

---

## Phase 0 — Documentation (complete)

**Features**
- Product definition, personas, JTBD, scope boundaries
- Canonical schemas: sources, competitors, all insight types, opportunities
- System architecture, data model, agent contracts, workflows, scoring
- Milestone-level implementation plan for the coding agent

**Dependencies:** none.

**Risks**
- Over-specification: docs that lock in decisions the first real data would change. *Mitigation:* every threshold is a config value with a stated default, not a hard-coded constant.
- Under-specification of platform reality (API limits change). *Mitigation:* `source-adapters.md` isolates platform assumptions in one place.

**Expected outcome:** an implementation-ready package with no unresolved internal contradictions.

**Exit criteria**
- [x] All files in the required structure exist.
- [x] Every insight type has a complete field-level schema.
- [x] Every score has range, formula, factors, thresholds, and a human-review rule.
- [x] `DOCUMENTATION-COMPLETE.md` lists decisions, limitations, and open questions.
- [x] No conflicting definitions across files (precedence rule documented in `README.md §4`).

---

## Phase 1 — MVP (target: 4–6 weeks)

**Goal:** one audience, three platforms, evidence-backed weekly radar, running on a schedule, under cost cap.

**Features**
- Project foundation: config loading, structured logging, SQLite storage, migrations, CLI
- Source config (`sources.yaml`) with validation and clear error messages
- Reddit adapter (subreddit listings, comments, keyword search)
- YouTube adapter (channel uploads, video comments, keyword search)
- RSS adapter (blogs, forum feeds, Google Alerts feeds)
- X adapter implemented but disabled by default (`unsupported` reason surfaced)
- Scheduler (APScheduler): per-source frequency, cursors, backoff
- Normalization + 3-layer deduplication
- Relevance gate: rules → embeddings → LLM adjudication for the 40–70 grey zone
- Insight extraction: pains, questions, objections, desires, phrases (strict JSON, evidence-bound)
- Semantic clustering into topics with stable cluster IDs
- Frequency + week-over-week trend detection
- Content opportunity scoring
- Weekly radar → markdown in git-tracked `knowledge/`
- Review queue CLI: list / show / promote / edit / reject
- Cost meter with hard monthly cap

**Dependencies**
- Reddit API credentials (script app); YouTube Data API key with quota
- One LLM provider key; one embedding path (local model default)
- A defined audience + 8–15 sources, written by the user

**Risks**

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Relevance gate too loose → LLM cost blowout | High | High | Cap + tighten thresholds; LLM only on grey zone; batch |
| YouTube comment quota exhaustion (10k units/day) | High | Medium | Prioritise by source priority; cursor per video; degrade to top-level comments only |
| Extraction returns unparseable JSON | Medium | Medium | Schema validation + one repair retry + quarantine, never silent drop |
| Clustering produces one giant cluster or 400 singletons | High | High | Tune `min_cluster_size`; adjudicate merges with the reasoning tier; ship with the "singletons are fine" default |
| User never opens the review queue | Medium | High | Cap queue at 20 items/week, ordered by score; radar links directly to it |
| X access unavailable | High | Low | Designed for: adapter degrades, no scope depends on X |

**Expected outcome:** the user reads a radar on Monday, can verify every claim, and picks at least one topic from it.

**Exit criteria**
1. `radar collect --all` completes with ≥95% source success across 3 platforms.
2. ≥500 items collected, normalized, deduped over a 7-day live run.
3. Relevance rate lands in 20–45%; audited false positives ≤25% (n=30).
4. ≥20 candidate insights generated, **100% with resolvable evidence URLs**.
5. Weekly radar generated end-to-end by the scheduler, twice, unattended.
6. Review queue used: ≥10 human decisions recorded; rejections persisted with reasons.
7. Measured cost ≤US$2.00 per 1,000 collected items; monthly cap enforced (tested by forcing the cap).
8. `radar doctor` reports config, credentials, quota, and schedule health accurately.

---

## Phase 2 — Intelligence (target: 3–5 weeks)

**Goal:** the insights get *good*. Quality, memory, and trend credibility.

**Features**
- Insight merge/dedup across weeks (same pain re-detected updates frequency, doesn't duplicate)
- Rejection feedback loop: rejected items become negative exemplars in the relevance gate (few-shot + embedding centroid distance)
- Audience language pack per topic: verbatim / normalized / marketing layers, exportable
- Custom audience segments (user-defined, inferred per item with confidence)
- Trend engine hardening: aligned windows, 90-day baseline, small-N guards, acceleration
- Objection register with underlying-concern inference
- Confidence calibration pass: compare stated confidence against human accept rate, adjust prompt/priors
- Alerting: velocity spike → notification between weekly reports
- Read-only local review UI (single-file HTML served by the CLI) — optional but high leverage

**Dependencies:** Phase 1 exit + ≥6 weeks of live data (trend math is meaningless before that).

**Risks**
- Baseline too short → false "emerging" everywhere. *Mitigation:* suppress trend classification until 28 days of data; label reports "baseline building".
- Feedback loop overfits to a few rejections. *Mitigation:* require ≥15 rejections before the negative centroid is applied; cap its weight.
- Merge logic collapses genuinely distinct pains. *Mitigation:* merges above a similarity band require human confirmation; all merges are reversible and logged.

**Expected outcome:** candidate rejection rate ≤20%; the user trusts trend labels enough to act on them.

**Exit criteria**
1. Re-detected pains update existing records (verified: no duplicate pain IDs for the same cluster across 4 weeks).
2. Rejection loop measurably improves precision: false-positive rate drops ≥5 points after ≥15 rejections.
3. Language pack exports for ≥5 topics, each with ≥10 verbatim phrases and correct layer separation.
4. Trend classifications reviewed by a human: ≥70% judged correct on a 20-item sample.
5. Confidence calibration report exists; median confidence within ±0.1 of observed human accept rate.

---

## Phase 3 — Competitor Intelligence (target: 3–4 weeks)

**Goal:** answer "where is the space?" not "what did they post?"

**Features**
- Competitor config + adapters for public surfaces (site RSS/sitemap, YouTube channel, public social where API allows)
- Coverage map: competitor content → topic clusters (same clusters as audience side — this is the whole trick)
- Performance signals where public (views, comment counts, engagement proxies) with explicit reliability caveats
- Answered-question matrix: which audience questions each competitor addresses, how well
- Gap engine: demand vs coverage with the scoring model in `02-insights/competitor-gaps.md`
- "Where competitors are silent" detection (zero coverage + real demand = highest-value gap class)
- Competitor promotion tracking (what they push, what offers appear)

**Dependencies:** Phase 2 clustering stability (gaps are only meaningful if both sides map to the same topics).

**Risks**
- Public engagement numbers are unreliable/absent → false performance conclusions. *Mitigation:* performance is a modifier, never a primary factor; always show `data_quality`.
- "Gap" is actually a topic competitors correctly ignore (no business value). *Mitigation:* gap score multiplies by business relevance; a gap with low relevance is reported as "deliberately unserved".
- Site scraping temptation. *Mitigation:* sitemap/RSS only; if unavailable, mark `coverage_data: unavailable` and reduce confidence rather than scraping around it.

**Expected outcome:** ≥5 credible gaps per month, each with demand evidence *and* coverage evidence.

**Exit criteria**
1. ≥3 competitors configured; coverage extracted for ≥100 competitor content items.
2. Competitor content maps into the same topic space as audience conversations (≥80% assigned to an existing cluster or a justified new one).
3. Gap list produced with both-sided evidence; human review judges ≥60% actionable.
4. At least one "silent gap" (demand ≥ high, coverage = 0) identified and verified manually.

---

## Phase 4 — Content Engine Integration (target: 3–4 weeks)

**Goal:** an accepted opportunity becomes a brief, then content, without re-explaining the audience.

**Features**
- Stable, versioned export contract (`opportunity.v1` JSON): problem, audience, evidence, language pack, angle, hooks, CTA, format, platform, do-not-say list
- Brief generator: opportunity → content brief with evidence appendix
- Handoff API/CLI: `radar export --opportunity <id> --format brief|json`
- Outcome ingestion: published URL + performance back into `Opportunity.outcome`
- Attribution loop: which insight types produce content that performs
- Guardrails passed downstream: no medical/health claims, no unverified factual claims, no fabricated quotes, claim-substantiation flags on any statistic

**Dependencies:** Content Engine exists and accepts the contract; Phase 2 language packs.

**Risks**
- Contract churn breaks both systems. *Mitigation:* version the schema, additive changes only, contract tests on both sides.
- Generated content launders AI interpretation as fact. *Mitigation:* the export carries the four-way label (`observed_fact` / `ai_interpretation` / `hypothesis` / `recommendation`) and a `claims_requiring_verification[]` array the Content Engine must resolve before publish.
- Automation makes bad opportunities easier to act on. *Mitigation:* only `trusted` opportunities are exportable.

**Expected outcome:** insight → published piece in one working session, with the evidence trail intact.

**Exit criteria**
1. `opportunity.v1` frozen and documented; contract tests pass in both repos.
2. ≥10 opportunities exported and turned into briefs.
3. ≥5 pieces published with lineage recorded; `radar outcome` captures performance.
4. Zero published pieces containing a claim the export flagged as requiring verification (audited).

---

## Phase 5 — Market Radar (target: 6–8 weeks)

**Goal:** from one audience to a market view; from content demand to product demand.

**Features**
- Multiple audience profiles / portfolios in one install; cross-audience comparison
- Multi-language: original language preserved, detected language, translated interpretation alongside (never replacing) verbatim text
- Product / feature / service / offer opportunity engine with hard evidence thresholds
- Pricing-signal detection (what people say things are worth, what they refuse to pay)
- Review-site mining (App Store, G2, Trustpilot) where ToS-compliant
- Category-level trend view; "market weather" monthly report
- Postgres migration path + optional hosted deployment

**Dependencies:** Phase 3 gap engine; Phase 2 confidence calibration; storage migration.

**Risks**
- Scope explosion into "a BI tool". *Mitigation:* Market Radar must still fit on one page per audience per week.
- Weak evidence → someone builds a product on noise. *Mitigation:* product opportunities require ≥12 conversations / ≥8 distinct authors / ≥2 platforms / ≥21-day span, enforced in code (see `03-opportunities/product-opportunities.md`).
- Translation flattens the exact language that made the system valuable. *Mitigation:* verbatim fields are immutable and always displayed in the original language first.
- SQLite contention with many audiences. *Mitigation:* Postgres switch behind the same repository interface.

**Expected outcome:** the system supports a portfolio (agency or multi-product founder) and produces defensible product demand signals.

**Exit criteria**
1. ≥2 audience profiles running independently on one install with isolated data and separate radars.
2. Non-English items collected, analyzed, and reported with verbatim language preserved and layers visibly separated.
3. ≥3 product opportunities meeting the full evidence threshold; each reviewed and judged credible.
4. Cost per audience stays within the per-audience cap; no cross-audience data leakage (tested).

---

## Sequencing rules

1. **No phase starts before the previous phase's exit criteria pass.** The temptation to start competitor intelligence before clustering is stable is the single most likely way to waste a month.
2. **Trend and gap features are data-gated, not effort-gated.** Six weeks of collection is a hard prerequisite for credible trend output, regardless of code readiness.
3. **Cost control ships in Phase 1**, not later. Retrofitting caps after a surprise bill is the common failure.
4. **Human review ships in Phase 1.** A system that can't be corrected can't be trusted, and Phase 2's quality loop has nothing to learn from.
