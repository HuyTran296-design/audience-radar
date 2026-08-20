# Audience Radar — Documentation Package

> **Reddit Integration Note**
> 
> **Status:** Pending Reddit Data API approval.
> 
> The Reddit adapter is implemented as an external, read-only data source. OAuth credentials are not included in this repository and are managed securely via environment variables.

**Version:** 1.0 (specification freeze for implementation)
**Status:** Phase 0 complete — ready for an AI coding agent (Antigravity) to implement
**Owner:** Product / Growth
**Last updated:** 2026-08-18

---

## 1. What Audience Radar is

Audience Radar is an **audience intelligence system**. It continuously listens to public conversations from a defined target audience (Reddit, YouTube, X, forums, RSS, public communities), filters aggressively for signal, and produces **evidence-backed intelligence**:

- what the audience is struggling with (pains)
- what they keep asking (hot questions)
- why they don't buy (objections)
- the exact words they use (audience language)
- what is accelerating right now (emerging topics)
- what competitors cover and, more importantly, what they *don't* (competitor gaps)
- what to create next (content opportunities) and what to build next (product opportunities)

It is not a dashboard of vanity metrics and not a scraper. It is a pipeline that turns raw public conversation into **ranked, traceable, reviewable decisions**.

## 2. Why it exists

Creators and small teams guess. They guess topics, guess hooks, guess wording, and guess what their market objects to. The information that would remove the guessing is public — it's sitting in comment threads — but it is unstructured, repetitive, and too voluminous to read.

Existing tools each solve one slice and none solve the job:

| Category | What it gives you | What it doesn't |
|---|---|---|
| Social listening (Brandwatch, Mention) | Brand mention volume + sentiment | Doesn't tell you what to make; brand-centric, not audience-centric |
| Generic scrapers | Rows of text | No relevance, no interpretation, no evidence chain |
| Social analytics | Your own post performance | Nothing about people who never saw your posts |
| AI content generators | Fluent output from a blank prompt | No grounding in real audience demand; invents the premise |
| Competitor monitors | What competitors published | Not what the audience wanted and didn't get |

Audience Radar sits between listening and creating: **demand discovery with citations**.

## 3. How the system works

```text
Sources (Reddit / YouTube / X / RSS / forums / websites)
        ↓  Collection Layer        adapters, rate limits, ToS-safe access
        ↓  Normalization Layer     one canonical Conversation shape, dedup
        ↓  Storage Layer           raw + normalized, immutable, timestamped
        ↓  AI Analysis Layer       cheap relevance gate → LLM insight extraction
        ↓  Insight Layer           pains / questions / objections / language / topics
        ↓  Scoring Layer           relevance, pain, frequency, trend, intent, competition, opportunity, confidence
        ↓  Reporting Layer         weekly radar + markdown knowledge base
        ↓  Content Engine          (Phase 4 integration, contract defined here)
```

Two non-negotiable properties:

1. **Evidence-first.** Every insight carries `evidence[]` pointing at real, retrievable sources. `Observation → Evidence → AI interpretation → Confidence → Recommendation` — never `AI assumption → fact`.
2. **Layers are append-only.** AI interpretation never overwrites raw or normalized data.

## 4. Documentation structure

```text
README.md                                  ← you are here
00-product/
  product-brief.md                         vision, personas, JTBD, MVP scope
  goals-and-success-metrics.md             product / content / system metrics + MVP targets
  roadmap.md                               phases 0–5 with exit criteria
01-sources/
  sources.md                               canonical source config schema + examples
  competitors.md                           competitor config + what to extract
02-insights/
  audience-pains.md                        pain point schema + lifecycle
  hot-questions.md                         question schema + intent taxonomy
  objections.md                            objection schema + taxonomy
  audience-language.md                     verbatim language capture (3-layer separation)
  emerging-topics.md                       trend detection rules
  competitor-gaps.md                       demand vs coverage + gap scoring
03-opportunities/
  content-opportunities.md                 opportunity schema + weighted scoring
  product-opportunities.md                 product/feature/service/offer + evidence thresholds
  weekly-radar.md                          weekly executive summary + worked example
04-system/
  architecture.md                          layers, MVP stack, deployment
  data-model.md                            entities, fields, relationships, indexes
  agents.md                                9 AI agents: contracts + guardrails
  workflows.md                             scheduled workflows + state machines
  scoring-system.md                        all formulas, ranges, thresholds  ← canonical
  source-adapters.md                       adapter interface + per-platform limits
  implementation-plan.md                   13 milestones for Antigravity  ← build order
DOCUMENTATION-COMPLETE.md                  decisions, risks, open questions, agent instructions
```

