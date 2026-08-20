# Product Brief — Audience Radar

## 1. Product name

**Audience Radar** — audience intelligence for people who have to publish and build.

Internal codename for the downstream system: **Content Engine** (separate product surface, integrated in Phase 4).

## 2. Product vision

> Nobody who creates should have to guess what their audience needs.

Audience Radar turns the public record of a market's frustrations into a ranked, cited, reviewable list of things worth making. In three years the ambition is that "check the radar" replaces "brainstorm ideas" as the first step of a content or roadmap cycle.

## 3. Problem statement

Creators, founders, and small marketing teams face a demand-discovery problem disguised as a content problem.

**Observable symptoms**

1. Topic selection is intuition-driven; hit rate is unpredictable and unexplained.
2. Copy uses the company's vocabulary, not the audience's, so it reads as generic even when the product is good.
3. Objections are discovered in sales calls and churn surveys — after money has been spent.
4. Research is done in bursts (a weekend of Reddit reading before a launch), then goes stale.
5. Competitor analysis catalogues what competitors *did*, which teaches you to imitate rather than to find the space they left open.
6. AI writing tools removed the cost of producing content but not the cost of choosing what to produce — so output volume went up and relevance did not.

**Root cause**: the raw signal is public but unstructured, extremely repetitive, and mixed with noise at roughly 20:1. Reading it properly is a full-time job nobody has. So it doesn't get read.

**What "solved" looks like**: a Monday-morning document, five minutes to read, that says *here is what changed in your market this week, here is the evidence, here are the three things worth making, and here is one thing you should stop planning*.

## 4. Target users

Initial user (MVP): **the solo creator or the 1–5 person marketing team that ships weekly and has no research function.**

| Segment | Priority | Why |
|---|---|---|
| Solo content creator | P0 | Highest pain, fastest decision cycle, no procurement |
| Small marketing team (2–5) | P0 | Same pain, has budget, needs shareable output |
| Founder / indie product builder | P1 | Wants product opportunities as much as content |
| Product marketer at a larger company | P2 | Values evidence chain for internal persuasion; slower to adopt |
| Personal brand / consultant | P2 | Values audience language most of all |
| Agency | P3 | Multi-client needs (workspaces) are out of MVP scope |

## 5. User personas

### P1 — "Mai", solo creator, 34

Publishes 3 short videos + 1 newsletter per week in the calm-productivity niche. Her single hardest recurring decision is *what should this week's video be about?* Spends 3–5 hours a week browsing Reddit and comment sections and calls it "research" while knowing it is skimming. Vulnerable to chasing whatever a big account posted. Success for Mai = a shortlist of 5 topics with the audience's own phrasing attached, ranked, every Monday.

- Tech comfort: high on tools, low on infrastructure. Will run a CLI if the README is good; will not operate Kubernetes.
- Budget sensitivity: extreme. \$20–40/month of LLM spend is acceptable; \$300 is not.
- Failure mode that loses her: a report full of confident-sounding insights she can't verify, or a report she can't distinguish from ChatGPT output.

### P2 — "Huy", growth marketer at a 4-person agency, 29

Runs content and ASO for 2–3 app clients. Needs deliverables that survive client scrutiny: "why this topic?" must have an answer with links. Cares about audience language for App Store metadata and ad copy. Needs export, not just a dashboard.

- Success = the weekly radar is a client-facing artifact with citations.
- Failure mode: an insight presented as fact that the client can disprove in one search.

### P3 — "Dana", indie founder, 41

Building a niche B2B tool. Uses the radar for objection discovery and feature demand more than content. Wants to know which recurring complaint about incumbents is worth a roadmap slot.

- Success = product opportunities with an explicit evidence threshold ("27 distinct people across 3 platforms in 6 weeks").
- Failure mode: the system encourages her to build something on the strength of two loud posts.

## 6. Jobs to be done

| # | Job (when… I want to… so I can…) | Priority |
|---|---|---|
| JTBD-1 | When I plan this week's content, I want a ranked list of what my audience is actively struggling with, so I can pick topics with real demand instead of guessing. | P0 |
| JTBD-2 | When I write, I want the audience's exact phrasing, so my copy sounds native instead of like marketing. | P0 |
| JTBD-3 | When I justify a topic (to myself or a client), I want the evidence trail, so the decision is defensible. | P0 |
| JTBD-4 | When something new starts spreading in my niche, I want to know within a week, so I'm early rather than late. | P1 |
| JTBD-5 | When I position against competitors, I want to know which audience questions nobody is answering, so I can own that space. | P1 |
| JTBD-6 | When I plan product/offers, I want to see which problems recur with enough weight to justify building, so I don't build on anecdote. | P1 |
| JTBD-7 | When I face sales resistance, I want the recurring objections and their real underlying concern, so I can address them in content pre-emptively. | P1 |
| JTBD-8 | When an insight is wrong, I want to reject it and have the system get better, so the tool improves with use. | P2 |

## 7. Core use cases

| ID | Use case | Primary output |
|---|---|---|
| UC-1 | Weekly content planning | Weekly Radar + top 5 content opportunities |
| UC-2 | Copy/hook writing | Audience language pack for a topic |
| UC-3 | Objection handling | Objection register with response angles |
| UC-4 | Trend early warning | Emerging topic alerts (velocity-based, not volume-based) |
| UC-5 | Competitive positioning | Competitor gap list with opportunity scores |
| UC-6 | Product/offer discovery | Product opportunities meeting evidence thresholds |
| UC-7 | Onboarding a new niche | Cold-start audit: 30 days back-collected, first baseline built |
| UC-8 | Insight curation | Review queue: promote, edit, or reject candidates |

## 8. Main user journey

**Setup (once, ~30 min)**

