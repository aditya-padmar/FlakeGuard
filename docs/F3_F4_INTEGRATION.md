# F3 & F4 Integration Guide

## Overview

This document describes the F3 (Remediation Generator) and F4 (Quarantine/CI Auditor) modules and how to integrate them with the rest of FlakeGuard.

## Files Created/Modified

### F3 Remediation

**New Files:**
- `backend/remediation/evidence_validator.py` - Validates F2 diagnosis evidence
- `backend/remediation/strategy.py` - Maps root causes to remediation strategies
- `tests/test_f3_remediation.py` - Tests for F3

**Modified Files:**
- `backend/remediation/generator.py` - Enhanced with evidence validation
- `backend/remediation/validator.py` - Fix validation against test runs
- `backend/remediation/templates.py` - Deterministic remediation templates

### F4 Audit

**New Files:**
- `backend/auditor/skip_detector.py` - Detects skip/xfail markers
- `backend/auditor/retry_detector.py` - Detects CI retry configuration
- `tests/test_f4_audit.py` - Tests for F4

**Modified Files:**
- `backend/auditor/auditor.py` - Enhanced with skip/retry detection integration
- `backend/auditor/quarantine_parser.py` - Parses QUARANTINE.md
- `backend/auditor/ci_parser.py` - Parses CI configuration

## How to Run Tests

```bash
# Run F3 tests
pytest tests/test_f3_remediation.py -v

# Run F4 tests
pytest tests/test_f4_audit.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/test_f3_remediation.py tests/test_f4_audit.py --cov=backend/remediation --cov=backend/auditor
```

## Example F2 Input (Diagnosis)

```json
{
  "test_name": "test_payment_timeout",
  "root_cause": "timing_race",
  "confidence": 0.91,
  "evidence": [
    {
      "file": "tests/test_payment.py",
      "line": 24,
      "reason": "sleep before assertion"
    },
    {
      "file": "tests/test_payment.py",
      "line": 26,
      "reason": "timing-dependent assertion"
    }
  ]
}
```

## Example F3 Output (Remediation)

```json
{
  "test_name": "test_payment_timeout",
  "root_cause": "timing_race",
  "strategy": "deterministic_wait",
  "fix_available": true,
  "evidence_valid": true,
  "diff": "--- a/tests/test_payment.py\n+++ b/tests/test_payment.py\n@@ -21,8 +21,8 @@\n def test_payment_timeout():\n     payment = initiate_payment()\n-    time.sleep(2)\n-    assert payment.status == 'complete'\n+    wait_for_completion(payment, timeout=5)\n+    assert payment.status == 'complete'",
  "files_changed": [
    "tests/test_payment.py"
  ],
  "requires_human_review": true,
  "validation": {
    "validated": true,
    "before": {
      "runs": 10,
      "passed": 7,
      "failed": 3
    },
    "after": {
      "runs": 10,
      "passed": 10,
      "failed": 0
    },
    "improvement": true
  }
}
```

## Example F4 Output (Audit)

```json
{
  "test_name": "test_payment_timeout",
  "diagnosis": {
    "root_cause": "timing_race",
    "confidence": 0.91
  },
  "remediation": {
    "strategy": "deterministic_wait",
    "fix_available": true,
    "fix_validated": true,
    "diff": "..."
  },
  "audit": {
    "quarantined": true,
    "retry_detected": true,
    "retry_count": 3,
    "retry_source": "github_actions",
    "skip_detected": false,
    "xfail_detected": false
  },
  "trust_status": "diagnosed_but_still_suppressed",
  "recommended_action": [
    "Review proposed fix",
    "Apply and verify fix",
    "Remove quarantine after successful validation",
    "Remove unnecessary CI retry"
  ]
}
```

## Integration Contract

### F3 Remediation Generator

**Input Contract:**
```python
# F2 Diagnosis object
diagnosis: Dict[str, Any] = {
    "test_name": str,
    "root_cause": str,  # One of: timing_race, order_dependency, data_leakage, environment_network
    "confidence": float,  # 0.0 to 1.0
    "evidence": List[Dict[str, Any]]  # List of evidence items
}
```

