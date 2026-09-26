"""Track visible orange wall bands; not anatomical or medical segmentation."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np


def measure(image):
    if image.shape[:2] != (360,640):
        raise ValueError('Expected 640x360 source evidence')
    b,g,r = image.astype(float).transpose(2,0,1)
    orange = (r>100)&(g>30)&(g<145)&(b<105)&(r>1.4*g)&(g>.23*r)&(b>.6*g)
    result = {}
    for name, lo, hi in [('upper',80,160),('lower',210,285)]:
        points=[]
        for x in range(10,631,10):
            support=orange[lo:hi,x-4:x+5].sum(axis=1)
            ys=np.flatnonzero(support>=5)
            if len(ys)<4:
                continue
            runs=np.split(ys,np.flatnonzero(np.diff(ys)>1)+1)
            runs=sorted(runs,key=len,reverse=True)
            if len(runs[0])<4 or (len(runs)>1 and len(runs[0])==len(runs[1])):
                continue
            band=runs[0]
            points.append([x,int(lo+band.min()),int(lo+band.max())])
        result[name]=points
    return result


def lumen_support(image):
    if image.shape[:2] != (360,640):
        raise ValueError('Expected 640x360 source evidence')
    b,g,r=image.astype(float).transpose(2,0,1)
    bright=(r>130)&(g>30)&(g<95)&(b>10)&(b<65)&(g>.22*r)&(g<.35*r)&(b>.35*g)&(b<.8*g)
    points=[]
    for x in range(10,631,10):
        support=bright[150:224,x-4:x+5].sum(axis=1)>=5
        adjacent=np.flatnonzero(support[:-1]&support[1:])
        if not len(adjacent):
            continue
        points.append([x,int(150+adjacent.min()),int(151+adjacent.max())])
    return points


def main():
    p=argparse.ArgumentParser()
    p.add_argument('analysis',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args()
    if args.output.exists():
        raise ValueError('Preserve previous evidence')
    source=json.loads(args.analysis.read_text(encoding='utf-8'))
    rows=[]
    for frame in source['frames']:
        if not 116<=frame['source_second']<=123:
            continue
        image=cv2.imread(str(args.analysis.parent/'frames'/frame['file']))
        if image is None:
            raise ValueError('Missing source frame')
        rows.append({'source_second':frame['source_second'],'file':frame['file'],**measure(image),'lumen_support':lumen_support(image)})
    result={'source_sha256':source['source_sha256'],'rows':rows,
        'limitations':'Color-band and bright-fluid support extrema, not anatomical surfaces. Particles can occlude fluid support; inferred contour between samples is authoring only. No medical validation.'}
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    for row in rows[::24]:
        print(json.dumps({'time':row['source_second'],'upper270':next((p for p in row['upper'] if p[0]==270),None),'lower270':next((p for p in row['lower'] if p[0]==270),None)}))
    print(json.dumps({'frames':len(rows)}))


if __name__=='__main__':
    main()
