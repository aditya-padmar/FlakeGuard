"""Timing subagent for detecting timing-related flakiness."""
import re
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class TimingSubagent:
    """Analyzes tests for timing-related flakiness patterns."""
    
    PATTERNS = {
        "sleep": r"time\.sleep|sleep\s*\(",
        "timeout": r"timeout|wait\s*=\s*\d+",
        "timing_assertion": r"assert.*<\s*\d|assert.*>\s*\d.*second|assert.*duration",
        "time_measurement": r"start_time|end_time|elapsed|time\.time\(\)"
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
        Analyze test for timing-related flakiness.
        
        Checks for:
        - Hard-coded sleeps
        - Time-based assertions
        - Timeout dependencies
        - Race conditions in timing
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
        
        # Check error messages for timing keywords
        timing_keywords = ["timeout", "timed out", "slow", "duration", "wait"]
        for msg in error_messages:
            for keyword in timing_keywords:
                if keyword.lower() in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error message contains timing keyword: {keyword}",
                        source="error_message",
                        snippet=msg[:100]
                    ))
                    score += 0.15
        
        # Check status history for intermittent failures
        if status_history and len(status_history) >= 3:
            failures = sum(1 for s in status_history if s == "failed")
            if 0 < failures < len(status_history):
                # Intermittent failure suggests timing
                score += 0.2
        
        # Cap score at 1.0
        score = min(score, 1.0)
        
        return {
            "score": score,
            "evidence": evidence,
            "reasoning": self._generate_reasoning(evidence, score),
            "root_cause": RootCauseType.TIMING
        }
    
    def _generate_reasoning(self, evidence: List[Evidence], score: float) -> str:
        """Generate human-readable reasoning."""
        if score < 0.3:
            return "No strong evidence of timing-related flakiness found."
        
        reasons = [e.description for e in evidence]
        return f"Timing-related flakiness detected: {'; '.join(reasons[:3])}."
