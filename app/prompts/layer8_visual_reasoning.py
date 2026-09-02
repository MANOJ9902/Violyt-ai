from __future__ import annotations

from typing import Any

from app.graph.models.layer2_models import BrandIntelligenceOutput
from app.graph.models.layer6_models import FormatPlanOutput
from app.graph.models.layer7_models import CopyOutput
from app.prompts.base import BasePromptBuilder
from app.prompts.brand_visual_palette import resolve_brand_palette_lock
from app.prompts.brand_copy_tone import (
    NEUTRAL_BG,
    NEUTRAL_HEADLINE,
    NEUTRAL_ACCENT,
    NEUTRAL_BODY,
    NEUTRAL_CARD,
    SOURCE_FOOTER_RULE,
    LEGAL_FOOTER_HINT,
    NO_LEGAL_STATIC_RULE,
    UNIVERSAL_FIT_LOCK,
)
from app.prompts.creative_sizes import canvas_label


class VisualReasoningPromptBuilder(BasePromptBuilder):
    """Layer 8 Visual Reasoning — composition from Brand Space + approved copy."""

    PROMPT_VERSION = "6.1-brand-reference-only"

    # Colors come from BrandVisualPack at call time; these are empty-pack fallbacks.
    CAROUSEL_BG = NEUTRAL_BG
    INFO_BG = NEUTRAL_BG
    NAVY = NEUTRAL_HEADLINE
    CAROUSEL_NAVY = NEUTRAL_HEADLINE
    CAROUSEL_ORANGE = NEUTRAL_ACCENT
    BODY_GRAY = NEUTRAL_BODY
    ORANGE = NEUTRAL_ACCENT
    GOLD = NEUTRAL_ACCENT
    CARD_BLUE = NEUTRAL_CARD
    BANNER_NAVY = NEUTRAL_HEADLINE

    def _selected_reference_lock(self, pack: dict[str, Any], *, fmt: str = "") -> str:
        selected = pack.get("selected_reference") if isinstance(pack.get("selected_reference"), dict) else {}
        name = str(selected.get("name") or "").strip()
        fmt_label = (fmt or "this format").strip() or "this format"
        if name:
            return (
                f"LAYOUT SOURCE: follow the uploaded Brand Space reference “{name}” for {fmt_label}. "
                "Copy its structure, spacing, hierarchy, icon style, and card pattern. "
                "Replace only the TEXT with approved copy. Do not invent a built-in format recipe."
            )
        return (
            f"LAYOUT SOURCE: this brand's Brand Space visual identity for {fmt_label}. "
            "Do not use a built-in carousel, infographic, or static poster recipe."
        )

    def build_system(self, fmt: str = "", **kwargs: Any) -> str:
        brand_name = str(kwargs.get("brand_name") or "")
        platform = str(kwargs.get("platform") or "")
        pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
        primary = str(pack.get("primary") or kwargs.get("brand_primary_color") or "")
        secondary = str(pack.get("secondary") or kwargs.get("brand_secondary_color") or "")
        accent = str(pack.get("accent") or "")
        background = str(pack.get("background") or "")
        font = str(
            pack.get("font_primary") or pack.get("font") or kwargs.get("brand_typography_font") or ""
        )
        palette_lock = resolve_brand_palette_lock(
            brand_name=brand_name,
            primary_color=primary,
            secondary_color=secondary,
            accent_color=accent,
            background_color=background,
            additional_colors=pack.get("additional") if isinstance(pack.get("additional"), list) else None,
        )
        canvas = canvas_label(fmt, platform)
        font_note = (
            f"Typography: bold {font} headlines; clean sans body; ALL copy baked."
            if font
            else "Typography: bold Brand Space primary headlines; ALL copy baked."
        )
        ref_lock = self._selected_reference_lock(pack, fmt=fmt)
        has_legal = bool(pack.get("has_legal") or pack.get("legal_footer"))
        legal_rule = LEGAL_FOOTER_HINT if fmt == "carousel" and has_legal else NO_LEGAL_STATIC_RULE
        headline_hex = primary or self.NAVY
        body_hex = str(pack.get("body") or self.BODY_GRAY)
        accent_hex = accent or secondary or headline_hex

        format_instructions = f"""
FORMAT: {fmt or "static"} for {brand_name or "this brand"} on {platform or "the selected platform"}.
Canvas: {canvas}. Every element fully inside the frame. Safe margin ≥6%. Never clip or cut off mid-word.
Background: Brand Space background full bleed ({background or "from Brand Space"}).
{palette_lock}
{font_note}
{ref_lock}
AUDIENCE: Brand Space persona only — never a borrowed crowd from another brand.
Icons and illustrations: match THIS brand's category and the selected reference.
TEXT QUALITY: letter-perfect spelling; complete sentences; shrink type rather than truncate.
TOP-RIGHT: empty logo pocket — Brand Space logo is composited later. Never draw logos, wordmarks, or platform watermarks.
"""

        return f"""You are Violyt's Visual Reasoning Engine. Plan composition for a finished AI image with baked-in typography.
Return ONE JSON object matching VisualReasoningOutput EXACTLY — every required key below must be present.

CRITICAL:
- dominant_visual_system: generated_image | type_led | illustration | infographic | data_visual | product_visual
- visual_format_type: comparison | timeline | chart | matrix | process_flow | hero_scene | data_grid
- Bake approved Creative Blueprint copy into the image as sharp typography (exact strings).
- Follow the Brand Space reference for layout. Never invent a built-in format poster.
- NEVER draw logos/wordmarks or brand-name text; Brand Space logo is composited later into a tiny top-right pocket.
- Spelling of every planned text string must be perfect.
- generated_image_url must be "".
- image_prompt_direction: describe layout FROM THE BRAND SPACE REFERENCE, Brand Space colors, AND exact text to render.

REQUIRED JSON SHAPE (fill every field; do not rename keys):
{{
  "dominant_visual_system": "generated_image",
  "visual_format_type": "hero_scene",
  "visual_style": "Match the selected Brand Space reference for {brand_name or 'this brand'}",
  "composition_logic": "Copy the uploaded reference hierarchy; swap in approved copy only",
  "focal_point": "Primary visual from the Brand Space reference",
  "negative_space_plan": "Generous margins; tiny logo-safe top-right pocket only — headline fully clear",
  "color_behavior": {palette_lock!r},
  "logo_zone_instruction": "Empty top-right pocket (~24% width x 12% height), 20px padding; never draw brand-name text",
  "typography_behavior": "Bold Brand Space primary sans headlines, readable body, baked into image",
  "image_prompt_direction": "Describe the Brand Space reference layout, Brand Space colors, and exact text...",
  "content_sections": [
    {{
      "section_id": "row_1",
      "title": "Section title from approved copy",
      "body": "Approved body",
      "metric": "",
      "visual_metaphor": "Topic-matched icon from this brand"
    }}
  ],
  "text_overlay_plan": [
    {{
      "element_type": "headline",
      "text": "Exact headline",
      "font_size": 42,
      "color_hex": "{headline_hex}",
      "position_box": "top-center"
    }},
    {{
      "element_type": "supporting_line",
      "text": "Exact supporting line",
      "font_size": 22,
      "color_hex": "{body_hex}",
      "position_box": "upper-center"
    }},
    {{
      "element_type": "cta",
      "text": "Exact CTA",
      "font_size": 20,
      "color_hex": "{accent_hex}",
      "position_box": "footer-strip"
    }}
  ],
  "generated_image_url": ""
}}

content_sections items MUST use keys section_id + title (not section_label).
text_overlay_plan items MUST include font_size, color_hex, position_box.
element_type allowed: headline|subheadline|supporting_line|body|cta|label|footer|section_label|stat|badge.

No preamble. No markdown fences. ONLY raw JSON.
{SOURCE_FOOTER_RULE}
{legal_rule}
{format_instructions}"""

    def build_user(
        self,
        brand_intelligence: BrandIntelligenceOutput,
        format_plan: FormatPlanOutput,
        copy: CopyOutput,
        concept: dict,
        user_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        fmt = str(kwargs.get("fmt") or "").strip().lower()
        colors = f"Primary: {brand_intelligence.visual_behavior.color_behavior}"
        mood = brand_intelligence.visual_behavior.visual_mood
        logo_zone = brand_intelligence.visual_behavior.logo_zone_instruction
        user_prompt_section = (
            f"\nUSER ORIGINAL PROMPT (primary topic direction):\n{user_prompt}\n" if user_prompt else ""
        )
        pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
        text_directive = self._selected_reference_lock(pack, fmt=fmt)

        return f"""BRAND VISUAL SYSTEM CONTEXT:
Brand Name: {brand_intelligence.brand_core.brand_name}
Value Proposition: {brand_intelligence.brand_core.value_proposition}
Brand Stands For: {', '.join(brand_intelligence.brand_core.stands_for)}
Brand Stands Against: {', '.join(brand_intelligence.brand_core.stands_against)}
Visual Mood: {mood}
Design Sophistication: {brand_intelligence.visual_behavior.design_sophistication}
Color Behavior: {colors}
Image Behavior: {brand_intelligence.visual_behavior.image_behavior}
Logo Zone Instruction: {logo_zone}
Format: {fmt or 'auto'}
{user_prompt_section}
CONCEPT:
Name: {concept.get('concept_name', '')}
Core Idea: {concept.get('core_idea', '')}
Hook: {concept.get('hook', '')}
Narrative Angle: {concept.get('narrative_angle', '')}
Visual Angle: {concept.get('visual_angle', '')}
Layout Archetype: {format_plan.layout_archetype}
Format Strategy: {format_plan.format_strategy}
Copy Headline: {copy.headline}
Supporting Line: {copy.supporting_line or 'N/A'}
Copy Body: {copy.body}
CTA: {copy.cta}

SLIDE ROLES AND VISUAL INTENTIONS:
{chr(10).join([f"- Slide {s.slide_number}: role={s.role}, focus={s.focus}, visual_intent={s.visual_intent}" for s in format_plan.slide_plan])}

INSTRUCTION:
Plan composition for THIS brand only. {text_directive}
Bake approved copy letter-perfect. Perfect spelling. Never cut off mid-word.

Return ONLY raw JSON."""

    def build_expander_system(
        self, dominant_visual_system: str = "generated_image", fmt: str = "static", **kwargs: Any
    ) -> str:
        brand_name = str(kwargs.get("brand_name") or "")
        return (
            f"You are a senior Art Director writing the FINAL image-generation prompt for gpt-image-1. "
            f"Use ONLY {brand_name or 'this brand'}'s Brand Space visual identity and uploaded reference. "
            "CRITICAL: The approved headline, body, sections and CTA text are FINAL — reproduce them WORD-FOR-WORD in the image prompt. Do NOT rephrase, summarise or replace them. "
            "Output ONLY the expanded prompt text — no preamble, no markdown headers."
        )

    def build_expander_user(
        self,
        brand_name: str,
        visual_mood: str,
        color_behavior: str,
        image_behavior: str,
        design_sophistication: str,
        concept_name: str,
        core_idea: str,
        visual_angle: str,
        copy_headline: str,
        copy_body: str,
        supporting_line: str = "",
        cta: str = "",
        infographic_sections: list[dict] | None = None,
        proof_points: list[str] | None = None,
        stat_highlights: list[str] | None = None,
        problem_statement: str = "",
        solution_statement: str = "",
        customer_quote: str = "",
        customer_name: str = "",
        process_steps: list[str] | None = None,
        format_strategy: str = "",
        layout_archetype: str = "",
        platform: str = "",
        initial_prompt: str = "",
        user_prompt: str = "",
        dominant_visual_system: str = "generated_image",
        fmt: str = "static",
        story_flow: list[str] | None = None,
        hook: str = "",
        slides: list[dict] | None = None,
        **kwargs: Any,
    ) -> str:
        canvas = canvas_label(fmt, platform)
        pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
        if not pack:
            pack = {
                "background": str(kwargs.get("background") or ""),
                "primary": str(kwargs.get("primary") or ""),
                "secondary": str(kwargs.get("secondary") or ""),
                "accent": str(kwargs.get("accent") or ""),
                "selected_reference": kwargs.get("selected_reference") or {},
            }
        return self._build_copy_bake_prompt(
            brand_name=brand_name,
            fmt=fmt,
            canvas=canvas,
            pack=pack,
            headline=copy_headline,
            supporting_line=supporting_line,
            body=copy_body,
            cta=cta,
            hook=hook,
            user_prompt=user_prompt,
            visual_mood=visual_mood,
            color_behavior=color_behavior,
            initial_prompt=initial_prompt,
            sections=infographic_sections or [],
            proof_points=proof_points or [],
            stat_highlights=stat_highlights or [],
            problem_statement=problem_statement,
            solution_statement=solution_statement,
            customer_quote=customer_quote,
            customer_name=customer_name,
            process_steps=process_steps or [],
            story_flow=story_flow or [],
            slides=slides or [],
        )

    def _build_copy_bake_prompt(
        self,
        *,
        brand_name: str,
        fmt: str,
        canvas: str,
        pack: dict[str, Any],
        headline: str,
        supporting_line: str,
        body: str,
        cta: str,
        hook: str,
        user_prompt: str,
        visual_mood: str,
        color_behavior: str,
        initial_prompt: str,
        sections: list[dict],
        proof_points: list[str],
        stat_highlights: list[str],
        problem_statement: str,
        solution_statement: str,
        customer_quote: str,
        customer_name: str,
        process_steps: list[str],
        story_flow: list[str],
        slides: list[dict],
    ) -> str:
        ref_lock = self._selected_reference_lock(pack, fmt=fmt)
        rows = []
        for i, sec in enumerate((sections or [])[:15], start=1):
            label = sec.get("section_label") or f"Item {i}"
            stat = sec.get("stat") or ""
            includes = sec.get("includes") or []
            if isinstance(includes, list):
                includes_txt = "; ".join(str(x) for x in includes[:3])
            else:
                includes_txt = str(includes)
            body_sec = " ".join(str(sec.get("body") or "").split()).strip()
            rows.append(
                f'{i}. "{label}"'
                + (f' | {stat}' if stat else "")
                + (f' | {includes_txt}' if includes_txt else "")
                + (f' | {body_sec}' if body_sec else "")
            )
        rows_text = "\n".join(rows) or "(none)"
        slides_block = "\n".join(
            f"Slide {s.get('slide_number', i+1)} [{s.get('role', 'insight')}]: "
            f"headline={s.get('headline', '')}; body={s.get('body', '')}; cta={s.get('cta') or ''}"
            for i, s in enumerate((slides or [])[:8])
        ) or "(single surface)"
        story = "\n".join(f"- {b}" for b in (story_flow or [])[:6]) or "- (from headline/body)"
        proofs = "\n".join(f"- {p}" for p in (proof_points or [])[:6]) or "- (omit if empty)"
        stats = "\n".join(f"- {s}" for s in (stat_highlights or [])[:6]) or "- (omit if empty)"
        steps = "\n".join(f"- {s}" for s in (process_steps or [])[:4]) or "- (omit if empty)"
        user_block = f'\nUSER TOPIC REQUEST:\n"{user_prompt}"\n' if user_prompt else ""
        has_legal = bool(pack.get("has_legal") or pack.get("legal_footer"))
        legal_rule = LEGAL_FOOTER_HINT if fmt == "carousel" and has_legal else NO_LEGAL_STATIC_RULE
        palette = resolve_brand_palette_lock(
            brand_name=brand_name,
            color_behavior=color_behavior,
            visual_mood=visual_mood,
            primary_color=str(pack.get("primary") or ""),
            secondary_color=str(pack.get("secondary") or ""),
            accent_color=str(pack.get("accent") or ""),
            background_color=str(pack.get("background") or ""),
        )

        return f"""Create ONE finished {fmt or 'static'} creative for {brand_name}.

{ref_lock}
Canvas: {canvas}. Every element fully inside the frame. Safe margin ≥6%. Never clip mid-word.
{palette}
{legal_rule}
{UNIVERSAL_FIT_LOCK}
TOP-RIGHT: empty logo pocket — never draw logo or brand-name text.
TEXT QUALITY: letter-perfect spelling; complete words; shrink type rather than cut off.

EXACT COPY TO BAKE (verbatim — do not paraphrase)
Brand: {brand_name}
Hook: {hook or '(optional)'}
Headline: {headline}
Supporting line: {supporting_line or '(optional)'}
Body: {body}
CTA (only if provided — never invent): {cta or '(omit)'}
Problem: {problem_statement or '(omit)'}
Solution: {solution_statement or '(omit)'}
Quote: {customer_quote or '(omit)'} {customer_name or ''}
Storyline:
{story}
Sections / rows:
{rows_text}
Stats:
{stats}
Proof points:
{proofs}
Process:
{steps}
Slide pack:
{slides_block}
Visual mood: {visual_mood}
Brand color behavior: {color_behavior}
{user_block}
Initial art direction (refine; still follow the Brand Space reference):
{(initial_prompt or '')[:1200]}

Return ONLY the finished image-generation prompt."""
