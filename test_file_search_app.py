"""Unit tests for FileSearchApp class and delegates."""

from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

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

    def test_tree_drag_handlers(self):
        from unittest.mock import MagicMock, patch

        app = FileSearchApp.__new__(FileSearchApp)
        app._drag_start_x = 0
        app._drag_start_y = 0
        app._drag_pending = False
        app._drag_item_clicked = None
        app.tree = MagicMock()
        app.results_map = {
            "1": FileItem(path=Path("item1.pdf"), year=2024, publisher="packt", modified=1700000000.0),
            "2": FileItem(path=Path("item2.pdf"), year=2025, publisher="oreilly", modified=1700000000.0),
        }

        # 1. Press outside rows
        app.tree.identify_row.return_value = ""
        event_outside = MagicMock(x=10, y=10, state=0)
        app._on_tree_press(event_outside)
        self.assertFalse(app._drag_pending)

        # 2. Press on an unselected row
        app.tree.identify_row.return_value = "1"
        app.tree.selection.return_value = ()
        event_press = MagicMock(x=10, y=10, state=0)
        app._on_tree_press(event_press)
        self.assertTrue(app._drag_pending)
        self.assertEqual(app._drag_item_clicked, "1")
        app.tree.selection_set.assert_called_with("1")

        # 3. Press on an item in a multi-selection without modifiers -> should return "break"
        app.tree.selection.return_value = ("1", "2")
        event_multi_press = MagicMock(x=10, y=10, state=0)
        res = app._on_tree_press(event_multi_press)
        self.assertEqual(res, "break")

        # 4. Motion below threshold (<= 5px) -> no drag triggered
        with patch("file_search_app.start_drag") as mock_start_drag:
            event_motion_small = MagicMock(x=12, y=12)
            app._on_tree_motion(event_motion_small)
            mock_start_drag.assert_not_called()
            self.assertTrue(app._drag_pending)

        # 5. Motion above threshold (> 5px) -> triggers start_drag
        with patch("file_search_app.start_drag") as mock_start_drag:
            event_motion_large = MagicMock(x=25, y=30)
            app._on_tree_motion(event_motion_large)
            self.assertFalse(app._drag_pending)
            mock_start_drag.assert_called_once()
            called_paths = mock_start_drag.call_args[0][0]
            self.assertEqual(len(called_paths), 2)
            self.assertEqual(called_paths[0], Path("item1.pdf"))
            self.assertEqual(called_paths[1], Path("item2.pdf"))

        # 6. Release after click on multi-selection without drag -> collapses selection
        app._drag_pending = True
        app._drag_item_clicked = "2"
        app.tree.selection.return_value = ("1", "2")
        event_release = MagicMock(state=0)
        app._on_tree_release(event_release)
        app.tree.selection_set.assert_called_with("2")
        self.assertFalse(app._drag_pending)

    def test_context_menu_actions(self):
        from unittest.mock import MagicMock

        app = FileSearchApp.__new__(FileSearchApp)
        app.tree = MagicMock()
        app.context_menu = MagicMock()
        app.empty_context_menu = MagicMock()
        app.clipboard_clear = MagicMock()
        app.clipboard_append = MagicMock()
        app.results_map = {
            "1": FileItem(path=Path("dir1/file1.pdf"), year=2024, publisher="packt", modified=1700000000.0),
            "2": FileItem(path=Path("dir2/file2.pdf"), year=2025, publisher="oreilly", modified=1700000000.0),
        }

        # Select all
        app.tree.get_children.return_value = ("1", "2")
        app._select_all_results()
        app.tree.selection_set.assert_called_with(("1", "2"))

        # Copy path
        app.tree.selection.return_value = ("1", "2")
        app._ctx_copy_path()
        app.clipboard_append.assert_called_with("dir1\\file1.pdf\ndir2\\file2.pdf" if "\\" in str(Path("dir1/file1.pdf")) else "dir1/file1.pdf\ndir2/file2.pdf")

        # Copy name
        app._ctx_copy_name()
        app.clipboard_append.assert_called_with("file1.pdf\nfile2.pdf")

        # Copy folder
        app._ctx_copy_folder()
        app.clipboard_append.assert_called_with("dir1\ndir2")

        # Show context menu on row
        app.tree.identify_row.return_value = "1"
        event = MagicMock(x=10, y=10, x_root=100, y_root=150)
        app._show_context_menu(event)
        app.context_menu.post.assert_called_with(100, 150)

        # Show context menu on empty space
        app.tree.identify_row.return_value = ""
        app._show_context_menu(event)
        app.empty_context_menu.post.assert_called_with(100, 150)

        # Test open_file_with delegate
        with patch("subprocess.Popen") as mock_popen, patch("os.path.exists", return_value=True), patch(
            "ctypes.windll.shell32.SHOpenWithDialog", return_value=0, create=True
        ):
            app.tree.selection.return_value = ("1",)
            app.results_map["1"].path = Path(__file__).resolve()
            app.open_file_with()


if __name__ == "__main__":
    unittest.main()
