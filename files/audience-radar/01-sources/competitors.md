# Competitor Configuration & Intelligence

File: `config/competitors.yaml`. Same loading and validation discipline as `sources.yaml`.

**The point of this file is not to track what competitors publish.** Publication tracking is a commodity and it teaches imitation. The point is to build a *coverage map* that can be diffed against audience demand, so the system can say: *this is what your market is asking for, and here is who is — and is not — answering it.*

---

## 1. What a competitor record is for

Each competitor contributes to four derived artifacts:

| Artifact | Question answered | Consumed by |
|---|---|---|
| **Coverage map** | Which audience topics do they cover, how deeply, how recently? | `competitor-gaps.md` |
| **Performance signal** | Which of their topics resonate (where measurable)? | opportunity scoring (modifier only) |
| **Answered-question matrix** | Which audience questions do they answer, and how well? | gap detection, content angles |
| **Positioning profile** | What language, promises, and offers do they lead with? | `audience-language.md` (competitor-descriptor layer), objection handling |

---

## 2. Schema

```yaml
version: 1

defaults:
  enabled: true
  monitoring_frequency: weekly
  max_items_per_run: 50
  max_age_days: 90
  collect_engagement: true
  collect_comments: true          # competitor audiences are OUR audience too
  comment_collection_purpose: audience_signal

competitors:
  - id: comp_example_calm
    name: "Example Calm App"
    enabled: true
    category: direct                 # direct | adjacent | substitute | aspirational | content_only
    monitoring_frequency: weekly
    priority: high

    # --- identity & surfaces ---
    website: "https://www.example-calm.com"
    blog_feed: "https://www.example-calm.com/blog/rss.xml"
    sitemap: "https://www.example-calm.com/sitemap.xml"
    changelog_url: "https://www.example-calm.com/whats-new"
    social_accounts:
      x: "@example_calm"
      instagram: "example_calm"        # metadata only; no compliant collection path at MVP
      linkedin: "company/example-calm"
    youtube_channel: "https://www.youtube.com/@example-calm"
    reddit_presence:
      official_subreddit: null
      mentioned_in: [Mindfulness, productivity, iosapps]
      brand_terms: ["example calm", "examplecalm", "example calm app"]
    app_listings:
      ios: "https://apps.apple.com/app/id000000000"
      android: null

    # --- product & commercial context (manually maintained) ---
    product:
      description: "Guided meditation library with courses and sleep content."
      key_features: [guided library, sleep stories, courses, streaks]
      differentiators: [large content library, celebrity narrators]
      known_weaknesses: [session length, content overwhelm, price]
      platforms: [ios, android, web]
    pricing:
      model: subscription
      tiers:
        - name: free
          price: 0
        - name: premium_annual
          price: 69.99
          currency: USD
          period: year
      last_verified: 2026-08-01        # REQUIRED; stale pricing is a reporting error
      source_url: "https://www.example-calm.com/pricing"
    target_audience: "General wellness consumers, 25–55, sleep and stress focus."
    positioning_claim: "Your daily dose of calm."

    # --- monitoring behaviour ---
    monitor:
      content: true                    # blog / YouTube / public posts
      engagement: true                 # views, comment counts where public
      comments: true                   # audience questions under their content
      pricing_changes: true            # from changelog/pricing page snapshots
      app_updates: true                # release notes where public
      brand_mentions: true             # via existing audience sources, not new scraping
    exclusion_keywords: [careers, press release, investor]
    notes: "Fictional example. Largest library in category — the anti-library positioning targets their overwhelm weakness."
```

