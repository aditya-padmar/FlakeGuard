"""Bob - Main AI agent for flaky test classification and orchestration."""
import ast
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

from backend.models.classification import Classification, RootCauseType, Confidence, Evidence
from backend.models.detection import FlakyTest
from backend.bob.classifier import TestClassifier
from backend.config import settings


class BobAgent:
    """
    Main IBM Bob 2.0 AI agent for classifying flaky tests.
    
    Orchestrates the classification pipeline:
    1. Resolves test source code from disk / AST if not provided.
    2. Spawns 4 parallel subagents (one per root-cause hypothesis).
    3. Evaluates competing hypotheses and selects the winning verdict.
    4. Automatically logs session evidence to docs/bob-sessions/ for hackathon proof.
    """

    def __init__(self, sessions_dir: Optional[str] = None):
        self.classifier = TestClassifier()
        self.llm_client = None
        self.sessions_dir = Path(sessions_dir or "docs/bob-sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._setup_llm()

    def _setup_llm(self):
        """Setup LLM client based on configuration."""
        if settings.openai_api_key:
            try:
                from openai import OpenAI
                self.llm_client = OpenAI(api_key=settings.openai_api_key)
            except Exception:
                self.llm_client = None
        elif settings.anthropic_api_key:
            try:
                from anthropic import Anthropic
                self.llm_client = Anthropic(api_key=settings.anthropic_api_key)
            except Exception:
                self.llm_client = None

    def extract_test_source(self, file_path: str, test_name: str) -> str:
        """
        Extract the target test method source code from disk using AST analysis.
        Searches relative, sample-repo, and repository paths.
        """
        path = Path(file_path)
        candidates = [
            path,
            Path("sample-repo") / file_path,
            Path("sample-repo/tests") / path.name,
            Path(".") / path.name
        ]

        resolved_path = None
        for cand in candidates:
            if cand.is_file():
                resolved_path = cand
                break

        if not resolved_path:
            # Search by filename
            matches = list(Path(".").glob(f"**/{path.name}"))
            if matches:
                resolved_path = matches[0]

        if not resolved_path:
            return ""

        try:
            content = resolved_path.read_text(encoding="utf-8")
        except Exception:
            return ""

        # Extract target function or method name
        clean_method = test_name.split("::")[-1].split(".")[-1]

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == clean_method:
                    lines = content.splitlines()
                    func_lines = lines[node.lineno - 1 : node.end_lineno]
                    return "\n".join(func_lines)
        except Exception:
            pass

        return content

    async def classify_test(
        self,
        flaky_test: FlakyTest,
        test_source: str = "",
        additional_context: Optional[dict] = None
    ) -> Classification:
        """
        Classify a flaky test to determine root cause.
        
        Args:
            flaky_test: The flaky test to classify
            test_source: Source code of the test (if empty, auto-extracted)
            additional_context: Optional context (logs, dependencies, etc.)
            
        Returns:
            Classification with root cause and evidence
        """
        classification_id = str(uuid.uuid4())

        # Auto-extract test source if not provided or is placeholder
        if not test_source or test_source.startswith("#"):
            extracted = self.extract_test_source(flaky_test.file_path, flaky_test.test_name)
            if extracted:
                test_source = extracted

        # Use parallel subagent classifier
        classification_result = await self.classifier.classify(
            flaky_test=flaky_test,
            test_source=test_source,
            llm_client=self.llm_client,
            additional_context=additional_context
        )

        metadata = {
            "agent": "bob",
            "model": classification_result.get("model", "bob-agent-parallel-rules"),
            "processing_time": classification_result.get("processing_time"),
            "subagent_scores": classification_result.get("subagent_scores", {})
        }

        classification = Classification(
            classification_id=classification_id,
            test_name=flaky_test.test_name,
            file_path=flaky_test.file_path,
            root_cause=classification_result["root_cause"],
            confidence=classification_result["confidence"],
            evidence=classification_result["evidence"],
            reasoning=classification_result["reasoning"],
            suggested_fix_area=classification_result["suggested_fix_area"],
            related_tests=classification_result.get("related_tests", []),
            metadata=metadata
        )

        # Log session evidence for IBM Bob hackathon audit
        self._record_session_evidence(classification, test_source)

        return classification

    async def classify_batch(
        self,
        flaky_tests: List[FlakyTest],
        test_sources: Optional[Dict[str, str]] = None
    ) -> List[Classification]:
        """
        Classify multiple flaky tests in batch, all running in parallel.
        """
        import asyncio
        test_sources = test_sources or {}

        tasks = [
            self.classify_test(test, test_sources.get(test.test_name, ""))
            for test in flaky_tests
        ]
        return await asyncio.gather(*tasks)

    def _record_session_evidence(self, classification: Classification, test_source: str):
        """
        Export Agent-mode session summary to docs/bob-sessions/ as submission evidence.
        Satisfies PRD FR10 requirement.
        """
        try:
            now = datetime.now(timezone.utc)
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", classification.test_name)[:50]
            session_file = self.sessions_dir / f"session_{timestamp_str}_{safe_name}.json"

            session_data = {
                "session_id": classification.classification_id,
                "timestamp": now.isoformat(),
                "test_name": classification.test_name,
                "file_path": classification.file_path,
                "verdict": {
                    "root_cause": classification.root_cause.value,
                    "confidence": classification.confidence.value,
                    "suggested_fix_area": classification.suggested_fix_area
                },
                "subagent_scores": classification.metadata.get("subagent_scores", {}),
                "reasoning": classification.reasoning,
                "evidence": [e.model_dump() for e in classification.evidence],
                "test_source_snippet": test_source[:500] if test_source else ""
            }

            session_file.write_text(json.dumps(session_data, indent=2), encoding="utf-8")

            # Also maintain a running log in SESSION_LOG.md
            log_file = self.sessions_dir / "SESSION_LOG.md"
            log_entry = (
                f"\n### Session: `{classification.test_name}` ({now.strftime('%Y-%m-%d %H:%M:%S UTC')})\n"
                f"- **Verdict**: `{classification.root_cause.value.upper()}` ({classification.confidence.value.upper()} confidence)\n"
                f"- **Subagent Scores**: `{classification.metadata.get('subagent_scores', {})}`\n"
                f"- **Reasoning**: {classification.reasoning}\n"
                f"- **Evidence Count**: {len(classification.evidence)} items identified\n"
            )
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

        except Exception as e:
            logger.warning("Session evidence logging failed for %s: %s", classification.test_name, e)

    def get_status(self) -> dict:
        """Get agent status and configuration."""
        return {
            "name": "Bob",
            "version": "2.0.0",
            "architecture": "parallel_subagents",
            "llm_configured": self.llm_client is not None,
            "supported_root_causes": [r.value for r in RootCauseType],
            "subagents": list(self.classifier.subagents.keys())
        }
