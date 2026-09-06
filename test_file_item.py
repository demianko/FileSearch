"""Unit tests for FileItem domain model."""

from pathlib import Path
import unittest

from file_item import FileItem


class TestFileItem(unittest.TestCase):
    """Unit tests for FileItem domain model."""

    def test_file_item_properties_and_sorting(self):
        item = FileItem(path=Path("/books/Packt - AI - 2024.pdf"), year=2024, publisher="packt", modified=1700000000.0)
        self.assertEqual(item.name, "Packt - AI - 2024.pdf")
        self.assertEqual(item.year_display, "2024")
        self.assertEqual(item.publisher_display, "Packt")

        key = item.get_sort_key(["published", "publisher", "modified"])
        self.assertEqual(key, (2024, "packt", 1700000000.0))

    def test_year_display_when_zero(self):
        item = FileItem(path=Path("book.pdf"), year=0, publisher="unknown", modified=1700000000.0)
        self.assertEqual(item.year_display, "-")

    def test_legacy_tuple_conversion(self):
        item = FileItem(path=Path("test.pdf"), year=2023, publisher="manning", modified=1600000000.0)
        t = item.to_legacy_tuple()
        self.assertEqual(t, (Path("test.pdf"), 2023, "manning", 1600000000.0))


if __name__ == "__main__":
    unittest.main()
