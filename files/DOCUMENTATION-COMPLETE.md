# DOCUMENTATION-COMPLETE

**Package:** Audience Radar specification v1.0
**Status:** Phase 0 complete. Implementation may begin at Milestone 1.
**Date:** 2026-08-18

This file is the binding summary. Where any other document conflicts with a decision recorded here, **and** the conflict is not about a formula or a schema, this file wins. (Formulas: `04-system/scoring-system.md`. Schemas: `04-system/data-model.md`.)

---

## 1. Architecture summary

A **modular monolith**, batch-scheduled, evidence-first.

```text
Sources → Collection → Normalization → Storage → AI Analysis → Insights → Scoring → Reporting → Content Engine
```

Nine layers, strict downward data flow, append-only between layers. Nine agents with fixed contracts and no autonomy over collection, promotion, or scoring. Everything numeric is computed in deterministic, unit-tested code; LLMs supply rubric-anchored ratings and prose only.

Three properties define the system:

1. **Evidence-first.** No claim without retrievable evidence. `observed_fact` / `ai_interpretation` / `hypothesis` / `recommendation` are separate fields on every insight and appear separately in every report.
2. **Cheap by construction.** Rules and embeddings filter ~75% of items before any LLM call; hard monthly cap enforced in code.
3. **Human promotion.** AI produces `candidate`. Only a human produces `trusted`. Nothing untrusted leaves the system.

---

## 2. Final MVP scope

**In:** Reddit + YouTube + RSS collection · X adapter disabled by default · scheduled daily collection · normalization + 3-layer dedup · 3-stage relevance gate · LLM insight extraction (pains, questions, objections, desires, phrases) · semantic clustering with stable topic IDs · distinct-author frequency · week-over-week trend detection with guards · basic competitor coverage + gap detection · content opportunity scoring · weekly radar in markdown · git-tracked knowledge base · CLI review queue · cost metering with a hard cap.

**Out:** web UI beyond a read-only local page · multi-tenant · Instagram/TikTok/LinkedIn/Discord/Slack · private or gated content · sentiment as a headline metric · automated publishing · real-time streaming · fine-tuning on collected data · non-English as a first-class path · anything requiring auth bypass, CAPTCHA solving, or robots.txt violation.

---

## 3. Technology recommendations

| Concern | Choice |
|---|---|
| Language / CLI | Python 3.12 · Typer |
| Config | YAML + Pydantic v2 (strict validation) |
| Storage | SQLite WAL + `sqlite-vec` → Postgres + pgvector at Phase 5 |
| ORM / migrations | SQLAlchemy 2.x · Alembic |
| Scheduler | APScheduler in-process (cron as an alternative) |
| HTTP | httpx + tenacity |
| Embeddings | `bge-small-en-v1.5` local, provider-pluggable |
| Clustering | HDBSCAN + cosine centroid matching |
| LLM | Two tiers, provider-agnostic client; ≥70% of calls on the cheap tier |
| Reports | Jinja2 → markdown in a git repo |
| Tests | pytest + recorded HTTP fixtures (no network in CI) |

---

## 4. Key decisions (binding)

| # | Decision | Rationale |
|---|---|---|
| D1 | Modular monolith, not services | Nightly batch over thousands of rows; services add cost, solve nothing |
| D2 | SQLite for MVP | Single writer, embedded, trivially backed up; Postgres path preserved |
| D3 | Markdown knowledge base in git | Free version history, diffable, user-editable, portable |
| D4 | CLI-first, no web UI in MVP | Interface effort buys nothing until insight quality is proven |
| D5 | **Distinct authors, not mentions**, is the frequency unit | 30 comments from 3 people is a conversation, not a market |
| D6 | Scores are integers 0–100, reported in bands | Two decimals on an LLM estimate is a lie about accuracy |
| D7 | LLMs never produce numbers | Every count and score is computed and testable |
| D8 | Verbatim verification on every extracted quote | Eliminates the most damaging hallucination class in code, not by prompt |
| D9 | Only humans create `trusted` | A system that self-certifies cannot be corrected |
| D10 | Competition is a **proportional** penalty (≤30%) | Fixed subtraction lets saturated high-volume topics dominate |
| D11 | Business relevance carries the highest single weight after pain (0.18) | The characteristic failure is popular, useless topics |
| D12 | Missing competitor data reduces confidence; it never means "no coverage" | Absence of observed coverage ≠ absence of coverage |
| D13 | Trend classification blocked before 28 days of data | Trends on a short baseline are noise with a label |
| D14 | Topic IDs are stable across re-clustering | Regenerated IDs destroy all trend history |
| D15 | Over-splitting preferred to over-merging | Splits are visible and fixable; merges corrupt history irreversibly |
| D16 | `exact_text` on phrases is immutable | The audience's words are the deliverable |
| D17 | Raw layer immutable; retention 180 days | Audit anchor + privacy limit |
| D18 | Author identifiers hashed outside the raw layer; no profiling fields in the schema | Privacy enforced structurally, not by policy |
| D19 | Product opportunities gated by hard, class-specific thresholds | The one place where being wrong is expensive |
| D20 | X is optional and degrades cleanly | API access is unstable; nothing may depend on it |
| D21 | No feasibility scoring | The system knows nothing about the team's constraints |
| D22 | Weekly radar always ships, caveated if degraded | A missing report is worse than an honest partial one |
| D23 | Quote limits: ≤15 words, one per source, ≤3 per insight; paraphrase preferred | Copyright and privacy discipline at the schema level |
| D24 | `search.list` never used for YouTube channel enumeration | 100 quota units vs 2; determines how many sources fit in a day |
| D25 | Report must include "what NOT to create" | A recommendation engine with no stop list generates infinite work |

