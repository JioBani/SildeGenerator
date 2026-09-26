"""Measure scene-specific foreground bounds, not anatomy or perceptual quality."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def bounds(image):
    image = cv2.resize(image, (640, 360))
    background = np.median(image[:12].reshape(-1, 3), axis=0)
    # Fail closed outside the observed yellow comparison field.
    b, g, r = background
    if not (r > 200 and 145 < g < 240 and b < 125):
        raise ValueError('Not the yellow comparison scene')
    mask = (np.linalg.norm(image.astype(float) - background, axis=2) > 65).astype('uint8')
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    keep = np.zeros_like(mask)
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] >= 12:
            keep[labels == i] = 1
    y, x = np.where(keep)
    if len(x) < 100:
        raise ValueError('Insufficient foreground')
    return [int(x.min()), int(y.min()), int(x.max() + 1), int(y.max() + 1)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('candidate', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Preserve earlier measurements')
    evidence = json.loads(args.source.read_text(encoding='utf-8'))
    cap = cv2.VideoCapture(str(args.candidate))
    rows = []
    try:
        for time in [94.5, 95.5, 96.5, 97.5, 98.5]:
            src = max((f for f in evidence['frames'] if f['source_second'] <= time), key=lambda f: f['source_second'])
            image = cv2.imread(str(args.source.parent / 'frames' / src['file']))
            cap.set(cv2.CAP_PROP_POS_MSEC, (time - 90) * 1000)
            ok, candidate = cap.read()
            if not ok:
                raise ValueError('Candidate decode failed')
            a, b = bounds(image), bounds(candidate)
            rows.append({'source_pts': src['source_second'], 'candidate_seconds': time - 90,
                         'source_bounds': a, 'candidate_bounds': b,
                         'edge_error': [y - x for x, y in zip(a, b)]})
    finally:
        cap.release()
    args.output.write_text(json.dumps({'rows': rows, 'limitations':
        'Yellow-field foreground includes actor, chair, table and laptop. Bounds do not measure joints, gaze, shape similarity or transition motion.'}, indent=2), encoding='utf-8')
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
