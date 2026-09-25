"""Models for audit logging and quarantine management."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class QuarantineTestStatus(str, Enum):
    """
    Status of a single quarantined test in a cross-reference audit.

    diagnosed_but_still_quarantined
        F2 found the root cause and F3 can generate a fix, but the test
        remains in the quarantine list — it should be unblocked.

    unexplained
        No F2 diagnosis available; manual investigation is still required.

    ready_to_unquarantine
        Fix has been verified; the quarantine entry can be removed.

    stale
        Test no longer exists in the codebase; the quarantine entry is stale.
    """
    DIAGNOSED_STILL_QUARANTINED = "diagnosed_but_still_quarantined"
    UNEXPLAINED = "unexplained"
    READY_TO_UNQUARANTINE = "ready_to_unquarantine"
    STALE = "stale"


class AuditedTest(BaseModel):
    """Single test entry in a quarantine audit report."""
    test_name: str
    diagnosed: bool = Field(..., description="True if F2 has a classification for this test")
    fixable: bool = Field(..., description="True if a remediable root cause was identified")
    status: QuarantineTestStatus
    root_cause: Optional[str] = Field(None, description="F2 root cause string, if diagnosed")
    confidence: Optional[str] = Field(None, description="F2 confidence level")
    fix_strategy: Optional[str] = Field(None, description="F3 strategy name, if fixable")
    quarantine_reason: Optional[str] = Field(None, description="Reason given in QUARANTINE.md")
    quarantined_at: Optional[datetime] = None
    source: str = Field("quarantine_file", description="Where this entry came from")


class QuarantineAuditReport(BaseModel):
    """
    Cross-reference of all quarantined tests against F2 diagnoses.

    This is the primary output of F4.
    """
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    quarantine_file: Optional[str] = None
    ci_config_files: List[str] = Field(default_factory=list)
    quarantined_tests: List[AuditedTest]
    total_quarantined: int
    diagnosed_count: int
    fixable_count: int
    unexplained_count: int
    summary: Dict[str, Any] = Field(default_factory=dict)


class QuarantineStatus(str, Enum):
    """Status of quarantined test."""
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REMOVED = "removed"


class AuditAction(str, Enum):
    """Types of audit actions."""
    TEST_DETECTED = "test_detected"
    TEST_CLASSIFIED = "test_classified"
    FIX_PROPOSED = "fix_proposed"
    FIX_APPLIED = "fix_applied"
    FIX_VERIFIED = "fix_verified"
    FIX_REJECTED = "fix_rejected"
    QUARANTINE_ADDED = "quarantine_added"
    QUARANTINE_REMOVED = "quarantine_removed"
    QUARANTINE_REVIEW = "quarantine_review"


class QuarantineEntry(BaseModel):
    """Entry in the test quarantine."""
    quarantine_id: str
    test_name: str
    file_path: str
    reason: str
    root_cause: Optional[str] = None
    quarantined_at: datetime = Field(default_factory=datetime.utcnow)
    quarantined_by: Optional[str] = None
    status: QuarantineStatus = QuarantineStatus.ACTIVE
    runs_since_quarantine: int = Field(default=0)
    runs_until_review: int = Field(default=10)
    last_review_at: Optional[datetime] = None
    last_review_result: Optional[str] = None
    resolution_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLog(BaseModel):
    """Audit log entry for tracking actions."""
    log_id: str
    action: AuditAction
    entity_type: str = Field(..., description="Type of entity: test, fix, quarantine")
    entity_id: str = Field(..., description="ID of the affected entity")
    actor: Optional[str] = Field(None, description="User or system that performed action")
    details: Dict[str, Any] = Field(default_factory=dict)
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuarantineReport(BaseModel):
    """Report on quarantine status."""
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_quarantined: int
    active_count: int
    under_review_count: int
    resolved_count: int
    average_quarantine_duration: float = Field(..., description="Average days in quarantine")
    oldest_quarantine_days: int
    upcoming_reviews: List[QuarantineEntry] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
