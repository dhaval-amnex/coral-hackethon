import { expect, test } from "@playwright/test"

test.beforeEach(async ({ page }) => {
  await page.route("**/api/source-health**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        sources: {
          pagerduty: "ok",
          github: "ok",
          slack: "ok",
          datadog: "ok",
        },
        env_missing: {},
      }),
    })
  })

  await page.route("**/api/artifacts/status**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        artifacts: {
          judge_pack_zip: {
            exists: true,
            path: "output/judge_pack.zip",
            download_url: "/api/artifacts/download?path=output/judge_pack.zip",
          },
        },
      }),
    })
  })

  await page.route("**/api/readiness**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        release_check: {
          go_for_submission: true,
          go_for_live_submission: true,
          progress_percent: 100,
          scorecard_overall: 85,
          quality_gate_passed: true,
          live_readiness: true,
          live_blockers: [],
          next_actions: ["proceed with submission"],
        },
        live_readiness: {},
        scorecard: { dimensions: { reliability: 100, speed: 60, impact: 80 } },
        quality_gate: { checks: [{ check: "success_rate_threshold", passed: true, detail: { actual: 1.0 } }] },
        demo_report: {},
        impact_report: {},
      }),
    })
  })

  await page.route("**/api/run-history**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        rows: [
          { incident_id: "INC-1001", query_errors: 0 },
          { incident_id: "INC-1002", query_errors: 1 },
        ],
      }),
    })
  })

  await page.route("**/api/ship-readiness", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        demo_report: {},
        quality_gate: {},
        scorecard: {},
        live_readiness: {},
        handoff_summary: {},
        release_check: {
          go_for_submission: true,
          go_for_live_submission: true,
          progress_percent: 100,
          scorecard_overall: 85,
          quality_gate_passed: true,
          live_readiness: true,
          live_blockers: [],
          next_actions: ["proceed with submission"],
        },
      }),
    })
  })

  await page.route("**/api/judge-pack", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        source_dir: "output/bundles/submission_bundle_INC-1001",
        output_zip: "output/judge_pack.zip",
      }),
    })
  })

  await page.route("**/api/analyze/start", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ job_id: "job-1", status: "running" }),
    })
  })

  await page.route("**/api/analyze/status**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: "job-1",
        status: "done",
        error: "",
        result: {
          incident_id: "INC-1001",
          total_duration_ms: 1000,
          workflow_log: [],
          brief: {
            incident_id: "INC-1001",
            summary: "ok",
            probable_root_cause: "deploy",
            confidence: "high",
            impacted_services: ["checkout"],
            owners: ["alice"],
            evidence: [],
            recommended_actions: [],
            executive_summary: [],
            diagnostics: {},
          },
        },
      }),
    })
  })
})

test("dashboard presenter mode and full demo entry are visible", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByText("Incident Captain")).toBeVisible()
  await expect(page.getByRole("button", { name: "Start Full Demo" })).toBeVisible()
  await page.getByRole("button", { name: "Presenter Mode: OFF" }).click()
  await expect(page.getByText("Presenter Checklist")).toBeVisible()
})

test("submission console can run release check and judge pack", async ({ page }) => {
  await page.goto("/")
  await page.getByRole("button", { name: "Submission", exact: true }).click()
  await expect(page.getByText("Submission Console")).toBeVisible()
  await page.getByRole("button", { name: "Run Release Check" }).click()
  await expect(page.getByText("Go for submission: true")).toBeVisible()
  await page.getByRole("button", { name: "Generate Judge Pack" }).click()
  await expect(page.getByRole("link", { name: "Download judge_pack.zip" })).toBeVisible()
})
