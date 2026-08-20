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
- Does not scrape Reddit pages. All Reddit data access is performed through OAuth-authenticated Reddit API requests.
- Does not bypass authentication, rate limits, anti-bot protections, paywalls, or other technical controls.
- Monitors API rate-limit information and backs off when required.
- Does not sell, license, or redistribute Reddit content.
- Does not use Reddit content to train, fine-tune, or otherwise improve AI/ML models.
- Keeps source references linking back to the original Reddit post or comment, including the applicable Reddit attribution required by Reddit's Developer Terms.
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

Current implementation status: Reddit deletion handling is not yet enabled because live Reddit API access is pending approval. Before production use, the Reddit adapter will implement deletion handling for removed posts/comments and deleted accounts in accordance with Reddit's current Data API requirements.

Audience Radar is designed to retain only the Reddit data necessary for its approved use case. Reddit-sourced content and related user data will be removed when required by Reddit's policies, applicable terms, an approved use case, or a valid deletion request.

The implementation will follow Reddit's current deletion requirements, including the recommended routine deletion window where applicable.

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
Sources (e.g., Reddit Data API)
        ↓  Collection Layer        minimally necessary source data
        ↓  Normalization Layer     one canonical shape for analysis
        ↓  Storage Layer           retrieval metadata + normalized records
        ↓  AI Analysis Layer       LLM insight extraction (content analysis only)
        ↓  Insight Layer           pains / questions / objections / language / topics
        ↓  Reporting Layer         human-reviewable summaries
```

Two non-negotiable properties:

1. **Evidence-first:** Every insight carries source references linking back to the original Reddit post or comment, including the applicable Reddit attribution required by Reddit's Developer Terms.
2. **Analysis Separation:** AI-generated interpretations are separated from source data. Reddit-sourced content can be removed when required by Reddit's policies or deletion requirements.

## 7. AI Agents

The system uses specialized AI agents to analyze retrieved content:
- **Insight Agent:** Extracts pains, questions, objections, and language from one item.
- **Clustering Agent:** Merges many phrasings of the same problem into one topic.
- **Trend Agent:** Compares aligned time windows and classifies momentum.
- **Radar Agent:** Writes the weekly executive summary from trusted insights only.

**Important constraint:** These agents operate on normalized research records derived from retrieved content for the approved use case. LLMs are used solely for the analysis of retrieved content; Reddit content is not used to train or fine-tune models.

## 8. Development & Implementation Rules

1. Never implement a collection method that bypasses authentication, anti-bot protection, paywalls, or private-group access. 
2. Do not use Reddit content to train, fine-tune, or otherwise improve AI/ML models.
3. The Reddit adapter must monitor Reddit API rate-limit headers and back off when limits are approached. It must not intentionally exceed or circumvent Reddit API limits.
4. Nothing is published downstream that hasn't been human-reviewed.
5. Preserve required Reddit attribution for Reddit-sourced content displayed by the application, including source links and applicable author attribution.
6. The Reddit adapter will routinely check for removed content and account deletions and implement deletion handling consistent with Reddit's current requirements.

## 9. Roadmap

| Phase | Theme |
|---|---|
| 0 | Documentation |
| 1 | Reddit API integration |
| 2 | Audience insight extraction |
| 3 | Human review and reporting |
| 4 | Additional approved data sources |

## 10. Privacy

Audience Radar is an internal tool and does not provide Reddit users with an account or user-facing Reddit features.

Reddit-sourced data is used only for the approved audience-research workflow and is not sold, licensed, or redistributed.

A privacy policy will be provided before production use and will describe how Reddit-sourced data is collected, used, stored, retained, and deleted.