**Output Contract:**
```python
# Remediation result
remediation: Dict[str, Any] = {
    "test_name": str,
    "root_cause": str,
    "strategy": str,  # Strategy name from RemediationStrategy enum
    "fix_available": bool,
    "evidence_valid": bool,
    "diff": str,  # Unified diff format
    "files_changed": List[str],
    "requires_human_review": bool,
    "validation": Optional[Dict[str, Any]]  # Before/after test results
}
```

### F4 Audit Module

**Input Contract:**
```python
# Repository path
repo_path: str = "sample-repo"

# F2 Classifications (optional, for cross-reference)
classifications: List[Classification] = [...]

# F3 Remediations (optional, for cross-reference)
remediations: List[Dict[str, Any]] = [...]
```

**Output Contract:**
```python
# Audit result for a test
audit: Dict[str, Any] = {
    "test_name": str,
    "quarantined": bool,
    "retry_detected": bool,
    "retry_count": int,
    "retry_source": Optional[str],
    "skip_detected": bool,
    "xfail_detected": bool,
    "trust_status": str,  # Status from defined enum
    "recommended_action": List[str]
}
```

## Integration Instructions for Member 5 (API)

### 1. Evidence Validation Endpoint

```python
from backend.remediation.evidence_validator import EvidenceValidator

@router.post("/remediation/validate-evidence")
async def validate_evidence(diagnosis: Dict[str, Any]):
    validator = EvidenceValidator()
    result = validator.validate(diagnosis)
    return result
```

### 2. Strategy Selection Endpoint

```python
from backend.remediation.strategy import StrategySelector

@router.post("/remediation/select-strategy")
async def select_strategy(root_cause: str, evidence: List[Dict[str, Any]] = None):
    strategies = StrategySelector.select_strategies(root_cause, evidence)
    return {
        "root_cause": root_cause,
        "strategies": [s.value for s in strategies],
        "descriptions": [StrategySelector.get_strategy_description(s) for s in strategies]
    }
```

### 3. Skip Detection Endpoint

```python
from backend.auditor.skip_detector import SkipDetector

@router.get("/audit/skip-detections")
async def detect_skips(repo_path: str = "sample-repo"):
    detector = SkipDetector(repo_root=repo_path)
    detections = detector.detect_in_directory("tests")
    summary = detector.summarize(detections)
    return {
        "detections": detections,
        "summary": summary
    }
```

### 4. Retry Detection Endpoint

```python
from backend.auditor.retry_detector import RetryDetector

@router.get("/audit/retry-detections")
async def detect_retries(repo_path: str = "sample-repo"):
    detector = RetryDetector(repo_root=repo_path)
    result = detector.detect_all()
    return result
```

### 5. Comprehensive Audit Endpoint

```python
from backend.auditor.skip_detector import SkipDetector
from backend.auditor.retry_detector import RetryDetector
from backend.auditor.quarantine_parser import QuarantineParser

@router.get("/audit/comprehensive")
async def comprehensive_audit(repo_path: str = "sample-repo"):
    # Detect all suppression mechanisms
    skip_detector = SkipDetector(repo_root=repo_path)
    skip_detections = skip_detector.detect_in_directory("tests")
    
    retry_detector = RetryDetector(repo_root=repo_path)
    retry_result = retry_detector.detect_all()
    
    # Parse quarantine
    quarantine_parser = QuarantineParser()
    quarantine_file = f"{repo_path}/QUARANTINE.md"
    try:
        quarantine_entries = quarantine_parser.parse_markdown(quarantine_file)
    except:
        quarantine_entries = []
    
    return {
        "skip_detections": skip_detections,
        "retry_configuration": retry_result,
        "quarantine": [e.dict() for e in quarantine_entries]
    }
```

## Usage Examples

### Example 1: Validate Evidence and Generate Fix

