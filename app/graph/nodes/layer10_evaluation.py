from __future__ import annotations

"""Layer 10 — 8-dimension gate. Blueprint-only in Phase 1; finished creative in Phase 2."""

import json
import time

from app.core.logging import get_logger
from app.graph.models.layer10_models import EvaluationOutput, RepairInstruction
from app.graph.state import ViolytState
from app.prompts.layer10_evaluation import EvaluationPromptBuilder
from app.services.blueprint_quality import (
    blueprint_passes_editorial_qa,
    evaluate_blueprint_gate,
    score_blueprint_editorial_qa,
)
from app.services.llm.llm_router import LLMRouter

logger = get_logger(__name__)

_router = LLMRouter()
_prompt_builder = EvaluationPromptBuilder()


def _dump(obj) -> dict:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return {}


def _image_urls(visual) -> list[str]:
    if visual is None:
        return []
    urls = [u for u in (getattr(visual, "generated_image_urls", None) or []) if u]
    extra = getattr(visual, "generated_image_url", "") or ""
    if extra and extra not in urls:
        urls.insert(0, extra)
    return urls


def _heuristic_finished(state: ViolytState, blueprint_eval: EvaluationOutput | None) -> EvaluationOutput:
    visual = state.get("visual_reasoning")
    scene = state.get("scene_graph")
    urls = _image_urls(visual)
    has_images = bool(urls)
    element_count = len(getattr(scene, "elements", None) or []) if scene else 0

    visual_quality = 0.86 if has_images else 0.40
    format_fit = 0.84 if element_count >= 2 else (0.70 if scene else 0.45)
    if blueprint_eval:
        brand = blueprint_eval.brand_alignment_score
        prompt = blueprint_eval.prompt_match_score
        audience = blueprint_eval.audience_relevance_score
        originality = blueprint_eval.originality_score
        uniqueness = blueprint_eval.brand_uniqueness_score
        strategic = blueprint_eval.strategic_quality_score
        contamination = blueprint_eval.contamination_risk
    else:
        brand = prompt = audience = originality = uniqueness = strategic = 0.72
        contamination = "medium"

    scores = [brand, prompt, audience, originality, visual_quality, format_fit, uniqueness, strategic]
    repairs: list[RepairInstruction] = []
    if not has_images:
        repairs.append(
            RepairInstruction(
                target_layer="l8_visual_reasoning",
                failure_reason="No generated image URL on finished creative",
                repair_action="Regenerate brand-conditioned artwork",
                priority="critical",
            )
        )
    overall = all(s >= 0.75 for s in scores) and contamination == "low" and has_images
    return EvaluationOutput(
        brand_alignment_score=round(brand, 2),
        prompt_match_score=round(prompt, 2),
        audience_relevance_score=round(audience, 2),
        originality_score=round(originality, 2),
        visual_quality_score=round(visual_quality, 2),
        format_fit_score=round(format_fit, 2),
        brand_uniqueness_score=round(uniqueness, 2),
        strategic_quality_score=round(strategic, 2),
        contamination_risk=contamination if contamination in ("low", "medium", "high") else "low",
        overall_pass=overall,
        required_repairs=repairs,
        evaluator_reasoning=(
            f"heuristic_finished images={len(urls)} elements={element_count} "
            f"pass={overall}"
        ),
    )


async def _claude_finished(state: ViolytState) -> tuple[EvaluationOutput | None, dict]:
    service = _router.get_service("l10_evaluation")
    system = _prompt_builder.build_system()
    user = _prompt_builder.build_user(
        user_prompt=state.get("user_prompt", ""),
        platform=state.get("platform", ""),
        format=state.get("format", ""),
        brand_intelligence_json=json.dumps(_dump(state.get("brand_intelligence")), default=str)[:6000],
        blueprint_json=json.dumps(_dump(state.get("creative_blueprint")), default=str)[:6000],
        visual_json=json.dumps(_dump(state.get("visual_reasoning")), default=str)[:4000],
        scene_json=json.dumps(_dump(state.get("scene_graph")), default=str)[:4000],
    )
    output, metadata = await service.complete_structured(
        system=system,
        user=user,
        output_model=EvaluationOutput,
        layer="l10_evaluation",
        max_tokens=4096,
    )
    return output, metadata


