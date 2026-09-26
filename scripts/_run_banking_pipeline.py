"""Run the full pipeline against Banking Management repo and print results table."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.harness.pipeline_service import PipelineService

BANKING_REPO = Path("c:/Projects/FlakeGuard/data/repos/Ajay-B-Acharya_Banking-management-systems_11412f8d")


async def main():
    print(f"\nRepository: {BANKING_REPO}")
    print(f"Exists: {BANKING_REPO.exists()}")
    print("Running pipeline (num_runs=5)...\n")

    result = await PipelineService.run_pipeline(
        repo_path=BANKING_REPO,
        num_runs=5,
        source_type="github",
        repo_url="https://github.com/Ajay-B-Acharya/Banking-management-systems",
        branch="main",
    )

    det = result.get("detection", {})
    cls = result.get("classifications", [])
    fixes = result.get("fixes", [])

    # Count by root cause
    cause_counts = {}
    for c in cls:
        cause = c.get("root_cause", "unknown")
        cause_counts[cause] = cause_counts.get(cause, 0) + 1

    diagnosed = sum(1 for c in cls if c.get("root_cause", "unknown") != "unknown")
    fixes_generated = len(fixes)
    fixes_validated = sum(
        1 for f in fixes
        for s in f.get("suggestions", [])
        if s.get("diff") and s["diff"].get("unified_diff")
    )

    print("=" * 60)
    print("PIPELINE RESULTS")
    print("=" * 60)
    print(f"Status               : {result.get('status')}")
    print(f"F1 detected tests    : {det.get('total_runs', 0)}")
    print(f"F1 flaky tests       : {det.get('flaky_tests_count', 0)}")
    print(f"F2 diagnosed tests   : {diagnosed} / {len(cls)}")
    print(f"  Timing/race        : {cause_counts.get('timing', 0) + cause_counts.get('race_condition', 0)}")
    print(f"  Order dependency   : {cause_counts.get('ordering', 0)}")
    print(f"  Data leakage       : {cause_counts.get('state_leakage', 0)}")
    print(f"  Environment        : {cause_counts.get('environment', 0)}")
    print(f"  Unclassified       : {cause_counts.get('unknown', 0)}")
    print(f"F3 fixes generated   : {fixes_generated}")
    print(f"F3 fixes with diffs  : {fixes_validated}")
    print()

    # Verify file_path consistency between flaky_tests and classifications
    flaky_paths = {t["test_name"]: t["file_path"] for t in det.get("flaky_tests", [])}
    cls_paths   = {c["test_name"]: c["file_path"] for c in cls}
    mismatches  = 0
    for name in flaky_paths:
        if name in cls_paths and flaky_paths[name] != cls_paths[name]:
            mismatches += 1
            print(f"  PATH MISMATCH: {name}")
            print(f"    flaky    : {flaky_paths[name]}")
            print(f"    classif  : {cls_paths[name]}")

    if mismatches == 0:
        print(f"file_path consistency : OK (0 mismatches across {len(flaky_paths)} tests)")
    else:
        print(f"file_path consistency : {mismatches} MISMATCHES — dashboard will show Unclassified")

    print()
    # Show sample classifications
    print("Sample classifications (first 5):")
    for c in cls[:5]:
        print(f"  [{c['root_cause']:15}] [{c['confidence']:6}]  {c['test_name'][:60]}")
    if result.get("errors"):
        print("\nErrors:", result["errors"])


if __name__ == "__main__":
    asyncio.run(main())
