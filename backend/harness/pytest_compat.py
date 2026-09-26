"""Pytest compatibility plugin for pytest-json-report on pytest 7+."""
import pytest


def pytest_addhooks(pluginmanager):
    """Register pytest_warning_captured hook specification expected by pytest-json-report 1.1.0."""
    class WarningHookSpec:
        @pytest.hookspec
        def pytest_warning_captured(self, warning_message, when):
            pass

    pluginmanager.add_hookspecs(WarningHookSpec)
