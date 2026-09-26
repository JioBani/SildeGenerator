import { chromium } from '@playwright/test';
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const dir = join(root, 'experiments/light-pollution-story-asset-v1/F-master-actor-v1');
const output = join(dir, 'inspection');
mkdirSync(output, { recursive: true });
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
const candidate = JSON.parse(readFileSync(join(root, 'docs/actor-assets/d-nightlight-candidate.json'), 'utf8'));
for (const evidence of [candidate.video, candidate.program, candidate.human_review]) {
  if (hash(readFileSync(join(root, evidence.path))) !== evidence.sha256) throw new Error('Approved D evidence changed');
}
const browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(pathToFileURL(join(dir, 'review.html')).href);
  await page.evaluate(async () => {
    const paths = [...document.querySelectorAll('svg image')].map((e) => e.getAttribute('href'));
    await Promise.all([...new Set(paths)].map((path) => new Promise((resolve, reject) => {
      const image = new Image(); image.onload = resolve; image.onerror = reject; image.src = path;
    })));
  });
  const spec = await page.evaluate(() => window.actorAuthoring.spec);
  const shots = [];
  for (const [name, pose] of Object.entries(spec.presets)) {
    await page.evaluate((pose) => { window.actorAuthoring.update(pose); }, pose);
    const png = await page.locator('.viewport').screenshot({ path: join(output, `${name}.png`), timeout: 20000 });
    shots.push({ name, pose, sha256: hash(png), joints: await page.evaluate(() => window.actorAuthoring.joints()) });
  }
  await page.evaluate(() => { window.actorAuthoring.update(window.actorAuthoring.spec.presets.neutral); });
  await page.selectOption('#backdrop', 'light');
  await page.locator('.viewport').screenshot({ path: join(output, 'neutral-light.png'), timeout: 20000 });
  await page.selectOption('#backdrop', 'dark');
  await page.screenshot({ path: join(output, 'desktop.png'), fullPage: true, timeout: 20000 });
  const sweep = await page.evaluate(() => {
    const result = [];
    for (let frame = 0; frame <= 100; frame++) {
      const t = frame / 100;
      const a = window.actorAuthoring;
      a.update({ shoulder: 5 + 25 * t, elbow: 80 - 70 * t, wrist: 0, head: 1.8 * t });
      const joints = a.joints();
      if (Object.values(joints).flat().some((n) => !Number.isFinite(n))) throw new Error('nonfinite_joint');
      result.push({ frame, joints });
    }
    window.actorAuthoring.update(window.actorAuthoring.spec.presets.neutral);
    return result;
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: join(output, 'mobile.png'), fullPage: true, timeout: 20000 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  if (overflow) errors.push('mobile_horizontal_overflow');
  const files = Object.fromEntries(Object.values(spec.textures).map((asset) => [asset.path, hash(readFileSync(join(dir, asset.path)))]));
  for (const [name, evidence] of Object.entries(candidate.layers).filter(([name]) => name.startsWith('head') || name === 'neck_underlay')) {
    const basename = evidence.path.split('/').at(-1);
    const actual = hash(readFileSync(join(dir, 'assets', basename)));
    if (actual !== evidence.sha256) errors.push(`${name}_copy_changed`);
    files[`assets/${basename}`] = actual;
  }
  const masterDir = join(dir, 'master-layers');
  mkdirSync(masterDir, { recursive: true });
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.evaluate(() => {
    window.actorAuthoring.update(window.actorAuthoring.spec.presets.neutral);
    document.querySelector('#guides').setAttribute('display', 'none');
    document.querySelector('#actor').setAttribute('viewBox', '0 0 1920 1080');
    const style = document.createElement('style');
    style.textContent = 'html,body{background:transparent!important}header,aside,footer{display:none!important}main{padding:0;margin:0;display:block;max-width:none}.viewport{background:transparent!important;position:fixed;inset:0;width:1920px;height:1080px;max-width:none;max-height:none;aspect-ratio:auto}';
    document.head.append(style);
  });
  let masterSvg = await page.locator('#actor').evaluate((node) => new XMLSerializer().serializeToString(node));
  for (const path of Object.keys(files)) {
    masterSvg = masterSvg.replaceAll(`href="${path}"`, `href="data:image/png;base64,${readFileSync(join(dir, path)).toString('base64')}"`);
  }
  masterSvg = masterSvg.replace('viewBox="0 0 1920 1080"', 'viewBox="0 0 1920 1080" width="1920" height="1080"');
  writeFileSync(join(dir, 'master-neutral.svg'), masterSvg);
  const layers = [];
  const selectors = { '00-assembled': '*', '10-far-arm': '#far-arm [data-texture]', '20-head-neck': '#head-origin',
    '30-torso': '[data-texture="torso"]', '40-upper-arm': '#near-upper > [data-texture="upper"]',
    '50-hand': '#near-wrist > [data-texture="hand"]', '60-forearm': '#near-elbow > [data-texture="forearm"]' };
  for (const [name, selector] of Object.entries(selectors)) {
    await page.evaluate((selector) => {
      document.querySelectorAll('[data-texture],#head-origin').forEach((node) => { node.style.visibility = selector === '*' ? '' : 'hidden'; });
      if (selector !== '*') document.querySelectorAll(selector).forEach((node) => { node.style.visibility = 'visible'; });
    }, selector);
    const png = await page.locator('#actor').screenshot({ path: join(masterDir, `${name}.png`), omitBackground: true, timeout: 20000 });
    layers.push({ name, path: `master-layers/${name}.png`, sha256: hash(png), canvas: [1920, 1080] });
  }
  writeFileSync(join(dir, 'authoring-manifest.json'), JSON.stringify({ ...spec, file_sha256: files, master_layers: layers,
    editable_master: { path: 'master-neutral.svg', sha256: hash(Buffer.from(masterSvg)) } }, null, 2) + '\n');
  writeFileSync(join(output, 'audit.json'), JSON.stringify({ status: errors.length ? 'TECHNICAL_BLOCKED' : 'ASSEMBLY_LOADED_HUMAN_REVIEW_REQUIRED',
    production_ready: false, original_d_unchanged: true, browser: browser.version(),
    program_sha256: hash(readFileSync(join(dir, 'actor.js'))), files, shots, sweep, errors,
    limits: ['Coordinates are authored joints, not image-detected anatomy or contact.', 'No IK, mesh, grasp, curtain action or human approval.', 'Static pose sweep is not an acting-quality test.'] }, null, 2) + '\n');
  console.log(JSON.stringify({ status: errors.length ? 'BLOCKED' : 'REVIEW_REQUIRED', errors, shots: shots.length, sweep: sweep.length }));
  if (errors.length) process.exitCode = 1;
} finally { await browser.close(); }
