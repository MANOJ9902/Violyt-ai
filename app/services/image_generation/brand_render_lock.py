"""Single mandatory render contract shared by EVERY image format and brand.

Carousel, static, infographic, ranking and hub prompts each carry their own layout
DNA, but the three rules below must hold identically for every brand and platform:

1. Colours come only from that brand's Brand Space palette.
2. The only brand mark is the Brand Space logo asset composited in post.
3. Nothing is cut off, and no line of information is repeated.

Prompt builders drift over time, so this lock is appended centrally at the single
image call site instead of being duplicated in each builder.
"""

from __future__ import annotations

from typing import Any

from app.utils.palette_roles import normalize_hex

# Kept short on purpose: it is prepended ahead of layout DNA and must survive the
# gpt-image-1 prompt budget even on the densest slide.
_PLATFORM_MARKS = "LinkedIn, Instagram, X/Twitter, Facebook, YouTube, WhatsApp"


def _hex_or(value: Any, fallback: str) -> str:
    return normalize_hex(str(value or "")) or fallback


def build_mandatory_render_lock(
    *,
    background: str = "",
    primary: str = "",
    secondary: str = "",
    accent: str = "",
    body: str = "",
    card: str = "",
    muted: str = "",
    brand_name: str = "",
    font: str = "",
    allow_section_bands: bool = False,
) -> str:
    """Universal per-brand contract appended to every generated image prompt.

    ``allow_section_bands`` opens the door for the banded infographic template, where
    inset solid primary strips act as section headers. The page background itself
    stays single and light either way.
    """
    bg = _hex_or(background, "#FFFFFF")
    pri = _hex_or(primary, "#1F2937")
    sec = _hex_or(secondary, pri)
    acc = _hex_or(accent, pri)
    bod = _hex_or(body, "#374151")
    crd = _hex_or(card, sec)
    mut = _hex_or(muted, bod)
    label = (brand_name or "this brand").strip() or "this brand"
    font_line = f" TYPEFACE: {font}." if font else ""

    if allow_section_bands:
        bg_rule = (
            f"COLOURS (Brand Space only; paint nothing else): PAGE BG {bg} full-bleed behind "
            f"every zone — no second page colour, no white page, no page frame. "
            f"HEADLINES {pri} = text, and the ONLY fill allowed for INSET rounded section/footer "
            f"BANDS (text on a band is WHITE); a band never bleeds to the canvas edges and never "
            f"becomes the page. CARDS {crd} (secondary {sec}). "
            f"ACCENT {acc} = pill/CTA/key figure/rule only. BODY {bod}. MUTED {mut}.{font_line} "
            "No invented tints, teal, mint, gold or neon.\n"
        )
        one_bg_rule = (
            f"ONE full-bleed {bg} page background only — inset bands and rounded cards sit ON "
            "it, but never a nested white/pale panel imitating a second page. "
        )
    else:
        bg_rule = (
            f"COLOURS (Brand Space only; paint nothing else): PAGE BG {bg} full-bleed on every "
            f"slide/format — no second page colour, no dark/navy header band, no white page. "
            f"HEADLINES {pri} = TEXT ONLY, never a page or banner fill. CARDS {crd} (secondary {sec}). "
            f"ACCENT {acc} = CTA/key figure/rule only. BODY {bod}. MUTED {mut}.{font_line} "
            "No invented tints, teal, mint, gold or neon.\n"
        )
        one_bg_rule = (
            "ONE full-bleed page background only — never a nested white/pale panel or second BG. "
        )

    return (
        f"=== BRAND RENDER CONTRACT ({label}) — OVERRIDES ALL OTHER STYLING ===\n"
        f"{bg_rule}"
        "BRAND MARKS: top-right pocket (~24%x12%) stays EMPTY page background — the real Brand "
        "Space logo is composited in post. Draw NO logo, wordmark, brand-name text, signature, "
        f"badge, white plate, or placeholder, and NO platform logos ({_PLATFORM_MARKS}).\n"
        "COMPLETENESS: bake every quoted string in full — never clip mid-word, never break a "
        "word across lines (never 'c' then 'an'), never end mid-phrase, never use '...'. "
        "If it does not fit, shrink the font or use fewer cards. "
        "Keep >=6% margin on all four sides; nothing may touch or be cropped by any edge. "
        f"{one_bg_rule}"
        "Do NOT bake a CTA button — leave the bottom empty (CTA is composited in post). "
        "Every card states a DIFFERENT fact; never repeat a sentence across cards and never "
        "repeat a card title as its own body.\n"
        "=== END CONTRACT ===\n"
    )


def build_lock_from_pack(pack: Any, *, fmt: str = "") -> str:
    """Convenience wrapper for a BrandVisualPack (or its dict form)."""
    get = (
        (lambda k: pack.get(k, ""))
        if isinstance(pack, dict)
        else (lambda k: getattr(pack, k, ""))
    )
    return build_mandatory_render_lock(
        background=get("background"),
        primary=get("primary"),
        secondary=get("secondary"),
        accent=get("accent"),
        body=get("body"),
        card=get("card"),
        muted=get("muted"),
        brand_name=get("brand_name"),
        font=get("font_primary"),
        # Only the banded infographic template uses inset solid section strips.
        allow_section_bands=str(fmt or "").strip().casefold() == "infographic",
    )
