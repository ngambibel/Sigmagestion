import { defineConfig, devices } from "@playwright/test";

/**
 * Tests bout-en-bout (§15.2 du cahier). Nécessite les serveurs lancés :
 *   - backend : `docker compose up` (http://localhost:8000)
 *   - frontend : `npm run dev` (http://localhost:5173)
 * puis `npx playwright test`.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    locale: "fr-FR",
    timezoneId: "Africa/Douala",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
