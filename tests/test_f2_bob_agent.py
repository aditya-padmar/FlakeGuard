"""
Tests for Feature F2: IBM Bob 2.0 AI Agent & Parallel Subagents.

Tests:
1. Agent status & configuration
2. Auto source extraction from repository
3. Timing / Race condition classification
4. Order dependency classification
5. State leakage classification
6. Environment / Network flakiness classification
7. Parallel batch classification (asyncio.gather)
8. Session evidence logging (PRD FR10)
"""
import pytest
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from backend.bob.agent import BobAgent
from backend.models.detection import FlakyTest, TestStatus
from backend.models.classification import RootCauseType, Confidence


@pytest.fixture
def agent(tmp_path):
    """Create BobAgent using a temp session directory."""
    session_dir = tmp_path / "sessions"
    return BobAgent(sessions_dir=str(session_dir))


def _make_flaky_test(name: str, path: str, failures=None) -> FlakyTest:
    return FlakyTest(
        test_name=name,
        file_path=path,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        total_runs=4,
        pass_count=2,
        fail_count=2,
        flake_rate=0.5,
        recent_failures=failures or ["AssertionError: test failed intermittently"],
        status_history=[TestStatus.PASSED, TestStatus.FAILED, TestStatus.PASSED, TestStatus.FAILED]
    )


class TestBobAgent:
    """Test suite for F2 Bob AI Agent."""

    def test_agent_status(self, agent):
        status = agent.get_status()
        assert status["name"] == "Bob"
        assert status["architecture"] == "parallel_subagents"
        assert len(status["subagents"]) == 4
        assert RootCauseType.TIMING in status["subagents"]
        assert RootCauseType.ORDERING in status["subagents"]
        assert RootCauseType.STATE_LEAKAGE in status["subagents"]
        assert RootCauseType.ENVIRONMENT in status["subagents"]

    def test_extract_test_source(self, agent):
        source = agent.extract_test_source(
            file_path="sample-repo/tests/test_timing.py",
            test_name="TestTimingIssues::test_sleep_based"
        )
        assert "def test_sleep_based" in source
        assert "time.sleep" in source

    @pytest.mark.asyncio
    async def test_timing_classification(self, agent):
        test = _make_flaky_test(
            "TestTimingIssues::test_sleep_based",
            "sample-repo/tests/test_timing.py"
        )
        result = await agent.classify_test(test)
        assert result.root_cause == RootCauseType.TIMING
        assert result.confidence in (Confidence.HIGH, Confidence.MEDIUM)
        assert len(result.evidence) > 0
        assert any(e.line_number is not None for e in result.evidence)

    @pytest.mark.asyncio
    async def test_ordering_classification(self, agent):
        test = _make_flaky_test(
            "TestOrderingIssues::test_second",
            "sample-repo/tests/test_order.py"
        )
        result = await agent.classify_test(test)
        assert result.root_cause == RootCauseType.ORDERING
        assert result.confidence in (Confidence.HIGH, Confidence.MEDIUM)

    @pytest.mark.asyncio
    async def test_leakage_classification(self, agent):
        test = _make_flaky_test(
            "TestStateLeakage::test_global_mutation",
            "sample-repo/tests/test_leakage.py"
        )
        result = await agent.classify_test(test)
        assert result.root_cause == RootCauseType.STATE_LEAKAGE
        assert result.confidence in (Confidence.HIGH, Confidence.MEDIUM)

    @pytest.mark.asyncio
    async def test_environment_classification(self, agent):
        test = _make_flaky_test(
            "TestEnvironmentIssues::test_random_failure",
            "sample-repo/tests/test_network.py",
            failures=["Failed: Random failure for flaky test demonstration"]
        )
        result = await agent.classify_test(test)
        assert result.root_cause == RootCauseType.ENVIRONMENT
        assert result.confidence in (Confidence.HIGH, Confidence.MEDIUM)

    @pytest.mark.asyncio
    async def test_classify_batch_parallel(self, agent):
        tests = [
            _make_flaky_test("TestTimingIssues::test_sleep_based", "sample-repo/tests/test_timing.py"),
            _make_flaky_test("TestEnvironmentIssues::test_random_failure", "sample-repo/tests/test_network.py")
        ]
        results = await agent.classify_batch(tests)
        assert len(results) == 2
        assert results[0].root_cause == RootCauseType.TIMING
        assert results[1].root_cause == RootCauseType.ENVIRONMENT

    @pytest.mark.asyncio
    async def test_session_evidence_logged(self, agent):
        test = _make_flaky_test(
            "TestTimingIssues::test_sleep_based",
            "sample-repo/tests/test_timing.py"
        )
        await agent.classify_test(test)

        session_files = list(Path(agent.sessions_dir).glob("session_*.json"))
        assert len(session_files) >= 1
        log_file = Path(agent.sessions_dir) / "SESSION_LOG.md"
        assert log_file.exists()
