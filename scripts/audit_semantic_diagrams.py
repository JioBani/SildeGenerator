"""Known-fixture measurements on decoded output, not a general semantic critic."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

COLORS = [(40,120,135),(185,77,72),(121,98,44)]


def masks(frame):
    pixels=frame.astype(float)
    return [np.linalg.norm(pixels-np.array(color),axis=2)<42 for color in COLORS]


def observe(frames,kind):
    measurements=[]
    for frame in frames:
        row=[]
        for j,mask in enumerate(masks(frame)):
            if kind=="comparison":
                y=int((165+j*125)*.6)
                region=mask[y+3:y+18,166:570]
                row.append(float(np.count_nonzero(region.mean(axis=0)>.7)))
            elif kind=="accumulation":
                region=mask[125:170,78:563]
                row.append(float(np.count_nonzero(region.mean(axis=0)>.7)))
            else:
                x=int(20+(140+j*360)*.6)
                region=mask[120:176,x-28:x+29]
                row.append(float(region.sum()))
        measurements.append(row)
    values=np.array(measurements)
    findings=[]
    expected={"comparison":[108,189,270],"accumulation":[96,144,240]}.get(kind)
    if np.max(values[0])>3: findings.append("missing_initial_hold")
    if expected is not None and np.max(np.abs(values[-1]-expected))>4:
        findings.append("wrong_final_quantity_geometry")
    if kind=="procedure" and np.min(values[-1])<200: findings.append("missing_completed_steps")
    threshold=10 if kind!="procedure" else 100
    arrivals=[next((i for i,v in enumerate(values[:,j]) if v>threshold),None) for j in range(3)]
    if any(v is None for v in arrivals) or not all(a<b for a,b in zip(arrivals,arrivals[1:]) if a is not None and b is not None):
        findings.append("missing_or_reversed_event_order")
    if np.min(np.diff(values,axis=0)) < (-4 if kind!="procedure" else -40): findings.append("unexpected_regression")
    if np.max(np.ptp(values[-6:],axis=0))>4: findings.append("missing_final_hold")
    return dict(findings=findings,first_visible_sample=arrivals,final_measurements=values[-1].tolist())


def main():
    parser=argparse.ArgumentParser();parser.add_argument("output",type=Path);args=parser.parse_args()
    reports=[]
    for kind in ("comparison","accumulation","procedure"):
        path=args.output/kind/"delivery/preview.mp4"
        raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-vf","fps=6,scale=640:360","-pix_fmt","rgb24","-f","rawvideo","pipe:1"],timeout=90)
        frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,360,640,3)
        result=observe(frames,kind)
        negatives={"frozen_early":observe(np.repeat(frames[:1],len(frames),axis=0),kind),
            "frozen_final":observe(np.repeat(frames[-1:],len(frames),axis=0),kind),
            "reversed":observe(frames[::-1],kind)}
        sheet=Image.new("RGB",(1280,770),"white")
        draw=ImageDraw.Draw(sheet)
        for j,fraction in enumerate((.05,.30,.55,.90)):
            sample=min(len(frames)-1,int(len(frames)*fraction))
            x,y=(j%2)*640,(j//2)*385
            sheet.paste(Image.fromarray(frames[sample]),(x,y))
            draw.text((x+8,y+362),f"{kind} | {sample/6:.2f}s",fill="black")
        sheet.save(args.output/kind/"decoded-frames.jpg")
        reports.append(dict(id=kind,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),samples=len(frames),observations=result,negative_controls=negatives))
    passed=all(not r["observations"]["findings"] and all(n["findings"] for n in r["negative_controls"].values()) for r in reports)
    report=dict(status="FIXTURE_TECHNICAL_PASS" if passed else "REVISE",scope="Known three-script fixture only; 6fps decoded geometry, not full-frame semantic, OCR or voice timing acceptance",results=reports,
        not_evaluated=["unseen_script_selection","narration_event_alignment","independent_story_comprehension","emotional_quality","full_frame_defects"],human_approval=None)
    (args.output/"geometry-review.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    if not passed: raise SystemExit(1)


if __name__=="__main__": main()
