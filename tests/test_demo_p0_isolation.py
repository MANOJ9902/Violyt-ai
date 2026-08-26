"""P0 demo regression: format resolution + brand isolation."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.brand_visual_pack import BrandVisualPack
from app.services.pipeline.format_resolution import (
    detect_prompt_format,
    resolve_pipeline_format,
)


def test_detect_prompt_format_prefers_infographic_word() -> None:
    assert detect_prompt_format("Make an infographic about bonds") == "infographic"
    assert detect_prompt_format("LinkedIn carousel on rates") == "carousel"
    assert detect_prompt_format("a static post on rates") == "static"
    assert detect_prompt_format("explain bond markets") == ""


def test_static_studio_upgrades_when_prompt_names_format() -> None:
    carousel = resolve_pipeline_format(
        studio_format="static",
        user_prompt="Create a LinkedIn carousel on bond mistakes",
    )
    assert carousel.format == "carousel"
    assert carousel.overridden is True
    assert "Carousel" in carousel.warning

    info = resolve_pipeline_format(
        studio_format="static",
        user_prompt="Create an infographic: why bond markets matter",
    )
    assert info.format == "infographic"
    assert info.overridden is True


def test_studio_carousel_wins_but_warns_on_infographic_prompt() -> None:
    """Demo P0: prompt says infographic, studio left on carousel — keep studio + warn."""
    resolved = resolve_pipeline_format(
        studio_format="carousel",
        user_prompt="Create an infographic about bond markets",
    )
    assert resolved.format == "carousel"
    assert resolved.prompt_format == "infographic"
    assert resolved.overridden is False
    assert "keeping Studio Carousel" in resolved.warning


def test_empty_legal_footer_means_no_sebi_for_other_brands() -> None:
    """Non-Jiraaf Brand Spaces with empty legal_disclaimers must not get a footer."""
    pack = BrandVisualPack(
        brand_id="flocco-test",
        brand_name="Flocco",
        tenant_id="t1",
        background="#FFFFFF",
        primary="#111111",
        secondary="#EEEEEE",
        accent="#FF0000",
        body="#333333",
        card="#F5F5F5",
        muted="#888888",
        legal_footer="",
        legal_color="#666666",
        font_primary="Inter",
    )
    assert pack.has_legal is False
    assert "SEBI" not in (pack.legal_footer or "")
    assert "Jiraaf" not in (pack.legal_footer or "")


def test_legal_footer_only_comes_from_brand_space_text() -> None:
    pack = BrandVisualPack(
        brand_id="jiraaf-test",
        brand_name="Jiraaf",
        tenant_id="t1",
        background="#EEF4FF",
        primary="#0D3A85",
        secondary="#DCE7FF",
        accent="#FF9E02",
        body="#1F2A44",
        card="#E4EDFF",
        muted="#5A6B8C",
        legal_footer="Jiraaf Platform Private Limited. SEBI Registration Number XYZ.",
        legal_color="#666666",
        font_primary="Inter",
    )
    assert pack.has_legal is True
    assert "SEBI" in pack.legal_footer


def test_icon_lock_does_not_force_finance_dna_for_all_brands() -> None:
    from app.prompts.brand_copy_tone import CAROUSEL_ICON_LOCK, ICON_STYLE_LOCK

    assert "unless the prompt is about finance" in CAROUSEL_ICON_LOCK
    assert "food / wellness" in ICON_STYLE_LOCK
    assert "learning / L&D" in ICON_STYLE_LOCK
    assert "Match sample style: soft-touch wallet" not in CAROUSEL_ICON_LOCK


def test_layer3_prompt_includes_brand_audience_persona() -> None:
    from app.prompts.layer3_brief_interpreter import BriefInterpreterPromptBuilder

    bi = SimpleNamespace(
        brand_core=SimpleNamespace(brand_name="Cognixia", value_proposition="L&D"),
        communication_behavior=SimpleNamespace(
            tone_spectrum="professional", emotional_territory="growth"
        ),
        visual_behavior=SimpleNamespace(visual_mood="clean"),
        guardrails=["no medical claims"],
        audience_model=SimpleNamespace(primary_persona="Women in tech leadership"),
    )
    prompt = BriefInterpreterPromptBuilder().build_user(
        user_prompt="Women's Day LinkedIn post",
        platform="linkedin",
        format="static",
        brand_intelligence=bi,
    )
    assert "Women in tech leadership" in prompt
    assert "AUDIENCE" in prompt
    assert "Do NOT invent a different audience" in prompt
