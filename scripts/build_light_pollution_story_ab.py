"""Local A/B of a flattened illustration and an unapproved layered reaction.

The same narration, background, timing and lighting are used in both cuts.
This is an authored experiment; it is not the automatic production renderer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "light-pollution-story-asset-v1"
ASSETS = EXPERIMENT / "assets"
VOICE = ROOT / "output" / "light-pollution-motion-20260924" / "audio" / "padded" / "scene-005.wav"
GSAP = ROOT / "video-generator" / "hyperframes-runtime" / "node_modules" / "gsap" / "dist" / "gsap.min.js"
CLI = ROOT / "video-generator" / "hyperframes-runtime" / "node_modules" / ".bin" / "hyperframes.cmd"


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path),
    ], text=True).strip())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page(variant: str, seconds: float) -> str:
    actor = (
        '<img class="full" src="assets/person-full.png" alt="">'
        if variant == "A" else
        '<div class="torso"><img src="assets/person-body.png" alt=""></div>'
        '<div class="head"><img class="neutral" src="assets/person-head-neutral.png" alt="">'
        '<img class="notice" src="assets/person-head-notice.png" alt=""></div>'
    )
    animation = (
        "tl.to('.person',{y:-2,duration:1.1,ease:'sine.inOut'},4.1);"
        if variant == "A" else
        "tl.to('.torso',{x:-5,y:-3,duration:.75,ease:'sine.inOut'},3.1);"
        "tl.to('.head',{x:-7,y:-6,rotation:-2,duration:.8,ease:'power2.out'},2.7);"
        "tl.to('.notice',{opacity:1,duration:.23,ease:'none'},3.35);"
        "tl.to('.head',{x:-4,y:-4,rotation:-1,duration:1.1,ease:'sine.out'},5.0);"
    )
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<script src="assets/gsap.min.js"></script><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#132a35}}
main{{position:relative;width:1920px;height:1080px;overflow:hidden;background:#142b36}}
svg{{position:absolute;inset:0;width:1920px;height:1080px}}
.person{{position:absolute;inset:0;filter:drop-shadow(16px 12px 10px rgba(4,12,20,.25))}}
.full{{position:absolute;left:1150px;top:235px;width:630px;height:840px}}
.torso{{position:absolute;left:1150px;top:235px;width:630px;height:840px}}
.torso img{{width:100%;height:100%}}
.head{{position:absolute;left:1280px;top:320px;width:420px;height:431px;transform-origin:65% 80%}}
.head img{{position:absolute;inset:0;width:100%;height:100%}}
.notice{{opacity:0}}
.light{{opacity:.12;transform-origin:460px 370px}}
.stars{{opacity:.35}}
</style></head><body><main data-composition-id="story-{variant.lower()}" data-width="1920" data-height="1080" data-start="0" data-duration="{seconds:.6f}" data-fps="30">
<svg viewBox="0 0 1920 1080" aria-hidden="true">
<defs><linearGradient id="beam" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f6c478" stop-opacity=".38"/><stop offset="1" stop-color="#f6c478" stop-opacity="0"/></linearGradient></defs>
<path d="M0 840H1920V1080H0Z" fill="#1a313a"/><path d="M0 850H1920" stroke="#597a79" stroke-width="4"/>
<g class="stars" fill="#d7d8c3"><circle cx="230" cy="244" r="3"/><circle cx="520" cy="290" r="2"/><circle cx="610" cy="193" r="3"/></g>
<rect x="165" y="110" width="600" height="570" rx="12" fill="#203a48" stroke="#a1c4c1" stroke-width="12"/>
<path d="M465 110V680 M165 395H765" stroke="#9db9b6" stroke-width="11"/>
<path class="light" d="M540 175 L1040 875 L680 900 L185 450Z" fill="url(#beam)"/>
<path d="M748 705H1870V870H748Z" fill="#315366"/><path d="M785 735H1820" stroke="#749291" stroke-width="7"/>
<path d="M0 1020 Q500 982 880 1020" stroke="#365c65" fill="none" stroke-width="16"/>
</svg><div class="person">{actor}</div></main>
<script>window.__timelines={{}};const tl=gsap.timeline({{paused:true}});
tl.to('.light',{{opacity:.68,duration:1.2,ease:'sine.inOut'}},.8);
{animation}
tl.set({{}},{{}},{seconds:.3f});window.__timelines['story-{variant.lower()}']=tl;</script></body></html>'''


def build() -> None:
    if not VOICE.is_file() or not GSAP.is_file():
        raise FileNotFoundError("Local narration or pinned GSAP runtime is missing")
    seconds = duration(VOICE)
    for name in ("person-full.png", "person-body.png", "person-head-neutral.png", "person-head-notice.png"):
        if not (ASSETS / name).is_file():
            raise FileNotFoundError(ASSETS / name)
    for variant in ("A", "B"):
        project = EXPERIMENT / variant / "project"
        target_assets = project / "assets"
        target_assets.mkdir(parents=True, exist_ok=True)
        shutil.copy2(GSAP, target_assets / "gsap.min.js")
        for asset in ASSETS.glob("*.png"):
            shutil.copy2(asset, target_assets / asset.name)
        (project / "index.html").write_text(page(variant, seconds), encoding="utf-8")
        (project / "meta.json").write_text(json.dumps({
            "name": f"story-{variant.lower()}", "duration": seconds,
            "resolution": {"width": 1920, "height": 1080}, "fps": 30,
        }), encoding="utf-8")
    (EXPERIMENT / "experiment.json").write_text(json.dumps({
        "status": "TECHNICAL_EXPERIMENT_HUMAN_REVIEW_REQUIRED",
        "scene": "scene-005", "narration_sha256": sha256(VOICE),
        "duration_seconds": seconds, "paid_api_calls": 0,
        "A": "flattened generated character; nearly static",
        "B": "generated torso, head and expression states; localized reaction",
        "asset_sha256": {asset.name: sha256(asset) for asset in ASSETS.glob("*.png")},
        "claim_limit": "This tests recognition acting only, not curtain closure or a full story arc.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def render(only_variant: str | None = None) -> None:
    if not CLI.is_file():
        raise FileNotFoundError(CLI)
    for variant in ((only_variant,) if only_variant else ("A", "B")):
        root = EXPERIMENT / variant
        temp = root / "temp"
        temp.mkdir(exist_ok=True)
        env = dict(__import__("os").environ, TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
        silent = root / "silent.mp4"
        subprocess.run([str(CLI), "render", f"--output={silent}", "--quality=looks",
                        "--workers=2", "--low-memory-mode", "--strict", str(root / "project")],
                       cwd=CLI.parent.parent.parent, env=env, check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(VOICE),
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(root / "comparison.mp4")],
                       check=True)
        print(root / "comparison.mp4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["build", "render"])
    parser.add_argument("--variant", choices=["A", "B"])
    args = parser.parse_args()
    build() if args.step == "build" else render(args.variant)
