"""Synthetic pipeline/runner regressions: no repositories or providers executed."""
import asyncio
import importlib
import io
import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, UploadFile

from backend.bob.agent import BobAgent
from backend.harness.executor import TestExecutor
from backend.harness.runner import TestRunner
from backend.harness.validate import RepositoryValidator
from backend.models.classification import Classification, Confidence, RootCauseType
from backend.models.detection import DetectionResult, FlakyTest, TestExecution, TestRun, TestStatus
from backend.models.remediation import CodeDiff, Fix, FixStatus, FixSuggestion, FixType

@pytest.fixture
def modules(tmp_path, monkeypatch):
    """Route imports allocate local stores; contain them in pytest's temp dir."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(BobAgent, "_setup_llm", lambda self: None)
    pipeline = importlib.import_module("backend.harness.pipeline_service")
    routes = importlib.import_module("backend.api.routes.repository")
    monkeypatch.setattr(routes, "_analysis_history", [])
    monkeypatch.setattr(routes, "_latest_analysis", None)
    return pipeline, routes


def _validation(framework="pytest"):
    return {
        "compatible": True,
        "confidence": 1.0,
        "primary_language": "python" if framework == "pytest" else "javascript/typescript",
        "framework": framework,
        "mode": "dynamic" if framework == "pytest" else "static_audit",
        "indicators": [], "warnings": [], "test_files": [], "config_files": [],
    }


def _run(index, status=TestStatus.PASSED, file_path="tests/test_unit.py", returncode=0):
    node = f"{file_path}::test_unit"
    return TestRun(
        run_id=f"run-{index}", repository="synthetic", branch="test", commit_sha="abc",
        timestamp=datetime.now(timezone.utc), returncode=returncode,
        executions=[TestExecution(test_name=node, file_path=file_path, status=status, duration=0.01)],
        ordering=[node], total_tests=1,
    )


def _mock_execution(monkeypatch, pipeline, runs=None):
    monkeypatch.setattr(RepositoryValidator, "detect_repository_compatibility", Mock(return_value=_validation()))
    monkeypatch.setattr(TestRunner, "collect_test_ids", Mock(return_value=["tests/test_unit.py::test_unit"]))
    supplied = [_run(0), _run(1)] if runs is None else runs

    async def execute(self, **kwargs):
        return supplied

    monkeypatch.setattr(TestExecutor, "execute_multiple_runs", execute)


@pytest.mark.parametrize("framework,language", [("jest", "javascript/typescript"), ("go", "go"), ("maven", "java")])
def test_validator_preserves_framework_identity(tmp_path, monkeypatch, framework, language):
    monkeypatch.setattr(
        "backend.harness.validate.detect_framework",
        lambda _: dict(framework=framework, language=language, confidence=0.9, indicators=[], test_files=[]),
    )
    result = RepositoryValidator.detect_repository_compatibility(tmp_path)
    assert result["framework"] == framework
    assert result["primary_language"] == language
    assert result["mode"] == "static_audit"


@pytest.mark.asyncio
async def test_unsupported_framework_does_not_execute_or_invent_outcomes(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    monkeypatch.setattr(RepositoryValidator, "detect_repository_compatibility", Mock(return_value=_validation("jest")))
    monkeypatch.setattr(TestRunner, "collect_test_ids", Mock(side_effect=AssertionError("must not execute pytest")))
    monkeypatch.setattr(pipeline, "BobAgent", Mock(side_effect=AssertionError("must not classify source as execution")))
    result = await pipeline.PipelineService.run_pipeline(tmp_path, num_runs=5)
    assert result["status"] == "unsupported"
    assert result["validation"]["framework"] == "jest"
    assert result["runs"] == result["detection"]["total_runs"] == 0
    assert result["detection"]["flaky_tests"] == []
    assert result["classifications"] == result["fixes"] == []
    assert result["quarantine_audit"]["tests"] == []


@pytest.mark.asyncio
async def test_runner_failure_does_not_become_static_success(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    _mock_execution(monkeypatch, pipeline)
    monkeypatch.setattr(TestRunner, "collect_test_ids", Mock(side_effect=RuntimeError("collection import failed")))
    result = await pipeline.PipelineService.run_pipeline(tmp_path)
    assert result["status"] == "error"
    assert result["errors"][0]["code"] == "EXECUTION_FAILED"
    assert result["runs"] == 0
    assert result["detection"]["flaky_tests"] == []


@pytest.mark.asyncio
async def test_pipeline_empty_filter_stops_before_repeated_runs(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    _mock_execution(monkeypatch, pipeline)
    called = Mock(side_effect=AssertionError("empty filter must not launch plan"))
    monkeypatch.setattr(TestExecutor, "execute_multiple_runs", called)
    result = await pipeline.PipelineService.run_pipeline(tmp_path, test_pattern="no_match")
    assert result["status"] == "no_tests"
    called.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_reports_actual_counts_and_empty_audit(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    _mock_execution(monkeypatch, pipeline)
    result = await pipeline.PipelineService.run_pipeline(tmp_path, num_runs=5)
    assert result["status"] == "success"
    assert result["runs"] == result["detection"]["total_runs"] == 2
    assert result["requested_runs"] == 5
    assert result["metrics"]["total_tests"] == 1
    assert result["metrics"]["fixes_applied"] == 0
    assert result["metrics"]["avg_resolution_time"] == 0
    assert result["quarantine_audit"] == pipeline._empty_audit()


@pytest.mark.asyncio
async def test_pipeline_marks_fixture_errors_incomplete(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    _mock_execution(monkeypatch, pipeline, [_run(0), _run(1, TestStatus.ERROR, returncode=1)])
    result = await pipeline.PipelineService.run_pipeline(tmp_path)
    assert result["status"] == "error"
    assert result["errors"][0]["code"] == "TEST_EXECUTION_ERROR"
    assert result["runs"] == 2


@pytest.mark.asyncio
async def test_pipeline_offloads_validation_collection_and_postprocessing(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    _mock_execution(monkeypatch, pipeline)
    main_thread = threading.get_ident()
    observed = []

    def validation(path):
        observed.append(threading.get_ident())
        return _validation()

    def collection(self):
        observed.append(threading.get_ident())
        return ["tests/test_unit.py::test_unit"]

    def details(cls, path, detection):
        observed.append(threading.get_ident())
        return {"classifications": [], "fixes": [], "quarantine_audit": pipeline._empty_audit(), "errors": []}

    monkeypatch.setattr(RepositoryValidator, "detect_repository_compatibility", staticmethod(validation))
    monkeypatch.setattr(TestRunner, "collect_test_ids", collection)
    monkeypatch.setattr(pipeline.PipelineService, "_build_details", classmethod(details))
    result = await pipeline.PipelineService.run_pipeline(tmp_path)
    assert result["status"] == "success"
    assert len(observed) == 3
    assert all(thread != main_thread for thread in observed)


@pytest.mark.asyncio
async def test_pipeline_timeout_is_explicit(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    _mock_execution(monkeypatch, pipeline)

    async def never_finishes(self, **kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(TestExecutor, "execute_multiple_runs", never_finishes)
    monkeypatch.setattr(pipeline.PipelineService, "EXECUTION_TIMEOUT_SECONDS", 0.01)
    result = await pipeline.PipelineService.run_pipeline(tmp_path)
    assert result["status"] == "error"
    assert result["errors"][0]["code"] == "EXECUTION_TIMEOUT"
    assert result["detection"]["flaky_tests"] == []


@pytest.mark.asyncio
async def test_detection_classification_fix_paths_match_and_client_closes(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    source_file = tmp_path / "tests" / "test_unit.py"
    source_file.parent.mkdir()
    source_file.write_text("def test_unit():\n    assert True\n", encoding="utf-8")
    runs = [_run(i, TestStatus.PASSED if i % 2 == 0 else TestStatus.FAILED, str(source_file)) for i in range(6)]
    _mock_execution(monkeypatch, pipeline, runs)
    now = datetime.now(timezone.utc)
    detection = DetectionResult(
        detection_id="det", repository="synthetic", analysis_period_start=now, analysis_period_end=now,
        total_test_runs=6, total_unique_tests=1, detection_confidence=0.4,
        flaky_tests=[FlakyTest(test_name="tests/test_unit.py::test_unit", file_path="tests/test_unit.py",
                              first_seen=now, last_seen=now, total_runs=6, pass_count=3, fail_count=3, flake_rate=0.5)],
    )
    monkeypatch.setattr(pipeline.TestAnalyzer, "analyze_runs", Mock(return_value=detection))
    client = SimpleNamespace(close=Mock())

    class FakeBob:
        llm_client = client

        async def classify_batch(self, tests, sources):
            assert Path(tests[0].file_path) == source_file
            assert sources[tests[0].test_name] == source_file.read_text(encoding="utf-8")
            return [Classification(classification_id="c", test_name=tests[0].test_name, file_path=tests[0].file_path,
                                   root_cause=RootCauseType.TIMING, confidence=Confidence.HIGH,
                                   reasoning="observed failure", suggested_fix_area="test_unit")]

    class FakeGenerator:
        async def generate_fix(self, classification, source):
            assert Path(classification.file_path) == source_file
            return Fix(fix_id="f", classification_id="c", test_name=classification.test_name,
                       file_path=classification.file_path, primary_suggestion_id="s", status=FixStatus.PROPOSED,
                       suggestions=[FixSuggestion(suggestion_id="s", fix_type=FixType.CODE_CHANGE,
                            description="fix", rationale="observed failure", confidence=0.5, estimated_effort="low",
                            diff=CodeDiff(file_path=classification.file_path, new_content=source,
                                unified_diff=f"--- a/{classification.file_path}\n+++ b/{classification.file_path}\n"))])

    monkeypatch.setattr(pipeline, "BobAgent", FakeBob)
    monkeypatch.setattr(pipeline, "FixGenerator", FakeGenerator)
    result = await pipeline.PipelineService.run_pipeline(tmp_path, num_runs=6)
    assert result["status"] == "success"
    records = [result["detection"]["flaky_tests"][0], result["classifications"][0], result["fixes"][0]]
    assert {record["file_path"] for record in records} == {"tests/test_unit.py"}
    assert {record["test_name"] for record in records} == {"tests/test_unit.py::test_unit"}
    assert result["fixes"][0]["suggestions"][0]["diff"]["file_path"] == "tests/test_unit.py"
    assert str(tmp_path) not in result["fixes"][0]["suggestions"][0]["diff"]["unified_diff"]
    client.close.assert_called_once()


@pytest.mark.asyncio
async def test_audit_reads_own_repo_even_without_flaky_tests(modules, tmp_path, monkeypatch):
    pipeline, _ = modules
    _mock_execution(monkeypatch, pipeline)
    (tmp_path / "QUARANTINE.md").write_text("- test_existing\n", encoding="utf-8")
    result = await pipeline.PipelineService.run_pipeline(tmp_path)
    assert result["status"] == "success"
    assert result["quarantine_audit"]["total_quarantined"] == 1
    assert result["quarantine_audit"]["tests"][0]["test_name"] == "test_existing"
    assert result["quarantine_audit"]["tests"][0]["source"] == "QUARANTINE.md"


@pytest.mark.asyncio
async def test_clone_offloads_work_and_retains_bounded_history(modules, tmp_path, monkeypatch):
    pipeline, routes = modules
    main_thread = threading.get_ident()
    observed = []

    def clone(**kwargs):
        observed.append(threading.get_ident())
        return dict(workspace_path=str(tmp_path), repo_url="https://github.com/example/repo", branch="main",
                    commit_sha="abc", owner="example", repo="repo", clone_id="test", test_files_count=0, test_files=[])

    async def analyze(**kwargs):
        return {"pipeline_id": "test", "status": "unsupported"}

    monkeypatch.setattr(routes.GitService, "clone_repository", clone)
    monkeypatch.setattr(pipeline.PipelineService, "run_pipeline", analyze)
    await routes.clone_and_analyze(routes.CloneRequest(repo_url="https://github.com/example/repo"))
    assert observed and observed[0] != main_thread
    for index in range(30):
        routes._remember_analysis({"pipeline_id": str(index)})
    assert len(routes._analysis_history) == routes._MAX_ANALYSIS_HISTORY
    assert routes._latest_analysis["pipeline_id"] == "29"


@pytest.mark.asyncio
async def test_upload_offloads_extraction_and_closes_file(modules, tmp_path, monkeypatch):
    pipeline, routes = modules
    main_thread = threading.get_ident()
    observed = []

    def extract(**kwargs):
        observed.append(threading.get_ident())
        return dict(workspace_path=str(tmp_path), upload_id="test", test_files_count=0, test_files=[])

    async def analyze(**kwargs):
        return {"pipeline_id": "test", "status": "unsupported"}

    monkeypatch.setattr(routes.GitService, "handle_archive_upload", extract)
    monkeypatch.setattr(pipeline.PipelineService, "run_pipeline", analyze)
    file = UploadFile(file=io.BytesIO(b"def test_x(): pass"), filename="test_x.py")
    await routes.upload_and_analyze(file=file, num_runs=5, test_pattern=None)
    assert observed and observed[0] != main_thread
    assert file.file.closed


@pytest.mark.asyncio
async def test_oversized_upload_rejected_before_extraction(modules, monkeypatch):
    _, routes = modules
    monkeypatch.setattr(routes, "_MAX_UPLOAD_BYTES", 4)
    extract = Mock(side_effect=AssertionError("must reject before extraction"))
    monkeypatch.setattr(routes.GitService, "handle_archive_upload", extract)
    file = UploadFile(file=io.BytesIO(b"12345"), filename="test_x.py")
    with pytest.raises(HTTPException) as exc:
        await routes.upload_and_analyze(file=file, num_runs=5, test_pattern=None)
    assert exc.value.status_code == 413
    assert file.file.closed
    extract.assert_not_called()


def _verified_runner(tmp_path):
    runner = TestRunner(tmp_path, collection_timeout=2, run_timeout=3)
    runner._pytest_plugins_verified = True
    runner._json_report_available = True
    runner._collected_test_ids = ["tests/test_unit.py::test_unit"]
    return runner


def test_runner_empty_filter_never_invokes_pytest(tmp_path, monkeypatch):
    runner = _verified_runner(tmp_path)
    launch = Mock(side_effect=AssertionError("empty filter must not run all tests"))
    monkeypatch.setattr(subprocess, "run", launch)
    result = runner.run_tests(test_pattern="missing")
    assert result.returncode == 5
    assert result.executions == []
    launch.assert_not_called()


@pytest.mark.parametrize("failure", ["timeout", "invalid_json", "success"])
def test_runner_owns_only_temporary_state_and_cleans_report(tmp_path, monkeypatch, failure):
    repo = tmp_path / "repo"
    repo.mkdir()
    state_parent = tmp_path / "caller_state"
    state_parent.mkdir()
    state_marker = state_parent / "keep.txt"
    state_marker.write_text("preserve", encoding="utf-8")
    cache = repo / ".venv" / "lib" / "__pycache__"
    cache.mkdir(parents=True)
    cache_marker = cache / "keep.pyc"
    cache_marker.write_bytes(b"preserve")
    monkeypatch.setenv("FLAKEGUARD_STATE_DIR", str(state_parent))
    runner = _verified_runner(repo)
    report_paths = []
    states = []

    def execute(cmd, **kwargs):
        assert kwargs["timeout"] > 0
        reports = [arg for arg in cmd if str(arg).startswith("--json-report-file=")]
        if not reports:
            return SimpleNamespace(returncode=0, stdout="test", stderr="")
        assert kwargs["timeout"] == 3
        assert "addopts=" in cmd
        path = Path(reports[0].split("=", 1)[1])
        report_paths.append(path)
        states.append(Path(kwargs["env"]["FLAKEGUARD_STATE_DIR"]))
        assert states[-1].is_dir()
        assert states[-1] != state_parent
        if failure == "timeout":
            path.write_text("partial", encoding="utf-8")
            raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
        if failure == "invalid_json":
            path.write_text("partial", encoding="utf-8")
        else:
            path.write_text(json.dumps({"tests": [{"nodeid": "tests/test_unit.py::test_unit", "outcome": "passed"}]}), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", execute)
    if failure == "timeout":
        with pytest.raises(TimeoutError):
            runner.run_tests()
    elif failure == "invalid_json":
        with pytest.raises(RuntimeError, match="parse JSON"):
            runner.run_tests()
    else:
        assert runner.run_tests().total_tests == 1
    assert report_paths and all(not path.exists() for path in report_paths)
    assert states and all(not path.exists() for path in states)
    assert state_marker.read_text(encoding="utf-8") == "preserve"
    assert cache_marker.read_bytes() == b"preserve"


def test_runner_does_not_inherit_retry_options(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--reruns 100 --reruns-delay 10")
    runner = _verified_runner(tmp_path)
    assert "PYTEST_ADDOPTS" not in runner._build_collection_env()
    assert "PYTEST_ADDOPTS" not in runner._build_execution_env(0, None, 0, tmp_path, None)


def test_collection_has_timeout_and_preserves_parameter_spaces(tmp_path, monkeypatch):
    runner = _verified_runner(tmp_path)
    runner._collected_test_ids = None

    def collect(cmd, **kwargs):
        assert kwargs["timeout"] == 2
        assert "no:cacheprovider" in cmd
        return SimpleNamespace(returncode=0, stdout="tests/test_unit.py::test_unit[a b]\n", stderr="")

    monkeypatch.setattr(subprocess, "run", collect)
    assert runner.collect_test_ids() == ["tests/test_unit.py::test_unit[a b]"]


@pytest.mark.parametrize("code", [2, 3, 4])
def test_partial_collection_failure_is_not_accepted(tmp_path, monkeypatch, code):
    runner = _verified_runner(tmp_path)
    runner._collected_test_ids = None
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        returncode=code, stdout="tests/test_unit.py::test_unit\n", stderr="failed"))
    with pytest.raises(RuntimeError, match="collection failed"):
        runner.collect_test_ids()


def test_collection_timeout_is_explicit(tmp_path, monkeypatch):
    runner = _verified_runner(tmp_path)
    runner._collected_test_ids = None

    def collect(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", collect)
    with pytest.raises(TimeoutError, match="collection exceeded"):
        runner.collect_test_ids()


def test_generic_validation_prunes_dependency_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(RepositoryValidator, "detect_pytest_compatibility", lambda path: {"compatible": False})
    (tmp_path / "node_modules" / "dependency").mkdir(parents=True)
    (tmp_path / "node_modules" / "dependency" / "test_fake.c").write_text("int main() {}", encoding="utf-8")
    result = RepositoryValidator.detect_repository_compatibility(tmp_path)
    assert result["compatible"] is False


def test_exact_source_lookup_does_not_fall_back_to_wrong_file(modules, tmp_path):
    pipeline, _ = modules
    (tmp_path / "unrelated").mkdir()
    (tmp_path / "unrelated" / "test_unit.py").write_text("wrong source", encoding="utf-8")
    assert pipeline.find_test_file(tmp_path, "missing/test_unit.py") is None
    with pytest.raises(ValueError, match="outside"):
        pipeline.find_test_file(tmp_path, "../test_unit.py")
