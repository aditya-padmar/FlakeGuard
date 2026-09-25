#!/usr/bin/env python
"""
Script to run the complete FlakeGuard pipeline.

Usage:
    python scripts/run_pipeline.py <repo_path> [--runs N]
"""
import asyncio
import argparse
from pathlib import Path
import json
from datetime import datetime

from backend.harness.runner import TestRunner
from backend.harness.executor import TestExecutor
from backend.harness.analyzer import TestAnalyzer
from backend.bob.agent import BobAgent
from backend.remediation.generator import FixGenerator
from backend.auditor.auditor import Auditor
from backend.config import settings


async def main():
    parser = argparse.ArgumentParser(description="Run complete FlakeGuard pipeline")
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument("--runs", type=int, default=5, help="Number of test runs")
    parser.add_argument("--output", default="pipeline_results.json", help="Output file")
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return
    
    results = {
        "repository": str(repo_path),
        "timestamp": datetime.utcnow().isoformat(),
        "runs": args.runs
    }
    
    print("=" * 60)
    print("FlakeGuard Pipeline")
    print("=" * 60)
    
    # Step 1: Detection
    print("\n[Step 1/4] Running test detection...")
    runner = TestRunner(repo_path)
    executor = TestExecutor(runner)
    
    test_runs = await executor.execute_multiple_runs(num_runs=args.runs)
    
    analyzer = TestAnalyzer()
    detection = await analyzer.analyze_runs(test_runs)
    
    results["detection"] = {
        "total_runs": detection.total_test_runs,
        "flaky_tests_count": len(detection.flaky_tests),
        "confidence": detection.detection_confidence
    }
    
    print(f"  Found {len(detection.flaky_tests)} flaky tests")
    
    if not detection.flaky_tests:
        print("\nNo flaky tests detected. Pipeline complete.")
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        return
    
    # Step 2: Classification
    print("\n[Step 2/4] Classifying flaky tests...")
    agent = BobAgent()
    classifications = []
    
    for test in detection.flaky_tests:
        # In production, fetch actual test source
        test_source = f"# Source for {test.test_name}"
        
        classification = await agent.classify_test(test, test_source)
        classifications.append(classification)
        
        print(f"  - {test.test_name}: {classification.root_cause.value} ({classification.confidence.value} confidence)")
    
    results["classifications"] = [
        {
            "test_name": c.test_name,
            "root_cause": c.root_cause.value,
            "confidence": c.confidence.value,
            "reasoning": c.reasoning
        }
        for c in classifications
    ]
    
    # Step 3: Remediation
    print("\n[Step 3/4] Generating fix suggestions...")
    fix_generator = FixGenerator()
    fixes = []
    
    for classification in classifications:
        test_source = f"# Source for {classification.test_name}"
        fix = await fix_generator.generate_fix(classification, test_source)
        fixes.append(fix)
        
        print(f"  - {fix.test_name}: {len(fix.suggestions)} suggestions")
    
    results["fixes"] = [
        {
            "test_name": f.test_name,
            "status": f.status.value,
            "suggestions_count": len(f.suggestions)
        }
        for f in fixes
    ]
    
    # Step 4: Audit
    print("\n[Step 4/4] Recording results...")
    auditor = Auditor()
    
    for test in detection.flaky_tests:
        auditor.add_to_quarantine(
            test_name=test.test_name,
            file_path=test.file_path,
            reason="Detected as flaky",
            root_cause=next(
                (c.root_cause.value for c in classifications if c.test_name == test.test_name),
                "unknown"
            )
        )
    
    report = auditor.generate_report()
    results["quarantine_report"] = {
        "total_quarantined": report.total_quarantined,
        "active_count": report.active_count
    }
    
    print(f"  Quarantined {report.active_count} tests")
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Pipeline Complete")
    print("=" * 60)
    print(f"Results saved to: {args.output}")
    print(f"\nSummary:")
    print(f"  Flaky tests detected: {len(detection.flaky_tests)}")
    print(f"  Classifications: {len(classifications)}")
    print(f"  Fix suggestions generated: {sum(len(f.suggestions) for f in fixes)}")
    print(f"  Tests quarantined: {report.active_count}")


if __name__ == "__main__":
    asyncio.run(main())
