"""Offline regressions for full-source proposals and non-destructive validation."""
import asyncio
import importlib.util
import re
import subprocess
import sys
import threading
from functools import partial
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.models.classification import Classification, Confidence, RootCauseType
from backend.models.remediation import CodeDiff, Fix, FixStatus, FixSuggestion, FixType
from backend.remediation.diff_generator import DiffGenerator
from backend.remediation.generator import FixGenerator
from backend.remediation import validator as validator_module
from backend.remediation.validator import FixValidator, ValidationResult


OLD_SOURCE = "def test_example():\n    assert False\n"
NEW_SOURCE = "def test_example():\n    assert True\n"


def _apply_unified_diff(source, patch):
    """Small independent parser to verify hunk counts and exact source round trips."""
    if not patch:
        return source
    lines = patch.splitlines(keepends=True)
    assert lines[0].startswith("--- a/") and lines[0].endswith("\n")
    assert lines[1].startswith("+++ b/") and lines[1].endswith("\n")
    records = []
    for line in lines[2:]:
        if line == "\\ No newline at end of file\n":
            assert records and records[-1].endswith("\n")
            records[-1] = records[-1][:-1]
        else:
            records.append(line)
    original = source.splitlines(keepends=True)
    output = []
    cursor = 0
    index = 0
    while index < len(records):
        header = re.fullmatch(
            r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n", records[index]
        )
        assert header is not None, records[index]
        old_start, old_count, new_start, new_count = header.groups()
        old_count = int(old_count) if old_count is not None else 1
        new_count = int(new_count) if new_count is not None else 1
        start = int(old_start) - (old_count != 0)
        assert start >= cursor
        output.extend(original[cursor:start])
        assert len(output) == int(new_start) - (new_count != 0)
        cursor = start
        removed = added = 0
        index += 1
        while index < len(records) and not records[index].startswith("@@ "):
            record = records[index]
            assert record[0] in " +-", record
            if record[0] in " -":
                assert original[cursor] == record[1:]
                cursor += 1
                removed += 1
            if record[0] in " +":
                output.append(record[1:])
                added += 1
            index += 1
        assert (removed, added) == (old_count, new_count)
    output.extend(original[cursor:])
    return "".join(output)


@pytest.fixture(autouse=True)
def subprocess_mock(monkeypatch):
    runner = Mock(side_effect=AssertionError("Unexpected real subprocess invocation"))
    monkeypatch.setattr(validator_module.subprocess, "run", runner)
    return runner


@pytest.fixture
def sample_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repository"
    source_file = repo / "tests" / "test_example.py"
    source_file.parent.mkdir(parents=True)
    # Preserve exact bytes (including BOM and CRLF), not just normalized text.
    source_file.write_bytes(b"\xef\xbb\xbf# original\r\ndef test_example():\r\n    assert False\r\n")
    (repo / "helper.py").write_text("VALUE = 'original'\n", encoding="utf-8")
    for name in (".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"):
        directory = repo / name
        directory.mkdir()
        (directory / "ignored").write_text("do not copy", encoding="utf-8")
    temp_root = tmp_path / "workspaces"
    temp_root.mkdir()
    monkeypatch.setattr(
        validator_module.tempfile,
        "TemporaryDirectory",
        partial(validator_module.tempfile.TemporaryDirectory, dir=temp_root),
    )
    return repo, source_file


def _classification(source_file, root_cause, test_name="test_example"):
    return Classification(
        classification_id="classification",
        test_name=test_name,
        file_path=str(source_file),
        root_cause=root_cause,
        confidence=Confidence.HIGH,
        reasoning="Offline regression fixture",
        suggested_fix_area=str(source_file),
    )


def _fix(source_file, new_content=NEW_SOURCE):
    suggestion = FixSuggestion(
        suggestion_id="suggestion",
        fix_type=FixType.CODE_CHANGE,
        description="A proposed change",
        rationale="Regression fixture",
        confidence=0.9,
        estimated_effort="low",
        diff=CodeDiff(
            file_path=str(source_file),
            old_content=OLD_SOURCE,
            new_content=new_content,
            unified_diff=DiffGenerator().generate_diff(OLD_SOURCE, NEW_SOURCE, str(source_file)),
        ),
    )
    return Fix(
        fix_id="fix",
        classification_id="classification",
        test_name="test_example",
        file_path=str(source_file),
        suggestions=[suggestion],
        primary_suggestion_id=suggestion.suggestion_id,
    )


