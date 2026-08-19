#!/bin/bash
set -e

echo "=== Deploying Pipeline Fix to Production Containers ==="

# 1. Update Python backend containers (API & Worker)
cd ~/Violyt_Repo
for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  sudo docker cp app/graph/hydrate.py "$c:/app/app/graph/hydrate.py"
  sudo docker cp app/api/routes/pipeline.py "$c:/app/app/api/routes/pipeline.py"
  sudo docker cp app/graph/state.py "$c:/app/app/app/graph/state.py" 2>/dev/null || sudo docker cp app/graph/state.py "$c:/app/app/graph/state.py"
  echo "Patched python container $c"
done

cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 5

# 2. Rebuild Frontend image with updated WorkspaceChat.tsx
echo "=== Rebuilding Frontend Container ==="
cd ~/Violyt_Repo/frontend
sudo docker build \
  --build-arg NEXT_PUBLIC_ENV=production \
  --build-arg NEXT_PUBLIC_API_BASE_URI=https://65.0.82.127 \
  --build-arg NEXT_PUBLIC_ENABLE_MOCK_UI=false \
  --build-arg NEXT_PUBLIC_MOCK_ROLE=TENANT_ADMIN \
  -t violyt-frontend:local .

cd ~/violyt-deploy
sudo docker compose up -d --no-deps frontend

echo "=== Deployment Complete ==="
curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8000/health
