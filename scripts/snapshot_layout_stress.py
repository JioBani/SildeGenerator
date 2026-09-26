"""Compile maximum permitted text lengths for font-box QA; not a film approval."""
import argparse
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'video-generator'))
sys.path.insert(0,str(ROOT/'harnesses/hybrid-story/src'))
from snapshot_pair_fixtures import cases
from app.harness_sdk.hybrid import HybridScene
from hybrid_story.hybrid_renderer import compile_project


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('output',type=Path)
    parser.add_argument('--layout',choices=['columns','rows','dot_tracks'],default='columns')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    payload=cases()[0]['hybrid']; d=payload['diagram']; p=d['snapshot_pair']
    if args.layout!='columns':
        payload['version']='hybrid-scene-0.6'
        payload['design'].update(version='film-design-0.2',snapshot_layout=args.layout)
    d['title']='가'*26; p.update(entity='나'*20,metric='다'*16,unit='라'*8,scale_max=100)
    for state,label,value in [(p['before'],'마'*12,0),(p['after'],'바'*12,99)]:
        state.update(time_label=label,value=value,source_quote=f'{label} {p["entity"]} {p["metric"]} {value}{p["unit"]}')
    payload['design']['typography'].update(title_px=38,caption_px=42,caption_margin_y=64)
    HybridScene.model_validate(payload)
    narration=p['before']['source_quote']+' '+p['after']['source_quote']
    scene=SimpleNamespace(id='stress',duration_seconds=15,narration=narration,layout={'hybrid':payload,'camera':{'mode':'hold'}})
    compile_project([scene],args.output,SimpleNamespace(width=1280,height=720,fps=24))


if __name__=='__main__': main()
