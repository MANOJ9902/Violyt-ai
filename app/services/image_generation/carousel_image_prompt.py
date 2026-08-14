from __future__ import annotations

"""Jiraaf carousel — LOCKED to the India Building Airports PDF design system.

The reference carousel (app/prompts/references/jiraaf_samples/carousel_airport_pdf/
slide_01..06) defines the ONLY approved carousel look:

  slide 1  COVER : logo top-right · large navy headline (left) · orange subhead with
                   the key number · large 3D hero scene lower half · navy rounded
                   teaser banner · small gray legal footer
  slides 2..n-1
           INFO  : centred navy headline · centred gray one-line subhead ·
                   3–4 WIDE rounded soft-blue cards (3D isometric icon LEFT,
                   thin divider, text RIGHT with bold navy keywords) ·
                   optional centred takeaway line · small gray legal footer
  last     CLOSE : large navy question headline (left) · short "share your thoughts"
                   line · right side EMPTY for the real Jiraaf mascot composite ·
                   small gray legal footer

Hard rules enforced here (carousel only):
  - NO source / survey / institution names in baked text
  - Text must fit fully — never mid-word clip; footer band stays empty
  - Logo + SEBI footer + close mascot are composited in post — never baked
  - Every slide belongs to the SAME campaign (consistency rule from the PDF)
"""

import re

from app.prompts.brand_copy_tone import (
    JIRAAF_CAROUSEL_BG,
    JIRAAF_CAROUSEL_BODY,
    JIRAAF_CAROUSEL_CARD,
    JIRAAF_CAROUSEL_MUTED,
    JIRAAF_CAROUSEL_NAVY,
    JIRAAF_CAROUSEL_ORANGE,
)
from app.prompts.brand_visual_palette import is_jiraaf_brand as _is_jiraaf_brand
from app.services.image_generation.ranking_board import sanitize_ranking_text

# Carousel palette — locked from the Airport PDF, NOT the sky-blue static palette.
CAROUSEL_BG = JIRAAF_CAROUSEL_BG          # #EDF7FC very pale blue canvas
CAROUSEL_BG_ALT = JIRAAF_CAROUSEL_BG
CAROUSEL_CARD = JIRAAF_CAROUSEL_CARD      # #DDEFF9 soft blue info cards
CAROUSEL_NAVY = JIRAAF_CAROUSEL_NAVY      # #063B78 headlines / bold keywords
CAROUSEL_ORANGE = JIRAAF_CAROUSEL_ORANGE  # #FFA500 accent only
CAROUSEL_BODY = JIRAAF_CAROUSEL_BODY      # #40484D body text
CAROUSEL_MUTED = JIRAAF_CAROUSEL_MUTED    # #68747D supporting / footer gray
CAROUSEL_WHITE = "#FFFFFF"

_SAFE = re.compile(r"[^\w\s₹%&.,'\"?!():;\-–/×+&]")
_HEADING_NUMBER_PREFIX = re.compile(
    r"^(?:\d{1,2}\s*[\.\)\-–:]\s*|\d{1,2}\s+)",
    re.IGNORECASE,
)
# Strip citation tails that must NEVER appear on carousel images.
_SOURCE_PREFIX = re.compile(
    r"\b(?:source|sources|via|according to|per|cite[ds]?)\s*[:\-–]\s*.+$",
    re.IGNORECASE,
)
_PAREN_CITE = re.compile(
    r"\s*[\(\[]\s*(?:source|sources|via|according to|per)\s*[:\-–]?\s*[^)\]]+[\)\]]\s*",
    re.IGNORECASE,
)
_ORG_CITE = re.compile(
    r"\s*[\(\[]\s*(?:BIS|IMF|RBI|SEBI|OECD|UN|World\s*Bank|Federal\s*Reserve|Fed|"
    r"US\s*Treasury|Treasury|Triennial(?:\s+Survey)?|Survey|Report|DPIIT|MoCA|"
    r"Airport\s*Authority|AAI|Statista|Bloomberg|Reuters)[^)\]]*[\)\]]\s*",
    re.IGNORECASE,
)
_BARE_ORG_TAIL = re.compile(
    r"\s+[–\-—]\s*(?:BIS|IMF|RBI|SEBI|OECD|World\s*Bank|Federal\s*Reserve|"
    r"Triennial\s+Survey|Survey|Report).*$",
    re.IGNORECASE,
)

