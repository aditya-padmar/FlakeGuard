"""Ordering subagent for detecting test order dependencies."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class OrderingSubagent:
    """Analyzes tests for order dependency issues."""

    PATTERNS = {
        "shared_state": r"get_shared_|shared_state|_shared_|class_state|global\s+\w+",
        "order_assertion": r"operation_count\s*==\s*[1-9]|last_result\s*==\s*\d+|state\s*==|run_order",
        "order_naming": r"test_first|test_second|test_third|test_[0-9]|before_|after_",
        "shared_fixture": r"shared_fixture|@pytest\.fixture\(scope=[\"'](module|session|class)[\"']\)"
    }

    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_file = Path(__file__).parent.parent / "prompts" / "ordering.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "Specialized AI subagent for test order dependency."

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
        Analyze test for order dependency issues.
        
        Checks for:
        - Shared fixtures between tests
        - Global or class-level state
        - Tests that depend on execution order
        - State not properly cleaned up
        """
        evidence: List[Evidence] = []
        score = 0.0

        # Pattern-based analysis with line numbers
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
                    if pattern_name in ("order_naming", "order_assertion"):
                        score += 0.35
                    else:
                        score += 0.2

        # Check for sequence in test name
        order_indicators = ["first", "second", "third", "before", "after", "step", "ordered", "order"]
        for indicator in order_indicators:
            if indicator in test_name.lower():
                evidence.append(Evidence(
                    type="naming_convention",
                    description=f"Test name explicitly suggests sequential dependency: '{indicator}'",
                    source="test_name",
                    snippet=test_name
                ))
                score += 0.35
                break

        # Check error messages for state missing or order failure
        order_keywords = ["not found", "not set", "undefined", "expected initial state", "already initialized"]
        for msg in error_messages:
            for keyword in order_keywords:
                if keyword in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error message indicates missing prior state: '{keyword}'",
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
            "root_cause": RootCauseType.ORDERING
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
            f"Analyze test '{test_name}' for execution order dependency.\n\n"
            f"Source:\n{test_source}\n\n"
            f"Errors: {error_messages}\n"
            f"History: {status_history}\n\n"
            "Explain if this test depends on a specific execution order."
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
            return "No strong evidence of execution order dependency found."

        snippets = [e.description for e in evidence if e.type == "code_pattern"]
        if snippets:
            return f"Order dependency detected ({score:.0%}): {'; '.join(snippets[:3])}."
        return f"Order dependency detected from test structure and naming indicators ({score:.0%})."
