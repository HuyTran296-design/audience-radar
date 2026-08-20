# Implementation Plan (for the Antigravity coding agent)

Thirteen milestones. **Build them in order.** Each has an objective, files to create, dependencies, inputs/outputs, acceptance criteria, tests, and failure modes. A milestone is done when its acceptance criteria pass — not when the code looks finished.

**Standing instructions**

1. Working software over abstraction. One concrete implementation before any base class. Extract the abstraction on the second implementation, not the first.
2. No speculative interfaces. If the plan doesn't call for it, don't build it.
3. Every milestone ends with a runnable CLI command and passing tests.
4. Never break the layer rule: data flows down. Analysis never mutates normalized data.
5. Never implement a collection method that bypasses auth, anti-bot, paywalls, or robots.txt. If a source can't be collected legally, return `SourceUnsupported` with a reason.
6. Numbers come from code, never from a model.
7. When this plan and reality disagree (an API changed, a library moved), implement the *intent*, document the deviation in `DECISIONS.md`, and keep going.

**Repo scaffold** (create at M1, fill in progressively): see `04-system/architecture.md §2`.

---

## Milestone 1 — Project foundation

**Objective:** a runnable skeleton with config, storage, logging, and cost accounting.

**Create:** `pyproject.toml` · `audience_radar/cli.py` · `config/{loader,models,credentials}.py` · `storage/{db,models,repositories}.py` + `migrations/` · `observability/{logging,cost}.py` · `config/audience.yaml`, `config/sources.yaml` (examples from `01-sources/sources.md`)

**Depends on:** nothing.
**Inputs:** the schemas in `04-system/data-model.md`.
**Outputs:** `radar doctor` reports config validity, DB status, credential presence.

**Acceptance**
1. `radar doctor` runs on a clean checkout and reports honestly.
2. Invalid config fails with a message naming the file, field, and line.
3. Migrations create every table in the data model; `alembic downgrade base` then `upgrade head` works.
4. Structured JSON logs to stdout with run IDs.
5. `CostLedger` exists with a working monthly-cap check (`--dry-run` proves enforcement).
6. Secrets resolve from env/keyring; inline secrets in YAML are rejected.

**Tests:** config validation (valid, unknown field, missing required, inline secret, bad regex); migration up/down; cost cap enforcement.

**Failure modes:** over-engineering config inheritance (keep it one level); putting secrets in YAML; skipping migrations "for now" (you will regret it at M5).

---

## Milestone 2 — Source configuration

**Objective:** sources load, validate, and persist with health tracking.

**Create:** `config/models.py` (SourceConfig, AudienceProfile) · `storage/repositories.py` (SourceRepository) · CLI `radar sources list|show|test|validate`

**Depends on:** M1.
**Outputs:** `Source` rows with `config_hash`; validation errors per `01-sources/sources.md §5`.

**Acceptance**
1. The 10-source example config loads without error.
2. All 10 validation rules produce specific, actionable errors.
3. `radar sources list` shows id, platform, priority, frequency, health.
4. Changing config updates `config_hash`; the change is visible in `AuditLog`.
5. `robots_respect: false` is rejected.

**Tests:** each validation rule; config-drift detection; enable/disable round-trip.

**Failure modes:** silently ignoring unknown fields (a typo in `exclusion_keywords` would then quietly disable filtering — fail loudly instead).

---

## Milestone 3 — Reddit adapter

**Objective:** the first real data end-to-end.

**Create:** `collection/adapters/{base,reddit}.py` · `collection/{runner,ratelimit}.py` · `normalize/{canonical,clean}.py` · CLI `radar collect --source <id>`

**Depends on:** M2.
**Inputs:** Reddit OAuth credentials; subreddit + keyword sources.
**Outputs:** `RawPayload`, `Conversation`, `Comment`, `Author`, `CollectionJob` rows.

**Acceptance**
1. Collects posts + comments from a real subreddit into all five tables.
2. Cursor resumes correctly: second run collects only new items.
3. Rate limits respected; 429 honours `x-ratelimit-reset`.
4. Private/banned subreddit → `SourceUnsupported`, not a crash.
5. `[deleted]` authors and bodies handled without null-pointer errors.
6. Raw payloads stored gzipped and are never mutated (trigger-enforced).
7. Author identifiers hashed with the install salt in the normalized layer.

