from __future__ import annotations

import re
from typing import Optional, Set


class ExtensionFilter:
    """Responsible for parsing and matching file extension criteria with inclusion and exclusion support."""

    def __init__(self, include_exts: Optional[Set[str]] = None, exclude_exts: Optional[Set[str]] = None):
        self.include_exts: Set[str] = include_exts or set()
        self.exclude_exts: Set[str] = exclude_exts or set()

    @classmethod
    def from_string(cls, exts_str: str) -> ExtensionFilter:
        """
        Parses comma-separated extension filter string into include and exclude sets.
        Supports:
          - Include: 'pdf', '.epub', '*.txt'
          - Exclude: '-java', '-.class', '-*.tmp', 'NOT java', 'not log'
        """
        include_exts: Set[str] = set()
        exclude_exts: Set[str] = set()

        if not exts_str or not exts_str.strip():
            return cls(include_exts, exclude_exts)

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

        return cls(include_exts, exclude_exts)

    def matches(self, file_ext: str) -> bool:
        """
        Determines if file_ext (without leading dot, lowercase) satisfies extension filtering rules.
        """
        norm_ext = file_ext.lstrip(".").lower()
        if self.exclude_exts and norm_ext in self.exclude_exts:
            return False
        if self.include_exts:
            return norm_ext in self.include_exts
        return True
