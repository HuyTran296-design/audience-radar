# Source Configuration

Canonical format for everything Audience Radar listens to. One file, git-tracked, human-editable: `config/sources.yaml`.

Design rules:
- **Config is data, not code.** Adding a source never requires a code change.
- **Validation is strict and loud.** Unknown fields fail the load with a line number; they are never ignored.
- **Every source declares its own relevance context.** A subreddit about ADHD and a subreddit about SaaS pricing need different keywords, and global keywords produce global noise.
- **Defaults are inherited** from `defaults:` and overridden per source. Inheritance is one level deep — no nesting games.

---

## 1. File structure

```yaml
version: 1

audience:
  id: calm_productivity
  name: "Busy knowledge workers seeking calmer routines"
  description: >
    28–45, desk/WFH professionals, often lapsed meditation-app users. Notification-tolerant.
    Value privacy and minimalism. Overlap with ADHD-adjacent routine seekers. English-first, global.
  goals:
    - "build a sustainable daily routine without another complicated system"
    - "reduce screen-driven stress during the workday"
    - "keep focus during long desk sessions"
  not_our_audience:
    - "clinical mental-health treatment seekers"
    - "hardcore biohacking / supplement stacks"
    - "enterprise wellness procurement"
  segments:                       # user-defined; NOT hard-coded in the system
    - beginner
    - routine_rebuilder
    - adhd_adjacent
    - founder
  languages: [en]
  primary_countries: [US, GB, CA, AU]

defaults:
  enabled: true
  priority: medium
  collection_frequency: daily
  max_age_days: 30
  min_relevance_score: 50
  collect_comments: true
  max_items_per_run: 100
  max_comments_per_item: 50
  language: en
  segments: []

sources:
  - id: reddit_mindfulness
    platform: reddit
    type: subreddit
    ...
```

---

## 2. Field reference

### 2.1 Identity & routing

| Field | Type | Req | Description |
|---|---|---|---|
| `id` | string, `^[a-z0-9_]{3,48}$` | ✅ | Stable unique key. **Never reuse or rename** — it's the join key for all historical data and evidence. |
| `platform` | enum | ✅ | `reddit` · `youtube` · `x` · `rss` · `forum` · `website` · `community` |
| `type` | enum (platform-scoped) | ✅ | See §3. e.g. `subreddit`, `channel`, `keyword`, `feed` |
| `name` | string | ✅ | Human label used in reports. |
| `url` | URL | ✅* | Canonical public URL. Required except for pure keyword/search sources, where `query` replaces it. |
| `query` | string | ⛔/✅ | Required for `type: keyword` / `search`. Platform search syntax allowed. |
| `handle` | string | ➖ | Platform handle when the URL isn't the natural key (X accounts, YouTube `@handle`). |
| `notes` | string | ➖ | Why this source is here. Free text; shown in the monthly source review. |

### 2.2 Control

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | `false` = skip entirely, keep history. |
| `priority` | enum | `medium` | `critical` · `high` · `medium` · `low`. Drives quota allocation, collection order, and a small relevance prior (see `scoring-system.md §2`). |
| `collection_frequency` | enum | `daily` | `hourly` · `every_6h` · `daily` · `every_2d` · `weekly` · `manual`. Hourly is reserved for `critical` sources; the validator rejects `hourly` on `low`. |
| `max_items_per_run` | int | `100` | Cap per collection run (cost control). |
| `max_comments_per_item` | int | `50` | Comment fan-out cap. Set `0` with `collect_comments: false`. |
| `collect_comments` | bool | `true` | Comments are usually where the pain language lives; disable only for quota reasons. |
| `max_age_days` | int | `30` | Ignore items older than this at collection time. Backfill overrides via `--since`. |
| `backfill_days` | int | `30` | One-time cold-start depth (platform permitting). |

### 2.3 Relevance context

