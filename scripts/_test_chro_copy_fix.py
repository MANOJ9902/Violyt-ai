from __future__ import annotations

from types import SimpleNamespace

from app.services.blueprint_quality import (
    condense_explain_blueprint_copy,
    repair_explain_infographic_copy,
)
from app.services.image_generation.data_story_image_prompt import (
    _finalize_stat_label,
    _finalize_title,
    build_data_story_prompt,
)

sec = SimpleNamespace(
    section_label="CHROs can enhance organizational agility through strategic workforce",
    body="CHROs can enhance organizational agility through strategic workforce planning.",
    stat="70% of organizations are investing in AI technologies.",
    includes=[
        "CHROs can enhance organizational agility through strategic workforce planning."
    ],
    icon_hint=None,
)
bp = SimpleNamespace(
    format="infographic",
    headline="Unlocking Potential: The CHRO Role in AI Transformation",
    title="Unlocking Potential: The CHRO Role in AI Transformation",
    supporting_line="Empowering organizations through strategic AI integration.",
    body="AI empowers organizations to enhance decision-making.",
    cta="Explore More",
    customer_quote=(
        "Liquidity depth keeps Create a post for CHROs explaining their "
        "trades easy to clear at scale."
    ),
    source_footer="",
    sections=[sec],
    stat_highlights=[
        "70% of organizations are investing in AI technologies.",
        "30% increase in productivity with effective AI integration.",
        "CHROs can bridge the gap between technology and talent.",
    ],
    solution_statement="CHROs are essential in driving AI transformation.",
    problem_statement="",
    proof_points=[],
    customer_name="",
)

bp2 = repair_explain_infographic_copy(
    bp,
    layout_type="carousel_story",
    user_prompt=(
        "Create a post for CHROs explaining their role in enterprise AI transformation."
    ),
)
print("quote cleared:", repr(bp2.customer_quote))
print("section:", bp2.sections[0].section_label, "| stat:", bp2.sections[0].stat)
print("stats:", bp2.stat_highlights)
print(
    "title finalize:",
    _finalize_title(
        "Organizations with strategic workforce planning goals", max_words=4
    ),
)
print(
    "stat finalize:",
    _finalize_stat_label(
        "AI can reduce recruitment time by up to 30 percent", max_words=6
    ),
)

bp3 = condense_explain_blueprint_copy(bp2, layout_type="carousel_story")
prompt = build_data_story_prompt(
    bp3,
    canvas_desc="1080x1350 4:5 portrait",
    palette={
        "headline": "#0952A9",
        "accent": "#74ADBA",
        "card": "#F3F9FF",
        "background": "#FFFFFF",
        "body": "#333",
    },
)
assert "Liquidity" not in prompt
assert "Organizations with" not in prompt
print("prompt len:", len(prompt))
print("OK")
