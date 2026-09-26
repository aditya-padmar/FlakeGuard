"""
F2 Unit Tests — IBM Bob 2.0 AI Agent & Parallel Subagents.

Covers:
  1. Subagent initialisation (all 4 load their prompt templates)
  2. AST source extractor (resolves function body from disk)
  3. Confidence scoring (pattern hits raise score correctly)
  4. Root-cause selection (highest score wins)
  5. Parallel batch execution (asyncio.gather path)
  6. Session evidence logging (JSON artefact written to disk)
  7. Agent status endpoint shape
  8. Edge-cases: empty source, unknown root cause

Run:
    pytest tests/test_f2_bob_agent.py -v
"""
import asyncio
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Make sure project root is importable when running pytest from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.bob.agent import BobAgent
from backend.bob.classifier import TestClassifier
from backend.bob.subagents.environment import EnvironmentSubagent
from backend.bob.subagents.leakage import LeakageSubagent
from backend.bob.subagents.ordering import OrderingSubagent
from backend.bob.subagents.timing import TimingSubagent
from backend.models.classification import Confidence, RootCauseType
from backend.models.detection import FlakyTest, TestStatus


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_flaky_test(
    test_name: str = "TestSample::test_example",
    file_path: str = "sample-repo/tests/test_timing.py",
    recent_failures: list | None = None,
    status_history: list | None = None,
) -> FlakyTest:
    now = datetime.now(timezone.utc)
    return FlakyTest(
        test_name=test_name,
        file_path=file_path,
        first_seen=now,
        last_seen=now,
        total_runs=4,
        pass_count=2,
        fail_count=2,
        flake_rate=0.5,
        recent_failures=recent_failures or ["AssertionError: flaky"],
        status_history=status_history or [TestStatus.PASSED, TestStatus.FAILED,
                                          TestStatus.PASSED, TestStatus.FAILED],
    )


# ── Test 1: All 4 subagents initialise and load prompts ──────────────────────

class TestSubagentInitialisation:
    def test_timing_subagent_loads(self):
        agent = TimingSubagent()
        assert agent is not None
        assert isinstance(agent.prompt_template, str)
        assert len(agent.prompt_template) > 0

    def test_ordering_subagent_loads(self):
        agent = OrderingSubagent()
        assert agent is not None
        assert isinstance(agent.prompt_template, str)

    def test_leakage_subagent_loads(self):
        agent = LeakageSubagent()
        assert agent is not None
        assert isinstance(agent.prompt_template, str)

    def test_environment_subagent_loads(self):
        agent = EnvironmentSubagent()
        assert agent is not None
        assert isinstance(agent.prompt_template, str)


# ── Test 2: AST source extractor ─────────────────────────────────────────────

class TestASTSourceExtractor:
    def test_extracts_function_from_real_file(self):
        agent = BobAgent()
        source = agent.extract_test_source(
            "sample-repo/tests/test_timing.py",
            "TestTimingIssues::test_worker_thread_race",
        )
        # Should return non-empty code containing the function
        assert source != ""
        assert "def test_worker_thread_race" in source or "time.sleep" in source

    def test_returns_empty_for_nonexistent_file(self):
        agent = BobAgent()
        source = agent.extract_test_source(
            "nonexistent/path/test_fake.py",
            "test_fake_method",
        )
        assert source == ""

    def test_extracts_correct_function_not_whole_file(self):
        """Extracted source should be shorter than the full file."""
        agent = BobAgent()
        full_path = Path("sample-repo/tests/test_timing.py")
        if not full_path.exists():
            pytest.skip("sample-repo not present")
        full_source = full_path.read_text(encoding="utf-8")
        extracted = agent.extract_test_source(
            str(full_path), "TestTimingIssues::test_worker_thread_race"
        )
        assert len(extracted) < len(full_source)


# ── Test 3: Confidence scoring from patterns ─────────────────────────────────

class TestConfidenceScoring:
    @pytest.mark.asyncio
    async def test_timing_subagent_scores_sleep(self):
        agent = TimingSubagent()
        result = await agent.analyze(
            test_name="test_example",
            test_source="def test_example():\n    time.sleep(2)\n    assert True",
            error_messages=[],
            status_history=[],
        )
        assert result["score"] > 0.3, "sleep() should raise timing score above 0.3"
        assert result["root_cause"] == RootCauseType.TIMING

    @pytest.mark.asyncio
    async def test_environment_subagent_scores_random(self):
        agent = EnvironmentSubagent()
        result = await agent.analyze(
            test_name="test_random",
            test_source="def test_random():\n    val = random.random()\n    assert val > 0",
            error_messages=[],
            status_history=[],
        )
        assert result["score"] > 0.3
        assert result["root_cause"] == RootCauseType.ENVIRONMENT

    @pytest.mark.asyncio
    async def test_leakage_subagent_scores_shared_instance(self):
        agent = LeakageSubagent()
        result = await agent.analyze(
            test_name="test_mutation",
            test_source="def test_mutation():\n    calc = get_shared_calculator()\n    calc.add(1)",
            error_messages=[],
            status_history=[],
        )
        assert result["score"] > 0.2

    @pytest.mark.asyncio
    async def test_score_clamped_to_one(self):
        """Score must never exceed 1.0 regardless of pattern hits."""
        agent = TimingSubagent()
        # Maximally suspicious source
        noisy_source = "\n".join([
            "import time",
            "def test_noisy():",
            "    time.sleep(1)",
            "    time.sleep(2)",
            "    time.sleep(3)",
            "    assert elapsed < 0.001",
            "    assert duration < 0.001",
        ])
        result = await agent.analyze(
            test_name="test_timing_heavy",
            test_source=noisy_source,
            error_messages=["timeout", "timed out"],
            status_history=[],
        )
        assert result["score"] <= 1.0


