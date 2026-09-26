"""Circle-fit visual coverage, intentionally independent of temporal identity."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def shapes(image):
    a=np.asarray(image.convert('RGB'),dtype=float)
    if a.shape!=(360,640,3):raise ValueError('Expected reviewed frame size')
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    mask=((r>155)&(g>140)&(b>75)&(b>r*.35)&(g>r*.7)).astype('uint8')
    mask[:130]=0;mask[250:]=0
    distance=cv2.distanceTransform(mask,cv2.DIST_L2,5)
    peaks=((distance>=4)&(distance>=cv2.dilate(distance,np.ones((9,9),np.uint8))-.01)).astype('uint8')
    count,labels,stats,centers=cv2.connectedComponentsWithStats(peaks,8)
    disks=[]
    for i in range(1,count):
        x,y=centers[i];xx,yy=int(round(x)),int(round(y));radius=float(distance[yy,xx])
        if not 4<=radius<=10:continue
        color=[int(v) for v in a[yy,xx]]
        disks.append({'x':float(x),'y':float(y),'radius':radius,'fill':'#'+''.join(f'{v:02x}' for v in color)})
    return sorted(disks,key=lambda d:(d['x'],d['y']))


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():p.error('Preserve prior output')
    source=json.loads(a.analysis.read_text(encoding='utf-8'));rows=[]
    for frame in source['frames']:
        if frame['source_second']<146:continue
        file=a.analysis.parent/'frames'/frame['file']
        with Image.open(file) as im:disks=shapes(im)
        rows.append({'source_second':frame['source_second'],'shapes':disks,'frame_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    a.output.write_text(json.dumps({'source_sha256':source['source_sha256'],'opencv_version':cv2.__version__,
        'scope':'Per-frame fitted circles; no identity, particle count truth or contact approval','rows':rows},indent=2),encoding='utf-8')
    print(json.dumps({'frames':len(rows),'max_shapes':max(len(r['shapes']) for r in rows)}))


if __name__=='__main__':main()
