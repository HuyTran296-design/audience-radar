# Logical Data Model

Storage: SQLite (MVP) → Postgres (Phase 5). Types below are logical; SQLite equivalents in parentheses where they differ.

**Conventions**
- Primary keys: prefixed ULIDs, `TEXT` (`pain_01J8K2M4P7QRXV3B`). Sortable by creation time, no coordination needed.
- Timestamps: `TIMESTAMPTZ` (`TEXT` ISO-8601 UTC). Every table has `created_at`, `updated_at`.
- Every insight-layer table has `audience_id` (multi-audience readiness from day one).
- Enums stored as `TEXT` with a `CHECK` constraint — readable in raw SQL, which matters for debugging.
- Score fields: `INTEGER 0–100`. Confidence: `REAL 0.0–1.0`.
- JSON fields: `JSONB` (`TEXT` JSON) for genuinely variable structures only.
- Soft delete (`deleted_at`) on insight-layer tables; hard delete only via retention/purge.

**Layer discipline**: tables belong to exactly one layer and only lower layers may be read by higher ones.

```text
RAW           RawPayload
NORMALIZED    Source · CollectionJob · Conversation · Comment · Author · Content
ANALYSIS      ItemAnalysis · Embedding · Evidence
AGGREGATE     Topic · PainPoint · Question · Objection · AudiencePhrase · Trend
COMPETITIVE   Competitor · CompetitorContent · CompetitorCoverage · CompetitorGap
OUTPUT        Opportunity · Insight(view) · Report · ReviewAction
SYSTEM        CostLedger · QuotaLedger · AuditLog
```

---

## 1. Entity relationship overview

```text
Source ──< CollectionJob ──< RawPayload
   │                            │
   └──< Conversation ──< Comment │
           │      │              │
           │      └──> Author <──┘
           │
           ├──> ItemAnalysis ──> Embedding
           └──> Evidence >── PainPoint / Question / Objection / AudiencePhrase / Topic / CompetitorGap / Opportunity

Topic ──< Trend
Competitor ──< CompetitorContent ──> Topic
Competitor ──< CompetitorCoverage ──> Topic
CompetitorGap ──> Topic, Question, PainPoint
Opportunity ──> PainPoint, Question, Objection, CompetitorGap, AudiencePhrase
ReviewAction ──> (any insight, polymorphic)
```

---

## 2. Normalized layer

### 2.1 `Source`
Mirrors `sources.yaml`, plus runtime state. Config is authoritative; this table caches and tracks health.

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK | ✅ | From config (`reddit_mindfulness`) — not a ULID; stable and human-chosen |
| `audience_id` | TEXT FK | ✅ | |
| `platform` | TEXT enum | ✅ | reddit·youtube·x·rss·forum·website·community |
| `type` | TEXT enum | ✅ | subreddit·channel·keyword·video·account·feed·sitemap·user |
| `name` / `url` / `query` | TEXT | ✅/➖ | |
| `enabled` | BOOLEAN | ✅ | default true |
| `priority` | TEXT enum | ✅ | critical·high·medium·low |
| `collection_frequency` | TEXT enum | ✅ | |
| `config_json` | JSON | ✅ | Full validated source config snapshot |
| `config_hash` | TEXT | ✅ | Detects config drift between runs |
| `last_run_at` / `last_success_at` | TIMESTAMPTZ | ➖ | |
| `last_cursor` | TEXT | ➖ | Platform-specific pagination/watermark |
| `consecutive_failures` | INTEGER | ✅ | default 0; ≥3 → auto-disable |
| `health` | TEXT enum | ✅ | ok·degraded·stale·disabled_by_system·unsupported |
| `items_collected_total` | INTEGER | ✅ | |
| `relevant_rate_30d` | REAL | ➖ | |
| `trusted_insights_attributed` | INTEGER | ✅ | The monthly-review metric |

Indexes: `(audience_id, enabled, collection_frequency)`, `(health)`.

