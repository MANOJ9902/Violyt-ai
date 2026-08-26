# Utility helpers collect shared formatting, parsing, and normalization rules used across services.
from __future__ import annotations

import re
from typing import Any


VALID_PALETTE_ROLES = {"primary", "secondary", "accent", "background", "surface", "neutral"}


def normalize_hex(value: Any) -> str | None:
    # Normalizes hex as a reusable helper for services that need the same formatting or normalization rule.
    text = str(value or "").strip().upper()
    if not text:
        return None
    if not text.startswith("#") and re.fullmatch(r"[0-9A-F]{6}", text):
        text = f"#{text}"
    return text if re.fullmatch(r"#[0-9A-F]{6}", text) else None


def hex_to_rgb(value: Any) -> tuple[int, int, int] | None:
    # Handles hex to rgb as a reusable helper for services that need the same formatting or normalization rule.
    normalized = normalize_hex(value)
    if not normalized:
        return None
    text = normalized.lstrip("#")
    return tuple(int(text[index:index + 2], 16) for index in range(0, 6, 2))


def is_soft_neutral_color(rgb: tuple[int, int, int]) -> bool:
    # Handles is soft neutral color as a reusable helper for services that need the same formatting or
    # normalization rule.
    return max(rgb) - min(rgb) <= 24 or sum(rgb) >= 660


def _entry_hex(entry: dict[str, Any]) -> str | None:
    # Handles entry hex as a reusable helper for services that need the same formatting or normalization rule.
    return normalize_hex(entry.get("hex_code") or entry.get("hex") or entry.get("color_code") or entry.get("value"))


def _entry_role(entry: dict[str, Any]) -> str:
    # Handles entry role as a reusable helper for services that need the same formatting or normalization rule.
    return str(entry.get("role") or "").strip().lower()


def _entry_name(entry: dict[str, Any]) -> str:
    # Handles entry name as a reusable helper for services that need the same formatting or normalization rule.
    return str(entry.get("color_name") or entry.get("name") or "").strip().lower()


def _collect_template_palette_entries(template_intelligence: object) -> list[dict[str, Any]]:
    # Handles collect template palette entries as a reusable helper for services that need the same formatting
    # or normalization rule.
    collected: list[dict[str, Any]] = []
    if not isinstance(template_intelligence, list):
        return collected
    for item in template_intelligence:
        if not isinstance(item, dict):
            continue
        analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else item
        if not isinstance(analysis, dict):
            continue
        for key in ("palette", "color_usage", "font_colors"):
            values = analysis.get(key)
            if not isinstance(values, list):
                continue
            for entry in values:
                if isinstance(entry, dict) and _entry_hex(entry):
                    collected.append(entry)
    return collected


def _luminance(rgb: tuple[int, int, int]) -> float:
    # Handles luminance as a reusable helper for services that need the same formatting or normalization rule.
    red, green, blue = rgb
    return (0.2126 * red) + (0.7152 * green) + (0.0722 * blue)


def _saturation(rgb: tuple[int, int, int]) -> float:
    # Handles saturation as a reusable helper for services that need the same formatting or normalization rule.
    return float(max(rgb) - min(rgb))


def _warmth(rgb: tuple[int, int, int]) -> float:
    # Handles warmth as a reusable helper for services that need the same formatting or normalization rule.
    red, green, blue = rgb
    return float((red + green) - (blue * 1.15))


def _score_background(entry: dict[str, Any], rgb: tuple[int, int, int]) -> float:
    # Scores background as a reusable helper for services that need the same formatting or normalization rule.
    role = _entry_role(entry)
    name = _entry_name(entry)
    score = 0.0
    if role in {"background", "surface", "neutral"}:
        score += 300.0
    if any(keyword in f"{role} {name}" for keyword in ("background", "surface", "ivory", "cream", "sand", "beige", "neutral")):
        score += 120.0
    score += _luminance(rgb) * 1.8
    score -= _saturation(rgb) * 0.35
    score += max(_warmth(rgb), 0.0) * 0.08
    if is_soft_neutral_color(rgb):
        score += 80.0
    return score


def _score_primary(entry: dict[str, Any], rgb: tuple[int, int, int]) -> float:
    # Scores primary as a reusable helper for services that need the same formatting or normalization rule.
    role = _entry_role(entry)
    name = _entry_name(entry)
    score = 0.0
    if role == "primary":
        score += 280.0
    if any(keyword in f"{role} {name}" for keyword in ("primary", "brand", "main")):
        score += 90.0
    score += _saturation(rgb) * 0.9
    score += max(180.0 - abs(_luminance(rgb) - 120.0), 0.0) * 0.5
    return score


def _score_secondary(entry: dict[str, Any], rgb: tuple[int, int, int]) -> float:
    # Scores secondary as a reusable helper for services that need the same formatting or normalization rule.
    role = _entry_role(entry)
    name = _entry_name(entry)
    score = 0.0
    if role == "secondary":
        score += 260.0
    if any(keyword in f"{role} {name}" for keyword in ("secondary", "supporting", "companion")):
        score += 80.0
    score += _saturation(rgb) * 0.65
    score += max(170.0 - abs(_luminance(rgb) - 105.0), 0.0) * 0.35
    return score


def _score_accent(entry: dict[str, Any], rgb: tuple[int, int, int]) -> float:
    # Scores accent as a reusable helper for services that need the same formatting or normalization rule.
    role = _entry_role(entry)
    name = _entry_name(entry)
    score = 0.0
    if role == "accent":
        score += 280.0
    if any(keyword in f"{role} {name}" for keyword in ("accent", "highlight", "cta", "signal")):
        score += 80.0
    score += _saturation(rgb) * 1.1
    score += max(220.0 - abs(_luminance(rgb) - 145.0), 0.0) * 0.25
    return score


