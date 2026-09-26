"""Decode numeric diagrams using their bound data, not a fixed topic/color fixture.

This measures geometry and timing only. It does not approve meaning, typography,
artwork or the entire film. Output remains development evidence.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np


def geometry(diagram):
    nodes=diagram['nodes']; maximum=diagram['comparison_scale_max']
    if maximum<=0: raise ValueError('positive_scale_required')
    result=[]; total=0
    for i,node in enumerate(nodes):
        if diagram['grammar']=='quantitative_comparison':
            box=(245,165+i*250/max(1,len(nodes)-1),540*node['quantity']/maximum,36)
        elif diagram['grammar']=='cumulative_change':
            box=(100+800*total/maximum,200,800*node['quantity']/maximum,92)
            total+=node['quantity']
        else:
            raise ValueError('unsupported_numeric_grammar')
        result.append(box)
    return result


def observe(frames, diagram, duration, fps=24, *, snapshot_layout='columns'):
    if frames.ndim!=4 or frames.shape[-1]!=3 or not len(frames):
        raise ValueError('decoded_rgb_frames_required')
    height,width=frames.shape[1:3]
    scale=min(width/1000,height/600)
    offset_x=(width-1000*scale)/2; offset_y=(height-600*scale)/2
    if diagram['grammar']=='cumulative_change':
        return observe_accumulation(frames,diagram,duration,fps,scale,offset_x,offset_y)
    if diagram['grammar']=='before_after':
        if snapshot_layout in {'rows','dot_tracks'}:
            return observe_snapshot_tracks(frames,diagram['snapshot_pair'],duration,fps,scale,offset_x,offset_y,snapshot_layout)
        if snapshot_layout!='columns': raise ValueError('unknown_snapshot_layout')
        return observe_snapshots(frames,diagram['snapshot_pair'],duration,fps,scale,offset_x,offset_y)
    measured=[]; expected=[]
    for node,(x,y,w,h) in zip(diagram['nodes'],geometry(diagram)):
        # Each increment has its own spatial ROI, so repeated accents are valid.
        left=int(round(offset_x+x*scale)); right=min(width,int(round(offset_x+1000*scale)))
        top=int(round(offset_y+(y+4)*scale)); bottom=int(round(offset_y+(y+h-4)*scale))
        expected.append(w*scale)
        if w==0:
            measured.append(np.zeros(len(frames))); continue
        roi=frames[:,top:bottom,left:right].astype(np.float32)
        color=np.array([int(node['color'][i:i+2],16) for i in (1,3,5)])
        mask=np.linalg.norm(roi-color,axis=3)<36
        widths=[]
        for columns in mask.mean(axis=1)>.65:
            positions=np.flatnonzero(columns)
            if not len(positions) or positions[0]>3:
                widths.append(0); continue
            gaps=np.flatnonzero(np.diff(positions)>3)
            end=positions[gaps[0]] if len(gaps) else positions[-1]
            widths.append(end-positions[0]+1)
        measured.append(np.array(widths))
    values=np.array(measured).T
    findings=[]; arrivals=[]
    for i,(node,target) in enumerate(zip(diagram['nodes'],expected)):
        samples=np.flatnonzero(values[:,i]>max(1,target*.03))
        arrival=None if not len(samples) else int(samples[0])
        arrivals.append(None if arrival is None else arrival/fps)
        if target>2:
            if arrival is None or abs(arrival/fps-duration*node['change_at'])>max(.12,2/fps):
                findings.append(node['id']+':event_voice_timing_mismatch')
            if np.min(np.diff(values[:,i])) < -4:
                findings.append(node['id']+':unexpected_width_regression')
        if abs(values[-1,i]-target)>4:
            findings.append(node['id']+':wrong_final_quantity_geometry')
        hold=min(len(frames),max(1,int(fps*.4)))
        if np.ptp(values[-hold:,i])>4:
            findings.append(node['id']+':missing_final_hold')
    return dict(findings=findings,first_visible_seconds=arrivals,
        final_width_px=values[-1].tolist(),expected_width_px=expected)


def observe_snapshot_tracks(frames,pair,duration,fps,scale,offset_x,offset_y,layout):
    color=np.array([int(pair['color'][i:i+2],16) for i in (1,3,5)])
    findings=[]; observed=[]; targets=[]; arrivals=[]
    for j,name in enumerate(('before','after')):
        state=pair[name]; y=250+j*140
        left=round(offset_x+200*scale); right=round(offset_x+800*scale)
        top=round(offset_y+(y-10)*scale); bottom=round(offset_y+(y+10)*scale)
        roi=frames[:,top:bottom,left:right].astype(np.float32)
        masks=np.linalg.norm(roi-color,axis=3)<36
        values=[]; visible=[]
        for mask in masks:
            columns=np.flatnonzero(mask.mean(axis=0)>.65)
            visible.append(bool(len(columns)))
            if not len(columns): values.append(0); continue
            if layout=='rows':
                if abs(left+columns[0]-(offset_x+220*scale))>3:
                    findings.append(name+':zero_origin_displaced')
                values.append(columns[-1]-columns[0]+1)
            else:
                values.append(left+float(columns.mean()))
        values=np.array(values); visible=np.array(visible)
        target=560*scale*state['value']/pair['scale_max']
        if layout=='dot_tracks': target+=offset_x+220*scale
        targets.append(target); observed.append(float(values[-1]))
        events=np.flatnonzero(visible); arrival=float(events[0]/fps) if len(events) else None
        arrivals.append(arrival)
        has_mark=layout=='dot_tracks' or state['value']>0
        if has_mark and (arrival is None or not -.05<=arrival-duration*state['show_at']<=.3):
            findings.append(name+':event_voice_timing_mismatch')
        settled=min(len(values)-1,round((duration*state['show_at']+.3)*fps))
        if has_mark and (not np.all(visible[settled:]) or np.max(np.abs(values[settled:]-target))>3):
            findings.append(name+':snapshot_not_fixed_at_value')
        if abs(values[-1]-target)>3: findings.append(name+':wrong_snapshot_quantity_geometry')
    return dict(findings=sorted(set(findings)),snapshot_layout=layout,first_visible_seconds=arrivals,
        final_measurement_px=observed,expected_measurement_px=targets,
        measurement='bar_length' if layout=='rows' else 'dot_center_x',
        limitation='Pixel geometry and onset only; text, semantics and subjective readability need separate checks')


def observe_snapshots(frames,pair,duration,fps,scale,offset_x,offset_y):
    color=np.array([int(pair['color'][i:i+2],16) for i in (1,3,5)])
    findings=[]; heights=[]; arrivals=[]; expected=[]
    for j,name in enumerate(('before','after')):
        state=pair[name]; x=270+j*380
        region=frames[:,round(offset_y+219*scale):round(offset_y+420*scale),
            round(offset_x+(x-50)*scale):round(offset_x+(x+50)*scale)].astype(np.float32)
        mask=np.linalg.norm(region-color,axis=3)<36
        values=(mask.mean(axis=2)>.7).sum(axis=1)
        target=200*scale*state['value']/pair['scale_max']; expected.append(target)
        heights.append(int(values[-1]))
        visible=np.flatnonzero(values>2)
        arrival=float(visible[0]/fps) if len(visible) else None
        arrivals.append(arrival)
        # Opacity reveals need time to enter the color tolerance. Test a bounded
        # onset window, then require a retained stable measurement for each state.
        if target>2 and (arrival is None or not -.05<=arrival-duration*state['show_at']<=.3):
            findings.append(name+':event_voice_timing_mismatch')
        if abs(values[-1]-target)>3: findings.append(name+':wrong_snapshot_quantity_geometry')
        if len(values)>1 and np.min(np.diff(values)) < -3: findings.append(name+':snapshot_not_retained')
        settled=min(len(values)-1,round((duration*state['show_at']+.3)*fps))
        if abs(values[settled]-target)>3: findings.append(name+':snapshot_not_present_after_reveal')
    return dict(findings=findings,first_visible_seconds=arrivals,final_height_px=heights,expected_height_px=expected,
        limitation='Zero values have no bar geometry; zero-label visibility requires separate text inspection')


def observe_accumulation(frames,diagram,duration,fps,scale,offset_x,offset_y):
    # Adjacent identical accents have no visible boundary. Observe running totals
    # between events instead of inventing a separately observable layer edge.
    left=round(offset_x+100*scale)
    right=min(frames.shape[2],round(offset_x+980*scale))
    top=round(offset_y+204*scale); bottom=round(offset_y+288*scale)
    roi=frames[:,top:bottom,left:right].astype(np.float32)
    mask=np.zeros(roi.shape[:3],dtype=bool)
    for color in {n['color'] for n in diagram['nodes']}:
        rgb=np.array([int(color[i:i+2],16) for i in (1,3,5)])
        mask |= np.linalg.norm(roi-rgb,axis=3)<36
    widths=[]
    for columns in mask.mean(axis=1)>.65:
        positions=np.flatnonzero(columns)
        if not len(positions) or positions[0]>3:
            widths.append(0); continue
        gaps=np.flatnonzero(np.diff(positions)>3)
        end=positions[gaps[0]] if len(gaps) else positions[-1]
        widths.append(end+1)
    widths=np.array(widths)
    targets=np.cumsum([n['quantity'] for n in diagram['nodes']])*800*scale/diagram['comparison_scale_max']
    findings=[]; arrivals=[]; observed=[]; checkpoints=[]; previous=0
    for i,(node,target) in enumerate(zip(diagram['nodes'],targets)):
        samples=np.flatnonzero(widths>previous+max(2,(target-previous)*.03))
        arrival=None if not len(samples) else int(samples[0])/fps
        arrivals.append(arrival)
        if target-previous>2 and (arrival is None or abs(arrival-duration*node['change_at'])>max(.12,2/fps)):
            findings.append(node['id']+':event_voice_timing_mismatch')
        checkpoint=len(frames)-1 if i+1==len(targets) else min(len(frames)-1,max(0,int(duration*diagram['nodes'][i+1]['change_at']*fps)-1))
        checkpoints.append(checkpoint/fps); observed.append(int(widths[checkpoint]))
        if abs(widths[checkpoint]-target)>4:
            findings.append(node['id']+':wrong_cumulative_quantity_geometry')
        previous=target
    if len(widths)>1 and np.min(np.diff(widths)) < -4:
        findings.append('accumulation:unexpected_width_regression')
    hold=min(len(frames),max(1,int(fps*.4)))
    if np.ptp(widths[-hold:])>4:
        findings.append('accumulation:missing_final_hold')
    return dict(findings=findings,measurement_kind='cumulative_checkpoints_not_individual_layer_edges',
        first_visible_seconds=arrivals,checkpoint_seconds=checkpoints,
        cumulative_width_px=observed,expected_cumulative_width_px=targets.tolist(),
        final_total_width_px=int(widths[-1]))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('plan',type=Path); parser.add_argument('video',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--receipt-case',help='Use one exact case from a hash-bound rendered fixture receipt')
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    plan=json.loads(args.plan.read_text(encoding='utf-8'))
    if args.receipt_case:
        selected=[c for c in plan.get('cases',[]) if c['id']==args.receipt_case]
        if len(selected)!=1: raise ValueError('one_exact_receipt_case_required')
        case=selected[0]
        if case['video_sha256']!=hashlib.sha256(args.video.read_bytes()).hexdigest():
            raise ValueError('receipt_video_hash_mismatch')
        plan={'scenes':[dict(id=case['id'],duration_seconds=case['duration_seconds'],layout=case['layout'])]}
    reports=[]; cursor=0
    for scene in plan['scenes']:
        duration=scene['duration_seconds']; hybrid=scene['layout']['hybrid']
        diagram=hybrid.get('diagram')
        if diagram and diagram['grammar'] in {'quantitative_comparison','cumulative_change','before_after'}:
            raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(cursor),'-i',str(args.video),
                '-t',str(duration),'-vf','fps=24,scale=640:360','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],timeout=120)
            frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,360,640,3)
            layout=(hybrid.get('design') or {}).get('snapshot_layout','columns')
            result=observe(frames,diagram,duration,snapshot_layout=layout)
            negatives={
                'frozen_initial':observe(np.repeat(frames[:1],len(frames),axis=0),diagram,duration,snapshot_layout=layout),
                'frozen_final':observe(np.repeat(frames[-1:],len(frames),axis=0),diagram,duration,snapshot_layout=layout),
                'reversed':observe(frames[::-1],diagram,duration,snapshot_layout=layout),
            }
            reports.append(dict(scene_id=scene['id'],grammar=diagram['grammar'],start=cursor,
                duration=duration,decoded_frames=len(frames),positive=result,negative_controls=negatives))
        cursor+=duration
    passed=bool(reports) and all(not r['positive']['findings'] and all(v['findings'] for v in r['negative_controls'].values()) for r in reports)
    report=dict(status='NUMERIC_PIXEL_PASS' if passed else 'REVISE',goal_status='GOAL_NOT_MET',
        scope='Native-rate downsampled numeric geometry and planned/word-aligned event timing, not whole-film approval',
        video_sha256=hashlib.sha256(args.video.read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest(),results=reports,
        human_approval=None,production_ready=False,
        not_evaluated=['OCR','quantity_semantics','full_resolution_defects','actual_viewer_understanding','aesthetic_quality'])
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if not passed: raise SystemExit(1)


if __name__=='__main__': main()
