"""Side-by-side local reference excerpts and candidate, with held source tails."""
import argparse
import subprocess
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
command = ['ffmpeg', '-v', 'error', '-y']
for name, start in [('fLu080UX25o',15),('1GowFTjbUnk',17),('7SWvDHvWXok',18)]:
    command += ['-ss', str(start), '-t', '4', '-i', str(a.directory / 'sources' / f'{name}.mp4')]
command += ['-i', str(a.candidate)]
filters = [f'[{i}:v]setpts=PTS-STARTPTS,scale=960:540,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=2[v{i}]' for i in range(3)]
filters += ['[v0][v1][v2]concat=n=3:v=1:a=0[left]', '[3:v]scale=960:540,setsar=1,fps=30[right]', '[left][right]hstack=inputs=2[out]']
command += ['-filter_complex', ';'.join(filters), '-map','[out]','-an','-t','18','-c:v','libx264','-crf','19','-pix_fmt','yuv420p',str(a.output)]
subprocess.run(command, check=True, timeout=120)
