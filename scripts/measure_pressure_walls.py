"""Measure cream vessel centerlines in a reviewed source ROI, not general tracking."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
from PIL import Image


def profile(image, lo, hi):
    image = image.convert('RGB')
    if image.size != (640, 360):
        raise ValueError('Expected 640x360 analysis frames')
    pixels = image.load()
    result = []
    for x in range(16, 625, 8):
        ys = []
        for y in range(lo, hi):
            hits = 0
            for xx in range(x-6, x+7):
                r, g, b = pixels[xx, y]
                hits += r > 210 and g > 170 and b > 130 and b > g*.78
            if hits >= 2:
                ys.append(y)
        if not ys:
            raise ValueError(f'No cream lining at x={x}, ROI={lo}:{hi}')
        if max(ys)-min(ys) > 15:
            raise ValueError('Ambiguous disconnected lining; review ROI')
        result.append([x, median(ys)])
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('analysis', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error('Use new output; preserve prior measurement')
    data = json.loads(a.analysis.read_text(encoding='utf-8'))
    rows = []
    for frame in data['frames']:
        if not 65 <= frame['source_second'] <= 78:
            continue
        file = a.analysis.parent/'frames'/frame['file']
        with Image.open(file) as im:
            try:
                upper, lower = profile(im, 70, 140), profile(im, 220, 295)
            except ValueError as exc:
                raise ValueError(f"Source {frame['source_second']} ({file.name}): {exc}") from exc
        peak = min(y for x, y in upper)
        baseline = median([y for x, y in upper if x < 140 or x > 500])
        xs = [x for x, y in upper if y <= peak+1]
        rows.append({'source_second': frame['source_second'], 'upper': upper, 'lower': lower,
                     'peak_x': median(xs), 'amplitude': baseline-peak,
                     'frame_sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    if not rows:
        raise ValueError('No eligible source frames')
    active = [r for r in rows if r['amplitude'] >= 5]
    result = {'source_sha256': data['source_sha256'], 'method': 'ROI cream centerline, 8px sampling, native PTS',
              'scope': '65-78s full vessel only; not anatomy or general optical flow',
              'rows': rows, 'active_peak_x_range': [min(r['peak_x'] for r in active), max(r['peak_x'] for r in active)],
              'amplitude_range': [min(r['amplitude'] for r in rows), max(r['amplitude'] for r in rows)]}
    a.output.write_text(json.dumps(result), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
