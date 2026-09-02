"""Run Jiraaf static LinkedIn image; auto-approve blueprint; print image URL."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
BRAND_ID = "1eeb4475-24ca-41dd-8cad-80bb50e0ca74"
OUT = Path(r"C:\Users\Lenovo\ai10\Violyt-ai\storage")
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Create a single LinkedIn static post: Why bond markets matter for investors "
    "funding infrastructure. One clear insight headline, one short supporting line, "
    "premium educational tone. Short CTA Explore More."
)


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _extract_images(payload: dict) -> list[str]:
    urls: list[str] = []
    fo = payload.get("final_output") or {}
    vr = payload.get("visual_reasoning") or {}
    for key in ("image_urls", "asset_urls", "slide_urls", "generated_image_urls"):
        val = fo.get(key) or vr.get(key)
        if isinstance(val, list):
            urls.extend([u for u in val if isinstance(u, str) and u])
    for key in ("asset_url", "generated_image_url", "image_url"):
        val = fo.get(key) or vr.get(key)
        if isinstance(val, str) and val:
            urls.append(val)
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


async def main() -> int:
    timeout = httpx.Timeout(60.0, read=120.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        h = await client.get(f"{BASE}/health")
        print(f"health={h.status_code}", flush=True)
        body = {
            "brand_id": BRAND_ID,
            "user_prompt": PROMPT,
            "platform": "linkedin",
            "format": "static",
        }
        print(f"[{_now()}] START static", flush=True)
        resp = await client.post(f"{BASE}/api/v1/pipeline/run", json=body)
        resp.raise_for_status()
        run_id = resp.json()["run_id"]
        print(f"[{_now()}] run_id={run_id}", flush=True)
        (OUT / "_jiraaf_static_run_id.txt").write_text(run_id, encoding="utf-8")

        approved = False
        last: dict = {}
        for _ in range(200):
            await asyncio.sleep(8 if not approved else 10)
            try:
                st = await client.get(f"{BASE}/api/v1/pipeline/{run_id}/status")
                st.raise_for_status()
                last = st.json()
            except Exception as exc:  # noqa: BLE001
                print(f"[{_now()}] poll_error: {exc}", flush=True)
                continue

            status = last.get("status")
            prog = last.get("progress") or {}
            imgs = _extract_images(last)
            print(
                f"[{_now()}] status={status} imgs={len(imgs)} "
                f"{prog.get('event')}/{prog.get('layer')}/{prog.get('message')}",
                flush=True,
            )

            if status == "awaiting_blueprint_approval" and not approved:
                (OUT / "_jiraaf_static_phase1.json").write_text(
                    json.dumps(last, indent=2, default=str), encoding="utf-8"
                )
                bp = last.get("creative_blueprint") or {}
                print(
                    f"[{_now()}] blueprint headline={(bp.get('headline') or '')[:100]}",
                    flush=True,
                )
                apr = await client.post(
                    f"{BASE}/api/v1/pipeline/approve", json={"run_id": run_id}
                )
                print(f"[{_now()}] APPROVE -> {apr.status_code}", flush=True)
                approved = True
                continue

            if status in {"complete", "failed", "cancelled"}:
                (OUT / "_jiraaf_static_phase2.json").write_text(
                    json.dumps(last, indent=2, default=str), encoding="utf-8"
                )
                if imgs:
                    (OUT / "_jiraaf_static_image_urls.txt").write_text(
                        "\n".join(imgs), encoding="utf-8"
                    )
                print(
                    f"DONE status={status} images={len(imgs)} error={last.get('error')}",
                    flush=True,
                )
                for u in imgs:
                    print(f"  {u}", flush=True)
                return 0 if status == "complete" and imgs else 1

        print("TIMEOUT", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
