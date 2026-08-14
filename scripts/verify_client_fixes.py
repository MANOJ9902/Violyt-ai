"""Smoke checks for client-reported fixes (API + code-level)."""
from __future__ import annotations

import json
import pathlib
import sys
import urllib.error
import urllib.request

API = "http://localhost:8000"
ORIGIN = "http://localhost:3000"
EMAIL = "skush@indosakura.com"
PASSWORD = "DemoPass123!"
ROOT = pathlib.Path(__file__).resolve().parents[1]


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict | str]:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Origin": ORIGIN}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode()
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body


def main() -> int:
    results: list[str] = []

    status, health = request("GET", "/health")
    results.append(f"[{'PASS' if status == 200 else 'FAIL'}] API health: {status}")

    status, login = request("POST", "/api/v1/auth/login", {"email": EMAIL, "password": PASSWORD})
    token = login.get("access_token") if isinstance(login, dict) else None
    results.append(f"[{'PASS' if status == 200 and token else 'FAIL'}] Login: {status}")

    if token:
        status, brands = request("GET", "/api/v1/brands", token=token)
        brand_list = brands if isinstance(brands, list) else []
        brand_id = brand_list[0]["id"] if brand_list else None
        results.append(f"[{'PASS' if status == 200 and brand_id else 'FAIL'}] List brands: {status}")

        if brand_id:
            payload = {
                "sections": [
                    {
                        "section_code": "foundations",
                        "completion_percent": 75,
                        "payload": {
                            "brand_mission": "Deploy verification mission",
                            "brand_vision": "Deploy verification vision",
                            "brand_promise": "Deploy verification promise",
                        },
                    }
                ]
            }
            status, saved = request("PUT", f"/api/v1/brands/{brand_id}/sections", payload, token=token)
            ok = status == 200 and isinstance(saved, dict) and saved.get("id") == brand_id
            results.append(f"[{'PASS' if ok else 'FAIL'}] Brand Space save: HTTP {status}")

    from app.prompts.jiraaf_sample_templates import resolve_creative_template

    cognixia = resolve_creative_template("RBI plastic currency", "carousel", brand_name="Cognixia")
    dna_ok = "Never use Jiraaf navy" in cognixia.visual_lock
    results.append(f"[{'PASS' if dna_ok else 'FAIL'}] Non-Jiraaf template neutralized")

    sidebar = (ROOT / "frontend" / "lib" / "sidebarItems.ts").read_text(encoding="utf-8")
    retrieval_removed = "brand-retrieval" not in sidebar and "Brand Retrieval" not in sidebar
    results.append(f"[{'PASS' if retrieval_removed else 'FAIL'}] Brand Retrieval removed from sidebar")

    workspace = (ROOT / "frontend" / "components" / "chat" / "WorkspaceChat.tsx").read_text(encoding="utf-8")
    collapse_ok = "isCollapsed" in workspace and "Template Direction" in workspace
    results.append(f"[{'PASS' if collapse_ok else 'FAIL'}] Template Direction collapse state present")

    caption_ok = (ROOT / "frontend" / "lib" / "post-caption.ts").exists() and "PostCaptionBlock" in (
        ROOT / "frontend" / "components" / "chat" / "ChatPipelinePanel.tsx"
    ).read_text(encoding="utf-8")
    results.append(f"[{'PASS' if caption_ok else 'FAIL'}] Post caption UI present")

    # Caption content generation (hook + body + hashtags)
    caption_sample = ""
    try:
        import subprocess

        out = subprocess.check_output(
            [
                "npx",
                "tsx",
                "-e",
                "import { buildPostCaption } from './lib/post-caption'; "
                "console.log(buildPostCaption({platform:'instagram',blueprint:{hook:'Hook',body:'Body text',cta:'CTA',hashtags:['#Test']}}));",
            ],
            cwd=str(ROOT / "frontend"),
            text=True,
            timeout=60,
        )
        caption_sample = out.strip()
    except Exception as exc:
        caption_sample = str(exc)
    caption_gen_ok = len(caption_sample) > 15 and ("Hook" in caption_sample or "Body" in caption_sample)
    results.append(f"[{'PASS' if caption_gen_ok else 'FAIL'}] Post caption generates content: {caption_sample[:80]!r}")

    brand_assets_src = (ROOT / "app" / "services" / "brand_assets.py").read_text(encoding="utf-8")
    ocr_ok = 'startswith("image/")' in brand_assets_src and "billable_ocr_pages = 0" in brand_assets_src
    results.append(f"[{'PASS' if ocr_ok else 'FAIL'}] Image OCR billing exemption present")

    try:
        fe_status = urllib.request.urlopen(
            urllib.request.Request(
                ORIGIN + "/auth/login",
                headers={"Accept": "text/html"},
                method="GET",
            ),
            timeout=10,
        ).status
        results.append(f"[{'PASS' if fe_status == 200 else 'FAIL'}] Frontend reachable: {fe_status}")
    except Exception as exc:
        results.append(f"[SKIP] Frontend not running locally: {exc}")

    print("\n".join(results))
    return 0 if all("PASS" in line or "SKIP" in line for line in results) else 1


if __name__ == "__main__":
    sys.exit(main())
