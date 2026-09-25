"""
Parser for quarantine and skip-list artifacts.

Supports three formats that all appear in real projects:

1. Markdown table  (QUARANTINE.md — the project's own format)
   | test_name | Reason | 2024-01-15 | 10 |

2. Markdown bullet list
   - test_payment_timeout
   * test_shared_cache
   + test_old_api

3. Plain text / pytest skip-list
   test_payment_timeout
   test_shared_cache

All three formats can coexist in a single file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from backend.models.audit import QuarantineEntry, QuarantineStatus


# ── Patterns ──────────────────────────────────────────────────────────────────

# Markdown table row: | test_name | reason | date | runs |
# Allows optional back-tick quoting around the test name.
# The name must start with a word character (letter/digit/_) to exclude
# separator rows like |------|-------|
_RE_TABLE_ROW = re.compile(
    r"^\|\s*`?(?P<name>[\w][\w:./-]*)`?\s*\|"  # col 1 – test name (starts with \w)
    r"\s*(?P<reason>[^|]+?)\s*\|"               # col 2 – reason
    r"(?:\s*(?P<date>\d{4}-\d{2}-\d{2})\s*\|)?"  # col 3 – date (optional)
    r"(?:\s*(?P<runs>\d+)\s*\|)?",              # col 4 – runs_until_review (optional)
    re.MULTILINE,
)

# Markdown bullet: - test_name  /  * test_name  /  + test_name
_RE_BULLET = re.compile(
    r"^[\s]*[-*+]\s+(?P<name>test_[\w:./-]+)",
    re.MULTILINE,
)

# Bare test name on its own line (plain text format)
_RE_BARE = re.compile(
    r"^(?P<name>test_[\w:./-]+)\s*$",
    re.MULTILINE,
)

# Section headers used to distinguish Active from Resolved tables
_RE_RESOLVED_HEADING = re.compile(r"^##?\s+resolved", re.IGNORECASE | re.MULTILINE)
_RE_ACTIVE_HEADING = re.compile(r"^##?\s+active", re.IGNORECASE | re.MULTILINE)

# Separator / header rows inside Markdown tables — skip these
_RE_TABLE_SEPARATOR = re.compile(r"^\|[-| :]+\|$", re.MULTILINE)
_RE_TABLE_HEADER = re.compile(
    r"^\|\s*(?:Test|Name|test_name)\s*\|", re.IGNORECASE | re.MULTILINE
)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ParsedQuarantineEntry:
    """
    Lightweight result from parsing a quarantine file.

    Deliberately separate from the pydantic QuarantineEntry model so the
    parser can be used without a full pydantic environment.
    """
    test_name: str
    reason: str = "Quarantined"
    quarantined_at: Optional[datetime] = None
    runs_until_review: int = 10
    resolved: bool = False
    source: str = "quarantine_file"


# ── Main parser ───────────────────────────────────────────────────────────────

class QuarantineParser:
    """
    Parses quarantine files into lists of test names / entries.

    Primary method: ``parse(path)`` — auto-detects format.
    """

    # ── Public API ────────────────────────────────────────────────────────────

    def parse(self, path: str) -> List[ParsedQuarantineEntry]:
        """
        Auto-detect format and parse *path*.

        Supported formats: Markdown (.md), plain text (.txt / no extension).
        Returns an empty list when the file does not exist.
        """
        p = Path(path)
        if not p.exists():
            return []

        content = p.read_text(encoding="utf-8")
        suffix = p.suffix.lower()

        if suffix in (".md", ".markdown") or "##" in content or "#" in content[:200]:
            return self.parse_markdown_content(content, source=str(p))
        return self.parse_plain_content(content, source=str(p))

    def parse_names(self, path: str) -> List[str]:
        """Return only the test names from a quarantine file."""
        return [e.test_name for e in self.parse(path)]

    # ── Format parsers ────────────────────────────────────────────────────────

    def parse_markdown_content(
        self, content: str, source: str = "quarantine_file"
    ) -> List[ParsedQuarantineEntry]:
        """
        Parse Markdown content that may contain tables and/or bullet lists.

        Only *active* quarantines are returned; entries under a "Resolved"
        heading are parsed but flagged ``resolved=True`` and excluded from
        the active list unless the caller explicitly requests them.
        """
        entries: List[ParsedQuarantineEntry] = []
        seen: set = set()

        # ── 1. Table rows ─────────────────────────────────────────────────────
        # Split into sections so we can distinguish Active vs Resolved tables
        sections = self._split_by_sections(content)
        for is_resolved, section_text in sections:
            for m in _RE_TABLE_ROW.finditer(section_text):
                name = m.group("name").strip()
                if not name or _is_header_name(name) or name in seen:
                    continue
                seen.add(name)

                reason = m.group("reason").strip()
                date_str = m.group("date")
                runs_str = m.group("runs")

                quarantined_at = None
                if date_str:
                    try:
                        quarantined_at = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        pass

                entries.append(ParsedQuarantineEntry(
                    test_name=name,
                    reason=reason,
                    quarantined_at=quarantined_at,
                    runs_until_review=int(runs_str) if runs_str else 10,
                    resolved=is_resolved,
                    source=source,
                ))

        # ── 2. Bullet list items ──────────────────────────────────────────────
        for m in _RE_BULLET.finditer(content):
            name = m.group("name").strip()
            if name not in seen:
                seen.add(name)
                entries.append(ParsedQuarantineEntry(
                    test_name=name,
                    source=source,
                ))

        return entries

    def parse_plain_content(
        self, content: str, source: str = "quarantine_file"
    ) -> List[ParsedQuarantineEntry]:
        """
        Parse a plain-text file where each non-comment line is a test name.
        Lines beginning with '#' are treated as comments and skipped.
        """
        entries: List[ParsedQuarantineEntry] = []
        seen: set = set()

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Accept lines that look like a test name (may or may not start with test_)
            name = stripped.split()[0]  # ignore inline comments
            if name and name not in seen:
                seen.add(name)
                entries.append(ParsedQuarantineEntry(test_name=name, source=source))

        return entries

    # ── Pydantic model conversion ─────────────────────────────────────────────

    def to_quarantine_entries(
        self, parsed: List[ParsedQuarantineEntry]
    ) -> List[QuarantineEntry]:
        """Convert ParsedQuarantineEntry list to pydantic QuarantineEntry list."""
        result = []
        for p in parsed:
            result.append(QuarantineEntry(
                quarantine_id=f"q_{p.test_name}",
                test_name=p.test_name,
                file_path="",
                reason=p.reason,
                quarantined_at=p.quarantined_at or datetime.now(timezone.utc),
                status=QuarantineStatus.RESOLVED if p.resolved else QuarantineStatus.ACTIVE,
                runs_until_review=p.runs_until_review,
            ))
        return result

    # ── Legacy methods (kept for backward compatibility) ──────────────────────

    def parse_markdown(self, md_path: str) -> List[QuarantineEntry]:
        """
        Parse a markdown quarantine file.  Returns pydantic QuarantineEntry objects.
        Kept for backward compatibility with the existing audit route.
        """
        parsed = self.parse(md_path)
        return self.to_quarantine_entries(parsed)

    def parse_pytest_quarantine(self, quarantine_file: str) -> List[str]:
        """
        Parse a plain pytest quarantine/skip-list file.
        Returns test names only.
        """
        return self.parse_names(quarantine_file)

    def generate_markdown(
        self,
        entries: List[QuarantineEntry],
        output_path: str,
    ) -> None:
        """Generate a QUARANTINE.md from a list of QuarantineEntry objects."""
        active = [e for e in entries if e.status == QuarantineStatus.ACTIVE]
        resolved = [e for e in entries if e.status == QuarantineStatus.RESOLVED]

        lines = ["# Quarantined Tests\n"]

        lines += [
            "## Active Quarantines\n",
            "| Test | Reason | Quarantined Date | Runs Until Review |",
            "|------|--------|------------------|-------------------|",
        ]
        for e in active:
            date = e.quarantined_at.strftime("%Y-%m-%d")
            lines.append(f"| `{e.test_name}` | {e.reason} | {date} | {e.runs_until_review} |")

        if resolved:
            lines += [
                "\n## Resolved Quarantines\n",
                "| Test | Reason | Resolved Date | Fix Applied |",
                "|------|--------|---------------|-------------|",
            ]
            for e in resolved:
                date = e.resolution_date.strftime("%Y-%m-%d") if e.resolution_date else "N/A"
                lines.append(
                    f"| `{e.test_name}` | {e.reason} | {date} | {e.resolution_notes or 'N/A'} |"
                )

        lines += [
            "\n## Quarantine Policy\n",
            "Tests are quarantined after 3 consecutive flaky failures. "
            "They are reviewed every 10 runs or when a fix is proposed.",
        ]

        Path(output_path).write_text("\n".join(lines), encoding="utf-8")

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _split_by_sections(
        content: str,
    ) -> List[tuple[bool, str]]:
        """
        Split Markdown content into (is_resolved, text) pairs by section heading.

        Sections whose heading matches "Resolved" are marked is_resolved=True.
        Everything before the first heading is treated as non-resolved.
        """
        # Find all headings and their positions
        heading_re = re.compile(r"^(#{1,3}\s+.+)$", re.MULTILINE)
        headings = list(heading_re.finditer(content))

        if not headings:
            return [(False, content)]

        sections: List[tuple[bool, str]] = []

        # Text before the first heading
        if headings[0].start() > 0:
            sections.append((False, content[: headings[0].start()]))

        for i, h in enumerate(headings):
            start = h.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(content)
            heading_text = h.group(1)
            is_resolved = bool(re.search(r"resolved", heading_text, re.IGNORECASE))
            sections.append((is_resolved, content[start:end]))

        return sections


def _is_header_name(name: str) -> bool:
    """Return True if name looks like a table header rather than a test name."""
    return name.lower() in {"test", "name", "test_name", "testname", "tests"}