```python
from backend.remediation.evidence_validator import EvidenceValidator
from backend.remediation.strategy import StrategySelector
from backend.remediation.generator import FixGenerator

# F2 diagnosis
diagnosis = {
    "test_name": "test_payment_timeout",
    "root_cause": "timing_race",
    "confidence": 0.91,
    "evidence": [
        {
            "file": "tests/test_payment.py",
            "line": 24,
            "reason": "sleep before assertion"
        }
    ]
}

# Step 1: Validate evidence
validator = EvidenceValidator()
validation = validator.validate(diagnosis)

if validation["valid"]:
    # Step 2: Select strategy
    strategies = StrategySelector.select_strategies(
        diagnosis["root_cause"],
        diagnosis["evidence"]
    )
    
    # Step 3: Generate fix
    generator = FixGenerator()
    fix = await generator.generate_fix(diagnosis, test_source="...")
    
    print(f"Fix available: {fix.fix_available}")
    print(f"Strategy: {fix.strategy}")
    print(f"Diff: {fix.diff}")
```

### Example 2: Comprehensive Audit

```python
from backend.auditor.skip_detector import SkipDetector
from backend.auditor.retry_detector import RetryDetector
from backend.auditor.quarantine_parser import QuarantineParser

# Initialize detectors
skip_detector = SkipDetector(repo_root="sample-repo")
retry_detector = RetryDetector(repo_root="sample-repo")
quarantine_parser = QuarantineParser()

# Detect all
skip_detections = skip_detector.detect_in_directory("tests")
retry_result = retry_detector.detect_all()
quarantine_entries = quarantine_parser.parse_markdown("sample-repo/QUARANTINE.md")

# Cross-reference
for entry in quarantine_entries:
    test_name = entry.test_name
    
    # Check if skipped
    is_skipped = any(d["test_name"] == test_name for d in skip_detections)
    
    # Check if retry
    retry_info = retry_detector.detect_for_test(test_name)
    
    status = "diagnosed_but_still_suppressed" if (entry.quarantined and is_skipped) else "quarantined"
    
    print(f"{test_name}: {status}")
    if retry_info["retry_detected"]:
        print(f"  - Retry count: {retry_info['retry_count']}")
```

## Known Limitations

### F3 Remediation

1. **Evidence Validation**: Currently validates file existence and line ranges. Does not perform deep semantic validation of code at the specified lines.

2. **Diff Generation**: Generates diffs for common patterns. Complex code structures may require manual refinement.

3. **Fix Validation**: Temporary validation by applying fix to a copy of the code. Does not integrate with full CI pipeline in hackathon MVP.

4. **LLM Integration**: Remediation uses deterministic templates. Optional LLM enhancement not implemented for hackathon.

### F4 Audit

1. **Skip Detection**: Detects common pytest markers. May miss custom skip mechanisms or conditional skips with complex logic.

2. **Retry Detection**: Detects common CI retry patterns (nick-invision/retry, pytest-rerunfailures). May miss custom retry implementations.

3. **Cross-Repository**: Currently designed for single repository analysis. Multi-repo aggregation not implemented.

4. **Historical Tracking**: Tracks current state. Historical quarantine trends not implemented in MVP.

## Future Enhancements

1. **LLM-Enhanced Remediation**: Use LLM for complex fix generation beyond templates
2. **Automated PR Creation**: Generate PRs with proposed fixes
3. **CI Integration**: Direct integration with CI systems for validation
4. **Multi-Repository Support**: Aggregate audit across multiple repositories
5. **Trend Analysis**: Track quarantine and fix success rates over time
6. **Custom Rules**: Allow users to define custom skip/retry patterns
7. **Auto-Fix Mode**: Automatically apply high-confidence validated fixes

## Testing

All modules include comprehensive unit tests. Run with:

```bash
pytest tests/test_f3_remediation.py tests/test_f4_audit.py -v --cov
```

Expected coverage: >80% for all new modules.

## Support

For questions or issues:
1. Check this documentation
2. Review test files for usage examples
3. Check module docstrings for detailed API documentation
