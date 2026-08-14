"""Verify Jiraaf brand detection routes misspelled Brand Space names correctly."""

from __future__ import annotations

import inspect
import sys

import app.graph  # noqa: F401  (avoids the prompts<->graph circular import)
import app.prompts.layer8_visual_reasoning as l8
from app.prompts.brand_visual_palette import is_jiraaf_brand

MATCH = ["Jiraaf", "jiraaf", "Jirraf", "Jiraff", "JIRRAF", "Jiraaf Platform Private Limited"]
NO_MATCH = ["Jira", "Jira Software", "Cognixia", "Niroggi", "Hyqoo", "Nykaa", "", None]

failures: list[str] = []

for name in MATCH:
    if not is_jiraaf_brand(name):
        failures.append(f"{name!r} should match Jiraaf")
for name in NO_MATCH:
    if is_jiraaf_brand(name):
        failures.append(f"{name!r} should NOT match Jiraaf")

builder_cls = next(
    v for v in vars(l8).values() if inspect.isclass(v) and hasattr(v, "INFO_BG")
)
builder = builder_cls()
signature = inspect.signature(builder._build_infographic_prompt)
kwargs = {
    "headline": "Why India Is Building Airports Everywhere",
    "supporting_line": "157 airports today, up from 74 in 2014.",
    "infographic_sections": [
        {"section_label": "UDAN links small cities", "includes": ["619 routes"], "stat": "619"}
    ],
    "cta": "Learn more",
    "user_prompt": "why India is building airports everywhere",
    "visual_mood": "premium editorial",
    "color_behavior": "",
    "layout_type": "carousel_story",
}
for param in signature.parameters.values():
    if param.kind is param.KEYWORD_ONLY and param.default is param.empty:
        kwargs.setdefault(param.name, [] if param.name.endswith(("s", "flow")) else "")
kwargs = {
    k: v for k, v in kwargs.items() if k in signature.parameters and k != "brand_name"
}

for name in ("Jiraaf", "Jirraf"):
    prompt = builder._build_infographic_prompt(brand_name=name, **kwargs)
    jiraaf_layout = "DENSE INFOGRAPHIC EXPLAIN" in prompt
    generic_layout = "BRAND EDUCATION POSTER" in prompt
    has_bg = "#87CEFA" in prompt
    print(
        f"{name:8} jiraaf_layout={jiraaf_layout} generic_teal={generic_layout} bg_87CEFA={has_bg}"
    )
    if not jiraaf_layout or generic_layout or not has_bg:
        failures.append(f"{name!r} did not route to the Jiraaf visual system")

if failures:
    print("\nFAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("\njiraaf_detection_ok")
