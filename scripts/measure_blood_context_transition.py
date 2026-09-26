"""Measure teal coverage in the reviewed blood-pressure context transition."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def teal_fraction(rgb):
    a = np.asarray(rgb, dtype=float)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = (g > 45) & (g > r * 1.2) & (b > r * 1.1) & (g > b * .85)
    return float(mask.mean())


def sustained_onset(rows, threshold=.01, count=3):
    for i in range(len(rows) - count + 1):
        if all(row['teal_fraction'] >= threshold for row in rows[i:i + count]):
            return rows[i]['source_second']
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve previous evidence')
    data = json.loads(args.source.read_text(encoding='utf-8'))
    rows = []
    for frame in data['frames']:
        path = args.source.parent / 'frames' / frame['file']
        with Image.open(path) as im:
            fraction = teal_fraction(im.convert('RGB'))
        rows.append({'source_second': frame['source_second'], 'file': frame['file'],
                     'frame_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'teal_fraction': fraction})
    report = {'source_sha256': data['source_sha256'],
              'analysis_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'threshold': .01, 'consecutive_frames': 3,
              'first_sustained_teal': sustained_onset(rows),
              'limitations': 'Scene-specific color evidence, not object identity, clinical semantics, optical flow or an exact authored transition boundary.',
              'human_approved': False, 'rows': rows}
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'frames': len(rows), 'first_sustained_teal': report['first_sustained_teal']}))


if __name__ == '__main__':
    main()
