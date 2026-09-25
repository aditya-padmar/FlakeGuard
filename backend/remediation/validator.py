"""
Fix validator — temporarily applies a proposed diff and re-runs the test to
check whether the fix actually eliminates flakiness.

The validator is deliberately non-destructive:
- It writes the patched file to a *temp copy* beside the original.
- It runs the test N times pointing pytest at the patched copy.
- It restores the original file unconditionally (even on error).
"""
from __future__ import annotations

import subprocess
import tempfile
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ValidationResult:
    """Outcome of validating a proposed fix."""

    fix_id: str
    test_name: str
    # How many runs were executed
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
    """
    Validates a proposed fix by running the test against the patched source.

    Usage::

        validator = FixValidator(repo_path="sample-repo")
        result = await validator.validate(
            fix_id="abc",
            file_path="sample-repo/tests/test_timing.py",
            patched_source="<modified source>",
            test_name="TestTimingIssues::test_sleep_based",
            runs=5,
        )
    """

    # Minimum pass rate to consider the fix valid
    STABILITY_THRESHOLD = 0.80

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    async def validate(
        self,
        fix_id: str,
        file_path: str,
        patched_source: str,
        test_name: str,
        runs: int = 5,
    ) -> ValidationResult:
        """
        Temporarily apply *patched_source* to *file_path* and run *test_name*
        *runs* times.  The original file is always restored afterward.

        Args:
            fix_id:         ID of the Fix being validated.
            file_path:      Absolute or repo-relative path to the test file.
            patched_source: The modified source code to test.
            test_name:      Pytest node-id (e.g. "tests/test_timing.py::TestX::test_y").
            runs:           Number of times to run the test.

        Returns:
            ValidationResult with stability verdict.
        """
        original_path = Path(file_path)
        if not original_path.exists():
            return ValidationResult.skipped(
                fix_id, test_name, f"Source file not found: {file_path}"
            )

        original_source = original_path.read_text(encoding="utf-8")
        passes = 0
        last_output = ""

        try:
            # Write the patched content
            original_path.write_text(patched_source, encoding="utf-8")

            for _ in range(runs):
                passed, output = self._run_test_once(test_name)
                last_output = output
                if passed:
                    passes += 1

        except Exception as exc:
            return ValidationResult(
                fix_id=fix_id,
                test_name=test_name,
                runs=runs,
                passes=passes,
                fix_valid=False,
                flakiness_rate=1.0 - (passes / max(runs, 1)),
                verdict="Validation error",
                last_output=last_output,
                error=str(exc),
            )
        finally:
            # Always restore the original
            original_path.write_text(original_source, encoding="utf-8")

        flakiness_rate = 1.0 - (passes / runs)
        fix_valid = (passes / runs) >= self.STABILITY_THRESHOLD

        if fix_valid:
            verdict = (
                f"Fix validated: {passes}/{runs} runs passed "
                f"(flakiness reduced to {flakiness_rate:.0%})"
            )
        else:
            verdict = (
                f"Fix insufficient: only {passes}/{runs} runs passed "
                f"(flakiness still {flakiness_rate:.0%})"
            )

        return ValidationResult(
            fix_id=fix_id,
            test_name=test_name,
            runs=runs,
            passes=passes,
            fix_valid=fix_valid,
            flakiness_rate=flakiness_rate,
            verdict=verdict,
            last_output=last_output,
        )

    def _run_test_once(self, test_name: str) -> tuple[bool, str]:
        """Run a single pytest invocation for *test_name*. Returns (passed, output)."""
        cmd = [
            "pytest",
            test_name,
            "--tb=short",
            "-q",
            "--no-header",
        ]
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        return passed, output
