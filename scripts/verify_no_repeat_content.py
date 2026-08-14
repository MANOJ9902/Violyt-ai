"""Thin evidence must produce a short honest poster, never a repeated one."""

from app.graph.models.layer7c_models import (
    BlueprintInfographicSection as S,
)
from app.graph.models.layer7c_models import (
    CreativeBlueprint,
)
from app.services.image_generation.data_story_image_prompt import build_data_story_prompt
from app.services.live_research import LiveResearchService

print("--- research query plan (was 2 polluted queries) ---")
plan = LiveResearchService()._heuristic_query_plan(
    "create an infographic with real data points on why India is building airports everywhere",
    {"platform_preset": "linkedin", "format": "infographic"},
    {},
)
for q in plan["queries"]:
    print(f"  - {q}")
assert len(plan["queries"]) >= 4, plan["queries"]
assert not any("infographic" in q.casefold() for q in plan["queries"]), "design words pollute search"
assert not any("linkedin" in q.casefold() for q in plan["queries"])
assert not plan["queries"][0].casefold().startswith("on "), plan["queries"][0]

# Reproduces the failing run: one real fact smeared across every slot.
repeated = CreativeBlueprint(
    format="infographic",
    layout_type="carousel_story",
    headline="India's Airport Boom: 100+ Airports Now",
    stat_highlights=[
        "100+ airports operational or developing",
        "500+ routes 500+UDAN Routes Connect Smaller",
        "100+ Airports Operational or Developing",
        "500+ UDAN routes connect smaller cities",
    ],
    sections=[
        S(section_label="100+ airports", stat="100+", body="100+ Airports Operational or Developing"),
        S(section_label="500+ routes", stat="500+", body="500+UDAN Routes Connect Smaller Cities"),
        S(section_label="Several new airports", body="India is building airports"),
    ],
)
prompt = build_data_story_prompt(repeated)

hero_lines = [ln for ln in prompt.splitlines() if ln.strip().startswith("COL")]
row_lines = [ln for ln in prompt.splitlines() if ln.strip().startswith("ROW")]
print("\n--- after dedup ---")
for ln in hero_lines + row_lines:
    print(f" {ln.strip()}")

slot_text = "\n".join(hero_lines + row_lines)
assert slot_text.count('"100+"') <= 1, "100+ rendered in more than one slot"
assert slot_text.count('"500+"') <= 1, "500+ rendered in more than one slot"
seen = set()
for line in hero_lines + row_lines:
    key = line.split(":", 1)[1].strip().casefold()
    assert key not in seen, f"duplicate slot rendered: {key}"
    seen.add(key)
print(f"\n  {len(hero_lines)} stat columns + {len(row_lines)} panel rows, all distinct")

# A healthy blueprint must still fill the full layout.
from scripts.verify_data_story_template import bp as rich_bp  # noqa: E402

rich = build_data_story_prompt(rich_bp)
assert len([ln for ln in rich.splitlines() if ln.strip().startswith("COL")]) == 4
print("  rich evidence still renders 4 stat columns")
print("no_repeat_content_ok")