@pytest.fixture
def routes(monkeypatch):
    # Load a private route module with a mocked Bob constructor. No providers,
    # session logs, or application-wide singleton state are initialized here.
    import backend.bob.agent as bob_module

    monkeypatch.setattr(bob_module, "BobAgent", Mock())
    path = Path(__file__).resolve().parents[1] / "backend" / "api" / "routes" / "remediation.py"
    spec = importlib.util.spec_from_file_location("_patch_regression_routes", path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "old,new",
    [
        (OLD_SOURCE, NEW_SOURCE),
        (OLD_SOURCE.rstrip("\n"), NEW_SOURCE.rstrip("\n")),
        (OLD_SOURCE.rstrip("\n"), NEW_SOURCE),
        (OLD_SOURCE, NEW_SOURCE.rstrip("\n")),
        ("", NEW_SOURCE),
        (OLD_SOURCE, ""),
        (OLD_SOURCE.replace("\n", "\r\n"), NEW_SOURCE.replace("\n", "\r\n")),
        ("first\n" + "same\n" * 12 + "last", "FIRST\n" + "same\n" * 12 + "LAST"),
        ("", ""),
        (OLD_SOURCE, OLD_SOURCE),
    ],
)
def test_unified_diff_has_separate_parseable_headers_and_round_trips(old, new):
    patch = DiffGenerator().generate_diff(old, new, "tests/test_example.py")
    if old != new:
        assert patch.splitlines()[0] == "--- a/tests/test_example.py"
        assert patch.splitlines()[1] == "+++ b/tests/test_example.py"
        assert patch.splitlines()[2].startswith("@@ ")
    else:
        assert patch == ""
    assert _apply_unified_diff(old, patch) == new


@pytest.mark.parametrize(
    "root_cause,source,test_name",
    [
        (
            RootCauseType.TIMING,
            "import time\n\ndef test_example():\n    time.sleep(0.1)\n    elapsed = 0.01\n    assert elapsed < 0.05\n",
            "test_example",
        ),
        (
            RootCauseType.ORDERING,
            "import pytest\n\nclass TestExample:\n    def test_example(self):\n        assert True\n",
            "TestExample::test_example",
        ),
        (
            RootCauseType.STATE_LEAKAGE,
            "import pytest\nfrom src.calculator import Calculator, get_shared_calculator\n\ndef test_example():\n    calc = get_shared_calculator()\n    assert calc is not None\n",
            "test_example",
        ),
        (
            RootCauseType.ENVIRONMENT,
            "import random\n\ndef test_example():\n    assert random.random() < 1\n",
            "test_example",
        ),
        (RootCauseType.NETWORK, OLD_SOURCE, "test_example"),
        (RootCauseType.UNKNOWN, OLD_SOURCE, "test_example"),
    ],
)
def test_generated_diffs_keep_complete_original_and_modified_source(
    tmp_path, root_cause, source, test_name
):
    source_file = tmp_path / "test_example.py"
    source_file.write_text(source, encoding="utf-8")
    original_bytes = source_file.read_bytes()
    classification = _classification(source_file, root_cause, test_name)
    fix = asyncio.run(FixGenerator().generate_fix(classification, "# not the full file"))
    diffs = [suggestion.diff for suggestion in fix.suggestions if suggestion.diff is not None]
    assert diffs
    assert fix.status == FixStatus.PROPOSED
    assert all(suggestion.requires_review for suggestion in fix.suggestions)
    for diff in diffs:
        assert diff.old_content == source
        assert isinstance(diff.new_content, str)
        assert diff.new_content != diff.unified_diff
        assert _apply_unified_diff(source, diff.unified_diff) == diff.new_content
        compile(diff.new_content, str(source_file), "exec")
    assert source_file.read_bytes() == original_bytes


