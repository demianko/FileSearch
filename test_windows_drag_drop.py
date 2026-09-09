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

    def test_normalize_drag_path_preserves_mapped_drive(self):
        from windows_drag_drop import normalize_drag_path

        # 1. Empty/whitespace
        self.assertEqual(normalize_drag_path(""), "")
        self.assertEqual(normalize_drag_path("   "), "")

        # 2. Local/mapped drive path preserves drive letter and does NOT resolve to UNC
        fake_mapped_path = r"Z:\Media\movie.mp4"
        norm = normalize_drag_path(fake_mapped_path)
        self.assertEqual(norm, fake_mapped_path)

        # 3. UNC path is mapped back to drive letter if in unc_to_drive map
        with patch("windows_drag_drop.get_unc_to_drive_map", return_value={r"\\server\share": "Z:"}):
            unc_input = r"\\server\share\Media\movie.mp4"
            mapped_out = normalize_drag_path(unc_input)
            self.assertEqual(mapped_out, r"Z:\Media\movie.mp4")

            unc_root = r"\\server\share"
            self.assertEqual(normalize_drag_path(unc_root), "Z:\\")

        # 4. Unmapped UNC path is preserved
        with patch("windows_drag_drop.get_unc_to_drive_map", return_value={}):
            unc_unknown = r"\\otherserver\share\file.mp4"
            self.assertEqual(normalize_drag_path(unc_unknown), unc_unknown)

    @unittest.skipUnless(IS_WINDOWS, "Requires Windows OS")
    def test_dataobject_query_and_getdata(self):
        from ctypes import byref, pointer
        test_file = str(Path(__file__).resolve())
        windows_drag_drop._active_drag_files = [test_file]
        dobj = pointer(windows_drag_drop._data_object_instance)

        # Verify CF_HDROP, CF_TEXT, CF_FILENAME, CF_FILENAMEW are all accepted
        for cf in [
            windows_drag_drop.CF_HDROP,
            windows_drag_drop.CF_TEXT,
            windows_drag_drop.CF_UNICODETEXT,
            windows_drag_drop.CF_FILENAME,
            windows_drag_drop.CF_FILENAMEW,
        ]:
            fetc = windows_drag_drop.FORMATETC(cf, None, 1, -1, 1)
            q_res = dobj.contents.lpVtbl.contents.QueryGetData(dobj, byref(fetc))
            self.assertEqual(q_res, 0, f"QueryGetData failed for format {cf}")

            med = windows_drag_drop.STGMEDIUM()
            g_res = dobj.contents.lpVtbl.contents.GetData(dobj, byref(fetc), byref(med))
            self.assertEqual(g_res, 0, f"GetData failed for format {cf}")
            self.assertEqual(med.tymed, windows_drag_drop.TYMED_HGLOBAL)
            self.assertIsNotNone(med.hGlobal)

    @unittest.skipUnless(IS_WINDOWS, "Requires Windows OS")
    def test_ascii_safe_path_resolution(self):
        import ctypes
        # Test 1: standard ASCII file
        test_file = str(Path(__file__).resolve())
        safe_p = windows_drag_drop._get_ascii_safe_path(test_file)
        self.assertEqual(safe_p, test_file)

        # Test 2: CF_TEXT buffer creation returns valid HGLOBAL and decodable string
        hmem = windows_drag_drop._create_text_buffer([test_file])
        self.assertIsNotNone(hmem)
        ptr = windows_drag_drop.kernel32.GlobalLock(hmem)
        try:
            val = ctypes.string_at(ptr).decode("mbcs")
            self.assertEqual(val, test_file)
        finally:
            windows_drag_drop.kernel32.GlobalUnlock(hmem)

        # Test 3: CF_FILENAME ansi buffer creation returns valid HGLOBAL
        hmem_fn = windows_drag_drop._create_filename_ansi_buffer([test_file])
        self.assertIsNotNone(hmem_fn)

    @unittest.skipUnless(IS_WINDOWS, "Requires Windows OS")
    def test_post_wm_dropfiles_creation(self):
        import ctypes
        test_file = str(Path(__file__).resolve())
        # Test with an invalid HWND (0) returns False
        self.assertFalse(windows_drag_drop._post_wm_dropfiles(0, [test_file]))
        self.assertFalse(windows_drag_drop._post_wm_dropfiles(0, []))

    @unittest.skipUnless(IS_WINDOWS, "Requires Windows OS")
    def test_drop_source_query_continue_drag(self):
        # Escape pressed should return DRAGDROP_S_CANCEL
        res = windows_drag_drop._drop_source_query_continue_drag(None, True, 0)
        self.assertEqual(res, windows_drag_drop.DRAGDROP_S_CANCEL)

        # Mouse still held down should return S_OK (0)
        res = windows_drag_drop._drop_source_query_continue_drag(None, False, windows_drag_drop.MK_LBUTTON)
        self.assertEqual(res, 0)


if __name__ == "__main__":
    unittest.main()


