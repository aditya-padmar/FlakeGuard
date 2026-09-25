"""Environment subagent for detecting environment-related flakiness."""
import re
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class EnvironmentSubagent:
    """Analyzes tests for environment-related flakiness."""
    
    PATTERNS = {
        "env_variable": r"os\.getenv|os\.environ|getenv|environ",
        "network_call": r"requests\.|httpx\.|urllib|aiohttp|fetch\s*\(",
        "file_system": r"open\s*\(|write\s*\(|read\s*\(|Path\s*\(",
        "random_value": r"random\.|randint|randrange|shuffle",
        "datetime_now": r"datetime\.now|datetime\.today|time\.time\(\)"
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
        Analyze test for environment-related flakiness.
        
        Checks for:
        - Environment variable dependencies
        - Network calls
        - File system operations
        - Random number generation
        - Date/time dependencies
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
                score += 0.2
        
        # Check error messages for environment-related keywords
        env_keywords = [
            "connection", "timeout", "network", "socket", "dns",
            "permission", "access denied", "not found", "file",
            "environment"
        ]
        
        for msg in error_messages:
            for keyword in env_keywords:
                if keyword.lower() in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error suggests environment issue: {keyword}",
                        source="error_message",
                        snippet=msg[:100]
                    ))
                    score += 0.1
        
        # Check for randomness
        if "random" in test_source.lower():
            # Check if random seed is set
            if "seed" not in test_source.lower():
                evidence.append(Evidence(
                    type="missing_pattern",
                    description="Random usage without fixed seed",
                    source="source_code"
                ))
                score += 0.25
        
        # Cap score at 1.0
        score = min(score, 1.0)
        
        return {
            "score": score,
            "evidence": evidence,
            "reasoning": self._generate_reasoning(evidence, score),
            "root_cause": RootCauseType.ENVIRONMENT
        }
    
    def _generate_reasoning(self, evidence: List[Evidence], score: float) -> str:
        """Generate human-readable reasoning."""
        if score < 0.3:
            return "No strong evidence of environment-related flakiness found."
        
        reasons = [e.description for e in evidence]
        return f"Environment-related flakiness detected: {'; '.join(reasons[:3])}."
