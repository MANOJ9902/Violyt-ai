"""Rebuild the infographic prompt from a saved run payload to inspect baked copy."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from app.services.image_generation.data_story_image_prompt import build_data_story_prompt

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "storage/_jiraaf_infographic_phase2.json")

PALETTE = {
    "background": "#EEF4FF",
    "primary": "#1B4DE4",
    "headline": "#12308F",
    "secondary": "#DCE7FF",
    "card": "#E4EDFF",
    "accent": "#FF9E02",
    "body": "#1F2A44",
    "muted": "#5A6B8C",
}


def main() -> int:
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    bp = payload.get("creative_blueprint") or {}
    blueprint = SimpleNamespace(
        headline=bp.get("headline") or "",
        title=bp.get("title") or "",
        supporting_line=bp.get("supporting_line") or "",
        stat_highlights=bp.get("stat_highlights") or [],
        proof_points=bp.get("proof_points") or [],
        cta=bp.get("cta") or "",
        source_footer=bp.get("source_footer") or "",
        customer_quote=bp.get("customer_quote") or "",
        body=bp.get("body") or "",
        problem_statement=bp.get("problem_statement") or "",
        solution_statement=bp.get("solution_statement") or "",
        sections=[
            SimpleNamespace(
                section_label=s.get("section_label") or "",
                body=s.get("body") or "",
                stat=s.get("stat") or "",
                includes=s.get("includes") or [],
            )
            for s in (bp.get("sections") or [])
        ],
    )
    prompt = build_data_story_prompt(
        blueprint, canvas_desc="1080x1350", supporting="", palette=PALETTE
    )
    copy_block = prompt.split("2. LAYOUT", 1)[0]
    print(copy_block)
    print(f"[prompt_len={len(prompt)}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
