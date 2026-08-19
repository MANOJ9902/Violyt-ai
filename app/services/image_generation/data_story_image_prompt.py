from __future__ import annotations

"""Build AI image prompts for the data-story infographic.

Layout DNA is measured from sample_infographic_data_story_airports.png: a
gradient ice-blue canvas, a hero stat band of big numbers, two side-by-side
panels (numbered proof + qualitative reasons), a closing couplet and a source
line. Use this for information/data-led explainers.

Not for ranking boards (ranking_board.py) or light card explainers
(explain_image_prompt.py).
"""

import re
from typing import Any

from app.prompts.brand_copy_tone import (
    NEUTRAL_BG,
    NEUTRAL_HEADLINE,
    NEUTRAL_ACCENT,
)
from app.services.image_generation.ranking_board import sanitize_ranking_text

DATA_BG_TOP = NEUTRAL_BG
DATA_BG_MID = NEUTRAL_BG
DATA_BG_BOTTOM = NEUTRAL_BG
DATA_HEADLINE = NEUTRAL_HEADLINE
DATA_ACCENT = NEUTRAL_ACCENT
DATA_BODY = "#374151"
DATA_PANEL = "#F3F4F6"
DATA_HAIRLINE = "#E5E7EB"

_SAFE_CHARS = re.compile(r"[^\w\s₹%&.,'\"?!():;\-–/×+]")

# Leading figure of a stat line: 15.4%, 352 MN+, 2.7X, No. 3, ₹1.5T, 148
_LEADING_FIGURE = re.compile(
    r"^\s*((?:No\.?\s*)?[₹$€£]?\d[\d,]*(?:\.\d+)?\s*"
    r"(?:%|X|MN|BN|CR|K|T|LAKH|CRORE|MILLION|BILLION|TRILLION)?\+?)\s*(.*)$",
    re.IGNORECASE,
)
_TOKEN_WITH_DIGIT = re.compile(r"^[₹$€£]?[\w./\-]*\d[\w%+./\-]*$")


# Words that must never end a rendered string — "connect Tiers2 and" was a
# word-count truncation landing mid-clause and getting baked into artwork.
_DANGLING = frozenset(
    """a an the and or but that which with for to of in on at by from as is are was were
    its their this these those than when while if into over under per vs about after
    before between during through across""".split()
)


def _scrub(text: str, *, max_words: int = 16) -> str:
    """Clip to a word budget without ever leaving a dangling clause."""
    t = sanitize_ranking_text(str(text or ""))
    # Normalise money units so the image model never splits "crore" mid-word.
    t = re.sub(r"\bRs\.?\s*", "₹", t, flags=re.I)
    t = re.sub(r"\bINR\s*", "₹", t, flags=re.I)
    t = re.sub(r"\bcrore\b", "cr", t, flags=re.I)
    t = re.sub(r"\blakh\b", "L", t, flags=re.I)
    t = _SAFE_CHARS.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    if len(words) > max_words:
        clipped = words[:max_words]
        # Prefer a natural boundary over a hard cut, when one is close enough.
        for i in range(len(clipped) - 1, max(2, int(max_words * 0.6)) - 1, -1):
            if clipped[i].endswith((".", ";", ",", ":")):
                clipped = clipped[: i + 1]
                break
        words = clipped
    while words and words[-1].strip(".,;:").casefold() in _DANGLING:
        words.pop()
    return " ".join(words).strip(" ,;:-–")


