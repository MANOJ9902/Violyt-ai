"""Every brand, every format: Brand Space colours, one logo, nothing cut off.

These are the three rules the user requires to hold for all brands, so the tests
run against several unrelated palettes rather than a single brand fixture.
"""

from types import SimpleNamespace

import pytest

from app.graph.nodes.layer8_visual_reasoning import _IMAGE_PROMPT_BUDGET, _budget_prompt
from app.services.brand_visual_pack import BrandVisualPack
from app.services.image_generation.brand_render_lock import build_lock_from_pack
from app.services.image_generation.carousel_image_prompt import (
    build_carousel_slide_image_prompt,
)
from app.services.image_generation.data_story_image_prompt import build_data_story_prompt
from app.services.image_generation.dense_content_bake import (
    extract_dense_cards,
    format_dense_cards_block,
)

BRANDS = [
    BrandVisualPack(
        brand_name="Jiraaf",
        primary="#0D3A85",
        secondary="#A2CDF5",
        accent="#FF9E02",
        background="#EBF3FC",
        card="#A2CDF5",
        body="#1F2937",
        muted="#6B7280",
    ),
    BrandVisualPack(
        brand_name="Verdant",
        primary="#14532D",
        secondary="#BBF7D0",
        accent="#F97316",
        background="#F0FDF4",
        card="#DCFCE7",
        body="#166534",
        muted="#4D7C6F",
    ),
    BrandVisualPack(
        brand_name="Noctis",
        primary="#F8FAFC",
        secondary="#334155",
        accent="#22D3EE",
        background="#0F172A",
        card="#1E293B",
        body="#CBD5E1",
        muted="#94A3B8",
    ),
]

PLATFORM_MARKS = ["LinkedIn", "Instagram", "X/Twitter", "Facebook", "YouTube"]


def _palette(pack: BrandVisualPack) -> dict[str, str]:
    pal = pack.palette_map()
    pal["headline"] = pack.primary
    return pal


def _blueprint() -> SimpleNamespace:
    sections = [
        SimpleNamespace(
            section_label=f"Insight {i}",
            body=f"Distinct mechanism number {i} that explains how capital is allocated.",
            stat=f"{i * 12}%",
            includes=[],
        )
        for i in range(1, 5)
    ]
    return SimpleNamespace(
        headline="Why bond markets matter for real economy financing",
        supporting_line="Connecting investors to growth opportunities",
        sections=sections,
        stat_highlights=["46T market size", "70% of corporate debt", "4T new issuance"],
        proof_points=[],
        cta="Explore More",
        source_footer="",
        customer_quote="",
    )


@pytest.mark.parametrize("pack", BRANDS, ids=lambda p: p.brand_name)
def test_contract_carries_only_brand_space_colours(pack: BrandVisualPack) -> None:
    lock = build_lock_from_pack(pack)
    for hex_value in (pack.background, pack.primary, pack.accent, pack.body):
        assert hex_value in lock, f"{hex_value} missing from contract"
    # A hex belonging to a different brand must never leak into the contract.
    for other in BRANDS:
        if other.brand_name == pack.brand_name:
            continue
        assert other.background not in lock


@pytest.mark.parametrize("pack", BRANDS, ids=lambda p: p.brand_name)
def test_contract_bans_all_non_brand_marks(pack: BrandVisualPack) -> None:
    lock = build_lock_from_pack(pack)
    for mark in PLATFORM_MARKS:
        assert mark in lock
    assert "composited in post" in lock
    assert "NO logo" in lock


@pytest.mark.parametrize("pack", BRANDS, ids=lambda p: p.brand_name)
def test_contract_forbids_cutoff_and_repetition(pack: BrandVisualPack) -> None:
    lock = build_lock_from_pack(pack)
    assert "never clip mid-word" in lock
    assert "cropped by any edge" in lock
    assert "DIFFERENT fact" in lock


@pytest.mark.parametrize("pack", BRANDS, ids=lambda p: p.brand_name)
def test_contract_survives_prompt_budget(pack: BrandVisualPack) -> None:
    """A huge layout block must not be able to push the contract out of the prompt."""
    lock = build_lock_from_pack(pack)
    out = _budget_prompt("X" * 40_000, "Y" * 5_000, mandatory=lock)
    assert out.startswith(lock)
    assert len(out) <= _IMAGE_PROMPT_BUDGET


