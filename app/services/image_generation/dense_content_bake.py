from __future__ import annotations

"""Shared dense content bake — used by infographic, static, and carousel.

Goal: blueprint insight (latest / most important facts + so-what paragraphs)
must reach the image, with SMALL icons and clear hierarchy — not sparse sample filler.
"""

import re
from typing import Any

_SAFE = re.compile(r"[^\w\s₹%&.,'\"?!():;\-–/×+]")
_DANGLING = frozenset(
    """a an the and or but that which with for to of in on at by from as is are was were
    its their this these those than when while if into over under per vs about after
    before between during through across""".split()
)


def scrub(text: str, *, max_words: int = 28) -> str:
    t = _SAFE.sub("", str(text or ""))
    t = re.sub(r"\bRs\.?\s*", "₹", t, flags=re.I)
    t = re.sub(r"\bcrore\b", "cr", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    if len(words) > max_words:
        words = words[:max_words]
    while words and words[-1].strip(".,;:").casefold() in _DANGLING:
        words.pop()
    return " ".join(words).strip(" ,;:-–")


def _is_filler(text: str) -> bool:
    t = (text or "").strip().casefold()
    if not t:
        return True
    return bool(
        re.search(
            r"everything you need|need to know|learn more|read more|key insight|"
            r"^item(\s+\d+)?$|lorem ipsum|placeholder",
            t,
        )
    )


DENSE_LAYOUT_LOCK = """
DENSE CONTENT LOCK (infographic / static — carousel uses CAROUSEL_DENSE_LOCK instead):
• Bake the latest and most important verified facts from the blueprint — never replace with generic sample filler.
• Hierarchy: huge headline → large key numbers → medium card titles → neat 2–3 line body paragraphs.
• Icons are SMALL–MEDIUM (~8–11% of card/column height) so TEXT stays the hero.
• Each insight card = SMALL clay-3D icon + TITLE + BODY paragraph (complete sentences).
• Prefer lines with digits / ₹ / % / named schemes. Omit empty slogan cards.
• Never clip mid-word. Never invent statistics not in the COPY block.
• CAROUSEL ONLY: never bake source / survey / institution names (no "Source:", no "(BIS…)").
"""


def extract_dense_cards(
    blueprint: Any,
    *,
    max_cards: int = 8,
) -> list[dict[str, str]]:
    """Pull title/body/stat cards from CreativeBlueprint sections + proof/stats fallback."""
    cards: list[dict[str, str]] = []
    used: set[str] = set()

    def _key(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (s or "").casefold())

    def _add(title: str, body: str, stat: str = "") -> None:
        title_s = scrub(title, max_words=8)
        body_s = scrub(body, max_words=28)
        stat_s = scrub(stat, max_words=8)
        if _is_filler(title_s) and _is_filler(body_s):
            return
        if not body_s and not title_s:
            return
        k = _key(body_s or title_s)
        if k and k in used:
            return
        if k:
            used.add(k)
        cards.append(
            {
                "title": title_s or scrub(body_s, max_words=6),
                "body": body_s or title_s,
                "stat": stat_s,
            }
        )

    for sec in list(getattr(blueprint, "sections", None) or [])[:12]:
        label = str(getattr(sec, "section_label", "") or "").strip()
        body = str(getattr(sec, "body", "") or "").strip()
        stat = str(getattr(sec, "stat", "") or "").strip()
        includes = [str(x).strip() for x in (getattr(sec, "includes", None) or []) if str(x).strip()]
        if not body and includes:
            body = max(includes, key=lambda x: len(x.split()))
        if body and includes and len(body.split()) < 10:
            for inc in includes:
                if _key(inc) not in _key(body):
                    body = scrub(f"{body} {inc}", max_words=28)
                    break
        _add(label, body, stat)
        if len(cards) >= max_cards:
            return cards

    for raw in list(getattr(blueprint, "stat_highlights", None) or [])[:6]:
        if len(cards) >= max_cards:
            break
        text = scrub(str(raw), max_words=20)
        if text and re.search(r"\d|₹|%", text):
            _add(scrub(text, max_words=5), text, "")

    for raw in list(getattr(blueprint, "proof_points", None) or [])[:6]:
        if len(cards) >= max_cards:
            break
        text = scrub(str(raw), max_words=28)
        if text:
            _add(scrub(text, max_words=5), text, "")

    return cards[:max_cards]


def format_dense_cards_block(
    cards: list[dict[str, str]],
    *,
    heading: str = "INSIGHT CARDS (bake every card — title + body paragraph)",
) -> str:
    if not cards:
        return ""
    lines = [f"\n{heading}:\n", DENSE_LAYOUT_LOCK, "\n"]
    for i, card in enumerate(cards, start=1):
        title = card.get("title") or f"Point {i}"
        body = card.get("body") or title
        stat = card.get("stat") or ""
        if stat:
            lines.append(
                f'  CARD {i}: SMALL ICON + STAT "{stat}" + TITLE "{title}" + BODY "{body}"\n'
            )
        else:
            lines.append(
                f'  CARD {i}: SMALL ICON + TITLE "{title}" + BODY "{body}"\n'
            )
    return "".join(lines)


def format_dense_stats_block(blueprint: Any, *, max_stats: int = 6) -> str:
    stats: list[str] = []
    for raw in list(getattr(blueprint, "stat_highlights", None) or []):
        t = scrub(str(raw), max_words=16)
        if t and not _is_filler(t):
            stats.append(t)
        if len(stats) >= max_stats:
            break
    if len(stats) < 3:
        for raw in list(getattr(blueprint, "proof_points", None) or []):
            t = scrub(str(raw), max_words=16)
            if t and re.search(r"\d|₹|%", t) and t not in stats:
                stats.append(t)
            if len(stats) >= max_stats:
                break
    if not stats:
        return ""
    lines = ["\nKEY STATISTICS (latest / most important — bake all):\n"]
    for i, s in enumerate(stats, start=1):
        lines.append(f'  STAT {i}: "{s}"\n')
    return "".join(lines)
