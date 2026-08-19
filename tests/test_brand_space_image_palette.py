from types import SimpleNamespace

from app.services.image_generation.data_story_image_prompt import build_data_story_prompt


def test_data_story_prompt_uses_brand_space_hexes_not_navy_orange_layout():
    blueprint = SimpleNamespace(
        headline="Why the dollar dominates global trade",
        title="",
        supporting_line="The dollar's role in international transactions",
        source_footer="",
        customer_quote="",
        cta="Learn more",
        stat_highlights=["60% of global reserves", "80% of trade invoices"],
        proof_points=[],
        sections=[
            SimpleNamespace(
                section_label="Reserve status",
                body="Central banks hold dollars because US markets are deep and liquid.",
                stat="60%",
                includes=[],
            )
        ],
    )
    palette = {
        "headline": "#3D3DBE",
        "primary": "#3D3DBE",
        "accent": "#00CB91",
        "secondary": "#FFCBCB",
        "background": "#FFFFFF",
        "card": "#FFCBCB",
        "body": "#374151",
    }
    prompt = build_data_story_prompt(blueprint, palette=palette)
    assert "#3D3DBE" in prompt
    assert "#00CB91" in prompt
    assert "#FFCBCB" in prompt
    assert "#FFFFFF" in prompt
    assert "secondary #FFCBCB" in prompt.lower() or "secondary #ffcbcb" in prompt.lower()
    # Layout instructions must not tell the model to paint generic navy/orange.
    lowered = prompt.lower()
    assert "bold navy" not in lowered
    assert "huge bold navy" not in lowered
    assert "vivid orange" not in lowered
    assert "float on ice-blue" not in lowered
    assert "#eaf4fd" not in lowered
    assert "#ffa400" not in lowered
