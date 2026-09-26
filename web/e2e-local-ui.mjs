import { chromium } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const token = process.env.LOCAL_PILOT_TOKEN;
if (!token) throw new Error('LOCAL_PILOT_TOKEN is required');
const root = process.env.LOCAL_SITE_URL ?? 'http://127.0.0.1:18776/';
const browser = await chromium.launch({ channel: 'chrome' });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  await page.goto(root);
  await page.getByText('제작 방식: 로컬 그래픽', { exact: false }).waitFor();
  if (await page.locator('#image-model').count()) throw new Error('GPT image selector must not appear in local mode');
  if (await page.locator('#creative-harness option[value="classic-slide"]').count()) {
    await page.locator('#creative-harness').selectOption('classic-slide');
    await page.locator('#image-model').waitFor();
    await page.locator('#creative-harness').selectOption('astra-motion');
    await page.getByText('제작 방식: 로컬 그래픽', { exact: false }).waitFor();
  }
  await page.getByLabel('접근 토큰', { exact: true }).fill(token);
  const full = await readFile('../experiments/motion-style-v08/attention-script.md', 'utf8');
  await page.getByLabel('영상 대본', { exact: true }).fill(full);
  await page.locator('#narration-speed').focus();
  await page.locator('#narration-speed').press('End');
  await page.locator('#narration-speed').press('ArrowLeft');
  await page.locator('#narration-speed').press('ArrowLeft');
  await page.waitForTimeout(1500);
  process.stdout.write(`duration UI: ${await page.locator('.duration-estimate').innerText()}\n`);
  await page.getByText('최대 1분 0초를 넘습니다', { exact: false }).waitFor();
  await page.getByRole('button', { name: '영상 만들기' }).click();
  await page.getByRole('alert').getByText('예상 길이가 1분 0초를 넘습니다', { exact: false }).waitFor();
  await page.getByLabel('영상 대본', { exact: true }).fill(
    '새로 눈여겨본 자동차가 거리에서 자꾸 보입니다. 차가 늘어난 게 아닙니다. 뇌가 관심 대상을 더 자주 알아차리는 겁니다.');
  await page.getByRole('button', { name: /내러티브형/ }).click();
  await page.getByRole('button', { name: '영상 만들기' }).click();
  await page.waitForTimeout(1500);
  const submissionError = await page.locator('.composer .error').allInnerTexts();
  if (submissionError.length) throw new Error(`video submission failed: ${submissionError.join('; ')}`);
  await page.locator('.job-card').waitFor({ timeout: 15000 });
  await page.locator('.episode-preview').waitFor({ timeout: 180000 });
  const ready = await page.locator('.episode-preview').evaluate(video => video.readyState >= 1);
  if (!ready) throw new Error('local video did not load');
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', { name: '영상 받기' }).click();
  const download = await downloadEvent;
  await download.saveAs('../experiments/motion-style-v08/local-ui-download.mp4');
  await page.screenshot({ path: '../experiments/motion-style-v08/local-ui-desktop.png', fullPage: true });
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto(root);
  await mobile.getByText('제작 방식: 로컬 그래픽', { exact: false }).waitFor();
  await mobile.screenshot({ path: '../experiments/motion-style-v08/local-ui-mobile.png', fullPage: true });
  if (await mobile.evaluate(() => document.documentElement.scrollWidth > innerWidth)) {
    throw new Error('mobile page overflows horizontally');
  }
  process.stdout.write('local UI: duration warning, create, playback, download, mobile layout PASS\n');
} finally {
  await browser.close();
}
