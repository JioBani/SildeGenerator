"""Re-render the preserved mixed-route fixture with only cinematic camera changes."""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "video-generator"), str(ROOT / "harnesses/hybrid-story/src")]

from app.source_media import prepare_source
from app.tracking import sha256_file
from hybrid_story.hybrid_renderer import compile_project


def run(command, **kwargs):
    subprocess.run(command, check=True, timeout=1800, **kwargs)


def main():
    source = ROOT / "output/hybrid-story-smoke-v3"
    old_project = source / "work/render-segments/segment-project-d59b86b2"
    target = ROOT / "output/hybrid-story-0.18.0-camera-ab"
    if target.exists():
        raise FileExistsError(target)
    target.mkdir(parents=True)
    project = target / "project"
    records = json.loads((old_project / "program.json").read_text(encoding="utf-8"))
    source_record = prepare_source(ROOT / "experiments/hybrid-story-v1/source-media",
        "antarctic-sea-ice-2016", target / "registered-source.png", size=(1280, 720))
    scenes = []
    asset_hashes = {}
    for index, record in enumerate(records):
        layout = {"hybrid": {key: record[key] for key in
                             ("version", "route", "reason", "diagram", "source_id")}}
        image_path = None
        if record["route"] == "cinematic":
            image_path = old_project / "assets" / f"shot-{index}.png"
            layout["camera"] = {"mode": "push" if index == 0 else "pull",
                                "focus": [.4, .5] if index == 0 else [.55, .5],
                                "strength": .045}
            asset_hashes[record["scene_id"]] = sha256_file(image_path)
        elif record["route"] == "source":
            image_path = Path(source_record["image_path"])
            layout["hybrid_source"] = source_record
            layout["camera"] = {"mode": "hold"}
            asset_hashes[record["scene_id"]] = sha256_file(image_path)
        else:
            layout["camera"] = {"mode": "hold"}
        scenes.append(SimpleNamespace(id=record["scene_id"],
            duration_seconds=record["duration"], layout=layout,
            image_path=str(image_path) if image_path else None))
    compile_project(scenes, project, SimpleNamespace(width=1280, height=720, fps=24))
    visual = target / "visual.mp4"
    run(["/app/hyperframes-runtime/node_modules/.bin/hyperframes", "render",
         f"--output={visual}", "--quality=looks", "--workers=1",
         "--low-memory-mode", "--strict", str(project)],
        cwd="/app/hyperframes-runtime")
    captioned = target / "captioned.mp4"
    captions = source / "work/captions.ass"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(visual),
         "-vf", f"subtitles=filename='{captions}'", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", "-preset", "medium", "-an", str(captioned)])
    output = target / "candidate.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(captioned),
         "-i", str(source / "work/narration.m4a"), "-map", "0:v:0", "-map", "1:a:0",
         "-c", "copy", "-shortest", "-movflags", "+faststart", str(output)])
    report = {"status": "TECHNICAL_AB_UNREVIEWED", "goal_status": "GOAL_NOT_MET",
              "baseline": str(source / "delivery/hybrid.mp4"),
              "candidate": str(output), "candidate_sha256": sha256_file(output),
              "scene_asset_hashes": asset_hashes,
              "registered_source": {key: source_record[key] for key in
                  ("id", "source_url", "rights_url", "usage_basis", "sha256", "prepared_sha256")},
              "voice_sha256": sha256_file(source / "work/narration.m4a"),
              "captions_sha256": sha256_file(captions),
              "new_paid_calls": 0, "human_approval": None,
              "scope": "Preserved authored film, same narration and stills; only cinematic camera curve changes. Not unseen-script transfer."}
    (target / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
