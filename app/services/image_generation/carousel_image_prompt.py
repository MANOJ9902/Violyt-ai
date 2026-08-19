from __future__ import annotations

"""Carousel image prompts — layout only; Brand Space owns colours/logo/legal.

Cover / info / close slide structure is format DNA. Palette, mascot, legal footer,
and logo always come from BrandVisualPack for the active brand_id.
"""

import re

from app.services.image_generation.ranking_board import sanitize_ranking_text

# Neutral defaults — real hexes always come from BrandVisualPack.palette_map().
CAROUSEL_BG = "#FFFFFF"
CAROUSEL_BG_ALT = "#FFFFFF"
CAROUSEL_CARD = "#F3F4F6"
CAROUSEL_NAVY = "#1F2937"
CAROUSEL_ORANGE = "#4B5563"
CAROUSEL_BODY = "#374151"
CAROUSEL_MUTED = "#6B7280"
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
_LEGAL_FOOTER_RESERVE = "14%"

def _palette(p: dict[str, str] | None) -> dict[str, str]:
    p = p or {}
    bg = (p.get("background") or CAROUSEL_BG).strip() or CAROUSEL_BG
    headline = (p.get("headline") or p.get("primary") or CAROUSEL_NAVY).strip()
    secondary = (p.get("secondary") or "").strip()
    accent = (p.get("accent") or secondary or headline).strip()
    card = (p.get("card") or secondary or CAROUSEL_CARD).strip()
    body = (p.get("body") or CAROUSEL_BODY).strip()
    muted = (p.get("muted") or CAROUSEL_MUTED).strip()
    font = (p.get("font") or "clean modern geometric sans").strip()
    return {
        "bg": bg,
        "headline": headline,
        "secondary": secondary or card,
        "accent": accent,
        "card": card,
        "body": body,
        "muted": muted,
        "font": font,
    }


def _design_system(p: dict[str, str], *, has_legal: bool, has_mascot: bool) -> str:
    footer = (
        f"bottom {_LEGAL_FOOTER_RESERVE} EMPTY {p['bg']} for the composited legal footer."
        if has_legal
        else "no legal footer band — do not invent disclaimer text."
    )
    mascot = (
        "CLOSE page: leave lower-right empty for a composited brand mascot."
        if has_mascot
        else "CLOSE page: no mascot unless Brand Space supplied one."
    )
    return f"""
CAROUSEL DESIGN SYSTEM (Brand Space palette — same structure every slide):
CANVAS: full-bleed {p['bg']}. 4:5 vertical (1080×1350). Spacious editorial, ~6% margins.
PALETTE (restrained — nothing else):
  headline {p['headline']} · secondary/cards {p['secondary']} · accent {p['accent']} only ·
  body {p['body']} · muted {p['muted']}.
TYPOGRAPHY: {p['font']}. Sentence case. ExtraBold headline 1–2 lines. Never serif/handwritten.
INFO CARDS: wide rounded rectangles, fill {p['card']}, icon LEFT ~25%, text RIGHT ~75%.
ICONS: premium miniature 3D isometric objects matching THIS slide's point — not another brand's icons.
SPACING: logo pocket top-right EMPTY · {footer}
{mascot}
Every slide = SAME campaign. Uncluttered. No neon. No second background.
"""

CAROUSEL_DENSE_LOCK = """
CAROUSEL CONTENT LOCK:
• Bake the latest / most important facts only — complete words, complete sentences.
• Bold the key number / scheme / phrase in Brand Space primary inside each card sentence.
• NO source line. NO survey names. Never bake "Source:", "(BIS…)", org cites.
• Never clip mid-word. Never invent statistics not in the COPY block.
"""

