"""Check two deliberately static handoff poses; not a general cut detector."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('video', type=Path)
    p.add_argument('report', type=Path)
    args = p.parse_args()
    if args.report.exists():
        raise ValueError('Preserve review evidence')
    cap = cv2.VideoCapture(str(args.video))
    if abs(cap.get(cv2.CAP_PROP_FPS) - 30) > .001 or int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) != 1800:
        raise ValueError('Expected the 60-second 30fps study')
    rows = []
    try:
        for boundary in [900, 1380]:
            frames = []
            for n in [boundary - 1, boundary]:
                cap.set(cv2.CAP_PROP_POS_FRAMES, n)
                ok, frame = cap.read()
                if not ok:
                    raise ValueError('Missing boundary frame')
                frames.append(cv2.resize(frame, (640,360)))
            delta = np.abs(frames[0].astype(float) - frames[1].astype(float))
            mean = float(delta.mean())
            changed = float((delta.max(axis=2) > 30).mean())
            rows.append({'boundary_frame': boundary, 'source_second': 60+boundary/30,
                'mean_channel_delta': mean, 'fraction_changed_over_30': changed,
                'pass': mean < 1.5 and changed < .005})
    finally:
        cap.release()
    result = {'pass': all(r['pass'] for r in rows), 'rows': rows,
        'sha256': hashlib.sha256(args.video.read_bytes()).hexdigest(),
        'scope': 'Two static shared handoff poses only. Compression-tolerant thresholds are experimental; no source fidelity, acting or motion approval.'}
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
