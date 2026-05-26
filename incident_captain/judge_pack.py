from __future__ import annotations

from pathlib import Path
import shutil


def create_judge_pack(source_dir: Path, output_zip: Path) -> Path:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    base = output_zip.with_suffix("")
    archive = shutil.make_archive(str(base), "zip", root_dir=str(source_dir))
    created = Path(archive)
    if created != output_zip:
        if output_zip.exists():
            output_zip.unlink()
        created.replace(output_zip)
    return output_zip

