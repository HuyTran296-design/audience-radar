# Objections

An **objection** is a stated reason not to adopt, buy, switch to, or keep using something in the category. Objections are the highest-leverage insight type for conversion work and the most commonly misread: the stated objection is frequently not the real one.

Storage: `knowledge/insights/objections/<objection_id>.md` + `Objection` table.

---

## 1. Objection taxonomy

| Code | Objection type | Surface form | Usual underlying concern |
|---|---|---|---|
| `price` | Price | "too expensive", "not paying monthly for this" | Value uncertainty, or subscription fatigue rather than the amount |
| `trust` | Trust | "another app that'll harvest my data", "seems scammy" | Prior betrayal; wants proof, not reassurance |
| `complexity` | Complexity | "looks complicated", "too many settings" | Fear of another abandoned system |
| `time` | Time | "no time for this", "who has 20 minutes" | Believes the benefit requires more time than they can commit |
| `quality` | Quality | "the sounds are awful", "feels cheap" | Craft signals; often a proxy for trust |
| `switching` | Switching | "already use X", "not migrating my data" | Sunk cost + migration effort |
| `security` | Security/privacy | "why does it need that permission" | Data handling, on-device vs cloud |
| `implementation` | Implementation | "I'd never keep it up", "how would this fit my day" | Doubts about integration into real routine |
| `efficacy` | Does it work | "does this actually do anything" | Wants mechanism or evidence |
| `necessity` | Necessity | "can't I just use a timer/alarm" | Substitute is good enough — the most dangerous class |

`necessity` deserves the flag: it is where substitutes (a phone alarm, a paper journal) win silently, and it rarely appears in customer interviews because those people never became customers.

---

## 2. Canonical schema

```yaml
id: obj_01J8N5T2WQ4ZK9P1
slug: another-app-i-will-ignore
type: objection
objection_type: implementation
secondary_type: complexity

objection: "I'd download it and forget about it like the last three"
normalized_objection: "Expects to abandon the app as they abandoned previous ones"

# --- measurement ---
frequency: 22
frequency_distinct_authors: 19
frequency_window: last_30_days
frequency_change: +0.10
trend: stable
confidence: 0.77
severity_to_conversion: high         # low | moderate | high | blocking

# --- audience & context ---
audience_segment: [routine_rebuilder, beginner]
context: >
  Raised in app-recommendation threads, usually as a self-deprecating aside rather
  than a challenge to a specific product. Appears before price is ever discussed.
raised_at_stage: consideration        # awareness | consideration | evaluation | purchase | onboarding | renewal
directed_at: category                 # category | our_product | competitor | substitute

# --- interpretation ---
stated_concern: "Will abandon it like previous apps"
likely_underlying_concern: >
  Not skepticism about the product — a prediction about themselves, based on a history
  of failed attempts. The blocker is self-efficacy, not features.
underlying_confidence: 0.66
evidence_for_underlying:
  - "18 of 22 instances reference a prior failed attempt in the same sentence"
  - "Only 3 instances mention a specific product flaw"

# --- evidence ---
source_count: 22
distinct_authors: 19
platforms: {reddit: 15, youtube: 6, forum: 1}
platform_spread: 3
representative_quotes:               # ≤3, ≤15 words each
  - text: "graveyard of habit apps on my phone already"
    evidence_id: ev_01J8N6...
    platform: reddit
paraphrased_examples:
  - "Predicts abandonment within two weeks based on past attempts."
  - "Describes a phone full of unused wellness apps as the reason for hesitating."
evidence: [...]                       # same structure as audience-pains.md
contradicting_evidence:
  - evidence_id: ev_01J8N9...
    note: "Two authors report a low-effort tool that did stick; both cite it requiring no daily decision."

# --- response ---
possible_responses:
  - approach: acknowledge_and_reframe
    summary: "Agree with the prediction; change what is being asked of them (10 seconds, not a session)."
    risk: "Must not become a promise about outcomes."
  - approach: evidence
    summary: "Show the mechanism that makes this different from the apps they abandoned."
    risk: "Requires real evidence; no efficacy claims."
  - approach: reduce_commitment
    summary: "Frame the first week as reversible and low-cost."
    risk: "None material."
responses_to_avoid:
  - "Motivation/discipline framing — blames the user for the thing they already fear."
  - "Any claim about health, attention, or clinical outcomes."

content_opportunity:
  exists: true
  angle: "The app graveyard, taken seriously"
  format: [short_video, landing_section, faq]
  hook: "You're right. You probably will forget about it."
  opportunity_ref: opp_01J8N7...
product_opportunity:
  exists: true
  summary: "Zero-decision default state — works without setup on day one."
  evidence_sufficient: false          # see product-opportunities.md thresholds
  ref: prod_01J8NA...

# --- four-way separation ---
observed_fact: "19 distinct authors across 3 platforms pre-emptively predicted their own abandonment, 18 citing prior failed attempts."
ai_interpretation: "The objection is about self-efficacy history, not product features."
hypothesis: "Reducing required commitment at onboarding addresses this better than proving quality."
recommended_action: "Write the acknowledge-and-reframe piece; test the framing in the FAQ before the landing page."

status: trusted
created_at: 2026-06-28T00:00:00Z
updated_at: 2026-08-17T00:00:00Z
version: 2
```

