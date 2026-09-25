"""Models for test remediation and fix suggestions."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class FixStatus(str, Enum):
    """Status of a fix suggestion."""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"
    VERIFIED = "verified"
    FAILED = "failed"


class FixType(str, Enum):
    """Type of fix applied."""
    CODE_CHANGE = "code_change"
    FIXTURE_UPDATE = "fixture_update"
    TIMEOUT_ADJUSTMENT = "timeout_adjustment"
    ISOLATION_FIX = "isolation_fix"
    CLEANUP_ADDITION = "cleanup_addition"
    MOCK_INTRODUCTION = "mock_introduction"
    CONFIGURATION = "configuration"
    TEST_REMOVAL = "test_removal"
    QUARANTINE = "quarantine"


class CodeDiff(BaseModel):
    """Code diff for a fix."""
    file_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    unified_diff: str = Field(..., description="Unified diff format")
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class FixSuggestion(BaseModel):
    """Individual fix suggestion."""
    suggestion_id: str
    fix_type: FixType
    description: str = Field(..., description="Human-readable description")
    rationale: str = Field(..., description="Why this fix should work")
    diff: Optional[CodeDiff] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in fix success")
    estimated_effort: str = Field(..., description="Effort estimate: low/medium/high")
    breaking_changes: bool = Field(default=False)
    requires_review: bool = Field(default=True)


class Fix(BaseModel):
    """Complete fix for a flaky test."""
    fix_id: str
    classification_id: str
    test_name: str
    file_path: str
    suggestions: List[FixSuggestion]
    primary_suggestion_id: str = Field(..., description="ID of the recommended suggestion")
    status: FixStatus = FixStatus.PROPOSED
    applied_by: Optional[str] = None
    applied_at: Optional[datetime] = None
    verified_runs: int = Field(default=0, description="Number of successful runs after fix")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RemediationResult(BaseModel):
    """Result of applying a fix."""
    result_id: str
    fix_id: str
    success: bool
    test_runs_after_fix: int
    test_passes_after_fix: int
    verification_status: str
    remaining_flakiness: Optional[float] = None
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
