from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# USD per 1M tokens when a layer's model family is known.
_MODEL_RATES: dict[str, tuple[float, float]] = {
    "claude": (3.00, 15.00),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "embeddings": (0.13, 0.0),
}

_LAYER_FAMILY: dict[str, str] = {
    "l1_brand_retrieval": "embeddings",
    "l1_retrieval": "embeddings",
    "l2_brand_intelligence": "claude",
    "l4_strategic_reasoning": "claude",
    "l5_concept_engine": "claude",
    "l5_creative_concepts": "claude",
    "l6b_content_intelligence": "claude",
    "l10_evaluation": "claude",
    "repair": "claude",
    "l3_brief_interpreter": "gpt-4o-mini",
    "l6_format_engine": "gpt-4o-mini",
    "l6_format_plan": "gpt-4o-mini",
    "l7_copy_engine": "gpt-4o-mini",
    "l7b_content_validator": "gpt-4o-mini",
    "l7c_content_prep": "gpt-4o-mini",
    "l8_visual_reasoning": "gpt-4o-mini",
    "l9_scene_graph": "gpt-4o-mini",
}


def _rates_for_layer(layer: str, settings: Any) -> tuple[float, float]:
    family = _LAYER_FAMILY.get(layer, "")
    if family in _MODEL_RATES:
        return _MODEL_RATES[family]
    return (
        float(settings.cost_estimation_text_input_usd_per_million or 0.40),
        float(settings.cost_estimation_text_output_usd_per_million or 1.60),
    )


def _image_count(state: dict[str, Any] | None) -> int:
    if not state:
        return 0
    visual = state.get("visual_reasoning") or {}
    if not isinstance(visual, dict) and hasattr(visual, "model_dump"):
        visual = visual.model_dump()
    if not isinstance(visual, dict):
        return 0
    urls = [u for u in (visual.get("generated_image_urls") or []) if u]
    extra = visual.get("generated_image_url")
    if extra and extra not in urls:
        urls.insert(0, extra)
    return len(urls)


def estimate_run_cost(
    token_usage: dict[str, Any] | None,
    *,
    state: dict[str, Any] | None = None,
    image_count: int | None = None,
) -> dict[str, Any]:
    """Compute USD cost from per-layer token_usage plus generated image count."""
    settings = get_settings()
    usage = token_usage or {}
    layers: list[dict[str, Any]] = []
    text_usd = 0.0
    in_tokens = 0
    out_tokens = 0

    for layer, raw in usage.items():
        if not isinstance(raw, dict):
            continue
        inp = int(raw.get("input_tokens") or 0)
        out = int(raw.get("output_tokens") or 0)
        in_rate, out_rate = _rates_for_layer(layer, settings)
        usd = (inp / 1_000_000) * in_rate + (out / 1_000_000) * out_rate
        text_usd += usd
        in_tokens += inp
        out_tokens += out
        layers.append(
            {
                "layer": layer,
                "input_tokens": inp,
                "output_tokens": out,
                "usd": round(usd, 6),
            }
        )

    n_images = image_count if image_count is not None else _image_count(state)
    per_image = float(settings.cost_estimation_image_generation_usd_per_call or 0.0)
    if per_image <= 0:
        per_image = 0.04
    image_usd = n_images * per_image
    total = round(text_usd + image_usd, 6)

    payload = {
        "total_cost_usd": total,
        "text_cost_usd": round(text_usd, 6),
        "image_cost_usd": round(image_usd, 6),
        "image_count": n_images,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "layers": layers,
    }
    logger.info("cost.estimated", total_cost_usd=total, image_count=n_images)
    return payload
