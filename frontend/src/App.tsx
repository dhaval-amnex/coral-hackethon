import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AnalyzePage } from "@/features/analyze-page"
import { ArtifactsPage } from "@/features/artifacts-page"
import { DashboardPage } from "@/features/dashboard-page"
import { EvidencePage } from "@/features/evidence-page"
import { HistoryPage } from "@/features/history-page"
import { ReadinessPage } from "@/features/readiness-page"
import type { AnalyzeResponse } from "@/lib/types"

type Section = "dashboard" | "analyze" | "evidence" | "readiness" | "artifacts" | "history"

const NAV: Array<{ id: Section; label: string }> = [
  { id: "dashboard", label: "Dashboard" },
  { id: "analyze", label: "Analyze" },
  { id: "evidence", label: "Evidence" },
  { id: "readiness", label: "Readiness" },
  { id: "artifacts", label: "Artifacts" },
  { id: "history", label: "Run History" },
]

export function App() {
  const [section, setSection] = useState<Section>("dashboard")
  const [activeIncidentId, setActiveIncidentId] = useState("INC-1001")
  const [lastAnalyze, setLastAnalyze] = useState<AnalyzeResponse | null>(null)

  function renderSection() {
    if (section === "dashboard") return <DashboardPage activeIncidentId={activeIncidentId} />
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
    return <HistoryPage />
  }

  return (
    <div className="min-h-svh bg-background text-foreground">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-4 p-4 md:grid-cols-[220px_1fr]">
        <aside className="rounded-lg border bg-card p-3">
          <h1 className="font-heading text-lg">Incident Captain</h1>
          <p className="mb-4 text-xs text-muted-foreground">Command Center</p>
          <div className="grid gap-2">
            {NAV.map((item) => (
              <Button
                key={item.id}
                variant={section === item.id ? "default" : "outline"}
                className="justify-start"
                onClick={() => setSection(item.id)}
              >
                {item.label}
              </Button>
            ))}
          </div>
        </aside>
        <main className="grid gap-4">
          <header className="flex flex-wrap items-center gap-2 rounded-lg border bg-card p-3 text-sm">
            <Badge variant="outline">API: http://127.0.0.1:8787</Badge>
            <Badge>{activeIncidentId}</Badge>
            {lastAnalyze ? (
              <Badge variant="outline">confidence: {lastAnalyze.brief.confidence}</Badge>
            ) : (
              <Badge variant="outline">no run yet</Badge>
            )}
          </header>
          {renderSection()}
        </main>
      </div>
    </div>
  )
}

export default App
