"""Test runner module for executing tests and capturing results with controlled variation."""
import json
import logging
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time
from typing import Dict, List, Optional
import uuid
from datetime import datetime, timezone

from backend.models.detection import TestRun, TestExecution, TestStatus

logger = logging.getLogger(__name__)

# The FlakeGuard project root (where *this* file lives under backend/harness/).
_FLAKEGUARD_ROOT = Path(__file__).resolve().parent.parent.parent


def normalize_pytest_target(raw: str, repo_root: Path) -> str:
    """
    Normalize a pytest node ID or file path so it is relative to repo_root.

    Examples (repo_root = C:/Projects/FlakeGuard/data/repos/box_flaky_123):
        "data/repos/box_flaky_123/test/t.py::Cls::fn"
            → "test/t.py::Cls::fn"
        "C:\\Projects\\FlakeGuard\\data\\repos\\box_flaky_123\\test\\t.py::Cls::fn"
            → "test/t.py::Cls::fn"
        "test/t.py::Cls::fn"           (already relative) → "test/t.py::Cls::fn"
        "tests/t.py"                   (already relative) → "tests/t.py"

    Only the filesystem portion *before* the first "::" is path-normalized.
    The class/function suffix is preserved verbatim.
    """
    # Split on the first "::" to isolate the filesystem part
    if "::" in raw:
        sep_idx = raw.index("::")
        fs_part = raw[:sep_idx]
        tail = raw[sep_idx:]       # includes the leading "::"
    else:
        fs_part = raw
        tail = ""

    # Normalise separators to the local OS convention for Path() parsing
    fs_path = Path(fs_part)

    # -----------------------------------------------------------------------
    # Case 1: absolute path
    # -----------------------------------------------------------------------
    if fs_path.is_absolute():
        try:
            rel = fs_path.relative_to(repo_root)
            return rel.as_posix() + tail
        except ValueError:
            # Absolute but NOT under repo_root — return as-is
            return raw

    # -----------------------------------------------------------------------
    # Case 2: relative path that encodes the repo dir as a prefix
    #   e.g. "data/repos/box_flaky_123/test/t.py"
    #   when cwd is C:\Projects\FlakeGuard and repo_root is
    #   C:\Projects\FlakeGuard\data\repos\box_flaky_123
    # -----------------------------------------------------------------------
    # Strategy: join with repo_root's parent hierarchy and try relative_to.
    # Walk up ancestors of repo_root to find if the forward path matches.
    try:
        cwd_candidate = Path.cwd() / fs_path
        resolved = cwd_candidate.resolve()
        rel = resolved.relative_to(repo_root.resolve())
        return rel.as_posix() + tail
    except (ValueError, OSError):
        pass

    # -----------------------------------------------------------------------
    # Case 3: already a clean repo-relative path — just normalise separators
    # -----------------------------------------------------------------------
    return fs_path.as_posix() + tail


