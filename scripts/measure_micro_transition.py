"""Track reviewed full-height teal panel columns, not arbitrary semantic scenes."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def bounds(image, axis=0):
    a=np.asarray(image.convert('RGB'),dtype=float)
    if a.shape != (360,640,3):raise ValueError('Expected reviewed 640x360 frames')
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    mask=(g>r*1.3)&(b>r*1.2)&(g>60)
    columns=np.flatnonzero(mask.mean(axis=axis)>.65)
    if not len(columns):return None
    # Reject isolated green props rather than joining unrelated regions.
    runs=np.split(columns,np.flatnonzero(np.diff(columns)>1)+1)
    run=max(runs,key=len)
    if len(run)<8:return None
    return [int(run[0]),int(run[-1]+1)]


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():p.error('Preserve previous evidence; choose new output')
    source=json.loads(a.analysis.read_text(encoding='utf-8'))
    rows=[]
    for row in source['frames']:
        if not 101<=row['source_second']<=110:continue
        file=a.analysis.parent/'frames'/row['file']
        with Image.open(file) as im: box=bounds(im); vertical=bounds(im,axis=1)
        rows.append({'source_second':row['source_second'],'bounds':box,'vertical_bounds':vertical,'file':row['file'],
                     'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    visible=[r for r in rows if r['bounds']]
    full=[r for r in visible if r['bounds'][1]-r['bounds'][0]>=632]
    if not visible or not full:raise ValueError('No reviewed full-panel event')
    report={'source_sha256':source['source_sha256'],'analysis_sha256':hashlib.sha256(a.analysis.read_bytes()).hexdigest(),
            'scope':'Teal panel column coverage only; color-specific, not a scene recognizer',
            'first_visible':visible[0]['source_second'],'first_full':full[0]['source_second'],
            'last_full':full[-1]['source_second'],'last_visible':visible[-1]['source_second'],'rows':rows}
    a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__=='__main__':main()
