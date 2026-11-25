import { defineConfig, devices } from '@playwright/test';

// Browser end-to-end tests (e2e/*.e2e.js).
//
// They need a running backend with the demo data loaded (seed_initial_data.py and
// scripts/seed_demo_clinical_data.py) and a frontend build that points at it:
//   VITE_API_BASE_URL=http://localhost:8000 npm run build
//   npm run test:e2e
// See the README section "Running the tests" and .github/workflows/tests.yml.
const PORT = Number(process.env.E2E_PORT || 5173);

export default defineConfig({
	testDir: './e2e',
	testMatch: '**/*.e2e.js',
	fullyParallel: false,
	workers: 1,
	timeout: 90_000,
	expect: { timeout: 15_000 },
	retries: process.env.CI ? 1 : 0,
	reporter: [['list']],
	use: {
		baseURL: `http://localhost:${PORT}`,
		trace: 'retain-on-failure'
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
	webServer: {
		command: `npm run preview -- --port ${PORT} --strictPort`,
		url: `http://localhost:${PORT}`,
		reuseExistingServer: !process.env.CI,
		timeout: 120_000
	}
});
