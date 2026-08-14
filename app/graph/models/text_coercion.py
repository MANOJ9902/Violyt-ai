from __future__ import annotations

"""Coercion helpers for LLM list fields declared as list[str].

Copy models ask for flat display strings, but the LLM regularly answers with
small objects such as {"number": "450", "label": "Operational Airports"}.
Rejecting those fails the whole run, and str()-ing them bakes Python dict
syntax into artwork, so they are flattened into the display line instead.
"""

from typing import Any

_NUMBER_KEYS = ("number", "value", "stat", "figure", "amount", "count")
_LABEL_KEYS = (
    "label",
    "title",
    "metric",
    "mini_title",
    "subtitle",
    "sub_title",
    "name",
    "heading",
    "caption",
    "text",
    "point",
)
_DETAIL_KEYS = ("description", "detail", "body", "fact", "explanation", "so_what", "note")


def _first_present(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        raw = data.get(key)
        if isinstance(raw, (str, int, float)) and str(raw).strip():
            return str(raw).strip()
    return ""


def stringify_item(value: Any) -> str:
    """Flatten one LLM list entry into a single display line."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        number = _first_present(value, _NUMBER_KEYS)
        label = _first_present(value, _LABEL_KEYS)
        detail = _first_present(value, _DETAIL_KEYS)
        if number and label:
            line = f"{number} {label}"
        elif label:
            line = label
        elif number:
            line = number
        else:
            line = " ".join(
                str(v).strip()
                for v in value.values()
                if isinstance(v, (str, int, float)) and str(v).strip()
            )
        if detail and detail not in line:
            line = f"{line} | {detail}" if line else detail
        return line.strip()
    if isinstance(value, (list, tuple, set)):
        parts = [stringify_item(v) for v in value]
        return " ".join(p for p in parts if p).strip()
    return str(value).strip()


def stringify_list(value: Any) -> list[str]:
    """Coerce an LLM list field into list[str], dropping empties."""
    if value is None:
        return []
    if isinstance(value, (str, dict)):
        single = stringify_item(value)
        return [single] if single else []
    if isinstance(value, (list, tuple, set)):
        out = [stringify_item(v) for v in value]
        return [v for v in out if v]
    single = stringify_item(value)
    return [single] if single else []
