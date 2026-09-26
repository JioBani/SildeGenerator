from __future__ import annotations

import unittest
from pathlib import Path

from app.actor_cutout_qc import inspect_cutout


ROOT = Path(__file__).resolve().parents[2] / "experiments" / "light-pollution-story-asset-v1"


class ActorCutoutScreenTests(unittest.TestCase):
    def test_approved_d_layer_is_not_falsely_auto_approved(self) -> None:
        result = inspect_cutout(ROOT / "D/project/assets/person-body.png")
        self.assertEqual(result["findings"], [])
        self.assertFalse(result["production_ready"])

    def test_reaching_pose_is_clipped_at_frame_edge(self) -> None:
        result = inspect_cutout(ROOT / "E-actor-rig-study/reach-keypose-v1.png")
        self.assertIn("subject_touches_canvas_edge", result["findings"])

    def test_generated_arm_halo_requires_review(self) -> None:
        result = inspect_cutout(ROOT / "E-actor-rig-study/forearm-hand-v1.png")
        self.assertIn("diffuse_alpha_halo_review", result["findings"])
        self.assertGreater(result["halo_extent_px"], 120)
