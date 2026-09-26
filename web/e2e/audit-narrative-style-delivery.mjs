import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const target = new URL('../../output/narrative-style-smoke-v3/review.html', import.meta.url);
const output = new URL('../../output/narrative-style-smoke-v3/', import.meta.url);
const browser = await chromium.launch({ channel: 'chrome' });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto(target.href);
  for (const video of await page.locator('video').all()) {
    await video.evaluate(async el => {
      if (!el.readyState) await new Promise((resolve, reject) => {
        el.addEventListener('loadedmetadata', resolve, { once: true });
        el.addEventListener('error', () => reject(new Error('video failed to load')), { once: true });
      });
      if (el.videoWidth !== 1280 || el.videoHeight !== 720 || el.duration < 9 || el.duration > 12) {
        throw new Error('unexpected output dimensions or duration');
      }
      await new Promise(resolve => { el.addEventListener('seeked', resolve, { once: true }); el.currentTime = 5; });
    });
  }
  await page.screenshot({ path: fileURLToPath(new URL('review-desktop.png', output)), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error('horizontal overflow');
  await page.screenshot({ path: fileURLToPath(new URL('review-mobile.png', output)), fullPage: true });
  console.log('PASS: four real videos load and seek; desktop/mobile screenshots saved.');
} finally { await browser.close(); }
