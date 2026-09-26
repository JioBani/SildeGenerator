import unittest
from pathlib import Path

from app.genre_profiles import bind_plan, planning_instruction
from app.models import RenderRequest, ScenePlan
from app.planner import _compose_prompt, compile_source_units, deterministic_plan, validate_plan
from app.prompts import load_prompts


class CinematicStylesTest(unittest.TestCase):
    def test_styles_preserve_source_and_survive_genre_binding(self):
        source = "밤에 한 사람이 컴퓨터를 봅니다. 결과를 보고 미소 짓습니다."
        for style in ("cute_character", "fantasy_anime", "cinematic_realism", "graphic_explainer", "editorial_illustration", "animation_3d", "disney_animation", "dystopian"):
            request = RenderRequest.model_validate({"job_id": "11111111-1111-1111-1111-111111111111", "scenario": source, "image_style": style})
            self.assertEqual(request.image_style, style)
            plan = deterministic_plan(source, "style guide", style)
            validate_plan(plan, source)
            before = plan.style_bible.medium_and_rendering
            for genre in ("motion_graphic",):
                self.assertIn(f"Surface art style: {style}.", planning_instruction(genre, style))
                bound = ScenePlan.model_validate(bind_plan(plan, genre).model_dump())
                self.assertEqual(bound.style_bible.medium_and_rendering, before)
                self.assertEqual([s.narration for s in bound.scenes], [s.narration for s in plan.scenes])

    def test_only_selected_style_is_in_director_prompt(self):
        root = Path(__file__).resolve().parents[2] / "harnesses" / "classic-slide" / "prompts"
        prompts, snapshots = load_prompts(root)
        source = "결과를 봅니다."
        for style, other in (("cute_character", "fantasy_anime"), ("fantasy_anime", "cute_character"), ("animation_3d", "disney_animation"), ("disney_animation", "dystopian"), ("dystopian", "animation_3d")):
            text = _compose_prompt(prompts, source, compile_source_units(source), False, style)
            path = f"style/presets/{style.replace('_', '-')}.md"
            self.assertIn(prompts[path], text)
            self.assertNotIn(prompts[f"style/presets/{other.replace('_', '-')}.md"], text)
            self.assertEqual(len([s for s in snapshots if s['relative_path'] == path and s['sha256']]), 1)


if __name__ == "__main__":
    unittest.main()
