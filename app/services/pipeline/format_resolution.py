"""Resolve studio format vs prompt-named format for pipeline runs.

Demo P0: leftover Studio dropdown (Carousel) while the prompt says Infographic —
or the reverse — produced the wrong creative shape. Policy from the Violyt Demo
Errors fix plan:

1. Explicit Studio Carousel / Infographic usually wins (user intentional pick).
2. When the prompt names a DIFFERENT format, keep Studio but attach a warning.
3. Leftover Studio Static is weak — an explicit prompt format (carousel /
   infographic / static) upgrades it, matching the existing carousel override.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_CAROUSEL_RE = re.compile(
    r"\bcarousels?\b|\bswipe(?:able)?\b|\bmulti[- ]?slide\b", re.I
)
_INFOGRAPHIC_RE = re.compile(r"\binfographics?\b", re.I)
_STATIC_RE = re.compile(r"\bstatic\s+post\b|\bsingle\s+(?:image|post)\b", re.I)


@dataclass(frozen=True)
class FormatResolution:
    format: str
    prompt_format: str
    studio_format: str
    warning: str
    overridden: bool


def detect_prompt_format(user_prompt: str) -> str:
    """Return the format the prompt explicitly names, or '' if none."""
    text = user_prompt or ""
    if _INFOGRAPHIC_RE.search(text):
        return "infographic"
    if _CAROUSEL_RE.search(text):
        return "carousel"
    if _STATIC_RE.search(text):
        return "static"
    return ""


def resolve_pipeline_format(
    *,
    studio_format: str | None,
    user_prompt: str,
) -> FormatResolution:
    """Pick the format that Phase 1 / L8 should run under."""
    studio = (studio_format or "").strip().lower()
    if studio not in ("static", "carousel", "infographic", "auto", ""):
        studio = "static"
    prompt_fmt = detect_prompt_format(user_prompt)

    # Auto / empty → prompt wins when present, else static.
    if not studio or studio == "auto":
        chosen = prompt_fmt or "static"
        return FormatResolution(
            format=chosen,
            prompt_format=prompt_fmt,
            studio_format=studio or "auto",
            warning="",
            overridden=bool(prompt_fmt),
        )

    # Weak Static: an explicit prompt format upgrades it.
    if studio == "static" and prompt_fmt and prompt_fmt != "static":
        return FormatResolution(
            format=prompt_fmt,
            prompt_format=prompt_fmt,
            studio_format=studio,
            warning=(
                f"Studio was Static but the prompt asked for {prompt_fmt.title()} — "
                f"using {prompt_fmt.title()}."
            ),
            overridden=True,
        )

    # Explicit Studio Carousel/Infographic wins; warn on conflict.
    if prompt_fmt and prompt_fmt != studio:
        return FormatResolution(
            format=studio,
            prompt_format=prompt_fmt,
            studio_format=studio,
            warning=(
                f"Studio format is {studio.title()} but the prompt mentions "
                f"{prompt_fmt.title()} — keeping Studio {studio.title()}. "
                f"Change Studio or the prompt so they match."
            ),
            overridden=False,
        )

    return FormatResolution(
        format=studio,
        prompt_format=prompt_fmt,
        studio_format=studio,
        warning="",
        overridden=False,
    )
