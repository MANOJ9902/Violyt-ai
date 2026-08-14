#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-jiraaf-dna.tgz

FILES="
app/prompts/brand_copy_tone.py
app/prompts/brand_visual_palette.py
app/prompts/layer7_copy_engine.py
app/prompts/layer7c_content_prep.py
app/prompts/layer8_visual_reasoning.py
app/prompts/jiraaf_sample_templates.py
app/prompts/carousel_layout_grid.py
app/graph/nodes/layer8_visual_reasoning.py
app/graph/models/text_coercion.py
app/graph/nodes/layer2_brand_intelligence.py
app/prompts/layer2_brand_intelligence.py
app/graph/models/layer7_models.py
app/graph/models/layer7c_models.py
app/services/blueprint_quality.py
app/services/content_intelligence.py
app/services/live_research.py
app/core/config.py
app/db/session.py
app/services/copy_proofread.py
app/services/image_generation/dalle_service.py
app/services/image_generation/explain_image_prompt.py
app/services/image_generation/data_story_image_prompt.py
app/services/image_generation/carousel_image_prompt.py
"

for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  for f in $FILES; do
    sudo docker cp "$f" "$c:/app/$f"
  done
  echo "patched_$c"
done

cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 14
sudo docker compose ps api worker

sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
import inspect
import app.graph  # noqa: F401  (avoids the prompts<->graph circular import)
import app.prompts.layer8_visual_reasoning as l8
from app.prompts.brand_copy_tone import JIRAAF_BG
from app.prompts.brand_visual_palette import is_jiraaf_brand
from app.prompts.layer7_copy_engine import CopyEnginePromptBuilder
from app.prompts.jiraaf_layout import classify_layout
from app.graph.models.layer7c_models import (
    CreativeBlueprint,
    BlueprintInfographicSection as S,
)
from app.services.blueprint_quality import evaluate_blueprint_gate
from app.services.image_generation import carousel_image_prompt as cip
from app.services.image_generation import dalle_service as ds

# 1. one palette everywhere
assert JIRAAF_BG == "#87CEFA", JIRAAF_BG
assert cip.CAROUSEL_BG == "#87CEFA", cip.CAROUSEL_BG
assert ds._SEBI_FOOTER_BG == (135, 206, 250, 255), ds._SEBI_FOOTER_BG

# 2. misspelled Brand Space names still resolve to Jiraaf
for name in ("Jiraaf", "Jirraf", "Jiraff", "JIRRAF"):
    assert is_jiraaf_brand(name), name
for name in ("Jira", "Cognixia", "Niroggi", "", None):
    assert not is_jiraaf_brand(name), name

# 3. a Jirraf-named space gets the Jiraaf visual system, not the generic teal one
builder_cls = next(v for v in vars(l8).values() if inspect.isclass(v) and hasattr(v, "INFO_BG"))
builder = builder_cls()
sig = inspect.signature(builder._build_infographic_prompt)
kw = {
    "headline": "Why India Is Building Airports Everywhere",
    "supporting_line": "157 airports today, up from 74 in 2014.",
    "infographic_sections": [{"section_label": "UDAN", "includes": ["619 routes"], "stat": "619"}],
    "cta": "Learn more",
    "user_prompt": "why India is building airports everywhere",
    "visual_mood": "premium editorial",
    "color_behavior": "",
    "layout_type": "carousel_story",
}
for p in sig.parameters.values():
    if p.kind is p.KEYWORD_ONLY and p.default is p.empty:
        kw.setdefault(p.name, [] if p.name.endswith(("s", "flow")) else "")
kw = {k: v for k, v in kw.items() if k in sig.parameters and k != "brand_name"}
for name in ("Jiraaf", "Jirraf"):
    prompt = builder._build_infographic_prompt(brand_name=name, **kw)
    assert "DENSE INFOGRAPHIC EXPLAIN" in prompt, name
    assert "BRAND EDUCATION POSTER" not in prompt, name
    assert "#87CEFA" in prompt, name

