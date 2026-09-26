import { test, expect } from '@playwright/test';
const frame = (name: string, color: string, width = 64) => ({ name, mimeType: 'image/svg+xml', buffer: Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="36"><rect width="100%" height="100%" fill="${color}"/></svg>`) });
test('matches filenames, compares pixels, rejects missing and mismatched frames', async ({ page }) => {
  await page.goto('/frame-review');
  await page.getByLabel('기준 프레임', { exact: true }).setInputFiles([frame('001.svg', 'red'), frame('002.svg', 'red'), frame('003.svg', 'red')]);
  await page.getByLabel('후보 프레임', { exact: true }).setInputFiles([frame('001.svg', 'red'), frame('002.svg', 'blue')]);
  await expect(page.getByRole('status')).toContainText('0.00%');
  await page.getByLabel('다음 프레임').click();
  await expect(page.getByRole('status')).toContainText('100.00%');
  await page.getByLabel('다음 프레임').click();
  await expect(page.getByRole('status')).toHaveText('대응 프레임 누락');
  await page.getByLabel('후보 프레임', { exact: true }).setInputFiles([frame('001.svg', 'red', 32)]);
  await expect(page.getByRole('status')).toHaveText('이미지 크기 불일치');
});
test('desktop and mobile comparison surfaces remain visible', async ({ page }) => {
  await page.goto('/frame-review');
  await page.getByLabel('기준 프레임', { exact: true }).setInputFiles(frame('001.svg', 'red'));
  await page.getByLabel('후보 프레임', { exact: true }).setInputFiles(frame('001.svg', 'blue'));
  await expect(page.locator('main')).toHaveAttribute('data-ready', 'true');
  await page.screenshot({ path: 'test-results/frame-review-desktop.png', fullPage: true, animations: 'disabled' });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('img', { name: '기준', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/frame-review-mobile.png', fullPage: true, animations: 'disabled' });
});
