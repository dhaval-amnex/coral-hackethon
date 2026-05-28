import type {
  AnalyzeResponse,
  AnalyzeJobStartResponse,
  AnalyzeJobStatusResponse,
  EvidenceResponse,
  JudgePackResponse,
  ArtifactsStatusResponse,
  ReadinessResponse,
  RunHistoryRow,
  ShipReadinessResponse,
  SourceHealthResponse,
} from "@/lib/types"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8787"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  })
  const payload = (await res.json()) as T | { error?: string }
  if (!res.ok) {
    const message = (payload as { error?: string }).error ?? `Request failed (${res.status})`
    throw new Error(message)
  }
  return payload as T
}

export function analyzeIncident(input: {
  incident_id: string
  planner_mode?: "sql" | "mcp" | "mcp_native"
  github_owner?: string
  github_repo?: string
  env_file?: string
  output_dir?: string
  metrics_log?: string
  workflow_log?: string
  coral_timeout_sec?: number
  coral_retries?: number
  coral_backoff_sec?: number
}): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function analyzeIncidentStart(input: {
  incident_id: string
  planner_mode?: "sql" | "mcp" | "mcp_native"
  github_owner?: string
  github_repo?: string
  env_file?: string
  output_dir?: string
  metrics_log?: string
  workflow_log?: string
  coral_timeout_sec?: number
  coral_retries?: number
  coral_backoff_sec?: number
}): Promise<AnalyzeJobStartResponse> {
  return request<AnalyzeJobStartResponse>("/api/analyze/start", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export function getAnalyzeJobStatus(jobId: string): Promise<AnalyzeJobStatusResponse> {
  const q = new URLSearchParams({ job_id: jobId })
  return request<AnalyzeJobStatusResponse>(`/api/analyze/status?${q.toString()}`)
}

export function getEvidence(incidentId: string, outputDir = "output"): Promise<EvidenceResponse> {
  const q = new URLSearchParams({ incident_id: incidentId, output_dir: outputDir })
  return request<EvidenceResponse>(`/api/evidence?${q.toString()}`)
}

export function getReadiness(reportDir = "output/report"): Promise<ReadinessResponse> {
  const q = new URLSearchParams({ report_dir: reportDir })
  return request<ReadinessResponse>(`/api/readiness?${q.toString()}`)
}

export function runShipReadiness(input: {
  incident_id: string
  root?: string
  output_dir?: string
  report_dir?: string
  metrics_log?: string
  recent_runs?: number
  min_progress_percent?: number
  min_scorecard_overall?: number
}): Promise<ShipReadinessResponse> {
  return request<ShipReadinessResponse>("/api/ship-readiness", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export async function getRunHistory(metricsLog = "output/run_metrics.jsonl"): Promise<RunHistoryRow[]> {
  const q = new URLSearchParams({ metrics_log: metricsLog })
  const payload = await request<{ rows: RunHistoryRow[] }>(`/api/run-history?${q.toString()}`)
  return payload.rows
}

export function getSourceHealth(
  sources = ["pagerduty", "github", "slack", "datadog"],
  envFile = ".env",
): Promise<SourceHealthResponse> {
  const q = new URLSearchParams({
    sources: sources.join(","),
    env_file: envFile,
  })
  return request<SourceHealthResponse>(`/api/source-health?${q.toString()}`)
}

export function generateJudgePack(input?: {
  bundle_root?: string
  output_zip?: string
  source_dir?: string
}): Promise<JudgePackResponse> {
  return request<JudgePackResponse>("/api/judge-pack", {
    method: "POST",
    body: JSON.stringify(input ?? {}),
  })
}

export function getJudgePackDownloadUrl(path = "output/judge_pack.zip"): string {
  const q = new URLSearchParams({ path })
  return `${API_BASE}/api/judge-pack/download?${q.toString()}`
}

export function getArtifactsStatus(
  outputDir = "output",
  reportDir = "output/report",
): Promise<ArtifactsStatusResponse> {
  const q = new URLSearchParams({ output_dir: outputDir, report_dir: reportDir })
  return request<ArtifactsStatusResponse>(`/api/artifacts/status?${q.toString()}`)
}

export function getArtifactDownloadUrl(path: string): string {
  const q = new URLSearchParams({ path })
  return `${API_BASE}/api/artifacts/download?${q.toString()}`
}
