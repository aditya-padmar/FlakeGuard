"""Main auditor module for tracking and logging."""
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import uuid

from backend.models.audit import AuditLog, AuditAction, QuarantineEntry, QuarantineStatus, QuarantineReport
from backend.config import settings


class Auditor:
    """
    Tracks all actions in FlakeGuard and manages quarantine.
    
    Responsible for:
    - Recording audit logs
    - Managing quarantine entries
    - Generating reports
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.audit_file = self.data_dir / "audit_logs.json"
        self.quarantine_file = self.data_dir / "quarantine.json"
        self._ensure_data_files()
    
    def _ensure_data_files(self):
        """Ensure data files exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.audit_file.exists():
            self._write_json(self.audit_file, [])
        
        if not self.quarantine_file.exists():
            self._write_json(self.quarantine_file, [])
    
    def _read_json(self, path: Path) -> List[dict]:
        """Read JSON file."""
        if not path.exists():
            return []
        with open(path, 'r') as f:
            return json.load(f)
    
    def _write_json(self, path: Path, data: List[dict]):
        """Write JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def log_action(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        actor: Optional[str] = None,
        details: Optional[dict] = None,
        previous_state: Optional[dict] = None,
        new_state: Optional[dict] = None
    ) -> AuditLog:
        """
        Log an audit action.
        
        Args:
            action: Type of action
            entity_type: Type of entity (test, fix, quarantine)
            entity_id: ID of the entity
            actor: Who performed the action
            details: Additional details
            previous_state: State before action
            new_state: State after action
            
        Returns:
            Created AuditLog
        """
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            details=details or {},
            previous_state=previous_state,
            new_state=new_state
        )
        
        logs = self._read_json(self.audit_file)
        logs.append(log.model_dump())
        self._write_json(self.audit_file, logs)
        
        return log
    
    def add_to_quarantine(
        self,
        test_name: str,
        file_path: str,
        reason: str,
        root_cause: Optional[str] = None,
        quarantined_by: Optional[str] = None
    ) -> QuarantineEntry:
        """
        Add a test to quarantine.
        
        Args:
            test_name: Name of the test
            file_path: Path to test file
            reason: Reason for quarantine
            root_cause: Optional root cause
            quarantined_by: Who initiated quarantine
            
        Returns:
            Created QuarantineEntry
        """
        entry = QuarantineEntry(
            quarantine_id=str(uuid.uuid4()),
            test_name=test_name,
            file_path=file_path,
            reason=reason,
            root_cause=root_cause,
            quarantined_by=quarantined_by
        )
        
        quarantine = self._read_json(self.quarantine_file)
        quarantine.append(entry.model_dump())
        self._write_json(self.quarantine_file, quarantine)
        
        # Log action
        self.log_action(
            action=AuditAction.QUARANTINE_ADDED,
            entity_type="test",
            entity_id=entry.quarantine_id,
            actor=quarantined_by,
            details={"test_name": test_name, "reason": reason}
        )
        
        return entry
    
    def get_quarantine(self, status: Optional[QuarantineStatus] = None) -> List[QuarantineEntry]:
        """
        Get quarantine entries.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            List of QuarantineEntry objects
        """
        quarantine = self._read_json(self.quarantine_file)
        entries = [QuarantineEntry(**entry) for entry in quarantine]
        
        if status:
            entries = [e for e in entries if e.status == status]
        
        return entries
    
    def update_quarantine(
        self,
        quarantine_id: str,
        status: QuarantineStatus,
        notes: Optional[str] = None
    ) -> Optional[QuarantineEntry]:
        """
        Update quarantine entry status.
        
        Args:
            quarantine_id: ID of quarantine entry
            status: New status
            notes: Optional resolution notes
            
        Returns:
            Updated QuarantineEntry or None
        """
        quarantine = self._read_json(self.quarantine_file)
        
        for i, entry in enumerate(quarantine):
            if entry["quarantine_id"] == quarantine_id:
                previous_state = entry.copy()
                
                entry["status"] = status.value
                if status == QuarantineStatus.RESOLVED:
                    entry["resolution_date"] = datetime.utcnow().isoformat()
                    entry["resolution_notes"] = notes
                if notes:
                    entry["last_review_result"] = notes
                    entry["last_review_at"] = datetime.utcnow().isoformat()
                
                quarantine[i] = entry
                self._write_json(self.quarantine_file, quarantine)
                
                # Log action
                self.log_action(
                    action=AuditAction.QUARANTINE_REVIEW,
                    entity_type="quarantine",
                    entity_id=quarantine_id,
                    previous_state=previous_state,
                    new_state=entry
                )
                
                return QuarantineEntry(**entry)
        
        return None
    
    def generate_report(self) -> QuarantineReport:
        """
        Generate a quarantine status report.
        
        Returns:
            QuarantineReport with current statistics
        """
        entries = self.get_quarantine()
        
        active = [e for e in entries if e.status == QuarantineStatus.ACTIVE]
        under_review = [e for e in entries if e.status == QuarantineStatus.UNDER_REVIEW]
        resolved = [e for e in entries if e.status == QuarantineStatus.RESOLVED]
        
        # Calculate average duration
        durations = []
        now = datetime.utcnow()
        for entry in active:
            delta = now - entry.quarantined_at
            durations.append(delta.days)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Find upcoming reviews
        upcoming = [
            e for e in active
            if (e.runs_since_quarantine or 0) >= (e.runs_until_review or 10) - 2
        ]
        
        return QuarantineReport(
            report_id=str(uuid.uuid4()),
            total_quarantined=len(entries),
            active_count=len(active),
            under_review_count=len(under_review),
            resolved_count=len(resolved),
            average_quarantine_duration=avg_duration,
            oldest_quarantine_days=max(durations) if durations else 0,
            upcoming_reviews=upcoming[:5],
            summary={
                "total_tests_quarantined": len(entries),
                "resolution_rate": len(resolved) / len(entries) if entries else 0
            }
        )