### 2.2 `CollectionJob`

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `source_id` | TEXT FK | ✅ | |
| `started_at` / `finished_at` | TIMESTAMPTZ | ✅/➖ | |
| `status` | TEXT enum | ✅ | running·success·partial·failed·skipped·rate_limited·unsupported |
| `trigger` | TEXT enum | ✅ | scheduled·manual·backfill·retry |
| `cursor_before` / `cursor_after` | TEXT | ➖ | |
| `items_fetched` / `items_new` / `items_duplicate` / `items_rejected` | INTEGER | ✅ | |
| `api_calls` / `quota_units_used` | INTEGER | ✅ | |
| `error_class` | TEXT enum | ➖ | rate_limited·auth·not_found·server·parse·timeout·unsupported |
| `error_detail` | TEXT | ➖ | Redacted of secrets |
| `window_start` / `window_end` | TIMESTAMPTZ | ➖ | Requested collection window |

Indexes: `(source_id, started_at DESC)`, `(status, started_at DESC)`.

### 2.3 `RawPayload` (raw layer, immutable)

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `collection_job_id` | TEXT FK | ✅ | |
| `platform_item_id` | TEXT | ✅ | Platform's native id |
| `payload_gz` | BLOB | ✅ | gzip JSON exactly as received |
| `payload_hash` | TEXT | ✅ | sha256 of canonical JSON |
| `fetched_at` | TIMESTAMPTZ | ✅ | |
| `expires_at` | TIMESTAMPTZ | ✅ | `fetched_at + retention_days` |

Unique: `(collection_job_id, platform_item_id)`. Index: `(expires_at)` for the retention sweep.
**No updates permitted.** Enforced by a trigger; the raw layer is the audit anchor for every downstream claim.

### 2.4 `Author`

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `platform` | TEXT enum | ✅ | |
| `author_hash` | TEXT | ✅ | `sha256(platform + platform_author_id + install_salt)` |
| `platform_author_id` | TEXT | ➖ | **Raw layer only**; nulled at retention expiry |
| `display_handle` | TEXT | ➖ | Same treatment as above |
| `first_seen_at` / `last_seen_at` | TIMESTAMPTZ | ✅ | |
| `item_count` | INTEGER | ✅ | For concentration metrics |
| `is_likely_bot` | BOOLEAN | ✅ | Heuristic: posting cadence, template similarity |
| `is_creator` | BOOLEAN | ✅ | Author is a tracked competitor/creator → excluded from audience frequency |

Unique: `(platform, author_hash)`. Index: `(author_hash)`.
**No profiling fields.** No follower counts, no bio storage, no cross-platform linkage, no contact data — a deliberate schema-level constraint, not a policy note.

### 2.5 `Conversation`
A top-level item: Reddit post, YouTube video, tweet, forum thread, RSS entry.

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `audience_id` / `source_id` | TEXT FK | ✅ | |
| `raw_payload_id` | TEXT FK | ✅ | Traceability anchor |
| `platform` / `platform_item_id` | TEXT | ✅ | |
| `url` | TEXT | ✅ | Canonical public URL |
| `title` | TEXT | ➖ | |
| `body` | TEXT | ➖ | Normalized text, **audience wording preserved** |
| `body_hash` / `simhash` | TEXT / INTEGER | ✅ | Dedup layers 1 and 2 |
| `author_id` | TEXT FK | ➖ | Null for anonymous/deleted |
| `posted_at` / `collected_at` | TIMESTAMPTZ | ✅ | |
| `language` / `detected_language` | TEXT | ➖ | ISO 639-1 |
| `engagement` | JSON | ➖ | `{score, upvotes, comments, views, likes}` — platform-dependent |
| `comment_count` | INTEGER | ✅ | |
| `is_duplicate_of` | TEXT FK | ➖ | Set by semantic dedup; row retained for auditability |
| `word_count` | INTEGER | ✅ | Cheap pre-filter |
| `content_type` | TEXT enum | ✅ | post·video·tweet·article·thread·review |

Unique: `(source_id, platform_item_id)`. Indexes: `(audience_id, posted_at DESC)`, `(body_hash)`, `(simhash)`, `(is_duplicate_of)`.

