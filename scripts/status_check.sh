#!/bin/bash
echo "=== health ==="
curl -s -o /dev/null -w 'api=%{http_code}\n' http://127.0.0.1:8000/health
curl -s -o /dev/null -w 'frontend=%{http_code}\n' http://127.0.0.1:3001

echo "=== nginx timeouts ==="
sudo grep -E 'proxy_read_timeout|send_timeout' /etc/nginx/sites-enabled/default | sort -u

echo "=== frontend timeout ==="
sudo docker exec violyt-deploy-frontend-1 sh -c \
  'grep -rho "timeout:12e5" /app/.next/static/chunks/*.js 2>/dev/null | head -1; echo; grep -rl "pipeline (20 min)" /app/.next 2>/dev/null | wc -l'

echo "=== pool + stall + carousel ==="
sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
from app.db.session import engine
from app.graph.nodes.layer7c_content_prep import _scores_improved
from app.services.image_generation.carousel_image_prompt import ROLE_LAYOUT_SPECS
print('pool', engine.pool.size(), engine.pool._max_overflow)
s={'answers_why':6,'has_real_data':3,'claims_verified':6,'narrative_coherent':7,'copy_complete':8}
print('stall_exit', _scores_improved(s, dict(s)) is False)
print('carousel_roles', sorted(ROLE_LAYOUT_SPECS))
PY