def test_remote_full_source_is_kept_without_writing_file(tmp_path):
    source_file = tmp_path / "missing.py"
    classification = _classification(source_file, RootCauseType.UNKNOWN)
    fix = asyncio.run(FixGenerator().generate_fix(classification, OLD_SOURCE))
    diff = fix.suggestions[0].diff
    assert diff.old_content == OLD_SOURCE
    assert _apply_unified_diff(OLD_SOURCE, diff.unified_diff) == diff.new_content
    assert not source_file.exists()


@pytest.mark.parametrize(
    "proposal",
    [
        None,
        b"def test_example(): pass",
        "",
        " \n\t",
        "--- a/test_example.py\n+++ b/test_example.py\n@@ -1 +1 @@\n-old\n+new\n",
        "--- a/test_example.py+++ b/test_example.py@@ -1 +1 @@-old+new",
        "def test_example(:\n    assert True\n",
        "return True\n",
        "def test_example():\n    pass\x00\n",
    ],
)
def test_invalid_or_missing_source_never_writes_or_runs(
    sample_repo, monkeypatch, subprocess_mock, proposal
):
    repo, source_file = sample_repo
    original = source_file.read_bytes()
    mtime = source_file.stat().st_mtime_ns
    no_copy = Mock(side_effect=AssertionError("Invalid source reached repository copying"))
    monkeypatch.setattr(validator_module.shutil, "copytree", no_copy)
    no_temp = Mock(side_effect=AssertionError("Invalid source created a workspace"))
    monkeypatch.setattr(validator_module.tempfile, "TemporaryDirectory", no_temp)
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", str(source_file), proposal, "test_example", runs=5)
    )
    assert not result.fix_valid
    assert result.runs == result.passes == 0
    assert result.error
    assert source_file.read_bytes() == original
    assert source_file.stat().st_mtime_ns == mtime
    subprocess_mock.assert_not_called()
    no_copy.assert_not_called()
    no_temp.assert_not_called()


@pytest.mark.parametrize("runs", [0, -1, True, 1.5])
def test_invalid_run_counts_skip_without_processes(sample_repo, subprocess_mock, runs):
    repo, source_file = sample_repo
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", str(source_file), NEW_SOURCE, "test_example", runs)
    )
    assert result.runs == 0
    assert not result.fix_valid
    assert "positive integer" in result.error
    subprocess_mock.assert_not_called()


@pytest.mark.parametrize(
    "file_kind,test_name",
    [
        ("missing", "test_example"),
        ("outside", "test_example"),
        ("other_language", "test_example"),
        ("valid", ""),
        ("valid", "tests/test_example.py"),
        ("valid", "tests/test_example.py::"),
        ("valid", "tests/test_other.py::test_other"),
    ],
)
def test_invalid_targets_are_refused_before_copying(
    sample_repo, tmp_path, monkeypatch, subprocess_mock, file_kind, test_name
):
    repo, source_file = sample_repo
    (repo / "tests" / "test_other.py").write_text(NEW_SOURCE, encoding="utf-8")
    if file_kind == "missing":
        source_file = repo / "missing.py"
    elif file_kind == "outside":
        source_file = tmp_path / "outside.py"
        source_file.write_text(OLD_SOURCE, encoding="utf-8")
    elif file_kind == "other_language":
        source_file = repo / "tests" / "test_example.js"
        source_file.write_text("// not Python", encoding="utf-8")
    copy = Mock(side_effect=AssertionError("Invalid target reached copying"))
    monkeypatch.setattr(validator_module.shutil, "copytree", copy)
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", str(source_file), NEW_SOURCE, test_name)
    )
    assert not result.fix_valid
    assert result.runs == 0
    assert result.error
    copy.assert_not_called()
    subprocess_mock.assert_not_called()


