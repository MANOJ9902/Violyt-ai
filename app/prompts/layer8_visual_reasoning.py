from __future__ import annotations

from typing import Any

from app.graph.models.layer2_models import BrandIntelligenceOutput
from app.graph.models.layer6_models import FormatPlanOutput
from app.graph.models.layer7_models import CopyOutput
from app.prompts.base import BasePromptBuilder
from app.prompts.brand_visual_palette import (
    resolve_brand_palette_lock,
    static_background_instruction,
)
from app.prompts.brand_copy_tone import (
    NEUTRAL_BG,
    NEUTRAL_HEADLINE,
    NEUTRAL_ACCENT,
    NEUTRAL_BODY,
    NEUTRAL_CARD,
    SOURCE_FOOTER_RULE,
    LEGAL_FOOTER_HINT,
    NO_LEGAL_STATIC_RULE,
    CAROUSEL_FIT_LOCK,
    UNIVERSAL_FIT_LOCK,
    ICON_STYLE_LOCK,
    ORANGE_COVERAGE_LOCK,
    HEADLINE_COLOR_LOCK,
    CONTENT_DEPTH_LOCK,
    CAROUSEL_ICON_LOCK,
    CAROUSEL_TEXT_FIT_LOCK,
    CAROUSEL_AUDIENCE_TONE_LOCK,
    PREMIUM_HD_ICON_LOCK,
    EDUCATION_POSTER_LAYOUT_LOCK,
    INFOGRAPHIC_EXPLAIN_LAYOUT_LOCK,
    INFOGRAPHIC_EXPLAIN_ORANGE_STUB,
    INFOGRAPHIC_EXPLAIN_QUALITY_LOCK,
    STATIC_EXPLAIN_LAYOUT_LOCK,
    STATIC_EXPLAIN_QUALITY_LOCK,
    STATIC_ORANGE_STUB,
    STATIC_RANKING_INSIGHT_LOCK,
    STATIC_HORIZONTAL_BAR_DNA_LOCK,
    STATIC_HORIZONTAL_BAR_IMAGE_STUB,
    INFOGRAPHIC_AUDIENCE_TONE_LOCK,
    INFOGRAPHIC_RANKING_FORMAT_LOCK,
    INFOGRAPHIC_TRADE_BOARD_LOCK,
    RANKING_IMAGE_STUB,
    STATIC_IMAGE_EXTRA_LOCKS,
)
from app.prompts.creative_sizes import size_string, canvas_label


