"""Unit tests for QueryParser class."""

import unittest
from query_parser import QueryParser


class TestQueryParser(unittest.TestCase):
    """Unit tests for QueryParser syntax compilation."""

    def test_wildcard_star(self):
        rx = QueryParser.term_to_regex("java * pattern")
        self.assertTrue(bool(rx.search("Packt - Java 17 Design Patterns - 2024.pdf")))
        self.assertTrue(bool(rx.search("java-concurrency-patterns.epub")))
        self.assertTrue(bool(rx.search("learn_java_pattern.txt")))
        self.assertFalse(bool(rx.search("python-basics.pdf")))

    def test_wildcard_question_mark(self):
        rx = QueryParser.term_to_regex("python?")
        self.assertTrue(bool(rx.search("python3.pdf")))
        self.assertTrue(bool(rx.search("pythons.epub")))
        self.assertFalse(bool(rx.search("pyth.pdf")))
        self.assertFalse(bool(rx.search("javascript.pdf")))

    def test_pipe_or_operator(self):
        rx = QueryParser.term_to_regex("ai agent|agents")
        self.assertTrue(bool(rx.search("Hands-On AI Agent.pdf")))
        self.assertTrue(bool(rx.search("Mastering Multi-AI Agents.epub")))
        self.assertFalse(bool(rx.search("Deep Learning Guide.pdf")))

    def test_pipe_or_with_wildcards(self):
        rx = QueryParser.term_to_regex("java|kotlin * pattern")
        self.assertTrue(bool(rx.search("Java Design Pattern.pdf")))
        self.assertTrue(bool(rx.search("Kotlin 2.0 Design Pattern.pdf")))
        self.assertFalse(bool(rx.search("Rust Concurrency.pdf")))

    def test_parse_exclude_terms_and(self):
        rxs = QueryParser.parse_exclude_terms("apress and addison and wiley")
        self.assertEqual(len(rxs), 3)
        self.assertTrue(bool(rxs[0].search("Apress Publishing")))
        self.assertTrue(bool(rxs[1].search("Addison-Wesley")))
        self.assertTrue(bool(rxs[2].search("John Wiley & Sons")))

    def test_parse_exclude_terms_variants(self):
        rxs_not = QueryParser.parse_exclude_terms("apress NOT addison")
        self.assertEqual(len(rxs_not), 2)

        rxs_and_not = QueryParser.parse_exclude_terms("apress and not addison")
        self.assertEqual(len(rxs_and_not), 2)

        rxs_amp = QueryParser.parse_exclude_terms("apress & addison")
        self.assertEqual(len(rxs_amp), 2)

    def test_parse_comma_or_query(self):
        rules, excludes = QueryParser.parse("java, j2ee")
        self.assertEqual(len(rules), 2)
        self.assertEqual(len(excludes), 0)

    def test_parse_inline_not_query(self):
        rules, excludes = QueryParser.parse("ai * pattern NOT apress and addison")
        self.assertEqual(len(rules), 1)
        self.assertEqual(len(excludes), 0)
        self.assertEqual(len(rules[0].exclude_regexes), 2)

    def test_parse_global_excludes(self):
        rules, excludes = QueryParser.parse("python, -draft, NOT old and deprecated")
        self.assertEqual(len(rules), 1)
        self.assertEqual(len(excludes), 3)  # draft, old, deprecated


if __name__ == "__main__":
    unittest.main()
