"""File Explorer Navigation Panel component for FileSearch Pro."""

from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Tuple

import customtkinter as ctk

from folder_tree_provider import get_system_drives, list_subdirectories


class FileExplorerNav(ctk.CTkFrame):
    """Left navigation panel displaying drives and expandable folder tree hierarchy."""

    DUMMY_NODE_TEXT = "__dummy__"

    def __init__(
        self,
        master,
        on_select_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(master, corner_radius=10, border_width=1, border_color="#333333", **kwargs)
        self.on_select_callback = on_select_callback

        # Mapping of tree item_id -> absolute folder path
        self.node_path_map: Dict[str, str] = {}
        # Reverse mapping for fast path lookup: normalized_path.lower() -> item_id
        self.path_node_map: Dict[str, str] = {}

        self._suppress_select_event = False

        self._create_widgets()
        self._populate_drives()

    def _create_widgets(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header Frame
        header_frame = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header_frame.grid_columnconfigure(0, weight=1)

        lbl_header = ctk.CTkLabel(
            header_frame,
            text="📁 Explorer",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            anchor="w",
        )
        lbl_header.grid(row=0, column=0, sticky="w")

        btn_refresh = ctk.CTkButton(
            header_frame,
            text="↻",
            width=24,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2b2b2b",
            hover_color="#383838",
            command=self.refresh,
        )
        btn_refresh.grid(row=0, column=1, sticky="e")

        # Treeview Container Frame
        tree_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        tree_container.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Style Treeview
        style = ttk.Style()
        style.configure(
            "Explorer.Treeview",
            background="#1e1e1e",
            foreground="#e0e0e0",
            fieldbackground="#1e1e1e",
            rowheight=24,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.map(
            "Explorer.Treeview",
            background=[("selected", "#1f6aa5")],
            foreground=[("selected", "#ffffff")],
        )

        self.tree = ttk.Treeview(
            tree_container,
            show="tree",
            style="Explorer.Treeview",
            selectmode="browse",
        )

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Bindings
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _populate_drives(self):
        """Discovers and populates system drives as root nodes."""
        self.tree.delete(*self.tree.get_children())
        self.node_path_map.clear()
        self.path_node_map.clear()

        drives = get_system_drives()
        for root_path, display_name in drives:
            norm_path = os.path.normpath(root_path)
            node_id = self.tree.insert("", "end", text=f"🖴  {display_name}", open=False)
            self.node_path_map[node_id] = norm_path
            self.path_node_map[norm_path.lower()] = node_id

            # Add dummy node so the expand arrow appears
            self.tree.insert(node_id, "end", text=self.DUMMY_NODE_TEXT)

    def _on_tree_open(self, event):
        """Lazily populates child subdirectories when a node is expanded."""
        node_id = self.tree.focus()
        if not node_id:
            return

        children = self.tree.get_children(node_id)
        if len(children) == 1 and self.tree.item(children[0], "text") == self.DUMMY_NODE_TEXT:
            # Remove dummy node
            self.tree.delete(children[0])

            folder_path = self.node_path_map.get(node_id)
            if not folder_path or not os.path.exists(folder_path):
                return

            subdirs = list_subdirectories(folder_path)
            for name, full_path, has_kids in subdirs:
                norm_p = os.path.normpath(full_path)
                child_id = self.tree.insert(node_id, "end", text=f"📁  {name}", open=False)
                self.node_path_map[child_id] = norm_p
                self.path_node_map[norm_p.lower()] = child_id

                if has_kids:
                    self.tree.insert(child_id, "end", text=self.DUMMY_NODE_TEXT)

    def _on_tree_select(self, event):
        """Triggers callback when user clicks a folder node."""
        if self._suppress_select_event:
            return

        selected = self.tree.selection()
        if not selected:
            return

        node_id = selected[0]
        folder_path = self.node_path_map.get(node_id)
        if folder_path and self.on_select_callback:
            self.on_select_callback(folder_path)

    def select_path(self, target_path: str):
        """Expands and highlights a specific directory path in the tree."""
        if not target_path or not os.path.exists(target_path):
            return

        norm_target = os.path.normpath(target_path)
        parts = Path(norm_target).parts
        if not parts:
            return

        # Start with drive root
        drive_root = parts[0]
        curr_path = os.path.normpath(drive_root)
        node_id = self.path_node_map.get(curr_path.lower())

        if not node_id:
            return

        self._suppress_select_event = True
        try:
            # Step down through each directory segment, expanding lazily as needed
            for part in parts[1:]:
                # Expand current node
                self.tree.item(node_id, open=True)
                children = self.tree.get_children(node_id)
                if len(children) == 1 and self.tree.item(children[0], "text") == self.DUMMY_NODE_TEXT:
                    self.tree.delete(children[0])
                    subdirs = list_subdirectories(curr_path)
                    for name, full_path, has_kids in subdirs:
                        norm_p = os.path.normpath(full_path)
                        child_id = self.tree.insert(node_id, "end", text=f"📁  {name}", open=False)
                        self.node_path_map[child_id] = norm_p
                        self.path_node_map[norm_p.lower()] = child_id
                        if has_kids:
                            self.tree.insert(child_id, "end", text=self.DUMMY_NODE_TEXT)

                curr_path = os.path.normpath(os.path.join(curr_path, part))
                node_id = self.path_node_map.get(curr_path.lower())
                if not node_id:
                    break

            if node_id:
                self.tree.selection_set(node_id)
                self.tree.focus(node_id)
                self.tree.see(node_id)
        finally:
            self._suppress_select_event = False

    def refresh(self):
        """Refreshes the drive and directory tree, maintaining the current path if possible."""
        current_selection = None
        sel = self.tree.selection()
        if sel:
            current_selection = self.node_path_map.get(sel[0])

        self._populate_drives()

        if current_selection and os.path.exists(current_selection):
            self.select_path(current_selection)
