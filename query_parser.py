from __future__ import annotations

import re
from typing import List, Optional, Tuple

from search_rule import SearchRule


class QueryParser:
    """Responsible for parsing search syntax (*, ?, |, NOT, AND, comma) into compiled regex rules."""

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
    def parse(cls, query_str: str) -> Tuple[List[SearchRule], List[re.Pattern]]:
        """
        Parses comma-separated query items.
        Supports:
          - 'patternA, patternB' (Comma OR)
          - 'patternA | patternB' (Pipe OR)
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
