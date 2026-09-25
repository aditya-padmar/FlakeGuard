"""
Tests for F3 Remediation Generator.

Tests:
1. timing/race diagnosis → correct remediation strategy
2. order dependency → correct strategy
3. data leakage → cleanup strategy
4. environment/network → mocking/deterministic strategy
5. invalid evidence → remediation rejected
"""
import pytest
from pathlib import Path
from backend.remediation.evidence_validator import EvidenceValidator
from backend.remediation.strategy import StrategySelector, RootCause, RemediationStrategy


class TestEvidenceValidator:
    """Test evidence validation."""
    
    def test_valid_evidence(self, tmp_path):
        """Test validation of valid evidence."""
        # Create test file
        test_file = tmp_path / "tests" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_foo():\n    assert True\n")
        
        validator = EvidenceValidator(repo_root=str(tmp_path))
        
        diagnosis = {
            "test_name": "test_foo",
            "root_cause": "timing",
            "confidence": 0.9,
            "evidence": [
                {
                    "file": "tests/test_example.py",
                    "line": 2,
                    "reason": "assertion found"
                }
            ]
        }
        
        result = validator.validate(diagnosis)
        
        assert result["valid"] is True
        assert len(result["locations"]) == 1
        assert "test_example.py:2" in result["locations"][0]
        assert result["message"] == "Evidence verified"
    
    def test_file_not_found(self, tmp_path):
        """Test validation when file doesn't exist."""
        validator = EvidenceValidator(repo_root=str(tmp_path))
        
        diagnosis = {
            "test_name": "test_missing",
            "root_cause": "timing",
            "evidence": [
                {
                    "file": "tests/nonexistent.py",
                    "line": 10,
                    "reason": "test"
                }
            ]
        }
        
        result = validator.validate(diagnosis)
        
        assert result["valid"] is False
        assert len(result["locations"]) == 0
        assert "No valid evidence" in result["message"]
    
    def test_line_out_of_range(self, tmp_path):
        """Test validation when line number is out of range."""
        test_file = tmp_path / "tests" / "test_example.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_foo():\n    pass\n")
        
        validator = EvidenceValidator(repo_root=str(tmp_path))
        
        diagnosis = {
            "test_name": "test_foo",
            "evidence": [
                {
                    "file": "tests/test_example.py",
                    "line": 100,
                    "reason": "test"
                }
            ]
        }
        
        result = validator.validate(diagnosis)
        
        assert result["valid"] is False
    
    def test_no_evidence(self):
        """Test validation with no evidence."""
        validator = EvidenceValidator()
        
        diagnosis = {
            "test_name": "test_foo",
            "evidence": []
        }
        
        result = validator.validate(diagnosis)
        
        assert result["valid"] is False
        assert result["message"] == "No evidence provided"


