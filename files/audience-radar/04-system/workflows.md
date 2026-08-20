# Workflows

Every scheduled and on-demand process. Each workflow specifies trigger, inputs, steps, outputs, idempotency, failure handling, and acceptance criteria.

**Universal properties:**
- Every workflow is **idempotent**: re-running produces no duplicates and no double-spend.
- Every workflow writes a job record (start, end, status, counts, cost).
- Every workflow can run standalone via CLI (`radar <workflow>`), which is how debugging stays cheap.
- Failure of one source, item, or agent never aborts a workflow; failures are recorded and reported.

---

## 1. Daily collection workflow

**Trigger:** scheduler, per-source `collection_frequency` (default 03:00 local, staggered by source to spread API load).

```text
Schedule
  → Load sources (validated config; skip disabled/failed/missing-credential)
  → Build plan (Collector Agent: priority order, quota allocation)
  → For each source:
        → adapter.collect(cursor, window, max_items)
        → persist RawPayload (immutable, gzip)
        → normalize → Conversation / Comment / Author / Content
        → deduplicate (hash → simhash → semantic)
        → advance cursor ONLY over persisted items
  → Write CollectionJob records
  → Update source health
```

**Steps in detail**

1. **Load & validate** — a config error fails loudly before any network call.
2. **Plan** — quota-constrained platforms allocate by priority; 10% held back for manual runs.
3. **Collect** — per adapter, respecting rate limits (token bucket) and `Retry-After`. 3 retries with exponential backoff + jitter.
4. **Persist raw first** — before any parsing. If normalization has a bug, the data is still there.
5. **Normalize** — canonical shapes; whitespace and entity cleanup only. Audience wording untouched.
6. **Dedup** —
   - L1 exact `body_hash` → drop
   - L2 `simhash` Hamming ≤3 → mark `is_duplicate_of`, keep row
   - L3 semantic cosine ≥0.93 within 30 days → mark `is_duplicate_of`
7. **Cursor advance** — only after successful persistence, inside the same transaction.

**Outputs:** new `Content` rows ready for analysis; `CollectionJob` records; updated health.

**Failure handling**

| Failure | Behaviour |
|---|---|
| Rate limit | Honour `Retry-After`, requeue remainder to the next run |
| Quota exhausted | Stop that platform for the day; log; reallocate tomorrow |
| Auth error | Fail loudly; surface in `radar doctor` and the radar footer |
| Parse error | Persist raw, quarantine the item, continue |
| Source 404/gone | Increment `consecutive_failures`; auto-disable at 3 with an audit entry |

**Acceptance:** running twice back-to-back creates zero new items the second time. Killing the process mid-run and restarting loses nothing and duplicates nothing.

---

## 2. Insight workflow

**Trigger:** after collection completes (or hourly over any unanalyzed backlog).

```text
New Content
  → Relevance gate (3 stages)
  → AI analysis (extraction, cheap tier, batched)
  → Verbatim verification
  → Embedding
  → Topic clustering
  → Insight upsert (merge or create)
  → Evidence linking
  → Scoring
  → Lifecycle transition
```

**Relevance gate**

| Stage | Method | Cost | Outcome |
|---|---|---|---|
| 1 | Rules: exclusion keywords, min length (<15 words), bot signatures, age, `not_our_audience` terms, creator authorship | free | ~40% rejected |
| 2 | Embedding similarity to the audience profile + source anchors → preliminary 0–100 | ~free | ≥70 pass · <40 reject · 40–69 grey |
| 3 | Relevance Agent on the grey zone, batched 10/call | cheap | final score |

**Analysis** — only items scoring ≥`min_relevance_score`. Cache key `(text_hash, prompt_version)`; hits cost nothing.

**Verbatim verification** — every `exact_phrasing` must string-match the source. Non-matching extractions are discarded and counted (a rising discard rate is an early warning that the model or prompt has drifted).

