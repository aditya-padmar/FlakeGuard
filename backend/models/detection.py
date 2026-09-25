"""Models for test detection and flaky test identification."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TestStatus(str, Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestExecution(BaseModel):
    """Single test execution record."""
    test_name: str = Field(..., description="Full test name (module::class::method)")
    file_path: str = Field(..., description="Path to test file")
    status: TestStatus
    duration: float = Field(..., description="Execution time in seconds")
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TestRun(BaseModel):
    """Complete test run with all executions."""
    run_id: str = Field(..., description="Unique run identifier")
    repository: str = Field(..., description="Repository name or URL")
    branch: str = Field(default="main", description="Git branch")
    commit_sha: str = Field(..., description="Git commit SHA")
    ci_build_id: Optional[str] = Field(None, description="CI/CD build ID")
    executions: List[TestExecution] = Field(default_factory=list)
    total_tests: int = Field(default=0)
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FlakyTest(BaseModel):
    """Identified flaky test with statistics."""
    test_name: str
    file_path: str
    first_seen: datetime
    last_seen: datetime
    total_runs: int
    pass_count: int
    fail_count: int
    flake_rate: float = Field(..., description="Percentage of times test was flaky")
    recent_failures: List[str] = Field(default_factory=list, description="Recent error messages")
    status_history: List[TestStatus] = Field(default_factory=list)


class DetectionResult(BaseModel):
    """Result of flaky test detection analysis."""
    detection_id: str
    repository: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    total_test_runs: int
    flaky_tests: List[FlakyTest]
    detection_confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
