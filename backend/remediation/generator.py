"""Fix generator for creating remediation suggestions."""
import re
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from backend.models.remediation import (
    Fix, FixSuggestion, FixType, FixStatus, CodeDiff
)
from backend.models.classification import Classification, RootCauseType
from backend.remediation.templates import FixTemplates
from backend.remediation.diff_generator import DiffGenerator


class FixGenerator:
    """Generates fix suggestions for flaky tests."""
    
    def __init__(self):
        self.templates = FixTemplates()
        self.diff_generator = DiffGenerator()
    
    async def generate_fix(
        self,
        classification: Classification,
        test_source: str,
        llm_client: Optional[Any] = None
    ) -> Fix:
        """
        Generate fix suggestions for a classified flaky test.
        
        Args:
            classification: Classification with root cause
            test_source: Source code of the test
            llm_client: Optional LLM client for advanced suggestions
            
        Returns:
            Fix with multiple suggestions
        """
        fix_id = str(uuid.uuid4())
        suggestions = []
        
        # Generate suggestions based on root cause
        if classification.root_cause == RootCauseType.TIMING:
            suggestions = self._generate_timing_fixes(
                classification, test_source
            )
        elif classification.root_cause == RootCauseType.ORDERING:
            suggestions = self._generate_ordering_fixes(
                classification, test_source
            )
        elif classification.root_cause == RootCauseType.STATE_LEAKAGE:
            suggestions = self._generate_leakage_fixes(
                classification, test_source
            )
        elif classification.root_cause == RootCauseType.ENVIRONMENT:
            suggestions = self._generate_environment_fixes(
                classification, test_source
            )
        else:
            suggestions = [self._generate_generic_fix(classification, test_source)]
        
        # Determine primary suggestion (highest confidence)
        if suggestions:
            primary = max(suggestions, key=lambda s: s.confidence)
        else:
            primary = suggestions[0] if suggestions else None
        
        return Fix(
            fix_id=fix_id,
            classification_id=classification.classification_id,
            test_name=classification.test_name,
            file_path=classification.file_path,
            suggestions=suggestions,
            primary_suggestion_id=primary.suggestion_id if primary else "",
            status=FixStatus.PROPOSED
        )
    
    def _generate_timing_fixes(
        self,
        classification: Classification,
        test_source: str
    ) -> List[FixSuggestion]:
        """Generate fixes for timing-related flakiness."""
        suggestions = []
        
        # Check for time.sleep
        if "time.sleep" in test_source or "sleep(" in test_source:
            suggestions.append(self._create_suggestion(
                fix_type=FixType.CODE_CHANGE,
                description="Replace hard-coded sleep with proper wait/retry mechanism",
                rationale="Hard-coded sleeps are unreliable and can cause flakiness",
                confidence=0.85,
                template="timing_await"
            ))
        
        # Check for timing assertions
        if "assert" in test_source and any(
            kw in test_source for kw in ["duration", "time", "elapsed", "<", ">"]
        ):
            suggestions.append(self._create_suggestion(
                fix_type=FixType.TIMEOUT_ADJUSTMENT,
                description="Remove or relax time-based assertions",
                rationale="Time-based assertions fail under varying system loads",
                confidence=0.75,
                template="timing_assertion"
            ))
        
        # Add retry mechanism
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CODE_CHANGE,
            description="Add retry mechanism for timing-sensitive operations",
            rationale="Retries handle transient timing issues gracefully",
            confidence=0.7,
            template="timing_retry"
        ))
        
        return suggestions
    
    def _generate_ordering_fixes(
        self,
        classification: Classification,
        test_source: str
    ) -> List[FixSuggestion]:
        """Generate fixes for order dependency issues."""
        suggestions = []
        
        # Add proper isolation
        suggestions.append(self._create_suggestion(
            fix_type=FixType.ISOLATION_FIX,
            description="Ensure each test has proper isolation with dedicated fixtures",
            rationale="Tests should not depend on execution order or shared state",
            confidence=0.85,
            template="ordering_isolation"
        ))
        
        # Add cleanup
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CLEANUP_ADDITION,
            description="Add teardown/cleanup to reset state between tests",
            rationale="Proper cleanup ensures tests start from a clean state",
            confidence=0.8,
            template="ordering_cleanup"
        ))
        
        return suggestions
    
    def _generate_leakage_fixes(
        self,
        classification: Classification,
        test_source: str
    ) -> List[FixSuggestion]:
        """Generate fixes for state leakage issues."""
        suggestions = []
        
        # Create fresh instances
        suggestions.append(self._create_suggestion(
            fix_type=FixType.ISOLATION_FIX,
            description="Use fresh test instances instead of shared/global state",
            rationale="Shared state can leak between tests causing unexpected failures",
            confidence=0.9,
            template="leakage_fresh_instance"
        ))
        
        # Add proper cleanup
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CLEANUP_ADDITION,
            description="Add proper teardown to clean up mutable state",
            rationale="Cleanup prevents state from affecting subsequent tests",
            confidence=0.85,
            template="leakage_cleanup"
        ))
        
        return suggestions
    
    def _generate_environment_fixes(
        self,
        classification: Classification,
        test_source: str
    ) -> List[FixSuggestion]:
        """Generate fixes for environment-related flakiness."""
        suggestions = []
        
        # Mock external dependencies
        suggestions.append(self._create_suggestion(
            fix_type=FixType.MOCK_INTRODUCTION,
            description="Mock external dependencies (network, file system, etc.)",
            rationale="Mocking makes tests deterministic and independent of environment",
            confidence=0.9,
            template="environment_mock"
        ))
        
        # Handle missing resources gracefully
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CODE_CHANGE,
            description="Add graceful handling for missing resources",
            rationale="Tests should skip or handle missing external resources gracefully",
            confidence=0.75,
            template="environment_graceful"
        ))
        
        # Use fixed random seed
        if "random" in test_source.lower():
            suggestions.append(self._create_suggestion(
                fix_type=FixType.CODE_CHANGE,
                description="Set fixed random seed for deterministic tests",
                rationale="Random values without fixed seed cause unpredictable behavior",
                confidence=0.95,
                template="environment_seed"
            ))
        
        return suggestions
    
    def _generate_generic_fix(
        self,
        classification: Classification,
        test_source: str
    ) -> FixSuggestion:
        """Generate a generic fix suggestion."""
        return self._create_suggestion(
            fix_type=FixType.QUARANTINE,
            description="Quarantine test until root cause is identified",
            rationale="Unknown flakiness requires manual investigation",
            confidence=0.5,
            template="generic_quarantine"
        )
    
    def _create_suggestion(
        self,
        fix_type: FixType,
        description: str,
        rationale: str,
        confidence: float,
        template: str
    ) -> FixSuggestion:
        """Create a fix suggestion."""
        return FixSuggestion(
            suggestion_id=str(uuid.uuid4()),
            fix_type=fix_type,
            description=description,
            rationale=rationale,
            confidence=confidence,
            estimated_effort="medium",
            breaking_changes=False,
            requires_review=True
        )
