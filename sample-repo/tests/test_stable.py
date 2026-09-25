"""Stable tests for comparison with flaky tests."""
import pytest
from src.calculator import Calculator


class TestStable:
    """Stable tests with proper isolation and assertions."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator for each test."""
        calc = Calculator()
        yield calc
        # Cleanup (though not strictly necessary with fresh instances)
        calc.clear()
    
    def test_addition(self, calculator):
        """Test addition with proper isolation."""
        result = calculator.add(2, 3)
        assert result == 5
        assert calculator.last_result == 5
    
    def test_subtraction(self, calculator):
        """Test subtraction with proper isolation."""
        result = calculator.subtract(10, 4)
        assert result == 6
        assert calculator.last_result == 6
    
    def test_multiplication(self, calculator):
        """Test multiplication with proper isolation."""
        result = calculator.multiply(3, 4)
        assert result == 12
        assert calculator.last_result == 12
    
    def test_division(self, calculator):
        """Test division with proper isolation."""
        result = calculator.divide(15, 3)
        assert result == 5
        assert calculator.last_result == 5
    
    def test_divide_by_zero(self, calculator):
        """Test division by zero raises error."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calculator.divide(10, 0)
    
    def test_clear(self, calculator):
        """Test clear functionality."""
        calculator.add(5, 5)
        assert calculator.last_result is not None
        
        calculator.clear()
        assert calculator.last_result is None
        assert calculator.operation_count == 0
