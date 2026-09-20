from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video-generator"))
os.environ.setdefault("HARNESSES_DIR", str(ROOT / "harnesses"))
from app.engine.harness_loader import HarnessRegistry  # noqa: E402

registry = HarnessRegistry(ROOT / "harnesses")


def main() -> int:
    parser = argparse.ArgumentParser(description="Slide Generator Creative Harness CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    for command in ("inspect", "validate", "hash", "test", "dev"):
        item = sub.add_parser(command); item.add_argument("id")
    clone = sub.add_parser("clone"); clone.add_argument("source"); clone.add_argument("target")
    args = parser.parse_args()
    if args.command == "list":
        for item in registry.list(): print(f"{item['id']}\t{item.get('version','-')}\t{'compatible' if item.get('compatible') else 'invalid'}")
        return 0
    if args.command == "clone":
        source = registry.load(args.source); target = ROOT / "harnesses" / args.target
        if target.exists(): raise SystemExit(f"target exists: {args.target}")
        if not args.target.replace("-", "").isalnum(): raise SystemExit("target id must use lowercase letters, numbers, and hyphens")
        shutil.copytree(source.root, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.mp4", "*.mp3", "*.png"))
        manifest_path = target / "harness.yaml"; manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifest.update({"id": args.target, "version": "0.1.0", "display_name": f"실험: {args.target}"}); manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(target.relative_to(ROOT)); return 0
    loaded = registry.load(args.id)
    if args.command == "inspect": print(json.dumps({"manifest": loaded.manifest.__dict__, "snapshot": loaded.snapshot.as_dict(), "config": loaded.config}, ensure_ascii=False, indent=2))
    elif args.command == "hash": print(json.dumps(loaded.snapshot.as_dict(), ensure_ascii=False, indent=2))
    elif args.command == "validate": print(f"PASS {loaded.manifest.id}@{loaded.manifest.version} {loaded.snapshot.source_sha256}")
    elif args.command == "test":
        child_env = os.environ.copy()
        python_path = str(ROOT / "video-generator")
        child_env["PYTHONPATH"] = os.pathsep.join(filter(None, (python_path, child_env.get("PYTHONPATH"))))
        return subprocess.call(
            [sys.executable, "-m", "pytest", "-q", str(ROOT / "video-generator" / "tests" / "test_harness_sdk.py")],
            cwd=ROOT,
            env=child_env,
        )
    elif args.command == "dev": print(f"Validated {loaded.manifest.id}@{loaded.manifest.version}. Restart runner before the next job to load code changes.")
    return 0


if __name__ == "__main__": raise SystemExit(main())
