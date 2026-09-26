"""Experimental assembly evidence gate, never an automatic acting approval.

Fixed probe regions are authored for one shot's motion envelope. Color differences
are review triggers, not seam detection or a universal perceptual quality score.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import cv2
import numpy as np

VERSION = "actor-assembly-gate-0.1"


def occlusion_findings(draw_order: list[str], covered: str, occluder: str) -> list[str]:
    """Motion parenting does not establish which surface draws in front."""
    if len(set(draw_order)) != len(draw_order) or covered == occluder:
        return ["occlusion_layer_ids_invalid"]
    if covered not in draw_order or occluder not in draw_order:
        return ["occlusion_layer_missing"]
    return [] if draw_order.index(occluder) > draw_order.index(covered) else ["occluder_not_in_front"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("artifact_outside_study")
    if not path.is_file():
        raise ValueError("artifact_missing:" + value)
    return path


def contract_findings(contract: dict) -> list[str]:
    findings = []
    if contract.get("version") != VERSION:
        return ["unsupported_contract_version"]
    if not contract.get("joints"):
        return ["joint_inventory_missing"]
    ids = [joint.get("id") for joint in contract["joints"]]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        return ["joint_ids_invalid"]
    for joint in contract["joints"]:
        name = joint["id"]
        if joint.get("surface") not in {"shaded_continuous", "flat_continuous", "occluded_boundary"}:
            findings.append(name + ":surface_undefined")
        if joint.get("construction") not in {"flat_color_patch", "shared_source_surface", "authored_overlap", "authored_mesh"}:
            findings.append(name + ":construction_undefined")
        if joint.get("surface") == "shaded_continuous" and joint.get("construction") == "flat_color_patch":
            findings.append(name + ":flat_patch_on_shaded_surface")
        if joint.get("registration") != "shared_canvas":
            findings.append(name + ":common_canvas_not_verified")
        if not joint.get("registration_evidence"):
            findings.append(name + ":registration_evidence_missing")
        if joint.get("overlap_policy") not in {"authored_hidden_overlap", "continuous_surface"}:
            findings.append(name + ":overlap_not_authored")
        if joint.get("surface") == "occluded_boundary" and not joint.get("occluder"):
            findings.append(name + ":occluder_missing")
        if joint.get("surface") == "occluded_boundary":
            findings.extend(name + ":" + value for value in occlusion_findings(
                contract.get("draw_order", []), joint.get("covered_layer"), joint.get("occluder")))
        if not joint.get("motion_binding"):
            findings.append(name + ":motion_binding_missing")
    return findings


def color_distance(frame: np.ndarray, a: list[int], b: list[int]) -> float:
    """CIE76 on patch medians; no claim of perceptual acceptability."""
    medians = []
    height, width = frame.shape[:2]
    for box in (a, b):
        if len(box) != 4 or any(type(n) is not int for n in box):
            raise ValueError("probe_box_invalid")
        x, y, w, h = box
        if min(w, h) <= 0 or min(x, y) < 0 or x + w > width or y + h > height:
            raise ValueError("probe_outside_frame")
        lab = cv2.cvtColor(frame[y:y+h, x:x+w].astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
        medians.append(np.median(lab, axis=(0, 1)))
    return float(np.linalg.norm(medians[0] - medians[1]))


def summarize_probe(values: list[float], trigger: float) -> dict:
    if not values or not math.isfinite(trigger) or trigger <= 0 or not np.isfinite(values).all():
        raise ValueError("probe_measurement_invalid")
    return {"max_delta_e76":float(max(values)), "median_delta_e76":float(np.median(values)),
            "worst_frame":int(np.argmax(values)),
            "frames_over_trigger":sum(value > trigger for value in values),
            "review_trigger":trigger, "threshold_status":"EXPERIMENTAL_NOT_CALIBRATED"}


def frame_count_findings(decoded: int, expected: int) -> list[str]:
    return [] if decoded == expected and expected > 0 else ["decoded_frame_count_mismatch"]


def audit(contract: dict, root: Path) -> dict:
    findings = contract_findings(contract)
    result = {"version":VERSION, "status":"BLOCKED", "production_ready":False,
              "findings":findings, "human_quality":"NOT_APPROVED", "measurements":{},
              "scope":"Declared joints and fixed probes only; not whole-character visual approval."}
    try:
        evidence = contract.get("evidence", [])
        if not evidence:
            raise ValueError("artifact_evidence_missing")
        for item in evidence:
            path = local_file(root, item["path"])
            if digest(path) != item["sha256"]:
                raise ValueError("stale_artifact:" + item["path"])
        video = local_file(root, contract["video"])
        if contract["video"] not in {item["path"] for item in evidence}:
            raise ValueError("video_not_bound_to_hash")
        evidence_paths = {item["path"] for item in evidence}
        for joint in contract["joints"]:
            if joint.get("registration_evidence") and joint["registration_evidence"] not in evidence_paths:
                raise ValueError("registration_not_bound_to_hash:" + joint["id"])
        expected = contract["expected_frames"]
        width, height = contract["canvas"]
        if type(expected) is not int or expected <= 0 or not math.isfinite(contract["fps"]) or contract["fps"] <= 0:
            raise ValueError("invalid_video_contract")
        probes = contract.get("probes", [])
        if not probes:
            raise ValueError("rendered_probe_evidence_missing")
        if len({probe["id"] for probe in probes}) != len(probes):
            raise ValueError("probe_ids_duplicate")
        series = {probe["id"]:[] for probe in probes}
        cap = cv2.VideoCapture(str(video))
        decoded = 0
        try:
            if not cap.isOpened():
                raise ValueError("video_not_decodable")
            if abs(cap.get(cv2.CAP_PROP_FPS) - contract["fps"]) > .001:
                raise ValueError("fps_mismatch")
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if frame.shape[:2] != (height, width):
                    raise ValueError("canvas_mismatch")
                for probe in probes:
                    series[probe["id"]].append(color_distance(frame, probe["a"], probe["b"]))
                decoded += 1
                if decoded > expected:
                    break
        finally:
            cap.release()
        findings.extend(frame_count_findings(decoded, expected))
        for probe in probes:
            measurement = summarize_probe(series[probe["id"]], probe["trigger_delta_e76"])
            result["measurements"][probe["id"]] = measurement
            if measurement["frames_over_trigger"]:
                findings.append(probe["id"] + ":color_continuity_review_required")
        result.update({"decoded_frames":decoded, "video_sha256":digest(video),
                       "probe_series":series})
        if not findings:
            result["status"] = "HUMAN_REVIEW_REQUIRED"
    except (ValueError, KeyError, TypeError, OSError, cv2.error) as error:
        findings.append(str(error))
    return result
