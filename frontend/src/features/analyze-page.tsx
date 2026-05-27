import { useState } from "react"

import { analyzeIncident } from "@/lib/api"
import type { AnalyzeResponse } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
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

  async function runAnalysis() {
    setLoading(true)
    setError("")
    try {
      const payload = await analyzeIncident({
        incident_id: incidentId.trim(),
        github_owner: owner.trim(),
        github_repo: repo.trim(),
      })
      setResult(payload)
      onAnalyzed(payload.incident_id, payload)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run analysis")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-4">
      <Card>
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
          <div className="flex items-end">
            <Button onClick={runAnalysis} disabled={loading || !incidentId.trim()}>
              {loading ? "Running..." : "Run Analysis"}
            </Button>
          </div>
          {error && <p className="text-sm text-destructive md:col-span-2">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Result <Badge>{result.brief.confidence}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
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
                    {String(step.step ?? `step-${idx}`)} - {String(step.status ?? "unknown")} (
                    {String(step.duration_ms ?? 0)}ms)
                  </li>
                ))}
              </ol>
            </div>
            <div className="grid gap-2">
              <p className="text-sm font-medium">Diagnostics</p>
              <p className="text-xs text-muted-foreground">
                Query errors:{" "}
                {Array.isArray(result.brief.diagnostics?.errors)
                  ? String(result.brief.diagnostics.errors.length)
                  : "0"}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
