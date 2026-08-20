# System Architecture

## 1. Layer overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│ SOURCE LAYER        sources.yaml · competitors.yaml · audience profile│
├──────────────────────────────────────────────────────────────────────┤
│ COLLECTION LAYER    adapters · scheduler · cursors · rate limits      │
├──────────────────────────────────────────────────────────────────────┤
│ NORMALIZATION LAYER canonical shapes · dedup (hash→simhash→semantic)  │
├──────────────────────────────────────────────────────────────────────┤
│ STORAGE LAYER       raw (immutable) · normalized · analysis · aggregate│
├──────────────────────────────────────────────────────────────────────┤
│ AI ANALYSIS LAYER   relevance gate · extraction · embeddings · cluster│
├──────────────────────────────────────────────────────────────────────┤
│ INSIGHT LAYER       pains · questions · objections · phrases · topics │
├──────────────────────────────────────────────────────────────────────┤
│ SCORING LAYER       relevance · pain · frequency · trend · intent ·   │
│                     competition · opportunity · confidence            │
├──────────────────────────────────────────────────────────────────────┤
│ REPORTING LAYER     weekly radar · knowledge base · review queue      │
├──────────────────────────────────────────────────────────────────────┤
│ INTEGRATION         opportunity.v1 export → Content Engine            │
└──────────────────────────────────────────────────────────────────────┘
```

### Layer responsibilities

| Layer | Owns | Must not |
|---|---|---|
| **Source** | Config parsing, validation, audience/competitor definitions, credential resolution | Contain business logic or make network calls |
| **Collection** | Adapter execution, scheduling, cursors, retries, rate limits, quota accounting, raw persistence | Interpret content, filter on relevance, or transform payloads |
| **Normalization** | Canonical `Conversation`/`Comment`/`Author`, text cleaning (whitespace, entity decoding), dedup, language detection | Discard the raw payload, "fix" the audience's wording, or call an LLM |
| **Storage** | Persistence, migrations, retention, integrity constraints, append-only guarantees | Contain analysis logic |
| **AI Analysis** | Relevance gating, embeddings, structured extraction, clustering, LLM budget enforcement | Write to raw or normalized tables |
| **Insight** | Insight records, merges, lifecycle transitions, evidence linking | Compute scores (delegates) or write reports |
| **Scoring** | Every formula in `scoring-system.md`, deterministically and testably | Call an LLM. **Scoring is pure functions over stored data** |
| **Reporting** | Radar generation, knowledge base rendering, review queue, metrics | Create insights or invent numbers |
| **Integration** | `opportunity.v1` export, outcome ingestion | Export anything not `trusted` |

**The one architectural rule that matters:** data flows down, never up. The AI Analysis layer reads normalized data and writes analysis records; it never mutates what it read. This makes every result reproducible, every bad prompt fixable by re-running one layer, and every insight auditable.

---

## 2. MVP architecture: modular monolith

One Python process, one SQLite file, one CLI. No services, no queues, no containers required.

```text
audience_radar/
├── cli.py                     # Typer entrypoints
├── config/
│   ├── loader.py              # YAML → validated models, precise error messages
│   ├── models.py              # Pydantic: AudienceProfile, SourceConfig, CompetitorConfig
│   └── credentials.py         # env/keyring resolution; never inline secrets
├── collection/
│   ├── scheduler.py           # APScheduler wiring, job registry
│   ├── runner.py              # orchestrates a collection run per source
│   ├── ratelimit.py           # token bucket per platform + quota ledger
│   └── adapters/
│       ├── base.py            # the interface in source-adapters.md
│       ├── reddit.py  youtube.py  rss.py  x.py  website.py
├── normalize/
│   ├── canonical.py           # payload → Conversation/Comment/Author
│   ├── clean.py               # whitespace, entities, boilerplate stripping
│   ├── dedup.py               # exact hash → simhash → semantic
│   └── language.py            # detection only; never translation at this layer
├── analysis/
│   ├── relevance.py           # 3-stage gate
│   ├── embeddings.py          # provider-agnostic; local default
│   ├── extraction.py          # structured insight extraction
│   ├── clustering.py          # HDBSCAN + centroid matching + stable IDs
│   ├── llm.py                 # provider client, retries, JSON repair, cost meter
│   └── prompts/               # versioned prompt files, one per agent
├── insights/
│   ├── models.py  merge.py  lifecycle.py  evidence.py
├── scoring/
│   ├── relevance.py  pain.py  frequency.py  trend.py  intent.py
│   ├── competition.py  opportunity.py  confidence.py
│   └── bands.py               # single source of truth for banding
├── competitors/
│   ├── coverage.py  gaps.py
├── reporting/
│   ├── radar.py  knowledge.py  review.py  metrics.py
│   └── templates/
├── integration/
│   └── content_engine.py      # opportunity.v1 export + outcome ingestion
├── storage/
│   ├── db.py  models.py  migrations/  repositories.py  retention.py
└── observability/
    ├── logging.py             # structured JSON logs
    └── cost.py                # token + spend ledger with hard cap
