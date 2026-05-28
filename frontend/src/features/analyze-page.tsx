import { useEffect, useState } from "react"

import { analyzeIncidentStart, getAnalyzeJobStatus } from "@/lib/api"
import type { AnalyzeResponse } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"

interface AnalyzePageProps {
  onAnalyzed: (incidentId: string, payload: AnalyzeResponse) => void
}

export function AnalyzePage({ onAnalyzed }: AnalyzePageProps) {
  const [incidentId, setIncidentId] = useState("INC-1001")
  const [owner, setOwner] = useState("")
  const [repo, setRepo] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [jobId, setJobId] = useState("")
  const [jobStatus, setJobStatus] = useState<"idle" | "queued" | "running" | "done" | "failed">("idle")

  function normalizeOwner(input: string): string {
    const value = input.trim()
    if (!value) return ""
    const match = value.match(/github\.com\/([^/\s]+)\/?$/i)
    if (match) return match[1]
    return value.replace(/^@/, "").replace(/\/+$/, "")
  }

  function normalizeRepo(input: string): string {
    const value = input.trim()
    if (!value) return ""
    const match = value.match(/github\.com\/[^/\s]+\/([^/\s]+)\/?$/i)
    if (match) return match[1].replace(/\.git$/i, "")
    return value.replace(/\/+$/, "").replace(/\.git$/i, "")
  }

  async function runAnalysis() {
    setLoading(true)
    setError("")
    try {
      const start = await analyzeIncidentStart({
        incident_id: incidentId.trim(),
        github_owner: normalizeOwner(owner),
        github_repo: normalizeRepo(repo),
      })
      setJobId(start.job_id)
      setJobStatus("queued")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run analysis")
      setLoading(false)
      setJobStatus("failed")
    }
  }

  useEffect(() => {
    if (!jobId) return
    const timer = setInterval(async () => {
      try {
        const status = await getAnalyzeJobStatus(jobId)
        setJobStatus(status.status === "running" ? "running" : status.status)
        if (status.status === "done" && status.result) {
          setResult(status.result)
          onAnalyzed(status.result.incident_id, status.result)
          setLoading(false)
          setJobId("")
          setJobStatus("done")
          clearInterval(timer)
        }
        if (status.status === "failed") {
          setError(status.error || "Analysis failed")
          setLoading(false)
          setJobId("")
          setJobStatus("failed")
          clearInterval(timer)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to poll analysis job")
        setLoading(false)
        setJobId("")
        setJobStatus("failed")
        clearInterval(timer)
      }
    }, 1200)
    return () => clearInterval(timer)
  }, [jobId, onAnalyzed])

  const queryDiagnostics = result?.brief.diagnostics?.queries as
    | Record<string, { rows?: number; duration_ms?: number; attempts?: number; row_quality_score?: number }>
    | undefined
  const coverageDiagnostics = result?.brief.diagnostics?.coverage as
    | { score?: number; max_score?: number; missing_families?: string[]; source_availability_influence?: number }
    | undefined
  const discoverStep = result?.workflow_log.find((step) => String(step.step) === "discover_catalog")
  const queryPlan = (discoverStep?.detail as { query_plan?: Record<string, { enabled?: boolean; missing_tables?: string[]; missing_vars?: string[] }> } | undefined)?.query_plan

  return (
    <div className="grid gap-4">
      <Card className="rounded-xl">
        <CardHeader>
          <CardTitle>Analyze Incident</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="incident">Incident ID</Label>
            <Input id="incident" value={incidentId} onChange={(e) => setIncidentId(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="owner">GitHub Owner</Label>
            <Input id="owner" value={owner} onChange={(e) => setOwner(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="repo">GitHub Repo</Label>
            <Input id="repo" value={repo} onChange={(e) => setRepo(e.target.value)} />
          </div>
          <div className="flex items-end gap-2">
            <Button onClick={runAnalysis} disabled={loading || !incidentId.trim()}>
              {loading ? "Running..." : "Run Analysis"}
            </Button>
            <Badge variant="outline">{jobStatus}</Badge>
          </div>
          {error && <p className="text-sm text-destructive md:col-span-2">{error}</p>}
          {loading && (
            <div className="md:col-span-2 rounded-lg border p-3">
              <p className="mb-2 text-xs text-muted-foreground">Progress</p>
              <ol className="grid gap-1 text-xs">
                <li>1. queued {jobStatus === "queued" || jobStatus === "running" || jobStatus === "done" ? "[x]" : "[ ]"}</li>
                <li>2. running {jobStatus === "running" || jobStatus === "done" ? "[x]" : "[ ]"}</li>
                <li>3. completed {jobStatus === "done" ? "[x]" : "[ ]"}</li>
              </ol>
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card className="rounded-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Result <Badge>{result.brief.confidence}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            <div className="grid gap-2 md:grid-cols-4">
              <div className="rounded-lg border p-2 text-xs">
                <p className="text-muted-foreground">Evidence</p>
                <p className="font-semibold">{result.brief.evidence.length}</p>
              </div>
              <div className="rounded-lg border p-2 text-xs">
                <p className="text-muted-foreground">Services</p>
                <p className="font-semibold">{result.brief.impacted_services.length}</p>
              </div>
              <div className="rounded-lg border p-2 text-xs">
                <p className="text-muted-foreground">Owners</p>
                <p className="font-semibold">{result.brief.owners.length}</p>
              </div>
              <div className="rounded-lg border p-2 text-xs">
                <p className="text-muted-foreground">Duration</p>
                <p className="font-semibold">{result.total_duration_ms}ms</p>
              </div>
            </div>
            <p className="text-sm">{result.brief.summary}</p>
            <p className="text-sm">
              <strong>Root cause:</strong> {result.brief.probable_root_cause}
            </p>
            <p className="text-sm">
              <strong>Services:</strong> {result.brief.impacted_services.join(", ") || "n/a"}
            </p>
            <p className="text-sm">
              <strong>Owners:</strong> {result.brief.owners.join(", ") || "n/a"}
            </p>
            <Separator />
            <div className="grid gap-2">
              <p className="text-sm font-medium">Workflow Timeline</p>
              <ol className="grid gap-1 text-xs text-muted-foreground">
                {result.workflow_log.map((step, idx) => (
                  <li key={idx}>
                    {String(step.step ?? `step-${idx}`)} - {String(step.status ?? "unknown")} ({String(step.duration_ms ?? 0)}ms)
                  </li>
                ))}
              </ol>
            </div>
            <div className="grid gap-2">
              <p className="text-sm font-medium">Diagnostics</p>
              <p className="text-xs text-muted-foreground">
                Query errors:{" "}
                {Array.isArray(result.brief.diagnostics?.errors) ? String(result.brief.diagnostics.errors.length) : "0"}
              </p>
              {coverageDiagnostics ? (
                <p className="text-xs text-muted-foreground">
                  Coverage: {coverageDiagnostics.score ?? 0}/{coverageDiagnostics.max_score ?? 4}
                  {" | "}
                  Source influence: {coverageDiagnostics.source_availability_influence ?? 0}%
                </p>
              ) : null}
              {queryDiagnostics ? (
                <div className="rounded-lg border p-2 text-xs">
                  <p className="mb-1 font-medium">Query Telemetry</p>
                  <div className="grid gap-1">
                    {Object.entries(queryDiagnostics).map(([name, q]) => (
                      <p key={name}>
                        {name}: rows={q.rows ?? 0}, ms={q.duration_ms ?? 0}, attempts={q.attempts ?? 1}, quality={q.row_quality_score ?? 0}
                      </p>
                    ))}
                  </div>
                </div>
              ) : null}
              {queryPlan ? (
                <div className="rounded-lg border p-2 text-xs">
                  <p className="mb-1 font-medium">Catalog Query Plan</p>
                  <div className="grid gap-1">
                    {Object.entries(queryPlan).map(([name, p]) => (
                      <p key={name}>
                        {name}: {p.enabled ? "enabled" : "disabled"}
                        {!p.enabled && (p.missing_tables?.length || p.missing_vars?.length)
                          ? ` (missing tables: ${(p.missing_tables ?? []).join(", ") || "none"}; missing vars: ${(p.missing_vars ?? []).join(", ") || "none"})`
                          : ""}
                      </p>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
