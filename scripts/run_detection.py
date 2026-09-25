#!/usr/bin/env python
"""
Script to run flaky test detection on a repository.

Usage:
    python scripts/run_detection.py <repo_path> [--runs N]
"""
import asyncio
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.harness.runner import TestRunner
from backend.harness.executor import TestExecutor
from backend.harness.analyzer import TestAnalyzer
from backend.config import settings


async def main():
    parser = argparse.ArgumentParser(description="Detect flaky tests")
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument("--runs", type=int, default=5, help="Number of test runs")
    parser.add_argument("--pattern", default=None, help="Test pattern to run")
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return
    
    print(f"Running flaky test detection on {repo_path}")
    print(f"Number of runs: {args.runs}")
    print("-" * 50)
    
    # Initialize runner and executor
    runner = TestRunner(repo_path)
    executor = TestExecutor(runner)
    
    # Run tests multiple times
    print("Executing test runs...")
    runs = await executor.execute_multiple_runs(
        num_runs=args.runs,
        test_pattern=args.pattern
    )
    
    print(f"Completed {len(runs)} test runs")
    
    # Analyze results
    print("Analyzing results for flaky tests...")
    analyzer = TestAnalyzer()
    detection = analyzer.analyze_runs(runs)
    
    # Print results
    print("-" * 50)
    print(f"Detection Results:")
    print(f"  Total test runs analyzed: {detection.total_test_runs}")
    print(f"  Flaky tests detected: {len(detection.flaky_tests)}")
    print(f"  Detection confidence: {detection.detection_confidence:.0%}")
    
    if detection.flaky_tests:
        print("\nFlaky Tests:")
        for test in detection.flaky_tests:
            print(f"  - {test.test_name}")
            print(f"    File: {test.file_path}")
            print(f"    Flake rate: {test.flake_rate:.0%}")
            print(f"    Runs: {test.total_runs} (P: {test.pass_count}, F: {test.fail_count})")
            print()


if __name__ == "__main__":
    asyncio.run(main())
