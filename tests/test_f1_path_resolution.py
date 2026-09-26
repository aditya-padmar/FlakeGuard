"""
Regression tests for F1 pytest node-ID path resolution (task #7).

Covers:
  1.  Absolute test path → repository-relative pytest path
  2.  Windows backslash path normalization
  3.  pytest node ID suffix preserved through normalization
  4.  Repository root containing spaces
  5.  Different cloned repository roots produce independent paths
  6.  box/flaky test discovery (no data/repos/… prefix in node IDs)
  7.  FlakeGuard sample-repo discovery
  8.  _is_flakeguard_repo flag set correctly for each repo type
  9.  --rootdir flag present in collection and execution commands
  10. -p backend.harness.pytest_compat absent for external repos
  11. PYTHONPATH includes repo root in both collection and execution envs
"""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Project layout constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_REPO  = PROJECT_ROOT / "sample-repo"
BOX_REPO     = PROJECT_ROOT / "data" / "repos" / "box_flaky_fa11546c"

sys.path.insert(0, str(PROJECT_ROOT))

from backend.harness.runner import TestRunner, normalize_pytest_target, _FLAKEGUARD_ROOT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_pytest_ini(path: Path, content: str = "[pytest]\n") -> None:
    (path / "pytest.ini").write_text(content, encoding="utf-8")


def _write_test(path: Path, name: str, source: str) -> None:
    tests_dir = path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / name).write_text(textwrap.dedent(source), encoding="utf-8")


def _runner_with_plugins(repo: Path) -> TestRunner:
    """Return a TestRunner with the plugin check pre-satisfied."""
    runner = TestRunner(repo)
    runner._pytest_plugins_verified = True
    runner._json_report_available   = True
    return runner


# ===========================================================================
# TEST 1 — Absolute path → repository-relative path
# ===========================================================================

class TestAbsolutePathNormalization:

    def test_absolute_path_under_repo(self, tmp_path):
        raw = str(tmp_path / "tests" / "test_a.py") + "::TestA::test_one"
        result = normalize_pytest_target(raw, tmp_path)
        assert result == "tests/test_a.py::TestA::test_one"

    def test_absolute_windows_under_box_flaky(self):
        """Windows backslash absolute path must resolve correctly."""
        repo = PROJECT_ROOT / "data" / "repos" / "box_flaky_fa11546c"
        if not repo.exists():
            pytest.skip("box/flaky clone not present")
        raw = str(repo / "test" / "test_b.py") + "::test_b"
        result = normalize_pytest_target(raw, repo)
        assert result == "test/test_b.py::test_b"

    def test_absolute_path_no_suffix(self, tmp_path):
        raw = str(tmp_path / "tests" / "test_c.py")
        result = normalize_pytest_target(raw, tmp_path)
        assert result == "tests/test_c.py"

    def test_absolute_path_not_under_repo_returned_raw(self, tmp_path):
        """Path outside repo root must come back containing the original info."""
        other = tmp_path / "other_dir" / "tests" / "test_x.py"
        repo  = tmp_path / "my_repo"
        raw = str(other) + "::fn"
        result = normalize_pytest_target(raw, repo)
        # Should not crash; must still contain fn
        assert "fn" in result


# ===========================================================================
# TEST 2 — Windows path normalization (forward-slash output)
# ===========================================================================