**Insight upsert** — the critical step:
```text
for each extracted insight:
    embed → find nearest existing insight of the same type (same audience)
    if cosine >= 0.88 and category compatible:
        → adjudicate (reasoning tier) → if same: UPDATE (frequency, evidence, last_detected, version++)
    elif cosine >= 0.80: → queue merge proposal for human review; create as separate candidate
    else: → CREATE new insight in `detected`
```

**Evidence linking** — every insight gets an `Evidence` row per contributing item, with URL snapshotted at creation.

**Lifecycle** — promotion to `candidate` requires the thresholds in each insight-type doc (`≥3 distinct authors`, `≥2 platforms` for pains). Promotion to `trusted` is human-only.

**Failure handling:** invalid JSON → one repair retry → quarantine. Budget exceeded → stop analysis, mark the batch `partial`, continue collecting. Embedding failure → retry next run; the item stays queued.

**Acceptance:** the same item analyzed twice produces one `ItemAnalysis` per prompt version and zero duplicate insights. Rejected items never reach the LLM.

---

## 3. Trend workflow

**Trigger:** weekly, Monday 06:00 UTC, after the week's collection is complete.

```text
Historical data
  → Aggregate by (topic, aligned week)     distinct-author-weighted
  → Compute windows: T0, T-1, 90d baseline (mean, stdev)
  → Compute growth_rate, velocity, acceleration, z_score, share_of_voice
  → Compute guards: small-N, concentration, single-thread, spike
  → Classify (rule engine, emerging-topics.md §3)
  → Trend Agent: narrative + caveats
  → Persist immutable Trend row per (topic, window_end)
```

**Preconditions:** ≥28 days of data, else everything is `insufficient_baseline` and the radar says "baseline building — week N of 4". `window_completeness < 0.8` → `data_incomplete` for affected platforms.

**Idempotency:** `(topic_id, window_end)` unique; recomputation of a completed window must produce identical results, which is a CI test with fixed fixtures.

**Acceptance:** a topic with 1→4 mentions is classified `stable` with `below_detection_floor`, not `+300% emerging`. A single 60-comment thread does not create a trend.

---

## 4. Competitor workflow

**Trigger:** weekly (or per-competitor `monitoring_frequency`), before the gap workflow.

```text
Competitor sources
  → Collect (blog_feed → sitemap → YouTube API; never HTML-crawl around a missing feed)
  → Normalize into CompetitorContent
  → Assign to the SAME topic clusters as audience data
  → Compute depth, recency, engagement percentile (within own catalogue)
  → Competitor Agent: coverage characterization, offers, positioning language
  → Compute CompetitorCoverage per (competitor, topic)
  → Record data_quality and uncollectable surfaces explicitly
```

**Then, gap detection:**

```text
for each topic with demand_score >= 45:
    join demand (audience side) with market_coverage (supply side)
    classify gap_type (competitor-gaps.md §6)
    Gap Agent: explain, list unanswered questions, name what needs manual verification
    score, apply evidence + coverage-reliability multipliers, apply business veto
    dedup against open gaps (8-week window) → update or create
```

**Failure handling:** an uncollectable surface sets `data_quality: partial/unavailable` and caps downstream gap confidence. **Missing data must never be recorded as zero coverage** — the single most consequential rule in this workflow.

**Acceptance:** a competitor with no collectable surface produces no `silent` gaps. Every absence claim in the output carries a window and an item count.

---

## 5. Weekly radar workflow

**Trigger:** Monday 07:00 local, after trend and gap workflows.

```text
Insights + Trends + Competitor data + Opportunities
  → Verify completeness (collection ≥80%, else annotate)
  → Generate opportunities (Opportunity Agent + scoring)
  → Rank per section; diversify (max 2 per cluster)
  → Assemble structured payload (numbers computed, caveats collected)
  → Radar Agent: compose prose from the payload ONLY
  → Validate: numerals ⊆ payload · IDs exist · quotes match AudiencePhrase · ≤900 words
  → Write knowledge/radar/<ISO-week>.md · update index · notify
  → Refresh review queue
```

**Failure handling**

