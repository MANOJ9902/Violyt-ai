#!/bin/bash
# Raw recent activity with timestamps, so we can see where a run stops.
echo "=== now (UTC) ==="; date -u '+%Y-%m-%d %H:%M:%S'
echo "=== container start times ==="
sudo docker inspect -f '{{.Name}} started={{.State.StartedAt}}' \
  violyt-deploy-api-1 violyt-deploy-worker-1

echo
echo "=== api: last 70 log lines, raw ==="
sudo docker logs violyt-deploy-api-1 --since 30m 2>&1 | grep -v 'allowed_objects' | tail -70

echo
echo "=== worker: last 40 log lines, raw ==="
sudo docker logs violyt-deploy-worker-1 --since 30m 2>&1 | grep -v 'allowed_objects' | tail -40
