"""Turn a flattened generated scene into reviewable motion layers.

The director supplies rough normalized boxes. GrabCut refines those boxes into
pixel masks, and OpenCV inpainting creates a clean plate behind the extracted
objects. Nothing is promoted silently: only layers that pass deterministic
mask checks are exposed to a renderer.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


VERSION = "astra-layer-decomposition-1.0"
MOVABLE_KINDS = {"path_follow", "group_split", "state_change", "reaction", "pulse", "reveal"}


def requested_objects(scene: Any) -> list[dict[str, Any]]:
    moving = {
        str(row.get("object_id"))
        for row in (getattr(scene, "motion", None) or [])
        if isinstance(row, dict) and row.get("kind") in MOVABLE_KINDS
    }
    result: list[dict[str, Any]] = []
    for row in getattr(scene, "object_states", None) or []:
        if not isinstance(row, dict) or row.get("object_id") not in moving:
            continue
        hint = row.get("region_hint")
        if row.get("isolation", "preferred") == "not_needed" or not _valid_box(hint):
            continue
        result.append({
            "object_id": str(row["object_id"]),
            "role": str(row.get("role") or "movable object"),
            "region_hint": [float(value) for value in hint],
            "depth_band": str(row.get("depth_band") or "midground"),
        })
    return result


def _valid_box(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    try:
        x, y, width, height = (float(item) for item in value)
    except (TypeError, ValueError):
        return False
    return 0 <= x < 1 and 0 <= y < 1 and width > 0 and height > 0 and x + width <= 1 and y + height <= 1


def validate_manifest(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("version") != VERSION:
        raise ValueError("layer_manifest_version_unsupported")
    if document.get("status") not in {"TECHNICAL_PASS", "REVIEW_REQUIRED", "UNAVAILABLE"}:
        raise ValueError("layer_manifest_status_invalid")
    layers = document.get("layers")
    if not isinstance(layers, list):
        raise ValueError("layer_manifest_layers_invalid")
    ids: set[str] = set()
    for layer in layers:
        if not isinstance(layer, dict):
            raise ValueError("layer_manifest_entry_invalid")
        object_id = layer.get("object_id")
        if not isinstance(object_id, str) or not object_id or object_id in ids:
            raise ValueError("layer_manifest_object_ids_invalid")
        ids.add(object_id)
        if not _valid_box(layer.get("bounds")):
            raise ValueError(f"{object_id}.bounds_invalid")
        if layer.get("technical_ready") is True and not layer.get("rgba_path"):
            raise ValueError(f"{object_id}.rgba_path_missing")
    return document


def decompose_scene(scene: Any, image_path: Path, output_dir: Path) -> dict[str, Any]:
    requests = requested_objects(scene)
    if not requests:
        return _write_manifest(output_dir, {
            "version": VERSION, "scene_id": scene.id, "status": "UNAVAILABLE",
            "source_sha256": _sha256(image_path), "background_path": None, "layers": [],
            "findings": ["no_movable_object_has_region_hint"],
        })
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return _write_manifest(output_dir, {
            "version": VERSION, "scene_id": scene.id, "status": "UNAVAILABLE",
            "source_sha256": _sha256(image_path), "background_path": None, "layers": [],
            "findings": ["opencv_runtime_unavailable"],
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    source = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if source is None:
        raise ValueError(f"layer_source_unreadable:{image_path}")
    height, width = source.shape[:2]
    combined = np.zeros((height, width), dtype=np.uint8)
    layers: list[dict[str, Any]] = []
    findings: list[str] = []
    for request in requests:
        x, y, box_width, box_height = request["region_hint"]
        left = max(1, min(width - 3, round(x * width)))
        top = max(1, min(height - 3, round(y * height)))
        right = max(left + 2, min(width - 1, round((x + box_width) * width)))
        bottom = max(top + 2, min(height - 1, round((y + box_height) * height)))
        mask = np.zeros((height, width), dtype=np.uint8)
        background_model = np.zeros((1, 65), dtype=np.float64)
        foreground_model = np.zeros((1, 65), dtype=np.float64)
        cv2.grabCut(source, mask, (left, top, right - left, bottom - top), background_model, foreground_model, 5, cv2.GC_INIT_WITH_RECT)
        binary = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        area = int(cv2.countNonZero(binary))
        area_ratio = area / float(width * height)
        component_count = max(0, int(cv2.connectedComponents(binary)[0]) - 1)
        touches_frame = bool(binary[0, :].any() or binary[-1, :].any() or binary[:, 0].any() or binary[:, -1].any())
        technical_ready = 0.0015 <= area_ratio <= 0.45 and component_count <= 12 and not touches_frame
        object_id = request["object_id"]
        rgba_path = output_dir / f"{object_id}.png"
        if technical_ready:
            alpha = cv2.GaussianBlur(binary, (0, 0), 1.2)
            rgba = cv2.cvtColor(source, cv2.COLOR_BGR2BGRA)
            rgba[:, :, 3] = alpha
            cv2.imwrite(str(rgba_path), rgba)
            combined = cv2.bitwise_or(combined, binary)
        else:
            findings.append(f"{object_id}:mask_quality_failed")
        layers.append({
            **request,
            "bounds": request["region_hint"],
            "rgba_path": str(rgba_path) if technical_ready else None,
            "technical_ready": technical_ready,
            "review_status": "HUMAN_PENDING" if technical_ready else "REJECTED",
            "metrics": {"area_ratio": round(area_ratio, 6), "component_count": component_count, "touches_frame": touches_frame},
        })

    background_path = output_dir / "background.png"
    if combined.any():
        expanded = cv2.dilate(combined, np.ones((15, 15), np.uint8), iterations=1)
        background = cv2.inpaint(source, expanded, 5, cv2.INPAINT_TELEA)
        cv2.imwrite(str(background_path), background)
    ready = [layer for layer in layers if layer["technical_ready"]]
    document = {
        "version": VERSION, "scene_id": scene.id,
        "status": "TECHNICAL_PASS" if ready and len(ready) == len(layers) else "REVIEW_REQUIRED",
        "source_sha256": _sha256(image_path),
        "background_path": str(background_path) if ready else None,
        "layers": layers, "findings": findings,
        "production_ready": False,
    }
    return _write_manifest(output_dir, document)


def _write_manifest(output_dir: Path, document: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validate_manifest(document)
    path = output_dir / "layer-manifest.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**document, "manifest_path": str(path)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
