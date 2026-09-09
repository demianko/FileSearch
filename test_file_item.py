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

    def test_directory_item(self):
        folder_item = FileItem(path=Path("/books/scifi"), year=0, publisher="Folder", modified=1700000000.0, is_directory=True)
        self.assertTrue(folder_item.is_directory)
        self.assertEqual(folder_item.name, "scifi")
        self.assertEqual(folder_item.name_display, "📁  scifi")
        self.assertEqual(folder_item.publisher_display, "Folder")
        self.assertEqual(folder_item.year_display, "-")


if __name__ == "__main__":
    unittest.main()
