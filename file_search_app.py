from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional
import webbrowser

import customtkinter as ctk

from app_config import AppConfig, ConfigManager
from extension_filter import ExtensionFilter
from file_explorer_nav import FileExplorerNav
from file_item import FileItem
from file_search_engine import FileSearchEngine
from metadata_extractor import MetadataExtractor
from query_matcher import QueryMatcher
from query_parser import QueryParser
from search_rule import SearchRule
from windows_drag_drop import copy_files_to_clipboard, normalize_drag_path, start_drag


# Configure CustomTkinter Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class FileSearchApp(ctk.CTk):
    """Modern 2026 Desktop File Search & Sort Application Presentation Layer."""

    # Backward-compatibility delegates to domain services
    term_to_regex = staticmethod(QueryParser.term_to_regex)
    parse_exclude_terms = classmethod(lambda cls, s: QueryParser.parse_exclude_terms(s))
    parse_search_query = classmethod(lambda cls, s: QueryParser.parse(s))
    parse_extensions = classmethod(
        lambda cls, s: (ExtensionFilter.from_string(s).include_exts, ExtensionFilter.from_string(s).exclude_exts)
    )
    matches_extension = staticmethod(lambda ext, inc, exc: ExtensionFilter(inc, exc).matches(ext))
    collect_files_sorted_by_mtime = staticmethod(FileSearchEngine.collect_files_sorted_by_mtime)
    matches_query = staticmethod(QueryMatcher.matches)
    extract_year = staticmethod(MetadataExtractor.extract_year)
    extract_publisher = staticmethod(MetadataExtractor.extract_publisher)

    def __init__(
        self,
        search_engine: Optional[FileSearchEngine] = None,
        config_manager: Optional[ConfigManager] = None,
    ):
        super().__init__()

        self.search_engine = search_engine or FileSearchEngine()
        self.config_manager = config_manager or ConfigManager()

        # Load persisted config from ~/.filesearch/config
        config = self.config_manager.load()

        self.title("FileSearch Pro — Fast Search & Sort")
        self.geometry("1350x850")
        self.minsize(1050, 650)

        # Reactive State Variables loaded from config
        self.folder_path = tk.StringVar(value=config.directory)
        self.search_patterns = tk.StringVar(value=config.pattern)
        self.extensions = tk.StringVar(value=config.extension)
        self.sort_by = tk.StringVar(value=config.sort_order)
        self.publisher_filters = tk.StringVar(value=config.publisher)
        self.limit = tk.IntVar(value=config.limit)
        self.filter_var = tk.StringVar(value=config.filter_result)

        # Data Storage
        self.all_results: List[FileItem] = []
        self.displayed_results: List[FileItem] = []
        self.results_map: Dict[str, FileItem] = {}
        self.sort_column = ""
        self.sort_reverse = False
        self.is_searching = False
        self.cancel_search = False

        # Drag State Tracking
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_pending = False
        self._drag_item_clicked: Optional[str] = None

        self._create_widgets()
        self._setup_context_menu()

        # Handle window closing to save configuration
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Select initial directory in explorer navigation tree
        initial_dir = self.folder_path.get().strip()
        if initial_dir and os.path.exists(initial_dir):
            self.after(100, lambda: self.explorer_nav.select_path(initial_dir))

    def save_current_config(self):
        """Persists the current user inputs into ~/.filesearch/config."""
        config = AppConfig(
            directory=self.folder_path.get(),
            pattern=self.search_patterns.get(),
            extension=self.extensions.get(),
            sort_order=self.sort_by.get(),
            publisher=self.publisher_filters.get(),
            limit=self.limit.get(),
            filter_result=self.filter_var.get(),
        )
        self.config_manager.save(config)

    def _on_close(self):
        """Window close handler: persists user configuration and destroys window."""
        self.save_current_config()
        self.destroy()

    def _create_widgets(self):
        # Configure root layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Style ttk Panedwindow
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TPanedwindow", background="#1a1a1a")

        # Root PanedWindow: Left File Explorer Panel + Right Search Workspace
        self.paned_window = ttk.PanedWindow(self, orient="horizontal")
        self.paned_window.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

        # Left Panel: File Explorer Navigation Pane (full window height)
        self.explorer_nav = FileExplorerNav(
            self.paned_window,
            width=280,
            on_select_callback=self._on_nav_folder_selected,
        )

        # Right Panel: Workspace Container holding Controls, Filter, Results Table & Footer
        right_container = ctk.CTkFrame(self.paned_window, fg_color="transparent")
        right_container.grid_rowconfigure(2, weight=1)
        right_container.grid_columnconfigure(0, weight=1)

        self.paned_window.add(self.explorer_nav, weight=1)
        self.paned_window.add(right_container, weight=4)
        self.after(50, self._init_paned_sash)

        # 1. Top Card: Folder Selection & Search Inputs
        self._build_controls_card(right_container)

        # 2. Progress & Live Filter Bar
        self._build_progress_and_filter_card(right_container)

        # 3. Center Card: Modern Results Table (occupies full width of right workspace)
        self._build_results_card(right_container)

        # 4. Bottom Footer: Status Bar
        self._build_footer_status(right_container)

    def _build_controls_card(self, parent=None):
        parent = parent or self
        top_card = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color="#333333")
        top_card.grid(row=0, column=0, padx=(8, 0), pady=(0, 8), sticky="ew")
        top_card.grid_columnconfigure(1, weight=1)
        top_card.grid_columnconfigure(3, weight=1)

        # Row 0: Target Folder Picker
        lbl_folder = ctk.CTkLabel(
            top_card, text="📁 Directory:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        lbl_folder.grid(row=0, column=0, padx=(16, 8), pady=(12, 6), sticky="w")

        self.entry_folder = ctk.CTkEntry(
            top_card, textvariable=self.folder_path, height=34,
            placeholder_text="Enter folder path or click Browse..."
        )
        self.entry_folder.grid(row=0, column=1, columnspan=3, padx=(0, 8), pady=(12, 6), sticky="ew")
        self.entry_folder.bind("<Return>", self.search_files)
        self.entry_folder.bind("<KP_Enter>", self.search_files)

        btn_browse = ctk.CTkButton(
            top_card, text="Browse...", width=100, height=34,
            fg_color="#2b2b2b", hover_color="#3a3a3a", border_width=1, border_color="#444444",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.select_folder
        )
        btn_browse.grid(row=0, column=4, padx=(0, 16), pady=(12, 6), sticky="e")

        # Row 1: Search Patterns & File Extensions
        lbl_pattern = ctk.CTkLabel(
            top_card, text="🔍 Patterns (*, ?, |, NOT):", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        lbl_pattern.grid(row=1, column=0, padx=(16, 8), pady=4, sticky="w")

        self.entry_patterns = ctk.CTkEntry(
            top_card, textvariable=self.search_patterns, height=34,
            placeholder_text="e.g. ai agent NOT agents, java * pattern, python|rust"
        )
        self.entry_patterns.grid(row=1, column=1, padx=(0, 12), pady=4, sticky="ew")
        self.entry_patterns.bind("<Return>", self.search_files)
        self.entry_patterns.bind("<KP_Enter>", self.search_files)

        lbl_ext = ctk.CTkLabel(
            top_card, text="📄 Extensions (+/-):", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        lbl_ext.grid(row=1, column=2, padx=(8, 8), pady=4, sticky="w")

        self.entry_extensions = ctk.CTkEntry(
            top_card, textvariable=self.extensions, height=34,
            placeholder_text="e.g. pdf, epub, txt, -java"
        )
        self.entry_extensions.grid(row=1, column=3, columnspan=2, padx=(0, 16), pady=4, sticky="ew")
        self.entry_extensions.bind("<Return>", self.search_files)
        self.entry_extensions.bind("<KP_Enter>", self.search_files)

        # Row 2: Sort By, Publisher Filters, Limit
        lbl_sort = ctk.CTkLabel(
            top_card, text="⚡ Sort Order:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        lbl_sort.grid(row=2, column=0, padx=(16, 8), pady=4, sticky="w")

        self.entry_sort = ctk.CTkEntry(
            top_card, textvariable=self.sort_by, height=34,
            placeholder_text="e.g. published, publisher, modified"
        )
        self.entry_sort.grid(row=2, column=1, padx=(0, 12), pady=4, sticky="ew")
        self.entry_sort.bind("<Return>", self.search_files)
        self.entry_sort.bind("<KP_Enter>", self.search_files)

        lbl_pub = ctk.CTkLabel(
            top_card, text="🏢 Publishers:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        lbl_pub.grid(row=2, column=2, padx=(8, 8), pady=4, sticky="w")

        self.entry_publisher = ctk.CTkEntry(
            top_card, textvariable=self.publisher_filters, height=34,
            placeholder_text="e.g. packt, o'reilly, -manning"
        )
        self.entry_publisher.grid(row=2, column=3, columnspan=2, padx=(0, 16), pady=4, sticky="ew")
        self.entry_publisher.bind("<Return>", self.search_files)
        self.entry_publisher.bind("<KP_Enter>", self.search_files)

        # Row 3: Action Buttons & Limit
        actions_frame = ctk.CTkFrame(top_card, fg_color="transparent")
        actions_frame.grid(row=3, column=0, columnspan=5, padx=16, pady=(10, 14), sticky="ew")
        actions_frame.grid_columnconfigure(5, weight=1)

        # Limit
        lbl_limit = ctk.CTkLabel(actions_frame, text="Limit:", font=ctk.CTkFont(family="Segoe UI", size=12))
        lbl_limit.grid(row=0, column=0, padx=(0, 6), pady=2, sticky="w")

        self.entry_limit = ctk.CTkEntry(actions_frame, textvariable=self.limit, width=75, height=32)
        self.entry_limit.grid(row=0, column=1, padx=(0, 16), pady=2, sticky="w")
        self.entry_limit.bind("<Return>", self.search_files)
        self.entry_limit.bind("<KP_Enter>", self.search_files)

        # Action Buttons
        self.btn_search = ctk.CTkButton(
            actions_frame, text="⚡ Search Files (Enter)", width=170, height=34,
            fg_color="#1f6aa5", hover_color="#144870",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.search_files
        )
        self.btn_search.grid(row=0, column=2, padx=(0, 8), pady=2, sticky="w")

        btn_sort_pub = ctk.CTkButton(
            actions_frame, text="📅 By Published", width=125, height=34,
            fg_color="#2b2b2b", hover_color="#3a3a3a", border_width=1, border_color="#444444",
            command=self.by_published
        )
        btn_sort_pub.grid(row=0, column=3, padx=(0, 6), pady=2, sticky="w")

        btn_sort_publisher = ctk.CTkButton(
            actions_frame, text="🏢 By Publisher", width=125, height=34,
            fg_color="#2b2b2b", hover_color="#3a3a3a", border_width=1, border_color="#444444",
            command=self.by_publisher
        )
        btn_sort_publisher.grid(row=0, column=4, padx=(0, 6), pady=2, sticky="w")

        btn_sort_date = ctk.CTkButton(
            actions_frame, text="⏱️ By Date", width=105, height=34,
            fg_color="#2b2b2b", hover_color="#3a3a3a", border_width=1, border_color="#444444",
            command=self.by_modified_date
        )
        btn_sort_date.grid(row=0, column=5, padx=(0, 6), pady=2, sticky="w")

        btn_reset = ctk.CTkButton(
            actions_frame, text="🔄 Reset", width=80, height=34,
            fg_color="#3a3a3a", hover_color="#4a4a4a",
            command=self.reset
        )
        btn_reset.grid(row=0, column=6, padx=(0, 0), pady=2, sticky="e")

        # Global Key Bindings
        self.bind("<Return>", self.search_files)
        self.bind("<KP_Enter>", self.search_files)
        self.bind("<Escape>", self.stop_search)

    def _build_progress_and_filter_card(self, parent=None):
        parent = parent or self
        mid_card = ctk.CTkFrame(parent, corner_radius=10, fg_color="transparent")
        mid_card.grid(row=1, column=0, padx=(8, 0), pady=(0, 6), sticky="ew")
        mid_card.grid_columnconfigure(1, weight=1)

        # Progress bar
        self.progress = ctk.CTkProgressBar(mid_card, height=12, corner_radius=6, progress_color="#1f6aa5")
        self.progress.grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        # Live Filter Bar
        lbl_filter = ctk.CTkLabel(
            mid_card, text="🎯 Filter Results:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        lbl_filter.grid(row=1, column=0, padx=(0, 8), pady=0, sticky="w")

        self.filter_entry = ctk.CTkEntry(
            mid_card, textvariable=self.filter_var, height=32,
            placeholder_text="Type to filter displayed items instantly (supports '|', 'NOT', '*', '?')..."
        )
        self.filter_entry.grid(row=1, column=1, padx=(0, 0), pady=0, sticky="ew")
        self.filter_entry.bind("<KeyRelease>", self.filter_results)

    def _build_results_card(self, parent=None):
        parent = parent or self
        results_frame = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color="#333333")
        results_frame.grid(row=2, column=0, padx=(8, 0), pady=(0, 8), sticky="nsew")
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Modern Treeview Styling
        style = ttk.Style()
        style.configure(
            "Modern.Treeview",
            background="#1e1e1e",
            foreground="#e0e0e0",
            fieldbackground="#1e1e1e",
            rowheight=30,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure(
            "Modern.Treeview.Heading",
            background="#2a2a2a",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=6
        )
        style.map("Modern.Treeview", background=[("selected", "#1f6aa5")], foreground=[("selected", "#ffffff")])
        style.map("Modern.Treeview.Heading", background=[("active", "#383838")])

        cols = ("name", "publisher", "year", "date", "path")
        self.tree = ttk.Treeview(
            results_frame, columns=cols, show="headings",
            style="Modern.Treeview", selectmode="extended"
        )

        self.tree.heading("name", text="File Name", command=lambda: self._sort_tree("name"))
        self.tree.heading("publisher", text="Publisher", command=lambda: self._sort_tree("publisher"))
        self.tree.heading("year", text="Year", command=lambda: self._sort_tree("year"))
        self.tree.heading("date", text="Date Modified", command=lambda: self._sort_tree("date"))
        self.tree.heading("path", text="Directory Path", command=lambda: self._sort_tree("path"))

        self.tree.column("name", width=750, minwidth=300)
        self.tree.column("publisher", width=110, minwidth=80, anchor="center")
        self.tree.column("year", width=65, minwidth=50, anchor="center")
        self.tree.column("date", width=125, minwidth=100, anchor="center")
        self.tree.column("path", width=100, minwidth=80)

        # Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        vsb.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=6)
        hsb.grid(row=1, column=0, sticky="ew", padx=(6, 0), pady=(0, 6))

        # Bindings
        self.tree.bind("<Double-1>", self.open_file)
        self.tree.bind("<Return>", self._on_tree_return)
        self.tree.bind("<KP_Enter>", self._on_tree_return)
        self.tree.bind("<<TreeviewSelect>>", self._on_results_tree_select)
        self.tree.bind("<Configure>", self._on_tree_resize)
        self.tree.bind("<ButtonPress-1>", self._on_tree_press)
        self.tree.bind("<B1-Motion>", self._on_tree_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_release)

    def _on_tree_return(self, event=None):
        """Enter key on results table: opens or navigates into the selected item."""
        self.open_file()
        return "break"

    def _on_results_tree_select(self, event=None):
        """When a folder row in search results is clicked/selected, update directory input and expand left nav."""
        sel = self.tree.selection()
        if not sel or len(sel) != 1:
            return
        item_id = sel[0]
        if item_id in self.results_map:
            file_item = self.results_map[item_id]
            if file_item.is_directory and file_item.path.exists():
                folder_str = str(file_item.path)
                self.folder_path.set(folder_str)
                self.save_current_config()
                self.explorer_nav.select_path(folder_str, expand_target=True)

    def _on_tree_press(self, event):
        """Records initial mouse coordinates and manages selection for drag vs click."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            self._drag_pending = False
            self._drag_item_clicked = None
            return

        self._drag_pending = True
        self._drag_item_clicked = row_id
        current_selection = self.tree.selection()

        has_modifier = bool(event.state & (0x0001 | 0x0004))  # Shift (0x1) or Ctrl (0x4)
        if not has_modifier:
            if row_id in current_selection and len(current_selection) > 1:
                # Retain multi-selection so user can drag all selected items
                return "break"
            elif row_id not in current_selection:
                self.tree.selection_set(row_id)

    def _on_tree_motion(self, event):
        """Initiates native Windows OLE file drag when mouse moves beyond threshold."""
        if not self._drag_pending:
            return
        dx = abs(event.x - self._drag_start_x)
        dy = abs(event.y - self._drag_start_y)
        if dx > 5 or dy > 5:
            self._drag_pending = False
            sel = self.tree.selection()
            if not sel and self._drag_item_clicked:
                sel = (self._drag_item_clicked,)

            file_paths = [
                self.results_map[item_id].path
                for item_id in sel
                if item_id in self.results_map
            ]
            if file_paths:
                start_drag(file_paths)

    def _on_tree_release(self, event):
        """Handles mouse release, resolving single selection when multi-selection click wasn't dragged."""
        if self._drag_pending and self._drag_item_clicked:
            has_modifier = bool(event.state & (0x0001 | 0x0004))
            if not has_modifier:
                current_selection = self.tree.selection()
                if len(current_selection) > 1 and self._drag_item_clicked in current_selection:
                    self.tree.selection_set(self._drag_item_clicked)
        self._drag_pending = False
        self._drag_item_clicked = None

    def _on_tree_resize(self, event):
        total_w = event.width - 20
        if total_w > 300:
            name_w = int(total_w * 0.65)
            rem_w = total_w - name_w
            pub_w = max(70, int(rem_w * 0.28))
            year_w = max(50, int(rem_w * 0.16))
            date_w = max(90, int(rem_w * 0.28))
            path_w = max(60, rem_w - pub_w - year_w - date_w)

            self.tree.column("name", width=name_w)
            self.tree.column("publisher", width=pub_w)
            self.tree.column("year", width=year_w)
            self.tree.column("date", width=date_w)
            self.tree.column("path", width=path_w)

    def _build_footer_status(self, parent=None):
        parent = parent or self
        footer_frame = ctk.CTkFrame(parent, height=32, corner_radius=0, fg_color="transparent")
        footer_frame.grid(row=3, column=0, padx=(8, 0), pady=(0, 2), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            footer_frame, text="Ready", text_color="#999999",
            font=ctk.CTkFont(family="Segoe UI", size=12), anchor="w"
        )
        self.lbl_status.grid(row=0, column=0, sticky="w")

        self.lbl_count = ctk.CTkLabel(
            footer_frame, text="0 files found", text_color="#1f6aa5",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), anchor="e"
        )
        self.lbl_count.grid(row=0, column=1, sticky="e")

    def _setup_context_menu(self):
        """Initializes context menus for search results table and input entry fields."""
        # 1. Search Results Context Menu (Row Selection)
        self.context_menu = tk.Menu(
            self, tearoff=0,
            bg="#2b2b2b", fg="#ffffff",
            activebackground="#1f6aa5", activeforeground="#ffffff",
            font=("Segoe UI", 10), relief="flat", bd=1
        )

        # 2. Search Results Context Menu (Empty Area)
        self.empty_context_menu = tk.Menu(
            self, tearoff=0,
            bg="#2b2b2b", fg="#ffffff",
            activebackground="#1f6aa5", activeforeground="#ffffff",
            font=("Segoe UI", 10), relief="flat", bd=1
        )
        self.empty_context_menu.add_command(label="⚡ Search / Refresh", accelerator="Enter", command=self.search_files)
        self.empty_context_menu.add_separator()
        self.empty_context_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all_results)
        self.empty_context_menu.add_command(label="🔄 Reset / Clear", command=self.reset)

        self.tree.bind("<Button-3>", self._show_context_menu)

        # Keyboard shortcuts on treeview
        self.tree.bind("<Control-a>", lambda e: (self._select_all_results(), "break"))
        self.tree.bind("<Control-A>", lambda e: (self._select_all_results(), "break"))
        self.tree.bind("<Control-c>", lambda e: (self.copy_selected_items(), "break"))
        self.tree.bind("<Control-C>", lambda e: (self.copy_selected_items(), "break"))
        self.tree.bind("<F2>", lambda e: (self.rename_selected_item(), "break"))

        # Attach context menus to all entry input fields
        for entry_widget in (
            getattr(self, "entry_folder", None),
            getattr(self, "entry_patterns", None),
            getattr(self, "entry_extensions", None),
            getattr(self, "entry_sort", None),
            getattr(self, "entry_publisher", None),
            getattr(self, "entry_limit", None),
            getattr(self, "filter_entry", None),
        ):
            if entry_widget is not None:
                self._attach_entry_context_menu(entry_widget)

    def _attach_entry_context_menu(self, ctk_entry: ctk.CTkEntry):
        """Attaches a modern dark context menu (Cut, Copy, Paste, Select All, Clear) to a CTkEntry."""
        menu = tk.Menu(
            self, tearoff=0,
            bg="#2b2b2b", fg="#ffffff",
            activebackground="#1f6aa5", activeforeground="#ffffff",
            font=("Segoe UI", 10), relief="flat", bd=1
        )

        def show_menu(event):
            menu.delete(0, "end")
            inner = getattr(ctk_entry, "_entry", None)
            if inner is None:
                return

            has_selection = False
            try:
                has_selection = bool(inner.select_present())
            except Exception:
                pass

            has_text = bool(ctk_entry.get())

            clipboard_has_text = False
            try:
                clipboard_has_text = bool(self.clipboard_get())
            except Exception:
                pass

            menu.add_command(
                label="Cut", accelerator="Ctrl+X",
                state="normal" if has_selection else "disabled",
                command=lambda: inner.event_generate("<<Cut>>")
            )
            menu.add_command(
                label="Copy", accelerator="Ctrl+C",
                state="normal" if has_selection else "disabled",
                command=lambda: inner.event_generate("<<Copy>>")
            )
            menu.add_command(
                label="Paste", accelerator="Ctrl+V",
                state="normal" if clipboard_has_text else "disabled",
                command=lambda: inner.event_generate("<<Paste>>")
            )
            menu.add_separator()
            menu.add_command(
                label="Select All", accelerator="Ctrl+A",
                state="normal" if has_text else "disabled",
                command=lambda: (inner.select_range(0, "end"), inner.icursor("end"))
            )
            menu.add_command(
                label="Clear",
                state="normal" if has_text else "disabled",
                command=lambda: (ctk_entry.delete(0, "end"), inner.event_generate("<KeyRelease>"))
            )
            menu.post(event.x_root, event.y_root)

        ctk_entry.bind("<Button-3>", show_menu)
        if hasattr(ctk_entry, "_entry"):
            ctk_entry._entry.bind("<Button-3>", show_menu)

    def _show_context_menu(self, event):
        """Displays context menu for selected items or for the empty results area."""
        row_id = self.tree.identify_row(event.y)
        if row_id:
            current_selection = self.tree.selection()
            if row_id not in current_selection:
                self.tree.selection_set(row_id)
                current_selection = (row_id,)

            count = len(current_selection)
            self.context_menu.delete(0, "end")

            if count == 1:
                item_id = current_selection[0]
                is_dir = item_id in self.results_map and self.results_map[item_id].is_directory
                open_label = "📂 Open Folder" if is_dir else "▶ Open File"
                self.context_menu.add_command(label=open_label, accelerator="Double-Click / Enter", command=self.open_file)
                if not is_dir:
                    self.context_menu.add_command(label="🎨 Open File With...", command=self.open_file_with)
                self.context_menu.add_command(label="📁 Open in Explorer", command=self._ctx_open_explorer)
                self.context_menu.add_separator()
                self.context_menu.add_command(label="📄 Copy", accelerator="Ctrl+C", command=self.copy_selected_items)
                self.context_menu.add_command(label="✏️ Rename", accelerator="F2", command=self.rename_selected_item)
                self.context_menu.add_separator()
                self.context_menu.add_command(label="📋 Copy Full Path", command=self._ctx_copy_path)
                self.context_menu.add_command(label="📄 Copy Name", command=self._ctx_copy_name)
                self.context_menu.add_command(label="📂 Copy Folder Path", command=self._ctx_copy_folder)
            else:
                self.context_menu.add_command(label=f"▶ Open {count} Files", command=self.open_file)
                self.context_menu.add_command(label="🎨 Open File With...", command=self.open_file_with)
                self.context_menu.add_command(label="📁 Open Containing Folder in Explorer", command=self._ctx_open_explorer)
                self.context_menu.add_separator()
                self.context_menu.add_command(label=f"📄 Copy ({count} items)", accelerator="Ctrl+C", command=self.copy_selected_items)
                self.context_menu.add_separator()
                self.context_menu.add_command(label=f"📋 Copy Full Paths ({count} files)", command=self._ctx_copy_path)
                self.context_menu.add_command(label=f"📄 Copy File Names ({count} files)", command=self._ctx_copy_name)
                self.context_menu.add_command(label="📂 Copy Folder Paths", command=self._ctx_copy_folder)

            self.context_menu.add_separator()
            self.context_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all_results)
            self.context_menu.post(event.x_root, event.y_root)
        else:
            self.empty_context_menu.post(event.x_root, event.y_root)

    def _select_all_results(self, event=None):
        """Selects all items currently displayed in the results table."""
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children)

    def _init_paned_sash(self):
        try:
            self.paned_window.sashpos(0, 280)
        except Exception:
            pass

    def _on_nav_folder_selected(self, folder_path: str):
        """Called when a folder is selected in the left navigation pane."""
        if not folder_path or not os.path.exists(folder_path):
            return
        self.folder_path.set(folder_path)
        self.save_current_config()
        self._load_direct_folder_files(folder_path)

    def _load_direct_folder_files(self, folder_path: str):
        """Populates the search results table with direct files in folder_path (non-recursive)."""
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return

        self.reset()
        files = self.search_engine.list_direct_folder_files(folder)

        sort_by = [s.strip().lower() for s in self.sort_by.get().split(",") if s.strip()]
        if sort_by and files:
            files = self.search_engine.sort_results(files, sort_by, reverse=True)

        self.all_results = files
        self.display_results(files)
        self.lbl_status.configure(text=f"Showing direct files in '{folder.name}' (non-recursive)")
        self.lbl_count.configure(text=f"{len(files):,} files found")

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)
            self.save_current_config()
            self.explorer_nav.select_path(folder)
            self._load_direct_folder_files(folder)

    def reset(self):
        self.progress.set(0)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.filter_var.set("")
        self.all_results = []
        self.displayed_results = []
        self.results_map = {}
        self.lbl_status.configure(text="Ready")
        self.lbl_count.configure(text="0 files found")
        self.update_idletasks()

    def get_sort_key(self, file_data, sort_by):
        """Helper to generate sort keys, supporting both FileItem and legacy tuples."""
        if isinstance(file_data, FileItem):
            return file_data.get_sort_key(sort_by)
        # Legacy tuple: (file, year, publisher, modified)
        file, year, publisher, modified = file_data
        key = []
        for criteria in sort_by:
            if criteria == "published":
                key.append(year)
            elif criteria == "publisher":
                key.append(publisher)
            elif criteria == "modified":
                key.append(modified)
        return tuple(key)

    def by_modified_date(self):
        self.all_results = self.search_engine.sort_results(self.all_results, ['modified'], reverse=True)
        self.display_results(self.all_results)

    def by_publisher(self):
        self.all_results = self.search_engine.sort_results(self.all_results, ['publisher'], reverse=True)
        self.display_results(self.all_results)

    def by_published(self):
        self.all_results = self.search_engine.sort_results(self.all_results, ['published'], reverse=True)
        self.display_results(self.all_results)

    def stop_search(self, event=None):
        """Immediately halts an in-progress file search when Escape is pressed."""
        if self.is_searching:
            self.cancel_search = True
            self.lbl_status.configure(text="Stopping search... (Esc pressed)")
            self.update_idletasks()

    def search_files(self, event=None):
        if self.is_searching:
            return

        # Save config when searching
        self.save_current_config()

        self.reset()
        self.update()

        self.is_searching = True
        self.cancel_search = False
        self.btn_search.configure(
            text="⏹️ Stop Search (Esc)", fg_color="#c0392b", hover_color="#962d22", command=self.stop_search
        )

        folder = Path(self.folder_path.get().strip())
        if not folder.exists():
            self.is_searching = False
            self.btn_search.configure(
                text="⚡ Search Files (Enter)", fg_color="#1f6aa5", hover_color="#144870", command=self.search_files
            )
            messagebox.showwarning("Folder Not Found", f"The directory does not exist:\n{folder}")
            return

        try:
            self.lbl_status.configure(text=f"Scanning directory: {folder.name}...")
            self.update_idletasks()
            start_time = time.time()

            def on_match(scanned_count: int, total_count: int, item: FileItem):
                self.all_results.append(item)
                self.displayed_results.append(item)

                item_id = str(len(self.all_results))
                self.results_map[item_id] = item
                self.tree.insert(
                    "", "end", iid=item_id,
                    values=(item.name_display, item.publisher_display, item.year_display, item.date_modified_str, item.parent_str)
                )

                progress_ratio = scanned_count / total_count if total_count > 0 else 1.0
                self.progress.set(progress_ratio)
                self.lbl_count.configure(text=f"{len(self.all_results)} files found")
                self.lbl_status.configure(text=f"Scanned {scanned_count:,} of {total_count:,} files... (Esc to stop)")

                if scanned_count % 10 == 0:
                    self.update_idletasks()

            self.all_results = self.search_engine.search(
                folder=folder,
                pattern_query=self.search_patterns.get(),
                publisher_query=self.publisher_filters.get(),
                extensions_query=self.extensions.get(),
                limit=self.limit.get(),
                cancel_check=lambda: self.cancel_search,
                progress_callback=on_match,
            )

            elapsed = time.time() - start_time
            sort_by = [s.strip().lower() for s in self.sort_by.get().split(",") if s.strip()]

            if sort_by and self.all_results:
                self.all_results = self.search_engine.sort_results(self.all_results, sort_by, reverse=True)
                self.display_results(self.all_results)

            if self.cancel_search:
                self.lbl_status.configure(
                    text=f"Search stopped (Esc) in {elapsed:.2f}s. Found {len(self.all_results):,} matching files."
                )
            else:
                self.progress.set(1.0)
                self.lbl_status.configure(
                    text=f"Completed in {elapsed:.2f}s (Found {len(self.all_results):,} files in '{folder.name}')"
                )
            self.lbl_count.configure(text=f"{len(self.all_results):,} files found")

        finally:
            self.is_searching = False
            self.cancel_search = False
            self.btn_search.configure(
                text="⚡ Search Files (Enter)", fg_color="#1f6aa5", hover_color="#144870", command=self.search_files
            )

    def display_results(self, files: List[FileItem]):
        self.displayed_results = list(files)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results_map.clear()

        for idx, item in enumerate(files, start=1):
            item_id = str(idx)
            self.results_map[item_id] = item
            self.tree.insert(
                "", "end", iid=item_id,
                values=(item.name_display, item.publisher_display, item.year_display, item.date_modified_str, item.parent_str)
            )
        self.lbl_count.configure(text=f"{len(files):,} files found")

    def filter_results(self, event=None):
        self.save_current_config()
        query = self.filter_var.get().strip()
        if not query:
            self.display_results(self.all_results)
            return

        filter_rules, filter_excludes = QueryParser.parse(query)
        filtered_files = [
            item for item in self.all_results
            if QueryMatcher.matches(item.name, filter_rules, filter_excludes)
        ]
        self.display_results(filtered_files)

    def _sort_tree(self, col: str):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        if col == "name":
            self.displayed_results.sort(key=lambda x: x.name.lower(), reverse=self.sort_reverse)
        elif col == "publisher":
            self.displayed_results.sort(key=lambda x: x.publisher.lower(), reverse=self.sort_reverse)
        elif col == "year":
            self.displayed_results.sort(key=lambda x: x.year, reverse=self.sort_reverse)
        elif col == "date":
            self.displayed_results.sort(key=lambda x: x.modified, reverse=self.sort_reverse)
        elif col == "path":
            self.displayed_results.sort(key=lambda x: x.parent_str.lower(), reverse=self.sort_reverse)

        self.display_results(self.displayed_results)

    def open_file(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        for item_id in sel:
            if item_id in self.results_map:
                file_item = self.results_map[item_id]
                if file_item.is_directory and file_item.path.exists():
                    folder_str = str(file_item.path)
                    self._on_nav_folder_selected(folder_str)
                    self.explorer_nav.select_path(folder_str, expand_target=True)
                    return
                elif file_item.path.exists():
                    try:
                        if sys.platform == "win32":
                            os.startfile(str(file_item.path))
                        else:
                            webbrowser.open(file_item.path.as_uri())
                    except Exception as e:
                        messagebox.showerror("Open File Error", f"Could not open file:\n{e}")
                else:
                    messagebox.showerror("File Not Found", f"File does not exist:\n{file_item.path}")

    def open_file_with(self, event=None):
        """Opens the native Windows 'Open with...' dialog for the selected file."""
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        if item_id in self.results_map:
            file_item = self.results_map[item_id]
            if file_item.path.exists():
                try:
                    if sys.platform == "win32":
                        resolved_path = normalize_drag_path(str(file_item.path))
                        try:
                            import ctypes
                            from ctypes import Structure, POINTER, byref, wintypes, HRESULT

                            class OPENASINFO(Structure):
                                _fields_ = [
                                    ("pcszFile", wintypes.LPCWSTR),
                                    ("pcszClass", wintypes.LPCWSTR),
                                    ("oaifInFlags", wintypes.DWORD),
                                ]

                            shell32 = ctypes.windll.shell32
                            shell32.SHOpenWithDialog.restype = HRESULT
                            shell32.SHOpenWithDialog.argtypes = [wintypes.HWND, POINTER(OPENASINFO)]
                            info = OPENASINFO(resolved_path, None, 0x00000004 | 0x00000001)  # OAIF_EXEC | OAIF_ALLOW_REGISTRATION
                            hr = shell32.SHOpenWithDialog(0, byref(info))
                            if hr != 0:
                                subprocess.Popen(["rundll32.exe", "shell32.dll,OpenAs_RunDLL", resolved_path])
                        except Exception:
                            subprocess.Popen(["rundll32.exe", "shell32.dll,OpenAs_RunDLL", resolved_path])
                    else:
                        webbrowser.open(file_item.path.as_uri())
                except Exception as e:
                    messagebox.showerror("Open With Error", f"Could not open 'Open with' dialog:\n{e}")
            else:
                messagebox.showerror("File Not Found", f"File does not exist:\n{file_item.path}")

    def _ctx_open_explorer(self):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        if item_id in self.results_map:
            file_item = self.results_map[item_id]
            if file_item.path.exists():
                try:
                    if sys.platform == "win32":
                        norm = os.path.normpath(str(file_item.path))
                        if file_item.is_directory:
                            subprocess.run(["explorer", norm], check=False)
                        else:
                            subprocess.run(["explorer", "/select,", norm], check=False)
                    else:
                        webbrowser.open(file_item.path.parent.as_uri())
                except Exception as e:
                    messagebox.showerror("Explorer Error", f"Could not open explorer:\n{e}")

    def _ctx_copy_path(self):
        sel = self.tree.selection()
        paths = [str(self.results_map[iid].path) for iid in sel if iid in self.results_map]
        if paths:
            self.clipboard_clear()
            self.clipboard_append("\n".join(paths))

    def _ctx_copy_name(self):
        sel = self.tree.selection()
        names = [self.results_map[iid].name for iid in sel if iid in self.results_map]
        if names:
            self.clipboard_clear()
            self.clipboard_append("\n".join(names))

    def _ctx_copy_folder(self):
        sel = self.tree.selection()
        folders = [str(self.results_map[iid].path.parent) for iid in sel if iid in self.results_map]
        if folders:
            unique_folders = list(dict.fromkeys(folders))
            self.clipboard_clear()
            self.clipboard_append("\n".join(unique_folders))

    def copy_selected_items(self, event=None):
        """Copies selected files and/or folders to the Windows clipboard (CF_HDROP + CF_UNICODETEXT)."""
        sel = self.tree.selection()
        if not sel:
            return "break"
        paths = [self.results_map[iid].path for iid in sel if iid in self.results_map]
        if not paths:
            return "break"

        success = copy_files_to_clipboard(paths)
        if not success:
            text = "\n".join(str(p) for p in paths)
            self.clipboard_clear()
            self.clipboard_append(text)

        count = len(paths)
        label = "item" if count == 1 else "items"
        self.lbl_status.configure(text=f"Copied {count} {label} to clipboard (Ctrl+V to paste in Explorer)")
        return "break"

    def rename_selected_item(self, event=None):
        """Opens a modal dialog to rename the selected file or folder, updating the UI and left tree."""
        sel = self.tree.selection()
        if not sel:
            return "break"
        item_id = sel[0]
        if item_id not in self.results_map:
            return "break"

        file_item = self.results_map[item_id]
        old_path = file_item.path
        if not old_path.exists():
            messagebox.showerror("Rename Error", f"The item no longer exists:\n{old_path}")
            return "break"

        old_name = old_path.name
        is_dir = file_item.is_directory

        # Create modern rename modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Rename {'Folder' if is_dir else 'File'}")
        dialog.geometry("460x170")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog over main window
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 460) // 2
        y = self.winfo_y() + (self.winfo_height() - 170) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        lbl = ctk.CTkLabel(
            dialog,
            text=f"Enter new name for {'folder' if is_dir else 'file'}:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        lbl.pack(padx=20, pady=(16, 8), anchor="w")

        name_var = tk.StringVar(value=old_name)
        entry = ctk.CTkEntry(dialog, textvariable=name_var, width=420, height=34)
        entry.pack(padx=20, pady=(0, 14))
        entry.focus_set()

        # Pre-select filename excluding extension (for files)
        if not is_dir and "." in old_name:
            ext_idx = old_name.rfind(".")
            if ext_idx > 0:
                entry._entry.select_range(0, ext_idx)
                entry._entry.icursor(ext_idx)
        else:
            entry._entry.select_range(0, "end")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(0, 14), fill="x")

        def do_rename():
            new_name = name_var.get().strip()
            if not new_name or new_name == old_name:
                dialog.destroy()
                return

            # Check invalid characters
            invalid_chars = r'\/:*?"<>|'
            if any(c in new_name for c in invalid_chars):
                messagebox.showerror(
                    "Invalid Name",
                    f"A name cannot contain any of the following characters:\n{invalid_chars}",
                    parent=dialog
                )
                return

            new_path = old_path.with_name(new_name)
            if new_path.exists():
                messagebox.showerror(
                    "Already Exists",
                    f"An item with the name '{new_name}' already exists in this folder.",
                    parent=dialog
                )
                return

            try:
                os.rename(old_path, new_path)
            except Exception as e:
                messagebox.showerror("Rename Error", f"Could not rename:\n{e}", parent=dialog)
                return

            # Update FileItem model
            file_item.path = new_path
            if is_dir:
                file_item.publisher = "Folder"
            else:
                file_item.publisher = self.search_engine.metadata_extractor.extract_publisher(new_name)
                file_item.year = self.search_engine.metadata_extractor.extract_year(new_name)

            # Update Treeview row
            self.tree.item(
                item_id,
                values=(file_item.name_display, file_item.publisher_display, file_item.year_display, file_item.date_modified_str, file_item.parent_str)
            )

            # If the renamed item is a folder, update directory path and refresh left tree
            if is_dir:
                if os.path.normpath(self.folder_path.get()).lower() == os.path.normpath(str(old_path)).lower():
                    self.folder_path.set(str(new_path))
                    self.save_current_config()
                self.explorer_nav.refresh()

            self.lbl_status.configure(text=f"Renamed '{old_name}' to '{new_name}'")
            dialog.destroy()

        btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancel", width=90, height=32,
            fg_color="#3a3a3a", hover_color="#4a4a4a",
            command=dialog.destroy
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_ok = ctk.CTkButton(
            btn_frame, text="Rename", width=100, height=32,
            fg_color="#1f6aa5", hover_color="#144870",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=do_rename
        )
        btn_ok.pack(side="right")

        dialog.bind("<Return>", lambda e: do_rename())
        dialog.bind("<KP_Enter>", lambda e: do_rename())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        return "break"


if __name__ == "__main__":
    app = FileSearchApp()
    app.mainloop()
