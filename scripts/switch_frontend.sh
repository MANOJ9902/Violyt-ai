#!/bin/bash
set -e
cd ~/violyt-deploy
sudo docker compose up -d --force-recreate frontend
sleep 12
sudo docker compose ps frontend

echo
echo "=== running bundle now says ==="
sudo docker exec violyt-deploy-frontend-1 sh -c '
  echo -n "  20 min message: "; grep -rl "pipeline (20 min)" /app/.next 2>/dev/null | wc -l
  echo -n "  10 min message: "; grep -rl "pipeline (10 min)" /app/.next 2>/dev/null | wc -l
  echo -n "  axios 12e5    : "; grep -rho "timeout:12e5" /app/.next/static/chunks/*.js 2>/dev/null | head -1
  echo -n "  axios 6e5     : "; grep -rho "timeout:6e5" /app/.next/static/chunks/*.js 2>/dev/null | head -1
'

echo
echo "=== end to end ==="
curl -s -o /dev/null -w '  frontend_local=%{http_code}\n' http://127.0.0.1:3001
curl -sk -o /dev/null -w '  https_root=%{http_code}\n' https://127.0.0.1/
curl -sk -o /dev/null -w '  api_through_nginx=%{http_code}\n' https://127.0.0.1/api/v1/brands
curl -s -o /dev/null -w '  api_health=%{http_code}\n' http://127.0.0.1:8000/health
