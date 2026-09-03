import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 360_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  outputDir: 'test-results',
  use: {
    baseURL: process.env.PO_AGENT_UI_BASE_URL ?? 'http://127.0.0.1:5175',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 30_000,
    navigationTimeout: 60_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: process.env.PO_AGENT_E2E_EXTERNAL_FRONTEND === '1'
    ? undefined
    : {
        command: 'npm run dev -- --host 127.0.0.1',
        url: process.env.PO_AGENT_UI_BASE_URL ?? 'http://127.0.0.1:5175',
        reuseExistingServer: true,
        timeout: 120_000,
      },
})
