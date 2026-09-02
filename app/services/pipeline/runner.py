from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.core.logging import get_logger
from app.graph.checkpoint import (
    get_checkpoint,
    save_checkpoint,
    serialize_state_for_checkpoint,
    update_checkpoint_status,
)
from app.graph.graph import build_phase1_graph, build_phase2_graph
from app.graph.hydrate import hydrate_state
from app.graph.models.layer7c_models import CreativeBlueprint
from app.prompts.layout_router import classify_layout
from app.services.blueprint_quality import finalize_blueprint_for_card
from app.services.copy_proofread import proofread_blueprint
from app.services.cost_tracking.cost_service import estimate_run_cost
from app.services.observability.tracing import layer_span
from app.services.pipeline.progress import astream_graph, emit_progress

logger = get_logger(__name__)


def _attach_cost(state: dict[str, Any]) -> dict[str, Any]:
    cost = estimate_run_cost(state.get("token_usage") or {}, state=state)
    state["total_cost_usd"] = cost["total_cost_usd"]
    state["cost"] = cost
    return cost


async def execute_phase1(run_id: str, request: dict[str, Any]) -> dict[str, Any]:
    """L1→L7c (+ L10 blueprint gate). Writes checkpoint; never raises to the HTTP worker."""
    from app.graph.state import ViolytState
    from app.services.brand_visual_pack import load_brand_visual_pack

    brand_id = str(request.get("brand_id") or "")
    user_prompt = str(request.get("user_prompt") or "")
    platform = str(request.get("platform") or "linkedin")
    fmt = str(request.get("format") or "static")

    initial_state: ViolytState = {
        "user_prompt": user_prompt,
        "brand_id": brand_id,
        "platform": platform,
        "format": fmt,
        "run_id": run_id,
        "repair_count": 0,
    }

    try:
        emit_progress(run_id, event="pipeline_start", message="phase1")
        update_checkpoint_status(run_id, "running")

        visual_pack = await load_brand_visual_pack(brand_id, fmt=fmt, user_prompt=user_prompt)
        initial_state["tenant_id"] = visual_pack.tenant_id
        initial_state["brand_name"] = visual_pack.brand_name
        initial_state["visual_pack"] = visual_pack.to_dict()

        from app.services.pipeline.format_resolution import resolve_pipeline_format

        fmt_in = fmt.strip().lower()
        resolved = resolve_pipeline_format(studio_format=fmt_in, user_prompt=user_prompt)
        chosen_fmt = resolved.format
        layout = classify_layout(user_prompt, chosen_fmt or None)
        # Prefer the layout router's suggestion when Studio was auto / empty.
        if (not fmt_in or fmt_in == "auto") and layout.suggested_format:
            chosen_fmt = layout.suggested_format
        if chosen_fmt != fmt_in or resolved.overridden:
            visual_pack = await load_brand_visual_pack(
                brand_id,
                fmt=chosen_fmt or "",
                user_prompt=user_prompt,
            )
            initial_state["visual_pack"] = visual_pack.to_dict()
        initial_state["format"] = chosen_fmt
        if resolved.warning:
            initial_state["format_warning"] = resolved.warning
        logger.info(
            "pipeline.run.format_resolved",
            layout=layout.layout_type,
            format=chosen_fmt,
            studio_format=resolved.studio_format,
            prompt_format=resolved.prompt_format or None,
            overridden=resolved.overridden,
            warning=resolved.warning or None,
            reason=layout.reason,
        )

        save_checkpoint(run_id, serialize_state_for_checkpoint(dict(initial_state)), status="running")

        with layer_span("phase1", run_id=run_id, brand_id=brand_id):
            graph = build_phase1_graph().compile()
            final_state = await astream_graph(graph, dict(initial_state), run_id)
    except Exception as exc:
        logger.error("pipeline.run.failed", run_id=run_id, error=str(exc), exc_info=True)
        failed = dict(initial_state)
        failed["error"] = str(exc)
        cost = _attach_cost(failed)
        save_checkpoint(
            run_id,
            serialize_state_for_checkpoint(failed),
            status="failed",
            cost=cost,
        )
        emit_progress(run_id, event="pipeline_failed", message=str(exc)[:240])
        return failed

    serialized = serialize_state_for_checkpoint(dict(final_state))
    cost = _attach_cost(serialized)
    error = serialized.get("error")
    isolation_fail = False
    ctx = serialized.get("brand_context") or {}
    if isinstance(ctx, dict) and ctx.get("brand_isolation_status") == "fail":
        isolation_fail = True
        error = error or "Brand isolation failed: no brand data retrieved."
        serialized["error"] = error

    status = "failed" if (error or isolation_fail) else "awaiting_blueprint_approval"
    save_checkpoint(run_id, serialized, status=status, cost=cost)
    emit_progress(
        run_id,
        event="pipeline_complete" if status != "failed" else "pipeline_failed",
        message=status,
    )
    logger.info("pipeline.run.phase1_complete", run_id=run_id, status=status)
    return serialized


