"""Scene-specific cream markers inside dark silhouettes; not anatomical joints."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def measure(rgb):
    a = np.asarray(rgb)
    if a.shape != (360, 640, 3):
        raise ValueError('Expected the reviewed 640x360 analysis space')
    r, g, b = [a[:, :, i].astype(float) for i in range(3)]
    cream = ((r > 210) & (g > 210) & (b > 190)).astype('uint8')
    dark = (r < 45) & (g < 110) & (b > 45) & (b < 150)
    n, labels, stats, centers = cv2.connectedComponentsWithStats(cream)
    points = []
    for i in range(1, n):
        x, y, w, h, area = [int(v) for v in stats[i]]
        if not (3 <= area <= 70 and 2 <= w <= 10 and 2 <= h <= 10):
            continue
        if y < 75 or y + h > 340 or x < 3 or x + w > 637:
            continue
        # Vertical neighbors are other markers in a dense dotted line.
        # Verify lateral support instead of rejecting those legitimate neighbors.
        support = float(np.concatenate((dark[y:y+h, x-3:x-1].ravel(),
                                         dark[y:y+h, x+w+1:x+w+3].ravel())).mean())
        if support < .8:
            continue
        cx, cy = centers[i]
        points.append({'x': round(float(cx), 3), 'y': round(float(cy), 3),
                       'area': area, 'dark_surround': round(support, 3)})
    points.sort(key=lambda p: (p['y'], p['x']))
    teal = (r < 80) & (g > 130) & (b > 100) & (b < 210)
    yellow = (r > 210) & (g > 150) & (b < 140)
    # Read the uncluttered top row, requiring substantial fields on both sides.
    candidates = [x for x in range(6, 635)
                  if teal[5:20, x-6:x-3].mean() > .95
                  and yellow[5:20, x+3:x+6].mean() > .95]
    contiguous = candidates and candidates[-1] - candidates[0] + 1 == len(candidates)
    divider = float(np.median(candidates)) if contiguous and len(candidates) <= 7 else None
    return {'points': points, 'divider_x': divider,
            'left': [p for p in points if divider is not None and p['x'] < divider],
            'right': [p for p in points if divider is not None and p['x'] >= divider]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    p.add_argument('--overlay', type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Preserve previous evidence')
    if args.overlay and args.overlay.exists():
        raise ValueError('Preserve previous overlay')
    data = json.loads(args.source.read_text(encoding='utf-8'))
    rows = []
    for f in data['frames']:
        if f['source_second'] < 106:
            continue
        with Image.open(args.source.parent / 'frames' / f['file']) as im:
            result = measure(im.convert('RGB'))
        rows.append({'source_second': f['source_second'], 'file': f['file'], **result})
    args.output.write_text(json.dumps({
        'source_sha256': data['source_sha256'],
        'analysis_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'coordinate_space': [640, 360], 'rows': rows,
        'limitations': 'Cream connected components with dark surroundings in a reviewed scene. '
        'Not anatomical identities, tracking, source asset permission or medical validation. '
        'Missing detections do not mean the source object disappeared.'}, indent=2), encoding='utf-8')
    split = [r for r in rows if r['divider_x'] is not None]
    if args.overlay:
        with Image.open(args.source.parent / 'frames' / rows[-1]['file']) as im:
            overlay = np.array(im.convert('RGB'))
        for point in rows[-1]['points']:
            cv2.circle(overlay, (round(point['x']), round(point['y'])), 4, (255, 60, 90), 1)
        if rows[-1]['divider_x'] is not None:
            x = round(rows[-1]['divider_x'])
            cv2.line(overlay, (x, 0), (x, 359), (255, 60, 90), 1)
        Image.fromarray(overlay).save(args.overlay)
    print(json.dumps({'frames': len(rows), 'split_frames': len(split),
                      'first_split': split[0]['source_second'] if split else None,
                      'last_counts': [len(rows[-1]['left']), len(rows[-1]['right'])]}))


if __name__ == '__main__':
    main()