1. Describe the audience in plain language (who they are, what they're trying to do, what they'd never care about).
2. Add 5–15 sources (`01-sources/sources.md`) and 2–5 competitors (`01-sources/competitors.md`).
3. Run the cold-start backfill: collect the last 30 days where the platform allows, build the baseline, generate the first draft insight set.
4. Review the first batch of candidates. Rejections here are the highest-value training signal the system will ever get.

**Weekly loop (~15 min of human time)**

```text
Mon 06:00  scheduler runs weekly aggregation on the week's collected data
Mon 07:00  Weekly Radar written to knowledge/radar/2026-W34.md
Mon 09:00  user reads radar (5 min), opens review queue (10 min):
             promote candidates → trusted
             reject wrong ones → feeds relevance filter
             pick 2–3 opportunities → sent to Content Engine / backlog
Daily      collection + per-item analysis runs quietly; no human input needed
```

**Monthly loop**: baseline refresh, source pruning (which sources actually produced trusted insights?), cost review, competitor re-scan.

## 9. Value proposition

**For solo creators and small teams who publish on a cadence, Audience Radar replaces guesswork and skim-reading with a weekly, cited, ranked view of what your audience actually needs — so every piece you make starts from evidence instead of a blank page.**

Three claims we are willing to be measured on:

1. **Signal over volume** — 20 relevant conversations beat 1,000 collected posts, and the system is tuned so a report never pads itself.
2. **Every insight is traceable** — no claim without retrievable evidence, and interpretation is visibly separated from observation.
3. **It runs itself and stays cheap** — daily collection is automated; cheap filtering keeps LLM cost under a hard monthly cap.

## 10. MVP scope

In scope for Phase 1 (see `00-product/roadmap.md` for exit criteria):

1. Source configuration (YAML, git-friendly)
2. Reddit monitoring (official API, subreddits + keyword search)
3. YouTube monitoring (Data API v3: channel videos, video comments, keyword search)
4. X monitoring **where access allows** — adapter implemented, disabled by default, degrades to "unsupported: no API tier"
5. Competitor monitoring (public content surfaces only; basic coverage characterization)
6. Scheduled data collection (per-source frequency: hourly / daily / weekly)
7. Data normalization to one canonical `Conversation`/`Comment` shape
8. Duplicate detection (exact hash → near-duplicate simhash → semantic threshold)
9. Relevance filtering (2-stage cheap gate, LLM adjudication for the grey zone only)
10. AI insight extraction (pains, questions, objections, desires, intent, phrases)
11. Topic clustering (embeddings + density clustering, stable cluster IDs across runs)
12. Frequency calculation (distinct-author-weighted, not raw mention counts)
13. Trend detection (aligned week-over-week + 90-day baseline)
14. Audience language extraction (verbatim / normalized / marketing layers kept separate)
15. Competitor gap detection (demand vs coverage diff — basic version)
16. Content opportunity generation with weighted scoring
17. Weekly radar report
18. Markdown knowledge storage (git-tracked `knowledge/`)
19. Human review before insights become trusted
20. Source attribution on every insight

## 11. Out of scope (MVP)

- Web UI beyond a read-only local review page (CLI + markdown is the MVP interface)
- Multi-tenant / multi-workspace / team permissions
- Instagram, TikTok, LinkedIn, Facebook, Discord, Slack collection (no compliant public-read path at MVP scale)
- Private communities, DMs, closed groups, gated content — permanently out of scope
- Sentiment scoring as a headline metric (it is a weak signal; emotional-intensity language capture replaces it)
- Automated publishing or automated outreach
- Fine-tuning models on collected data
- Paid data resellers / firehose licences
- Real-time streaming (daily batch is sufficient and 50× cheaper)
- Non-English collection as a first-class path (schema supports it; Phase 5 activates it)
- Anything that requires bypassing authentication, CAPTCHAs, rate limits, or robots.txt

## 12. Future capabilities

| Horizon | Capability |
|---|---|
| Phase 2 | Insight quality loop (rejections train the relevance gate), audience segments, alerting on velocity spikes |
| Phase 3 | Full competitor intelligence: content performance modelling, question-answered coverage matrix |
| Phase 4 | Content Engine contract: opportunity → brief → drafts, with the language pack injected |
| Phase 5 | Market Radar: multi-audience portfolios, multi-language, product/offer discovery, pricing-signal detection |
| Later | Podcast/YouTube transcript mining, review-site mining (App Store / G2 / Trustpilot), survey triangulation, shareable public radar pages |

## 13. Key product principles

1. **Evidence or silence.** If it can't be cited, it isn't reported. Insufficient evidence is a valid, expected output.
2. **Signal over volume.** Coverage is not a metric. Precision beats recall; a small trustworthy report beats a large plausible one.
3. **Separate observation from interpretation.** Four distinct labels — `observed_fact`, `ai_interpretation`, `hypothesis`, `recommendation` — appear in every insight and in every report.
4. **Never overwrite the record.** Raw → normalized → analysis → aggregate are append-only layers.
5. **The audience's words are sacred.** Verbatim language is stored and surfaced unchanged; normalization sits beside it, never over it.
6. **Humans hold the promotion power.** AI proposes `candidate`; only a human creates `trusted`.
7. **Cheap by design.** Every expensive call must be earned by a cheap filter. Cost caps are enforced in code, not in guidance.
8. **Legal and polite by construction.** Documented APIs, published feeds, robots.txt, rate limits, retention limits. No bypasses, ever — including "just for testing".
9. **Boring architecture.** Modular monolith, one process, one file-based database until measurements demand more.
10. **Volume is not a trend.** Growth and acceleration on a small base can matter more than a large flat topic — and small-N results must say so.
