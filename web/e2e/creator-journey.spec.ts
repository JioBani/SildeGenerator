import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { creatorFixture } from './creator-fixture';

const movie = readFileSync(new URL('./fixtures/playback-smoke.mp4', import.meta.url));
const a = '00000000-0000-0000-0000-000000000001';
const b = '00000000-0000-0000-0000-000000000002';
const completed = (id: string) => ({ id, status: 'completed', progress: 100, currentStage: 'done', error: null });

test('script, style, submit, progress, playback, download and reload', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  let created = false;
  let polls = 0;
  await page.route('**/api/**', async route => {
    const url = route.request().url();
    if (url.endsWith('/api/jobs') && route.request().method() === 'POST') {
      expect(route.request().postDataJSON()).toMatchObject({ harnessId: 'astra-motion', motionStyleId: 'educational_info' });
      created = true;
      return route.fulfill({ status: 202, json: { id: a, status: 'queued', progress: 0 } });
    }
    if (url.endsWith(`/jobs/${a}`)) return route.fulfill({ json: ++polls < 2 ? { id: a, status: 'running', progress: 50 } : completed(a) });
    if (url.endsWith(`/jobs/${a}/video`)) return route.fulfill({ contentType: 'video/mp4', body: movie });
    if (url.endsWith('/api/jobs')) return route.fulfill({ json: created ? [{ ...completed(a), title: '이번 대본', queuedAt: new Date().toISOString() }] : [] });
    return creatorFixture(route);
  });
  await page.goto('/');
  await page.getByLabel('접근 토큰', { exact: true }).fill('test-only');
  await page.getByLabel('영상 대본', { exact: true }).fill('시선이 화면 중앙으로 향합니다.');
  await page.getByRole('button', { name: /교육·정보형/ }).click();
  await expect(page.getByText('음성 대본 미리보기')).toBeVisible();
  await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
  const video = page.locator('video.episode-preview');
  await expect(video).toBeVisible({ timeout: 15000 });
  await video.evaluate(async (v: HTMLVideoElement) => { v.muted = true; await v.play(); });
  await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.currentTime)).toBeGreaterThan(0);
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: '영상 받기', exact: true }).click();
  expect((await download).suggestedFilename()).toBe(`slide-${a}.mp4`);
  await page.reload();
  await expect(video).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await video.scrollIntoViewIfNeeded();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/creator-playback-mobile.png' });
  expect(errors).toEqual([]);
});

test('switching jobs clears old playback and failed media can be retried', async ({ page }) => {
  let failSecondVideo = true;
  await page.addInitScript(() => localStorage.setItem('slidegen.token', 'test-only'));
  await page.route('**/api/**', async route => {
    const url = route.request().url();
    if (url.endsWith('/api/jobs')) return route.fulfill({ json: [a, b].map((id, i) => ({ ...completed(id), title: `영상 ${i + 1}`, queuedAt: new Date().toISOString() })) });
    if (url.endsWith(`/jobs/${a}`)) return route.fulfill({ json: completed(a) });
    if (url.endsWith(`/jobs/${b}`)) return route.fulfill({ json: completed(b) });
    if (url.endsWith(`/jobs/${a}/video`)) return route.fulfill({ contentType: 'video/mp4', body: movie });
    if (url.endsWith(`/jobs/${b}/video`)) {
      if (failSecondVideo) return route.fulfill({ status: 503, json: { message: 'temporary' } });
      return route.fulfill({ contentType: 'video/mp4', body: movie });
    }
    return creatorFixture(route);
  });
  await page.goto(`/?job=${a}`);
  await expect(page.locator('video')).toBeVisible();
  const oldUrl = await page.locator('video').getAttribute('src');
  await page.getByRole('button', { name: /영상 2/ }).click();
  await expect(page.locator('video')).toHaveCount(0);
  await expect(page.getByRole('alert')).toContainText('영상을 불러오지 못했습니다');
  failSecondVideo = false;
  await page.getByRole('button', { name: '영상 다시 불러오기' }).click();
  await expect(page.locator('video')).toBeVisible();
  expect(await page.locator('video').getAttribute('src')).not.toBe(oldUrl);
});

test('failed settings do not invent renderers and retry recovers', async ({ page }) => {
  let fail = true;
  await page.route('**/api/**', route => route.request().url().endsWith('/options/harnesses') && fail
    ? route.fulfill({ status: 503, json: {} }) : creatorFixture(route));
  await page.goto('/');
  await expect(page.getByLabel('영상 구성 방식')).toBeDisabled();
  await expect(page.getByRole('alert')).toContainText('제작 설정');
  fail = false;
  await page.getByRole('button', { name: '제작 설정 다시 불러오기' }).click();
  await expect(page.getByLabel('영상 구성 방식')).toBeEnabled();
});

