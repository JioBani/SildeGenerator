"""Offline harness graph delivery smoke using reviewed fixtures and Windows SAPI."""
import argparse
import asyncio
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'video-generator'))
from app.engine.graph_executor import GraphExecutor, LocalLeaseProvider
from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import validate_harness_plan
from app.engine.process_runner import ProcessRunner
from app.harness_sdk.artifacts import ArtifactStore
from app.harness_sdk.context import HarnessContext


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--reuse-voice-work', type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding='utf-8')) if args.fixture else None
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    work = out / 'work'
    segments = work / 'render-segments'
    segments.mkdir(parents=True)
    (out / 'delivery').mkdir()
    lines = [{'id': 'scene-001', 'narration': '밤늦게, 한 사람이 컴퓨터 앞에 앉아 있습니다.'},
             {'id': 'scene-002', 'narration': '몇 초 뒤, 존재하지 않았던 이미지가 화면에 나타납니다.'}]
    plan = None
    if fixture:
        from app.planner import deterministic_plan, validate_plan
        from app.scene_contracts import build_production_pack
        plan = deterministic_plan(fixture['script'], 'Original slide cinematic artwork.', fixture['image_style'])
        if fixture.get('genre_id'):
            from app.genre_profiles import bind_plan
            plan = bind_plan(plan, fixture['genre_id'])
        if len(plan.scenes) != len(fixture['shots']):
            raise ValueError('Every source sentence needs exactly one fixture shot')
        for scene, shot in zip(plan.scenes, fixture['shots']):
            scene.layout = {**scene.layout, 'camera': shot['camera']}
            if shot.get('transition'):
                scene.transition = shot['transition']
            if shot.get('asset_origin'):
                scene.layout['asset_origin'] = shot['asset_origin']
            scene.visual_summary = shot['visual_summary']
            scene.renderer_requirements = {'preferred': 'cinematic-slide', 'capabilities': ['image', 'text', 'camera_push']}
            scene.object_states = [{'object_id': 'scene-image', 'role': 'subject', 'initial': 'visible', 'final': 'visible'}]
            scene.motion = [{'object_id': 'scene-image', 'kind': shot['camera']['mode'], 'phases': ['read', 'settle']}]
        validate_plan(plan, fixture['script'])
        loaded = HarnessRegistry(ROOT / 'harnesses').load('cinematic-slide')
        if validate_harness_plan(loaded, plan.scenes):
            raise ValueError('Fixture camera preflight failed')
        pack = build_production_pack(plan, duration_profile='episode_60', harness_id='cinematic-slide')
        if pack['status'] != 'READY_FOR_COMPILATION':
            raise ValueError(pack['findings'])
        (work / 'production-pack.json').write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding='utf-8')
        lines = [{'id': s.id, 'narration': s.narration} for s in plan.scenes]
    manifest = work / 'voice-input.json'
    manifest.write_text(json.dumps(lines, ensure_ascii=False), encoding='utf-8')
    if args.reuse_voice_work:
        voice_work = args.reuse_voice_work.resolve()
        if json.loads((voice_work / 'voice-input.json').read_text(encoding='utf-8')) != lines:
            raise ValueError('Shared voice must match every narration and scene ID exactly')
        for line in lines:
            shutil.copyfile(voice_work / (line['id'] + '.wav'), work / (line['id'] + '.wav'))
    else:
        subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                        str(ROOT / 'scripts/synthesize_local_review_voice.ps1'), '-InputPath', str(manifest)], check=True)
    images = ['cute-character-neutral-v1.png', 'cute-character-v2.png']
    if fixture:
        images = [s['image'] for s in fixture['shots']]
    scenes = []
    for line, image in zip(lines, images):
        wav = work / (line['id'] + '.wav')
        values = dict(duration_seconds=float(probe(wav)['format']['duration']),
                      audio_path=str(wav), image_path=str(ROOT / 'web/public/style-previews' / image))
        if plan:
            scene = plan.scenes[len(scenes)]
            for key, value in values.items():
                setattr(scene, key, value)
        else:
            scene = SimpleNamespace(**line, **values, layout={'continuity_group': 'same-room', 'camera': {'mode': 'hold'}})
        scenes.append(scene)
    if plan:
        (work / 'scene-plan.json').write_text(plan.model_dump_json(indent=2), encoding='utf-8')
    expected = sum(s.duration_seconds for s in scenes)
    assert expected <= 60
    loaded = HarnessRegistry(ROOT / 'harnesses').load('cinematic-slide')
    assert not validate_harness_plan(loaded, scenes)
    settings = SimpleNamespace(width=1920, height=1080, fps=30, crossfade_seconds=.3, ffmpeg_preset='fast')
    config = {**loaded.config, 'subtitle_font': 'Malgun Gothic', 'subtitle_size': 44}
    if fixture:
        config['crossfade_seconds'] = fixture.get('crossfade_seconds', .3)
    completed = []
    async def operation(name, **metadata):
        context = HarnessContext('cinematic-offline-smoke', out, settings, ProcessRunner(),
                                 ArtifactStore(out), LocalLeaseProvider(),
                                 metadata={'operation': name, 'config': config, **metadata})
        graph = await loaded.instance.build_pipeline(context)
        result = await GraphExecutor(loaded.snapshot).execute(graph, context)
        completed.extend(result.keys())
        return context
    segment = segments / 'segment.mp4'
    await operation('render_segment', scenes=scenes, subtitles=work / 'captions.ass', output=segment)
    await operation('audio_assembly', scenes=scenes, work=work)
    video = out / 'delivery/cinematic.mp4'
    context = await operation('video_assembly', segments=[segment], audio=work / 'narration.m4a', output=video)
    info = probe(video)
    visual = next(s for s in info['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    num, den = map(int, visual['avg_frame_rate'].split('/'))
    result = {'video_codec': visual['codec_name'], 'audio_codec': audio['codec_name'],
              'width': visual['width'], 'height': visual['height'], 'fps': num / den,
              'duration_seconds': float(info['format']['duration'])}
    validation = await loaded.instance.validate_result(context, result)
    assert validation.valid and abs(result['duration_seconds'] - expected) < .15
    receipt = {'harness': loaded.snapshot.as_dict(), 'completed_tasks': completed, 'result': result,
               'narration_sha256': hashlib.sha256(json.dumps(lines, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
               'assets': [{'scene_id': s.id, 'duration_seconds': s.duration_seconds,
                           'image_sha256': hashlib.sha256(Path(s.image_path).read_bytes()).hexdigest(),
                           'voice_sha256': hashlib.sha256(Path(s.audio_path).read_bytes()).hexdigest()}
                          for s in scenes],
               'expected_voice_seconds': expected, 'technical_pass': validation.valid,
               'human_approved': False, 'voice_provider': 'Windows SAPI offline', 'paid_api_calls': 0,
               'video_sha256': hashlib.sha256(video.read_bytes()).hexdigest(),
               'scope': 'complete fixture script with authored assets; local graph, not server/queue E2E' if fixture else 'real local harness graph; two nonconsecutive script excerpts; not server/queue E2E',
               'image_style': fixture['image_style'] if fixture else 'cute_character'}
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result))
    print(video)


if __name__ == '__main__':
    asyncio.run(main())