_ADDITIONAL_ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "primary": ("primary colour", "primary color", "primary"),
    "secondary": ("secondary colour", "secondary color", "secondary"),
    "accent": ("accent", "highlight", "cta", "button"),
    "background": ("background", "bg", "canvas"),
    "surface": ("surface", "card", "panel", "primary tint", "secondary tint", "tint"),
    "neutral": ("neutral", "muted", "grey", "gray", "supporting dark", "body"),
}


def resolve_role_from_additional(additional: Any, role: str) -> str | None:
    # Looks up an explicit Role (e.g. "Background", "Supporting Dark") tagged on a brand_color_palette
    # "additional" row from the Brand Color Palette table. Without this, a color only ever set via that
    # table's Role column (instead of a bare top-level "background"/"accent" key) would be invisible to
    # every downstream palette-aware prompt/render step that calls derive_palette_roles().
    if not isinstance(additional, list) or role not in VALID_PALETTE_ROLES:
        return None
    keywords = _ADDITIONAL_ROLE_KEYWORDS.get(role, ())
    for item in additional:
        if not isinstance(item, dict):
            continue
        hint = str(item.get("role") or "").strip().casefold()
        label = str(item.get("name") or "").strip().casefold()
        haystack = hint or label
        if not haystack:
            continue
        if haystack == role or any(keyword in haystack for keyword in keywords):
            hex_code = normalize_hex(item.get("hex") or item.get("hex_code") or item.get("color"))
            if hex_code:
                return hex_code
    return None


def derive_palette_roles(
    visual_identity: dict[str, Any] | None,
    *,
    allow_template_swatches: bool = False,
) -> dict[str, str]:
    """Resolve palette roles from Brand Space form + role-tagged entries.

    By default PDF/template creative swatches are ignored so image generation
    never invents another brand's navy/orange from reference PDFs.
    Set allow_template_swatches=True only for non-generation analytics.
    """
    visual_identity = visual_identity or {}
    explicit_palette = visual_identity.get("brand_color_palette", {}) or {}
    explicit: dict[str, str] = {}
    if isinstance(explicit_palette, dict):
        explicit = {
            str(key).strip().lower(): normalized
            for key, value in explicit_palette.items()
            if str(key).strip().lower() in VALID_PALETTE_ROLES
            if (normalized := normalize_hex(value))
        }
        for role in VALID_PALETTE_ROLES:
            if role in explicit:
                continue
            resolved = resolve_role_from_additional(explicit_palette.get("additional"), role)
            if resolved:
                explicit[role] = resolved

    palette_entries = [
        entry
        for entry in (
            explicit_palette
            if isinstance(explicit_palette, list)
            else (visual_identity.get("palette_entries", []) or [])
        )
        if isinstance(entry, dict) and _entry_hex(entry)
    ]
    template_entries = (
        _collect_template_palette_entries(visual_identity.get("template_intelligence"))
        if allow_template_swatches
        else []
    )
    # When templates are disabled, only use entries that already declare a role
    # (Brand Space upload / form) — never invent roles by scoring random hexes.
    if not allow_template_swatches:
        palette_entries = [e for e in palette_entries if _entry_role(e) in VALID_PALETTE_ROLES]
    candidates = [*palette_entries, *template_entries]
    merged: dict[str, str] = dict(explicit)

    for entry in candidates:
        role = _entry_role(entry)
        hex_code = _entry_hex(entry)
        if role in VALID_PALETTE_ROLES and hex_code:
            merged.setdefault(role, hex_code)

    # Heuristic scoring invents primary/secondary from random swatches — only allow
    # when explicitly opted in (never for image generation / Brand Space form path).
    if not allow_template_swatches:
        if "background" not in merged and merged.get("neutral"):
            merged["background"] = merged["neutral"]
        return {key: value for key, value in merged.items() if value}

    used = {value for value in merged.values() if value}

    def choose_best(
        scorer,
        *,
        avoid_light_for_non_background: bool = False,
    ) -> str | None:
        # Handles choose best as a reusable helper for services that need the same formatting or normalization
        # rule.
        best_hex: str | None = None
        best_score = float("-inf")
        for entry in candidates:
            hex_code = _entry_hex(entry)
            rgb = hex_to_rgb(hex_code)
            if not hex_code or not rgb or hex_code in used:
                continue
            if avoid_light_for_non_background and _luminance(rgb) >= 235:
                continue
            score = scorer(entry, rgb)
            if score > best_score:
                best_score = score
                best_hex = hex_code
        return best_hex

    if "background" not in merged:
        background = choose_best(_score_background)
        if background:
            merged["background"] = background
            used.add(background)

    if "primary" not in merged:
        primary = choose_best(_score_primary, avoid_light_for_non_background=True)
        if primary:
            merged["primary"] = primary
            used.add(primary)

    if "secondary" not in merged:
        secondary = choose_best(_score_secondary, avoid_light_for_non_background=True)
        if secondary:
            merged["secondary"] = secondary
            used.add(secondary)

    if "accent" not in merged:
        accent = choose_best(_score_accent, avoid_light_for_non_background=True)
        if accent:
            merged["accent"] = accent

    if "background" not in merged and merged.get("neutral"):
        merged["background"] = merged["neutral"]

    return {key: value for key, value in merged.items() if value}
