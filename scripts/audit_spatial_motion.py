"""Independent decoded-pixel checks for relative places, not script truth approval."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np


def observe(frames,spatial,duration,fps=24,line_color=None):
    height,width=frames.shape[1:3]
    scale=min(width/1000,height/600)
    ox,oy=(width-1000*scale)/2,(height-600*scale)/2
    findings=[]; observed={}; measured=[]; borders=[]
    for place in spatial['places']:
        ex=ox+(130+place['x']*740)*scale; ey=oy+(150+place['y']*280)*scale
        x0,x1=max(0,int(ex-18*scale)),min(width,int(ex+18*scale)+1)
        y0,y1=max(0,int(ey-18*scale)),min(height,int(ey+18*scale)+1)
        color=np.array([int(place['color'][i:i+2],16) for i in (1,3,5)])
        distance=np.linalg.norm(frames[:,y0:y1,x0:x1].astype(np.float32)-color,axis=3)
        mask=distance<38
        count=mask.sum(axis=(1,2))
        threshold=max(5,3.1416*(9*scale)**2)
        visible=np.flatnonzero(count>=threshold)
        first=None if not len(visible) else visible[0]/fps
        target=duration*place['reveal_at']
        if first is None or not .0 <= first-target <= .35:
            findings.append(place['id']+':reveal_time_or_missing_marker')
        stable=max(0,int((target+.4)*fps))
        centers=[]
        for index in range(stable,len(frames)-1):
            ys,xs=np.where(mask[index])
            if len(xs)<threshold:
                findings.append(place['id']+':reference_not_retained'); break
            centers.append((float(xs.mean()+x0),float(ys.mean()+y0)))
        center=None
        if centers:
            center=np.median(centers,axis=0)
            if np.linalg.norm(center-[ex,ey])>2.5 or np.ptp(np.array(centers),axis=0).max()>2:
                findings.append(place['id']+':wrong_or_moving_location')
            observed[place['id']]=center
        measured.append(dict(id=place['id'],expected_xy=[ex,ey],observed_xy=None if center is None else center.tolist(),first_visible=first))
    regions={r['id']:r for r in spatial['regions']}
    if regions and line_color:
        color=np.array([int(line_color[i:i+2],16) for i in (1,3,5)])
        for region in regions.values():
            left=round(ox+(130+740*region['left'])*scale); right=round(ox+(130+740*region['right'])*scale)
            top=round(oy+(150+280*region['top'])*scale); bottom=round(oy+(150+280*region['bottom'])*scale)
            start=min(len(frames)-2,round((duration*region['reveal_at']+.4)*fps))
            for label,roi in [('top',frames[start:-1,top-2:top+3,left:right]),('bottom',frames[start:-1,bottom-2:bottom+3,left:right]),
                              ('left',frames[start:-1,top:bottom,left-2:left+3]),('right',frames[start:-1,top:bottom,right-2:right+3])]:
                # Dashed borders encode extent by length, not by ink area. Taking
                # the cross-stroke maximum avoids bias from subpixel thickness.
                mask=np.linalg.norm(roi.astype(np.float32)-color,axis=3)<38
                fraction=mask.any(axis=1 if label in {'top','bottom'} else 2).mean(axis=1)
                borders.append(dict(region=region['id'],edge=label,minimum=float(fraction.min()) if len(fraction) else None,maximum=float(fraction.max()) if len(fraction) else None,minimum_frame=start+int(fraction.argmin()) if len(fraction) else None))
                if not len(fraction) or fraction.min()<.35:
                    findings.append(region['id']+':region_boundary_missing_'+label)
    for relation in spatial['relations']:
        a=observed.get(relation['subject']); b=observed.get(relation['target'])
        kind=relation['relation']
        valid=a is not None
        if valid and kind in {'inside','outside'}:
            r=regions[relation['target']]
            inside=ox+(130+740*r['left'])*scale<a[0]<ox+(130+740*r['right'])*scale and oy+(150+280*r['top'])*scale<a[1]<oy+(150+280*r['bottom'])*scale
            valid=inside if kind=='inside' else not inside
        elif valid:
            valid=b is not None
            if valid:
                valid={'north_of':a[1]<b[1], 'south_of':a[1]>b[1], 'east_of':a[0]>b[0], 'west_of':a[0]<b[0]}[kind]
        if not valid: findings.append(relation['subject']+':rendered_relation_wrong_or_unobservable')
    return dict(findings=sorted(set(findings)),places=measured,borders=borders,
        scope='Decoded fixed marker geometry, reveal and retention; all four region borders when line color is supplied. Not script truth or typography approval')


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('output',type=Path); parser.add_argument('--report-name',default='spatial-pixel-audit.json'); args=parser.parse_args()
    if Path(args.report_name).name!=args.report_name or not args.report_name.endswith('.json'): raise ValueError('report_filename_required')
    receipt=json.loads((args.output/'receipt.json').read_text(encoding='utf-8'))
    results=[]
    for case in receipt['cases']:
        video=args.output/case['id']/'delivery/preview.mp4'
        if hashlib.sha256(video.read_bytes()).hexdigest()!=case['video_sha256']: raise ValueError('video_evidence_changed')
        raw=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vf','scale=640:360','-pix_fmt','rgb24','-f','rawvideo','-'],check=True,capture_output=True).stdout
        frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,360,640,3)
        spatial=case['layout']['hybrid']['diagram']['spatial_map']; duration=case['duration_seconds']
        line=case['layout']['hybrid']['design']['palette']['line']
        actual=observe(frames,spatial,duration,line_color=line)
        controls={}
        for kind,bad in [('mirrored',frames[:,:,::-1]),('vertical_flip',frames[:,::-1]),('frozen_end',np.broadcast_to(frames[-3],frames.shape)),('reversed_time',frames[::-1])]:
            controls[kind]=bool(observe(bad,spatial,duration,line_color=line)['findings'])
        if spatial['regions']:
            region=spatial['regions'][0]
            top=round((150+280*region['top'])*.6); bottom=round((150+280*region['bottom'])*.6)
            left=round(20+(130+740*region['left'])*.6); right=round(20+(130+740*region['right'])*.6)
            for side,(y0,y1,x0,x1) in {'top':(top-4,top+5,left,right),'bottom':(bottom-4,bottom+5,left,right),
                                     'left':(top,bottom,left-4,left+5),'right':(top,bottom,right-4,right+5)}.items():
                bad=frames.copy(); bad[:,y0:y1,x0:x1]=0
                controls['missing_region_'+side]=bool(observe(bad,spatial,duration,line_color=line)['findings'])
        results.append(dict(id=case['id'],video_sha256=case['video_sha256'],frames=len(frames),actual=actual,negative_controls=controls))
    passed=all(not c['actual']['findings'] and all(c['negative_controls'].values()) for c in results)
    report=dict(status='PIXEL_GEOMETRY_PASS' if passed else 'REVISE',cases=results,goal_status='GOAL_NOT_MET',human_approval=None,
        scope='Three authored development scripts, not unseen director transfer or aesthetic validation')
    target=args.output/args.report_name
    with target.open('x',encoding='utf-8') as file: json.dump(report,file,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False))
    if not passed: raise SystemExit(1)


if __name__=='__main__': main()
