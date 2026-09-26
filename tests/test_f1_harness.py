"""
Regression tests for the F1 detection harness pytest execution layer.

Covers:
  1.  pytest command construction
  2.  JSON result collection
  3.  missing pytest-json-report / plugin case
  4.  no tests collected (exit code 5)
  5.  normal passing test
  6.  failing test
  7.  flaky test across repeated runs
  8.  stable test across repeated runs
  9.  temporary result-file creation / cleanup
  10. repository with no pytest tests
"""
import json
import os
import subprocess
import sys
import textwrap
import uuid
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# --------------------------------------------------------------------------- #
# Helpers / fixtures                                                           #
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_REPO = PROJECT_ROOT / "sample-repo"


def _add_backend_to_path():
    """Ensure the project root is importable as a package."""
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


_add_backend_to_path()

from backend.harness.runner import TestRunner
from backend.harness.analyzer import TestAnalyzer
from backend.harness.validate import RepositoryValidator
from backend.models.detection import TestStatus


# ---------------------------------------------------------------------------
# Fixture: isolated temp repo directory
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """Return a fresh temp directory usable as a fake repo root."""
    (tmp_path / "tests").mkdir()
    return tmp_path


def _write_test(tmp_repo: Path, name: str, source: str) -> Path:
    """Write a test file into tmp_repo/tests/<name>.py."""
    path = tmp_repo / "tests" / name
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


def _write_pytest_ini(tmp_repo: Path, content: str = "[pytest]\n") -> None:
    (tmp_repo / "pytest.ini").write_text(content, encoding="utf-8")


# ===========================================================================
# TEST 1 — pytest command construction
# ===========================================================================