# ── Test 4: Root-cause selection ─────────────────────────────────────────────

class TestRootCauseSelection:
    @pytest.mark.asyncio
    async def test_classify_timing_test(self):
        agent = BobAgent()
        flaky = _make_flaky_test(
            test_name="TestTimingIssues::test_worker_thread_race",
            file_path="sample-repo/tests/test_timing.py",
            recent_failures=["AssertionError: assert result == 4"],
        )
        classification = await agent.classify_test(flaky)
        assert classification.root_cause == RootCauseType.TIMING
        assert classification.confidence == Confidence.HIGH

    @pytest.mark.asyncio
    async def test_classify_environment_test(self):
        agent = BobAgent()
        flaky = _make_flaky_test(
            test_name="TestEnvironmentIssues::test_region_dependent_totals",
            file_path="sample-repo/tests/test_environment.py",
            recent_failures=["AssertionError: Suspected cause: environment dependency. Observed SALES_REGION='EU'"],
        )
        classification = await agent.classify_test(flaky)
        assert classification.root_cause == RootCauseType.ENVIRONMENT

    @pytest.mark.asyncio
    async def test_unknown_cause_for_empty_source(self):
        """With no source and no error signals, should return LOW confidence."""
        agent = BobAgent()
        flaky = _make_flaky_test(
            test_name="test_completely_opaque",
            file_path="does_not_exist.py",
            recent_failures=[],
            status_history=[TestStatus.PASSED, TestStatus.FAILED],
        )
        classification = await agent.classify_test(flaky, test_source="")
        # Score will be near 0 → LOW confidence
        assert classification.confidence == Confidence.LOW


# ── Test 5: Parallel batch execution ─────────────────────────────────────────

class TestParallelBatch:
    @pytest.mark.asyncio
    async def test_batch_returns_all_results(self):
        agent = BobAgent()
        tests = [
            _make_flaky_test("TestTimingIssues::test_worker_thread_race",
                             "sample-repo/tests/test_timing.py"),
            _make_flaky_test("TestEnvironmentIssues::test_region_dependent_totals",
                             "sample-repo/tests/test_environment.py"),
        ]
        results = await agent.classify_batch(tests)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_batch_classifications_are_correct_types(self):
        agent = BobAgent()
        tests = [_make_flaky_test()]
        results = await agent.classify_batch(tests)
        assert results[0].root_cause in list(RootCauseType)
        assert results[0].confidence in list(Confidence)


# ── Test 6: Session evidence logging ─────────────────────────────────────────

class TestSessionEvidenceLogging:
    @pytest.mark.asyncio
    async def test_session_json_written_to_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = BobAgent(sessions_dir=tmp)
            flaky = _make_flaky_test(
                test_name="TestTimingIssues::test_worker_thread_race",
                file_path="sample-repo/tests/test_timing.py",
            )
            await agent.classify_test(flaky)

            session_files = list(Path(tmp).glob("session_*.json"))
            assert len(session_files) == 1

            data = json.loads(session_files[0].read_text())
            assert data["test_name"] == "TestTimingIssues::test_worker_thread_race"
            assert "verdict" in data
            assert "subagent_scores" in data

    @pytest.mark.asyncio
    async def test_session_log_md_appended(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = BobAgent(sessions_dir=tmp)
            flaky = _make_flaky_test(
                test_name="TestTimingIssues::test_worker_thread_race",
                file_path="sample-repo/tests/test_timing.py",
            )
            await agent.classify_test(flaky)

            log_file = Path(tmp) / "SESSION_LOG.md"
            assert log_file.exists()
            content = log_file.read_text()
            assert "test_worker_thread_race" in content


# ── Test 7: Agent status shape ───────────────────────────────────────────────

class TestAgentStatus:
    def test_status_keys_present(self):
        agent = BobAgent()
        status = agent.get_status()
        assert status["name"] == "Bob"
        assert status["version"] == "2.0.0"
        assert status["architecture"] == "parallel_subagents"
        assert isinstance(status["subagents"], list)
        assert len(status["subagents"]) == 4

    def test_all_four_subagents_listed(self):
        agent = BobAgent()
        subagents = [s.value for s in agent.get_status()["subagents"]]
        assert "timing" in subagents
        assert "ordering" in subagents
        assert "state_leakage" in subagents
        assert "environment" in subagents
