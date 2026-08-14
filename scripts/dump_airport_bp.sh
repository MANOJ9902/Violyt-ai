#!/bin/bash
sudo docker exec -i violyt-deploy-api-1 python - <<'PY'
import json, glob, os, re
files = sorted(glob.glob("/app/storage/pipeline_checkpoints/*.json"), key=os.path.getmtime, reverse=True)[:12]
for path in files:
    data = json.load(open(path))
    raw = json.dumps(data)
    if "98000" in raw or "98,000" in raw or "Everything you need" in raw or "Greenfield" in raw:
        print("===", path, "===")
        def find(obj, depth=0):
            if depth > 8: return None
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
            print(f"sec[{i}] label={s.get('section_label')!r} stat={s.get('stat')!r}")
            print(f"         body={s.get('body')!r}")
            print(f"         includes={s.get('includes')}")
        # also show copy if present
        print()
PY
