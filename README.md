# Audience Radar

> **Reddit Integration Note**
> 
> **Status:** Pending Reddit Data API approval.
> 
> The Reddit adapter interface and integration design are implemented. Live Reddit API access remains disabled pending Reddit Data API approval.
>
> - Public data only
> - Official Reddit Data API only
> - No scraping
> - No private communities
> - No posting, commenting, voting, or moderation
> - OAuth credentials are not included in this repository and are managed securely via environment variables.

## 1. Reddit API Usage & Compliance

Audience Radar uses Reddit's official Data API as a read-only source for internal audience research.

The Reddit integration:
- Uses OAuth 2 authentication.
- Uses the official Reddit Data API only.
- Reads publicly accessible posts and comments within explicitly configured communities.
- Does not access private messages or private communities.
- Does not post, comment, vote, moderate, or automate Reddit accounts.
- Does not scrape Reddit pages.
- Does not bypass authentication, rate limits, anti-bot protections, paywalls, or other technical controls.
- Monitors API rate-limit information and backs off when required.
- Does not sell, license, or redistribute Reddit content.
- Does not use Reddit content to train, fine-tune, or otherwise improve an AI/ML model unless explicitly permitted by Reddit and the applicable rights holders.
- Keeps source references so findings can be traced back to the original Reddit conversation.
- Applies human review before insights are used downstream.
- Removes Reddit content when required by Reddit's policies or the approved use case.

## 2. Reddit Data Scope

The Reddit integration is limited to publicly accessible posts and comments available through the official Reddit Data API.

It does not access:
- private messages
- private communities
- restricted user data
- user credentials
- account passwords
- voting actions
- moderation actions

## 3. Reddit Data Retention

Audience Radar stores only the Reddit data necessary for its approved use case.
The system does not intentionally retain deleted Reddit content.
Reddit-sourced content and user-related data are subject to deletion when required by Reddit's policies, applicable terms, or an approved use case.
Source identifiers and metadata are kept only as necessary for traceability and compliance.

*(Note: Deletion handling is part of the Reddit adapter compliance implementation and must be completed before production use.)*

## 4. What Audience Radar is

Audience Radar is an internal audience research tool that retrieves relevant public conversations through official platform APIs and organizes them into evidence-backed insights for human review.

**Why it exists:** Audience Radar helps an internal marketing team identify recurring audience questions, pain points, and language from public conversations. The system provides source references so findings can be reviewed against the original conversation before use.

**Important distinction:** Audience Radar does not scrape Reddit pages. Reddit data is accessed only through the official Reddit Data API.

## 5. Insight Types

Audience Radar extracts the following core insights:
- **Pains** (what the audience is struggling with)
- **Questions** (what they keep asking)
- **Objections** (why they hesitate)
- **Audience language** (exact words and phrasing)
- **Emerging topics**

## 6. How the system works

```text
Sources (e.g., Official Reddit API)
        ↓  Collection Layer        minimally necessary source data
        ↓  Normalization Layer     one canonical shape for analysis
        ↓  Storage Layer           retrieval metadata + normalized records
        ↓  AI Analysis Layer       LLM insight extraction (content analysis only)
        ↓  Insight Layer           pains / questions / objections / language / topics
        ↓  Reporting Layer         human-reviewable summaries
```

Two non-negotiable properties:

1. **Evidence-first:** Every insight carries source references linking back to the original Reddit post or comment where applicable.
2. **Analysis Separation:** AI-generated interpretations are separated from source data. Reddit-sourced content can be removed when required by Reddit's policies or deletion requirements.

## 7. AI Agents

The system uses specialized AI agents to analyze retrieved content:
- **Insight Agent:** Extracts pains, questions, objections, and language from one item.
- **Clustering Agent:** Merges many phrasings of the same problem into one topic.
- **Trend Agent:** Compares aligned time windows and classifies momentum.
- **Radar Agent:** Writes the weekly executive summary from trusted insights only.

**Important constraint:** These agents operate on normalized research records and do not train models on Reddit content. LLMs are used solely for the analysis of retrieved content; Reddit content is not used to train or fine-tune models.

## 8. Development & Implementation Rules

1. Never implement a collection method that bypasses authentication, anti-bot protection, paywalls, or private-group access. 
2. Do not use Reddit content to train, fine-tune, or otherwise improve an AI/ML model unless explicitly permitted by Reddit and the applicable rights holders.
3. The Reddit adapter must monitor Reddit API rate-limit headers and back off when limits are approached. It must not intentionally exceed or circumvent Reddit API limits.
4. Nothing is published downstream that hasn't been human-reviewed.

## 9. Roadmap

| Phase | Theme |
|---|---|
| 0 | Documentation |
| 1 | Reddit API integration |
| 2 | Audience insight extraction |
| 3 | Human review and reporting |
| 4 | Additional approved data sources |
