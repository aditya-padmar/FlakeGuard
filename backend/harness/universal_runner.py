"""Universal multi-language test runner — wraps pytest, Jest/Vitest, Go, Maven, Gradle, RSpec."""
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.models.detection import TestRun, TestExecution, TestStatus
from backend.harness.framework_detector import (
    detect_framework,
    FRAMEWORK_PYTEST,
    FRAMEWORK_JEST,
    FRAMEWORK_VITEST,
    FRAMEWORK_GO,
    FRAMEWORK_MAVEN,
    FRAMEWORK_GRADLE,
    FRAMEWORK_RSPEC,
)

logger = logging.getLogger(__name__)

_PATH_RE = re.compile(r'[A-Za-z]:\\[^\s]+|(?:/[^\s]*){4,}')


def _strip_paths(text: str) -> str:
    return _PATH_RE.sub('<path>', text)


class UniversalRunner:
    """
    Detects the test framework in a cloned repository and runs tests repeatedly,
    returning results as the standard TestRun model regardless of language.
    """

    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path).resolve()
        self._framework_info: Optional[Dict] = None
        self._collected_tests: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # Framework info (lazy, cached)
    # ------------------------------------------------------------------

    @property
    def framework_info(self) -> Dict:
        if self._framework_info is None:
            self._framework_info = detect_framework(self.repo_path)
        return self._framework_info

    @property
    def framework(self) -> str:
        return self.framework_info["framework"]

    @property
    def language(self) -> str:
        return self.framework_info["language"]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def collect_test_ids(self) -> List[str]:
        """Return a list of test identifiers. Raises RuntimeError if none found."""
        if self._collected_tests is not None:
            return self._collected_tests

        fw = self.framework
        if fw == FRAMEWORK_PYTEST:
            ids = self._collect_pytest()
        elif fw in (FRAMEWORK_JEST, FRAMEWORK_VITEST):
            ids = self._collect_jest_vitest()
        elif fw == FRAMEWORK_GO:
            ids = self._collect_go()
        elif fw == FRAMEWORK_MAVEN:
            ids = self._collect_maven()
        elif fw == FRAMEWORK_GRADLE:
            ids = self._collect_gradle()
        elif fw == FRAMEWORK_RSPEC:
            ids = self._collect_rspec()
        else:
            raise RuntimeError(
                f"No supported test framework detected in this repository. "
                f"Supported: Python/pytest, JavaScript/Jest, JavaScript/Vitest, "
                f"Go, Java/Maven, Java/Gradle, Ruby/RSpec."
            )

        if not ids:
            raise RuntimeError(
                f"No tests were collected for framework '{fw}'. "
                f"Ensure the repository has test files and all dependencies are installed."
            )

        self._collected_tests = ids
        return ids

    def run_tests(
        self,
        run_index: int = 0,
        ordering_seed: Optional[int] = None,
        jitter_ms: int = 0,
        env_chaos: Optional[Dict[str, str]] = None,
        parallel: bool = False,
        test_pattern: Optional[str] = None,
    ) -> TestRun:
        """Execute one full test run and return a TestRun."""
        run_id = str(uuid.uuid4())
        node_ids = list(self.collect_test_ids())

        if test_pattern:
            node_ids = [t for t in node_ids if test_pattern in t]

        if jitter_ms > 0:
            time.sleep(jitter_ms / 1000.0)

        child_env = {**os.environ}
        if env_chaos:
            child_env.update(env_chaos)

        fw = self.framework
        start = time.perf_counter()

        if fw == FRAMEWORK_PYTEST:
            executions, returncode = self._run_pytest(run_id, node_ids, child_env, ordering_seed)
        elif fw in (FRAMEWORK_JEST, FRAMEWORK_VITEST):
            executions, returncode = self._run_jest_vitest(run_id, node_ids, child_env)
        elif fw == FRAMEWORK_GO:
            executions, returncode = self._run_go(run_id, node_ids, child_env)
        elif fw == FRAMEWORK_MAVEN:
            executions, returncode = self._run_maven(run_id, child_env)
        elif fw == FRAMEWORK_GRADLE:
            executions, returncode = self._run_gradle(run_id, child_env)
        elif fw == FRAMEWORK_RSPEC:
            executions, returncode = self._run_rspec(run_id, node_ids, child_env)
        else:
            executions, returncode = [], 1

        duration = round(time.perf_counter() - start, 4)
        passed = sum(1 for e in executions if e.status == TestStatus.PASSED)
        failed = sum(1 for e in executions if e.status == TestStatus.FAILED)

        return TestRun(
            run_id=run_id,
            repository=str(self.repo_path),
            branch=self._git_branch(),
            commit_sha=self._git_sha(),
            executions=executions,
            total_tests=len(executions),
            passed=passed,
            failed=failed,
            timestamp=datetime.now(timezone.utc),
            ordering_seed=ordering_seed,
            ordering=node_ids,
            jitter_ms=jitter_ms,
            env_chaos=env_chaos or {},
            parallel=parallel,
            duration_seconds=duration,
            returncode=returncode,
        )

    # ------------------------------------------------------------------
    # pytest
    # ------------------------------------------------------------------

    def _collect_pytest(self) -> List[str]:
        cmd = [
            sys.executable, "-m", "pytest",
            f"--rootdir={self.repo_path}",
            "--collect-only", "-q",
            "-o", "addopts=",
        ]
        res = subprocess.run(cmd, cwd=str(self.repo_path), capture_output=True, text=True)

        if res.returncode == 5:
            raise RuntimeError(
                "No tests were collected (exit code: 5). "
                "The repository contains no files matching test_*.py or *_test.py."
            )

        ids = []
        for line in res.stdout.splitlines():
            s = line.strip()
            if s and "::" in s and not s.startswith("="):
                ids.append(s.split()[0])

        if not ids and res.returncode != 0:
            hint = _strip_paths((res.stderr or "").strip())
            first = next((l.strip() for l in hint.splitlines() if l.strip() and not l.strip().startswith("=")), "")
            raise RuntimeError(
                f"No tests were collected (exit code: {res.returncode})."
                + (f" Hint: {first}" if first else "")
            )
        return ids

    def _run_pytest(
        self,
        run_id: str,
        node_ids: List[str],
        env: Dict,
        ordering_seed: Optional[int],
    ) -> Tuple[List[TestExecution], int]:
        report_file = self.repo_path / f".fg_results_{run_id}.json"
        cmd = [
            sys.executable, "-m", "pytest",
            f"--rootdir={self.repo_path}",
            "-p", "no:cacheprovider",
            "--tb=short", "-v",
            "--json-report", f"--json-report-file={report_file}",
            "-o", "addopts=",
        ] + node_ids

        res = subprocess.run(cmd, cwd=str(self.repo_path), env=env, capture_output=True, text=True)

        if not report_file.exists():
            return [], res.returncode

        try:
            data = json.loads(report_file.read_text(encoding="utf-8"))
        except Exception:
            return [], res.returncode
        finally:
            try:
                report_file.unlink()
            except Exception:
                pass

        return self._parse_pytest_json(data, run_id), res.returncode

    def _parse_pytest_json(self, data: dict, run_id: str) -> List[TestExecution]:
        status_map = {"passed": TestStatus.PASSED, "failed": TestStatus.FAILED,
                      "skipped": TestStatus.SKIPPED, "error": TestStatus.ERROR}
        executions = []
        for idx, test in enumerate(data.get("tests", [])):
            error_message = error_tb = None
            for phase in ("call", "setup", "teardown"):
                info = test.get(phase, {})
                if "crash" in info:
                    error_message = info["crash"].get("message")
                    error_tb = info["crash"].get("traceback")
                    break
            file_path = test.get("location", [test["nodeid"].split("::")[0]])[0]
            executions.append(TestExecution(
                test_name=test["nodeid"],
                file_path=file_path,
                status=status_map.get(test.get("outcome"), TestStatus.ERROR),
                duration=float(test.get("duration", 0.0)),
                error_message=error_message,
                error_traceback=error_tb,
                timestamp=datetime.now(timezone.utc),
                run_id=run_id,
                attempt_index=idx,
            ))
        return executions

    # ------------------------------------------------------------------
    # Jest / Vitest
    # ------------------------------------------------------------------

    def _collect_jest_vitest(self) -> List[str]:
        """List test files as IDs — Jest/Vitest doesn't have a cheap collect-only mode."""
        patterns = ("**/*.test.ts", "**/*.test.js", "**/*.spec.ts", "**/*.spec.js",
                    "**/*.test.tsx", "**/*.spec.tsx", "**/*.test.jsx", "**/*.spec.jsx")
        found = []
        for pat in patterns:
            for p in self.repo_path.glob(pat):
                if "node_modules" not in p.parts and ".next" not in p.parts:
                    found.append(str(p.relative_to(self.repo_path)).replace("\\", "/"))
        if not found:
            raise RuntimeError(
                "No JavaScript/TypeScript test files found (*.test.ts, *.spec.js, etc.)."
            )
        return sorted(set(found))

    def _run_jest_vitest(
        self, run_id: str, node_ids: List[str], env: Dict
    ) -> Tuple[List[TestExecution], int]:
        report_file = self.repo_path / f".fg_jest_{run_id}.json"

        # Determine runner: vitest or jest
        pkg_json = self.repo_path / "package.json"
        use_vitest = self.framework == FRAMEWORK_VITEST

        if use_vitest:
            cmd = ["npx", "--yes", "vitest", "run", "--reporter=json",
                   f"--outputFile={report_file}"]
        else:
            cmd = ["npx", "--yes", "jest", "--json", f"--outputFile={report_file}",
                   "--forceExit", "--passWithNoTests"]

        res = subprocess.run(
            cmd, cwd=str(self.repo_path), env=env,
            capture_output=True, text=True, timeout=300,
        )

        if not report_file.exists():
            logger.warning("Jest/Vitest JSON report not produced. Stderr: %s", res.stderr[:500])
            return [], res.returncode

        try:
            data = json.loads(report_file.read_text(encoding="utf-8"))
        except Exception:
            return [], res.returncode
        finally:
            try:
                report_file.unlink()
            except Exception:
                pass

        return self._parse_jest_json(data, run_id, use_vitest), res.returncode

    def _parse_jest_json(self, data: dict, run_id: str, vitest: bool) -> List[TestExecution]:
        executions = []
        idx = 0
        # Jest JSON: { testResults: [{ testFilePath, testResults: [...] }] }
        # Vitest JSON: similar structure under "testResults" or "files"
        test_suites = data.get("testResults") or data.get("files") or []
        for suite in test_suites:
            file_path = suite.get("testFilePath") or suite.get("name") or ""
            try:
                file_path = str(Path(file_path).relative_to(self.repo_path)).replace("\\", "/")
            except Exception:
                pass
            for t in suite.get("testResults") or suite.get("tests") or []:
                status_str = (t.get("status") or "").lower()
                status = {"passed": TestStatus.PASSED, "failed": TestStatus.FAILED,
                          "skipped": TestStatus.SKIPPED, "pending": TestStatus.SKIPPED}.get(
                    status_str, TestStatus.ERROR)
                full_name = " > ".join(t.get("ancestorTitles", [])) + " > " + t.get("title", "")
                full_name = full_name.lstrip(" > ")
                error_msg = "; ".join(t.get("failureMessages") or []) or None
                executions.append(TestExecution(
                    test_name=f"{file_path}::{full_name}",
                    file_path=file_path,
                    status=status,
                    duration=float(t.get("duration") or 0) / 1000.0,
                    error_message=_strip_paths(error_msg) if error_msg else None,
                    timestamp=datetime.now(timezone.utc),
                    run_id=run_id,
                    attempt_index=idx,
                ))
                idx += 1
        return executions

    # ------------------------------------------------------------------
    # Go
    # ------------------------------------------------------------------

    def _collect_go(self) -> List[str]:
        res = subprocess.run(
            ["go", "test", "./...", "-list", ".*"],
            cwd=str(self.repo_path), capture_output=True, text=True, timeout=60,
        )
        ids = [l.strip() for l in res.stdout.splitlines() if l.strip().startswith("Test")]
        if not ids:
            # Fall back to listing packages as IDs
            res2 = subprocess.run(
                ["go", "list", "./..."],
                cwd=str(self.repo_path), capture_output=True, text=True, timeout=30,
            )
            ids = [l.strip() for l in res2.stdout.splitlines() if l.strip()]
        if not ids:
            raise RuntimeError("No Go tests found. Ensure `go test ./...` works in this repository.")
        return ids

    def _run_go(
        self, run_id: str, node_ids: List[str], env: Dict
    ) -> Tuple[List[TestExecution], int]:
        res = subprocess.run(
            ["go", "test", "./...", "-v", "-json"],
            cwd=str(self.repo_path), env=env, capture_output=True, text=True, timeout=300,
        )
        return self._parse_go_json(res.stdout, run_id), res.returncode

    def _parse_go_json(self, stdout: str, run_id: str) -> List[TestExecution]:
        executions = []
        timings: Dict[str, float] = {}
        idx = 0
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except Exception:
                continue
            action = event.get("Action", "")
            test_name = event.get("Test")
            if not test_name:
                continue
            pkg = event.get("Package", "")
            full_name = f"{pkg}/{test_name}" if pkg else test_name
            elapsed = float(event.get("Elapsed") or 0)
            if action == "run":
                timings[full_name] = 0.0
            elif action in ("pass", "fail", "skip"):
                timings[full_name] = timings.get(full_name, 0.0) + elapsed
                status = {"pass": TestStatus.PASSED, "fail": TestStatus.FAILED,
                          "skip": TestStatus.SKIPPED}.get(action, TestStatus.ERROR)
                executions.append(TestExecution(
                    test_name=full_name,
                    file_path=pkg.replace(".", "/") if pkg else "",
                    status=status,
                    duration=timings.get(full_name, elapsed),
                    timestamp=datetime.now(timezone.utc),
                    run_id=run_id,
                    attempt_index=idx,
                ))
                idx += 1
        return executions

    # ------------------------------------------------------------------
    # Maven
    # ------------------------------------------------------------------

    def _collect_maven(self) -> List[str]:
        found = list(self.repo_path.glob("**/src/test/**/*.java"))
        if not found:
            raise RuntimeError("No Java test files found under src/test/.")
        return [str(f.relative_to(self.repo_path)).replace("\\", "/") for f in found[:200]]

    def _run_maven(self, run_id: str, env: Dict) -> Tuple[List[TestExecution], int]:
        mvn = "mvnw" if (self.repo_path / "mvnw").exists() else "mvn"
        res = subprocess.run(
            [mvn, "test", "-B", "--no-transfer-progress"],
            cwd=str(self.repo_path), env=env, capture_output=True, text=True, timeout=600,
        )
        executions = self._parse_surefire_reports(run_id)
        if not executions:
            executions = self._parse_maven_stdout(res.stdout, run_id)
        return executions, res.returncode

    def _parse_surefire_reports(self, run_id: str) -> List[TestExecution]:
        """Parse Maven Surefire XML reports."""
        import xml.etree.ElementTree as ET
        executions = []
        idx = 0
        for xml_file in self.repo_path.glob("**/surefire-reports/TEST-*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                class_name = root.get("name", "")
                for tc in root.findall("testcase"):
                    name = f"{class_name}#{tc.get('name', '')}"
                    duration = float(tc.get("time") or 0)
                    failure = tc.find("failure") or tc.find("error")
                    skipped = tc.find("skipped")
                    if skipped is not None:
                        status = TestStatus.SKIPPED
                        error_msg = None
                    elif failure is not None:
                        status = TestStatus.FAILED
                        error_msg = _strip_paths((failure.get("message") or failure.text or "")[:500])
                    else:
                        status = TestStatus.PASSED
                        error_msg = None
                    executions.append(TestExecution(
                        test_name=name,
                        file_path=str(xml_file.relative_to(self.repo_path)),
                        status=status,
                        duration=duration,
                        error_message=error_msg,
                        timestamp=datetime.now(timezone.utc),
                        run_id=run_id,
                        attempt_index=idx,
                    ))
                    idx += 1
            except Exception as e:
                logger.debug("Failed to parse %s: %s", xml_file, e)
        return executions

    def _parse_maven_stdout(self, stdout: str, run_id: str) -> List[TestExecution]:
        """Fallback: extract pass/fail from Maven console output."""
        executions = []
        idx = 0
        for line in stdout.splitlines():
            m = re.search(r'\[INFO\] Tests run: (\d+).*?Failures: (\d+).*?Errors: (\d+).*?Skipped: (\d+)', line)
            if m:
                total, failures, errors, skipped = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                for _ in range(total - failures - errors - skipped):
                    executions.append(TestExecution(test_name=f"maven_test_{idx}", file_path="",
                        status=TestStatus.PASSED, duration=0.0,
                        timestamp=datetime.now(timezone.utc), run_id=run_id, attempt_index=idx))
                    idx += 1
                for _ in range(failures + errors):
                    executions.append(TestExecution(test_name=f"maven_test_{idx}", file_path="",
                        status=TestStatus.FAILED, duration=0.0,
                        timestamp=datetime.now(timezone.utc), run_id=run_id, attempt_index=idx))
                    idx += 1
        return executions

    # ------------------------------------------------------------------
    # Gradle
    # ------------------------------------------------------------------

    def _collect_gradle(self) -> List[str]:
        found = list(self.repo_path.glob("**/src/test/**/*.java")) + \
                list(self.repo_path.glob("**/src/test/**/*.kt"))
        if not found:
            raise RuntimeError("No Java/Kotlin test files found under src/test/.")
        return [str(f.relative_to(self.repo_path)).replace("\\", "/") for f in found[:200]]

    def _run_gradle(self, run_id: str, env: Dict) -> Tuple[List[TestExecution], int]:
        gradle = "./gradlew" if (self.repo_path / "gradlew").exists() else "gradle"
        res = subprocess.run(
            [gradle, "test", "--continue"],
            cwd=str(self.repo_path), env=env, capture_output=True, text=True, timeout=600,
        )
        executions = self._parse_gradle_xml_reports(run_id)
        return executions, res.returncode

    def _parse_gradle_xml_reports(self, run_id: str) -> List[TestExecution]:
        """Parse Gradle XML test reports (same Surefire XML format)."""
        return self._parse_surefire_reports(run_id)  # Same XML schema

    # ------------------------------------------------------------------
    # RSpec
    # ------------------------------------------------------------------

    def _collect_rspec(self) -> List[str]:
        found = list(self.repo_path.glob("spec/**/*_spec.rb"))
        if not found:
            raise RuntimeError("No RSpec files found under spec/.")
        return [str(f.relative_to(self.repo_path)).replace("\\", "/") for f in found[:200]]

    def _run_rspec(
        self, run_id: str, node_ids: List[str], env: Dict
    ) -> Tuple[List[TestExecution], int]:
        report_file = self.repo_path / f".fg_rspec_{run_id}.json"
        cmd = ["bundle", "exec", "rspec", "--format", "json", "--out", str(report_file)] + node_ids
        res = subprocess.run(
            cmd, cwd=str(self.repo_path), env=env, capture_output=True, text=True, timeout=300,
        )
        if not report_file.exists():
            return [], res.returncode
        try:
            data = json.loads(report_file.read_text(encoding="utf-8"))
        except Exception:
            return [], res.returncode
        finally:
            try:
                report_file.unlink()
            except Exception:
                pass
        return self._parse_rspec_json(data, run_id), res.returncode

    def _parse_rspec_json(self, data: dict, run_id: str) -> List[TestExecution]:
        executions = []
        for idx, ex in enumerate(data.get("examples", [])):
            status_str = ex.get("status", "").lower()
            status = {"passed": TestStatus.PASSED, "failed": TestStatus.FAILED,
                      "pending": TestStatus.SKIPPED}.get(status_str, TestStatus.ERROR)
            error_msg = None
            if ex.get("exception"):
                error_msg = _strip_paths(str(ex["exception"].get("message", ""))[:500])
            executions.append(TestExecution(
                test_name=ex.get("full_description", ex.get("id", f"spec_{idx}")),
                file_path=ex.get("file_path", ""),
                status=status,
                duration=float(ex.get("run_time") or 0),
                error_message=error_msg,
                timestamp=datetime.now(timezone.utc),
                run_id=run_id,
                attempt_index=idx,
            ))
        return executions

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------

    def _git_branch(self) -> str:
        try:
            r = subprocess.run(["git", "branch", "--show-current"],
                               cwd=str(self.repo_path), capture_output=True, text=True)
            return r.stdout.strip() or "main"
        except Exception:
            return "main"

    def _git_sha(self) -> str:
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"],
                               cwd=str(self.repo_path), capture_output=True, text=True)
            return r.stdout.strip() or "unknown"
        except Exception:
            return "unknown"