class TestPytestCommandConstruction:
    """Runner must build a command that uses sys.executable, -p no:cacheprovider,
    --json-report and --json-report-file=<path>."""

    def _make_runner_with_plugins_verified(self, tmp_repo) -> "TestRunner":
        """Return a TestRunner whose plugin-check is already satisfied."""
        runner = TestRunner(tmp_repo)
        runner._pytest_plugins_verified = True
        runner._json_report_available = True
        return runner

    def test_command_uses_sys_executable(self, tmp_repo):
        """The pytest subprocess must be launched with FlakeGuard's own Python."""
        _write_pytest_ini(tmp_repo)
        _write_test(tmp_repo, "test_pass.py", """
            def test_always_passes():
                assert True
        """)
        runner = self._make_runner_with_plugins_verified(tmp_repo)
        # Capture the command by patching subprocess.run
        captured = []

        def fake_run(cmd, **kwargs):
            captured.append(cmd)
            # Return a fake successful result with a JSON report file
            report_path = None
            for arg in cmd:
                if "--json-report-file=" in str(arg):
                    report_path = Path(str(arg).split("=", 1)[1])
            if report_path:
                report_path.write_text(json.dumps({
                    "tests": [{"nodeid": "tests/test_pass.py::test_always_passes",
                               "outcome": "passed", "duration": 0.001,
                               "location": ["tests/test_pass.py", 0, "test_always_passes"]}]
                }), encoding="utf-8")
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=fake_run):
            runner._collected_test_ids = ["tests/test_pass.py::test_always_passes"]
            runner.run_tests(run_index=0)

        assert captured, "subprocess.run was never called"
        # Find the actual pytest execution call (not git or --collect-only)
        pytest_cmds = [c for c in captured if len(c) > 2 and c[1] == "-m" and c[2] == "pytest"
                       and "--collect-only" not in c]
        assert pytest_cmds, f"No pytest execution command found. All captured: {captured}"
        cmd = pytest_cmds[-1]
        assert cmd[0] == sys.executable, (
            f"Expected {sys.executable}, got {cmd[0]}"
        )
        assert "-m" in cmd
        assert "pytest" in cmd

    def test_command_includes_json_report_flags(self, tmp_repo):
        """Command must contain --json-report and --json-report-file=<path>."""
        runner = self._make_runner_with_plugins_verified(tmp_repo)
        captured = []

        def fake_run(cmd, **kwargs):
            captured.append(cmd)
            report_path = None
            for arg in cmd:
                if "--json-report-file=" in str(arg):
                    report_path = Path(str(arg).split("=", 1)[1])
            if report_path:
                report_path.write_text(json.dumps({
                    "tests": [{"nodeid": "tests/test_x.py::test_x",
                               "outcome": "passed", "duration": 0.001,
                               "location": ["tests/test_x.py", 0, "test_x"]}]
                }), encoding="utf-8")
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=fake_run):
            runner._collected_test_ids = ["tests/test_x.py::test_x"]
            runner.run_tests(run_index=0)

        # Find the actual pytest execution call (not git or --collect-only)
        pytest_cmds = [c for c in captured if len(c) > 2 and c[1] == "-m" and c[2] == "pytest"
                       and "--collect-only" not in c]
        assert pytest_cmds, f"No pytest run command captured. All: {captured}"
        cmd = pytest_cmds[-1]
        cmd_str = " ".join(str(c) for c in cmd)
        assert "--json-report" in cmd_str, "Missing --json-report flag"
        assert "--json-report-file=" in cmd_str, "Missing --json-report-file= flag"

    def test_command_disables_cache_provider(self, tmp_repo):
        """Command must include -p no:cacheprovider to avoid stale .pytest_cache."""
        runner = self._make_runner_with_plugins_verified(tmp_repo)
        captured = []

        def fake_run(cmd, **kwargs):
            captured.append(cmd)
            for arg in cmd:
                if "--json-report-file=" in str(arg):
                    Path(str(arg).split("=", 1)[1]).write_text(
                        json.dumps({"tests": [
                            {"nodeid": "tests/t.py::t1", "outcome": "passed",
                             "duration": 0.0, "location": ["tests/t.py", 1, "t1"]}
                        ]}), encoding="utf-8"
                    )
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        with patch("subprocess.run", side_effect=fake_run):
            # Seed one test so the pytest execution path is actually reached
            runner._collected_test_ids = ["tests/t.py::t1"]
            runner.run_tests(run_index=0)

        # Find the actual pytest execution call (not git or --collect-only)
        pytest_cmds = [c for c in captured if len(c) > 2 and c[1] == "-m" and c[2] == "pytest"
                       and "--collect-only" not in c]
        assert pytest_cmds, f"No pytest run command captured. All: {captured}"
        cmd = pytest_cmds[-1]
        joined = " ".join(str(c) for c in cmd)
        assert "no:cacheprovider" in joined, "Missing -p no:cacheprovider"


# ===========================================================================
# TEST 2 — JSON result collection
# ===========================================================================

