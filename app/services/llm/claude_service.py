from __future__ import annotations

import time
from typing import Any, Type, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm.json_utils import parse_structured_output

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class TruncatedOutputError(Exception):
    """Raised when LLM output is truncated due to max_tokens limit."""
    pass


class ClaudeService:
    """Async Anthropic client with retry, token tracking, structured output validation,
    JSON fence stripping, and automatic fallback to claude-opus-4-5 on outage/rate-limit.

    Note: Claude Sonnet 4.6 uses adaptive thinking by default and rejects temperature,
    top_p, and top_k parameters. The `temperature` argument is accepted for interface
    parity with OpenAIService but is silently ignored.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.anthropic_model
        self._fallback_model = fallback_model or settings.anthropic_fallback_model
        self._client: anthropic.AsyncAnthropic | None = None
        if self._api_key:
            timeout = float(getattr(settings, "llm_request_timeout_seconds", 180.0) or 180.0)
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key, timeout=timeout)

    # ── Core API call (retriable) ─────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(
            (anthropic.InternalServerError, TruncatedOutputError, ValidationError)
        ),
        reraise=True,
    )
    async def _call(
        self,
        model: str,
        system: str,
        user: str,
        output_model: Type[T],
        layer: str,
        max_tokens: int,
    ) -> tuple[T, dict[str, Any]]:
        if not self._client:
            raise ValueError("Anthropic API key not configured")

        start = time.monotonic()
        logger.info("llm.request", model=model, layer=layer)

        message = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        latency_ms = int((time.monotonic() - start) * 1000)
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens

        # Claude Sonnet 4.6 adaptive thinking returns a ThinkingBlock BEFORE
        # the TextBlock. We must find the first TextBlock explicitly.
        raw_text = ""
        for block in message.content:
            block_type = getattr(block, "type", "")
            if block_type == "text" and hasattr(block, "text"):
                raw_text = block.text
                break

        logger.info(
            "llm.response",
            model=model,
            layer=layer,
            stop_reason=message.stop_reason,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw_text_length=len(raw_text),
        )

        if message.stop_reason == "max_tokens" and not raw_text.strip():
            logger.error("llm.truncated_empty", model=model, layer=layer, max_tokens=max_tokens)
            raise TruncatedOutputError(f"Output fully truncated at {max_tokens} tokens for {layer}")

        parsed = parse_structured_output(raw_text, output_model, layer=layer)

        return parsed, {
            "layer": layer,
            "model": model,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    # ── Public interface ──────────────────────────────────────────────────────

    async def complete_structured(
        self,
        system: str,
        user: str,
        output_model: Type[T],
        layer: str = "unknown",
        max_tokens: int = 16000,
        temperature: float | None = None,
    ) -> tuple[T, dict[str, Any]]:
        """Return a validated Pydantic model plus metadata dict.

        Falls back to claude-opus-4-5 on RateLimitError or InternalServerError.
        """
        try:
            return await self._call(self._model, system, user, output_model, layer, max_tokens)
        except (anthropic.RateLimitError, anthropic.InternalServerError) as exc:
            if not self._fallback_model or self._fallback_model == self._model:
                raise
            logger.warning(
                "claude.fallback",
                primary=self._model,
                fallback=self._fallback_model,
                reason=repr(exc),
            )
            return await self._call(self._fallback_model, system, user, output_model, layer, max_tokens)
