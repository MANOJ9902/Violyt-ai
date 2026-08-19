from app.graph.models.layer2_models import BrandIntelligenceOutput
from app.services.llm.json_utils import parse_structured_output, repair_llm_json


def test_repair_interior_quotes_in_brand_intelligence():
    # Mimics the L2 failure mode: unescaped " inside a string value.
    raw = """
    {
      "brand_core": {
        "brand_name": "Acme",
        "value_proposition": "We make "smart" money tools",
        "market_tension": "Confusion",
        "stands_for": ["clarity", "trust"],
        "stands_against": ["noise"],
        "competitive_position": "Leader"
      },
      "communication_behavior": {
        "tone_spectrum": "warm",
        "emotional_territory": "confidence",
        "boldness_level": "medium",
        "authority_level": "high",
        "simplicity_level": "high",
        "preferred_language_behavior": "Use "plain" English",
        "prohibited_phrases": ["guaranteed"]
      },
      "visual_behavior": {
        "visual_mood": "clean",
        "design_sophistication": "minimal",
        "color_behavior": "primary",
        "image_behavior": "photo",
        "logo_zone_instruction": "top-right",
        "typography_behavior": "sans"
      },
      "creative_territory": {"themes": ["education"]},
      "audience_model": {
        "primary_persona": "Retail investor",
        "core_motivations": ["growth"],
        "core_objections": ["risk"],
        "emotional_needs": ["safety"]
      },
      "guardrails": ["no guarantees"],
      "weak_signals": [],
      "confidence": 0.72
    }
    """
    repaired = repair_llm_json(raw)
    parsed = parse_structured_output(raw, BrandIntelligenceOutput, layer="l2_test")
    assert parsed.brand_core.brand_name == "Acme"
    assert "smart" in parsed.brand_core.value_proposition
    assert parsed.confidence == 0.72
    assert '"smart"' in repaired or '\\"smart\\"' in repaired


def test_trailing_comma_repair():
    raw = '{"brand_core": {"brand_name": "X", "value_proposition": "a", "market_tension": "b", "stands_for": ["a",], "stands_against": ["b"], "competitive_position": "c"}, "communication_behavior": {"tone_spectrum": "t", "emotional_territory": "e", "boldness_level": "low", "authority_level": "low", "simplicity_level": "low", "preferred_language_behavior": "p", "prohibited_phrases": []}, "visual_behavior": {"visual_mood": "m", "design_sophistication": "minimal", "color_behavior": "c", "image_behavior": "i", "logo_zone_instruction": "l", "typography_behavior": "t"}, "creative_territory": {}, "audience_model": {"primary_persona": "p", "core_motivations": [], "core_objections": [], "emotional_needs": []}, "guardrails": [], "weak_signals": [], "confidence": 0.5,}'
    parsed = parse_structured_output(raw, BrandIntelligenceOutput, layer="l2_test")
    assert parsed.brand_core.brand_name == "X"