class VisualReasoningPromptBuilder(BasePromptBuilder):
    """Layer 8 Visual Reasoning — composition from Brand Space + approved copy."""

    PROMPT_VERSION = "5.1-infographic-explain-static-bar-samples"

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

    def build_system(self, fmt: str = "", **kwargs: Any) -> str:
        layout_type = str(kwargs.get("layout_type") or "")
        brand_name = str(kwargs.get("brand_name") or "")
        pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
        _primary = str(pack.get("primary") or kwargs.get("brand_primary_color") or "")
        _secondary = str(pack.get("secondary") or kwargs.get("brand_secondary_color") or "")
        palette_lock = resolve_brand_palette_lock(
            brand_name=brand_name,
            primary_color=_primary,
            secondary_color=_secondary,
            accent_color=str(pack.get("accent") or ""),
            additional_colors=pack.get("additional") if isinstance(pack.get("additional"), list) else None,
        )
        color_json_example = palette_lock
        icon_style_note = "Use premium 3D icons matching this brand's category."
        layout_lock = ""
        if layout_type == "carousel_story":
            if fmt in ("static", "infographic"):
                layout_lock = (
                    "LAYOUT_TYPE=carousel_story (education poster on static/infographic): "
                    "headline + 3–5 heading+explanation cards — NOT ranking rows, NOT country flags."
                )
            else:
                layout_lock = (
                    "LAYOUT_TYPE=carousel_story: 4–7 swipe education slides; one idea per slide; short lines."
                )
        elif layout_type == "static_hub_facts":
            layout_lock = "LAYOUT_TYPE=static_hub_facts: hub + 4–5 short fact cards with real ₹/% facts — never teaser-only."
        elif layout_type == "static_ranking":
            layout_lock = "LAYOUT_TYPE=static_ranking: ranked Name|%|amount rows; almost no paragraphs."

        # Dynamically build brand-specific color/typography instructions for carousel/infographic
        _brand_primary = str(pack.get("primary") or kwargs.get("brand_primary_color") or "")
        _brand_secondary = str(pack.get("secondary") or kwargs.get("brand_secondary_color") or "")
        _brand_accent = str(pack.get("accent") or "")
        _brand_font = str(pack.get("font_primary") or pack.get("font") or kwargs.get("brand_typography_font") or "")
        _carousel_bg = pack.get("background") or "#FFFFFF"
        _carousel_headline_color = _brand_primary or "#1F2937"
        _carousel_accent_color = _brand_accent or _brand_secondary or _brand_primary or "#4B5563"
        _carousel_card = pack.get("card") or _brand_secondary or "#FFFFFF"
        _font_note = (
            f"Typography: bold {_brand_font} headlines; clean sans body text; ALL copy baked."
            if _brand_font
            else "Typography: bold Brand Space primary headlines; ALL copy baked."
        )

        if fmt == "carousel":
            carousel_color_rules = f"""Background: SOLID {_carousel_bg} FULL BLEED edge-to-edge — same hex everywhere.
NO white side panels. NO second background.
Style: Clean premium education carousel for {brand_name or 'this brand'}.
{_font_note}
Brand colours LOCKED from Brand Space — PRIMARY: {_carousel_headline_color}; SECONDARY/CARDS: {_brand_secondary or _carousel_card}; ACCENT: {_carousel_accent_color}.
AUDIENCE: Use EXACT brand audience demographics.
ILLUSTRATIONS: Use the brand's own visual style.
- Perfect spelling. Complete sentences. No truncated bullets.
- EACH SLIDE UNIQUE: different headline, different content, different visual angle."""
            carousel_icon_hint = f"category-appropriate 3D icons matching {brand_name}'s industry"
            carousel_depth_hint = "EACH card = short bold label + one clear explanation (6–15 plain English words)."
            sebi_note = ""

            format_instructions = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAROUSEL — BRAND DESIGN SYSTEM (LOCKED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Canvas: 1080x1350 portrait (4:5) educational carousel slide.
ABSOLUTE BOUNDARY: every element fully inside the 1080x1350 canvas — nothing bleeds or clips past edges.
Safe margin ≥6% all sides. Reduce/drop content rather than clip.
{carousel_color_rules}
Soft ULTRA-PREMIUM HD clay-3D icons (4K-sharp studio product renders, strong shadows — NOT flat, NOT blurry, NOT low-poly).
Text must render as clean printed sans-serif, not embossed, not glowing, not outlined, not metallic.

SLIDE ANATOMY — TEXT DOMINANT:
1. TOP-RIGHT CORNER: leave it COMPLETELY BLANK — solid background colour only, zero elements. NEVER draw a logo, wordmark, leaf icon, compass icon, circular badge, brand symbol, decorative icon, or ANY graphic in the top-right. Brand logo is composited in post-processing. This corner must be 100% empty.
2. MANDATORY UNIQUE headline at top-left on EVERY slide — never omit, never repeat topic title.
3. Supporting line with mechanism or real number (required).
4. DEPTH BLOCK (REQUIRED, ~35–45% of slide height): max TWO cards with soft shadow.
   {carousel_depth_hint}
5. ICONS/AVATARS: premium HD 3D object (~12–16% height) bottom-right — {carousel_icon_hint}. NEVER omit. NEVER giant hero.
6. Accent divider optional between cards — never a stack of lines as the layout.
7. NEVER empty Pros/Cons/Examples/Advantages navigation buttons.
{sebi_note}
{ICON_STYLE_LOCK}
{CAROUSEL_ICON_LOCK}
{CAROUSEL_TEXT_FIT_LOCK}
{CAROUSEL_FIT_LOCK}

RULES:
- Required every slide: mandatory unique headline + supporting + max 2 explained fact cards.
- Icons must stay tiny. If unsure, prefer MORE text and SMALLER icons.
- Text style must be plain printed sans-serif with perfect English spelling — no stylized chrome/glow outlines.
- EACH SLIDE UNIQUE: different headline, different facts, different look.
- FAIL if: repeated headlines, empty Pros/Cons chips, giant icons, thin one-line content, clipped text.
"""
        elif fmt == "infographic":
            infographic_instructions = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INFOGRAPHIC — BRAND-SPECIFIC ({brand_name or 'active brand'}) POSTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Canvas: 1080x1350 portrait educational poster.
ABSOLUTE BOUNDARY: every element fully inside the 1080x1350 canvas — nothing bleeds or clips past edges.
Safe margin ≥6% all sides. Reduce/drop content rather than clip.
Background: Brand Space background full bleed.
{_font_note}
{palette_lock}

CHOOSE LAYOUT BY TOPIC (pick ONE):
A) EDUCATION / WHY / BENEFITS: Hero icon + 3–5 BENEFIT/REASON cards
B) RANKING LIST (only if user asked top-N): Vertical ranked rows with brand-coloured bars
C) HUB + SHORT FACTS: Center hub + 4–5 short fact cards

POSTER RULES:
1. TOP-RIGHT CORNER: leave COMPLETELY BLANK — background colour only. NEVER draw logo, wordmark, leaf, compass, circular badge, decorative icon, or ANY graphic here. Brand logo is composited in post.
2. Prefer short labels over paragraphs.
3. {palette_lock}
4. Soft matte 3D icons matching the brand's category.
5. Bake exact approved strings; spelling must be PERFECT — zero typos.
6. AUDIENCE: represent the EXACT brand audience in visuals — correct age group, demographics.
7. COMPLETE SENTENCES REQUIRED — every card must end with a full sentence. NEVER cut off mid-word or mid-sentence. If text is too long, reduce font size rather than truncate.
8. No empty shells.
9. CARD TEXT MUST BE FULLY VISIBLE — shrink font if needed, do not clip or hide any text.
"""
            format_instructions = infographic_instructions
        else:
            bg_note = static_background_instruction(brand_name=brand_name)
            palette_note = palette_lock
            format_instructions = f"""
STATIC SOCIAL FORMAT — BRAND-SPECIFIC ({brand_name or 'active brand'}):
- Canvas: exact format×platform size (LinkedIn static 1200x627, Instagram 1080x1080, X 1200x675).
- ABSOLUTE BOUNDARY: every element fully inside the canvas — nothing bleeds or clips past edges.
- Safe margin ≥6% all sides. Reduce/drop content rather than clip.
- Background: {bg_note}.
- {palette_note}
- Education / explain topics → hub + icon cards with short facts.
- Ranking / comparison ONLY when the user asked for top-N / country-wise / vs ranks.
- TOP-RIGHT CORNER: leave COMPLETELY BLANK — background only. NEVER draw logo, leaf, compass, badge, or decorative icon here. Brand logo is composited in post.
- Headline + 1 support line + short facts. NO textbook paragraphs.
- COMPLETE SENTENCES — never truncate mid-word. Shrink font if needed; never clip text.
- Perfect spelling on all baked text. Zero typos.
"""

        return f"""You are Violyt's Visual Reasoning Engine. Plan composition for a finished AI image with baked-in typography.
Return ONE JSON object matching VisualReasoningOutput EXACTLY — every required key below must be present.

CRITICAL:
- dominant_visual_system: generated_image | type_led | illustration | infographic | data_visual | product_visual
- visual_format_type: comparison | timeline | chart | matrix | process_flow | hero_scene | data_grid
- Bake approved Creative Blueprint copy into the image as sharp typography (exact strings).
- {icon_style_note}
- NEVER draw logos/wordmarks or brand-name text; Brand Space logo is composited later into a tiny top-right pocket.
- Spelling of every planned text string must be perfect.
- generated_image_url must be "".
- image_prompt_direction: 600–900 words describing layout, soft matte 3D icons, colors, AND exact text to render.

REQUIRED JSON SHAPE (fill every field; do not rename keys):
{{
  "dominant_visual_system": "infographic",
  "visual_format_type": "data_grid",
  "visual_style": "Premium corporate educational creative with soft matte clay-3D icons",
  "composition_logic": "Top-down educational hierarchy with hero visual and structured rows",
  "focal_point": "Central soft matte clay-3D icon cluster",
  "negative_space_plan": "Generous margins; tiny logo-safe top-right pocket only — headline fully clear",
  "color_behavior": "{color_json_example}",
  "logo_zone_instruction": "Empty top-right pocket (~24% width x 12% height), 20px padding; never draw brand-name text",
  "typography_behavior": "Bold Brand Space primary sans headlines, readable body, baked into image",
  "image_prompt_direction": "Detailed image prompt covering layout, icons, colors, and exact text...",
  "content_sections": [
    {{
      "section_id": "row_1",
      "title": "Section title",
      "body": "Why it matters",
      "metric": "45%",
      "visual_metaphor": "3D classical bank building"
    }}
  ],
  "text_overlay_plan": [
    {{
      "element_type": "headline",
      "text": "Exact headline",
      "font_size": 42,
      "color_hex": "#0B2C5F",
      "position_box": "top-center"
    }},
    {{
      "element_type": "supporting_line",
      "text": "Exact supporting line",
      "font_size": 22,
      "color_hex": "#4A5568",
      "position_box": "upper-center"
    }},
    {{
      "element_type": "cta",
      "text": "Exact CTA",
      "font_size": 20,
      "color_hex": "#FFFFFF",
      "position_box": "footer-strip"
    }}
  ],
  "generated_image_url": ""
}}

content_sections items MUST use keys section_id + title (not section_label).
text_overlay_plan items MUST include font_size, color_hex, position_box.
element_type allowed: headline|subheadline|supporting_line|body|cta|label|footer|section_label|stat|badge.

No preamble. No markdown fences. ONLY raw JSON.
{layout_lock}
{SOURCE_FOOTER_RULE}
{(LEGAL_FOOTER_HINT if fmt == "carousel" and bool((kwargs.get("visual_pack") or {}).get("has_legal") or (kwargs.get("visual_pack") or {}).get("legal_footer")) else NO_LEGAL_STATIC_RULE)}
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
        layout_type = str(kwargs.get("layout_type") or "").strip()
        colors = f"Primary: {brand_intelligence.visual_behavior.color_behavior}"
        mood = brand_intelligence.visual_behavior.visual_mood
        logo_zone = brand_intelligence.visual_behavior.logo_zone_instruction
        user_prompt_section = (
            f"\nUSER ORIGINAL PROMPT (primary topic direction):\n{user_prompt}\n" if user_prompt else ""
        )

        if fmt == "carousel" or layout_type == "carousel_story":
            text_directive = (
                f"Follow the LOCKED carousel sample system: solid background {self.CAROUSEL_BG}, "
                "soft matte clay-3D multi-object hero, callout box, 3 bottom insight cards, baked text."
            )
        elif layout_type == "static_hub_facts":
            pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
            primary = str(pack.get("primary") or pack.get("headline") or self.NAVY)
            accent = str(pack.get("accent") or pack.get("secondary") or self.ORANGE)
            text_directive = (
                f"Follow hub+fact-cards sample: soft bg {self.INFO_BG}, center hub, 4–5 short fact cards, "
                f"headline {primary} + accent {accent}, Source footer if provided."
            )
        elif layout_type == "static_ranking":
            from app.prompts.layout_router import is_trade_data_board

            pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
            primary = str(pack.get("primary") or pack.get("headline") or self.NAVY)
            accent = str(pack.get("accent") or pack.get("secondary") or self.ORANGE)
            if is_trade_data_board(user_prompt or ""):
                text_directive = (
                    f"Follow TRADE DEFICIT data board: soft bg {self.INFO_BG}, "
                    f"EXPORT({accent})|BALANCE|IMPORT({primary}) year rows with dual bars, "
                    f"'What India buys most' category box, Source footer. "
                    f"NO FD/bond benefit cards. Primary {primary} + accent {accent}."
                )
            else:
                text_directive = (
                    f"Follow ranking sample: soft bg {self.INFO_BG}, Name|%|amount rows, "
                    f"primary {primary} + accent {accent}, Source footer if provided."
                )
        elif fmt == "infographic" or (
            layout_type == "carousel_story" and fmt in ("static", "infographic")
        ):
            pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
            primary = str(pack.get("primary") or pack.get("headline") or self.NAVY)
            accent = str(pack.get("accent") or pack.get("secondary") or self.ORANGE)
            if layout_type == "carousel_story" and fmt == "infographic":
                text_directive = (
                    f"Follow DENSE INFOGRAPHIC EXPLAIN: "
                    f"BG {self.INFO_BG}, headlines {primary}, accent {accent}. "
                    f"Multi-section editorial with accent bars + 3-col fact cards + callout. "
                    f"Headline NOT oversized. Fill canvas with real content. Perfect spelling."
                )
            else:
                text_directive = (
                    f"Follow STATIC EXPLAIN poster: soft bg {self.INFO_BG}, hero clay-3D icon, "
                    f"3–5 heading + explanation cards, headlines {primary} + accent {accent}."
                )
        else:
            text_directive = (
                "Bake approved headline/supporting/CTA as sharp typography; use soft matte clay-3D icons."
            )

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
Layout Type (LOCKED): {layout_type or 'auto'}
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
Think like a world-class fintech art director. Plan a scannable educational layout with short copy and soft matte clay-3D icons.
{text_directive}

Return ONLY raw JSON."""

    def build_expander_system(
        self, dominant_visual_system: str = "generated_image", fmt: str = "static", **kwargs: Any
    ) -> str:
        brand_name = str(kwargs.get("brand_name") or "")
        brand_style = (
            f"Use ONLY {brand_name or 'this brand'}'s Brand Space visual identity."
        )
        return (
            f"You are a senior Art Director writing the FINAL image-generation prompt for gpt-image-1. "
            f"{brand_style} "
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
        # Resolve exact export size for this format+platform — used in every sub-builder
        canvas = canvas_label(fmt, platform)  # e.g. "1080x1350 4:5 portrait"
        layout_type = str(kwargs.get("layout_type") or layout_archetype or "")

        if fmt == "infographic":
            return self._build_infographic_prompt(
                brand_name=brand_name,
                headline=copy_headline,
                supporting_line=supporting_line,
                body=copy_body,
                cta=cta,
                hook=hook,
                story_flow=story_flow or [],
                infographic_sections=infographic_sections or [],
                stat_highlights=stat_highlights or [],
                proof_points=proof_points or [],
                problem_statement=problem_statement,
                solution_statement=solution_statement,
                customer_quote=customer_quote,
                customer_name=customer_name,
                process_steps=process_steps or [],
                user_prompt=user_prompt,
                visual_mood=visual_mood,
                color_behavior=color_behavior,
                canvas=canvas,
                layout_type=layout_type,
            )

        if fmt == "carousel":
            return self._build_carousel_prompt(
                brand_name=brand_name,
                headline=copy_headline,
                supporting_line=supporting_line,
                body=copy_body,
                cta=cta,
                hook=hook,
                story_flow=story_flow or [],
                proof_points=proof_points or [],
                stat_highlights=stat_highlights or [],
                process_steps=process_steps or [],
                slides=slides or [],
                user_prompt=user_prompt,
                visual_mood=visual_mood,
                color_behavior=color_behavior,
                initial_prompt=initial_prompt,
                canvas=canvas,
            )

        return self._build_static_prompt(
            brand_name=brand_name,
            headline=copy_headline,
            supporting_line=supporting_line,
            body=copy_body,
            cta=cta,
            user_prompt=user_prompt,
            visual_mood=visual_mood,
            color_behavior=color_behavior,
            platform=platform,
            sections=infographic_sections or [],
            customer_quote=customer_quote,
            customer_name=customer_name,
            layout_type=layout_type,
            canvas=canvas,
        )

    def _build_carousel_prompt(
        self,
        *,
        brand_name: str,
        headline: str,
        supporting_line: str,
        body: str,
        cta: str,
        hook: str,
        story_flow: list[str],
        proof_points: list[str],
        stat_highlights: list[str],
        process_steps: list[str],
        slides: list[dict],
        user_prompt: str,
        visual_mood: str,
        color_behavior: str,
        initial_prompt: str,
        canvas: str = "1080x1350 4:5 portrait",
    ) -> str:
        story = "\n".join(f"- {b}" for b in (story_flow or [])[:5]) or "- (derive from headline/body)"
        proofs = "\n".join(f"- {p}" for p in (proof_points or [])[:5]) or "- (omit if empty)"
        stats = "\n".join(f"- {s}" for s in (stat_highlights or [])[:4]) or "- (omit if empty)"
        steps = "\n".join(f"- {s}" for s in (process_steps or [])[:4]) or "- (omit if empty)"
        slides_block = "\n".join(
            f"Slide {s.get('slide_number', i+1)} [{s.get('role', 'insight')}]: "
            f"headline={s.get('headline', '')}; body={s.get('body', '')}; cta={s.get('cta') or ''}"
            for i, s in enumerate((slides or [])[:8])
        ) or "Use headline/body/cta as a single educational slide."

        user_block = f'\nUSER TOPIC REQUEST:\n"{user_prompt}"\n' if user_prompt else ""

        from app.services.image_generation.carousel_image_prompt import (
            build_carousel_style_stub,
        )

        return f"""Create ONE finished LinkedIn educational CAROUSEL SLIDE — ultra-premium editorial DNA.

{CAROUSEL_AUDIENCE_TONE_LOCK}
{build_carousel_style_stub()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CANVAS BOUNDARY LOCK (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Canvas: {canvas} (1080×1350 vertical).
ABSOLUTE BOUNDARY: Every pixel inside the canvas. Outer safe margin ≥8% on ALL sides.
Content that does not fit must be shortened or dropped — never clip.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOCKED VISUAL SYSTEM (PREMIUM AGENCY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACKGROUND: Brand Space background full bleed.
NO full-page heavy gradients. NO PowerPoint / Canva look.
Colors: Brand Space primary for titles; Brand Space accent only for numbers/CTA/icons.
Wide rounded info cards (3D isometric icon left, thin divider, text right).
Icons: premium photoreal 3D matching THIS topic — NO flat icons, NO emoji.
Typography: Extra Bold headline ≤12 words; body ≤20 words / max 2 lines. Perfect spelling.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOCKED LAYOUT (TOP → BOTTOM)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1) TOP-RIGHT: empty logo pocket (~24% wide × ~12% tall) — NEVER draw logo/wordmark/"{brand_name}".
2) HEADLINE: Extra Bold — max 12 words — never cut mid-word.
3) SUPPORTING LINE: one short subhead.
4) Hero 3D visual matching this slide's topic.
5) 3–4 wide rounded info cards (icon left → divider → short text right).
6) Tiny takeaway ABOVE footer zone.
7) FOOTER SAFE ZONE: leave bottom empty only if Brand Space has a legal footer.
8) CTA: ONLY if provided on closing slide — compact pill 2–4 words.
   NEVER invent CTAs.

{CAROUSEL_FIT_LOCK}

Prefer less content that fits over more that breaks. One visual focus per slide.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXACT COPY TO BAKE (verbatim — do not paraphrase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brand: {brand_name}
Hook: {hook or '(optional)'}
Headline: {headline}
Supporting line: {supporting_line or '(optional)'}
Body / callout source: {body}
CTA (closing slides only if provided — never invent): {cta or '(omit)'}
Storyline beats:
{story}
Proof / bottom-card labels source:
{proofs}
Stats:
{stats}
Process cues:
{steps}
Slide pack context (SAME background {self.CAROUSEL_BG}):
{slides_block}
Visual mood: {visual_mood}
Brand color behavior: {color_behavior}
{user_block}
Initial art direction (refine, do not ignore locked system):
{initial_prompt[:1200]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-NEGOTIABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Background solid Brand Space colour — identical slide-to-slide.
2. Premium 3D icons; leave legal-footer zone empty only if Brand Space has a footer.
3. Bake ONLY quoted copy letter-perfect — no mid-word cuts; no invented CTA/icon text.
4. Hierarchy: headline → hero 3D → cards → takeaway.
5. No flat clipart. No neon AI look. No watermark.
6. NEVER draw logos or brand-name text — top-right pocket only.
7. Do not invent registration / disclaimer text.

Return ONLY the finished image-generation prompt."""

    def _build_infographic_prompt(
        self,
        *,
        brand_name: str,
        headline: str,
        supporting_line: str,
        body: str,
        cta: str,
        hook: str,
        story_flow: list[str],
        infographic_sections: list[dict],
        stat_highlights: list[str],
        proof_points: list[str],
        problem_statement: str,
        solution_statement: str,
        customer_quote: str,
        customer_name: str,
        process_steps: list[str],
        user_prompt: str,
        visual_mood: str,
        color_behavior: str,
        canvas: str = "1080x1350 4:5 portrait",
        layout_type: str = "",
    ) -> str:
        title = headline or "Untitled"
        subtitle = supporting_line or ""
        layout_type = str(layout_type or "").strip()
        from app.prompts.layout_router import is_trade_data_board

        is_rank = layout_type == "static_ranking"
        is_hub = layout_type == "static_hub_facts"
        is_education = layout_type == "carousel_story" or (
            not is_rank and not is_hub
        )

        rows = []
        for i, sec in enumerate((infographic_sections or [])[:15], start=1):
            label = sec.get("section_label") or f"Item {i}"
            stat = sec.get("stat") or ""
            includes = sec.get("includes") or []
            if isinstance(includes, list):
                includes_txt = "; ".join(str(x) for x in includes[:3])
            else:
                includes_txt = str(includes)
            body_sec = " ".join(str(sec.get("body") or "").split()).strip()
            # Keep insightful paragraphs — do NOT wipe long bodies (that made posters sparse).
            if body_sec:
                body_words = body_sec.split()
                if len(body_words) > 28:
                    body_sec = " ".join(body_words[:28])
            if not body_sec and isinstance(includes, list) and includes:
                body_sec = " ".join(str(includes[0]).split()[:28])
            icon = sec.get("icon_hint") or (
                "flag/metric icon" if is_rank else "SMALL clay-3D topic icon"
            )

            if is_education:
                sub_lines = []
                if isinstance(includes, list):
                    for inc in includes[:3]:
                        sub_lines.append(f"    - {inc}")
                rows.append(
                    f'SECTION {i}: TITLE "{label}"'
                    + (f' | STAT "{stat}"' if stat else "")
                    + (f'\n    BODY: "{body_sec}"' if body_sec else "")
                    + (("\n" + "\n".join(sub_lines)) if sub_lines else "")
                    + f"\n    ICON: SMALL clay-3D ({icon})"
                )
            else:
                rows.append(
                    f"RANK {i}: {label}"
                    f"{f' | {stat}' if stat else ''}"
                    f"{f' | {includes_txt}' if includes_txt else ''}"
                    f"{f' | BODY: {body_sec}' if body_sec else ''}"
                    f" | icon: SMALL {icon}"
                )

        if is_education:
            rows_text = "\n".join(rows) or (
                "Build DENSE insight sections: SMALL icons + title + 2–3 line body paragraphs "
                "with latest verified facts — NOT sparse sample poster."
            )
        else:
            rows_text = "\n".join(rows) or (
                "Build ranked rows from the topic data — NOT benefit cards."
            )

        stats = "\n".join(f"- {s}" for s in (stat_highlights or [])[:6]) or "- (optional)"
        proofs = "\n".join(f"- {p}" for p in (proof_points or [])[:6]) or "- (optional)"
        objectives = "\n".join(f"- {s}" for s in (process_steps or proof_points or [])[:4]) or (
            "- Section 1: Why it matters\n- Section 2: How it works\n- Section 3: What to watch"
        )
        note = customer_quote or ""
        user_block = f'\nUSER TOPIC REQUEST:\n"{user_prompt}"\n' if user_prompt else ""

        if is_rank:
            layout_section = f"""LOCKED LAYOUT — RANKING LIST (layout_type=static_ranking):
{INFOGRAPHIC_RANKING_FORMAT_LOCK}
Ranked rows from the user prompt. Brand Space palette only. Bake ALL row text."""
        elif is_hub:
            layout_section = """LOCKED LAYOUT — HUB + SHORT FACTS (layout_type=static_hub_facts):
Center hub + fact cards for the named entities in the user prompt."""
        else:
            pack = kwargs.get("visual_pack") if isinstance(kwargs.get("visual_pack"), dict) else {}
            bg = pack.get("background") or "#FFFFFF"
            primary = pack.get("primary") or _brand_primary or "#1F2937"
            accent = pack.get("accent") or _brand_secondary or primary
            font = pack.get("font") or pack.get("font_primary") or _brand_font or "clean modern sans"
            layout_section = f"""LOCKED LAYOUT — EDUCATION POSTER for {brand_name} (layout_type=carousel_story):
Background: {bg} full bleed.
1) Bold {font} headline in {primary} + supporting line
2) Cards tinted from Brand Space with accent {accent}
3) 3D icons matching THIS topic
4) Compact CTA pill in {primary}
5) Empty top-right logo pocket only
FAIL if: another brand's palette, clipped text."""

        visual_system_block = f"""LOCKED VISUAL SYSTEM (BRAND SPACE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brand: {brand_name}
Canvas: {canvas}.
BACKGROUND + palette: {color_behavior or visual_mood or 'Use Brand Space visual identity only'}.
{ICON_STYLE_LOCK}
Typography: Bold headlines; short labels. ALL text baked into pixels. Perfect spelling.
CTA (if any): COMPACT pill — 2–4 words max."""
        tone_line = f"Create ONE finished educational INFOGRAPHIC for {brand_name} using its Brand Space colors and mood."

        return f"""{tone_line}

{INFOGRAPHIC_AUDIENCE_TONE_LOCK}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CANVAS BOUNDARY LOCK (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Canvas: {canvas}.
ABSOLUTE BOUNDARY: Every pixel of every element (headline, icon, bar, card, source line) MUST be
fully inside the canvas rectangle. Nothing may bleed, clip, or extend past any edge.
Safe margin ≥6% on ALL four sides. If content does not fit, shorten labels or drop optional rows.
No mid-word breaks. Perfect spelling (USD not ESD; Import not Emp; UAE not HAE).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{visual_system_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{layout_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXACT COPY TO BAKE (verbatim — keep short + simple)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brand: {brand_name}
Hook: {hook or title}
Headline: {title}
Supporting / subtitle: {subtitle or body}
Body (use ONLY if short; else omit visually): {body}
Problem: {problem_statement or '(omit)'}
Solution: {solution_statement or '(omit)'}
Storyline:
{chr(10).join(f"{i}. {b}" for i, b in enumerate((story_flow or [])[:6], start=1)) or "1. Hook\n2. Explain\n3. CTA"}
{"Section blocks (heading + sub-points):" if is_education else "Rank / data rows (label first):"}
{rows_text}
Stats:
{stats}
Proof points:
{proofs}
Objective strip labels:
{objectives}
CTA / source / banner: {cta or '(short CTA ≤4 words for education; Source line only if ranking)'}
Note box: {note or '(omit note box if empty)'}
Quote attribution: {customer_name or ''}
Visual mood: {visual_mood}
Brand color behavior: {color_behavior}
{user_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-NEGOTIABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. layout_type={layout_type or 'auto'} — follow the LOCKED LAYOUT above; do NOT switch to ranking for explain topics.
2. Bake exact short strings; never paraphrase into heavier textbook wording.
3. Spelling perfect — never invent gibberish on cards (USD/Import/UAE correct).
4. Brand colours: ONLY {brand_name} palette — {color_behavior or visual_mood}.
5. India market: ₹/% only when numbers belong; never invent foreign yield comparison tables.
6. NEVER invent country flags / India-USA-Germany-Japan boards for education prompts.
{UNIVERSAL_FIT_LOCK}
7. NEVER draw logos/wordmarks or brand-name text — tiny top-right pocket only.
8. No purple neon AI aesthetic. No empty shells. No text breaking / mid-word cuts.
9. {NO_LEGAL_STATIC_RULE}

Return ONLY the finished image-generation prompt."""

    def _build_static_prompt(
        self,
        *,
        brand_name: str,
        headline: str,
        supporting_line: str,
        body: str,
        cta: str,
        user_prompt: str,
        visual_mood: str,
        color_behavior: str,
        platform: str,
        sections: list[dict] | None = None,
        customer_quote: str = "",
        customer_name: str = "",
        layout_type: str = "",
        canvas: str = "",
    ) -> str:
        # Use canvas from size_string if not passed in
        if not canvas:
            canvas = canvas_label("static", platform)
        ratio = canvas
        user_block = f'\nUSER TOPIC REQUEST:\n"{user_prompt}"\n' if user_prompt else ""
        topic = (user_prompt or "").lower()
        layout_type = str(layout_type or "").strip()
        brand_palette = resolve_brand_palette_lock(
            brand_name=brand_name,
            color_behavior=color_behavior,
            visual_mood=visual_mood,
        )
        bg_note = static_background_instruction(brand_name=brand_name)
        is_bank_hub = layout_type == "static_hub_facts" or any(
            k in topic
            for k in (
                "penalty",
                "penalties",
                "top 5 bank",
                "top five bank",
                "key rules",
                "fd penalty",
                "premature withdrawal",
            )
        )
        # NEVER treat ranking / country lists as bank hub just because section count >= 4
        if layout_type == "static_ranking":
            is_bank_hub = False

        from app.prompts.layout_router import requested_rank_count

        # BUG FIX: do NOT hard-slice to 5 — that killed "top 10" rankings.
        # Hub stays at most 5 banks; ranking uses user top-N or all provided rows (cap 15).
        rank_n = requested_rank_count(user_prompt)
        if layout_type == "static_ranking":
            row_limit = rank_n or min(max(len(sections or []), 1), 15)
        elif is_bank_hub:
            row_limit = 5
        else:
            row_limit = min(max(len(sections or []), 1), 15)

        rows = []
        is_education = layout_type == "carousel_story" and not is_bank_hub
        for i, sec in enumerate((sections or [])[:row_limit], start=1):
            label = sec.get("section_label") or f"Item {i}"
            includes = sec.get("includes") or []
            if isinstance(includes, list):
                fact_parts = [str(x).strip() for x in includes[:2] if str(x).strip()]
            else:
                fact_parts = [str(includes).strip()] if str(includes).strip() else []
            quoted_bits = []
            for f in fact_parts:
                short = " ".join(f.replace("£", "₹").split()[:12])
                quoted_bits.append(f'"{short}"')
            quoted = " | ".join(quoted_bits) or '"(no extra line)"'
            if is_bank_hub:
                rows.append(f'{i}. Bank name "{label}" — facts: {quoted}')
            elif is_education:
                rows.append(f'{i}. HEADING "{label}" — explanation: {quoted}')
            else:
                rows.append(f'{i}. Row name "{label}" — facts: {quoted}')
        rows_text = "\n".join(rows)

        if is_bank_hub and rows_text:
            return f"""Create a finished premium LinkedIn/social STATIC hub + fact cards for {brand_name}.

Canvas: {ratio}.
ABSOLUTE BOUNDARY: every element fully inside the canvas. Safe margin ≥6%.
Background: Brand Space background. Palette: {brand_palette}
{ICON_STYLE_LOCK}

Logo pocket: empty top-right — Brand Space logo is composited later.

LOCKED LAYOUT (HUB + FACT CARDS):
1) Top: bold title (exact headline)
2) Optional supporting line
3) Center hub + fact cards for the named entities in the copy
4) Each card: 3D icon + exact name + exact fact lines only
5) {NO_LEGAL_STATIC_RULE}

Exact title: "{headline}"
Supporting (optional): "{supporting_line}"
CTA (optional, omit if empty): "{cta}"

Exact fact cards — bake ONLY these strings:
{rows_text}

Mood: {visual_mood}
{user_block}

Return ONLY the finished image-generation prompt."""

        education_block = ""
        if layout_type == "carousel_story" and not is_bank_hub:
            education_block = f"""
LAYOUT LOCK — STATIC EXPLAIN POSTER for {brand_name}:
Canvas: {ratio}. Background: {bg_note}.
{brand_palette}
- Bold headline + supporting line — fully baked
- Hero icon + 4–6 cards with Brand Space accent
Exact cards (letter-perfect):
{rows_text or '(use sections below)'}
"""

        ranking_block = ""
        if layout_type == "static_ranking" and rows_text:
            ranking_block = f"""
LAYOUT LOCK — RANKING for {brand_name}:
Canvas: {ratio}. {brand_palette}
Ranked rows from the copy. Bake ALL row text. Empty top-right logo pocket.
Exact ranked rows (letter-perfect):
{rows_text}
"""

        static_tone = f"for {brand_name} using Brand Space colours"
        static_bg = bg_note
        static_colours = brand_palette
        static_orange_line = f"Colors: {brand_palette}"

        return f"""Create a finished premium LinkedIn/social STATIC creative {static_tone}.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CANVAS BOUNDARY LOCK (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Canvas: {ratio}.
ABSOLUTE BOUNDARY: Every pixel of every element (headline, icon, card, CTA, source line) MUST be
fully inside the {ratio} canvas. Nothing may bleed, clip, or extend past any edge.
Safe margin ≥6% on ALL four sides. Shorten or drop content before clipping occurs.

Background: {static_bg}.
Style: premium educational creative with glossy 3D accents + sharp baked typography.
{static_colours}
Logo: tiny top-right empty pocket only — never draw brand-name text.
Layout: Bold large headline, supporting line, ranked rows OR fact cards, compact CTA.
{education_block}
{ranking_block}
If sections/facts are provided below and this is NOT a ranking, prefer education cards or hub layout.
{NO_LEGAL_STATIC_RULE}
Never use $ or US $ — prefer ₹ / ¥ / USD letters / %.

Exact text (bake letter-perfect — never invent gibberish):
Headline: {headline}
Supporting: {supporting_line}
Body: {body}
CTA: {cta}
Quote (omit if empty): {customer_quote} {customer_name}
Fact / rank rows:
{rows_text or '(none)'}
Mood: {visual_mood}
{static_orange_line}
{user_block}

Return ONLY the finished image-generation prompt."""
