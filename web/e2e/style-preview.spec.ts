import { test, expect } from '@playwright/test';
import { creatorFixture } from './creator-fixture';

test('slide styles each show their own representative image without a provider call', async ({ page }) => {
  let posts = 0;
  await page.route('**/api/**', async route => {
    if (route.request().method() === 'POST') posts++;
    await creatorFixture(route);
  });
  await page.goto('/');
  await page.getByLabel('영상 구성 방식').selectOption('classic-slide');
  for (const [name, file] of [
    ['귀여운 캐릭터', 'slide-character-original'], ['판타지 애니메이션', 'slide-fantasy-original'],
    ['실사 영화', 'cinematic-realism-v1'], ['3D 애니메이션', 'animation-3d-v1'],
    ['디즈니풍', 'disney-animation-v1'], ['디스토피아', 'dystopian-v1'],
  ]) {
    const choice = page.getByRole('button', { name: new RegExp(name) });
    await choice.click();
    await expect(choice).toHaveAttribute('aria-pressed', 'true');
    const preview = choice.locator('img');
    await expect(preview).toHaveAttribute('src', `/style-previews/${file}.png`);
    await expect.poll(() => preview.evaluate((el: HTMLImageElement) => el.naturalWidth)).toBeGreaterThan(1000);
    await choice.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `test-results/${file}-desktop.png` });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('.style-options').scrollIntoViewIfNeeded();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/style-preview-mobile.png' });
  await expect(page.locator('.style-choice')).toHaveCount(6);
  expect(posts).toBe(0);
});

test('new styles cannot accidentally request the local illustration fallback', async ({ page }) => {
  const requests: Record<string, unknown>[] = [];
  await page.route('**/api/**', async route => {
    const url = route.request().url();
    if (url.endsWith('/api/jobs') && route.request().method() === 'POST') {
      requests.push(route.request().postDataJSON());
      await route.fulfill({ status: 400, json: { message: 'test stops before production' } });
    } else if (url.endsWith('/options/production')) {
      await route.fulfill({ json: { imageProvider: 'oauth', voiceProvider: 'microsoft_edge', slideV05LocalImages: true } });
    } else {
      await creatorFixture(route);
    }
  });
  await page.goto('/');
  await page.getByLabel('영상 구성 방식').selectOption('classic-slide');
  await page.getByLabel('접근 토큰', { exact: true }).fill('test-only');
  await page.getByLabel('영상 대본', { exact: true }).fill('그는 동료를 발견하고 돌아섰습니다.');
  await expect(page.getByText('음성 대본 미리보기')).toBeVisible();
  await page.locator('#local-slide-images').check();
  for (const [name, id] of [['실사 영화', 'cinematic_realism'], ['3D 애니메이션', 'animation_3d'], ['디즈니풍', 'disney_animation'], ['디스토피아', 'dystopian']]) {
    await page.getByRole('button', { name: new RegExp(name) }).click();
    await expect(page.locator('#local-slide-images')).toHaveCount(0);
    await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
    await expect.poll(() => requests.at(-1)?.imageStyle).toBe(id);
    expect(requests.at(-1)).not.toHaveProperty('sceneVisualMode');
  }
});