**Conflict rule:** if two documents disagree, precedence is
`04-system/scoring-system.md` (numbers) > `04-system/data-model.md` (shapes) > `DOCUMENTATION-COMPLETE.md` (decisions) > everything else.

## 5. MVP in one paragraph

A modular monolith in Python 3.12 with a Typer CLI and APScheduler, SQLite (WAL) for storage, `sqlite-vec` for embeddings, a Reddit adapter (official API) + YouTube adapter (Data API v3) + RSS adapter at launch, X behind a feature flag pending access, a two-stage relevance gate (rules + embeddings, LLM only for the grey zone), LLM insight extraction with strict JSON schemas and mandatory evidence IDs, HDBSCAN-style semantic clustering into topics, week-over-week trend detection, an opportunity scorer, and a weekly radar rendered to markdown in a git-tracked `knowledge/` directory. Human review promotes insights from `candidate` to `trusted`. Nothing is published downstream that hasn't been reviewed.

## 6. Data flow (canonical)

```text
Raw Data          immutable payload as returned by the platform (+ fetch metadata)
   ↓
Normalized Data   Conversation / Comment / Author in one canonical shape
   ↓
AI Analysis       per-item extraction: relevance, pains, questions, objections, phrases
   ↓
Aggregated        clusters → PainPoint / Question / Objection / Topic / Trend / Gap
   ↓
Opportunities     scored, ranked, human-reviewable
   ↓
Reports           weekly radar + markdown knowledge base
```

## 7. AI agents

| Agent | One-line job |
|---|---|
| Collector | Plan and execute collection runs per source, respect limits |
| Relevance | Decide in/out for the target audience (grey zone only) |
| Insight | Extract pains, questions, objections, desires, intent, language from one item |
| Clustering | Merge many phrasings of the same problem into one topic |
| Trend | Compare aligned time windows, classify momentum |
| Competitor | Characterize competitor coverage and performance |
| Gap | Diff audience demand against competitor supply |
| Opportunity | Turn insights + gaps into scored content/product opportunities |
| Radar | Write the weekly executive summary from trusted insights only |

Full contracts, system instructions, and hallucination guards: `04-system/agents.md`.

## 8. Insight types

`pain_point` · `question` · `objection` · `desired_outcome` · `audience_phrase` · `topic` · `trend` · `competitor_gap` · `content_opportunity` · `product_opportunity`

All share the review lifecycle:
`detected → analyzed → candidate → reviewed → trusted → archived` (with `rejected` as a labelled terminal state that feeds relevance training).

## 9. Scoring

All scores are integers `0–100` and are reported **in bands**, not as false precision:

| Band | Range |
|---|---|
| low | 0–24 |
| moderate | 25–49 |
| high | 50–74 |
| critical / exceptional | 75–100 |

Confidence is `0.00–1.00` (2 dp) with bands `low <0.5`, `medium 0.5–0.74`, `high ≥0.75`. Insights below `0.5` confidence never appear in a radar report as anything but "watchlist". Canonical formulas: `04-system/scoring-system.md`.

## 10. Roadmap

| Phase | Theme | Outcome |
|---|---|---|
| 0 | Documentation | This package |
| 1 | MVP | Reddit + YouTube + RSS → pains/questions → weekly radar |
| 2 | Intelligence | Clustering quality, trends, audience language, human-in-the-loop |
| 3 | Competitor intelligence | Competitor coverage + gap engine |
| 4 | Content Engine integration | Opportunities → briefs → multi-platform content |
| 5 | Market Radar | Multi-audience, multi-language, product opportunity discovery |

Details and exit criteria: `00-product/roadmap.md`.

## 11. How Antigravity should use this documentation

1. Read `DOCUMENTATION-COMPLETE.md` first — it contains the binding decisions and the exact build instructions.
2. Read `04-system/implementation-plan.md` and implement **milestone by milestone**. Do not skip ahead; each milestone has acceptance criteria and tests that must pass before the next begins.
3. Treat `04-system/data-model.md` and `04-system/scoring-system.md` as the source of truth for shapes and numbers. If a prose file disagrees, the system docs win.
4. Do not invent new architecture. If a requirement seems missing, check `DOCUMENTATION-COMPLETE.md § Open questions` — if it's listed there, stub it behind an interface and keep going.
5. Never implement a collection method that bypasses authentication, anti-bot protection, paywalls, or private-group access. If a source cannot be collected legally through a documented API or public feed, mark the adapter `unsupported` and surface the reason.
6. Prioritize working software over abstraction. One concrete adapter working end-to-end beats three abstract ones.