def _infer_repair_target(evaluation: EvaluationOutput, *, finished: bool) -> str | None:
    if evaluation.overall_pass:
        return None
    if evaluation.required_repairs:
        layer = (evaluation.required_repairs[0].target_layer or "").lower()
        if "l8" in layer or "visual" in layer:
            return "l8"
        if "l9" in layer or "scene" in layer:
            return "l9"
        if "l7c" in layer or "blueprint" in layer:
            return "l7c"
        if "l7" in layer or "copy" in layer:
            return "l7"
        if "l6b" in layer or "insight" in layer:
            return "l6b"
        if "l5" in layer or "concept" in layer:
            return "l5"
    return "l8" if finished else "l5"


async def layer10_evaluation(state: ViolytState) -> dict:
    started = time.monotonic()
    if state.get("force_repair"):
        return {
            "evaluation": EvaluationOutput(
                brand_alignment_score=0.65,
                prompt_match_score=0.80,
                audience_relevance_score=0.78,
                originality_score=0.61,
                visual_quality_score=0.76,
                format_fit_score=0.79,
                brand_uniqueness_score=0.70,
                strategic_quality_score=0.74,
                contamination_risk="low",
                overall_pass=False,
                required_repairs=[
                    RepairInstruction(
                        target_layer="l5_concept_engine",
                        failure_reason="Forced repair for loop testing",
                        repair_action="Regenerate with stronger brand-specific insight tension",
                        priority="major",
                    )
                ],
                evaluator_reasoning="Forced failure stub for repair-loop testing.",
            ),
            "repair_target": "l5",
            "layer_latencies": {"l10_evaluation": int((time.monotonic() - started) * 1000)},
        }

    blueprint = state.get("creative_blueprint")
    visual = state.get("visual_reasoning")
    scene = state.get("scene_graph")
    finished = bool(_image_urls(visual) or scene)

    blueprint_eval: EvaluationOutput | None = None
    if blueprint is not None:
        blueprint_eval, _ = evaluate_blueprint_gate(
            blueprint,
            user_prompt=state.get("user_prompt", ""),
            content_intelligence=state.get("content_intelligence"),
            brand_intelligence=state.get("brand_intelligence"),
        )

    metadata: dict = {"input_tokens": 0, "output_tokens": 0}
    if finished:
        evaluation = None
        try:
            evaluation, metadata = await _claude_finished(state)
        except Exception as exc:  # noqa: BLE001
            logger.warning("evaluation.claude_failed", error=str(exc)[:200])
        if evaluation is None:
            evaluation = _heuristic_finished(state, blueprint_eval)
        # Never pass a finished creative with no image.
        if not _image_urls(visual):
            evaluation.overall_pass = False
            evaluation.visual_quality_score = min(evaluation.visual_quality_score, 0.4)
    elif blueprint is None:
        evaluation = EvaluationOutput(
            brand_alignment_score=0.4,
            prompt_match_score=0.4,
            audience_relevance_score=0.4,
            originality_score=0.4,
            visual_quality_score=0.4,
            format_fit_score=0.4,
            brand_uniqueness_score=0.4,
            strategic_quality_score=0.4,
            contamination_risk="medium",
            overall_pass=False,
            required_repairs=[
                RepairInstruction(
                    target_layer="l7c_content_prep",
                    failure_reason="Missing creative blueprint",
                    repair_action="Regenerate blueprint from Content Intelligence package",
                    priority="critical",
                )
            ],
            evaluator_reasoning="No creative blueprint present.",
        )
    else:
        evaluation = blueprint_eval
        scores = score_blueprint_editorial_qa(
            blueprint,
            user_prompt=state.get("user_prompt", ""),
            content_intelligence=state.get("content_intelligence"),
        )
        logger.info(
            "evaluation.blueprint_gate",
            overall_pass=evaluation.overall_pass,
            editorial=scores,
            passes_editorial=blueprint_passes_editorial_qa(scores),
        )

    repair_target = _infer_repair_target(evaluation, finished=finished)
    latency_ms = int((time.monotonic() - started) * 1000)
    logger.info(
        "evaluation.complete",
        overall_pass=evaluation.overall_pass,
        repair_target=repair_target,
        finished=finished,
        latency_ms=latency_ms,
    )
    return {
        "evaluation": evaluation,
        "repair_target": repair_target,
        "layer_latencies": {"l10_evaluation": latency_ms},
        "token_usage": {
            "l10_evaluation": {
                "input_tokens": metadata.get("input_tokens", 0),
                "output_tokens": metadata.get("output_tokens", 0),
            }
        },
    }
