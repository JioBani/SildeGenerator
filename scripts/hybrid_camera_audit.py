"""Inspect the rendered camera A/B film without granting narrative approval."""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video-generator"))

from app.rendered_review import inspect_render


def main():
    output = ROOT / "output/hybrid-story-0.18.0-camera-ab"
    candidate = output / "candidate.mp4"
    program = json.loads((output / "project/program.json").read_text(encoding="utf-8"))
    scenes = []
    for index, item in enumerate(program, 1):
        scene = SimpleNamespace(id=item["scene_id"], duration_seconds=item["duration"],
            narration="", layout={"hybrid": {"route": item["route"],
                "diagram": item["diagram"]},
                "direction": {"repeat_of_scene_number": 1} if index == 4 else {}})
        scenes.append(scene)
    report = inspect_render(candidate, scenes, width=1280, height=720, fps=24)
    report["camera_windows"] = [{"scene_id": item["scene_id"],
        "camera_window": item["camera_window"]} for item in program]
    report["scope"] = "Decoded technical observations of preserved authored fixture; not narrative, emotion, source-meaning or held-out quality approval"
    moments = [3, 11, 20, 29]
    sheet = Image.new("RGB", (1280, 4 * 760), "white")
    draw = ImageDraw.Draw(sheet)
    for index, second in enumerate(moments):
        frame = output / f"frame-{second:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(second),
            "-i", str(candidate), "-frames:v", "1", str(frame)], check=True, timeout=60)
        with Image.open(frame) as image:
            sheet.paste(image.convert("RGB"), (0, index * 760 + 40))
        draw.text((24, index * 760 + 12), f"scene-{index+1}: {second}s", fill="black")
    sheet.save(output / "contact-sheet.png")
    (output / "observations.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(json.dumps({"status": report["status"], "findings": report["findings"],
                      "duration": report["duration_seconds"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
