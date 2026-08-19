from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.graph.checkpoint import (
    append_checkpoint_event,
    get_checkpoint_record,
    save_checkpoint,
    serialize_state_for_checkpoint,
)

logger = get_logger(__name__)

TERMINAL_STATUSES = frozenset(
    {"awaiting_blueprint_approval", "complete", "failed", "cancelled"}
)


def emit_progress(
    run_id: str,
    *,
    event: str,
    layer: str | None = None,
    latency_ms: int | None = None,
    message: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = {
        "event": event,
        "layer": layer,
        "latency_ms": latency_ms,
        "message": message,
        "ts": time.time(),
        **(extra or {}),
    }
    try:
        append_checkpoint_event(run_id, payload)
    except Exception:
        pass
    # structlog uses the first positional arg as `event`; never pass event= as a kwarg.
    try:
        logger.info(
            "pipeline.progress",
            run_id=run_id,
            progress_event=event,
            layer=layer,
            latency_ms=latency_ms,
            message=message,
        )
    except Exception:
        pass


def latest_progress(run_id: str) -> dict[str, Any] | None:
    rec = get_checkpoint_record(run_id)
    events = list((rec or {}).get("events") or [])
    return events[-1] if events else None


def apply_graph_delta(merged: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    """Merge a LangGraph node update onto accumulated state (token/latency reducers)."""
    for key, value in delta.items():
        if key in {"token_usage", "layer_latencies"} and isinstance(value, dict):
            bucket = dict(merged.get(key) or {})
            bucket.update(value)
            merged[key] = bucket
        else:
            merged[key] = value
    return merged


async def astream_graph(compiled, initial: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Run the graph, emitting layer_complete events. Falls back to ainvoke."""
    merged: dict[str, Any] = dict(initial)
    progressed = False
    try:
        async for update in compiled.astream(initial, stream_mode="updates"):
            if not isinstance(update, dict):
                continue
            for node_name, delta in update.items():
                if isinstance(delta, dict):
                    progressed = True
                    apply_graph_delta(merged, delta)
                    latencies = delta.get("layer_latencies") or {}
                    latency = None
                    if isinstance(latencies, dict) and latencies:
                        latency = next(iter(latencies.values()), None)
                    emit_progress(
                        run_id,
                        event="layer_complete",
                        layer=str(node_name),
                        latency_ms=int(latency) if latency is not None else None,
                    )
                    try:
                        save_checkpoint(
                            run_id,
                            serialize_state_for_checkpoint(merged),
                            status="running",
                        )
                    except Exception:
                        pass
        return merged
    except Exception as exc:
        if progressed:
            raise
        logger.warning("pipeline.astream_unsupported", run_id=run_id, error=str(exc)[:160])
        emit_progress(run_id, event="layer_complete", layer="graph", message="fallback_ainvoke")
        return await compiled.ainvoke(initial)
