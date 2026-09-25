"""F4 smoke tests — run via: python scripts/test_f4.py"""
import pathlib, sys, types
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Build a comprehensive stub for backend.models.audit ──────────────────────
# (must happen BEFORE any backend.auditor import triggers the import chain)

class QuarantineStatus(str, Enum):
    ACTIVE = "active"; UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"; REMOVED = "removed"

class QuarantineTestStatus(str, Enum):
    DIAGNOSED_STILL_QUARANTINED = "diagnosed_but_still_quarantined"
    UNEXPLAINED = "unexplained"
    READY_TO_UNQUARANTINE = "ready_to_unquarantine"
    STALE = "stale"

class AuditAction(str, Enum):
    TEST_DETECTED = "test_detected"; TEST_CLASSIFIED = "test_classified"
    FIX_PROPOSED = "fix_proposed"; FIX_APPLIED = "fix_applied"
    FIX_VERIFIED = "fix_verified"; FIX_REJECTED = "fix_rejected"
    QUARANTINE_ADDED = "quarantine_added"; QUARANTINE_REMOVED = "quarantine_removed"
    QUARANTINE_REVIEW = "quarantine_review"

@dataclass
class QuarantineEntry:
    quarantine_id: str; test_name: str; file_path: str; reason: str
    quarantined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    quarantined_by: Optional[str] = None
    status: QuarantineStatus = QuarantineStatus.ACTIVE
    runs_since_quarantine: int = 0; runs_until_review: int = 10
    last_review_at: Optional[datetime] = None; last_review_result: Optional[str] = None
    resolution_date: Optional[datetime] = None; resolution_notes: Optional[str] = None
    root_cause: Optional[str] = None; metadata: Dict = field(default_factory=dict)

@dataclass
class AuditedTest:
    test_name: str; diagnosed: bool; fixable: bool; status: QuarantineTestStatus
    root_cause: Optional[str] = None; confidence: Optional[str] = None
    fix_strategy: Optional[str] = None; quarantine_reason: Optional[str] = None
    quarantined_at: Optional[datetime] = None; source: str = "quarantine_file"

@dataclass
class QuarantineAuditReport:
    report_id: str; quarantined_tests: List[AuditedTest]
    total_quarantined: int; diagnosed_count: int; fixable_count: int; unexplained_count: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    quarantine_file: Optional[str] = None; ci_config_files: List[str] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)

@dataclass
class AuditLog:
    log_id: str; action: AuditAction; entity_type: str; entity_id: str
    actor: Optional[str] = None; details: Dict = field(default_factory=dict)
    previous_state: Optional[Dict] = None; new_state: Optional[Dict] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    def model_dump(self): return self.__dict__

@dataclass
class QuarantineReport:
    report_id: str; total_quarantined: int; active_count: int
    under_review_count: int; resolved_count: int; average_quarantine_duration: float
    oldest_quarantine_days: int; upcoming_reviews: List = field(default_factory=list)
    summary: Dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

fake_audit = types.ModuleType("backend.models.audit")
for name in [
    "QuarantineStatus", "QuarantineTestStatus", "AuditAction",
    "QuarantineEntry", "AuditedTest", "QuarantineAuditReport",
    "AuditLog", "QuarantineReport",
]:
    setattr(fake_audit, name, eval(name))
sys.modules["backend.models.audit"] = fake_audit

# Stub backend.models.classification (for auditor.py imports)
class RootCauseType(str, Enum):
    TIMING = "timing"; ORDERING = "ordering"; STATE_LEAKAGE = "state_leakage"
    ENVIRONMENT = "environment"; NETWORK = "network"; RESOURCE = "resource"
    RACE_CONDITION = "race_condition"; FLOATING_POINT = "floating_point"; UNKNOWN = "unknown"

class Confidence(str, Enum):
    HIGH = "high"; MEDIUM = "medium"; LOW = "low"

@dataclass
class Classification:
    classification_id: str; test_name: str; file_path: str
    root_cause: RootCauseType; confidence: Confidence
    reasoning: str = ""; suggested_fix_area: str = ""
    evidence: List = field(default_factory=list)
    related_tests: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

fake_cls = types.ModuleType("backend.models.classification")
fake_cls.RootCauseType = RootCauseType
fake_cls.Confidence = Confidence
fake_cls.Classification = Classification
sys.modules["backend.models.classification"] = fake_cls

# Stub backend.config
fake_cfg = types.ModuleType("backend.config")
class _S: pass
fake_cfg.settings = _S()
sys.modules["backend.config"] = fake_cfg

# ── Now it's safe to import the auditor modules ────────────────────────────────
from backend.auditor.quarantine_parser import QuarantineParser
from backend.auditor.ci_parser import CIParser
from backend.auditor.auditor import _name_variants, _lookup, Auditor

