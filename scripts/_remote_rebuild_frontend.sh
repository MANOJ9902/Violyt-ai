#!/bin/bash
set -e
cd ~/Violyt_Repo
tar xzf _deploy_fe.tar.gz
rm -f _deploy_fe.tar.gz
rm -f frontend/components/chat/ChatHistorySidebar.tsx

echo "=== Rebuilding frontend ==="
cd ~/Violyt_Repo/frontend
sudo docker tag violyt-frontend:local violyt-frontend:rollback || true
sudo docker build \
  --build-arg NEXT_PUBLIC_ENV=production \
  --build-arg NEXT_PUBLIC_API_BASE_URI=https://65.0.82.127 \
  --build-arg NEXT_PUBLIC_ENABLE_MOCK_UI=false \
  --build-arg NEXT_PUBLIC_MOCK_ROLE=TENANT_ADMIN \
  -t violyt-frontend:local .

cd ~/violyt-deploy
sudo docker compose up -d --no-deps --force-recreate frontend
sleep 8
curl -s -o /dev/null -w "frontend_local=%{http_code}\n" http://127.0.0.1:3001/ || true
curl -sk -o /dev/null -w "site_https=%{http_code}\n" https://127.0.0.1/ || true
curl -s -o /dev/null -w "api_health=%{http_code}\n" http://127.0.0.1:8000/health || true
echo "=== Deploy complete ==="