async def execute_phase2(run_id: str, creative_blueprint: dict[str, Any] | None) -> dict[str, Any]:
    """Apply approved blueprint and run L8→L9→L10→renderer."""
    raw = get_checkpoint(run_id)
    if not raw:
        raise FileNotFoundError("Pipeline run not found or expired")

    if creative_blueprint is not None:
        bp = CreativeBlueprint.model_validate(creative_blueprint)
        try:
            bp = await proofread_blueprint(bp, use_llm=False)
        except Exception as exc:
            logger.warning("pipeline.approve.proofread_failed", error=str(exc))
        user_prompt = str(raw.get("user_prompt", ""))
        fmt = str(raw.get("format", bp.format or "static"))
        layout = classify_layout(user_prompt, fmt)
        bp = finalize_blueprint_for_card(
            bp,
            layout_type=layout.layout_type,
            user_prompt=user_prompt,
            live_research=raw.get("live_research") or {},
        )
        raw["creative_blueprint"] = bp.model_dump()
    elif raw.get("creative_blueprint"):
        try:
            bp = CreativeBlueprint.model_validate(raw["creative_blueprint"])
            bp = await proofread_blueprint(bp, use_llm=False)
            user_prompt = str(raw.get("user_prompt", ""))
            fmt = str(raw.get("format", bp.format or "static"))
            layout = classify_layout(user_prompt, fmt)
            bp = finalize_blueprint_for_card(
                bp,
                layout_type=layout.layout_type,
                user_prompt=user_prompt,
                live_research=raw.get("live_research") or {},
            )
            raw["creative_blueprint"] = bp.model_dump()
        except Exception as exc:
            logger.warning("pipeline.approve.checkpoint_proofread_failed", error=str(exc))

    if not raw.get("creative_blueprint"):
        raw["error"] = "No creative_blueprint available to approve"
        cost = _attach_cost(raw)
        save_checkpoint(run_id, serialize_state_for_checkpoint(raw), status="failed", cost=cost)
        emit_progress(run_id, event="pipeline_failed", message=raw["error"])
        return raw

    update_checkpoint_status(run_id, "generating")
    emit_progress(run_id, event="pipeline_start", message="phase2")
    save_checkpoint(run_id, serialize_state_for_checkpoint(raw), status="generating")
    state = hydrate_state(raw)

    try:
        with layer_span("phase2", run_id=run_id):
            graph = build_phase2_graph().compile()
            final_state = await astream_graph(graph, dict(state), run_id)
    except Exception as exc:
        logger.error("pipeline.approve.failed", run_id=run_id, error=str(exc), exc_info=True)
        raw["error"] = str(exc)
        cost = _attach_cost(raw)
        save_checkpoint(run_id, serialize_state_for_checkpoint(raw), status="failed", cost=cost)
        emit_progress(run_id, event="pipeline_failed", message=str(exc)[:240])
        return raw

    serialized = serialize_state_for_checkpoint(dict(final_state))
    cost = _attach_cost(serialized)
    status = "failed" if serialized.get("error") else "complete"
    save_checkpoint(run_id, serialized, status=status, cost=cost)
    emit_progress(run_id, event="pipeline_complete", message=status)
    return serialized


def new_run_id() -> str:
    return str(uuid4())
