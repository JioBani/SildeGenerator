from __future__ import annotations

import json
from dataclasses import dataclass

from .models import ContinuityAsset, Scene, StyleBible


@dataclass(frozen=True)
class AssetImageSubject:
    id: str
    image_prompt: str


def canonical_asset_prompt(asset: ContinuityAsset, prompts: dict[str, str], style_bible: StyleBible | None = None) -> str:
    return (prompts["continuity/build-canonical-asset.md"]
        .replace("{{CANONICAL_IDENTITY}}", asset.canonical_identity)
        .replace("{{MUST_REMAIN_CONSISTENT}}", ", ".join(asset.must_remain_consistent) or "없음")
        .replace("{{ALLOWED_VARIATIONS}}", ", ".join(asset.allowed_variations) or "없음")
        .replace("{{ANCHOR_PROMPT}}", asset.anchor_prompt)
        .replace("{{STYLE_GUIDE}}", json.dumps(style_bible.model_dump(), ensure_ascii=False, indent=2) if style_bible else prompts["image/style-guide.md"]))


def scene_image_prompt(
    scene: Scene,
    assets: list[ContinuityAsset],
    prompts: dict[str, str],
    style_bible: StyleBible | None = None,
) -> str:
    reference_lines = []
    for index, asset in enumerate(assets, 1):
        reference_lines.append(
            f"참조 {index} / {asset.asset_id} / {asset.name}\n"
            f"- 반드시 유지: {', '.join(asset.must_remain_consistent) or asset.canonical_identity}\n"
            f"- 허용 변화: {', '.join(asset.allowed_variations) or '장면 지시에 따른 조명과 구도'}\n"
            "- 복사 금지: 기준 이미지의 배경, 포즈, 카메라 구도, 프레이밍"
        )
    reference_contract = prompts["image/reference-contract.md"].replace(
        "{{REFERENCE_MAP}}", "\n\n".join(reference_lines) or "참조 이미지 없음",
    )
    scene_payload = json.dumps({
        "id": scene.id,
        "narration": scene.narration,
        "visual_summary": scene.visual_summary,
        "image_prompt": scene.image_prompt,
        "present_asset_ids": scene.present_asset_ids,
        "reference_asset_ids": scene.reference_asset_ids,
        "sequence_id": scene.sequence_id,
        "cut_role": scene.cut_role,
        "parent_keycut_scene_id": scene.parent_keycut_scene_id,
        "keycut_dna": scene.keycut_dna.model_dump() if scene.keycut_dna else None,
    }, ensure_ascii=False, indent=2)
    style_text = json.dumps(style_bible.model_dump(), ensure_ascii=False, indent=2) if style_bible else prompts["image/style-guide.md"]
    keycut_contract = prompts["keycut/reference-contract.md"] if scene.cut_role != "keycut" else "이 장면은 sequence keycut이다. Style Bible과 keycut DNA를 직접 구현한다."
    return (prompts["image/generate-scene.md"]
        .replace("{{SCENE_JSON}}", scene_payload)
        .replace("{{REFERENCE_CONTRACT}}", keycut_contract + "\n\n" + reference_contract)
        .replace("{{STYLE_GUIDE}}", style_text))
