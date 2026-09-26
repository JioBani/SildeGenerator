import { readFile, writeFile } from 'node:fs/promises';

const token = process.env.LOCAL_PILOT_TOKEN;
if (!token) throw new Error('LOCAL_PILOT_TOKEN is required');
const root = (process.env.LOCAL_SITE_URL ?? 'http://127.0.0.1:18776').replace(/\/$/, '');
const options = await fetch(`${root}/api/jobs/options/production`).then(response => response.json());
if ((options.motionImageProvider ?? options.imageProvider) !== 'local_graphic' || options.voiceProvider !== 'microsoft_edge') {
  throw new Error('This smoke test requires local graphics and Edge voice');
}
const scenario = process.env.LOCAL_SCENARIO_PATH
  ? await readFile(process.env.LOCAL_SCENARIO_PATH, 'utf8')
  : '새로 눈여겨본 자동차가 거리에서 자꾸 보입니다. 차가 늘어난 게 아닙니다. 뇌가 관심 대상을 더 자주 알아차리는 겁니다.';
const suffix = process.env.LOCAL_OUTPUT_SUFFIX ?? 'v2';
const aspectRatio = process.env.LOCAL_ASPECT_RATIO ?? '16:9';
const styles = process.env.LOCAL_STYLES?.split(',') ?? ['narrative', 'educational_info'];
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
for (const style of styles) {
  let created;
  for (let attempt = 0; attempt < 8; attempt++) {
    created = await fetch(`${root}/api/jobs`, {
      method: 'POST',
      headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
      body: JSON.stringify({ scenario, harnessId: 'astra-motion', motionStyleId: style,
        narrationSpeed: 1.1, aspectRatio, subtitlesEnabled: true, continuityEnabled: false }),
    });
    if (created.status !== 429) break;
    await pause(10_000);
  }
  const job = await created.json();
  if (!created.ok) throw new Error(`${style} create failed: ${JSON.stringify(job)}`);
  const accepted = await fetch(`${root}/api/jobs/${job.id}`, { headers: { authorization: `Bearer ${token}` } }).then(response => response.json());
  if (options.imageProvider !== 'local_graphic' && accepted.motionStyle?.productionRoute !== 'local_graphic') {
    throw new Error(`${style} lost its pinned local production route`);
  }
  const deadline = Date.now() + 600_000;
  let state;
  do {
    await pause(3000);
    const response = await fetch(`${root}/api/jobs/${job.id}`, { headers: { authorization: `Bearer ${token}` } });
    state = await response.json();
    if (state.status === 'failed') throw new Error(`${style} render failed: ${state.error}`);
  } while (state.status !== 'completed' && Date.now() < deadline);
  if (state.status !== 'completed') throw new Error(`${style} render timed out at ${state.currentStage}`);
  const video = await fetch(`${root}/api/jobs/${job.id}/video`, { headers: { authorization: `Bearer ${token}` } });
  if (!video.ok) throw new Error(`${style} download failed: ${video.status}`);
  const bytes = Buffer.from(await video.arrayBuffer());
  if (bytes.length < 100_000) throw new Error(`${style} video is unexpectedly small: ${bytes.length}`);
  await writeFile(`../experiments/motion-style-v08/local-${style}-${suffix}.mp4`, bytes);
  process.stdout.write(`${style}: ${job.id} ${bytes.length} bytes completed\n`);
}
