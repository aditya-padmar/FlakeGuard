"""Evidence validator for F2 diagnosis results.

Verifies that evidence from F2 classification can be used for remediation:
- File exists and is readable
- Line references are valid
- Code can be extracted
- Evidence is consistent
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os


class EvidenceValidator:
    """Validates evidence from F2 diagnosis before attempting remediation."""
    
    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize validator.
        
        Args:
            repo_root: Root directory of the repository. Defaults to sample-repo.
        """
        if repo_root is None:
            # Default to sample-repo for hackathon demo
            self.repo_root = Path("sample-repo")
        else:
            self.repo_root = Path(repo_root)
    
    def validate(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate F2 diagnosis evidence.
        
        Args:
            diagnosis: F2 diagnosis object with evidence
            
        Returns:
            Validation result with locations and message
            
        Example input:
            {
                "test_name": "test_payment_timeout",
                "root_cause": "timing_race",
                "confidence": 0.91,
                "evidence": [
                    {
                        "file": "tests/test_payment.py",
                        "line": 24,
                        "reason": "sleep before assertion"
                    }
                ]
            }
            
        Example output:
            {
                "valid": True,
                "locations": ["sample-repo/tests/test_payment.py:24"],
                "message": "Evidence verified",
                "details": [...]
            }
        """
        test_name = diagnosis.get("test_name", "unknown")
        evidence = diagnosis.get("evidence", [])
        
        if not evidence:
            return {
                "valid": False,
                "locations": [],
                "message": "No evidence provided",
                "details": []
            }
        
        locations = []
        details = []
        all_valid = True
        
        for item in evidence:
            result = self._validate_evidence_item(item)
            details.append(result)
            
            if result["valid"]:
                locations.append(result["location"])
            else:
                all_valid = False
        
        # Require at least one valid piece of evidence
        if not locations:
            return {
                "valid": False,
                "locations": [],
                "message": "No valid evidence found",
                "details": details
            }
        
        return {
            "valid": all_valid,
            "locations": locations,
            "message": "Evidence verified" if all_valid else "Partial evidence verified",
            "details": details
        }
    
    def _validate_evidence_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single evidence item.
        
        Args:
            item: Evidence item with file, line, reason
            
        Returns:
            Validation result for this item
        """
        file_path = item.get("file")
        line_num = item.get("line")
        reason = item.get("reason", "")
        
        if not file_path:
            return {
                "valid": False,
                "location": None,
                "message": "No file specified",
                "file_exists": False,
                "line_exists": False,
                "code_snippet": None
            }
        
        # Construct full path
        full_path = self.repo_root / file_path
        location = f"{full_path}:{line_num}" if line_num else str(full_path)
        
        # Check file exists
        if not full_path.exists():
            return {
                "valid": False,
                "location": location,
                "message": f"File not found: {full_path}",
                "file_exists": False,
                "line_exists": False,
                "code_snippet": None
            }
        
        # Check file is readable
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return {
                "valid": False,
                "location": location,
                "message": f"Cannot read file: {e}",
                "file_exists": True,
                "line_exists": False,
                "code_snippet": None
            }
        
        # Check line number if specified
        if line_num is not None:
            if line_num < 1 or line_num > len(lines):
                return {
                    "valid": False,
                    "location": location,
                    "message": f"Line {line_num} out of range (file has {len(lines)} lines)",
                    "file_exists": True,
                    "line_exists": False,
                    "code_snippet": None
                }
            
            # Extract code snippet (3 lines context)
            start = max(0, line_num - 2)
            end = min(len(lines), line_num + 1)
            snippet = ''.join(lines[start:end]).strip()
            
            return {
                "valid": True,
                "location": location,
                "message": "Evidence verified",
                "file_exists": True,
                "line_exists": True,
                "code_snippet": snippet,
                "reason": reason
            }
        else:
            # No line number, just verify file exists and is readable
            return {
                "valid": True,
                "location": location,
                "message": "File verified (no line number)",
                "file_exists": True,
                "line_exists": None,
                "code_snippet": None,
                "reason": reason
            }
    
    def extract_code_at_location(
        self, 
        file_path: str, 
        line_num: int,
        context_lines: int = 5
    ) -> Optional[Tuple[str, int, int]]:
        """
        Extract code snippet at a specific location.
        
        Args:
            file_path: Relative path to file
            line_num: Line number (1-indexed)
            context_lines: Number of lines before/after to include
            
        Returns:
            Tuple of (code_snippet, start_line, end_line) or None
        """
        full_path = self.repo_root / file_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return None
        
        if line_num < 1 or line_num > len(lines):
            return None
        
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        snippet = ''.join(lines[start:end])
        
        return snippet, start + 1, end
