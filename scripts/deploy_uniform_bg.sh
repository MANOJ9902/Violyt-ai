#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-uniform-bg.tgz
for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  sudo docker cp app/services/image_generation/dalle_service.py \
    "$c:/app/app/services/image_generation/dalle_service.py"
  sudo docker cp app/services/image_generation/carousel_image_prompt.py \
    "$c:/app/app/services/image_generation/carousel_image_prompt.py"
  echo "patched_$c"
done
cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 12
sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
from io import BytesIO
from PIL import Image
from app.services.image_generation.dalle_service import _composite_sebi_footer
BG = (211, 234, 252)
img = Image.new("RGB", (1080, 1350), BG)
buf = BytesIO(); img.save(buf, format="PNG")
out = _composite_sebi_footer(buf.getvalue(), 1080, 1350)
px = Image.open(BytesIO(out)).convert("RGB").load()
for x in (8, 20, 1060, 1072):
    assert px[x, 1320] == BG, px[x, 1320]
src = open("/app/app/services/image_generation/dalle_service.py").read()
assert "NO filled rectangle" in src or "text floats on the slide" in src
print("uniform_bg_live=1")
PY
curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
