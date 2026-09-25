"""Test runner module for executing tests and capturing results."""
import subprocess
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from backend.models.detection import TestRun, TestExecution, TestStatus


class TestRunner:
    """Executes tests and captures results."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def run_tests(
        self, 
        test_pattern: Optional[str] = None,
        pytest_args: Optional[List[str]] = None
    ) -> TestRun:
        """
        Run pytest and capture results.
        
        Args:
            test_pattern: Optional test pattern to run
            pytest_args: Additional pytest arguments
            
        Returns:
            TestRun with execution results
        """
        run_id = str(uuid.uuid4())
        
        # Build pytest command
        cmd = [
            "pytest",
            "--tb=short",
            "-v",
            "--json-report",  # Requires pytest-json-report
            f"--json-report-file=.temp_results_{run_id}.json"
        ]
        
        if test_pattern:
            cmd.extend(["-k", test_pattern])
        
        if pytest_args:
            cmd.extend(pytest_args)
        
        # Execute tests
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        # Parse results
        results_file = self.repo_path / f".temp_results_{run_id}.json"
        
        executions = []
        if results_file.exists():
            with open(results_file) as f:
                data = json.load(f)
                executions = self._parse_pytest_results(data)
            results_file.unlink()
        
        return TestRun(
            run_id=run_id,
            repository=str(self.repo_path),
            branch=self._get_current_branch(),
            commit_sha=self._get_current_commit(),
            executions=executions,
            total_tests=len(executions),
            passed=sum(1 for e in executions if e.status == TestStatus.PASSED),
            failed=sum(1 for e in executions if e.status == TestStatus.FAILED)
        )
    
    def _parse_pytest_results(self, data: dict) -> List[TestExecution]:
        """Parse pytest JSON report into TestExecution objects."""
        executions = []
        status_map = {
            "passed": TestStatus.PASSED,
            "failed": TestStatus.FAILED,
            "skipped": TestStatus.SKIPPED,
            "error": TestStatus.ERROR
        }
        
        for test in data.get("tests", []):
            nodeid = test.get("nodeid", "")
            loc = test.get("location")
            if loc and isinstance(loc, (list, tuple)) and len(loc) > 0:
                file_path = loc[0]
            else:
                file_path = nodeid.split("::")[0] if "::" in nodeid else nodeid
            
            call_info = test.get("call") or test.get("setup") or test.get("teardown") or {}
            crash = call_info.get("crash") or {}
            error_msg = crash.get("message")
            error_tb = crash.get("traceback")
            
            executions.append(TestExecution(
                test_name=nodeid,
                file_path=file_path,
                status=status_map.get(test.get("outcome"), TestStatus.ERROR),
                duration=test.get("duration", 0.0),
                error_message=error_msg,
                error_traceback=error_tb
            ))
        
        return executions
    
    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"
    
    def _get_current_commit(self) -> str:
        """Get current git commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"
