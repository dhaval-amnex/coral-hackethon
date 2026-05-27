from pathlib import Path
import json

from incident_captain.coral import CoralClient
from incident_captain.briefing import QUERY_FILES
from incident_captain.orchestration import run_deterministic_workflow, write_workflow_log


def test_run_deterministic_workflow(tmp_path: Path, monkeypatch) -> None:
    for _, file_name in QUERY_FILES:
        (tmp_path / file_name).write_text("SELECT 1", encoding="utf-8")

    def fake_run_sql(self, sql: str):
        return ([{"title": "x"}], 1)

    monkeypatch.setattr(CoralClient, "run_sql", fake_run_sql)

    workflow = run_deterministic_workflow(
        coral=CoralClient("coral"),
        incident_id="INC-8",
        sql_dir=tmp_path,
        extra_vars={"GITHUB_OWNER": "o", "GITHUB_REPO": "r"},
    )
    assert len(workflow.workflow_log) == 3
    assert workflow.workflow_log[0]["step"] == "discover_catalog"
    assert workflow.brief.incident_id == "INC-8"


def test_write_workflow_log(tmp_path: Path) -> None:
    out = tmp_path / "workflow.json"
    write_workflow_log(out, [{"step": "x", "status": "ok"}])
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload[0]["step"] == "x"
