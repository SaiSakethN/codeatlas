import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests", timeout: 240000, workers: 1,
  use: { baseURL: "http://127.0.0.1:3000", ...devices["Desktop Chrome"], channel: process.env.CI ? undefined : "chrome" },
  reporter: "list",
});