---

## 5. Known limitations

1. **Sampling bias.** Reddit and YouTube commenters are not the audience; they are the vocal, public part of it. Every insight is about *what is said publicly*, and reports must not silently generalize to "users".
2. **Absence is unprovable.** Coverage claims are scoped to what was examined. `silent` gaps always require manual verification before a public claim.
3. **Small-N reality.** A niche audience produces 5–20 relevant items a day. Most weeks will honestly report "stable". Users expecting weekly drama will be disappointed; that is correct behaviour.
4. **Trend math needs 6+ weeks.** Phases are data-gated, not effort-gated.
5. **Segment inference is weak.** Confidence rarely exceeds 0.65 from text alone. Segments are priors, not labels.
6. **Engagement metrics are inconsistent** across platforms and often absent. They are modifiers, never primary factors.
7. **Content performance attribution is directional forever at this scale.** No statistical claims below n=10 per arm.
8. **English-first.** Multi-language is schema-ready and Phase 5-gated; verbatim capture in other languages works, interpretation quality does not.
9. **No private signal.** The highest-value conversations (DMs, private communities, support tickets) are permanently out of scope by design.
10. **LLM drift.** Model updates change extraction behaviour. Prompt versioning + golden-set CI catch it; nothing prevents it.
11. **The review queue is the bottleneck.** If the human stops reviewing, quality plateaus and then degrades. Queue size is capped at 20/week for exactly this reason.

---

## 6. Implementation order

```text
M1  Project foundation          M8   Topic clustering
M2  Source configuration        M9   Frequency + trends
M3  Reddit adapter              M10  Competitor monitoring
M4  YouTube adapter             M11  Opportunity engine
M5  Storage + dedup             M12  Weekly radar
M6  Relevance gate + embeddings M13  Content Engine integration
M7  Insight extraction
```

Parallelizable: M3 ∥ M4 (after M2); M9 ∥ M10 (after M8). Everything else sequential. Full detail: `04-system/implementation-plan.md`.

---

## 7. Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| LLM cost blowout | High | Cheap gate + hard cap + cache + batching, all in M6 | Engineering |
| Insight quality too low to trust | Fatal | Golden sets in CI, verbatim verification, review queue, calibration report | Product |
| Clustering instability corrupts trends | High | Stable IDs, bias to over-split, stability test in M8 | Engineering |
| User abandons the review queue | High | 20-item cap, radar links directly to it, engagement tracked as a metric | Product |
| Platform API changes / access revoked | Medium | Adapter isolation, capability declarations, graceful `unsupported` | Engineering |
| False "nobody covers this" claim published | Medium-High | Scoped claims, `claims_requiring_verification`, export gating | Product |
| Over-collection producing noise | Medium | Relevance-rate health band (20–45%), monthly source audit | Product |
| Privacy/ToS violation | Fatal | No-bypass rules enforced in config validation, hashed authors, retention limits | Engineering |
| Scope creep into a BI tool | Medium | One-page report constraint; MVP scope frozen here | Product |
| Trend claims on thin data | Medium | 28-day gate, four guards, banned word "significant" in generated prose | Engineering |

---

## 8. Questions that must be answered before production

**Product**
1. Who is the first real user, and what is their audience? Everything else follows from a concrete audience definition.
2. What is the acceptable monthly cost ceiling for that user? (Default cap US$30 — confirm.)
3. Which metric will judge content performance (saves, watch-through, signups)? Needed for `radar outcome`.
4. Is the review queue a daily habit or a weekly ritual? Changes the queue cap and radar cadence.

