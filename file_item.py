from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


@dataclass
class FileItem:
    """Domain model representing a file with its extracted metadata and formatting helpers."""

    path: Path
    year: int
    publisher: str
    modified: float

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def parent_str(self) -> str:
        return str(self.path.parent)

    @property
    def publisher_display(self) -> str:
        return self.publisher.title()

    @property
    def year_display(self) -> str:
        return str(self.year) if self.year > 0 else "-"

    @property
    def date_modified_str(self) -> str:
        return datetime.fromtimestamp(self.modified).strftime("%Y-%m-%d %H:%M")

    def get_sort_key(self, sort_by: List[str]) -> Tuple:
        key = []
        for criteria in sort_by:
            if criteria == "published":
                key.append(self.year)
            elif criteria == "publisher":
                key.append(self.publisher)
            elif criteria == "modified":
                key.append(self.modified)
            elif criteria == "name":
                key.append(self.name.lower())
        return tuple(key)

    def to_legacy_tuple(self) -> Tuple[Path, int, str, float]:
        """Helper to convert to legacy 4-tuple format: (path, year, publisher, modified)."""
        return (self.path, self.year, self.publisher, self.modified)
