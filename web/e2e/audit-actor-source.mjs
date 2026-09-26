import { chromium } from '@playwright/test';
import { createHash } from 'node:crypto';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const manifestPath = join(root, 'docs/actor-assets/d-nightlight-candidate.json');
const outputPath = join(root, 'experiments/light-pollution-story-asset-v1/E-actor-rig-study/source-assembly-audit.json');
const staticSheets = process.argv.includes('--static-sheets');
const candidate = JSON.parse(readFileSync(manifestPath, 'utf8'));
const programPath = join(root, candidate.program.path);
const actualHash = createHash('sha256').update(readFileSync(programPath)).digest('hex');
if (actualHash !== candidate.program.sha256) throw new Error('Source program hash changed');
const sourceLayers = Object.fromEntries(Object.entries(candidate.layers).map(([id, asset]) => {
  const actual = createHash('sha256').update(readFileSync(join(root, asset.path))).digest('hex');
  if (actual !== asset.sha256) throw new Error(`Source layer hash changed: ${id}`);
  return [id, actual];
}));
const gsapHash = createHash('sha256').update(readFileSync(join(dirname(programPath), 'assets/gsap.min.js'))).digest('hex');

const launchOptions = process.env.PLAYWRIGHT_BROWSER_PATH
  ? { executablePath: process.env.PLAYWRIGHT_BROWSER_PATH }
  : process.platform === 'win32'
    ? { executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' }
    : {};
const browser = await chromium.launch({ headless: true, ...launchOptions });
try {
  const [width, height] = candidate.source_assembly.canvas_px;
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(programPath).href, { waitUntil: 'load' });
  const observed = await page.evaluate(async () => {
    await Promise.all([...document.images].map((image) => image.decode().catch(() => null)));
    const torso = document.querySelector('.person > .torso:not(.collar-front)');
    const head = document.querySelector('.person > .head');
    const collar = document.querySelector('.person > .collar-front');
    const neck = document.querySelector('.head .neck-surface');
    const timeline = window.__timelines?.['story-d'];
    if (!torso || !head || !collar || !neck || !timeline) return { missing_dom_or_timeline: true };
    const bounds = (node) => {
      const style = getComputedStyle(node);
      return [style.left, style.top, style.width, style.height].map((value) => Number.parseFloat(value));
    };
    const geometry = {
      torso_bounds_px: bounds(torso),
      head_bounds_px: bounds(head),
      head_pivot_local_px: getComputedStyle(head).transformOrigin.split(' ').slice(0, 2).map(Number.parseFloat),
      head_z: Number.parseInt(getComputedStyle(head).zIndex, 10),
      collar_z: Number.parseInt(getComputedStyle(collar).zIndex, 10),
      collar_clipped: getComputedStyle(collar).clipPath !== 'none',
      neck_clipped: getComputedStyle(neck).clipPath !== 'none',
      images_loaded: [...document.images].every((image) => image.naturalWidth > 0),
    };
    const samples = [];
    let maxAbsHeadRotation = 0;
    const frames = Math.floor(Number(document.querySelector('main').dataset.duration) * 30);
    for (let frame = 0; frame < frames; frame += 1) {
      timeline.time(frame / 30, true);
      const transform = getComputedStyle(head).transform;
      const matrix = transform === 'none' ? [1, 0] : transform.match(/matrix\(([^)]+)\)/)?.[1].split(',').slice(0, 2).map(Number.parseFloat);
      const angle = matrix ? Math.atan2(matrix[1], matrix[0]) * 180 / Math.PI : NaN;
      maxAbsHeadRotation = Math.max(maxAbsHeadRotation, Math.abs(angle));
      if ([0, 45, 66, 84, 105, 150, frames - 1].includes(frame)) {
        samples.push({
          frame,
          head_rotation_deg: angle,
          notice_opacity: Number.parseFloat(getComputedStyle(document.querySelector('.notice')).opacity),
          squint_opacity: Number.parseFloat(getComputedStyle(document.querySelector('.squint')).opacity),
          lamp_opacity: Number.parseFloat(getComputedStyle(document.querySelector('.lamp-lit')).opacity),
        });
      }
    }
    timeline.time(0, true);
    return { geometry, max_abs_head_rotation_deg: maxAbsHeadRotation, frames, samples };
  });
  const expected = candidate.source_assembly;
  const findings = [];
  if (observed.missing_dom_or_timeline) findings.push('source_dom_or_timeline_missing');
  else {
    for (const key of ['torso_bounds_px', 'head_bounds_px', 'head_pivot_local_px']) {
      if (JSON.stringify(observed.geometry[key]) !== JSON.stringify(expected[key])) findings.push(`${key}_mismatch`);
    }
    if (observed.geometry.head_z >= observed.geometry.collar_z || !observed.geometry.collar_clipped || !observed.geometry.neck_clipped) {
      findings.push('collar_occlusion_missing');
    }
    if (!observed.geometry.images_loaded) findings.push('actor_image_failed_to_load');
    if (observed.max_abs_head_rotation_deg > expected.head_rotation_observed_deg + 0.05) findings.push('head_rotation_outside_recorded_range');
  }
  const report = {
    status: findings.length ? 'SOURCE_ASSEMBLY_BLOCKED' : 'SOURCE_ASSEMBLY_TECHNICAL_PASS_HUMAN_REVIEW_PENDING',
    production_ready: false,
    source_program_sha256: actualHash,
    source_layer_sha256: sourceLayers,
    source_gsap_sha256: gsapHash,
    browser_version: browser.version(),
    manifest_actor_id: candidate.actor_id,
    observed,
    findings,
    limits: ['Checks CSS geometry, layer ordering, image loads and GSAP head rotation only.', 'Does not verify arm rig, contact, acting quality, retargeting or new poses.'],
  };
  mkdirSync(dirname(outputPath), { recursive: true });
  if (staticSheets && !findings.length) {
    const sheetDir = join(dirname(outputPath), 'static-sheets');
    mkdirSync(sheetDir, { recursive: true });
    const sheets = [];
    for (const [name, time] of [['rest', 0], ['notice', 2.45], ['squint-max-turn', 3.9], ['settled', 5.8]]) {
      await page.evaluate((time) => { window.__timelines['story-d'].time(time, true); }, time);
      const path = join(sheetDir, `${name}.png`);
      const clip = { x: 1150, y: 235, width: 630, height: 840 };
      const first = await page.screenshot({ path, clip, timeout: 20000 });
      await page.evaluate(() => { window.__timelines['story-d'].time(0, true); });
      await page.evaluate((time) => { window.__timelines['story-d'].time(time, true); }, time);
      const second = await page.screenshot({ clip, timeout: 20000 });
      const hash = (data) => createHash('sha256').update(data).digest('hex');
      sheets.push({ name, source_time_s: time, path, sha256: hash(first), repeat_sha256: hash(second),
        deterministic_same_session: hash(first) === hash(second) });
      if (name === 'squint-max-turn') {
        const neckPath = join(sheetDir, 'neck-collar-max-turn.png');
        const neck = await page.screenshot({ path: neckPath, clip: { x: 1280, y: 620, width: 420, height: 235 }, timeout: 20000 });
        sheets.push({ name: 'neck-collar-max-turn', source_time_s: time, path: neckPath, sha256: hash(neck) });
      }
    }
    report.static_sheets = sheets;
    report.static_sheet_scope = 'Snapshots of the existing D program; not a new rig, independent face controls, hand states, or cross-browser determinism.';
    if (sheets.some((sheet) => sheet.deterministic_same_session === false)) {
      findings.push('static_sheet_repeat_mismatch');
      report.status = 'SOURCE_ASSEMBLY_BLOCKED';
    }
  }
  writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`${report.status}: ${findings.join(', ') || 'no technical findings'}`);
  if (findings.length) process.exitCode = 1;
} finally {
  await browser.close();
}
