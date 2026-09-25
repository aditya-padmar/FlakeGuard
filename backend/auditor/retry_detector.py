"""Retry detector for CI/test retry configuration.

Detects retry mechanisms in:
- GitHub Actions CI configuration
- pytest configuration
- pytest-retry plugins
"""
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


class RetryDetector:
    """Detects retry mechanisms in CI and test configuration."""
    
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
    
    def detect_all(self) -> Dict[str, Any]:
        """
        Detect all retry mechanisms.
        
        Returns:
            Combined retry detection results
        """
        results = {
            "github_actions": self.detect_github_actions(),
            "pytest_config": self.detect_pytest_config(),
            "summary": {
                "retry_detected": False,
                "sources": []
            }
        }
        
        # Determine if any retries detected
        if results["github_actions"]["retry_detected"]:
            results["summary"]["retry_detected"] = True
            results["summary"]["sources"].append("github_actions")
        
        if results["pytest_config"]["retry_detected"]:
            results["summary"]["retry_detected"] = True
            results["summary"]["sources"].append("pytest_config")
        
        return results
    
    def detect_github_actions(self) -> Dict[str, Any]:
        """
        Detect retries in GitHub Actions workflow.
        
        Returns:
            Detection result with retry configuration
        """
        # Check common workflow file locations
        workflow_paths = [
            ".github/workflows/ci.yml",
            ".github/workflows/tests.yml",
            ".github/workflows/test.yml",
        ]
        
        for workflow_path in workflow_paths:
            full_path = self.repo_root / workflow_path
            if full_path.exists():
                result = self._parse_github_workflow(full_path, workflow_path)
                if result["retry_detected"]:
                    return result
        
        return {
            "retry_detected": False,
            "source": "github_actions",
            "file": None,
            "retry_count": 0,
            "details": []
        }
    
    def _parse_github_workflow(
        self, 
        file_path: Path, 
        relative_path: str
    ) -> Dict[str, Any]:
        """Parse GitHub Actions workflow file for retry configuration."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return {
                "retry_detected": False,
                "source": "github_actions",
                "file": relative_path,
                "retry_count": 0,
                "details": []
            }
        
        details = []
        max_retry = 0
        
        # Check for retry action usage
        retry_patterns = [
            (r'uses:\s*nick-invision/retry@', "nick-invision/retry action"),
            (r'uses:\s*Wandalen/wretry\.action@', "wretry action"),
            (r'pytest.*--reruns[=\s]+(\d+)', "pytest reruns plugin"),
        ]
        
        for pattern, description in retry_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Try to extract retry count
                retry_count = self._extract_retry_count(content, match.start())
                if retry_count > max_retry:
                    max_retry = retry_count
                
                details.append({
                    "mechanism": description,
                    "retry_count": retry_count,
                    "line": content[:match.start()].count('\n') + 1
                })
        
        return {
            "retry_detected": len(details) > 0,
            "source": "github_actions",
            "file": relative_path,
            "retry_count": max_retry,
            "details": details
        }
    
    def _extract_retry_count(self, content: str, start_pos: int) -> int:
        """Extract retry count from configuration near position."""
        # Look in the next 500 characters for retry count
        snippet = content[start_pos:start_pos + 500]
        
        # Common patterns for retry count
        patterns = [
            r'max_attempts:\s*(\d+)',
            r'max-attempts:\s*(\d+)',
            r'attempts:\s*(\d+)',
            r'reruns:\s*(\d+)',
            r'--reruns[=\s]+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, snippet)
            if match:
                return int(match.group(1))
        
        # Default retry count if found but not specified
        return 3
    
    def detect_pytest_config(self) -> Dict[str, Any]:
        """
        Detect retries in pytest configuration.
        
        Returns:
            Detection result with pytest retry config
        """
        # Check pytest.ini and setup.cfg
        config_files = ["pytest.ini", "setup.cfg", "pyproject.toml"]
        
        for config_file in config_files:
            full_path = self.repo_root / config_file
            if full_path.exists():
                result = self._parse_pytest_config(full_path, config_file)
                if result["retry_detected"]:
                    return result
        
        return {
            "retry_detected": False,
            "source": "pytest_config",
            "file": None,
            "retry_count": 0,
            "details": []
        }
    
    def _parse_pytest_config(
        self, 
        file_path: Path, 
        relative_path: str
    ) -> Dict[str, Any]:
        """Parse pytest configuration file for retry settings."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return {
                "retry_detected": False,
                "source": "pytest_config",
                "file": relative_path,
                "retry_count": 0,
                "details": []
            }
        
        details = []
        max_retry = 0
        
        # Check for pytest-rerunfailures configuration
        retry_patterns = [
            (r'--reruns[=\s]+(\d+)', "pytest reruns option"),
            (r'reruns\s*=\s*(\d+)', "reruns configuration"),
            (r'pytest-rerunfailures', "pytest-rerunfailures plugin"),
        ]
        
        for pattern, description in retry_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                retry_count = int(match.group(1)) if match.lastindex else 3
                if retry_count > max_retry:
                    max_retry = retry_count
                
                details.append({
                    "mechanism": description,
                    "retry_count": retry_count,
                    "line": content[:match.start()].count('\n') + 1
                })
        
        return {
            "retry_detected": len(details) > 0,
            "source": "pytest_config",
            "file": relative_path,
            "retry_count": max_retry,
            "details": details
        }
    
    def detect_for_test(self, test_name: str) -> Dict[str, Any]:
        """
        Detect if a specific test has retry configuration.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Detection result for this specific test
        """
        # Get global retry configuration
        global_config = self.detect_all()
        
        if not global_config["summary"]["retry_detected"]:
            return {
                "test_name": test_name,
                "retry_detected": False,
                "retry_count": 0,
                "source": None
            }
        
        # For hackathon demo, assume global retry applies to all tests
        # In production, would check for test-specific retry decorators
        
        max_retry = 0
        sources = []
        
        if global_config["github_actions"]["retry_detected"]:
            count = global_config["github_actions"]["retry_count"]
            if count > max_retry:
                max_retry = count
            sources.append(global_config["github_actions"]["source"])
        
        if global_config["pytest_config"]["retry_detected"]:
            count = global_config["pytest_config"]["retry_count"]
            if count > max_retry:
                max_retry = count
            sources.append(global_config["pytest_config"]["source"])
        
        return {
            "test_name": test_name,
            "retry_detected": max_retry > 0,
            "retry_count": max_retry,
            "source": ", ".join(sources) if sources else None
        }
