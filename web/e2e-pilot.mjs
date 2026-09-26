import { chromium } from '@playwright/test';

const token = process.env.PILOT_TOKEN;
if (!token) throw new Error('PILOT_TOKEN is required');
const root = 'http://127.0.0.1:18776/';
const browser = await chromium.launch({ channel: 'chrome' });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  await page.goto(root);
  await page.getByLabel('접근 토큰', { exact: true }).fill(token);
  await page.getByLabel('영상 대본', { exact: true }).fill('밤의 가로등 빛을 발견한 사람이 커튼을 닫습니다. 방은 다시 어두워집니다.');
  await page.getByRole('button', { name: /교육·정보형/ }).click();
  await page.screenshot({ path: '../experiments/motion-style-v08/pilot-desktop.png', fullPage: true });
  await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
  await page.locator('.episode-preview').waitFor({ timeout: 120000 });
  const playbackReady = await page.locator('.episode-preview').evaluate(video => video.readyState >= 1);
  if (!playbackReady) throw new Error('completed video did not load');
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', { name: '영상 받기' }).click();
  const download = await downloadEvent;
  await download.saveAs('../experiments/motion-style-v08/pilot-ui-download.mp4');
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto(root);
  await mobile.screenshot({ path: '../experiments/motion-style-v08/pilot-mobile.png', fullPage: true });
  const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (overflow) throw new Error('mobile page overflows horizontally');
  console.log('pilot UI: create, playback, download, desktop/mobile layout PASS');
} finally {
  await browser.close();
}
