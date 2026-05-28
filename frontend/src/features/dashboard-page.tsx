import { useEffect, useState } from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { ArtifactsStatusResponse, ReadinessResponse } from "@/lib/types"
import { getArtifactDownloadUrl, getReadiness } from "@/lib/api"

interface DashboardPageProps {
  activeIncidentId: string
  onNavigate: (section: "analyze" | "evidence" | "readiness" | "artifacts" | "submission" | "history") => void
  artifactsStatus: ArtifactsStatusResponse | null
  onRunFullDemo: () => Promise<void>
  demoRunning: boolean
  demoSteps: Array<{ name: string; status: "pending" | "running" | "done" | "failed"; detail?: string }>
  presenterMode: boolean
  onTogglePresenterMode: () => void
  onResetPresenterChecklist: () => void
  presenterChecklist: Array<{ name: string; done: boolean }>
}

export function DashboardPage({
  activeIncidentId,
  onNavigate,
  artifactsStatus,
  onRunFullDemo,
  demoRunning,
  demoSteps,
  presenterMode,
  onTogglePresenterMode,
  onResetPresenterChecklist,
  presenterChecklist,
}: DashboardPageProps) {
  const artifactEntries = artifactsStatus ? Object.entries(artifactsStatus.artifacts) : []
  const doneCount = presenterChecklist.filter((x) => x.done).length
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)

  useEffect(() => {
    getReadiness()
      .then((payload) => setReadiness(payload))
      .catch(() => setReadiness(null))
  }, [])

  const release = readiness?.release_check
  const blockers = release?.live_blockers ?? []

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card className="md:col-span-2 rounded-2xl border-2 shadow-sm">
        <CardHeader>
          <CardTitle>Live Readiness Score</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm md:grid-cols-4">
          <p>
            Score: <strong>{release?.scorecard_overall ?? "n/a"}</strong>
          </p>
          <p>
            Submission: <strong>{String(release?.go_for_submission ?? false)}</strong>
          </p>
          <p>
            Live: <strong>{String(release?.go_for_live_submission ?? false)}</strong>
          </p>
          <p>
            Blockers: <strong>{blockers.length}</strong>
          </p>
        </CardContent>
      </Card>
      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle>Mission Control</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <p>Active Incident: {activeIncidentId || "None"}</p>
          <p className="text-muted-foreground">
            Use Analyze to run cross-source investigation and then move to Readiness for submission state.
          </p>
        </CardContent>
      </Card>
      <Card className="rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <ul className="list-disc pl-5">
            <li>Run Analyze with incident ID</li>
            <li>Review Evidence Explorer</li>
            <li>Generate Ship-Readiness artifacts</li>
          </ul>
        </CardContent>
      </Card>
      <Card className="md:col-span-2 rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle>Demo Runbook ({doneCount}/{presenterChecklist.length} ready)</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <Button variant={presenterMode ? "default" : "outline"} onClick={onTogglePresenterMode}>
              {presenterMode ? "Presenter Mode: ON" : "Presenter Mode: OFF"}
            </Button>
            <Button variant="outline" onClick={onResetPresenterChecklist}>
              Reset Checklist
            </Button>
          </div>
          <ol className="grid gap-2">
            <li>1. Open Analyze and run incident investigation.</li>
            <li>2. Review correlated evidence and diagnostics.</li>
            <li>3. Confirm readiness and release-go signals.</li>
            <li>4. Generate artifacts and judge pack download.</li>
          </ol>
          <div className="flex flex-wrap gap-2">
            <Button variant="default" className="rounded-xl px-5 font-semibold" onClick={() => void onRunFullDemo()} disabled={demoRunning}>
              {demoRunning ? "Running Full Demo..." : "Start Full Demo"}
            </Button>
            <Button className="rounded-xl" onClick={() => onNavigate("analyze")}>Go to Analyze</Button>
            <Button variant="outline" onClick={() => onNavigate("evidence")}>
              Go to Evidence
            </Button>
            <Button variant="outline" onClick={() => onNavigate("readiness")}>
              Go to Readiness
            </Button>
            <Button variant="outline" onClick={() => onNavigate("artifacts")}>
              Go to Artifacts
            </Button>
            <Button variant="outline" onClick={() => onNavigate("submission")}>
              Go to Submission
            </Button>
          </div>
          {presenterMode ? (
            <div className="grid gap-1">
              <p className="font-medium">Presenter Checklist</p>
              <ol className="grid gap-1 text-xs">
                {presenterChecklist.map((item) => (
                  <li key={item.name} className={item.done ? "text-green-700" : "text-amber-700"}>
                    {item.done ? "done" : "pending"}: {item.name}
                  </li>
                ))}
              </ol>
              <div className="mt-2 rounded-xl border bg-muted/30 p-3 text-xs">
                <p className="font-medium">Demo Script (2 minutes)</p>
                <p>1. We unify PagerDuty, GitHub, Datadog, Slack evidence in one run.</p>
                <p>2. We show confidence, root-cause hints, and source-aware diagnostics.</p>
                <p>3. We run ship-readiness to produce a go/no-go submission signal.</p>
                <p>4. We generate judge pack artifacts for submission in one click.</p>
              </div>
            </div>
          ) : null}
          <div className="grid gap-1">
            <p className="font-medium">Demo Step Status</p>
            <ol className="grid gap-1 text-xs">
              {demoSteps.map((s) => (
                <li
                  key={s.name}
                  className={
                    s.status === "done"
                      ? "text-green-700"
                      : s.status === "failed"
                        ? "text-red-700"
                        : s.status === "running"
                          ? "text-blue-700"
                          : "text-muted-foreground"
                  }
                >
                  {s.name}: {s.status}
                  {s.detail ? ` (${s.detail})` : ""}
                </li>
              ))}
            </ol>
          </div>
          <div className="grid gap-2">
            <p className="font-medium">Artifact Status</p>
            {artifactEntries.length === 0 ? (
              <p className="text-muted-foreground">No artifact status loaded yet.</p>
            ) : (
              <ul className="grid gap-1">
                {artifactEntries.map(([name, meta]) => (
                  <li key={name} className="flex items-center gap-2">
                    <span className={meta.exists ? "text-green-600" : "text-amber-600"}>
                      {meta.exists ? "ready" : "missing"}
                    </span>
                    <span className="font-mono text-xs">{name}</span>
                    {meta.exists ? (
                      <a
                        href={getArtifactDownloadUrl(meta.path)}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary underline"
                      >
                        download
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