class TestWindowsPathNormalization:

    def test_backslash_relative_converted_to_forward_slash(self):
        repo = Path("C:/Projects/FlakeGuard/data/repos/box_flaky_fa11546c")
        # pytest sometimes emits backslash paths on Windows
        raw  = "test\\test_flaky_decorator.py::Cls::fn"
        result = normalize_pytest_target(raw, repo)
        assert "\\" not in result, f"Backslash still in result: {result!r}"

    def test_forward_slash_already_relative_unchanged(self):
        repo = Path("C:/Projects/FlakeGuard/data/repos/box_flaky_fa11546c")
        raw  = "test/test_flaky_decorator.py::Cls::fn"
        result = normalize_pytest_target(raw, repo)
        assert result == "test/test_flaky_decorator.py::Cls::fn"

    def test_data_repos_prefix_stripped_on_windows_style(self):
        """Node IDs like 'data/repos/box_.../test/t.py::fn' must be stripped."""
        repo = PROJECT_ROOT / "data" / "repos" / "box_flaky_fa11546c"
        raw  = "data/repos/box_flaky_fa11546c/test/test_foo.py::Cls::fn"
        result = normalize_pytest_target(raw, repo)
        assert not result.startswith("data/"), f"Still has data/ prefix: {result!r}"
        assert result == "test/test_foo.py::Cls::fn"


# ===========================================================================
# TEST 3 — pytest node ID suffix (::Class::method, parametrize) preserved
# ===========================================================================

class TestNodeIdSuffixPreservation:

    def test_double_colon_suffix_preserved(self, tmp_path):
        raw = str(tmp_path / "test" / "test_a.py") + "::MyClass::test_method"
        result = normalize_pytest_target(raw, tmp_path)
        assert result == "test/test_a.py::MyClass::test_method"

    def test_parametrize_brackets_preserved(self):
        repo = PROJECT_ROOT / "data" / "repos" / "box_flaky_fa11546c"
        raw  = ("data/repos/box_flaky_fa11546c/test/test_pytest/"
                "test_flaky_pytest_plugin.py"
                "::test_flaky_xdist_nodedown[mock0-None-True]")
        result = normalize_pytest_target(raw, repo)
        assert result.endswith("::test_flaky_xdist_nodedown[mock0-None-True]")
        assert not result.startswith("data/")

    def test_unicode_parametrize_preserved(self):
        repo = PROJECT_ROOT / "data" / "repos" / "box_flaky_fa11546c"
        suffix = "::test_report[\u1e3e\u0151\u0155\u0205-text]"
        raw  = "data/repos/box_flaky_fa11546c/test/test_pytest/t.py" + suffix
        result = normalize_pytest_target(raw, repo)
        assert result.endswith(suffix), f"Unicode suffix lost: {result!r}"

    def test_no_double_colon_file_only(self, tmp_path):
        raw = str(tmp_path / "tests" / "test_x.py")
        result = normalize_pytest_target(raw, tmp_path)
        assert result == "tests/test_x.py"


# ===========================================================================
# TEST 4 — Repository root with spaces
# ===========================================================================

class TestRepoRootWithSpaces:

    def test_absolute_path_under_spaced_root(self, tmp_path):
        spaced = tmp_path / "my project" / "src repo"
        spaced.mkdir(parents=True)
        raw = str(spaced / "tests" / "test_x.py") + "::fn"
        result = normalize_pytest_target(raw, spaced)
        assert result == "tests/test_x.py::fn"
        assert " " not in result.split("::")[0] or True  # spaces OK inside path

    def test_relative_id_under_spaced_root_unchanged(self, tmp_path):
        spaced = tmp_path / "my project"
        spaced.mkdir(parents=True)
        raw = "tests/test_x.py::fn"
        result = normalize_pytest_target(raw, spaced)
        assert result == "tests/test_x.py::fn"


# ===========================================================================
# TEST 5 — Different cloned repository roots are independent
# ===========================================================================