| Field | Type | Default | Description |
|---|---|---|---|
| `target_topics` | string[] | `[]` | Topic anchors for this source. Used as embedding anchors, not literal matches. |
| `relevance_keywords` | string[] | `[]` | Positive lexical signals. Substring, case-insensitive, word-boundary aware. |
| `relevance_phrases` | string[] | `[]` | Multi-word positives, weighted higher than single keywords. |
| `exclusion_keywords` | string[] | `[]` | Hard negatives → immediate reject before any embedding/LLM cost. |
| `exclusion_patterns` | regex[] | `[]` | For structural noise (`^\[?giveaway`, `promo code`, mod-bot signatures). |
| `audience_description` | string | inherits | Source-specific audience note when it differs from the global audience. |
| `min_relevance_score` | int 0–100 | `50` | Gate for this source. Raise for noisy generalist sources, lower for tightly niche ones. |
| `segments` | string[] | `[]` | Segment prior — items from this source lean toward these segments (a prior, not a label). |
| `language` | ISO 639-1 | `en` | Expected language; mismatch lowers relevance and sets `language_mismatch`. |
| `country` | ISO 3166-1 α2[] | inherits | Expected audience geography (weak signal; rarely reliable per-item). |

### 2.4 Access & platform specifics

| Field | Type | Description |
|---|---|---|
| `auth_profile` | string | Named credential set from `config/credentials.yaml` / env (never inline secrets). |
| `platform_options` | map | Adapter-specific. Validated per adapter; unknown keys fail. See §3. |
| `rate_limit_class` | enum | `default` · `conservative` · `aggressive`. `conservative` halves the request rate for fragile sources. |
| `robots_respect` | bool | Default `true` for `website`/`forum`. **Cannot be set to `false`** — the validator rejects it. Present only to make the guarantee explicit. |

### 2.5 Derived / system-managed (not user-editable)

`last_run_at` · `last_success_at` · `last_cursor` · `consecutive_failures` · `items_collected_total` · `relevant_rate_30d` · `trusted_insights_attributed` · `health` (`ok` · `degraded` · `stale` · `disabled_by_system`)

`trusted_insights_attributed` is the field that matters at the monthly review: a source that has produced zero trusted insights in 60 days is a candidate for removal regardless of how much it collected.

---

## 3. Per-platform `type` values and options

| Platform | `type` | Required | `platform_options` |
|---|---|---|---|
| `reddit` | `subreddit` | `url` | `sort` (`new`\|`hot`\|`top`), `time_filter` (`day`\|`week`\|`month`), `min_score`, `min_comments`, `include_flairs[]`, `exclude_flairs[]` |
| `reddit` | `keyword` | `query` | `subreddits[]` (scope search), `sort`, `time_filter` |
| `reddit` | `user` | `url` | `include_comments` — use sparingly; see privacy note §6 |
| `youtube` | `channel` | `url` | `include_shorts`, `min_views`, `comment_order` (`relevance`\|`time`), `include_video_description` |
| `youtube` | `video` | `url` | `comment_order`, `max_comments` |
| `youtube` | `keyword` | `query` | `order`, `published_after_days`, `region_code`, `relevance_language` |
| `x` | `account` | `handle` | `include_replies`, `include_reposts` |
| `x` | `keyword` | `query` | `lang`, `min_faves`, `exclude_retweets` |
| `rss` | `feed` | `url` | `full_text_fetch` (follow link if the feed is truncated **and** robots.txt allows), `item_selector` |
| `forum` | `feed` | `url` | Must be an RSS/Atom or documented API endpoint. HTML-only forums → `unsupported`. |
| `website` | `sitemap` | `url` | `path_include[]`, `path_exclude[]`, `max_pages_per_run` |
| `community` | `feed` | `url` | Public read-only feeds only (e.g. Discourse `/latest.json`, public Lemmy). |

**Unsupported by design:** anything requiring login, private groups, DMs, paywalled archives, or anti-bot circumvention. The adapter must return `SourceUnsupported(reason)`, and the source is reported in the radar as uncollectable rather than silently skipped.

---

## 4. Example configuration (5–10 sources)

Real platform names are used where they are public and well-known; fictional examples are marked `example.com`.

