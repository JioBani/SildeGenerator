"""Local feature displacement evidence, not particle identities or anatomical flow."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def displacement(first, second, mask):
    a = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)
    points = cv2.goodFeaturesToTrack(a, 100, .01, 5, mask=mask)
    if points is None:
        return None
    forward, status, _ = cv2.calcOpticalFlowPyrLK(a, b, points, None, winSize=(15, 15), maxLevel=2)
    if forward is None:
        return None
    backward, back_status, _ = cv2.calcOpticalFlowPyrLK(b, a, forward, None, winSize=(15, 15), maxLevel=2)
    if backward is None:
        return None
    valid = (status.ravel() == 1) & (back_status.ravel() == 1)
    valid &= np.linalg.norm((backward-points).reshape(-1, 2), axis=1) < .5
    valid &= np.isfinite(forward.reshape(-1, 2)).all(axis=1)
    delta = (forward-points).reshape(-1, 2)[valid]
    if len(delta) < 3:
        return None
    median = np.median(delta, axis=0)
    return {'features': len(delta), 'dx': float(median[0]), 'dy': float(median[1]),
            'median_deviation': float(np.median(np.linalg.norm(delta-median, axis=1)))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('analysis', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve previous evidence')
    source = json.loads(args.analysis.read_text(encoding='utf-8'))
    frames = [r for r in source['frames'] if 116 <= r['source_second'] <= 123]
    rows = []
    for left, right in zip(frames, frames[1:]):
        first = cv2.imread(str(args.analysis.parent/'frames'/left['file']))
        second = cv2.imread(str(args.analysis.parent/'frames'/right['file']))
        if first is None or second is None:
            raise ValueError('Missing source frame')
        if first.shape[:2] != (360, 640):
            raise ValueError('Expected 640x360 evidence')
        b, g, r = first.transpose(2, 0, 1)
        mask = ((r > 80) & (r < 190) & (g < 45) & (b < 35)).astype('uint8')*255
        roi = np.zeros_like(mask)
        # Stable upstream channel, away from the bulge and moving wall edges.
        roi[174:204, 70:240] = 255
        result = displacement(first, second, cv2.bitwise_and(mask, roi))
        dt = right['source_second']-left['source_second']
        if dt <= 0:
            raise ValueError('Non-increasing timestamps')
        rows.append({'start': left['source_second'], 'end': right['source_second'],
                     'measurement': result, 'vx': None if result is None else result['dx']/dt})
    usable = [r for r in rows if r['measurement'] is not None]
    speeds = [r['vx'] for r in usable]
    report = {'source_sha256': source['source_sha256'], 'rows': rows,
              'measured_pairs': len(usable), 'total_pairs': len(rows),
              'median_vx': float(np.median(speeds)) if speeds else None,
              'vx_quartiles': np.percentile(speeds, [25, 75]).tolist() if speeds else None,
              'scope': 'Median LK feature displacement in upstream ROI only. Re-detected each pair; no persistent particle identity. Near-zero estimates may be held animation frames. Not physical blood velocity.'}
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__ == '__main__':
    main()