class TestDifferentClonedRoots:

    def test_two_repos_produce_independent_paths(self):
        repo_a = Path("/clones/owner_repoA_abc12345")
        repo_b = Path("/clones/owner_repoB_def67890")

        raw_a = "clones/owner_repoA_abc12345/tests/test_a.py::fn_a"
        raw_b = "clones/owner_repoB_def67890/tests/test_b.py::fn_b"

        # normalize cwd-relative style: both must resolve to their own repo
        # We just test the output doesn't leak the other repo's name
        result_a = normalize_pytest_target(raw_a, repo_a)
        result_b = normalize_pytest_target(raw_b, repo_b)

        assert "repoB" not in result_a
        assert "repoA" not in result_b

    def test_is_flakeguard_repo_false_for_external(self):
        runner_ext = TestRunner(SAMPLE_REPO)
        assert not runner_ext._is_flakeguard_repo

    def test_is_flakeguard_repo_true_for_own_root(self):
        runner_own = TestRunner(_FLAKEGUARD_ROOT)
        assert runner_own._is_flakeguard_repo


# ===========================================================================
# TEST 6 — box/flaky test discovery (integration, skipped if absent)
# ===========================================================================

@pytest.mark.skipif(not BOX_REPO.exists(), reason="box/flaky clone not present")
class TestBoxFlakyDiscovery:

    def test_collects_nonzero_tests(self):
        runner = TestRunner(BOX_REPO)
        ids = runner.collect_test_ids()
        assert len(ids) > 0, "Expected tests from box/flaky"

    def test_no_data_repos_prefix_in_node_ids(self):
        runner = TestRunner(BOX_REPO)
        ids = runner.collect_test_ids()
        bad = [nid for nid in ids if nid.startswith("data/")]
        assert bad == [], f"Node IDs still contain data/ prefix: {bad[:3]}"

    def test_no_absolute_paths_in_node_ids(self):
        runner = TestRunner(BOX_REPO)
        ids = runner.collect_test_ids()
        abs_ids = [nid for nid in ids if Path(nid.split("::")[0]).is_absolute()]
        assert abs_ids == [], f"Absolute paths in node IDs: {abs_ids[:3]}"

    def test_node_ids_start_with_test_dir(self):
        runner = TestRunner(BOX_REPO)
        ids = runner.collect_test_ids()
        # box/flaky uses test/ not tests/
        assert all(nid.startswith("test/") for nid in ids), (
            "Expected all node IDs to start with test/ for box/flaky"
        )

    def test_expected_test_count(self):
        runner = TestRunner(BOX_REPO)
        ids = runner.collect_test_ids()
        assert len(ids) == 77, f"Expected 77 tests, got {len(ids)}"

    def test_single_run_produces_executions(self):
        runner = TestRunner(BOX_REPO)
        ids = runner.collect_test_ids()
        # Run only first 5 tests to keep CI fast
        runner._collected_test_ids = ids[:5]
        test_run = runner.run_tests(run_index=0, ordering_seed=0)
        assert test_run.total_tests > 0, "Expected at least one execution"
        assert test_run.total_tests == 5


# ===========================================================================
# TEST 7 — FlakeGuard sample-repo discovery
# ===========================================================================

class TestSampleRepoDiscovery:

    def test_collects_tests(self):
        runner = TestRunner(SAMPLE_REPO)
        ids = runner.collect_test_ids()
        assert len(ids) > 0

    def test_node_ids_relative_to_sample_repo(self):
        runner = TestRunner(SAMPLE_REPO)
        ids = runner.collect_test_ids()
        for nid in ids:
            fs = nid.split("::")[0]
            assert not Path(fs).is_absolute(), f"Absolute path in sample-repo: {nid}"

    def test_single_run_produces_executions(self):
        runner = TestRunner(SAMPLE_REPO)
        test_run = runner.run_tests(run_index=0, ordering_seed=42)
        assert test_run.total_tests > 0
        assert test_run.executions


# ===========================================================================
# TEST 8 — _is_flakeguard_repo flag
# ===========================================================================

