from __future__ import annotations

import hashlib
from pathlib import Path


PROMPT_FILES = (
    "director/system.md",
    "narrative/story-intent.md",
    "narrative/analyze-sequences.md",
    "narrative/analyze-scene-groups.md",
    "narrative/analyze-scenes.md",
    "keycut/select-keycuts.md",
    "keycut/reference-contract.md",
    "style/common.md",
    "style/presets/editorial-illustration.md",
    "style/presets/cinematic-realism.md",
    "style/presets/graphic-explainer.md",
    "continuity/select-assets.md",
    "continuity/assign-scene-references.md",
    "continuity/disabled.md",
    "continuity/build-canonical-asset.md",
    "image/system.md",
    "image/build-image-prompt.md",
    "image/reference-contract.md",
    "image/generate-scene.md",
    "image/style-guide.md",
    "repair/revise-image-prompt.md",
)


def load_prompts(root: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    values: dict[str, str] = {}
    snapshots: list[dict[str, str]] = []
    shared = Path(__file__).parent / "style_presets"
    extra = (
        "style/presets/cute-character.md", "style/presets/fantasy-anime.md",
        "style/presets/animation-3d.md", "style/presets/disney-animation.md",
        "style/presets/dystopian.md",
    )
    for relative in (*PROMPT_FILES, *extra):
        base = shared if relative in extra else root
        path = (base / Path(relative).name if relative in extra else base / relative).resolve()
        if base.resolve() not in path.parents or not path.is_file():
            raise RuntimeError(f"required prompt is missing: {relative}")
        content = path.read_text(encoding="utf-8")
        values[relative] = content
        snapshots.append({
            "name": Path(relative).stem,
            "relative_path": relative,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "content": content,
        })
    return values, snapshots
