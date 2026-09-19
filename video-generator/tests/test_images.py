from __future__ import annotations

import unittest
from pathlib import Path

from app.image_prompts import scene_image_prompt
from pydantic import ValidationError

from app.models import ContinuityAsset, RenderRequest, Scene
from app.providers.images import validate_reference_count


def asset(index: int) -> ContinuityAsset:
    return ContinuityAsset(
        asset_id=f"asset-character-{index:03d}", category="character", name=f"인물 {index}",
        canonical_identity=f"인물 {index}의 고유 외형", must_remain_consistent=[f"특징 {index}"],
        allowed_variations=["표정"], states=[{"state_id": "default", "description": "기본"}],
        appearing_scene_ids=["scene-001", "scene-002"], selection_reason_code="IDENTITY_CRITICAL",
        selection_reason="정체성 유지", failure_if_inconsistent="다른 인물로 보임", confidence=0.9,
        anchor_prompt="단순 배경의 3/4 전신",
    )


class ReferencePromptTests(unittest.TestCase):
    def test_reference_order_and_asset_mapping_are_preserved(self) -> None:
        assets = [asset(2), asset(1)]
        scene = Scene(
            id="scene-001", narration="두 사람이 만납니다.", visual_summary="두 인물의 만남",
            image_prompt="와이드 장면", present_asset_ids=[item.asset_id for item in assets],
            reference_asset_ids=[item.asset_id for item in assets],
        )
        prompts = {
            "keycut/reference-contract.md": "KEYCUT_REFERENCE",
            "image/reference-contract.md": "{{REFERENCE_MAP}}",
            "image/generate-scene.md": "{{SCENE_JSON}}\n{{REFERENCE_CONTRACT}}\n{{STYLE_GUIDE}}",
            "image/style-guide.md": "스타일",
        }

        compiled = scene_image_prompt(scene, assets, prompts)

        self.assertLess(compiled.index("참조 1 / asset-character-002"), compiled.index("참조 2 / asset-character-001"))
        self.assertIn("복사 금지", compiled)

    def test_scene_without_references_compiles_without_fallback(self) -> None:
        scene = Scene(id="scene-001", narration="도시 전경입니다.", visual_summary="도시", image_prompt="와이드")
        prompts = {
            "keycut/reference-contract.md": "KEYCUT_REFERENCE",
            "image/reference-contract.md": "{{REFERENCE_MAP}}",
            "image/generate-scene.md": "{{REFERENCE_CONTRACT}}",
            "image/style-guide.md": "스타일",
        }

        compiled = scene_image_prompt(scene, [], prompts)

        self.assertIn("참조 이미지 없음", compiled)
        self.assertNotIn("직전", compiled)


class ProviderReferenceContractTests(unittest.TestCase):
    def test_accepts_zero_one_two_four_and_eight_references(self) -> None:
        for count in (0, 1, 2, 4, 8):
            with self.subTest(count=count):
                validate_reference_count([Path(f"{index}.png") for index in range(count)])

    def test_rejects_nine_without_override(self) -> None:
        with self.assertRaisesRegex(ValueError, "default reference limit"):
            validate_reference_count([Path(f"{index}.png") for index in range(9)])

    def test_hard_limit_rejects_seventeen_even_with_override(self) -> None:
        with self.assertRaisesRegex(ValueError, "hard limit"):
            validate_reference_count([Path(f"{index}.png") for index in range(17)], allow_override=True)


class ImageModelSelectionTests(unittest.TestCase):
    def test_accepts_all_supported_image_models(self) -> None:
        for model in ("gpt-image-2", "gpt-image-2.5-sunburst", "gpt-image-2.5-flare"):
            with self.subTest(model=model):
                request = RenderRequest(job_id="00000000-0000-0000-0000-000000000001", scenario="테스트", image_model=model)
                self.assertEqual(request.image_model, model)

    def test_rejects_unlisted_image_model(self) -> None:
        with self.assertRaises(ValidationError):
            RenderRequest(job_id="00000000-0000-0000-0000-000000000001", scenario="테스트", image_model="unknown-image")


if __name__ == "__main__":
    unittest.main()