**Tests:** recorded fixtures for listing, comments, `MoreComments`, 429, 403, deleted content; idempotency (run twice → 0 new); cursor resume after simulated crash.

**Failure modes:** parsing before persisting raw; advancing the cursor before persistence; treating `hot` as deterministic; unbounded `MoreComments` expansion (cap it, breadth-first).

---

## Milestone 4 — YouTube adapter

**Objective:** second platform, under a hard quota.

**Create:** `collection/adapters/youtube.py` · `collection/quota.py` · quota ledger

**Depends on:** M3 (reuse runner and normalization).

**Acceptance**
1. Channel collection uses the **uploads playlist**, not `search.list` (verified in tests by asserting quota units used ≤5 for a channel run).
2. Comment threads collected with pagination up to `max_comments_per_item`.
3. Quota ledger tracks units; stops at 90% of daily limit; allocates by source priority.
4. `commentsDisabled` handled as a normal state, not an error.
5. Keyword search costs are estimated and shown before running.

**Tests:** fixtures for playlist, comment threads, disabled comments, `quotaExceeded`; quota accounting assertions per call type.

**Failure modes:** using `search.list` for channel enumeration (100× cost); retrying after `quotaExceeded`; assuming `order=relevance` is stable for pagination.

---

## Milestone 5 — Raw conversation storage + dedup

**Objective:** clean, deduped, retained data.

**Create:** `normalize/dedup.py` · `storage/retention.py` · `normalize/language.py` · CLI `radar purge`

**Depends on:** M3, M4.

**Acceptance**
1. Three dedup layers work: exact hash, simhash (Hamming ≤3), semantic (deferred to M6 for the vector part — stub with a TODO and wire it at M6).
2. Duplicates are marked (`is_duplicate_of`), never deleted — auditability requires the row.
3. Retention sweep deletes expired raw payloads, nulls author identifiers, truncates bodies.
4. `radar purge --source <id>` hard-deletes and quarantines dependent insights.
5. Language detection populates `detected_language`.
6. Dedup rate is reported per layer.

**Tests:** identical, near-identical (whitespace/quote/emoji variants), crossposts, retention expiry, purge cascade.

**Failure modes:** deleting duplicates (breaks evidence); "cleaning" text so aggressively that audience wording changes — normalize whitespace and entities only.

---

## Milestone 6 — Relevance gate + embeddings

**Objective:** cheap filtering before any expensive call. **The most important cost decision in the system.**

**Create:** `analysis/{embeddings,relevance,llm}.py` · `analysis/prompts/relevance.v1.md` · CLI `radar analyze --relevance-only`

**Depends on:** M5.

**Acceptance**
1. Three stages implemented per `scoring-system.md §2`, each recording which stage decided.
2. Stage 1 rejects ≥30% of a real corpus at zero cost.
3. Stage 3 fires only on the 40–69 band, batched 10 per call.
4. Cosine rescaling from the practical range is implemented (not raw cosine).
5. Semantic dedup (L3) wired using the same embeddings.
6. Every LLM call writes to `CostLedger`; cache hits by `(text_hash, prompt_version)` cost nothing.
7. `--no-llm` runs stages 1–2 only and still produces scores.
8. Measured relevance rate on real data lands in 20–45%; if not, tune config before code.

**Tests:** golden set of 50 hand-labelled items — precision ≥0.8, recall ≥0.7; cache hit produces zero ledger entries; budget exceeded raises `BudgetExceeded` without data loss.

**Failure modes:** sending everything to the LLM (cost blowout on day one); using raw cosine (no resolution); defaulting to *accept* on error — default to reject.

---

## Milestone 7 — AI insight extraction

**Objective:** structured insights with verifiable evidence.

**Create:** `analysis/extraction.py` · `analysis/prompts/insight.v1.md` · `insights/{models,evidence}.py` · CLI `radar analyze`

**Depends on:** M6.

**Acceptance**
1. Extraction returns strict JSON matching the schema in `agents.md §3`.
2. **Verbatim verification:** every `exact_phrasing` string-matches the source; non-matching extractions are discarded and counted.
3. PII redaction runs before storage (names, employers, locations, health disclosures).
4. `Evidence` rows created for every contributing item, URL snapshotted.
5. Malformed JSON → one repair retry → quarantine with an error, never silent drop.
6. `insufficient_signal: true` is common and handled as success.
7. Extraction rate on relevant items ≥60%.

