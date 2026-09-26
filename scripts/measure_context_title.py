"""Track a reviewed heading patch; reject low correlation, never infer hidden motion."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Preserve previous evidence')
    data = json.loads(a.source.read_text(encoding='utf-8'))
    root = a.source.parent / 'frames'
    reference = root / 'frame-00518.png'
    template = cv2.imread(str(reference), cv2.IMREAD_GRAYSCALE)[40:100, 140:510]
    rows = []
    for frame in data['frames']:
        if not 185 <= frame['source_second'] <= 189:
            continue
        im = cv2.imread(str(root / frame['file']), cv2.IMREAD_GRAYSCALE)
        scores = cv2.matchTemplate(im[:, 140:510], template, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, location = cv2.minMaxLoc(scores)
        rows.append({'source_second': frame['source_second'], 'score': confidence,
                     'top': location[1] if confidence >= .85 else None})
    divider = []
    for frame in data['frames']:
        if frame['source_second'] < 188:
            continue
        im = cv2.imread(str(root / frame['file']))
        b, g, r = im[:, :, 0], im[:, :, 1], im[:, :, 2]
        pale = (r > 210) & (g > 200) & (b > 150)
        columns = np.flatnonzero(pale.mean(axis=0) > .9)
        x = float(np.median(columns)) if 1 <= len(columns) <= 12 else None
        divider.append({'source_second': frame['source_second'], 'x': x})
    a.output.write_text(json.dumps({'source_sha256': data['source_sha256'],
        'template_frame_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
        'template_box': [140, 40, 510, 100], 'minimum_correlation': .85,
        'limitations': 'Reviewed rigid title only; clipped or low-score samples unresolved. Not whole-scene motion.',
        'rows': rows, 'divider_rows': divider}, indent=2), encoding='utf-8')
    good = [r for r in rows if r['top'] is not None]
    print(json.dumps({'samples': len(rows), 'accepted': len(good), 'first': good[0], 'last': good[-1]}))


if __name__ == '__main__':
    main()
