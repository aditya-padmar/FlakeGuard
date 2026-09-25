"""Timing subagent for detecting timing-related flakiness."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.models.classification import Evidence, RootCauseType


class TimingSubagent:
    """Analyzes tests for timing-related flakiness patterns."""

    PATTERNS = {
        "sleep": r"time\.sleep\s*\(|asyncio\.sleep\s*\(|sleep\s*\(",
        "timeout": r"timeout\s*=\s*\d+|wait\s*=\s*\d+|wait_for\s*\(",
        "timing_assertion": r"assert\s+elapsed|assert.*took.*long|assert.*<.*0\.\d+|assert.*duration",
        "time_measurement": r"time\.time\(\)|time\.perf_counter\(\)|start\s*=\s*time|elapsed\s*="
    }

    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_file = Path(__file__).parent.parent / "prompts" / "timing.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "Specialized AI subagent for timing-related flaky tests."

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
        Analyze test for timing-related flakiness.
        
        Checks for:
        - Hard-coded sleeps
        - Time-based assertions
        - Timeout dependencies
        - Race conditions in timing
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
                    if pattern_name in ("sleep", "timing_assertion"):
                        score += 0.4
                    else:
                        score += 0.2

        # Check test name for timing hints
        timing_name_keywords = ["timing", "timeout", "sleep", "delay", "slow", "async", "race"]
        for kw in timing_name_keywords:
            if kw in test_name.lower():
                evidence.append(Evidence(
                    type="naming_convention",
                    description=f"Test name indicates timing sensitivity: '{kw}'",
                    source="test_name",
                    snippet=test_name
                ))
                score += 0.25
                break

        # Check error messages for timing keywords
        timing_keywords = ["timeout", "timed out", "slow", "duration", "wait", "operation took too long"]
        for msg in error_messages:
            for keyword in timing_keywords:
                if keyword in msg.lower():
                    evidence.append(Evidence(
                        type="error_pattern",
                        description=f"Error message contains timing indicator: '{keyword}'",
                        source="error_message",
                        snippet=msg[:120]
                    ))
                    score += 0.25
                    break

        # Check status history for intermittent execution
        if status_history and len(status_history) >= 3:
            failures = sum(1 for s in status_history if str(s).lower() in ("failed", "teststatus.failed"))
            if 0 < failures < len(status_history):
                evidence.append(Evidence(
                    type="execution_history",
                    description=f"Intermittent pass/fail variance observed ({failures}/{len(status_history)} runs failed)",
                    source="status_history"
                ))
                score += 0.15

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
            "root_cause": RootCauseType.TIMING
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
            f"Analyze test '{test_name}' for timing flakiness.\n\n"
            f"Source:\n{test_source}\n\n"
            f"Errors: {error_messages}\n"
            f"History: {status_history}\n\n"
            "Explain if this test exhibits timing/race flakiness."
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
            return "No significant timing or race condition patterns detected in test code or execution logs."

        snippets = [e.description for e in evidence if e.type == "code_pattern"]
        if snippets:
            return f"High probability of timing flakiness ({score:.0%}): {'; '.join(snippets[:3])}."
        return f"Timing flakiness detected based on execution logs and test characteristics ({score:.0%})."
