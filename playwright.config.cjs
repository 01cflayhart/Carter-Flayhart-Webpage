const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/browser',
  testMatch: 'dashboard.spec.cjs',
  outputDir: 'test-results/api',
  fullyParallel: true,
  workers: 2,
  timeout: 45000,
  use: { baseURL: 'http://127.0.0.1:8766', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } }
  ],
  webServer: { command: 'python3 -m tennis.server --port 8766', url: 'http://127.0.0.1:8766/api/meta?tour=ATP', reuseExistingServer: false }
});