@pytest.mark.parametrize(
    "test_name,selector",
    [
        ("test_example", "test_example"),
        ("TestExample::test_example", "TestExample::test_example"),
        ("tests/test_example.py::TestExample::test_example", "TestExample::test_example"),
        ("absolute", "test_example"),
        ("test_example[path/to/value::case]", "test_example[path/to/value::case]"),
    ],
)
def test_validation_runs_only_patched_copy_and_keeps_original_bytes(
    sample_repo, monkeypatch, subprocess_mock, test_name, selector
):
    repo, source_file = sample_repo
    original = source_file.read_bytes()
    mtime = source_file.stat().st_mtime_ns
    if test_name == "absolute":
        test_name = f"{source_file}::test_example"
    monkeypatch.setenv("PYTHONPATH", validator_module.os.pathsep.join([str(repo / "tests"), "src"]))
    monkeypatch.setenv("PYTEST_ADDOPTS", "tests/test_unrelated.py")
    workspaces = []
    calling_thread = threading.get_ident()

    def run(cmd, *, cwd, env, **kwargs):
        cwd = Path(cwd)
        workspaces.append(cwd)
        assert cwd != repo and not cwd.is_relative_to(repo)
        assert threading.get_ident() != calling_thread
        assert cmd[:3] == [sys.executable, "-m", "pytest"]
        assert cmd[-2:] == ["--", f"tests/test_example.py::{selector}"]
        assert "addopts=" in cmd
        assert "PYTEST_ADDOPTS" not in env
        assert env["PYTHONPATH"].split(validator_module.os.pathsep) == [
            str(cwd), str(cwd / "tests"), str(cwd / "src")
        ]
        assert kwargs["timeout"] == 60
        assert (cwd / "tests" / "test_example.py").read_bytes() == NEW_SOURCE.encode("utf-8")
        assert not any((cwd / name).exists() for name in FixValidator._COPY_EXCLUDES)
        assert source_file.read_bytes() == original
        assert source_file.stat().st_mtime_ns == mtime
        (cwd / "helper.py").write_text("VALUE = 'sandbox-only'\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "1 passed\n", "")

    subprocess_mock.side_effect = run
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", "tests/test_example.py", NEW_SOURCE, test_name, runs=3)
    )
    assert result.fix_valid
    assert result.runs == result.passes == 3
    assert result.test_name == test_name
    assert result.flakiness_rate == 0.0
    assert len(set(workspaces)) == 1
    assert all(not workspace.exists() for workspace in workspaces)
    assert source_file.read_bytes() == original
    assert source_file.stat().st_mtime_ns == mtime
    assert (repo / "helper.py").read_text(encoding="utf-8") == "VALUE = 'original'\n"


@pytest.mark.parametrize("returncode", [2, 3, 4, 5])
def test_collection_and_runner_errors_stop_after_one_attempt(
    sample_repo, subprocess_mock, returncode
):
    repo, source_file = sample_repo
    original = source_file.read_bytes()
    subprocess_mock.side_effect = None
    subprocess_mock.return_value = subprocess.CompletedProcess([], returncode, "collection failed\n", "detail")
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", str(source_file), NEW_SOURCE, "test_example", runs=5)
    )
    assert not result.fix_valid
    assert result.runs == 1 and result.passes == 0
    assert result.error
    assert result.last_output == "collection failed\ndetail"
    subprocess_mock.assert_called_once()
    assert not Path(subprocess_mock.call_args.kwargs["cwd"]).exists()
    assert source_file.read_bytes() == original


@pytest.mark.parametrize(
    "error",
    [RuntimeError("runner unavailable"), subprocess.TimeoutExpired("pytest", 60, output=b"partial output")],
)
def test_subprocess_exception_leaves_original_untouched_and_cleans_copy(
    sample_repo, subprocess_mock, error
):
    repo, source_file = sample_repo
    original = source_file.read_bytes()
    mtime = source_file.stat().st_mtime_ns
    subprocess_mock.side_effect = error
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", str(source_file), NEW_SOURCE, "test_example", runs=5)
    )
    assert not result.fix_valid
    assert result.runs == 1
    assert result.error
    if isinstance(error, subprocess.TimeoutExpired):
        assert result.last_output == "partial output"
    assert source_file.read_bytes() == original
    assert source_file.stat().st_mtime_ns == mtime
    assert not Path(subprocess_mock.call_args.kwargs["cwd"]).exists()


