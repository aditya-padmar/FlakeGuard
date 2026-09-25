"""Parser for CI/CD pipeline outputs."""
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from backend.models.detection import TestRun, TestExecution, TestStatus


class CIParser:
    """Parses CI/CD pipeline outputs to extract test results."""
    
    def parse_github_actions(self, log_content: str, run_id: str) -> TestRun:
        """
        Parse GitHub Actions test output.
        
        Args:
            log_content: Raw log content from GitHub Actions
            run_id: CI run identifier
            
        Returns:
            TestRun with parsed results
        """
        executions = []
        
        # Parse pytest output
        pytest_pattern = r"(\S+\.py::\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)"
        matches = re.findall(pytest_pattern, log_content)
        
        for test_name, status in matches:
            status_map = {
                "PASSED": TestStatus.PASSED,
                "FAILED": TestStatus.FAILED,
                "SKIPPED": TestStatus.SKIPPED,
                "ERROR": TestStatus.ERROR
            }
            
            file_path = test_name.split("::")[0]
            
            executions.append(TestExecution(
                test_name=test_name,
                file_path=file_path,
                status=status_map.get(status, TestStatus.ERROR),
                duration=0.0  # Not available in simple parse
            ))
        
        return TestRun(
            run_id=run_id,
            repository="unknown",
            branch=self._extract_branch(log_content),
            commit_sha=self._extract_commit(log_content),
            executions=executions,
            total_tests=len(executions),
            passed=sum(1 for e in executions if e.status == TestStatus.PASSED),
            failed=sum(1 for e in executions if e.status == TestStatus.FAILED)
        )
    
    def parse_junit_xml(self, xml_path: str, run_id: str) -> TestRun:
        """
        Parse JUnit XML test results.
        
        Args:
            xml_path: Path to JUnit XML file
            run_id: Run identifier
            
        Returns:
            TestRun with parsed results
        """
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        executions = []
        
        for testcase in root.iter('testcase'):
            classname = testcase.get('classname', '')
            name = testcase.get('name', '')
            time = float(testcase.get('time', 0))
            
            # Determine status
            status = TestStatus.PASSED
            error_msg = None
            
            failure = testcase.find('failure')
            if failure is not None:
                status = TestStatus.FAILED
                error_msg = failure.get('message', '')
            
            error = testcase.find('error')
            if error is not None:
                status = TestStatus.ERROR
                error_msg = error.get('message', '')
            
            skipped = testcase.find('skipped')
            if skipped is not None:
                status = TestStatus.SKIPPED
            
            test_name = f"{classname}::{name}" if classname else name
            
            executions.append(TestExecution(
                test_name=test_name,
                file_path=classname.replace('.', '/') + '.py',
                status=status,
                duration=time,
                error_message=error_msg
            ))
        
        return TestRun(
            run_id=run_id,
            repository="unknown",
            branch="unknown",
            commit_sha="unknown",
            executions=executions,
            total_tests=len(executions),
            passed=sum(1 for e in executions if e.status == TestStatus.PASSED),
            failed=sum(1 for e in executions if e.status == TestStatus.FAILED)
        )
    
    def _extract_branch(self, log_content: str) -> str:
        """Extract branch name from log."""
        pattern = r"ref:\s*refs/heads/(\S+)"
        match = re.search(pattern, log_content)
        return match.group(1) if match else "unknown"
    
    def _extract_commit(self, log_content: str) -> str:
        """Extract commit SHA from log."""
        pattern = r"commit\s+([a-f0-9]{40})"
        match = re.search(pattern, log_content)
        return match.group(1) if match else "unknown"