class TestRunner:
    """Executes tests with controlled ordering, environment chaos, jitter, and parallelism."""

    def __init__(
        self,
        repo_path: str | Path,
        collection_timeout: float = 30.0,
        run_timeout: float = 60.0,
    ):
        self.repo_path = Path(repo_path).resolve()
        if collection_timeout <= 0 or run_timeout <= 0:
            raise ValueError("Test timeouts must be positive")
        self.collection_timeout = collection_timeout
        self.run_timeout = run_timeout
        self._collected_test_ids: Optional[List[str]] = None
        self._pytest_plugins_verified = False
        self._json_report_available = False
        # True when this runner operates on FlakeGuard's own test suite
        self._is_flakeguard_repo = (self.repo_path == _FLAKEGUARD_ROOT)

    # ------------------------------------------------------------------
    # Environment verification
    # ------------------------------------------------------------------

    def verify_pytest_environment(self) -> Dict[str, object]:
        """
        Verify pytest environment and check for required plugins.
        Returns dict with: verified, json_report, pytest_version,
                           python_executable, warnings.
        """
        if self._pytest_plugins_verified:
            import pytest as _pytest
            return {
                "verified": True,
                "json_report": self._json_report_available,
                "python_executable": sys.executable,
                "warnings": [],
                "pytest_version": _pytest.__version__,
            }

        result: Dict[str, object] = {
            "verified": False,
            "json_report": False,
            "pytest_version": None,
            "python_executable": sys.executable,
            "warnings": [],
        }

        try:
            import pytest
            result["pytest_version"] = pytest.__version__

            help_result = subprocess.run(
                [sys.executable, "-m", "pytest", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if "--json-report" in help_result.stdout:
                result["json_report"] = True
                self._json_report_available = True
            else:
                result["warnings"].append(  # type: ignore[union-attr]
                    "pytest-json-report plugin not available. "
                    "Install with: pip install pytest-json-report"
                )

            result["verified"] = True
            self._pytest_plugins_verified = True

            logger.info(
                "Pytest environment verified: pytest=%s, json-report=%s, "
                "python=%s, repo=%s",
                result["pytest_version"],
                result["json_report"],
                sys.executable,
                self.repo_path,
            )

        except ImportError as exc:
            result["warnings"].append(f"pytest not importable: {exc}")  # type: ignore[union-attr]
            logger.error("Pytest import failed: %s", exc)
        except Exception as exc:
            result["warnings"].append(f"Verification failed: {exc}")  # type: ignore[union-attr]
            logger.error("Pytest verification failed: %s", exc)

        return result

    # ------------------------------------------------------------------
    # PYTHONPATH helpers
    # ------------------------------------------------------------------

    def _build_collection_env(self) -> Dict[str, str]:
        """
        Build environment for the pytest --collect-only subprocess.

        PYTHONPATH always includes:
          1. The target repo root  (so its own source packages import correctly)
          2. FlakeGuard root       (so backend.harness.pytest_compat is importable
                                    *only when running FlakeGuard's own suite*)
        """
        env = os.environ.copy()
        # Collection and execution must share controlled options. Inherited
        # retry/addopts settings otherwise hide failures or multiply work.
        env.pop("PYTEST_ADDOPTS", None)
        parts: List[str] = [str(self.repo_path)]
        if self._is_flakeguard_repo:
            parts.append(str(_FLAKEGUARD_ROOT))
        existing = env.get("PYTHONPATH", "")
        if existing:
            parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(parts)
        return env

    def _build_execution_env(
        self,
        run_index: int,
        ordering_seed: Optional[int],
        jitter_ms: int,
        state_dir: Path,
        env_chaos: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        """Build environment for the actual pytest execution subprocess."""
        env = self._build_collection_env()
        env["FLAKEGUARD_STATE_DIR"] = str(state_dir)
        env["FG_RUN_INDEX"] = str(run_index)
        env["FG_ORDERING_SEED"] = str(ordering_seed if ordering_seed is not None else 0)
        env["FG_JITTER_MS"] = str(jitter_ms)
        if env_chaos:
            env.update(env_chaos)
        return env

    # ------------------------------------------------------------------
    # Test collection
    # ------------------------------------------------------------------

    def collect_test_ids(self) -> List[str]:
        """
        Collect and cache pytest node IDs from the target repository.

        Node IDs are always returned as paths relative to self.repo_path,
        using forward slashes (POSIX style), e.g.:
            test/test_foo.py::MyClass::test_bar
        """
        if self._collected_test_ids is not None:
            return self._collected_test_ids

        env_check = self.verify_pytest_environment()
        if not env_check["verified"]:
            raise RuntimeError(
                f"Pytest environment verification failed: {env_check['warnings']}"
            )

        env = self._build_collection_env()

        cmd = [
            sys.executable, "-m", "pytest",
            # --rootdir forces pytest to anchor at the target repo root,
            # preventing it from walking up and finding FlakeGuard's pytest.ini.
            f"--rootdir={self.repo_path}",
            "--collect-only", "-q",
            "-p", "no:cacheprovider",
            # Clear any inherited addopts that might add unknown flags
            "-o", "addopts=",
        ]

        # Only load the compat plugin when running FlakeGuard's own suite.
        # Loading it for external repos causes pytest to resolve paths relative
        # to the FlakeGuard project root instead of the target repo root.
        if self._is_flakeguard_repo:
            cmd += ["-p", "backend.harness.pytest_compat"]

        logger.debug(
            "Collecting tests: cwd=%s, rootdir=%s, cmd=%s",
            self.repo_path, self.repo_path, " ".join(cmd),
        )

        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.collection_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Test collection exceeded {self.collection_timeout:g} seconds") from exc

        # A clean no-tests result is different from a broken collection. Never
        # accept partial IDs when imports or pytest configuration failed.
        if res.returncode == 5:
            self._collected_test_ids = []
            return []
        if res.returncode != 0:
            raise RuntimeError(f"Test collection failed (exit code: {res.returncode})")

        raw_ids: List[str] = []
        for line in res.stdout.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("="):
                continue
            if "::" in stripped:
                # Parameter IDs may contain spaces; preserve the whole node ID.
                raw_ids.append(stripped)

        # Fallback: pytest printed tree format (<Module>, <Class>, <Function>)
        if not raw_ids:
            current_mod = ""
            current_cls = ""
            for raw_line in res.stdout.splitlines():
                s = raw_line.strip()
                if s.startswith("<Module "):
                    current_mod = s[len("<Module "):-1].strip("'\"")
                    current_cls = ""
                elif s.startswith("<Class "):
                    current_cls = s[len("<Class "):-1].strip("'\"")
                elif s.startswith("<Function "):
                    fn = s[len("<Function "):-1].strip("'\"")
                    if current_cls:
                        raw_ids.append(f"{current_mod}::{current_cls}::{fn}")
                    else:
                        raw_ids.append(f"{current_mod}::{fn}")

        if not raw_ids:
            # Build a clean hint from stderr (strip local paths before raising)
            import re as _re
            _path_re = _re.compile(r'[A-Za-z]:\\[^\s]+|(?:/[^\s]*){3,}')
            stderr_clean = _path_re.sub('<path>', res.stderr.strip()) if res.stderr else ""
            hint = ""
            if stderr_clean:
                # Grab only the first meaningful line to keep the message short
                first_line = next(
                    (ln.strip() for ln in stderr_clean.splitlines() if ln.strip() and not ln.strip().startswith("=")),
                    ""
                )
                if first_line:
                    hint = f" Hint: {first_line}"
            logger.warning(
                "Collection returned zero tests (exit=%d). Stderr: %s",
                res.returncode, res.stderr,
            )
            raise RuntimeError(
                f"No tests were collected (exit code: {res.returncode}).{hint}"
            )

        # Normalize every raw ID to be repo-root-relative
        node_ids = sorted(
            normalize_pytest_target(nid, self.repo_path) for nid in raw_ids
        )

        logger.info(
            "Collected %d tests from %s (first: %s)",
            len(node_ids), self.repo_path,
            node_ids[0] if node_ids else "<none>",
        )
        self._collected_test_ids = node_ids
        return node_ids

    # ------------------------------------------------------------------
    # Test execution
    # ------------------------------------------------------------------

    def run_tests(
        self,
        run_index: int = 0,
        ordering_seed: Optional[int] = None,
        jitter_ms: int = 0,
        env_chaos: Optional[Dict[str, str]] = None,
        parallel: bool = False,
        test_pattern: Optional[str] = None,
    ) -> TestRun:
        """
        Execute pytest with injected controlled variation and parse results.

        cwd is always self.repo_path.  Node IDs passed to pytest are always
        relative to self.repo_path (repo-root-relative, POSIX paths).
        """
        env_check = self.verify_pytest_environment()
        if not env_check["verified"]:
            raise RuntimeError(
                f"Pytest environment not verified: {env_check['warnings']}"
            )
        if not env_check["json_report"]:
            raise RuntimeError(
                "pytest-json-report plugin is required but not installed. "
                "Install with: pip install pytest-json-report"
            )

        run_id = str(uuid.uuid4())
        node_ids = list(self.collect_test_ids())
        if test_pattern:
            node_ids = [node for node in node_ids if test_pattern in node]
        if not node_ids:
            # Running pytest with no node arguments would execute the entire
            # suite again, including when the requested filter matched nothing.
            return TestRun(
                run_id=run_id, repository=str(self.repo_path),
                branch="unknown", commit_sha="unknown", executions=[],
                ordering=[], ordering_seed=ordering_seed, returncode=5,
            )
        if ordering_seed is not None:
            random.Random(ordering_seed).shuffle(node_ids)

        # Own only a unique temporary child. Never delete caller state, source
        # caches, virtualenv caches, or another concurrent run's working files.
        state_parent_env = os.environ.get("FLAKEGUARD_STATE_DIR")
        state_parent = Path(state_parent_env).resolve() if state_parent_env else None
        if state_parent is not None:
            state_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="flakeguard-", dir=state_parent) as temporary:
            state_dir = Path(temporary) / "state"
            state_dir.mkdir()
            report_file = Path(temporary) / f".temp_results_{run_id}.json"
            return self._execute_collected_tests(
                run_id, node_ids, state_dir, report_file,
                run_index, ordering_seed, jitter_ms, env_chaos, parallel,
            )

    def _execute_collected_tests(
        self, run_id: str, node_ids: List[str], state_dir: Path, report_file: Path,
        run_index: int, ordering_seed: Optional[int], jitter_ms: int,
        env_chaos: Optional[Dict[str, str]], parallel: bool,
    ) -> TestRun:
        # 3. Build child environment
        child_env = self._build_execution_env(
            run_index=run_index,
            ordering_seed=ordering_seed,
            jitter_ms=jitter_ms,
            state_dir=state_dir,
            env_chaos=env_chaos,
        )

        # 4. Jitter
        if jitter_ms > 0:
            time.sleep(jitter_ms / 1000.0)

        # 5. Parallelism
        actual_parallel = parallel
        if actual_parallel:
            try:
                import xdist  # noqa: F401
            except ImportError:
                actual_parallel = False

        # 6. Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            # Anchor rootdir to the target repo — prevents FlakeGuard's
            # pytest.ini from being discovered and poisoning node ID paths.
            f"--rootdir={self.repo_path}",
            "-p", "no:cacheprovider",
            "--tb=short",
            "-v",
            "--json-report",
            f"--json-report-file={report_file}",
            "-o", "addopts=",
        ]

        if self._is_flakeguard_repo:
            cmd += ["-p", "backend.harness.pytest_compat"]

        if actual_parallel:
            cmd.extend(["-n", "4"])

        cmd.extend(node_ids)

        logger.info(
            "Pytest run %d: cwd=%s, rootdir=%s, tests=%d, cmd=%s",
            run_index, self.repo_path, self.repo_path,
            len(node_ids), " ".join(str(c) for c in cmd[:8]) + " ...",
        )

        start_time = time.perf_counter()
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                env=child_env,
                capture_output=True,
                text=True,
                timeout=self.run_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Test run exceeded {self.run_timeout:g} seconds") from exc
        duration_seconds = time.perf_counter() - start_time

        logger.info(
            "Pytest run %d completed: exit_code=%d, duration=%.2fs",
            run_index, res.returncode, duration_seconds,
        )

        # 7. Handle missing result file
        if not report_file.exists():
            if res.returncode == 5:
                logger.warning("Pytest run %d: no tests collected (exit 5)", run_index)
                return TestRun(
                    run_id=run_id,
                    repository=str(self.repo_path),
                    branch=self._get_current_branch(),
                    commit_sha=self._get_current_commit(),
                    executions=[],
                    total_tests=0,
                    passed=0,
                    failed=0,
                    timestamp=datetime.now(timezone.utc),
                    ordering_seed=ordering_seed,
                    ordering=node_ids,
                    jitter_ms=jitter_ms,
                    env_chaos=env_chaos or {},
                    parallel=actual_parallel,
                    duration_seconds=round(duration_seconds, 4),
                    returncode=5,
                )

            error_msg = (
                f"Pytest run {run_index} (id: {run_id}) failed to produce "
                f"results file {report_file}.\n"
                f"Return code: {res.returncode}\n"
                f"Command: {' '.join(str(c) for c in cmd)}\n"
                f"Working directory: {self.repo_path}\n"
                f"Python executable: {sys.executable}\n"
            )
            if res.stderr:
                error_msg += f"Stderr:\n{res.stderr}\n"
            if res.stdout:
                error_msg += f"Stdout (last 1000 chars):\n{res.stdout[-1000:]}\n"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # 8. Parse result file
        with open(report_file, "r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to parse JSON report {report_file}: {exc}\n"
                    f"Return code: {res.returncode}\n"
                    f"Stderr:\n{res.stderr}"
                ) from exc
        # Unlink after close (Windows cannot delete open files)
        try:
            report_file.unlink()
        except Exception:
            pass

        # 9. Parse individual test results
        executions = self._parse_pytest_results(data, run_id)
        if not executions and node_ids:
            raise RuntimeError(
                f"Pytest run {run_index} (id: {run_id}) produced zero test "
                f"executions despite {len(node_ids)} tests queued.\n"
                f"Return code: {res.returncode}\n"
                f"Stderr:\n{res.stderr}\n"
                f"Stdout:\n{res.stdout}"
            )

        passed_count = sum(1 for e in executions if e.status == TestStatus.PASSED)
        failed_count = sum(1 for e in executions if e.status == TestStatus.FAILED)

        return TestRun(
            run_id=run_id,
            repository=str(self.repo_path),
            branch=self._get_current_branch(),
            commit_sha=self._get_current_commit(),
            executions=executions,
            total_tests=len(executions),
            passed=passed_count,
            failed=failed_count,
            timestamp=datetime.now(timezone.utc),
            ordering_seed=ordering_seed,
            ordering=node_ids,
            jitter_ms=jitter_ms,
            env_chaos=env_chaos or {},
            parallel=actual_parallel,
            duration_seconds=round(duration_seconds, 4),
            returncode=res.returncode,
        )

    # ------------------------------------------------------------------
    # Result parsing
    # ------------------------------------------------------------------

    def _parse_pytest_results(self, data: dict, run_id: str) -> List[TestExecution]:
        """Parse pytest JSON report into TestExecution objects."""
        status_map = {
            "passed": TestStatus.PASSED,
            "failed": TestStatus.FAILED,
            "skipped": TestStatus.SKIPPED,
            "error": TestStatus.ERROR,
        }

        executions: List[TestExecution] = []
        for idx, test in enumerate(data.get("tests", [])):
            error_message = None
            error_traceback = None

            call_info = test.get("call", {})
            if "crash" in call_info:
                error_message = call_info["crash"].get("message")
                error_traceback = call_info["crash"].get("traceback")
            elif test.get("outcome") in ("failed", "error"):
                for phase in ("setup", "call", "teardown"):
                    phase_info = test.get(phase, {})
                    if "crash" in phase_info:
                        error_message = phase_info["crash"].get("message")
                        error_traceback = phase_info["crash"].get("traceback")
                        break

            file_path = test.get("location", [test["nodeid"].split("::")[0]])[0]

            executions.append(
                TestExecution(
                    test_name=test["nodeid"],
                    file_path=file_path,
                    status=status_map.get(test.get("outcome"), TestStatus.ERROR),
                    duration=float(test.get("duration", 0.0)),
                    error_message=error_message,
                    error_traceback=error_traceback,
                    timestamp=datetime.now(timezone.utc),
                    run_id=run_id,
                    attempt_index=idx,
                )
            )

        return executions

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------

    def _get_current_branch(self) -> str:
        try:
            res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.stdout.strip() or "main"
        except Exception:
            return "main"

    def _get_current_commit(self) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.stdout.strip() or "unknown"
        except Exception:
            return "unknown"
