#!/usr/bin/env python3
"""Copy listed host files into api/worker containers under /app/."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Violyt_Repo"
LIST = ROOT / "_deploy_app_files.txt"
CONTAINERS = ("violyt-deploy-api-1", "violyt-deploy-worker-1")


def main() -> int:
    text = LIST.read_text(encoding="utf-8").replace("\r", "")
    files = [line.strip() for line in text.splitlines() if line.strip()]
    ok = miss = 0
    for rel in files:
        src = ROOT / rel
        if not src.is_file():
            print(f"MISSING {rel!r}")
            miss += 1
            continue
        for container in CONTAINERS:
            if rel == "main.py":
                dest = f"{container}:/app/main.py"
            else:
                rel_path = Path(rel)
                parent = rel_path.parent.as_posix()
                if parent and parent != ".":
                    subprocess.check_call(
                        ["sudo", "docker", "exec", container, "mkdir", "-p", f"/app/{parent}"]
                    )
                dest = f"{container}:/app/{rel}"
            subprocess.check_call(["sudo", "docker", "cp", str(src), dest])
        print(f"patched {rel}")
        ok += 1
    print(f"patched_ok={ok} missing={miss}")
    return 0 if miss == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