### 2.6 `Comment`
Same shape, plus threading. Comments are usually where pain language lives.

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `conversation_id` | TEXT FK | ✅ | |
| `parent_comment_id` | TEXT FK | ➖ | |
| `depth` | INTEGER | ✅ | 0 = top-level |
| `body` / `body_hash` / `simhash` | | ✅ | |
| `author_id` | TEXT FK | ➖ | |
| `posted_at` / `collected_at` | TIMESTAMPTZ | ✅ | |
| `engagement` | JSON | ➖ | |
| `is_author_reply` | BOOLEAN | ✅ | Comment by the conversation's author |

Unique: `(conversation_id, platform_item_id)`. Index: `(conversation_id, posted_at)`.

### 2.7 `Content`
Generic normalized text unit — the analysis layer's uniform input, so extraction doesn't branch on conversation-vs-comment.

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `origin_type` | TEXT enum | ✅ | conversation·comment·competitor_content |
| `origin_id` | TEXT | ✅ | Polymorphic FK |
| `audience_id` | TEXT FK | ✅ | |
| `text` | TEXT | ✅ | Analysis-ready text |
| `text_hash` | TEXT | ✅ | Analysis cache key (with `prompt_version`) |
| `posted_at` | TIMESTAMPTZ | ✅ | |
| `platform` / `source_id` | TEXT | ✅ | Denormalized for query speed |
| `author_hash` | TEXT | ➖ | Denormalized for distinct-author counts |

Unique: `(origin_type, origin_id)`. Indexes: `(audience_id, posted_at)`, `(text_hash)`, `(author_hash)`.

---

## 3. Analysis layer

### 3.1 `ItemAnalysis`
One row per `Content` per `prompt_version`. Append-only; re-analysis creates a new row.

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `content_id` | TEXT FK | ✅ | |
| `prompt_version` / `model` / `model_tier` | TEXT | ✅ | Reproducibility |
| `relevance_score` | INTEGER | ✅ | 0–100 |
| `relevance_stage` | TEXT enum | ✅ | rules·embedding·llm — which stage decided |
| `relevance_reason` | TEXT | ➖ | Short, human-readable |
| `is_relevant` | BOOLEAN | ✅ | |
| `intent` / `intent_confidence` | TEXT / REAL | ➖ | |
| `segments` | JSON | ➖ | `[{segment, confidence}]` |
| `extracted` | JSON | ➖ | Raw structured extraction output |
| `is_rhetorical` / `is_creator_content` / `is_spam` | BOOLEAN | ✅ | |
| `tokens_in` / `tokens_out` / `cost_usd` | INTEGER/REAL | ✅ | Cost attribution |
| `analyzed_at` | TIMESTAMPTZ | ✅ | |
| `error` | TEXT | ➖ | Set for quarantined items |

Unique: `(content_id, prompt_version)`. Indexes: `(is_relevant, analyzed_at)`, `(relevance_score)`.

### 3.2 `Embedding`

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `content_id` | TEXT FK | ➖ | Null for insight/topic centroid embeddings |
| `owner_type` / `owner_id` | TEXT | ✅ | content·pain·question·topic·phrase·competitor_content |
| `vector` | BLOB (`sqlite-vec`) | ✅ | |
| `model` / `dimensions` | TEXT / INTEGER | ✅ | |
| `created_at` | TIMESTAMPTZ | ✅ | |

Unique: `(owner_type, owner_id, model)`. Vector index via `sqlite-vec` / `pgvector`.

### 3.3 `Evidence`
The join table that makes the evidence-first architecture real. **Every insight-layer claim must have ≥1 row here.**

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | TEXT PK ULID | ✅ | |
| `insight_type` / `insight_id` | TEXT | ✅ | Polymorphic |
| `content_id` | TEXT FK | ✅ | |
| `conversation_id` | TEXT FK | ➖ | Denormalized for URL access |
| `url` | TEXT | ✅ | Snapshotted at creation — survives content deletion |
| `platform` / `source_id` | TEXT | ✅ | |
| `author_hash` | TEXT | ➖ | Distinct-author counting |
| `collected_at` / `posted_at` | TIMESTAMPTZ | ✅ | |
| `exact_phrasing` | TEXT | ➖ | **≤15 words**, verbatim, redacted of PII |
| `contribution` | TEXT enum | ✅ | primary·supporting·contradicting |
| `relevance_score` | INTEGER | ✅ | |
| `evidence_expired` | BOOLEAN | ✅ | Raw expired; URL retained |

