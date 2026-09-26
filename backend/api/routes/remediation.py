"""Remediation API routes."""
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid

from backend.models.remediation import Fix, FixSuggestion, FixStatus
from backend.models.classification import Classification, RootCauseType, Evidence, Confidence
from backend.remediation.generator import FixGenerator
from backend.remediation.validator import FixValidator, ValidationResult
from backend.remediation.evidence_validator import EvidenceValidator
from backend.remediation.strategy import StrategySelector
from backend.bob.agent import BobAgent

router = APIRouter()

# In-memory storage
fixes_db: dict = {}
# Store patched sources keyed by (fix_id, suggestion_id) for validation
_patched_sources: dict = {}

_bob_agent = BobAgent()


# ── F2 input schema ───────────────────────────────────────────────────────────

class F2ClassificationInput(BaseModel):
    """
    The JSON shape produced by F2 (root-cause classifier).

    Example::

        {
            "test_name": "test_payment_timeout",
            "root_cause": "timing_race",
            "confidence": 0.91,
            "evidence": [
                "Background thread started",
                "Assertion occurs before thread completion"
            ],
            "file_path": "tests/test_payment.py"
        }
    """

    test_name: str
    root_cause: str = Field(
        ...,
        description=(
            "Root cause string from F2. "
            "One of: timing_race, timing, race_condition, order_dependency, ordering, "
            "data_leakage, state_leakage, environment_network, environment, network."
        ),
    )
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    file_path: str = Field(
        "",
        description="Path to the test file. Used to read source and produce real diffs.",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

# Map F2 root_cause strings → RootCauseType
_ROOT_CAUSE_MAP = {
    "timing_race": RootCauseType.TIMING,
    "timing": RootCauseType.TIMING,
    "race_condition": RootCauseType.RACE_CONDITION,
    "order_dependency": RootCauseType.ORDERING,
    "ordering": RootCauseType.ORDERING,
    "data_leakage": RootCauseType.STATE_LEAKAGE,
    "state_leakage": RootCauseType.STATE_LEAKAGE,
    "environment_network": RootCauseType.ENVIRONMENT,
    "environment": RootCauseType.ENVIRONMENT,
    "network": RootCauseType.NETWORK,
}

_CONFIDENCE_MAP = {
    range(0, 60): Confidence.LOW,
    range(60, 80): Confidence.MEDIUM,
    range(80, 101): Confidence.HIGH,
}


def _map_confidence(score: float) -> Confidence:
    pct = int(score * 100)
    if pct >= 80:
        return Confidence.HIGH
    if pct >= 60:
        return Confidence.MEDIUM
    return Confidence.LOW


def _f2_to_classification(inp: F2ClassificationInput) -> Classification:
    """Convert an F2ClassificationInput into a Classification model."""
    root_cause = _ROOT_CAUSE_MAP.get(inp.root_cause.lower(), RootCauseType.UNKNOWN)
    evidence = [
        Evidence(type="f2_evidence", description=e, source="f2_classifier")
        for e in inp.evidence
    ]
    return Classification(
        classification_id=str(uuid.uuid4()),
        test_name=inp.test_name,
        file_path=inp.file_path or f"tests/{inp.test_name}.py",
        root_cause=root_cause,
        confidence=_map_confidence(inp.confidence),
        evidence=evidence,
        reasoning=f"F2 classified root cause as '{inp.root_cause}' with confidence {inp.confidence:.2f}",
        suggested_fix_area=inp.file_path or inp.test_name,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=Fix)
async def generate_fix(classification: Classification):
    """
    Generate fix suggestions for a classified flaky test.

    Accepts a full Classification object (F2 internal model).
    Returns multiple fix suggestions with confidence scores and unified diffs.
    """
    generator = FixGenerator()

    # Extract real source code using Bob's AST extractor
    test_source = _bob_agent.extract_test_source(
        classification.file_path, classification.test_name
    )

    fix = await generator.generate_fix(classification, test_source=test_source)
    fixes_db[fix.fix_id] = fix
    _store_patched_sources(fix)

    return fix


@router.post("/generate-from-f2", response_model=Fix)
async def generate_fix_from_f2(f2_input: F2ClassificationInput):
    """
    Generate fix suggestions directly from F2 classifier output.

    Accepts the lightweight JSON produced by F2::

        {
          "test_name": "test_payment_timeout",
          "root_cause": "timing_race",
          "confidence": 0.91,
          "evidence": ["Background thread started", "Assertion occurs before thread completion"],
          "file_path": "tests/test_payment.py"
        }

    Returns a Fix with reviewable unified diffs — the fix is *proposed*, not
    automatically applied (``requires_review: true`` on every suggestion).
    """
    classification = _f2_to_classification(f2_input)
    generator = FixGenerator()

    test_source = _bob_agent.extract_test_source(
        classification.file_path, classification.test_name
    )

    fix = await generator.generate_fix(classification, test_source=test_source)
    fixes_db[fix.fix_id] = fix
    _store_patched_sources(fix)

    return fix


@router.get("/fixes", response_model=List[Fix])
async def list_fixes(status: Optional[FixStatus] = None):
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
    The fix is *not* written to disk here — a human must review the diff first.
    """
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail="Fix not found")

    fix = fixes_db[fix_id]
    suggestion = next(
        (s for s in fix.suggestions if s.suggestion_id == suggestion_id), None
    )
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    fix.status = FixStatus.APPLIED
    fix.applied_by = "api_user"

    return {
        "message": "Fix applied",
        "fix_id": fix_id,
        "suggestion_id": suggestion_id,
        "fix_type": suggestion.fix_type,
        "requires_review": suggestion.requires_review,
    }


@router.post("/fixes/{fix_id}/validate", response_model=ValidationResult)
async def validate_fix(fix_id: str, suggestion_id: str, runs: int = 5, repo_path: str = "."):
    """
    Validate that a proposed fix actually eliminates flakiness.

    Workflow:
    1. Retrieve the fix and the requested suggestion.
    2. Require full patched source; unified diff text is never executable source.
    3. Check Python syntax, then run the test in a disposable repository copy.
    4. Leave the original repository untouched.
    5. Return a ValidationResult with ``fix_valid`` and ``flakiness_rate``.

    The fix is only promoted to VERIFIED status if ``fix_valid`` is true.
    """
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail="Fix not found")

    fix = fixes_db[fix_id]
    suggestion = next(
        (s for s in fix.suggestions if s.suggestion_id == suggestion_id), None
    )
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if suggestion.diff is None or not suggestion.diff.unified_diff:
        raise HTTPException(
            status_code=422,
            detail="This suggestion has no diff to validate.",
        )

    patched_source = suggestion.diff.new_content
    if not isinstance(patched_source, str):
        raise HTTPException(
            status_code=422,
            detail="Patched source not available for this suggestion. Re-generate the fix.",
        )

    validator = FixValidator(repo_path=repo_path)
    result = await validator.validate(
        fix_id=fix_id,
        file_path=fix.file_path,
        patched_source=patched_source,
        test_name=fix.test_name,
        runs=runs,
    )

    # Promote or reject the fix based on validation outcome
    if result.fix_valid:
        fix.status = FixStatus.VERIFIED
        fix.verified_runs = result.passes
    else:
        fix.status = FixStatus.FAILED

    return result


@router.post("/fixes/{fix_id}/verify")
async def verify_fix(fix_id: str, successful_runs: int):
    """
    Manually record successful runs after a fix has been applied.

    Promotes the fix to VERIFIED status when successful_runs >= 10.
    """
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail="Fix not found")

    fix = fixes_db[fix_id]
    fix.verified_runs = successful_runs

    if successful_runs >= 10:
        fix.status = FixStatus.VERIFIED

    return {
        "message": "Fix verification recorded",
        "fix_id": fix_id,
        "successful_runs": successful_runs,
        "status": fix.status,
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
        "reason": reason,
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _store_patched_sources(fix: Fix) -> None:
    """Cache full source only; a display patch cannot reconstruct a file.

    Missing source clears stale entries. Empty full source remains distinct
    from missing source, and is left for the validator's target checks.
    """
    for suggestion in fix.suggestions:
        key = f"{fix.fix_id}:{suggestion.suggestion_id}"
        patched = suggestion.diff.new_content if suggestion.diff is not None else None
        if isinstance(patched, str):
            _patched_sources[key] = patched
        else:
            _patched_sources.pop(key, None)


# ── F3 Evidence & Strategy Endpoints ─────────────────────────────────────────

class EvidenceValidationRequest(BaseModel):
    """F2 diagnosis object submitted for evidence validation."""
    test_name: str
    root_cause: str
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "List of evidence dicts: {file: str, line: int, reason: str}. "
            "These are the structured evidence items produced by F2."
        ),
    )


class StrategyRequest(BaseModel):
    """Request to select a remediation strategy."""
    root_cause: str
    evidence: Optional[List[Dict[str, Any]]] = None


@router.post("/validate-evidence")
async def validate_evidence(request: EvidenceValidationRequest):
    """
    **F3** — Validate F2 diagnosis evidence.

    Checks that every evidence item points to a real file and valid line number
    so that the fix generator can proceed with confidence.

    Returns a validation result with:
    - ``valid``: whether all evidence is usable
    - ``locations``: resolved file:line strings
    - ``details``: per-item validation breakdown
    """
    validator = EvidenceValidator()
    result = validator.validate(request.model_dump())
    return result


@router.post("/select-strategy")
async def select_strategy(request: StrategyRequest):
    """
    **F3** — Select remediation strategies for a root cause.

    Maps the F2 root cause to ordered remediation strategies.
    Optionally refines the selection using the provided evidence.

    Returns:
    - ``strategies``: ordered strategy names
    - ``descriptions``: human-readable descriptions of each strategy
    """
    strategies = StrategySelector.select_strategies(request.root_cause, request.evidence)
    return {
        "root_cause": request.root_cause,
        "strategies": [s.value for s in strategies],
        "descriptions": [StrategySelector.get_strategy_description(s) for s in strategies],
    }
