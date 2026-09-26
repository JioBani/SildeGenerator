import { defineConfig } from '@playwright/test';
const port = Number(process.env.PLAYWRIGHT_PORT ?? 5187);
export default defineConfig({
  testDir: './e2e', timeout: 30000,
  use: { baseURL: `http://127.0.0.1:${port}`, channel: 'chrome', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: { command: `npm run dev -- --host 127.0.0.1 --port ${port} --strictPort`, url: `http://127.0.0.1:${port}`, reuseExistingServer: false },
});
