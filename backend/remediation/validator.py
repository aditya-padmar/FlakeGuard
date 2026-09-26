"""Validate proposed Python source in a disposable repository copy.

Syntax and target checks happen before copying files or launching pytest. The
original repository is never patched or restored. This isolates normal test
writes, but is not an OS-level sandbox for executing untrusted test code.
"""
import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Outcome of validating a proposed fix."""

    fix_id: str
    test_name: str
    # How many runs were attempted
    runs: int
    # How many of those passed
    passes: int
    # Whether the fix is considered stable
    fix_valid: bool
    # Remaining flakiness rate (0.0 = fully stable)
    flakiness_rate: float
    # Human-readable verdict
    verdict: str
    # Raw pytest stdout/stderr from the last run (for debugging)
    last_output: str = ""
    error: Optional[str] = None

    @classmethod
    def skipped(cls, fix_id: str, test_name: str, reason: str) -> "ValidationResult":
        return cls(
            fix_id=fix_id,
            test_name=test_name,
            runs=0,
            passes=0,
            fix_valid=False,
            flakiness_rate=1.0,
            verdict=f"Validation skipped: {reason}",
        )


class FixValidator:
    """Re-run a selected test against full patched source without applying it."""

    STABILITY_THRESHOLD = 0.80
    _COPY_EXCLUDES = {
        ".git", ".hg", ".svn", ".venv", "venv", ".tox", ".nox",
        "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    }

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    async def validate(
        self,
        fix_id: str,
        file_path: str,
        patched_source: str,
        test_name: str,
        runs: int = 5,
    ) -> ValidationResult:
        """Validate full source, not a patch, in a temporary repository copy.

        ``file_path`` may be absolute or repo-relative. ``test_name`` may be a
        full pytest node-id or just ``TestClass::test_method`` / ``test_function``.
        File copying and bounded subprocess calls run off the async event loop.
        """
        return await asyncio.to_thread(
            self._validate, fix_id, file_path, patched_source, test_name, runs
        )

    def _validate(
        self,
        fix_id: str,
        file_path: str,
        patched_source: str,
        test_name: str,
        runs: int,
    ) -> ValidationResult:
        try:
            if isinstance(runs, bool) or not isinstance(runs, int) or runs < 1:
                raise ValueError("Validation runs must be a positive integer")
            if not isinstance(patched_source, str):
                raise ValueError("Full patched source is required; a unified diff is not source")
            if not patched_source.strip():
                raise ValueError("Patched source is empty; there is no test to validate")
            original_path = self._resolve_source_path(file_path)
            if original_path.suffix.lower() != ".py":
                raise ValueError("Only Python test files can be validated with pytest")
            # compile (without execution) catches more than ast.parse, including
            # a return outside a function. Invalid proposals never reach disk.
            compile(patched_source, str(original_path), "exec", dont_inherit=True)
            relative_path = original_path.relative_to(self.repo_path)
            node_id = self._test_node_id(original_path, relative_path, test_name)
        except (OSError, SyntaxError, TypeError, ValueError) as exc:
            result = ValidationResult.skipped(fix_id, test_name, str(exc))
            result.error = str(exc)
            return result

        passes = 0
        attempted_runs = 0
        last_output = ""
        try:
            with tempfile.TemporaryDirectory(prefix="flakeguard-validate-") as temp_dir:
                workspace = Path(temp_dir) / "repo"
                if workspace.is_relative_to(self.repo_path):
                    raise ValueError("Validation workspace must be outside the repository")
                # Copy once per proposal, not per run. Never link files back to
                # the original, or traverse repository symlinks/junctions.
                shutil.copytree(self.repo_path, workspace, ignore=self._ignore_copy_paths)
                patched_path = workspace / relative_path
                with patched_path.open("w", encoding="utf-8", newline="") as handle:
                    handle.write(patched_source)

                for _ in range(runs):
                    attempted_runs += 1
                    passed, last_output = self._run_test_once(node_id, repo_path=workspace)
                    passes += int(passed)
        except Exception as exc:
            if isinstance(exc, (subprocess.CalledProcessError, subprocess.TimeoutExpired)):
                last_output = self._output_text(exc.stdout, exc.stderr)
            return ValidationResult(
                fix_id=fix_id,
                test_name=test_name,
                runs=attempted_runs,
                passes=passes,
                fix_valid=False,
                flakiness_rate=1.0 - passes / max(attempted_runs, 1),
                verdict="Validation error",
                last_output=last_output,
                error=str(exc),
            )

        flakiness_rate = 1.0 - passes / attempted_runs
        fix_valid = passes / attempted_runs >= self.STABILITY_THRESHOLD
        if fix_valid:
            verdict = (
                f"Fix validated: {passes}/{attempted_runs} runs passed "
                f"(flakiness reduced to {flakiness_rate:.0%})"
            )
        else:
            verdict = (
                f"Fix insufficient: only {passes}/{attempted_runs} runs passed "
                f"(flakiness still {flakiness_rate:.0%})"
            )
        return ValidationResult(
            fix_id=fix_id,
            test_name=test_name,
            runs=attempted_runs,
            passes=passes,
            fix_valid=fix_valid,
            flakiness_rate=flakiness_rate,
            verdict=verdict,
            last_output=last_output,
        )

    def _resolve_source_path(self, file_path: str) -> Path:
        """Resolve only inside this repository, without filename-wide searches."""
        path = Path(file_path)
        # The second candidate preserves callers passing cwd-relative paths
        # such as sample-repo/tests/test_example.py with repo_path=sample-repo.
        candidates = (path,) if path.is_absolute() else (self.repo_path / path, path)
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_relative_to(self.repo_path) and resolved.is_file():
                return resolved
        raise ValueError(f"Source file not found inside repository: {file_path}")

    def _test_node_id(self, original_path: Path, relative_path: Path, test_name: str) -> str:
        if not isinstance(test_name, str) or not test_name.strip():
            raise ValueError("A test name is required for scoped validation")
        file_part, separator, selector = test_name.partition("::")
        # Parameter IDs may themselves contain paths or '::'. Do not interpret
        # these as a file prefix when the caller supplied a bare test name.
        name_part = file_part.split("[", 1)[0]
        if name_part.endswith(".py") or "/" in name_part or "\\" in name_part:
            if self._resolve_source_path(file_part) != original_path:
                raise ValueError("Test node-id does not refer to the patched source file")
            if not separator or not selector:
                raise ValueError("A specific test selector is required, not only a file")
        else:
            selector = test_name
        return relative_path.as_posix() + "::" + selector

    @classmethod
    def _ignore_copy_paths(cls, directory: str, names: list[str]) -> set[str]:
        ignored = set(names) & cls._COPY_EXCLUDES
        for name in set(names) - ignored:
            path = Path(directory) / name
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                ignored.add(name)
        return ignored

    @staticmethod
    def _output_text(stdout, stderr) -> str:
        return "".join(
            part.decode("utf-8", errors="replace") if isinstance(part, bytes) else (part or "")
            for part in (stdout, stderr)
        )

    def _run_test_once(
        self, test_name: str, *, repo_path: Optional[Path] = None
    ) -> tuple[bool, str]:
        """Run only the selected node; stop retries on collection/runner errors."""
        cwd = repo_path if repo_path is not None else self.repo_path
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # Ambient/repository addopts must not inject additional test targets.
        env.pop("PYTEST_ADDOPTS", None)
        python_paths = [str(cwd)]
        for entry in env.get("PYTHONPATH", "").split(os.pathsep):
            if entry:
                path = Path(entry)
                if not path.is_absolute():
                    path = cwd / path
                else:
                    path = path.resolve()
                    if path.is_relative_to(self.repo_path):
                        path = cwd / path.relative_to(self.repo_path)
                python_paths.append(str(path))
        env["PYTHONPATH"] = os.pathsep.join(python_paths)
        cmd = [
            sys.executable, "-m", "pytest",
            "--tb=short", "-q", "--no-header",
            "--rootdir=.", "--confcutdir=.", "-o", "addopts=",
            "--", test_name,
        ]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode not in (0, 1):
            # A broken collection or invocation is not stochastic test failure;
            # rerunning it N times only wastes time.
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )
        return result.returncode == 0, self._output_text(result.stdout, result.stderr)