# ── 1. QuarantineParser ───────────────────────────────────────────────────────
qp = QuarantineParser()
parsed = qp.parse("sample-repo/QUARANTINE.md")
print(f"OK  QuarantineParser: {len(parsed)} entries parsed")
for e in parsed:
    print(f"      {e.test_name!r}  resolved={e.resolved}  reason={e.reason!r}")

active_names = [e.test_name for e in parsed if not e.resolved]
assert "test_timing_dependent" in active_names, f"Missing test_timing_dependent in {active_names}"
assert "test_shared_state" in active_names, f"Missing test_shared_state in {active_names}"
assert "------" not in active_names, "Separator row leaked into results"
resolved_names = [e.test_name for e in parsed if e.resolved]
assert "test_async_order" in resolved_names, f"Missing test_async_order in {resolved_names}"
print("OK  Active/resolved split correct, no separator leak")

# ── 2. CIParser ───────────────────────────────────────────────────────────────
cp = CIParser()

pytest_cfg = cp.parse_pytest_ini("sample-repo/pytest.ini")
print(f"OK  CIParser.parse_pytest_ini: testpaths={pytest_cfg.testpaths} addopts={pytest_cfg.addopts!r}")
assert pytest_cfg.testpaths == ["tests"], pytest_cfg.testpaths
assert "-v" in pytest_cfg.addopts

workflow_cfg = cp.parse_workflow_yaml("sample-repo/.github/workflows/ci.yml")
print(f"OK  CIParser.parse_workflow_yaml: platform={workflow_cfg.platform} ci_flag={workflow_cfg.ci_flag}")
assert workflow_cfg.platform == "github_actions", workflow_cfg.platform
assert workflow_cfg.ci_flag is True
assert any("pytest" in c for c in workflow_cfg.pytest_commands), workflow_cfg.pytest_commands

# ── 3. _name_variants + _lookup ──────────────────────────────────────────────
idx: Dict[str, Classification] = {}
c1 = Classification(
    classification_id="c1",
    test_name="tests/test_timing.py::TestTimingIssues::test_timing_dependent",
    file_path="sample-repo/tests/test_timing.py",
    root_cause=RootCauseType.TIMING,
    confidence=Confidence.HIGH,
)
for v in _name_variants(c1.test_name):
    idx[v] = c1

assert _lookup("test_timing_dependent", idx) is c1, "Short name lookup failed"
assert _lookup("test_old_api", idx) is None, "Unknown test should return None"
print("OK  _name_variants / _lookup: fuzzy matching works")

# ── 4. Full audit_quarantine via Auditor ─────────────────────────────────────
# Stub the Auditor's file I/O so it doesn't touch disk
import json, tempfile, os
tmp_dir = tempfile.mkdtemp()
aud = Auditor(data_dir=tmp_dir)

c2 = Classification(
    classification_id="c2",
    test_name="test_shared_state",
    file_path="sample-repo/tests/test_leakage.py",
    root_cause=RootCauseType.STATE_LEAKAGE,
    confidence=Confidence.MEDIUM,
)

report = aud.audit_quarantine(
    quarantine_path="sample-repo/QUARANTINE.md",
    classifications=[c1, c2],
    repo_path="sample-repo",
)

print(f"OK  audit_quarantine: {report.total_quarantined} total, "
      f"{report.diagnosed_count} diagnosed, {report.fixable_count} fixable, "
      f"{report.unexplained_count} unexplained")

for t in report.quarantined_tests:
    print(f"      {t.test_name!r}  diagnosed={t.diagnosed}  fixable={t.fixable}  status={t.status.value}")

# test_timing_dependent → timing → diagnosed + fixable
timing_entry = next(t for t in report.quarantined_tests if t.test_name == "test_timing_dependent")
assert timing_entry.diagnosed is True
assert timing_entry.fixable is True
assert timing_entry.status == QuarantineTestStatus.DIAGNOSED_STILL_QUARANTINED
assert timing_entry.fix_strategy == "replace_sleep_with_deterministic_wait"
print("OK  test_timing_dependent: diagnosed=True, fixable=True, correct strategy")

# test_shared_state → state_leakage → diagnosed + fixable
state_entry = next(t for t in report.quarantined_tests if t.test_name == "test_shared_state")
assert state_entry.diagnosed is True
assert state_entry.fixable is True
assert state_entry.fix_strategy == "add_cleanup_or_fixture_isolation"
print("OK  test_shared_state: diagnosed=True, fixable=True, correct strategy")

# ── 5. CI config is listed in the report ─────────────────────────────────────
assert any("pytest.ini" in f for f in report.ci_config_files), report.ci_config_files
assert any("ci.yml" in f for f in report.ci_config_files), report.ci_config_files
print(f"OK  ci_config_files: {report.ci_config_files}")

print()
print("All F4 smoke tests passed.")