test('rejected narration parsing prevents generation and explains why', async ({ page }) => {
  let creates = 0;
  await page.route('**/api/**', route => {
    if (route.request().url().endsWith('/estimate')) return route.fulfill({ status: 400, json: { message: '읽을 나레이션이 없습니다.' } });
    if (route.request().method() === 'POST' && route.request().url().endsWith('/api/jobs')) creates++;
    return creatorFixture(route);
  });
  await page.goto('/');
  await page.getByLabel('접근 토큰', { exact: true }).fill('test-only');
  await page.getByLabel('영상 대본', { exact: true }).fill('화면: 도형만 표시');
  await expect(page.getByRole('alert')).toContainText('나레이션이 없습니다');
  await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
  expect(creates).toBe(0);
  await expect(page.getByLabel('영상 대본', { exact: true })).toBeFocused();
});

test('server rejects access token with an actionable message', async ({ page }) => {
  await page.route('**/api/**', route => route.request().method() === 'POST' && route.request().url().endsWith('/api/jobs')
    ? route.fulfill({ status: 401, json: { message: 'Unauthorized' } }) : creatorFixture(route));
  await page.goto('/');
  await page.getByLabel('접근 토큰', { exact: true }).fill('invalid');
  await page.getByLabel('영상 대본', { exact: true }).fill('빛이 창문으로 들어옵니다.');
  await expect(page.getByText('음성 대본 미리보기')).toBeVisible();
  await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('접근 토큰이 거부');
  await expect(page.getByLabel('접근 토큰', { exact: true })).toBeFocused();
});

test('sixty-second limit blocks motion but keeps long slide contract separate', async ({ page }) => {
  let creates = 0;
  await page.route('**/api/**', route => {
    if (route.request().url().endsWith('/estimate')) return route.fulfill({ json: { narrationText: '긴 대본', narrationChars: 800, estimatedSeconds: 80, maximumSeconds: 60 } });
    if (route.request().method() === 'POST' && route.request().url().endsWith('/api/jobs')) creates++;
    return creatorFixture(route);
  });
  await page.goto('/');
  await page.getByLabel('접근 토큰', { exact: true }).fill('test-only');
  await page.getByLabel('영상 대본', { exact: true }).fill('긴 대본입니다.');
  await expect(page.getByText('음성 대본 미리보기')).toBeVisible();
  await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
  expect(creates).toBe(0);
  await expect(page.locator('#narration-speed')).toBeFocused();
  await page.getByLabel('영상 구성 방식').selectOption('classic-slide');
  await expect(page.getByText('영상 한 편 최대 30분 0초')).toBeVisible();
});

test('failed job retry surfaces version conflict instead of silently doing nothing', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('slidegen.token', 'test-only'));
  await page.route('**/api/**', route => {
    if (route.request().url().endsWith(`/jobs/${a}`)) return route.fulfill({ json: { id: a, status: 'failed', progress: 5, error: '이미지 연결 실패' } });
    if (route.request().url().endsWith(`/jobs/${a}/remake`)) return route.fulfill({ status: 409, json: { message: '현재 제작 버전이 변경되었습니다.' } });
    return creatorFixture(route);
  });
  await page.goto(`/?job=${a}`);
  await page.getByRole('button', { name: '같은 설정으로 다시 만들기' }).click();
  await expect(page.getByText('현재 제작 버전이 변경되었습니다.')).toBeVisible();
  await expect(page.getByRole('button', { name: '같은 설정으로 다시 만들기' })).toBeEnabled();
});

test('hidden tabs stop polling and offscreen history does not fetch every thumbnail', async ({ page }) => {
  let reads = 0;
  let thumbnails = 0;
  await page.clock.install();
  await page.addInitScript(() => localStorage.setItem('slidegen.token', 'test-only'));
  await page.route('**/api/**', route => {
    const url = route.request().url();
    if (url.endsWith('/thumbnail')) { thumbnails++; return route.fulfill({ status: 404 }); }
    if (url.endsWith(`/jobs/${a}`)) { reads++; return route.fulfill({ json: { id: a, status: 'running', progress: 5 } }); }
    if (url.endsWith('/api/jobs')) {
      reads++;
      return route.fulfill({ json: Array.from({ length: 50 }, (_, i) => ({ ...completed(`history-${i}`), title: `이전 작업 ${i}`, hasThumbnail: true, queuedAt: new Date().toISOString() })) });
    }
    return creatorFixture(route);
  });
  await page.goto(`/?job=${a}`);
  await expect(page.locator('.my-job-row')).toHaveCount(50);
  expect(thumbnails).toBe(0);
  await page.evaluate(() => { Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' }); document.dispatchEvent(new Event('visibilitychange')); });
  const before = reads;
  await page.clock.runFor(65_000);
  expect(reads).toBe(before);
});
