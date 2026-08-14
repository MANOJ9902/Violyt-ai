#!/bin/bash
set -e
# The frontend image is prebuilt and compose has no build: section, so the axios
# timeout (inlined by Next at build time) only changes on a real image build.
# NEXT_PUBLIC_API_BASE_URI is a build ARG defaulting to localhost:8000 — it MUST
# be passed or the browser would call nothing.

echo "=== API origin baked into the CURRENT bundle ==="
sudo docker exec violyt-deploy-frontend-1 sh -c \
  "grep -rhoE 'https?://[0-9a-zA-Z._:-]+' /app/.next/static/chunks/*.js | sort | uniq -c | sort -rn | head -8"

echo
echo "=== keep a rollback tag of the working image ==="
sudo docker tag violyt-frontend:local violyt-frontend:rollback
sudo docker images violyt-frontend --format '{{.Repository}}:{{.Tag}} {{.ID}}'

echo
echo "=== building (args mirror the compose environment) ==="
cd ~/Violyt_Repo/frontend
sudo docker build \
  --build-arg NEXT_PUBLIC_ENV=production \
  --build-arg NEXT_PUBLIC_API_BASE_URI=https://65.0.82.127 \
  --build-arg NEXT_PUBLIC_ENABLE_MOCK_UI=false \
  --build-arg NEXT_PUBLIC_MOCK_ROLE=TENANT_ADMIN \
  -t violyt-frontend:local . 2>&1 | tail -25
