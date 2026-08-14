#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-insight.tgz

FILES="
app/services/blueprint_quality.py
app/services/image_generation/data_story_image_prompt.py
app/prompts/layer7_copy_engine.py
"
for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  for f in $FILES; do
    sudo docker cp "$f" "$c:/app/$f"
  done
  echo "patched_$c"
done

cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 12

sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
from types import SimpleNamespace
from app.graph.models.layer7c_models import BlueprintInfographicSection as S, CreativeBlueprint
from app.services.blueprint_quality import (
    ensure_insightful_sections, is_empty_insight, score_blueprint_editorial_qa,
)
from app.services.image_generation.data_story_image_prompt import split_stat

assert is_empty_insight("Everything you need to know about India's")
fig, lab = split_stat("Rs 98,000 crore total investment")
assert "cr" in fig and "ore" not in lab.casefold(), (fig, lab)

bad = CreativeBlueprint(
    format="infographic", layout_type="carousel_story",
    headline="India airports",
    stat_highlights=["₹98,000 crore total investment"],
    sections=[
        S(section_label="NUMBERED PROOF", stat="1", body="India needs a lot. India needs a lot more airports."),
        S(section_label="SUPPORTING", body="Everything you need to know about India's"),
    ],
)
scores = score_blueprint_editorial_qa(bad, user_prompt="why airports")
assert scores["copy_complete"] < 6

ci = SimpleNamespace(
    insight_thesis="Airport spend decentralises growth beyond metros.",
    evidence=[
        SimpleNamespace(approved_for_creative=True, claim="UDAN unlocks Tier-2 connectivity", value="79 airports under UDAN"),
        SimpleNamespace(approved_for_creative=True, claim="Greenfield airports open new tourism belts", value="₹38,000 cr greenfield"),
    ],
    format_architecture=SimpleNamespace(hero_statistic="₹98,000 cr", supporting_data_points=[], core_insight="Decentralise growth"),
)
fixed = ensure_insightful_sections(bad, content_intelligence=ci)
bodies = " | ".join(s.body or "" for s in fixed.sections)
assert "Everything you need" not in bodies
assert "UDAN" in bodies or "Greenfield" in bodies
print("insight_live=1 bodies=", bodies)
PY

curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