def split_stat(raw: str) -> tuple[str, str]:
    """Split a flattened stat line into (figure, label).

    "15.4% Annual growth in traffic" -> ("15.4%", "Annual growth in traffic")
    "₹98,000 cr total investment"     -> ("₹98,000 cr", "total investment")
    "Tier-2/3 Cities Connected"      -> ("Tier-2/3", "Cities Connected")

    The figure is always the numeric token PLUS its unit, so labels never carry
    a lone "crore" that the image model wraps as "cr ore".
    """
    text = _scrub(raw, max_words=14)
    if not text:
        return "", ""
    match = _LEADING_FIGURE.match(text)
    if match and match.group(1).strip():
        figure = match.group(1).strip()
        label = _scrub(match.group(2), max_words=8)
        # Pull a trailing unit that escaped the figure group (e.g. "cr" after a gap).
        label_words = label.split()
        if label_words and label_words[0].casefold() in {"cr", "l", "%", "x", "mn", "bn"}:
            figure = f"{figure} {label_words[0]}"
            label = " ".join(label_words[1:])
        return figure, label
    words = text.split()
    for i, word in enumerate(words):
        if _TOKEN_WITH_DIGIT.match(word):
            # Absorb an immediate unit token into the figure.
            figure_words = [word]
            rest = words[:i] + words[i + 1 :]
            if rest and rest[0].casefold() in {"cr", "l", "%", "x", "mn", "bn", "crore"}:
                unit = "cr" if rest[0].casefold() == "crore" else rest[0]
                figure_words.append(unit)
                rest = rest[1:]
            label = _scrub(" ".join(rest), max_words=8)
            return " ".join(figure_words), label
    return "", text


def _headline_lines(headline: str, *, max_per_line: int = 22) -> list[str]:
    """Wrap the headline into at most 3 balanced lines that fit the canvas."""
    words = (headline or "").upper().split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_per_line and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if len(lines) > 3:
        lines = lines[:2] + [" ".join(lines[2:])]
    return lines