@pytest.mark.parametrize("pack", BRANDS, ids=lambda p: p.brand_name)
def test_every_format_prompt_fits_beside_the_contract(pack: BrandVisualPack) -> None:
    """Copy blocks must not be chopped by the budget once the contract is added."""
    budget = _IMAGE_PROMPT_BUDGET - len(build_lock_from_pack(pack)) - 8
    pal = _palette(pack)

    story = build_data_story_prompt(
        _blueprint(), canvas_desc="1080x1350", supporting="s", palette=pal
    )
    assert len(story) <= budget

    for role, is_last in (("cover", False), ("info", False), ("cta", True)):
        slide = build_carousel_slide_image_prompt(
            slide_number=1,
            total_slides=6,
            role=role,
            headline="Deep markets, stronger growth",
            supporting="Countries with deep bond markets grow faster",
            body="Bond markets allocate capital efficiently across the economy",
            story_blocks=[
                "Governments issue bonds to fund infrastructure",
                "Deep markets lower borrowing costs",
                "Investors gain predictable returns",
            ],
            cta="Start investing" if is_last else "",
            canvas_desc="1080x1350",
            topic="bond markets",
            is_last=is_last,
            prior_headlines=["How bonds build our world"],
            palette=pal,
            has_legal=True,
            has_mascot=True,
            brand_name=pack.brand_name,
        )
        assert len(slide) <= budget, f"{role} slide prompt is over budget"
        # Copy leads the prompt so tail trimming can never remove it.
        assert slide.index("COPY TO BAKE") < 400


def test_card_body_never_repeats_its_own_title() -> None:
    blueprint = SimpleNamespace(
        sections=[
            SimpleNamespace(
                section_label="Bond markets provide predictable returns",
                body="Bond markets provide predictable returns",
                stat="",
                includes=[],
            ),
            SimpleNamespace(
                section_label="Liquidity",
                body="Deep secondary markets let investors exit positions quickly",
                stat="4T",
                includes=[],
            ),
        ],
        stat_highlights=[],
        proof_points=[],
    )
    block = format_dense_cards_block(extract_dense_cards(blueprint))
    card1 = next(l for l in block.splitlines() if "CARD 1" in l)
    assert card1.count("Bond markets provide predictable returns") == 1
    assert "title only" in card1


def test_lean_static_prompt_fits_under_budget() -> None:
    from app.services.image_generation.lean_static_prompt import build_lean_static_prompt

    lean = build_lean_static_prompt(
        canvas_desc="1200x627",
        headline="Why Bond Markets Are Key to Infrastructure Investment",
        supporting="Bond markets provide stable financing for essential projects",
        cards=[
            {"title": "Global issuance topped 500 billion", "body": ""},
            {"title": "Stable long-term financing", "body": ""},
            {"title": "Stable investment returns", "body": ""},
            {"title": "Diversified portfolios cut risk", "body": ""},
        ],
        palette={
            "background": "#EBF3FC",
            "primary": "#0D3A85",
            "secondary": "#A2CDF5",
            "accent": "#FF9E02",
            "body": "#1F2937",
            "card": "#A2CDF5",
        },
        brand_name="Jiraaf",
        cta="Explore More",
    )
    lock = build_lock_from_pack(BRANDS[0])
    assert "COPY TO BAKE" in lean
    assert "DO NOT bake any CTA" in lean
    assert "no extra lines" in lean
    assert "BODY" not in lean.split("CARDS", 1)[-1].split("LAYOUT", 1)[0]
    assert len(lock) + 2 + len(lean) <= _IMAGE_PROMPT_BUDGET


def test_stat_figure_keeps_its_unit_word() -> None:
    """"46 trillion" must not split into figure "46 t" + label "rillion"."""
    from app.services.image_generation.data_story_image_prompt import split_stat

    assert split_stat("46 trillion global bond market") == (
        "46 trillion",
        "global bond market",
    )
    assert split_stat("4 trillion new debt issued")[0] == "4 trillion"
    for raw in ("80% of investments", "2.7X returns", "352 MN+ users", "98000 crore spend"):
        figure, label = split_stat(raw)
        assert figure, raw
        assert not label.lower().startswith(("rillion", "illion", "rore")), raw


def test_infographic_cards_do_not_echo_the_headline() -> None:
    blueprint = SimpleNamespace(
        headline="Why bond markets matter for real-economy financing",
        supporting_line="Connecting investors to essential projects",
        sections=[
            SimpleNamespace(
                section_label="Why bond markets connect investors",
                body="Bond markets serve as crucial mechanisms for capital",
                stat="",
                includes=[],
            ),
            SimpleNamespace(
                section_label="Liquidity depth keeps trades clearing",
                body="Deep books let large orders settle without price shocks",
                stat="",
                includes=[],
            ),
        ],
        stat_highlights=["46 trillion global bond market"],
        proof_points=[],
        cta="Explore More",
        source_footer="",
        customer_quote="",
    )
    prompt = build_data_story_prompt(
        blueprint, canvas_desc="1080x1350", palette=_palette(BRANDS[0])
    )
    assert "46 trillion" in prompt
    assert '"rillion' not in prompt
    assert '"46 t"' not in prompt
    # The headline's opening words must appear once (in the headline block only).
    assert "REASON GRID CARDS" in prompt
    card_region = prompt.split("REASON GRID CARDS", 1)[1].split("=== ", 1)[0]
    assert "Why bond markets connect" not in card_region