| Condition | Behaviour |
|---|---|
| Validation fails | Regenerate once, then fall back to templated tables without prose |
| No new insights | Short radar stating so + source-health diagnosis. Never fabricate |
| Cost cap reached | Compose from existing data, mark `partial` |
| Collection incomplete | Publish with a banner; suppress trend claims for affected platforms |

**Acceptance:** the radar is produced every week without exception, including weeks where the honest answer is "nothing changed".

---

## 6. Human review workflow

**Trigger:** on demand (`radar review`), prompted by the weekly radar.

```text
Review queue (candidates, ranked by score × confidence, capped at 20)
  → for each: show claim, evidence links, contradicting evidence, computed scores
  → human action: promote | edit | reject | merge | defer
  → write ReviewAction (append-only)
  → apply state transition
  → feed rejections into the relevance/extraction feedback store
```

State machine (all insight types):

```text
detected ──► analyzed ──► candidate ──► reviewed ──► trusted ──► archived
                 │            │            │             │           │
                 └──────► rejected ◄───────┴─────────────┘           │
                                                                     ▼
                                              (new evidence) ──► candidate
```

Rules: only humans create `trusted`. Archived insights reopen to `candidate`, never straight to `trusted`. Rejections require a reason code. Edits are recorded field-by-field — the diff between what the system said and what the human meant is the most valuable training data the product generates.

**Feedback application (Phase 2):** after ≥15 rejections, rejected items form a negative centroid used in relevance stage 2 (weight capped at 0.2), plus few-shot negatives in the Relevance Agent prompt. Effect is measured against the audited false-positive rate; if precision does not improve, the loop is disabled rather than tuned blindly.

---

## 7. Maintenance workflows

| Workflow | Trigger | Does |
|---|---|---|
| **Retention sweep** | Daily 04:00 | Delete expired raw payloads, null author identifiers, truncate bodies, set `evidence_expired` |
| **Evidence integrity** | Daily | Verify every `candidate`+ insight has resolvable evidence; quarantine failures; alert |
| **Cost reconciliation** | Daily | Aggregate `CostLedger`; warn at 80% of cap; enforce at 100% |
| **Source health review** | Weekly | Flag stale/failing sources; auto-disable at 3 consecutive failures |
| **Cluster maintenance** | Weekly | Recompute centroids, cohesion; propose splits/merges to review |
| **Monthly source audit** | Monthly | Per source: items, relevance rate, **trusted insights produced**, cost share → keep/tighten/cut |
| **Calibration report** | Monthly | Stated confidence vs human accept rate; flag systematic over/under-confidence |
| **Backup** | Daily | Copy `radar.db` + commit `knowledge/` |

---

## 8. Cold start (new audience)

```text
radar init
  → interactive audience definition (description, goals, not-our-audience, segments)
  → source suggestions (advisory; human approves every one)
  → credential check (radar doctor)
radar backfill --days 30
  → collect historical data where platforms permit
  → analyze in batches with an explicit cost estimate shown BEFORE starting
  → build initial clusters
  → NO trend classification (baseline insufficient — stated plainly)
radar review
  → first candidate batch; rejections here are the highest-value signal the system will get
radar radar --now
  → first report, labelled "baseline building — week 1 of 4"
```

Expected cold-start cost for 30 days across 8 sources: US$3–8. The estimate is shown and confirmed before spending, every time.

---

## 9. CLI surface

```bash
radar doctor                          # config, credentials, quota, schedule, DB health
radar sources list|test <id>|add      # config management
radar collect [--source <id>] [--all] [--since <date>]
radar analyze [--limit N] [--no-llm]
radar cluster [--rebuild]
radar trends [--week <iso>]
radar competitors scan
radar gaps
radar opportunities [--top 10]
radar radar [--now] [--week <iso>]    # generate report
radar review [--type pain] [--limit 20]
radar export --opportunity <id> --format brief|json
radar outcome --opportunity <id> --url <url> --metric saves=340
radar metrics [--month 2026-08]
radar purge --source <id>|--author <hash>|--before <date>
radar cost [--month]
```

Every command is safe to re-run. Every command that spends money prints an estimate and requires confirmation above a configurable threshold (default US$1.00).
