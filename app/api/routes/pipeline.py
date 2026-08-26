from __future__ import annotations

import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.graph.checkpoint import (
    delete_checkpoint,
    fail_if_stale,
    get_checkpoint,
    get_checkpoint_record,
    save_checkpoint,
    serialize_state_for_checkpoint,
    update_checkpoint_status,
)
from app.graph.hydrate import hydrate_state
from app.schemas.pipeline import (
    PipelineApproveRequest,
    PipelineEditImageTextRequest,
    PipelineEditImageTextResponse,
    PipelineProgressEvent,
    PipelineRejectRequest,
    PipelineRunRequest,
    PipelineRunResponse,
)
from app.services.image_text_edit import apply_text_edits
from app.services.pipeline.progress import TERMINAL_STATUSES
from app.services.pipeline.runner import execute_phase1, execute_phase2

logger = get_logger(__name__)

router = APIRouter(tags=["pipeline"])


def _dump(obj):
    return obj.model_dump() if hasattr(obj, "model_dump") else obj


def _hydrate_state(raw: dict):
    return hydrate_state(raw)


def _response_from_state(
    *,
    run_id: str,
    status: str,
    request_brand_id: str,
    request_prompt: str,
    request_platform: str,
    request_format: str,
    state: dict,
    error: str | None = None,
    cost: dict | None = None,
    events: list | None = None,
) -> PipelineRunResponse:
    progress = None
    if events:
        last = events[-1]
        try:
            progress = PipelineProgressEvent.model_validate(last)
        except Exception:
            progress = None
    total_cost = None
    if isinstance(cost, dict):
        total_cost = cost.get("total_cost_usd")
    elif state.get("total_cost_usd") is not None:
        total_cost = state.get("total_cost_usd")
    return PipelineRunResponse(
        run_id=run_id,
        status=status,
        brand_id=request_brand_id or state.get("brand_id", ""),
        user_prompt=request_prompt or state.get("user_prompt", ""),
        platform=request_platform or state.get("platform", "linkedin"),
        format=request_format or state.get("format", "static"),
        format_warning=(str(state.get("format_warning") or "").strip() or None),
        brand_context=_dump(state.get("brand_context")),
        brand_intelligence=_dump(state.get("brand_intelligence")),
        campaign_brief=_dump(state.get("campaign_brief")),
        strategic_reasoning=_dump(state.get("strategic_reasoning")),
        creative_concepts=_dump(state.get("creative_concepts")),
        format_plan=_dump(state.get("format_plan")),
        content_intelligence=_dump(state.get("content_intelligence")),
        copy=_dump(state.get("copy")),
        content_validation=_dump(state.get("content_validation")),
        creative_blueprint=_dump(state.get("creative_blueprint")),
        visual_reasoning=_dump(state.get("visual_reasoning")),
        scene_graph=_dump(state.get("scene_graph")),
        evaluation=_dump(state.get("evaluation")),
        final_output=state.get("final_output"),
        layer_latencies=state.get("layer_latencies"),
        token_usage=state.get("token_usage"),
        total_cost_usd=total_cost,
        cost=cost or state.get("cost"),
        progress=progress,
        progress_events=events,
        error=error or state.get("error"),
    )


def _response_from_record(run_id: str, rec: dict) -> PipelineRunResponse:
    state = rec.get("state") or {}
    return _response_from_state(
        run_id=run_id,
        status=str(rec.get("status") or "pending"),
        request_brand_id=str(state.get("brand_id", "")),
        request_prompt=str(state.get("user_prompt", "")),
        request_platform=str(state.get("platform", "linkedin")),
        request_format=str(state.get("format", "static")),
        state=state,
        error=state.get("error"),
        cost=rec.get("cost") or state.get("cost"),
        events=list(rec.get("events") or []),
    )


def _enqueue_phase1(background_tasks: BackgroundTasks, run_id: str, payload: dict) -> None:
    settings = get_settings()
    if settings.pipeline_use_celery:
        try:
            from app.workers.pipeline_worker import run_phase1_task

            run_phase1_task.delay(run_id, payload)
            logger.info("pipeline.enqueued_celery", run_id=run_id, phase="1")
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("pipeline.celery_enqueue_failed", run_id=run_id, error=str(exc)[:160])
    background_tasks.add_task(execute_phase1, run_id, payload)


def _enqueue_phase2(
    background_tasks: BackgroundTasks,
    run_id: str,
    creative_blueprint: dict | None,
) -> None:
    settings = get_settings()
    if settings.pipeline_use_celery:
        try:
            from app.workers.pipeline_worker import run_phase2_task

            run_phase2_task.delay(run_id, creative_blueprint)
            logger.info("pipeline.enqueued_celery", run_id=run_id, phase="2")
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("pipeline.celery_enqueue_failed", run_id=run_id, error=str(exc)[:160])
    background_tasks.add_task(execute_phase2, run_id, creative_blueprint)


