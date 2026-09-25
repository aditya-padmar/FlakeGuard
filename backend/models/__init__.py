"""Models package for FlakeGuard data structures."""
from backend.models.detection import TestRun, FlakyTest, DetectionResult
from backend.models.classification import Classification, RootCauseType
from backend.models.remediation import Fix, FixSuggestion
from backend.models.audit import AuditLog, QuarantineEntry

__all__ = [
    "TestRun",
    "FlakyTest", 
    "DetectionResult",
    "Classification",
    "RootCauseType",
    "Fix",
    "FixSuggestion",
    "AuditLog",
    "QuarantineEntry"
]
