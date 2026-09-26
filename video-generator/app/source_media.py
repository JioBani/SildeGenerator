"""Trusted local evidence registry. Planner strings never grant asset access."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image
from .rendered_review import file_sha256


def read_catalog(root: Path) -> dict:
    file = root / "catalog.json"
    if not file.is_file():
        return {}
    content = json.loads(file.read_text(encoding="utf-8"))
    if content.get("version") != "source-media-0.1":
        raise ValueError("unsupported_source_catalog")
    records = {}
    for item in content["assets"]:
        if item["id"] in records:
            raise ValueError("duplicate_source_id")
        for field in ("title", "source_url", "rights_url", "usage_basis", "attribution", "date_label", "meaning_limit", "sha256", "file"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"source_metadata_missing:{field}")
        if item.get("origin") not in {"photograph", "document", "observational_visualization"}:
            raise ValueError("invalid_source_origin")
        records[item["id"]] = item
    return records


def source_brief(root: Path) -> list[dict]:
    result = []
    for item in read_catalog(root).values():
        verified_source_path(root, item)
        result.append({key: item[key] for key in ("id", "title", "source_url", "date_label", "meaning_limit", "origin")})
    return result


def verified_source_path(root: Path, item: dict) -> Path:
    target = (root / item["file"]).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError("source_path_outside_registry_or_missing")
    if file_sha256(target) != item["sha256"]:
        raise ValueError("source_hash_changed")
    with Image.open(target) as image:
        image.verify()
    return target


def prepare_source(root: Path, source_id: str, output: Path, size=None) -> dict:
    item = read_catalog(root).get(source_id)
    if item is None:
        raise ValueError("source_not_registered")
    target = verified_source_path(root, item)
    # Format conversion only: retain the complete image without generative edits.
    with Image.open(target) as original:
        image = original.convert("RGB")
        if size is not None:
            from PIL import ImageOps
            image = ImageOps.pad(image, size, color="#161c1b")
        image.save(output, format="PNG")
    return {**item, "prepared_sha256": file_sha256(output), "original_sha256": item["sha256"],
            "prepared_by": "trusted_source_registry", "image_path": str(output)}
