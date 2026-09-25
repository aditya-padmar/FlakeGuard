"""Tests with ordering-related flakiness patterns."""
import pytest
from src.calculator import Calculator, get_shared_calculator


class TestOrderingIssues:
    """Tests that depend on execution order."""
    
    def test_first(self):
        """Test that must run first - ordering dependency."""
        calc = get_shared_calculator()
        calc.clear()
        
        calc.add(10, 5)
        assert calc.last_result == 15
    
    def test_second(self):
        """Test that depends on test_first running before it."""
        calc = get_shared_calculator()
        
        # Flaky: assumes test_first already ran
        assert calc.operation_count == 1
        calc.add(5, 5)
        assert calc.operation_count == 2
    
    def test_shared_state_a(self):
        """Test A that shares state with test B."""
        calc = get_shared_calculator()
        calc.multiply(3, 4)
        
        # Doesn't verify state is clean
        assert calc.last_result == 12
    
    def test_shared_state_b(self):
        """Test B that depends on A's cleanup."""
        calc = get_shared_calculator()
        
        # Flaky: depends on whether A ran and what it left behind
        # This will fail if A ran before and didn't clean up
        assert calc.last_result is None or calc.last_result == 12