def _norm(text: str) -> str:
    """Comparison key for duplicate detection."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").casefold()).strip()


def _is_placeholder(text: str) -> bool:
    """Reject our own scaffolding and numbered stubs before they reach the canvas."""
    t = (text or "").strip().casefold()
    if not t:
        return True
    if re.search(r"\b(rationale|point|item|reason|section|beat)\s*\d+\s*$", t):
        return True
    return any(
        marker in t
        for marker in (
            "simple view before wider adoption",
            "here's the simple view",
            "web search",
            "answer why",
            "lorem ipsum",
            "placeholder",
            "everything you need",
            "need to know",
            "needs a lot",
            "a lot more airports",
        )
    )


def build_data_story_prompt(
    blueprint: Any,
    *,
    canvas_desc: str = "1080x1350",
    supporting: str = "",
    palette: dict[str, str] | None = None,
) -> str:
    palette = palette or {}
    headline_c = palette.get("headline") or palette.get("primary") or DATA_HEADLINE
    secondary_c = palette.get("secondary") or palette.get("card") or DATA_PANEL
    accent_c = palette.get("accent") or DATA_ACCENT
    bg = palette.get("background") or DATA_BG_TOP
    card = palette.get("card") or secondary_c or DATA_PANEL
    body_c = palette.get("body") or palette.get("muted") or DATA_BODY
    hairline = palette.get("muted") or DATA_HAIRLINE

    headline = _scrub(
        getattr(blueprint, "headline", None) or getattr(blueprint, "title", None) or "",
        max_words=14,
    ).upper()
    subhead = _scrub(
        getattr(blueprint, "supporting_line", None) or supporting or "", max_words=20
    )
    source_footer = _scrub(getattr(blueprint, "source_footer", None) or "", max_words=20)
    closing = _scrub(getattr(blueprint, "customer_quote", None) or "", max_words=22)
    cta = _scrub(getattr(blueprint, "cta", None) or "", max_words=12)

    # Thin research makes the copy engine reuse one fact across every slot, which
    # renders as a poster that repeats itself. Track what has been used and show
    # each fact at most once, even if that means fewer slots.
    used_figures: set[str] = set()
    used_text: set[str] = set()

    def _claim(figure: str, text: str) -> bool:
        fig_key, text_key = _norm(figure), _norm(text)
        if fig_key and fig_key in used_figures:
            return False
        if text_key and text_key in used_text:
            return False
        if text_key and any(
            text_key in seen or seen in text_key for seen in used_text if len(seen) > 8
        ):
            return False
        if fig_key:
            used_figures.add(fig_key)
        if text_key:
            used_text.add(text_key)
        return True

    # Hero band: latest at-a-glance figures (prefer blueprint order = newest first).
    hero: list[tuple[str, str]] = []
    for raw in list(getattr(blueprint, "stat_highlights", None) or []):
        if _is_placeholder(str(raw)):
            continue
        figure, label = split_stat(str(raw))
        if figure and label and _claim(figure, label):
            hero.append((figure, label))
        if len(hero) == 6:
            break
    # Also promote numeric proof_points into the hero when highlights are thin.
    if len(hero) < 4:
        for raw in list(getattr(blueprint, "proof_points", None) or []):
            if _is_placeholder(str(raw)) or not re.search(r"\d", str(raw)):
                continue
            figure, label = split_stat(str(raw))
            if figure and label and _claim(figure, label):
                hero.append((figure, label))
            if len(hero) == 6:
                break

    # Panels: keep TITLE + BODY (so-what paragraph) — do not drop insight into a label only.
    # numbered = (figure, title, body); reasons = (title, body)
    numbered: list[tuple[str, str, str]] = []
    reasons: list[tuple[str, str]] = []
    for sec in list(getattr(blueprint, "sections", None) or [])[:12]:
        label = _scrub(getattr(sec, "section_label", None) or "", max_words=8)
        body = _scrub(getattr(sec, "body", None) or "", max_words=28)
        stat = _scrub(getattr(sec, "stat", None) or "", max_words=6)
        includes = [
            str(x) for x in (getattr(sec, "includes", None) or []) if str(x).strip()
        ]
        if _is_placeholder(label) and _is_placeholder(body):
            continue
        if not body and includes:
            # Prefer the longest include so we keep the insightful sentence, not a chip.
            best = max(includes, key=lambda x: len(str(x).split()))
            body = _scrub(best, max_words=28)
        if _is_placeholder(body):
            body = ""
        # If body is thin but includes have a second fact, append one short clause.
        if body and includes and len(body.split()) < 12:
            for inc in includes:
                extra = _scrub(inc, max_words=14)
                if extra and _norm(extra) not in _norm(body):
                    body = _scrub(f"{body} {extra}".strip(), max_words=28)
                    break
        title = label or _scrub(body, max_words=6)
        if stat:
            if _claim(stat, title or body):
                numbered.append((stat, title, body or title))
        elif label or body:
            figure, rest = split_stat(label or body)
            if figure:
                if _claim(figure, rest or body):
                    numbered.append((figure, rest or title, body or rest or title))
            else:
                if (title or body) and _claim("", body or title):
                    reasons.append((title, body or title))
    numbered = numbered[:5]
    reasons = [(t, b) for t, b in reasons if t or b][:5]

    # If dedup emptied the hero band but proof rows survived, promote them so the
    # poster still leads with numbers instead of opening on an empty band.
    if not hero and numbered:
        hero = [(fig, lab) for fig, lab, _body in numbered[:5]]
        numbered = numbered[5:]

    hero_block = (
        "\n".join(
            f'  COL{i}: FIGURE "{fig}" | LABEL "{lab}"'
            for i, (fig, lab) in enumerate(hero, start=1)
        )
        or "  (omit the hero stat band entirely if no figures are supplied)"
    )
    # Supporting zone — each insight = small icon + title + neat 2–3 line paragraph.
    insight_cards: list[str] = []
    for i, (num, lab, body) in enumerate(numbered, start=1):
        insight_cards.append(
            f'  CARD{i}: SMALL ICON + NUMBER "{num}" + TITLE "{lab}" + BODY "{body}"'
        )
    for i, (title, body) in enumerate(reasons, start=len(insight_cards) + 1):
        insight_cards.append(
            f'  CARD{i}: SMALL ICON + TITLE "{title}" + BODY "{body}"'
        )
    insight_block = "\n".join(insight_cards) or "  (omit the insight cards)"

    n_cards = len(insight_cards)
    if n_cards >= 4:
        panel_zone = (
            f"SUPPORTING INSIGHTS — {n_cards} soft rounded cards in a neat 2-column grid\n"
            f"   (2×2 / 2×3). Every card: SMALL clay-3D icon (~8–11% of card height) on\n"
            f"   the left, bold TITLE in {headline_c}, then a neat 2–3 line BODY paragraph with the\n"
            "   latest / most important so-what. Equal card height, soft shadow, clear\n"
            "   hierarchy. Bake EVERY card — do not omit or invent filler."
        )
    elif n_cards >= 2:
        panel_zone = (
            f"SUPPORTING INSIGHTS — {n_cards} soft rounded cards side-by-side (or stacked).\n"
            "   Every card: SMALL clay-3D icon + bold title + neat 2–3 line body paragraph.\n"
            "   Equal visual weight. Prefer latest verified numbers in the body text."
        )
    elif n_cards == 1:
        panel_zone = (
            "ONE full-width soft rounded insight card with a SMALL clay-3D icon +\n"
            "   bold title + neat 2–3 line body paragraph. Never leave empty canvas."
        )
    else:
        panel_zone = "(no insight cards — close the layout directly after KEY STATISTICS)"

    headline_block = "\n".join(
        f'  LINE{i}: "{line}"' for i, line in enumerate(_headline_lines(headline), start=1)
    )
    n_hero = len(hero) or 4

    return (
        "Create a PREMIUM LinkedIn editorial infographic poster.\n"
        "Claymorphic 3D icons, strong type hierarchy, rounded insight cards,\n"
        "generous whitespace, ultra-sharp typography.\n"
        f"Vertical portrait {canvas_desc}, ultra HD, consulting-report craft.\n\n"
        "================= 1. CONTENT =================\n"
        "Bake ONLY the strings below, letter-perfect and COMPLETE. Render nothing that is\n"
        "not listed. No invented labels, no filler, no extra sentences.\n"
        "HEADLINE (max 3 lines):\n"
        f"{headline_block}\n"
        + (f'SUBTITLE (one short line): "{subhead}"\n' if subhead else "")
        + "KEY STATISTICS (hero band):\n"
        f"{hero_block}\n"
        "SUPPORTING INSIGHT CARDS:\n"
        f"{insight_block}\n"
        + (f'TAKEAWAY LINE 1 (colour {headline_c}): "{closing}"\n' if closing else "")
        + (f'TAKEAWAY LINE 2 (colour {accent_c}): "{cta}"\n' if cta else "")
        + (f'SOURCE LINE: "{source_footer}"\n' if source_footer else "")
        + "Dense but neat: bake ALL listed stats and insight cards. Prefer latest verified\n"
        "numbers and so-what paragraphs — never replace with generic sample filler.\n\n"
        "================= 2. LAYOUT (STRUCTURED INFORMATION POSTER) =================\n"
        "Top-to-bottom story. Strong alignment. Clear section breathing room — mapped,\n"
        "not dumped. MARGINS: ≥5% inset. Every string fully inside the frame.\n"
        "ZONE A — HEADER:\n"
        f"  LEFT ~55%: huge bold ALL-CAPS headline in {headline_c} (max 3 lines), tight leading.\n"
        f"  Short thick accent rule (~80×6px, colour {accent_c}) under the first headline line.\n"
        f"  One-line subtitle under the rule in {body_c}.\n"
        "  RIGHT ~40%: ONE large hero clay-3D illustration of the TOPIC (not a logo).\n"
        "  Hero sits on a soft contact shadow / subtle podium. Glossy, dimensional,\n"
        "  studio-lit — like a product still. NO text, NO wordmark inside the hero.\n"
        "  TOP-RIGHT ~22%×11% logo pocket COMPLETELY BLANK (brand logo composited later).\n"
        "ZONE B — KEY STATISTICS:\n"
        f"  Small ALL-CAPS label 'KEY STATISTICS' in {headline_c} + thin hairline rule.\n"
        f"  {n_hero} equal columns across the width. NO boxes around the columns.\n"
        "  Each column stack (top→bottom):\n"
        "    1) SMALL clay-3D icon (~8–11% of column width) with soft shadow\n"
        f"    2) VERY LARGE bold figure in {headline_c} (largest type after the headline)\n"
        f"    3) 1–2 line short label in {body_c}\n"
        "  Icons must be different objects that literally mean their own figure.\n"
        f"ZONE C — SUPPORTING INSIGHTS:\n"
        f"  Small ALL-CAPS label 'SUPPORTING INSIGHTS' + hairline.\n"
        f"  {panel_zone}\n"
        "ZONE D — CLOSE:\n"
        f"  Centred takeaway line in {headline_c}, then bold ALL-CAPS second line in {accent_c}.\n"
        "  Tiny centred source line at the very bottom.\n\n"
        "================= 3. VISUAL STYLE =================\n"
        "Premium consulting-report craft with claymorphic icons — NOT a sparse sample\n"
        "poster that hides the data, NOT flat PowerPoint.\n"
        "3D CRAFT (mandatory on EVERY icon + the hero):\n"
        "- Claymorphic / Octane / Pixar-mini product look: rounded forms, soft SSS,\n"
        "  crisp specular highlights, gentle ambient occlusion, real contact shadows.\n"
        "- Each icon is a miniature you could hold: hourglass, stacked notes, % glyph,\n"
        "  map pin, shield+lock, coins, water drop, recycle, bar chart, wallet, etc.\n"
        "  Pick the object that matches THAT card's meaning — never reuse an icon.\n"
        f"- Materials: glossy {headline_c} and {accent_c}, soft white, Brand Space card {card}\n"
        "  glass. Consistent lighting direction across the whole poster.\n"
        "- Icon scale is SMALL–MEDIUM and consistent (~8–11% of card/column) so TEXT\n"
        "  and numbers stay the hero. Never giant icons that crowd out paragraphs.\n"
        "- FORBIDDEN: flat vector, emoji, line icons, UI chrome, clipart, 2D stickers,\n"
        "  the same icon twice, generic abstract blobs.\n"
        "CARDS: soft translucent panels, rounded ~20px, light hairline border, soft\n"
        "drop shadow, generous inner padding so text never touches the edge.\n"
        "TYPOGRAPHY hierarchy (strict):\n"
        "  1) Huge headline  2) Huge stat figures  3) Medium card titles\n"
        "  4) Neat readable body paragraphs (2–3 complete lines)  5) Tiny source\n"
        "CRITICAL: every string fits fully — never clip, crop, or truncate a word.\n"
        "Bake the BODY paragraphs letter-perfect — they carry the insight.\n\n"
        "================= 4. BRAND STYLE =================\n"
        "Use ONLY these Brand Space hex colours. Do NOT invent tints or another palette.\n"
        f"  primary/headlines {headline_c}\n"
        f"  secondary {secondary_c} — MUST appear as card/panel fills\n"
        f"  accent {accent_c} — CTA, accent rule, key-number emphasis only\n"
        f"  background {bg} · body {body_c} · cards {card} · hairline {hairline}.\n"
        "BACKGROUND: smooth VERTICAL GRADIENT, full-bleed edge to edge —\n"
        f"  top {bg} -> middle {bg} -> bottom {bg}.\n"
        "  NEVER a second page colour. NO border or frame.\n"
        f"PRIMARY TEXT: {headline_c}. SECONDARY FILLS: {secondary_c}. "
        f"ACCENT {accent_c} for the rule, small labels, and the final takeaway line only.\n"
        f"BODY COPY: {body_c}. PANELS: {card} fill, {hairline} border.\n"
        "COLOUR BAN: do not paint navy, orange, gold, teal, or ice-blue unless that\n"
        "exact hex is listed above. Never skip the secondary hex. Never invent a tint\n"
        "of primary for cards or background.\n\n"
        "================= 5. AVOID =================\n"
        "No PowerPoint look, no sparse empty poster that drops the blueprint facts,\n"
        "no giant icons drowning text, no hub-and-spoke diagram, no ranking table,\n"
        "no white logo box, no page frame, no teal/gold/neon, no lorem ipsum, no\n"
        "duplicated headings, no truncated words, no generic slogans replacing data.\n"
        "Result = structured, insight-rich information poster with latest facts.\n"
    )
