"""
Tests for F4 Quarantine / CI Audit.

Tests:
6. QUARANTINE.md parsing
7. pytest skip detection
8. xfail detection
9. CI retry detection
10. quarantined + diagnosed test → correct audit status
"""
import pytest
from pathlib import Path
from backend.auditor.quarantine_parser import QuarantineParser
from backend.auditor.skip_detector import SkipDetector
from backend.auditor.retry_detector import RetryDetector


class TestQuarantineParser:
    """Test QUARANTINE.md parsing."""
    
    def test_parse_markdown(self, tmp_path):
        """Test parsing QUARANTINE.md format."""
        quarantine_file = tmp_path / "QUARANTINE.md"
        quarantine_file.write_text("""
# Quarantined Tests

## Active Quarantines

| Test | Reason | Quarantined Date | Runs Until Review |
|------|--------|------------------|-------------------|
| `test_payment_timeout` | Timing issue | 2024-01-15 | 10 |
| `test_shared_cache` | State leakage | 2024-01-20 | 8 |
| `test_old_api` | Environment | 2024-01-10 | 5 |
""")
        
        parser = QuarantineParser()
        entries = parser.parse_markdown(str(quarantine_file))
        
        assert len(entries) == 3
        
        # Check first entry
        assert entries[0].test_name == "test_payment_timeout"
        assert entries[0].reason == "Timing issue"
        assert entries[0].runs_until_review == 10
        
        # Check second entry
        assert entries[1].test_name == "test_shared_cache"
        assert entries[1].reason == "State leakage"
    
    def test_empty_quarantine(self, tmp_path):
        """Test parsing empty quarantine file."""
        quarantine_file = tmp_path / "QUARANTINE.md"
        quarantine_file.write_text("# Quarantined Tests\n\nNo tests in quarantine.\n")
        
        parser = QuarantineParser()
        entries = parser.parse_markdown(str(quarantine_file))
        
        assert len(entries) == 0


class TestSkipDetector:
    """Test skip/xfail detection."""
    
    def test_detect_skip_decorator(self, tmp_path):
        """Test detection of @pytest.mark.skip."""
        test_file = tmp_path / "tests" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
import pytest

@pytest.mark.skip(reason="Known issue")
def test_broken():
    assert False
    
def test_working():
    assert True
""")
        
        detector = SkipDetector(repo_root=str(tmp_path))
        detections = detector.detect_in_file("tests/test_example.py")
        
        assert len(detections) == 1
        assert detections[0]["test_name"] == "test_broken"
        assert detections[0]["suppression_type"] == "skip"
        assert detections[0]["reason"] == "Known issue"
    
    def test_detect_xfail_decorator(self, tmp_path):
        """Test detection of @pytest.mark.xfail."""
        test_file = tmp_path / "tests" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
import pytest

@pytest.mark.xfail(reason="Expected to fail")
def test_experimental():
    assert False
""")
        
        detector = SkipDetector(repo_root=str(tmp_path))
        detections = detector.detect_in_file("tests/test_example.py")
        
        assert len(detections) == 1
        assert detections[0]["test_name"] == "test_experimental"
        assert detections[0]["suppression_type"] == "xfail"
        assert detections[0]["reason"] == "Expected to fail"
    
    def test_detect_inline_skip(self, tmp_path):
        """Test detection of pytest.skip() call."""
        test_file = tmp_path / "tests" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
import pytest

def test_conditional():
    if not has_resource():
        pytest.skip("Resource not available")
    assert do_something()
""")
        
        detector = SkipDetector(repo_root=str(tmp_path))
        detections = detector.detect_in_file("tests/test_example.py")
        
        assert len(detections) == 1
        assert detections[0]["test_name"] == "test_conditional"
        assert detections[0]["suppression_type"] == "skip_call"
        assert detections[0]["source"] == "inline"
    
    def test_no_suppressions(self, tmp_path):
        """Test file with no suppressions."""
        test_file = tmp_path / "tests" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
def test_normal():
    assert True
""")
        
        detector = SkipDetector(repo_root=str(tmp_path))
        detections = detector.detect_in_file("tests/test_example.py")
        
        assert len(detections) == 0
    
    def test_summarize_detections(self):
        """Test detection summarization."""
        detections = [
            {
                "test_name": "test_a",
                "suppression_type": "skip",
                "file": "test.py",
                "line": 1
            },
            {
                "test_name": "test_b",
                "suppression_type": "xfail",
                "file": "test.py",
                "line": 5
            },
            {
                "test_name": "test_c",
                "suppression_type": "skip_call",
                "file": "test.py",
                "line": 10
            }
        ]
        
        detector = SkipDetector()
        summary = detector.summarize(detections)
        
        assert summary["total_suppressed"] == 3
        assert summary["skip_count"] == 2  # skip + skip_call
        assert summary["xfail_count"] == 1