Unique: `(insight_type, insight_id, content_id)`. Indexes: `(insight_type, insight_id)`, `(content_id)`, `(author_hash)`.
Constraint: `LENGTH(exact_phrasing) ≤ 120` characters, enforced at write.

---

## 4. Aggregate insight layer

All insight tables share this common block:

```text
id · audience_id · slug · status · confidence · version · supersedes ·
created_at · updated_at · reviewed_at · reviewed_by · review_notes ·
observed_fact · ai_interpretation · hypothesis · recommended_action ·
first_detected · last_detected · deleted_at
```

`status ∈ {detected, analyzed, candidate, reviewed, trusted, archived, rejected}` with `CHECK`.

### 4.1 `Topic`

| Field | Type | Notes |
|---|---|---|
| `label` / `description` | TEXT | LLM-generated, human-editable |
| `cluster_id` | TEXT | Stable across re-clustering runs |
| `centroid_embedding_id` | TEXT FK | |
| `cohesion` | REAL | Mean intra-cluster similarity; <0.6 → propose split |
| `item_count` / `distinct_authors` | INTEGER | |
| `platforms` | JSON | `{reddit: 22, youtube: 11}` |
| `share_of_voice` | REAL | |
| `superseded_by` | TEXT FK | Preserves trend continuity across merges |

Indexes: `(audience_id, status)`, `(cluster_id)`.

### 4.2 `PainPoint`
Fields per `02-insights/audience-pains.md`. Key columns: `title`, `category` (JSON array), `severity` enum, `severity_score`, `frequency`, `frequency_distinct_authors`, `frequency_change`, `trend`, `platform_spread`, `topic_id` FK, `cluster_id`, `affected_segments` JSON, `representative_quotes` JSON (max 3, each ≤15 words), `paraphrased_examples` JSON, `related_*` JSON arrays, `single_thread` BOOLEAN.

Unique: `(audience_id, slug)`. Indexes: `(audience_id, status, severity_score DESC)`, `(topic_id)`, `(last_detected DESC)`.
Constraints: `status != 'candidate'` unless `frequency_distinct_authors >= 3`; `json_array_length(representative_quotes) <= 3`.

### 4.3 `Question`
Per `02-insights/hot-questions.md`: `question`, `normalized_question`, `question_variants` JSON, `intent` enum, `intent_confidence`, `secondary_intent`, `urgency_score`, `answered_in_thread_rate`, `content_potential`, `business_potential`, `platform_distribution` JSON, `competitor_coverage` JSON, `suggested_formats`/`hooks` JSON, `asked_by` enum (audience·creator), `is_rhetorical`.

Unique: `(audience_id, slug)`. Indexes: `(audience_id, status, urgency_score DESC)`, `(intent)`.

### 4.4 `Objection`
Per `02-insights/objections.md`: `objection`, `normalized_objection`, `objection_type` enum, `secondary_type`, `raised_at_stage` enum, `directed_at` enum, `stated_concern`, `likely_underlying_concern`, `underlying_confidence`, `evidence_for_underlying` JSON, `severity_to_conversion` enum, `possible_responses` JSON, `responses_to_avoid` JSON, `addressability` INTEGER, `objection_priority` INTEGER.

Constraint: `underlying_confidence <= MIN(0.8, confidence)`.

### 4.5 `AudiencePhrase`

| Field | Type | Notes |
|---|---|---|
| `exact_text` | TEXT | **IMMUTABLE** — enforced by trigger |
| `exact_context` | TEXT | ≤15 words verbatim |
| `category` | TEXT enum | 11 categories from `audience-language.md` |
| `normalized_concept` / `normalized_label` | TEXT | Layer 2 |
| `marketing_interpretation` | JSON | Layer 3, `authored_by: system` |
| `occurrences` / `distinct_authors` | INTEGER | |
| `variants` | JSON | Each verbatim |
| `distinctiveness` / `resonance_signal` | REAL | 0–1 |
| `language` / `detected_language` | TEXT | |
| `translated_interpretation` | JSON | Phase 5; never replaces `exact_text` |
| `suppressed` | BOOLEAN | From `language_suppress.yaml` |

