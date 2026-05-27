import { useEffect, useState } from "react"

import { getReadiness, getRunHistory } from "@/lib/api"
import type { ReadinessResponse } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ReadinessPage() {
  const [data, setData] = useState<ReadinessResponse | null>(null)
  const [trend, setTrend] = useState<Array<{ id: string; score: number }>>([])
  const [error, setError] = useState("")

  useEffect(() => {
    getReadiness()
      .then((payload) => {
        setData(payload)
        setError("")
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load readiness")
      })
    getRunHistory()
      .then((rows) => {
        const points = rows.slice(-8).map((r) => ({
          id: String(r.incident_id ?? "n/a"),
          score: Math.max(0, 100 - Number(r.query_errors ?? 0) * 25),
        }))
        setTrend(points)
      })
      .catch(() => setTrend([]))
  }, [])

  if (error) {
    return <p className="text-sm text-destructive">{error}</p>
  }

  if (!data) {
    return <p className="text-sm text-muted-foreground">Loading readiness...</p>
  }

  const release = data.release_check
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Release Check</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm">
          <p>
            Submission:{" "}
            <Badge variant={release.go_for_submission ? "default" : "destructive"}>
              {String(release.go_for_submission)}
            </Badge>
          </p>
          <p>
            Live submission:{" "}
            <Badge variant={release.go_for_live_submission ? "default" : "destructive"}>
              {String(release.go_for_live_submission)}
            </Badge>
          </p>
          <p>Score: {release.scorecard_overall}</p>
          <p>Progress: {release.progress_percent}%</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Next Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-5 text-sm">
            {release.next_actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Recent Reliability Trend</CardTitle>
        </CardHeader>
        <CardContent>
          {trend.length === 0 ? (
            <p className="text-sm text-muted-foreground">No trend data yet.</p>
          ) : (
            <div className="grid gap-2">
              {trend.map((p, idx) => (
                <div key={`${p.id}-${idx}`} className="grid gap-1">
                  <div className="flex items-center justify-between text-xs">
                    <span>{p.id}</span>
                    <span>{p.score.toFixed(0)}</span>
                  </div>
                  <div className="h-2 rounded bg-muted">
                    <div className="h-2 rounded bg-primary" style={{ width: `${p.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
