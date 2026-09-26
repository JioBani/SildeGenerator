import { test, expect } from '@playwright/test';
import { creatorFixture } from './creator-fixture';

test('creator defaults to the promoted motion engine and retains slide video', async ({ page }) => {
  const requests: Record<string, unknown>[] = [];
  await page.route('**/api/**', async route => {
    if (route.request().method() === 'POST' && route.request().url().endsWith('/api/jobs')) {
      requests.push(route.request().postDataJSON());
      await route.fulfill({ status: 202, json: { id: '00000000-0000-0000-0000-000000000001', status: 'queued', progress: 0 } });
      return;
    }
    if (route.request().url().endsWith('/options/harnesses')) {
      await route.fulfill({ json: [
        { id: 'classic-slide', version: '1.1.0', display_name: '기본 슬라이드', compatible: true, public: true },
        { id: 'astra-motion', version: '0.8.0', display_name: '모션그래픽', compatible: true, public: true },
      ] });
      return;
    }
    await creatorFixture(route);
  });

  await page.goto('/');
  await expect(page.getByRole('group', { name: '영상 장르' })).toHaveCount(0);
  await expect(page.getByLabel('영상 구성 방식').locator('option[value="astra-motion"]')).toHaveCount(1);
  await expect(page.getByLabel('영상 구성 방식')).toHaveValue('astra-motion');
  await expect(page.getByText('모션그래픽 영상', { exact: true }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: /내러티브형/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /교육·정보형/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /귀여운 캐릭터/ })).toHaveCount(0);
  await page.getByLabel('접근 토큰', { exact: true }).fill('test-only');
  await page.getByLabel('영상 대본', { exact: true }).fill('GPU 계산 원리를 시각적으로 설명합니다.');
  await expect(page.getByText('음성 대본 미리보기')).toBeVisible();
  await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
  await expect.poll(() => requests.length).toBe(1);
  expect(requests[0]).toMatchObject({ harnessId: 'astra-motion', motionStyleId: 'narrative', aspectRatio: '16:9', subtitlesEnabled: true });
  expect(requests[0]).not.toHaveProperty('imageStyle');
  expect(requests[0]).not.toHaveProperty('genreId');
  await page.getByLabel('영상 구성 방식').selectOption('classic-slide');
  await expect(page.getByText('슬라이드 영상', { exact: true }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: /귀여운 캐릭터/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /내러티브형/ })).toHaveCount(0);
});

test('create explains blocking inputs while keeping the button usable', async ({ page }) => {
  await page.route('**/api/**', creatorFixture);
  await page.goto('/');
  const create = page.getByRole('button', { name: '영상 만들기', exact: true });
  await create.click();
  await expect(page.getByRole('alert')).toContainText('대본을 입력');
  await page.getByLabel('영상 대본', { exact: true }).fill('빛은 어디에서 올까요?');
  await create.click();
  await expect(page.getByRole('alert')).toContainText('접근 토큰');
  await expect(page.getByLabel('접근 토큰', { exact: true })).toBeFocused();
});

test('creator previews only narration extracted from a timed storyboard', async ({ page }) => {
  await page.route('**/api/**', route => {
    if (route.request().url().endsWith('/api/jobs/estimate')) {
      return route.fulfill({ json: {
        title: '영화 속 프레임의 비밀', narrationText: '시선이 화면 중앙으로 향합니다.',
        narrationChars: 17, estimatedSeconds: 5, maximumSeconds: 60,
      } });
    }
    return creatorFixture(route);
  });
  await page.goto('/');
  await page.getByLabel('영상 대본', { exact: true }).fill('- **[00~03초] 화면: 빨간 격자선**\n- **나레이션:** "시선이 화면 중앙으로 향합니다."');
  await page.getByText('음성 대본 미리보기').click();
  await expect(page.locator('.narration-preview p')).toHaveText('시선이 화면 중앙으로 향합니다.');
  await expect(page.locator('.narration-preview p')).not.toContainText('화면:');
});

test('cinematic style cards select the supported slide renderer and art preset', async ({ page }) => {
  const requests: Record<string, unknown>[] = [];
  await page.route('**/api/**', route => {
    if (route.request().url().endsWith('/options/harnesses')) return route.fulfill({ json: [
      { id: 'astra-motion', version: '0.9.1', display_name: '모션그래픽', compatible: true, public: true },
      { id: 'classic-slide', version: '1.2.0', display_name: '기본 슬라이드 연출', compatible: true, public: true },
    ] });
    if (route.request().method() === 'POST' && route.request().url().endsWith('/api/jobs')) {
      requests.push(route.request().postDataJSON());
      return route.fulfill({ status: 202, json: { id: '00000000-0000-0000-0000-000000000002', status: 'queued', progress: 0 } });
    }
    return creatorFixture(route);
  });
  for (const [index, [label, preset]] of [
    ['실사 영화', 'cinematic_realism'], ['3D 애니메이션', 'animation_3d'],
    ['디즈니풍', 'disney_animation'], ['디스토피아', 'dystopian'],
  ].entries()) {
    await page.goto('/');
    await page.getByRole('button', { name: new RegExp(`^${label}`) }).click();
    await expect(page.getByLabel('영상 구성 방식')).toHaveValue('classic-slide');
    await expect(page.getByRole('button', { name: new RegExp(`^${label}`) })).toHaveAttribute('aria-pressed', 'true');
    await page.getByLabel('접근 토큰', { exact: true }).fill('test-only');
    await page.getByLabel('영상 대본', { exact: true }).fill('도시의 밤을 바라봅니다.');
    await expect(page.getByText('음성 대본 미리보기')).toBeVisible();
    await page.getByRole('button', { name: '영상 만들기', exact: true }).click();
    await expect.poll(() => requests.length).toBe(index + 1);
    expect(requests[index]).toMatchObject({ harnessId: 'classic-slide', imageStyle: preset });
    expect(requests[index]).not.toHaveProperty('motionStyleId');
  }
});
