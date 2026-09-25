"""Parser for quarantine files."""
import re
from typing import List
from pathlib import Path
from datetime import datetime

from backend.models.audit import QuarantineEntry, QuarantineStatus


class QuarantineParser:
    """Parses quarantine files from various formats."""
    
    def parse_markdown(self, md_path: str) -> List[QuarantineEntry]:
        """
        Parse a markdown quarantine file (like QUARANTINE.md).
        
        Args:
            md_path: Path to markdown file
            
        Returns:
            List of QuarantineEntry objects
        """
        with open(md_path, 'r') as f:
            content = f.read()
        
        entries = []
        
        # Find table rows
        # Assuming format: | test_name | reason | date | runs |
        table_pattern = r'\|\s*`?(\S+)`?\s*\|\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\d+)'
        
        matches = re.findall(table_pattern, content)
        
        for test_name, reason, date_str, runs in matches:
            try:
                quarantined_at = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                quarantined_at = datetime.utcnow()
            
            entry = QuarantineEntry(
                quarantine_id=f"q_{test_name}",
                test_name=test_name,
                file_path="",  # Not in markdown
                reason=reason.strip(),
                quarantined_at=quarantined_at,
                status=QuarantineStatus.ACTIVE,
                runs_until_review=int(runs)
            )
            entries.append(entry)
        
        return entries
    
    def parse_pytest_quarantine(self, quarantine_file: str) -> List[str]:
        """
        Parse pytest quarantine configuration.
        
        Args:
            quarantine_file: Path to pytest quarantine config
            
        Returns:
            List of quarantined test names
        """
        tests = []
        
        with open(quarantine_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    tests.append(line)
        
        return tests
    
    def generate_markdown(
        self,
        entries: List[QuarantineEntry],
        output_path: str
    ):
        """
        Generate a markdown quarantine file.
        
        Args:
            entries: List of quarantine entries
            output_path: Path to write markdown file
        """
        active = [e for e in entries if e.status == QuarantineStatus.ACTIVE]
        resolved = [e for e in entries if e.status == QuarantineStatus.RESOLVED]
        
        md_content = ["# Quarantined Tests\n"]
        
        # Active quarantines
        md_content.append("## Active Quarantines\n")
        md_content.append("| Test | Reason | Quarantined Date | Runs Until Review |")
        md_content.append("|------|--------|------------------|-------------------|")
        
        for entry in active:
            date = entry.quarantined_at.strftime("%Y-%m-%d")
            md_content.append(
                f"| `{entry.test_name}` | {entry.reason} | {date} | {entry.runs_until_review} |"
            )
        
        # Resolved quarantines
        if resolved:
            md_content.append("\n## Resolved Quarantines\n")
            md_content.append("| Test | Reason | Resolved Date | Fix Applied |")
            md_content.append("|------|--------|---------------|-------------|")
            
            for entry in resolved:
                date = entry.resolution_date.strftime("%Y-%m-%d") if entry.resolution_date else "N/A"
                md_content.append(
                    f"| `{entry.test_name}` | {entry.reason} | {date} | {entry.resolution_notes or 'N/A'} |"
                )
        
        # Policy
        md_content.append("\n## Quarantine Policy\n")
        md_content.append(
            "Tests are quarantined after 3 consecutive flaky failures. "
            "They are reviewed every 10 runs or when a fix is proposed."
        )
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(md_content))
