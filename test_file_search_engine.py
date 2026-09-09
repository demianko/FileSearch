"""Unit tests for FileSearchEngine class."""

import os
from pathlib import Path
import tempfile
import unittest

from file_item import FileItem
from file_search_engine import FileSearchEngine


class TestFileSearchEngine(unittest.TestCase):
    """Unit tests for FileSearchEngine directory scanning, search, and sorting."""

    def test_collect_files_sorted_by_mtime(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            f_old = tmppath / "old_book.pdf"
            f_mid = tmppath / "mid_book.pdf"
            f_new = tmppath / "new_book.pdf"

            f_old.write_text("old")
            os.utime(f_old, (1000000, 1000000))

            f_mid.write_text("mid")
            os.utime(f_mid, (2000000, 2000000))

            f_new.write_text("new")
            os.utime(f_new, (3000000, 3000000))

            # Newest to oldest (reverse=True)
            files = FileSearchEngine.collect_files_sorted_by_mtime(tmppath, reverse=True)
            self.assertEqual(len(files), 3)
            self.assertEqual(files[0][0].name, "new_book.pdf")
            self.assertEqual(files[1][0].name, "mid_book.pdf")
            self.assertEqual(files[2][0].name, "old_book.pdf")

            # Oldest to newest (reverse=False)
            files_asc = FileSearchEngine.collect_files_sorted_by_mtime(tmppath, reverse=False)
            self.assertEqual(files_asc[0][0].name, "old_book.pdf")
            self.assertEqual(files_asc[1][0].name, "mid_book.pdf")
            self.assertEqual(files_asc[2][0].name, "new_book.pdf")

    def test_engine_search_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "Packt - AI Agents - 2024.pdf").write_text("1")
            (tmppath / "Apress - AI Patterns - 2023.pdf").write_text("2")
            (tmppath / "Wiley - Java Basics - 2022.pdf").write_text("3")

            engine = FileSearchEngine()
            results = engine.search(
                folder=tmppath,
                pattern_query="ai * NOT apress",
                extensions_query="pdf",
            )
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].name, "Packt - AI Agents - 2024.pdf")

    def test_engine_search_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            for i in range(10):
                (tmppath / f"Book_{i}.pdf").write_text(str(i))

            engine = FileSearchEngine()
            results = engine.search(
                folder=tmppath,
                extensions_query="pdf",
                limit=3,
            )
            self.assertEqual(len(results), 3)

    def test_engine_sort_results(self):
        engine = FileSearchEngine()
        item1 = FileItem(path=Path("A.pdf"), year=2020, publisher="packt", modified=100.0)
        item2 = FileItem(path=Path("B.pdf"), year=2024, publisher="manning", modified=200.0)

        sorted_items = engine.sort_results([item1, item2], ["published"], reverse=True)
        self.assertEqual(sorted_items[0].year, 2024)
        self.assertEqual(sorted_items[1].year, 2020)

    def test_list_direct_folder_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Direct files
            f1 = tmppath / "Wiley - Direct Book - 2023.pdf"
            f2 = tmppath / "Packt - Guide - 2022.epub"
            f1.write_text("1")
            f2.write_text("2")
            os.utime(f1, (1000000, 1000000))
            os.utime(f2, (2000000, 2000000))

            # Subdirectory with a file inside (should NOT be included)
            subdir = tmppath / "subfolder"
            subdir.mkdir()
            (subdir / "nested.pdf").write_text("nested")

            engine = FileSearchEngine()
            results = engine.list_direct_folder_files(tmppath)

            self.assertEqual(len(results), 3)
            names = [r.name for r in results]
            self.assertIn("subfolder", names)
            self.assertIn("Wiley - Direct Book - 2023.pdf", names)
            self.assertIn("Packt - Guide - 2022.epub", names)
            self.assertNotIn("nested.pdf", names)

            # Subfolders are listed first
            self.assertTrue(results[0].is_directory)
            self.assertEqual(results[0].name, "subfolder")
            self.assertEqual(results[0].publisher_display, "Folder")

            # Followed by files sorted newest first
            self.assertFalse(results[1].is_directory)
            self.assertEqual(results[1].name, "Packt - Guide - 2022.epub")
            self.assertEqual(results[1].year, 2022)
            self.assertEqual(results[1].publisher, "packt")


if __name__ == "__main__":
    unittest.main()
