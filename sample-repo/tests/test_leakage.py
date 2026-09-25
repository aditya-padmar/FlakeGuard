"""Tests with state leakage patterns."""
import pytest
from src.calculator import Calculator, get_shared_calculator


class TestStateLeakage:
    """Tests that exhibit state leakage issues."""
    
    def test_leaky_setup(self):
        """Test with improper setup - leaks state."""
        calc = get_shared_calculator()
        # Forgot to clear - leaks state from previous tests
        calc.add(100, 200)
        assert calc.last_result == 300
    
    def test_leaky_assertion(self):
        """Test that can pass for wrong reasons due to leakage."""
        calc = get_shared_calculator()
        
        # This might pass if previous test left last_result = 300
        # even if our operation failed
        result = calc.subtract(400, 100)
        # Should assert result, not last_result
        assert calc.last_result == 300 or calc.last_result == 300
    
    def test_global_mutation(self):
        """Test that mutates global state."""
        calc = get_shared_calculator()
        calc.clear()
        
        # Modifies global state
        for i in range(5):
            calc.add(i, i)
        
        # Leaves state dirty
        assert calc.operation_count == 5
    
    def test_depends_on_global(self):
        """Test that depends on global state being clean."""
        calc = get_shared_calculator()
        
        # Flaky: assumes global state is clean
        # Will fail if test_global_mutation ran before
        assert calc.operation_count == 0
