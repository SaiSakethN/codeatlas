import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  if (process.env.E2E_PASSWORD) {
    const response = await page.request.post("/api/session", {
      headers: { Origin: "http://127.0.0.1:3000" },
      data: { password: process.env.E2E_PASSWORD },
    });
    expect(response.ok()).toBeTruthy();
  }
});

test("production session rejects anonymous access and cross-origin mutations", async ({ playwright }) => {
  test.skip(!process.env.E2E_PASSWORD, "Requires production session configuration.");
  const context = await playwright.request.newContext({ baseURL: "http://127.0.0.1:3000" });
  expect((await context.get("/api/backend/api/repositories")).status()).toBe(401);
  expect((await context.post("/api/session", {
    headers: { Origin: "https://untrusted.example" }, data: { password: "invalid" },
  })).status()).toBe(403);
  await context.dispose();
});

test("landing and responsive layout", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "A new codebase. A clearer way in." })).toBeVisible();
  await page.screenshot({ path: "../docs/screenshots/landing.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("link", { name: "Explore a repository" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});

test("public repository import, exploration, architecture and source", async ({ page }) => {
  test.skip(process.env.E2E_LIVE !== "1", "Requires the local API and embedding provider.");
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Import repository", exact: true }).click();
  await page.getByLabel("Public GitHub repository URL").fill("https://github.com/psf/requests");
  await page.getByRole("button", { name: "Import & index" }).click();
  await expect(page.getByRole("heading", { name: "Less searching. More understanding." })).toBeVisible({ timeout: 180000 });
  await page.getByRole("button", { name: "Repository overview", exact: true }).click();
  await expect(page.getByRole("heading", { name: "requests", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Architecture", exact: true }).click();
  await expect(page.locator(".react-flow")).toBeVisible();
  await page.getByRole("button", { name: "Onboarding", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Get oriented." })).toBeVisible();
  await page.getByRole("button", { name: "Change impact", exact: true }).click();
  await expect(page.getByText("Requires at least two local commits", { exact: false })).toBeVisible();
  await page.getByLabel("Filter files").fill("adapters.py");
  await page.locator(".file-tree").getByText("src", { exact: true }).click();
  await page.locator(".file-tree").getByText("requests", { exact: true }).click();
  await page.locator(".file-tree").getByRole("button", { name: "adapters.py" }).click();
  await expect(page.getByText("src/requests/adapters.py", { exact: true })).toBeVisible();
  await expect(page.getByText("Lines 1–120")).toBeVisible();
  await page.getByRole("button", { name: "Investigation", exact: true }).click();
  await page.screenshot({ path: "../docs/screenshots/workspace.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Close source evidence" }).click();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByLabel("Repository navigation")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});

test("live RAG and agent answers expose inspectable evidence", async ({ page }) => {
  test.skip(process.env.E2E_AI !== "1", "Opt-in live inference check.");
  await page.goto("/workspace");
  await page.getByLabel("Ask about this repository").fill("How does HTTPAdapter initialize its retry configuration?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.locator(".message")).toHaveCount(1, { timeout: 180000 });
  await expect(page.locator(".message .citation").first()).toBeVisible();
  await page.locator(".message .citation").first().click();
  await expect(page.locator(".source-path")).toBeVisible();
  await page.getByLabel("Investigation mode").selectOption("agent");
  await page.getByLabel("Ask about this repository").fill("Find HTTPAdapter and inspect how it initializes retries.");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.locator(".message")).toHaveCount(2, { timeout: 180000 });
  await page.screenshot({ path: "../docs/screenshots/investigation.png", fullPage: true });
  const metadata = await page.locator(".message").allTextContents();
  console.log("Live response metadata:", metadata.map(text => text.slice(-240)));
});
