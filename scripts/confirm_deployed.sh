#!/bin/bash
echo "=== health ==="
curl -s -o /dev/null -w 'api=%{http_code}\n' http://127.0.0.1:8000/health

echo "=== live checks ==="
sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
from io import BytesIO
from PIL import Image, ImageDraw
from app.services.image_generation.dalle_service import _make_background_transparent
from app.services.image_generation.data_story_image_prompt import build_data_story_prompt
from app.graph.models.layer7c_models import CreativeBlueprint, BlueprintInfographicSection as S

img = Image.new("RGBA", (400, 160), (255, 255, 255, 255))
d = ImageDraw.Draw(img)
d.ellipse((30, 40, 110, 120), fill=(255, 164, 0, 255))
d.rectangle((140, 55, 360, 105), fill=(0, 57, 117, 255))
cleared = _make_background_transparent(img)
px = cleared.load(); w, h = cleared.size
white = sum(1 for y in range(h) for x in range(w) if px[x,y][3] and px[x,y][0]>240 and px[x,y][1]>240 and px[x,y][2]>240)

bp = CreativeBlueprint(
    format="infographic", layout_type="carousel_story",
    headline="RBI TO TEST PLASTIC CURRENCY NOTES",
    supporting_line="Testing plastic notes for durability.",
    stat_highlights=["2-3X longer lifespan", "30% cost reduction"],
    sections=[S(section_label="Why", body="More durable currency"), S(section_label="Trial", body="Select cities first")],
)
p = build_data_story_prompt(bp)
print("logo_white_left", white)
print("claymorphic", "Claymorphic / Octane" in p)
print("key_stats", "KEY STATISTICS" in p)
print("supporting", "SUPPORTING INSIGHTS" in p)
print("cards", "soft rounded cards" in p)
print("uptime_ok", white < 40 and "Claymorphic / Octane" in p)
PY

sudo docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'api-1|worker-1'
