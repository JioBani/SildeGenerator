"""Trusted generated art packs, separate from source evidence and planner paths."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from PIL import Image
from .rendered_review import file_sha256


def read_packs(root: Path) -> dict:
    catalog = root / "catalog.json"
    if not catalog.is_file():
        return {}
    data = json.loads(catalog.read_text(encoding="utf-8"))
    if data.get("version") != "illustration-packs-0.1":
        raise ValueError("unsupported_illustration_catalog")
    records = {}
    for item in data["packs"]:
        identity = item.get("id", "")
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", identity) or identity in records:
            raise ValueError("invalid_or_duplicate_illustration_id")
        for key in ("title", "meaning_limit", "usage_basis", "prompt_record"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"illustration_metadata_missing:{key}")
        if item.get("origin") != "generated_illustration" or item.get("heading_degrees") != 0:
            raise ValueError("illustration_origin_or_heading_unsupported")
        rect = item.get("safe_rect", [])
        if len(rect) != 4 or not all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in rect) or not (rect[0] < rect[2] and rect[1] < rect[3]):
            raise ValueError("illustration_invalid_safe_rect")
        for role in ("background", "subject"):
            record = item[role]
            path = (root / record["file"]).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError("illustration_path_outside_registry_or_missing")
            if file_sha256(path) != record["sha256"]:
                raise ValueError("illustration_hash_changed")
            with Image.open(path) as image:
                image.load()
                if role == "subject":
                    if "A" not in image.getbands() or image.getchannel("A").getextrema() != (0, 255):
                        raise ValueError("illustration_subject_requires_real_alpha")
                    bbox = image.getchannel("A").getbbox()
                    if bbox is None or bbox[2] - bbox[0] < 10 or bbox[3] - bbox[1] < 10:
                        raise ValueError("illustration_subject_empty")
        records[identity] = item
    return records


def illustration_brief(root: Path) -> list[dict]:
    return [{k: item[k] for k in ("id", "title", "meaning_limit", "origin", "safe_rect")}
            for item in read_packs(root).values()]


def prepare_illustration(root: Path, composition, output: Path, size) -> dict:
    item = read_packs(root).get(composition.asset_pack_id)
    if item is None:
        raise ValueError("illustration_not_registered")
    with Image.open(root / item["background"]["file"]) as background:
        aspect = background.width / background.height
        if abs(aspect / (size[0] / size[1]) - 1) > .015:
            raise ValueError("illustration_aspect_requires_reauthoring")
    # Conservative rotation envelope for the complete sprite, not just its pivot.
    with Image.open(root / item["subject"]["file"]) as subject:
        ratio = subject.height / subject.width
    radius = composition.subject_width * (1 + ratio * ratio) ** .5 / 2
    left, top, right, bottom = item["safe_rect"]
    if any(not (left + radius <= p.x <= right - radius and top + radius * aspect <= p.y <= bottom - radius * aspect) for p in composition.points):
        raise ValueError("illustration_path_outside_safe_envelope")
    with Image.open(root / item["background"]["file"]) as background:
        background.convert("RGB").resize(size, Image.Resampling.LANCZOS).save(output)
    target = output.with_name(output.stem + "-subject.png")
    shutil.copy2(root / item["subject"]["file"], target)
    return {"prepared_by": "trusted_illustration_registry", "id": item["id"],
            "origin": item["origin"], "usage_basis": item["usage_basis"], "meaning_limit": item["meaning_limit"],
            "background_path": str(output), "background_sha256": file_sha256(output),
            "subject_path": str(target), "subject_sha256": file_sha256(target),
            "catalog_sha256": file_sha256(root / "catalog.json"), "safe_rect": item["safe_rect"],
            "image_generation_calls": 0}
