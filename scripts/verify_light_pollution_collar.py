"""Shot-specific regression checks; not a generic skin or acting classifier."""
import json
import subprocess
import cv2
import numpy as np

from actor_assembly_gate import occlusion_findings
from build_light_pollution_story_ab import EXPERIMENT, sha256


def warm_patch(frame, box):
    x,y,w,h = box
    b,g,r = np.median(frame[y:y+h,x:x+w],axis=(0,1))
    return bool(r-g > 15 and g-b > 10)


def verify():
    receipt = json.loads((EXPERIMENT / "D/receipt.json").read_text())
    if sha256(EXPERIMENT / "C/comparison.mp4") != receipt["source_performance_sha256"]:
        raise ValueError("Approved reference changed")
    c = cv2.VideoCapture(str(EXPERIMENT / "C/comparison.mp4"))
    d = cv2.VideoCapture(str(EXPERIMENT / "D/comparison.mp4"))
    if not c.isOpened() or not d.isOpened():
        raise ValueError("Comparison videos missing")
    rows = []
    try:
        while True:
            ok_a, a = c.read()
            ok_b, b = d.read()
            if not ok_a and not ok_b:
                break
            if not ok_a or not ok_b or a.shape != b.shape:
                raise ValueError("Video correspondence broken")
            diff = np.abs(a[325:625,1290:1680].astype(float)-b[325:625,1290:1680].astype(float))
            rows.append({"frame":len(rows), "face_mean_channel_delta":float(diff.mean()),
                "neck_probe_covered":all(warm_patch(b, box) for box in ([1466,710,5,5],[1480,744,5,5]))})
    finally:
        c.release()
        d.release()
    audio = {}
    for variant in ("C","D"):
        audio[variant] = subprocess.check_output(["ffmpeg","-v","error","-i",str(EXPERIMENT / variant / "comparison.mp4"),
            "-map","0:a:0","-c:a","pcm_s16le","-f","hash","-hash","sha256","-"],text=True).strip()
    findings = occlusion_findings(receipt["draw_order"],"head_and_neck",receipt["occluder"])
    if len(rows) != 282:
        findings.append("frame_count_changed")
    if audio["C"] != audio["D"]:
        findings.append("audio_changed")
    if any(not row["neck_probe_covered"] for row in rows):
        findings.append("neck_probe_exposes_non_skin_color")
    if not rows or max(row["face_mean_channel_delta"] for row in rows) > 1.5:
        findings.append("approved_face_changed")
    result = {"status":"BLOCKED" if findings else "TECHNICAL_CHECKS_PASS_HUMAN_REVIEW_REQUIRED",
        "production_ready":False,"frames":len(rows),"findings":findings,
        "max_face_mean_channel_delta":max((row["face_mean_channel_delta"] for row in rows),default=None),
        "uncovered_probe_frames":[row["frame"] for row in rows if not row["neck_probe_covered"]],
        "video_sha256":sha256(EXPERIMENT / "D/comparison.mp4"),"audio_hashes":audio,
        "scope":"Two shot-specific warm-palette probes and an approved face ROI across 282 frames. Not every collar edge or every possible pose.",
        "rows":rows}
    (EXPERIMENT / "D/verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"},indent=2))
    return result


if __name__ == "__main__":
    raise SystemExit(2 if verify()["findings"] else 0)
