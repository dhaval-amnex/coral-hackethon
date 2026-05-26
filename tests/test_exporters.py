from pathlib import Path

from incident_captain.exporters import write_markdown
from incident_captain.models import Evidence, IncidentBrief


def test_write_markdown(tmp_path: Path) -> None:
    brief = IncidentBrief(
        incident_id="INC-9",
        summary="test summary",
        probable_root_cause="test cause",
        confidence="medium",
        impacted_services=["payments"],
        owners=["alice"],
        evidence=[Evidence(type="deploy", detail="deploy detail", link="http://example")],
        recommended_actions=["action 1"],
    )
    out = tmp_path / "brief.md"
    write_markdown(out, brief)
    text = out.read_text(encoding="utf-8")
    assert "# Incident Brief: INC-9" in text
    assert "deploy detail" in text
    assert "action 1" in text

