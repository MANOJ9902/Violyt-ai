from __future__ import annotations

"""Layout picker only. Visual identity comes from Brand Space, never sample brands."""

from dataclasses import dataclass
from typing import Literal

from app.prompts.brand_visual_palette import resolve_brand_palette_lock
from app.prompts.layout_router import LayoutType, classify_layout

TemplateId = Literal["carousel_story", "static_explain", "static_hub_facts", "static_ranking"]


@dataclass(frozen=True)
class CreativeTemplate:
    template_id: TemplateId
    layout_type: LayoutType
    format: Literal["static", "carousel", "infographic"]
    visual_style: str
    copy_lock: str
    visual_lock: str
    image_stub: str

    def l7c_layout_block(self, *, rank_n: int | None = None) -> str:
        if self.layout_type == "static_ranking":
            n = f"exactly {rank_n} " if rank_n else "all requested "
            return (
                f"LAYOUT: ranked rows. sections[] must include {n}entities from the user prompt. "
                "Each row = name + stat + one short fact. Do not invent a bank or country list."
            )
        if self.layout_type == "static_hub_facts":
            return (
                "LAYOUT: hub + fact cards. sections[] = the named entities from the user prompt. "
                "No fake testimonials. No borrowed sample brand lists."
            )
        if self.format == "carousel":
            return (
                "LAYOUT: carousel story. Unique complete headline per slide. "
                "body + proof_points teach with facts from THIS prompt — not another campaign."
            )
        return (
            "LAYOUT: education poster. sections[] = unique headings + short explanations. "
            "Dense, on-topic, Brand Space palette only."
        )

    def l8_image_hint(self, *, canvas_desc: str = "1080x1350") -> str:
        return (
            f"Canvas {canvas_desc}. Full-bleed Brand Space background. "
            f"{self.visual_lock} {self.image_stub} "
            "Bake quoted copy only. Empty top-right logo pocket. No invented mascot or legal text."
    )


def resolve_creative_template(
    user_prompt: str,
    selected_format: str | None = None,
    brand_name: str | None = None,
) -> CreativeTemplate:
    decision = classify_layout(user_prompt, selected_format)
    layout = decision.layout_type
    fmt = (selected_format or decision.suggested_format or "static").strip().lower()
    if fmt not in ("static", "carousel", "infographic"):
        fmt = decision.suggested_format or "static"

    brand_label = (brand_name or "").strip() or "this brand"
    palette = resolve_brand_palette_lock(brand_name=brand_label)

    if layout == "static_hub_facts":
        template_id: TemplateId = "static_hub_facts"
        visual_style = "hub_facts"
        stub = "Hub plus fact cards. Brand Space palette only."
    elif layout == "static_ranking":
        template_id = "static_ranking"
        visual_style = "ranking"
        stub = "Ranked rows from the user prompt. Brand Space palette only."
    elif fmt == "carousel":
        template_id = "carousel_story"
        visual_style = "carousel"
        stub = "Education carousel. Brand Space palette only."
    else:
        template_id = "static_explain"
        visual_style = "explain"
        stub = "Education poster. Brand Space palette only."
        if layout != "carousel_story":
            layout = "carousel_story"

    return CreativeTemplate(
        template_id=template_id,
        layout_type=layout,
        format=fmt,  # type: ignore[arg-type]
        visual_style=visual_style,
        copy_lock=f"Brand: {brand_label}. Use this Brand Space voice, topic, and category only.",
        visual_lock=palette,
        image_stub=stub,
    )


def list_locked_samples() -> list[dict[str, str]]:
    return [
        {"template_id": "carousel_story", "layout_type": "carousel_story", "format": "carousel", "style": "carousel"},
        {"template_id": "static_explain", "layout_type": "carousel_story", "format": "static", "style": "explain"},
        {"template_id": "static_hub_facts", "layout_type": "static_hub_facts", "format": "static", "style": "hub_facts"},
        {"template_id": "static_ranking", "layout_type": "static_ranking", "format": "infographic", "style": "ranking"},
    ]
