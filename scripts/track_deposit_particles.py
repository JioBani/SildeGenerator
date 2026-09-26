"""Conservative adjacent-frame tracks for reviewed light circular symbols."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def detect(image):
    a=np.asarray(image.convert('RGB'),dtype=float)
    if a.shape!=(360,640,3):raise ValueError('Expected reviewed 640x360 frame')
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    mask=(r>155)&(g>140)&(b>75)&(b>r*.35)&(g>r*.7)
    mask[:130]=False;mask[250:]=False
    pending=set(zip(*np.where(mask)));result=[]
    while pending:
        origin=pending.pop();queue=deque([origin]);points=[origin]
        while queue:
            y,x=queue.popleft()
            for q in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if q in pending:pending.remove(q);queue.append(q);points.append(q)
        ys,xs=np.array(points).T;w=int(xs.max()-xs.min()+1);h=int(ys.max()-ys.min()+1)
        # Merged or clipped shapes are intentionally not split into invented identities.
        if 75<=len(points)<=230 and 10<=w<=19 and 10<=h<=19 and .75<=w/h<=1.33:
            result.append({'x':float(xs.mean()),'y':float(ys.mean()),'area':len(points)})
    return sorted(result,key=lambda p:p['x'])


def associate(previous,current,limit=10):
    choices=[[j for j,b in enumerate(current) if (a['x']-b['x'])**2+(a['y']-b['y'])**2<=limit**2] for a in previous]
    links={}
    for i,js in enumerate(choices):
        if len(js)==1 and sum(js[0] in other for other in choices)==1:links[js[0]]=i
    return links


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():p.error('Preserve prior evidence')
    data=json.loads(a.analysis.read_text(encoding='utf-8'));tracks=[];previous=[];ids=[];rows=[]
    for frame in data['frames']:
        if frame['source_second']<146:continue
        file=a.analysis.parent/'frames'/frame['file']
        with Image.open(file) as im:current=detect(im)
        links=associate(previous,current);next_ids=[]
        for j,point in enumerate(current):
            if j in links:ident=ids[links[j]]
            else:ident=len(tracks);tracks.append({'id':ident,'samples':[]})
            tracks[ident]['samples'].append({'source_second':frame['source_second'],**point});next_ids.append(ident)
        rows.append({'source_second':frame['source_second'],'detections':current,'track_ids':next_ids,
                     'frame_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
        previous,ids=current,next_ids
    report={'source_sha256':data['source_sha256'],'scope':'Adjacent unique-neighbor association; not identity, contact or retained-object approval',
            'tracks':tracks,'rows':rows,'human_approved':False}
    a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'tracks':len(tracks),'tracks_at_least_24_samples':sum(len(t['samples'])>=24 for t in tracks),'frames':len(rows)}))


if __name__=='__main__':main()
