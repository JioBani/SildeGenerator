import { test, expect } from '@playwright/test';
import { creatorFixture } from './creator-fixture';

test('private slide and hybrid candidates remain hidden', async ({ page }) => {
  await page.route('**/api/**', async route => {
    if (!route.request().url().endsWith('/options/harnesses')) return creatorFixture(route);
    await route.fulfill({ json: route.request().url().endsWith('/options/harnesses') ? [
      { id: 'classic-slide', version: '1.2.0', display_name: '기본 슬라이드', compatible: true, public: true },
      { id: 'narrative-slide', version: '0.1.0', display_name: '강화 슬라이드', compatible: true, public: false },
      { id: 'hybrid-story', version: '0.1.0', display_name: '모션·슬라이드 혼합형', compatible: true, public: false },
    ] : [] });
  });
  await page.goto('/');
  await expect(page.locator('#creative-harness option[value="classic-slide"]')).toHaveCount(1);
  await expect(page.locator('#creative-harness option[value="hybrid-story"]')).toHaveCount(0);
  await expect(page.locator('#creative-harness option[value="narrative-slide"]')).toHaveCount(0);
});

test('authorized options preserve independent labels and request IDs', async ({ page }) => {
  const requests: Record<string, unknown>[] = [];
  await page.route('**/api/**', async route => {
    const url = route.request().url();
    if (url.endsWith('/options/harnesses')) {
      // Synthetic server publication, not a change to real manifests.
      await route.fulfill({ json: [
        { id: 'narrative-slide', version: '0.1.0', display_name: '강화 슬라이드', compatible: true, public: true },
        { id: 'hybrid-story', version: '0.1.0', display_name: '모션·슬라이드 혼합형', compatible: true, public: true },
      ] });
    } else if (url.endsWith('/api/jobs') && route.request().method() === 'POST') {
      requests.push(route.request().postDataJSON());
      await route.fulfill({ status: 400, json: { message: 'Test ends before providers' } });
    } else { await creatorFixture(route); }
  });
  await page.goto('/');
  await page.getByLabel('접근 토큰', { exact: true }).fill('test-only');
  await page.getByLabel('영상 대본', { exact: true }).fill('그는 동료를 발견하고 돌아섰습니다.');
  for (const [id, title] of [['narrative-slide', '슬라이드 영상'], ['hybrid-story', '모션·슬라이드 혼합 영상']]) {
    await page.getByLabel('영상 구성 방식').selectOption(id);
    await expect(page.getByRole('heading', { level: 1 })).toContainText(title);
    await page.getByRole('button', { name: /실사 영화/ }).click();
    await expect(page.getByText('음성 대본 미리보기')).toBeVisible();
    await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
    await expect.poll(() => requests.at(-1)?.harnessId).toBe(id);
    expect(requests.at(-1)?.imageStyle).toBe('cinematic_realism');
    expect(requests.at(-1)).not.toHaveProperty('motionStyleId');
  }
});
