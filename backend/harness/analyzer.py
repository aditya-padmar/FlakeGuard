"""Test run analyzer for detecting flaky tests."""
from collections import defaultdict
from typing import List, Dict
from datetime import datetime
import uuid

from backend.models.detection import TestRun, TestExecution, FlakyTest, DetectionResult, TestStatus


class TestAnalyzer:
    """Analyzes test runs to detect flaky tests."""
    
    def __init__(self, flake_threshold: float = 0.1):
        """
        Initialize analyzer.
        
        Args:
            flake_threshold: Minimum failure rate to consider a test flaky (default 10%)
        """
        self.flake_threshold = flake_threshold
    
    def analyze_runs(self, runs: List[TestRun]) -> DetectionResult:
        """
        Analyze multiple test runs to detect flaky tests.
        
        Args:
            runs: List of test runs to analyze
            
        Returns:
            DetectionResult with identified flaky tests
        """
        # Group executions by test name
        test_executions: Dict[str, List[TestExecution]] = defaultdict(list)
        
        for run in runs:
            for execution in run.executions:
                test_executions[execution.test_name].append(execution)
        
        # Detect flaky tests
        flaky_tests = []
        
        for test_name, executions in test_executions.items():
            flaky_test = self._detect_flakiness(test_name, executions)
            if flaky_test:
                flaky_tests.append(flaky_test)
        
        # Sort by flake rate (most flaky first)
        flaky_tests.sort(key=lambda t: t.flake_rate, reverse=True)
        
        return DetectionResult(
            detection_id=str(uuid.uuid4()),
            repository=runs[0].repository if runs else "unknown",
            analysis_period_start=min(run.timestamp for run in runs),
            analysis_period_end=max(run.timestamp for run in runs),
            total_test_runs=len(runs),
            flaky_tests=flaky_tests,
            detection_confidence=self._calculate_confidence(runs)
        )
    
    def _detect_flakiness(
        self, 
        test_name: str, 
        executions: List[TestExecution]
    ) -> FlakyTest:
        """
        Detect if a test is flaky based on its executions.
        
        A test is flaky if it has both passes and failures.
        """
        if not executions:
            return None
        
        # Count statuses
        passes = sum(1 for e in executions if e.status == TestStatus.PASSED)
        failures = sum(1 for e in executions if e.status == TestStatus.FAILED)
        total = len(executions)
        
        # A test is flaky only if it has both passes and failures
        if passes == 0 or failures == 0:
            return None
        
        flake_rate = failures / total
        
        # Filter to only flake_rate threshold
        if flake_rate < self.flake_threshold:
            return None
        
        # Get recent failure messages
        recent_failures = [
            e.error_message
            for e in executions
            if e.status == TestStatus.FAILED and e.error_message
        ][:5]  # Keep last 5 failures
        
        return FlakyTest(
            test_name=test_name,
            file_path=executions[0].file_path,
            first_seen=min(e.timestamp for e in executions),
            last_seen=max(e.timestamp for e in executions),
            total_runs=total,
            pass_count=passes,
            fail_count=failures,
            flake_rate=flake_rate,
            recent_failures=recent_failures,
            status_history=[e.status for e in executions]
        )
    
    def _calculate_confidence(self, runs: List[TestRun]) -> float:
        """
        Calculate confidence in detection results.
        
        More runs = higher confidence.
        """
        if not runs:
            return 0.0
        
        # Base confidence on number of runs
        # 5 runs = 0.7, 10 runs = 0.85, 20 runs = 0.95
        num_runs = len(runs)
        
        if num_runs >= 20:
            return 0.95
        elif num_runs >= 10:
            return 0.85
        elif num_runs >= 5:
            return 0.7
        else:
            return 0.5 * (num_runs / 5)
