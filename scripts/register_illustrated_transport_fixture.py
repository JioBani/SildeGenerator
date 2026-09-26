"""Register the two original built-in ImageGen assets for the local benchmark."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root = ROOT / "experiments/illustrated-transport-v1/assets"
manifest = {
    "version": "illustration-packs-0.1",
    "packs": [{
        "id": "fictional-coast-launch", "title": "Original gouache coastal launch and fictional waterway",
        "meaning_limit": "Fictional geography and generic boat. Not Shackleton, a historical record, or a verified real route.",
        "origin": "generated_illustration", "usage_basis": "Original assets generated for this project with built-in ImageGen; no reference film assets used.",
        "prompt_record": "../generation-prompts.json", "heading_degrees": 0,
        "safe_rect": [.12, .38, .86, .8],
        **{role: {"file": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
           for role, name in [("background", "coast.png"), ("subject", "boat.png")]}
    }]
}
target = root / "catalog.json"
if target.exists():
    raise SystemExit("Refusing to overwrite existing catalog")
target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(target)
