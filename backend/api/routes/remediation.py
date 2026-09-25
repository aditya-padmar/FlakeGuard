"""Remediation API routes."""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid

from backend.models.remediation import Fix, FixSuggestion, FixStatus
from backend.models.classification import Classification
from backend.remediation.generator import FixGenerator
from backend.bob.agent import BobAgent

router = APIRouter()

# In-memory storage
fixes_db = {}

_bob_agent = BobAgent()


@router.post("/generate", response_model=Fix)
async def generate_fix(classification: Classification):
    """
    Generate fix suggestions for a classified flaky test.
    
    Returns multiple fix suggestions with confidence scores.
    """
    generator = FixGenerator()

    # Extract real source code using Bob's AST extractor
    test_source = _bob_agent.extract_test_source(
        classification.file_path, classification.test_name
    )

    fix = await generator.generate_fix(classification, test_source)
    fixes_db[fix.fix_id] = fix

    return fix


@router.get("/fixes", response_model=List[Fix])
async def list_fixes(status: FixStatus = None):
    """List all fixes, optionally filtered by status."""
    fixes = list(fixes_db.values())
    
    if status:
        fixes = [f for f in fixes if f.status == status]
    
    return fixes


@router.get("/fixes/{fix_id}", response_model=Fix)
async def get_fix(fix_id: str):
    """Get a specific fix by ID."""
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail="Fix not found")
    
    return fixes_db[fix_id]


@router.post("/fixes/{fix_id}/apply")
async def apply_fix(fix_id: str, suggestion_id: str):
    """
    Apply a specific fix suggestion.
    
    Marks the fix as applied and records the action.
    """
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail="Fix not found")
    
    fix = fixes_db[fix_id]
    
    # Verify suggestion exists
    suggestion = next(
        (s for s in fix.suggestions if s.suggestion_id == suggestion_id),
        None
    )
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Update fix status
    fix.status = FixStatus.APPLIED
    fix.applied_by = "api_user"  # Would be actual user in production
    
    return {
        "message": "Fix applied",
        "fix_id": fix_id,
        "suggestion_id": suggestion_id,
        "fix_type": suggestion.fix_type
    }


@router.post("/fixes/{fix_id}/verify")
async def verify_fix(fix_id: str, successful_runs: int):
    """
    Verify that a fix resolved the flakiness.
    
    Records the number of successful runs after the fix.
    """
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail="Fix not found")
    
    fix = fixes_db[fix_id]
    fix.verified_runs = successful_runs
    
    # If enough successful runs, mark as verified
    if successful_runs >= 10:
        fix.status = FixStatus.VERIFIED
    
    return {
        "message": "Fix verification recorded",
        "fix_id": fix_id,
        "successful_runs": successful_runs,
        "status": fix.status
    }


@router.post("/fixes/{fix_id}/reject")
async def reject_fix(fix_id: str, reason: str):
    """Reject a fix suggestion."""
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail="Fix not found")
    
    fix = fixes_db[fix_id]
    fix.status = FixStatus.REJECTED
    
    return {
        "message": "Fix rejected",
        "fix_id": fix_id,
        "reason": reason
    }
