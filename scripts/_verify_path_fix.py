"""Verification script for F1 path-resolution fix. Run from FlakeGuard root."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.harness.runner import TestRunner, normalize_pytest_target

FLAKEGUARD_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_REPO = FLAKEGUARD_ROOT / "sample-repo"
BOX_REPO = FLAKEGUARD_ROOT / "data" / "repos" / "box_flaky_fa11546c"


# ---------------------------------------------------------------------------
# Part 1: normalize_pytest_target unit checks
# ---------------------------------------------------------------------------
def check_normalize():
    print("=" * 60)
    print("Part 1: normalize_pytest_target()")
    print("=" * 60)
    repo = BOX_REPO

    cases = [
        # (raw_input, expected_output)
        (
            "data/repos/box_flaky_fa11546c/test/test_foo.py::Cls::fn",
            "test/test_foo.py::Cls::fn",
        ),
        (
            "test/test_foo.py::Cls::fn",
            "test/test_foo.py::Cls::fn",
        ),
        (
            "test/test_pytest/test_flaky_pytest_plugin.py::test_fn",
            "test/test_pytest/test_flaky_pytest_plugin.py::test_fn",
        ),
        (
            str(repo / "test" / "test_foo.py") + "::Cls::fn",
            "test/test_foo.py::Cls::fn",
        ),
        # Param-set node IDs must keep their brackets
        (
            "data/repos/box_flaky_fa11546c/test/test_pytest/test_flaky_pytest_plugin.py"
            "::test_flaky_xdist_nodedown[mock0-None-True]",
            "test/test_pytest/test_flaky_pytest_plugin.py"
            "::test_flaky_xdist_nodedown[mock0-None-True]",
        ),
    ]

    all_ok = True
    for raw, expected in cases:
        result = normalize_pytest_target(raw, repo)
        ok = result == expected
        if not ok:
            all_ok = False
        status = "OK  " if ok else "FAIL"
        print(f"  {status}: {raw[:70]!r}")
        if not ok:
            print(f"        got      {result!r}")
            print(f"        expected {expected!r}")

    print()
    return all_ok


# ---------------------------------------------------------------------------
# Part 2: box/flaky collection
# ---------------------------------------------------------------------------
def check_box_collection():
    print("=" * 60)
    print("Part 2: box/flaky – test collection")
    print("=" * 60)

    if not BOX_REPO.exists():
        print(f"SKIP: {BOX_REPO} does not exist")
        return True

    runner = TestRunner(BOX_REPO)
    ids = runner.collect_test_ids()

    print(f"Collected : {len(ids)} tests")
    if ids:
        print("First 5   :")
        for nid in ids[:5]:
            print(f"  {nid}")
        print("Last  3   :")
        for nid in ids[-3:]:
            print(f"  {nid}")

    bad = [nid for nid in ids if nid.startswith("data/") or "box_flaky_fa11546c" in nid]
    print(f"Bad paths : {len(bad)}")
    if bad:
        for b in bad[:5]:
            print(f"  {b}")

    ok = len(ids) > 0 and len(bad) == 0
    print("COLLECTION", "OK" if ok else "FAILED")
    print()
    return ok


# ---------------------------------------------------------------------------
# Part 3: box/flaky single run
# ---------------------------------------------------------------------------
def check_box_single_run():
    print("=" * 60)
    print("Part 3: box/flaky – single test run")
    print("=" * 60)

    if not BOX_REPO.exists():
        print(f"SKIP: {BOX_REPO} does not exist")
        return True

    runner = TestRunner(BOX_REPO)
    # Limit to a small, fast subset so verification doesn't take too long
    runner._collected_test_ids = None
    all_ids = runner.collect_test_ids()

    # Run only the first 10 tests for speed
    runner._collected_test_ids = all_ids[:10]
    print(f"Running first {len(runner._collected_test_ids)} tests...")

    try:
        run = runner.run_tests(run_index=0, ordering_seed=42)
        print(f"Total tests  : {run.total_tests}")
        print(f"Passed       : {run.passed}")
        print(f"Failed       : {run.failed}")
        print(f"Return code  : {run.returncode}")
        print(f"Duration     : {run.duration_seconds:.2f}s")
        if run.executions:
            print("Sample executions:")
            for ex in run.executions[:5]:
                print(f"  [{ex.status.value:8}] {ex.test_name}")

        ok = run.total_tests > 0
        print("SINGLE RUN", "OK" if ok else "FAILED (zero executions)")
        print()
        return ok
    except Exception as exc:
        print(f"SINGLE RUN FAILED: {exc}")
        print()
        return False


# ---------------------------------------------------------------------------
# Part 4: sample-repo collection + single run
# ---------------------------------------------------------------------------
def check_sample_repo():
    print("=" * 60)
    print("Part 4: sample-repo – collection + single run")
    print("=" * 60)

    runner = TestRunner(SAMPLE_REPO)
    ids = runner.collect_test_ids()
    print(f"Collected : {len(ids)} tests")
    if ids:
        for nid in ids[:5]:
            print(f"  {nid}")

    if not ids:
        print("SAMPLE COLLECTION FAILED")
        return False

    try:
        run = runner.run_tests(run_index=0, ordering_seed=0)
        print(f"Total tests : {run.total_tests}")
        print(f"Passed      : {run.passed}")
        print(f"Failed      : {run.failed}")
        print(f"Return code : {run.returncode}")
        ok = run.total_tests > 0
        print("SAMPLE RUN", "OK" if ok else "FAILED")
        print()
        return ok
    except Exception as exc:
        print(f"SAMPLE RUN FAILED: {exc}")
        print()
        return False


# ---------------------------------------------------------------------------
# Part 5: FlakeGuard itself (regression – must still work)
# ---------------------------------------------------------------------------
def check_flakeguard_own():
    print("=" * 60)
    print("Part 5: FlakeGuard own suite – collection (_is_flakeguard_repo)")
    print("=" * 60)

    runner = TestRunner(FLAKEGUARD_ROOT)
    assert runner._is_flakeguard_repo, "_is_flakeguard_repo should be True"

    ids = runner.collect_test_ids()
    print(f"Collected : {len(ids)} tests")
    if ids:
        for nid in ids[:5]:
            print(f"  {nid}")

    ok = len(ids) > 0
    print("OWN SUITE COLLECTION", "OK" if ok else "FAILED")
    print()
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    results = {
        "normalize_pytest_target": check_normalize(),
        "box/flaky collection": check_box_collection(),
        "box/flaky single run": check_box_single_run(),
        "sample-repo": check_sample_repo(),
        "FlakeGuard own suite": check_flakeguard_own(),
    }

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"  {status}  {name}")

    print()
    if all_passed:
        print("All checks passed.")
        sys.exit(0)
    else:
        print("Some checks FAILED.")
        sys.exit(1)