def test_workspace_copy_failure_never_touches_original(sample_repo, monkeypatch, subprocess_mock):
    repo, source_file = sample_repo
    original = source_file.read_bytes()
    mtime = source_file.stat().st_mtime_ns
    copy = Mock(side_effect=OSError("copy failed"))
    monkeypatch.setattr(validator_module.shutil, "copytree", copy)
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", str(source_file), NEW_SOURCE, "test_example")
    )
    assert not result.fix_valid and result.runs == 0
    assert result.error == "copy failed"
    assert source_file.read_bytes() == original
    assert source_file.stat().st_mtime_ns == mtime
    assert not Path(copy.call_args.args[1]).parent.exists()
    subprocess_mock.assert_not_called()


def test_cwd_relative_source_paths_are_mapped_to_repository(sample_repo, monkeypatch, subprocess_mock):
    repo, source_file = sample_repo
    monkeypatch.chdir(repo.parent)
    subprocess_mock.side_effect = None
    subprocess_mock.return_value = subprocess.CompletedProcess([], 0, "1 passed", "")
    result = asyncio.run(
        FixValidator(repo.name).validate(
            "fix", "repository/tests/test_example.py", NEW_SOURCE,
            "repository/tests/test_example.py::test_example", runs=1,
        )
    )
    assert result.fix_valid
    assert subprocess_mock.call_args.args[0][-1] == "tests/test_example.py::test_example"


def test_repository_links_are_not_followed_during_copy(sample_repo, monkeypatch):
    repo, source_file = sample_repo
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path, "is_symlink", lambda path: path.name == "linked.py" or original_is_symlink(path)
    )
    monkeypatch.setattr(Path, "is_junction", lambda path: path.name == "junction", raising=False)
    assert FixValidator._ignore_copy_paths(str(repo), ["linked.py", "junction", "helper.py", ".git"]) == {
        "linked.py", "junction", ".git"
    }


def test_normal_failures_still_get_repeated_stability_checks(sample_repo, subprocess_mock):
    repo, source_file = sample_repo
    subprocess_mock.side_effect = [
        subprocess.CompletedProcess([], code, "1 passed" if code == 0 else "1 failed", "")
        for code in (1, 0, 0, 0, 0)
    ]
    result = asyncio.run(
        FixValidator(str(repo)).validate("fix", str(source_file), NEW_SOURCE, "test_example", runs=5)
    )
    assert result.fix_valid
    assert result.runs == 5 and result.passes == 4
    assert result.flakiness_rate == pytest.approx(0.2)
    assert subprocess_mock.call_count == 5


def test_parallel_validation_uses_independent_workspaces(sample_repo, subprocess_mock):
    repo, source_file = sample_repo
    original = source_file.read_bytes()
    validator = FixValidator(str(repo))
    proposals = (NEW_SOURCE, NEW_SOURCE + "# another proposal\n")
    observed = []

    def run(cmd, *, cwd, **kwargs):
        observed.append((Path(cwd), (Path(cwd) / "tests" / "test_example.py").read_text(encoding="utf-8")))
        return subprocess.CompletedProcess(cmd, 0, "1 passed", "")

    subprocess_mock.side_effect = run

    async def validate_both():
        return await asyncio.gather(*(
            validator.validate(str(index), str(source_file), source, "test_example", runs=1)
            for index, source in enumerate(proposals)
        ))

    results = asyncio.run(validate_both())
    assert all(result.fix_valid for result in results)
    assert len({path for path, _ in observed}) == 2
    assert {source for _, source in observed} == set(proposals)
    assert all(not path.exists() for path, _ in observed)
    assert validator.repo_path == repo
    assert source_file.read_bytes() == original


@pytest.mark.parametrize("source", [None, "", NEW_SOURCE])
def test_source_cache_never_falls_back_to_unified_diff(routes, sample_repo, source):
    _, source_file = sample_repo
    fix = _fix(source_file, source)
    key = "fix:suggestion"
    routes._patched_sources[key] = "stale patch text"
    routes._store_patched_sources(fix)
    if source is None:
        assert key not in routes._patched_sources
    else:
        assert routes._patched_sources[key] == source
    fix.suggestions[0].diff = None
    routes._store_patched_sources(fix)
    assert key not in routes._patched_sources


