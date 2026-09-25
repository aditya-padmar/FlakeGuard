"""Leakage subagent for detecting state leakage between tests."""
import re
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class LeakageSubagent:
    """Analyzes tests for state leakage issues."""
    
    PATTERNS = {
        "global_variable": r"^[A-Z_]+\s*=|global\s+\w+",
        "shared_instance": r"get_shared_|shared_instance|_instance\s*=",
        "missing_teardown": r"def setup|@pytest\.fixture(?!.*yield)",
        "mutable_default": r"def\s+\w+\([^)]*=\s*\[\]|def\s+\w+\([^)]*=\s*\{"
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
        Analyze test for state leakage issues.
        
        Checks for:
        - Shared mutable state
        - Missing teardown/cleanup
        - Global variables
        - Singleton patterns
        """
        evidence = []
        score = 0.0
        
        # Pattern-based analysis
        for pattern_name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, test_source, re.MULTILINE)
            if matches:
                evidence.append(Evidence(
                    type="code_pattern",
                    description=f"Found {len(matches)} instances of {pattern_name} pattern",
                    source="source_code",
                    snippet=matches[0] if matches else None
                ))
                score += 0.3
        
        # Check for cleanup patterns
        if "yield" not in test_source and "teardown" not in test_source.lower():
            if "setup" in test_source.lower() or "fixture" in test_source.lower():
                evidence.append(Evidence(
                    type="missing_pattern",
                    description="Setup found without corresponding teardown",
                    source="source_code"
                ))
                score += 0.25
        
        # Check error messages for state leakage indicators
        leakage_keywords = ["already", "stale", "previous", "unexpected value", "different"]
        for msg in error_messages:
            for keyword in leakage_keywords:
                if keyword.lower() in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error suggests state leakage: {keyword}",
                        source="error_message",
                        snippet=msg[:100]
                    ))
                    score += 0.15
        
        # Cap score at 1.0
        score = min(score, 1.0)
        
        return {
            "score": score,
            "evidence": evidence,
            "reasoning": self._generate_reasoning(evidence, score),
            "root_cause": RootCauseType.STATE_LEAKAGE
        }
    
    def _generate_reasoning(self, evidence: List[Evidence], score: float) -> str:
        """Generate human-readable reasoning."""
        if score < 0.3:
            return "No strong evidence of state leakage found."
        
        reasons = [e.description for e in evidence]
        return f"State leakage detected: {'; '.join(reasons[:3])}."
