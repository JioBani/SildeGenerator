"""Read-only screening for candidate actor cutouts, not an art approval."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image


VERSION = "astra-actor-cutout-screen-0.1"


def inspect_cutout(path: Path, *, halo_review_px: int = 120) -> dict:
    with Image.open(path) as image:
        if image.mode != "RGBA":
            return {"version": VERSION, "status": "TECHNICAL_REVIEW_REQUIRED", "findings": ["rgba_required"], "production_ready": False}
        alpha = image.getchannel("A")
        width, height = image.size
        bounds = {
            str(threshold): alpha.point(lambda value, limit=threshold: 255 if value >= limit else 0).getbbox()
            for threshold in (1, 16, 128)
        }
    findings = []
    core = bounds["128"]
    faint = bounds["1"]
    halo_extent = None
    if core is None:
        findings.append("opaque_subject_missing")
    elif faint is not None:
        halo_extent = max(core[0] - faint[0], core[1] - faint[1], faint[2] - core[2], faint[3] - core[3])
        if halo_extent > halo_review_px:
            findings.append("diffuse_alpha_halo_review")
        if core[0] <= 0 or core[1] <= 0 or core[2] >= width or core[3] >= height:
            findings.append("subject_touches_canvas_edge")
    return {
        "version": VERSION,
        "status": "TECHNICAL_REVIEW_REQUIRED" if findings else "TECHNICAL_SCREEN_PASS_HUMAN_REVIEW_REQUIRED",
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": [width, height],
        "alpha_bounds": {key: list(value) if value else None for key, value in bounds.items()},
        "halo_extent_px": halo_extent,
        "halo_review_threshold_px": halo_review_px,
        "findings": findings,
        "production_ready": False,
        "scope": "Experimental alpha extent and frame-edge screening only; does not assess anatomy, style, rigging or acting.",
    }
