import { useState } from "react"
import { useEffect } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AnalyzePage } from "@/features/analyze-page"
import { ArtifactsPage } from "@/features/artifacts-page"
import { DashboardPage } from "@/features/dashboard-page"
import { EvidencePage } from "@/features/evidence-page"
import { HistoryPage } from "@/features/history-page"
import { ReadinessPage } from "@/features/readiness-page"
import { SubmissionPage } from "@/features/submission-page"
import type { AnalyzeResponse } from "@/lib/types"
import {
  analyzeIncidentStart,
  generateJudgePack,
  getAnalyzeJobStatus,
  getArtifactsStatus,
  getSourceHealth,
  runShipReadiness,
} from "@/lib/api"
import type { ArtifactsStatusResponse } from "@/lib/types"

type Section = "dashboard" | "analyze" | "evidence" | "readiness" | "artifacts" | "submission" | "history"

const NAV: Array<{ id: Section; label: string }> = [
  { id: "dashboard", label: "Dashboard" },
  { id: "analyze", label: "Analyze" },
  { id: "evidence", label: "Evidence" },
  { id: "readiness", label: "Readiness" },
  { id: "artifacts", label: "Artifacts" },
  { id: "submission", label: "Submission" },
  { id: "history", label: "Run History" },
]

function statusVariant(state: string): "default" | "destructive" | "outline" | "secondary" {
  if (state === "ok" || state === "done") return "default"
  if (state === "failed") return "destructive"
  if (state === "running") return "secondary"
  return "outline"
}

