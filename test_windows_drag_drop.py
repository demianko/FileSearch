"""Unit tests for windows_drag_drop module."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

import windows_drag_drop
from windows_drag_drop import IS_WINDOWS, start_drag


class TestWindowsDragDrop(unittest.TestCase):
    """Unit tests for windows_drag_drop functionality."""

    def test_start_drag_empty_or_nonexistent(self):
        # Empty list should return 0 without error
        self.assertEqual(start_drag([]), 0)

        # Non-existent files should return 0
        self.assertEqual(start_drag(["non_existent_file_12345.xyz"]), 0)

    @unittest.skipUnless(IS_WINDOWS, "Requires Windows OS")
    def test_windows_com_structures_loaded(self):
        self.assertTrue(hasattr(windows_drag_drop, "IID_IDataObject"))
        self.assertTrue(hasattr(windows_drag_drop, "DataObject"))
        self.assertTrue(hasattr(windows_drag_drop, "DropSource"))
        self.assertEqual(windows_drag_drop.CF_HDROP, 15)
        self.assertEqual(windows_drag_drop.CF_UNICODETEXT, 13)
        self.assertEqual(windows_drag_drop.DRAGDROP_S_DROP, 0x00040100)
        self.assertEqual(windows_drag_drop.DRAGDROP_S_CANCEL, 0x00040101)
        self.assertEqual(windows_drag_drop.DRAGDROP_S_USEDEFAULTCURSORS, 0x00040102)

    @unittest.skipUnless(IS_WINDOWS, "Requires Windows OS")
    def test_hdrop_buffer_creation(self):
        test_file = str(Path(__file__).resolve())
        hdrop = windows_drag_drop._create_hdrop_buffer([test_file])
        self.assertIsNotNone(hdrop)

        # Test DragQueryFileW extracts the path from HDROP
        count = windows_drag_drop.shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
        self.assertEqual(count, 1)

        import ctypes
        buf = ctypes.create_unicode_buffer(512)
        windows_drag_drop.shell32.DragQueryFileW(hdrop, 0, buf, 512)
        self.assertEqual(buf.value.lower(), test_file.lower())

    @unittest.skipUnless(IS_WINDOWS, "Requires Windows OS")
    def test_unicodetext_buffer_creation(self):
        import ctypes
        test_file = str(Path(__file__).resolve())
        hmem = windows_drag_drop._create_unicodetext_buffer([test_file])
        self.assertIsNotNone(hmem)
        ptr = windows_drag_drop.kernel32.GlobalLock(hmem)
        try:
            val = ctypes.wstring_at(ptr)
            self.assertEqual(val, test_file)
        finally:
            windows_drag_drop.kernel32.GlobalUnlock(hmem)

    def test_start_drag_mocked_execution(self):
        dummy_file = Path(__file__).resolve()
        with patch("windows_drag_drop.IS_WINDOWS", False):
            res = start_drag([dummy_file])
            self.assertEqual(res, 0)


if __name__ == "__main__":
    unittest.main()
