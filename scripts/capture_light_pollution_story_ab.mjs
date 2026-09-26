import { spawnSync } from 'node:child_process';
import { join, resolve } from 'node:path';
import { mkdirSync } from 'node:fs';

const root = resolve('experiments/light-pollution-story-asset-v1');
for (const variant of ['A', 'B']) {
  const source = join(root, variant, 'comparison.mp4');
  const out = join(root, variant, 'frames');
  mkdirSync(out, { recursive: true });
  for (const time of [0, 3.4, 5.0]) {
    const target = join(out, `t-${time.toFixed(1)}.png`);
    const result = spawnSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(time), '-i', source,
      '-frames:v', '1', target], { stdio: 'inherit' });
    if (result.status !== 0) throw new Error(`Frame extraction failed: ${variant} ${time}`);
  }
}
