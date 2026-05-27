import { useEffect, useState } from "react"

import { getEvidence } from "@/lib/api"
import type { EvidenceItem } from "@/lib/types"
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

  useEffect(() => {
    if (!incidentId) return
    getEvidence(incidentId)
      .then((data) => {
        setEvidence(data.evidence)
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Evidence Explorer</CardTitle>
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
        )}
      </CardContent>
    </Card>
  )
}

