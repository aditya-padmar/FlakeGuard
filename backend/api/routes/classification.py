"""Classification API routes."""
from fastapi import APIRouter, HTTPException
from typing import List

from backend.models.classification import Classification, RootCauseType
from backend.bob.agent import BobAgent
from backend.models.detection import FlakyTest

router = APIRouter()

# In-memory storage (replace with database in production)
classifications_db = {}

# Singleton agent — created once, reused across all requests
_bob_agent = BobAgent()


@router.post("/classify", response_model=Classification)
async def classify_test(test: FlakyTest):
    """
    Classify a flaky test to determine root cause.

    Returns classification with evidence and suggested fixes.
    """
    classification = await _bob_agent.classify_test(test)
    classifications_db[classification.classification_id] = classification
    return classification


@router.post("/classify-batch", response_model=List[Classification])
async def classify_batch(tests: List[FlakyTest]):
    """
    Classify multiple flaky tests in parallel.

    All tests are dispatched to Bob's subagents simultaneously.
    """
    results = await _bob_agent.classify_batch(tests)
    for c in results:
        classifications_db[c.classification_id] = c
    return results


@router.get("/bob/status")
async def get_bob_status():
    """Return Bob agent status: architecture, subagents, and LLM config."""
    return _bob_agent.get_status()


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
