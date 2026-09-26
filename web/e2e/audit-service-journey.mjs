// Opt-in live acceptance test. No credentials are written to reports or traces.
import { chromium } from '@playwright/test';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const base = process.env.SERVICE_E2E_URL ?? 'http://127.0.0.1:8080';
if (!/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(base)) throw new Error('Local service only');
const root = path.resolve('..');
const output = path.join(root, 'output', 'service-readiness-20260926');
await mkdir(output, { recursive: true });
const token = (await readFile(path.join(root, '.runtime', 'access-token.txt'), 'utf8')).trim();
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const context = await browser.newContext({ viewport: { width: 1365, height: 900 }, acceptDownloads: true });
const page = await context.newPage();
const pageErrors = [];
page.on('pageerror', error => pageErrors.push(error.message));
let id = process.env.SERVICE_E2E_JOB;
try {
  await context.addInitScript(value => localStorage.setItem('slidegen.token', value), token);
  const mode = await (await context.request.get(`${base}/api/jobs/options/production`)).json();
  if (mode.imageProvider !== 'oauth' || mode.voiceProvider !== 'microsoft_edge') throw new Error('Live OAuth + Edge required; no mock or paid fallback');
  if (!id) {
    if (process.env.SERVICE_E2E_CREATE !== '1') throw new Error('Set SERVICE_E2E_CREATE=1 only with live production authorization');
    await page.goto(base);
    await page.getByLabel('영상 구성 방식').selectOption('classic-slide');
    await page.getByRole('button', { name: /귀여운 캐릭터/ }).click();
    await page.getByLabel('영상 대본', { exact: true }).fill('창가에 앉은 여행자가 노을 진 도시를 바라봅니다. 하루의 끝에서 잠시 숨을 고릅니다.');
    await page.locator('#narration-speed').fill('1.1');
    await page.getByText('음성 대본 미리보기').waitFor();
    const response = page.waitForResponse(r => r.url().endsWith('/api/jobs') && r.request().method() === 'POST');
    await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
    const created = await response;
    if (created.status() !== 202) throw new Error(`create failed: HTTP ${created.status()}`);
    id = (await created.json()).id;
    console.log(JSON.stringify({ created: id }));
    await writeFile(path.join(output, 'created-job.json'), JSON.stringify({ jobId: id }, null, 2));
  } else await page.goto(`${base}/?job=${id}`);
  let status;
  let previous = '';
  const deadline = Date.now() + 15 * 60_000;
  while (Date.now() < deadline) {
    const response = await context.request.get(`${base}/api/jobs/${id}`, { headers: { Authorization: `Bearer ${token}` } });
    if (response.status() === 429) { console.log(JSON.stringify({ jobId: id, state: 'status_rate_limited_waiting' })); await new Promise(resolve => setTimeout(resolve, 65_000)); continue; }
    if (!response.ok()) throw new Error(`status HTTP ${response.status()}`);
    status = await response.json();
    const state = `${status.status}/${status.currentStage}/${status.progress}`;
    if (state !== previous) console.log(JSON.stringify({ jobId: id, state }));
    previous = state;
    if (['completed', 'failed'].includes(status.status)) break;
    await new Promise(resolve => setTimeout(resolve, 15000));
  }
  if (status?.status !== 'completed') throw new Error(`job ${id}: ${status?.error ?? status?.status}`);
  const video = page.locator('video.episode-preview');
  await video.waitFor({ timeout: 20000 });
  await video.evaluate(async v => { v.muted = true; await v.play(); });
  await page.waitForFunction(() => document.querySelector('video')?.currentTime > 0.5);
  const media = await video.evaluate(v => ({ width: v.videoWidth, height: v.videoHeight, duration: v.duration, time: v.currentTime, error: v.error?.code ?? null }));
  await video.scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(output, `${id}-desktop.png`) });
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: '영상 받기', exact: true }).click();
  const file = await download;
  await file.saveAs(path.join(output, `${id}.mp4`));
  if (await file.failure()) throw new Error('download failed');
  await page.reload();
  await video.waitFor({ timeout: 20000 });
  await page.setViewportSize({ width: 390, height: 844 });
  await video.scrollIntoViewIfNeeded();
  const noOverflow = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
  await page.screenshot({ path: path.join(output, `${id}-mobile.png`) });
  if (!noOverflow || pageErrors.length) throw new Error('UI layout or runtime errors');
  const report = { jobId: id, status: status.status, harness: status.harnessId, version: status.harnessVersion,
    imageStyle: status.imageStyle, voiceProvider: status.voiceProvider, mode, media, download: file.suggestedFilename(),
    reload: true, mobileNoOverflow: noOverflow, pageErrors, qualityGate: status.qualityGateStatus };
  await writeFile(path.join(output, `${id}-report.json`), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally { await browser.close(); }
