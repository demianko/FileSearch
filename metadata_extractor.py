from __future__ import annotations

from pathlib import Path
import re
from typing import Optional

from file_item import FileItem


class MetadataExtractor:
    """Responsible for extracting publishing year and publisher name from file names."""

    @staticmethod
    def extract_year(filename: str) -> int:
        match = re.search(r'\b(19\d{2}|20\d{2})\b', filename)
        return int(match.group()) if match else 0

    @staticmethod
    def extract_publisher(filename: str) -> str:
        match = re.match(r'([^\-]+)-', filename)
        return match.group(1).strip().lower() if match else "unknown"

    @classmethod
    def create_file_item(cls, file_path: Path, mtime: Optional[float] = None) -> FileItem:
        if mtime is None:
            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                mtime = 0.0
        filename = file_path.name
        year = cls.extract_year(filename)
        publisher = cls.extract_publisher(filename)
        return FileItem(path=file_path, year=year, publisher=publisher, modified=mtime)