```

**Why a monolith:** the entire workload is a nightly batch over thousands of rows. Microservices would add deployment, network, and debugging cost while solving nothing. Module boundaries above are strict enough that any module could later become a service without redesign — which is the actual benefit people want from microservices.

**Why SQLite:** single writer, batch workload, embedded, zero ops, trivially backed up (copy the file), and `sqlite-vec` gives vector search in-process. Postgres + pgvector behind the same repository interface when Phase 5 needs concurrency.

---

## 3. Recommended stack

| Concern | Choice | Rationale |
|---|---|---|
| Language | Python 3.12 | Ecosystem for HTTP, embeddings, clustering, LLM SDKs |
| CLI | Typer | Argument parsing + help for free; the MVP interface |
| Config | YAML + Pydantic v2 | Human-editable, git-diffable, strictly validated |
| Storage | SQLite (WAL) + `sqlite-vec` | Embedded, sufficient to ~10M rows for this workload |
| ORM | SQLAlchemy 2.x (or SQLModel) | Migration path to Postgres unchanged |
| Migrations | Alembic | Schema will change; ad-hoc DDL will not survive |
| Scheduler | APScheduler (in-process) | No broker; cron as an alternative for `radar run` |
| HTTP | httpx + tenacity | Async-capable, retries with jitter |
| Embeddings | `bge-small-en-v1.5` local, provider-pluggable | Cost is the constraint; local is free and adequate for clustering |
| Clustering | HDBSCAN + cosine centroid matching | Handles unknown cluster counts and noise; noise points are a feature |
| LLM | Two tiers, provider-agnostic client | Cheap tier for classification/extraction, reasoning tier for adjudication/synthesis |
| Reports | Jinja2 → markdown | Git-friendly, diffable, portable, no UI needed |
| Tests | pytest + recorded HTTP fixtures | Adapter tests must not hit live APIs in CI |
| Logging | structlog → JSON | Every LLM call, cost, and decision logged |

### Model tiering policy

| Task | Tier | Why |
|---|---|---|
| Relevance grey zone (score 40–70) | cheap | Binary-ish decision, short input, high volume |
| Insight extraction (pains, questions, objections, phrases) | cheap | Structured extraction with a tight schema; volume dominates cost |
| Intent + category classification | cheap | Rubric-anchored, short |
| Cluster merge adjudication | reasoning | Judgement about sameness; errors corrupt trend history |
| Underlying-concern inference | reasoning | Highest hallucination risk in the system |
| Gap analysis | reasoning | Multi-document comparison |
| Opportunity synthesis | reasoning | Combines many inputs; output is user-facing |
| Weekly radar prose | reasoning | User-facing, and constrained to supplied numbers |

Target mix: ≥70% of calls on the cheap tier (`goals-and-success-metrics.md §3.5`).

---

## 4. Cost control architecture

Cost is a first-class design constraint, enforced at four points:

```text
1000 collected items
  → rule filters (free)            ~40% dropped: exclusions, too short, bot signatures, age
  → embedding similarity (~free)   ~35% dropped: below relevance floor
  → LLM adjudication (cheap)       only the 40–70 grey zone, batched 10/call  ≈ 6% of items
  → LLM extraction (cheap)         only items scoring ≥50                     ≈ 25% of items
  → reasoning tier                 only aggregates: merges, gaps, radar       ≈ 20–40 calls/week
