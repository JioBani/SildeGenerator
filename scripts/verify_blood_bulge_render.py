"""Raster checks at two visible-fluid states; not whole-motion approval."""
import argparse
import json
from pathlib import Path
import cv2
from measure_blood_bulge import lumen_support


def main():
    p=argparse.ArgumentParser()
    p.add_argument('video',type=Path);p.add_argument('track',type=Path);p.add_argument('report',type=Path)
    args=p.parse_args()
    if args.report.exists():
        raise ValueError('Preserve previous report')
    source=json.loads(args.track.read_text(encoding='utf-8'))['rows']
    cap=cv2.VideoCapture(str(args.video));rows=[]
    try:
        for frame in [0,120]:
            cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,image=cap.read()
            if not ok:
                raise ValueError('Missing rendered frame')
            observed=next(p for p in lumen_support(cv2.resize(image,(640,360))) if p[0]==320)
            time=source[0]['source_second']+frame/30
            row=max((r for r in source if r['source_second']<=time),key=lambda r:r['source_second'])
            expected=next(p for p in row['lumen_support'] if p[0]==320)
            residual=max(abs(a-b) for a,b in zip(observed[1:],expected[1:]))
            rows.append({'frame':frame,'observed':observed,'expected':expected,'max_edge_error':residual})
    finally:
        cap.release()
    narrowed=(rows[1]['observed'][2]-rows[1]['observed'][1])<(rows[0]['observed'][2]-rows[0]['observed'][1])
    result={'pass':narrowed and all(r['max_edge_error']<=4 for r in rows),'rows':rows,
        'scope':'Two center-column bright-fluid observations. Particle occlusion, other columns, texture and clinical claims are not validated.'}
    args.report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
    raise SystemExit(0 if result['pass'] else 1)


if __name__=='__main__':
    main()
