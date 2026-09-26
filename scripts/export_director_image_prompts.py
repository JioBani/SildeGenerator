"""Export the Core's exact cinematic prompts for explicit builtin-image experiments."""
import argparse
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'video-generator'))
from app.models import ScenePlan
from app.image_prompts import scene_image_prompt
from app.prompts import load_prompts
from app.tracking import atomic_json, sha256_file


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('plan',type=Path); parser.add_argument('output',type=Path)
    args=parser.parse_args()
    plan=ScenePlan.model_validate_json(args.plan.read_text(encoding='utf-8'))
    prompts,_=load_prompts(ROOT/'harnesses/hybrid-story/prompts')
    args.output.mkdir(parents=True,exist_ok=False)
    entries=[]
    for scene in plan.scenes:
        if scene.layout['hybrid']['route']!='cinematic': continue
        if not re.fullmatch(r'scene-[0-9]{3}',scene.id): raise ValueError('unsafe_scene_id')
        references=[a for a in plan.continuity_assets if a.asset_id in scene.reference_asset_ids]
        prompt=scene_image_prompt(scene,references,prompts,plan.style_bible)
        path=args.output/(scene.id+'.prompt.txt'); path.write_text(prompt,encoding='utf-8')
        entries.append(dict(scene_id=scene.id,prompt_file=path.name,prompt_sha256=sha256_file(path),
            target_image=scene.id+'.png',route='cinematic',reference_asset_ids=scene.reference_asset_ids))
    atomic_json(args.output/'generation-plan.json',dict(version='builtin-director-assets-0.1',
        plan_sha256=sha256_file(args.plan),images=entries,source='Core scene_image_prompt; no agent-authored scene replacement',
        status='PROMPTS_EXPORTED_NOT_IMAGES_GENERATED',human_approval=None))
    print(json.dumps(entries,ensure_ascii=False))


if __name__=='__main__': main()
