import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const require = createRequire(new URL('../web/package.json', import.meta.url));
const { chromium } = require('@playwright/test');
const project = path.resolve(process.argv[2]);
const timelineId = process.argv[3] || 'three-reference-study';
const assets = process.argv.slice(4);
if (!assets.length) assets.push('assets/heat.png', 'assets/tech.png');
if (assets.length === 1 && assets[0] === '--no-images') assets.length = 0;
const metadata = JSON.parse(await fs.readFile(path.join(project, 'meta.json'), 'utf8'));
const finalTime = Number(metadata.duration) - 1 / Number(metadata.fps);
if (!Number.isFinite(finalTime) || finalTime < 0) throw new Error('Invalid composition duration/fps');
const checkpoints = metadata.verificationTimes ?? [];
if (!Array.isArray(checkpoints) || checkpoints.some(t => !Number.isFinite(t) || t < 0 || t > finalTime)) {
  throw new Error('verificationTimes must contain valid composition times');
}
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', error => console.error(error.message));
  await page.goto(pathToFileURL(path.join(project, 'index.html')).href);
  await page.waitForFunction(id => Boolean(window.__timelines?.[id]), timelineId);
  await page.evaluate(async sources => {
    await Promise.all(sources.map(src => new Promise((resolve,reject) => {
      const image = new Image(); image.onload=resolve; image.onerror=reject; image.src=src;
    })));
  }, assets);
  async function capture(time) {
    await page.evaluate(({t,id}) => { window.__timelines[id].seek(t, true); }, {t:time,id:timelineId});
    return page.screenshot();
  }
  const hash = b => crypto.createHash('sha256').update(b).digest('hex');
  const rows = [];
  for (const time of [...new Set([0, 1.5, 3, 6.5, 9.5, 12.2, 14, 17, ...checkpoints, finalTime].filter(t=>t<=finalTime))]) {
    const first = await capture(time);
    await capture(finalTime);
    await capture(0);
    const repeated = await capture(time);
    rows.push({ time, order_independent: hash(first) === hash(repeated), sha256: hash(first) });
    if (hash(first) !== hash(repeated)) await fs.writeFile(path.join(project, `first-${time}.png`), first);
    await fs.writeFile(path.join(project, `verified-${time}.png`), repeated);
  }
  await fs.writeFile(path.join(project, 'seek-review.json'), JSON.stringify(rows,null,2));
  console.log(JSON.stringify(rows));
  if(rows.some(row=>!row.order_independent))process.exitCode=1;
} finally { await browser.close(); }
