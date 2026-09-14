"""
Shared radio.conf parsing.

radio.conf is a plain KEY=VALUE file with #-comment lines. Two consumers
parse it: main._load_radio_conf (seeds os.environ at startup, strips inline
comments) and the settings API (_read_conf, preserves values verbatim).
Both use these helpers so the format is defined exactly once.
"""

from pathlib import Path
from typing import Dict, Iterable


def parse_conf_lines(
    lines: Iterable[str], strip_inline_comments: bool = False
) -> Dict[str, str]:
    """Parse KEY=VALUE lines, skipping blanks, comments, and non-assignments.

    Args:
        lines: Lines of a radio.conf-style file.
        strip_inline_comments: Drop everything after a '#' in the value.
            (Values may legitimately contain '#' — e.g. passwords — so this
            is opt-in for the env-seeding path that has always done it.)
    """
    result: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if strip_inline_comments:
            value = value.split("#")[0]
        value = value.strip()
        if key:
            result[key] = value
    return result


def parse_conf_file(path: Path, strip_inline_comments: bool = False) -> Dict[str, str]:
    """Parse a radio.conf file. See parse_conf_lines."""
    with open(path) as f:
        return parse_conf_lines(f, strip_inline_comments=strip_inline_comments)
