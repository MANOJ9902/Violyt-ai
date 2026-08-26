"""Lean static / landscape prompt — COPY first, under budget, neat layout.

LinkedIn static (1200x627) cannot survive a 6k+ expander prompt: the model truncates
and drops colour / no-cutoff rules. This builder emits a short, copy-led prompt that
fits beside the mandatory Brand Render Contract.
"""

from __future__ import annotations

from typing import Any


def _scrub(text: str, max_words: int) -> str:
    words = " ".join(str(text or "").split()).strip().rstrip("….").strip()
    if not words:
        return ""
    parts = words.split()
    if len(parts) <= max_words:
        return words
    return " ".join(parts[:max_words]).rstrip(".,;:")


def build_lean_static_prompt(
    *,
    canvas_desc: str,
    headline: str,
    supporting: str,
    cards: list[dict[str, str]],
    palette: dict[str, str] | None = None,
    brand_name: str = "",
    cta: str = "",
) -> str:
    """Build a budget-safe static prompt: exact copy + compact Brand Space style."""
    pal = palette or {}
    bg = pal.get("background") or pal.get("bg") or "#FFFFFF"
    primary = pal.get("primary") or pal.get("headline") or "#1F2937"
    secondary = pal.get("secondary") or pal.get("card") or primary
    accent = pal.get("accent") or primary
    body = pal.get("body") or "#374151"
    card = pal.get("card") or secondary

    hl = _scrub(headline, 10)
    sub = _scrub(supporting, 8)
    brand = (brand_name or "Brand").strip() or "Brand"

    # Landscape static has ~180px per card — TITLE ONLY, max 8 complete words.
    card_lines: list[str] = []
    for i, c in enumerate((cards or [])[:4], start=1):
        title = _scrub(c.get("title") or c.get("body") or "", 8)
        if not title:
            continue
        card_lines.append(f'  CARD {i}: SMALL clay-3D icon + TITLE "{title}" — no extra lines')
    if not card_lines:
        card_lines.append('  CARD 1: SMALL clay-3D icon + TITLE "Key insight" — no extra lines')

    cta_note = _scrub(cta or "Explore More", 3)

    return (
        f"=== LEAN STATIC — {brand} ===\n"
        f"Canvas {canvas_desc}. Premium neat educational LinkedIn static.\n\n"
        "COPY TO BAKE (letter-perfect, COMPLETE words — never break a word across lines):\n"
        f'HEADLINE: "{hl}"\n'
        + (f'SUBHEAD: "{sub}"\n' if sub else "")
        + "CARDS (exactly these, left→right):\n"
        + "\n".join(card_lines)
        + "\n\n"
        "LAYOUT (neat, clean, uncluttered):\n"
        f"- PAGE BG: solid full-bleed {bg} edge to edge — ONE colour only. "
        "NO nested white/pale panel, NO floating frame, NO second background, NO side bars.\n"
        f"- Headline ExtraBold {primary} top-left ~70% width, max 2 complete lines.\n"
        f"- One short subhead under it in {body} — ONE complete line, never hyphenate.\n"
        f"- Exactly {len(card_lines)} SEPARATE rounded cards in one row, fill {card}, "
        f"with {bg} clearly visible BETWEEN every card. NEVER merge cards into one blue bar "
        "or nested page panel.\n"
        "Each card = one small icon + ONE complete title (max 8 words). "
        "No body paragraph, no second line, no hyphenation, no cutoff.\n"
        "- 16px inner padding inside every card. Title must sit fully inside the card.\n"
        "- TOP-RIGHT ~20%x12% EMPTY page background (logo composited in post).\n"
        f"- BOTTOM ≥16% EMPTY {bg} — DO NOT bake any CTA / button / '{cta_note}' pill "
        "(composited in post).\n"
        "- ≥8% side margins. Scale font down — never clip, never mid-word wrap.\n\n"
        "COLOURS (Brand Space only):\n"
        f"BG {bg} · HEADLINE {primary} · CARD {card} · ACCENT {accent} · BODY {body}.\n"
        "No green, mint, teal, gold, neon, or white page panels.\n"
        "Icons: small clay-3D studio objects using ONLY the hexes above.\n"
        "=== END ===\n"
    )


def cards_from_blueprint(blueprint: Any, *, max_cards: int = 4, max_words: int = 12) -> list[dict[str, str]]:
    """Pull short card titles from a blueprint for the lean static prompt.

    Landscape static (~627px) only has room for a title under each icon — bodies
    that restate the title are dropped so nothing clips mid-phrase.
    """
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    def _key(s: str) -> str:
        return "".join(ch for ch in (s or "").casefold() if ch.isalnum())

    for sec in list(getattr(blueprint, "sections", None) or [])[: max_cards * 2]:
        label = _scrub(getattr(sec, "section_label", "") or "", 12)
        body = _scrub(getattr(sec, "body", "") or "", max_words)
        stat = _scrub(getattr(sec, "stat", "") or "", 6)
        title = label or _scrub(body, 10)
        if not title:
            continue
        k = _key(title)
        if k in seen:
            continue
        seen.add(k)
        # Landscape static: title only. Bodies clip on 627px canvases.
        title = _scrub(title, 8)
        out.append({"title": title, "body": "", "stat": stat})
        if len(out) >= max_cards:
            break
    if len(out) < max_cards:
        for raw in list(getattr(blueprint, "stat_highlights", None) or [])[:max_cards]:
            t = _scrub(str(raw), 12)
            k = _key(t)
            if t and k not in seen:
                seen.add(k)
                out.append({"title": t, "body": "", "stat": ""})
            if len(out) >= max_cards:
                break
    return out[:max_cards]
