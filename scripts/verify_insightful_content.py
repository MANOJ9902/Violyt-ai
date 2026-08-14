"""Empty filler must fail QA and get replaced with real evidence insights."""
from types import SimpleNamespace

from app.graph.models.layer7c_models import (
    BlueprintInfographicSection as S,
    CreativeBlueprint,
)
from app.services.blueprint_quality import (
    count_empty_insight_sections,
    ensure_insightful_sections,
    is_empty_insight,
    score_blueprint_editorial_qa,
)
from app.services.image_generation.data_story_image_prompt import (
    _is_placeholder,
    build_data_story_prompt,
    split_stat,
)


print("--- empty insight detector ---")
for text, expect in [
    ("Everything you need to know about India's", True),
    ("India needs a lot. India needs a lot more airports.", True),
    ("UDAN links Tier-2 cities to metros", False),
    ("Cargo hubs cut logistics cost 20%", False),
    ("", True),
    ("Key insight", True),
]:
    got = is_empty_insight(text)
    assert got is expect, (text, got, expect)
    print(f"  ok  empty={got}  {text[:50]!r}")

print("\n--- figure keeps unit (no crore left to wrap as 'cr ore') ---")
fig, lab = split_stat("Rs 98,000 crore total investment allocated")
print(f"  figure={fig!r} label={lab!r}")
assert "crore" not in f"{fig} {lab}".casefold()
assert "cr" in fig.casefold()
assert "98,000" in fig or "98000" in fig.replace(",", "")
assert "ore" not in lab.casefold()

print("\n--- filler blueprint fails QA even with digit-heavy stats ---")
bad = CreativeBlueprint(
    format="infographic",
    layout_type="carousel_story",
    headline="India's ₹98,000 crore Airport Build-Out",
    supporting_line="Expanding airports to decentralize economic growth.",
    stat_highlights=[
        "₹98,000 crore total investment",
        "₹60,000 crore for existing upgrades",
        "₹38,000 crore for greenfield airports",
        "5 more airports needed",
    ],
    sections=[
        S(section_label="NUMBERED PROOF", stat="1", body="India needs a lot. India needs a lot more airports."),
        S(section_label="SUPPORTING INSIGHTS", body="Everything you need to know. Everything you need to know about India's"),
    ],
    customer_quote="Indian airports currently lag behind global ones",
    cta="EXPLORE AIRPORT DATA",
)
assert count_empty_insight_sections(bad) >= 1
scores = score_blueprint_editorial_qa(bad, user_prompt="why india is building airports")
print(f"  scores={scores}")
assert scores["copy_complete"] < 6 or scores["narrative_coherent"] < 6

print("\n--- ensure_insightful_sections injects real evidence ---")
ci = SimpleNamespace(
    insight_thesis="Airport spend decentralises growth beyond metros into Tier-2 cities.",
    evidence=[
        SimpleNamespace(
            approved_for_creative=True,
            claim="UDAN unlocks Tier-2 connectivity",
            value="79 airports under UDAN",
        ),
        SimpleNamespace(
            approved_for_creative=True,
            claim="Greenfield airports open new tourism belts",
            value="₹38,000 crore greenfield spend",
        ),
        SimpleNamespace(
            approved_for_creative=True,
            claim="Cargo capacity cuts logistics cost",
            value="cargo hubs at new airports",
        ),
    ],
    format_architecture=SimpleNamespace(
        hero_statistic="₹98,000 crore total investment",
        supporting_data_points=[
            "₹60,000 crore upgrades",
            "₹38,000 crore greenfield",
        ],
        core_insight="Decentralising aviation spend spreads jobs and trade inland.",
    ),
)
fixed = ensure_insightful_sections(bad, content_intelligence=ci)
bodies = " | ".join((s.body or "") for s in fixed.sections)
print(f"  bodies={bodies}")
assert "Everything you need" not in bodies
assert "needs a lot" not in bodies.casefold()
assert any("UDAN" in (s.body or "") or "UDAN" in (s.section_label or "") for s in fixed.sections) or any(
    "decentral" in (s.body or "").casefold() for s in fixed.sections
)

print("\n--- data-story prompt drops filler panels ---")
prompt = build_data_story_prompt(fixed)
assert "Everything you need" not in prompt
assert _is_placeholder("Everything you need to know about India's")
print("  prompt_len", len(prompt))
print("insightful_content_ok")
