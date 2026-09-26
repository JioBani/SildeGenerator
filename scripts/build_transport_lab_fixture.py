"""Offline compiler-route transfer fixture; not a finished narrated GPU film."""
import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'harnesses/astra-transport-lab/src'))
from astra_transport_lab import renderer


def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('runtime',type=Path)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve prior fixture')
    a.output.mkdir(parents=True)
    background=a.output/'background.png'
    Image.new('RGB',(1920,1080),(30,48,51)).save(background)
    states=[];motion=[]
    for i in range(6):
        name=f'job{i+1}'
        expression=f'{i+1} x 3'
        states.append({'object_id':name,'role':'token','label':expression,'performance_states':[
            {'time':1.5,'state':'processing','label':expression},
            {'time':2.5,'state':'complete','label':str((i+1)*3)}]})
        motion.append({'object_id':name,'kind':'transport_track','points':[
            {'time':.5,'x':.18,'y':.30+i*.08},
            {'time':1.5,'x':.50,'y':.30+i*.08},
            {'time':2.5,'x':.50,'y':.30+i*.08},
            {'time':3.2,'x':.82,'y':.30+i*.08}]})
    scene=SimpleNamespace(id='gpu',duration_seconds=4,scene_function='parallel_processing',
        viewer_takeaway='여섯 개의 계산을 동시에 처리합니다',narration='',image_path=str(background),
        object_states=states,motion=motion,layout={'mode':'process','columns':[
            {'x':.18,'label':'입력'},{'x':.5,'label':'병렬 계산'},{'x':.82,'label':'결과'}]})
    renderer.RUNTIME=a.runtime
    renderer.compile_project([scene],a.output/'project',SimpleNamespace(width=1920,height=1080,fps=30))


if __name__=='__main__':main()
