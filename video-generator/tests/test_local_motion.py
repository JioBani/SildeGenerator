from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

from PIL import ImageChops, Image

ROOT = Path("/app") if Path("/app/harnesses").exists() else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harnesses" / "astra-motion" / "src"))

from app.local_motion import author_local_motion, author_directed_local_motion, _primitive
from app.config import Settings, production_settings
from app.motion_style import bind_motion_style
from app.planner import deterministic_plan
from app.providers.local_graphics import draw_background
from astra_motion.local_renderer import local_scene_html, local_timeline_lines
from astra_motion.scene_program import compile_scene_program


SCRIPT = "차를 보자 뇌가 그 차를 계속 찾아냅니다. 관심 대상에 주의를 기울입니다."
SPOTLIGHT_SCRIPT = (
    "옷에 작은 자국이 묻어 모두가 나를 볼까 걱정합니다.\n"
    "심리학에서는 이를 스포트라이트 효과라고 부릅니다.\n"
    "하지만 실제 실험에서 타인의 차림새를 기억한 사람은 절반도 되지 않았습니다.\n"
    "사람들은 저마다 자기 삶에 집중합니다."
)


def authored(style_id: str):
    preset = "editorial_illustration" if style_id == "narrative" else "graphic_explainer"
    plan = deterministic_plan(SCRIPT, "local vector artwork", preset)
    plan = bind_motion_style(plan, {"id": style_id, "version": "1.0.0", "imagePreset": preset}, mock=True)
    return author_local_motion(plan, {"id": style_id}, SCRIPT)


