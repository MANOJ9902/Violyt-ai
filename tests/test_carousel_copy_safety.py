"""Carousel / static copy safety — no prompt leakage, complete sentences."""

from app.services.image_generation.carousel_image_prompt import build_carousel_slide_image_prompt
from app.services.image_generation.dense_content_bake import (
    ensure_complete_sentence,
    strip_design_request_meta,
)


def test_strip_design_request_meta_removes_carousel_instruction():
    raw = (
        "Find a recent AI workforce trend and turn it into a data-led "
        "Cognixia LinkedIn carousel"
    )
    assert strip_design_request_meta(raw) == ""


def test_ensure_complete_sentence_drops_incomplete_tail():
    raw = (
        "Organizations are investing heavily in AI, but talent readiness lags behind. "
        "This gap can"
    )
    assert ensure_complete_sentence(raw).endswith("behind.")


def test_carousel_prompt_never_bakes_topic_or_user_prompt():
    prompt = build_carousel_slide_image_prompt(
        slide_number=1,
        total_slides=5,
        role="cover",
        headline="The Gap in Workforce Readiness",
        supporting="AI adoption is outpacing workforce preparation.",
        body=(
            "Organizations are investing heavily in AI, but talent readiness lags behind. "
            "This gap can slow ROI."
        ),
        topic="Find a recent AI workforce trend and turn it into a data-led carousel",
        canvas_desc="1080x1350",
        brand_name="Cognixia",
    )
    assert 'TOPIC: "' not in prompt
    assert "Find a recent AI workforce trend" not in prompt
    assert "turn it into a data-led" not in prompt
    assert "The Gap in Workforce Readiness" in prompt
    assert "AI adoption is outpacing workforce preparation." in prompt
