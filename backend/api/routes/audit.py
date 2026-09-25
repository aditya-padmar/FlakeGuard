"""Audit API routes."""
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid

from backend.models.audit import (
    AuditLog,
    AuditAction,
    QuarantineEntry,
    QuarantineStatus,
    QuarantineReport,
    QuarantineAuditReport,
)
from backend.models.classification import Classification
from backend.auditor.auditor import Auditor
from backend.auditor.quarantine_parser import QuarantineParser
from backend.auditor.ci_parser import CIParser
from backend.auditor.skip_detector import SkipDetector
from backend.auditor.retry_detector import RetryDetector

router = APIRouter()

auditor = Auditor()


# ── F2 × F4 cross-reference request schema ────────────────────────────────────

class QuarantineAuditRequest(BaseModel):
    """
    Request body for POST /audit/quarantine-audit.

    Combines the quarantine file path with a list of F2 classifications
    so the auditor can produce a full cross-reference report.
    """
    quarantine_path: str = Field(
        "sample-repo/QUARANTINE.md",
        description="Path to QUARANTINE.md or plain skip-list file.",
    )
    classifications: List[Classification] = Field(
        default_factory=list,
        description="F2 Classification objects to match against the quarantine list.",
    )
    repo_path: Optional[str] = Field(
        None,
        description="Repository root path, used to discover CI config files.",
    )


@router.get("/logs", response_model=List[AuditLog])
async def list_audit_logs(
    action: Optional[AuditAction] = None,
    entity_type: Optional[str] = None,
    limit: int = 100
):
    """
    List audit logs.
    
    Optionally filter by action type or entity type.
    """
    logs = auditor._read_json(auditor.audit_file)
    logs = [AuditLog(**log) for log in logs]
    
    if action:
        logs = [l for l in logs if l.action == action]
    
    if entity_type:
        logs = [l for l in logs if l.entity_type == entity_type]
    
    return logs[:limit]


# Quarantine endpoints

@router.get("/quarantine", response_model=List[QuarantineEntry])
async def list_quarantine(status: Optional[QuarantineStatus] = None):
    """
    List quarantined tests.
    
    Optionally filter by status.
    """
    return auditor.get_quarantine(status)


@router.post("/quarantine", response_model=QuarantineEntry)
async def add_to_quarantine(
    test_name: str,
    file_path: str,
    reason: str,
    root_cause: Optional[str] = None
):
    """
    Add a test to quarantine.
    
    The test will be tracked and reviewed periodically.
    """
    return auditor.add_to_quarantine(
        test_name=test_name,
        file_path=file_path,
        reason=reason,
        root_cause=root_cause
    )


@router.get("/quarantine/{quarantine_id}", response_model=QuarantineEntry)
async def get_quarantine_entry(quarantine_id: str):
    """Get a specific quarantine entry."""
    entries = auditor.get_quarantine()
    entry = next((e for e in entries if e.quarantine_id == quarantine_id), None)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Quarantine entry not found")
    
    return entry


@router.put("/quarantine/{quarantine_id}/status")
async def update_quarantine_status(
    quarantine_id: str,
    status: QuarantineStatus,
    notes: Optional[str] = None
):
    """
    Update quarantine entry status.
    
    Used to mark tests as resolved, under review, etc.
    """
    entry = auditor.update_quarantine(quarantine_id, status, notes)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Quarantine entry not found")
    
    return {
        "message": "Status updated",
        "quarantine_id": quarantine_id,
        "new_status": status
    }


@router.get("/quarantine/report", response_model=QuarantineReport)
async def get_quarantine_report():
    """
    Get a comprehensive quarantine report.
    
    Includes statistics and upcoming reviews.
    """
    return auditor.generate_report()


