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
# Units are longest-first and must not be followed by another letter, otherwise
# the "T" branch matched the "t" inside "trillion" and split it into "46 t"/"rillion".
_LEADING_FIGURE = re.compile(
    r"^\s*((?:No\.?\s*)?[₹$€£]?\d[\d,]*(?:\.\d+)?\s*"
    r"(?:TRILLION|BILLION|MILLION|CRORE|LAKH|MN|BN|CR|%|X|K|T|L)?(?![A-Za-z])\+?)\s*(.*)$",
    re.IGNORECASE,
)
# A label that is really the tail of a chopped unit word ("rillion" from "trillion").
_BROKEN_UNIT_TAIL = re.compile(
    r"^(?:r?illion|illion|rore|akh|n|x|%)\b", re.IGNORECASE
)
_TOKEN_WITH_DIGIT = re.compile(r"^[₹$€£]?[\w./\-]*\d[\w%+./\-]*$")


# Words that must never end a rendered string — "connect Tiers2 and" was a
# word-count truncation landing mid-clause and getting baked into artwork.
_DANGLING = frozenset(
    """a an the and or but that which with for to of in on at by from as is are was were
    its their this these those than when while if into over under per vs about after
    before between during through across beyond within toward towards upon""".split()
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
        # A chopped unit tail means the figure lost its unit — never bake the fragment.
        if _BROKEN_UNIT_TAIL.match(label):
            label = _scrub(
                " ".join(label.split()[1:]), max_words=8
            )
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


def _headline_lines(headline: str, *, max_per_line: int = 18) -> list[str]:
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


# The brief text itself leaks into section labels upstream ("a clean : Why" came
# straight out of "Create a clean LinkedIn infographic: Why bond markets ...").
_BRIEF_SCAFFOLD = re.compile(
    r"^(?:a|an|the)\s+(?:clean|simple|premium|modern|short|neat)\b"
    r"|^(?:create|design|make|build|generate|write)\b"
    r"|\bno filler\b|\bshort cta\b|\buse \d+\s+(?:key|short)\b",
    re.I,
)

# Raw research dumps arrive in `stat` as markdown ("### Why ... 1. **Key Stats**:").
# Clipping them to six words produced a fake card title, so reject the raw string.
_PROSE_DUMP = re.compile(
    r"###|\*\*|^\s*\d+\.\s+\*|\bkey stats?\b|\bseveral reasons\b|\binsight\b\s*:",
    re.I,
)

# A real stat is a short numeric token, not a sentence.
_STAT_MAX_WORDS = 6


def _looks_like_stat(raw: str) -> bool:
    """True only for short numeric stat tokens — never for a research paragraph."""
    t = " ".join(str(raw or "").split())
    if not t or _PROSE_DUMP.search(t):
        return False
    if not re.search(r"\d", t):
        return False
    return len(t.split()) <= _STAT_MAX_WORDS


def _lead_clause(text: str, *, max_words: int = 8) -> str:
    """First complete clause of a sentence, so derived titles never stop mid-phrase.

    A plain word clip gave "Bond markets connect investors to real-economy"; cutting at
    the comma yields the whole clause instead.
    """
    first = re.split(r"[,;:—–]| - ", str(text or ""), maxsplit=1)[0]
    clause = _scrub(first, max_words=max_words)
    return clause or _scrub(text, max_words=max_words)


def _pair(card_title: str, card_body: str) -> tuple[str, str]:
    """Collapse a card to one string when title and body carry the same idea.

    The old check only caught an exact match, so a title that was a *prefix* of its
    body still baked twice ("Bond markets connect investors to real-economy" above
    "Bond markets connect investors to real-economy financing"). When either string
    contains the other the section holds a single idea, so render it once as a short
    title and leave the body empty.
    """
    title, body = (card_title or "").strip(), (card_body or "").strip()
    if not body:
        return title, ""
    if not title:
        return _lead_clause(body), ""
    nt, nb = _norm(title), _norm(body)
    if nt and nb and (nt in nb or nb in nt):
        # Keep the editorial label: it is a complete phrase, whereas clipping the
        # longer body to fit a title left danglers like "... and economic".
        return title, ""
    return title, body


def _is_placeholder(text: str) -> bool:
    """Reject our own scaffolding and numbered stubs before they reach the canvas."""
    t = (text or "").strip().casefold()
    if not t:
        return True
    if re.search(r"\b(rationale|point|item|reason|section|beat)\s*\d+\s*$", t):
        return True
    if _BRIEF_SCAFFOLD.search(t):
        return True
    if _PROSE_DUMP.search(t):
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
            # Editorial direction that the copy engine emits instead of real copy.
            "use as proof",
            "then explain implication",
            "quantifies scale of change",
            "so-what",
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
        max_words=9,
    ).upper()
    # Reads as an ALL-CAPS pill in the hero, so keep it tagline-short and unpunctuated.
    subhead = _lead_clause(
        getattr(blueprint, "supporting_line", None) or supporting or "", max_words=8
    ).rstrip(".")
    source_footer = _scrub(getattr(blueprint, "source_footer", None) or "", max_words=20)
    closing = _scrub(getattr(blueprint, "customer_quote", None) or "", max_words=22)
    cta = _scrub(getattr(blueprint, "cta", None) or "", max_words=12)
    # Extra slots the reference template needs: a hero intro paragraph and the
    # rationale card that sits between the hero and the reason grid.
    intro = _scrub(getattr(blueprint, "body", None) or "", max_words=20)
    context_body = _scrub(
        getattr(blueprint, "solution_statement", None)
        or getattr(blueprint, "problem_statement", None)
        or "",
        max_words=22,
    )
    if _is_placeholder(intro):
        intro = ""
    if _is_placeholder(context_body):
        context_body = ""
    # Never print the same sentence in the hero and the rationale card.
    if context_body and intro and (_norm(context_body) in _norm(intro) or _norm(intro) in _norm(context_body)):
        context_body = ""
    if intro and subhead and (_norm(intro) in _norm(subhead) or _norm(subhead) in _norm(intro)):
        intro = ""

    # Thin research makes the copy engine reuse one fact across every slot, which
    # renders as a poster that repeats itself. Track what has been used and show
    # each fact at most once, even if that means fewer slots.
    used_figures: set[str] = set()
    used_text: set[str] = set()

    # Cards that re-open with the headline's own words read as repetition on the
    # poster ("Why bond markets ..." twice), so block that lead-in explicitly.
    _headline_lead = " ".join(_norm(headline).split()[:3])

    def _echoes_headline(text: str) -> bool:
        if not _headline_lead:
            return False
        return " ".join(_norm(text).split()[:3]) == _headline_lead

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
        raw_label = str(getattr(sec, "section_label", None) or "")
        raw_body = str(getattr(sec, "body", None) or "")
        raw_stat = str(getattr(sec, "stat", None) or "")
        label = "" if _is_placeholder(raw_label) else _scrub(raw_label, max_words=7)
        # Cards hold ~2 short lines. 16 words overflowed and baked "mech-" / "depte".
        body = "" if _is_placeholder(raw_body) else _scrub(raw_body, max_words=10)
        # Only a genuine short numeric token may drive the card's figure.
        stat = _scrub(raw_stat, max_words=_STAT_MAX_WORDS) if _looks_like_stat(raw_stat) else ""
        includes = [
            str(x) for x in (getattr(sec, "includes", None) or []) if str(x).strip()
        ]
        if not label and not body:
            continue
        if not body and includes:
            # Prefer the longest include so we keep the insightful sentence, not a chip.
            best = max(includes, key=lambda x: len(str(x).split()))
            body = _scrub(best, max_words=10)
        if _is_placeholder(body):
            body = ""
        title = label or _lead_clause(body)
        # Never let a card restate the headline's opening words.
        if _echoes_headline(title):
            alt = _lead_clause(body)
            title = alt if alt and not _echoes_headline(alt) else ""
        if _echoes_headline(body):
            body = ""
        if not title and not body:
            continue
        if stat:
            if _claim(stat, title or body):
                t, b = _pair(title, body)
                numbered.append((stat, t, b))
        elif label or body:
            figure, rest = split_stat(label or body)
            if figure:
                if _claim(figure, rest or body):
                    t, b = _pair(rest or title, body)
                    numbered.append((figure, t, b))
            else:
                if (title or body) and _claim("", body or title):
                    t, b = _pair(title, body)
                    reasons.append((t, b))
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
    # Reason grid — numbered clay-3D cards under a solid section band (template DNA).
    grid_cards: list[str] = []
    for i, (num, lab, body) in enumerate(numbered, start=1):
        body_part = f' + BODY "{body}"' if body else " (title only — bake NO body line)"
        grid_cards.append(
            f'  CARD{i}: 3D ICON + NUMBER "{num}" + TITLE "{lab}"{body_part}'
        )
    for i, (title, body) in enumerate(reasons, start=len(grid_cards) + 1):
        body_part = f' + BODY "{body}"' if body else " (title only — bake NO body line)"
        grid_cards.append(f'  CARD{i}: 3D ICON + TITLE "{title}"{body_part}')
    grid_block = "\n".join(grid_cards) or "  (omit the reason grid entirely)"

    n_cards = len(grid_cards)
    cols = 4 if n_cards >= 7 else 3 if n_cards >= 5 else 2 if n_cards >= 3 else max(n_cards, 1)
    rows = -(-n_cards // cols) if n_cards else 0
    band_title = "TOP REASONS" if headline.startswith("WHY") else "KEY INSIGHTS"

    headline_block = "\n".join(
        f'  LINE{i}: "{line}"' for i, line in enumerate(_headline_lines(headline), start=1)
    )
    n_hero = len(hero) or 4

    return (
        "Create a PREMIUM editorial infographic poster in the style of a top-tier explainer\n"
        "one-pager: claymorphic 3D icons, strong type hierarchy, banded sections, rounded\n"
        f"cards, generous whitespace. Portrait {canvas_desc}, ultra HD.\n\n"
        "================= 1. COPY TO BAKE (letter-perfect, COMPLETE) =================\n"
        "Render ONLY the strings below. No invented labels, no filler, no extra sentences.\n"
        "Every word must appear in full — never drop a leading letter, never cut a line short.\n"
        "HEADLINE (max 3 lines):\n"
        f"{headline_block}\n"
        + (f'ACCENT PILL (ALL-CAPS, max 2 lines): "{subhead}"\n' if subhead else "")
        + (f'HERO INTRO (2-3 complete lines): "{intro}"\n' if intro else "")
        + (f'RATIONALE CARD BODY (2-3 complete lines): "{context_body}"\n' if context_body else "")
        + "KEY STATISTICS (stat strip):\n"
        f"{hero_block}\n"
        f'SECTION BAND TITLE (ALL-CAPS): "{band_title}"\n'
        "REASON GRID CARDS:\n"
        f"{grid_block}\n"
        + (f'FOOTER BAND LINE (one complete line): "{closing}"\n' if closing else "")
        + (f'SOURCE LINE (tiny): "{source_footer}"\n' if source_footer else "")
        + "Bake ALL listed stats and cards. Each card BODY is a DIFFERENT sentence and must\n"
        "never repeat its own title. Where a card is marked 'title only', bake the title and\n"
        "NOTHING else in that card — do not invent a body line to fill space.\n"
        f'Do NOT bake the CTA "{cta or "Explore More"}" anywhere — it is composited in post.\n\n'
        "================= 2. LAYOUT (top to bottom, banded) =================\n"
        "MARGINS: >=7% inset left/right/top. BOTTOM >=14% COMPLETELY EMPTY page background\n"
        "  below the LAST baked element — the CTA is composited there in post. Nothing may\n"
        "  sit in that bottom strip; scale every zone up the page so nothing is clipped.\n"
        f"ZONE A HERO (~24% height): LEFT ~55% = huge bold ALL-CAPS headline in {headline_c}\n"
        f"  (max 3 COMPLETE lines), then a rounded {accent_c} PILL (~8px radius) holding the\n"
        "  ACCENT PILL text in bold ALL-CAPS white, then the HERO INTRO paragraph in\n"
        f"  {body_c}. RIGHT ~40% = ONE large claymorphic 3D hero illustration on a soft\n"
        f"  {card} rounded platform (no text inside it).\n"
        f"  TOP-RIGHT ~24%x12% pocket COMPLETELY BLANK {bg} — logo composited later,\n"
        "  no white plate, no platform mark, no wordmark.\n"
        f"ZONE B RATIONALE CARD (~12%): ONE full-width soft rounded card filled {card}\n"
        "  (radius ~24px, hairline border, soft shadow): circular clay-3D icon badge on the\n"
        f"  LEFT, bold ALL-CAPS title in {headline_c}, then the RATIONALE CARD BODY in\n"
        f"  {body_c}; one small round 3D badge far right. Skip this zone if no body given.\n"
        f"ZONE C STAT STRIP (~10%): small ALL-CAPS label 'KEY STATISTICS' in {headline_c} +\n"
        f"  hairline {hairline}, then {n_hero} equal columns, NO boxes. Each column: small\n"
        f"  clay-3D icon (~8-11%), VERY LARGE figure in {headline_c}, then a 1-2 line COMPLETE\n"
        f"  label in {body_c}. A different icon per figure.\n"
        f"ZONE D SECTION BAND (~5%): full-width SOLID {headline_c} band, rounded ~12px,\n"
        "  spanning the content width. Centred SECTION BAND TITLE in bold ALL-CAPS WHITE,\n"
        f"  flanked left and right by short {accent_c} dashes. This band is a SECTION HEADER\n"
        "  strip only — it is NOT the page background and must not touch the canvas edges.\n"
        f"ZONE E REASON GRID (~30%): the {n_cards} REASON GRID CARDS in a tidy\n"
        f"  {cols}-column x {rows}-row grid on the {bg} page. Each cell: ONE distinct\n"
        f"  claymorphic 3D icon centred on top (~10-13% of cell), then the NUMBER in {accent_c}\n"
        f"  + bold ALL-CAPS TITLE in {headline_c}, then the BODY in {body_c} (max 3 COMPLETE\n"
        f"  lines). Separate cells with thin {hairline} vertical + horizontal rules. Equal cell\n"
        "  height, equal padding (>=14px), perfect column alignment. Bake EVERY card.\n"
        f"ZONE F FOOTER BAND: full-width SOLID {headline_c} rounded band (~6% height) holding a\n"
        f"  small {accent_c} clay-3D icon + the FOOTER BAND LINE in WHITE, one COMPLETE line,\n"
        "  centred. Tiny SOURCE LINE beneath it. Both must sit ABOVE the empty bottom 14%.\n\n"
        "================= 3. VISUAL STYLE =================\n"
        "Consulting-report craft, NOT flat PowerPoint, NOT a sparse poster hiding the data.\n"
        "Every icon + hero: claymorphic Octane look — rounded forms, soft SSS, crisp highlights,\n"
        "ambient occlusion, real contact shadows. Each icon is a distinct miniature matching its\n"
        "own card's meaning (hourglass, coins, % glyph, map pin, shield, bar chart...).\n"
        f"Materials: glossy {headline_c} and {accent_c} on Brand Space card {card}. Consistent light.\n"
        "Grid icons stay SMALL-MEDIUM (~10-13%) so text and numbers remain the hero; only the\n"
        "ZONE A hero illustration is large.\n"
        "FORBIDDEN: flat vector, emoji, line icons, clipart, 2D stickers, repeated icons, blobs.\n"
        "CARDS: soft panels, rounded ~20px, hairline border, soft shadow, generous inner padding.\n"
        "TYPE ORDER: huge headline > stat figures > card titles > body lines > tiny source.\n\n"
        "================= 4. BRAND STYLE =================\n"
        f"Brand Space hexes only: headlines {headline_c} (also the ONLY fill allowed for the two\n"
        f"solid section/footer BANDS), secondary {secondary_c} and {card} as card/panel fills,\n"
        f"accent {accent_c} for the pill, numbers, dashes and rules, body {body_c},\n"
        f"hairline {hairline}. Text on a {headline_c} band is WHITE.\n"
        f"PAGE BACKGROUND: SOLID full-bleed {bg} edge to edge behind every zone — the section\n"
        "  and footer bands are inset strips ON that page, never a second page colour, never a\n"
        "  full-bleed dark header, never a page frame. Never invent a tint for cards or canvas.\n\n"
        "================= 5. AVOID =================\n"
        "No platform logos or chrome, no white logo box, no PowerPoint look, no hub-and-spoke\n"
        "diagram, no ranking table, no page frame, no teal/gold/neon, no lorem ipsum, no\n"
        "duplicated headings, no truncated words (e.g. 'rillion' for 'trillion'), no mid-card\n"
        "cutoffs, no text overlapping a band edge, no baked CTA button, no generic slogans\n"
        "replacing data.\n"
    )