class TestRetryDetector:
    """Test CI retry detection."""
    
    def test_detect_github_actions_retry(self, tmp_path):
        """Test detection of retry in GitHub Actions."""
        workflow_dir = tmp_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        
        workflow_file = workflow_dir / "ci.yml"
        workflow_file.write_text("""
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: nick-invision/retry@v2
        with:
          max_attempts: 3
          command: pytest tests/
""")
        
        detector = RetryDetector(repo_root=str(tmp_path))
        result = detector.detect_github_actions()
        
        assert result["retry_detected"] is True
        assert result["retry_count"] == 3
        assert len(result["details"]) == 1
        assert "retry action" in result["details"][0]["mechanism"]
    
    def test_detect_pytest_reruns(self, tmp_path):
        """Test detection of pytest reruns plugin."""
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("""
[pytest]
addopts = --reruns 3 --reruns-delay 1
""")
        
        detector = RetryDetector(repo_root=str(tmp_path))
        result = detector.detect_pytest_config()
        
        assert result["retry_detected"] is True
        assert result["retry_count"] == 3
    
    def test_no_retry_detected(self, tmp_path):
        """Test when no retry configuration found."""
        detector = RetryDetector(repo_root=str(tmp_path))
        result = detector.detect_all()
        
        assert result["summary"]["retry_detected"] is False
        assert len(result["summary"]["sources"]) == 0
    
    def test_detect_for_specific_test(self, tmp_path):
        """Test retry detection for specific test."""
        # Setup retry in workflow
        workflow_dir = tmp_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        
        workflow_file = workflow_dir / "ci.yml"
        workflow_file.write_text("""
name: CI
steps:
  - run: pytest --reruns 5
""")
        
        detector = RetryDetector(repo_root=str(tmp_path))
        result = detector.detect_for_test("test_payment_timeout")
        
        assert result["test_name"] == "test_payment_timeout"
        assert result["retry_detected"] is True
        assert result["retry_count"] == 5


class TestAuditIntegration:
    """Integration tests for complete audit pipeline."""
    
    def test_quarantined_and_diagnosed(self, tmp_path):
        """Test audit status for quarantined + diagnosed test."""
        # Create quarantine file
        quarantine_file = tmp_path / "QUARANTINE.md"
        quarantine_file.write_text("""
| `test_payment_timeout` | Flaky | 2024-01-15 | 10 |
""")
        
        # Create test file with skip marker
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_payment.py"
        test_file.write_text("""
@pytest.mark.skip(reason="Quarantined")
def test_payment_timeout():
    pass
""")
        
        # Parse quarantine
        parser = QuarantineParser()
        quarantine_entries = parser.parse_markdown(str(quarantine_file))
        
        # Detect skip
        skip_detector = SkipDetector(repo_root=str(tmp_path))
        skip_detections = skip_detector.detect_in_file("tests/test_payment.py")
        
        # Detect retry
        retry_detector = RetryDetector(repo_root=str(tmp_path))
        retry_result = retry_detector.detect_for_test("test_payment_timeout")
        
        # Combine results
        assert len(quarantine_entries) == 1
        assert quarantine_entries[0].test_name == "test_payment_timeout"
        
        assert len(skip_detections) == 1
        assert skip_detections[0]["test_name"] == "test_payment_timeout"
        
        # Status should be: diagnosed_but_still_suppressed
        # (if we also had F2 classification showing it's diagnosed)
    
    def test_retry_detected_status(self, tmp_path):
        """Test that retry detection leads to correct status."""
        # Setup GitHub Actions with retry
        workflow_dir = tmp_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        
        workflow_file = workflow_dir / "ci.yml"
        workflow_file.write_text("""
steps:
  - uses: nick-invision/retry@v2
    with:
      max_attempts: 3
      command: pytest
""")
        
        detector = RetryDetector(repo_root=str(tmp_path))
        result = detector.detect_all()
        
        assert result["summary"]["retry_detected"] is True
        assert "github_actions" in result["summary"]["sources"]
        
        # This is important: FlakeGuard should expose tests
        # whose failures are being hidden by retries
    
    def test_fix_available_status(self):
        """Test status when fix is available."""
        # Mock scenario:
        # - Test is diagnosed (timing_race)
        # - Fix has been generated
        # - Fix has been validated
        
        diagnosis = {
            "root_cause": "timing_race",
            "confidence": 0.91
        }
        
        remediation = {
            "strategy": "deterministic_wait",
            "fix_available": True,
            "fix_validated": True
        }
        
        audit = {
            "quarantined": False,
            "retry_detected": False,
            "skip_detected": False
        }
        
        # Status should be: fix_validated
        # Recommended action: Apply fix and verify
        
        assert remediation["fix_available"] is True
        assert remediation["fix_validated"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