def test_route_rejects_missing_full_source_even_if_patch_is_cached(routes, sample_repo, monkeypatch):
    _, source_file = sample_repo
    fix = _fix(source_file, None)
    routes.fixes_db[fix.fix_id] = fix
    routes._patched_sources["fix:suggestion"] = fix.suggestions[0].diff.unified_diff
    validate = AsyncMock()
    monkeypatch.setattr(routes.FixValidator, "validate", validate)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(routes.validate_fix("fix", "suggestion"))
    assert exc_info.value.status_code == 422
    assert "Patched source not available" in exc_info.value.detail
    assert fix.status == FixStatus.PROPOSED
    validate.assert_not_awaited()


def test_route_uses_authoritative_source_not_stale_cached_patch(routes, sample_repo, monkeypatch):
    repo, source_file = sample_repo
    fix = _fix(source_file)
    routes.fixes_db[fix.fix_id] = fix
    routes._patched_sources["fix:suggestion"] = fix.suggestions[0].diff.unified_diff
    result = ValidationResult(
        fix_id="fix", test_name="test_example", runs=1, passes=1,
        fix_valid=True, flakiness_rate=0.0, verdict="Offline fixture",
    )
    validate = AsyncMock(return_value=result)
    monkeypatch.setattr(routes.FixValidator, "validate", validate)
    assert asyncio.run(routes.validate_fix("fix", "suggestion", runs=1, repo_path=str(repo))) == result
    assert validate.await_args.kwargs["patched_source"] == NEW_SOURCE
    assert fix.status == FixStatus.VERIFIED
    assert fix.verified_runs == 1


@pytest.mark.parametrize("proposal", ["", "def test_example(:\n", "--- a/file\n+++ b/file\n@@ -1 +1 @@\n-x\n+y\n"])
def test_route_invalid_proposals_never_write_original_or_run_pytest(
    routes, sample_repo, subprocess_mock, proposal
):
    repo, source_file = sample_repo
    original = source_file.read_bytes()
    mtime = source_file.stat().st_mtime_ns
    fix = _fix(source_file, proposal)
    routes.fixes_db[fix.fix_id] = fix
    routes._store_patched_sources(fix)
    result = asyncio.run(routes.validate_fix("fix", "suggestion", repo_path=str(repo)))
    assert result.runs == 0
    assert not result.fix_valid
    assert fix.status == FixStatus.FAILED
    assert source_file.read_bytes() == original
    assert source_file.stat().st_mtime_ns == mtime
    subprocess_mock.assert_not_called()


def test_generate_to_route_validation_uses_full_file_without_applying(
    routes, sample_repo, subprocess_mock
):
    repo, source_file = sample_repo
    source = "import time\n\ndef test_example():\n    time.sleep(0.01)\n    assert True\n"
    source_file.write_text(source, encoding="utf-8")
    original = source_file.read_bytes()
    routes._bob_agent.extract_test_source.return_value = "    time.sleep(0.01)"
    fix = asyncio.run(routes.generate_fix(_classification(source_file, RootCauseType.TIMING)))
    suggestion = next(s for s in fix.suggestions if s.suggestion_id == fix.primary_suggestion_id)
    assert suggestion.diff.old_content == source
    assert routes._patched_sources[f"{fix.fix_id}:{suggestion.suggestion_id}"] == suggestion.diff.new_content

    def run(cmd, *, cwd, **kwargs):
        patched = (Path(cwd) / "tests" / "test_example.py").read_text(encoding="utf-8")
        assert patched == suggestion.diff.new_content
        compile(patched, str(source_file), "exec")
        assert source_file.read_bytes() == original
        return subprocess.CompletedProcess(cmd, 0, "1 passed", "")

    subprocess_mock.side_effect = run
    result = asyncio.run(routes.validate_fix(fix.fix_id, suggestion.suggestion_id, runs=2, repo_path=str(repo)))
    assert result.fix_valid and result.runs == result.passes == 2
    assert source_file.read_bytes() == original