**Tests:** golden set of 50 items with expected extractions; fabricated-quote injection is caught by verbatim verification; malformed JSON path; PII redaction.

**Failure modes:** allowing quotes >15 words; letting the model output counts; accepting extractions without evidence links; treating `insufficient_signal` as failure and retrying (wastes money).

---

## Milestone 8 — Topic clustering

**Objective:** many phrasings → one topic, stably, across weeks.

**Create:** `analysis/clustering.py` · `analysis/prompts/clustering.v1.md` · `insights/merge.py` · CLI `radar cluster [--rebuild]`

**Depends on:** M7.

**Acceptance**
1. HDBSCAN over embeddings with tuned `min_cluster_size` (start at 4).
2. **Stability:** re-running assigns existing topic IDs; new topics only for genuinely new content. Verified by re-running on identical data → zero new topic IDs.
3. Merge rules: auto ≥0.88 + adjudication; 0.80–0.88 → review queue; <0.80 never.
4. Split proposal when cohesion <0.6; never automatic.
5. Noise points stay unclustered — that is correct behaviour, not a bug to tune away.
6. `supersedes`/`superseded_by` maintained so trend history survives merges.

**Tests:** the three paraphrases from the brief ("I don't know which AI tool to use" / "There's too many AI tools" / "I can't decide between Claude and ChatGPT") land in one cluster; stability test; merge adjudication; split proposal.

**Failure modes:** over-merging (irreversible trend damage — bias toward more clusters); regenerating topic IDs each run (destroys every trend); clustering raw text instead of embeddings.

---

## Milestone 9 — Frequency + trend detection

**Objective:** honest momentum.

**Create:** `scoring/{frequency,trend}.py` · `analysis/prompts/trend.v1.md` · CLI `radar trends`

**Depends on:** M8 + ≥28 days of data (use a synthetic time series to develop, real data to validate).

**Acceptance**
1. Distinct-author-weighted frequency with the 3-per-author cap.
2. Aligned ISO-week windows; `window_completeness` computed.
3. All classification rules from `emerging-topics.md §3` in order, with all four guards.
4. `insufficient_baseline` before 28 days — no trend claims, no exceptions.
5. `Trend` rows immutable per `(topic_id, window_end)`; recomputation is deterministic.
6. The Topic A / Topic B worked example reproduces exactly (`emerging-topics.md §8`).

**Tests:** the worked example as a fixture; small-N guard (1→4 mentions = stable); single-thread guard; misaligned-window detection; determinism on recompute.

**Failure modes:** percentages on tiny bases; unequal windows; mutable trend rows; classifying before the baseline exists.

---

## Milestone 10 — Competitor monitoring

**Objective:** coverage mapped into the same topic space.

**Create:** `config/models.py` (CompetitorConfig) · `collection/adapters/{rss,website}.py` · `competitors/coverage.py` · `analysis/prompts/competitor.v1.md` · CLI `radar competitors scan`

**Depends on:** M8 (shared topic space is the whole point).

**Acceptance**
1. RSS adapter with ETag/`If-Modified-Since`; website adapter honours robots.txt and `Crawl-delay`.
2. Competitor content assigned to **existing audience topics** (≥80% assignment rate).
3. Coverage score per `competitors.md §5`; depth percentile computed within the competitor's own catalogue.
4. `data_quality` set honestly; uncollectable surfaces recorded, not treated as zero coverage.
5. No verbatim storage beyond a ≤15-word attributed phrase; summaries are system-written.
6. Stale pricing (>90 days) flagged.

**Tests:** feed fixtures; robots.txt disallow → no fetch; missing feed → `data_quality: partial`, no crawl fallback; topic assignment.

**Failure modes:** HTML-crawling around a missing feed; comparing depth across competitors; treating missing data as absence of coverage.

---

## Milestone 11 — Opportunity engine

**Objective:** ranked, decision-ready recommendations.

