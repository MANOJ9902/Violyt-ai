#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-qa-fix.tgz

for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  sudo docker cp app/graph/nodes/layer7c_content_prep.py \
    "$c:/app/app/graph/nodes/layer7c_content_prep.py"
  echo "patched_$c"
done

cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 12

sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
from app.graph.nodes.layer7c_content_prep import _scores_improved

stuck = {"answers_why": 6, "has_real_data": 3, "claims_verified": 6,
         "narrative_coherent": 7, "copy_complete": 8}
assert _scores_improved(stuck, dict(stuck)) is False, "stalled retry must stop"
assert _scores_improved({**stuck, "has_real_data": 6}, stuck) is True
assert _scores_improved({**stuck, "has_real_data": 6, "answers_why": 4}, stuck) is False
print("stall_exit_live=1")
PY

curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
