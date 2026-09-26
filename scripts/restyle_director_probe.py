"""Controlled design-only render; explicit reused inputs, no new-director claim."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'video-generator'))
from app.models import ScenePlan
from app.harness_sdk.film_design import FilmDesign, design_sha256
from app.harness_sdk.hybrid import evaluate_hybrid
from app.tracking import atomic_json, sha256_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('baseline', type=Path)
    parser.add_argument('design', type=Path)
    parser.add_argument('assets', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    baseline = args.baseline.resolve(); output = args.output.resolve()
    receipt = json.loads((baseline/'receipt.json').read_text())
    if sha256_file(baseline/'delivery/preview.mp4') != receipt['video_sha256']:
        raise ValueError('baseline_video_changed')
    design = FilmDesign.model_validate_json(args.design.read_text())
    plan = ScenePlan.model_validate_json((baseline/'prepared-plan.json').read_text())
    for scene in plan.scenes:
        original = next(a for a in receipt['assets'] if a['scene_id'] == scene.id)
        if sha256_file(baseline/f'{scene.id}.wav') != original['audio_sha256']:
            raise ValueError('baseline_voice_changed')
        if scene.layout['hybrid']['route'] == 'cinematic':
            if sha256_file(args.assets/f'{scene.id}.png') != original['image_sha256']:
                raise ValueError('baseline_image_changed')
        scene.layout['hybrid'].update(version='hybrid-scene-0.4', design=design.model_dump(mode='json'))
    findings = evaluate_hybrid(plan.scenes, expected_version='hybrid-scene-0.4')
    if findings: raise ValueError(findings)
    # Keep the intermediate and final candidates separate; no baseline overwrite.
    inputs = output.with_name(output.name+'-inputs'); inputs.mkdir(parents=True, exist_ok=False)
    candidate = inputs/'scene-plan.json'
    atomic_json(candidate, plan.model_dump(mode='json'))
    command = [sys.executable, str(ROOT/'scripts/render_director_probe.py'), str(candidate), str(args.assets), str(output)]
    subprocess.run([*command, '--prepare-voice'], check=True)
    for scene in plan.scenes:
        for suffix in ('.wav', '.words.json'):
            shutil.copy2(baseline/f'{scene.id}{suffix}', output/f'{scene.id}{suffix}')
    atomic_json(output/'design-experiment.json', dict(status='EXPERIMENTAL', baseline_video_sha256=receipt['video_sha256'],
        baseline_plan_sha256=sha256_file(baseline/'prepared-plan.json'), design_sha256=design_sha256(design),
        design_origin='Explicit authored development candidate, not blind concept selection',
        reuse='Same script, source images, local voice, timing and information geometry for controlled comparison',
        new_director_calls=0, new_image_calls=0, new_voice_calls=0, paid_api_calls=0, human_approval=None))
    subprocess.run(command, check=True)


if __name__ == '__main__': main()