**Create:** `competitors/gaps.py` · `scoring/{pain,intent,competition,opportunity,confidence,bands}.py` · `analysis/prompts/{gap,opportunity}.v1.md` · `insights/lifecycle.py` · CLI `radar gaps`, `radar opportunities`, `radar review`

**Depends on:** M9, M10.

**Acceptance**
1. Every formula in `scoring-system.md` implemented as a pure function with unit tests.
2. The worked calculation in `content-opportunities.md §2.5` reproduces exactly (result: 60).
3. All four vetoes applied; `business_relevance < 30` routes to "what NOT to create".
4. Gaps require both-sided evidence; `silent` requires ≥50 items examined.
5. Product opportunities enforce the class thresholds in `product-opportunities.md §2`; below threshold → `signal_only`.
6. Review queue works: promote/edit/reject/merge/defer, each writing an immutable `ReviewAction`.
7. Only humans can set `trusted` — attempting it programmatically raises.
8. Diversification: max 2 opportunities per cluster in a top-5.

**Tests:** every scoring function against worked examples; veto paths; threshold gates for each opportunity class; review state machine including illegal transitions.

**Failure modes:** letting an LLM produce scores; additive competition penalty; skipping the diversification rule; allowing export of non-trusted records.

---

## Milestone 12 — Weekly radar

**Objective:** the artifact the user actually reads.

**Create:** `reporting/{radar,knowledge,metrics,review}.py` · `reporting/templates/` · `analysis/prompts/radar.v1.md` · `collection/scheduler.py` · CLI `radar radar`

**Depends on:** M11.

**Acceptance**
1. All ten sections in fixed order; ≤900 words; empty sections say "Nothing this week".
2. **Numeric validation:** every numeral in the output exists in the payload — a draft that fails is regenerated once, then falls back to templated tables.
3. ID validation and quote validation pass; quotes match `AudiencePhrase.exact_text`.
4. Written to `knowledge/radar/<ISO-week>.md`; index updated; `knowledge/` is a git repo.
5. Scheduler runs collection → analysis → trends → gaps → radar unattended, twice.
6. Degraded modes produce a caveated report, never nothing.
7. Footer shows collection rate, cost, review-queue size.

**Tests:** hallucinated-numeral injection is caught; empty-week path; incomplete-collection banner; cost-cap path; word-count enforcement; end-to-end scheduled run on fixtures.

**Failure modes:** letting the model recall numbers from earlier context; padding empty sections; skipping the "what NOT to create" section (it's mandatory).

---

## Milestone 13 — Content Engine integration

**Objective:** opportunities leave the system safely.

**Create:** `integration/content_engine.py` · schema `opportunity.v1` · CLI `radar export`, `radar outcome`

**Depends on:** M12.

**Acceptance**
1. `opportunity.v1` matches `content-opportunities.md §5` exactly; contract tests both directions.
2. Export requires `status: trusted`, 100% evidence integrity, guardrails attached, `blocked: false` — all four enforced.
3. `claims_requiring_verification` and `do_not_say` travel with every export.
4. Brief generation produces a usable document with an evidence appendix.
5. `radar outcome` records published URL + metrics into `Opportunity.outcome`.
6. Attribution report links insight types to published performance (labelled directional while n is small).

**Tests:** export gating (each precondition blocks independently); schema round-trip; outcome ingestion; guardrail propagation.

**Failure modes:** exporting candidates; dropping guardrails at the boundary; breaking the schema instead of versioning it.

---

## Build order dependency graph

```text
M1 ──► M2 ──► M3 ──┬──► M5 ──► M6 ──► M7 ──► M8 ──┬──► M9 ──┐
              M4 ──┘                               └──► M10 ─┴──► M11 ──► M12 ──► M13
```

M3 and M4 can run in parallel after M2. M9 and M10 can run in parallel after M8. Everything else is strictly sequential.

## Definition of done (every milestone)

- [ ] Acceptance criteria pass, demonstrably, on real or fixture data
- [ ] Tests written and passing; no network calls in CI
- [ ] A CLI command exercises the feature end-to-end
- [ ] Errors are handled per the failure-modes list, not by crashing
- [ ] Costs (if any) are metered and capped
- [ ] Deviations from this plan recorded in `DECISIONS.md`
- [ ] No layer violation introduced (analysis never mutates normalized data)