```yaml
version: 1

audience:
  id: calm_productivity
  name: "Busy knowledge workers seeking calmer routines"
  description: >
    28–45, desk/WFH knowledge workers, often lapsed meditation-app users, notification-tolerant,
    privacy-minded, minimalism-leaning; overlaps ADHD-adjacent routine seekers.
  goals:
    - "pause during a stressful workday without a 20-minute session"
    - "keep a simple routine that survives a bad week"
  not_our_audience:
    - "clinical treatment seekers"
    - "meditation-retreat / teacher-training audience"
  segments: [beginner, routine_rebuilder, adhd_adjacent, founder]
  languages: [en]
  primary_countries: [US, GB, CA, AU]

defaults:
  enabled: true
  priority: medium
  collection_frequency: daily
  max_age_days: 30
  min_relevance_score: 50
  collect_comments: true
  max_items_per_run: 100
  max_comments_per_item: 50
  language: en

sources:

  # 1 — high-signal niche subreddit
  - id: reddit_mindfulness
    platform: reddit
    type: subreddit
    name: "r/Mindfulness"
    url: "https://www.reddit.com/r/Mindfulness/"
    priority: high
    collection_frequency: daily
    target_topics: [mindfulness practice, daily habits, meditation dropout]
    relevance_keywords: [reminder, habit, routine, streak, forget, consistency, timer, bell]
    relevance_phrases: ["can't stick with it", "keep forgetting", "fell off"]
    exclusion_keywords: [retreat, teacher training, ayahuasca, supplement]
    min_relevance_score: 45
    segments: [beginner, routine_rebuilder]
    platform_options:
      sort: new
      min_comments: 2
    notes: "Primary source for practice-abandonment language."

  # 2 — adjacent, noisier, tighter gate
  - id: reddit_productivity
    platform: reddit
    type: subreddit
    name: "r/productivity"
    url: "https://www.reddit.com/r/productivity/"
    priority: medium
    target_topics: [focus, breaks, workday structure, burnout prevention]
    relevance_keywords: [break, focus, pomodoro, reminder, notification, overwhelm, deep work]
    exclusion_keywords: [resume, salary, job interview, crypto, "hiring"]
    min_relevance_score: 60
    max_items_per_run: 60
    notes: "High volume, low density — gate is deliberately strict."

  # 3 — segment-specific
  - id: reddit_adhd_routines
    platform: reddit
    type: subreddit
    name: "r/getdisciplined"
    url: "https://www.reddit.com/r/getdisciplined/"
    priority: medium
    target_topics: [routine building, accountability, habit collapse]
    relevance_phrases: ["I always start and stop", "nothing sticks", "reminders don't work"]
    exclusion_keywords: [nofap, weight loss challenge]
    segments: [adhd_adjacent, routine_rebuilder]
    min_relevance_score: 55

  # 4 — cross-subreddit keyword sweep
  - id: reddit_kw_mindful_reminders
    platform: reddit
    type: keyword
    name: "Reddit search: mindful reminder apps"
    query: '("mindfulness app" OR "meditation reminder" OR "mindful bell" OR "interval timer") self:yes'
    priority: high
    collection_frequency: daily
    platform_options:
      subreddits: [Mindfulness, Meditation, productivity, digitalminimalism, iosapps]
      sort: new
      time_filter: week
    target_topics: [app selection, app fatigue, reminder apps]
    min_relevance_score: 55
    notes: "Catches high-intent app-shopping threads the subreddit listings miss."

  # 5 — YouTube comments (richest pain language, highest quota cost)
  - id: yt_calm_productivity_channels
    platform: youtube
    type: keyword
    name: "YouTube: calm productivity / mindful workday"
    query: "calm productivity mindful workday routine"
    priority: medium
    collection_frequency: every_2d
    collect_comments: true
    max_items_per_run: 15
    max_comments_per_item: 100
    platform_options:
      order: relevance
      published_after_days: 60
      relevance_language: en
      comment_order: relevance
    target_topics: [workday routine, focus rituals, screen fatigue]
    exclusion_keywords: [giveaway, "link in bio", "free course"]
    min_relevance_score: 55
    notes: "Comments only; video transcripts are out of MVP scope."

  # 6 — single competitor-adjacent channel (audience side, not competitor side)
  - id: yt_channel_example_wellness
    platform: youtube
    type: channel
    name: "Example Wellness Channel (illustrative)"
    url: "https://www.youtube.com/@example-wellness"
    priority: low
    collection_frequency: weekly
    collect_comments: true
    max_comments_per_item: 60
    platform_options:
      include_shorts: true
      min_views: 2000
    notes: "Fictional example. Audience questions in comments are the target, not the videos."

  # 7 — X, disabled until access is confirmed
  - id: x_kw_meditation_reminder
    platform: x
    type: keyword
    name: "X search: meditation reminder"
    query: '("meditation reminder" OR "mindfulness bell") -is:retweet lang:en'
    enabled: false
    priority: low
    collection_frequency: daily
    platform_options:
      exclude_retweets: true
    notes: "Enable only when an API tier permitting search is active. Adapter reports 'unsupported: no_search_access' otherwise."

  # 8 — RSS feed of a niche blog's comment stream
  - id: rss_example_forum
    platform: forum
    type: feed
    name: "Example Habit Forum — latest threads (illustrative)"
    url: "https://forum.example.com/latest.rss"
    priority: medium
    collection_frequency: daily
    platform_options:
      full_text_fetch: true
    target_topics: [habit tracking, streaks, routine tools]
    exclusion_patterns: ['^\[Announcement\]', 'sponsored']
    min_relevance_score: 50

  # 9 — public Discourse community (read-only JSON)
  - id: community_example_discourse
    platform: community
    type: feed
    name: "Example Focus Community (illustrative)"
    url: "https://community.example.com/latest.json"
    priority: low
    collection_frequency: every_2d
    rate_limit_class: conservative
    min_relevance_score: 55
    notes: "Public endpoint only. No login. If it ever requires auth, mark unsupported."

  # 10 — review-mining placeholder (Phase 5)
  - id: website_example_reviews
    platform: website
    type: sitemap
    name: "Example Review Site (illustrative, Phase 5)"
    url: "https://reviews.example.com/sitemap.xml"
    enabled: false
    priority: low
    collection_frequency: weekly
    robots_respect: true
    platform_options:
      path_include: ["/reviews/mindfulness-apps/"]
      max_pages_per_run: 25
    notes: "Disabled until ToS review completes (see DOCUMENTATION-COMPLETE open questions)."
```

