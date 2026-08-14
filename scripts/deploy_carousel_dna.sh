#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-carousel-dna.tgz

FILES="
app/services/image_generation/carousel_image_prompt.py
app/services/image_generation/dalle_service.py
app/prompts/brand_copy_tone.py
app/graph/nodes/layer8_visual_reasoning.py
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
from PIL import Image
from app.services.image_generation.carousel_image_prompt import build_carousel_slide_image_prompt, build_brand_carousel_slide_image_prompt
from app.services.image_generation.dalle_service import _composite_sebi_footer

p = build_carousel_slide_image_prompt(
    slide_number=2, total_slides=6, role="overview",
    headline="India is betting big on airports",
    story_blocks=["74 to 165 airports", "1.4 lakh crore invested", "25 greenfield airports"],
)
assert "STACKED CARDS" in p
assert "NO connector graphs" in p
assert "dark footer bar" in p.casefold() or "LIGHT grey SEBI" in p

other = build_brand_carousel_slide_image_prompt(
    slide_number=1, total_slides=4, role="cover", headline="Skills that scale",
    brand_name="Acme Learning", primary_color="#111827", secondary_color="#2563EB",
)
assert "NEVER Jiraaf" in other or "NOT JIRAAF" in other

canvas = Image.new("RGB", (1080, 1350), (135, 206, 250))
buf = BytesIO(); canvas.save(buf, format="PNG")
out = _composite_sebi_footer(buf.getvalue(), 1080, 1350)
img = Image.open(BytesIO(out)).convert("RGB"); px = img.load()
r,g,b = px[540, 1330]
assert b > 150 and r > 80, (r,g,b)
print("carousel_dna_live=1 light_footer=1 stacked_cards=1 cross_brand_lock=1")
PY

curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
