export type Confidence = "high" | "medium" | "low" | "unknown"

export interface EvidenceItem {
  type: string
  detail: string
  link?: string
}

export interface IncidentBrief {
  incident_id: string
  summary: string
  probable_root_cause: string
  confidence: Confidence
  impacted_services: string[]
  owners: string[]
  evidence: EvidenceItem[]
  recommended_actions: string[]
  executive_summary: string[]
  diagnostics: Record<string, unknown>
}

export interface AnalyzeResponse {
  incident_id: string
  brief: IncidentBrief
  workflow_log: Array<Record<string, unknown>>
  total_duration_ms: number
}

export interface AnalyzeJobStartResponse {
  job_id: string
  status: "running" | "done" | "failed"
}

export interface AnalyzeJobStatusResponse {
  job_id: string
  status: "running" | "done" | "failed"
  result: AnalyzeResponse | null
  error: string
}

export interface SourceHealthResponse {
  sources: Record<string, string>
  env_missing: Record<string, string[]>
}

export interface EvidenceResponse {
  incident_id: string
  evidence: EvidenceItem[]
  diagnostics: Record<string, unknown>
}

export interface ReleaseCheck {
  go_for_submission: boolean
  go_for_live_submission: boolean
  progress_percent: number
  scorecard_overall: number
  quality_gate_passed: boolean
  live_readiness: boolean
  live_blockers: string[]
  next_actions: string[]
}

export interface ReadinessResponse {
  release_check: ReleaseCheck
  live_readiness: Record<string, unknown>
  scorecard: Record<string, unknown>
  quality_gate: Record<string, unknown>
  demo_report: Record<string, unknown>
  impact_report: Record<string, unknown>
}

export interface ShipReadinessResponse {
  demo_report: Record<string, unknown>
  quality_gate: Record<string, unknown>
  scorecard: Record<string, unknown>
  live_readiness: Record<string, unknown>
  release_check: ReleaseCheck
  handoff_summary: Record<string, unknown>
}

export interface RunHistoryRow {
  incident_id: string
  ts?: string
  total_duration_ms?: number
  confidence?: string
  evidence_count?: number
  query_errors?: number
  [k: string]: unknown
}

export interface JudgePackResponse {
  source_dir: string
  output_zip: string
}
