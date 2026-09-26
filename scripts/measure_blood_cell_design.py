"""Describe isolated dark silhouettes in a fixed study ROI; not biological analysis."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def measure(image):
    image=cv2.resize(image,(640,360))
    b,g,r=image.transpose(2,0,1)
    mask=((r>80)&(r<190)&(g<50)&(b<40)).astype('uint8')
    # Upstream channel at the initial wide state. Reject objects touching the crop.
    crop=mask[163:213,40:250]
    count,labels,stats,centers=cv2.connectedComponentsWithStats(crop,8)
    objects=[]
    for label in range(1,count):
        x,y,w,h,area=map(int,stats[label])
        if area<35 or x==0 or y==0 or x+w>=crop.shape[1] or y+h>=crop.shape[0]:
            continue
        # Fill internal decorative holes before comparing silhouette coverage.
        component=(labels==label).astype('uint8')
        contours,_=cv2.findContours(component,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        contour=max(contours,key=cv2.contourArea)
        filled=np.zeros_like(component)
        cv2.drawContours(filled,[contour],-1,1,-1)
        objects.append({'x':x+40,'y':y+163,'width':w,'height':h,
                        'filled_area':int(filled.sum()),'box_fill':float(filled.sum()/(w*h))})
    summary={key:float(np.median([o[key] for o in objects])) if objects else None
             for key in ('width','height','filled_area','box_fill')}
    return {'count':len(objects),'median':summary,'objects':objects}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('report',type=Path)
    args=p.parse_args()
    if args.report.exists():raise ValueError('Preserve previous report')
    result={'scope':'Initial upstream ROI only. Thresholded isolated silhouettes, not persistent identities or automatic quality approval.'}
    for name in ('source','candidate'):
        image=cv2.imread(str(getattr(args,name)))
        if image is None:raise ValueError('Missing image')
        result[name]=measure(image)
    args.report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:{'count':v['count'],'median':v['median']} for k,v in result.items() if k!='scope'}))


if __name__=='__main__':main()
