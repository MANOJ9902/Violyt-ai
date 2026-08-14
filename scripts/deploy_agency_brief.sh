#!/bin/bash
set -e
cd ~/Violyt_Repo
for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  sudo docker cp app/graph/models/content_intelligence_models.py "$c:/app/app/graph/models/content_intelligence_models.py"
  sudo docker cp app/graph/models/layer7c_models.py "$c:/app/app/graph/models/layer7c_models.py"
  sudo docker cp app/services/content_intelligence.py "$c:/app/app/services/content_intelligence.py"
  sudo docker cp app/services/blueprint_quality.py "$c:/app/app/services/blueprint_quality.py"
  sudo docker cp app/graph/nodes/layer7c_content_prep.py "$c:/app/app/graph/nodes/layer7c_content_prep.py"
  echo "patched_$c"
done
cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 14
sudo docker compose ps api worker
sudo docker exec violyt-deploy-api-1 grep -n 'class AgencyBrief' /app/app/graph/models/content_intelligence_models.py | head -1
sudo docker exec violyt-deploy-api-1 grep -n 'agency_brief' /app/app/services/content_intelligence.py | head -3
curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