@router.post("/run", response_model=PipelineRunResponse, status_code=202)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
) -> PipelineRunResponse:
    """Submit Phase 1. Returns job_id immediately; poll GET /{run_id}/status or stream."""
    run_id = str(uuid4())
    logger.info(
        "pipeline.run.accepted",
        run_id=run_id,
        brand_id=request.brand_id,
        platform=request.platform,
        format=request.format,
        prompt_preview=(request.user_prompt or "")[:120],
    )
    initial = {
        "user_prompt": request.user_prompt,
        "brand_id": request.brand_id,
        "platform": request.platform,
        "format": request.format,
        "run_id": run_id,
        "repair_count": 0,
    }
    save_checkpoint(run_id, serialize_state_for_checkpoint(initial), status="pending")
    _enqueue_phase1(background_tasks, run_id, request.model_dump())
    return _response_from_state(
        run_id=run_id,
        status="pending",
        request_brand_id=request.brand_id,
        request_prompt=request.user_prompt,
        request_platform=request.platform,
        request_format=request.format,
        state=initial,
    )


@router.post("/approve", response_model=PipelineRunResponse, status_code=202)
async def approve_blueprint(
    request: PipelineApproveRequest,
    background_tasks: BackgroundTasks,
) -> PipelineRunResponse:
    """Submit Phase 2 (L8→L9→L10→renderer). Returns immediately; poll status."""
    logger.info("pipeline.approve.accepted", run_id=request.run_id)
    rec = get_checkpoint_record(request.run_id)
    if not rec:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found or expired. Start a new run (server restarts clear old in-memory runs; checkpoints are now saved to disk).",
        )
    raw = rec.get("state") or {}
    if not raw.get("creative_blueprint") and request.creative_blueprint is None:
        raise HTTPException(status_code=400, detail="No creative_blueprint available to approve")
    update_checkpoint_status(request.run_id, "generating")
    _enqueue_phase2(background_tasks, request.run_id, request.creative_blueprint)
    return _response_from_record(request.run_id, {**rec, "status": "generating"})


@router.post("/reject", response_model=PipelineRunResponse)
async def reject_blueprint(request: PipelineRejectRequest) -> PipelineRunResponse:
    """Cancel a paused Phase-1 run."""
    raw = get_checkpoint(request.run_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Pipeline run not found or expired")

    delete_checkpoint(request.run_id)
    return _response_from_state(
        run_id=request.run_id,
        status="cancelled",
        request_brand_id=str(raw.get("brand_id", "")),
        request_prompt=str(raw.get("user_prompt", "")),
        request_platform=str(raw.get("platform", "linkedin")),
        request_format=str(raw.get("format", "static")),
        state=raw,
    )


@router.get("/{run_id}/status", response_model=PipelineRunResponse)
async def pipeline_status(run_id: str) -> PipelineRunResponse:
    rec = fail_if_stale(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Pipeline run not found or expired")
    return _response_from_record(run_id, rec)


@router.get("/{run_id}/scores")
async def pipeline_scores(run_id: str) -> dict:
    rec = get_checkpoint_record(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Pipeline run not found or expired")
    state = rec.get("state") or {}
    return {
        "run_id": run_id,
        "status": rec.get("status"),
        "evaluation": state.get("evaluation"),
        "total_cost_usd": (rec.get("cost") or state.get("cost") or {}).get("total_cost_usd")
        if isinstance(rec.get("cost") or state.get("cost"), dict)
        else state.get("total_cost_usd"),
        "cost": rec.get("cost") or state.get("cost"),
        "repair_instructions": state.get("repair_instructions"),
        "repair_count": state.get("repair_count", 0),
    }


@router.get("/{run_id}/retrieval-log")
async def pipeline_retrieval_log(run_id: str) -> dict:
    rec = get_checkpoint_record(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Pipeline run not found or expired")
    state = rec.get("state") or {}
    log = state.get("retrieval_log")
    if not log:
        raise HTTPException(status_code=404, detail="No retrieval log for this run yet")
    return {"run_id": run_id, "retrieval_log": log}


@router.get("/{run_id}/stream")
async def pipeline_stream(run_id: str) -> StreamingResponse:
    rec = get_checkpoint_record(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Pipeline run not found or expired")

    async def gen():
        last = 0
        while True:
            current = get_checkpoint_record(run_id)
            if not current:
                yield f"data: {json.dumps({'event': 'pipeline_failed', 'message': 'missing'})}\n\n"
                break
            events = list(current.get("events") or [])
            for ev in events[last:]:
                yield f"data: {json.dumps(ev, default=str)}\n\n"
            last = len(events)
            status = str(current.get("status") or "")
            if status in TERMINAL_STATUSES:
                yield f"data: {json.dumps({'event': 'pipeline_complete', 'status': status})}\n\n"
                break
            await asyncio.sleep(0.8)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/edit-image-text", response_model=PipelineEditImageTextResponse)
async def edit_image_text(request: PipelineEditImageTextRequest) -> PipelineEditImageTextResponse:
    """Fix spelling / copy on a generated image inside chat (real fonts, logo untouched)."""
    if not (request.headline or request.supporting_line or request.body or request.cta):
        raise HTTPException(status_code=400, detail="Provide at least one text field to apply")
    try:
        new_url = apply_text_edits(
            image_url=request.image_url,
            headline=request.headline,
            supporting_line=request.supporting_line,
            body=request.body,
            cta=request.cta,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found in storage")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("pipeline.edit_image_text_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Could not edit image text: {exc}") from exc

    return PipelineEditImageTextResponse(
        image_url=new_url,
        headline=request.headline,
        supporting_line=request.supporting_line,
        body=request.body,
        cta=request.cta,
    )
