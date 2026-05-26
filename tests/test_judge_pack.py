from pathlib import Path

from incident_captain.judge_pack import create_judge_pack


def test_create_judge_pack(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "a.txt").write_text("hello", encoding="utf-8")
    out = tmp_path / "judge_pack.zip"
    created = create_judge_pack(src, out)
    assert created.exists()
    assert created.suffix == ".zip"