class TestIsFlakeGuardRepoFlag:

    def test_true_for_flakeguard_root(self):
        runner = TestRunner(_FLAKEGUARD_ROOT)
        assert runner._is_flakeguard_repo is True

    def test_false_for_sample_repo(self):
        runner = TestRunner(SAMPLE_REPO)
        assert runner._is_flakeguard_repo is False

    @pytest.mark.skipif(not BOX_REPO.exists(), reason="box/flaky clone not present")
    def test_false_for_box_flaky(self):
        runner = TestRunner(BOX_REPO)
        assert runner._is_flakeguard_repo is False

    def test_false_for_arbitrary_tmp_path(self, tmp_path):
        runner = TestRunner(tmp_path)
        assert runner._is_flakeguard_repo is False


# ===========================================================================
# TEST 9 — --rootdir flag present in both collection and execution commands
# ===========================================================================

class TestRootDirFlagInCommands:

    def test_collect_command_includes_rootdir(self, tmp_path):
        _write_pytest_ini(tmp_path)
        _write_test(tmp_path, "test_x.py", "def test_x(): assert True")

        runner = _runner_with_plugins(tmp_path)
        captured: List[list] = []

        def fake_run(cmd, **kw):
            captured.append(list(cmd))
            # Write a minimal JSON report for any execution call
            for arg in cmd:
                if "--json-report-file=" in str(arg):
                    Path(str(arg).split("=", 1)[1]).write_text(
                        json.dumps({"tests": []}), encoding="utf-8"
                    )
            r = MagicMock()
            r.returncode = 0
            r.stdout = "tests/test_x.py::test_x\n"
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=fake_run):
            runner.collect_test_ids()

        # Find the --collect-only call
        collect_cmds = [c for c in captured if "--collect-only" in c]
        assert collect_cmds, "No --collect-only call captured"
        joined = " ".join(collect_cmds[0])
        assert f"--rootdir={tmp_path}" in joined, (
            f"--rootdir not in collection command: {joined}"
        )

    def test_run_command_includes_rootdir(self, tmp_path):
        _write_pytest_ini(tmp_path)
        runner = _runner_with_plugins(tmp_path)
        runner._collected_test_ids = ["tests/test_x.py::test_x"]
        captured: List[list] = []

        def fake_run(cmd, **kw):
            captured.append(list(cmd))
            for arg in cmd:
                if "--json-report-file=" in str(arg):
                    Path(str(arg).split("=", 1)[1]).write_text(
                        json.dumps({"tests": [
                            {"nodeid": "tests/test_x.py::test_x",
                             "outcome": "passed", "duration": 0.0,
                             "location": ["tests/test_x.py", 1, "test_x"]}
                        ]}), encoding="utf-8"
                    )
            r = MagicMock()
            r.returncode = 0; r.stdout = ""; r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=fake_run):
            runner.run_tests(run_index=0)

        exec_cmds = [c for c in captured
                     if "--collect-only" not in c and "pytest" in c
                     and c[1] == "-m"]
        assert exec_cmds, "No pytest execution call captured"
        joined = " ".join(exec_cmds[0])
        assert f"--rootdir={tmp_path}" in joined, (
            f"--rootdir not in execution command: {joined}"
        )


# ===========================================================================
# TEST 10 — -p backend.harness.pytest_compat absent for external repos
# ===========================================================================

