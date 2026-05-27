import { useEffect, useState } from "react"

import { getReadiness } from "@/lib/api"
import type { ReadinessResponse } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ReadinessPage() {
  const [data, setData] = useState<ReadinessResponse | null>(null)
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
    </div>
  )
}

