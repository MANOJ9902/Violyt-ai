"""Pick a Brand Space reference/template for image generation.

SaaS rule: layout DNA comes from THIS brand's uploaded references, never from
hardcoded sample posters (airports, RBI plastic, oil bars, Jiraaf carousels).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_FORMATS = ("carousel", "infographic", "static")
_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")

_FORMAT_HINTS: dict[str, tuple[str, ...]] = {
    "carousel": ("carousel", "swipe", "slide", "deck", "multi-slide", "multislide"),
    "infographic": ("infographic", "explainer", "poster", "data story", "one-pager"),
    "static": ("static", "single post", "feed post", "linkedin post", "banner"),
}

# Brand Space fields that hold layout references / templates for image gen.
REFERENCE_FIELD_KEYS = (
    "reference_creatives",
    "mood_board",
    "brand_knowledge_templates",
    "brand_knowledge_other",
)


def _as_dict(item: Any) -> dict[str, Any]:
    return item if isinstance(item, dict) else {}


def _text_blob(item: dict[str, Any]) -> str:
    bits = [
        item.get("name"),
        item.get("label"),
        item.get("kind"),
        item.get("template_kind"),
        item.get("templateKind"),
        item.get("format"),
        item.get("role"),
        item.get("asset_category"),
        item.get("original_filename"),
        item.get("filename"),
        item.get("field_key"),
        " ".join(str(t) for t in (item.get("tags") or []) if t),
    ]
    return " ".join(str(b) for b in bits if b).casefold()


def infer_template_format(item: dict[str, Any]) -> str:
    blob = _text_blob(item)
    for fmt, hints in _FORMAT_HINTS.items():
        if any(h in blob for h in hints):
            return fmt
    return ""


def resolve_reference_preview_path(storage_path: str) -> str:
    """Prefer an OCR page PNG for PDFs so images.edit can learn the layout."""
    path = str(storage_path or "").strip().replace("\\", "/")
    if not path:
        return ""
    lower = path.casefold()
    if lower.endswith(_IMAGE_SUFFIXES):
        return path
    try:
        from app.integrations.object_storage import get_object_storage

        storage = get_object_storage()
        absolute = Path(storage.absolute_path(path))
        stem = absolute.stem
        ocr_root = absolute.parent / "_ocr"
        if not ocr_root.is_dir():
            return path
        page1_candidates: list[Path] = []
        for child in ocr_root.iterdir():
            if not child.is_dir():
                continue
            # OCR folders are typically "<stem>-<hash>"
            if child.name == stem or child.name.startswith(f"{stem}-"):
                page1 = child / "page_images" / "page_1.png"
                if page1.is_file():
                    page1_candidates.append(page1)
        if not page1_candidates:
            page1_candidates = sorted(ocr_root.glob("*/page_images/page_1.png"))
        if not page1_candidates:
            return path
        base = Path(getattr(storage, "base_path", "") or "")
        chosen = page1_candidates[0]
        if base and str(base) and chosen.is_relative_to(base):
            return chosen.relative_to(base).as_posix()
        return str(chosen)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "reference_template.preview_resolve_failed",
            error=str(exc)[:200],
            path=path[:120],
        )
        return path


def _reference_record(rec: dict[str, Any]) -> dict[str, str] | None:
    path = str(
        rec.get("storage_path")
        or rec.get("storagePath")
        or rec.get("path")
        or rec.get("preview_path")
        or rec.get("previewPath")
        or ""
    ).strip()
    url = str(rec.get("url") or rec.get("asset_url") or rec.get("assetUrl") or "").strip()
    asset_id = str(rec.get("asset_id") or rec.get("id") or "").strip()
    name = str(
        rec.get("name")
        or rec.get("label")
        or rec.get("filename")
        or rec.get("original_filename")
        or "Reference"
    ).strip()
    if path:
        path = resolve_reference_preview_path(path)
    # images.edit needs a readable image/file path or URL — asset_id alone is not enough.
    if not path and not url:
        return None
    key = path or url
    if not key:
        return None
    fmt = infer_template_format(rec) or infer_template_format({"name": name})
    return {
        "name": name[:120],
        "storage_path": path,
        "url": url,
        "format": fmt,
        "kind": str(
            rec.get("kind")
            or rec.get("template_kind")
            or rec.get("templateKind")
            or rec.get("field_key")
            or ""
        ),
        "asset_id": asset_id,
    }


def extract_brand_references(
    *,
    visual_identity: dict[str, Any] | None = None,
    knowledge: dict[str, Any] | None = None,
    prompt_intelligence: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Collect image-capable Brand Space references + templates (this brand only)."""
    visual = visual_identity or {}
    knowledge = knowledge or {}
    pi = prompt_intelligence or {}
    raw: list[Any] = []
    for bucket in (
        visual.get("reference_creatives"),
        visual.get("referenceCreatives"),
        knowledge.get("template_files"),
        knowledge.get("templateFiles"),
        (pi.get("platform_rules") or {}).get("recommended_templates")
        if isinstance(pi.get("platform_rules"), dict)
        else None,
    ):
        if isinstance(bucket, list):
            raw.extend(bucket)

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        record = _reference_record(_as_dict(item))
        if not record:
            continue
        key = record.get("storage_path") or record.get("url") or record.get("asset_id") or ""
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(record)
    return out


