import os
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from astra_motion.renderer import compile_project


project = Path(os.environ.get("ASTRA_SMOKE_PROJECT", "/tmp/astra-motion-smoke"))
project.mkdir(parents=True, exist_ok=True)
image = project.parent / "astra-motion-scene.png"
Image.new("RGB", (1920, 1080), (42, 91, 105)).save(image)
scene = SimpleNamespace(
    id="scene-1",
    image_path=str(image),
    viewer_takeaway="GPU parallel motion",
    narration="Object-level motion graphics verification",
    scene_function="explain_parallelism",
    layout={"mode": "comparison"},
    object_states=[
        {"object_id": "scene-image", "role": "subject"},
        {"object_id": "evidence-card", "role": "evidence"},
        {"object_id": "accent", "role": "highlight"},
    ],
    motion=[
        {"object_id": "scene-image", "kind": "camera_push"},
        {"object_id": "evidence-card", "kind": "reveal"},
        {"object_id": "accent", "kind": "emphasize"},
    ],
    transition="crossfade",
    rhythm="compare_then_resolve",
    duration_seconds=1.5,
)
compile_project([scene], project, SimpleNamespace(width=1920, height=1080, fps=30))
