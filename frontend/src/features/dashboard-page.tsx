import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface DashboardPageProps {
  activeIncidentId: string
}

export function DashboardPage({ activeIncidentId }: DashboardPageProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Mission Control</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <p>Active Incident: {activeIncidentId || "None"}</p>
          <p className="text-muted-foreground">
            Use Analyze to run cross-source investigation and then move to Readiness for submission state.
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <ul className="list-disc pl-5">
            <li>Run Analyze with incident ID</li>
            <li>Review Evidence Explorer</li>
            <li>Generate Ship-Readiness artifacts</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

