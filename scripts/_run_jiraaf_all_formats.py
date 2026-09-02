"""Run Jiraaf pipeline for carousel, infographic, and static; auto-approve; collect image URLs."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
BRAND_ID = "1eeb4475-24ca-41dd-8cad-80bb50e0ca74"
OUT_DIR = Path(r"C:\Users\Lenovo\ai10\Violyt-ai\storage")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPTS = {
    "carousel": (
        "Create a LinkedIn carousel explaining why bond markets connect investors to financing. "
        "Cover how governments issue bonds, how deep markets allocate capital, and why Eurozone "
        "infrastructure needs bond funding beyond capital cities. Each slide must teach a DIFFERENT "
        "insight. Insight-led for Indian LinkedIn investors."
    ),
    "infographic": (
        "Create a clean LinkedIn infographic: Why bond markets connect investors to real-economy financing. "
        "Use 2 key stats and 2 short distinct supporting insights. No filler phrases. Short CTA Explore More."
    ),
    "static": (
        "Create a single LinkedIn static post: Why bond markets matter for investors funding infrastructure. "
        "One clear insight headline, one short supporting line, premium educational tone. Short CTA Explore More."
    ),
}


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
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


async def run_one(client: httpx.AsyncClient, fmt: str) -> dict:
    body = {
        "brand_id": BRAND_ID,
        "user_prompt": PROMPTS[fmt],
        "platform": "linkedin",
        "format": fmt,
    }
    print(f"[{_now()}] START {fmt}", flush=True)
    resp = await client.post(f"{BASE}/api/v1/pipeline/run", json=body)
    resp.raise_for_status()
    run_id = resp.json()["run_id"]
    print(f"[{_now()}] {fmt} run_id={run_id}", flush=True)
    (OUT_DIR / f"_jiraaf_{fmt}_run_id.txt").write_text(run_id, encoding="utf-8")

    approved = False
    last: dict = {}
    for i in range(200):
        await asyncio.sleep(8 if not approved else 10)
        try:
            st = await client.get(f"{BASE}/api/v1/pipeline/{run_id}/status")
            st.raise_for_status()
            last = st.json()
        except Exception as exc:  # noqa: BLE001
            print(f"[{_now()}] {fmt} poll_error: {exc}", flush=True)
            continue

        status = last.get("status")
        prog = last.get("progress") or {}
        imgs = _extract_images(last)
        print(
            f"[{_now()}] {fmt} status={status} imgs={len(imgs)} "
            f"{prog.get('event')}/{prog.get('layer')}/{prog.get('message')}",
            flush=True,
        )

        if status == "awaiting_blueprint_approval" and not approved:
            bp = last.get("creative_blueprint") or {}
            (OUT_DIR / f"_jiraaf_{fmt}_phase1.json").write_text(
                json.dumps(last, indent=2, default=str), encoding="utf-8"
            )
            slides = bp.get("slides") or []
            sections = bp.get("sections") or []
            print(f"[{_now()}] {fmt} blueprint slides={len(slides)} sections={len(sections)}", flush=True)
            if slides:
                for idx, s in enumerate(slides[:8], 1):
                    hl = (s.get("headline") or s.get("title") or "")[:80]
                    print(f"  slide{idx}: {hl}", flush=True)
            if sections:
                for sec in sections[:6]:
                    print(f"  [{sec.get('section_label')}] {(sec.get('body') or '')[:90]}", flush=True)
            apr = await client.post(f"{BASE}/api/v1/pipeline/approve", json={"run_id": run_id})
            print(f"[{_now()}] {fmt} APPROVE -> {apr.status_code}", flush=True)
            approved = True
            continue

        if status in {"complete", "failed", "cancelled"}:
            (OUT_DIR / f"_jiraaf_{fmt}_phase2.json").write_text(
                json.dumps(last, indent=2, default=str), encoding="utf-8"
            )
            if imgs:
                (OUT_DIR / f"_jiraaf_{fmt}_image_urls.txt").write_text(
                    "\n".join(imgs), encoding="utf-8"
                )
            return {
                "format": fmt,
                "run_id": run_id,
                "status": status,
                "error": last.get("error"),
                "images": imgs,
                "format_reported": (last.get("creative_blueprint") or {}).get("format")
                or last.get("format"),
            }

    (OUT_DIR / f"_jiraaf_{fmt}_phase2.json").write_text(
        json.dumps(last, indent=2, default=str), encoding="utf-8"
    )
    return {
        "format": fmt,
        "run_id": run_id,
        "status": "timeout",
        "error": "timed out waiting for pipeline",
        "images": _extract_images(last),
    }


async def main() -> int:
    timeout = httpx.Timeout(60.0, read=120.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # health
        h = await client.get(f"{BASE}/health")
        print(f"health={h.status_code}", flush=True)
        # run all three in parallel
        results = await asyncio.gather(
            *(run_one(client, fmt) for fmt in ("carousel", "infographic", "static")),
            return_exceptions=True,
        )

    summary = []
    for r in results:
        if isinstance(r, Exception):
            summary.append({"error": str(r)})
        else:
            summary.append(r)
            print(
                f"DONE {r.get('format')} status={r.get('status')} images={len(r.get('images') or [])}",
                flush=True,
            )
            for u in r.get("images") or []:
                print(f"  {u}", flush=True)

    out_path = OUT_DIR / "_jiraaf_all_formats_summary.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"SUMMARY -> {out_path}", flush=True)
    ok = all(isinstance(r, dict) and r.get("status") == "complete" and r.get("images") for r in summary)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
