#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-wipe-fix.tgz
for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  sudo docker cp app/graph/nodes/layer8_visual_reasoning.py \
    "$c:/app/app/graph/nodes/layer8_visual_reasoning.py"
  sudo docker cp app/core/config.py "$c:/app/app/core/config.py"
  echo "patched_$c"
done
cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 12
sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
import inspect
from app.graph.nodes import layer8_visual_reasoning as m
from app.core.config import get_settings
src = inspect.getsource(m)
assert "wipe_reserved_corner = True" in src
assert get_settings().image_generation_timeout_seconds >= 300
print("wipe_fix_live=1 timeout_s=", get_settings().image_generation_timeout_seconds)
PY
curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
