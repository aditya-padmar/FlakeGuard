"""Test executor for running multiple test iterations."""
import asyncio
from typing import List, Optional
from datetime import datetime
import uuid

from backend.harness.runner import TestRunner
from backend.models.detection import TestRun


class TestExecutor:
    """Executes tests multiple times to detect flakiness."""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
    
    async def execute_multiple_runs(
        self,
        num_runs: int = 5,
        test_pattern: Optional[str] = None,
        delay_seconds: float = 0.0
    ) -> List[TestRun]:
        """
        Execute multiple test runs to detect flakiness.
        
        Args:
            num_runs: Number of test runs to execute
            test_pattern: Optional test pattern to filter tests
            delay_seconds: Delay between runs
            
        Returns:
            List of TestRun objects
        """
        runs = []
        
        for i in range(num_runs):
            print(f"Running test iteration {i + 1}/{num_runs}")
            
            # Run in thread to avoid blocking
            run = await asyncio.to_thread(
                self.runner.run_tests,
                test_pattern=test_pattern
            )
            runs.append(run)
            
            if i < num_runs - 1 and delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        return runs
    
    def execute_single_run(
        self,
        test_pattern: Optional[str] = None,
        pytest_args: Optional[List[str]] = None
    ) -> TestRun:
        """
        Execute a single test run.
        
        Args:
            test_pattern: Optional test pattern to filter tests
            pytest_args: Additional pytest arguments
            
        Returns:
            TestRun with results
        """
        return self.runner.run_tests(test_pattern, pytest_args)
