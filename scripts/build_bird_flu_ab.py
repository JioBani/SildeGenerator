"""Local analysis comparison. Reference excerpts are not redistributable output assets."""
import argparse
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--candidate', default='bird-flu-v4.mp4')
a = p.parse_args()
source = a.root / 'sources/bHB5iiDDJ-s.mp4'
candidate = a.root / a.candidate
inputs = []
filters = []
for i, start in enumerate([121.8, 176, 256]):
    inputs.extend(['-ss', str(start), '-t', '6', '-i', str(source)])
    filters.append(f'[{i}:v]fps=30,scale=960:540,setsar=1,setpts=PTS-STARTPTS[r{i}]')
inputs.extend(['-i', str(candidate)])
filters.extend(['[r0][r1][r2]concat=n=3:v=1:a=0[ref]',
                '[3:v]fps=30,scale=960:540,setsar=1,setpts=PTS-STARTPTS[candidate]',
                '[ref][candidate]hstack=inputs=2[v]'])
subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(filters),
                '-map', '[v]', '-t', '18', '-an', '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p',
                str(a.root / 'reference-vs-study.mp4')], check=True, timeout=180)
