"""Audit API routes."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid

from backend.models.audit import (
    AuditLog, AuditAction, QuarantineEntry, QuarantineStatus, QuarantineReport
)
from backend.auditor.auditor import Auditor
from backend.auditor.quarantine_parser import QuarantineParser

router = APIRouter()

auditor = Auditor()


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
