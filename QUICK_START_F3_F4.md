# Quick Start Guide - F3 & F4

## Installation

```bash
# Already included in requirements.txt
pip install -r requirements.txt
```

## Run Tests

```bash
# All F3 & F4 tests
pytest tests/test_f3_remediation.py tests/test_f4_audit.py -v

# With coverage
pytest tests/test_f3_remediation.py tests/test_f4_audit.py --cov=backend/remediation --cov=backend/auditor -v
```

## Quick Usage Examples

### 1. Validate F2 Evidence

```python
from backend.remediation.evidence_validator import EvidenceValidator

validator = EvidenceValidator(repo_root="sample-repo")

diagnosis = {
    "test_name": "test_timing_dependent",
    "root_cause": "timing",
    "evidence": [
        {"file": "tests/test_timing.py", "line": 15, "reason": "sleep found"}
    ]
}

result = validator.validate(diagnosis)
print(f"Valid: {result['valid']}")
print(f"Locations: {result['locations']}")
```

### 2. Select Remediation Strategy

```python
from backend.remediation.strategy import StrategySelector

strategies = StrategySelector.select_strategies(
    root_cause="timing_race",
    evidence=[{"reason": "sleep before assertion"}]
)

print(f"Primary strategy: {strategies[0].value}")
print(f"Description: {StrategySelector.get_strategy_description(strategies[0])}")
```

### 3. Detect Skip/Xfail Markers

```python
from backend.auditor.skip_detector import SkipDetector

detector = SkipDetector(repo_root="sample-repo")
detections = detector.detect_in_directory("tests")

for d in detections:
    print(f"{d['test_name']}: {d['suppression_type']} - {d['reason']}")
```

### 4. Detect CI Retries

```python
from backend.auditor.retry_detector import RetryDetector

detector = RetryDetector(repo_root="sample-repo")
result = detector.detect_all()

if result["summary"]["retry_detected"]:
    print(f"Retry detected in: {result['summary']['sources']}")
    print(f"Max retry count: {result['github_actions']['retry_count']}")
```

### 5. Comprehensive Audit

```python
from backend.auditor.skip_detector import SkipDetector
from backend.auditor.retry_detector import RetryDetector
from backend.auditor.quarantine_parser import QuarantineParser

# Initialize
skip_detector = SkipDetector(repo_root="sample-repo")
retry_detector = RetryDetector(repo_root="sample-repo")
parser = QuarantineParser()

# Detect all
skips = skip_detector.detect_in_directory("tests")
retries = retry_detector.detect_all()
quarantine = parser.parse_markdown("sample-repo/QUARANTINE.md")

# Report
print(f"Quarantined: {len(quarantine)}")
print(f"Skipped: {len(skips)}")
print(f"Retry enabled: {retries['summary']['retry_detected']}")
```

## Root Cause → Strategy Mapping

| Root Cause | Primary Strategy | Description |
|------------|------------------|-------------|
| `timing_race` | `deterministic_wait` | Replace sleep with proper wait |
| `order_dependency` | `add_fresh_fixture` | Isolate test state |
| `state_leakage` | `use_fresh_instance` | Use fresh objects |
| `environment_network` | `mock_external_dependency` | Mock external calls |

## Trust Status Values

- `not_suppressed` - Test runs normally
- `quarantined` - In QUARANTINE.md
- `retry_detected` - Has CI retry
- `diagnosed_but_still_suppressed` - Fix available but still hidden
- `fix_available` - Remediation generated
- `fix_validated` - Fix tested successfully

## Common Workflows

### Workflow 1: Generate Remediation

```python
# 1. Validate evidence
validation = validator.validate(f2_diagnosis)

# 2. Select strategy
if validation["valid"]:
    strategies = StrategySelector.select_strategies(
        f2_diagnosis["root_cause"],
        f2_diagnosis["evidence"]
    )

# 3. Generate fix (existing generator)
from backend.remediation.generator import FixGenerator
generator = FixGenerator()
fix = await generator.generate_fix(f2_diagnosis, test_source)
```

### Workflow 2: Audit Repository

```python
# 1. Detect all suppressions
skip_detections = skip_detector.detect_in_directory("tests")
retry_result = retry_detector.detect_all()
quarantine_entries = parser.parse_markdown("QUARANTINE.md")

# 2. Cross-reference with F2 diagnosis
for entry in quarantine_entries:
    test_name = entry.test_name
    
    # Check if diagnosed
    has_diagnosis = test_name in f2_classifications
    
    # Check if skipped
    is_skipped = any(d["test_name"] == test_name for d in skip_detections)
    
    # Check if retry
    retry_info = retry_detector.detect_for_test(test_name)
    
    # Determine status
    if has_diagnosis and is_skipped and retry_info["retry_detected"]:
        status = "diagnosed_but_still_suppressed"
```

## API Integration (for Member 5)

```python
# In backend/api/routes/remediation.py
from backend.remediation.evidence_validator import EvidenceValidator
from backend.remediation.strategy import StrategySelector

@router.post("/remediation/validate-evidence")
async def validate_evidence(diagnosis: dict):
    validator = EvidenceValidator()
    return validator.validate(diagnosis)

@router.post("/remediation/strategies")
async def get_strategies(root_cause: str, evidence: list = None):
    strategies = StrategySelector.select_strategies(root_cause, evidence)
    return {
        "strategies": [s.value for s in strategies],
        "descriptions": [StrategySelector.get_strategy_description(s) for s in strategies]
    }
```

```python
# In backend/api/routes/audit.py
from backend.auditor.skip_detector import SkipDetector
from backend.auditor.retry_detector import RetryDetector

@router.get("/audit/suppressions")
async def get_suppressions(repo_path: str = "sample-repo"):
    skip_detector = SkipDetector(repo_root=repo_path)
    retry_detector = RetryDetector(repo_root=repo_path)
    
    return {
        "skips": skip_detector.detect_in_directory("tests"),
        "retries": retry_detector.detect_all()
    }
```

## Testing Your Integration

```bash
# 1. Run unit tests
pytest tests/test_f3_remediation.py tests/test_f4_audit.py -v

# 2. Test with sample-repo
cd sample-repo
pytest tests/ --verbose

# 3. Test evidence validation
python -c "
from backend.remediation.evidence_validator import EvidenceValidator
v = EvidenceValidator()
print(v.validate({'evidence': [{'file': 'tests/test_timing.py', 'line': 1}]}))
"

# 4. Test skip detection
python -c "
from backend.auditor.skip_detector import SkipDetector
d = SkipDetector()
print(d.detect_in_directory('tests'))
"
```

## Troubleshooting

**Issue**: "Module not found"
```bash
# Solution: Ensure you're in the FlakeGuard directory
cd c:\Projects\FlakeGuard
export PYTHONPATH=.
```

**Issue**: "File not found" during evidence validation
```bash
# Solution: Check repo_root parameter
validator = EvidenceValidator(repo_root="sample-repo")  # Correct path
```

**Issue**: Tests failing
```bash
# Solution: Install test dependencies
pip install pytest pytest-asyncio
```

## Documentation

- **Full Integration Guide**: `docs/F3_F4_INTEGRATION.md`
- **Completion Summary**: `F3_F4_COMPLETION_SUMMARY.md`
- **Architecture**: `docs/architecture.md`

## Support

For issues or questions:
1. Check module docstrings
2. Review test files for examples
3. See integration guide for detailed examples
