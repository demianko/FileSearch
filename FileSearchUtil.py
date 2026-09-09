"""FileSearchUtil - Modern 2026 Desktop File Search & Sort Utility.

Main entrypoint re-exporting all modular single-responsibility components:
- AppConfig, ConfigManager (from app_config)
- SearchRule (from search_rule)
- QueryParser (from query_parser)
- QueryMatcher (from query_matcher)
- ExtensionFilter (from extension_filter)
- FileItem (from file_item)
- MetadataExtractor (from metadata_extractor)
- FileSearchEngine (from file_search_engine)
- FileSearchApp (from file_search_app)
"""

from __future__ import annotations

from app_config import AppConfig, ConfigManager
from extension_filter import ExtensionFilter
from file_item import FileItem
from file_search_app import FileSearchApp
from file_search_engine import FileSearchEngine
from metadata_extractor import MetadataExtractor
from query_matcher import QueryMatcher
from query_parser import QueryParser
from search_rule import SearchRule
from windows_drag_drop import normalize_drag_path, start_drag

__all__ = [
    "AppConfig",
    "ConfigManager",
    "SearchRule",
    "QueryParser",
    "QueryMatcher",
    "ExtensionFilter",
    "FileItem",
    "MetadataExtractor",
    "FileSearchEngine",
    "FileSearchApp",
    "normalize_drag_path",
    "start_drag",
]


if __name__ == "__main__":
    app = FileSearchApp()
    app.mainloop()