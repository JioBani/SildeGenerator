"""Reinspect an existing delivery without rerendering or changing its receipt."""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video-generator"))
from app.rendered_review import file_sha256, inspect_render
from app.autonomous_policy import adoption_decision

parser = argparse.ArgumentParser()
parser.add_argument("delivery", type=Path)
args = parser.parse_args()
folder = args.delivery.resolve()
receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
scenes = [SimpleNamespace(**row) for row in receipt["scenes"]]
review = inspect_render(folder / "delivery/hybrid.mp4", scenes, width=1280, height=720, fps=24)
report = {
    "scope": "Technical pixel observations only; not semantic or emotional acceptance",
    "original_receipt_sha256": file_sha256(folder / "receipt.json"),
    "observer_code_sha256": file_sha256(ROOT / "video-generator/app/rendered_review.py"),
    "inspection": review,
}
destination = folder / f"observations-{report['observer_code_sha256'][:12]}.json"
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
baseline = folder.parent / "hybrid-story-smoke-v2/delivery/hybrid.mp4"
candidate_hash, baseline_hash = file_sha256(folder / "delivery/hybrid.mp4"), file_sha256(baseline)
verified_hash = file_sha256(destination)
pixel_evidence = {"status": "PASS" if review["status"] == "PIXEL_CHECKS_PASS" else "FAIL",
    "critical_failures": len(review["findings"]), "candidate_sha256": candidate_hash, "report_sha256": verified_hash}
decision = adoption_decision({"candidate_sha256": candidate_hash, "baseline_sha256": baseline_hash,
    "checks": {"technical": pixel_evidence, "output_frames": pixel_evidence}},
    candidate_hash=candidate_hash, baseline_hash=baseline_hash, verified_report_hashes={verified_hash})
checkpoint = {"decision": decision, "engine": receipt["harness"], "video": str(folder / "delivery/hybrid.mp4"),
    "routes": receipt["routes"], "concept_selection": "NOT_YET_EVALUATED_WITH_THREE_BLINDED_CANDIDATES",
    "critical_pixel_findings": review["findings"], "other_critical_dimensions": "UNVERIFIED",
    "comparison": "v2 missing artwork; v3 visible artwork, diagram state changes and dated source. Not an independent semantic A/B test.",
    "render_attempts": 3, "discarded_from_adoption": {"v1": "strict font declaration failure", "v2": "subtitle-only output"},
    "calls_this_render": {"image_generation": 0, "separately_billed_api": 0, "elevenlabs": 0},
    "runtime_seconds": "NOT_INSTRUMENTED_FOR_THIS_DEVELOPMENT_RUN", "source_media": [s.layout.get("hybrid_source") for s in scenes if s.layout.get("hybrid_source")],
    "learned_candidate": "Measure channel-wise spatial variation; tinted blank output is not content.",
    "promoted_capabilities": [], "maintained": ["private mixed-route rendering"], "production_deployed": False,
    "not_evaluated": review["not_evaluated"],
    "next_bottleneck": "Independent meaning/route/design evaluation and held-out benchmark before autonomous adoption"}
(folder / "unattended-checkpoint.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"path": str(destination), "status": review["status"], "findings": review["findings"]}))
