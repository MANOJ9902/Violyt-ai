"""Shared LLM JSON extraction + light repair for structured outputs."""

from __future__ import annotations

import json
import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
_SMART_QUOTES = str.maketrans(
    {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u00a0": " ",
    }
)


def extract_json_object(raw: str) -> str:
    """Pull the first top-level JSON object from model text (fences / preamble OK)."""
    text = (raw or "").strip()
    if not text:
        return "{}"

    if text.startswith("```"):
        lines = text.split("\n")
        end_line = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end_line = i
                break
        text = "\n".join(lines[1:end_line]).strip()

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    start_idx = text.find("{")
    if start_idx == -1:
        return text

    depth = 0
    in_string = False
    escape_next = False
    last_valid_end = -1
    for i, ch in enumerate(text[start_idx:], start=start_idx):
        if escape_next:
            escape_next = False
            continue
        if in_string:
            if ch == "\\":
                escape_next = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                last_valid_end = i
                break

    if last_valid_end != -1:
        candidate = text[start_idx : last_valid_end + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return candidate

    truncated = text[start_idx:]
    open_depth = 0
    in_str = False
    esc = False
    for ch in truncated:
        if esc:
            esc = False
            continue
        if in_str:
            if ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            open_depth += 1
        elif ch == "}":
            open_depth -= 1
    return truncated + "}" * max(0, open_depth)


def _escape_bare_control_chars_in_strings(text: str) -> str:
    """Escape raw newlines/tabs that appear inside JSON string literals."""
    out: list[str] = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            out.append(ch)
            escape_next = False
            continue
        if ch == "\\" and in_string:
            out.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string:
            if ch == "\n":
                out.append("\\n")
                continue
            if ch == "\r":
                out.append("\\r")
                continue
            if ch == "\t":
                out.append("\\t")
                continue
            if ord(ch) < 32:
                out.append(f"\\u{ord(ch):04x}")
                continue
        out.append(ch)
    return "".join(out)


def _escape_interior_quotes(text: str) -> str:
    """Escape unescaped \" that appear inside string values (common LLM bug)."""
    chars = list(text)
    i = 0
    n = len(chars)
    in_string = False
    while i < n:
        ch = chars[i]
        if ch == "\\" and in_string and i + 1 < n:
            i += 2
            continue
        if ch == '"':
            if not in_string:
                in_string = True
                i += 1
                continue
            j = i + 1
            while j < n and chars[j] in " \t\r\n":
                j += 1
            nxt = chars[j] if j < n else ""
            if nxt in (",", "}", "]", ":", ""):
                in_string = False
                i += 1
                continue
            chars[i] = '\\"'
            i += 1
            continue
        i += 1
    return "".join(chars)


def repair_llm_json(raw: str) -> str:
    """Best-effort repair of near-JSON from LLMs."""
    text = extract_json_object(raw)
    text = text.translate(_SMART_QUOTES)
    text = text.replace("\ufeff", "")
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    text = re.sub(r"\bNone\b", "null", text)
    text = _TRAILING_COMMA_RE.sub(r"\1", text)
    text = _escape_bare_control_chars_in_strings(text)

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    repaired = _escape_interior_quotes(text)
    repaired = _TRAILING_COMMA_RE.sub(r"\1", repaired)
    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        return repaired


def parse_structured_output(raw: str, output_model: Type[T], *, layer: str = "unknown") -> T:
    """Extract + repair + validate into a Pydantic model."""
    cleaned = extract_json_object(raw)
    try:
        return output_model.model_validate_json(cleaned)
    except ValidationError:
        repaired = repair_llm_json(raw)
        try:
            parsed = output_model.model_validate_json(repaired)
            logger.warning("llm.json_repaired", layer=layer)
            return parsed
        except ValidationError:
            try:
                data: Any = json.loads(repaired)
                return output_model.model_validate(data)
            except Exception:
                logger.error(
                    "llm.json_parse_failed",
                    layer=layer,
                    preview=repaired[:400],
                )
                raise