# Bottom reserve for the Pillow-composited gray legal footer (PDF footer ≈ 10%).
_SEBI_RESERVE = "14%"

# ── Master design system — condensed from the India Building Airports PDF ──
JIRAAF_CAROUSEL_DESIGN_SYSTEM = f"""
JIRAAF CAROUSEL DESIGN SYSTEM (India Building Airports PDF — NON-NEGOTIABLE):
CANVAS: full-bleed very pale blue {CAROUSEL_BG}. 4:5 vertical (1080×1350). Spacious
  editorial composition, generous margins (~6%), never overcrowded, nothing touches edges.
PALETTE (restrained — nothing else):
  navy {CAROUSEL_NAVY} dominates typography · orange {CAROUSEL_ORANGE} accent ONLY ·
  card fill {CAROUSEL_CARD} · body {CAROUSEL_BODY} · supporting gray {CAROUSEL_MUTED} · white.
TYPOGRAPHY: modern geometric sans (Inter/Manrope/Montserrat feel). Sentence case.
  HEADLINE: very large ExtraBold navy, 1–2 lines, tight leading.
  SUBHEAD: ~60% of headline size, regular, charcoal {CAROUSEL_BODY}.
  BODY: short readable sentences — never dense paragraphs.
  KEY NUMBERS + KEY PHRASES: bold navy inside body sentences. Orange text sparingly.
  NEVER serif / decorative / handwritten fonts.
INFO CARDS: WIDE horizontal rounded rectangles, soft {CAROUSEL_CARD} fill, large corner
  radius, no border, very subtle depth, generous inner padding. Inside each card:
  3D isometric icon LEFT (~25% width) → thin vertical divider → text RIGHT (~75% width).
  Cards evenly spaced. Icon visually secondary to text.
ICONS: premium miniature 3D isometric objects on a small base — soft studio light,
  subtle shadow, navy/blue structure + orange accent + small green details.
  Each icon depicts ITS OWN card's point. NEVER flat emoji / clipart / line icons.
SPACING: logo pocket top-right EMPTY · headline in top third · card gap 2–3% ·
  bottom {_SEBI_RESERVE} EMPTY pale-blue for the small gray legal footer composite.
FEEL: trustworthy premium fintech editorial — uncluttered, no gradients, no neon,
  no dark backgrounds, no decorative extras. Every slide = SAME campaign.
"""

CAROUSEL_DENSE_LOCK = """
CAROUSEL CONTENT LOCK:
• Bake the latest / most important facts only — complete words, complete sentences.
• Bold the key number / scheme / phrase in navy inside each card sentence.
• NO source line. NO survey names. Never bake "Source:", "(BIS…)", org cites.
• Never clip mid-word. Never invent statistics not in the COPY block.
"""

CLEAN_LAYOUT_LOCK = f"""
CLEAN EDITORIAL LOCK:
• Calm LinkedIn-native craft. NO connector graphs / path lines / flowchart arrows.
• Leave TOP-RIGHT logo pocket EMPTY. Leave BOTTOM {_SEBI_RESERVE} EMPTY pale-blue.
• ≥4% clear gap between last content and the footer band — cards must NOT touch it.
• BAN: page counters, white logo boxes, navy footer bars, source citations, second background.
"""

CREATIVE_DEPTH_LOCK = """
3D CRAFT (premium, not flat):
• Miniature isometric 3D objects — soft studio light, contact shadows, small base/platform.
• Icons stay visually secondary — text is the hero of every card.
• Every icon depicts its own card's point; never reuse the previous slide's hero.
"""

