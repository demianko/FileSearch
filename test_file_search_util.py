"""Unit Tests for FileSearchUtil query parser, pattern matching, and metadata extractors."""

import unittest
from pathlib import Path
from FileSearchUtil import FileSearchApp, SearchRule


class TestFileSearchUtil(unittest.TestCase):

    def setUp(self):
        self.app_cls = FileSearchApp

    # --- 1. Term to Regex Tests ---

    def test_wildcard_star(self):
        rx = self.app_cls.term_to_regex("java * pattern")
        self.assertTrue(bool(rx.search("Packt - Java 17 Design Patterns - 2024.pdf")))
        self.assertTrue(bool(rx.search("java-concurrency-patterns.epub")))
        self.assertTrue(bool(rx.search("learn_java_pattern.txt")))
        self.assertFalse(bool(rx.search("python-basics.pdf")))

    def test_wildcard_question_mark(self):
        rx = self.app_cls.term_to_regex("python?")
        self.assertTrue(bool(rx.search("python3.pdf")))
        self.assertTrue(bool(rx.search("pythons.epub")))
        self.assertFalse(bool(rx.search("pyth.pdf")))  # Missing 'on' + character
        self.assertFalse(bool(rx.search("javascript.pdf")))

    def test_pipe_or_operator(self):
        rx = self.app_cls.term_to_regex("ai agent|agents")
        self.assertTrue(bool(rx.search("Hands-On AI Agent.pdf")))
        self.assertTrue(bool(rx.search("Mastering Multi-AI Agents.epub")))
        self.assertFalse(bool(rx.search("Deep Learning Guide.pdf")))

    def test_pipe_or_with_wildcards(self):
        rx = self.app_cls.term_to_regex("java|kotlin * pattern")
        self.assertTrue(bool(rx.search("Java Design Pattern.pdf")))
        self.assertTrue(bool(rx.search("Kotlin 2.0 Design Pattern.pdf")))
        self.assertFalse(bool(rx.search("Rust Concurrency.pdf")))

    # --- 2. Query Parsing and NOT Logic Tests ---

    def test_comma_or_operator(self):
        # Query: "java, j2ee" (comma separates multiple alternative search patterns)
        rules, excludes = self.app_cls.parse_search_query("java, j2ee")
        self.assertEqual(len(rules), 2)
        self.assertEqual(len(excludes), 0)

        # Matches "java"
        self.assertTrue(self.app_cls.matches_query("Packt - Java 17 Basics.pdf", rules, excludes))
        # Matches "j2ee"
        self.assertTrue(self.app_cls.matches_query("Manning - J2EE Architecture.epub", rules, excludes))
        # Neither matches
        self.assertFalse(self.app_cls.matches_query("OReilly - Python Deep Learning.pdf", rules, excludes))

    def test_not_exclusion_within_clause(self):
        # Query: "ai agent NOT agents"
        rules, excludes = self.app_cls.parse_search_query("ai agent NOT agents")
        self.assertEqual(len(rules), 1)

        # File containing "ai agent" but not "agents" -> MATCH
        self.assertTrue(
            self.app_cls.matches_query("Packt - Practical AI Agent Development.pdf", rules, excludes)
        )
        # File containing "agents" -> EXCLUDED
        self.assertFalse(
            self.app_cls.matches_query("Mastering Multi-AI Agents in Practice.pdf", rules, excludes)
        )
        # File without "ai agent" -> NO MATCH
        self.assertFalse(
            self.app_cls.matches_query("Python Basics 2024.pdf", rules, excludes)
        )

    def test_multiple_not_exclusions_with_and(self):
        # User query: "ai * pattern not apress and addison"
        rules, excludes = self.app_cls.parse_search_query("ai * pattern not apress and addison")
        self.assertEqual(len(rules), 1)

        # Matches include pattern and not in excluded publishers
        self.assertTrue(
            self.app_cls.matches_query("Packt - AI Design Patterns - 2024.pdf", rules, excludes)
        )
        self.assertTrue(
            self.app_cls.matches_query("Wiley - AI Enterprise Patterns.pdf", rules, excludes)
        )
        # Excluded because publisher is Apress
        self.assertFalse(
            self.app_cls.matches_query("Apress - AI Architecture Patterns.pdf", rules, excludes)
        )
        # Excluded because publisher is Addison-Wesley
        self.assertFalse(
            self.app_cls.matches_query("Addison-Wesley - AI Integration Patterns.pdf", rules, excludes)
        )

    def test_multiple_not_exclusions_variants(self):
        # Variant 1: repeated NOT -> "ai * pattern not apress not addison"
        rules1, exc1 = self.app_cls.parse_search_query("ai * pattern not apress not addison")
        self.assertTrue(self.app_cls.matches_query("Packt - AI Design Patterns.pdf", rules1, exc1))
        self.assertFalse(self.app_cls.matches_query("Apress - AI Patterns.pdf", rules1, exc1))
        self.assertFalse(self.app_cls.matches_query("Addison-Wesley - AI Patterns.pdf", rules1, exc1))

        # Variant 2: "and not" -> "ai * pattern not apress and not addison"
        rules2, exc2 = self.app_cls.parse_search_query("ai * pattern not apress and not addison")
        self.assertTrue(self.app_cls.matches_query("Packt - AI Design Patterns.pdf", rules2, exc2))
        self.assertFalse(self.app_cls.matches_query("Apress - AI Patterns.pdf", rules2, exc2))
        self.assertFalse(self.app_cls.matches_query("Addison-Wesley - AI Patterns.pdf", rules2, exc2))

        # Variant 3: ampersand -> "ai * pattern not apress & addison"
        rules3, exc3 = self.app_cls.parse_search_query("ai * pattern not apress & addison")
        self.assertTrue(self.app_cls.matches_query("Packt - AI Design Patterns.pdf", rules3, exc3))
        self.assertFalse(self.app_cls.matches_query("Apress - AI Patterns.pdf", rules3, exc3))
        self.assertFalse(self.app_cls.matches_query("Addison-Wesley - AI Patterns.pdf", rules3, exc3))

    def test_global_exclusion_with_multiple_terms(self):
        # Query: "python, NOT apress and addison"
        rules, excludes = self.app_cls.parse_search_query("python, NOT apress and addison")
        self.assertTrue(self.app_cls.matches_query("Packt - Python Clean Code.pdf", rules, excludes))
        self.assertFalse(self.app_cls.matches_query("Apress - Python Beginners.pdf", rules, excludes))
        self.assertFalse(self.app_cls.matches_query("Addison-Wesley - Python Distilled.pdf", rules, excludes))


    def test_global_exclusion_dash_and_not(self):
        # Query: "python, -draft, NOT old"
        rules, excludes = self.app_cls.parse_search_query("python, -draft, NOT old")

        self.assertTrue(
            self.app_cls.matches_query("Python Clean Code.pdf", rules, excludes)
        )
        # Excluded by -draft
        self.assertFalse(
            self.app_cls.matches_query("Python Clean Code Draft.pdf", rules, excludes)
        )
        # Excluded by NOT old
        self.assertFalse(
            self.app_cls.matches_query("Python Old Edition.pdf", rules, excludes)
        )

    def test_multiple_comma_clauses(self):
        # Query: "python | rust NOT old, java * pattern NOT draft"
        rules, excludes = self.app_cls.parse_search_query(
            "python | rust NOT old, java * pattern NOT draft"
        )
        self.assertTrue(self.app_cls.matches_query("Rust Async Guide.pdf", rules, excludes))
        self.assertTrue(self.app_cls.matches_query("Java 21 Design Pattern.pdf", rules, excludes))
        self.assertFalse(self.app_cls.matches_query("Rust Old Guide.pdf", rules, excludes))
        self.assertFalse(self.app_cls.matches_query("Java Pattern Draft.pdf", rules, excludes))

    def test_empty_query_matches_all(self):
        rules, excludes = self.app_cls.parse_search_query("")
        self.assertTrue(self.app_cls.matches_query("AnyFile.pdf", rules, excludes))

    # --- 3. Metadata Extraction Tests ---

    def test_extract_year(self):
        app = self.app_cls.__new__(self.app_cls)
        self.assertEqual(app.extract_year("Packt - Python 3.12 - 2024.pdf"), 2024)
        self.assertEqual(app.extract_year("OReilly - Unix Systems - 1998.epub"), 1998)
        self.assertEqual(app.extract_year("NoYearBook.pdf"), 0)

    def test_extract_publisher(self):
        app = self.app_cls.__new__(self.app_cls)
        self.assertEqual(app.extract_publisher("Packt - Deep Learning - 2023.pdf"), "packt")
        self.assertEqual(app.extract_publisher("Manning - Java in Action - 2022.pdf"), "manning")
        self.assertEqual(app.extract_publisher("SimpleBookWithoutDash.pdf"), "unknown")

    # --- 4. Sorting Key Tests ---

    def test_sort_key_generation(self):
        app = self.app_cls.__new__(self.app_cls)
        file_data = (Path("test.pdf"), 2024, "packt", 1700000000.0)

        sort_by = ["published", "publisher", "modified"]
        key = app.get_sort_key(file_data, sort_by)
        self.assertEqual(key, (2024, "packt", 1700000000.0))

        sort_by_publisher = ["publisher"]
        key_pub = app.get_sort_key(file_data, sort_by_publisher)
    # --- 5. Extension Inclusion & Exclusion Tests ---

    def test_parse_extensions(self):
        inc, exc = self.app_cls.parse_extensions("pdf, epub, -java")
        self.assertEqual(inc, {"pdf", "epub"})
        self.assertEqual(exc, {"java"})

    def test_parse_extensions_variants(self):
        inc, exc = self.app_cls.parse_extensions("*.pdf, .epub, -*.java, NOT class, -tmp")
        self.assertEqual(inc, {"pdf", "epub"})
        self.assertEqual(exc, {"java", "class", "tmp"})

    def test_parse_extensions_only_excludes(self):
        inc, exc = self.app_cls.parse_extensions("-java, -class, -tmp")
        self.assertEqual(inc, set())
        self.assertEqual(exc, {"java", "class", "tmp"})

    def test_matches_extension(self):
        inc = {"pdf", "epub"}
        exc = {"java"}

        self.assertTrue(self.app_cls.matches_extension("pdf", inc, exc))
        self.assertTrue(self.app_cls.matches_extension(".epub", inc, exc))
        self.assertFalse(self.app_cls.matches_extension("java", inc, exc))
        self.assertFalse(self.app_cls.matches_extension("txt", inc, exc))

    def test_matches_extension_with_only_excludes(self):
        inc = set()
        exc = {"java", "class"}

        self.assertTrue(self.app_cls.matches_extension("pdf", inc, exc))
        self.assertTrue(self.app_cls.matches_extension("txt", inc, exc))
        self.assertFalse(self.app_cls.matches_extension("java", inc, exc))
        self.assertFalse(self.app_cls.matches_extension("class", inc, exc))


if __name__ == "__main__":
    unittest.main()
