"""Offline visual probe of the actual classic-slide renderer; no providers."""
import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('classic_media', ROOT / 'harnesses/classic-slide/src/classic_slide/effects/media.py')
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class LocalProcess:
    async def run(self, command):
        result = await asyncio.create_subprocess_exec(*command)
        code = await result.wait()
        if code:
            raise RuntimeError(f'Local renderer failed: {code}')


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--camera-mode', choices=['legacy_restart', 'shared_locked'], default='shared_locked')
    parser.add_argument('--harness', choices=['classic-slide', 'cinematic-slide'], default='classic-slide')
    args = parser.parse_args()
    selected_media = media
    if args.harness == 'cinematic-slide':
        sys.path.insert(0, str(ROOT / 'video-generator'))
        sys.path.insert(0, str(ROOT / 'harnesses/cinematic-slide/src'))
        import importlib
        selected_media = importlib.import_module('cinematic_slide.effects.media')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    names = ['cute-character-neutral-v1.png', 'cute-character-v2.png']
    captions = ['밤늦게, 한 사람이 컴퓨터 앞에 앉아 있습니다.',
                '몇 초 뒤, 존재하지 않았던 이미지가 화면에 나타납니다.']
    scenes = [SimpleNamespace(image_path=str(ROOT / 'web/public/style-previews' / name),
                              duration_seconds=5.0, narration=caption,
                              layout={'continuity_group': 'result-appears', 'camera': {'mode': 'hold'}})
              for name, caption in zip(names, captions)]
    settings = SimpleNamespace(width=1920, height=1080, fps=30,
                               crossfade_seconds=0.3, ffmpeg_preset='fast')
    config = {'subtitle_font': 'Malgun Gothic', 'subtitle_size': 44,
              'subtitle_margin_vertical': 65, 'zoom_strength': 0.02 if args.camera_mode == 'legacy_restart' else 0.0,
              'crossfade_seconds': 0.3}
    subtitles = out / 'captions.ass'
    selected_media.write_subtitles(scenes, subtitles, settings, config)
    video = out / 'continuity.mp4'
    await selected_media.render_segment(scenes, subtitles, video, settings, config, LocalProcess())
    probe = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
    stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    assert (stream['width'], stream['height'], stream['r_frame_rate']) == (1920, 1080, '30/1')
    assert abs(float(probe['format']['duration']) - 10) < .05
    frames = []
    for index, timestamp in enumerate([0, 4.9, 5.15, 5.4, 9.9]):
        path = out / f'frame-{index}.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(timestamp), '-i', str(video),
                        '-frames:v', '1', '-update', '1', str(path)], check=True)
        frames.append({'time': timestamp, 'path': path.name})
    receipt = {
        'scope': 'two-cut silent style continuity probe, not a full script production',
        'renderer': args.harness + ('@1.1.0' if args.harness == 'classic-slide' else '@0.1.0'), 'config': config,
        'camera_mode': args.camera_mode,
        'duration': float(probe['format']['duration']), 'human_approved': False,
        'rigged_acting': False, 'provider_calls_in_render': 0,
        'source': [{'path': s.image_path, 'sha256': hashlib.sha256(Path(s.image_path).read_bytes()).hexdigest(),
                    'caption': s.narration} for s in scenes],
        'video_sha256': hashlib.sha256(video.read_bytes()).hexdigest(), 'samples': frames,
        'limits': ['No voice; captions are non-consecutive excerpts from GPU script.',
                   'Whole-image crossfade is not sequential eye/head acting.',
                   'Manual framing review required; no automatic Gold approval.'],
    }
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(video)


if __name__ == '__main__':
    asyncio.run(main())