# Page types from the PDF. All middle slides use the SAME info-page system
# (consistency rule) — only card count / takeaway line varies.
ROLE_LAYOUT_SPECS: dict[str, dict[str, object]] = {
    "cover": {
        "role": "cover",
        "geometry": "cover",
        "composition": (
            "COVER PAGE (PDF slide 1): TOP-RIGHT logo pocket EMPTY. UPPER-LEFT: very large "
            "ExtraBold navy headline, left-aligned, max 2 lines, fully left of the logo pocket. "
            "Directly below: large orange supporting statement carrying the key number. "
            "LOWER ~55%: ONE large premium cinematic 3D hero scene related to the topic "
            "(clean, realistic, blue/white corporate light, orange accents) — it must NOT "
            "overpower the headline. Just above the footer reserve: ONE slim dark-navy rounded "
            "banner with short white bold teaser text + small orange accent icon. "
            "NO info cards on the cover."
        ),
        "max_blocks": 0,
        "max_words_block": 14,
    },
    "info": {
        "role": "info",
        "geometry": "info",
        "composition": (
            "INFORMATION PAGE (PDF slides 2–5): TOP-RIGHT logo pocket EMPTY. "
            "TOP-CENTRE: large ExtraBold navy headline (1–2 lines, centred). "
            "Below: ONE short centred gray explanatory sentence. "
            "MIDDLE: 3–4 WIDE rounded soft-blue cards stacked with even gaps — each card = "
            "miniature 3D isometric icon LEFT (~25% width) → thin vertical divider → concise "
            "text RIGHT with the key number/phrase in bold navy. "
            "Optionally ONE centred navy takeaway sentence below the cards (bold key phrase). "
            "Everything stops ≥4% above the footer reserve."
        ),
        "max_blocks": 4,
        "max_words_block": 20,
    },
    "close": {
        "role": "close",
        "geometry": "close",
        "composition": (
            "CLOSE PAGE (PDF slide 6): TOP-RIGHT logo pocket EMPTY. LEFT ~55%: very large "
            "ExtraBold navy question headline (max 3 short lines), left-aligned. Below it: "
            "one short bold charcoal invite line (e.g. share your thoughts in the comments). "
            "RIGHT ~45% of the canvas stays EMPTY pale-blue — the real Jiraaf giraffe mascot "
            "(yellow sweater, glasses) is composited there in post. NEVER draw a giraffe, "
            "mascot, animal character, or fake Jiraaf figure. NO info cards. NO hero scene."
        ),
        "max_blocks": 0,
        "max_words_block": 12,
    },
}


def strip_carousel_source_citations(text: str) -> str:
    """Remove source / survey / institution citations from carousel bake strings."""
    t = str(text or "")
    if not t.strip():
        return ""
    t = _PAREN_CITE.sub(" ", t)
    t = _ORG_CITE.sub(" ", t)
    t = _BARE_ORG_TAIL.sub("", t)
    t = _SOURCE_PREFIX.sub("", t)
    # Drop trailing "Source …" fragments without punctuation
    t = re.sub(r"\bSource\b.*$", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" ,;:-–")
    return t


def _scrub(text: str, *, max_words: int = 24) -> str:
    t = sanitize_ranking_text(str(text or ""))
    t = strip_carousel_source_citations(t)
    t = _SAFE.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    if len(words) > max_words:
        words = words[:max_words]
    # Never end on a dangling connector
    dangling = {
        "a", "an", "the", "and", "or", "but", "with", "for", "to", "of", "in", "on",
        "at", "by", "from", "as", "is", "are", "than", "that", "which",
    }
    while words and words[-1].strip(".,;:").casefold() in dangling:
        words.pop()
    return " ".join(words).strip(" ,;:-–")


def strip_carousel_heading_numbers(text: str) -> str:
    """Remove list/slide number prefixes from headlines — user forbids numbers in headings."""
    t = _scrub(text, max_words=12)
    t = _HEADING_NUMBER_PREFIX.sub("", t).strip()
    t = re.sub(r"^slide\s+\d+\s*[-:]\s*", "", t, flags=re.IGNORECASE).strip()
    return t if t else "KEY INSIGHT"


def _fit_headline(text: str, *, max_chars: int = 34, max_lines: int = 2) -> str:
    """Keep headline short enough to sit clear of the logo pocket without mid-word clip.

    Hard cap at 6 words — Airport PDF headlines are 4–7 words and always fit fully.
    The image model is told to scale the font DOWN to fit, not clip.
    """
    t = strip_carousel_heading_numbers(text)
    words = t.split()
    if not words:
        return "KEY INSIGHT"
    # Hard cap at 6 words — anything longer risks overflow at the ExtraBold weight.
    if len(words) > 6:
        words = words[:6]
    # Also remove dangling connectors at the end
    dangling = {"a", "an", "the", "and", "or", "with", "for", "to", "of", "in", "on", "is"}
    while words and words[-1].strip(".,;:").casefold() in dangling:
        words.pop()
    return " ".join(words) if words else "KEY INSIGHT"