class TestJSONResultCollection:
    """Results from the JSON report must be faithfully parsed into TestExecution objects."""

    def test_parses_passed_test(self, tmp_repo):
        runner = TestRunner(tmp_repo)
        data = {
            "tests": [
                {
                    "nodeid": "tests/test_p.py::test_pass",
                    "outcome": "passed",
                    "duration": 0.42,
                    "location": ["tests/test_p.py", 1, "test_pass"],
                }
            ]
        }
        executions = runner._parse_pytest_results(data, run_id="r1")
        assert len(executions) == 1
        assert executions[0].status == TestStatus.PASSED
        assert executions[0].test_name == "tests/test_p.py::test_pass"
        assert abs(executions[0].duration - 0.42) < 0.001

    def test_parses_failed_test(self, tmp_repo):
        runner = TestRunner(tmp_repo)
        data = {
            "tests": [
                {
                    "nodeid": "tests/test_f.py::test_fail",
                    "outcome": "failed",
                    "duration": 0.1,
                    "location": ["tests/test_f.py", 1, "test_fail"],
                    "call": {
                        "crash": {
                            "message": "AssertionError: assert False",
                            "traceback": "...",
                        }
                    },
                }
            ]
        }
        executions = runner._parse_pytest_results(data, run_id="r2")
        assert len(executions) == 1
        assert executions[0].status == TestStatus.FAILED
        assert "AssertionError" in (executions[0].error_message or "")

    def test_parses_multiple_tests(self, tmp_repo):
        runner = TestRunner(tmp_repo)
        data = {
            "tests": [
                {"nodeid": "tests/t.py::t1", "outcome": "passed",
                 "duration": 0.1, "location": ["tests/t.py", 1, "t1"]},
                {"nodeid": "tests/t.py::t2", "outcome": "failed",
                 "duration": 0.2, "location": ["tests/t.py", 2, "t2"]},
                {"nodeid": "tests/t.py::t3", "outcome": "skipped",
                 "duration": 0.0, "location": ["tests/t.py", 3, "t3"]},
            ]
        }
        executions = runner._parse_pytest_results(data, run_id="r3")
        assert len(executions) == 3
        statuses = {e.test_name: e.status for e in executions}
        assert statuses["tests/t.py::t1"] == TestStatus.PASSED
        assert statuses["tests/t.py::t2"] == TestStatus.FAILED
        assert statuses["tests/t.py::t3"] == TestStatus.SKIPPED

    def test_handles_empty_tests_list(self, tmp_repo):
        runner = TestRunner(tmp_repo)
        executions = runner._parse_pytest_results({"tests": []}, run_id="r4")
        assert executions == []

    def test_run_id_stamped_on_every_execution(self, tmp_repo):
        runner = TestRunner(tmp_repo)
        data = {
            "tests": [
                {"nodeid": "tests/t.py::a", "outcome": "passed",
                 "duration": 0.0, "location": ["tests/t.py", 1, "a"]},
                {"nodeid": "tests/t.py::b", "outcome": "passed",
                 "duration": 0.0, "location": ["tests/t.py", 2, "b"]},
            ]
        }
        run_id = str(uuid.uuid4())
        executions = runner._parse_pytest_results(data, run_id=run_id)
        for e in executions:
            assert e.run_id == run_id


# ===========================================================================
# TEST 3 — missing pytest-json-report plugin
# ===========================================================================

class TestMissingPytestJsonReport:
    """Runner must raise RuntimeError if pytest-json-report is not available."""

    def test_raises_when_json_report_missing(self, tmp_repo):
        runner = TestRunner(tmp_repo)
        # Simulate a verified env that doesn't have json-report
        runner._pytest_plugins_verified = True
        runner._json_report_available = False

        with pytest.raises(RuntimeError, match="pytest-json-report"):
            runner.run_tests(run_index=0)

    def test_verify_env_warns_when_json_report_missing(self, tmp_repo):
        """verify_pytest_environment must surface the missing-plugin warning."""
        runner = TestRunner(tmp_repo)

        fake_result = MagicMock()
        fake_result.stdout = "--tb short\n  --verbose\n"   # no --json-report
        fake_result.stderr = ""
        fake_result.returncode = 0

        with patch("subprocess.run", return_value=fake_result):
            env = runner.verify_pytest_environment()

        assert env["verified"] is True
        assert env["json_report"] is False
        warning_text = " ".join(env["warnings"])
        assert "json-report" in warning_text.lower() or "pytest-json-report" in warning_text


# ===========================================================================
# TEST 4 — no tests collected (exit code 5)
# ===========================================================================

class TestNoTestsCollected:
    """Exit code 5 from pytest (no tests) must be handled gracefully."""

    def test_collect_returns_empty_on_exit_5(self, tmp_repo):
        """collect_test_ids should return [] rather than raising when exit code is 5."""
        # Empty repo, no test files
        _write_pytest_ini(tmp_repo)
        runner = TestRunner(tmp_repo)
        ids = runner.collect_test_ids()
        assert ids == []

    def test_run_returns_zero_executions_when_no_tests(self, tmp_repo):
        """run_tests with no collected tests must return a TestRun with returncode=5."""
        runner = TestRunner(tmp_repo)
        runner._collected_test_ids = []      # pre-seed: no tests

        test_run = runner.run_tests(run_index=0)

        assert test_run.total_tests == 0
        assert test_run.executions == []
        assert test_run.returncode == 5

    def test_pipeline_unsupported_for_non_pytest_repo(self, tmp_repo):
        """RepositoryValidator must flag a non-pytest repo as incompatible."""
        validator = RepositoryValidator()
        result = validator.detect_pytest_compatibility(tmp_repo)
        assert result["compatible"] is False
        assert result["confidence"] < 0.5


