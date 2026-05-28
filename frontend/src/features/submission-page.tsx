import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { generateJudgePack, getArtifactDownloadUrl, getArtifactsStatus, runShipReadiness } from "@/lib/api"
import type { ArtifactsStatusResponse, ShipReadinessResponse } from "@/lib/types"

export function SubmissionPage() {
  const [incidentId, setIncidentId] = useState("INC-1001")
  const [recentRuns, setRecentRuns] = useState("1")
  const [minProgress, setMinProgress] = useState("90")
  const [minScore, setMinScore] = useState("70")
  const [running, setRunning] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<ShipReadinessResponse | null>(null)
  const [artifacts, setArtifacts] = useState<ArtifactsStatusResponse | null>(null)
  const [judgePackPath, setJudgePackPath] = useState("")

  async function runChecks() {
    setRunning(true)
    setError("")
    try {
      const payload = await runShipReadiness({
        incident_id: incidentId.trim(),
        recent_runs: Number(recentRuns) || 1,
        min_progress_percent: Number(minProgress) || 90,
        min_scorecard_overall: Number(minScore) || 70,
      })
      setResult(payload)
      setArtifacts(await getArtifactsStatus())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run submission checks")
    } finally {
      setRunning(false)
    }
  }

  async function runJudgePack() {
    setRunning(true)
    setError("")
    try {
      const pack = await generateJudgePack()
      setJudgePackPath(pack.output_zip)
      setArtifacts(await getArtifactsStatus())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate judge pack")
    } finally {
      setRunning(false)
    }
  }

  const release = result?.release_check
  const artifactEntries = artifacts ? Object.entries(artifacts.artifacts) : []

  return (
    <div className="grid gap-4">
      <Card className="rounded-xl">
        <CardHeader>
          <CardTitle>Submission Console</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-4">
          <div className="grid gap-1">
            <Label htmlFor="submission-incident">Incident ID</Label>
            <Input id="submission-incident" value={incidentId} onChange={(e) => setIncidentId(e.target.value)} />
          </div>
          <div className="grid gap-1">
            <Label htmlFor="submission-runs">Recent Runs</Label>
            <Input id="submission-runs" value={recentRuns} onChange={(e) => setRecentRuns(e.target.value)} />
          </div>
          <div className="grid gap-1">
            <Label htmlFor="submission-progress">Min Progress %</Label>
            <Input id="submission-progress" value={minProgress} onChange={(e) => setMinProgress(e.target.value)} />
          </div>
          <div className="grid gap-1">
            <Label htmlFor="submission-score">Min Scorecard</Label>
            <Input id="submission-score" value={minScore} onChange={(e) => setMinScore(e.target.value)} />
          </div>
          <div className="md:col-span-4 flex flex-wrap gap-2">
            <Button onClick={runChecks} disabled={running || !incidentId.trim()}>
              {running ? "Running..." : "Run Release Check"}
            </Button>
            <Button variant="outline" onClick={runJudgePack} disabled={running}>
              {running ? "Running..." : "Generate Judge Pack"}
            </Button>
          </div>
          {error ? <p className="md:col-span-4 text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      {release ? (
        <Card className="rounded-xl">
          <CardHeader>
            <CardTitle>Submission Decision</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm">
            <p>
              Go for submission:{" "}
              <Badge variant={release.go_for_submission ? "default" : "destructive"}>
                {String(release.go_for_submission)}
              </Badge>
            </p>
            <p>
              Go for live submission:{" "}
              <Badge variant={release.go_for_live_submission ? "default" : "destructive"}>
                {String(release.go_for_live_submission)}
              </Badge>
            </p>
            <p>Scorecard overall: {release.scorecard_overall}</p>
            <p>Progress: {release.progress_percent}%</p>
            <p>
              Quality gate passed:{" "}
              <Badge variant={release.quality_gate_passed ? "default" : "destructive"}>
                {String(release.quality_gate_passed)}
              </Badge>
            </p>
            <p>
              Live readiness:{" "}
              <Badge variant={release.live_readiness ? "default" : "destructive"}>
                {String(release.live_readiness)}
              </Badge>
            </p>
            <p>Live blockers: {release.live_blockers.length > 0 ? release.live_blockers.join(", ") : "none"}</p>
            <p>Next actions: {release.next_actions.join(", ")}</p>
          </CardContent>
        </Card>
      ) : null}

      <Card className="rounded-xl">
        <CardHeader>
          <CardTitle>Artifacts</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm">
          {judgePackPath ? (
            <a href={getArtifactDownloadUrl(judgePackPath)} className="text-primary underline" target="_blank" rel="noreferrer">
              Download judge_pack.zip
            </a>
          ) : null}
          {artifactEntries.length === 0 ? (
            <p className="text-muted-foreground">Run release check to refresh artifact list.</p>
          ) : (
            <ul className="grid gap-1">
              {artifactEntries.map(([name, meta]) => (
                <li key={name}>
                  {name}: {meta.exists ? "ready" : "missing"}{" "}
                  {meta.exists ? (
                    <a href={getArtifactDownloadUrl(meta.path)} className="text-primary underline" target="_blank" rel="noreferrer">
                      download
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
