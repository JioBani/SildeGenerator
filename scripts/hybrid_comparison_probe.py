"""Render three authored comparison layouts for private visual review."""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "video-generator"), str(ROOT / "video-generator/tests"),
                str(ROOT / "harnesses/hybrid-story/src")]

from app.harness_sdk.hybrid import HybridScene
from app.tracking import sha256_file
from hybrid_story.hybrid_renderer import compile_project
from semantic_diagram_fixtures import cases


def main(output):
    output.mkdir(parents=True, exist_ok=True)
    palette = {"background": "#18201f", "text": "#f2f0e5", "secondary_text": "#e0ded2",
               "surface": "#333e3b", "line": "#d49a55", "accents": ["#d49a55", "#6bc3c0", "#ef8f8b"]}
    frames = []
    records = []
    for layout, treatment in (("rows", "explainer"), ("columns", "editorial"),
                              ("dot_tracks", "documentary")):
        payload = cases()[0]["hybrid"]
        payload["version"] = "hybrid-scene-0.6"
        payload["diagram"]["snapshot_pair"] = None
        payload["diagram"]["spatial_map"] = None
        for i, node in enumerate(payload["diagram"]["nodes"]):
            node["color"] = palette["accents"][i]
        payload["design"] = {"version": "film-design-0.3", "concept_id": "comparison_probe",
            "central_idea": "Compare three quoted travel times on one common scale.",
            "cinematic_language": "No cinematic beat is used in this authored probe.",
            "diagram_language": "The same source values use three executable chart geometries.",
            "source_treatment": "No source media is used in this authored probe.",
            "palette": palette,
            "typography": {"font": "Noto Sans CJK KR", "title_px": 34,
                           "caption_px": 36, "caption_margin_y": 48},
            "line_width": 3, "snapshot_layout": "columns",
            "comparison_layout": layout, "type_treatment": treatment}
        HybridScene.model_validate(payload)
        scene = SimpleNamespace(id=layout, layout={"hybrid": payload}, duration_seconds=10)
        project = output / layout
        compile_project([scene], project, SimpleNamespace(width=1280, height=720, fps=24))
        subprocess.run(["/app/hyperframes-runtime/node_modules/.bin/hyperframes", "snapshot",
                        str(project), "--at=9", "--no-end", "--describe=false"],
                       check=True, capture_output=True, timeout=90)
        frame = next((project / "snapshots").glob("frame-*.png"))
        records.append({"layout": layout, "type_treatment": treatment,
                        "frame": str(frame), "sha256": sha256_file(frame)})
        with Image.open(frame) as image:
            frames.append(image.convert("RGB"))
    board = Image.new("RGB", (1280, 3 * 760), "#ffffff")
    draw = ImageDraw.Draw(board)
    for i, (record, frame) in enumerate(zip(records, frames)):
        y = 760 * i
        draw.text((24, y + 12), f"{record['layout']} / {record['type_treatment']}", fill="#18201f")
        board.paste(frame, (0, y + 40))
    board.save(output / "comparison-board.png")
    (output / "report.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output / "comparison-board.png")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