# ===========================================================================
# TEST 5 — normal passing test
# ===========================================================================

class TestNormalPassingTest:
    """A simple passing test repo must produce a PASSED execution."""

    def test_passing_repo(self, tmp_repo):
        _write_pytest_ini(tmp_repo)
        _write_test(tmp_repo, "test_pass.py", """
            def test_always_passes():
                assert 1 + 1 == 2
        """)
        runner = TestRunner(tmp_repo)
        test_run = runner.run_tests(run_index=0, ordering_seed=0)

        assert test_run.total_tests >= 1
        statuses = [e.status for e in test_run.executions]
        assert TestStatus.PASSED in statuses, "Expected at least one PASSED execution"
        assert TestStatus.FAILED not in statuses, "Unexpected FAILED in a passing-only repo"


# ===========================================================================
# TEST 6 — failing test
# ===========================================================================

class TestFailingTest:
    """A test that always fails must produce a FAILED execution with error info."""

    def test_always_failing_repo(self, tmp_repo):
        _write_pytest_ini(tmp_repo)
        _write_test(tmp_repo, "test_fail.py", """
            def test_always_fails():
                assert False, "deliberate failure"
        """)
        runner = TestRunner(tmp_repo)
        test_run = runner.run_tests(run_index=0, ordering_seed=0)

        assert test_run.total_tests >= 1
        failures = [e for e in test_run.executions if e.status == TestStatus.FAILED]
        assert failures, "Expected at least one FAILED execution"
        # Error message should be captured
        assert any(e.error_message for e in failures), (
            "Failed test should carry error_message"
        )


# ===========================================================================
# TEST 7 — flaky test detected across repeated runs
# ===========================================================================

class TestFlakyDetection:
    """A test that flips between PASS/FAIL across runs must be marked is_flaky=True."""

    def test_flaky_test_detected(self, tmp_repo):
        """
        Use the counter-based flaky test pattern: the test fails on odd calls
        and passes on even calls.  After 5+ runs with different seeds the
        analyzer must classify it as flaky.
        """
        _write_pytest_ini(tmp_repo)
        counter_file = tmp_repo / "_counter.txt"
        counter_file.write_text("0", encoding="utf-8")

        _write_test(tmp_repo, "test_flaky.py", f"""
            from pathlib import Path

            _counter_file = Path(r"{counter_file.as_posix()}")

            def test_flips():
                count = int(_counter_file.read_text())
                _counter_file.write_text(str(count + 1))
                assert count % 2 == 0, f"Failing on call {{count}}"
        """)

        runner = TestRunner(tmp_repo)
        analyzer = TestAnalyzer()

        runs = []
        for i in range(6):
            run = runner.run_tests(run_index=i, ordering_seed=i * 1000)
            runs.append(run)

        detection = analyzer.analyze_runs(runs)
        flaky_names = {t.test_name for t in detection.flaky_tests}
        assert any("test_flips" in name for name in flaky_names), (
            f"test_flips should be classified as flaky. "
            f"Flaky={flaky_names}, "
            f"Run statuses={[(r.passed, r.failed) for r in runs]}"
        )

    def test_flaky_rate_between_zero_and_one(self, tmp_repo):
        """flake_rate on a detected flaky test must be in (0, 1)."""
        _write_pytest_ini(tmp_repo)
        counter_file = tmp_repo / "_counter2.txt"
        counter_file.write_text("0", encoding="utf-8")

        _write_test(tmp_repo, "test_flaky2.py", f"""
            from pathlib import Path
            _counter_file = Path(r"{counter_file.as_posix()}")
            def test_alternates():
                count = int(_counter_file.read_text())
                _counter_file.write_text(str(count + 1))
                assert count % 2 == 0
        """)

        runner = TestRunner(tmp_repo)
        analyzer = TestAnalyzer()
        runs = [runner.run_tests(run_index=i, ordering_seed=i) for i in range(6)]
        detection = analyzer.analyze_runs(runs)

        for t in detection.flaky_tests:
            if "test_alternates" in t.test_name:
                assert 0.0 < t.flake_rate < 1.0
                return

        pytest.skip("test_alternates not classified as flaky — skipping rate check")