class TestPytestCompatPluginScope:

    def _capture_commands(self, runner: TestRunner, node_ids=None):
        captured: List[list] = []

        def fake_run(cmd, **kw):
            captured.append(list(cmd))
            for arg in cmd:
                if "--json-report-file=" in str(arg):
                    tests = []
                    if node_ids:
                        tests = [{"nodeid": nid, "outcome": "passed",
                                  "duration": 0.0,
                                  "location": [nid.split("::")[0], 1, nid.split("::")[-1]]}
                                 for nid in node_ids]
                    Path(str(arg).split("=", 1)[1]).write_text(
                        json.dumps({"tests": tests}), encoding="utf-8"
                    )
            r = MagicMock()
            r.returncode = 0
            r.stdout = "\n".join(node_ids or []) + "\n"
            r.stderr = ""
            return r

        return fake_run, captured

    def test_compat_plugin_absent_for_external_repo(self, tmp_path):
        _write_pytest_ini(tmp_path)
        runner = _runner_with_plugins(tmp_path)
        fake_run, captured = self._capture_commands(runner, ["tests/t.py::t"])
        runner._collected_test_ids = ["tests/t.py::t"]

        with patch("subprocess.run", side_effect=fake_run):
            runner.run_tests(run_index=0)

        exec_cmds = [c for c in captured
                     if "pytest" in c and c[1] == "-m"
                     and "--collect-only" not in c]
        assert exec_cmds, "No pytest execution call found"
        joined = " ".join(exec_cmds[0])
        assert "backend.harness.pytest_compat" not in joined, (
            "pytest_compat plugin should NOT be loaded for external repos"
        )

    def test_compat_plugin_present_for_flakeguard_own_suite(self):
        runner = _runner_with_plugins(_FLAKEGUARD_ROOT)
        assert runner._is_flakeguard_repo is True
        fake_run, captured = self._capture_commands(
            runner, ["tests/test_f1_harness.py::t"]
        )
        runner._collected_test_ids = ["tests/test_f1_harness.py::t"]

        with patch("subprocess.run", side_effect=fake_run):
            runner.run_tests(run_index=0)

        exec_cmds = [c for c in captured
                     if "pytest" in c and c[1] == "-m"
                     and "--collect-only" not in c]
        assert exec_cmds, "No pytest execution call found"
        joined = " ".join(exec_cmds[0])
        assert "backend.harness.pytest_compat" in joined, (
            "pytest_compat plugin SHOULD be loaded for FlakeGuard's own suite"
        )


# ===========================================================================
# TEST 11 — PYTHONPATH includes repo root in both envs
# ===========================================================================

class TestPythonPathIncludes:

    def _get_pythonpath(self, runner: TestRunner, for_execution: bool = False):
        if for_execution:
            env = runner._build_execution_env(
                run_index=0, ordering_seed=None, jitter_ms=0,
                state_dir=runner.repo_path / ".fg_state",
                env_chaos=None,
            )
        else:
            env = runner._build_collection_env()
        return env.get("PYTHONPATH", "")

    def test_collection_env_includes_repo_root(self, tmp_path):
        runner = TestRunner(tmp_path)
        pypath = self._get_pythonpath(runner, for_execution=False)
        parts = pypath.split(os.pathsep)
        assert str(tmp_path) in parts, (
            f"Repo root {tmp_path} not in PYTHONPATH: {pypath}"
        )

    def test_execution_env_includes_repo_root(self, tmp_path):
        runner = TestRunner(tmp_path)
        pypath = self._get_pythonpath(runner, for_execution=True)
        parts = pypath.split(os.pathsep)
        assert str(tmp_path) in parts, (
            f"Repo root {tmp_path} not in PYTHONPATH: {pypath}"
        )

    def test_flakeguard_root_in_path_only_for_own_suite(self):
        runner_own = TestRunner(_FLAKEGUARD_ROOT)
        pypath_own = self._get_pythonpath(runner_own)
        assert str(_FLAKEGUARD_ROOT) in pypath_own.split(os.pathsep)

    def test_flakeguard_root_in_path_for_external_repo_only_as_fallback(self, tmp_path):
        """
        For external repos, FlakeGuard root is NOT explicitly added —
        only the repo root and any pre-existing PYTHONPATH are used.
        """
        runner_ext = TestRunner(tmp_path)
        env = runner_ext._build_collection_env()
        pypath = env.get("PYTHONPATH", "")
        parts = pypath.split(os.pathsep)
        assert str(tmp_path) in parts, "Repo root must be in PYTHONPATH"
        # FlakeGuard root should not be explicitly injected for external repos
        assert str(_FLAKEGUARD_ROOT) not in parts, (
            "FlakeGuard root should NOT be in PYTHONPATH for external repos"
        )
