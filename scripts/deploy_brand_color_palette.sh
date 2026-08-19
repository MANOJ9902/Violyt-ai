#!/bin/bash
# Deploys the Brand Space -> Visual Identity "Brand Color Palette" table change:
#   - app/services/brand_visual_pack.py (additive: optional explicit "role" hint per
#     additional palette color, backward compatible with existing saved data)
#   - frontend: types/brand-space.types.ts, components/brandSpaces/tabs/FormFields.tsx,
#     components/brandSpaces/tabs/VisualIdentity.tsx, components/brandSpaces/BrandSpaceEditor.tsx,
#     lib/brand-mappers.ts
#
# Run this ON THE SERVER (not locally). It assumes ~/Violyt_Repo is a git checkout of this
# repo and ~/violyt-deploy is the docker-compose project directory (same layout as the other
# scripts/deploy_*.sh scripts in this repo).
#
# IMPORTANT: rotate any AWS console password / SSH key that was ever shared over chat or
# committed anywhere before running deploys with it.

set -e

echo "=== Pulling latest code ==="
cd ~/Violyt_Repo
git fetch origin
git pull --ff-only

echo "=== Patching backend containers (api & worker) ==="
for c in violyt-deploy-api-1 violyt-deploy-worker-1; do
  sudo docker cp app/services/brand_visual_pack.py "$c:/app/app/services/brand_visual_pack.py"
  echo "patched_$c"
done

cd ~/violyt-deploy
sudo docker compose restart api worker
sleep 8

echo "=== Backend smoke test (role hint + legacy fallback) ==="
sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
from app.services.brand_visual_pack import build_visual_pack

pack = build_visual_pack(
    brand_id="deploy-check",
    resolved_brand_context={
        "brand_name": "Deploy Check",
        "visual_identity": {
            "brand_color_palette": {
                "additional": [
                    {"name": "Deep Violet Ink", "hex": "#331958", "role": "Supporting Dark"},
                    {"name": "Soft Lilac", "hex": "#EEE1FA", "role": "Primary Tint"},
                ]
            }
        },
    },
)
assert pack.card == "#EEE1FA", pack.card
assert pack.body == "#331958", pack.body

legacy = build_visual_pack(
    brand_id="deploy-check-legacy",
    resolved_brand_context={
        "visual_identity": {
            "brand_color_palette": {"additional": [{"name": "Supporting Dark", "hex": "#331958"}]}
        }
    },
)
assert legacy.body == "#331958", legacy.body
print("brand_color_palette_role_hint_live=1")
PY

curl -s -o /dev/null -w 'api_health=%{http_code}\n' http://127.0.0.1:8000/health

echo "=== Rebuilding frontend image (Next.js needs a full build for TS/TSX changes) ==="
cd ~/Violyt_Repo/frontend
sudo docker build \
  --build-arg NEXT_PUBLIC_ENV=production \
  --build-arg NEXT_PUBLIC_API_BASE_URI=https://65.0.82.127 \
  --build-arg NEXT_PUBLIC_ENABLE_MOCK_UI=false \
  --build-arg NEXT_PUBLIC_MOCK_ROLE=TENANT_ADMIN \
  -t violyt-frontend:local .

cd ~/violyt-deploy
sudo docker compose up -d --no-deps frontend

echo "=== Deployment complete ==="
sudo docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'api-1|worker-1|frontend-1'
