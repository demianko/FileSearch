"""Unit tests for MetadataExtractor class."""

from pathlib import Path
import unittest

from metadata_extractor import MetadataExtractor


class TestMetadataExtractor(unittest.TestCase):
    """Unit tests for MetadataExtractor."""

    def test_extract_year(self):
        self.assertEqual(MetadataExtractor.extract_year("Packt - Python 3.12 - 2024.pdf"), 2024)
        self.assertEqual(MetadataExtractor.extract_year("OReilly - Unix Systems - 1998.epub"), 1998)
        self.assertEqual(MetadataExtractor.extract_year("NoYearBook.pdf"), 0)

    def test_extract_publisher(self):
        self.assertEqual(MetadataExtractor.extract_publisher("Packt - Deep Learning - 2023.pdf"), "packt")
        self.assertEqual(MetadataExtractor.extract_publisher("Manning - Java in Action - 2022.pdf"), "manning")
        self.assertEqual(MetadataExtractor.extract_publisher("SimpleBookWithoutDash.pdf"), "unknown")

    def test_create_file_item(self):
        item = MetadataExtractor.create_file_item(Path("Packt - AI Agents - 2025.pdf"), mtime=1700000000.0)
        self.assertEqual(item.year, 2025)
        self.assertEqual(item.publisher, "packt")
        self.assertEqual(item.publisher_display, "Packt")
        self.assertEqual(item.year_display, "2025")


if __name__ == "__main__":
    unittest.main()
