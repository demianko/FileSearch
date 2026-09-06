"""Unit tests for SearchRule class."""

import unittest
from query_parser import QueryParser
from search_rule import SearchRule


class TestSearchRule(unittest.TestCase):
    """Unit tests for SearchRule inclusion and exclusion evaluation."""

    def test_single_include_rule(self):
        rule = SearchRule(include_regex=QueryParser.term_to_regex("python"))
        self.assertTrue(rule.matches("Learn Python Programming.pdf"))
        self.assertFalse(rule.matches("Java Design Patterns.epub"))

    def test_include_with_single_exclude(self):
        rule = SearchRule(
            include_regex=QueryParser.term_to_regex("python"),
            exclude_regex=QueryParser.term_to_regex("draft"),
        )
        self.assertTrue(rule.matches("Python Clean Code.pdf"))
        self.assertFalse(rule.matches("Python Clean Code Draft.pdf"))

    def test_include_with_multiple_excludes(self):
        excludes = [QueryParser.term_to_regex("draft"), QueryParser.term_to_regex("deprecated")]
        rule = SearchRule(include_regex=QueryParser.term_to_regex("python"), exclude_regex=excludes)
        self.assertTrue(rule.matches("Python Clean Code.pdf"))
        self.assertFalse(rule.matches("Python Draft.pdf"))
        self.assertFalse(rule.matches("Python Deprecated Edition.pdf"))

    def test_no_include_matches_all_non_excluded(self):
        rule = SearchRule(include_regex=None, exclude_regex=QueryParser.term_to_regex("draft"))
        self.assertTrue(rule.matches("Python Clean Code.pdf"))
        self.assertFalse(rule.matches("Python Clean Code Draft.pdf"))


if __name__ == "__main__":
    unittest.main()
