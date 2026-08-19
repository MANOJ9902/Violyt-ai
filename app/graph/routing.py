from app.graph.state import ViolytState


def route_after_l1(state: ViolytState) -> str:
    """Abort the graph when brand isolation cannot be guaranteed."""
    if (state.get("error") or "").lower().startswith("brand isolation failed"):
        return "abort"
    ctx = state.get("brand_context")
    if ctx is not None and getattr(ctx, "brand_isolation_status", None) == "fail":
        return "abort"
    return "continue"


def _image_urls(visual) -> list[str]:
    if visual is None:
        return []
    if isinstance(visual, dict):
        urls = [u for u in (visual.get("generated_image_urls") or []) if u]
        extra = visual.get("generated_image_url") or ""
    else:
        urls = [u for u in (getattr(visual, "generated_image_urls", None) or []) if u]
        extra = getattr(visual, "generated_image_url", "") or ""
    if extra and extra not in urls:
        urls.insert(0, extra)
    return urls


def _is_finished_creative(state: ViolytState) -> bool:
    return bool(
        _image_urls(state.get("visual_reasoning"))
        or state.get("scene_graph")
        or state.get("final_output")
    )


def _has_critical_repairs(evaluation) -> bool:
    for item in evaluation.required_repairs or []:
        priority = getattr(item, "priority", None)
        if priority is None and isinstance(item, dict):
            priority = item.get("priority")
        if priority == "critical":
            return True
    return False


def route_evaluation(state: ViolytState) -> str:
    """Route from L10 evaluation to pass (END/renderer) or repair."""
    evaluation = state.get("evaluation")

    if state.get("force_repair"):
        return "repair"

    if evaluation is None:
        return "repair"

    finished = _is_finished_creative(state)
    if not finished:
        # Phase 1 has no artwork yet. Do not block the blueprint card on
        # visual_quality_score or soft (major) copy nits — those are shown
        # on the card. Only loop on contamination / critical editorial fails.
        if evaluation.contamination_risk == "high" or _has_critical_repairs(evaluation):
            return "repair"
        return "pass"

    if not evaluation.overall_pass:
        return "repair"

    if evaluation.contamination_risk != "low":
        return "repair"

    threshold = 0.75
    scores = [
        evaluation.brand_alignment_score,
        evaluation.prompt_match_score,
        evaluation.audience_relevance_score,
        evaluation.originality_score,
        evaluation.visual_quality_score,
        evaluation.format_fit_score,
        evaluation.brand_uniqueness_score,
        evaluation.strategic_quality_score,
    ]
    if any(score < threshold for score in scores):
        return "repair"

    return "pass"


def _repair_mapping(target: str) -> str:
    mapping = {
        "l6b": "retry_l6b",
        "content_intelligence": "retry_l6b",
        "insight": "retry_l6b",
        "l5": "retry_l5",
        "concept": "retry_l5",
        "l7": "retry_l7",
        "copy": "retry_l7",
        "l7c": "retry_l7c",
        "blueprint": "retry_l7c",
        "l8": "retry_l8",
        "visual": "retry_l8",
        "l9": "retry_l9",
        "scene": "retry_l9",
    }
    return mapping.get(target, "retry_l5")


def route_repair(state: ViolytState) -> str:
    """Route repair to the failed layer (max 2), else fail/deliver."""
    repair_count = state.get("repair_count", 0)
    if repair_count >= 2:
        return "fail"

    target = (state.get("repair_target") or "l5").strip().lower()
    return _repair_mapping(target)


def route_repair_phase2(state: ViolytState) -> str:
    """Phase 2 repair: retry L8/L9, or deliver images with scores after 2 failures."""
    repair_count = state.get("repair_count", 0)
    if repair_count >= 2:
        return "deliver"

    target = (state.get("repair_target") or "l8").strip().lower()
    mapped = _repair_mapping(target)
    if mapped in {"retry_l8", "retry_l9"}:
        return mapped
    return "retry_l8"
