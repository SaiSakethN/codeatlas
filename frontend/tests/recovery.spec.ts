import { test, expect } from "@playwright/test";

const repository = { id: "fixture", name: "fixture", source: "https://github.com/example/fixture", statistics: { chunks: 2 } };
const overview = {
  name: "fixture", python_files: 1, symbols: 1, lines: 3, test_files: 0,
  nodes: [], edges: [], external_imports: {}, failed_files: [], limitations: "Static imports only.",
  onboarding: { summary: "Fixture", entrypoints: [], tests: [], suggested_questions: ["Explain the entry point."], method: "Static" },
};

test("expired session during a question returns to sign in", async ({ page }) => {
  await page.route("**/api/session", route => route.fulfill({ json: { ok: true } }));
  await page.route("**/api/backend/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/questions")) return route.fulfill({ status: 401, json: { error: { message: "Sign in to the workspace first." } } });
    if (path.endsWith("/repositories")) return route.fulfill({ json: [repository] });
    if (path.endsWith("/overview")) return route.fulfill({ json: overview });
    return route.fulfill({ json: path.endsWith("/tree") ? { files: [] } : { available: false } });
  });
  await page.goto("/workspace");
  await page.getByLabel("Ask about this repository").fill("Explain the entry point.");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Your investigation workspace" })).toBeVisible();
  await expect(page.getByLabel("Workspace password")).toBeVisible();
  await page.getByLabel("Workspace password").fill("test-only-recovery-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByLabel("Ask about this repository")).toBeVisible();
});

test("HTML backend failure offers a working connection retry", async ({ page }) => {
  let recovered = false;
  await page.route("**/api/backend/api/repositories", route => {
    return !recovered
      ? route.fulfill({ status: 503, contentType: "text/html", body: "<html>Service restarting</html>" })
      : route.fulfill({ json: [] });
  });
  await page.goto("/workspace");
  await expect(page.getByText("The backend is waking up or restarting.", { exact: false })).toBeVisible();
  recovered = true;
  await page.getByRole("button", { name: "Retry connection" }).click();
  await expect(page.getByLabel("Public GitHub repository URL")).toBeVisible();
});

test("index progress recovers after temporary backend failure", async ({ page }) => {
  let finished = false, polls = 0;
  await page.route("**/api/backend/**", async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith("/repositories")) {
      if (request.method() === "POST") return route.fulfill({ status: 202, json: { id: "job", status: "indexing", progress: 0 } });
      return route.fulfill({ json: finished ? [repository] : [] });
    }
    if (path.includes("/jobs/")) {
      polls++;
      if (polls === 1) return route.fulfill({ status: 503, json: { error: { message: "Backend restarting." } } });
      finished = true;
      return route.fulfill({ json: { id: "job", status: "completed", progress: 100, repository_id: "fixture" } });
    }
    if (path.endsWith("/overview")) return route.fulfill({ json: overview });
    return route.fulfill({ json: path.endsWith("/tree") ? { files: [] } : { available: false } });
  });
  await page.goto("/workspace");
  await page.getByLabel("Public GitHub repository URL").fill("https://github.com/example/fixture");
  await page.getByRole("button", { name: "Import & index" }).click();
  await expect(page.getByText("Progress updates will retry automatically.", { exact: false })).toBeVisible({ timeout: 8000 });
  await expect(page.getByRole("heading", { name: "Less searching. More understanding." })).toBeVisible({ timeout: 15000 });
  expect(polls).toBeGreaterThanOrEqual(2);
});
