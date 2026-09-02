"""Run Cognixia LinkedIn carousel; auto-approve blueprint; print slide URLs."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

BASE = "https://65.0.82.127"
BRAND_ID = "457ec5dd-a0e8-4e9a-9dec-29aa6d41eda9"
OUT = Path(r"C:\Users\Lenovo\ai10\Violyt-ai\storage")
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Create a data-led Cognixia LinkedIn carousel on this AI workforce trend. "
    "Do not recap the news — extract the business implication for CHROs, CDOs, and CTOs. "
    "Source: Accenture Pulse of Change, July 2026 (3,000 C-suite and 3,000 employees across 20 countries). "
    "Use these exact facts, written as complete sentences with no ellipses or truncated headlines: "
    "82% of C-suite leaders are increasing AI investment; "
    "only 23% report widespread sustained business value from AI, down from 32% earlier in 2026; "
    "the largest AI skills gap is in middle management (36% of both leaders and employees); "
    "78% of leaders expect employee roles to change in the next 12 months; "
    "61% of employees now turn to AI before a colleague. "
    "Business implication: AI ROI is stalling because companies bought tools faster than they built "
    "the managers who can redesign work. The bottleneck is not the model — it is middle-manager "
    "capability to redesign workflows, coach hybrid human-AI teams, and turn experiments into an operating model. "
    "Cognixia angle: upskill managers as AI workflow architects, not generic tool training. "
    "5 to 6 slides. Each slide must teach a DIFFERENT insight. "
    "Cover slide gets one hero stat. Do not repeat the same three percentages on every slide. "
    "Short CTA Explore More on the last slide."
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
    async with httpx.AsyncClient(timeout=timeout, verify=False, follow_redirects=True) as client:
        h = await client.get(f"{BASE}/health")
        print(f"health={h.status_code}", flush=True)
        body = {
            "brand_id": BRAND_ID,
            "user_prompt": PROMPT,
            "platform": "linkedin",
            "format": "carousel",
        }
        print(f"[{_now()}] START carousel", flush=True)
        print(f"prompt={PROMPT[:90]}...", flush=True)
        resp = await client.post(f"{BASE}/api/v1/pipeline/run", json=body)
        resp.raise_for_status()
        run_id = resp.json()["run_id"]
        print(f"[{_now()}] run_id={run_id}", flush=True)
        (OUT / "_cognixia_carousel_run_id.txt").write_text(run_id, encoding="utf-8")

        approved = False
        last: dict = {}
        for _ in range(360):
            await asyncio.sleep(8 if not approved else 12)
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
                (OUT / "_cognixia_carousel_phase1.json").write_text(
                    json.dumps(last, indent=2, default=str), encoding="utf-8"
                )
                bp = last.get("creative_blueprint") or {}
                copy = last.get("copy") or {}
                print(
                    f"[{_now()}] blueprint headline={(bp.get('headline') or '')[:120]}",
                    flush=True,
                )
                slides = list(copy.get("slide_copy") or bp.get("slide_copy") or [])
                for slide in slides:
                    print(
                        f"  s{slide.get('slide_number')}: {(slide.get('headline') or '')[:90]}",
                        flush=True,
                    )
                joined = " ".join(
                    f"{s.get('headline') or ''} {s.get('body') or ''}" for s in slides
                )
                bad = (
                    "…" in joined
                    or "..." in joined
                    or "2024" in joined
                    or any(len((s.get("headline") or "").rstrip(".")) < 12 for s in slides)
                )
                if bad:
                    print(f"[{_now()}] REJECT copy quality (truncated/stale). Not approving.", flush=True)
                    return 2
                apr = await client.post(
                    f"{BASE}/api/v1/pipeline/approve", json={"run_id": run_id}
                )
                print(f"[{_now()}] APPROVE -> {apr.status_code}", flush=True)
                approved = True
                continue

            if status in {"complete", "failed", "cancelled"}:
                (OUT / "_cognixia_carousel_phase2.json").write_text(
                    json.dumps(last, indent=2, default=str), encoding="utf-8"
                )
                if imgs:
                    (OUT / "_cognixia_carousel_image_urls.txt").write_text(
                        "\n".join(imgs), encoding="utf-8"
                    )
                print(
                    f"DONE status={status} images={len(imgs)} error={last.get('error')}",
                    flush=True,
                )
                for i, u in enumerate(imgs, 1):
                    print(f"  slide{i}: {u}", flush=True)
                return 0 if status == "complete" and imgs else 1

        print("TIMEOUT", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
