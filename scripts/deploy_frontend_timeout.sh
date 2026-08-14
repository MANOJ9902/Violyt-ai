#!/bin/bash
set -e
cd ~/Violyt_Repo
tar -xzf ~/violyt-frontend-fix.tgz

echo "=== source now says ==="
grep -n 'timeout:' frontend/lib/api/client.ts

cd ~/violyt-deploy
echo "=== rebuilding frontend (Next.js bundles the timeout at build time) ==="
sudo docker compose build frontend
sudo docker compose up -d frontend
sleep 10
sudo docker compose ps frontend

echo "=== the built bundle must carry 1200000, not 600000 ==="
sudo docker exec violyt-deploy-frontend-1 sh -c \
  "grep -rlo '1200000' /app/.next 2>/dev/null | head -3" || echo "not found in .next"

curl -s -o /dev/null -w 'frontend=%{http_code}\n' http://127.0.0.1:3001
