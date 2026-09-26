# F1 Harness Fix — pytest Execution Layer

## Root Cause

The F1 detection harness invoked pytest with:

```
python -m pytest ... --json-report --json-report-file=<path>
```

but `pytest-json-report` was **not installed** in the FlakeGuard Python environment — it was listed in `requirements.txt` but never actually installed (`pip install -r requirements.txt` had not been run). Pytest therefore rejected the unknown CLI arguments:

```
ERROR: usage: python -m pytest [options] [file_or_dir] ...
error: unrecognized arguments: --json-report --json-report-file=...
```

This caused every repository analysis to fail at the very first run, before any test was executed.

---

## Files Changed

| File | Change |
|---|---|
| `backend/harness/runner.py` | Plugin verification, graceful no-tests handling, Windows file-cleanup fix, improved error messages |
| `backend/harness/validate.py` | **New** — `RepositoryValidator` for pytest-compatibility detection |
| `backend/harness/pipeline_service.py` | Runs compatibility check before F1; returns `"unsupported"` for non-pytest repos |
| `tests/test_f1_harness.py` | **New** — 30 regression tests covering all 10 required scenarios |
| `requirements.txt` | Already correct (`pytest-json-report>=1.5.0`); packages now installed |

F2, F3, F4 and all frontend files are **unchanged**.

---

## Dependencies

### Added to environment (pip install)

```
pytest-json-report==1.5.0
pytest-asyncio==1.4.0
pytest-xdist==3.8.0
pytest-random-order==1.2.0
```

These were already listed in `requirements.txt`. The fix ensures they are present in the active environment.

### Whether pytest-json-report is still required

**Yes.** The harness uses `--json-report` and `--json-report-file=<path>` to collect structured per-test results (PASSED / FAILED / SKIPPED, duration, crash message, traceback) from each run. These are required for F1's repeated-run flakiness detection. No external plugin is installed into the *target* repository — FlakeGuard's own environment provides the plugin.

---

## Exact Pytest Execution Command

```
<FlakeGuard python.exe> -m pytest
  -p backend.harness.pytest_compat
  -p no:cacheprovider
  --tb=short
  -v
  --json-report
  --json-report-file=<repo_root>/.temp_results_<uuid>.json
  [test_node_ids...]
```

Key properties:
- Always uses `sys.executable` (FlakeGuard's own Python, never the system `pytest`).
- `PYTHONPATH` includes the FlakeGuard project root so `backend.*` is importable.
- `FG_RUN_INDEX`, `FG_ORDERING_SEED`, `FG_JITTER_MS` are stamped into the child environment.
- Result file is a UUID-named temp file inside `<repo_root>/` — written by pytest-json-report, read by the harness, then deleted.

---

## What Each Fix Does

### 1 — pytest plugin verification (`runner.py`)

`TestRunner.verify_pytest_environment()` is called before every `collect_test_ids()` and `run_tests()`. It:
- Imports `pytest` to get the version.
- Runs `python -m pytest --help` and checks for `--json-report` in the output.
- Returns a dict with `verified`, `json_report`, `pytest_version`, `python_executable`, `warnings`.
- Caches the result after first call (no overhead on repeated runs).

If `json_report` is `False`, `run_tests()` raises `RuntimeError` with an install hint before ever launching a subprocess.

### 2 — No tests collected (exit code 5)

Pytest returns exit code 5 when it finds no tests. Both collection and execution now handle this:

- `collect_test_ids()`: returns `[]` instead of raising.
- `run_tests()`: if `_collected_test_ids` is empty, returns a `TestRun` with `returncode=5`, `total_tests=0`, `executions=[]` without calling pytest at all.

### 3 — Repository compatibility detection (`validate.py`)

`RepositoryValidator.detect_pytest_compatibility(repo_path)` scans for pytest indicators before any test execution:

- `pytest.ini`, `pyproject.toml`, `setup.cfg` (config files)
- `tests/`, `test/` directories
- `test_*.py` / `*_test.py` files
- `conftest.py`
- `pytest` in `requirements.txt`

Returns `{"compatible": bool, "confidence": float, "indicators": [...], "warnings": [...]}`.  
Confidence ≥ 0.5 → compatible.

### 4 — Pipeline short-circuits for incompatible repos (`pipeline_service.py`)

Before starting F1, `PipelineService.run_pipeline()` calls `RepositoryValidator`. If `compatible=False`, it immediately returns:

```json
{
  "status": "unsupported",
  "message": "Repository does not appear to be pytest-compatible...",
  "flaky_tests": [],
  ...
}
```

No pytest subprocess is ever launched against a non-Python/non-pytest repository.

### 5 — Windows file-cleanup fix (`runner.py`)

On Windows, a file cannot be deleted while a file handle is open. The original code called `report_file.unlink()` inside the `finally` of the `with open(...) as f:` block — while `f` was still open. The fix moves `unlink()` outside and after the `with` block.

### 6 — Missing plugin error messages

If a target repository's `pytest.ini` references a plugin that is not installed (e.g., `asyncio_mode = auto` without `pytest-asyncio`), pytest emits a `PytestConfigWarning`. FlakeGuard does **not** modify the target repository. The warning appears in the captured stderr and is surfaced in the error message returned to the API caller.

---

## How F1 Determines a Flaky Test

The `TestAnalyzer.analyze_runs(runs)` method aggregates `TestExecution` objects across all `N` runs:

1. For each test, count `pass_count` and `fail_count` across all runs.
2. Compute `flake_rate = fail_count / total_runs`.
3. A test is **flaky** if it has at least one pass **and** at least one failure (`0 < flake_rate < 1.0`).
4. A test is **stable** if it never failed across all runs.

The repeated-run plan (`TestExecutor.build_run_plan`) injects controlled variation:
- Randomised test ordering (different seed each run)
- Environment chaos (`SALES_REGION=EU` on ~50% of runs)
- Jitter (sleep before launch)
- Parallel execution on every 3rd run

An early-stop check terminates the run plan once every discovered test has been conclusively classified as flaky or stable.

---

## Test Results

```
tests/test_f1_harness.py — 30/30 passed (42.93s)

TestPytestCommandConstruction      3/3   ✓
TestJSONResultCollection           5/5   ✓
TestMissingPytestJsonReport        2/2   ✓
TestNoTestsCollected               3/3   ✓
TestNormalPassingTest              1/1   ✓
TestFailingTest                    1/1   ✓
TestFlakyDetection                 2/2   ✓
TestStableDetection                2/2   ✓
TestTempResultFiles                2/2   ✓
TestNonPytestRepository            5/5   ✓
TestSampleRepoIntegration          4/4   ✓
```

### Manual validation

| Repository | Result |
|---|---|
| `c:\Projects\FlakeGuard` | 57 tests collected, environment verified |
| `sample-repo` | 15 tests collected, 13 passed / 2 failed in single run |
| Empty temp dir | `compatible=False`, `returncode=5`, no crash |

---

## Pipeline Integrity

The full pipeline is preserved:

```
Repository
    ↓ RepositoryValidator (new — pre-flight check)
    ↓ F1: TestRunner + TestExecutor + TestAnalyzer
    ↓ F2: BobAgent classification
    ↓ F3: FixGenerator remediation
    ↓ F4: Auditor quarantine/CI audit
    ↓ FastAPI → Dashboard
```

F2, F3, F4, and the frontend are **not modified**.
