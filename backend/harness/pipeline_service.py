"""Core pipeline execution service for FlakeGuard (F1 -> F2 -> F3 -> F4)."""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.detection import DetectionResult, TestStatus
from backend.harness.runner import TestRunner, normalize_pytest_target
from backend.harness.executor import TestExecutor
from backend.harness.analyzer import TestAnalyzer
from backend.harness.validate import RepositoryValidator
from backend.bob.agent import BobAgent
from backend.remediation.generator import FixGenerator
from backend.auditor.auditor import Auditor

logger = logging.getLogger(__name__)


def _empty_detection(total_runs: int = 0) -> Dict[str, Any]:
    return {
        "total_runs": total_runs,
        "total_unique_tests": 0,
        "flaky_tests_count": 0,
        "confidence": 0.0,
        "flaky_tests": [],
        "stable_tests": [],
        "rejected_tests": [],
    }


def _empty_audit() -> Dict[str, Any]:
    return {
        "report_id": "",
        "total_quarantined": 0,
        "diagnosed_count": 0,
        "fixable_count": 0,
        "unexplained_count": 0,
        "tests": [],
    }


def _empty_metrics() -> Dict[str, Any]:
    return {
        "total_tests": 0,
        "flaky_tests": 0,
        "flakiness_rate": 0.0,
        "active_quarantined": 0,
        "fixes_applied": 0,
        "avg_resolution_time": 0.0,
    }


def _error_response(
    pipeline_id: str,
    status: str,
    source_type: str,
    repo_url: Optional[str],
    branch: Optional[str],
    commit_sha: Optional[str],
    started_at: str,
    errors: List[Dict[str, str]],
    validation: Optional[Dict[str, Any]] = None,
    message: str = "",
    requested_runs: int = 0,
) -> Dict[str, Any]:
    """Return a complete, empty schema without claiming unobserved executions."""
    return {
        "pipeline_id": pipeline_id,
        "status": status,
        "source_type": source_type,
        "repository": repo_url or "",
        "branch": branch or "main",
        "commit_sha": commit_sha or "unknown",
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "runs": 0,
        "requested_runs": requested_runs,
        "analysis_mode": "not_executed",
        "validation": validation or {},
        "message": message,
        "detection": _empty_detection(),
        "classifications": [],
        "fixes": [],
        "quarantine_audit": _empty_audit(),
        "quarantine_list": [],
        "root_causes_chart": [],
        "metrics": _empty_metrics(),
        "errors": errors,
    }


def _relative_path(repo: Path, file_path: str) -> str:
    """Canonical API identity; never expose or resolve files outside this repo."""
    normalized = normalize_pytest_target(str(file_path), repo)
    path = Path(normalized)
    absolute = path if path.is_absolute() else repo / path
    try:
        return absolute.resolve().relative_to(repo).as_posix()
    except ValueError as exc:
        raise ValueError("Test file is outside the analyzed repository") from exc


def find_test_file(repo: Path, file_path: str) -> Optional[Path]:
    """Resolve an exact repository path, not the first same-named file on disk."""
    target = repo / _relative_path(repo, file_path)
    return target if target.is_file() else None


