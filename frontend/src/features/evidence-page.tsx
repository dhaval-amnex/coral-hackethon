import { useEffect, useState } from "react"

import { getEvidence } from "@/lib/api"
import type { EvidenceItem } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"

interface EvidencePageProps {
  incidentId: string
}

export function EvidencePage({ incidentId }: EvidencePageProps) {
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [filter, setFilter] = useState("")
  const [error, setError] = useState("")
  const [diagnostics, setDiagnostics] = useState<Record<string, unknown>>({})

  useEffect(() => {
    if (!incidentId) return
    getEvidence(incidentId)
      .then((data) => {
        setEvidence(data.evidence)
        setDiagnostics(data.diagnostics ?? {})
        setError("")
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load evidence")
      })
  }, [incidentId])

  const filtered = evidence.filter(
    (e) =>
      e.type.toLowerCase().includes(filter.toLowerCase()) ||
      e.detail.toLowerCase().includes(filter.toLowerCase()),
  )
  const typeCounts = filtered.reduce<Record<string, number>>((acc, item) => {
    acc[item.type] = (acc[item.type] || 0) + 1
    return acc
  }, {})

  return (
    <Card className="rounded-xl">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          Evidence Explorer
          <Badge variant="outline">{filtered.length} visible</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <Input
          placeholder="Filter by type or detail"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="max-w-md"
        />
        {error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : (
          <div className="grid gap-4">
            <div className="flex flex-wrap gap-2">
              {Object.entries(typeCounts).map(([type, count]) => (
                <Badge key={type} variant="secondary">
                  {type}: {count}
                </Badge>
              ))}
              {Object.keys(typeCounts).length === 0 ? (
                <p className="text-xs text-muted-foreground">No evidence rows for current filter.</p>
              ) : null}
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Detail</TableHead>
                  <TableHead>Link</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((row, idx) => (
                  <TableRow key={`${row.type}-${idx}`}>
                    <TableCell>{row.type}</TableCell>
                    <TableCell>{row.detail}</TableCell>
                    <TableCell>
                      {row.link ? (
                        <a className="text-primary underline" href={row.link} target="_blank" rel="noreferrer">
                          open
                        </a>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="rounded-md border p-3">
              <p className="mb-2 text-sm font-medium">Diagnostics</p>
              <pre className="max-h-56 overflow-auto text-xs text-muted-foreground">
                {JSON.stringify(diagnostics, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
