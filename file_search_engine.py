from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from extension_filter import ExtensionFilter
from file_item import FileItem
from metadata_extractor import MetadataExtractor
from query_matcher import QueryMatcher
from query_parser import QueryParser


class FileSearchEngine:
    """Responsible for scanning file systems, filtering, and sorting FileItems."""

    def __init__(
        self,
        query_parser: Optional[QueryParser] = None,
        query_matcher: Optional[QueryMatcher] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
    ):
        self.query_parser = query_parser or QueryParser()
        self.query_matcher = query_matcher or QueryMatcher()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()

    @staticmethod
    def collect_files_sorted_by_mtime(folder: Path, reverse: bool = True) -> List[Tuple[Path, float]]:
        """
        Scans all files recursively in folder and sorts them by last modified date.
        By default (reverse=True), orders files from newest to oldest.
        """
        file_entries: List[Tuple[Path, float]] = []
        for f in folder.glob("**/*"):
            try:
                if f.is_file():
                    file_entries.append((f, f.stat().st_mtime))
            except (OSError, PermissionError):
                continue

        file_entries.sort(key=lambda x: x[1], reverse=reverse)
        return file_entries

    def search(
        self,
        folder: Path,
        pattern_query: str = "",
        publisher_query: str = "",
        extensions_query: str = "",
        limit: int = 0,
        cancel_check: Optional[Callable[[], bool]] = None,
        progress_callback: Optional[Callable[[int, int, FileItem], None]] = None,
    ) -> List[FileItem]:
        """
        Executes search on target folder and yields matching FileItems ordered from newest to oldest.
        """
        pattern_rules, pattern_excludes = self.query_parser.parse(pattern_query)
        pub_rules, pub_excludes = self.query_parser.parse(publisher_query)
        ext_filter = ExtensionFilter.from_string(extensions_query)

        file_entries = self.collect_files_sorted_by_mtime(folder, reverse=True)
        total_files = len(file_entries)
        results: List[FileItem] = []

        for idx, (file, mtime) in enumerate(file_entries):
            if cancel_check and cancel_check():
                break

            file_ext = file.suffix.lstrip(".").lower()
            if not ext_filter.matches(file_ext):
                continue

            filename = file.name
            if not self.query_matcher.matches(filename, pattern_rules, pattern_excludes):
                continue

            publisher = self.metadata_extractor.extract_publisher(filename)
            if not self.query_matcher.matches(publisher, pub_rules, pub_excludes):
                continue

            year = self.metadata_extractor.extract_year(filename)
            item = FileItem(path=file, year=year, publisher=publisher, modified=mtime)
            results.append(item)

            if progress_callback:
                progress_callback(idx + 1, total_files, item)

            if limit > 0 and len(results) >= limit:
                break

        return results

    @staticmethod
    def sort_results(results: List[FileItem], sort_by: List[str], reverse: bool = True) -> List[FileItem]:
        """Sorts a list of FileItems by multi-criteria sort list."""
        if not sort_by or not results:
            return results
        return sorted(results, key=lambda item: item.get_sort_key(sort_by), reverse=reverse)

    def list_direct_folder_files(self, folder: Path) -> List[FileItem]:
        """Lists only files directly located within folder (non-recursive), extracting metadata."""
        if not folder.exists() or not folder.is_dir():
            return []
        items: List[FileItem] = []
        try:
            with os.scandir(folder) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            stat = entry.stat()
                            mtime = stat.st_mtime
                            filename = entry.name
                            p = Path(entry.path)
                            pub = self.metadata_extractor.extract_publisher(filename)
                            year = self.metadata_extractor.extract_year(filename)
                            items.append(FileItem(path=p, year=year, publisher=pub, modified=mtime))
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            return []

        # Sort newest to oldest by default
        items.sort(key=lambda item: item.modified, reverse=True)
        return items