Unique: `(audience_id, exact_text, category)`. Indexes: `(audience_id, distinctiveness DESC)`, `(normalized_concept)`.

### 4.6 `Trend`
One row per `(topic_id, window_end)` — an immutable time series, not a mutable current-state row. This is what makes historical trend claims reproducible.

| Field | Type | Notes |
|---|---|---|
| `topic_id` | TEXT FK | |
| `window_start` / `window_end` | TIMESTAMPTZ | Aligned ISO weeks |
| `window_completeness` | REAL | <0.8 → excluded from claims |
| `current_frequency` / `previous_frequency` | INTEGER | |
| `baseline_mean` / `baseline_stdev` | REAL | 90-day |
| `growth_rate` / `velocity` / `acceleration` / `z_score` | REAL | |
| `classification` | TEXT enum | emerging·rising·stable·declining·saturated·insufficient_baseline·data_incomplete |
| `trend_score` / `significance_score` | INTEGER | |
| `guards_fired` | JSON | `[small_n, concentration, single_thread, spike]` |
| `author_concentration` | REAL | |
| `external_trigger` | JSON | |

Unique: `(topic_id, window_end)`. Index: `(window_end DESC, significance_score DESC)`.

---

## 5. Competitive layer

### 5.1 `Competitor`
Mirrors `competitors.yaml` + state: `id`, `name`, `category` enum, `priority`, `website`, `blog_feed`, `sitemap`, `youtube_channel`, `social_accounts` JSON, `brand_terms` JSON, `product` JSON, `pricing` JSON, `pricing_last_verified` DATE, `monitor` JSON, `data_quality` enum, `content_items_total`, `last_run_at`, `health`.

Constraint: if `pricing` present, `pricing_last_verified` required; >90 days → `pricing_stale` computed flag.

### 5.2 `CompetitorContent`

| Field | Type | Notes |
|---|---|---|
| `competitor_id` | TEXT FK | |
| `url` / `title` | TEXT | |
| `format` | TEXT enum | article·video·short·podcast·landing_page·changelog·social_post |
| `published_at` / `collected_at` | TIMESTAMPTZ | |
| `summary` | TEXT | **System-written.** No extended verbatim storage |
| `word_count` / `duration_seconds` | INTEGER | Depth signals |
| `engagement` / `engagement_percentile` | JSON / INTEGER | Percentile within this competitor's catalogue only |
| `topic_id` | TEXT FK | Same topic space as audience data — the mechanism that makes gaps computable |
| `topic_confidence` | REAL | |
| `is_primary_topic` | BOOLEAN | Directness component |
| `promoted_offers` | JSON | |
| `data_quality` | TEXT enum | |

Unique: `(competitor_id, url)`. Indexes: `(competitor_id, published_at DESC)`, `(topic_id)`.

### 5.3 `CompetitorCoverage`
Computed per `(competitor_id, topic_id, computed_at)`: `coverage_score`, `volume_component`, `depth_component`, `recency_component`, `directness_component`, `items_on_topic`, `last_seen`, `performance_index`, `low_sample` BOOLEAN, `data_quality`.

### 5.4 `CompetitorGap`
Per `02-insights/competitor-gaps.md`: `gap_type` enum, `topic_id`, `demand_score`, `market_coverage`, `coverage_by_competitor` JSON, `competitors_checked`/`competitors_uncheckable` JSON, `items_examined`, `examination_window_start/end`, `unanswered_questions` JSON, `opportunity_score`, `score_components` JSON, `confidence_caps_applied` JSON, `claims_requiring_verification` JSON, `addressed_by`.

Constraint: `opportunity_score` may only be `>= 60` when `items_examined >= 50`.

---

## 6. Output layer

### 6.1 `Opportunity`
Per `03-opportunities/*`: `opportunity_class` enum (content·feature·product·service·offer), `title`, `slug`, `core_idea`, `audience_segments` JSON, `problem_ref`, `audience_language` JSON, `scores` JSON, `opportunity_score`, `score_band`, `recommended_platform`/`format` JSON, `angle`, `hook_ideas` JSON, `structure_suggestion` JSON, `cta_idea`, `do_not_say` JSON, `claims_requiring_verification` JSON, `blocked` BOOLEAN, `decision` enum, `decision_reason`, `outcome` JSON, `exported_at`, `export_schema_version`, `thresholds_met` JSON, `gate_status` enum.

