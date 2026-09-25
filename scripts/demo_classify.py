#!/usr/bin/env python
"""
Interactive / CLI Live Demo for Feature F2: IBM Bob 2.0 AI Agent.

Allows judges and teammates to diagnose any test on-demand and watch
the 4 parallel subagents vote in real time.

Usage:
    python scripts/demo_classify.py [timing | order | leakage | env | <custom_test_path>]

Examples:
    python scripts/demo_classify.py timing
    python scripts/demo_classify.py sample-repo/tests/test_order.py::TestOrderingIssues::test_second
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.bob.agent import BobAgent
from backend.models.detection import FlakyTest, TestStatus

PRESETS = {
    "timing": {
        "name": "TestTimingIssues::test_sleep_based",
        "path": "sample-repo/tests/test_timing.py",
        "error": "AssertionError: assert result == 4"
    },
    "order": {
        "name": "TestOrderingIssues::test_second",
        "path": "sample-repo/tests/test_order.py",
        "error": "AssertionError: assert calc.operation_count == 1 (was 0)"
    },
    "leakage": {
        "name": "TestStateLeakage::test_global_mutation",
        "path": "sample-repo/tests/test_leakage.py",
        "error": "AssertionError: residual shared state detected"
    },
    "env": {
        "name": "TestEnvironmentIssues::test_random_failure",
        "path": "sample-repo/tests/test_network.py",
        "error": "Failed: Random failure for flaky test demonstration"
    }
}


async def main():
    target = sys.argv[1].lower() if len(sys.argv) > 1 else "timing"

    if target in PRESETS:
        preset = PRESETS[target]
        test_name = preset["name"]
        file_path = preset["path"]
        recent_error = preset["error"]
    else:
        # Custom test path
        parts = target.split("::")
        file_path = parts[0]
        test_name = parts[-1] if len(parts) > 1 else Path(file_path).stem
        recent_error = "AssertionError: test failed non-deterministically"

    print("=" * 70)
    print("  IBM Bob 2.0 Agent - Live Parallel Subagent Diagnostic")
    print("=" * 70)
    print(f"Target Test   : {test_name}")
    print(f"Test File     : {file_path}")

    agent = BobAgent()
    source = agent.extract_test_source(file_path, test_name)
    line_count = len(source.splitlines()) if source else 0
    print(f"Source Code   : {line_count} lines resolved from disk via AST parser")
    print("\nDispatching 4 Competing Subagents in Parallel (asyncio.gather)...")

    flaky_test = FlakyTest(
        test_name=test_name,
        file_path=file_path,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        total_runs=5,
        pass_count=3,
        fail_count=2,
        flake_rate=0.4,
        recent_failures=[recent_error],
        status_history=[TestStatus.PASSED, TestStatus.FAILED, TestStatus.PASSED, TestStatus.FAILED, TestStatus.PASSED]
    )

    classification = await agent.classify_test(flaky_test, source)

    scores = classification.metadata.get("subagent_scores", {})
    winning_cause = classification.root_cause.value

    print("\n" + "-" * 70)
    print("  Parallel Subagent Scoreboard:")
    print("-" * 70)
    for cause, score in scores.items():
        bar_len = int(score * 25)
        bar = "#" * bar_len + "-" * (25 - bar_len)
        crown = " <-- [WINNER]" if cause == winning_cause else ""
        print(f"  [{cause:<13}] {bar} {score:>5.1%} {crown}")

    print("\n" + "=" * 70)
    print(f"VERDICT       : {classification.root_cause.value.upper()} ({classification.confidence.value.upper()} CONFIDENCE)")
    print(f"SUGGESTED FIX : {classification.suggested_fix_area}")
    print(f"REASONING     : {classification.reasoning}")
    print(f"EVIDENCE CITED: {len(classification.evidence)} items")
    for i, ev in enumerate(classification.evidence[:3], 1):
        line = f" (line {ev.line_number})" if ev.line_number else ""
        print(f"   {i}. {ev.description}{line}")

    print("\n[Audit Trail] Session logged to docs/bob-sessions/")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
