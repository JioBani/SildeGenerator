"""Render an authored, provider-free diagram sample for frame inspection."""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "video-generator"), str(ROOT / "harnesses/hybrid-story/src")]

from app.harness_sdk.hybrid import HybridScene
from hybrid_story.hybrid_renderer import compile_project
from semantic_diagram_fixtures import cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    design = json.loads((ROOT / "experiments/meaning-planning-v1/film-design-candidate.json").read_text(encoding="utf-8"))
    scenes = []
    for case in cases()[:2]:
        hybrid = case["hybrid"]
        hybrid.update(version="hybrid-scene-0.6", design=design)
        for index, node in enumerate(hybrid["diagram"]["nodes"]):
            node["color"] = design["palette"]["accents"][index % len(design["palette"]["accents"])]
        HybridScene.model_validate(hybrid)
        scenes.append(SimpleNamespace(id=case["id"], layout={"hybrid": hybrid}, duration_seconds=5))
    args.output.mkdir(parents=True, exist_ok=True)
    compile_project(scenes, args.output, SimpleNamespace(width=1280, height=720, fps=24))
    print(args.output / "index.html")


if __name__ == "__main__":
    main()
