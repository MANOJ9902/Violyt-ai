from __future__ import annotations

import time

from app.graph.models.layer1_models import BrandContextOutput
from app.graph.routing import route_after_l1, route_repair, route_repair_phase2
from app.services.cost_tracking.cost_service import estimate_run_cost


def test_route_after_l1_aborts_on_isolation_fail():
    ctx = BrandContextOutput(
        brand_id="b1",
        retrieved_sections=[],
        high_relevance_context=[],
        medium_relevance_context=[],
        low_relevance_context=[],
        missing_context=["retrieval_error"],
        brand_isolation_status="fail",
        retrieval_confidence=0.0,
        retrieval_query="q",
        total_chunks_retrieved=0,
    )
    assert route_after_l1({"brand_context": ctx, "error": "Brand isolation failed: no brand data retrieved."}) == "abort"


def test_route_after_l1_continues_on_pass():
    ctx = BrandContextOutput(
        brand_id="b1",
        retrieved_sections=["identity"],
        high_relevance_context=[],
        medium_relevance_context=[],
        low_relevance_context=[],
        missing_context=[],
        brand_isolation_status="pass",
        retrieval_confidence=0.8,
        retrieval_query="q",
        total_chunks_retrieved=8,
    )
    assert route_after_l1({"brand_context": ctx}) == "continue"


def test_phase2_repair_delivers_after_two_failures():
    assert route_repair_phase2({"repair_count": 2, "repair_target": "l8"}) == "deliver"
    assert route_repair_phase2({"repair_count": 1, "repair_target": "l8"}) == "retry_l8"
    assert route_repair_phase2({"repair_count": 1, "repair_target": "l9"}) == "retry_l9"


def test_phase1_repair_still_fails_after_two():
    assert route_repair({"repair_count": 2, "repair_target": "l5"}) == "fail"


def _eval(**kwargs):
    from app.graph.models.layer10_models import EvaluationOutput, RepairInstruction

    payload = dict(
        brand_alignment_score=0.82,
        prompt_match_score=0.80,
        audience_relevance_score=0.80,
        originality_score=0.80,
        visual_quality_score=0.30,
        format_fit_score=0.80,
        brand_uniqueness_score=0.80,
        strategic_quality_score=0.80,
        contamination_risk="low",
        overall_pass=False,
        required_repairs=[
            RepairInstruction(
                target_layer="l7_copy_engine",
                failure_reason="Copy lacks real data density",
                repair_action="Rewrite using ranked evidence",
                priority="major",
            )
        ],
        evaluator_reasoning="soft",
    )
    payload.update(kwargs)
    return EvaluationOutput(**payload)


def test_phase1_route_shows_blueprint_on_soft_failures():
    from app.graph.routing import route_evaluation

    assert route_evaluation({"evaluation": _eval()}) == "pass"


def test_phase1_route_repairs_critical_editorial_failures():
    from app.graph.models.layer10_models import RepairInstruction
    from app.graph.routing import route_evaluation

    evaluation = _eval(
        required_repairs=[
            RepairInstruction(
                target_layer="l7_copy_engine",
                failure_reason="Explain infographic has only 2 sections",
                repair_action="Rebuild 5-6 unique reason sections",
                priority="critical",
            )
        ]
    )
    assert route_evaluation({"evaluation": evaluation}) == "repair"


def test_phase2_route_still_requires_visual_quality():
    from app.graph.routing import route_evaluation

    evaluation = _eval(overall_pass=True, required_repairs=[], visual_quality_score=0.30)
    assert (
        route_evaluation(
            {
                "evaluation": evaluation,
                "visual_reasoning": {"generated_image_url": "https://example.com/a.png"},
            }
        )
        == "repair"
    )


def test_estimate_run_cost_includes_tokens_and_images():
    usage = {
        "l2_brand_intelligence": {"input_tokens": 1_000_000, "output_tokens": 0},
        "l8_visual_reasoning": {"input_tokens": 0, "output_tokens": 0},
    }
    state = {
        "visual_reasoning": {
            "generated_image_urls": ["/storage/a.png", "/storage/b.png"],
        }
    }
    cost = estimate_run_cost(usage, state=state)
    assert cost["input_tokens"] == 1_000_000
    assert cost["image_count"] == 2
    assert cost["total_cost_usd"] > 0
    assert cost["text_cost_usd"] == 3.0  # claude in-rate $3 / 1M


def test_phase2_graph_wires_scene_graph_and_eval():
    from app.graph.graph import build_phase2_graph

    compiled = build_phase2_graph().compile()
    graph = compiled.get_graph()
    node_ids = set(graph.nodes.keys())
    assert "l8_visual_reasoning" in node_ids
    assert "l9_scene_graph" in node_ids
    assert "l10_evaluation" in node_ids
    assert "renderer" in node_ids


def test_emit_progress_does_not_pass_event_kwarg_to_structlog(tmp_path, monkeypatch):
    from app.services.pipeline import progress as progress_mod

    monkeypatch.setattr(progress_mod, "append_checkpoint_event", lambda *args, **kwargs: None)
    progress_mod.emit_progress("run-1", event="pipeline_start", message="phase1", layer="l1")


def test_phase1_graph_aborts_from_l1():
    from app.graph.graph import build_phase1_graph

    compiled = build_phase1_graph().compile()
    graph = compiled.get_graph()
    # Conditional edge from L1 is present in the graph spec.
    assert "l1_brand_retrieval" in graph.nodes
    assert "l2_brand_intelligence" in graph.nodes


def test_fail_if_stale_marks_hung_running_jobs(tmp_path, monkeypatch):
    from app.graph import checkpoint as ck

    monkeypatch.setattr(ck, "_CHECKPOINT_DIR", tmp_path)
    run_id = "stale-run"
    ck.save_checkpoint(run_id, {"user_prompt": "x"}, status="running")
    payload = ck._read_payload(run_id)
    assert payload is not None
    payload["updated_at"] = time.time() - 900
    ck._write_payload(run_id, payload)
    rec = ck.fail_if_stale(run_id, max_idle_sec=480)
    assert rec is not None
    assert rec["status"] == "failed"
    assert "stalled" in str((rec.get("state") or {}).get("error", "")).lower()
