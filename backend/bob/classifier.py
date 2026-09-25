"""Test classifier using specialized subagents."""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from backend.models.classification import RootCauseType, Confidence, Evidence
from backend.models.detection import FlakyTest
from backend.bob.subagents.timing import TimingSubagent
from backend.bob.subagents.ordering import OrderingSubagent
from backend.bob.subagents.leakage import LeakageSubagent
from backend.bob.subagents.environment import EnvironmentSubagent


class TestClassifier:
    """
    Classifier that coordinates subagents for root cause analysis.
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
        llm_client: Any,
        additional_context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Classify a flaky test using subagents.
        
        Each subagent analyzes the test for its specific failure pattern.
        The classifier then selects the most likely root cause.
        """
        start_time = time.time()
        
        # Run all subagent analyses
        subagent_results = {}
        
        for cause_type, subagent in self.subagents.items():
            result = await subagent.analyze(
                test_name=flaky_test.test_name,
                test_source=test_source,
                error_messages=flaky_test.recent_failures,
                status_history=flaky_test.status_history,
                llm_client=llm_client,
                context=additional_context
            )
            subagent_results[cause_type] = result
        
        # Select the most likely root cause
        root_cause, confidence, evidence = self._select_root_cause(
            subagent_results,
            flaky_test
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(subagent_results, root_cause)
        
        # Determine fix area
        suggested_fix_area = self._determine_fix_area(root_cause, test_source)
        
        processing_time = time.time() - start_time
        
        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": evidence,
            "reasoning": reasoning,
            "suggested_fix_area": suggested_fix_area,
            "related_tests": self._find_related_tests(root_cause, test_source),
            "model": "gpt-4" if llm_client else "rule-based",
            "processing_time": processing_time
        }
    
    def _select_root_cause(
        self,
        subagent_results: Dict[RootCauseType, Dict],
        flaky_test: FlakyTest
    ) -> tuple:
        """Select the most likely root cause from subagent results."""
        # Find the cause with highest score
        best_cause = RootCauseType.UNKNOWN
        best_score = 0.0
        best_evidence = []
        
        for cause_type, result in subagent_results.items():
            score = result.get("score", 0.0)
            if score > best_score:
                best_score = score
                best_cause = cause_type
                best_evidence = result.get("evidence", [])
        
        # Map score to confidence
        if best_score >= 0.8:
            confidence = Confidence.HIGH
        elif best_score >= 0.5:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW
        
        return best_cause, confidence, best_evidence
    
    def _generate_reasoning(
        self,
        subagent_results: Dict[RootCauseType, Dict],
        root_cause: RootCauseType
    ) -> str:
        """Generate human-readable reasoning for the classification."""
        result = subagent_results.get(root_cause, {})
        return result.get("reasoning", "Classification based on pattern analysis.")
    
    def _determine_fix_area(self, root_cause: RootCauseType, test_source: str) -> str:
        """Determine the code area that needs to be fixed."""
        fix_areas = {
            RootCauseType.TIMING: "Test timing and assertions",
            RootCauseType.ORDERING: "Test execution order and dependencies",
            RootCauseType.STATE_LEAKAGE: "Test isolation and cleanup",
            RootCauseType.ENVIRONMENT: "Environment configuration and setup",
            RootCauseType.RACE_CONDITION: "Async operations and synchronization",
            RootCauseType.UNKNOWN: "Unknown - manual investigation required"
        }
        
        return fix_areas.get(root_cause, "Test code")
    
    def _find_related_tests(self, root_cause: RootCauseType, test_source: str) -> List[str]:
        """Find related tests that might have similar issues."""
        # Placeholder - would analyze imports and fixtures
        return []