### 2.1 Field reference

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `^comp_[a-z0-9_]+$` | ✅ | Stable join key. |
| `name` | string | ✅ | Display name. |
| `category` | enum | ✅ | `direct` (same job, same audience) · `adjacent` (same audience, different job) · `substitute` (different tool, same outcome — a phone alarm, a paper journal) · `aspirational` (bigger, sets category expectations) · `content_only` (a creator/publisher who owns the topic space but sells nothing competing) |
| `priority` | enum | ➖ | `high`/`medium`/`low` — quota allocation. |
| `monitoring_frequency` | enum | ➖ | `daily` · `weekly` · `biweekly` · `monthly`. Weekly is right for almost everyone. |
| `website` / `blog_feed` / `sitemap` | URL | ➖ | Collection prefers `blog_feed` → `sitemap` → nothing. **Never HTML-crawl around a missing feed.** |
| `youtube_channel` | URL | ➖ | Uploads + comments via Data API. |
| `social_accounts` | map | ➖ | Recorded even when uncollectable; the record documents *why* coverage data is incomplete. |
| `reddit_presence.brand_terms` | string[] | ➖ | Used to detect mentions inside already-collected audience data — no new collection. |
| `app_listings` | map | ➖ | Phase 5 review mining. |
| `product.known_weaknesses` | string[] | ➖ | Human hypothesis input. Flagged `hypothesis`, never reported as fact. |
| `pricing.last_verified` | date | ✅ if `pricing` present | Pricing older than 90 days is reported as `stale` and excluded from claims. |
| `monitor.*` | bool | ➖ | Per-signal switches. |
| `comment_collection_purpose` | enum | ➖ | `audience_signal` (default) — makes explicit that competitor comment sections are collected as *audience* sources, and those items flow into normal insight extraction. |

### 2.2 System-managed fields

`last_run_at` · `content_items_total` · `topics_covered` · `coverage_last_updated` · `avg_engagement_by_format` · `data_quality` (`good` · `partial` · `unavailable`) · `health`

---

## 3. What is collected

| Signal | Source | Reliability | Use |
|---|---|---|---|
| Content items (title, published date, URL, summary, format) | RSS / sitemap / YouTube API | high | Coverage map |
| Topic assignment | embeddings → **the same clusters as audience data** | medium-high | Gap diff |
| Depth of treatment | word count / video duration / structure signals | medium | Coverage depth score |
| Recency | published date | high | Staleness detection |
| Public engagement (views, comments, likes) | YouTube API; public counters only | low-medium | Performance modifier only |
| Audience questions under their content | comments | high | Hot questions + unanswered detection |
| Promoted products/offers | CTA and link extraction from collected content | medium | Offer landscape |
| Pricing | pricing page snapshot / manual `pricing` block | medium | Objection context, positioning |
| Positioning language | headings, taglines, repeated phrasing | medium | Competitor-descriptor language layer |

**Never collected:** anything behind login or paywall, ad-library data requiring circumvention, private communities, employee personal accounts, customer lists, or scraped emails.

**When a surface is uncollectable**, the competitor's `data_quality` drops to `partial`/`unavailable`, and every gap derived from them carries a reduced confidence and a visible caveat. Missing data must degrade confidence, never be silently treated as "no coverage" — that is the single most dangerous failure mode of this file, because *absence of observed coverage is not evidence of absent coverage*.

---

## 4. The eight required competitor questions

The spec for this system says competitor monitoring must answer eight questions. Each maps to a concrete computation:

| # | Question | How it is computed | Output field |
|---|---|---|---|
| 1 | What do they talk about? | Topic distribution of their content over 90 days, weighted by recency | `coverage_map[topic] = {items, share, last_seen}` |
| 2 | What performs well? | Engagement percentile within their own catalogue (never cross-competitor) | `performance_index[topic]` 0–100, with `data_quality` |
| 3 | What products do they promote? | CTA/link extraction + `product` config | `promoted_offers[]` |
| 4 | What do audiences respond to? | Comment volume + question density under their items | `audience_response[topic]` |
| 5 | What questions do they answer? | Match audience `Question` clusters against their content; require topical *and* intent match | `answered_questions[]` with `answer_quality` (`direct` · `partial` · `tangential`) |
| 6 | What questions remain unanswered? | Audience questions with `frequency ≥ threshold` and no `direct`/`partial` match across **all** competitors | `unanswered_questions[]` → primary gap input |
| 7 | What topics are gaining audience interest? | Audience-side trend (from `emerging-topics.md`) intersected with competitor coverage recency | `demand_rising_coverage_flat[]` |
| 8 | Where are they weak or silent? | `silent`: demand high, coverage 0. `weak`: coverage exists but shallow, stale, or poorly received | `weakness_map[topic] = {type, evidence}` |

