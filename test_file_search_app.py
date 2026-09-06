"""Unit tests for FileSearchApp class and delegates."""

from pathlib import Path
import unittest

from file_item import FileItem
from file_search_app import FileSearchApp


class TestFileSearchApp(unittest.TestCase):
    """Unit tests for FileSearchApp delegates and helpers."""

    def test_app_static_delegates(self):
        self.assertEqual(FileSearchApp.extract_year("Packt - AI - 2025.pdf"), 2025)
        self.assertEqual(FileSearchApp.extract_publisher("Packt - AI - 2025.pdf"), "packt")

        rx = FileSearchApp.term_to_regex("java * pattern")
        self.assertTrue(bool(rx.search("Packt - Java 17 Design Patterns - 2024.pdf")))

        rules, exc = FileSearchApp.parse_search_query("java, j2ee")
        self.assertEqual(len(rules), 2)
        self.assertTrue(FileSearchApp.matches_query("Java 21.pdf", rules, exc))

        inc, exc_exts = FileSearchApp.parse_extensions("pdf, epub, -java")
        self.assertEqual(inc, {"pdf", "epub"})
        self.assertEqual(exc_exts, {"java"})
        self.assertTrue(FileSearchApp.matches_extension("pdf", inc, exc_exts))
        self.assertFalse(FileSearchApp.matches_extension("java", inc, exc_exts))

    def test_app_get_sort_key(self):
        app = FileSearchApp.__new__(FileSearchApp)

        # FileItem instance
        item = FileItem(path=Path("test.pdf"), year=2024, publisher="packt", modified=1700000000.0)
        key1 = app.get_sort_key(item, ["published", "publisher", "modified"])
        self.assertEqual(key1, (2024, "packt", 1700000000.0))

        # Legacy tuple instance
        legacy = (Path("test.pdf"), 2024, "packt", 1700000000.0)
        key2 = app.get_sort_key(legacy, ["published", "publisher", "modified"])
        self.assertEqual(key2, (2024, "packt", 1700000000.0))


if __name__ == "__main__":
    unittest.main()