export function App() {
  const [section, setSection] = useState<Section>("dashboard")
  const [activeIncidentId, setActiveIncidentId] = useState("INC-1001")
  const [lastAnalyze, setLastAnalyze] = useState<AnalyzeResponse | null>(null)
  const [sourceHealth, setSourceHealth] = useState<Record<string, string>>({})
  const [artifactsStatus, setArtifactsStatus] = useState<ArtifactsStatusResponse | null>(null)
  const [demoRunning, setDemoRunning] = useState(false)
  const [demoSteps, setDemoSteps] = useState<
    Array<{ name: string; status: "pending" | "running" | "done" | "failed"; detail?: string }>
  >([
    { name: "Analyze", status: "pending" },
    { name: "Ship-Readiness", status: "pending" },
    { name: "Judge-Pack", status: "pending" },
  ])
  const [presenterMode, setPresenterMode] = useState(false)
  const [visitedEvidence, setVisitedEvidence] = useState(false)
  const [visitedReadiness, setVisitedReadiness] = useState(false)
  const [visitedSubmission, setVisitedSubmission] = useState(false)
  const [lastHealthRefreshAt, setLastHealthRefreshAt] = useState<string>("")
  const [lastArtifactsRefreshAt, setLastArtifactsRefreshAt] = useState<string>("")
  const [activityFeed, setActivityFeed] = useState<string[]>([])

  function pushActivity(message: string) {
    const ts = new Date().toLocaleTimeString()
    setActivityFeed((prev) => [`${ts} ${message}`, ...prev].slice(0, 4))
  }

  useEffect(() => {
    getSourceHealth()
      .then((x) => {
        setSourceHealth(x.sources)
        setLastHealthRefreshAt(new Date().toLocaleTimeString())
      })
      .catch(() => setSourceHealth({}))
  }, [])

  useEffect(() => {
    const timer = window.setInterval(() => {
      getSourceHealth()
        .then((x) => {
          setSourceHealth(x.sources)
          setLastHealthRefreshAt(new Date().toLocaleTimeString())
        })
        .catch(() => {})
    }, 15000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    getArtifactsStatus()
      .then((x) => {
        setArtifactsStatus(x)
        setLastArtifactsRefreshAt(new Date().toLocaleTimeString())
      })
      .catch(() => setArtifactsStatus(null))
  }, [section, lastAnalyze])

  useEffect(() => {
    const timer = window.setInterval(() => {
      getArtifactsStatus()
        .then((x) => {
          setArtifactsStatus(x)
          setLastArtifactsRefreshAt(new Date().toLocaleTimeString())
        })
        .catch(() => {})
    }, 10000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!lastAnalyze) return
    pushActivity(`Analyze completed (${lastAnalyze.incident_id}, ${lastAnalyze.brief.confidence})`)
  }, [lastAnalyze])

  useEffect(() => {
    if (!artifactsStatus) return
    const ready = artifactsStatus.artifacts?.judge_pack_zip?.exists
    pushActivity(ready ? "Judge pack ready" : "Judge pack missing")
  }, [artifactsStatus])

  function navigateTo(next: Section) {
    setSection(next)
    if (next === "evidence") setVisitedEvidence(true)
    if (next === "readiness") setVisitedReadiness(true)
    if (next === "submission") setVisitedSubmission(true)
  }

  function resetPresenterChecklist() {
    setVisitedEvidence(false)
    setVisitedReadiness(false)
    setVisitedSubmission(false)
  }

  function renderSection() {
    if (section === "dashboard")
      return (
        <DashboardPage
          activeIncidentId={activeIncidentId}
          onNavigate={(next) => navigateTo(next)}
          artifactsStatus={artifactsStatus}
          onRunFullDemo={runFullDemo}
          demoRunning={demoRunning}
          demoSteps={demoSteps}
          presenterMode={presenterMode}
          onTogglePresenterMode={() => setPresenterMode((x) => !x)}
          onResetPresenterChecklist={resetPresenterChecklist}
          presenterChecklist={[
            { name: "Analyze completed", done: Boolean(lastAnalyze) },
            { name: "Evidence explored", done: visitedEvidence },
            { name: "Readiness reviewed", done: visitedReadiness || visitedSubmission },
            {
              name: "Judge pack generated",
              done: Boolean(artifactsStatus?.artifacts?.judge_pack_zip?.exists),
            },
          ]}
        />
      )
    if (section === "analyze")
      return (
        <AnalyzePage
          onAnalyzed={(incidentId, payload) => {
            setActiveIncidentId(incidentId)
            setLastAnalyze(payload)
          }}
        />
      )
    if (section === "evidence") return <EvidencePage incidentId={activeIncidentId} />
    if (section === "readiness") return <ReadinessPage />
    if (section === "artifacts") return <ArtifactsPage />
    if (section === "submission") return <SubmissionPage />
    return <HistoryPage />
  }

  function setStepStatus(
    name: "Analyze" | "Ship-Readiness" | "Judge-Pack",
    status: "pending" | "running" | "done" | "failed",
    detail = "",
  ) {
    setDemoSteps((prev) =>
      prev.map((x) => (x.name === name ? { ...x, status, detail } : x)),
    )
  }

  async function runFullDemo() {
    if (demoRunning) return
    setDemoRunning(true)
    setDemoSteps([
      { name: "Analyze", status: "pending" },
      { name: "Ship-Readiness", status: "pending" },
      { name: "Judge-Pack", status: "pending" },
    ])
    try {
      setStepStatus("Analyze", "running")
      const runId = new Date().toISOString().replace(/[:.]/g, "-")
      const demoMetricsLog = `output/run_metrics_live_${runId}.jsonl`
      const demoWorkflowLog = `output/workflow_log_live_${runId}.json`
      const start = await analyzeIncidentStart({
        incident_id: activeIncidentId || "INC-1001",
        planner_mode: "mcp_native",
        github_owner: "dhaval-amnex",
        github_repo: "coral-hackethon",
        metrics_log: demoMetricsLog,
        workflow_log: demoWorkflowLog,
      })
      const jobId = start.job_id
      let analyzeDone = false
      let analyzedIncidentId = activeIncidentId || "INC-1001"
      for (let i = 0; i < 120; i += 1) {
        const status = await getAnalyzeJobStatus(jobId)
        if (status.status === "done" && status.result) {
          setLastAnalyze(status.result)
          setActiveIncidentId(status.result.incident_id)
          analyzedIncidentId = status.result.incident_id
          setStepStatus("Analyze", "done")
          analyzeDone = true
          break
        }
        if (status.status === "failed") {
          setStepStatus("Analyze", "failed", status.error || "failed")
          throw new Error(status.error || "Analyze job failed")
        }
        await new Promise((resolve) => setTimeout(resolve, 1000))
      }
      if (!analyzeDone) {
        setStepStatus("Analyze", "failed", "timeout")
        throw new Error("Analyze timeout")
      }

      setStepStatus("Ship-Readiness", "running")
      let ship = await runShipReadiness({
        incident_id: analyzedIncidentId,
        recent_runs: 1,
        metrics_log: demoMetricsLog,
        workflow_log: demoWorkflowLog,
      })
      if (!ship.release_check.go_for_submission) {
        ship = await runShipReadiness({
          incident_id: analyzedIncidentId,
          recent_runs: 1,
          metrics_log: "output/run_metrics_submit.jsonl",
          workflow_log: "output/workflow_log_submit.json",
        })
      }
      if (!ship.release_check.go_for_submission) {
        setStepStatus("Ship-Readiness", "failed", "go_for_submission=false")
        throw new Error("Ship-readiness failed")
      }
      setStepStatus("Ship-Readiness", "done")

      setStepStatus("Judge-Pack", "running")
      const pack = await generateJudgePack()
      setStepStatus("Judge-Pack", "done", pack.output_zip)

      const refreshed = await getArtifactsStatus()
      setArtifactsStatus(refreshed)
      setSection("artifacts")
    } catch (err) {
      const message = err instanceof Error ? err.message : "Full demo failed"
      setDemoSteps((prev) => {
        const firstRunning = prev.find((x) => x.status === "running")
        if (!firstRunning) return prev
        return prev.map((x) =>
          x.name === firstRunning.name ? { ...x, status: "failed", detail: message } : x,
        )
      })
    } finally {
      setDemoRunning(false)
    }
  }

  return (
    <div className="min-h-svh bg-[radial-gradient(circle_at_top,_rgba(0,0,0,0.04),_transparent_35%),linear-gradient(to_bottom,_transparent,_rgba(0,0,0,0.03))] text-foreground">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-4 p-4 md:grid-cols-[240px_1fr]">
        <aside className="rounded-2xl border bg-card/95 p-4 shadow-sm backdrop-blur">
          <h1 className="font-heading text-lg tracking-wide">Incident Captain</h1>
          <p className="mb-4 text-xs text-muted-foreground">Enterprise Command Center</p>
          <div className="grid gap-2">
            {NAV.map((item) => (
              <Button
                key={item.id}
                variant={section === item.id ? "default" : "outline"}
                className="justify-start rounded-xl"
                onClick={() => navigateTo(item.id)}
              >
                {item.label}
              </Button>
            ))}
          </div>
        </aside>
        <main className="grid gap-4">
          <header className="flex flex-wrap items-center gap-2 rounded-2xl border bg-card/95 p-3 text-sm shadow-sm backdrop-blur">
            <Badge variant="outline">API: http://127.0.0.1:8787</Badge>
            <Badge>{activeIncidentId}</Badge>
            {Object.entries(sourceHealth).map(([name, state]) => (
              <Badge key={name} variant={statusVariant(state)}>
                {name}:{state}
              </Badge>
            ))}
            {lastAnalyze ? (
              <Badge variant="outline">confidence: {lastAnalyze.brief.confidence}</Badge>
            ) : (
              <Badge variant="outline">no run yet</Badge>
            )}
            <Badge variant="outline">health: {lastHealthRefreshAt || "..."}</Badge>
            <Badge variant="outline">artifacts: {lastArtifactsRefreshAt || "..."}</Badge>
            {activityFeed.length > 0 ? (
              <Badge variant="secondary">activity: {activityFeed[0]}</Badge>
            ) : null}
          </header>
          {renderSection()}
        </main>
      </div>
    </div>
  )
}

export default App
