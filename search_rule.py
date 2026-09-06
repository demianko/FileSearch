from __future__ import annotations

import re
from typing import List, Optional


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
        """Determines if the text satisfies the include pattern and is not rejected by any exclude pattern."""
        if self.include_regex and not self.include_regex.search(text):
            return False
        for exc in self.exclude_regexes:
            if exc.search(text):
                return False
        return True
