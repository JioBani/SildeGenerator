import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import cv2

from scripts.actor_assembly_gate import VERSION, audit, color_distance, contract_findings, frame_count_findings, local_file, summarize_probe, occlusion_findings


class AssemblyGateTests(unittest.TestCase):
    def test_collar_must_draw_in_front_of_neck(self):
        self.assertEqual(occlusion_findings(["torso","neck","collar"],"neck","collar"),[])
        self.assertIn("occluder_not_in_front",occlusion_findings(["torso","collar","neck"],"neck","collar"))

    def test_occluder_must_be_an_actual_distinct_layer(self):
        self.assertTrue(occlusion_findings(["neck"],"neck","missing"))
        self.assertTrue(occlusion_findings(["neck"],"neck","neck"))

    def joint(self):
        return {"version":VERSION, "joints":[{"id":"neck", "surface":"shaded_continuous",
            "construction":"shared_source_surface", "registration":"shared_canvas",
            "registration_evidence":"registered.json", "overlap_policy":"continuous_surface",
            "motion_binding":"neck-skin-mesh"}]}

    def test_shaded_skin_cannot_be_patched_with_flat_color(self):
        contract = self.joint()
        contract["joints"][0]["construction"] = "flat_color_patch"
        self.assertIn("neck:flat_patch_on_shaded_surface", contract_findings(contract))

    def test_declared_shared_canvas_without_evidence_is_not_enough(self):
        contract = self.joint()
        contract["joints"][0]["registration_evidence"] = None
        self.assertIn("neck:registration_evidence_missing", contract_findings(contract))

    def test_each_joint_requires_motion_binding(self):
        contract = self.joint()
        contract["joints"][0]["motion_binding"] = None
        self.assertIn("neck:motion_binding_missing", contract_findings(contract))

    def test_empty_and_duplicate_joint_inventory(self):
        self.assertTrue(contract_findings({"version":VERSION,"joints":[]}))
        contract = self.joint()
        contract["joints"].append(copy.deepcopy(contract["joints"][0]))
        self.assertIn("joint_ids_invalid", contract_findings(contract))

    def test_occluded_seam_requires_occluder(self):
        contract = self.joint()
        contract["joints"][0]["surface"] = "occluded_boundary"
        self.assertIn("neck:occluder_missing", contract_findings(contract))

    def test_solid_color_vs_discontinuity(self):
        frame = np.full((20,20,3),100,np.uint8)
        self.assertAlmostEqual(color_distance(frame,[2,2,3,3],[12,2,3,3]),0)
        frame[:,10:] = 180
        self.assertGreater(color_distance(frame,[2,2,3,3],[12,2,3,3]),5)

    def test_outside_probe_rejected_not_silently_clamped(self):
        with self.assertRaises(ValueError):
            color_distance(np.zeros((20,20,3),np.uint8),[-1,0,4,4],[4,4,3,3])

    def test_intermediate_bad_frame_not_hidden_by_good_endpoints(self):
        report = summarize_probe([0,0,9,0,0],5)
        self.assertEqual(report["frames_over_trigger"],1)
        self.assertEqual(report["worst_frame"],2)

    def test_truncated_video_cannot_pass(self):
        self.assertTrue(frame_count_findings(281,282))
        self.assertTrue(frame_count_findings(0,0))
        self.assertFalse(frame_count_findings(282,282))

    def test_asset_change_invalidates_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / "source.txt"
            file.write_text("old")
            old_hash = hashlib.sha256(file.read_bytes()).hexdigest()
            file.write_text("new")
            contract = self.joint()
            contract["evidence"] = [{"path":"source.txt","sha256":old_hash}]
            result = audit(contract,root)
            self.assertIn("stale_artifact:source.txt",result["findings"])
            self.assertFalse(result["production_ready"])

    def test_no_path_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                local_file(Path(folder),"../elsewhere")

    def test_empty_measurement_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            summarize_probe([],5)

    def test_complete_mock_audit_never_grants_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            video = root / "mock.avi"
            writer = cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*"MJPG"),30,(32,32))
            self.assertTrue(writer.isOpened())
            for _ in range(6):
                writer.write(np.full((32,32,3),100,np.uint8))
            writer.release()
            registration = root / "registered.json"
            registration.write_text('{"fixture":"uniform mock only"}')
            contract = self.joint()
            contract.update({"video":"mock.avi","canvas":[32,32],"fps":30,"expected_frames":6,
                "evidence":[{"path":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in (video,registration)],
                "probes":[{"id":"mock-probe","a":[2,2,3,3],"b":[12,2,3,3],"trigger_delta_e76":5}]})
            report = audit(contract,root)
            self.assertEqual(report["status"],"HUMAN_REVIEW_REQUIRED",report)
            self.assertFalse(report["production_ready"])
            self.assertEqual(report["decoded_frames"],6)

    def test_actual_rejected_candidate_is_blocked(self):
        root = Path(__file__).resolve().parents[1] / "experiments/light-pollution-story-asset-v1"
        if not (root / "C/comparison.mp4").is_file():
            self.skipTest("Local rendered regression fixture is not distributed in source")
        contract = json.loads((root / "C/assembly-contract.json").read_text(encoding="utf-8"))
        report = audit(contract,root)
        self.assertEqual(report["decoded_frames"],282)
        self.assertEqual(report["status"],"BLOCKED")
        self.assertIn("neck-shirt:flat_patch_on_shaded_surface",report["findings"])


if __name__ == "__main__":
    unittest.main()
