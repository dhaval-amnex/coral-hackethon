import { useState } from "react"

import { generateJudgePack, getJudgePackDownloadUrl, runShipReadiness } from "@/lib/api"
import type { ShipReadinessResponse } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function ArtifactsPage() {
  const [incidentId, setIncidentId] = useState("INC-1001")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<ShipReadinessResponse | null>(null)
  const [judgePackPath, setJudgePackPath] = useState("")

  async function generate() {
    setLoading(true)
    setError("")
    try {
      const payload = await runShipReadiness({
        incident_id: incidentId.trim(),
        recent_runs: 1,
      })
      setResult(payload)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run ship-readiness")
    } finally {
      setLoading(false)
    }
  }

  async function generatePack() {
    setLoading(true)
    setError("")
    try {
      const payload = await generateJudgePack()
      setJudgePackPath(payload.output_zip)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate judge pack")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Artifact & Submission Center</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-[1fr_auto]">
          <div className="grid gap-2">
            <Label htmlFor="artifact-incident">Incident ID</Label>
            <Input
              id="artifact-incident"
              value={incidentId}
              onChange={(e) => setIncidentId(e.target.value)}
              className="max-w-md"
            />
          </div>
          <div className="flex items-end">
            <Button onClick={generate} disabled={loading || !incidentId.trim()}>
              {loading ? "Generating..." : "Generate Ship-Readiness"}
            </Button>
          </div>
          {error && <p className="text-sm text-destructive md:col-span-2">{error}</p>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Judge Pack</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <Button variant="outline" onClick={generatePack} disabled={loading}>
            {loading ? "Generating..." : "Generate judge_pack.zip"}
          </Button>
          {judgePackPath ? (
            <div className="grid gap-2 text-sm">
              <p>Generated: {judgePackPath}</p>
              <a
                className="text-primary underline"
                href={getJudgePackDownloadUrl(judgePackPath)}
                target="_blank"
                rel="noreferrer"
              >
                Download judge_pack.zip
              </a>
            </div>
          ) : null}
        </CardContent>
      </Card>
      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm">
            <p>Submission: {String(result.release_check.go_for_submission)}</p>
            <p>Live submission: {String(result.release_check.go_for_live_submission)}</p>
            <p>Scorecard overall: {result.release_check.scorecard_overall}</p>
            <p>Next actions: {result.release_check.next_actions.join(", ")}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
