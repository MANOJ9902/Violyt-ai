from __future__ import annotations

"""Build AI image prompts for INFOGRAPHIC EXPLAIN / paragraph-information layouts ONLY.

LOCKED premium LinkedIn editorial DNA (Apple + Stripe + Notion + McKinsey + Bloomberg).
Do NOT use for ranking / top-N list boards — those stay on ranking_board.py.
"""

import re
from typing import Any

from app.prompts.brand_copy_tone import NEUTRAL_BG, NEUTRAL_HEADLINE, NEUTRAL_ACCENT
from app.services.image_generation.ranking_board import sanitize_ranking_text

EXPLAIN_BG = NEUTRAL_BG
EXPLAIN_HEADING = NEUTRAL_HEADLINE
EXPLAIN_ORANGE = NEUTRAL_ACCENT
EXPLAIN_SECONDARY_BLUE = "#2D8CFF"
EXPLAIN_CARD = "#F8FBFF"
EXPLAIN_BORDER = "#DCEAF5"
EXPLAIN_BODY = "#4E6272"

_SAFE_CHARS = re.compile(r"[^\w\s₹%&.,'\"?!():;\-–/×+]")


def _scrub(text: str, *, max_words: int = 16) -> str:
    t = sanitize_ranking_text(str(text or ""))
    # Strip conversational filler before bake
    t = re.sub(
        r"^\s*(Certainly!?|Sure!?|Of course!?|Absolutely!?)\s*",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(
        r"^\s*(Here'?s|Here is)\s+(an?\s+)?(explanation|overview|summary|breakdown)\s+(of\s+)?(why\s+)?",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(
        r"^\s*(Create an infographic|Cover liquidity|explaining why the US)\b[:\s,-]*",
        "",
        t,
        flags=re.I,
    )
    t = _SAFE_CHARS.sub("", t)
    t = re.sub(r"\s+", " ", t).strip(" ,;:-")
    # Common bake typos the model still invents
    for bad, good in (
        ("giobal", "global"),
        ("explaing", "explaining"),
        ("wny", "why"),
        ("dominancein", "dominance in"),
        ("drven", "driven"),
        ("opportunitites", "opportunities"),
        ("liqudity", "liquidity"),
    ):
        t = re.sub(rf"\b{bad}\b", good, t, flags=re.I)
    words = t.split()
    if len(words) <= max_words:
        return t
    clipped = " ".join(words[:max_words]).rstrip(" ,;:-")
    # Never leave a dangling hyphenated fragment like "attri-"
    clipped = re.sub(r"\b\w+-\s*$", "", clipped).strip()
    return clipped


def _split_fact(raw: str) -> tuple[str, str]:
    fact = sanitize_ranking_text(raw)
    if "|" in fact:
        title, rest = [p.strip() for p in fact.split("|", 1)]
    elif ". " in fact and len(fact.split(". ")[0].split()) <= 5:
        title, rest = fact.split(". ", 1)
    else:
        parts = fact.split()
        title = " ".join(parts[:3])
        rest = " ".join(parts[3:])
    return _scrub(title, max_words=4).upper(), _scrub(rest, max_words=14)


def _headline_three_lines(headline: str) -> str:
    """Split headline into 3-line layout with middle word largest."""
    words = (headline or "").upper().split()
    if not words:
        return 'Line1: ""\nLine2: "" (LARGEST)\nLine3: ""'
    if len(words) <= 2:
        return f'Line1: "{words[0]}"\nLine2: "{" ".join(words[1:])}" (LARGEST)'
    third = max(1, len(words) // 3)
    return (
        f'Line1: "{" ".join(words[:third])}"\n'
        f'Line2: "{" ".join(words[third : third * 2])}" (LARGEST)\n'
        f'Line3: "{" ".join(words[third * 2 :])}"'
    )


def build_explain_infographic_prompt(
    blueprint: Any,
    *,
    canvas_desc: str,
    supporting: str = "",
    customer_quote: str = "",
    palette: dict[str, str] | None = None,
) -> str:
    """LOCKED premium paragraph/info LinkedIn infographic prompt (not ranking).

    Uses the actual blueprint content — headline, sections, CTA — NOT hardcoded defaults.
    Layout structure is fixed; colours come from Brand Space and ALL copy comes from the blueprint.
    """
    pal = palette or {}
    heading = pal.get("headline") or pal.get("primary") or EXPLAIN_HEADING
    secondary = pal.get("secondary") or pal.get("card") or EXPLAIN_CARD
    accent = pal.get("accent") or EXPLAIN_ORANGE
    bg = pal.get("background") or EXPLAIN_BG
    card = pal.get("card") or secondary
    body_c = pal.get("body") or EXPLAIN_BODY
    hairline = pal.get("muted") or EXPLAIN_BORDER
    sections = getattr(blueprint, "sections", None) or []

    # ── Extract headline, supporting, CTA from blueprint ──────────────────────
    hl = _scrub(
        getattr(blueprint, "headline", None) or getattr(blueprint, "title", None) or "",
        max_words=14,
    ).upper()
    sub_headline = _scrub(
        getattr(blueprint, "supporting_line", None) or supporting or "",
        max_words=24,
    )
    cta_text = _scrub(
        getattr(blueprint, "cta", None) or "",
        max_words=10,
    ).upper()
    source_footer = _scrub(
        getattr(blueprint, "source_footer", None) or customer_quote or "",
        max_words=18,
    )

    # ── Extract section cards from blueprint sections ──────────────────────────
    # Cap density so CTA + footer fit with bottom margin (prevents cropped buttons).
    cards: list[tuple[str, str, str]] = []  # (TITLE, body, icon_hint)
    for sec in sections[:4]:
        raw_label = _scrub(getattr(sec, "section_label", None) or "", max_words=6).upper()
        raw_body = _scrub(getattr(sec, "body", None) or "", max_words=22)
        includes = [str(x).strip() for x in (getattr(sec, "includes", None) or []) if str(x).strip()]
        stat = _scrub(getattr(sec, "stat", None) or "", max_words=8)

        # Use includes as body if body is empty
        if not raw_body and includes:
            raw_body = _scrub(includes[0], max_words=22)

        # Use stat as suffix if available
        if stat and stat not in raw_body:
            raw_body = f"{raw_body} ({stat})" if raw_body else stat

        if not raw_label or re.search(r"EXPLAINING WHY|COVER LIQUIDITY|CREATE AN", raw_label):
            seed = raw_body or stat or "KEY POINT"
            raw_label = _scrub(seed, max_words=5).upper() or "KEY POINT"

        if raw_label or raw_body:
            icon_hint = _pick_icon_hint(raw_label + " " + raw_body)
            cards.append((raw_label or "POINT", raw_body, icon_hint))

    # Prefer short CTAs so the pill never wraps/clips
    if cta_text and len(cta_text.split()) > 3:
        cta_text = " ".join(cta_text.split()[:3])

    # ── Build card lines for the prompt ───────────────────────────────────────
    card_lines = "\n".join(
        f'{i}. TITLE "{title}" | BODY "{body}" | ICON {icon}'
        for i, (title, body, icon) in enumerate(cards, start=1)
    ) if cards else "(Use the topic facts to generate relevant card content.)"

    headline_lines = _headline_three_lines(hl)
    num_cards = len(cards) or 4
    grid_desc = f"2 rows x {(num_cards + 1) // 2} columns" if num_cards > 2 else f"{num_cards} cards"

    return (
        "=== LOCKED FORMAT: INFOGRAPHIC EXPLAIN — STORYTELLING (NOT TEXTBOOK) ===\n"
        "NOT a ranking board. NOT hub-and-spoke web-search collage.\n"
        f"Canvas: {canvas_desc or '1080x1350'} portrait 4:5. Ultra HD LinkedIn-ready.\n\n"
        f"BACKGROUND: full-bleed {bg} (Brand Space background).\n"
        "BRANDING: tiny empty TOP-RIGHT corner (~7% width × ~6% height) — COMPLETELY BLANK sky gradient only. "
        "NEVER draw ANY logo, Cognixia C, brand icon, badge, or navy logo plate in the top-right. "
        "Give the hero illustration maximum space — one tiny logo is composited in post.\n"
        "NEVER bake plain brand-name watermark text anywhere (corners/footer/signature).\n"
        "Do not bake a legal disclaimer on this infographic.\n\n"
        "SAFE MARGINS (NON-NEGOTIABLE):\n"
        "- Keep ≥8% empty margin on LEFT/RIGHT/TOP.\n"
        "- Keep ≥12% empty margin at BOTTOM below the CTA — NEVER crop the CTA button or its text.\n"
        "- CTA pill must sit FULLY inside the frame, centered, with clear space under it.\n"
        "- Prefer fewer larger cards over cramped overflow.\n\n"
        "COLOUR PALETTE (Brand Space only):\n"
        f"- Headlines / section titles: {heading}\n"
        f"- Secondary {secondary} — MUST appear as card/panel fills\n"
        f"- Accent {accent} — CTA, dividers, highlight keyword\n"
        f"- Soft cards: {card} floating on the page background\n"
        f"- Card border: {hairline}\n"
        f"- Body text: {body_c}\n"
        "STORY ARC (required): hook headline → insight thesis line → at-a-glance stats → "
        "up to 4 reason cards (each a story beat) → Brand Space primary footer tagline → CTA.\n"
        "Language: everyday investor, insight-led, COMPLETE sentences. No textbook essays.\n"
        "FORBIDDEN baked text: 'Web Search:', 'Certainly!', 'Here's an explanation', "
        "'Cover liquidity', 'Answer WHY', research meta-labels, mid-sentence cuts, ADAN, "
        "'Find a recent', 'turn it into a carousel', user design instructions, 'TOPIC:'.\n"
        "SPELLING LOCK: bake EVERY word letter-perfect exactly as written below — "
        "do not invent typos (global not giobal, driven not drven, explaining not explaing).\n\n"
        "TYPOGRAPHY: bold geometric sans. Hierarchy = huge title > section > body.\n\n"
        f"TITLE (3-line layout, key middle word LARGEST — allow ONE keyword in {accent}):\n"
        f"{headline_lines}\n\n"
        "HERO (under logo pocket — NO text on hero):\n"
        "Premium photoreal/3D topic object — studio lit, soft shadow.\n\n"
        "CARDS: rounded ~20px, soft shadow, float on Brand Space background. ONE SMALL clay-3D icon each "
        "(~8–11% of card) + bold TITLE + neat 2-line BODY paragraph.\n"
        f"ICON STYLE: glossy 3D in {heading}/{accent} — NOT flat, NOT emoji, NOT giant icons crowding text.\n\n"
        "LAYOUT:\n"
        f"1) TOP: headline in {heading} + insight supporting line in {body_c} + empty top-right logo pocket (~7% W × ~6% H)\n"
        f'   Supporting thesis: "{sub_headline}"\n'
        "2) Optional at-a-glance stat strip (2–3 latest numbers)\n"
        f"3) MIDDLE: {grid_desc} reason cards — bake EVERY section body (REQUIRED)\n"
        "4) FOOTER line only — leave the bottom ~12% EMPTY for a composited CTA pill "
        "(do NOT bake any CTA button or Explore More text into the image)\n"
        "5) NEVER empty cards. NEVER repeated titles. NEVER repeated bodies. "
        "Each card BODY must be a different sentence — do not paste one insight on every card.\n"
        "6) NEVER replace facts with sample filler. NEVER cut off words mid-token.\n\n"
        "RENDER: Octane/Redshift look — crisp edges, GI, HDR.\n"
        "NEGATIVE: cream BG, teal titles, generic navy/orange, hub-spoke web-search UI, clipart, "
        "watermark, neon, handwritten fonts, truncated text, cropped CTA, misspelled words.\n"
        f"COLOUR BAN: never paint navy/orange/gold/ice-blue unless that hex is {heading}, {secondary}, or {accent}.\n\n"
        "=== BAKE ONLY THIS COPY (letter-perfect, COMPLETE sentences) ===\n"
        f'HEADLINE: "{hl}"\n'
        + (f'CTA (fill {accent}, white text, compact pill, FULLY inside bottom margin): "{cta_text}"\n' if cta_text else "")
        + f'SUPPORTING LINE: "{sub_headline}"\n'
        f"SECTION CARDS ({num_cards} cards total):\n"
        f"{card_lines}\n"
        + (f'SOURCE FOOTER: "{source_footer}"\n' if source_footer else "")
        + "=== END LOCKED EXPLAIN INFOGRAPHIC PROMPT ===\n"
    )


def _pick_icon_hint(text: str) -> str:
    """Pick a relevant 3D icon hint based on keywords in the label/body."""
    t = text.lower()
    if any(k in t for k in ("airport", "flight", "air", "runway", "terminal", "plane", "udan")):
        return "3D glossy airplane or airport tower with soft shadow"
    if any(k in t for k in ("money", "invest", "fund", "crore", "lakh", "₹", "revenue", "cost")):
        return "3D coins or rising bar chart"
    if any(k in t for k in ("job", "employ", "work", "labour", "skill")):
        return "3D briefcase or handshake"
    if any(k in t for k in ("connect", "route", "region", "city", "map", "network")):
        return "3D location pin or network nodes"
    if any(k in t for k in ("growth", "expand", "develop", "build", "construct", "infra")):
        return "3D building or construction crane"
    if any(k in t for k in ("trade", "export", "import", "global", "international")):
        return "3D cargo ship or globe"
    if any(k in t for k in ("tech", "digital", "data", "software", "cloud")):
        return "3D chip or circuit board"
    if any(k in t for k in ("health", "medical", "hospital", "care")):
        return "3D medical cross or stethoscope"
    if any(k in t for k in ("learn", "education", "school", "skill", "train")):
        return "3D book or graduation cap"
    if any(k in t for k in ("secure", "safe", "protect", "lock")):
        return "3D shield with checkmark"
    if any(k in t for k in ("environment", "green", "eco", "sustain", "solar", "energy")):
        return "3D green leaf or solar panel"
    if any(k in t for k in ("time", "fast", "speed", "quick")):
        return "3D clock or lightning bolt"
    if any(k in t for k in ("passenger", "tourist", "travel", "trip")):
        return "3D suitcase or passport"
    return "Premium 3D icon relevant to the topic with soft studio lighting"
