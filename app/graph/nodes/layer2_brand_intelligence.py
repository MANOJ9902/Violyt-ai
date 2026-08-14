from __future__ import annotations

from app.core.logging import get_logger
from app.graph.models.layer2_models import BrandIntelligenceOutput
from app.graph.state import ViolytState
from app.prompts.layer2_brand_intelligence import BrandIntelligencePromptBuilder
from app.services.cache.brand_cache import BrandCacheService
from app.services.llm.claude_service import ClaudeService

logger = get_logger(__name__)

_claude_service = ClaudeService()
_brand_cache = BrandCacheService()
_prompt_builder = BrandIntelligencePromptBuilder()


async def _brand_space_name(brand_id: str) -> str:
    """Authoritative brand name from the Brand Space row."""
    from uuid import UUID

    from app.db.session import AsyncSessionLocal
    from app.models.brand import BrandSpace

    try:
        brand_uuid = brand_id if isinstance(brand_id, UUID) else UUID(str(brand_id))
        async with AsyncSessionLocal() as session:
            row = await session.get(BrandSpace, brand_uuid)
            return (getattr(row, "name", "") or "").strip() if row else ""
    except Exception as exc:  # noqa: BLE001 - name is a best-effort enrichment
        logger.warning("brand_intelligence.name_lookup_failed", error=str(exc)[:120])
        return ""


def _is_placeholder_name(name: str) -> bool:
    text = (name or "").strip().casefold()
    return not text or text.startswith("unknown") or "brand id" in text


def _apply_brand_space_name(output: BrandIntelligenceOutput, brand_space_name: str):
    """Force the Brand Space name onto the model output.

    The LLM invents placeholders like "Unknown — Brand ID 7fe7bd57" when the
    retrieved chunks are ambiguous. Downstream layers switch entire visual
    systems on this string, so it must never be guessed.
    """
    if not brand_space_name:
        return output
    core = getattr(output, "brand_core", None)
    if core is None:
        return output
    current = getattr(core, "brand_name", "") or ""
    if current.strip() == brand_space_name:
        return output
    if _is_placeholder_name(current):
        logger.info(
            "brand_intelligence.brand_name_recovered",
            llm_name=current[:60],
            brand_space_name=brand_space_name,
        )
    core.brand_name = brand_space_name
    return output


async def layer2_brand_intelligence(state: ViolytState) -> dict:
    brand_id = state.get("brand_id", "unknown")
    brand_context = state.get("brand_context")
    data_version: int = state.get("data_version") or 1  # set by L1 from brand.data_version in DB

    # Try cache first — key includes data_version so re-indexing the brand auto-invalidates.
    brand_space_name = await _brand_space_name(brand_id)

    cached = await _brand_cache.get(brand_id, data_version=data_version)
    if cached:
        logger.info("brand_intelligence.cache_hit", brand_id=brand_id, data_version=data_version)
        # Correct entries cached before the name was pinned to the Brand Space.
        return {"brand_intelligence": _apply_brand_space_name(cached, brand_space_name)}

    if not brand_context:
        logger.error("brand_intelligence.no_context", brand_id=brand_id)
        raise ValueError("Layer 1 brand_context is required for Layer 2")

    system = _prompt_builder.build_system()
    user = _prompt_builder.build_user(
        brand_id=brand_id,
        high_context=brand_context.high_relevance_context,
        medium_context=brand_context.medium_relevance_context,
        weak_signals=brand_context.missing_context,
        brand_name=brand_space_name,
    )

    output, metadata = await _claude_service.complete_structured(
        system=system,
        user=user,
        output_model=BrandIntelligenceOutput,
        layer="l2_brand_intelligence",
        max_tokens=8192,
    )

    output = _apply_brand_space_name(output, brand_space_name)
    await _brand_cache.set(brand_id, output, data_version=data_version)

    return {
        "brand_intelligence": output,
        "layer_latencies": {"l2_brand_intelligence": metadata["latency_ms"]},
        "token_usage": {
            "l2_brand_intelligence": {
                "input_tokens": metadata["input_tokens"],
                "output_tokens": metadata["output_tokens"],
            }
        },
    }
