from types import SimpleNamespace

from app.services.blueprint_quality import (
    count_duplicate_insight_bodies,
    dedupe_repeated_insight_bodies,
    score_blueprint_editorial_qa,
)


def _bp(*bodies: str):
    sections = [
        SimpleNamespace(
            section_label=f"Card {i}",
            body=body,
            includes=[],
            stat=None,
            icon_hint=None,
        )
        for i, body in enumerate(bodies, start=1)
    ]
    return SimpleNamespace(
        headline="Why the US dollar dominates",
        supporting_line="A strategic economic story",
        body="",
        sections=sections,
        slides=[],
        format="infographic",
        layout_type="carousel_story",
        brand_alignment_notes=[],
    )


def test_count_duplicate_insight_bodies_detects_clones():
    bp = _bp(
        "The US dollar's dominance in global trade",
        "The US dollar's dominance in global trade",
        "Liquidity keeps dollar trades easy to clear",
    )
    assert count_duplicate_insight_bodies(bp) == 1


def test_count_duplicate_bodies_ignores_different_stats():
    """Same body with different stats must still count as a clone."""
    sections = [
        SimpleNamespace(
            section_label="Card 1",
            body="The US dollar's dominance in global trade",
            includes=["60% reserves"],
            stat="60%",
            icon_hint=None,
        ),
        SimpleNamespace(
            section_label="Card 2",
            body="The US dollar's dominance in global trade",
            includes=["88% forex"],
            stat="88%",
            icon_hint=None,
        ),
    ]
    bp = SimpleNamespace(
        headline="Why",
        supporting_line="",
        body="",
        sections=sections,
        slides=[],
        format="infographic",
        layout_type="carousel_story",
        brand_alignment_notes=[],
    )
    assert count_duplicate_insight_bodies(bp) == 1


def test_score_fails_when_insight_bodies_repeat():
    bp = _bp(
        "The US dollar's dominance in global trade",
        "The US dollar's dominance in global trade",
        "The US dollar's dominance in global trade",
    )
    scores = score_blueprint_editorial_qa(bp, user_prompt="why does the dollar dominate")
    assert scores["unique_insight_bodies"] < 6
    assert scores["copy_complete"] < 6


def test_dedupe_repeated_insight_bodies_rewrites_clones():
    bp = _bp(
        "The US dollar's dominance in global trade",
        "The US dollar's dominance in global trade",
        "The US dollar's dominance in global trade",
    )
    out = dedupe_repeated_insight_bodies(
        bp,
        user_prompt="why the US dollar dominates global trade",
    )
    bodies = [s.body for s in out.sections]
    assert len(set(b.casefold() for b in bodies)) == len(bodies)
    assert count_duplicate_insight_bodies(out) == 0