def _slide_spec(slide_number: int, role: str, *, is_last: bool = False) -> dict[str, object]:
    """Map every slide onto the PDF page system: cover / info / close."""
    n = max(1, min(int(slide_number or 1), 12))
    if is_last:
        return dict(ROLE_LAYOUT_SPECS["close"])
    if n == 1 or (role or "").strip().lower() == "cover":
        return dict(ROLE_LAYOUT_SPECS["cover"])
    spec = dict(ROLE_LAYOUT_SPECS["info"])
    key = (role or "").strip().lower()
    if key:
        spec["role"] = key
    return spec


def _render_blocks(blocks: list[str], spec: dict[str, object]) -> str:
    """Map fact lines into the PDF info-card system."""
    geometry = str(spec.get("geometry") or "info").lower()
    max_blocks = int(spec.get("max_blocks") or 4)
    items = [b for b in blocks if b][:max_blocks]

    if geometry == "cover":
        return "NO INFO CARDS on the cover — headline + orange subhead + hero + teaser banner only.\n"
    if geometry == "close" or not items:
        if geometry == "close":
            return "NO INFO CARDS on the close — headline + invite line; right side empty for mascot.\n"
        return "NO INFO CARDS available — headline + subhead + one takeaway sentence only.\n"

    n = len(items)
    return (
        f"INFO CARDS (exactly {n} wide rounded soft-blue cards, stacked with even gaps):\n"
        + "\n".join(
            f'  CARD {i}: [3D isometric icon depicting this point] | divider | '
            f'"{b}" (bold the key number/phrase in navy)'
            for i, b in enumerate(items, start=1)
        )
        + f"\nAll {n} cards identical shape/fill/radius. Icon LEFT ~25%, text RIGHT ~75%.\n"
        "Do NOT add extra cards. Do NOT place cards inside the bottom footer reserve.\n"
    )


