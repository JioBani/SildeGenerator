"""Fixture-scoped output critic: decoded video, not timeline declarations.

Detects the registered coral roof in the clear water corridor. This is not a
general visual tracker or a semantic/acting critic. Negative controls are required.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np


def observe(frames):
    positions = []
    for frame in frames:
        pixels = frame.astype(np.float32)
        mask = (pixels[:,:,0] > pixels[:,:,1] * 1.35) & (pixels[:,:,0] > pixels[:,:,2] * 1.65) & (pixels[:,:,0] > 130)
        mask[:int(frame.shape[0]*.38)] = False
        mask[int(frame.shape[0]*.8):] = False
        ys, xs = np.where(mask)
        positions.append(None if len(xs) < 8 else (float(xs.mean()), float(ys.mean())))
    found = [p for p in positions if p is not None]
    errors = []
    if len(found) != len(frames):
        errors.append("subject_missing")
    if found:
        if found[-1][0] - found[0][0] < frames.shape[2] * .45:
            errors.append("forward_transport_not_visible")
        if any(b[0] < a[0] - .8 for a,b in zip(found,found[1:])):
            errors.append("backtracking_or_discontinuity")
        if max(abs(b[0]-a[0]) for a,b in zip(found,found[1:])) > frames.shape[2] * .035:
            errors.append("transport_jump")
        # Fixed fixture: motion starts at 1.6s, stops at 6s of an 8s/24fps shot.
        for name, subset in [("initial",positions[:30]),("final",positions[-30:])]:
            if any(p is None for p in subset) or max(p[0] for p in subset if p) - min(p[0] for p in subset if p) > 1.5:
                errors.append(f"{name}_hold_missing")
    region = frames[:,30:70,10:70,:].astype(float)
    drift = float(np.max(np.mean(np.abs(region-region[0]),axis=(1,2,3))))
    if drift > 2.5:
        errors.append("background_not_fixed")
    return {"findings":errors,"subject_positions":positions,"background_drift":drift}


def main():
    p=argparse.ArgumentParser();p.add_argument("video",type=Path);a=p.parse_args()
    data=subprocess.check_output(["ffmpeg","-v","error","-i",str(a.video),"-vf","scale=320:180","-pix_fmt","rgb24","-f","rawvideo","pipe:1"],timeout=60)
    frames=np.frombuffer(data,dtype=np.uint8).reshape(-1,180,320,3)
    if len(frames)!=192:
        raise ValueError("fixture_requires_192_frames")
    positive=observe(frames)
    frozen=np.repeat(frames[:1],len(frames),axis=0).copy()
    frozen[:,150:]=frames[:,150:]  # Unrelated bottom labels cannot rescue a frozen boat.
    moved=np.stack([np.roll(frame,i//8,axis=1) for i,frame in enumerate(frames)])
    controls={"frozen_subject_with_changing_labels":observe(frozen),"reversed_transport":observe(frames[::-1]),"background_pan":observe(moved)}
    report={"version":"coral-launch-output-critic-0.1","video_sha256":hashlib.sha256(a.video.read_bytes()).hexdigest(),
        "scope":"Known original coral-launch fixture only; all decoded frames; not general semantic acceptance",
        "observations":positive,"negative_controls":controls,
        "status":"TECHNICAL_CAPABILITY_PASS" if not positive["findings"] and all(c["findings"] for c in controls.values()) else "REVISE",
        "not_evaluated":["audio","subtitle_sync","story","historical_accuracy","independent_concept_comparison","held_out_transfer"],"human_approval":None}
    target=a.video.with_name("transport-observations.json")
    target.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"status":report["status"],"findings":positive["findings"],"negatives":{k:v["findings"] for k,v in controls.items()},"report":str(target)}))
    if report["status"]=="REVISE":
        raise SystemExit(1)


if __name__=="__main__":
    main()
