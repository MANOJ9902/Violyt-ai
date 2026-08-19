from __future__ import annotations

"""Carousel story structure (hook → teach → choice → CTA). Colors come from Brand Space."""

from app.prompts.brand_copy_tone import (
    CAROUSEL_AUDIENCE_TONE_LOCK,
    CAROUSEL_CONTENT_DEPTH_LOCK,
    HEADLINE_COLOR_LOCK,
)

CAROUSEL_SAMPLE_DNA = f"""
════════════════════════════════════════════════════════
CAROUSEL STORY DNA
════════════════════════════════════════════════════════

{CAROUSEL_AUDIENCE_TONE_LOCK}

VISUAL SYSTEM (every slide — Brand Space palette):
- Canvas 1080x1350 portrait (4:5)
- Background: Brand Space background full-bleed
- Headlines / subheads: Brand Space primary ONLY — never the accent colour
- Brand Space accent: key numbers, CTA fill ONLY
- INFO CARDS: wide rounded Brand Space card fill — miniature 3D
  isometric icon LEFT (~25% width), thin divider, concise text RIGHT with bold keywords.
  NOT blurry toy blobs. NOT empty slides. NOT giant full-width heroes.
- Bottom ~14% reserved EMPTY only if Brand Space has a legal footer
- EVERY slide MUST have a full headline at top-left — NEVER omit, NEVER truncate mid-word
- Everything fully inside frame — never clip chips/text/icons

STORY ARC (5–6 slides):
1 HOOK — surprising concrete tension with a real fact/number
2 SCENARIO / DEFINE — plain mechanism + concrete example in 3 short text blocks
3 HOW IT WORKS — simple comparison OR numbered steps OR clear mechanism
4 IMPLICATION / CHOICE — what the reader might do + one honest condition
5 NUANCE / PROS-CONS — honest trade-offs WITH full reason sentences (never empty Pros/Cons)
6 CTA — short question inviting comment

PER-SLIDE VISUAL RECIPE:
HOOK: big question headline (full words) + 1 support line + 1–2 insight cards + premium icon
SCENARIO: short headline + THREE stacked story blocks with real amounts
HOW IT WORKS: headline + mechanism line + comparison/table OR 2–3 fact cards with numbers
CHOICE: question headline + 2–3 explained cards + caveat note
PROS/CONS: headline + TWO columns/cards each with FULL reason sentences (not empty labels)
CTA: big question + invite to comment + premium icon
   Optional accent CTA button: COMPACT only (≤28% width, ≤4.5% height) — never a wide bar

DEPTH RULES:
{CAROUSEL_CONTENT_DEPTH_LOCK}
- Put REAL numbers from research on 2+ slides — explain them simply.
- Prefer a mini scenario over a slogan.
- Prefer a comparison or choice (A vs B, hold vs exit, pros vs cons WITH short reasons).
- Include ONE honest caveat/note somewhere.
- supporting_line on every slide must add a plain fact — not restate the headline.

FORBIDDEN (instant fail):
- Truncated headlines (mid-word cuts / "…")
- Missing headline on any slide
- Sparse slides with only 1–2 short lines and huge empty space
- Empty Pros/Cons/Examples chips with no explanation
- Topic title alone as headline
- Cloning the same body across slides
- Cheap blurry calculator / toy icons
- Technical jargon without a plain-English translation

PER-SLIDE COPY SHAPE:
- headline: max 8–10 words, COMPLETE (no truncation), unique, concrete
- supporting_line: 1 short plain sentence with a fact or "what it means" (REQUIRED)
- body: 18–32 words — full scenario / comparison / caveat in simple words
- proof_points: 2–3 SHORT explanation lines (6–12 words each)
- chip_labels: exactly 3 ONE-WORD content labels matching THIS slide's beat

COLOUR LOCK:
{HEADLINE_COLOR_LOCK}
"""

CAROUSEL_SAMPLE_DNA_COMPACT = """
CAROUSEL ONLY:
TONE: plain retail voice — short sentences, real facts, NO jargon.
STORY: hook → scenario (3 blocks) → how it works → choice → pros/cons WITH short reasons → CTA.
EVERY slide: FULL headline top-left (never omit, never truncate mid-word).
CONTENT DENSE: 3–4 info cards (3D icon left, divider, text right).
Legal footer band only if Brand Space supplied one. COLOUR: Brand Space palette only.
"""
