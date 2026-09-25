"""Fix templates for common flaky test patterns."""
from typing import Dict


# Maps F2 root_cause strings to remediation strategy names
REMEDIATION_STRATEGIES = {
    "timing_race": "replace_sleep_with_deterministic_wait",
    "timing": "replace_sleep_with_deterministic_wait",
    "race_condition": "replace_sleep_with_deterministic_wait",
    "order_dependency": "isolate_shared_state",
    "ordering": "isolate_shared_state",
    "data_leakage": "add_cleanup_or_fixture_isolation",
    "state_leakage": "add_cleanup_or_fixture_isolation",
    "environment_network": "mock_external_dependency",
    "environment": "mock_external_dependency",
    "network": "mock_external_dependency",
}


class FixTemplates:
    """Templates for common fix patterns."""

    # Human-readable strategy descriptions keyed by strategy name
    FIX_TEMPLATES: Dict[str, Dict] = {
        "timing_race": {
            "description": "Replace arbitrary sleep with deterministic wait",
            "strategy": "replace_sleep_with_deterministic_wait",
        },
        "order_dependency": {
            "description": "Isolate shared state between tests",
            "strategy": "isolate_shared_state",
        },
        "data_leakage": {
            "description": "Add fixture cleanup/teardown",
            "strategy": "add_cleanup_or_fixture_isolation",
        },
        "environment_network": {
            "description": "Mock external network dependency",
            "strategy": "mock_external_dependency",
        },
    }

    # Detailed code-level templates keyed by internal template name
    TEMPLATES: Dict[str, Dict] = {
        # ── Timing ────────────────────────────────────────────────────────────
        "timing_await": {
            "description": "Replace sleep with proper wait",
            "strategy": "replace_sleep_with_deterministic_wait",
            "import": "import threading",
            "code_example": (
                "# Before:\n"
                "time.sleep(1)\n"
                "result = get_result()\n\n"
                "# After:\n"
                "result = wait_for_result(timeout=5, interval=0.1)"
            ),
            "effort": "medium",
        },
        "timing_assertion": {
            "description": "Relax or remove timing assertion",
            "strategy": "replace_sleep_with_deterministic_wait",
            "import": None,
            "code_example": (
                "# Before:\n"
                "assert elapsed < 0.001\n\n"
                "# After:\n"
                "assert elapsed < 1.0  # Increased tolerance"
            ),
            "effort": "low",
        },
        "timing_retry": {
            "description": "Add retry logic",
            "strategy": "replace_sleep_with_deterministic_wait",
            "import": "from tenacity import retry, stop_after_attempt, wait_exponential",
            "code_example": (
                "@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.1))\n"
                "def test_something():\n"
                "    # Test code\n"
                "    pass"
            ),
            "effort": "medium",
        },

        # ── Ordering ──────────────────────────────────────────────────────────
        "ordering_isolation": {
            "description": "Add proper test isolation",
            "strategy": "isolate_shared_state",
            "import": "import pytest",
            "code_example": (
                "class TestWithIsolation:\n"
                "    @pytest.fixture\n"
                "    def calculator(self):\n"
                "        # Fresh instance for each test\n"
                "        return Calculator()\n\n"
                "    def test_operation(self, calculator):\n"
                "        result = calculator.add(1, 2)\n"
                "        assert result == 3"
            ),
            "effort": "medium",
        },
        "ordering_cleanup": {
            "description": "Add teardown/cleanup",
            "strategy": "isolate_shared_state",
            "import": "import pytest",
            "code_example": (
                "@pytest.fixture\n"
                "def resource():\n"
                "    res = create_resource()\n"
                "    yield res\n"
                "    res.cleanup()"
            ),
            "effort": "low",
        },

        # ── Leakage ───────────────────────────────────────────────────────────
        "leakage_fresh_instance": {
            "description": "Use fresh instances instead of global state",
            "strategy": "add_cleanup_or_fixture_isolation",
            "import": None,
            "code_example": (
                "# Before:\n"
                "calc = get_shared_calculator()\n\n"
                "# After:\n"
                "calc = Calculator()  # Fresh instance per test"
            ),
            "effort": "low",
        },
        "leakage_cleanup": {
            "description": "Reset mutable state",
            "strategy": "add_cleanup_or_fixture_isolation",
            "import": "import pytest",
            "code_example": (
                "def test_with_cleanup():\n"
                "    shared_state.clear()\n"
                "    try:\n"
                "        # Test code\n"
                "        pass\n"
                "    finally:\n"
                "        shared_state.clear()"
            ),
            "effort": "low",
        },

        # ── Environment / Network ─────────────────────────────────────────────
        "environment_mock": {
            "description": "Mock external dependencies",
            "strategy": "mock_external_dependency",
            "import": "from unittest.mock import patch, MagicMock",
            "code_example": (
                "@patch('module.external_api_call')\n"
                "def test_with_mock(mock_api):\n"
                "    mock_api.return_value = {\"status\": \"ok\"}\n"
                "    # Test code that uses mocked API"
            ),
            "effort": "medium",
        },
        "environment_graceful": {
            "description": "Handle missing resources gracefully",
            "strategy": "mock_external_dependency",
            "import": "import pytest",
            "code_example": (
                "def test_with_skip():\n"
                "    if not resource_available():\n"
                "        pytest.skip(\"Resource not available\")\n"
                "    # Test code"
            ),
            "effort": "low",
        },
        "environment_seed": {
            "description": "Set fixed random seed",
            "strategy": "mock_external_dependency",
            "import": "import random",
            "code_example": (
                "def test_deterministic():\n"
                "    random.seed(42)\n"
                "    value = random.randint(1, 100)\n"
                "    assert value == 82  # Predictable with seed"
            ),
            "effort": "low",
        },

        # ── Generic ───────────────────────────────────────────────────────────
        "generic_quarantine": {
            "description": "Quarantine test",
            "strategy": "quarantine",
            "import": "import pytest",
            "code_example": (
                "@pytest.mark.quarantine(reason=\"Flaky - under investigation\")\n"
                "def test_quarantined():\n"
                "    # Test code\n"
                "    pass"
            ),
            "effort": "low",
        },
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

    def get_strategy(self, root_cause: str) -> str:
        """Map a root-cause string to a remediation strategy name."""
        return REMEDIATION_STRATEGIES.get(root_cause.lower(), "manual_investigation")
