#!/usr/bin/env python
"""
Verification script for IBM Bob 2.0 AI Agent & Parallel Subagents.

Tests BobAgent across all 4 seeded flaky test categories:
1. Timing / Race Condition (test_timing.py)
2. Order Dependency (test_order.py)
3. State / Fixture Leakage (test_leakage.py)
4. Environment / Network (test_network.py)

Usage:
    python scripts/verify_bob_agent.py
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.bob.agent import BobAgent
from backend.models.detection import FlakyTest, TestStatus
from backend.models.classification import RootCauseType


async def run_verification():
    print("=" * 70)
    print(" FlakeGuard - IBM Bob 2.0 Agent & Subagents Verification")
    print("=" * 70)

    agent = BobAgent()
    status = agent.get_status()
    print(f"Agent Name    : {status['name']} v{status['version']}")
    print(f"Architecture  : {status['architecture']}")
    print(f"LLM Configured: {status['llm_configured']}")
    print(f"Subagents     : {[s.value for s in status['subagents']]}")
    print("-" * 70)

    test_cases = [
        {
            "test_name": "TestTimingIssues::test_sleep_based",
            "file_path": "sample-repo/tests/test_timing.py",
            "expected_cause": RootCauseType.TIMING,
            "recent_failures": ["AssertionError: assert result == 4"],
            "status_history": [TestStatus.PASSED, TestStatus.FAILED, TestStatus.PASSED, TestStatus.FAILED]
        },
        {
            "test_name": "TestOrderingIssues::test_second",
            "file_path": "sample-repo/tests/test_order.py",
            "expected_cause": RootCauseType.ORDERING,
            "recent_failures": ["AssertionError: assert calc.operation_count == 1 (was 0)"],
            "status_history": [TestStatus.PASSED, TestStatus.FAILED, TestStatus.PASSED]
        },
        {
            "test_name": "TestStateLeakage::test_global_mutation",
            "file_path": "sample-repo/tests/test_leakage.py",
            "expected_cause": RootCauseType.STATE_LEAKAGE,
            "recent_failures": ["AssertionError: state left dirty from previous execution"],
            "status_history": [TestStatus.FAILED, TestStatus.PASSED, TestStatus.FAILED]
        },
        {
            "test_name": "TestEnvironmentIssues::test_random_failure",
            "file_path": "sample-repo/tests/test_network.py",
            "expected_cause": RootCauseType.ENVIRONMENT,
            "recent_failures": ["Failed: Random failure for flaky test demonstration"],
            "status_history": [TestStatus.PASSED, TestStatus.FAILED, TestStatus.PASSED, TestStatus.PASSED, TestStatus.FAILED]
        }
    ]

    all_passed = True
    results_summary = []

    for i, tc in enumerate(test_cases, 1):
        print(f"\n[Test {i}/4] Evaluating '{tc['test_name']}'...")
        flaky_test = FlakyTest(
            test_name=tc["test_name"],
            file_path=tc["file_path"],
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            total_runs=len(tc["status_history"]),
            pass_count=sum(1 for s in tc["status_history"] if s == TestStatus.PASSED),
            fail_count=sum(1 for s in tc["status_history"] if s == TestStatus.FAILED),
            flake_rate=0.5,
            recent_failures=tc["recent_failures"],
            status_history=tc["status_history"]
        )

        classification = await agent.classify_test(flaky_test)

        is_match = classification.root_cause == tc["expected_cause"]
        if not is_match:
            all_passed = False

        status_icon = "[PASS]" if is_match else "[FAIL]"
        print(f"  Result: {status_icon}")
        print(f"  - Detected Cause : {classification.root_cause.value.upper()} (Expected: {tc['expected_cause'].value.upper()})")
        print(f"  - Confidence     : {classification.confidence.value.upper()}")
        print(f"  - Subagent Scores: {classification.metadata.get('subagent_scores', {})}")
        print(f"  - Fix Area       : {classification.suggested_fix_area}")
        print(f"  - Evidence Items : {len(classification.evidence)}")
        for ev in classification.evidence[:2]:
            line_info = f" (line {ev.line_number})" if ev.line_number else ""
            print(f"    * {ev.description}{line_info}")

        results_summary.append({
            "test": tc["test_name"],
            "detected": classification.root_cause.value,
            "expected": tc["expected_cause"].value,
            "match": is_match,
            "confidence": classification.confidence.value
        })

    print("\n" + "=" * 70)
    print(" VERIFICATION SUMMARY")
    print("=" * 70)
    for r in results_summary:
        mark = "[PASS]" if r["match"] else "[FAIL]"
        print(f"{mark} {r['test']:<42} -> {r['detected']:<14} [{r['confidence'].upper()}]")

    # Check evidence directory
    sessions = list(Path("docs/bob-sessions").glob("session_*.json"))
    print(f"\nSaved Session Artifacts in docs/bob-sessions/: {len(sessions)} JSON files recorded.")

    if all_passed:
        print("\nSUCCESS: All 4 root-cause categories accurately classified in parallel!")
        return 0
    else:
        print("\nWARNING: One or more classifications did not match expectations.")
        return 1


if __name__ == "__main__":
    code = asyncio.run(run_verification())
    sys.exit(code)
