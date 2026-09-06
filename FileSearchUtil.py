"""FileSearchUtil - Modern 2026 Desktop File Search & Sort Utility.

Supports:
- '|' as OR (e.g. 'ai agent|agents')
- 'NOT' as exclusion (e.g. 'ai agent NOT agents')
- '*' (zero or more characters)
- '?' (single character)
- '-' or 'NOT' for global exclusions (e.g. '-draft', 'NOT old')
- Comma-separated multiple search rules
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Set, Tuple
import webbrowser

import customtkinter as ctk


# Configure CustomTkinter Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class SearchRule:
    """Represents a search rule with an include pattern (supporting '|') and optional exclude patterns ('NOT', 'AND')."""

    def __init__(
        self,
        include_regex: Optional[re.Pattern],
        exclude_regex: Optional[re.Pattern | List[re.Pattern]] = None,
    ):
        self.include_regex = include_regex
        if exclude_regex is None:
            self.exclude_regexes: List[re.Pattern] = []
        elif isinstance(exclude_regex, list):
            self.exclude_regexes = exclude_regex
        else:
            self.exclude_regexes = [exclude_regex]

    @property
    def exclude_regex(self) -> Optional[re.Pattern]:
        """Backward-compatibility property returning the first exclude regex if present."""
        return self.exclude_regexes[0] if self.exclude_regexes else None

    def matches(self, text: str) -> bool:
        if self.include_regex and not self.include_regex.search(text):
            return False
        for exc in self.exclude_regexes:
            if exc.search(text):
                return False
        return True


class FileSearchApp(ctk.CTk):
    """Modern 2026 Desktop File Search & Sort Application."""

    def __init__(self):
        super().__init__()

        self.title("FileSearch Pro — Fast Search & Sort")
        self.geometry("1200x840")
        self.minsize(980, 640)

        # Reactive State Variables
        self.folder_path = tk.StringVar(value="D:/ABogue/Books/")
        self.search_patterns = tk.StringVar(value="ai * pattern")
        self.extensions = tk.StringVar(value="pdf, epub, txt")
        self.sort_by = tk.StringVar(value="published, publisher, modified")
        self.publisher_filters = tk.StringVar()
        self.limit = tk.IntVar(value=100)
        self.filter_var = tk.StringVar()

        # Data Storage
        self.all_results: List[Tuple[Path, int, str, float]] = []
        self.displayed_results: List[Tuple[Path, int, str, float]] = []
        self.results_map: Dict[str, Tuple[Path, int, str, float]] = {}
        self.sort_column = ""
        self.sort_reverse = False
        self.is_searching = False
        self.cancel_search = False

        self._create_widgets()
        self._setup_context_menu()

    def _create_widgets(self):
        # Configure root grid
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Top Card: Folder Selection & Search Inputs
        self._build_controls_card()

        # 2. Progress & Live Filter Bar
        self._build_progress_and_filter_card()

        # 3. Center Card: Modern Results Table
        self._build_results_card()

        # 4. Bottom Footer: Status Bar
        self._build_footer_status()

    def _build_controls_card(self):
        top_card = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color="#333333")
        top_card.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
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

    def _build_progress_and_filter_card(self):
        mid_card = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        mid_card.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="ew")
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

    def _build_results_card(self):
        results_frame = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color="#333333")
        results_frame.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="nsew")
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Modern Treeview Styling
        style = ttk.Style()
        style.theme_use("clam")
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
        self.tree.bind("<Configure>", self._on_tree_resize)

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

    def _build_footer_status(self):
        footer_frame = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color="transparent")
        footer_frame.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="ew")
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
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="#ffffff", activebackground="#1f6aa5")
        self.context_menu.add_command(label="Open File", command=self.open_file)
        self.context_menu.add_command(label="Open Containing Folder in Explorer", command=self._ctx_open_explorer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Full Path", command=self._ctx_copy_path)
        self.context_menu.add_command(label="Copy File Name", command=self._ctx_copy_name)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            if row_id not in self.tree.selection():
                self.tree.selection_set(row_id)
            self.context_menu.post(event.x_root, event.y_root)

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)

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

    def by_modified_date(self):
        sort_by = ['modified']
        self.all_results.sort(key=lambda x: self.get_sort_key(x, sort_by), reverse=True)
        self.display_results(self.all_results)

    def by_publisher(self):
        sort_by = ['publisher']
        self.all_results.sort(key=lambda x: self.get_sort_key(x, sort_by), reverse=True)
        self.display_results(self.all_results)

    def by_published(self):
        sort_by = ['published']
        self.all_results.sort(key=lambda x: self.get_sort_key(x, sort_by), reverse=True)
        self.display_results(self.all_results)

    @staticmethod
    def term_to_regex(term_str: str) -> re.Pattern:
        """
        Converts a pattern term with '*', '?', and '|' into a compiled regex.
        Supports:
          - '*' : matches zero or more characters (e.g. 'java * pattern')
          - '?' : matches any single character (e.g. 'python?')
          - '|' : OR operator (e.g. 'ai agent|agents' matches 'ai agent' or 'agents')
          - spaces : matches common filename word separators (space, dot, dash, underscore, plus)
        """
        raw = term_str.strip()
        if not raw:
            return re.compile(r".*", re.IGNORECASE)

        # Normalize whitespace around wildcards so 'java * pattern' becomes 'java*pattern'
        raw = re.sub(r'\s*\*\s*', '*', raw)
        raw = re.sub(r'\s*\?\s*', '?', raw)

        # Split by '|' to support OR options within the term
        branches = raw.split('|')
        branch_regexes = []

        for branch in branches:
            branch = branch.strip()
            if not branch:
                continue

            tokens = re.split(r'([\*\?])', branch)
            branch_parts = []
            for token in tokens:
                if token == '*':
                    branch_parts.append(r'.*')
                elif token == '?':
                    branch_parts.append(r'.')
                else:
                    escaped = re.escape(token)
                    # Allow spaces in the pattern to match common word separators
                    escaped = escaped.replace(r'\ ', r'[\s\._\-\+]+').replace(' ', r'[\s\._\-\+]+')
                    branch_parts.append(escaped)

            branch_regexes.append("".join(branch_parts))

        if len(branch_regexes) > 1:
            full_regex = r"(?:" + r"|".join(branch_regexes) + r")"
        else:
            full_regex = branch_regexes[0] if branch_regexes else r".*"

        try:
            return re.compile(full_regex, re.IGNORECASE)
        except re.error:
            return re.compile(re.escape(raw), re.IGNORECASE)

    @classmethod
    def parse_exclude_terms(cls, raw_exclude_str: str) -> List[re.Pattern]:
        """
        Parses an exclusion substring containing one or more terms separated by
        'and', 'not', 'and not', '&', or '-' prefixes.
        Examples:
          - 'apress and addison' -> [regex('apress'), regex('addison')]
          - 'apress NOT addison' -> [regex('apress'), regex('addison')]
          - 'apress and not addison' -> [regex('apress'), regex('addison')]
          - 'apress & addison' -> [regex('apress'), regex('addison')]
        """
        if not raw_exclude_str or not raw_exclude_str.strip():
            return []

        text = raw_exclude_str.strip()
        # Normalize ' -' to a split delimiter if someone writes 'apress -addison'
        text = re.sub(r'\s+-\s*', '|SPLIT|', text)
        # Normalize ' and not ', ' & not ', ' not ', ' and ', ' & '
        text = re.sub(r'\s+(?:and\s+not|&\s*not|and|not|&)\s+', '|SPLIT|', text, flags=re.IGNORECASE)

        parts = [p.strip() for p in text.split('|SPLIT|') if p.strip()]

        regexes: List[re.Pattern] = []
        for part in parts:
            clean = re.sub(r'^(?:NOT\s+|-)', '', part, flags=re.IGNORECASE).strip()
            if clean:
                regexes.append(cls.term_to_regex(clean))

        return regexes

    @classmethod
    def parse_search_query(cls, query_str: str) -> Tuple[List[SearchRule], List[re.Pattern]]:
        """
        Parses comma-separated query items.
        Supports:
          - 'patternA | patternB' (OR)
          - 'patternA NOT patternB and patternC' (Include patternA, exclude patternB, patternC)
          - '-pattern' or 'NOT patternA and patternB' (Global exclusions)
        """
        raw_clauses = [c.strip() for c in query_str.split(",") if c.strip()]
        rules: List[SearchRule] = []
        global_excludes: List[re.Pattern] = []

        for clause in raw_clauses:
            # Standalone global exclude: "-draft" or "NOT draft and old"
            if clause.startswith("-"):
                clean = clause[1:].strip()
                if clean:
                    global_excludes.extend(cls.parse_exclude_terms(clean))
                continue

            if re.match(r'^NOT\s+', clause, re.IGNORECASE):
                clean = re.sub(r'^NOT\s+', '', clause, flags=re.IGNORECASE).strip()
                if clean:
                    global_excludes.extend(cls.parse_exclude_terms(clean))
                continue

            # Check for inline ' NOT ' (e.g. 'ai * pattern NOT apress and addison')
            not_parts = re.split(r'\s+NOT\s+', clause, maxsplit=1, flags=re.IGNORECASE)
            if len(not_parts) == 2:
                inc_str, exc_str = not_parts[0].strip(), not_parts[1].strip()
                inc_rx = cls.term_to_regex(inc_str) if inc_str else None
                exc_rxs = cls.parse_exclude_terms(exc_str) if exc_str else []
                rules.append(SearchRule(inc_rx, exc_rxs))
            else:
                inc_rx = cls.term_to_regex(clause)
                rules.append(SearchRule(inc_rx, None))

        return rules, global_excludes

    @classmethod
    def parse_extensions(cls, exts_str: str) -> Tuple[Set[str], Set[str]]:
        """
        Parses comma-separated extension filter string into include and exclude sets.
        Supports:
          - Include: 'pdf', '.epub', '*.txt'
          - Exclude: '-java', '-.class', '-*.tmp', 'NOT java', 'not log'
        Returns:
          (include_exts, exclude_exts) as sets of lowercase extension strings without leading dot.
        """
        include_exts: Set[str] = set()
        exclude_exts: Set[str] = set()

        if not exts_str or not exts_str.strip():
            return include_exts, exclude_exts

        raw_items = [item.strip() for item in exts_str.split(",") if item.strip()]
        for item in raw_items:
            is_exclude = False
            clean = item
            if clean.startswith("-"):
                is_exclude = True
                clean = clean[1:].strip()
            elif re.match(r'^NOT\s+', clean, re.IGNORECASE):
                is_exclude = True
                clean = re.sub(r'^NOT\s+', '', clean, flags=re.IGNORECASE).strip()

            clean = clean.lstrip("*").lstrip(".").strip().lower()
            if not clean:
                continue

            if is_exclude:
                exclude_exts.add(clean)
            else:
                include_exts.add(clean)

        return include_exts, exclude_exts

    @staticmethod
    def matches_extension(file_ext: str, include_exts: Set[str], exclude_exts: Set[str]) -> bool:
        """
        Determines if file_ext (without leading dot, lowercase) satisfies extension filtering rules.
        - If file_ext is in exclude_exts -> False
        - If include_exts is empty -> True (matches all non-excluded)
        - If include_exts is not empty -> True only if file_ext in include_exts
        """
        norm_ext = file_ext.lstrip(".").lower()
        if exclude_exts and norm_ext in exclude_exts:
            return False
        if include_exts:
            return norm_ext in include_exts
        return True

    @staticmethod
    def collect_files_sorted_by_mtime(folder: Path, reverse: bool = True) -> List[Tuple[Path, float]]:
        """
        Scans all files recursively in folder and sorts them by last modified date.
        By default (reverse=True), orders files from newest to oldest.
        """
        file_entries: List[Tuple[Path, float]] = []
        for f in folder.glob("**/*"):
            try:
                if f.is_file():
                    file_entries.append((f, f.stat().st_mtime))
            except (OSError, PermissionError):
                continue

        file_entries.sort(key=lambda x: x[1], reverse=reverse)
        return file_entries

    @staticmethod
    def matches_query(text: str, rules: List[SearchRule], global_excludes: List[re.Pattern]) -> bool:
        """Evaluates whether text satisfies the parsed rules and global exclusions."""
        for ex in global_excludes:
            if ex.search(text):
                return False

        if not rules:
            return True

        return any(rule.matches(text) for rule in rules)

    def stop_search(self, event=None):
        """Immediately halts an in-progress file search when Escape is pressed."""
        if self.is_searching:
            self.cancel_search = True
            self.lbl_status.configure(text="Stopping search... (Esc pressed)")
            self.update_idletasks()

    def search_files(self, event=None):
        if self.is_searching:
            return

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
            pattern_rules, pattern_excludes = self.parse_search_query(self.search_patterns.get())
            pub_rules, pub_excludes = self.parse_search_query(self.publisher_filters.get())
            include_exts, exclude_exts = self.parse_extensions(self.extensions.get())

            sort_by = [s.strip().lower() for s in self.sort_by.get().split(",") if s.strip()]
            limit_val = self.limit.get()

            self.lbl_status.configure(text=f"Scanning directory: {folder}...")
            self.update_idletasks()

            file_entries = self.collect_files_sorted_by_mtime(folder, reverse=True)
            total_files = len(file_entries)
            start_time = time.time()
            stopped_early = False

            for idx, (file, mtime) in enumerate(file_entries):
                if self.cancel_search:
                    stopped_early = True
                    break

                file_ext = file.suffix.lstrip(".").lower()
                if not self.matches_extension(file_ext, include_exts, exclude_exts):
                    continue

                filename = file.name
                if not self.matches_query(filename, pattern_rules, pattern_excludes):
                    continue

                publisher = self.extract_publisher(filename)
                if not self.matches_query(publisher, pub_rules, pub_excludes):
                    continue

                year = self.extract_year(filename)
                item = (file, year, publisher, mtime)

                self.all_results.append(item)
                self.displayed_results.append(item)

                # Insert row progressively into modern treeview
                item_id = str(len(self.all_results))
                self.results_map[item_id] = item
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                self.tree.insert(
                    "", "end", iid=item_id,
                    values=(file.name, publisher.title(), year or "-", date_str, str(file.parent))
                )

                # Update progress bar
                progress_ratio = (idx + 1) / total_files if total_files > 0 else 1.0
                self.progress.set(progress_ratio)
                self.lbl_count.configure(text=f"{len(self.all_results)} files found")
                self.lbl_status.configure(text=f"Scanned {idx + 1:,} of {total_files:,} files... (Esc to stop)")

                if idx % 10 == 0:
                    self.update_idletasks()

                if limit_val > 0 and len(self.all_results) >= limit_val:
                    break

            elapsed = time.time() - start_time

            if sort_by and self.all_results:
                self.all_results.sort(key=lambda x: self.get_sort_key(x, sort_by), reverse=True)
                self.display_results(self.all_results)

            if stopped_early:
                self.lbl_status.configure(
                    text=f"Search stopped (Esc) in {elapsed:.2f}s. Found {len(self.all_results):,} matching files."
                )
            else:
                self.progress.set(1.0)
                self.lbl_status.configure(
                    text=f"Completed in {elapsed:.2f}s (Scanned {total_files:,} files in '{folder.name}')"
                )
            self.lbl_count.configure(text=f"{len(self.all_results):,} files found")

        finally:
            self.is_searching = False
            self.cancel_search = False
            self.btn_search.configure(
                text="⚡ Search Files (Enter)", fg_color="#1f6aa5", hover_color="#144870", command=self.search_files
            )

    def extract_year(self, filename: str) -> int:
        match = re.search(r'\b(19\d{2}|20\d{2})\b', filename)
        return int(match.group()) if match else 0

    def extract_publisher(self, filename: str) -> str:
        match = re.match(r'([^\-]+)-', filename)
        return match.group(1).strip().lower() if match else "unknown"

    def get_sort_key(self, file_data, sort_by):
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

    def display_results(self, files):
        self.displayed_results = list(files)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results_map.clear()

        for idx, (file, year, publisher, mtime) in enumerate(files, start=1):
            item_id = str(idx)
            self.results_map[item_id] = (file, year, publisher, mtime)
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            self.tree.insert(
                "", "end", iid=item_id,
                values=(file.name, publisher.title(), year or "-", date_str, str(file.parent))
            )
        self.lbl_count.configure(text=f"{len(files):,} files found")

    def filter_results(self, event=None):
        query = self.filter_var.get().strip()
        if not query:
            self.display_results(self.all_results)
            return

        filter_rules, filter_excludes = self.parse_search_query(query)
        filtered_files = [
            f for f in self.all_results
            if self.matches_query(f[0].name, filter_rules, filter_excludes)
        ]
        self.display_results(filtered_files)

    def _sort_tree(self, col: str):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        if col == "name":
            self.displayed_results.sort(key=lambda x: x[0].name.lower(), reverse=self.sort_reverse)
        elif col == "publisher":
            self.displayed_results.sort(key=lambda x: x[2].lower(), reverse=self.sort_reverse)
        elif col == "year":
            self.displayed_results.sort(key=lambda x: x[1], reverse=self.sort_reverse)
        elif col == "date":
            self.displayed_results.sort(key=lambda x: x[3], reverse=self.sort_reverse)
        elif col == "path":
            self.displayed_results.sort(key=lambda x: str(x[0].parent).lower(), reverse=self.sort_reverse)

        self.display_results(self.displayed_results)

    def open_file(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        if item_id in self.results_map:
            file_path = self.results_map[item_id][0]
            if file_path.exists():
                try:
                    if sys.platform == "win32":
                        os.startfile(str(file_path))
                    else:
                        webbrowser.open(file_path.as_uri())
                except Exception as e:
                    messagebox.showerror("Open File Error", f"Could not open file:\n{e}")
            else:
                messagebox.showerror("File Not Found", f"File does not exist:\n{file_path}")

    def _ctx_open_explorer(self):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        if item_id in self.results_map:
            file_path = self.results_map[item_id][0]
            if file_path.exists():
                try:
                    if sys.platform == "win32":
                        subprocess.run(["explorer", "/select,", os.path.normpath(str(file_path))], check=False)
                    else:
                        webbrowser.open(file_path.parent.as_uri())
                except Exception as e:
                    messagebox.showerror("Explorer Error", f"Could not open explorer:\n{e}")

    def _ctx_copy_path(self):
        sel = self.tree.selection()
        paths = [str(self.results_map[iid][0]) for iid in sel if iid in self.results_map]
        if paths:
            self.clipboard_clear()
            self.clipboard_append("\n".join(paths))

    def _ctx_copy_name(self):
        sel = self.tree.selection()
        names = [self.results_map[iid][0].name for iid in sel if iid in self.results_map]
        if names:
            self.clipboard_clear()
            self.clipboard_append("\n".join(names))


if __name__ == "__main__":
    app = FileSearchApp()
    app.mainloop()