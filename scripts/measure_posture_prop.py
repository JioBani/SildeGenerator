"""Scene-specific striped prop color support; does not infer grip or emotion."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def detect(rgb):
    a = np.asarray(rgb, dtype=float)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = ((g > 110) & (g > r * 1.6) & (b > 65) & (b < g * .95)).astype('uint8')
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 7), np.uint8))
    count, _, stats, centers = cv2.connectedComponentsWithStats(mask)
    candidates = []
    for i in range(1, count):
        x, y, w, h, area = map(int, stats[i])
        if 20 <= w <= 150 and 3 <= h <= 45 and w / h >= 1.5 and 60 <= area <= 4500:
            candidates.append({'bounds': [x, y, x + w, y + h],
                               'center': list(map(float, centers[i])), 'area': area})
    # Ambiguity is not resolved by choosing the largest component.
    return {'candidates': candidates, 'resolved': candidates[0] if len(candidates) == 1 else None}


def fit_visible_fragment(rows, start, end):
    selected = [r for r in rows if start <= r['source_second'] <= end]
    if len(selected) < 5 or any(r['resolved'] is None for r in selected):
        return {'status': 'UNRESOLVED', 'reason': 'Missing or ambiguous evidence'}
    times = np.array([r['source_second'] for r in selected])
    if np.max(np.diff(times)) > .05:
        return {'status': 'UNRESOLVED', 'reason': 'Decoded sample gap'}
    t = times - times[0]
    points = np.array([r['resolved']['center'] for r in selected])
    coefficients = [np.polyfit(t, points[:, axis], 2) for axis in (0, 1)]
    predicted = np.column_stack([np.polyval(c, t) for c in coefficients])
    return {'status': 'MEASURED_FRAGMENT_NOT_IDENTITY_APPROVAL',
            'start': float(times[0]), 'end': float(times[-1]), 'samples': len(selected),
            'x_quadratic_coefficients': coefficients[0].tolist(),
            'y_quadratic_coefficients': coefficients[1].tolist(),
            'maximum_center_residual_pixels': float(np.linalg.norm(points-predicted, axis=1).max()),
            'extrapolation_allowed': False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--start', type=float, default=72)
    p.add_argument('--end', type=float, default=86)
    p.add_argument('--fit-start', type=float, default=82.82)
    p.add_argument('--fit-end', type=float, default=83.09)
    a = p.parse_args()
    if not 0 <= a.start < a.end:
        p.error('Require 0 <= start < end')
    if a.output.exists():
        raise ValueError('Preserve prior evidence')
    data = json.loads(a.source.read_text(encoding='utf-8'))
    rows = []
    for frame in data['frames']:
        if not a.start <= frame['source_second'] < a.end:
            continue
        path = a.source.parent / 'frames' / frame['file']
        with Image.open(path) as im:
            detected = detect(im.convert('RGB'))
        rows.append({'source_second': frame['source_second'], 'file': frame['file'],
                     'frame_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **detected})
    report = {'source_sha256': data['source_sha256'], 'rows': rows,
              'visible_fragment': fit_visible_fragment(rows, a.fit_start, a.fit_end),
              'limitations': 'Green color-support centroid, not whole prop center, rotation, grip anchor or emotion. Ambiguous and absent detections remain unresolved.'}
    a.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    good = [r for r in rows if r['resolved']]
    print(json.dumps({'frames': len(rows), 'resolved': len(good), 'visible_fragment': report['visible_fragment'],
                      'first': good[0] if good else None, 'last': good[-1] if good else None}))


if __name__ == '__main__':
    main()