def merge_reference_lists(*groups: list[dict[str, str]]) -> list[dict[str, str]]:
    """Dedupe reference lists while preserving first-seen order."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for group in groups:
        for item in group or []:
            key = item.get("storage_path") or item.get("url") or item.get("asset_id") or item.get("name") or ""
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


def select_reference_template(
    references: list[dict[str, str]],
    *,
    fmt: str = "",
    user_prompt: str = "",
) -> dict[str, str]:
    """Choose the Brand Space template that matches Studio format + prompt."""
    if not references:
        return {}
    wanted = (fmt or "").strip().casefold()
    if wanted not in _FORMATS:
        wanted = ""
    prompt = (user_prompt or "").casefold()
    if not wanted:
        for f, hints in _FORMAT_HINTS.items():
            if any(re.search(rf"\b{re.escape(h)}\b", prompt) for h in hints):
                wanted = f
                break

    same_fmt = [r for r in references if r.get("format") == wanted] if wanted else []
    pool = same_fmt or list(references)

    def score(item: dict[str, str]) -> int:
        blob = " ".join(item.get(k, "") for k in ("name", "kind", "format")).casefold()
        n = 0
        if wanted and item.get("format") == wanted:
            n += 10
        for word in prompt.split():
            if len(word) > 4 and word in blob:
                n += 2
        if item.get("storage_path", "").casefold().endswith(_IMAGE_SUFFIXES):
            n += 3
        elif item.get("storage_path"):
            n += 1
        return n

    chosen = max(pool, key=score)
    if chosen.get("storage_path"):
        chosen = {
            **chosen,
            "storage_path": resolve_reference_preview_path(chosen["storage_path"]),
        }
    logger.info(
        "reference_template.selected",
        name=chosen.get("name"),
        format=chosen.get("format") or wanted or None,
        wanted=wanted or None,
        candidates=len(references),
        matched_format=len(same_fmt),
        storage_path=(chosen.get("storage_path") or "")[:160],
        prompt_snippet=(user_prompt or "")[:120],
    )
    return chosen


def template_follow_lock(selected: dict[str, str] | None, *, fmt: str = "") -> str:
    """Prompt lock: learn layout from the Brand Space reference, invent nothing else."""
    name = (selected or {}).get("name") or "the Brand Space reference"
    fmt_label = (fmt or "this format").strip() or "this format"
    return (
        f"LAYOUT SOURCE: follow the uploaded Brand Space reference “{name}” for {fmt_label}. "
        "Copy its structure, spacing, card pattern, icon style, and hierarchy. "
        "Do NOT invent a different brand logo. NEVER draw ANY logo, icon, or brand mark in the top-right — "
        "no Cognixia C, no watermark, no navy logo plate. Leave that corner empty for exact Brand Space logo compositing. "
        "KEEP the reference's background treatment and accent colors (do not wash the page to plain white). "
        "Replace only the TEXT with the COPY TO BAKE block. "
        "Do NOT copy another brand's look, and do NOT fall back to any built-in sample poster. "
        "If a detail is not in this brand's Brand Space, web research for this brand, "
        "or this brand's vector store, omit it. "
        "TEXT QUALITY: letter-perfect spelling; complete words; never cut off mid-word."
    )