CLEAN_LAYOUT_LOCK = f"""
CLEAN EDITORIAL LOCK:
• Calm LinkedIn-native craft. NO connector graphs / path lines / flowchart arrows.
• Leave TOP-RIGHT logo pocket EMPTY. Leave BOTTOM {_LEGAL_FOOTER_RESERVE} EMPTY pale-blue.
• ≥4% clear gap between last content and the footer band — cards must NOT touch it.
• BAN: page counters, white logo boxes, dark invented footer bars, source citations, second background.
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
            "ExtraBold headline in Brand Space primary, left-aligned, max 2 lines, fully left of the logo pocket. "
            "Directly below: large Brand Space accent supporting statement carrying the key number. "
            "LOWER ~55%: ONE large premium cinematic 3D hero scene related to the topic "
            "(clean, realistic, Brand Space lighting, Brand Space accent) — it must NOT "
            "overpower the headline. Just above the footer reserve: ONE slim Brand Space primary rounded "
            "banner with short white bold teaser text + small Brand Space accent icon. "
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
            "TOP-CENTRE: large ExtraBold headline in Brand Space primary (1–2 lines, centred). "
            "Below: ONE short centred gray explanatory sentence. "
            "MIDDLE: 3–4 WIDE rounded Brand Space card fills stacked with even gaps — each card = "
            "miniature 3D isometric icon LEFT (~25% width) → thin vertical divider → concise "
            "text RIGHT with the key number/phrase in bold Brand Space primary. "
            "Optionally ONE centred Brand Space primary takeaway sentence below the cards (bold key phrase). "
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
            "ExtraBold question headline in Brand Space primary (max 3 short lines), left-aligned. Below it: "
            "one short bold charcoal invite line (e.g. share your thoughts in the comments). "
            "RIGHT ~45% of the canvas stays EMPTY for a composited Brand Space mascot "
            "when one exists. NEVER draw a mascot, animal character, or fake brand figure. "
            "NO info cards. NO hero scene."
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

    Hard cap at 6 words — headlines stay short so they fit fully.
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
        return "NO INFO CARDS on the cover — headline + accent subhead + hero + teaser banner only.\n"
    if geometry == "close" or not items:
        if geometry == "close":
            return "NO INFO CARDS on the close — headline + invite line; right side empty for mascot.\n"
        return "NO INFO CARDS available — headline + subhead + one takeaway sentence only.\n"

    n = len(items)
    return (
        f"INFO CARDS (exactly {n} wide rounded soft-blue cards, stacked with even gaps):\n"
        + "\n".join(
            f'  CARD {i}: [3D isometric icon depicting this point] | divider | '
            f'"{b}" (bold the key number/phrase in Brand Space primary)'
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
    has_legal: bool = False,
    has_mascot: bool = False,
    brand_name: str = "",
) -> str:
    """Carousel slide using Brand Space palette. Page geometry is format-level."""
    pal = _palette(palette)
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
    if geometry == "close" and has_mascot:
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

    footer_rule = (
        f"• Bottom {_LEGAL_FOOTER_RESERVE} EMPTY {pal['bg']} for the composited legal footer.\n"
        "• Content STOPS ≥4% above that band — never overlap the footer reserve.\n"
        if has_legal
        else "• Do not invent a legal/disclaimer footer.\n"
    )
    mascot_rule = (
        "• CLOSE SLIDE: never draw a mascot/character — composited in post.\n"
        if has_mascot
        else ""
    )
    return (
        f"=== BRAND CAROUSEL — {brand_name or 'Brand Space'} ===\n"
        "Premium editorial carousel. Every slide belongs to the same campaign.\n"
        f"Canvas {canvas_desc} (4:5 vertical). Slide {slide_number}/{total_slides}. "
        f"Page type: {geometry.upper()} (role: {spec['role']}).\n"
        f"{_design_system(pal, has_legal=has_legal, has_mascot=has_mascot)}\n"
        f"{CAROUSEL_DENSE_LOCK}\n"
        "════════════════════════════════════\n"
        "ABSOLUTE BANS\n"
        "════════════════════════════════════\n"
        "• NO connector graphs, path lines, dotted trails, flowchart arrows.\n"
        "• NO numbers in headline — never '1.', '2.', '01', step counters.\n"
        "• NO page numbers / '1 of N' / slide badges.\n"
        "• NO logo / brand wordmark baked — top-right EMPTY (Brand Space PNG composite).\n"
        "• NO source names, survey names, 'Source:' labels, or institution cites — EVER.\n"
        f"{footer_rule}"
        "• Complete words only — NEVER clip mid-word.\n"
        "• FONT SIZE: scale the headline font DOWN until ALL words fit fully — never clip, never '...'.\n"
        "  INFO pages: headline is centred, Bold, within the centre 80%, clear of the logo pocket.\n"
        "  COVER pages: headline is LEFT-aligned ExtraBold in the left 60% of the canvas.\n"
        "• Props from THIS slide's copy only.\n"
        f"{mascot_rule}\n"
        f"COMPOSITION: {spec['composition']}\n"
        f"{cards}\n"
        f'HEADLINE (ExtraBold {pal["headline"]}): "{hl}"\n'
        f"FORBIDDEN prior headlines: {prior_line}\n\n"
        "COPY TO BAKE (already scrubbed — no sources):\n"
        + (f'TOPIC: "{topic_clean}"\n' if topic_clean else "")
        + f'HEADLINE: "{hl}"\n'
        + (f'SUBHEAD: "{sup}"\n' if sup and geometry != "close" else "")
        + (f'BODY: "{body_txt}"\n' if body_txt else "")
        + (f'TEASER BANNER (primary pill, white text): "{teaser}"\n' if teaser else "")
        + (f'CTA / INVITE LINE: "{cta_label}"\n' if cta_label else "")
        + "=== END ===\n"
    )


def build_carousel_style_stub(palette: dict[str, str] | None = None) -> str:
    pal = _palette(palette)
    return (
        f"CAROUSEL: BG {pal['bg']}; headlines {pal['headline']}; accent {pal['accent']}; "
        f"cards {pal['card']} (3D isometric icon left, divider, text right); "
        "NO source names; NO numbers in headline; empty logo pocket."
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
    palette: dict[str, str] | None = None,
    has_legal: bool = False,
    has_mascot: bool = False,
) -> str:
    """Same carousel builder — Brand Space palette only."""
    merged = dict(palette or {})
    if primary_color and not merged.get("primary"):
        merged["primary"] = primary_color
        merged.setdefault("headline", primary_color)
    if secondary_color and not merged.get("secondary"):
        merged["secondary"] = secondary_color
        merged.setdefault("accent", secondary_color or accent_color)
    if accent_color and not merged.get("accent"):
        merged["accent"] = accent_color
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
        palette=merged,
        has_legal=has_legal,
        has_mascot=has_mascot,
        brand_name=brand_name,
    )
