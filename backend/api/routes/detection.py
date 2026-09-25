"""Detection API routes."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime

from backend.models.detection import TestRun, FlakyTest, DetectionResult
from backend.harness.runner import TestRunner
from backend.harness.executor import TestExecutor
from backend.harness.analyzer import TestAnalyzer

router = APIRouter()

# In-memory storage (replace with database in production)
runs_db = {}
detections_db = {}


@router.post("/runs", response_model=TestRun)
async def create_test_run(run: TestRun):
    """
    Create a new test run record.
    
    Records test execution results for later flaky detection analysis.
    """
    if not run.run_id:
        run.run_id = str(uuid.uuid4())
    
    runs_db[run.run_id] = run
    return run


@router.get("/runs", response_model=List[TestRun])
async def list_test_runs(limit: int = 10):
    """List recent test runs."""
    runs = list(runs_db.values())
    runs.sort(key=lambda r: r.timestamp, reverse=True)
    return runs[:limit]


@router.get("/runs/{run_id}", response_model=TestRun)
async def get_test_run(run_id: str):
    """Get a specific test run by ID."""
    if run_id not in runs_db:
        raise HTTPException(status_code=404, detail="Test run not found")
    return runs_db[run_id]


@router.post("/analyze", response_model=DetectionResult)
async def analyze_test_runs(min_runs: int = 3):
    """
    Analyze test runs to detect flaky tests.
    
    Requires at least min_runs test runs for reliable detection.
    """
    if len(runs_db) < min_runs:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {min_runs} test runs for analysis"
        )
    
    runs = list(runs_db.values())
    analyzer = TestAnalyzer()
    
    detection = await analyzer.analyze_runs(runs)
    detections_db[detection.detection_id] = detection
    
    return detection


@router.get("/detections", response_model=List[DetectionResult])
async def list_detections(limit: int = 10):
    """List recent detection results."""
    detections = list(detections_db.values())
    detections.sort(key=lambda d: d.timestamp, reverse=True)
    return detections[:limit]


@router.get("/detections/{detection_id}", response_model=DetectionResult)
async def get_detection(detection_id: str):
    """Get a specific detection result by ID."""
    if detection_id not in detections_db:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detections_db[detection_id]


@router.post("/execute")
async def execute_tests(
    repo_path: str,
    num_runs: int = 5,
    test_pattern: Optional[str] = None
):
    """
    Execute tests multiple times to detect flakiness.
    
    This is an async operation that will run tests and record results.
    """
    # This would normally be a background task
    return {
        "message": "Test execution started",
        "repo_path": repo_path,
        "num_runs": num_runs,
        "test_pattern": test_pattern
    }