def test_infographic_rejects_research_dump_as_a_stat() -> None:
    """A raw markdown research blob must never become a card figure or title."""
    dump = (
        "### Why Bond Markets Connect Investors to Real-Economy Financing "
        "1. **Key Stats**: Over $46 trillion is held in global bond markets."
    )
    blueprint = SimpleNamespace(
        headline="Why bond markets matter for real-economy financing",
        supporting_line="Connecting investors to essential projects",
        sections=[
            # section_label here is brief scaffolding leaked from the user prompt.
            SimpleNamespace(
                section_label="a clean : Why",
                body="Bond markets connect investors to real-economy financing, driving growth.",
                stat=dump,
                includes=[],
            ),
        ],
        stat_highlights=["$128 trillion: Global bond market size."],
        proof_points=[],
        cta="Explore More",
        source_footer="",
        customer_quote="",
    )
    prompt = build_data_story_prompt(
        blueprint, canvas_desc="1080x1350", palette=_palette(BRANDS[0])
    )
    assert "Key Stats" not in prompt
    assert "a clean" not in prompt
    # The surviving card keeps a complete clause, not a mid-phrase clip.
    assert "Bond markets connect investors to real-economy financing" in prompt


def test_infographic_uses_banded_template_zones() -> None:
    """The infographic must carry the reference template's banded structure."""
    blueprint = SimpleNamespace(
        headline="Why bond markets matter for real-economy financing",
        supporting_line="A smarter route to essential projects",
        body="Bond markets channel long-term capital into infrastructure and industry.",
        solution_statement="They let investors fund real assets while issuers raise durable capital.",
        sections=[
            SimpleNamespace(
                section_label=f"Reason number {i}",
                body=f"Distinct supporting insight number {i} for the grid.",
                stat="",
                includes=[],
            )
            for i in range(1, 6)
        ],
        stat_highlights=["46 trillion global market", "70% of new financing"],
        proof_points=[],
        cta="Explore More",
        source_footer="Source: example.com",
        customer_quote="Deep bond markets lower the cost of building real things.",
    )
    prompt = build_data_story_prompt(
        blueprint, canvas_desc="1080x1350", palette=_palette(BRANDS[0])
    )
    for zone in (
        "ZONE A HERO",
        "ZONE B RATIONALE CARD",
        "ZONE C STAT STRIP",
        "ZONE D SECTION BAND",
        "ZONE E REASON GRID",
        "ZONE F FOOTER BAND",
    ):
        assert zone in prompt, zone
    assert "ACCENT PILL" in prompt
    assert "HERO INTRO" in prompt
    assert "RATIONALE CARD BODY" in prompt
    assert "SECTION BAND TITLE" in prompt
    # Bottom strip stays clear for the composited CTA.
    assert "BOTTOM >=14% COMPLETELY EMPTY" in prompt
    assert "Do NOT bake the CTA" in prompt


def test_infographic_contract_allows_bands_but_other_formats_do_not() -> None:
    pack = BRANDS[0]
    info = build_lock_from_pack(pack, fmt="infographic")
    carousel = build_lock_from_pack(pack, fmt="carousel")
    assert "INSET rounded section/footer" in info
    assert "no dark/navy header band" not in info
    # Every other format keeps the strict single-background rule.
    assert "no dark/navy header band" in carousel
    # The page itself is still one light colour in both variants.
    for lock in (info, carousel):
        assert "full-bleed" in lock
        assert "never a nested white/pale panel" in lock


def test_data_story_drops_body_that_restates_the_title() -> None:
    blueprint = SimpleNamespace(
        headline="H",
        supporting_line="S",
        sections=[
            SimpleNamespace(
                section_label="Bond markets provide predictable returns",
                body="Bond markets provide predictable returns.",
                stat="",
                includes=[],
            )
        ],
        stat_highlights=[],
        proof_points=[],
        cta="",
        source_footer="",
        customer_quote="",
    )
    prompt = build_data_story_prompt(
        blueprint, canvas_desc="1080x1350", palette=_palette(BRANDS[0])
    )
    card = next(l for l in prompt.splitlines() if "CARD1" in l)
    assert card.count("Bond markets provide predictable returns") == 1
