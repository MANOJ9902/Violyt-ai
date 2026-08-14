#!/bin/bash
# Dump the latest blueprint copy so we can see what garbage reached the image.
LATEST=$(sudo docker exec violyt-deploy-api-1 sh -c 'ls -t /app/storage/pipeline_checkpoints/*.json | head -1')
echo "checkpoint=$LATEST"
sudo docker exec -i violyt-deploy-api-1 python - <<PY
import json, glob, os
files = sorted(glob.glob("/app/storage/pipeline_checkpoints/*.json"), key=os.path.getmtime, reverse=True)
path = files[0]
print("using", path)
data = json.load(open(path))
# try common keys
bp = data.get("creative_blueprint") or data.get("blueprint") or {}
if not bp:
    # nested state
    for k in ("state", "phase1", "result", "payload"):
        if isinstance(data.get(k), dict):
            bp = data[k].get("creative_blueprint") or data[k].get("blueprint") or {}
            if bp: break
if not bp:
    # print top keys
    print("top_keys", list(data.keys())[:40])
    # search recursively for headline
    def find(obj, depth=0):
        if depth > 6: return None
        if isinstance(obj, dict):
            if "headline" in obj and ("sections" in obj or "stat_highlights" in obj):
                return obj
            for v in obj.values():
                r = find(v, depth+1)
                if r: return r
        elif isinstance(obj, list):
            for v in obj:
                r = find(v, depth+1)
                if r: return r
        return None
    bp = find(data) or {}
print("headline:", bp.get("headline"))
print("supporting:", bp.get("supporting_line"))
print("stats:", bp.get("stat_highlights"))
print("cta:", bp.get("cta"))
print("quote:", bp.get("customer_quote"))
print("source:", bp.get("source_footer"))
for i, s in enumerate(bp.get("sections") or []):
    print(f"sec[{i}] label={s.get('section_label')!r} stat={s.get('stat')!r} body={s.get('body')!r} includes={s.get('includes')}")
PY