# 4. no reference-sample copy leaks into an explain prompt
topic = "create an infographic with real data points on why India is building airports everywhere"
assert classify_layout(topic, "infographic").layout_type == "carousel_story"
sys_prompt = CopyEnginePromptBuilder().build_system(
    format_name="infographic", user_prompt=topic, layout_type="carousel_story"
).lower()
for leak in ("top investor in india", "strong economic ties", "top 6 countries investing"):
    assert leak not in sys_prompt, leak

# 5. wrong-topic and sparse blueprints are blocked
bad = CreativeBlueprint(
    headline="Top 6 Countries Investing in India",
    supporting_line="A strong signal from global investors.",
    sections=[S(section_label="United States", includes=["Top investor in India"], stat="Rs 50B")],
)
ev, target = evaluate_blueprint_gate(bad, user_prompt=topic)
assert not ev.overall_pass and ev.contamination_risk == "high"

thin = CreativeBlueprint(
    format="infographic",
    layout_type="carousel_story",
    headline="India Airport Network Is Expanding Fast",
    sections=[S(section_label=f"Card {i}", includes=["short line"]) for i in range(3)],
)
ev2, target2 = evaluate_blueprint_gate(thin, user_prompt=topic)
assert not ev2.overall_pass and target2 == "l7", target2

# 6. dict-shaped LLM list entries no longer crash the run
from app.graph.models.layer7_models import CopyOutput
c = CopyOutput.model_validate({
    "headline": "Why India Is Building Airports Everywhere",
    "stat_highlights": [
        {"number": "450", "label": "Operational Airports"},
        {"number": "$1.5T", "label": "Infrastructure Investment"},
    ],
    "infographic_sections": [
        {"section_label": "UDAN", "includes": [{"mini_title": "Routes", "fact": "619 operational"}]}
    ],
})
assert c.stat_highlights[0] == "450 Operational Airports", c.stat_highlights
assert c.infographic_sections[0].includes == ["Routes | 619 operational"], c.infographic_sections[0].includes

# 7. LLM placeholder brand names never reach downstream layers
import importlib
l2 = importlib.import_module("app.graph.nodes.layer2_brand_intelligence")
assert l2._is_placeholder_name("Unknown \u2014 Brand ID 7fe7bd57")
assert l2._is_placeholder_name("Unknown - Brand ID 7fe7bd57")
assert l2._is_placeholder_name("")
assert not l2._is_placeholder_name("Jiraaf")

# 8. Brand Space palette drives Jiraaf colours, with a locked fallback
from app.prompts.brand_visual_palette import resolve_jiraaf_palette
live = resolve_jiraaf_palette(primary="#003A79", secondary="#FF9E00")
assert live["headline"] == "#003A79" and live["headline_source"] == "brand_space", live
assert live["accent"] == "#FF9E00" and live["accent_source"] == "brand_space", live
assert live["background"] == JIRAAF_BG, live
blank = resolve_jiraaf_palette()
assert blank["headline_source"] == "locked_default" and blank["accent_source"] == "locked_default", blank

# 9. Data-story infographic template matches the reference sample
from app.graph.models.layer7c_models import BlueprintInfographicSection as S
from app.services.image_generation.data_story_image_prompt import (
    DATA_BG_BOTTOM, DATA_BG_MID, DATA_BG_TOP, build_data_story_prompt, split_stat,
)
assert split_stat("15.4% Annual growth in traffic") == ("15.4%", "Annual growth in traffic")
assert split_stat("352 MN+ Passengers in FY2024")[0] == "352 MN+"
assert split_stat("No. 3 largest domestic aviation market")[0] == "No. 3"

