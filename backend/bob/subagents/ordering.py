"""Ordering subagent for detecting test order dependencies."""
import re
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class OrderingSubagent:
    """Analyzes tests for order dependency issues."""
    
    PATTERNS = {
        "shared_fixture": r"shared_fixture|conftest\.py|@pytest\.fixture\s*\(",
        "class_level_setup": r"setup_class|setup_method|@classmethod",
        "global_state": r"global\s+\w+|_shared_|shared_state|class_state",
        "order_dependent": r"test_[a-z]+_[0-9]+|test_first|test_second|test_final"
    }
    
    async def analyze(
        self,
        test_name: str,
        test_source: str,
        error_messages: List[str],
        status_history: List[str],
        llm_client: Any,
        context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze test for order dependency issues.
        
        Checks for:
        - Shared fixtures between tests
        - Global or class-level state
        - Tests that depend on execution order
        - State not properly cleaned up
        """
        evidence = []
        score = 0.0
        
        # Pattern-based analysis
        for pattern_name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, test_source, re.IGNORECASE)
            if matches:
                evidence.append(Evidence(
                    type="code_pattern",
                    description=f"Found {len(matches)} instances of {pattern_name} pattern",
                    source="source_code",
                    snippet=matches[0] if matches else None
                ))
                score += 0.25
        
        # Check for test ordering in name
        order_indicators = ["first", "second", "third", "before", "after", "final"]
        for indicator in order_indicators:
            if indicator in test_name.lower():
                evidence.append(Evidence(
                    type="naming_convention",
                    description=f"Test name suggests order dependency: {indicator}",
                    source="test_name"
                ))
                score += 0.3
        
        # Check error messages for order-related keywords
        order_keywords = ["not found", "not set", "undefined", "null", "none"]
        for msg in error_messages:
            for keyword in order_keywords:
                if keyword.lower() in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error suggests state issue: {keyword}",
                        source="error_message",
                        snippet=msg[:100]
                    ))
                    score += 0.1
        
        # Cap score at 1.0
        score = min(score, 1.0)
        
        return {
            "score": score,
            "evidence": evidence,
            "reasoning": self._generate_reasoning(evidence, score),
            "root_cause": RootCauseType.ORDERING
        }
    
    def _generate_reasoning(self, evidence: List[Evidence], score: float) -> str:
        """Generate human-readable reasoning."""
        if score < 0.3:
            return "No strong evidence of order dependency found."
        
        reasons = [e.description for e in evidence]
        return f"Order dependency detected: {'; '.join(reasons[:3])}."
