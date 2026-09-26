"""Runtime evidence for generated scene images, never inferred from planner prose."""
import hashlib
from pathlib import Path


def record_generated_origin(scene, image_path: Path, *, provider: str, task_id: str):
    # Unknown providers must not silently acquire a trusted origin classification.
    origin = {'mock': 'mock', 'oauth': 'generated'}.get(provider, 'unknown')
    evidence = {
        'schema_version': 1,
        'origin': origin,
        'provider': provider,
        'image_task_id': task_id,
        'sha256': hashlib.sha256(Path(image_path).read_bytes()).hexdigest(),
        'recorded_by': 'runtime_asset_preparation',
        'archive_verified': False,
    }
    scene.layout = {**(scene.layout or {}), 'asset_origin': origin, 'asset_provenance': evidence}
    return evidence
