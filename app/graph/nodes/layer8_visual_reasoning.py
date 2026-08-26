from __future__ import annotations

import re
from uuid import UUID, uuid4

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.graph.models.layer8_models import VisualReasoningOutput
from app.graph.state import ViolytState
from app.models.brand import BrandSpace
from app.prompts.layer8_visual_reasoning import VisualReasoningPromptBuilder
from app.services.image_generation.dalle_service import DalleService
from app.services.image_generation.logo_fetcher import get_brand_logo_storage_path
from app.services.image_generation.sdxl_service import SdxlService
from app.services.llm.llm_router import LLMRouter
from app.prompts.brand_copy_tone import (
    SOURCE_FOOTER_RULE,
    ICON_STYLE_LOCK,
    INFOGRAPHIC_AUDIENCE_TONE_LOCK,
)
from app.prompts.layout_router import classify_layout
from app.prompts.creative_templates import resolve_creative_template
from app.prompts.creative_sizes import canvas_label, size_string
from app.services.image_generation.brand_render_lock import build_lock_from_pack
from app.services.blueprint_quality import repair_explain_infographic_copy, repair_generic_headline

# gpt-image-1 accepts 32k prompt chars. The old 5800 budget silently trimmed the
# banded infographic layout — losing the brand-colour and no-cutoff blocks at the
# tail — which is why palette adherence looked random between runs.
_IMAGE_PROMPT_BUDGET = 12000


def _budget_prompt(
    content: str,
    locks: str = "",
    budget: int = _IMAGE_PROMPT_BUDGET,
    *,
    mandatory: str = "",
) -> str:
    """Keep slide CONTENT intact; only trim trailing locks if over budget.

    `mandatory` (the per-brand render contract) is never trimmed — it leads the
    prompt so a long layout block can't push the colour/logo/no-cutoff rules out.
    """
    content = (content or "").strip()
    locks = (locks or "").strip()
    mandatory = (mandatory or "").strip()

    head = f"{mandatory}\n\n" if mandatory else ""
    room = max(0, budget - len(head))
    if len(content) >= room:
        return f"{head}{content[:room]}"
    remaining = room - len(content) - 2
    if remaining <= 0 or not locks:
        return f"{head}{content}"
    return f"{head}{content}\n\n{locks[:remaining]}"

logger = get_logger(__name__)

_router = LLMRouter()
_prompt_builder = VisualReasoningPromptBuilder()


def _q(value: object, max_chars: int = 280) -> str:
    """Quote exact copy for image prompts; trim on word boundary (never bake '…')."""
    if isinstance(value, (list, tuple)):
        parts: list[str] = []
        for v in value:
            if isinstance(v, dict):
                label = v.get("section_label") or v.get("label") or ""
                body = v.get("body") or v.get("stat") or ""
                chunk = f"{label}: {body}".strip(": ").strip()
                if chunk:
                    parts.append(chunk)
            else:
                s = str(v).strip()
                if s:
                    parts.append(s)
        text = " | ".join(parts)
    else:
        text = str(value or "")
    text = " ".join(text.split()).strip()
    text = text.rstrip("….").strip()
    if not text:
        return '""'
    if len(text) > max_chars:
        cut = text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,.;:")
        text = cut if cut else text[:max_chars].rstrip(" ,.;:")
    safe = text.replace('"', "'")
    return f'"{safe}"'


def _chip_label(value: object, max_words: int = 1, max_chars: int = 14) -> str:
    words = " ".join(str(value or "").split()).strip().split()
    label = (words[0] if words else "").strip(".,;:!")
    if len(label) > max_chars:
        label = label[:max_chars]
    return _q(label, max_chars)


