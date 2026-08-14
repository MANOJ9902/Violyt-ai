#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-sample-dna.tgz

FILES="
app/services/image_generation/dalle_service.py
app/services/image_generation/data_story_image_prompt.py
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
from io import BytesIO
from PIL import Image, ImageDraw
from app.services.image_generation.dalle_service import _make_background_transparent
from app.services.image_generation.data_story_image_prompt import build_data_story_prompt
from app.graph.models.layer7c_models import CreativeBlueprint, BlueprintInfographicSection as S

# Logo white plate must vanish
img = Image.new("RGBA", (400, 160), (255, 255, 255, 255))
d = ImageDraw.Draw(img)
d.ellipse((30, 40, 110, 120), fill=(255, 164, 0, 255))
d.rectangle((140, 55, 360, 105), fill=(0, 57, 117, 255))
cleared = _make_background_transparent(img)
px = cleared.load(); w, h = cleared.size
white = sum(1 for y in range(h) for x in range(w) if px[x,y][3] and px[x,y][0]>240 and px[x,y][1]>240 and px[x,y][2]>240)
assert white < 40, white

bp = CreativeBlueprint(
    format="infographic", layout_type="carousel_story",
    headline="RBI TO TEST PLASTIC CURRENCY NOTES",
    supporting_line="Testing plastic notes for durability, security and sustainability.",
    stat_highlights=["2-3X longer lifespan", "20 billion notes replaced yearly", "30% cost reduction", "5 pilot cities tested"],
    sections=[
        S(section_label="Why is RBI planning this?", body="More durable, secure, cost-effective currency"),
        S(section_label="Trial before rollout", body="Tests in select cities before nationwide launch"),
        S(section_label="Top reasons", body="Longer life notes last much longer than paper"),
    ],
    customer_quote="Innovating today for a stronger tomorrow",
    cta="A SMARTER STEP TOWARDS A STRONGER INDIA",
    source_footer="Source: rbi.org.in",
)
p = build_data_story_prompt(bp)
assert "Claymorphic / Octane" in p
assert "KEY STATISTICS" in p and "SUPPORTING INSIGHTS" in p
assert "soft rounded cards" in p
assert "flat vector" in p.casefold()
print("sample_dna_live=1 logo_clear=1 prompt_len=", len(p))
PY

curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
