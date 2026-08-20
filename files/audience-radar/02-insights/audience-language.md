# Audience Language

The most valuable output of the system and the most easily destroyed. Everything else can be re-derived from stored data; **the audience's exact wording cannot be reconstructed once it has been paraphrased away.**

Purpose: give the Content Engine (and the human) vocabulary that reads as native — hooks, headlines, ad copy, app-store metadata, FAQ phrasing — built from words the audience actually used rather than words marketers reach for.

Storage: `knowledge/insights/language/<topic_slug>.md` (the "language pack") + `AudiencePhrase` table.

---

## 1. The three-layer rule (non-negotiable)

```text
Layer 1 — EXACT AUDIENCE LANGUAGE     immutable, verbatim, attributed, original spelling/casing/typos
Layer 2 — AI-NORMALIZED TERMINOLOGY   clustered concept labels for machine use
Layer 3 — MARKETING INTERPRETATION    proposed usable phrasing, clearly authored by us
```

Rules:
1. Layer 1 records are **write-once**. No edits, no cleanup, no "fixing" grammar. A typo is data.
2. Layer 2 never replaces Layer 1 in storage or in any output. They appear side by side.
3. Layer 3 is always visibly labelled as *our* wording. It is never presented as something the audience said.
4. A quote in Layer 3 output must trace to a Layer 1 record ID or it cannot be published.
5. Translation (Phase 5) creates a *fourth* parallel field, never an overwrite. Original language first, always.

Violating any of these turns the product into a paraphrase generator, which is what every competitor already is.

---

## 2. What is tracked

| Category | Definition | Example (illustrative) | Primary use |
|---|---|---|---|
| `phrase` | Recurring multi-word expression | "fell off the wagon again" | Hooks, headlines |
| `terminology` | The audience's name for a concept | "streak anxiety" | Naming features, SEO |
| `slang` | Community-specific shorthand | "doomscroll spiral" | Native tone |
| `recurring_description` | How they describe their situation | "brain full of tabs" | Empathy openers |
| `emotional_language` | Intensity and feeling words | "exhausting", "guilt-tripped" | Emotional register calibration |
| `metaphor` | Figurative framing of the problem | "app graveyard", "notification wallpaper" | Strongest hook material |
| `complaint` | Recurring negative formulation | "it just nags me" | Objection handling |
| `desired_outcome` | How they describe what they want | "just want to breathe for a second" | Value proposition |
| `competitor_descriptor` | Words used about competitors | "bloated", "another library" | Positioning |
| `solution_descriptor` | Words used about solutions generally | "gentle", "one-tap", "no setup" | Feature naming, ASO |
| `trigger_context` | Situations they name | "3pm slump", "back-to-back meetings" | Scene/vignette content |

---

## 3. Canonical schema (Layer 1 record)

```yaml
id: phr_01J8R4V6XZ0MB2K7
type: audience_phrase
category: metaphor

exact_text: "notification wallpaper"          # IMMUTABLE. verbatim.
exact_context: "after a week it's just notification wallpaper"   # ≤15 words surrounding, verbatim
language: en
detected_language: en
original_casing_preserved: true

# --- occurrence ---
occurrences: 6
distinct_authors: 6
first_seen: 2026-07-11
last_seen: 2026-08-14
platforms: {reddit: 4, youtube: 2}
variants:                                     # near-identical phrasings, each verbatim
  - text: "became wallpaper"
    occurrences: 3
  - text: "part of the background now"
    occurrences: 2

# --- layer 2 ---
normalized_concept: cue_habituation
normalized_label: "Reminder becomes background noise"
concept_cluster: clu_habit_cue_decay
related_pain_points: [pain_01J8K2M4P7QRXV3B]
related_topics: [topic_notification_fatigue]

# --- layer 3 (ours, labelled) ---
marketing_interpretation:
  suggested_usage: "Hook line for short video and landing page section header."
  proposed_copy:                              # OUR wording, clearly attributed to us
    - "When your reminder becomes wallpaper"
    - "The alert you stopped seeing"
  authored_by: system
  requires_review: true
  do_not_use_if: "Never present as a quote from a user without the evidence link."

# --- quality ---
distinctiveness: 0.81      # 0–1: how unlike generic marketing language (§5)
resonance_signal: 0.64     # upvote/like weighting of items containing it (weak signal, labelled)
confidence: 0.74
status: trusted

evidence:
  - evidence_id: ev_01J8R5...
    url: "https://www.reddit.com/r/Mindfulness/comments/xxxxxx/"
    collected_at: 2026-07-11T18:03:00Z
    author_hash: 7c21ab90
    exact_text_in_context: "after a week it's just notification wallpaper"
```