Indexes: `(audience_id, status, opportunity_score DESC)`, `(week)`, `(decision)`.
Constraint: `exported_at` may only be set when `status = 'trusted'` AND `blocked = false`.

### 6.2 `Insight` (view, not a table)
A `UNION ALL` view over the insight tables exposing the common block plus `insight_type`. Powers the review queue, the knowledge index, and evidence-integrity checks without an inheritance hierarchy.

### 6.3 `ReviewAction` (append-only audit)

| Field | Type | Notes |
|---|---|---|
| `insight_type` / `insight_id` | TEXT | |
| `action` | TEXT enum | promote·reject·edit·merge·split·defer·reopen |
| `from_status` / `to_status` | TEXT | |
| `reason_code` | TEXT enum | Per insight-type taxonomies |
| `notes` | TEXT | |
| `field_changes` | JSON | Before/after for edits |
| `actor` | TEXT | human·system |
| `created_at` | TIMESTAMPTZ | |

Index: `(insight_type, insight_id, created_at DESC)`, `(action, created_at DESC)`.
**Never updated or deleted** — this is the training signal for the Phase-2 quality loop and the audit trail for every promotion.

### 6.4 `Report`
`report_type` (weekly_radar·monthly·metrics), `period_start`/`period_end`, `file_path`, `word_count`, `insight_refs` JSON, `validation_status` enum, `caveats` JSON, `generated_at`.

---

## 7. System layer

**`CostLedger`** — `occurred_at`, `agent`, `model`, `model_tier`, `tokens_in`, `tokens_out`, `cost_usd`, `content_id`, `cache_hit` BOOLEAN, `job_id`. Indexes `(occurred_at)`, `(agent)`. Monthly aggregate drives the hard cap.

**`QuotaLedger`** — `platform`, `date`, `units_used`, `units_limit`, `requests`. Unique `(platform, date)`. Drives YouTube quota allocation by source priority.

**`AuditLog`** — `event_type`, `entity_type`, `entity_id`, `detail` JSON, `created_at`. Records config changes, auto-disables, purges, cap breaches, quarantines.

---

## 8. Key constraints (correctness invariants)

1. Every insight in `candidate`+ has ≥1 `Evidence` row. *(CI test, and a nightly integrity job.)*
2. Every `Evidence.url` is non-null and was captured at creation time.
3. `PainPoint.status != 'candidate'` unless `frequency_distinct_authors >= 3`.
4. `Opportunity.exported_at` non-null ⟹ `status = 'trusted' AND blocked = false`.
5. `AudiencePhrase.exact_text` is immutable (trigger-enforced).
6. `RawPayload` rows are never updated (trigger-enforced).
7. `Trend` rows are immutable once written; corrections create a new row.
8. Insight `confidence <= 1.0` and `>= 0.0`; `Objection.underlying_confidence <= confidence`.
9. Deleting a `Source` never cascades to insights; dependent insights are quarantined for review.
10. Every table with `audience_id` is filtered by it in every query (repository-enforced, tested).

## 9. Retention & deletion

| Data | Default retention | On expiry |
|---|---|---|
| `RawPayload.payload_gz` | 180 days | Deleted; hash + fetch metadata retained |
| `Author.platform_author_id`, `display_handle` | 180 days | Nulled; `author_hash` retained |
| `Conversation.body` / `Comment.body` | 180 days | Truncated to first 200 chars + hash |
| `Evidence.exact_phrasing` | Follows raw | `evidence_expired = true`, confidence −0.1 |
| `Evidence.url` | Indefinite | Retained for verification |
| Insights, topics, trends, opportunities | Indefinite | — |
| `CostLedger`, `AuditLog` | 24 months | Aggregated then deleted |

`radar purge --author <hash>` / `--source <id>` / `--before <date>` performs hard deletion and quarantines dependent insights, which then require re-review because they have lost evidence.
