import { useEffect, useState } from "react"

import { getRunHistory } from "@/lib/api"
import type { RunHistoryRow } from "@/lib/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export function HistoryPage() {
  const [rows, setRows] = useState<RunHistoryRow[]>([])
  const [error, setError] = useState("")

  useEffect(() => {
    getRunHistory()
      .then((items) => {
        setRows(items.reverse())
        setError("")
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load run history")
      })
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run History</CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Incident</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Duration (ms)</TableHead>
                <TableHead>Evidence</TableHead>
                <TableHead>Query Errors</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r, idx) => (
                <TableRow key={`${r.incident_id}-${idx}`}>
                  <TableCell>{String(r.incident_id ?? "")}</TableCell>
                  <TableCell>{String(r.confidence ?? "-")}</TableCell>
                  <TableCell>{String(r.total_duration_ms ?? "-")}</TableCell>
                  <TableCell>{String(r.evidence_count ?? "-")}</TableCell>
                  <TableCell>{String(r.query_errors ?? "-")}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

