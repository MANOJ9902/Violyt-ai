from __future__ import annotations

from app.graph.models.content_intelligence_models import ContentIntelligenceOutput
from app.graph.models.layer1_models import BrandContextOutput
from app.graph.models.layer2_models import BrandIntelligenceOutput
from app.graph.models.layer3_models import CampaignBriefOutput
from app.graph.models.layer4_models import StrategicReasoningOutput
from app.graph.models.layer5_models import CreativeConceptsOutput
from app.graph.models.layer6_models import FormatPlanOutput
from app.graph.models.layer7_models import CopyOutput
from app.graph.models.layer7b_models import ContentValidationOutput
from app.graph.models.layer7c_models import CreativeBlueprint
from app.graph.models.layer8_models import VisualReasoningOutput
from app.graph.models.layer9_models import SceneGraphOutput
from app.graph.models.layer10_models import EvaluationOutput
from app.graph.state import ViolytState


def hydrate_state(raw: dict) -> ViolytState:
    """Rebuild Pydantic layer outputs from a serialized checkpoint dict."""
    state: ViolytState = {
        "user_prompt": raw.get("user_prompt", ""),
        "brand_id": raw.get("brand_id", ""),
        "platform": raw.get("platform", "linkedin"),
        "format": raw.get("format", "static"),
        "run_id": raw.get("run_id"),
        "org_id": raw.get("org_id"),
        "tenant_id": raw.get("tenant_id"),
        "brand_name": raw.get("brand_name"),
        "visual_pack": raw.get("visual_pack") or {},
        "data_version": raw.get("data_version"),
        "repair_count": raw.get("repair_count", 0),
        "force_repair": raw.get("force_repair", False),
        "layer_latencies": raw.get("layer_latencies") or {},
        "token_usage": raw.get("token_usage") or {},
        "error": raw.get("error"),
        "retrieval_log": raw.get("retrieval_log"),
        "repair_instructions": raw.get("repair_instructions"),
        "repair_target": raw.get("repair_target"),
        "final_output": raw.get("final_output"),
        "live_research": raw.get("live_research") or {},
    }

    mapping = [
        ("brand_context", BrandContextOutput),
        ("brand_intelligence", BrandIntelligenceOutput),
        ("campaign_brief", CampaignBriefOutput),
        ("strategic_reasoning", StrategicReasoningOutput),
        ("creative_concepts", CreativeConceptsOutput),
        ("format_plan", FormatPlanOutput),
        ("content_intelligence", ContentIntelligenceOutput),
        ("copy", CopyOutput),
        ("content_validation", ContentValidationOutput),
        ("creative_blueprint", CreativeBlueprint),
        ("visual_reasoning", VisualReasoningOutput),
        ("scene_graph", SceneGraphOutput),
        ("evaluation", EvaluationOutput),
    ]
    for key, model in mapping:
        val = raw.get(key)
        if val is None:
            continue
        if isinstance(val, model):
            state[key] = val  # type: ignore[literal-required]
        elif isinstance(val, dict):
            try:
                state[key] = model.model_validate(val)  # type: ignore[literal-required]
            except Exception:
                continue

    return state