class LocalMotionTests(unittest.TestCase):
    def test_user_jobs_reject_mock_planning_and_images(self):
        with self.assertRaisesRegex(ValueError, "mock scene planning"):
            production_settings(Settings(runner_mode="mock", image_provider="oauth"),
                                "classic-slide", None, production_job=True)
        with self.assertRaisesRegex(ValueError, "mock images"):
            production_settings(Settings(runner_mode="live", image_provider="mock"),
                                "classic-slide", None, production_job=True)
        self.assertEqual(production_settings(Settings(runner_mode="mock", image_provider="mock"),
                                             "classic-slide", None).image_provider, "mock")
        self.assertEqual(production_settings(Settings(runner_mode="live", image_provider="oauth"),
                                             "classic-slide", None, production_job=True).image_provider, "oauth")

    def test_local_route_changes_only_motion_job_settings(self):
        base = Settings(runner_mode="live", image_provider="oauth", motion_local_production=True)
        route = {"id": "narrative", "productionRoute": "local_graphic"}
        motion = production_settings(base, "astra-motion", route)
        self.assertEqual((motion.runner_mode, motion.image_provider), ("live", "local_graphic"))
        self.assertFalse(motion.layer_decomposition_enabled)
        self.assertEqual((base.runner_mode, base.image_provider), ("live", "oauth"))
        self.assertIs(production_settings(base, "classic-slide", route), base)
        self.assertIs(production_settings(base, "astra-motion", {"id": "narrative"}), base)
        with self.assertRaises(ValueError):
            production_settings(Settings(motion_local_production=False), "astra-motion", route)
        with self.assertRaisesRegex(ValueError, "live scene direction"):
            production_settings(Settings(runner_mode="mock", motion_local_production=True), "astra-motion", route)

    def test_directed_local_scene_uses_script_objects_not_fixed_presenter(self):
        plan = deterministic_plan("포인트 네모 위를 우주정거장이 지납니다.", "local", "editorial_illustration")
        scene = plan.scenes[0]
        scene.object_states = [
            {"object_id": "point-nemo-marker", "role": "subject", "initial": "isolated", "final": "located"},
            {"object_id": "space-station", "role": "context", "initial": "far", "final": "closer"},
        ]
        scene.motion = [
            {"object_id": "point-nemo-marker", "kind": "reveal"},
            {"object_id": "space-station", "kind": "path_follow"},
        ]
        scene.layout["visual_labels"] = [
            {"text": "포인트 네모", "x": .3, "y": .4},
            {"text": "우주정거장", "x": .7, "y": .4},
        ]
        directed = author_directed_local_motion(plan, {"id": "narrative"})
        program = compile_scene_program(directed.scenes[0])
        markup = local_scene_html(directed.scenes[0], 1, program)
        self.assertIn("포인트 네모", markup)
        self.assertIn("우주정거장", markup)
        self.assertIn("primitive-marker", markup)
        self.assertIn("primitive-satellite", markup)
        self.assertNotIn("person-head", markup)
        self.assertNotIn("local-prop", markup)
        self.assertNotIn("<strong>subject</strong>", markup)
        self.assertTrue(any("directed-object-1" in line for line in local_timeline_lines("#scene-1", 0, 4, program)))

    def test_directed_local_scene_rejects_generic_plan(self):
        plan = deterministic_plan("포인트 네모 위를 우주정거장이 지납니다.", "local", "editorial_illustration")
        with self.assertRaisesRegex(ValueError, "no directed visual objects"):
            author_directed_local_motion(plan, {"id": "narrative"})

    def test_directed_local_scene_rejects_unavailable_artwork(self):
        plan = deterministic_plan("새 물체가 등장합니다.", "local", "graphic_explainer")
        scene = plan.scenes[0]
        scene.object_states = [{"object_id": "unbuilt-machine", "role": "새 기계", "initial": "off", "final": "on"}]
        scene.motion = [{"object_id": "unbuilt-machine", "kind": "reveal"}]
        scene.layout["visual_labels"] = [{"text": "새 기계", "x": .5, "y": .4}]
        with self.assertRaisesRegex(ValueError, "need authored assets for unbuilt-machine"):
            author_directed_local_motion(plan, {"id": "educational_info"})

    def test_film_framing_uses_distinct_editable_objects(self):
        expected = {
            "frame-set": "frame_set", "eye-symbol": "eye",
            "balanced-panel": "balanced_panel", "offset-panel": "offset_panel",
            "uncertainty-cloud": "cloud", "frame-grid": "grid",
            "eye-line": "eye_line", "lock-pin": "pin", "figure-frame": "figure",
            "subject-token": "figure", "upper-third-guide": "thirds_line",
            "travel-path": "path", "attention-dots": "dots",
            "speech-wave": "wave", "stable-eye-line": "eye_line",
            "level-frame": "level_frame", "warning-mark": "accent",
            "tilting-frame": "tilted_frame", "horizon-guide": "thirds_line",
            "imbalance-accent": "accent", "phone-frame": "phone",
            "screen-guide": "grid", "viewer-eye-symbol": "eye",
            "filmframes": "frame_set", "eyepointer": "eye",
            "calmframe": "balanced_panel", "uneasyframe": "offset_panel",
            "leftgaze": "eye_line", "rightgaze": "eye_line",
            "fixationpoint": "pin", "thirdline": "eye_line",
            "protagonistmarker": "figure", "dialoguewave": "wave",
            "periphery": "dots", "imbalancecue": "accent",
            "stableguide": "thirds_line", "tiltframe": "tilted_frame",
            "referencegrid": "grid", "phoneframe": "phone",
            "phoneguide": "grid", "outertiltguide": "thirds_line",
            "frame-stack": "frame_set", "crosshair-guide": "crosshair",
            "stable-frame": "level_frame", "unstable-frame": "tilted_frame",
            "gaze-paths": "path", "fixation-point": "pin",
            "eye-guide": "eye", "actor-positions": "figure",
            "eye-markers": "eye", "dialogue-symbol": "wave",
            "peripheral-shapes": "dots", "balance-frame": "level_frame",
            "balance-weights": "weights", "viewer-path": "path",
            "frame-triptych": "frame_set", "control-axis": "crosshair",
            "gaze-marker": "eye", "target-point": "pin",
            "thirds-line": "thirds_line", "protagonist-marker": "figure",
            "dialogue-wave": "wave", "tilt-frame": "tilted_frame",
            "balance-line": "thirds_line", "frame-guides": "grid",
        }
        for object_id, primitive in expected.items():
            with self.subTest(object_id=object_id):
                self.assertEqual(_primitive(object_id, "visual guide"), primitive)
        plan = deterministic_plan("영화 속 프레임은 시선을 이끕니다.", "local", "graphic_explainer")
        plan.title = "영화 속 프레임의 비밀"
        scene = plan.scenes[0]
        scene.object_states = [
            {"object_id": "frame-set", "role": "영화 프레임", "initial": "hidden", "final": "visible"},
            {"object_id": "eye-symbol", "role": "시선 표식", "initial": "dim", "final": "bright"},
        ]
        scene.motion = [
            {"object_id": "frame-set", "kind": "group_split"},
            {"object_id": "eye-symbol", "kind": "pulse"},
        ]
        scene.layout["visual_labels"] = [{"text": "재구성 예시", "x": .5, "y": .7}]
        directed = author_directed_local_motion(plan, {"id": "educational_info"})
        program = compile_scene_program(directed.scenes[0])
        markup = local_scene_html(directed.scenes[0], 1, program)
        self.assertIn("directed-theme-film_framing", markup)
        self.assertIn("primitive-frame_set", markup)
        self.assertIn("primitive-eye", markup)
        self.assertIn("재구성 예시", markup)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "frame.png"
            draw_background(directed.scenes[0], path, 640, 360)
            self.assertEqual(Image.open(path).getpixel((0, 60)), (19, 36, 47))

    def test_six_object_eye_line_scene_is_executable(self):
        plan = deterministic_plan("인물의 눈과 대사를 함께 봅니다.", "local", "graphic_explainer")
        scene = plan.scenes[0]
        ids = ["frame-grid", "upper-third-guide", "figure-frame", "eye-line", "lock-pin", "speech-wave"]
        scene.object_states = [{"object_id": object_id, "role": object_id, "initial": "hidden", "final": "visible"}
                               for object_id in ids]
        scene.motion = [{"object_id": object_id, "kind": "reveal"} for object_id in ids]
        scene.layout["visual_labels"] = [{"text": "상단 3분의 1", "x": .5, "y": .3}]
        directed = author_directed_local_motion(plan, {"id": "educational_info"})
        program = compile_scene_program(directed.scenes[0])
        self.assertEqual(len(program["local_visual"]["objects"]), 6)
        self.assertEqual(len(program["local_visual"]["motions"]), 6)
        self.assertIn("primitive-eye_line", local_scene_html(directed.scenes[0], 1, program))

    def test_narrative_has_repeated_actor_and_visible_artwork(self):
        plan = authored("narrative")
        self.assertGreaterEqual(len(plan.scenes), 2)
        self.assertEqual({scene.object_states[0]["object_id"] for scene in plan.scenes}, {"local-guide-v1"})
        program = compile_scene_program(plan.scenes[0])
        markup = local_scene_html(plan.scenes[0], 1, program)
        self.assertIn("person-head", markup)
        self.assertIn("local-prop", markup)
        self.assertTrue(any("person-eye" in line for line in local_timeline_lines("#scene-1", 0, 4, program)))

    def test_info_has_editable_nodes_and_distinct_background(self):
        plan = authored("educational_info")
        program = compile_scene_program(plan.scenes[0])
        markup = local_scene_html(plan.scenes[0], 1, program)
        self.assertEqual(program["local_visual"]["theme"], "attention")
        self.assertIn("평소 거리", markup)
        self.assertIn("info-node", markup)
        self.assertTrue(any("flow-token" in line for line in local_timeline_lines("#scene-1", 0, 4, program)))
        with TemporaryDirectory() as directory:
            path = Path(directory) / "background.png"
            attention_path = Path(directory) / "attention.png"
            draw_background(plan.scenes[0], path, 640, 360)
            draw_background(authored("narrative").scenes[0], attention_path, 640, 360)
            self.assertIsNotNone(ImageChops.difference(Image.open(path), Image.open(attention_path)).getbbox())

    def test_spotlight_script_does_not_reuse_car_artwork(self):
        preset = "editorial_illustration"
        plan = deterministic_plan(SPOTLIGHT_SCRIPT, "local vector artwork", preset)
        plan = bind_motion_style(plan, {"id": "narrative", "version": "1.0.0", "imagePreset": preset}, mock=True)
        plan = author_local_motion(plan, {"id": "narrative"}, SPOTLIGHT_SCRIPT)
        visuals = [scene.layout["local_visual"] for scene in plan.scenes]
        self.assertEqual({visual["theme"] for visual in visuals}, {"spotlight"})
        self.assertGreater(len({visual["mode"] for visual in visuals}), 1)
        program = compile_scene_program(plan.scenes[0])
        markup = local_scene_html(plan.scenes[0], 1, program)
        self.assertIn("shirt-mark", markup)
        self.assertIn("spotlight-crowd", markup)
        self.assertNotIn("local-prop", markup)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "background.png"
            attention_path = Path(directory) / "attention.png"
            draw_background(plan.scenes[0], path, 640, 360)
            draw_background(authored("narrative").scenes[0], attention_path, 640, 360)
            self.assertIsNotNone(ImageChops.difference(Image.open(path), Image.open(attention_path)).getbbox())


if __name__ == "__main__":
    unittest.main()
