#!/bin/bash
set -euo pipefail
cd ~/Violyt_Repo
tar -xzf ~/violyt-isolation.tgz

FILES="
app/services/brand_visual_pack.py
app/graph/nodes/layer2_brand_intelligence.py
app/graph/nodes/layer8_visual_reasoning.py
app/prompts/brand_visual_palette.py
app/prompts/layer2_brand_intelligence.py
app/prompts/layer8_visual_reasoning.py
app/services/image_generation/carousel_image_prompt.py
app/services/image_generation/data_story_image_prompt.py
app/services/image_generation/explain_image_prompt.py
"

for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  for f in $FILES; do
    sudo docker exec "$c" mkdir -p "/app/$(dirname "$f")"
    sudo docker cp "$f" "$c:/app/$f"
    sudo docker cp "$f" "$c:/usr/local/lib/python3.12/site-packages/$f" 2>/dev/null || true
  done
  echo "patched_$c"
done

cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 16

sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
from app.services.brand_visual_pack import build_visual_pack
from app.services.image_generation.data_story_image_prompt import build_data_story_prompt
from types import SimpleNamespace

pack = build_visual_pack(
    brand_id="test",
    brand_name="Jiraaf",
    resolved_brand_context={
        "brand_name": "Jiraaf",
        "visual_identity": {
            "brand_color_palette": {
                "primary": "#3D3DBE",
                "secondary": "#FFCBCB",
                "additional": [
                    {"name": "accent", "hex": "#00CB91"},
                    {"name": "secondary", "hex": "#FFA400"},
                ],
            }
        },
    },
)
assert pack.primary == "#3D3DBE", pack.primary
assert pack.secondary == "#FFCBCB", pack.secondary
assert pack.accent == "#00CB91", pack.accent
assert pack.card == "#FFCBCB", pack.card
assert pack.background == "#FFFFFF", pack.background
lock = pack.palette_lock()
assert "#FFA400" not in lock
assert "#3D3DBE" in lock and "#FFCBCB" in lock and "#00CB91" in lock
bp = SimpleNamespace(
    headline="Why the dollar dominates",
    title="", supporting_line="Trade", source_footer="", customer_quote="",
    cta="Learn more", stat_highlights=["60% of reserves"], proof_points=[],
    sections=[SimpleNamespace(section_label="Reserves", body="Deep markets.", stat="60%", includes=[])],
)
prompt = build_data_story_prompt(bp, palette=pack.palette_map())
assert "#FFCBCB" in prompt and "#3D3DBE" in prompt and "#00CB91" in prompt
assert "#FFA400" not in prompt
print("palette_from_brand_space=1 secondary_on_cards=1 extra_orange_blocked=1")
PY

curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
sudo docker ps --format '{{.Names}} {{.Status}}' | grep -E 'api-1|worker-1'
