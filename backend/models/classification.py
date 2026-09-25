"""Models for test classification and root cause analysis."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RootCauseType(str, Enum):
    """Classification of flaky test root causes."""
    TIMING = "timing"
    ORDERING = "ordering"
    STATE_LEAKAGE = "state_leakage"
    ENVIRONMENT = "environment"
    NETWORK = "network"
    RESOURCE = "resource"
    RACE_CONDITION = "race_condition"
    FLOATING_POINT = "floating_point"
    UNKNOWN = "unknown"


class Confidence(str, Enum):
    """Classification confidence level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    """Evidence supporting a classification."""
    type: str = Field(..., description="Type of evidence")
    description: str = Field(..., description="Human-readable description")
    source: str = Field(..., description="Where evidence was found")
    snippet: Optional[str] = Field(None, description="Code snippet or log excerpt")
    line_number: Optional[int] = None


class Classification(BaseModel):
    """Root cause classification for a flaky test."""
    classification_id: str
    test_name: str
    file_path: str
    root_cause: RootCauseType
    confidence: Confidence
    evidence: List[Evidence] = Field(default_factory=list)
    reasoning: str = Field(..., description="LLM reasoning for classification")
    suggested_fix_area: str = Field(..., description="Code area to fix")
    related_tests: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ClassificationBatch(BaseModel):
    """Batch of classifications from analysis run."""
    batch_id: str
    detection_id: str
    classifications: List[Classification]
    total_classified: int
    unclassified: List[str] = Field(default_factory=list, description="Tests that couldn't be classified")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
