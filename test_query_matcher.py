"""Unit tests for QueryMatcher class."""

import unittest
from query_matcher import QueryMatcher
from query_parser import QueryParser


class TestQueryMatcher(unittest.TestCase):
    """Unit tests for QueryMatcher rule evaluation."""

    def test_comma_or_matches(self):
        rules, excludes = QueryParser.parse("java, j2ee")
        self.assertTrue(QueryMatcher.matches("Packt - Java 17 Basics.pdf", rules, excludes))
        self.assertTrue(QueryMatcher.matches("Manning - J2EE Architecture.epub", rules, excludes))
        self.assertFalse(QueryMatcher.matches("OReilly - Python Deep Learning.pdf", rules, excludes))

    def test_inline_not_matches(self):
        rules, excludes = QueryParser.parse("ai * pattern NOT apress and addison")
        self.assertTrue(QueryMatcher.matches("Packt - AI Design Patterns - 2024.pdf", rules, excludes))
        self.assertTrue(QueryMatcher.matches("Wiley - AI Enterprise Patterns.pdf", rules, excludes))
        self.assertFalse(QueryMatcher.matches("Apress - AI Architecture Patterns.pdf", rules, excludes))
        self.assertFalse(QueryMatcher.matches("Addison-Wesley - AI Integration Patterns.pdf", rules, excludes))

    def test_global_exclusion_matches(self):
        rules, excludes = QueryParser.parse("python, NOT apress and addison")
        self.assertTrue(QueryMatcher.matches("Packt - Python Clean Code.pdf", rules, excludes))
        self.assertFalse(QueryMatcher.matches("Apress - Python Beginners.pdf", rules, excludes))
        self.assertFalse(QueryMatcher.matches("Addison-Wesley - Python Distilled.pdf", rules, excludes))

    def test_empty_query_matches_all(self):
        rules, excludes = QueryParser.parse("")
        self.assertTrue(QueryMatcher.matches("AnyFile.pdf", rules, excludes))


if __name__ == "__main__":
    unittest.main()