class PipelineService:
    """Execute supported tests; source heuristics are not execution evidence."""

    EXECUTION_TIMEOUT_SECONDS = 300.0

    @classmethod
    def _build_details(cls, repo_path: Path, detection: DetectionResult) -> Dict[str, Any]:
        """Worker boundary for source I/O and Bob's synchronous provider clients."""
        return asyncio.run(cls._classify_remediate_audit(repo_path, detection))

    @classmethod
    async def _classify_remediate_audit(
        cls, repo_path: Path, detection: DetectionResult
    ) -> Dict[str, Any]:
        classifications = []
        fixes = []
        errors = []
        agent = None
        try:
            if detection.flaky_tests:
                agent = BobAgent()
                sources: Dict[str, str] = {}
                file_cache: Dict[str, str] = {}
                tests_with_sources = []
                for test in detection.flaky_tests:
                    target = find_test_file(repo_path, test.file_path)
                    if target is None:
                        errors.append({
                            "code": "SOURCE_UNAVAILABLE",
                            "message": f"Source unavailable for {test.test_name}; classification skipped.",
                        })
                        continue
                    key = str(target)
                    if key not in file_cache:
                        file_cache[key] = target.read_text(encoding="utf-8", errors="replace")
                    sources[test.test_name] = file_cache[key]
                    # Bob's extractor needs an actual path, but public detection
                    # and joins must retain repository-relative identities.
                    tests_with_sources.append(test.model_copy(update={"file_path": key}))

                classifications = await agent.classify_batch(tests_with_sources, sources)
                generator = FixGenerator()
                for classification in classifications:
                    source = sources.get(classification.test_name, "")
                    # The generator reads the real file through its absolute path.
                    fix = await generator.generate_fix(classification, source)
                    public_path = _relative_path(repo_path, classification.file_path)
                    classification.file_path = public_path
                    fix.file_path = public_path
                    for suggestion in fix.suggestions:
                        if suggestion.diff:
                            suggestion.diff.file_path = public_path
                            # Diff headers are display/patch identities too.
                            absolute_path = str(repo_path / public_path)
                            suggestion.diff.unified_diff = suggestion.diff.unified_diff.replace(
                                f"a/{absolute_path}", f"a/{public_path}"
                            ).replace(f"b/{absolute_path}", f"b/{public_path}")
                    fixes.append(fix)
        finally:
            client = getattr(agent, "llm_client", None)
            if client is not None and hasattr(client, "close"):
                try:
                    client.close()
                except Exception:
                    logger.warning("Could not close pipeline provider client", exc_info=True)

        audit_data = _empty_audit()
        quarantine_path = repo_path / "QUARANTINE.md"
        # Missing quarantine is empty, not the unrelated sample repository's list.
        # Audit also runs when there are no flaky tests to classify.
        if quarantine_path.is_file():
            report = Auditor().audit_quarantine(
                quarantine_path=str(quarantine_path),
                classifications=classifications,
                repo_path=str(repo_path),
            )
            audit_data = {
                "report_id": report.report_id,
                "total_quarantined": report.total_quarantined,
                "diagnosed_count": report.diagnosed_count,
                "fixable_count": report.fixable_count,
                "unexplained_count": report.unexplained_count,
                "tests": [
                    {
                        "test_name": t.test_name,
                        "status": t.status.value,
                        "diagnosed": t.diagnosed,
                        "root_cause": t.root_cause,
                        "confidence": t.confidence,
                        "fixable": t.fixable,
                        "fix_strategy": t.fix_strategy,
                        "quarantine_reason": t.quarantine_reason,
                        "quarantined_at": t.quarantined_at.isoformat() if t.quarantined_at else None,
                        "source": "QUARANTINE.md",
                    }
                    for t in report.quarantined_tests
                ],
            }

        return {
            "classifications": [
                {
                    "classification_id": c.classification_id,
                    "test_name": c.test_name,
                    "file_path": c.file_path,
                    "root_cause": c.root_cause.value,
                    "confidence": c.confidence.value,
                    "evidence": [e.description for e in c.evidence],
                    "reasoning": c.reasoning,
                    "suggested_fix_area": c.suggested_fix_area,
                }
                for c in classifications
            ],
            "fixes": [fix.model_dump(mode="json") for fix in fixes],
            "quarantine_audit": audit_data,
            "errors": errors,
        }

    @classmethod
    async def run_pipeline(
        cls,
        repo_path: Path,
        num_runs: int = 5,
        test_pattern: Optional[str] = None,
        source_type: str = "local",
        repo_url: Optional[str] = None,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run F1-F4 without replacing errors/unsupported code with invented data."""
        pipeline_id = str(uuid.uuid4())
        repo_path = Path(repo_path).resolve()
        started_at = datetime.now(timezone.utc).isoformat()
        validation: Dict[str, Any] = {}

        def failure(status: str, code: str, message: str) -> Dict[str, Any]:
            return _error_response(
                pipeline_id, status, source_type, repo_url or str(repo_path),
                branch, commit_sha, started_at,
                [{"code": code, "message": message}], validation, message, num_runs,
            )

        if not 2 <= num_runs <= 20:
            return failure("error", "INVALID_RUN_COUNT", "Number of runs must be between 2 and 20.")
        if not await asyncio.to_thread(repo_path.is_dir):
            return failure("error", "INVALID_REPOSITORY", "Repository path is not an existing directory.")

        try:
            validation = await asyncio.to_thread(
                RepositoryValidator.detect_repository_compatibility, repo_path
            )
        except Exception:
            logger.exception("Repository validation failed")
            return failure("error", "VALIDATION_FAILED", "Could not inspect repository compatibility.")

        if not validation["compatible"]:
            return failure("no_tests", "NO_TESTS", "No supported test framework or source files were found.")
        if validation.get("framework") != "pytest" or validation.get("mode") != "dynamic":
            framework = validation.get("framework", "unknown")
            return failure(
                "unsupported", "UNSUPPORTED_FRAMEWORK",
                f"Detected {framework}; reliable test execution is not supported by this pipeline yet. "
                "No tests were run. Static source indicators are not flaky-test evidence.",
            )

        runner = TestRunner(repo_path)
        try:
            # Cached by the runner: preflight happens once, not for every rerun.
            test_ids = await asyncio.to_thread(runner.collect_test_ids)
            if not test_ids or (test_pattern and not any(test_pattern in node for node in test_ids)):
                return failure("no_tests", "NO_TESTS", "No tests matched the requested selection.")
            test_runs = await asyncio.wait_for(
                TestExecutor(runner).execute_multiple_runs(num_runs=num_runs, test_pattern=test_pattern),
                timeout=cls.EXECUTION_TIMEOUT_SECONDS,
            )
            for run in test_runs:
                for execution in run.executions:
                    execution.test_name = normalize_pytest_target(execution.test_name, repo_path)
                    execution.file_path = _relative_path(repo_path, execution.file_path)
                run.ordering = [normalize_pytest_target(node, repo_path) for node in run.ordering]
            detection = await asyncio.to_thread(TestAnalyzer().analyze_runs, test_runs)
        except TimeoutError:
            return failure("error", "EXECUTION_TIMEOUT", "Test execution exceeded the pipeline time budget.")
        except Exception:
            logger.exception("Dynamic test execution failed")
            return failure(
                "error", "EXECUTION_FAILED",
                "Test collection or execution failed. Check the runner environment and test configuration; "
                "no static results have been substituted.",
            )

        if not detection.total_unique_tests:
            return failure("no_tests", "NO_TESTS", "The runner returned no test executions.")

        try:
            details = await asyncio.to_thread(cls._build_details, repo_path, detection)
        except Exception:
            logger.exception("Classification, remediation, or audit failed")
            details = {
                "classifications": [], "fixes": [], "quarantine_audit": _empty_audit(),
                "errors": [{"code": "POSTPROCESSING_FAILED", "message": "Detection completed, but classification, remediation, or audit failed."}],
            }

        # An all-error run is not a clean suite. Preserve observations, but make
        # execution problems visible instead of reporting a successful analysis.
        if any(run.returncode not in (None, 0, 1) for run in test_runs):
            details["errors"].append({"code": "RUNNER_ERROR", "message": "One or more runs ended with a runner or collection error."})
        elif any(e.status == TestStatus.ERROR for run in test_runs for e in run.executions):
            details["errors"].append({"code": "TEST_EXECUTION_ERROR", "message": "One or more tests had setup or teardown errors; analysis is incomplete."})
        elif not any(e.status in (TestStatus.PASSED, TestStatus.FAILED) for run in test_runs for e in run.executions):
            details["errors"].append({"code": "NO_EXECUTABLE_RESULTS", "message": "Only skipped or error outcomes were observed; flakiness is inconclusive."})

        cause_counts: Dict[str, int] = {}
        for classification in details["classifications"]:
            cause = classification["root_cause"]
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        quarantine_list = [
            {
                "quarantine_id": str(uuid.uuid4())[:8],
                "test_name": test["test_name"],
                "file_path": test["test_name"].split("::", 1)[0] if "::" in test["test_name"] else "",
                "reason": test.get("quarantine_reason") or "Quarantined test",
                "status": test["status"],
                "quarantined_at": test.get("quarantined_at"),
            }
            for test in details["quarantine_audit"]["tests"]
        ]

        return {
            "pipeline_id": pipeline_id,
            "status": "error" if details["errors"] else "success",
            "source_type": source_type,
            "repository": repo_url or str(repo_path),
            "branch": branch or test_runs[0].branch,
            "commit_sha": commit_sha or test_runs[0].commit_sha,
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "runs": len(test_runs),
            "requested_runs": num_runs,
            "analysis_mode": "dynamic",
            "validation": validation,
            "detection": {
                "total_runs": len(test_runs),
                "total_unique_tests": detection.total_unique_tests,
                "flaky_tests_count": len(detection.flaky_tests),
                "confidence": detection.detection_confidence,
                "flaky_tests": [test.model_dump(mode="json") for test in detection.flaky_tests],
                "stable_tests": list(detection.stable_tests),
                "rejected_tests": detection.rejected_tests,
            },
            **details,
            "quarantine_list": quarantine_list,
            "root_causes_chart": [
                {"root_cause": cause, "count": count, "percentage": round(count / len(details["classifications"]) * 100, 1)}
                for cause, count in cause_counts.items()
            ],
            "metrics": {
                **_empty_metrics(),
                "total_tests": detection.total_unique_tests,
                "flaky_tests": len(detection.flaky_tests),
                "flakiness_rate": round(len(detection.flaky_tests) / detection.total_unique_tests * 100, 1),
                "active_quarantined": details["quarantine_audit"]["total_quarantined"],
                # Proposals are not applied or verified fixes.
                "fixes_applied": 0,
            },
        }
