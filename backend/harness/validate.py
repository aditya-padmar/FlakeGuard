"""Validation module for FlakeGuard acceptance gate."""
import asyncio
from pathlib import Path
import time
from typing import Dict, List, Optional

from backend.harness.analyzer import TestAnalyzer
from backend.harness.executor import TestExecutor
from backend.harness.runner import TestRunner

HARDCODED_EXPECTED_FLAKY = [
    "tests/test_timing.py::TestTimingIssues::test_worker_thread_race",
    "tests/test_order.py::TestOrderingIssues::test_depends_on_retry_limit",
    "tests/test_leakage.py::TestStateLeakage::test_expects_clean_inventory",
    "tests/test_environment.py::TestEnvironmentIssues::test_region_dependent_totals",
]

HARDCODED_EXPECTED_STABLE = [
    "tests/test_stable.py::TestStable::test_addition",
    "tests/test_stable.py::TestStable::test_subtraction",
    "tests/test_stable.py::TestStable::test_multiplication",
    "tests/test_stable.py::TestStable::test_division",
    "tests/test_stable.py::TestStable::test_divide_by_zero",
    "tests/test_stable.py::TestStable::test_clear",
    "tests/test_timing.py::TestTimingIssues::test_wait_is_deterministic_control",
    "tests/test_leakage.py::TestStateLeakage::test_inventory_roundtrip_control",
    "tests/test_environment.py::TestEnvironmentIssues::test_totals_lookup_control",
]


async def run_single_validation_pass(
    repo_path: Path,
    pass_index: int,
    num_runs: int = 10,
    expected_flaky: Optional[List[str]] = None,
    expected_stable: Optional[List[str]] = None,
    base_seed: Optional[int] = None,
) -> Dict[str, object]:
    exp_flaky = set(expected_flaky or HARDCODED_EXPECTED_FLAKY)
    exp_stable = set(expected_stable or HARDCODED_EXPECTED_STABLE)

    seed = (base_seed if base_seed is not None else 42) + pass_index * 17

    runner = TestRunner(repo_path)
    analyzer = TestAnalyzer()
    executor = TestExecutor(runner, analyzer)

    start_time = time.perf_counter()
    runs = await executor.execute_multiple_runs(
        num_runs=num_runs,
        batch_size=3,
        base_seed=seed,
    )
    detection = analyzer.analyze_runs(runs)
    elapsed = time.perf_counter() - start_time

    flagged_ids = {t.test_name for t in detection.flaky_tests}
    stable_ids = set(detection.stable_tests)

    # False positive: a test in expected_stable flagged flaky, or any test flagged not in expected_flaky
    false_positives = sorted(list(flagged_ids - exp_flaky))

    # False negative: an expected flaky test never flagged
    false_negatives = sorted(list(exp_flaky - flagged_ids))

    pass_ok = (len(false_positives) == 0 and len(false_negatives) == 0)

    return {
        "iteration": pass_index + 1,
        "seed": seed,
        "seconds": round(elapsed, 2),
        "total_runs": len(runs),
        "flaky_found": sorted(list(flagged_ids)),
        "stable_found": sorted(list(stable_ids)),
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "detection_result": detection,
        "passed": pass_ok,
    }


def validate(
    repo_path: str | Path,
    num_runs: int = 10,
    expected_flaky: Optional[List[str]] = None,
    expected_stable: Optional[List[str]] = None,
    iterations: int = 3,
    base_seed: int = 42,
) -> Dict[str, object]:
    """
    Run `iterations` independent full detection passes and validate zero false positives / negatives.
    """
    path = Path(repo_path).resolve()
    exp_flaky = expected_flaky or HARDCODED_EXPECTED_FLAKY
    exp_stable = expected_stable or HARDCODED_EXPECTED_STABLE

    results = []

    async def _run_all():
        for i in range(iterations):
            iter_res = await run_single_validation_pass(
                repo_path=path,
                pass_index=i,
                num_runs=num_runs,
                expected_flaky=exp_flaky,
                expected_stable=exp_stable,
                base_seed=base_seed,
            )
            results.append(iter_res)

    asyncio.run(_run_all())

    all_passed = all(r["passed"] for r in results) and len(results) == iterations

    return {
        "iterations": results,
        "passed": all_passed,
        "total_iterations": iterations,
        "expected_flaky": exp_flaky,
        "expected_stable": exp_stable,
    }
