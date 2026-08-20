# Apple Ads API Integration Specification

This document details the architecture, authentication, and endpoint capabilities for integrating the Apple Ads API as a Tier 2 Data Source (Search Demand Signal) into Audience Radar, based on the newest **Apple Ads Platform API**.

## 1. Endpoints in Use
We will leverage the new **Apple Ads Platform API** (replacing the legacy Campaign Management API v5) as it introduces critical "Insights" endpoints alongside standard reporting capabilities.

*   **Search Term Popularity Insights:** `POST /api/v1/insights/searchterms`
    *   *Purpose:* Fetch official search popularity indicators for specific keywords without needing an active campaign running for them.
*   **Search Term Reports:** `POST /api/v1/reports/campaigns/{campaignId}/searchterms`
    *   *Purpose:* Fetch performance data (taps, impressions, conversions) for the actual search terms users entered before tapping an ad.
*   **Keyword Reports:** `POST /api/v1/reports/campaigns/{campaignId}/keywords`
    *   *Purpose:* Fetch performance data for the targeted keywords configured in Zen Bell's ad groups.

## 2. Available Fields and Metrics
Based on the API capabilities, the following data points can be extracted and mapped to the `SearchSignal` entity:
*   **Search Behavior:**
    *   `searchTermText` (The actual term entered by the user)
    *   `keyword` (The targeted keyword triggering the ad)
    *   `matchType` (Exact, Broad, Search Match)
*   **Performance Metrics:**
    *   `impressions`
    *   `taps`
    *   `conversions`
    *   `localSpend`
    *   `avgCPT` (Cost Per Tap)
    *   `avgCPA` (Cost Per Acquisition)
    *   `ttr` (Tap-Through Rate)
    *   `conversionRate`
*   **Demand/Popularity:**
    *   `searchPopularity` (A relative index score provided by the Insights endpoint indicating search volume)
*   **Dimensions:**
    *   `countryOrRegion`
    *   `date`

## 3. Authentication Requirements
The Apple Ads Platform API utilizes OAuth 2.0 with a signed JWT.
Credentials required in the environment:
*   `APPLE_ADS_CLIENT_ID`
*   `APPLE_ADS_TEAM_ID`
*   `APPLE_ADS_KEY_ID`
*   `APPLE_ADS_PRIVATE_KEY` (The `.p8` key file contents)

The auth flow involves generating a JWT signed with the `APPLE_ADS_PRIVATE_KEY`, and exchanging it at `https://appleid.apple.com/auth/oauth2/token` for a short-lived bearer access token.

## 4. Rate Limits
*   Apple Ads typically imposes limits such as 100 requests per minute or 500 requests per hour depending on the endpoint.
*   The adapter must implement standard HTTP `429 Too Many Requests` handling with exponential backoff.

## 5. Historical Data Limitations
*   Reporting endpoints support historical queries, usually limited to the retention period of the account (often up to 3-5 years, depending on the specific Apple Ads org tier).
*   Search Popularity Insights may only reflect current or recent rolling windows, rather than exact granular historical tracking. Audience Radar will need to periodically poll and store this data to build its own historical trendline for "Search Demand Scoring".

## 6. Geographic / Language Limitations
*   Metrics can be segmented by `countryOrRegion`.
*   Apple Ads does not natively expose the user's specific `language` setting in standard search term reports (ads are targeted by storefront/region). Language will be inferred or tied to the storefront country.

## 7. Architecture Considerations
*   **Missing Metrics:** If a keyword has no active spend, fields like `taps` and `impressions` will be null. The scoring engine will fallback to the Insights `searchPopularity` score.
*   **Separation of Types:** The adapter will map `searchTermText` to `keyword_type = "user_search_term"` and `keyword` to `keyword_type = "target_keyword"`.
