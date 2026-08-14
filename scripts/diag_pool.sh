#!/bin/bash
# Surface the call path that exhausts the SQLAlchemy connection pool.
echo "=== QueuePool traceback (app frames only) ==="
sudo docker logs violyt-deploy-api-1 --since 60m 2>&1 \
  | grep -B 60 'QueuePool limit' \
  | grep -E '/app/app/|QueuePool limit' \
  | tail -40

echo
echo "=== how many times it happened ==="
sudo docker logs violyt-deploy-api-1 --since 60m 2>&1 | grep -c 'QueuePool limit'

echo
echo "=== slowest layers this hour ==="
sudo docker logs violyt-deploy-api-1 --since 60m 2>&1 \
  | grep -oE '"l[0-9a-z_]+":[0-9]+' | sort -t: -k2 -n -r | head -12

echo
echo "=== image size / crop signals ==="
sudo docker logs violyt-deploy-api-1 --since 60m 2>&1 \
  | grep -oE 'dalle\.(resized_to_export|corner_wiped|save_complete|black_bg_rekeyed)[^|]{0,80}' | tail -15
