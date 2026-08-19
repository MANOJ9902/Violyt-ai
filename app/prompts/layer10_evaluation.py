from __future__ import annotations

from typing import Any

from app.prompts.base import BasePromptBuilder


class EvaluationPromptBuilder(BasePromptBuilder):
    """Builds the Layer 10 8-dimension evaluation prompt for a finished creative."""

    PROMPT_VERSION = "1.0-finished-creative"

    def build_system(self, **kwargs: Any) -> str:
        return """You are Violyt's Evaluation Engine.
Score the FINISHED creative (copy + visual reasoning + scene graph + generated image URLs)
before it is delivered to the user.

Score each dimension from 0.0 to 1.0. Every dimension must be >= 0.75 to pass.
contamination_risk must be "low" to pass.

Score BEHAVIOR, not keyword presence:
- brand_alignment_score: does the output behave like THIS brand (tone, visual mood, claims)?
- prompt_match_score: does it answer the user's actual request?
- audience_relevance_score: is it useful for the stated audience?
- originality_score: is the angle brand-ownable, not generic AI filler?
- visual_quality_score: is the visual system coherent (composition, hierarchy, logo zone, image present)?
- format_fit_score: does structure match static / carousel / infographic?
- brand_uniqueness_score: could this belong to a competitor with a logo swap? If yes, score low.
- strategic_quality_score: does it express the strategic problem and brand truth?

If any dimension fails, populate required_repairs with specific target_layer values:
l5_concept_engine | l7_copy_engine | l7c_content_prep | l8_visual_reasoning | l9_scene_graph

Return ONLY valid JSON:
{
  "brand_alignment_score": 0.0,
  "prompt_match_score": 0.0,
  "audience_relevance_score": 0.0,
  "originality_score": 0.0,
  "visual_quality_score": 0.0,
  "format_fit_score": 0.0,
  "brand_uniqueness_score": 0.0,
  "strategic_quality_score": 0.0,
  "contamination_risk": "low",
  "overall_pass": false,
  "required_repairs": [
    {
      "target_layer": "l8_visual_reasoning",
      "failure_reason": "string",
      "repair_action": "string",
      "priority": "critical"
    }
  ],
  "evaluator_reasoning": "string"
}
No markdown. JSON only."""

    def build_user(self, **kwargs: Any) -> str:
        return (
            f"USER PROMPT:\n{kwargs.get('user_prompt', '')}\n\n"
            f"PLATFORM / FORMAT: {kwargs.get('platform', '')} / {kwargs.get('format', '')}\n\n"
            f"BRAND INTELLIGENCE:\n{kwargs.get('brand_intelligence_json', '{}')}\n\n"
            f"CREATIVE BLUEPRINT:\n{kwargs.get('blueprint_json', '{}')}\n\n"
            f"VISUAL REASONING:\n{kwargs.get('visual_json', '{}')}\n\n"
            f"SCENE GRAPH:\n{kwargs.get('scene_json', '{}')}\n"
        )
