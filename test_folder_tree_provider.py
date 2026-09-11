"""Unit tests for folder_tree_provider module."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import folder_tree_provider
from folder_tree_provider import (
    get_system_drives,
    get_unc_to_drive_map,
    has_subdirectories,
    list_subdirectories,
)


class TestFolderTreeProvider(unittest.TestCase):
    """Tests for drive enumeration and directory listing."""

    def test_get_system_drives(self):
        drives = get_system_drives()
        self.assertIsInstance(drives, list)
        if folder_tree_provider.IS_WINDOWS:
            self.assertGreater(len(drives), 0)
            for root, label in drives:
                self.assertTrue(root.endswith("\\"))
                self.assertIn(":", root)
                self.assertIsInstance(label, str)
                self.assertGreater(len(label), 0)

    def test_has_subdirectories_and_list_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_p = Path(tmpdir)
            # Empty dir has no subdirectories
            self.assertFalse(has_subdirectories(tmpdir))
            self.assertEqual(list_subdirectories(tmpdir), [])

            # Create subdirectories: sub1, sub2 (with a subchild), and a file
            (tmp_p / "sub1").mkdir()
            sub2 = tmp_p / "sub2"
            sub2.mkdir()
            (sub2 / "child").mkdir()
            (tmp_p / "file.txt").write_text("hello", encoding="utf-8")

            # Test has_subdirectories
            self.assertTrue(has_subdirectories(tmpdir))
            self.assertFalse(has_subdirectories(str(tmp_p / "sub1")))
            self.assertTrue(has_subdirectories(str(sub2)))

            # Test list_subdirectories
            dirs = list_subdirectories(tmpdir)
            self.assertEqual(len(dirs), 2)
            names = [d[0] for d in dirs]
            self.assertEqual(names, ["sub1", "sub2"])

            # Verify has_children flag
            sub1_tuple = next(d for d in dirs if d[0] == "sub1")
            sub2_tuple = next(d for d in dirs if d[0] == "sub2")
            self.assertFalse(sub1_tuple[2])
            self.assertTrue(sub2_tuple[2])

    def test_system_directories_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_p = Path(tmpdir)
            (tmp_p / "$RECYCLE.BIN").mkdir()
            (tmp_p / "System Volume Information").mkdir()
            (tmp_p / "RealFolder").mkdir()

            dirs = list_subdirectories(tmpdir)
            self.assertEqual(len(dirs), 1)
            self.assertEqual(dirs[0][0], "RealFolder")


class TestFileExplorerNavCallbacks(unittest.TestCase):
    """Tests for FileExplorerNav callback triggering."""

    def test_on_f2_triggers_rename_callback(self):
        from file_explorer_nav import FileExplorerNav

        nav = FileExplorerNav.__new__(FileExplorerNav)
        nav.tree = MagicMock()
        nav.tree.selection.return_value = ("node_1",)
        nav.node_path_map = {"node_1": "D:\\MyDir\\SubDir"}
        mock_rename = MagicMock()
        nav.on_rename_callback = mock_rename

        res = nav._on_f2()
        self.assertEqual(res, "break")
        mock_rename.assert_called_once_with("D:\\MyDir\\SubDir")


if __name__ == "__main__":
    unittest.main()
