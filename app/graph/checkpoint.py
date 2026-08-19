from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_TTL_SECONDS = 60 * 60 * 6  # 6 hours
_CHECKPOINT_DIR = Path(__file__).resolve().parents[2] / "storage" / "pipeline_checkpoints"


def _ensure_dir() -> Path:
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return _CHECKPOINT_DIR


def _path_for(run_id: str) -> Path:
    safe = "".join(ch for ch in str(run_id) if ch.isalnum() or ch in "-_")
    return _ensure_dir() / f"{safe}.json"


def _purge_expired() -> None:
    now = time.time()
    root = _ensure_dir()
    for path in root.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            created = float(data.get("created_at") or 0)
            if now - created > _TTL_SECONDS:
                path.unlink(missing_ok=True)
                logger.info("pipeline_checkpoint.purged", run_id=path.stem)
        except Exception:
            continue


def _read_payload(run_id: str) -> dict[str, Any] | None:
    path = _path_for(run_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("pipeline_checkpoint.read_failed", run_id=run_id, error=str(exc))
        return None


def _write_payload(run_id: str, payload: dict[str, Any]) -> None:
    path = _path_for(run_id)
    path.write_text(json.dumps(payload, default=str), encoding="utf-8")


def save_checkpoint(
    run_id: str,
    state: dict[str, Any],
    status: str = "awaiting_blueprint_approval",
    *,
    events: list[dict[str, Any]] | None = None,
    cost: dict[str, Any] | None = None,
) -> None:
    _purge_expired()
    existing = _read_payload(run_id) or {}
    payload = {
        "state": deepcopy(state),
        "created_at": existing.get("created_at") or time.time(),
        "updated_at": time.time(),
        "status": status,
        "events": events if events is not None else list(existing.get("events") or []),
        "cost": cost if cost is not None else existing.get("cost"),
    }
    _write_payload(run_id, payload)
    logger.info("pipeline_checkpoint.saved", run_id=run_id, status=status, path=str(_path_for(run_id)))


def get_checkpoint(run_id: str) -> dict[str, Any] | None:
    data = _read_payload(run_id)
    if not data:
        logger.warning("pipeline_checkpoint.miss", run_id=run_id)
        return None
    return deepcopy(data.get("state") or {})


def get_checkpoint_record(run_id: str) -> dict[str, Any] | None:
    data = _read_payload(run_id)
    if not data:
        return None
    return deepcopy(data)


def fail_if_stale(
    run_id: str,
    *,
    max_idle_sec: float = 480.0,
) -> dict[str, Any] | None:
    """Mark a run failed when the worker died mid-layer (reload / hang)."""
    data = _read_payload(run_id)
    if not data:
        return None
    status = str(data.get("status") or "")
    if status not in {"pending", "running", "generating"}:
        return deepcopy(data)
    updated = float(data.get("updated_at") or data.get("created_at") or 0)
    idle = time.time() - updated
    if idle < max_idle_sec:
        return deepcopy(data)
    state = data.get("state") if isinstance(data.get("state"), dict) else {}
    state["error"] = (
        "Pipeline stalled with no progress. The worker likely stopped "
        "(server reload) or a layer hung. Start a new run."
    )
    data["state"] = state
    data["status"] = "failed"
    data["updated_at"] = time.time()
    _write_payload(run_id, data)
    logger.warning("pipeline_checkpoint.stale_failed", run_id=run_id, idle_sec=round(idle, 1))
    return deepcopy(data)


def get_checkpoint_status(run_id: str) -> str | None:
    data = _read_payload(run_id)
    if not data:
        return None
    return data.get("status")


def update_checkpoint_status(run_id: str, status: str) -> None:
    data = _read_payload(run_id)
    if not data:
        return
    data["status"] = status
    data["updated_at"] = time.time()
    _write_payload(run_id, data)


def append_checkpoint_event(run_id: str, event: dict[str, Any]) -> None:
    data = _read_payload(run_id)
    if not data:
        data = {"state": {}, "created_at": time.time(), "events": [], "status": "pending"}
    events = list(data.get("events") or [])
    events.append(event)
    data["events"] = events[-80:]
    data["updated_at"] = time.time()
    _write_payload(run_id, data)


def delete_checkpoint(run_id: str) -> None:
    path = _path_for(run_id)
    path.unlink(missing_ok=True)
    logger.info("pipeline_checkpoint.deleted", run_id=run_id)


def serialize_state_for_checkpoint(state: dict[str, Any]) -> dict[str, Any]:
    """Convert ViolytState (may contain Pydantic models) to JSON-friendly dict."""

    def _dump(obj: Any) -> Any:
        if obj is None:
            return None
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if isinstance(obj, dict):
            return {k: _dump(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_dump(v) for v in obj]
        return obj

    return _dump(state)
