"""Leakage subagent for detecting state leakage between tests."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class LeakageSubagent:
    """Analyzes tests for state leakage issues."""

    PATTERNS = {
        "shared_instance": r"get_shared_|shared_instance|_instance\s*=|singleton",
        "global_mutation": r"global\s+\w+|^[A-Z_]{3,}\s*=",
        "state_mutation": r"calc\.add|calc\.clear|calc\.subtract|\.append\(|\.pop\(|\.update\(",
        "missing_teardown": r"def setup|@pytest\.fixture(?!.*yield)"
    }

    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_file = Path(__file__).parent.parent / "prompts" / "leakage.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "Specialized AI subagent for state and fixture leakage."

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
        Analyze test for state leakage issues.
        
        Checks for:
        - Shared mutable state
        - Missing teardown/cleanup
        - Global variables and singleton mutations
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
                    if pattern_name in ("shared_instance", "global_mutation"):
                        score += 0.3
                    else:
                        score += 0.2

        # Check for test name indicating state leakage
        leakage_indicators = ["leak", "leaky", "mutation", "mutate", "dirty", "uncleaned", "shared_state", "global"]
        for kw in leakage_indicators:
            if kw in test_name.lower():
                evidence.append(Evidence(
                    type="naming_convention",
                    description=f"Test name indicates mutable state leakage: '{kw}'",
                    source="test_name",
                    snippet=test_name
                ))
                score += 0.35
                break

        # Check for lack of teardown in test source
        if "yield" not in test_source and "teardown" not in test_source.lower() and "clear" not in test_source.lower():
            if "setup" in test_source.lower() or "fixture" in test_source.lower() or "calc.add" in test_source:
                evidence.append(Evidence(
                    type="missing_pattern",
                    description="State mutation found without teardown/cleanup context",
                    source="source_code"
                ))
                score += 0.25

        # Check error messages for state leakage indicators
        leakage_keywords = ["already", "stale", "previous", "unexpected value", "state left dirty"]
        for msg in error_messages:
            for keyword in leakage_keywords:
                if keyword in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error suggests residual state: '{keyword}'",
                        source="error_message",
                        snippet=msg[:120]
                    ))
                    score += 0.2
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
            "root_cause": RootCauseType.STATE_LEAKAGE
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
            f"Analyze test '{test_name}' for state leakage / uncleaned fixtures.\n\n"
            f"Source:\n{test_source}\n\n"
            f"Errors: {error_messages}\n"
            f"History: {status_history}\n\n"
            "Explain if this test leaks state or is polluted by shared fixtures."
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
            return "No strong evidence of state or fixture leakage detected."

        snippets = [e.description for e in evidence if e.type == "code_pattern"]
        if snippets:
            return f"State leakage detected ({score:.0%}): {'; '.join(snippets[:3])}."
        return f"State leakage identified from shared mutable state and missing cleanup ({score:.0%})."
