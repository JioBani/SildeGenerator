"""Reviewed yellow deposit envelope; does not identify cells or diagnose disease."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image


def envelope(image):
    a=np.asarray(image.convert('RGB'),dtype=float)
    if a.shape!=(360,640,3):raise ValueError('Expected reviewed 640x360 frame')
    roi=a[200:320,90:550]
    r,g,b=roi[:,:,0],roi[:,:,1],roi[:,:,2]
    mask=(r>175)&(g>125)&(b<80)&(g>r*.58)
    selected=np.zeros_like(mask);queue=deque()
    for y,x in zip(*np.where(mask[45:66,200:241])):
        y,x=int(y)+45,int(x)+200;selected[y,x]=True;queue.append((y,x))
    while queue:
        y,x=queue.popleft()
        for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0<=yy<120 and 0<=xx<460 and mask[yy,xx] and not selected[yy,xx]:
                selected[yy,xx]=True;queue.append((yy,xx))
    ys,xs=np.where(selected)
    if len(xs)<4:return None
    if xs.min()==0 or xs.max()==459 or ys.min()==0 or ys.max()==119:
        raise ValueError('Deposit touches ROI boundary; measurement is censored')
    return {'bounds':[int(xs.min())+90,int(ys.min())+200,int(xs.max())+91,int(ys.max())+201],
            'colored_pixels':int(len(xs))}


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():p.error('Preserve prior measurement')
    data=json.loads(a.analysis.read_text(encoding='utf-8'));rows=[]
    for frame in data['frames']:
        file=a.analysis.parent/'frames'/frame['file']
        with Image.open(file) as im:
            try:box=envelope(im)
            except ValueError as exc:raise ValueError(f"{frame['source_second']}: {exc}") from exc
        rows.append({'source_second':frame['source_second'],'envelope':box,'file':frame['file'],
                     'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    visible=[r for r in rows if r['envelope']]
    if not visible:raise ValueError('No yellow deposit in reviewed ROI')
    report={'source_sha256':data['source_sha256'],
            'analysis_sha256':hashlib.sha256(a.analysis.read_bytes()).hexdigest(),
            'scope':'Yellow pixel envelope, not total material area, contact or individual particle tracking',
            'first_detected':visible[0]['source_second'],'last_detected':visible[-1]['source_second'],
            'first_bounds':visible[0]['envelope']['bounds'],'last_bounds':visible[-1]['envelope']['bounds'],
            'rows':rows,'human_approved':False,'production_promotion':False}
    a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__=='__main__':main()