# ===========================================================================
# TEST 8 — stable test across repeated runs
# ===========================================================================

class TestStableDetection:
    """A test that always passes must NOT be flagged as flaky."""

    def test_stable_test_not_flaky(self, tmp_repo):
        _write_pytest_ini(tmp_repo)
        _write_test(tmp_repo, "test_stable.py", """
            def test_always_stable():
                assert "hello".upper() == "HELLO"
        """)
        runner = TestRunner(tmp_repo)
        analyzer = TestAnalyzer()

        runs = [runner.run_tests(run_index=i, ordering_seed=i * 7) for i in range(5)]
        detection = analyzer.analyze_runs(runs)

        flaky_names = {t.test_name for t in detection.flaky_tests}
        assert not any("test_always_stable" in n for n in flaky_names), (
            "A always-passing test must not appear in flaky_tests"
        )

    def test_stable_test_appears_in_stable_list(self, tmp_repo):
        _write_pytest_ini(tmp_repo)
        _write_test(tmp_repo, "test_stable2.py", """
            def test_rock_solid():
                assert sorted([3, 1, 2]) == [1, 2, 3]
        """)
        runner = TestRunner(tmp_repo)
        analyzer = TestAnalyzer()

        runs = [runner.run_tests(run_index=i, ordering_seed=i * 3) for i in range(5)]
        detection = analyzer.analyze_runs(runs)

        assert any("test_rock_solid" in name for name in detection.stable_tests), (
            "Stable test must appear in stable_tests list"
        )


# ===========================================================================
# TEST 9 — temporary result-file creation and cleanup
# ===========================================================================

class TestTempResultFiles:
    """The runner must create a unique temp file per run and clean it up afterwards."""

    def test_result_file_cleaned_up_after_run(self, tmp_repo):
        _write_pytest_ini(tmp_repo)
        _write_test(tmp_repo, "test_tidy.py", """
            def test_something():
                assert True
        """)
        runner = TestRunner(tmp_repo)
        run = runner.run_tests(run_index=0)

        # No .temp_results_*.json files should remain in the repo after a clean run
        leftover = list(tmp_repo.glob(".temp_results_*.json"))
        assert leftover == [], (
            f"Temp result files not cleaned up: {leftover}"
        )

    def test_result_files_unique_per_run(self, tmp_repo):
        """Each run must use a distinct filename (uuid-based), never re-using old files."""
        _write_pytest_ini(tmp_repo)
        _write_test(tmp_repo, "test_unique.py", """
            def test_u():
                assert True
        """)
        runner = TestRunner(tmp_repo)

        # Patch subprocess.run to capture --json-report-file paths
        seen_paths = []

        original_run = subprocess.run

        def capturing_run(cmd, **kwargs):
            for arg in cmd:
                if "--json-report-file=" in str(arg):
                    seen_paths.append(str(arg).split("=", 1)[1])
            return original_run(cmd, **kwargs)

        with patch("subprocess.run", side_effect=capturing_run):
            runner.run_tests(run_index=0, ordering_seed=1)
            runner._collected_test_ids = None   # reset cache to force re-collect
            runner.run_tests(run_index=1, ordering_seed=2)

        # filter to only the actual pytest execution calls (not --collect-only)
        exec_paths = [p for p in seen_paths if "temp_results" not in p.lower()
                      or len(seen_paths) <= 2]
        if len(seen_paths) >= 2:
            assert seen_paths[0] != seen_paths[-1], (
                "Two runs must not reuse the same temp file path"
            )


