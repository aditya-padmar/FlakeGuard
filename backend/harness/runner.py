"""Test runner module for executing tests and capturing results with controlled variation."""
import json
import logging
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Optional
import uuid
from datetime import datetime, timezone

from backend.models.detection import TestRun, TestExecution, TestStatus

logger = logging.getLogger(__name__)


class TestRunner:
    """Executes tests with controlled ordering, environment chaos, jitter, and parallelism."""

    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path).resolve()
        self._collected_test_ids: Optional[List[str]] = None
        self._pytest_plugins_verified = False
        self._json_report_available = False

    def verify_pytest_environment(self) -> Dict[str, any]:
        """
        Verify pytest environment and check for required plugins.
        Returns dict with status and available features.
        """
        if self._pytest_plugins_verified:
            import pytest as _pytest
            return {
                "verified": True,
                "json_report": self._json_report_available,
                "python_executable": sys.executable,
                "warnings": [],
                "pytest_version": _pytest.__version__
            }

        result = {
            "verified": False,
            "json_report": False,
            "pytest_version": None,
            "python_executable": sys.executable,
            "warnings": []
        }

        try:
            # Check if pytest is importable
            import pytest
            result["pytest_version"] = pytest.__version__
            
            # Check for json-report plugin by running pytest --help
            help_cmd = [sys.executable, "-m", "pytest", "--help"]
            help_result = subprocess.run(
                help_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "--json-report" in help_result.stdout:
                result["json_report"] = True
                self._json_report_available = True
            else:
                result["warnings"].append(
                    "pytest-json-report plugin not available. "
                    "Install with: pip install pytest-json-report"
                )
                
            result["verified"] = True
            self._pytest_plugins_verified = True
            
            logger.info(
                f"Pytest environment verified: pytest={result['pytest_version']}, "
                f"json-report={result['json_report']}, python={sys.executable}"
            )
            
        except ImportError as e:
            result["warnings"].append(f"pytest not importable: {e}")
            logger.error(f"Pytest import failed: {e}")
        except Exception as e:
            result["warnings"].append(f"Verification failed: {e}")
            logger.error(f"Pytest verification failed: {e}")

        return result

    def collect_test_ids(self) -> List[str]:
        """Collect and cache test node IDs from repository."""
        if self._collected_test_ids is not None:
            return self._collected_test_ids

        # Verify pytest environment first
        env_check = self.verify_pytest_environment()
        if not env_check["verified"]:
            raise RuntimeError(
                f"Pytest environment verification failed: {env_check['warnings']}"
            )

        # Ensure project root is in PYTHONPATH
        project_root = Path(__file__).resolve().parent.parent.parent
        env = os.environ.copy()
        curr_pypath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{curr_pypath}" if curr_pypath else str(project_root)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "backend.harness.pytest_compat",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
        ]
        res = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            env=env,
            capture_output=True,
            text=True,
        )

        # Handle exit code 5 (no tests collected)
        if res.returncode == 5:
            logger.warning(f"No tests collected from {self.repo_path}")
            return []

        node_ids: List[str] = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("="):
                continue
            if "::" in line:
                node_id = line.split()[0]
                node_ids.append(node_id)

        # Fallback: if -o addopts= was not supported or tree format was printed
        if not node_ids:
            current_mod = ""
            current_cls = ""
            for raw_line in res.stdout.splitlines():
                stripped = raw_line.strip()
                if stripped.startswith("<Module "):
                    current_mod = stripped[len("<Module "):-1].strip("'\"")
                    current_cls = ""
                elif stripped.startswith("<Class "):
                    current_cls = stripped[len("<Class "):-1].strip("'\"")
                elif stripped.startswith("<Function "):
                    fn = stripped[len("<Function "):-1].strip("'\"")
                    mod_path = f"tests/{current_mod}" if not current_mod.startswith("tests/") else current_mod
                    if current_cls:
                        node_ids.append(f"{mod_path}::{current_cls}::{fn}")
                    else:
                        node_ids.append(f"{mod_path}::{fn}")

        if not node_ids:
            logger.warning(
                f"Collection returned zero tests from {self.repo_path}.\n"
                f"Exit code: {res.returncode}\n"
                f"This may indicate: no test files found, incompatible pytest plugins, "
                f"or misconfigured pytest.ini"
            )
            # Don't raise here - return empty list and let caller decide
            self._collected_test_ids = []
            return []

        self._collected_test_ids = sorted(node_ids)
        return self._collected_test_ids

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
        """
        # Verify pytest environment
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

        # 1. RESET STATE FIRST before every single run
        state_dir_env = os.environ.get("FLAKEGUARD_STATE_DIR")
        if state_dir_env:
            state_dir = Path(state_dir_env).resolve()
        else:
            state_dir = (self.repo_path / ".flakeguard_state").resolve()

        if state_dir.exists():
            shutil.rmtree(state_dir, ignore_errors=True)
        state_dir.mkdir(parents=True, exist_ok=True)

        for pycache in self.repo_path.glob("**/__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache, ignore_errors=True)

        # 2. ORDERING: shuffle collected node IDs with random.Random(ordering_seed)
        all_node_ids = list(self.collect_test_ids())
        
        # Handle no tests collected
        if not all_node_ids:
            logger.warning(f"No tests collected from {self.repo_path}")
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
                ordering=[],
                jitter_ms=jitter_ms,
                env_chaos=env_chaos or {},
                parallel=False,
                duration_seconds=0.0,
                returncode=5,  # pytest exit code for no tests collected
            )
        
        if test_pattern:
            all_node_ids = [nid for nid in all_node_ids if test_pattern in nid]

        node_ids = list(all_node_ids)
        if ordering_seed is not None:
            rng = random.Random(ordering_seed)
            rng.shuffle(node_ids)

        # 3. ENVIRONMENT: build child env and stamp FG_* vars
        child_env = os.environ.copy()
        project_root = Path(__file__).resolve().parent.parent.parent
        curr_pypath = child_env.get("PYTHONPATH", "")
        child_env["PYTHONPATH"] = f"{project_root}{os.pathsep}{curr_pypath}" if curr_pypath else str(project_root)
        child_env["FLAKEGUARD_STATE_DIR"] = str(state_dir)
        child_env["FG_RUN_INDEX"] = str(run_index)
        child_env["FG_ORDERING_SEED"] = str(ordering_seed if ordering_seed is not None else 0)
        child_env["FG_JITTER_MS"] = str(jitter_ms)

        if env_chaos:
            child_env.update(env_chaos)

        # 4. JITTER: sleep before launching pytest
        if jitter_ms > 0:
            time.sleep(jitter_ms / 1000.0)

        # 5. PARALLELISM: check xdist importability
        actual_parallel = parallel
        if actual_parallel:
            try:
                import xdist  # noqa: F401
            except ImportError:
                actual_parallel = False

        # 6. Build pytest command using sys.executable
        report_file = self.repo_path / f".temp_results_{run_id}.json"
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "backend.harness.pytest_compat",
            "-p",
            "no:cacheprovider",
            "--tb=short",
            "-v",
            "--json-report",
            f"--json-report-file={report_file}",
        ]

        if actual_parallel:
            cmd.extend(["-n", "4"])

        cmd.extend(node_ids)

        start_time = time.perf_counter()
        res = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            env=child_env,
            capture_output=True,
            text=True,
        )
        duration_seconds = time.perf_counter() - start_time

        # Log pytest execution details
        logger.info(
            f"Pytest run {run_index} completed: exit_code={res.returncode}, "
            f"duration={duration_seconds:.2f}s, tests={len(node_ids)}"
        )

        # 8. HANDLE MISSING RESULT FILE
        if not report_file.exists():
            # Check if exit code 5 (no tests collected)
            if res.returncode == 5:
                logger.warning(f"Pytest run {run_index}: no tests collected")
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
                    returncode=res.returncode,
                )
            
            # Otherwise it's an infrastructure failure
            error_msg = (
                f"Pytest run {run_index} (id: {run_id}) failed to produce results file {report_file}.\n"
                f"Return code: {res.returncode}\n"
                f"Command: {' '.join(cmd)}\n"
                f"Working directory: {self.repo_path}\n"
                f"Python executable: {sys.executable}\n"
            )
            if res.stderr:
                error_msg += f"Stderr:\n{res.stderr}\n"
            if res.stdout:
                error_msg += f"Stdout (last 500 chars):\n{res.stdout[-500:]}\n"
            
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        with open(report_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to parse json report {report_file}: {e}\n"
                    f"Return code: {res.returncode}\n"
                    f"Stderr:\n{res.stderr}"
                ) from e
        # Cleanup after file handle is closed (important on Windows)
        try:
            report_file.unlink()
        except Exception:
            pass

        # 7. Stamp run_id and attempt_index onto every TestExecution
        executions = self._parse_pytest_results(data, run_id)
        if not executions and node_ids:
            raise RuntimeError(
                f"Pytest run {run_index} (id: {run_id}) produced zero test executions despite {len(node_ids)} tests run.\n"
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

    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
            )
            return res.stdout.strip() or "main"
        except Exception:
            return "main"

    def _get_current_commit(self) -> str:
        """Get current git commit SHA."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
            )
            return res.stdout.strip() or "unknown"
        except Exception:
            return "unknown"
