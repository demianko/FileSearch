from __future__ import annotations

import re
from typing import List

from search_rule import SearchRule


class QueryMatcher:
    """Responsible for evaluating text against compiled SearchRules and global exclusions."""

    @staticmethod
    def matches(text: str, rules: List[SearchRule], global_excludes: List[re.Pattern]) -> bool:
        """Evaluates whether text satisfies the parsed rules and global exclusions."""
        for ex in global_excludes:
            if ex.search(text):
                return False

        if not rules:
            return True

        return any(rule.matches(text) for rule in rules)