ds = CreativeBlueprint(
    format="infographic", layout_type="carousel_story",
    headline="Why India Is Building Airports Everywhere",
    stat_highlights=["15.4% growth in traffic", "352 MN+ passengers in FY2024",
                     "2.7X aircraft movements", "No. 3 aviation market"],
    sections=[
        S(section_label="Airports operational", stat="148"),
        S(section_label="Underserved destinations", stat="120+"),
        S(section_label="Operational under UDAN", stat="79"),
        S(section_label="Regional connectivity", body="Boosts inclusive growth"),
        S(section_label="New markets", body="Drives tourism and trade"),
        S(section_label="Logistics", body="Strengthens cargo infrastructure"),
        S(section_label="How it works", body="Here's the simple view before wider adoption:"),
    ],
    source_footer="Source: Ministry of Civil Aviation, IATA",
)
dsp = build_data_story_prompt(ds, canvas_desc="1080x1350")
assert DATA_BG_TOP in dsp and DATA_BG_MID in dsp and DATA_BG_BOTTOM in dsp, "gradient BG missing"
assert "#87CEFA" not in dsp, "saturated sky-blue leaked into data-story prompt"
assert "simple view before wider adoption" not in dsp, "scaffolding leaked into artwork"
assert "SUPPORTING INSIGHTS" in dsp and "soft rounded cards" in dsp
assert '"148"' in dsp and '"79"' in dsp
assert "every string fits fully" in dsp and "NO border, frame, outline" in dsp
assert len(dsp) < 9000, len(dsp)
for part in ("1. CONTENT", "2. LAYOUT", "3. VISUAL STYLE", "4. BRAND STYLE", "5. AVOID"):
    assert part in dsp, part
assert "Claymorphic / Octane" in dsp, "sample-grade 3D craft missing"
assert "premium sample-grade 3D information poster" in dsp, "AVOID block must be last"

# 11. Infographic copy prompt no longer contradicts itself
from app.prompts.layer7_copy_engine import CopyEnginePromptBuilder
_b = CopyEnginePromptBuilder()
_info = _b.build_system("infographic", layout_type="carousel_story", user_prompt="why india builds airports")
_car = _b.build_system("carousel", layout_type="carousel_story", user_prompt="explain sweep in FD")
assert "Emit exactly 5\u20136 slides" not in _info, "carousel slide rules leaked into infographic"
assert "Emit exactly 5\u20136 slides" in _car, "real carousels still need slide rules"
assert "2\u20134 section blocks" not in _info, "section-count contradiction still present"
assert "sections[] = UP TO 6" in _info and "stat_highlights = UP TO 4" in _info
assert "NO-REPEAT RULE" in _info, "anti-repetition rule missing from copy contract"
assert "FEWER IS BETTER THAN REPEATED" in _info, "padding guard missing"

# 12. Word-budget clipping never ends on a dangling connector
from app.services.image_generation.data_story_image_prompt import _scrub
assert _scrub("UDAN routes connect Tiers2 and Tier3 cities", max_words=6).split()[-1].lower() != "and"

# 13. One fact can never be printed into several slots
dup = CreativeBlueprint(
    format="infographic", layout_type="carousel_story", headline="India's Airport Boom",
    stat_highlights=["100+ airports operational or developing",
                     "500+ UDAN routes connect smaller cities",
                     "100+ Airports Operational or Developing",
                     "500+ routes connect smaller cities"],
    sections=[S(section_label="100+ airports", stat="100+", body="100+ Airports Operational or Developing"),
              S(section_label="500+ routes", stat="500+", body="500+ UDAN Routes Connect Smaller Cities"),
              S(section_label="Several new airports", body="India is building airports")],
)
dp = build_data_story_prompt(dup)
slots = [l.strip() for l in dp.splitlines() if l.strip().startswith(("COL", "ROW"))]
bodies = [s.split(":", 1)[1].strip().casefold() for s in slots]
assert len(bodies) == len(set(bodies)), f"duplicate slot rendered: {bodies}"
slot_text = "\n".join(slots)
assert slot_text.count('"100+"') <= 1 and slot_text.count('"500+"') <= 1, slot_text

# 14. Research queries hunt for data, not design articles
from app.services.live_research import LiveResearchService
_plan = LiveResearchService()._heuristic_query_plan(
    "create an infographic with real data points on why India is building airports everywhere",
    {"platform_preset": "linkedin", "format": "infographic"}, {})
assert len(_plan["queries"]) >= 4, _plan["queries"]
assert not any("infographic" in q.casefold() or "linkedin" in q.casefold() for q in _plan["queries"]), _plan["queries"]

