# Source Adapters

Every platform is different. The adapter layer contains **all** platform-specific knowledge so that nothing above it needs to know whether data came from Reddit or an RSS feed.

**Rule: platform quirks stop at the adapter boundary.** If a platform detail leaks upward, the design is wrong.

---

## 1. Common interface

```python
class SourceAdapter(Protocol):
    platform: str
    supported_types: set[str]
    capabilities: Capabilities

    def discover(self, source: SourceConfig) -> DiscoveryResult:
        """Resolve config to concrete collectable targets.
        Subreddit → itself. Channel → recent video IDs. Keyword → a search plan.
        Validates existence/accessibility. Cheap. No content collection."""

    def collect(self, source: SourceConfig, cursor: Cursor | None,
                window: TimeWindow, limits: Limits) -> CollectionResult:
        """Fetch raw items. Returns raw payloads + a new cursor.
        MUST NOT parse into canonical models. MUST respect limits."""

    def normalize(self, raw: RawItem) -> NormalizedBundle:
        """Payload → Conversation/Comment/Author. Pure function, no I/O.
        Preserves the author's wording exactly."""

    def deduplicate(self, items: list[NormalizedBundle]) -> DedupResult:
        """Platform-specific dedup only (crossposts, quote-tweets, re-uploads).
        Generic hash/simhash/semantic dedup happens above."""

    def get_metadata(self, source: SourceConfig) -> SourceMetadata:
        """Subscriber counts, activity level, accessibility, last-post date.
        Used for health checks and the monthly source review."""

    def handle_rate_limit(self, response, state: RateLimitState) -> RateLimitAction:
        """Return wait | retry_after(seconds) | abort_source | abort_platform."""

    def handle_error(self, exc, context) -> ErrorAction:
        """Classify: retry | skip_item | fail_source | disable_source | unsupported."""
```

### Capabilities declaration

Every adapter declares what it can actually do. Higher layers branch on capabilities, never on platform names.

```python
@dataclass
class Capabilities:
    supports_search: bool
    supports_comments: bool
    supports_historical: bool
    max_historical_days: int | None
    provides_engagement: bool
    provides_author_id: bool
    provides_timestamps: bool
    supports_cursor_pagination: bool
    rate_limit_model: str          # "requests_per_minute" | "quota_units_per_day" | "unspecified"
    requires_auth: bool
    tos_permits_storage: bool
```

### Cursor contract

Cursors are opaque strings owned by the adapter, and must be **monotonic and resumable**. Two valid strategies:
- **Watermark:** highest `posted_at` seen (feeds, listings). Overlap slightly (10 minutes) to tolerate clock skew; dedup absorbs it.
- **Token:** platform pagination token (search APIs). Store alongside a watermark fallback, because tokens expire.

A cursor advances **only** after items are persisted, inside the same transaction.

---

## 2. Reddit adapter

**Access:** official API via a registered script app (OAuth2 client credentials). Descriptive User-Agent required.

| Capability | Value |
|---|---|
| search / comments / historical | ✅ / ✅ / partial (~1,000 items per listing) |
| engagement / author id / timestamps | ✅ (score, upvote ratio, comment count) / ✅ / ✅ |
| rate limit | ~100 requests/minute (OAuth), headers report remaining |

**Types:** `subreddit`, `keyword`, `user`.

**Collection**
- `subreddit`: `/r/{sub}/new` (default — deterministic and complete) with `before`/`after`; `hot`/`top` available but non-deterministic and only for discovery.
- Comments: `/comments/{id}` with `depth` and `limit`; expand `MoreComments` up to `max_comments_per_item`, breadth-first (top-level comments carry more signal than deep replies).
- `keyword`: `/search` with `restrict_sr` when `subreddits[]` is set. Reddit search is weak — treat it as recall, not precision, and let the relevance gate do the work.

**Limitations**
- ~1,000-item listing ceiling: deep backfill is impossible. Backfill beyond ~30 days is best-effort and must be reported as incomplete.
- Deleted/removed items appear as `[deleted]` → skip, and mark existing evidence `content_removed` (keep the URL).
- Some subreddits are private/quarantined → `unsupported`, never a workaround.
- Author `[deleted]` → null author; the item still counts for frequency but contributes no distinct author.

**Normalization:** post → `Conversation` (title + selftext); each comment → `Comment` with `depth`; crossposts detected via `crosspost_parent` → deduped at adapter level.

**Errors:** 401 → auth failure (loud). 403 → private/banned → `unsupported`. 429 → honour `x-ratelimit-reset`. 503 → retry ×3.

---

## 3. YouTube adapter

**Access:** Data API v3 with an API key (read-only public data).

| Capability | Value |
|---|---|
| search / comments / historical | ✅ / ✅ (public, non-disabled) / ✅ via `publishedAfter` |
| rate limit | **quota units/day** (default 10,000) — the binding constraint |

**Quota costs (the number that shapes the whole adapter):**
| Call | Units |
|---|---|
| `search.list` | **100** |
| `videos.list` | 1 |
| `commentThreads.list` | 1 |
| `channels.list` | 1 |
| `playlistItems.list` | 1 |

**Consequence:** one search costs as much as 100 comment fetches. Therefore: **never use `search.list` to enumerate a channel's uploads.** Use `channels.list` → `contentDetails.relatedPlaylists.uploads` → `playlistItems.list` (2 units instead of 100). This one decision is the difference between 8 channels/day and 100.

**Collection**
- `channel`: uploads playlist → videos → comment threads.
- `video`: direct comment threads.
- `keyword`: `search.list` (expensive) → `videos.list` for stats → comment threads. Budget explicitly; `max_items_per_run` defaults low (15).
- Comments: `commentThreads.list` with `order=relevance` (better signal) or `time` (complete); `maxResults=100`; replies fetched only for threads above an engagement floor.

