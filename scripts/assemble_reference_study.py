"""Assemble silent research excerpts with explicit coverage and immutable receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def validate(parts):
    if not parts:
        raise ValueError('No study parts')
    previous = None
    for part in parts:
        start, end = part['source_window']
        if end <= start or (previous is not None and abs(start - previous) > 1e-6):
            raise ValueError('Coverage gap, overlap or invalid ordering')
        previous = end


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
        '-show_streams', '-of', 'json', str(path)]))['streams']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('manifest', type=Path)
    p.add_argument('root', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    receipt = args.output.with_suffix('.receipt.json')
    if args.output.exists() or receipt.exists():
        raise ValueError('Preserve existing study output')
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    parts = manifest['parts']
    validate(parts)
    inputs, records, filters = [], [], []
    for i, part in enumerate(parts):
        path = (args.root / part['file']).resolve()
        if not path.is_relative_to(args.root.resolve()):
            raise ValueError('Study path escapes root')
        streams = probe(path)
        if any(s['codec_type'] == 'audio' for s in streams):
            raise ValueError('Silent study assembly must not silently discard audio')
        video = [s for s in streams if s['codec_type'] == 'video']
        duration = part['source_window'][1] - part['source_window'][0]
        if len(video) != 1 or abs(float(video[0]['duration']) - duration) > 1 / 30:
            raise ValueError('Input duration does not match coverage')
        inputs += ['-i', str(path)]
        filters.append(f'[{i}:v]scale=1920:1080,setsar=1,fps=30,trim=duration={duration},setpts=PTS-STARTPTS[v{i}]')
        records.append({**part, 'sha256': digest(path), 'duration': duration})
    filters.append(''.join(f'[v{i}]' for i in range(len(parts))) + f'concat=n={len(parts)}:v=1:a=0[out]')
    subprocess.run(['ffmpeg', '-v', 'error', *inputs, '-filter_complex', ';'.join(filters),
        '-map', '[out]', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(args.output)], check=True)
    output = probe(args.output)[0]
    expected = round(sum(r['duration'] for r in records) * 30)
    if int(output['nb_frames']) != expected:
        raise ValueError('Assembled frame count mismatch')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(args.output), '-f', 'null', '-'], check=True)
    result = {'status': 'TECHNICAL_ASSEMBLY_ONLY_REVISE', 'human_approved': False,
        'production_enabled': False, 'parts': records, 'frames': expected,
        'sha256': digest(args.output), 'manifest_sha256': digest(args.manifest),
        'limitations': 'Coverage and decoding only; continuity, source fidelity and artistic quality not approved.'}
    receipt.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'frames': expected, 'status': result['status']}))


if __name__ == '__main__':
    main()
