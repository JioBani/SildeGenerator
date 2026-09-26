"""Reviewed orange outer bands only; not a generic anatomical segmenter."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image


def boundaries(image, regions=None):
    a = np.asarray(image.convert('RGB'), dtype=float)
    if a.shape != (360, 640, 3):
        raise ValueError('Expected reviewed 640x360 frames')
    r,g,b = a[:,:,0],a[:,:,1],a[:,:,2]
    orange = (r>150)&(g>45)&(g>r*.25)&(g<r*.65)&(g<165)&(b<110)
    # Close only short horizontal texture gaps; retain vertical wall displacement.
    padded=np.pad(orange,((0,0),(6,6)),mode='edge')
    expanded=np.logical_or.reduce([padded[:,i:i+640] for i in range(13)])
    padded=np.pad(expanded,((0,0),(6,6)),mode='edge')
    orange=np.logical_and.reduce([padded[:,i:i+640] for i in range(13)])
    # Wall bands continue to the image edge; floating label pixels do not.
    connected=np.zeros_like(orange)
    queue=deque()
    for x in (0,639):
        for y in np.flatnonzero(orange[:,x]):
            connected[y,x]=True;queue.append((int(y),x))
    while queue:
        y,x=queue.popleft()
        for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0<=yy<360 and 0<=xx<640 and orange[yy,xx] and not connected[yy,xx]:
                connected[yy,xx]=True;queue.append((yy,xx))
    orange=connected
    profiles=[]
    for start,end,edge in (regions or [(35,170,'first'),(200,345,'last')]):
        points=[]
        for x in range(4,637,8):
            band=orange[start:end,max(0,x-2):min(640,x+3)]
            ys=np.flatnonzero(band.mean(axis=1)>=.55)
            if not len(ys):raise ValueError(f'Band missing at {x}/{start}')
            points.append([x,int(ys[0] if edge=='first' else ys[-1])+start])
        smooth=[[x,float(np.median([p[1] for p in points[max(0,i-1):i+2]]))] for i,(x,y) in enumerate(points)]
        profiles.append(smooth)
    return profiles


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--start',type=float,default=132)
    p.add_argument('--end',type=float,default=141)
    a=p.parse_args()
    if not 0<=a.start<a.end:p.error('Require ordered nonnegative window')
    if a.output.exists():p.error('Preserve previous output')
    data=json.loads(a.analysis.read_text(encoding='utf-8'));rows=[]
    for row in data['frames']:
        if not a.start<=row['source_second']<a.end:continue
        file=a.analysis.parent/'frames'/row['file']
        with Image.open(file) as image: upper,lower=boundaries(image)
        rows.append({'source_second':row['source_second'],'upper':upper,'lower':lower,
                     'frame_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    if not rows:raise ValueError('Empty source window')
    a.output.write_text(json.dumps({'source_sha256':data['source_sha256'],
        'scope':'Outer orange band, not lumen or anatomy','rows':rows}),encoding='utf-8')
    print(json.dumps({'frames':len(rows),'output':str(a.output)}))


if __name__=='__main__':main()
