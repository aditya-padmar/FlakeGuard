"""Tests with environment/network-related flakiness patterns."""
import pytest
import os
import random


class TestEnvironmentIssues:
    """Tests that depend on environment conditions."""
    
    def test_env_dependent(self):
        """Test that depends on environment variables."""
        # Flaky: depends on external env var
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Might fail if env not set correctly
        assert "localhost" in api_url or "api" in api_url
    
    def test_random_failure(self):
        """Test with random behavior - true flakiness."""
        # This is intentionally flaky for demo purposes
        if random.random() < 0.3:  # 30% failure rate
            pytest.fail("Random failure for flaky test demonstration")
        
        assert True
    
    def test_ci_vs_local(self):
        """Test that behaves differently in CI vs local."""
        is_ci = os.getenv("CI") == "true"
        
        if is_ci:
            # Different behavior in CI
            timeout = 5
        else:
            timeout = 10
        
        # Flaky: timeout might be insufficient in CI
        assert timeout > 0
    
    def test_resource_availability(self):
        """Test that depends on external resources."""
        # Flaky: resource might not be available
        try:
            # Simulating external resource check
            available = os.getenv("RESOURCE_AVAILABLE", "true") == "true"
            assert available
        except Exception:
            pytest.skip("Resource not available")
