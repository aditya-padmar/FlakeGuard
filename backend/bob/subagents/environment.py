"""Environment subagent for detecting environment-related flakiness."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class EnvironmentSubagent:
    """Analyzes tests for environment, network, and non-determinism flakiness."""

    PATTERNS = {
        "env_variable": r"os\.getenv|os\.environ|getenv\(|environ\[",
        "network_call": r"requests\.|httpx\.|urllib|aiohttp|fetch\s*\(|https?://|api_url|socket\.",
        "random_value": r"random\.random|random\.choice|random\.randint|random\.randrange|random\.shuffle",
        "ci_check": r"os\.getenv\([\"']CI[\"']\)|is_ci",
        "file_system": r"open\s*\(|Path\s*\(|tempfile\."
    }

    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_file = Path(__file__).parent.parent / "prompts" / "environment.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "Specialized AI subagent for environment and network flakiness."

    async def analyze(
        self,
        test_name: str,
        test_source: str,
        error_messages: List[str],
        status_history: List[str],
        llm_client: Any = None,
        context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze test for environment-related flakiness.
        
        Checks for:
        - Environment variable dependencies
        - Network calls & external APIs
        - Random number generation without seeds
        - Date/time or CI vs local discrepancies
        """
        evidence: List[Evidence] = []
        score = 0.0

        # Line-by-line pattern matching
        lines = test_source.splitlines()
        for idx, line in enumerate(lines, start=1):
            for pattern_name, pattern in self.PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    evidence.append(Evidence(
                        type="code_pattern",
                        description=f"Line {idx}: Found {pattern_name} pattern: '{line.strip()}'",
                        source="source_code",
                        snippet=line.strip(),
                        line_number=idx
                    ))
                    if pattern_name in ("network_call", "random_value"):
                        score += 0.4
                    else:
                        score += 0.25

        # Check for unseeded randomness specifically
        if "random" in test_source.lower() and "seed" not in test_source.lower():
            evidence.append(Evidence(
                type="missing_pattern",
                description="Pseudorandom generator used without explicit deterministic seed",
                source="source_code"
            ))
            score += 0.35

        # Check test name for environment indicators
        env_indicators = ["env", "network", "random", "external", "resource", "ci", "socket"]
        for kw in env_indicators:
            if kw in test_name.lower():
                evidence.append(Evidence(
                    type="naming_convention",
                    description=f"Test name indicates environmental/external dependency: '{kw}'",
                    source="test_name",
                    snippet=test_name
                ))
                score += 0.3
                break

        # Check error messages for environment keywords
        env_keywords = ["connection", "network", "socket", "dns", "api", "environment", "unreachable", "refused"]
        for msg in error_messages:
            for keyword in env_keywords:
                if keyword in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error indicates environment/network failure: '{keyword}'",
                        source="error_message",
                        snippet=msg[:120]
                    ))
                    score += 0.25
                    break

        # If LLM client is available, attempt enhanced agent evaluation
        llm_reasoning = None
        if llm_client:
            try:
                llm_reasoning = await self._run_llm_analysis(
                    llm_client=llm_client,
                    test_name=test_name,
                    test_source=test_source,
                    error_messages=error_messages,
                    status_history=status_history
                )
            except Exception:
                pass

        score = min(score, 1.0)
        reasoning = llm_reasoning or self._generate_reasoning(evidence, score)

        return {
            "score": score,
            "evidence": evidence,
            "reasoning": reasoning,
            "root_cause": RootCauseType.ENVIRONMENT
        }

    async def _run_llm_analysis(
        self,
        llm_client: Any,
        test_name: str,
        test_source: str,
        error_messages: List[str],
        status_history: List[str]
    ) -> Optional[str]:
        """Invoke LLM client with the specialized prompt."""
        system_msg = self.prompt_template
        user_msg = (
            f"Analyze test '{test_name}' for environment or network flakiness.\n\n"
            f"Source:\n{test_source}\n\n"
            f"Errors: {error_messages}\n"
            f"History: {status_history}\n\n"
            "Explain if this test depends on environment, network, or unseeded randomness."
        )
        if hasattr(llm_client, "chat") and hasattr(llm_client.chat, "completions"):
            response = llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=250
            )
            return response.choices[0].message.content
        return None

    def _generate_reasoning(self, evidence: List[Evidence], score: float) -> str:
        """Generate human-readable reasoning."""
        if score < 0.3:
            return "No strong evidence of environment or network dependency found."

        snippets = [e.description for e in evidence if e.type == "code_pattern"]
        if snippets:
            return f"Environment/network dependency detected ({score:.0%}): {'; '.join(snippets[:3])}."
        return f"Environment or unseeded randomness flakiness identified ({score:.0%})."
