#!/bin/bash
set -e
cd ~/Violyt_Repo
for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  sudo docker cp app/graph/graph.py "$c:/app/app/graph/graph.py"
  sudo docker cp app/graph/state.py "$c:/app/app/graph/state.py"
  sudo docker cp app/graph/routing.py "$c:/app/app/graph/routing.py"
  sudo docker cp app/graph/models/content_intelligence_models.py "$c:/app/app/graph/models/content_intelligence_models.py"
  sudo docker cp app/graph/nodes/layer5_concept_engine.py "$c:/app/app/graph/nodes/layer5_concept_engine.py"
  sudo docker cp app/graph/nodes/layer6_format_engine.py "$c:/app/app/graph/nodes/layer6_format_engine.py"
  sudo docker cp app/graph/nodes/layer6b_content_intelligence.py "$c:/app/app/graph/nodes/layer6b_content_intelligence.py"
  sudo docker cp app/graph/nodes/layer7_copy_engine.py "$c:/app/app/graph/nodes/layer7_copy_engine.py"
  sudo docker cp app/graph/nodes/layer10_evaluation.py "$c:/app/app/graph/nodes/layer10_evaluation.py"
  sudo docker cp app/graph/nodes/repair_layer.py "$c:/app/app/graph/nodes/repair_layer.py"
  sudo docker cp app/services/content_intelligence.py "$c:/app/app/services/content_intelligence.py"
  sudo docker cp app/services/blueprint_quality.py "$c:/app/app/services/blueprint_quality.py"
  sudo docker cp app/prompts/layer3_brief_interpreter.py "$c:/app/app/prompts/layer3_brief_interpreter.py"
  sudo docker cp app/prompts/layer5_concept_engine.py "$c:/app/app/prompts/layer5_concept_engine.py"
  sudo docker cp app/prompts/layer6_format_engine.py "$c:/app/app/prompts/layer6_format_engine.py"
  echo "patched_$c"
done
cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 14
sudo docker compose ps api worker
sudo docker exec violyt-deploy-api-1 grep -n 'l6b_content_intelligence", "l5' /app/app/graph/graph.py | head -2
sudo docker exec violyt-deploy-api-1 grep -n evaluate_blueprint_gate /app/app/services/blueprint_quality.py | head -1
curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