Definitions used above:
- **shallow** — depth score in the bottom tercile of that competitor's catalogue for that format.
- **stale** — no content on the topic in ≥180 days while demand is `rising`/`emerging`.
- **poorly received** — engagement percentile <25 within their own catalogue, with `data_quality: good` only.

---

## 5. Coverage scoring (input to gap detection)

For each `(competitor, topic)`:

```text
coverage_score (0–100) =
    0.35 × volume_component      # items on topic, log-scaled: 100 × min(1, ln(1+n)/ln(1+8))
  + 0.25 × depth_component       # mean depth percentile within competitor's catalogue
  + 0.25 × recency_component     # 100 if ≤30d, 70 ≤90d, 40 ≤180d, 10 ≤365d, 0 older
  + 0.15 × directness_component  # share of items where the topic is primary, not incidental
```

Then per topic across competitors:

```text
market_coverage = weighted_max(coverage_score by competitor)
  weights: direct 1.0 · adjacent 0.7 · substitute 0.5 · aspirational 0.8 · content_only 0.9
```

`market_coverage` feeds the Competition Score in `04-system/scoring-system.md §7`. Using a weighted max (not a mean) is deliberate: if one strong competitor covers a topic exhaustively, the space is taken regardless of how many others ignore it.

**Small-N guard:** if a competitor has <10 collected items in the window, `coverage_score` is computed but marked `low_sample`, and any gap derived from it is capped at `confidence 0.55`.

---

## 6. Example: three competitors (illustrative)

```yaml
competitors:
  - id: comp_example_calm
    name: "Example Calm App"
    category: direct
    priority: high
    website: "https://www.example-calm.com"
    blog_feed: "https://www.example-calm.com/blog/rss.xml"
    youtube_channel: "https://www.youtube.com/@example-calm"
    reddit_presence:
      brand_terms: ["example calm"]
    product:
      description: "Large guided-meditation library."
      known_weaknesses: [content overwhelm, session length, price]
    pricing:
      model: subscription
      tiers: [{name: premium_annual, price: 69.99, currency: USD, period: year}]
      last_verified: 2026-08-01
    monitor: {content: true, engagement: true, comments: true, pricing_changes: true}

  - id: comp_example_timer
    name: "Example Interval Timer"
    category: substitute
    priority: medium
    website: "https://www.example-timer.io"
    sitemap: "https://www.example-timer.io/sitemap.xml"
    product:
      description: "Generic interval timer used as a makeshift mindfulness reminder."
      known_weaknesses: [no journaling, harsh sounds, no context]
    monitor: {content: true, engagement: false, comments: false}
    notes: "Substitute, not competitor. Their user complaints are the richest demand signal we have."

  - id: comp_example_creator
    name: "Example Focus Creator"
    category: content_only
    priority: medium
    youtube_channel: "https://www.youtube.com/@example-focus-creator"
    monitor: {content: true, engagement: true, comments: true}
    notes: "Owns the topic space without a competing product. Their comment sections are pure audience-question mining."
```

---

## 7. Reporting rules

1. Every competitor claim in a radar carries `data_quality` and `last_verified`. Pricing older than 90 days is reported as *"pricing as of <date>, unverified since"*, never as current.
2. Comparative claims ("they don't cover X") are always phrased as observations about *collected* data: *"no coverage of X found in 92 items collected since 2026-05-20"* — a scoped, checkable statement.
3. `known_weaknesses` from config is `hypothesis` in the four-way label scheme, never `observed_fact`.
4. Competitor content is never reproduced. Store title, URL, date, structural metadata, and a system-written summary; do not store or output extended verbatim text. If a phrase is quoted for positioning analysis it is ≤15 words, attributed, and limited to one per competitor item.
5. No competitor comparison is exported to the Content Engine without `data_quality: good` on both the demand and the coverage side.
