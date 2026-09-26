"""Tests with environment-dependent flakiness patterns."""
import os


class TestEnvironmentIssues:
    """Tests exhibiting environment dependency flakiness."""

    def test_region_dependent_totals(self):
        """Calculates totals depending on SALES_REGION environment variable."""
        region = os.environ.get("SALES_REGION", "US")
        totals = {"US": 100, "EU": 200}
        val = totals.get(region)
        assert val == 100, (
            f"Suspected cause: environment dependency. Observed SALES_REGION={region!r} "
            f"yielding total {val} (expected 100)."
        )

    def test_totals_lookup_control(self):
        """Stable control test with pure in-process dictionary lookup."""
        totals = {"US": 100, "EU": 200}
        assert totals["US"] + totals["EU"] == 300
