"""Provider-free integration for the unified motion-graphics contract."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.genre_profiles import snapshot
from app.models import RenderRequest, ScenePlan
from app.planner import create_plan, validate_plan


class MotionGraphicPipelineTests(unittest.TestCase):
    def test_unified_contract_preserves_narration_and_serializes(self):
        script = "GPU는 여러 계산을 동시에 처리합니다. 계산 결과는 화면을 만드는 데 사용됩니다."
        prompts = {"image/style-guide.md": "Clear simple illustration."}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = asyncio.run(create_plan(script, prompts, SimpleNamespace(runner_mode="mock"), None, root))
            plan = asyncio.run(create_plan(
                script,
                prompts,
                SimpleNamespace(runner_mode="mock"),
                None,
                root,
                genre_id="motion_graphic",
            ))
            validate_plan(plan, script)
            self.assertEqual([scene.narration for scene in plan.scenes], [scene.narration for scene in legacy.scenes])
            self.assertEqual(plan.genre_contract, snapshot())
            self.assertEqual(plan.style_bible.medium_and_rendering, legacy.style_bible.medium_and_rendering)
            restored = ScenePlan.model_validate_json(plan.model_dump_json())
            self.assertEqual(restored.genre_contract, plan.genre_contract)
            self.assertTrue(all(scene.layout["production_format"] == "motion_graphic" for scene in restored.scenes))

    def test_request_allows_only_unified_format_with_astra_motion(self):
        args = {"job_id": "00000000-0000-0000-0000-000000000001", "scenario": "원문"}
        self.assertIsNone(RenderRequest(**args).genre_id)
        request = RenderRequest(
            **args,
            genre_id="motion_graphic",
            genre_version="1.0.0",
            harness_id="astra-motion",
        )
        self.assertEqual(request.genre_id, "motion_graphic")
        with self.assertRaises(ValueError):
            RenderRequest(**args, genre_id="knowledge", harness_id="astra-motion")
        with self.assertRaises(ValueError):
            RenderRequest(**args, genre_id="motion_graphic", harness_id="classic-slide")
        with self.assertRaises(ValueError):
            RenderRequest(**args, genre_version="1.0.0")


if __name__ == "__main__":
    unittest.main()
