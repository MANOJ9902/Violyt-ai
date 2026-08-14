from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.prompts.brand_copy_tone import JIRAAF_BG, JIRAAF_NAVY, JIRAAF_ORANGE
from app.prompts.cognixia_brand_dna import (
    cognixia_color_behavior,
    cognixia_default_palette,
    is_cognixia_brand,
)

JIRAAF_FORBIDDEN = (
    "FORBIDDEN for this brand: Jiraaf navy #003975, orange #FFA400, sky-blue #87CEFA."
)


_JIRAAF_CANON = "jiraaf"
_JIRAAF_LETTERS = frozenset(_JIRAAF_CANON)


def is_jiraaf_brand(brand_name: str | None) -> bool:
    """Match the Jiraaf brand tolerantly.

    Brand Space names are typed by hand and real data contains "Jirraf" and
    "Jiraff". An exact substring test silently routed those spaces to the
    generic (teal/white) template system instead of the Jiraaf one.
    """
    for token in re.split(r"[^a-z]+", (brand_name or "").casefold()):
        if _JIRAAF_CANON in token:
            return True
        # Only near-misses built from Jiraaf's own letters; "jira" stays unmatched.
        if (
            token.startswith("ji")
            and 5 <= len(token) <= 8
            and set(token) <= _JIRAAF_LETTERS
            and SequenceMatcher(None, token, _JIRAAF_CANON).ratio() >= 0.72
        ):
            return True
    return False


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    text = (value or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    if len(text) != 6:
        return None
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError:
        return None


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two hex colours (0.0 when unparseable)."""
    fg_rgb, bg_rgb = _hex_to_rgb(fg), _hex_to_rgb(bg)
    if not fg_rgb or not bg_rgb:
        return 0.0
    l1, l2 = _relative_luminance(fg_rgb), _relative_luminance(bg_rgb)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _color_distance(a: str, b: str) -> float:
    """Euclidean RGB distance (0.0 when either colour is unparseable)."""
    a_rgb, b_rgb = _hex_to_rgb(a), _hex_to_rgb(b)
    if not a_rgb or not b_rgb:
        return 0.0
    return sum((x - y) ** 2 for x, y in zip(a_rgb, b_rgb)) ** 0.5


def resolve_jiraaf_palette(
    *,
    primary: str = "",
    secondary: str = "",
    background: str = JIRAAF_BG,
) -> dict[str, str]:
    """Brand Space colours for Jiraaf, falling back to the locked palette.

    Brand Spaces are user-edited and some hold unusable values, so a stored
    colour is only accepted when it is a valid hex with enough contrast against
    the locked canvas to actually be legible.
    """
    # Headlines sit directly on the canvas, so they must clear a readability bar.
    headline = primary if contrast_ratio(primary, background) >= 4.5 else JIRAAF_NAVY
    # Accents are fills and numerals, often on white cards. A bright accent on a
    # light canvas is low-contrast by design (the locked orange scores ~1.2), so
    # they are only rejected when unparseable or too close to the canvas to read.
    accent = secondary if _color_distance(secondary, background) >= 60 else JIRAAF_ORANGE
    return {
        "background": background,
        "headline": headline,
        "accent": accent,
        "headline_source": "brand_space" if headline == primary else "locked_default",
        "accent_source": "brand_space" if accent == secondary else "locked_default",
    }


def jiraaf_palette_override_block(palette: dict[str, str]) -> str:
    """Authoritative palette line appended after the static Jiraaf locks."""
    return (
        "\nBRAND SPACE PALETTE (AUTHORITATIVE — overrides any other hex above):\n"
        f"- Page background: {palette['background']} full-bleed\n"
        f"- Headlines / section titles: {palette['headline']}\n"
        f"- Accents / CTA / stat numbers / dividers: {palette['accent']}\n"
        "- Body copy: gray on white cards. Use NO other hues.\n"
    )


def resolve_brand_palette_lock(
    *,
    brand_name: str = "",
    color_behavior: str = "",
    visual_mood: str = "",
    primary_color: str = "",
    secondary_color: str = "",
    additional_colors: list[dict] | None = None,
) -> str:
    """Authoritative palette lock for non-Jiraaf image prompts."""
    label = (brand_name or "this brand").strip() or "this brand"

    if is_jiraaf_brand(label):
        return (
            f"JIRAAF LOCK: Navy {JIRAAF_NAVY} headlines on ice-blue {JIRAAF_BG} "
            f"with REQUIRED orange {JIRAAF_ORANGE} accents."
        )

    if is_cognixia_brand(label):
        return cognixia_color_behavior(
            primary_color=primary_color,
            secondary_color=secondary_color,
        )

    parts = [
        f"BRAND LOCK ({label}): Use ONLY this brand's official colour palette.",
        JIRAAF_FORBIDDEN,
    ]
    if primary_color:
        parts.append(f"PRIMARY colour: {primary_color} — use for headlines, key accents, CTA buttons.")
    if secondary_color:
        parts.append(f"SECONDARY colour: {secondary_color} — use for supporting accents, icons, highlights.")
    if additional_colors:
        extras = [
            f"{c.get('name', '')} {c.get('hex', '')}"
            for c in additional_colors
            if c.get("hex") and c.get("hex") not in (primary_color, secondary_color)
        ]
        if extras:
            parts.append(f"Additional palette: {', '.join(extras[:4])}.")
    if color_behavior or visual_mood:
        parts.append(color_behavior or visual_mood)
    if not primary_color and not secondary_color:
        parts.append("Use Brand Space visual identity colors only.")
    return " ".join(parts)


def static_background_instruction(*, brand_name: str) -> str:
    if is_jiraaf_brand(brand_name):
        return f"solid ice-blue {JIRAAF_BG}"
    if is_cognixia_brand(brand_name):
        palette = cognixia_default_palette()
        return f"clean WHITE {palette['white']} or soft card tint {palette['card_bg']}"
    return "clean WHITE #FFFFFF — soft subtle gradient allowed, never ice-blue"


def jiraaf_accent_requirement(*, brand_name: str) -> str:
    if is_jiraaf_brand(brand_name):
        return f"Brand colours REQUIRED: navy {JIRAAF_NAVY} + visible orange {JIRAAF_ORANGE} accents."
    return resolve_brand_palette_lock(brand_name=brand_name)