def _content_fact_lines(
    bp_slide: object | None,
    slide_body: str,
    slide_supporting: str,
    *,
    parent_blueprint: object | None = None,
) -> list[str]:
    """Pull explanation lines to bake as content cards — SLIDE-SPECIFIC content first.

    Priority order (highest → lowest):
      1. This slide's body text (split into sentences) — unique per slide
      2. This slide's supporting line
      3. This slide's own proof_points / stat_highlights
      4. Parent blueprint sections (body sentences, NOT the global proof_points)
      5. Parent proof_points ONLY as absolute last resort when the slide has no body

    Root-cause fix: the old code added parent proof_points BEFORE slide body, causing
    the SAME 3 global facts ("Over 80%", "1944", "4 reasons") to appear on every slide.
    """
    lines: list[str] = []
    parent_fallback: list[str] = []

    # Patterns that indicate garbage / leaked content — never bake these as cards.
    _GARBAGE_RE = re.compile(
        r"""
        \d{4}\.\d{4,5}                        # arXiv paper ID (e.g. 2211.07180)
        | \d+\.\d{2}\s+(?:subscribe|buy|get)  # price + action (107.88 24.99 Subscribe)
        | \b(?:subscribe|skip|download|sign[\s-]up|log[\s-]in|click\s+here
               |read\s+more|share\s+this|follow\s+us|register|login|signup
               |dillinger|paywalled?)\b        # web nav / paywall words
        | \buse\s+as\s+proof\b                 # prompt instruction leak
        | \bthen\s+explain\b                   # prompt instruction leak
        | \bexplain\s+implication\b            # prompt instruction leak
        | \bas\s+(?:a\s+)?source\b             # prompt instruction leak
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def _clean(s: str, max_len: int = 110) -> str | None:
        from app.services.image_generation.carousel_image_prompt import (
            strip_carousel_source_citations,
        )
        t = strip_carousel_source_citations(" ".join(str(s).split()).strip())
        if not t:
            return None
        if _GARBAGE_RE.search(t):
            return None
        # Reject lines with no real words (all numbers / punctuation)
        real_words = [w for w in t.split() if re.search(r"[a-zA-Z₹]", w)]
        if len(real_words) < 3:
            return None
        if len(t) > max_len:
            cut = t[:max_len].rsplit(" ", 1)[0].strip()
            t = cut or t[:max_len]
        return t or None

    def _add(target: list[str], s: str, max_len: int = 110) -> None:
        t = _clean(s, max_len)
        if t and t not in target:
            target.append(t)

    def _prefer_numeric(items: list[str]) -> list[str]:
        return sorted(
            items,
            key=lambda x: (
                0 if re.search(r"\d|₹|%", x) else 1,
                -len(x.split()),
            ),
        )

    # ── 1. Slide body — highest priority, unique to this slide ──────────────
    body = " ".join((slide_body or "").split()).strip()
    if body:
        parts = [p.strip() for p in body.replace(";", ".").split(".") if p.strip()]
        if len(parts) >= 2:
            for part in parts[:6]:
                if len(part.split()) >= 4:
                    _add(lines, part, 130)
        else:
            words = body.split()
            if len(words) >= 20:
                third = max(6, len(words) // 3)
                _add(lines, " ".join(words[:third]), 130)
                _add(lines, " ".join(words[third : third * 2]), 130)
                _add(lines, " ".join(words[third * 2 :]), 130)
            elif len(words) >= 12:
                mid = len(words) // 2
                _add(lines, " ".join(words[:mid]), 130)
                _add(lines, " ".join(words[mid:]), 130)
            else:
                _add(lines, body, 140)

    # ── 2. Slide supporting line ─────────────────────────────────────────────
    if len(lines) < 2 and slide_supporting:
        _add(lines, slide_supporting, 130)

    # ── 3. Slide-specific proof_points / stat_highlights ────────────────────
    if bp_slide and len(lines) < 4:
        for p in list(getattr(bp_slide, "proof_points", None) or [])[:5]:
            _add(lines, str(p), 130)
        for p in list(getattr(bp_slide, "stat_highlights", None) or [])[:4]:
            _add(lines, str(p), 130)
        for c in list(getattr(bp_slide, "chip_labels", None) or [])[:3]:
            s = " ".join(str(c).split()).strip()
            if s and (any(ch.isdigit() for ch in s) or "₹" in s or "%" in s or len(s.split()) >= 3):
                _add(lines, s, 120)

    # ── 4. Parent blueprint SECTIONS (not the global proof_points) ───────────
    if parent_blueprint is not None and len(lines) < 3:
        for sec in list(getattr(parent_blueprint, "sections", None) or [])[:8]:
            body_sec = " ".join(str(getattr(sec, "body", "") or "").split()).strip()
            label = " ".join(str(getattr(sec, "section_label", "") or "").split()).strip()
            stat = " ".join(str(getattr(sec, "stat", "") or "").split()).strip()
            if stat and body_sec:
                _add(lines, f"{stat} — {body_sec}", 140)
            elif body_sec:
                _add(lines, body_sec, 140)
            elif label and stat:
                _add(lines, f"{stat} {label}", 120)

    # ── 5. Parent proof_points — LAST RESORT only when slide has NO body ─────
    if parent_blueprint is not None and not body and len(lines) < 2:
        for p in list(getattr(parent_blueprint, "stat_highlights", None) or [])[:5]:
            _add(parent_fallback, str(p), 130)
        for p in list(getattr(parent_blueprint, "proof_points", None) or [])[:4]:
            _add(parent_fallback, str(p), 130)
        for f in parent_fallback:
            if f not in lines:
                lines.append(f)
            if len(lines) >= 3:
                break

    return _prefer_numeric(lines)[:4]


def _normalize_role(role: object) -> str:
    r = str(role or "insight").strip().lower()
    aliases = {
        "hook": "hook",
        "intro": "hook",
        "define": "define",
        "definition": "define",
        "impact": "impact",
        "how": "impact",
        "mechanism": "impact",
        "why": "impact",
        "implication": "implication",
        "affect": "implication",
        "investor": "implication",
        "proof": "proof",
        "example": "proof",
        "nuance": "proof",
        "watch": "proof",
        "myth": "myth",
        "myth-bust": "myth",
        "cta": "cta",
        "close": "cta",
        "closing": "cta",
    }
    for key, val in aliases.items():
        if key in r:
            return val
    return "insight"


def _one_word_chips(values: list[str] | tuple[str, ...]) -> tuple[str, str, str] | None:
    words: list[str] = []
    for v in values:
        w = " ".join(str(v or "").split()).strip()
        if not w:
            continue
        token = w.split()[0].strip(".,;:!")
        if token:
            words.append(token[:14])
        if len(words) == 3:
            return (words[0], words[1], words[2])
    return None


def _derive_carousel_chips(
    *,
    bp_slide: object | None,
    slide_headline: str,
    slide_body: str,
) -> tuple[str, str, str]:
    if bp_slide and getattr(bp_slide, "chip_labels", None):
        got = _one_word_chips(list(bp_slide.chip_labels or []))
        if got:
            return got
    if bp_slide and getattr(bp_slide, "proof_points", None):
        got = _one_word_chips([str(p) for p in (bp_slide.proof_points or [])])
        if got:
            return got
    got = _one_word_chips([slide_headline, slide_body])
    return got or ("", "", "")


def _derive_carousel_hero(
    *,
    n: int,
    slide_headline: str,
    used_heroes: set[str],
) -> str:
    hero = f"premium 3D object matching this slide: {slide_headline or f'slide {n}'}"
    if hero in used_heroes:
        hero = f"{hero} (slide {n})"
    used_heroes.add(hero)
    return hero


def _error_free_text_block(lines: list[tuple[str, str]], *, is_carousel: bool = False) -> str:
    """Build quoted-text bake instructions (font + contrast + exact strings). Keep SHORT for image budget."""
    parts = [
        "\nEXACT BAKED TEXT (letter-perfect — never truncate mid-word):\n",
        "Font: clean sans-serif. Use Brand Space colours. Never invent currency symbols.\n",
    ]
    if is_carousel:
        parts.append("Leave bottom empty only if Brand Space has a legal footer. No AI logo.\n")
    else:
        parts.append("No legal footer strip. No AI logo.\n")
    for label, quoted in lines:
        if quoted and quoted != '""':
            parts.append(f"{label}: {quoted}\n")
    return "".join(parts)


async def layer8_visual_reasoning(state: ViolytState) -> dict:
    brand_intelligence = state.get("brand_intelligence")
    format_plan = state.get("format_plan")
    copy = state.get("copy")
    blueprint = state.get("creative_blueprint")
    creative_concepts = state.get("creative_concepts")
    user_prompt = state.get("user_prompt", "")

    brand_id = state.get("brand_id", "unknown")
    platform = state.get("platform", "linkedin")
    fmt = str(state.get("format", "static") or "static").strip().lower()
    user_prompt_l8 = str(state.get("user_prompt") or "")
    if fmt == "static" and re.search(
        r"\bcarousels?\b|\bswipe(?:able)?\b|\bmulti[- ]?slide\b", user_prompt_l8, re.I
    ):
        fmt = "carousel"
        logger.info("visual_reasoning.format_prompt_override", format="carousel")

    if not brand_intelligence or not format_plan or not copy or not creative_concepts:
        logger.error("visual_reasoning.missing_inputs")
        raise ValueError(
            "Layer 2 brand_intelligence, Layer 5 creative_concepts, Layer 6 format_plan, "
            "and Layer 7 copy are required for Layer 8"
        )

    # Prefer approved Creative Blueprint text for art direction cues
    from app.services.brand_visual_pack import BrandVisualPack, load_brand_visual_pack, visual_pack_from_state

    pack = visual_pack_from_state(state)
    if not pack.primary or pack.source == "neutral_fallback":
        try:
            pack = await load_brand_visual_pack(str(brand_id), fmt=fmt)
        except Exception as exc:
            logger.warning("visual_reasoning.visual_pack_reload_failed", error=str(exc)[:120])
    brand_name = pack.brand_name or (brand_intelligence.brand_core.brand_name or "").strip()
    brand_primary_color = pack.primary
    brand_secondary_color = pack.secondary
    brand_additional_colors = list(pack.additional or [])
    brand_typography_font = pack.font_primary
    brand_palette = pack.palette_map()
    locked_palette = pack.palette_lock()
    brand_intelligence = brand_intelligence.model_copy(
        update={
            "visual_behavior": brand_intelligence.visual_behavior.model_copy(
                update={"color_behavior": locked_palette}
            )
        }
    )
    logger.info(
        "visual_reasoning.visual_pack",
        brand_name=brand_name,
        source=pack.source,
        primary=pack.primary,
        background=pack.background,
        has_legal=pack.has_legal,
        has_mascot=pack.has_mascot,
    )
    headline = (blueprint.headline if blueprint and blueprint.headline else copy.headline)
    body = (blueprint.body if blueprint and blueprint.body else copy.body)
    supporting = (
        blueprint.supporting_line
        if blueprint and blueprint.supporting_line is not None
        else copy.supporting_line
    ) or ""
    cta = (blueprint.cta if blueprint and blueprint.cta else copy.cta) or ""
    sections = (
        [s.model_dump() for s in blueprint.sections]
        if blueprint and blueprint.sections
        else [s.model_dump() for s in copy.infographic_sections]
    )
    proof_points = (
        list(blueprint.proof_points)
        if blueprint and blueprint.proof_points
        else list(copy.proof_points or [])
    )
    stat_highlights = (
        list(blueprint.stat_highlights)
        if blueprint and blueprint.stat_highlights
        else list(copy.stat_highlights or [])
    )
    problem_statement = (
        (blueprint.problem_statement if blueprint else None) or copy.problem_statement or ""
    )
    solution_statement = (
        (blueprint.solution_statement if blueprint else None) or copy.solution_statement or ""
    )
    customer_quote = (
        (blueprint.customer_quote if blueprint else None) or copy.customer_quote or ""
    )
    customer_name = (
        (blueprint.customer_name if blueprint else None) or copy.customer_name or ""
    )
    process_steps = (
        list(blueprint.process_steps)
        if blueprint and blueprint.process_steps
        else list(copy.process_steps or [])
    )

    recommended = creative_concepts.recommended_concept

    layout_decision = classify_layout(user_prompt, fmt)
    layout_type = layout_decision.layout_type
    creative_template = resolve_creative_template(user_prompt, fmt, brand_name=brand_name)
    if creative_template.layout_type != layout_type:
        layout_type = creative_template.layout_type
    is_infographic_explain = fmt == "infographic" and layout_type == "carousel_story"
    if blueprint and is_infographic_explain:
        blueprint = repair_explain_infographic_copy(
            blueprint,
            layout_type=layout_type,
            user_prompt=user_prompt or "",
        )
        blueprint = repair_generic_headline(blueprint, layout_type=layout_type)
        headline = blueprint.headline or headline
        supporting = blueprint.supporting_line or supporting
        customer_quote = blueprint.customer_quote or customer_quote
        sections = [s.model_dump() for s in blueprint.sections] if blueprint.sections else sections
    logger.info(
        "visual_reasoning.template_locked",
        template_id=creative_template.template_id,
        layout=layout_type,
        format=fmt,
        style=creative_template.visual_style,
    )
    if blueprint:
        stale = (blueprint.layout_type or blueprint.layout_archetype or "").strip()
        if stale and stale != layout_type:
            logger.warning(
                "visual_reasoning.layout_override",
                blueprint_layout=stale,
                resolved_layout=layout_type,
                reason=layout_decision.reason,
            )
            blueprint.layout_type = layout_type
            blueprint.layout_archetype = layout_type

    # Convert Concept Pydantic model to dict
    concept_dict = {
        "concept_name": recommended.concept_name,
        "core_idea": recommended.core_idea,
        "hook": recommended.hook,
        "narrative_angle": recommended.narrative_angle,
        "visual_angle": recommended.visual_angle,
    }

    system = _prompt_builder.build_system(
        fmt=fmt,
        layout_type=layout_type,
        brand_name=brand_name,
        brand_primary_color=brand_primary_color,
        brand_secondary_color=brand_secondary_color,
        brand_typography_font=brand_typography_font,
        visual_pack=pack.to_dict(),
    )
    user = _prompt_builder.build_user(
        brand_intelligence=brand_intelligence,
        format_plan=format_plan,
        copy=copy,
        concept=concept_dict,
        user_prompt=user_prompt,
        fmt=fmt,
        layout_type=layout_type,
    )

    # Visual-semantic blueprint from Content Intelligence (Phase-1 package)
    content_intelligence = state.get("content_intelligence")
    if content_intelligence and getattr(content_intelligence, "format_architecture", None):
        fa = content_intelligence.format_architecture
        thesis = getattr(content_intelligence, "insight_thesis", "") or ""
        beats = getattr(content_intelligence, "narrative_beats", None) or []
        beat_lines = "; ".join(
            f"[{getattr(b, 'role', '')}] {getattr(b, 'message', '')}"
            for b in beats[:6]
        )
        user = (
            user
            + "\n\n════════════════════════════════════════\n"
            + "VISUAL-SEMANTIC BLUEPRINT (EXECUTE THIS HIERARCHY)\n"
            + "════════════════════════════════════════\n"
            + f"INSIGHT THESIS: {thesis}\n"
            + f"HERO STATISTIC (largest visual number): {fa.hero_statistic}\n"
            + f"SUPPORTING DATA POINTS: {fa.supporting_data_points}\n"
            + f"CORE INSIGHT: {fa.core_insight}\n"
            + f"HIERARCHY: {fa.hierarchy_notes}\n"
            + f"VISUAL PLAN: {fa.visual_plan}\n"
            + (f"NARRATIVE BEATS: {beat_lines}\n" if beat_lines else "")
            + "Hero statistic must dominate. Supporting cards secondary. "
            "Do not give equal visual weight to every box. "
            "Complete sentences only. Spell UDAN correctly (never ADAN).\n"
        )

    if blueprint:
        story = "; ".join(blueprint.story_flow or [])
        source_footer = (blueprint.source_footer or "").strip()
        sources_note = ""
        if blueprint.sources:
            sources_note = "; ".join(
                f"{s.title or 'source'}: {s.url}" for s in blueprint.sources[:4] if s.url
            )
        user = (
            user
            + "\n\n════════════════════════════════════════\n"
            + "USER-APPROVED CREATIVE BLUEPRINT — LOCK THIS EXACTLY\n"
            + "════════════════════════════════════════\n"
            + "The user reviewed and approved these EXACT strings. Render them word-for-word in the image.\n"
            + "DO NOT paraphrase, summarise, or replace ANY approved text with your own wording.\n"
            + "DO NOT change the topic, facts, or messaging from what is listed below.\n"
            + f"HEADLINE (render EXACTLY): \"{headline}\"\n"
            + (f"SUPPORTING LINE (render EXACTLY): \"{supporting}\"\n" if supporting else "")
            + (f"BODY TEXT (render EXACTLY): \"{body}\"\n" if body else "")
            + (f"CTA (render EXACTLY): \"{cta}\"\n" if cta else "")
            + (f"HOOK: \"{blueprint.hook}\"\n" if blueprint.hook else "")
            + (f"STORY FLOW: {story}\n" if story else "")
            + (f"SECTIONS (render these section labels/facts): {sections}\n" if sections else "")
            + (
                "SECTION UNIQUENESS LOCK: every section body/insight line above is DISTINCT. "
                "Render each card with its OWN body — never repeat one sentence across cards.\n"
                if sections and len(sections) >= 2
                else ""
            )
            + (f"PROOF POINTS: {proof_points}\n" if proof_points else "")
            + (f"STAT HIGHLIGHTS: {stat_highlights}\n" if stat_highlights else "")
            + (
                # Carousel: NEVER bake source / survey names into slide images.
                ""
                if fmt == "carousel"
                else (f"SOURCE FOOTER: \"{source_footer}\"\n" if source_footer else "")
            )
            + f"layout_type={layout_type} layout={blueprint.layout_archetype} purpose={blueprint.purpose}\n"
            + "════════════════════════════════════════\n"
            + "CRITICAL: Generate a FINISHED creative. Render the approved strings as sharp typography in the image. "
            "Do not leave empty shells. Do not invent alternate copy. The approved headline/body/sections are FINAL — do not rewrite them. "
            + (
                f"REQUIRED: use {brand_name}'s EXACT Brand Space hexes ONLY — "
                + f"PRIMARY {pack.primary}, SECONDARY {pack.secondary}, ACCENT {pack.accent}, "
                + f"BACKGROUND {pack.background}. "
                + "Do NOT paint sample navy (#0B2C5F/#003975) or sample orange (#FFA400) "
                + "unless that exact hex is listed above. "
                + (f"FONT: {pack.font_primary} — use this font for all headlines; " if pack.font_primary else "")
                + "AUDIENCE: depict the EXACT target audience from Brand Space persona. "
            )
            + "ULTRA-PREMIUM clay-3D icons; content must fit fully. "
            + (
                "CAROUSEL: do NOT bake any Source line, survey name, or institution cite into slides. "
                if fmt == "carousel"
                else (
                    (
                        f'Bake compact footer text EXACTLY as: "{source_footer}". '
                        if source_footer
                        else "If no source_footer, omit Source line (do not invent domains). "
                    )
                    + SOURCE_FOOTER_RULE
                )
            )
        )

    # Size computation early — needed by expander prompts AND image generation
    size = size_string(fmt, platform)
    canvas_desc = canvas_label(fmt, platform)
    logger.info("visual_reasoning.canvas_size", format=fmt, platform=platform, size=size)

    # 1. Complete visual reasoning structure (GPT-4o)
    service = _router.get_service("l8_visual_reasoning")
    output, metadata = await service.complete_structured(
        system=system,
        user=user,
        output_model=VisualReasoningOutput,
        layer="l8_visual_reasoning",
        max_tokens=8192,
    )

    # 1b. STAGE 2: Expand image prompt — SKIP for carousel (per-slide prompts are built below;
    # expander output was unused and burned tokens every run).
    expander_meta: dict = {}
    image_gen_prompt = output.image_prompt_direction
    if fmt == "carousel" or is_infographic_explain:
        logger.info(
            "visual_reasoning.prompt_expansion_skipped",
            reason="carousel_or_explain_uses_direct_image_prompt",
        )
    else:
        logger.info(
            "visual_reasoning.prompt_expansion_start",
            initial_prompt_len=len(output.image_prompt_direction),
        )
        expander_system = _prompt_builder.build_expander_system(
            dominant_visual_system=output.dominant_visual_system,
            fmt=fmt,
            brand_name=brand_name,
        )
        expander_user = _prompt_builder.build_expander_user(
            brand_name=brand_intelligence.brand_core.brand_name,
            visual_mood=brand_intelligence.visual_behavior.visual_mood,
            color_behavior=brand_intelligence.visual_behavior.color_behavior,
            image_behavior=brand_intelligence.visual_behavior.image_behavior,
            design_sophistication=brand_intelligence.visual_behavior.design_sophistication,
            concept_name=concept_dict.get("concept_name", ""),
            core_idea=concept_dict.get("core_idea", ""),
            visual_angle=concept_dict.get("visual_angle", ""),
            copy_headline=headline,
            copy_body=body,
            supporting_line=supporting,
            cta=cta,
            infographic_sections=sections,
            proof_points=proof_points,
            stat_highlights=stat_highlights,
            problem_statement=problem_statement,
            solution_statement=solution_statement,
            customer_quote=customer_quote,
            customer_name=customer_name,
            process_steps=process_steps,
            format_strategy=format_plan.format_strategy,
            layout_archetype=(
                blueprint.layout_archetype if blueprint and blueprint.layout_archetype else format_plan.layout_archetype
            ),
            platform=platform,
            initial_prompt=output.image_prompt_direction,
            user_prompt=user_prompt,
            dominant_visual_system=output.dominant_visual_system,
            fmt=fmt,
            layout_type=layout_type,
            hook=(blueprint.hook if blueprint else "") or getattr(copy, "hook", None) or "",
            story_flow=list(blueprint.story_flow) if blueprint and blueprint.story_flow else [],
            slides=(
                [s.model_dump() for s in blueprint.slides]
                if blueprint and blueprint.slides
                else [s.model_dump() for s in (copy.slide_copy or [])]
            ),
            canvas=canvas_desc,
            background=pack.background,
            primary=pack.primary,
            secondary=pack.secondary,
            accent=pack.accent,
        )

        try:
            expanded_prompt, expander_meta = await service.complete_text(
                system=expander_system,
                user=expander_user,
                layer="l8_prompt_expander",
                temperature=0.35,
                max_tokens=2048,
            )
            logger.info(
                "visual_reasoning.prompt_expansion_complete",
                expanded_prompt_len=len(expanded_prompt),
                expander_tokens=expander_meta.get("output_tokens", 0),
            )
            exact_lock = (
                "\n\nLOCKED EXACT COPY (bake letter-perfect — do not rewrite):\n"
                f'Headline: "{headline}"\n'
                f'Supporting: "{supporting}"\n'
                f'CTA: "{cta}"\n'
            )
            if sections:
                exact_lock += "Sections:\n"
                for i, sec in enumerate(sections[:15], start=1):
                    if isinstance(sec, dict):
                        lab = str(sec.get("section_label") or "").strip()
                        if not lab or lab.casefold() in {"item", f"item {i}"}:
                            body = str(sec.get("body") or "").strip()
                            incs_raw = sec.get("includes") or []
                            first = (
                                str(incs_raw[0]).strip()
                                if isinstance(incs_raw, list) and incs_raw
                                else ""
                            )
                            lab = " ".join((body or first).split()[:8]).rstrip(".,;:") or f"Point {i}"
                        st = sec.get("stat") or ""
                        incs = sec.get("includes") or []
                        if isinstance(incs, list):
                            incs_txt = "; ".join(str(x) for x in incs[:2])
                        else:
                            incs_txt = str(incs)
                        exact_lock += f'{i}. "{lab}" | "{st}" | "{incs_txt}"\n'
            palette_lock = pack.palette_lock()
            image_gen_prompt = (expanded_prompt + exact_lock + f"\n{ICON_STYLE_LOCK}\n")[
                : 6000 - len(palette_lock)
            ] + palette_lock
            brand_icon_lock = (
                "\nBRAND ICON LOCK: Match THIS brand's visual mood and topic objects only. "
                f"Brand: {brand_name or 'active Brand Space'}. "
                "Do NOT invent another brand's icon set.\n"
            )
            image_gen_prompt = (image_gen_prompt + brand_icon_lock)[:6000]
            output.image_prompt_direction = image_gen_prompt
        except Exception as e:
            logger.warning(
                f"visual_reasoning.prompt_expansion_failed, using original prompt: {e}"
            )
            image_gen_prompt = output.image_prompt_direction

    # 2. Get the correct tenant_id and brand logo path from DB
    tenant_id = None
    logo_storage_path: str | None = None
    logo_zone_instruction: str | None = brand_intelligence.visual_behavior.logo_zone_instruction

    try:
        brand_uuid = UUID(str(brand_id)) if not isinstance(brand_id, UUID) else brand_id
        async with AsyncSessionLocal() as session:
            brand = await session.get(BrandSpace, brand_uuid)
            if brand:
                tenant_id = brand.tenant_id

            # Fetch the brand logo path for composite overlay
            logo_storage_path = await get_brand_logo_storage_path(
                brand_space_id=brand_uuid,
                session=session,
            )

        if logo_storage_path:
            logger.info(
                "visual_reasoning.logo_found",
                logo_path=logo_storage_path,
                zone=logo_zone_instruction,
            )
        else:
            logger.info(
                "visual_reasoning.logo_not_found",
                brand_id=str(brand_id),
            )
    except Exception as e:
        logger.warning(f"visual_reasoning.db_tenant_or_logo_failed: {e}")

    # Fallback default UUID if DB call fails
    if not tenant_id:
        tenant_id = UUID("00000000-0000-0000-0000-000000000000")

    # 4. Image generation with gpt-image-1 + brand logo composite, falling back to SDXL/Mock
    # Reserve room for the mandatory contract so no builder's COPY block gets chopped.
    _mandatory_lock = build_lock_from_pack(pack, fmt=fmt)
    _content_budget = max(2000, _IMAGE_PROMPT_BUDGET - len(_mandatory_lock) - 8)

    async def _generate_one_image(
        prompt: str,
        image_size: str,
        fallback_suffix: str = "",
        *,
        composite_legal_footer: bool = False,
        image_quality: str | None = None,
        skip_extra_locks: bool = False,
        letterbox_to_aspect: bool = False,
        composite_close_mascot: bool = False,
    ) -> str:
        wipe_reserved_corner = True
        extra = ""
        if not skip_extra_locks:
            extra = pack.image_extra_locks(fmt=fmt)
        # Applies to EVERY brand, format and platform — never skipped, never trimmed.
        safe_prompt = _budget_prompt(
            prompt,
            extra,
            _IMAGE_PROMPT_BUDGET,
            mandatory=_mandatory_lock,
        )
        logger.info(
            "visual_reasoning.image_prompt_budget",
            suffix=fallback_suffix,
            prompt_len=len(safe_prompt),
            has_headline=("HEADLINE" in safe_prompt) or ("Headline:" in safe_prompt),
            carousel=composite_legal_footer,
        )
        try:
            dalle = DalleService()
            url = await dalle.generate_and_save(
                tenant_id=tenant_id,
                brand_space_id=brand_id,
                prompt=safe_prompt,
                size=image_size,
                logo_storage_path=logo_storage_path,
                logo_zone_instruction=logo_zone_instruction
                or "plain empty top-right corner — no text, no box, no logo drawn",
                composite_legal_footer=composite_legal_footer,
                legal_footer_text=pack.legal_footer if composite_legal_footer else "",
                wipe_reserved_corner=True,
                quality=image_quality,
                letterbox_to_aspect=letterbox_to_aspect,
                composite_close_mascot=composite_close_mascot,
                close_mascot_storage_path=pack.mascot_storage_path if composite_close_mascot else "",
                canvas_bg_hex=pack.background,
                composite_cta_text=(cta or "Explore More") if fmt in {"static", "infographic"} else "",
                cta_accent_hex=pack.accent if fmt in {"static", "infographic"} else "",
                legal_color_hex=pack.legal_color,
            )
            logger.info(
                "visual_reasoning.dalle_success",
                url=url,
                suffix=fallback_suffix,
                logo_composited=bool(logo_storage_path),
            )
            return url
        except Exception as e:
            logger.warning(
                f"visual_reasoning.dalle_failed{fallback_suffix}, falling back to SDXL: {type(e).__name__}: {e}"
            )
            try:
                from app.integrations.object_storage import get_object_storage
                from app.services.image_generation.dalle_service import apply_brand_image_overlays

                sdxl = SdxlService()
                sdxl_url = await sdxl.generate_and_save(
                    tenant_id=tenant_id,
                    brand_space_id=brand_id,
                    prompt=safe_prompt,
                    size=image_size,
                )
                if (
                    logo_storage_path
                    or composite_legal_footer
                    or wipe_reserved_corner
                    or composite_close_mascot
                ):
                    storage = get_object_storage()
                    rel_path = sdxl_url.removeprefix("/storage/").lstrip("/")
                    raw_bytes = storage.read_bytes(rel_path)
                    processed = apply_brand_image_overlays(
                        raw_bytes,
                        storage=storage,
                        logo_storage_path=logo_storage_path,
                        logo_zone_instruction=logo_zone_instruction,
                        composite_legal_footer=composite_legal_footer,
                        legal_footer_text=pack.legal_footer if composite_legal_footer else "",
                        wipe_reserved_corner=wipe_reserved_corner,
                        composite_close_mascot=composite_close_mascot,
                        close_mascot_storage_path=pack.mascot_storage_path if composite_close_mascot else "",
                        canvas_bg_hex=pack.background,
                        legal_color_hex=pack.legal_color,
                    )
                    filename = f"sdxl-branded-{uuid4().hex[:8]}.png"
                    stored = storage.save_bytes(
                        tenant_id=UUID(str(tenant_id)),
                        brand_space_id=UUID(str(brand_id)),
                        category="generated",
                        filename=filename,
                        content=processed,
                    )
                    url = f"/storage/{stored.storage_path}"
                else:
                    url = sdxl_url
                logger.info(
                    "visual_reasoning.sdxl_success",
                    url=url,
                    suffix=fallback_suffix,
                    logo_composited=bool(logo_storage_path),
                )
                return url
            except Exception as e_sdxl:
                logger.error(f"visual_reasoning.sdxl_failed{fallback_suffix}: {e_sdxl}")
                raise RuntimeError(
                    f"Image generation failed for {fallback_suffix or 'creative'} "
                    f"(DALL·E: {type(e).__name__}; SDXL: {type(e_sdxl).__name__}: {e_sdxl})"
                ) from e_sdxl

    generated_urls: list[str] = []
    # Prefer approved blueprint slides as the carousel source of truth
    carousel_slides = list(format_plan.slide_plan or [])
    if fmt == "carousel" and blueprint and blueprint.slides:
        from types import SimpleNamespace

        carousel_slides = [
            SimpleNamespace(
                slide_number=s.slide_number,
                focus=s.role or "insight",
                visual_intent=s.headline or "",
            )
            for s in blueprint.slides
        ]
    elif fmt == "carousel" and not carousel_slides and copy.slide_copy:
        from types import SimpleNamespace

        carousel_slides = [
            SimpleNamespace(
                slide_number=s.slide_number,
                focus="insight",
                visual_intent=s.headline or "",
            )
            for s in copy.slide_copy
        ]

    if fmt == "carousel" and not carousel_slides:
        raise ValueError(
            "Carousel selected but no slides were prepared in the blueprint. "
            "Re-run Phase 1 or add slides on the approval card before generating."
        )
    if fmt == "carousel" and len(carousel_slides) < 4:
        raise ValueError(
            f"Carousel selected but only {len(carousel_slides)} slide(s) are ready "
            "(need at least 4). Re-run Phase 1 or add slides before generating."
        )

    if fmt == "carousel" and carousel_slides:
        slide_copy_by_number = {s.slide_number: s for s in (copy.slide_copy or [])}
        blueprint_slides = {
            s.slide_number: s for s in ((blueprint.slides if blueprint else None) or [])
        }
        # SHORT style stub ONLY — mega-locks were ~16k chars and wiped slide content at [:6500]
        from app.services.image_generation.carousel_image_prompt import build_carousel_style_stub

        style_stub = (
            f"Finished {platform} carousel for {brand_name}, canvas {canvas_desc}. "
            f"{build_carousel_style_stub(brand_palette)} "
            f"{pack.palette_lock()}"
        )
        total = len(carousel_slides)
        # Build ordered storyline from blueprint for swipe continuity
        ordered_bp = sorted(
            ((blueprint.slides if blueprint else None) or []),
            key=lambda s: s.slide_number,
        )
        storyline_lines = []
        for s in ordered_bp:
            storyline_lines.append(
                f"{s.slide_number}. [{s.role}] {s.headline} — {(s.body or '')[:80]}"
            )
        if not storyline_lines and blueprint and blueprint.story_flow:
            storyline_lines = [str(x) for x in blueprint.story_flow]
        storyline_block = "\n".join(storyline_lines) or "(derive from per-slide headlines)"
        topic_lock = _q(user_prompt, 160)
        used_heroes: set[str] = set()
        used_headlines: list[str] = []

        for idx, slide in enumerate(carousel_slides):
            bp_slide = blueprint_slides.get(slide.slide_number)
            slide_copy = slide_copy_by_number.get(slide.slide_number)
            n = int(getattr(slide, "slide_number", 0) or 0) or (idx + 1)
            slide_headline = (
                (bp_slide.headline if bp_slide else None)
                or (slide_copy.headline if slide_copy else None)
                or getattr(slide, "visual_intent", None)
                or f"Slide {n}"
            )
            slide_body = (
                (bp_slide.body if bp_slide else None)
                or (slide_copy.body if slide_copy else None)
                or ""
            )
            slide_cta = (
                (bp_slide.cta if bp_slide else None)
                or (slide_copy.cta if slide_copy else None)
                or ""
            )
            slide_supporting = (
                (bp_slide.supporting_line if bp_slide else None)
                or (getattr(slide_copy, "supporting_line", None) if slide_copy else None)
                or ""
            )
            role_raw = (
                (bp_slide.role if bp_slide else None)
                or getattr(slide, "focus", None)
                or "insight"
            )
            role = _normalize_role(role_raw)
            prev_hl = ""
            next_hl = ""
            if ordered_bp:
                for j, s in enumerate(ordered_bp):
                    if s.slide_number == n:
                        if j > 0:
                            prev_hl = ordered_bp[j - 1].headline or ""
                        if j + 1 < len(ordered_bp):
                            next_hl = ordered_bp[j + 1].headline or ""
                        break
            hero = _derive_carousel_hero(
                n=n,
                slide_headline=str(slide_headline or ""),
                used_heroes=used_heroes,
            )
            bottoms = _derive_carousel_chips(
                bp_slide=bp_slide,
                slide_headline=str(slide_headline or ""),
                slide_body=str(slide_body or ""),
            )

            is_last = n == total or role == "cta"
            if not (slide_supporting or "").strip():
                slide_supporting = (slide_body or "").split(".")[0].strip()[:90]
            if not str(slide_headline or "").strip():
                slide_headline = (slide_body or "").split(".")[0].strip() or f"Slide {n}"

            hl_words = str(slide_headline or "").split()
            # Prefer complete headlines — never leave dangling verbs ("drive", "are").
            if len(hl_words) > 12:
                hl_words = hl_words[:12]
            _dangling = {
                "a", "an", "the", "and", "or", "with", "for", "to", "of", "in", "on",
                "is", "are", "drive", "drives", "make", "makes", "how", "why", "what",
            }
            while hl_words and hl_words[-1].strip(".,;:?!").casefold() in _dangling:
                hl_words.pop()
            slide_headline = " ".join(hl_words).rstrip(".,;:") if hl_words else str(slide_headline or "")

            fact_lines = _content_fact_lines(
                bp_slide,
                str(slide_body or ""),
                str(slide_supporting or ""),
                parent_blueprint=blueprint,
            )

            hl = _q(slide_headline, 80)
            sup = _q(slide_supporting, 140)
            body_txt = _q(slide_body, 320)
            fact_q = [_q(f, 110) for f in fact_lines[:4]]
            prior = "; ".join(used_headlines[-3:]) if used_headlines else "(none yet)"
            used_headlines.append(str(slide_headline or "")[:60])

            from app.services.image_generation.carousel_image_prompt import (
                build_carousel_slide_image_prompt,
                strip_carousel_heading_numbers,
                strip_carousel_source_citations,
            )

            story_blocks = [
                str(x).strip('"')
                for x in fact_q
                if str(x).strip() and str(x).strip() != '""'
            ]
            story_blocks = [b.strip('"') for b in story_blocks if b.strip('"')]
            slide_headline = strip_carousel_heading_numbers(str(slide_headline or ""))
            slide_headline = strip_carousel_source_citations(str(slide_headline or ""))
            slide_supporting = strip_carousel_source_citations(str(slide_supporting or ""))
            slide_body = strip_carousel_source_citations(str(slide_body or ""))
            story_blocks = [
                strip_carousel_source_citations(b) for b in story_blocks if b
            ]
            # Prefer 2–3 fully-visible teaching cards (depth over clutter).
            story_blocks = [b for b in story_blocks if b][:3]

            color_behavior = ""
            if brand_intelligence and brand_intelligence.visual_behavior:
                color_behavior = str(brand_intelligence.visual_behavior.color_behavior or "")

            slide_prompt = build_carousel_slide_image_prompt(
                slide_number=n,
                total_slides=total,
                role=role,
                headline=str(slide_headline or ""),
                supporting=str(slide_supporting or ""),
                body=str(slide_body or ""),
                story_blocks=story_blocks,
                cta=str(slide_cta or "") if is_last else "",
                canvas_desc=canvas_desc,
                topic=str(topic_lock or ""),
                is_last=is_last,
                prior_headlines=list(used_headlines[:-1]) if used_headlines else [],
                palette=brand_palette,
                has_legal=pack.has_legal,
                has_mascot=pack.has_mascot,
                brand_name=brand_name,
            )
            carousel_style_extra = style_stub
            # Keep continuity + prior-headline guard under budget without wiping locked DNA
            continuity = (
                f"\nSTORYLINE:\n{storyline_block}\n"
                f"Prior headlines (do not repeat): {prior}\n"
                f"Hero cue: {hero}\n"
            )
            slide_prompt = _budget_prompt(
                slide_prompt,
                continuity + "\n" + carousel_style_extra,
                _content_budget,
            )
            logger.info(
                "visual_reasoning.carousel_slide_prompt",
                slide=n,
                role=role,
                prompt_len=len(slide_prompt),
                has_headline=hl in slide_prompt or "HEADLINE" in slide_prompt,
                headline=str(slide_headline or "")[:60],
            )
            slide_url = await _generate_one_image(
                slide_prompt,
                size,
                f"-slide-{n}",
                composite_legal_footer=pack.has_legal,
                composite_close_mascot=bool(pack.has_mascot and is_last),
            )
            generated_urls.append(slide_url)
    else:
        # Static / hub / ranking / trade / explain — AI image only (NO Pillow renderers).
        from app.services.image_generation.ranking_board import sanitize_ranking_text

        if is_infographic_explain and blueprint:
            color_behavior = ""
            if brand_intelligence and brand_intelligence.visual_behavior:
                color_behavior = str(brand_intelligence.visual_behavior.color_behavior or "")

            from app.services.image_generation.data_story_image_prompt import (
                build_data_story_prompt,
            )

            explain_prompt = build_data_story_prompt(
                blueprint,
                canvas_desc=canvas_desc,
                supporting=supporting or "",
                palette=brand_palette,
            )
            logger.info(
                "visual_reasoning.data_story_prompt_built",
                stats=len(blueprint.stat_highlights or []),
                sections=len(blueprint.sections or []),
            )
            logger.info(
                "visual_reasoning.explain_ai_prompt",
                prompt_len=len(explain_prompt),
                headline=(blueprint.headline or "")[:60],
                sections=len(blueprint.sections or []),
            )
            last_err: Exception | None = None
            for attempt in range(2):
                try:
                    suffix = "" if attempt == 0 else "-explain-retry"
                    prompt_try = explain_prompt
                    if attempt == 1:
                        prompt_try = (
                            explain_prompt
                            + "\nRETRY: Previous output had spelling errors. "
                            "Render ONLY the quoted COPY block — zero paraphrase.\n"
                        )
                    single_url = await _generate_one_image(
                        # The structured data-story prompt runs ~5.8k; a 6k cap
                        # silently amputated the AVOID block at the end.
                        prompt_try[:9000],
                        size,
                        suffix,
                        composite_legal_footer=False,
                        image_quality="high",
                        skip_extra_locks=True,
                        # Fit 2:3 API canvas into 4:5 without chopping headline
                        # or takeaway — centre-crop was amputating edge text.
                        letterbox_to_aspect=True,
                    )
                    generated_urls.append(single_url)
                    break
                except Exception as exc:
                    last_err = exc
                    logger.warning(
                        "visual_reasoning.explain_ai_attempt_failed",
                        attempt=attempt + 1,
                        error=str(exc)[:200],
                    )
            else:
                raise RuntimeError(
                    f"Explain infographic image failed after 2 attempts: {last_err}"
                ) from last_err
        else:
            from app.services.image_generation.dense_content_bake import (
                DENSE_LAYOUT_LOCK,
                extract_dense_cards,
                format_dense_cards_block,
                format_dense_stats_block,
                scrub as _dense_scrub,
            )
            from app.services.image_generation.lean_static_prompt import (
                build_lean_static_prompt,
                cards_from_blueprint,
            )

            text_bake_suffix = _error_free_text_block(
                [
                    ("HEADLINE", _q(sanitize_ranking_text(str(headline or "")), 140)),
                    ("SUPPORTING LINE", _q(sanitize_ranking_text(str(supporting or "")), 200)),
                    ("BODY", _q(body, 320)),
                    ("CTA", _q(sanitize_ranking_text(str(cta or "")), 40)),
                    ("PROBLEM", _q(problem_statement, 180)),
                    ("SOLUTION", _q(solution_statement, 180)),
                    ("STATS", _q(stat_highlights, 220)),
                    ("PROOF POINTS", _q(proof_points, 220)),
                    ("PROCESS STEPS", _q(process_steps, 180)),
                    ("QUOTE", _q(customer_quote, 180)),
                    ("QUOTE ATTRIBUTION", _q(customer_name, 60)),
                    (
                        "SOURCE FOOTER",
                        _q(
                            sanitize_ranking_text(
                                str((blueprint.source_footer if blueprint else "") or "")
                            ),
                            100,
                        ),
                    ),
                ],
                is_carousel=False,
            )
            card_bake = ""
            is_rank_layout = layout_type == "static_ranking"
            # LinkedIn static is short landscape (~627px) — long card bodies get clipped.
            try:
                _ew, _eh = (int(x) for x in str(size).split("x")[:2])
            except Exception:
                _ew, _eh = 1080, 1080
            is_short_landscape = fmt == "static" and _ew > _eh and _eh <= 720
            max_card_words = 10 if is_short_landscape else 28
            max_cards = 4 if is_short_landscape else (8 if not is_rank_layout else 12)

            # Landscape static: one lean copy-first prompt under budget — do NOT
            # concatenate expander + dense locks (that was truncating rules).
            if is_short_landscape and blueprint and not is_rank_layout:
                lean_cards = cards_from_blueprint(
                    blueprint, max_cards=4, max_words=8
                )
                if not lean_cards:
                    lean_cards = [
                        {
                            "title": (c.get("title") or "")[:],
                            "body": "",
                            "stat": "",
                        }
                        for c in extract_dense_cards(blueprint, max_cards=4)
                    ]
                lean_prompt = build_lean_static_prompt(
                    canvas_desc=canvas_desc,
                    headline=str(headline or ""),
                    supporting=str(supporting or ""),
                    cards=lean_cards,
                    palette=brand_palette,
                    brand_name=brand_name,
                    cta=str(cta or "Explore More"),
                )
                logger.info(
                    "visual_reasoning.lean_static_prompt",
                    prompt_len=len(lean_prompt),
                    cards=len(lean_cards),
                    budget=_content_budget,
                )
                single_url = await _generate_one_image(
                    lean_prompt[:_content_budget],
                    size,
                    composite_legal_footer=False,
                    skip_extra_locks=True,
                )
                generated_urls.append(single_url)
            else:
                if blueprint:
                    dense_cards = extract_dense_cards(blueprint, max_cards=max_cards)
                    if is_short_landscape:
                        for card in dense_cards:
                            body_c = (card.get("body") or "").strip()
                            title = (card.get("title") or "").strip()
                            if body_c and title and body_c.casefold() != title.casefold():
                                card["body"] = _dense_scrub(body_c, max_words=max_card_words)
                            else:
                                card["body"] = ""
                    card_lines = [
                        "\nEXACT CARD / ROW TEXT — bake ONLY these quoted strings (zero invented words):\n",
                        DENSE_LAYOUT_LOCK,
                        "\n",
                        format_dense_stats_block(blueprint, max_stats=4 if is_short_landscape else 6),
                    ]
                    if is_rank_layout and (blueprint.sections or []):
                        for i, sec in enumerate((blueprint.sections or [])[:12], start=1):
                            raw_label = (sec.section_label or "").strip()
                            sec_body = (sec.body or "").strip()
                            first = next(
                                (str(x).strip() for x in (sec.includes or []) if str(x).strip()),
                                "",
                            )
                            if not raw_label or raw_label.casefold() in {"item", f"item {i}"}:
                                raw_label = (
                                    " ".join((sec_body or first).split()[:8]).rstrip(".,;:")
                                    or f"Point {i}"
                                )
                            label = sanitize_ranking_text(raw_label)
                            stat = sanitize_ranking_text(str(sec.stat or "").strip())
                            if stat:
                                import re as _re

                                stat = _re.sub(r"US\s*\$", "USD ", stat, flags=_re.I)
                                stat = _re.sub(r"\$", "", stat)
                            body_line = _dense_scrub(sec_body or first, max_words=22)
                            card_lines.append(f'ROW {i} name: "{label}"\n')
                            if stat:
                                card_lines.append(f'ROW {i} metric: "{stat}"\n')
                            if body_line:
                                card_lines.append(f'ROW {i} BODY: "{body_line}"\n')
                    elif dense_cards:
                        card_lines.append(format_dense_cards_block(dense_cards))
                    elif blueprint.sections:
                        for i, sec in enumerate((blueprint.sections or [])[:max_cards], start=1):
                            label = sanitize_ranking_text(
                                (sec.section_label or f"Point {i}").strip()
                            )
                            body_line = _dense_scrub(sec.body or "", max_words=max_card_words)
                            if not body_line:
                                first = next(
                                    (
                                        str(x).strip()
                                        for x in (sec.includes or [])
                                        if str(x).strip()
                                    ),
                                    "",
                                )
                                body_line = _dense_scrub(first, max_words=max_card_words)
                            if is_short_landscape and body_line.casefold() == label.casefold():
                                body_line = ""
                            if body_line:
                                card_lines.append(
                                    f'CARD {i}: SMALL ICON + TITLE "{label}" + BODY "{body_line}"\n'
                                )
                            else:
                                card_lines.append(
                                    f'CARD {i}: SMALL ICON + TITLE "{label}" (no body line — title only)\n'
                                )
                    card_lines.append(
                        f"Layout: {creative_template.image_stub}\n"
                        "Icons SMALL. Bake every TITLE + BODY. Prefer latest numbers.\n"
                    )
                    card_bake = "".join(card_lines)

                layout_hint = creative_template.l8_image_hint(canvas_desc=canvas_desc)
                if creative_template.layout_type == "static_ranking":
                    layout_hint += f"\n{INFOGRAPHIC_AUDIENCE_TONE_LOCK}\n"
                layout_hint += (
                    f"Canvas size LOCKED: {canvas_desc}. Fit every element inside with >=8% side/top margins "
                    "and >=14% EMPTY bottom reserve (NO baked CTA — CTA is composited in post).\n"
                    "ONE full-bleed Brand Space background only — never a nested white/pale page panel "
                    "or second background colour.\n"
                    "Never clip text/icons. Never break a word mid-letter (no 'c'+'an').\n"
                    "Icon materials ONLY Brand Space hexes — no green/mint/teal/gold.\n"
                    "SPELLING: bake letter-perfect locked copy only — no invented typos.\n"
                    "STATIC/INFOGRAPHIC: dense structured cards with small icons + neat paragraphs.\n"
                )
                # Put dense card copy first so the prompt cut never drops the facts.
                single_url = await _generate_one_image(
                    (card_bake + text_bake_suffix + layout_hint + image_gen_prompt)[:_content_budget],
                    size,
                    composite_legal_footer=False,
                )
                generated_urls.append(single_url)

    # Set the generated image fields on the output Pydantic model
    output.generated_image_url = generated_urls[0] if generated_urls else ""
    output.generated_image_urls = generated_urls

    total_l8_latency = metadata["latency_ms"]
    total_l8_input = metadata["input_tokens"]
    total_l8_output = metadata["output_tokens"]
    try:
        total_l8_latency += expander_meta["latency_ms"]
        total_l8_input += expander_meta["input_tokens"]
        total_l8_output += expander_meta["output_tokens"]
    except (KeyError, TypeError):
        pass

    return {
        "visual_reasoning": output,
        "layer_latencies": {"l8_visual_reasoning": total_l8_latency},
        "token_usage": {
            "l8_visual_reasoning": {
                "input_tokens": total_l8_input,
                "output_tokens": total_l8_output,
            }
        },
    }
