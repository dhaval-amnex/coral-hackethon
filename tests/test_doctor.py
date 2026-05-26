from pathlib import Path

from incident_captain.doctor import build_doctor_report


def test_build_doctor_report(tmp_path: Path) -> None:
    report = build_doctor_report(tmp_path)
    assert "python_version" in report
    assert "coral_available" in report
    assert "report_dir_exists" in report

