from pathlib import Path

from incident_captain.coral import render_sql_from_template


def test_render_sql_from_template(tmp_path: Path) -> None:
    sql_file = tmp_path / "x.sql"
    sql_file.write_text("select '{{INCIDENT_ID}}' as incident_id", encoding="utf-8")
    rendered = render_sql_from_template(sql_file, "INC-100")
    assert "INC-100" in rendered

