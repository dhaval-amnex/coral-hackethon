from pathlib import Path

from incident_captain.external_kit import write_external_kit


def test_write_external_kit(tmp_path: Path) -> None:
    result = write_external_kit(tmp_path / "kit")
    assert Path(result["readme"]).exists()
    assert Path(result["collect_script"]).exists()
    assert Path(result["metrics_template"]).exists()

