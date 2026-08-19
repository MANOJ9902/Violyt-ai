"""Palette helpers for image prompts — Brand Space pack only.

Visual DNA comes from BrandVisualPack. No brand-name detectors.
"""

from __future__ import annotations

from app.utils.palette_roles import normalize_hex


def resolve_brand_palette_lock(
    *,
    brand_name: str = "",
    color_behavior: str = "",
    visual_mood: str = "",
    primary_color: str = "",
    secondary_color: str = "",
    accent_color: str = "",
    additional_colors: list[dict] | None = None,
) -> str:
    label = (brand_name or "this brand").strip() or "this brand"
    parts = [f"BRAND LOCK ({label}): Use ONLY this Brand Space palette."]
    if primary_color:
        parts.append(f"PRIMARY: {primary_color} — headlines.")
    if secondary_color:
        parts.append(f"SECONDARY: {secondary_color} — cards and supporting fills.")
    if accent_color:
        parts.append(f"ACCENT: {accent_color} — CTA and highlights.")
    if additional_colors:
        extras = [
            f"{c.get('name', '')} {c.get('hex', '')}".strip()
            for c in additional_colors
            if isinstance(c, dict) and c.get("hex") and c.get("role") in {"accent", "background", "surface", "muted"}
        ]
        if extras:
            parts.append("Role extras: " + ", ".join(extras[:4]) + ".")
    if color_behavior or visual_mood:
        parts.append(color_behavior or visual_mood)
    if not primary_color and not secondary_color:
        parts.append("Use Brand Space visual identity colors only — do not invent another brand's palette.")
    return " ".join(parts)


def static_background_instruction(*, brand_name: str = "", background: str = "") -> str:
    bg = normalize_hex(background) or "#FFFFFF"
    return f"solid background {bg} full bleed"


def resolve_brand_palette(
    *,
    primary: str = "",
    secondary: str = "",
    background: str = "",
) -> dict[str, str]:
    headline = normalize_hex(primary) or "#1F2937"
    accent = normalize_hex(secondary) or headline
    bg = normalize_hex(background) or "#FFFFFF"
    return {
        "headline": headline,
        "accent": accent,
        "background": bg,
        "headline_source": "brand_space" if primary else "neutral",
        "accent_source": "brand_space" if secondary else "neutral",
    }


def brand_space_palette_override(palette: dict[str, str]) -> str:
    return (
        "\nBRAND SPACE PALETTE (AUTHORITATIVE):\n"
        f"- Page background: {palette.get('background', '#FFFFFF')} full-bleed\n"
        f"- Headlines: {palette.get('headline') or palette.get('primary', '#1F2937')}\n"
        f"- Secondary/cards: {palette.get('secondary') or palette.get('card', '#FFFFFF')}\n"
        f"- Accents: {palette.get('accent') or '#4B5563'}\n"
        "- Use NO other hues.\n"
    )
