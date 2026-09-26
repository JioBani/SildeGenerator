import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';

const output = new URL('../../output/hybrid-story-smoke-v3/', import.meta.url);
// file:// media taints canvas; use one short-lived same-origin review server.
const server = createServer(async (req, res) => {
  const files = { '/review.html': ['review.html', 'text/html; charset=utf-8'], '/delivery/hybrid.mp4': ['delivery/hybrid.mp4', 'video/mp4'] };
  const entry = files[new URL(req.url, 'http://localhost').pathname];
  if (!entry) { res.writeHead(404).end(); return; }
  try {
    const data = await readFile(new URL(entry[0], output));
    res.setHeader('Content-Type', entry[1]);
    const range = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range || '');
    if (range) {
      const start = Number(range[1]), end = range[2] ? Math.min(Number(range[2]), data.length - 1) : data.length - 1;
      if (start > end) { res.writeHead(416).end(); return; }
      res.writeHead(206, { 'Content-Range': `bytes ${start}-${end}/${data.length}`, 'Content-Length': end - start + 1, 'Accept-Ranges': 'bytes' });
      res.end(data.subarray(start, end + 1));
    } else { res.setHeader('Content-Length', data.length); res.end(data); }
  } catch { res.writeHead(500).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ channel: 'chrome' });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto(`http://127.0.0.1:${server.address().port}/review.html`);
  const frames = await page.locator('video').evaluate(async video => {
    if (!video.readyState) await new Promise((resolve, reject) => {
      video.addEventListener('loadedmetadata', resolve, { once: true });
      video.addEventListener('error', () => reject(new Error('video load failed')), { once: true });
    });
    if (video.videoWidth !== 1280 || video.videoHeight !== 720 || video.duration > 60) throw new Error('delivery contract mismatch');
    const result = [];
    for (const t of [3, 9.3, 15.1, 20, 30]) {
      await new Promise(resolve => { video.addEventListener('seeked', resolve, { once: true }); video.currentTime = t; });
      const canvas = document.createElement('canvas');
      canvas.width = 128; canvas.height = 72;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, 128, 72);
      const rgba = [...ctx.getImageData(0, 0, 128, 54).data];
      const channels = [0, 1, 2].map(c => rgba.filter((_, i) => i % 4 === c));
      const stddev = channels.map(values => {
        const mean = values.reduce((a, b) => a + b) / values.length;
        return Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length);
      });
      if (Math.max(...stddev) < 1.5) throw new Error(`blank picture at ${t}`);
      result.push({ time: t, stddev, pixels: rgba });
    }
    const delta = (a, b) => a.pixels.reduce((sum, x, i) => sum + Math.abs(x - b.pixels[i]), 0) / (a.pixels.length * 255);
    if (delta(result[1], result[2]) < .0005) throw new Error('diagram is frozen');
    if (delta(result[0], result[3]) < .05) throw new Error('registered source not visibly distinct');
    return result.map(({ pixels, ...row }) => row);
  });
  await page.screenshot({ path: fileURLToPath(new URL('review-desktop.png', output)), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error('horizontal overflow');
  await page.screenshot({ path: fileURLToPath(new URL('review-mobile.png', output)), fullPage: true });
  await writeFile(fileURLToPath(new URL('browser-observations.json', output)), JSON.stringify({ frames, scope: 'Playback, pixel presence, diagram change and responsive review only', human_approval: null }, null, 2));
  console.log('PASS: real video loads/seeks, three routes are visible, diagram changes, desktop/mobile review fits.');
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