def build_carousel_slide_image_prompt(
    *,
    slide_number: int,
    total_slides: int,
    role: str,
    headline: str,
    supporting: str = "",
    body: str = "",
    story_blocks: list[str] | None = None,
    cta: str = "",
    canvas_desc: str = "1080x1350",
    topic: str = "",
    is_last: bool = False,
    prior_headlines: list[str] | None = None,
    palette: dict[str, str] | None = None,
) -> str:
    """Jiraaf carousel slide — Airport PDF design system is authoritative.

    NOTE: the ``palette`` argument is intentionally ignored for Jiraaf carousels.
    The PDF design system colours are locked; Brand Space sky-blue (#87CEFA)
    must never leak into carousel slides.
    """
    spec = _slide_spec(slide_number, role, is_last=is_last)
    geometry = str(spec.get("geometry") or "info").lower()
    max_words = int(spec.get("max_words_block") or 18)

    hl = _fit_headline(headline)
    sup = _scrub(supporting, max_words=16)
    # Close slide: mascot occupies the right half — only headline + invite line.
    # Body and supporting would be clipped by the mascot composite; strip them.
    body_txt = ""
    if geometry == "cover":
        body_txt = _scrub(body, max_words=20)
    if geometry == "close":
        sup = ""  # supporting is clipped by mascot — omit
    raw_blocks = [
        _scrub(b, max_words=max_words)
        for b in (story_blocks or [])
        if str(b).strip()
    ]
    blocks = [b for b in raw_blocks if b]
    cta_label = _scrub(cta, max_words=8) if (is_last and cta) else ""
    topic_clean = _scrub(topic, max_words=12)
    priors = [_fit_headline(p) for p in (prior_headlines or []) if str(p).strip()][:9]
    prior_line = "; ".join(f'"{p}"' for p in priors) if priors else "(first slide)"

    cards = _render_blocks(blocks, spec)

    # Cover teaser banner text — prefer supporting/CTA, else default from the PDF.
    teaser = ""
    if geometry == "cover":
        teaser = _scrub(cta or "Here's what you need to know", max_words=9) or (
            "Here's what you need to know"
        )

    return (
        "=== JIRAAF CAROUSEL — INDIA BUILDING AIRPORTS PDF DESIGN SYSTEM ===\n"
        "Premium fintech editorial carousel. Every slide belongs to the same campaign.\n"
        f"Canvas {canvas_desc} (4:5 vertical). Slide {slide_number}/{total_slides}. "
        f"Page type: {geometry.upper()} (role: {spec['role']}).\n"
        f"{JIRAAF_CAROUSEL_DESIGN_SYSTEM}\n"
        f"{CAROUSEL_DENSE_LOCK}\n"
        f"{CLEAN_LAYOUT_LOCK}\n"
        f"{CREATIVE_DEPTH_LOCK}\n"
        "════════════════════════════════════\n"
        "ABSOLUTE BANS\n"
        "════════════════════════════════════\n"
        "• NO connector graphs, path lines, dotted trails, flowchart arrows.\n"
        "• NO numbers in headline — never '1.', '2.', '01', step counters.\n"
        "• NO page numbers / '1 of N' / slide badges.\n"
        "• NO logo / brand wordmark baked — top-right EMPTY (Brand Space PNG composite).\n"
        "• NO dark footer bar, NO separate footer band — footer text is composited in post.\n"
        "• NO source names, survey names, 'Source:' labels, or institution cites — EVER.\n"
        f"• Bottom {_SEBI_RESERVE} EMPTY pale-blue {CAROUSEL_BG} for the gray legal footer.\n"
        "• Content STOPS ≥4% above that band — never overlap the footer reserve.\n"
        "• Complete words only — NEVER clip mid-word (Marke→Market is a FAIL).\n"
        "• FONT SIZE: scale the headline font DOWN until ALL words fit fully — never clip, never '...'.\n"
        "  INFO pages: headline is centred but uses a MEDIUM-LARGE Bold (not ExtraBold) so it fits\n"
        "  within the centre 80% of the canvas, clear of the top-right logo pocket.\n"
        "  COVER pages: headline is LEFT-aligned ExtraBold in the left 60% of the canvas.\n"
        "• Props from THIS slide's copy only.\n"
        "• CLOSE SLIDE: never draw giraffe/mascot/animal character — composited in post.\n\n"
        f"COMPOSITION: {spec['composition']}\n"
        f"{cards}\n"
        f'HEADLINE (ExtraBold navy {CAROUSEL_NAVY}): "{hl}"\n'
        f"FORBIDDEN prior headlines: {prior_line}\n\n"
        "COPY TO BAKE (already scrubbed — no sources):\n"
        + (f'TOPIC: "{topic_clean}"\n' if topic_clean else "")
        + f'HEADLINE: "{hl}"\n'
        + (f'SUBHEAD: "{sup}"\n' if sup and geometry != "close" else "")
        + (f'BODY: "{body_txt}"\n' if body_txt else "")
        + (f'TEASER BANNER (navy pill, white text): "{teaser}"\n' if teaser else "")
        + (f'CTA / INVITE LINE: "{cta_label}"\n' if cta_label else "")
        + "=== END ===\n"
    )


def build_carousel_style_stub() -> str:
    return (
        f"CAROUSEL (Airport PDF system): pale-blue BG {CAROUSEL_BG}; navy {CAROUSEL_NAVY} "
        f"headlines; orange {CAROUSEL_ORANGE} accent only; wide rounded {CAROUSEL_CARD} info "
        "cards (3D isometric icon left, divider, text right); NO source names; NO numbers in "
        f"headline; bottom {_SEBI_RESERVE} empty for gray legal footer; empty logo pocket."
    )