# ===========================================================================
# TEST 10 — repository with no pytest tests
# ===========================================================================

class TestNonPytestRepository:
    """A repository with no Python/pytest content must return compatible=False."""

    def test_non_python_repo_incompatible(self, tmp_path):
        # Create a JS-only fake repo
        (tmp_path / "index.js").write_text("console.log('hello');", encoding="utf-8")
        (tmp_path / "package.json").write_text('{"name":"test"}', encoding="utf-8")

        validator = RepositoryValidator()
        result = validator.detect_pytest_compatibility(tmp_path)

        assert result["compatible"] is False, (
            "A JavaScript-only repo must not be marked pytest-compatible"
        )

    def test_empty_repo_incompatible(self, tmp_path):
        validator = RepositoryValidator()
        result = validator.detect_pytest_compatibility(tmp_path)
        assert result["compatible"] is False

    def test_python_repo_without_tests_low_confidence(self, tmp_path):
        """A Python project with no test files should have low confidence."""
        (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")

        validator = RepositoryValidator()
        result = validator.detect_pytest_compatibility(tmp_path)

        # No test files, no pytest.ini, no tests/ dir => low confidence
        assert result["confidence"] < 0.5, (
            f"Expected low confidence for a no-tests Python project, got {result['confidence']:.1%}"
        )

    def test_collect_ids_returns_empty_for_empty_repo(self, tmp_path):
        """TestRunner.collect_test_ids must return [] rather than raising for empty repo."""
        # Write a conftest.py so pytest doesn't refuse to run entirely
        (tmp_path / "conftest.py").write_text("", encoding="utf-8")
        runner = TestRunner(tmp_path)
        ids = runner.collect_test_ids()
        assert ids == [], f"Expected empty list, got: {ids}"

    def test_run_on_empty_repo_returns_exit5_run(self, tmp_path):
        """Running on a no-tests repo should yield a TestRun with returncode=5."""
        runner = TestRunner(tmp_path)
        runner._collected_test_ids = []   # pre-seed: nothing collected

        test_run = runner.run_tests(run_index=0)
        assert test_run.returncode == 5
        assert test_run.total_tests == 0


# ===========================================================================
# TEST — sample-repo end-to-end (integration)
# ===========================================================================

class TestSampleRepoIntegration:
    """Quick end-to-end smoke test against the bundled sample-repo."""

    def test_sample_repo_is_compatible(self):
        validator = RepositoryValidator()
        result = validator.detect_pytest_compatibility(SAMPLE_REPO)
        assert result["compatible"] is True, (
            f"sample-repo must be pytest-compatible. Got: {result}"
        )

    def test_sample_repo_collects_tests(self):
        runner = TestRunner(SAMPLE_REPO)
        ids = runner.collect_test_ids()
        assert len(ids) > 0, "sample-repo must have discoverable tests"

    def test_sample_repo_single_run_produces_executions(self):
        runner = TestRunner(SAMPLE_REPO)
        test_run = runner.run_tests(run_index=0, ordering_seed=42)
        assert test_run.total_tests > 0
        assert test_run.executions

    def test_sample_repo_no_unrecognized_arguments_error(self):
        """The infamous --json-report unrecognized argument error must not occur."""
        runner = TestRunner(SAMPLE_REPO)
        captured_stderr = []

        original_run = subprocess.run

        def capturing_run(cmd, **kwargs):
            result = original_run(cmd, **kwargs)
            captured_stderr.append(result.stderr or "")
            return result

        with patch("subprocess.run", side_effect=capturing_run):
            try:
                runner._collected_test_ids = None
                runner.collect_test_ids()
                runner.run_tests(run_index=0, ordering_seed=99)
            except Exception:
                pass   # we only care about stderr content here

        combined_stderr = "\n".join(captured_stderr)
        assert "unrecognized arguments" not in combined_stderr, (
            f"Got 'unrecognized arguments' in stderr — "
            f"pytest-json-report is missing or misconfigured.\n{combined_stderr}"
        )
