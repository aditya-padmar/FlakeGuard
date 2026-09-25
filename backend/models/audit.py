"""Models for audit logging and quarantine management."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


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
