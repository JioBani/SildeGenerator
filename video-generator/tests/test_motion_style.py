from pathlib import Path
import unittest

from app.image_prompts import scene_image_prompt
from app.motion_style import bind_motion_style, style_instruction
from app.planner import deterministic_plan
from app.models import RenderRequest
from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import validate_harness_plan


ROOT = Path("/app") if Path("/app/harnesses").exists() else Path(__file__).resolve().parents[2]


def style(style_id, image_preset):
    return {"id": style_id, "version": "1.0.0", "imagePreset": image_preset}


class MotionStyleTests(unittest.TestCase):
    def test_styles_produce_different_editable_scene_contracts(self):
        script = "빛이 창으로 들어옵니다. 커튼을 닫자 방이 어두워집니다."
        base = deterministic_plan(script, "flat", "editorial_illustration")
        narrative = bind_motion_style(base, style("narrative", "editorial_illustration"), mock=True)
        educational = bind_motion_style(base, style("educational_info", "graphic_explainer"), mock=True)
        self.assertEqual(narrative.scenes[0].layout["continuity_group"], "mock-primary-subject")
        self.assertTrue(educational.scenes[0].layout["visual_labels"])
        self.assertIn("same object_id", style_instruction(style("narrative", "editorial_illustration")))
        self.assertIn("visual_labels", style_instruction(style("educational_info", "graphic_explainer")))
        self.assertIn("Do not bake labels", scene_image_prompt(educational.scenes[0], [], {
            "image/reference-contract.md": "{{REFERENCE_MAP}}",
            "keycut/reference-contract.md": "",
            "image/generate-scene.md": "{{SCENE_JSON}} {{REFERENCE_CONTRACT}} {{STYLE_GUIDE}}",
            "image/style-guide.md": "flat",
        }))
        harness = HarnessRegistry(ROOT / "harnesses").load("astra-motion")
        self.assertEqual(validate_harness_plan(harness, narrative.scenes), [])
        self.assertEqual(validate_harness_plan(harness, educational.scenes), [])

    def test_live_narrative_requires_subject_and_info_requires_labels(self):
        base = deterministic_plan("첫 장면입니다. 둘째 장면입니다.", "flat")
        with self.assertRaisesRegex(ValueError, "continuity_group"):
            bind_motion_style(base, style("narrative", "editorial_illustration"))
        for scene in base.scenes:
            scene.layout["continuity_group"] = "main"
        with self.assertRaisesRegex(ValueError, "object_id"):
            bind_motion_style(base, style("narrative", "editorial_illustration"))
        for scene in base.scenes:
            scene.object_states.append({"object_id": "night-window-light", "role": "subject", "initial": "dim", "final": "bright"})
        bound = bind_motion_style(base, style("narrative", "editorial_illustration"))
        self.assertEqual(bound.scenes[0].layout["continuity_group"], "main")
        with self.assertRaisesRegex(ValueError, "visual_labels"):
            bind_motion_style(base, style("educational_info", "graphic_explainer"))

    def test_request_rejects_style_on_slide_and_preset_mismatch(self):
        common = {"job_id": "00000000-0000-0000-0000-000000000001", "scenario": "설명입니다."}
        with self.assertRaises(ValueError):
            RenderRequest(**common, harness_id="classic-slide", motion_style=style("narrative", "editorial_illustration"))
        with self.assertRaises(ValueError):
            RenderRequest(**common, harness_id="astra-motion", image_style="cute_character", motion_style=style("educational_info", "graphic_explainer"))


if __name__ == "__main__":
    unittest.main()
