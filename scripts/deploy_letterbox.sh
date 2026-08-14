#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-letterbox.tgz

FILES="
app/services/image_generation/dalle_service.py
app/services/image_generation/data_story_image_prompt.py
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
from PIL import Image, ImageDraw
from app.services.image_generation.dalle_service import _resize_to_export
from app.services.image_generation.data_story_image_prompt import build_data_story_prompt
from app.graph.models.layer7c_models import CreativeBlueprint, BlueprintInfographicSection as S

img = Image.new("RGB", (1024, 1536), (211, 234, 252))
d = ImageDraw.Draw(img)
d.rectangle((40, 8, 984, 70), fill=(0, 57, 117))
d.rectangle((40, 1466, 984, 1528), fill=(255, 164, 0))
buf = BytesIO(); img.save(buf, format="PNG"); raw = buf.getvalue()

def count(data, pred):
    im = Image.open(BytesIO(data)).convert("RGB"); px = im.load(); n = 0
    for y in range(0, im.height, 4):
        for x in range(0, im.width, 4):
            if pred(*px[x, y]): n += 1
    return n

lb = _resize_to_export(raw, 1080, 1350, letterbox=True)
cr = _resize_to_export(raw, 1080, 1350, allow_crop=True)
assert count(lb, lambda r,g,b: r>180 and g<200 and b<80) > 50
assert count(cr, lambda r,g,b: r>180 and g<200 and b<80) < 10

bp = CreativeBlueprint(format="infographic", layout_type="carousel_story",
                       headline="RBI TO TEST", sections=[S(section_label="a", body="x")])
p = build_data_story_prompt(bp)
assert "cropped to 4:5" not in p
assert "6% in from every" in p
print("letterbox_live=1 no_text_crop=1")
PY

curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
