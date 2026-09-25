"""Fix templates for common flaky test patterns."""
from typing import Dict


class FixTemplates:
    """Templates for common fix patterns."""
    
    TEMPLATES = {
        # Timing templates
        "timing_await": {
            "description": "Replace sleep with proper wait",
            "code_example": """
# Before:
time.sleep(1)
result = get_result()

# After:
result = wait_for_result(timeout=5, interval=0.1)
""",
            "effort": "medium"
        },
        "timing_assertion": {
            "description": "Relax or remove timing assertion",
            "code_example": """
# Before:
assert elapsed < 0.01

# After:
assert elapsed < 1.0  # Increased tolerance
# Or remove the assertion entirely
""",
            "effort": "low"
        },
        "timing_retry": {
            "description": "Add retry logic",
            "code_example": """
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.1))
def test_something():
    # Test code
    pass
""",
            "effort": "medium"
        },
        
        # Ordering templates
        "ordering_isolation": {
            "description": "Add proper test isolation",
            "code_example": """
class TestWithIsolation:
    @pytest.fixture
    def calculator(self):
        # Fresh instance for each test
        return Calculator()
    
    def test_operation(self, calculator):
        # Use isolated fixture
        result = calculator.add(1, 2)
        assert result == 3
""",
            "effort": "medium"
        },
        "ordering_cleanup": {
            "description": "Add teardown/cleanup",
            "code_example": """
class TestWithCleanup:
    @pytest.fixture
    def resource(self):
        # Setup
        res = create_resource()
        yield res
        # Teardown
        res.cleanup()
""",
            "effort": "low"
        },
        
        # Leakage templates
        "leakage_fresh_instance": {
            "description": "Use fresh instances instead of global state",
            "code_example": """
# Before:
calc = get_shared_calculator()

# After:
calc = Calculator()  # Fresh instance per test
""",
            "effort": "low"
        },
        "leakage_cleanup": {
            "description": "Reset mutable state",
            "code_example": """
def test_with_cleanup():
    shared_state.clear()
    try:
        # Test code
        pass
    finally:
        shared_state.clear()
""",
            "effort": "low"
        },
        
        # Environment templates
        "environment_mock": {
            "description": "Mock external dependencies",
            "code_example": """
from unittest.mock import patch, MagicMock

@patch('module.external_api_call')
def test_with_mock(mock_api):
    mock_api.return_value = {"status": "ok"}
    # Test code that uses mocked API
""",
            "effort": "medium"
        },
        "environment_graceful": {
            "description": "Handle missing resources gracefully",
            "code_example": """
import pytest

def test_with_skip():
    if not resource_available():
        pytest.skip("Resource not available")
    # Test code
""",
            "effort": "low"
        },
        "environment_seed": {
            "description": "Set fixed random seed",
            "code_example": """
import random

def test_deterministic():
    random.seed(42)
    # Now random operations are deterministic
    value = random.randint(1, 100)
    assert value == 82  # Predictable with seed
""",
            "effort": "low"
        },
        
        # Generic templates
        "generic_quarantine": {
            "description": "Quarantine test",
            "code_example": """
import pytest

@pytest.mark.quarantine(reason="Flaky - under investigation")
def test_quarantined():
    # Test code
    pass
""",
            "effort": "low"
        }
    }
    
    def get_template(self, template_name: str) -> Dict:
        """Get a fix template by name."""
        return self.TEMPLATES.get(template_name, {})
    
    def get_code_example(self, template_name: str) -> str:
        """Get code example for a template."""
        template = self.get_template(template_name)
        return template.get("code_example", "# No example available")
    
    def get_effort(self, template_name: str) -> str:
        """Get effort estimate for a template."""
        template = self.get_template(template_name)
        return template.get("effort", "medium")
