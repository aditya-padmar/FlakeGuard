"""
Main auditor module.

Responsibilities
----------------
1. Record audit logs for every FlakeGuard action (detect, classify, fix, …).
2. Manage the live quarantine list (add / update / remove entries).
3. Generate QuarantineReports from the live list.
4. **audit_quarantine()** — F4's key function:
   cross-reference a QUARANTINE.md (or any quarantine file) against
   F2 Classification objects and produce a QuarantineAuditReport.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.models.audit import (
    AuditAction,
    AuditedTest,
    AuditLog,
    QuarantineAuditReport,
    QuarantineEntry,
    QuarantineReport,
    QuarantineStatus,
    QuarantineTestStatus,
)
from backend.models.classification import Classification, Confidence, RootCauseType
from backend.config import settings
from backend.auditor.quarantine_parser import QuarantineParser
from backend.auditor.ci_parser import CIParser
from backend.remediation.templates import REMEDIATION_STRATEGIES


# Root causes that have a known remediation strategy in F3
_FIXABLE_CAUSES = {
    RootCauseType.TIMING,
    RootCauseType.RACE_CONDITION,
    RootCauseType.ORDERING,
    RootCauseType.STATE_LEAKAGE,
    RootCauseType.ENVIRONMENT,
    RootCauseType.NETWORK,
}


class Auditor:
    """
    Tracks all actions in FlakeGuard and manages quarantine.

    Responsible for:
    - Recording audit logs
    - Managing quarantine entries
    - Generating reports
    - Cross-referencing quarantine with F2 diagnoses (audit_quarantine)
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.audit_file = self.data_dir / "audit_logs.json"
        self.quarantine_file = self.data_dir / "quarantine.json"
        self._ensure_data_files()

    # ── F4 Core: quarantine × F2 cross-reference ──────────────────────────────

    def audit_quarantine(
        self,
        quarantine_path: str,
        classifications: List[Classification],
        repo_path: Optional[str] = None,
    ) -> QuarantineAuditReport:
        """
        Cross-reference a quarantine file with F2 classification results.

        For every test listed in the quarantine file:
        - If F2 has a classification → diagnosed=True
        - If the root cause has a known F3 strategy → fixable=True
        - Status is set to one of the QuarantineTestStatus values

        Also reads CI config from *repo_path* (if provided) for context.

        Args:
            quarantine_path:   Path to QUARANTINE.md or plain skip-list.
            classifications:   F2 Classification objects.
            repo_path:         Root of the sample repo (for CI config parsing).

        Returns:
            QuarantineAuditReport ready for the dashboard.
        """
        parser = QuarantineParser()
        parsed = parser.parse(quarantine_path)

        # Index F2 diagnoses by normalised test name
        diagnosis_index: Dict[str, Classification] = {}
        for c in classifications:
            for key in _name_variants(c.test_name):
                diagnosis_index[key] = c

        # Optional: also pull in CI config file names for the report
        ci_config_files: List[str] = []
        if repo_path:
            ci_parser = CIParser()
            root = Path(repo_path)
            for ini in ("pytest.ini", "setup.cfg"):
                if (root / ini).exists():
                    ci_config_files.append(str(root / ini))
            for yml in (root / ".github" / "workflows").glob("*.yml"):
                ci_config_files.append(str(yml))

        # Build the audited list
        audited: List[AuditedTest] = []
        for entry in parsed:
            classification = _lookup(entry.test_name, diagnosis_index)
            diagnosed = classification is not None
            fixable = diagnosed and classification.root_cause in _FIXABLE_CAUSES

            # Determine status
            if not diagnosed:
                status = QuarantineTestStatus.UNEXPLAINED
            elif fixable:
                status = QuarantineTestStatus.DIAGNOSED_STILL_QUARANTINED
            else:
                # Diagnosed but no actionable fix (e.g. FLOATING_POINT, RESOURCE)
                status = QuarantineTestStatus.DIAGNOSED_STILL_QUARANTINED

            fix_strategy: Optional[str] = None
            if fixable and classification is not None:
                fix_strategy = REMEDIATION_STRATEGIES.get(
                    classification.root_cause.value, None
                )

            audited.append(AuditedTest(
                test_name=entry.test_name,
                diagnosed=diagnosed,
                fixable=fixable,
                status=status,
                root_cause=classification.root_cause.value if classification else None,
                confidence=classification.confidence.value if classification else None,
                fix_strategy=fix_strategy,
                quarantine_reason=entry.reason,
                quarantined_at=entry.quarantined_at,
                source=entry.source,
            ))

        diagnosed_count = sum(1 for a in audited if a.diagnosed)
        fixable_count = sum(1 for a in audited if a.fixable)
        unexplained_count = sum(1 for a in audited if not a.diagnosed)

        return QuarantineAuditReport(
            report_id=str(uuid.uuid4()),
            quarantine_file=quarantine_path,
            ci_config_files=ci_config_files,
            quarantined_tests=audited,
            total_quarantined=len(audited),
            diagnosed_count=diagnosed_count,
            fixable_count=fixable_count,
            unexplained_count=unexplained_count,
            summary={
                "diagnosis_rate": diagnosed_count / len(audited) if audited else 0.0,
                "fixability_rate": fixable_count / len(audited) if audited else 0.0,
                "unexplained_tests": [a.test_name for a in audited if not a.diagnosed],
                "ready_to_fix": [a.test_name for a in audited if a.fixable],
            },
        )

    # ── Audit logging ─────────────────────────────────────────────────────────

    def log_action(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        actor: Optional[str] = None,
        details: Optional[dict] = None,
        previous_state: Optional[dict] = None,
        new_state: Optional[dict] = None,
    ) -> AuditLog:
        """Record an audit action to disk."""
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            details=details or {},
            previous_state=previous_state,
            new_state=new_state,
        )

        logs = self._read_json(self.audit_file)
        logs.append(log.model_dump())
        self._write_json(self.audit_file, logs)

        return log

    # ── Quarantine management ─────────────────────────────────────────────────

    def add_to_quarantine(
        self,
        test_name: str,
        file_path: str,
        reason: str,
        root_cause: Optional[str] = None,
        quarantined_by: Optional[str] = None,
    ) -> QuarantineEntry:
        """Add a test to the live quarantine list."""
        entry = QuarantineEntry(
            quarantine_id=str(uuid.uuid4()),
            test_name=test_name,
            file_path=file_path,
            reason=reason,
            root_cause=root_cause,
            quarantined_by=quarantined_by,
        )

        quarantine = self._read_json(self.quarantine_file)
        quarantine.append(entry.model_dump())
        self._write_json(self.quarantine_file, quarantine)

        self.log_action(
            action=AuditAction.QUARANTINE_ADDED,
            entity_type="test",
            entity_id=entry.quarantine_id,
            actor=quarantined_by,
            details={"test_name": test_name, "reason": reason},
        )

        return entry

    def get_quarantine(
        self, status: Optional[QuarantineStatus] = None
    ) -> List[QuarantineEntry]:
        """Return quarantine entries, optionally filtered by status."""
        quarantine = self._read_json(self.quarantine_file)
        entries = [QuarantineEntry(**e) for e in quarantine]
        if status:
            entries = [e for e in entries if e.status == status]
        return entries

    def update_quarantine(
        self,
        quarantine_id: str,
        status: QuarantineStatus,
        notes: Optional[str] = None,
    ) -> Optional[QuarantineEntry]:
        """Update a quarantine entry's status."""
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

                self.log_action(
                    action=AuditAction.QUARANTINE_REVIEW,
                    entity_type="quarantine",
                    entity_id=quarantine_id,
                    previous_state=previous_state,
                    new_state=entry,
                )

                return QuarantineEntry(**entry)

        return None

    def generate_report(self) -> QuarantineReport:
        """Generate a QuarantineReport from the live quarantine list."""
        entries = self.get_quarantine()

        active = [e for e in entries if e.status == QuarantineStatus.ACTIVE]
        under_review = [e for e in entries if e.status == QuarantineStatus.UNDER_REVIEW]
        resolved = [e for e in entries if e.status == QuarantineStatus.RESOLVED]

        durations = []
        now = datetime.utcnow()
        for e in active:
            delta = now - e.quarantined_at
            durations.append(delta.days)

        avg_duration = sum(durations) / len(durations) if durations else 0.0

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
                "resolution_rate": len(resolved) / len(entries) if entries else 0,
            },
        )

    # ── Storage helpers ───────────────────────────────────────────────────────

    def _ensure_data_files(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.audit_file.exists():
            self._write_json(self.audit_file, [])
        if not self.quarantine_file.exists():
            self._write_json(self.quarantine_file, [])

    def _read_json(self, path: Path) -> List[dict]:
        if not path.exists():
            return []
        with open(path, "r") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: List[dict]):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)


# ── Module-level helpers ──────────────────────────────────────────────────────

def _name_variants(test_name: str) -> List[str]:
    """
    Return multiple lookup keys for a test name so that partial matches work.

    e.g. "tests/test_timing.py::TestTimingIssues::test_sleep_based"
    produces ["tests/test_timing.py::TestTimingIssues::test_sleep_based",
              "TestTimingIssues::test_sleep_based",
              "test_sleep_based"]
    """
    parts = test_name.replace("\\", "/").split("::")
    variants = []
    for i in range(len(parts)):
        variants.append("::".join(parts[i:]))
    return variants


def _lookup(name: str, index: Dict[str, Classification]) -> Optional[Classification]:
    """
    Look up a quarantine entry name in the diagnosis index.
    Tries progressively shorter variants (full → class::method → method).
    """
    for variant in _name_variants(name):
        if variant in index:
            return index[variant]
    # Last-resort: case-insensitive prefix match on the final segment
    leaf = name.rsplit("::", 1)[-1].lower()
    for key, val in index.items():
        if key.lower().endswith(leaf):
            return val
    return None
