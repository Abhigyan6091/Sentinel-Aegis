"""Filesystem store for campaign, gate, and regression report artifacts."""

import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from app.core.config import get_settings

_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ArtifactRecord(BaseModel):
    name: str
    size_bytes: int
    modified_at: datetime


class ArtifactStore:
    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory or get_settings().report_artifacts_dir)

    def _path(self, name: str) -> Path:
        if not _SAFE_NAME.match(name):
            raise ValueError(f"unsafe artifact name: {name!r}")
        return self.directory / name

    def write(self, name: str, content: str) -> Path:
        path = self._path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read(self, name: str) -> str | None:
        path = self._path(name)
        return path.read_text(encoding="utf-8") if path.exists() else None

    def list(self) -> list[ArtifactRecord]:
        if not self.directory.exists():
            return []
        return [
            ArtifactRecord(
                name=path.name,
                size_bytes=path.stat().st_size,
                modified_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
            )
            for path in sorted(self.directory.iterdir())
            if path.is_file()
        ]
