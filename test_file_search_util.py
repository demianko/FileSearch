"""Master Test Suite for FileSearchUtil project.

Imports and executes all individual component test suites:
- TestAppConfig (test_app_config.py)
- TestSearchRule (test_search_rule.py)
- TestQueryParser (test_query_parser.py)
- TestQueryMatcher (test_query_matcher.py)
- TestExtensionFilter (test_extension_filter.py)
- TestFileItem (test_file_item.py)
- TestMetadataExtractor (test_metadata_extractor.py)
- TestFileSearchEngine (test_file_search_engine.py)
- TestFileSearchApp (test_file_search_app.py)
"""

import unittest

from test_app_config import TestAppConfig
from test_extension_filter import TestExtensionFilter
from test_file_item import TestFileItem
from test_file_search_app import TestFileSearchApp
from test_file_search_engine import TestFileSearchEngine
from test_metadata_extractor import TestMetadataExtractor
from test_query_matcher import TestQueryMatcher
from test_query_parser import TestQueryParser
from test_search_rule import TestSearchRule

__all__ = [
    "TestAppConfig",
    "TestSearchRule",
    "TestQueryParser",
    "TestQueryMatcher",
    "TestExtensionFilter",
    "TestFileItem",
    "TestMetadataExtractor",
    "TestFileSearchEngine",
    "TestFileSearchApp",
]


if __name__ == "__main__":
    unittest.main()
