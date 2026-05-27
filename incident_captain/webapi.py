from __future__ import annotations

import json
import os
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .briefing import compose_brief
from .config import validate_source_env
from .coral import CoralClient, CoralError, load_env_file
from .metrics import append_run_metrics
from .orchestration import run_deterministic_workflow, write_workflow_log
from .release import write_release_check
from .reporting import write_demo_report
from .quality import run_quality_gate
from .scorecard import write_scorecard
from .readiness import write_live_readiness_report
from .dashboard import write_dashboard
from .handoff import write_handoff_note
from .judge_pack import create_judge_pack


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _build_coral(payload: dict[str, Any]) -> CoralClient:
    return CoralClient(
        coral_bin=str(payload.get("coral_bin") or "coral"),
        timeout_sec=float(payload.get("coral_timeout_sec") or 30.0),
        retries=int(payload.get("coral_retries") or 2),
        backoff_sec=float(payload.get("coral_backoff_sec") or 0.5),
    )


_JOBS_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}


class _Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:  # noqa: N802
        _json_response(self, HTTPStatus.OK, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/health":
            _json_response(self, HTTPStatus.OK, {"ok": True, "service": "incident-captain-api"})
            return

        if path == "/api/source-health":
            sources_param = (qs.get("sources", ["pagerduty,github,slack,datadog"])[0] or "").strip()
            sources = [s.strip() for s in sources_param.split(",") if s.strip()]
            env_file = Path((qs.get("env_file", [".env"])[0] or ".env").strip())
            if env_file:
                load_env_file(env_file)
            v = validate_source_env(sources)
            health: dict[str, str] = {}
            if v.ok:
                coral = CoralClient()
                try:
                    health = coral.source_health(sources)
                except CoralError:
                    health = {s: "failed" for s in sources}
            else:
                health = {s: ("missing_env" if s in v.missing else "unknown") for s in sources}
            _json_response(self, HTTPStatus.OK, {"sources": health, "env_missing": v.missing})
            return

        if path == "/api/evidence":
            incident_id = (qs.get("incident_id", [""])[0] or "").strip()
            output_dir = Path((qs.get("output_dir", ["output"])[0] or "output").strip())
            if not incident_id:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "incident_id is required"})
                return
            brief = _read_json(output_dir / f"{incident_id}.json")
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "incident_id": incident_id,
                    "evidence": brief.get("evidence", []),
                    "diagnostics": brief.get("diagnostics", {}),
                },
            )
            return

        if path == "/api/readiness":
            report_dir = Path((qs.get("report_dir", ["output/report"])[0] or "output/report").strip())
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "release_check": _read_json(report_dir / "release_check.json"),
                    "live_readiness": _read_json(report_dir / "live_readiness.json"),
                    "scorecard": _read_json(report_dir / "scorecard.json"),
                    "quality_gate": _read_json(report_dir / "quality_gate.json"),
                    "demo_report": _read_json(report_dir / "demo_report.json"),
                    "impact_report": _read_json(report_dir / "impact_report.json"),
                },
            )
            return

        if path == "/api/run-history":
            metrics_log = Path((qs.get("metrics_log", ["output/run_metrics.jsonl"])[0] or "output/run_metrics.jsonl").strip())
            _json_response(self, HTTPStatus.OK, {"rows": _read_jsonl(metrics_log)})
            return

        if path == "/api/analyze/status":
            job_id = (qs.get("job_id", [""])[0] or "").strip()
            if not job_id:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "job_id is required"})
                return
            with _JOBS_LOCK:
                job = _JOBS.get(job_id)
            if not job:
                _json_response(self, HTTPStatus.NOT_FOUND, {"error": "job not found"})
                return
            _json_response(self, HTTPStatus.OK, job)
            return

        _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                payload = {}
        except json.JSONDecodeError:
            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})
            return

        try:
            if parsed.path == "/api/analyze":
                self._post_analyze(payload)
                return
            if parsed.path == "/api/analyze/start":
                self._post_analyze_start(payload)
                return
            if parsed.path == "/api/ship-readiness":
                self._post_ship_readiness(payload)
                return
            if parsed.path == "/api/judge-pack":
                self._post_judge_pack(payload)
                return
            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
        except CoralError as exc:
            _json_response(
                self,
                HTTPStatus.BAD_REQUEST,
                {"error": str(exc), "category": getattr(exc, "category", "unknown")},
            )
        except Exception as exc:  # defensive API boundary
            _json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep server stdout clean for CLI usage.
        return

    def _post_analyze(self, payload: dict[str, Any]) -> None:
        env_file = Path(str(payload.get("env_file") or ".env"))
        if env_file:
            load_env_file(env_file)

        validate_sources = ["pagerduty", "datadog", "slack"]
        github_owner = str(payload.get("github_owner") or "")
        github_repo = str(payload.get("github_repo") or "")
        if github_owner and github_repo:
            validate_sources.append("github")
        v = validate_source_env(validate_sources)
        if not v.ok:
            parts = [f"{src}: {', '.join(vals)}" for src, vals in v.missing.items()]
            raise CoralError("Missing required environment variables. " + "; ".join(parts), category="config")

        incident_id = str(payload.get("incident_id") or "").strip()
        if not incident_id:
            raise CoralError("incident_id is required", category="config")

        output_dir = Path(str(payload.get("output_dir") or "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        metrics_log = Path(str(payload.get("metrics_log") or "output/run_metrics.jsonl"))
        workflow_log = Path(str(payload.get("workflow_log") or "output/workflow_log.json"))
        sql_dir = Path(str(payload.get("sql_dir") or "deliverables/sql"))

        extra_vars: dict[str, str] = {}
        if github_owner:
            extra_vars["GITHUB_OWNER"] = github_owner
        if github_repo:
            extra_vars["GITHUB_REPO"] = github_repo

        coral = _build_coral(payload)
        workflow = run_deterministic_workflow(
            coral=coral,
            incident_id=incident_id,
            sql_dir=sql_dir,
            extra_vars=extra_vars or None,
        )
        brief = workflow.brief
        (output_dir / f"{incident_id}.json").write_text(json.dumps(brief.to_dict(), indent=2), encoding="utf-8")
        write_workflow_log(workflow_log, workflow.workflow_log)
        append_run_metrics(
            metrics_log,
            incident_id=incident_id,
            mode="live",
            total_duration_ms=workflow.total_duration_ms,
            brief=brief,
        )
        _json_response(
            self,
            HTTPStatus.OK,
            {
                "incident_id": incident_id,
                "brief": brief.to_dict(),
                "workflow_log": workflow.workflow_log,
                "total_duration_ms": workflow.total_duration_ms,
            },
        )

    def _post_analyze_start(self, payload: dict[str, Any]) -> None:
        job_id = str(uuid.uuid4())
        with _JOBS_LOCK:
            _JOBS[job_id] = {"job_id": job_id, "status": "running", "result": None, "error": ""}

        def _runner() -> None:
            try:
                env_file = Path(str(payload.get("env_file") or ".env"))
                if env_file:
                    load_env_file(env_file)
                validate_sources = ["pagerduty", "datadog", "slack"]
                github_owner = str(payload.get("github_owner") or "")
                github_repo = str(payload.get("github_repo") or "")
                if github_owner and github_repo:
                    validate_sources.append("github")
                v = validate_source_env(validate_sources)
                if not v.ok:
                    parts = [f"{src}: {', '.join(vals)}" for src, vals in v.missing.items()]
                    raise CoralError("Missing required environment variables. " + "; ".join(parts), category="config")
                incident_id = str(payload.get("incident_id") or "").strip()
                if not incident_id:
                    raise CoralError("incident_id is required", category="config")
                output_dir = Path(str(payload.get("output_dir") or "output"))
                output_dir.mkdir(parents=True, exist_ok=True)
                metrics_log = Path(str(payload.get("metrics_log") or "output/run_metrics.jsonl"))
                workflow_log = Path(str(payload.get("workflow_log") or "output/workflow_log.json"))
                sql_dir = Path(str(payload.get("sql_dir") or "deliverables/sql"))
                extra_vars: dict[str, str] = {}
                if github_owner:
                    extra_vars["GITHUB_OWNER"] = github_owner
                if github_repo:
                    extra_vars["GITHUB_REPO"] = github_repo
                coral = _build_coral(payload)
                workflow = run_deterministic_workflow(
                    coral=coral,
                    incident_id=incident_id,
                    sql_dir=sql_dir,
                    extra_vars=extra_vars or None,
                )
                brief = workflow.brief
                (output_dir / f"{incident_id}.json").write_text(json.dumps(brief.to_dict(), indent=2), encoding="utf-8")
                write_workflow_log(workflow_log, workflow.workflow_log)
                append_run_metrics(
                    metrics_log,
                    incident_id=incident_id,
                    mode="live",
                    total_duration_ms=workflow.total_duration_ms,
                    brief=brief,
                )
                result = {
                    "incident_id": incident_id,
                    "brief": brief.to_dict(),
                    "workflow_log": workflow.workflow_log,
                    "total_duration_ms": workflow.total_duration_ms,
                }
                with _JOBS_LOCK:
                    _JOBS[job_id] = {"job_id": job_id, "status": "done", "result": result, "error": ""}
            except Exception as exc:
                with _JOBS_LOCK:
                    _JOBS[job_id] = {"job_id": job_id, "status": "failed", "result": None, "error": str(exc)}

        threading.Thread(target=_runner, daemon=True).start()
        _json_response(self, HTTPStatus.OK, {"job_id": job_id, "status": "running"})

    def _post_ship_readiness(self, payload: dict[str, Any]) -> None:
        report_dir = Path(str(payload.get("report_dir") or "output/report"))
        output_dir = Path(str(payload.get("output_dir") or "output"))
        report_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        incident_id = str(payload.get("incident_id") or "").strip()
        if not incident_id:
            raise CoralError("incident_id is required", category="config")

        metrics_log = Path(str(payload.get("metrics_log") or "output/run_metrics.jsonl"))
        recent_runs = int(payload.get("recent_runs") or 0)
        min_success_rate = float(payload.get("min_success_rate") or 0.7)
        min_improvement_percent = float(payload.get("min_improvement_percent") or 10.0)
        min_progress_percent = float(payload.get("min_progress_percent") or 90.0)
        min_scorecard_overall = float(payload.get("min_scorecard_overall") or 70.0)
        root = Path(str(payload.get("root") or "."))

        demo_report = write_demo_report(
            metrics_log,
            report_dir / "demo_report.json",
            report_dir / "demo_report.md",
            recent_runs=recent_runs,
        )
        quality = run_quality_gate(
            incident_id=incident_id,
            output_dir=output_dir,
            report_dir=report_dir,
            min_success_rate=min_success_rate,
            min_improvement_percent=min_improvement_percent,
        )
        (report_dir / "quality_gate.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
        scorecard = write_scorecard(
            report_dir=report_dir,
            quality_gate_path=report_dir / "quality_gate.json",
            out_json=report_dir / "scorecard.json",
            out_md=report_dir / "scorecard.md",
        )
        readiness = write_live_readiness_report(
            root,
            report_dir / "live_readiness.json",
            report_dir / "live_readiness.md",
        )
        release = write_release_check(
            root,
            report_dir / "release_check.json",
            report_dir / "release_check.md",
            min_progress_percent=min_progress_percent,
            min_scorecard_overall=min_scorecard_overall,
        )
        write_dashboard(report_dir, report_dir / "status_dashboard.md")
        handoff = write_handoff_note(report_dir, report_dir / "handoff_note.md")
        _json_response(
            self,
            HTTPStatus.OK,
            {
                "demo_report": demo_report,
                "quality_gate": quality,
                "scorecard": scorecard,
                "live_readiness": readiness,
                "release_check": release,
                "handoff_summary": handoff,
            },
        )

    def _post_judge_pack(self, payload: dict[str, Any]) -> None:
        bundle_root = Path(str(payload.get("bundle_root") or "output/bundles"))
        output_zip = Path(str(payload.get("output_zip") or "output/judge_pack.zip"))
        source_dir = str(payload.get("source_dir") or "").strip()
        if source_dir:
            src = Path(source_dir)
        else:
            dirs = [p for p in bundle_root.glob("submission_bundle_*") if p.is_dir()]
            if not dirs:
                raise CoralError("no submission bundle directory found", category="config")
            dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            src = dirs[0]
        out = create_judge_pack(src, output_zip)
        _json_response(self, HTTPStatus.OK, {"source_dir": str(src), "output_zip": str(out)})


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), _Handler)
    print(f"Incident Captain API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
