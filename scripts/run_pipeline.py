#!/usr/bin/env python
"""
Script to run the complete FlakeGuard pipeline.

Usage:
    python scripts/run_pipeline.py <repo_path> [--runs N] [--output FILE]
"""
import asyncio
import argparse
import sys
from pathlib import Path
import json
from datetime import datetime, timezone
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.harness.runner import TestRunner
from backend.harness.executor import TestExecutor
from backend.harness.analyzer import TestAnalyzer
from backend.bob.agent import BobAgent
from backend.remediation.generator import FixGenerator
from backend.auditor.auditor import Auditor
from backend.config import settings


def _find_test_file(repo: Path, file_path: str) -> Optional[Path]:
    """Resolve test file path relative to repo or by filename search."""
    p = repo / file_path
    if p.exists() and p.is_file():
        return p
    candidates = list(repo.glob(f"**/{Path(file_path).name}"))
    return candidates[0] if candidates else None


async def main():
    parser = argparse.ArgumentParser(description="Run complete FlakeGuard pipeline")
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument("--runs", type=int, default=5, help="Number of test runs")
    parser.add_argument("--output", default="pipeline_results.json", help="Output file")
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return
    
    results = {
        "repository": str(repo_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runs": args.runs,
        "pipeline_version": "2.0-integrated",
    }
    
    print("=" * 60)
    print("FlakeGuard Integrated Pipeline (F1 -> F2 -> F3 -> F4)")
    print("=" * 60)
    
    # Step 1: Detection (F1)
    print(f"\n[Step 1/4] Running test detection ({args.runs} iterations)...")
    runner = TestRunner(str(repo_path))
    executor = TestExecutor(runner)
    
    test_runs = await executor.execute_multiple_runs(num_runs=args.runs)
    
    analyzer = TestAnalyzer()
    detection = analyzer.analyze_runs(test_runs)
    
    results["detection"] = {
        "total_runs": detection.total_test_runs,
        "flaky_tests_count": len(detection.flaky_tests),
        "confidence": detection.detection_confidence,
        "flaky_tests": [
            {
                "test_name": t.test_name,
                "file_path": t.file_path,
                "flake_rate": t.flake_rate,
                "pass_count": t.pass_count,
                "fail_count": t.fail_count,
            }
            for t in detection.flaky_tests
        ]
    }
    
    print(f"  Analyzed {detection.total_test_runs} test executions")
    print(f"  Found {len(detection.flaky_tests)} flaky tests (confidence: {detection.detection_confidence:.0%})")
    
    if not detection.flaky_tests:
        print("\nNo flaky tests detected. Pipeline complete.")
        with open(args.output, 'w', encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        return
    
    # Step 2: Classification with Parallel Subagents (F2)
    print("\n[Step 2/4] Classifying flaky tests with parallel root-cause subagents...")
    agent = BobAgent()
    classifications = []
    
    for test in detection.flaky_tests:
        target_file = _find_test_file(repo_path, test.file_path)
        if target_file and target_file.exists():
            test_source = target_file.read_text(encoding="utf-8")
            test.file_path = str(target_file)
        else:
            test_source = f"# Source for {test.test_name}"
        
        classification = await agent.classify_test(test, test_source)
        classifications.append(classification)
        
        ev_summary = f"[{len(classification.evidence)} evidence items]" if classification.evidence else ""
        print(f"  - {test.test_name}")
        print(f"    Root Cause: {classification.root_cause.value.upper()} ({classification.confidence.value} confidence) {ev_summary}")
        print(f"    Reasoning:  {classification.reasoning}")
    
    results["classifications"] = [
        {
            "classification_id": c.classification_id,
            "test_name": c.test_name,
            "file_path": c.file_path,
            "root_cause": c.root_cause.value,
            "confidence": c.confidence.value,
            "evidence": [e.description for e in c.evidence],
            "reasoning": c.reasoning,
            "suggested_fix_area": c.suggested_fix_area
        }
        for c in classifications
    ]
    
    # Step 3: Remediation Generator & Diffs (F3)
    print("\n[Step 3/4] Generating concrete code remediation diffs...")
    fix_generator = FixGenerator()
    fixes = []
    
    for classification in classifications:
        target_file = _find_test_file(repo_path, classification.file_path)
        test_source = target_file.read_text(encoding="utf-8") if target_file and target_file.exists() else ""
        fix = await fix_generator.generate_fix(classification, test_source)
        fixes.append(fix)
        
        diff_count = sum(1 for s in fix.suggestions if s.diff and s.diff.unified_diff)
        print(f"  - {fix.test_name}: {len(fix.suggestions)} suggestions ({diff_count} diffs generated)")
        for s in fix.suggestions:
            print(f"    [{s.fix_type}] {s.description}")
    
    results["fixes"] = [
        {
            "fix_id": f.fix_id,
            "test_name": f.test_name,
            "file_path": f.file_path,
            "status": f.status.value,
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "fix_type": s.fix_type,
                    "description": s.description,
                    "rationale": s.rationale,
                    "confidence": s.confidence,
                    "unified_diff": s.diff.unified_diff if s.diff else None
                }
                for s in f.suggestions
            ]
        }
        for f in fixes
    ]
    
    # Step 4: Quarantine & CI Audit (F4)
    print("\n[Step 4/4] Cross-referencing quarantine list and CI configuration...")
    auditor = Auditor()
    
    quarantine_path = repo_path / "QUARANTINE.md"
    if not quarantine_path.exists():
        quarantine_path = Path("sample-repo/QUARANTINE.md")
    
    audit_report = auditor.audit_quarantine(
        quarantine_path=str(quarantine_path),
        classifications=classifications,
        repo_path=str(repo_path)
    )
    
    results["quarantine_audit"] = {
        "report_id": audit_report.report_id,
        "total_quarantined": audit_report.total_quarantined,
        "diagnosed_count": audit_report.diagnosed_count,
        "fixable_count": audit_report.fixable_count,
        "unexplained_count": audit_report.unexplained_count,
        "tests": [
            {
                "test_name": t.test_name,
                "status": t.status.value,
                "diagnosed": t.diagnosed,
                "root_cause": t.root_cause,
                "confidence": t.confidence,
                "fixable": t.fixable,
                "fix_strategy": t.fix_strategy,
                "quarantine_reason": t.quarantine_reason,
                "source": t.source,
            }
            for t in audit_report.quarantined_tests
        ]
    }
    
    print(f"  Quarantine Audit Summary:")
    print(f"    Total Quarantined:    {audit_report.total_quarantined}")
    print(f"    Diagnosed with Cause: {audit_report.diagnosed_count}")
    print(f"    Fixable & Ready to Un-quarantine: {audit_report.fixable_count}")
    print(f"    Unexplained:          {audit_report.unexplained_count}")
    
    # Save session evidence in docs/bob-sessions/
    sessions_dir = ROOT / "docs" / "bob-sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_file = sessions_dir / f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(session_file, 'w', encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[Evidence] Bob session summary logged to {session_file}")
    
    # Save pipeline output
    with open(args.output, 'w', encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Pipeline Execution Complete!")
    print("=" * 60)
    print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
