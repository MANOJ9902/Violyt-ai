"""Verify the Jiraaf data-story infographic template against the reference sample."""

from app.graph.models.layer7c_models import (
    BlueprintInfographicSection as S,
)
from app.graph.models.layer7c_models import (
    CreativeBlueprint,
)
from app.services.image_generation.data_story_image_prompt import (
    DATA_BG_BOTTOM,
    DATA_BG_MID,
    DATA_BG_TOP,
    _headline_lines,
    _is_placeholder,
    build_data_story_prompt,
    split_stat,
)

print("--- split_stat ---")
CASES = [
    ("15.4% Annual growth in passenger traffic", "15.4%"),
    ("352 MN+ Passengers in FY2024", "352 MN+"),
    ("2.7X Increase in aircraft movements", "2.7X"),
    ("No. 3 largest domestic aviation market", "No. 3"),
    ("450 Operational Airports", "450"),
    ("Tier-2/3 Cities Connected", "Tier-2/3"),
    ("Routes | 619 operational", "619"),
]
for raw, expected_figure in CASES:
    figure, label = split_stat(raw)
    flag = "ok " if figure == expected_figure else "BAD"
    print(f"  {flag} {raw!r:46} -> figure={figure!r:10} label={label!r}")
    assert figure == expected_figure, (raw, figure, expected_figure)

print("\n--- headline wrapping (max 3 lines) ---")
for hl in (
    "WHY INDIA IS BUILDING AIRPORTS EVERYWHERE",
    "INDIA'S AIRPORTS CONNECT MORE THAN JUST CITIES",
    "SHORT ONE",
):
    lines = _headline_lines(hl)
    print(f"  {hl!r} -> {lines}")
    assert len(lines) <= 3, lines
    assert " ".join(lines).split() == hl.upper().split(), lines

print("\n--- scaffolding rejection ---")
for text, expected in [
    ("Why India is Building Airports: Economic Rationale 1", True),
    ("Here's the simple view before wider adoption:", True),
    ("Web Search: airports india", True),
    ("", True),
    ("Government Push", False),
    ("Boosts regional connectivity", False),
]:
    got = _is_placeholder(text)
    print(f"  placeholder={got!s:5} (expected {expected!s:5}) {text!r}")
    assert got is expected, (text, got, expected)

bp = CreativeBlueprint(
    format="infographic",
    layout_type="carousel_story",
    headline="Why India Is Building Airports Everywhere",
    supporting_line="Building today for a connected, empowered tomorrow.",
    stat_highlights=[
        "15.4% Annual growth in passenger traffic",
        "352 MN+ Passengers in FY2024",
        "2.7X Increase in aircraft movements",
        "No. 3 largest domestic aviation market",
        "999 This fifth stat must be dropped",
    ],
    sections=[
        S(section_label="Airports operational as of May 2024", stat="148"),
        S(section_label="Underserved destinations identified", stat="120+"),
        S(section_label="Airports made operational under UDAN", stat="79"),
        S(section_label="Regional connectivity", body="Boosts inclusive growth"),
        S(section_label="New markets", body="Drives tourism and trade"),
        S(section_label="Logistics", body="Strengthens cargo infrastructure"),
        S(section_label="Security", body="Enhances disaster response"),
        S(section_label="How it works", body="Here's the simple view before wider adoption:"),
    ],
    customer_quote="More airports. More connections.",
    cta="More opportunities. A Viksit Bharat in the sky.",
    source_footer="Source: Ministry of Civil Aviation, IATA, McKinsey",
)

prompt = build_data_story_prompt(bp, canvas_desc="1080x1350")

assert DATA_BG_TOP in prompt and DATA_BG_MID in prompt and DATA_BG_BOTTOM in prompt
assert "#87CEFA" not in prompt, "saturated sky-blue must not appear"
assert "simple view before wider adoption" not in prompt, "scaffolding leaked into prompt"
assert prompt.count("COL") >= 4, "hero band needs 4 columns"
assert '"148"' in prompt and '"120+"' in prompt and '"79"' in prompt
assert "999" not in prompt, "hero band must cap at 4 figures"
assert "every string fits fully" in prompt or "never clip" in prompt.casefold()
assert "NO border, frame, outline" in prompt

assert "SUPPORTING INSIGHTS" in prompt and "soft rounded cards" in prompt
assert "Claymorphic / Octane" in prompt or "claymorphic" in prompt.casefold()
assert len(prompt) < 9000, f"prompt would be truncated at the 9000 cap: {len(prompt)}"
assert "premium sample-grade 3D information poster" in prompt, "AVOID block must survive"

print("\n--- five prompt components present ---")
for part in ("1. CONTENT", "2. LAYOUT", "3. VISUAL STYLE", "4. BRAND STYLE", "5. AVOID"):
    assert part in prompt, part
    print(f"  ok  {part}")

print("\n--- real 3D icon spec ---")
for phrase in (
    "Claymorphic / Octane",
    "FORBIDDEN: flat vector, emoji",
    "contact shadows",
):
    assert phrase in prompt, phrase
    print(f"  ok  {phrase}")

print("\n--- dangling truncation guard ---")
from app.services.image_generation.data_story_image_prompt import _scrub

for raw, limit in [
    ("UDAN routes connect Tiers2 and Tier3 cities across the country", 6),
    ("India's widespread airport construction is driven by a strategic economic", 9),
    ("Boosts regional connectivity and inclusive growth for the", 20),
]:
    out = _scrub(raw, max_words=limit)
    last = out.split()[-1].casefold()
    print(f"  {out!r}")
    assert last not in {"and", "a", "the", "for", "by", "of", "to", "with"}, out

# Reason-only content must collapse to a single full-width panel.
thin = CreativeBlueprint(
    format="infographic",
    layout_type="carousel_story",
    headline="Why India Is Building Airports Everywhere",
    sections=[
        S(section_label="Regional connectivity", body="Boosts inclusive growth"),
        S(section_label="New markets", body="Drives tourism and trade"),
    ],
)
thin_prompt = build_data_story_prompt(thin)
assert "soft rounded cards side-by-side" in thin_prompt or "soft rounded cards" in thin_prompt
assert "2-column grid" not in thin_prompt or "CARD" in thin_prompt

print("\n--- generated prompt ---")
print(prompt)
print(f"\nprompt length: {len(prompt)} chars (limit 6000)")
print("data_story_template_ok")