```

Enforced mechanisms:
1. **Hard monthly cap** in `cost.py`. At 80% → warn in logs and radar; at 100% → LLM calls raise `BudgetExceeded`, collection continues, analysis marked `partial`.
2. **Per-run budget** so one runaway source can't consume the month.
3. **Cache by content hash + prompt version.** Re-analysis of unchanged content is free; a prompt version bump invalidates deliberately.
4. **Batching.** Relevance adjudication batches 10 items per call; extraction batches short items.
5. **Dedup before analysis, always.** The cheapest LLM call is the one not made.

---

## 5. Storage layout

```text
data/
  radar.db                  # SQLite: all structured data
  raw/                      # compressed raw payloads (gzip JSON), 180d retention
knowledge/                  # git-tracked markdown — the human-readable product
  index.md
  radar/2026-W34.md
  insights/pains/…  questions/…  objections/…  language/…  topics/…
  opportunities/…
  metrics/2026-08.md
config/
  audience.yaml  sources.yaml  competitors.yaml  business.yaml  taxonomy.yaml
  language_suppress.yaml
```

`knowledge/` being a git repo is deliberate: version history for free, diffs show how understanding changed week to week, and the user can edit files directly (edits are respected — the generator writes only into marked regions).

---

## 6. Reliability

| Failure | Handling |
|---|---|
| Source API down | Retry with exponential backoff + jitter (3 attempts); mark run failed; next scheduled run resumes from cursor |
| Rate limit | Token bucket pre-empts; on 429 honour `Retry-After`, requeue remainder |
| Quota exhausted (YouTube) | Stop that platform for the day, log, allocate tomorrow's quota by source priority |
| Auth failure | Immediate loud failure — surfaces in `radar doctor` and the radar footer |
| Malformed LLM JSON | Schema validate → one repair retry → quarantine item, never silent-drop |
| Partial run | Cursor advances only over confirmed-persisted items; re-runs are idempotent |
| Corrupt cluster state | Clustering is recomputable from embeddings; topic IDs restored via `supersedes` chain |
| Process crash mid-run | SQLite transactions per item batch; `CollectionJob` records the last good cursor |

**Idempotency** is guaranteed by `(source_id, platform_item_id)` uniqueness plus content hashing. Re-running any job is always safe — the property that makes an unattended nightly system tolerable to operate.

---

## 7. Extensibility

| Extension | Cost |
|---|---|
| New platform | One adapter implementing the interface + a config type. No changes elsewhere. |
| New insight type | Model + extraction prompt + scoring function + a radar section. |
| New scoring model | `scoring/` functions are pure; swap and re-run over stored data, no re-collection. |
| Multi-audience (Phase 5) | `audience_id` is already on every table; add a scoping filter and separate knowledge dirs. |
| Postgres | Repository interface unchanged; swap the engine URL and run migrations. |
| Web UI | Reporting layer already emits structured data; add a read-only server over the same repositories. |
| Real-time | Replace the scheduler trigger; layers below are unaware of cadence. |

---

## 8. Security & privacy posture

- Secrets from environment or keyring only; config files are validated to reject inline credentials.
- Author identifiers stored as `sha256(platform + author_id + install_salt)` in the insight layer; raw handles live only in the raw layer, which expires on the retention schedule.
- No cross-platform identity resolution, no follower graphs, no contact enrichment, no profiling of individuals.
- Only public, ToS-permitted, documented-API or published-feed access. `robots.txt` honoured for web sources. No auth bypass, no CAPTCHA solving, no paywall circumvention — enforced by config validation, not just policy.
- Retention: raw 180 days (configurable), derived insights indefinite, evidence URLs indefinite. `radar purge` supports deletion by source, author hash, or date range, with dependent insights quarantined for review.
- Collected data is never used to train or fine-tune models; LLM calls are stateless and carry only the item under analysis.
