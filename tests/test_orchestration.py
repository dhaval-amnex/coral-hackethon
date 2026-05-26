from pathlib import Path
import json

from incident_captain.coral import CoralClient
from incident_captain.orchestration import run_deterministic_workflow, write_workflow_log


def test_run_deterministic_workflow_mock(tmp_path: Path) -> None:
    files = [
        "active_incidents.json",
        "deploy_correlation.json",
        "telemetry_context.json",
        "team_comms.json",
        "final_dataset.json",
    ]
    for name in files:
        (tmp_path / name).write_text(json.dumps([{"title": "x"}]), encoding="utf-8")

    workflow = run_deterministic_workflow(
        coral=CoralClient("coral"),
        incident_id="INC-8",
        sql_dir=tmp_path,
        mock_data_dir=tmp_path,
    )
    assert len(workflow.workflow_log) == 3
    assert workflow.workflow_log[0]["step"] == "discover_catalog"
    assert workflow.brief.incident_id == "INC-8"


def test_write_workflow_log(tmp_path: Path) -> None:
    out = tmp_path / "workflow.json"
    write_workflow_log(out, [{"step": "x", "status": "ok"}])
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload[0]["step"] == "x"

