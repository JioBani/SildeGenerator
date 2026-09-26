"""Measure a color-isolated actor; missing observations stay missing."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('window', type=Path)
p.add_argument('--hue-min', type=int, default=85)
p.add_argument('--hue-max', type=int, default=115)
a = p.parse_args()
motion = json.loads((a.window / 'motion.json').read_text(encoding='utf-8'))
rows = []
for frame in motion['frames']:
    im = cv2.imread(str(a.window / 'frames' / frame['file']))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([a.hue_min, 90, 80]), np.array([a.hue_max, 255, 255]))
    count, labels, stats, centers = cv2.connectedComponentsWithStats(mask)
    candidates = [i for i in range(1, count) if 200 < stats[i, 4] < im.shape[0]*im.shape[1]*.18]
    best = max(candidates, key=lambda i: stats[i, 4]) if candidates else None
    rows.append({'source_second': frame['source_second'], 'observed': best is not None,
                 'center_normalized': [round(float(centers[best][0])/im.shape[1], 5), round(float(centers[best][1])/im.shape[0], 5)] if best is not None else None,
                 'color_area': int(stats[best, 4]) if best is not None else 0})
result = {'method': 'HSV largest component; blue actor hypothesis, not semantic tracking',
          'limitations': 'Occlusion, same-color props and camera movement require visual review. No missing-frame interpolation.',
          'source_sha256': motion['source_sha256'], 'frames': rows}
(a.window / 'color-track.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'observed': sum(r['observed'] for r in rows), 'total': len(rows)}))