def build_brand_carousel_slide_image_prompt(
    *,
    slide_number: int,
    total_slides: int,
    role: str,
    headline: str,
    supporting: str = "",
    body: str = "",
    story_blocks: list[str] | None = None,
    cta: str = "",
    canvas_desc: str = "1080x1350",
    topic: str = "",
    is_last: bool = False,
    prior_headlines: list[str] | None = None,
    brand_name: str = "",
    color_behavior: str = "",
    primary_color: str = "",
    secondary_color: str = "",
    accent_color: str = "",
) -> str:
    """Brand-specific carousel — Brand Space colours ONLY. Same page system as Jiraaf."""
    if _is_jiraaf_brand(brand_name):
        return build_carousel_slide_image_prompt(
            slide_number=slide_number,
            total_slides=total_slides,
            role=role,
            headline=headline,
            supporting=supporting,
            body=body,
            story_blocks=story_blocks,
            cta=cta,
            canvas_desc=canvas_desc,
            topic=topic,
            is_last=is_last,
            prior_headlines=prior_headlines,
        )

    from app.prompts.cognixia_brand_dna import cognixia_carousel_palette_line, is_cognixia_brand

    spec = _slide_spec(slide_number, role, is_last=is_last)
    geometry = str(spec.get("geometry") or "info").lower()
    max_words = int(spec.get("max_words_block") or 18)

    hl = _fit_headline(headline)
    sup = _scrub(supporting, max_words=16)
    body_txt = _scrub(body, max_words=20) if geometry in ("cover", "close") else ""
    blocks = [
        _scrub(b, max_words=max_words)
        for b in (story_blocks or [])
        if str(b).strip()
    ]
    blocks = [b for b in blocks if b]
    cta_label = _scrub(cta, max_words=8) if (is_last and cta) else ""
    topic_clean = _scrub(topic, max_words=12)
    priors = [_fit_headline(p) for p in (prior_headlines or []) if str(p).strip()][:9]
    prior_line = "; ".join(f'"{p}"' for p in priors) if priors else "(first slide)"

    if is_cognixia_brand(brand_name):
        palette = cognixia_carousel_palette_line(
            primary_color=primary_color,
            secondary_color=secondary_color,
        )
        bg_note = "Background from Cognixia Brand Space palette only."
        typography_note = "Typography: Outfit sans — bold headlines, gray body."
    else:
        primary = (primary_color or "").strip() or "#1F2937"
        secondary = (secondary_color or "").strip() or "#4B5563"
        accent = (accent_color or "").strip() or secondary
        palette = (
            color_behavior
            or f"primary {primary}, secondary {secondary}, accent {accent}"
        )
        bg_note = (
            "Background: soft tint from this brand's Brand Space colours, or clean white. "
            "NEVER Jiraaf pale-blue #EDF7FC / sky-blue #87CEFA, NEVER Jiraaf navy, "
            "NEVER Jiraaf orange #FFA500."
        )
        typography_note = (
            f"Typography: clean modern sans. Headlines in brand primary {primary}. "
            "Complete sentences. Perfect spelling."
        )

    cards = _render_blocks(blocks, spec)

    return (
        "=== BRAND CAROUSEL SLIDE — EDITORIAL INFO-CARD SYSTEM (NOT JIRAAF COLOURS) ===\n"
        f"Brand: {brand_name or 'this brand'}. Use ONLY this brand's Brand Space colours.\n"
        f"Canvas {canvas_desc}. Beat {slide_number}/{total_slides}. "
        f"Page type: {geometry.upper()} (role: {spec['role']}).\n\n"
        f"{CAROUSEL_DENSE_LOCK}\n"
        f"BRAND COLOURS: {palette}\n"
        f"{bg_note}\n"
        f"{typography_note}\n\n"
        f"COMPOSITION: {spec['composition']}\n"
        "RECOLOUR RULE: keep the page structure above but replace every Jiraaf colour "
        "(pale-blue canvas, soft-blue cards, navy, orange) with THIS brand's palette — "
        "canvas = soft brand tint or white, cards = light brand tint, headlines = brand primary.\n"
        f"{cards}\n"
        "BANS: NO source/survey names, NO numbers in headline, NO page badges, "
        "NO logo baked, NO connector graphs, NO mid-word clipping.\n"
        f"Leave bottom {_SEBI_RESERVE} empty. Headline clear of the logo pocket (max 2 lines).\n\n"
        f'HEADLINE: "{hl}"\n'
        f"FORBIDDEN priors: {prior_line}\n"
        + (f'SUBHEAD: "{sup}"\n' if sup else "")
        + (f'BODY: "{body_txt}"\n' if body_txt else "")
        + (f'CTA: "{cta_label}"\n' if cta_label else "")
        + (f'TOPIC: "{topic_clean}"\n' if topic_clean else "")
        + "=== END ===\n"
    )
