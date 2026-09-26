"""Compile a narrated-excerpt visual comparison using the private transport harness."""
import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'harnesses/astra-transport-lab/src'))
from astra_transport_lab import renderer


def scene(mode,duration,image):
    states=[];motion=[]
    for i in range(1 if mode=='DEMO' else 6):
        name=f'job{i+1}';expression=f'{i+1} x 3';y=.50 if mode=='DEMO' else .30+i*.08
        if mode=='CPU' and i>=2:
            states.append({'object_id':name,'role':'token','label':expression})
            motion.append({'object_id':name,'kind':'transport_track','points':[
                {'time':0,'x':.18,'y':y},{'time':duration,'x':.18,'y':y}]})
            continue
        begin=.30+i*1.40 if mode=='CPU' else .50 if mode=='DEMO' else .30
        arrive=begin+.30 if mode=='CPU' else 2.0 if mode=='DEMO' else 1.0
        complete=begin+.80 if mode=='CPU' else 3.5 if mode=='DEMO' else 2.5
        end=begin+1.10 if mode=='CPU' else 5.0 if mode=='DEMO' else 3.5
        states.append({'object_id':name,'role':'token','label':expression,'performance_states':[
            {'time':arrive,'state':'processing','label':expression},
            {'time':complete,'state':'complete','label':str((i+1)*3)}]})
        motion.append({'object_id':name,'kind':'transport_track','points':[
            {'time':0,'x':.18,'y':y},{'time':begin,'x':.18,'y':y},
            {'time':arrive,'x':.5,'y':y},{'time':complete,'x':.5,'y':y},
            {'time':end,'x':.82,'y':y}]})
    label='하나씩 처리' if mode=='CPU' else '계산' if mode=='DEMO' else '동시에 처리'
    return SimpleNamespace(id=mode.lower(),duration_seconds=duration,scene_function='compare',
        viewer_takeaway='하나의 계산: 입력에서 결과까지' if mode=='DEMO' else f'{mode}: {label}',
        narration='처리 방식의 개념도이며 실제 속도 비율이 아닙니다.',
        image_path=str(image),object_states=states,motion=motion,layout={'mode':'process','columns':[
            {'x':.18,'label':'입력'},{'x':.5,'label':label},{'x':.82,'label':'결과'}]})


def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('runtime',type=Path)
    p.add_argument('--token-size',choices=('compact','readable'),default='compact')
    a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve prior output')
    a.output.mkdir(parents=True)
    image=a.output/'background.png';Image.new('RGB',(1920,1080),(242,246,245)).save(image)
    renderer.RUNTIME=a.runtime
    scenes=[scene('DEMO',6.913197,image),scene('CPU',3.508934,image),scene('GPU',475/30-10.422131,image)]
    for item in scenes:item.layout['token_size']=a.token_size
    renderer.compile_project(scenes,
        a.output/'project',SimpleNamespace(width=1920,height=1080,fps=30))


if __name__=='__main__':main()
