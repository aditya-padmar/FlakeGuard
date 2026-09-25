"""Simple calculator module with intentional flaky test patterns."""


class Calculator:
    """Calculator class with basic operations."""
    
    def __init__(self):
        self.last_result = None
        self.operation_count = 0
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        self.operation_count += 1
        self.last_result = a + b
        return self.last_result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        self.operation_count += 1
        self.last_result = a - b
        return self.last_result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        self.operation_count += 1
        self.last_result = a * b
        return self.last_result
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        self.operation_count += 1
        self.last_result = a / b
        return self.last_result
    
    def clear(self) -> None:
        """Clear calculator state."""
        self.last_result = None
        self.operation_count = 0


# Global instance for testing state leakage
_shared_calculator = Calculator()


def get_shared_calculator() -> Calculator:
    """Get shared calculator instance (can cause state leakage)."""
    return _shared_calculator