# 10. Empty-fact blueprints no longer get seeded with invented filler
from app.services.blueprint_quality import ensure_explain_sections
empty = CreativeBlueprint(format="infographic", layout_type="carousel_story", headline="X")
seeded = ensure_explain_sections(empty, layout_type="carousel_story", user_prompt="why airports")
assert not seeded.sections, "must stay empty so the gate routes to repair"

# 15. Connection pool is big enough that a long run cannot starve auth
from app.db.session import engine
from app.core.config import get_settings as _gs
_s = _gs()
assert engine.pool.size() == 15 and engine.pool._max_overflow == 10, engine.pool.status()
assert _s.db_pool_size + _s.db_max_overflow == 25
# api + worker must stay well under Postgres max_connections (100)
assert (_s.db_pool_size + _s.db_max_overflow) * 2 < 90

# 16. Export letterboxes to 4:5 — never chops headline/takeaway text
from io import BytesIO
from PIL import Image, ImageDraw
from app.services.image_generation.dalle_service import _resize_to_export
_c = Image.new("RGB", (1024, 1536), (211, 234, 252))
_d = ImageDraw.Draw(_c)
_d.rectangle((40, 8, 984, 70), fill=(0, 57, 117))
_d.rectangle((40, 1466, 984, 1528), fill=(255, 164, 0))
_buf = BytesIO(); _c.save(_buf, format="PNG"); _raw = _buf.getvalue()

def _count(data, pred):
    im = Image.open(BytesIO(data)).convert("RGB"); px = im.load(); n = 0
    for y in range(0, im.height, 4):
        for x in range(0, im.width, 4):
            if pred(*px[x, y]): n += 1
    return n

_lb = _resize_to_export(_raw, 1080, 1350, letterbox=True)
_cr = _resize_to_export(_raw, 1080, 1350, allow_crop=True)
assert Image.open(BytesIO(_lb)).size == (1080, 1350)
assert _count(_lb, lambda r,g,b: r>180 and g<200 and b<80) > 50, "letterbox must keep takeaway"
assert _count(_cr, lambda r,g,b: r>180 and g<200 and b<80) < 10, "crop must erase takeaway (sanity)"
assert ("≥6% inset" in dsp or "6% inset" in dsp) and "cropped to 4:5" not in dsp, "margin rule missing"

# 17. Panels no longer force circular icons on every row
assert "3D circular icon" not in dsp, "forced circle icons still in the prompt"
assert "never reuse an icon" in dsp or "never reuse an icon" in dsp.casefold()

# 18. Carousels stop reusing the banknote sample's props for every brand/topic
from app.services.image_generation.carousel_image_prompt import (
    _slide_spec, build_carousel_slide_image_prompt,
)
_LEAK = ("rbi seal", "note in glass", "hourglass", "recycle symbol", "india map",
         "central shield", "shield hub", "orbiting nodes", "plastic emphasised")
for _n in range(1, 11):
    _sp = _slide_spec(_n, "")
    _blob = (_sp["composition"] + " " + _sp["infographic"]).lower()
    assert not [w for w in _LEAK if w in _blob], f"slide {_n} still leaks sample props"
assert _slide_spec(7, "cover")["role"] == "cover", "role must beat slide position"
assert len({_slide_spec(n, "detail")["infographic"] for n in range(4, 9)}) >= 4
_s3 = build_carousel_slide_image_prompt(
    slide_number=3, total_slides=10, role="overview", headline="AIRPORT EXPANSION",
    body="Short line.", story_blocks=["148 airports live", "UDAN routes"], topic="airports")
assert not [w for w in _LEAK if w in _s3.lower()], "carousel prompt still leaks props"
assert "NO connector graphs" in _s3

print("all_ok bg=%s jiraaf_typo_detected=1 no_sample_leak=1 sparse_blocked=1 dict_stats_ok=1 brand_name_pinned=1 brand_space_palette=1 data_story_template=1 no_filler_seed=1 no_suffix_conflict=1 no_dangling_clip=1 no_repeat_slots=1 pool=%d no_text_crop=1 no_forced_circles=1 carousel_props_unlocked=1 research_queries=%d" % (JIRAAF_BG, _s.db_pool_size + _s.db_max_overflow, len(_plan["queries"])))
PY

curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
