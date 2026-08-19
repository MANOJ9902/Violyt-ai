from __future__ import annotations

from typing import Any

from app.graph.models.layer1_models import RetrievedChunk
from app.prompts.base import BasePromptBuilder


class BrandIntelligencePromptBuilder(BasePromptBuilder):
    """Builds prompts for Layer 2: Brand Intelligence Engine."""

    PROMPT_VERSION = "1.2"

    def build_system(self, **kwargs: Any) -> str:
        return """You are Violyt's Brand Intelligence Engine.
Your job is NOT to summarize brand data.
Your job is to convert retrieved brand data into a strategic brand behavior model.

CRITICAL RULES:
- Do not invent brand facts. If signals are weak, mark them in weak_signals.
- Do not produce generic or interchangeable brand behavior.
- The same architecture works across all brands, but the resulting behavior must be UNIQUE to the selected brand.
- Every output field must be brand-conditioned, not template-filled.
- Confidence below 0.5 means brand data is too sparse to proceed safely.

Return ONLY valid JSON with this exact structure:
{
  "brand_core": {
    "brand_name": "string",
    "value_proposition": "string",
    "market_tension": "string",
    "stands_for": ["string", ...],
    "stands_against": ["string", ...],
    "competitive_position": "string"
  },
  "communication_behavior": {
    "tone_spectrum": "string",
    "emotional_territory": "string",
    "boldness_level": "low|medium|high",
    "authority_level": "low|medium|high",
    "simplicity_level": "low|medium|high",
    "preferred_language_behavior": "string",
    "prohibited_phrases": ["string", ...]
  },
  "visual_behavior": {
    "visual_mood": "string",
    "design_sophistication": "minimal|moderate|elaborate",
    "color_behavior": "string",
    "image_behavior": "string",
    "logo_zone_instruction": "string",
    "typography_behavior": "string"
  },
  "creative_territory": {},
  "audience_model": {
    "primary_persona": "string",
    "secondary_persona": "string|null",
    "core_motivations": ["string", ...],
    "core_objections": ["string", ...],
    "emotional_needs": ["string", ...]
  },
  "guardrails": ["string", ...],
  "weak_signals": ["string", ...],
  "confidence": 0.0-1.0
}

No preamble. No explanation. No markdown. JSON only."""

    def build_user(
        self,
        brand_id: str,
        high_context: list[RetrievedChunk],
        medium_context: list[RetrievedChunk],
        weak_signals: list[str] | None = None,
        brand_name: str = "",
        **kwargs: Any,
    ) -> str:
        name_line = (
            f"Brand Name (authoritative, from the Brand Space — use EXACTLY this "
            f"as brand_core.brand_name): {brand_name}\n"
            if brand_name
            else ""
        )
        pack = kwargs.get("visual_pack") or {}
        pack_block = ""
        if isinstance(pack, dict) and pack.get("primary"):
            pack_block = (
                "\nBRAND SPACE VISUAL PACK (authoritative colours — do not invent other hexes):\n"
                f"- brand_name: {pack.get('brand_name') or brand_name}\n"
                f"- primary: {pack.get('primary')}\n"
                f"- secondary: {pack.get('secondary')}\n"
                f"- accent: {pack.get('accent')}\n"
                f"- background: {pack.get('background')}\n"
                f"- cards: {pack.get('card')}\n"
                f"- font: {pack.get('font_primary') or 'Brand Space typography'}\n"
                f"- design: {pack.get('design_system_summary') or '(none)'}\n"
                "Retrieved vector chunks are for voice, audience, facts, and mood ONLY.\n"
                "If a chunk mentions navy, orange, gold, teal, or any hex not listed above, ignore it.\n"
                "visual_behavior.color_behavior MUST describe ONLY these Brand Space hexes.\n"
            )
        return f"""{name_line}Brand ID: {brand_id}
{pack_block}
HIGH RELEVANCE BRAND DATA:
{self._format_chunks(high_context)}

MEDIUM RELEVANCE BRAND DATA:
{self._format_chunks(medium_context)}

Known weak signals from retrieval: {weak_signals or []}

Build the complete brand behavior model."""

    def _format_chunks(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "No chunks available."
        return "\n---\n".join(
            [
                (
                    f"Source: {c.source}\nSection: {c.section}\n"
                    f"Influence area: {c.influence_area}\n"
                    f"Content: {(getattr(c, 'content', '') or c.content_summary or '')}"
                )
                for c in chunks
            ]
        )