class TestStrategySelector:
    """Test remediation strategy selection."""
    
    def test_timing_race_strategy(self):
        """Test strategy selection for timing/race condition."""
        strategies = StrategySelector.select_strategies("timing_race")
        
        assert RemediationStrategy.DETERMINISTIC_WAIT in strategies
        assert RemediationStrategy.REMOVE_SLEEP in strategies
        assert RemediationStrategy.RELAX_TIMING_ASSERTION in strategies
    
    def test_order_dependency_strategy(self):
        """Test strategy selection for order dependency."""
        strategies = StrategySelector.select_strategies("order_dependency")
        
        assert RemediationStrategy.ADD_FRESH_FIXTURE in strategies
        assert RemediationStrategy.ISOLATE_SHARED_STATE in strategies
    
    def test_data_leakage_strategy(self):
        """Test strategy selection for data/state leakage."""
        strategies = StrategySelector.select_strategies("data_leakage")
        
        assert RemediationStrategy.USE_FRESH_INSTANCE in strategies
        assert RemediationStrategy.ADD_CLEANUP_TEARDOWN in strategies
    
    def test_environment_network_strategy(self):
        """Test strategy selection for environment/network issues."""
        strategies = StrategySelector.select_strategies("environment_network")
        
        assert RemediationStrategy.MOCK_EXTERNAL_DEPENDENCY in strategies
        assert RemediationStrategy.MAKE_DETERMINISTIC in strategies
        assert RemediationStrategy.ADD_RANDOM_SEED in strategies
    
    def test_unknown_cause_quarantine(self):
        """Test that unknown causes default to quarantine."""
        strategies = StrategySelector.select_strategies("unknown")
        
        assert strategies == [RemediationStrategy.QUARANTINE]
    
    def test_evidence_based_refinement_sleep(self):
        """Test that evidence mentioning 'sleep' prioritizes sleep removal."""
        evidence = [
            {"reason": "sleep before assertion"}
        ]
        
        strategies = StrategySelector.select_strategies("timing", evidence)
        
        # REMOVE_SLEEP should be first priority
        assert strategies[0] == RemediationStrategy.REMOVE_SLEEP
    
    def test_evidence_based_refinement_assertion(self):
        """Test that evidence mentioning timing assertion prioritizes relaxation."""
        evidence = [
            {"reason": "assertion on elapsed time"}
        ]
        
        strategies = StrategySelector.select_strategies("timing", evidence)
        
        # RELAX_TIMING_ASSERTION should be prioritized
        assert RemediationStrategy.RELAX_TIMING_ASSERTION in strategies[:2]
    
    def test_evidence_based_refinement_shared_state(self):
        """Test that evidence mentioning shared state prioritizes isolation."""
        evidence = [
            {"reason": "shared global state"}
        ]
        
        strategies = StrategySelector.select_strategies("order_dependency", evidence)
        
        # ISOLATE_SHARED_STATE should be first
        assert strategies[0] == RemediationStrategy.ISOLATE_SHARED_STATE
    
    def test_evidence_based_refinement_random(self):
        """Test that evidence mentioning random prioritizes seed."""
        evidence = [
            {"reason": "random number generation"}
        ]
        
        strategies = StrategySelector.select_strategies("environment", evidence)
        
        # ADD_RANDOM_SEED should be first
        assert strategies[0] == RemediationStrategy.ADD_RANDOM_SEED
    
    def test_strategy_descriptions(self):
        """Test that all strategies have descriptions."""
        for strategy in RemediationStrategy:
            desc = StrategySelector.get_strategy_description(strategy)
            assert desc is not None
            assert len(desc) > 0


class TestRemediationIntegration:
    """Integration tests for full remediation pipeline."""
    
    def test_timing_diagnosis_to_strategy(self):
        """Test end-to-end: timing diagnosis → strategy selection."""
        # Mock F2 diagnosis
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
        
        # Select strategies
        strategies = StrategySelector.select_strategies(
            diagnosis["root_cause"],
            diagnosis["evidence"]
        )
        
        # Should prioritize sleep removal
        assert strategies[0] == RemediationStrategy.REMOVE_SLEEP
        assert RemediationStrategy.DETERMINISTIC_WAIT in strategies
    
    def test_leakage_diagnosis_to_strategy(self):
        """Test end-to-end: leakage diagnosis → cleanup strategy."""
        diagnosis = {
            "test_name": "test_shared_cache",
            "root_cause": "state_leakage",
            "confidence": 0.85,
            "evidence": [
                {
                    "file": "tests/test_cache.py",
                    "line": 15,
                    "reason": "missing teardown"
                }
            ]
        }
        
        strategies = StrategySelector.select_strategies(
            diagnosis["root_cause"],
            diagnosis["evidence"]
        )
        
        # Should include cleanup strategies
        assert RemediationStrategy.ADD_CLEANUP_TEARDOWN in strategies
        assert RemediationStrategy.USE_FRESH_INSTANCE in strategies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
