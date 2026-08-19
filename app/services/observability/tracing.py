from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _langsmith_enabled() -> bool:
    settings = get_settings()
    return bool(
        getattr(settings, "langsmith_api_key", None)
        or getattr(settings, "langchain_tracing_v2", False)
    )


@contextmanager
def layer_span(layer: str, run_id: str | None = None, **attrs: Any) -> Iterator[dict[str, Any]]:
    """Structured span per layer. Logs always; LangSmith if configured."""
    start = time.monotonic()
    span: dict[str, Any] = {"layer": layer, "run_id": run_id, **attrs}
    logger.info("otel.span.start", **span)
    try:
        yield span
    except Exception as exc:
        span["error"] = str(exc)
        logger.error("otel.span.error", **span)
        raise
    finally:
        span["latency_ms"] = int((time.monotonic() - start) * 1000)
        logger.info("otel.span.end", **{k: v for k, v in span.items() if k != "error"})
        if _langsmith_enabled():
            try:
                from langsmith import Client  # type: ignore

                client = Client(api_key=get_settings().langsmith_api_key)
                client.create_run(
                    name=layer,
                    run_type="chain",
                    inputs={"run_id": run_id, **attrs},
                    outputs={"latency_ms": span.get("latency_ms"), "error": span.get("error")},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("langsmith.span_failed", error=str(exc)[:160])
