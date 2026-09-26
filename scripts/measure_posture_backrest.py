"""Measure reviewed green backrest orientation before the camera close-up."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def orientation(rgb):
    a = np.asarray(rgb, dtype=float)[60:246, 50:255]
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = ((r < 90) & (g > 100) & (g > r*1.3) & (b > 60) & (b < g)).astype('uint8')
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    candidates = []
    for i in range(1, count):
        x, y, w, h, area = stats[i]
        if w < 90 or area < 250:
            continue
        yy, xx = np.where(labels == i)
        points = np.column_stack((xx, yy))
        values, vectors = np.linalg.eigh(np.cov(points.T))
        ratio = float(values[-1] / max(values[0], 1e-9))
        if ratio < 15:
            continue
        direction = vectors[:, -1]
        if direction[0] < 0:
            direction = -direction
        candidates.append({'angle_degrees': float(np.degrees(np.arctan2(direction[1], direction[0]))),
                           'elongation_ratio': ratio, 'pixels': int(area)})
    return candidates[0] if len(candidates) == 1 else None


def main():
    p = argparse.ArgumentParser(); p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists(): raise ValueError('Preserve previous evidence')
    data = json.loads(a.source.read_text(encoding='utf-8')); rows = []
    for frame in data['frames']:
        if not 62.687 <= frame['source_second'] < 66.3: continue
        with Image.open(a.source.parent / 'frames' / frame['file']) as im: fit = orientation(im.convert('RGB'))
        rows.append({'source_second': frame['source_second'], 'file': frame['file'], 'fit': fit})
    a.output.write_text(json.dumps({'source_sha256': data['source_sha256'], 'rows': rows,
        'limitations': 'Scene-specific backrest color-region PCA angle. Not a measured body joint angle, anatomical rig, camera estimate or contact approval.'}, indent=2), encoding='utf-8')
    good = [r for r in rows if r['fit']]
    print(json.dumps({'frames': len(rows), 'accepted': len(good), 'first': good[0] if good else None, 'last': good[-1] if good else None}))


if __name__ == '__main__': main()
