"""Extract every decoded frame in a bounded reference window with source PTS."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from analyze_reference_video import frame_metrics

p = argparse.ArgumentParser()
p.add_argument('video', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--start', type=float, required=True)
p.add_argument('--duration', type=float, default=4)
a = p.parse_args()
if a.start < 0 or not 0 < a.duration <= 30:
    p.error('Use a nonnegative start and a window up to 30 seconds')
a.output.mkdir(parents=True, exist_ok=False)
frames = a.output / 'frames'
frames.mkdir()
cmd = ['ffmpeg', '-v', 'info', '-ss', str(a.start), '-i', str(a.video), '-t', str(a.duration),
       '-vf', 'scale=640:-2,showinfo', '-fps_mode', 'passthrough', str(frames / 'frame-%05d.png')]
result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
import re
pts = [float(t) for t in re.findall(r'\bpts_time:([\d.\-]+)', result.stderr)]
rows, previous = [], None
for i, frame in enumerate(sorted(frames.glob('*.png'))):
    metrics, previous = frame_metrics(frame, previous)
    rows.append({'frame_index': i, 'source_second': round(a.start + pts[i], 6),
                 'file': frame.name, **metrics})
report = {'source': str(a.video.resolve()), 'source_sha256': hashlib.sha256(a.video.read_bytes()).hexdigest(),
          'start': a.start, 'duration': a.duration, 'sampling': 'every decoded frame; original PTS',
          'limitations': 'Image change is not optical flow, object trajectory or acting approval.', 'frames': rows}
(a.output / 'motion.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'frames': len(rows), 'report': str(a.output / 'motion.json')}))
