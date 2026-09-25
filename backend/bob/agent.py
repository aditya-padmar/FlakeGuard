"""Bob - Main AI agent for flaky test classification."""
import json
from typing import List, Optional
import uuid
from datetime import datetime

from backend.models.classification import Classification, RootCauseType, Confidence, Evidence
from backend.models.detection import FlakyTest
from backend.bob.classifier import TestClassifier
from backend.config import settings


class BobAgent:
    """
    Main AI agent for classifying flaky tests.
    
    Bob analyzes test failures and determines the root cause
    using specialized subagents for different failure patterns.
    """
    
    def __init__(self):
        self.classifier = TestClassifier()
        self.llm_client = None  # Will be initialized based on config
        self._setup_llm()
    
    def _setup_llm(self):
        """Setup LLM client based on configuration."""
        if settings.openai_api_key:
            from openai import OpenAI
            self.llm_client = OpenAI(api_key=settings.openai_api_key)
        elif settings.anthropic_api_key:
            from anthropic import Anthropic
            self.llm_client = Anthropic(api_key=settings.anthropic_api_key)
    
    async def classify_test(
        self,
        flaky_test: FlakyTest,
        test_source: str,
        additional_context: Optional[dict] = None
    ) -> Classification:
        """
        Classify a flaky test to determine root cause.
        
        Args:
            flaky_test: The flaky test to classify
            test_source: Source code of the test
            additional_context: Optional context (logs, dependencies, etc.)
            
        Returns:
            Classification with root cause and evidence
        """
        classification_id = str(uuid.uuid4())
        
        # Use classifier to determine root cause
        classification_result = await self.classifier.classify(
            flaky_test=flaky_test,
            test_source=test_source,
            llm_client=self.llm_client,
            additional_context=additional_context
        )
        
        return Classification(
            classification_id=classification_id,
            test_name=flaky_test.test_name,
            file_path=flaky_test.file_path,
            root_cause=classification_result["root_cause"],
            confidence=classification_result["confidence"],
            evidence=classification_result["evidence"],
            reasoning=classification_result["reasoning"],
            suggested_fix_area=classification_result["suggested_fix_area"],
            related_tests=classification_result.get("related_tests", []),
            metadata={
                "agent": "bob",
                "model": classification_result.get("model", "unknown"),
                "processing_time": classification_result.get("processing_time")
            }
        )
    
    async def classify_batch(
        self,
        flaky_tests: List[FlakyTest],
        test_sources: dict
    ) -> List[Classification]:
        """
        Classify multiple flaky tests in batch.
        
        Args:
            flaky_tests: List of flaky tests to classify
            test_sources: Dict mapping test_name to source code
            
        Returns:
            List of Classifications
        """
        classifications = []
        
        for test in flaky_tests:
            source = test_sources.get(test.test_name, "")
            classification = await self.classify_test(test, source)
            classifications.append(classification)
        
        return classifications
    
    def get_status(self) -> dict:
        """Get agent status and configuration."""
        return {
            "name": "Bob",
            "version": "1.0.0",
            "llm_configured": self.llm_client is not None,
            "supported_root_causes": [r.value for r in RootCauseType]
        }
