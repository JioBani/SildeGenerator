import type { Route } from '@playwright/test';

export const publicHarnesses = [
  { id: 'astra-motion', version: '0.9.1', display_name: '모션그래픽', compatible: true, public: true },
  { id: 'classic-slide', version: '1.2.0', display_name: '기본 슬라이드', compatible: true, public: true },
];
export async function creatorFixture(route: Route) {
  const url = route.request().url();
  if (url.endsWith('/options/harnesses')) return route.fulfill({ json: publicHarnesses });
  if (url.endsWith('/options/production')) return route.fulfill({ json: { imageProvider: 'oauth', voiceProvider: 'microsoft_edge', motionImageProvider: 'local_graphic' } });
  if (url.endsWith('/estimate')) return route.fulfill({ json: { narrationText: route.request().postDataJSON().scenario, narrationChars: 20, estimatedSeconds: 8, maximumSeconds: 60 } });
  if (url.endsWith('/wallet')) return route.fulfill({ json: { enabled: false } });
  return route.fulfill({ json: [] });
}
