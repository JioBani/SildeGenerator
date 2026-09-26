"""Measure the reviewed yellow callout in 640px reference frames, not semantics."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def measure(image):
    a = np.asarray(image.convert('RGB'), dtype=float)
    if a.shape != (360, 640, 3):
        raise ValueError('Expected 640x360 reviewed frames')
    roi = a[60:160, 280:340]
    r, g, b = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    ys, xs = np.where((r > 200) & (g > 170) & (b < 150) & (g > b*1.8))
    if len(ys) < 20:
        return None
    tip_y = int(ys.max()) + 60
    tip_x = float(np.median(xs[ys >= ys.max()-1])) + 280
    x = int(round(tip_x))
    wall = a[tip_y:170, x-8:x+9]
    r, g, b = wall[:, :, 0], wall[:, :, 1], wall[:, :, 2]
    candidates = np.flatnonzero(((r > 150) & (g > 65) & (g < 165) & (b < 110)).sum(axis=1) >= 8)
    if not len(candidates):
        return {'tip': [tip_x, tip_y], 'wall_y': None, 'gap': None}
    wall_y = int(candidates[0]) + tip_y
    return {'tip': [tip_x, tip_y], 'wall_y': wall_y, 'gap': wall_y-tip_y}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('analysis', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error('Preserve previous measurement')
    source = json.loads(args.analysis.read_text(encoding='utf-8'))
    rows = []
    for frame in source['frames']:
        if not 130 <= frame['source_second'] <= 141:
            continue
        file = args.analysis.parent/'frames'/frame['file']
        with Image.open(file) as image:
            result = measure(image)
        rows.append({'source_second': frame['source_second'], 'measurement': result,
                     'file': frame['file'], 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    visible = [r for r in rows if r['measurement']]
    valid = [r['measurement'] for r in visible if r['measurement']['gap'] is not None]
    if not valid:
        raise ValueError('No measurable reviewed callout')
    report = {'source_sha256': source['source_sha256'],
              'analysis_sha256': hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
              'scope': 'Yellow arrow tip and nearest orange wall band in reviewed ROI; not anatomy, OCR or approval',
              'first_detected': visible[0]['source_second'], 'last_detected': visible[-1]['source_second'],
              'gap_range_px': [min(r['gap'] for r in valid), max(r['gap'] for r in valid)],
              'unresolved_wall_frames': len(visible)-len(valid), 'rows': rows}
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
