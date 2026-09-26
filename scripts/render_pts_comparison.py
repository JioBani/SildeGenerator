"""Compare CFR candidate frames with the last presented native reference frame."""
import argparse
from bisect import bisect_right
import hashlib
import json
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np


def presented_index(times, target):
    index = bisect_right(times, target + 1e-7) - 1
    if index < 0:
        raise ValueError('Reference evidence starts after requested time')
    return index


def main():
    p = argparse.ArgumentParser()
    p.add_argument('analysis', type=Path); p.add_argument('candidate', type=Path)
    p.add_argument('output', type=Path); p.add_argument('--origin', type=float, required=True)
    args = p.parse_args()
    if args.output.exists() or args.output.with_suffix('.json').exists():
        raise ValueError('Preserve prior comparison')
    source = json.loads(args.analysis.read_text(encoding='utf-8'))
    frames = source['frames']; times = [f['source_second'] for f in frames]
    if not times or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Reference PTS must be strictly increasing')
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', str(args.candidate)]))
    candidate_times = [float(f['best_effort_timestamp_time']) for f in probe['frames']]
    if len(candidate_times) < 2:
        raise ValueError('Candidate must have at least two frames')
    step = candidate_times[1] - candidate_times[0]
    if step <= 0 or any(abs((b-a)-step) > 2e-6 for a, b in zip(candidate_times, candidate_times[1:])):
        raise ValueError('This comparator requires a CFR candidate')
    fps = round(1 / step, 3)
    end = source['start'] + source['duration']
    if args.origin + candidate_times[-1] >= end:
        raise ValueError('Candidate extends beyond reference evidence')
    cap = cv2.VideoCapture(str(args.candidate))
    process = subprocess.Popen(['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', '1280x392', '-r', str(fps), '-i', 'pipe:0', '-an', '-c:v', 'libx264',
        '-crf', '20', '-pix_fmt', 'yuv420p', str(args.output)], stdin=subprocess.PIPE)
    rows = []
    try:
        for n, t in enumerate(candidate_times):
            ok, candidate = cap.read()
            if not ok:
                raise ValueError('Candidate decode ended early')
            target = args.origin + t
            index = presented_index(times, target)
            row = frames[index]
            reference = cv2.imread(str(args.analysis.parent / 'frames' / row['file']))
            if reference is None:
                raise ValueError('Missing reference image')
            image = np.zeros((392, 1280, 3), np.uint8)
            image[:360, :640] = cv2.resize(reference, (640, 360))
            image[:360, 640:] = cv2.resize(candidate, (640, 360))
            label = f"SOURCE PTS {times[index]:.6f} | TARGET {target:.6f} | CANDIDATE {t:.6f} frame {n}"
            cv2.putText(image, label, (8, 382), cv2.FONT_HERSHEY_SIMPLEX, .47, (255, 255, 255), 1)
            process.stdin.write(image.tobytes())
            if abs(t-7.3) < .001:
                cv2.imwrite(str(args.output.with_suffix('.png')), image)
            rows.append({'candidate_frame': n, 'candidate_pts': t, 'target_source_time': target,
                         'source_frame': row['file'], 'source_pts': times[index],
                         'sample_age': target-times[index]})
        process.stdin.close()
        if process.wait(timeout=60) != 0:
            raise RuntimeError('Comparison encoding failed')
    finally:
        cap.release()
        if process.poll() is None:
            process.kill(); process.wait()
    args.output.with_suffix('.json').write_text(json.dumps({
        'source_sha256': source['source_sha256'],
        'analysis_sha256': hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
        'candidate_sha256': hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        'policy': 'Last source frame with PTS <= origin + candidate PTS; no future-frame selection.',
        'limitations': 'Relies on extraction PTS and chosen origin. Not automatic semantic alignment or fidelity approval.',
        'rows': rows}, indent=2), encoding='utf-8')
    print(json.dumps({'frames': len(rows), 'max_sample_age': max(r['sample_age'] for r in rows)}))


if __name__ == '__main__':
    main()
