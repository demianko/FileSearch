"""Unit tests for ExtensionFilter class."""

import unittest
from extension_filter import ExtensionFilter


class TestExtensionFilter(unittest.TestCase):
    """Unit tests for ExtensionFilter inclusion and exclusion."""

    def test_parse_extensions(self):
        f = ExtensionFilter.from_string("pdf, epub, -java")
        self.assertEqual(f.include_exts, {"pdf", "epub"})
        self.assertEqual(f.exclude_exts, {"java"})

    def test_parse_extensions_variants(self):
        f = ExtensionFilter.from_string("*.pdf, .epub, -*.java, NOT class, -tmp")
        self.assertEqual(f.include_exts, {"pdf", "epub"})
        self.assertEqual(f.exclude_exts, {"java", "class", "tmp"})

    def test_matches_extension_with_includes_and_excludes(self):
        f = ExtensionFilter.from_string("pdf, epub, -java")
        self.assertTrue(f.matches("pdf"))
        self.assertTrue(f.matches(".epub"))
        self.assertFalse(f.matches("java"))
        self.assertFalse(f.matches("txt"))

    def test_matches_extension_with_only_excludes(self):
        f = ExtensionFilter.from_string("-java, -class")
        self.assertTrue(f.matches("pdf"))
        self.assertTrue(f.matches("txt"))
        self.assertFalse(f.matches("java"))
        self.assertFalse(f.matches("class"))

    def test_empty_extension_filter_matches_all(self):
        f = ExtensionFilter.from_string("")
        self.assertTrue(f.matches("pdf"))
        self.assertTrue(f.matches("exe"))


if __name__ == "__main__":
    unittest.main()
