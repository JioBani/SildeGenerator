"""Decoded common-scale and timed-narration evidence for an actual mixed-film probe."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"video-generator"))
from app.tracking import atomic_json, sha256_file


def widths(frames,nodes):
    rows=[]
    for frame in frames:
        found=[]
        for j,node in enumerate(nodes):
            color=np.array([int(node["color"][i:i+2],16) for i in (1,3,5)])
            y=round((165+j*250/max(1,len(nodes)-1))*.6)
            region=frame[y+3:y+18,167:602].astype(float)
            mask=np.linalg.norm(region-color,axis=2)<38
            found.append(int(np.count_nonzero(mask.mean(axis=0)>.7)))
        rows.append(found)
    return np.array(rows)


def assess(values,expected,starts,fps):
    findings=[]
    if np.max(values[0])>3: findings.append("no_initial_read_hold")
    if np.max(np.abs(values[-1]-expected))>4: findings.append("wrong_common_scale_geometry")
    arrivals=[next((i/fps for i,v in enumerate(values[:,j]) if v>3),None) for j in range(len(expected))]
    for actual,wanted in zip(arrivals,starts):
        if actual is None or abs(actual-wanted)>.15: findings.append("narration_event_alignment_error")
    if any(v is None for v in arrivals) or arrivals!=sorted(arrivals,key=lambda v:-1 if v is None else v):
        findings.append("missing_or_reversed_events")
    if np.min(np.diff(values,axis=0)) < -4: findings.append("unexpected_quantity_regression")
    if np.max(np.ptp(values[-24:],axis=0))>4: findings.append("no_final_read_hold")
    return dict(findings=findings,first_visible_seconds=arrivals,final_width_pixels=values[-1].tolist(),expected_width_pixels=expected.tolist())


def main():
    parser=argparse.ArgumentParser();parser.add_argument("output",type=Path);args=parser.parse_args()
    out=args.output.resolve()
    destination=out/"decoded-review.json"
    if destination.exists(): raise FileExistsError(destination)
    receipt=json.loads((out/"receipt.json").read_text())
    plan=json.loads((out/"prepared-plan.json").read_text())
    video=out/"delivery/preview.mp4"
    if sha256_file(video)!=receipt["video_sha256"]: raise ValueError("render_evidence_changed")
    scene=next(s for s in plan["scenes"] if (s["layout"]["hybrid"]["diagram"] or {}).get("grammar")=="quantitative_comparison")
    metadata=next(a for a in receipt["assets"] if a["scene_id"]==scene["id"])
    start,duration=metadata["start_seconds"],metadata["duration_seconds"]
    raw=subprocess.check_output(["ffmpeg","-v","error","-ss",str(start),"-i",str(video),"-t",str(duration),
        "-vf","scale=640:360","-pix_fmt","rgb24","-f","rawvideo","pipe:1"],timeout=120)
    frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,360,640,3)
    diagram=scene["layout"]["hybrid"]["diagram"];nodes=diagram["nodes"]
    expected=np.array([324*n["quantity"]/diagram["comparison_scale_max"] for n in nodes])
    starts=[n["change_at"]*duration for n in nodes]
    values=widths(frames,nodes)
    result=assess(values,expected,starts,24)
    controls={"frozen_initial":assess(np.repeat(values[:1],len(values),axis=0),expected,starts,24),
        "frozen_final":assess(np.repeat(values[-1:],len(values),axis=0),expected,starts,24),
        "reversed":assess(values[::-1],expected,starts,24),
        "wrong_quantity":assess(values,np.array(list(reversed(expected))),starts,24)}
    times=[2.5,start+.5,start+starts[0]+.6,start+starts[1]+.6,start+duration-1,receipt["assets"][-1]["start_seconds"]+2]
    sheet=Image.new("RGB",(1280,1152),"white");draw=ImageDraw.Draw(sheet)
    for i,time in enumerate(times):
        data=subprocess.check_output(["ffmpeg","-v","error","-ss",str(time),"-i",str(video),"-frames:v","1",
            "-vf","scale=640:360","-pix_fmt","rgb24","-f","rawvideo","pipe:1"],timeout=30)
        x,y=i%2*640,i//2*384
        sheet.paste(Image.frombytes("RGB",(640,360),data),(x,y))
        draw.text((x+8,y+364),f"Actual output frame: {time:.3f}s",fill="black")
    sheet.save(out/"decoded-contact-sheet.jpg")
    caption_windows=[dict(scene_id=s["id"],start=c["start"],end=c["end"],text=c["text"],
        minimum_seconds=max(1.2,len(c["text"])/8),actual_seconds=c["end"]-c["start"])
        for s in plan["scenes"] for c in s["layout"]["subtitle_cues"]]
    passed=not result["findings"] and all(c["findings"] for c in controls.values()) and all(c["actual_seconds"]>=c["minimum_seconds"] for c in caption_windows)
    atomic_json(destination,dict(status="DECODED_GEOMETRY_TIMING_PASS" if passed else "REVISE",video_sha256=sha256_file(video),
        native_fps=24,diagram_frames_decoded=len(frames),inspection_resolution=[640,360],comparison=result,negative_controls=controls,
        caption_windows=caption_windows,contact_sheet_sha256=sha256_file(out/"decoded-contact-sheet.jpg"),
        human_approval=None,production_ready=False,not_evaluated=["full_resolution_defects","OCR","human_voice_listening","emotion","independent_film_preference","held_out_transfer"]))
    print(json.dumps(dict(passed=passed,diagram_frames=len(frames),result=result,controls_rejected={k:bool(v["findings"]) for k,v in controls.items()})))
    if not passed: raise SystemExit(1)


if __name__=="__main__": main()
