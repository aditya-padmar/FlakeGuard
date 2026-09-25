"""Skip/xfail detector for test suppression mechanisms.

Detects tests using:
- @pytest.mark.skip
- @pytest.mark.xfail
- pytest.skip() calls
- Other suppression patterns
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class SkipDetector:
    """Detects skip and xfail markers in test files."""
    
    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize detector.
        
        Args:
            repo_root: Root directory of repository
        """
        if repo_root is None:
            self.repo_root = Path("sample-repo")
        else:
            self.repo_root = Path(repo_root)
    
    def detect_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect skip/xfail markers in a file.
        
        Args:
            file_path: Relative path to test file
            
        Returns:
            List of detected suppressions
        """
        full_path = self.repo_root / file_path
        
        if not full_path.exists():
            return []
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            return []
        
        detections = []
        
        # Detect decorator markers
        detections.extend(self._detect_decorators(lines, file_path))
        
        # Detect inline skip calls
        detections.extend(self._detect_inline_skips(lines, file_path))
        
        return detections
    
    def _detect_decorators(
        self, 
        lines: List[str], 
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Detect @pytest.mark.skip and @pytest.mark.xfail decorators."""
        detections = []
        
        # Pattern for test function names
        test_pattern = re.compile(r'^\s*def\s+(test_\w+)\s*\(')
        
        # Patterns for markers
        skip_pattern = re.compile(r'@pytest\.mark\.skip')
        xfail_pattern = re.compile(r'@pytest\.mark\.xfail')
        
        current_test = None
        decorators = []
        
        for i, line in enumerate(lines, start=1):
            # Check if this is a test function
            test_match = test_pattern.search(line)
            if test_match:
                # Found test function
                current_test = test_match.group(1)
                
                # Check if previous lines had skip/xfail decorators
                for dec_line, dec_type, reason in decorators:
                    detections.append({
                        "test_name": current_test,
                        "file": file_path,
                        "line": dec_line,
                        "suppression_type": dec_type,
                        "reason": reason,
                        "source": "decorator"
                    })
                
                # Reset decorators
                decorators = []
                current_test = None
            
            # Check for skip/xfail markers
            if skip_pattern.search(line):
                reason = self._extract_reason(line)
                decorators.append((i, "skip", reason))
            
            if xfail_pattern.search(line):
                reason = self._extract_reason(line)
                decorators.append((i, "xfail", reason))
        
        return detections
    
    def _detect_inline_skips(
        self, 
        lines: List[str], 
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Detect pytest.skip() calls inside test functions."""
        detections = []
        
        # Pattern for test function
        test_pattern = re.compile(r'^\s*def\s+(test_\w+)\s*\(')
        
        # Pattern for pytest.skip call
        skip_call_pattern = re.compile(r'pytest\.skip\s*\(')
        
        current_test = None
        in_test = False
        
        for i, line in enumerate(lines, start=1):
            # Check if entering a test function
            test_match = test_pattern.search(line)
            if test_match:
                current_test = test_match.group(1)
                in_test = True
                continue
            
            # Check if exiting test function (dedent)
            if in_test and line and not line[0].isspace() and current_test:
                in_test = False
                current_test = None
            
            # Check for skip call inside test
            if in_test and current_test and skip_call_pattern.search(line):
                reason = self._extract_reason(line)
                detections.append({
                    "test_name": current_test,
                    "file": file_path,
                    "line": i,
                    "suppression_type": "skip_call",
                    "reason": reason,
                    "source": "inline"
                })
        
        return detections
    
    def _extract_reason(self, line: str) -> Optional[str]:
        """Extract reason from skip/xfail marker or call."""
        # Try to extract reason from parentheses or quotes
        reason_pattern = re.compile(r'reason\s*=\s*["\']([^"\']+)["\']')
        match = reason_pattern.search(line)
        if match:
            return match.group(1)
        
        # Try to extract from simple string argument
        simple_pattern = re.compile(r'["\']([^"\']+)["\']')
        match = simple_pattern.search(line)
        if match:
            return match.group(1)
        
        return None
    
    def detect_in_directory(self, test_dir: str = "tests") -> List[Dict[str, Any]]:
        """
        Detect skip/xfail markers in all test files in a directory.
        
        Args:
            test_dir: Directory containing test files
            
        Returns:
            List of all detected suppressions
        """
        test_path = self.repo_root / test_dir
        
        if not test_path.exists():
            return []
        
        all_detections = []
        
        for test_file in test_path.glob("test_*.py"):
            relative_path = test_file.relative_to(self.repo_root)
            detections = self.detect_in_file(str(relative_path))
            all_detections.extend(detections)
        
        return all_detections
    
    def summarize(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize skip/xfail detections.
        
        Args:
            detections: List of detections
            
        Returns:
            Summary statistics
        """
        if not detections:
            return {
                "total_suppressed": 0,
                "skip_count": 0,
                "xfail_count": 0,
                "tests": []
            }
        
        skip_count = sum(1 for d in detections if d["suppression_type"] in ["skip", "skip_call"])
        xfail_count = sum(1 for d in detections if d["suppression_type"] == "xfail")
        
        # Group by test name
        tests = {}
        for d in detections:
            test_name = d["test_name"]
            if test_name not in tests:
                tests[test_name] = []
            tests[test_name].append(d)
        
        return {
            "total_suppressed": len(tests),
            "skip_count": skip_count,
            "xfail_count": xfail_count,
            "tests": list(tests.keys())
        }