@router.post("/quarantine/import")
async def import_quarantine_file(file_path: str):
    """
    Import quarantine from a markdown file.
    
    Parses QUARANTINE.md style files.
    """
    parser = QuarantineParser()
    
    try:
        entries = parser.parse_markdown(file_path)
        
        # Add to auditor
        for entry in entries:
            auditor.add_to_quarantine(
                test_name=entry.test_name,
                file_path=entry.file_path,
                reason=entry.reason,
                root_cause=entry.root_cause
            )
        
        return {
            "message": "Quarantine imported",
            "entries_imported": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── F4: quarantine × F2 cross-reference ──────────────────────────────────────

@router.post("/quarantine-audit", response_model=QuarantineAuditReport)
async def quarantine_audit(request: QuarantineAuditRequest):
    """
    **F4 core endpoint** — cross-reference a quarantine file with F2 diagnoses.

    Reads the quarantine file at *quarantine_path*, matches every entry against
    the provided *classifications* (F2 output), and returns a
    QuarantineAuditReport that shows:

    - Which quarantined tests have been diagnosed (``diagnosed: true``)
    - Which have a fixable root cause (``fixable: true``)
    - Which remain unexplained (``status: unexplained``)

    Example request body::

        {
          "quarantine_path": "sample-repo/QUARANTINE.md",
          "classifications": [
            {
              "classification_id": "...",
              "test_name": "test_timing_dependent",
              "file_path": "sample-repo/tests/test_timing.py",
              "root_cause": "timing",
              "confidence": "high",
              "reasoning": "...",
              "suggested_fix_area": "..."
            }
          ],
          "repo_path": "sample-repo"
        }
    """
    try:
        report = auditor.audit_quarantine(
            quarantine_path=request.quarantine_path,
            classifications=request.classifications,
            repo_path=request.repo_path,
        )
        return report
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/quarantine-audit/sample", response_model=QuarantineAuditReport)
async def quarantine_audit_sample(
    quarantine_path: str = "sample-repo/QUARANTINE.md",
    repo_path: str = "sample-repo",
):
    """
    Run F4 audit against the sample repository with zero F2 input.

    Useful for verifying the pipeline end-to-end when F2 has not yet
    been run — all quarantined tests will appear as ``unexplained``.
    """
    report = auditor.audit_quarantine(
        quarantine_path=quarantine_path,
        classifications=[],
        repo_path=repo_path,
    )
    return report


@router.get("/ci-config")
async def get_ci_config(repo_path: str = "sample-repo"):
    """
    Parse and return CI configuration signals from *repo_path*.

    Reads pytest.ini and any .github/workflows/*.yml files and extracts
    markers, addopts flags, skip signals, and environment variables.
    """
    parser = CIParser()
    pytest_cfg, workflow_cfg = parser.parse_all(repo_path)
    return {
        "pytest_ini": {
            "markers": pytest_cfg.markers,
            "addopts": pytest_cfg.addopts,
            "testpaths": pytest_cfg.testpaths,
            "skip_markers": pytest_cfg.skip_markers,
            "deselected": pytest_cfg.deselected,
            "k_expression": pytest_cfg.k_expression,
            "m_expression": pytest_cfg.m_expression,
            "extra": pytest_cfg.extra,
        },
        "workflow": {
            "platform": workflow_cfg.platform,
            "python_versions": workflow_cfg.python_versions,
            "pytest_commands": workflow_cfg.pytest_commands,
            "ci_flag": workflow_cfg.ci_flag,
            "skip_signals": workflow_cfg.skip_signals,
            "env_vars": workflow_cfg.env_vars,
        },
    }


# ── F4: Skip / Retry / Comprehensive Detection ────────────────────────────────

@router.get("/skip-detections")
async def detect_skips(repo_path: str = "sample-repo"):
    """
    **F4** — Detect skip and xfail markers in test files.

    Scans every ``test_*.py`` file under ``<repo_path>/tests/`` and returns
    every ``@pytest.mark.skip``, ``@pytest.mark.xfail``, and ``pytest.skip()``
    it finds, together with a summary.
    """
    detector = SkipDetector(repo_root=repo_path)
    detections = detector.detect_in_directory("tests")
    summary = detector.summarize(detections)
    return {
        "repo_path": repo_path,
        "detections": detections,
        "summary": summary,
    }


@router.get("/retry-detections")
async def detect_retries(repo_path: str = "sample-repo"):
    """
    **F4** — Detect CI retry configuration.

    Checks GitHub Actions workflow files and pytest config for retry
    mechanisms (nick-invision/retry, wretry, --reruns, etc.).
    """
    detector = RetryDetector(repo_root=repo_path)
    result = detector.detect_all()
    return result


@router.post("/run")
async def run_audit(
    quarantine_path: str = "sample-repo/QUARANTINE.md",
    repo_path: str = "sample-repo",
    classifications: List[Classification] = None,
    remediations: Optional[List[Dict[str, Any]]] = None,
):
    """
    **F4 core** — Run a full audit of the repository.

    Combines:
    1. Quarantine × F2 cross-reference (``audit_quarantine``)
    2. Skip/xfail detection
    3. CI retry detection

    ``classifications`` (optional) — F2 Classification objects to match.
    ``remediations``  (optional) — F3 remediation results for context (stored
    in the report summary but not used for logic in the MVP).

    Returns a QuarantineAuditReport enriched with skip/retry data.
    """
    try:
        report = auditor.audit_quarantine(
            quarantine_path=quarantine_path,
            classifications=classifications or [],
            repo_path=repo_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Enrich summary with skip/retry data
    skip_detector = SkipDetector(repo_root=repo_path)
    skip_detections = skip_detector.detect_in_directory("tests")
    skip_summary = skip_detector.summarize(skip_detections)

    retry_detector = RetryDetector(repo_root=repo_path)
    retry_result = retry_detector.detect_all()

    report.summary["skip_detections"] = skip_summary
    report.summary["retry_configuration"] = retry_result.get("summary", {})
    if remediations:
        report.summary["remediations_provided"] = len(remediations)

    return report


@router.get("/report")
async def get_audit_report(
    quarantine_path: str = "sample-repo/QUARANTINE.md",
    repo_path: str = "sample-repo",
):
    """
    **F4** — Get a comprehensive audit report for the sample repository.

    Combines the live quarantine list with skip/retry detection.
    No F2 classifications are required — all tests appear as *unexplained*
    unless the quarantine file has been cross-referenced separately.

    Use ``POST /api/audit/run`` when you have F2 classifications to provide.
    """
    try:
        report = auditor.audit_quarantine(
            quarantine_path=quarantine_path,
            classifications=[],
            repo_path=repo_path,
        )
    except FileNotFoundError:
        report = None

    quarantine_report = auditor.generate_report()

    skip_detector = SkipDetector(repo_root=repo_path)
    skip_detections = skip_detector.detect_in_directory("tests")
    skip_summary = skip_detector.summarize(skip_detections)

    retry_detector = RetryDetector(repo_root=repo_path)
    retry_result = retry_detector.detect_all()

    return {
        "quarantine_audit": report.model_dump() if report else None,
        "quarantine_report": quarantine_report.model_dump(),
        "skip_detections": {
            "detections": skip_detections,
            "summary": skip_summary,
        },
        "retry_configuration": retry_result,
    }