**Limitations**
- Comments may be disabled → not an error; record `comments_unavailable`.
- `relevance` ordering is not stable across calls → cursor by watermark, not by page.
- Comment edit history unavailable; treat the latest text as canonical.
- View counts are cumulative, not windowed → engagement percentiles only within a competitor's own catalogue.
- No transcripts in MVP (separate quota/ToS considerations).

**Quota management:** daily ledger; allocate by source priority; hard-stop at 90% reserving 10% for manual runs; on `quotaExceeded`, stop the platform for the day and log — never retry into the wall.

---

## 4. X adapter

**Access:** official API only. Tier-dependent and historically unstable.

| Capability | Value |
|---|---|
| search | tier-dependent; frequently unavailable at low tiers |
| comments/replies | limited; conversation reconstruction is expensive |
| historical | 7 days on most tiers |

**Design stance:** implemented, **disabled by default**, and degrades cleanly. `discover()` probes access at startup; on failure the adapter returns `SourceUnsupported("no_search_access")`, the source is marked `unsupported`, and the radar notes the missing platform. **No part of the system's value depends on X.**

**Limitations:** short posts carry less pain language than Reddit/YouTube comments; retweets/quotes inflate volume (excluded by default); ToS restricts storage and redistribution — store minimal fields, respect deletion, never rehydrate deleted content.

**Prohibited:** scraping the web interface, unofficial endpoints, logged-out HTML parsing, third-party proxies. If the API is unavailable, the answer is "no X data", not a workaround.

---

## 5. RSS / Atom adapter

**Access:** published feeds. The most reliable, cheapest, most under-used source class.

| Capability | Value |
|---|---|
| search / comments | ❌ / ❌ (unless the feed *is* a comment feed) |
| historical | only what the feed contains (typically 10–50 items) |
| rate limit | none published — self-imposed 1 req/source/minute, ETag + `If-Modified-Since` |

**Collection:** fetch feed → parse entries → optional `full_text_fetch` when the feed is truncated **and** robots.txt allows **and** the domain is the feed's own.

**Limitations:** inconsistent date formats (normalize defensively, fall back to fetch time and flag it); no author IDs on many feeds (author hash falls back to a name hash, flagged `weak_author_identity`, and such items are excluded from distinct-author counts); feeds silently 404 or move (auto-disable at 3 failures).

**Why it matters:** many forums, blogs, and communities expose RSS. Before writing a scraper for anything, check for a feed — the answer is yes more often than people expect.

---

## 6. Generic website adapter

**Access:** sitemap-driven, robots-respecting, conservative.

**Hard rules (enforced, not advisory):**
1. `robots.txt` fetched and honoured, always. `robots_respect: false` is rejected by config validation.
2. `Crawl-delay` honoured; default 2s between requests to one host.
3. Descriptive User-Agent identifying the tool.
4. `max_pages_per_run` capped (default 25).
5. No login, no cookies-with-session, no CAPTCHA handling, no headless-browser evasion, no paywall circumvention.
6. If content requires JS rendering → `unsupported`. Not a challenge to solve.

**Collection:** sitemap → filter by `path_include`/`path_exclude` and `lastmod` → fetch → readability extraction → normalize as `Conversation` with `content_type: article`.

**Use case:** competitor content surfaces without feeds, and public review/documentation pages. Not a general scraping capability, and deliberately unpleasant to abuse.

---

## 7. Community adapter (Discourse-style)

**Access:** public JSON endpoints only (`/latest.json`, `/t/{id}.json`).

Rich structure when available: threads, replies, authors, timestamps, and useful engagement (likes, views). Rate-limit conservatively (1 req/2s). If any endpoint requires authentication, the source is `unsupported` — public means public.

---

## 8. Capability matrix

| | Reddit | YouTube | X | RSS | Website | Community |
|---|---|---|---|---|---|---|
| Search | ✅ | ✅ (100u) | tier | ❌ | ❌ | partial |
| Comments | ✅ | ✅ | limited | ❌ | ❌ | ✅ |
| Historical depth | ~1k items | ✅ | 7d | feed only | sitemap | ✅ |
| Engagement | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Stable author ID | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Auth required | ✅ | key | ✅ | ❌ | ❌ | ❌ |
| Rate model | req/min | quota/day | tier | self-imposed | self-imposed | self-imposed |
| MVP status | ✅ ship | ✅ ship | flagged off | ✅ ship | Phase 3 | Phase 2 |
| Signal density | **highest** | high (comments) | low | medium | low | high |

Signal density is the row that should drive effort. Reddit and YouTube comments are where people describe problems in their own words at length; that is why they ship first.

---

## 9. Adding a new adapter

1. Implement the interface in `collection/adapters/<platform>.py`.
2. Declare `Capabilities` honestly — over-claiming breaks higher layers silently.
3. Add config types + validation in `config/models.py`.
4. Record HTTP fixtures; write tests for: happy path, empty result, rate limit, auth failure, malformed payload, cursor resume, dedup.
5. Document limitations in this file. An adapter whose limitations are undocumented will produce silently wrong trend data.
6. Verify ToS permits programmatic read and storage of what you collect. If unclear, do not ship it.

**Test requirements per adapter:**
- Idempotency: run twice → zero new items on the second run.
- Cursor resume: kill mid-run → restart → no loss, no duplicates.
- Rate-limit handling: simulated 429 → correct backoff, no data loss.
- Normalization: fixture payload → expected canonical output, byte-for-byte on text fields.
- Unsupported path: inaccessible source → `SourceUnsupported` with a reason, never a crash and never a silent empty result.