**Legal / compliance**
5. Confirm current ToS positions for Reddit API, YouTube Data API, and any review site (Phase 5) regarding storage and derived analysis. **Blocking for Phase 5 review mining; not blocking for M1–M13.**
6. Retention: is 180 days right for raw payloads in the target jurisdiction?
7. Does displaying ≤15-word verbatim quotes with attribution meet the user's own legal comfort? (Paraphrase-only mode should be a config flag if not.)

**Technical**
8. Which LLM provider and which two tiers? Affects cost model and prompt tuning, not architecture.
9. Local embeddings adequate, or is a hosted embedding model required for quality? Measure at M6 against the golden set.
10. Where does this run — the user's laptop or a small always-on box? Affects scheduler choice only.
11. Is X access available at any usable tier? If not, the adapter stays flagged off permanently.

**Open design questions (stub behind an interface; do not block)**
12. Multi-audience isolation model for Phase 5 — one DB with `audience_id` scoping (current assumption) or one DB per audience.
13. Whether rejection feedback should adjust embeddings, prompts, or both. Measure before choosing.
14. Whether competitor performance data is reliable enough to keep as a scoring input at all, or should become display-only.

---

## 9. Instructions for the Antigravity coding agent

**Read in this order:** this file → `04-system/implementation-plan.md` → `04-system/data-model.md` → `04-system/scoring-system.md` → `04-system/architecture.md`. Read the insight-type docs when you implement the corresponding extraction.

**Then:**

1. **Implement milestone by milestone, in order.** Do not start M(n+1) until M(n)'s acceptance criteria demonstrably pass. The order encodes dependency, not preference.
2. **Treat acceptance criteria as tests.** Each is verifiable; write the test first where practical.
3. **Never let a model produce a number.** Counts, frequencies, scores, and classifications come from code. If you find yourself parsing a number out of an LLM response for anything except a rubric rating, stop.
4. **Implement verbatim verification (M7) before any extraction ships.** It is the cheapest, highest-value hallucination control in the system.
5. **Enforce the layer rule.** Analysis code may read normalized tables and write analysis tables. It may never update them. Add the check to code review.
6. **Never implement a bypass.** No login automation, no CAPTCHA handling, no headless-browser evasion, no paywall circumvention, no ignoring robots.txt — including "temporarily, for testing". If a source can't be collected legally, return `SourceUnsupported(reason)` and surface it.
7. **Cost controls ship in M6, not later.** Cap, cache, batch, and meter before the first extraction run.
8. **Prefer more clusters to fewer.** When merge confidence is uncertain, don't merge.
9. **Default to reject** on relevance errors and **to abstain** on extraction uncertainty. A missed insight costs one item; a fabricated one costs trust.
10. **Keep the CLI honest.** Every command that spends money prints an estimate and asks for confirmation above US$1.00.
11. **Record deviations in `DECISIONS.md`** with the reason. APIs and libraries will have moved since this was written; implement the intent, document the difference, keep going.
12. **Do not add features not in the plan.** No dashboards, no notifications beyond the radar, no extra platforms, no "while I'm here" abstractions. Scope discipline is the difference between a working M13 and an abandoned M7.

**Definition of done for the whole build:** a scheduled unattended run collects from three platforms, produces a caveated weekly radar with 100% resolvable evidence, stays under the cost cap, and a human can promote or reject every insight it proposes.

---

## 10. Consistency check

Verified across this package:

- Insight lifecycle is identical everywhere: `detected → analyzed → candidate → reviewed → trusted → archived`, plus `rejected`.
- Score ranges (0–100 integers) and bands (0–24 / 25–49 / 50–74 / 75–100) are used uniformly; confidence is 0.00–1.00 with bands at 0.50 and 0.75.
- Evidence floors match across documents: pains ≥3 distinct authors + ≥2 platforms; gaps ≥5 authors + ≥50 items examined; opportunity classes per `product-opportunities.md §2`.
- The opportunity formula appears in `content-opportunities.md §2` and `scoring-system.md §8` in identical form; the worked example resolves to 60, and the stored sample record notes that it uses different stored inputs.
- Time windows (aligned ISO weeks, 90-day baseline, 28-day gate) are consistent in `emerging-topics.md`, `workflows.md`, and `scoring-system.md`.
- Quote policy (≤15 words, one per source, ≤3 per insight, paraphrase preferred) is identical in `audience-pains.md`, `audience-language.md`, `competitors.md`, and the data model constraint.
- Retention (raw 180 days, insights indefinite) matches in `architecture.md`, `data-model.md`, and `workflows.md`.
- Precedence rule for any remaining conflict: `scoring-system.md` (numbers) > `data-model.md` (shapes) > this file (decisions) > everything else.
