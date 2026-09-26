"""Reviewed inner wall and ochre cell rectangles; no biological interpretation."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from measure_wall_geometry import boundaries


def columns(image):
    a=np.asarray(image.convert('RGB'),dtype=float);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    mask=((r>130)&(r<225)&(g>70)&(g>r*.5)&(g<r*.8)&(b<60)).astype('uint8')
    mask[:215]=0;mask[290:]=0;mask[:,:120]=0;mask[:,520:]=0
    count,labels,stats,centers=cv2.connectedComponentsWithStats(mask,8)
    return sorted([{'x':int(x),'y':int(y),'width':int(w),'height':int(h)} for x,y,w,h,area in stats[1:]
                   if 3<=w<=30 and 2<=h<=70 and area>=6],key=lambda p:p['x'])


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():p.error('Preserve previous output')
    source=json.loads(a.analysis.read_text(encoding='utf-8'));rows=[]
    for frame in source['frames']:
        file=a.analysis.parent/'frames'/frame['file']
        with Image.open(file) as im:
            inner=boundaries(im,[(175,330,'first')])[0];cells=columns(im)
        rows.append({'source_second':frame['source_second'],'inner':inner,'columns':cells,
                     'frame_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    a.output.write_text(json.dumps({'source_sha256':source['source_sha256'],'scope':'Scene-specific color/topology measurements','rows':rows}),encoding='utf-8')
    print(json.dumps({'frames':len(rows),'max_columns':max(len(r['columns']) for r in rows)}))


if __name__=='__main__':main()
