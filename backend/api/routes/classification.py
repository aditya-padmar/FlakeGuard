"""Classification API routes."""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid

from backend.models.classification import Classification, RootCauseType
from backend.bob.agent import BobAgent
from backend.models.detection import FlakyTest

router = APIRouter()

# In-memory storage (replace with database in production)
classifications_db = {}


@router.post("/classify", response_model=Classification)
async def classify_test(test: FlakyTest):
    """
    Classify a flaky test to determine root cause.
    
    Returns classification with evidence and suggested fixes.
    """
    agent = BobAgent()
    
    # In production, fetch test source from repository
    test_source = "# Test source would be fetched here"
    
    classification = await agent.classify_test(test, test_source)
    
    classifications_db[classification.classification_id] = classification
    
    return classification


@router.get("/classifications", response_model=List[Classification])
async def list_classifications():
    """List all classifications."""
    return list(classifications_db.values())


@router.get("/classifications/{classification_id}", response_model=Classification)
async def get_classification(classification_id: str):
    """Get a specific classification by ID."""
    if classification_id not in classifications_db:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    return classifications_db[classification_id]


@router.get("/root-causes")
async def list_root_causes():
    """List all possible root cause types."""
    return {
        "root_causes": [
            {"type": r.value, "description": _get_root_cause_description(r)}
            for r in RootCauseType
        ]
    }


def _get_root_cause_description(cause: RootCauseType) -> str:
    """Get human-readable description for root cause."""
    descriptions = {
        RootCauseType.TIMING: "Test depends on timing or has race conditions",
        RootCauseType.ORDERING: "Test depends on execution order",
        RootCauseType.STATE_LEAKAGE: "Test leaks state between executions",
        RootCauseType.ENVIRONMENT: "Test depends on external environment",
        RootCauseType.NETWORK: "Test has network-related flakiness",
        RootCauseType.RESOURCE: "Test has resource constraints",
        RootCauseType.RACE_CONDITION: "Test has concurrent execution issues",
        RootCauseType.FLOATING_POINT: "Test has floating point precision issues",
        RootCauseType.UNKNOWN: "Root cause could not be determined"
    }
    return descriptions.get(cause, "Unknown root cause")