---

## 3. Where objections come from

| Signal | Typical platform | Reliability |
|---|---|---|
| Recommendation threads ("looking for an app that…") | Reddit | high — objections are stated before purchase |
| Comment sections under competitor content | YouTube | high — reacting to a concrete offer |
| Complaint threads about incumbents | Reddit, forums | high for `quality`, `price`, `trust` |
| Reviews (Phase 5) | App Store, G2 | very high but post-purchase — biased toward `implementation` and `quality` |
| Our own content comments | any | high but small-n; flag `directed_at: our_product` |

**Pre-purchase objections and post-purchase complaints are different data.** `raised_at_stage` keeps them distinguishable; mixing them produces content that answers the wrong question.

---

## 4. Underlying-concern inference (constrained)

The most valuable field is also the most hallucination-prone. Rules:

1. `likely_underlying_concern` is **always** labelled `ai_interpretation`, never `observed_fact`.
2. It requires **≥3 supporting evidence items** and an explicit `evidence_for_underlying[]` list of observable patterns. No pattern, no inference.
3. `underlying_confidence` is capped at `min(0.8, insight_confidence)`. The system may not be more certain about a motive than about the objection itself.
4. If evidence is consistent with two different underlying concerns, both are recorded with their support; the agent must not pick one for narrative tidiness.
5. Psychological framing is limited to what the audience says about itself. No clinical inference, no diagnosis language, ever — this is a hard guardrail, not a style note.

---

## 5. Scoring

```text
objection_priority =
    0.30 × frequency_score
  + 0.25 × conversion_severity        # blocking 100 · high 75 · moderate 45 · low 20
  + 0.20 × stage_weight               # purchase 100 · evaluation 85 · consideration 65 · awareness 40 · onboarding 70 · renewal 80
  + 0.15 × trend_score
  + 0.10 × addressability             # can content/product realistically move it? (0–100, human-editable)
```

`addressability` is deliberately human-editable: some objections are true and correct (the product genuinely isn't for that person), and the right action is to stop targeting them, not to write a rebuttal. Objections with `addressability < 30` are reported under "Who this isn't for" rather than as opportunities.

---

## 6. Reporting rules

1. Objections appear in the weekly radar under **"Why they don't buy"** with frequency, trend, and one paraphrase.
2. Every objection with a proposed response carries `responses_to_avoid` — the guardrail travels with the opportunity.
3. Objections never become marketing claims. "Users say competitors are overpriced" is an observation about statements, not a fact about prices.
4. An objection about a *named* competitor is reported with the same care as a competitor claim: scoped to collected data, dated, and never generalized.
5. Objections that contradict a trusted pain point are surfaced as a **conflict**, not silently reconciled. Conflicts are shown to the human; the system does not pick a winner.
