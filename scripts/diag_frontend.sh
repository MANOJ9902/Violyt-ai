#!/bin/bash
echo "=== compose frontend service definition ==="
cd ~/violyt-deploy
sed -n '/frontend:/,/^  [a-z]/p' docker-compose*.y*ml | head -30

echo
echo "=== does the running bundle still carry the OLD 10 min timeout? ==="
sudo docker exec violyt-deploy-frontend-1 sh -c \
  "grep -rho 'timeout:6[0-9]*' /app/.next/static/chunks/*.js 2>/dev/null | sort -u | head"
sudo docker exec violyt-deploy-frontend-1 sh -c \
  "grep -rho 'timeout:1[0-9]*' /app/.next/static/chunks/*.js 2>/dev/null | sort -u | head"

echo
echo "=== where is the frontend source on the box? ==="
ls -d ~/Violyt_Repo/frontend 2>/dev/null && grep -n 'timeout:' ~/Violyt_Repo/frontend/lib/api/client.ts
