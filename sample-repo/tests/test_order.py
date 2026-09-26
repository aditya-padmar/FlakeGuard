"""Tests with order dependency flakiness patterns."""
from src import settings


class TestOrderingIssues:
    """Tests exhibiting order dependency flakiness."""

    def test_configures_retry_limit(self):
        """Configures the module-level retry limit; must always pass."""
        settings.RETRY_LIMIT = 3
        settings.RETRY_LIMIT_SET_BY = "test_configures_retry_limit"
        assert settings.RETRY_LIMIT == 3

    def test_depends_on_retry_limit(self):
        """Depends on RETRY_LIMIT being configured by test_configures_retry_limit."""
        observed = settings.RETRY_LIMIT
        assert observed == 3, (
            f"Suspected cause: order dependency. Observed default value {observed} (expected 3). "
            f"Expected setter test_configures_retry_limit must run before this test."
        )