---

## 5. Validation rules

The loader fails fast on:

1. Duplicate or malformed `id`.
2. `platform`/`type` pair not implemented by any adapter.
3. `type: keyword` without `query`, or non-keyword type without `url`.
4. `collection_frequency: hourly` on `priority: low`/`medium`.
5. `max_items_per_run > 500` or `max_comments_per_item > 500` (cost guard).
6. `robots_respect: false`, or any option that implies auth bypass.
7. Regex in `exclusion_patterns` that fails to compile.
8. `min_relevance_score` outside 0–100.
9. Secrets inline (any value matching a key/token pattern) — hard error with remediation text.
10. `enabled: true` on a source whose `auth_profile` credentials are missing (warn + auto-degrade at runtime, not a load failure).

## 6. Operational and privacy notes

- **Priority ≠ quality.** Priority allocates quota. A `low` source that produces trusted insights should be promoted at the monthly review; a `high` source that produces none should be demoted or removed.
- **`reddit/user` and `x/account` sources collect from identifiable individuals.** Only public accounts, only for topical signal, never to build a person-level profile. Author records store a stable hashed identifier plus platform handle; no cross-platform identity resolution, no follower-graph collection, no contact enrichment (see `04-system/data-model.md § Author`).
- **Delete cascades.** Removing a source stops collection but retains history by default; `radar source purge <id>` deletes raw payloads and quarantines dependent insights for review (they lose evidence and therefore cannot stay trusted).
- **Monthly source review** is a first-class ritual, not an admin chore: for each source report items collected, relevance rate, insights produced, trusted insights, and cost share. Keep, tighten, or cut.
