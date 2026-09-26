import { chromium } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const base = join(root, 'experiments/image-motion-intake/output');
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' });
const results = [];
try {
  for (const name of ['f-actor', 'd-rest']) {
    const page = await browser.newPage({ viewport: { width: 1360, height: 1000 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(join(base, name, 'review.html')).href);
    await page.evaluate(async () => {
      const img = new Image(); img.src = document.querySelector('svg image').getAttribute('href'); await img.decode();
    });
    await page.screenshot({ path: join(base, name, 'desktop.png'), fullPage: true });
    await page.locator('svg').screenshot({ path: join(base, name, 'overlay.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: join(base, name, 'mobile.png'), fullPage: true });
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) errors.push('horizontal_overflow');
    const report = JSON.parse(readFileSync(join(base, name, 'analysis.json'), 'utf8'));
    if (report.actions.some(a => a.execution_allowed || a.production_ready)) errors.push('intake_cannot_grant_approval');
    results.push({ name, errors, status: report.status });
    await page.close();
  }
} finally { await browser.close(); }
writeFileSync(join(base, 'browser-audit.json'), JSON.stringify(results, null, 2));
console.log(JSON.stringify(results));
if (results.some(r => r.errors.length)) process.exitCode = 1;