---

## 4. Extraction pipeline

```text
relevant item
  → n-gram + phrase-chunk candidate generation (cheap, no LLM)
  → filter: stopword-only, boilerplate, platform furniture ("edit:", "TIA", "OP")
  → frequency across DISTINCT authors  (≥3 authors to become a candidate phrase)
  → LLM categorization: which of the 11 categories, is it audience-native or generic?
  → distinctiveness scoring vs a generic-marketing baseline corpus
  → cluster variants (cosine ≥0.90 on short-text embeddings)
  → store Layer 1 verbatim; derive Layer 2; propose Layer 3
```

Cost note: candidate generation is pure text processing. The LLM sees only the shortlist (typically 20–60 phrases per week), which is why this feature costs almost nothing while producing the highest-value output.

---

## 5. Distinctiveness scoring

A phrase is valuable in proportion to how *unlike* marketing boilerplate it is.

```text
distinctiveness = 0.45 × rarity_vs_baseline      # inverse doc frequency against a generic corpus
                + 0.30 × concreteness            # sensory/specific vs abstract (LLM-rated, rubric)
                + 0.25 × audience_exclusivity    # appears in audience data, absent from competitor content
```

| Band | Meaning | Action |
|---|---|---|
| ≥0.75 | Highly distinctive — this is the good stuff | Promote to the hook shortlist |
| 0.50–0.74 | Useful, somewhat common | Body copy |
| 0.25–0.49 | Generic | Store, don't surface |
| <0.25 | Marketing cliché ("game changer", "life hack") | Auto-suppress from packs |

The auto-suppress list is important: without it the system will confidently hand back the exact language it was built to escape.

---

## 6. The language pack (per topic)

The exportable artifact. One markdown file per topic, regenerated weekly.

```markdown
# Language Pack — Notification fatigue
Generated 2026-08-17 · 41 phrases from 63 conversations · 48 distinct authors

## How they describe the problem (verbatim)
- "notification wallpaper" (6 authors) — metaphor
- "swipe it away without reading" (5) — recurring_description
- "app graveyard" (4) — metaphor
- "it just nags me" (4) — complaint

## What they say they want (verbatim)
- "something that doesn't need me to open it" (5)
- "one tap and back to work" (3)
- "gentle, not another alarm" (3)

## Words for competitors (verbatim)
- "bloated" (4) · "another library" (3) · "course-y" (2)

## Emotional register
Dominant: fatigue, resignation, mild self-blame.
Rare: anger, urgency. → Avoid urgency-driven copy; it misreads the room.

## Normalized concepts (ours)
cue_habituation · commitment_aversion · minimal_interaction_preference

## Proposed copy (OURS — review before use)
- "When your reminder becomes wallpaper"
- "Ten seconds. Then back to work."

## Do not use
- "game changer", "transform your life", "unlock" — absent from audience data, cliché band
- any clinical or attention-related claim
- fabricated user quotes: every quote must link to an evidence ID
```

---

## 7. Guardrails

1. **Quote limits** — ≤15 words per verbatim phrase, ≤3 verbatim quotes per exported document, one per source. Language packs list *phrases*, not passages; a phrase list is not a reconstruction of anyone's post.
2. **No identity leakage** — never store or surface phrases containing names, employers, locations, or health/medical disclosures. Rule-based redaction runs before storage; the LLM extractor is instructed to drop them; both are logged.
3. **No fabricated quotes** — the system may not generate a "typical user quote". If Layer 3 copy resembles a quotation it must be rendered without quotation marks and labelled as our phrasing.
4. **Retention** — phrase records survive raw-payload expiry (they are short, derived, and evidence-linked). When the underlying raw item expires, `evidence_expired: true` is set and the URL is retained for verification.
5. **Multi-language** — `language` and `detected_language` are separate fields. Translation adds `translated_interpretation`; `exact_text` is never touched. Reports show the original first, translation second, in that order.
6. **Suppression list** — a user-editable `config/language_suppress.yaml` for phrases they never want surfaced (brand-unsafe, off-tone, competitor trademarks).
