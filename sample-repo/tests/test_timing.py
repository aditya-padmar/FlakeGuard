"""Tests with timing-related flakiness patterns."""
import time
import pytest
from src.calculator import Calculator


class TestTimingIssues:
    """Tests that exhibit timing-related flakiness."""
    
    def test_timing_dependent(self):
        """Test that depends on timing - can be flaky."""
        calc = Calculator()
        start = time.time()
        
        # This test can fail if system is slow
        result = calc.add(5, 3)
        elapsed = time.time() - start
        
        # Flaky: depends on system load
        assert elapsed < 0.001, f"Operation took too long: {elapsed}s"
        assert result == 8
    
    def test_sleep_based(self):
        """Test using sleep - unreliable."""
        calc = Calculator()
        
        # Flaky: sleep doesn't guarantee exact timing
        time.sleep(0.01)
        result = calc.add(2, 2)
        
        assert result == 4
    
    def test_timeout_sensitive(self):
        """Test that might timeout on slow systems."""
        calc = Calculator()
        
        # This might timeout on CI with heavy load
        for _ in range(10000):
            calc.add(1, 1)
        
        assert calc.operation_count == 10000
