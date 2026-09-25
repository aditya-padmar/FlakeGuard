"""Test classifier using specialized parallel subagents."""
import asyncio
import time
from typing import Dict, List, Any, Optional

from backend.models.classification import RootCauseType, Confidence, Evidence
from backend.models.detection import FlakyTest
from backend.bob.subagents.timing import TimingSubagent
from backend.bob.subagents.ordering import OrderingSubagent
from backend.bob.subagents.leakage import LeakageSubagent
from backend.bob.subagents.environment import EnvironmentSubagent


class TestClassifier:
    """
    Classifier that coordinates parallel subagents for root cause analysis.
    Implements IBM Bob 2.0 parallel subagent architecture.
    """

    def __init__(self):
        self.subagents = {
            RootCauseType.TIMING: TimingSubagent(),
            RootCauseType.ORDERING: OrderingSubagent(),
            RootCauseType.STATE_LEAKAGE: LeakageSubagent(),
            RootCauseType.ENVIRONMENT: EnvironmentSubagent()
        }

    async def classify(
        self,
        flaky_test: FlakyTest,
        test_source: str,
        llm_client: Any = None,
        additional_context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Classify a flaky test by dispatching competing subagents in parallel.
        
        Each subagent investigates one mutually exclusive root-cause hypothesis.
        The classifier evaluates confidence scores and selects the winning verdict.
        """
        start_time = time.time()

        # Execute all subagents concurrently (IBM Bob 2.0 Parallel Subagents)
        subagent_keys = list(self.subagents.keys())
        tasks = [
            self.subagents[cause_type].analyze(
                test_name=flaky_test.test_name,
                test_source=test_source,
                error_messages=flaky_test.recent_failures,
                status_history=flaky_test.status_history,
                llm_client=llm_client,
                context=additional_context
            )
            for cause_type in subagent_keys
        ]

        results = await asyncio.gather(*tasks)
        subagent_results: Dict[RootCauseType, Dict[str, Any]] = dict(zip(subagent_keys, results))

        # Select highest-confidence root cause
        root_cause, confidence, evidence = self._select_root_cause(
            subagent_results,
            flaky_test
        )

        # Generate synthesized reasoning and fix area
        reasoning = self._generate_reasoning(subagent_results, root_cause)
        suggested_fix_area = self._determine_fix_area(root_cause, test_source)
        processing_time = round(time.time() - start_time, 3)

        # Subagent score distribution for dashboard and evidence reporting
        score_breakdown = {
            cause.value: round(res.get("score", 0.0), 3)
            for cause, res in subagent_results.items()
        }

        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": evidence,
            "reasoning": reasoning,
            "suggested_fix_area": suggested_fix_area,
            "related_tests": self._find_related_tests(root_cause, test_source),
            "subagent_scores": score_breakdown,
            "model": "bob-agent-llm" if llm_client else "bob-agent-parallel-rules",
            "processing_time": processing_time
        }

    def _select_root_cause(
        self,
        subagent_results: Dict[RootCauseType, Dict],
        flaky_test: FlakyTest
    ) -> tuple:
        """Select the most likely root cause from subagent results."""
        best_cause = RootCauseType.UNKNOWN
        best_score = 0.0
        best_evidence = []

        for cause_type, result in subagent_results.items():
            score = result.get("score", 0.0)
            if score > best_score:
                best_score = score
                best_cause = cause_type
                best_evidence = result.get("evidence", [])

        # Thresholds for confidence
        if best_score >= 0.65:
            confidence = Confidence.HIGH
        elif best_score >= 0.35:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW

        return best_cause, confidence, best_evidence

    def _generate_reasoning(
        self,
        subagent_results: Dict[RootCauseType, Dict],
        root_cause: RootCauseType
    ) -> str:
        """Generate human-readable reasoning based on the winning subagent."""
        result = subagent_results.get(root_cause, {})
        reasoning = result.get("reasoning", "")
        if reasoning:
            return reasoning
        return f"Classified as {root_cause.value} based on parallel subagent pattern analysis."

    def _determine_fix_area(self, root_cause: RootCauseType, test_source: str) -> str:
        """Determine the code area that needs to be fixed."""
        fix_areas = {
            RootCauseType.TIMING: "Test timing, sleeps, and timeout assertions",
            RootCauseType.ORDERING: "Test execution order, state isolation, and fixtures",
            RootCauseType.STATE_LEAKAGE: "Fixture teardown, shared singleton cleanup, and global state reset",
            RootCauseType.ENVIRONMENT: "Network mocking, deterministic RNG seeds, and environment variable defaults",
            RootCauseType.RACE_CONDITION: "Concurrency synchronization and async/await barriers",
            RootCauseType.UNKNOWN: "Manual triage required - ambiguous failure signals"
        }
        return fix_areas.get(root_cause, "Test code")

    def _find_related_tests(self, root_cause: RootCauseType, test_source: str) -> List[str]:
        """Find related tests that might share similar issues."""
        related = []
        if "get_shared_calculator" in test_source:
            related.append("tests using get_shared_calculator")
        if "time.sleep" in test_source:
            related.append("tests using time.sleep")
        if "random" in test_source:
            related.append("tests using unseeded random")
        return related
