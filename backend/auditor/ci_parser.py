"""
Parser for CI configuration artifacts that contain skip/quarantine signals.

Reads two types of files:

1. pytest.ini (or setup.cfg / pyproject.toml [tool.pytest.ini_options])
   — extracts markers, addopts flags, and any deselect/skip-list entries.

2. GitHub Actions workflow YAML
   — extracts pytest invocation flags, environment variables, and any
     inline references to quarantine/skip markers.
"""
from __future__ import annotations

import configparser
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ── Patterns ──────────────────────────────────────────────────────────────────

# pytest -k expression that deselects tests:  -k "not test_foo"
_RE_K_EXPR = re.compile(r"""-k\s+["']?([^"'\s]+)["']?""")

# pytest --deselect flag
_RE_DESELECT = re.compile(r"--deselect[= ](\S+)")

# pytest -m / --markers expression referencing skip/quarantine
_RE_M_EXPR = re.compile(r"""-m\s+["']?([^"'\s]+)["']?""")

# Marker declarations in pytest.ini:  markers = skip_reason: ...
_RE_MARKER_LINE = re.compile(r"^\s*(?P<name>[\w_]+)\s*[=:?]?\s*(?P<desc>.*)", re.MULTILINE)

# "skip", "xfail", "quarantine" tokens anywhere in addopts / run command
_SKIP_TOKENS = re.compile(
    r"\b(?:skip|xfail|quarantine|disabled?|deselect)\b", re.IGNORECASE
)

# GitHub Actions env var that signals CI context
_RE_CI_ENV = re.compile(r"^\s+CI\s*:\s*(.+)$", re.MULTILINE)

# pytest run command line in a workflow step
_RE_PYTEST_CMD = re.compile(r"pytest\s+(.+?)(?:\n|$)")

# YAML 'run:' block content
_RE_RUN_BLOCK = re.compile(r"run:\s*\|?\s*\n((?:[ \t]+.+\n?)+)", re.MULTILINE)


# ── Result models ─────────────────────────────────────────────────────────────

@dataclass
class PytestConfig:
    """Parsed content of pytest.ini (or equivalent)."""
    # Declared markers (name → description)
    markers: Dict[str, str] = field(default_factory=dict)
    # addopts value as a raw string
    addopts: str = ""
    # Test paths
    testpaths: List[str] = field(default_factory=list)
    # Any -k expression found in addopts
    k_expression: Optional[str] = None
    # Any -m expression found in addopts
    m_expression: Optional[str] = None
    # Names of skip/quarantine-related markers
    skip_markers: List[str] = field(default_factory=list)
    # Deselected test node-ids
    deselected: List[str] = field(default_factory=list)
    # Raw asyncio_mode and other recognised options
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass
class CIWorkflowConfig:
    """Parsed signals from a CI workflow file."""
    # Detected CI platform
    platform: str = "unknown"
    # Python versions used
    python_versions: List[str] = field(default_factory=list)
    # Full pytest command lines found in 'run:' blocks
    pytest_commands: List[str] = field(default_factory=list)
    # -k expressions from pytest commands
    k_expressions: List[str] = field(default_factory=list)
    # -m expressions from pytest commands
    m_expressions: List[str] = field(default_factory=list)
    # Environment variables set in the workflow
    env_vars: Dict[str, str] = field(default_factory=dict)
    # Whether CI=true is set
    ci_flag: bool = False
    # Any skip/quarantine tokens found in the workflow
    skip_signals: List[str] = field(default_factory=list)


# ── Main parsers ──────────────────────────────────────────────────────────────

class CIParser:
    """
    Parses CI configuration files to identify quarantine/skip signals.

    Primary methods:
        parse_pytest_ini(path)     → PytestConfig
        parse_workflow_yaml(path)  → CIWorkflowConfig
        parse_all(repo_path)       → (PytestConfig, CIWorkflowConfig)
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def parse_pytest_ini(self, path: str) -> PytestConfig:
        """
        Parse pytest.ini (also handles setup.cfg [tool:pytest] sections).

        Returns a PytestConfig with extracted markers, addopts, and any
        skip/quarantine signals.
        """
        p = Path(path)
        if not p.exists():
            return PytestConfig()

        content = p.read_text(encoding="utf-8")

        # Try standard configparser first
        cfg = configparser.ConfigParser(strict=False)
        try:
            cfg.read_string(content)
        except configparser.Error:
            return self._parse_pytest_ini_manual(content)

        # Find the [pytest] section (pytest.ini) or [tool:pytest] (setup.cfg)
        section = None
        for candidate in ("pytest", "tool:pytest"):
            if cfg.has_section(candidate):
                section = candidate
                break

        if section is None:
            return PytestConfig()

        result = PytestConfig()

        # addopts
        if cfg.has_option(section, "addopts"):
            result.addopts = cfg.get(section, "addopts").strip()
            result.k_expression = self._extract_k(result.addopts)
            result.m_expression = self._extract_m(result.addopts)
            result.deselected = _RE_DESELECT.findall(result.addopts)

        # testpaths
        if cfg.has_option(section, "testpaths"):
            result.testpaths = cfg.get(section, "testpaths").split()

        # markers
        if cfg.has_option(section, "markers"):
            raw = cfg.get(section, "markers")
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Format: marker_name: description text
                # or just: marker_name
                if ":" in line:
                    name, _, desc = line.partition(":")
                else:
                    name, desc = line, ""
                name = name.strip()
                if name:
                    result.markers[name] = desc.strip()
                    if _SKIP_TOKENS.search(name) or _SKIP_TOKENS.search(desc):
                        result.skip_markers.append(name)

        # Extra recognised options
        for opt in ("asyncio_mode", "python_files", "python_classes", "python_functions"):
            if cfg.has_option(section, opt):
                result.extra[opt] = cfg.get(section, opt).strip()

        return result

    def parse_workflow_yaml(self, path: str) -> CIWorkflowConfig:
        """
        Parse a GitHub Actions (or generic) CI workflow YAML file.

        Uses regex-based extraction rather than a full YAML parser to avoid
        a PyYAML dependency at import time.
        """
        p = Path(path)
        if not p.exists():
            return CIWorkflowConfig()

        content = p.read_text(encoding="utf-8")
        result = CIWorkflowConfig()

        # Detect platform — normalise path separators for cross-platform matching
        path_str = str(p).replace("\\", "/")
        if ".github/workflows" in path_str or "github" in content.lower():
            result.platform = "github_actions"
        elif "gitlab-ci" in path_str.lower() or "gitlab" in content.lower():
            result.platform = "gitlab_ci"
        elif "bitbucket-pipelines" in path_str.lower():
            result.platform = "bitbucket_pipelines"

        # Python versions
        py_re = re.compile(r"python-version['\"]?\s*:\s*['\"]?([\d.]+)['\"]?")
        result.python_versions = py_re.findall(content)

        # CI env var
        ci_match = _RE_CI_ENV.search(content)
        if ci_match:
            result.ci_flag = ci_match.group(1).strip().lower() in ("true", "1", "yes")
        result.env_vars.update(self._extract_env_vars(content))

        # pytest commands from 'run:' blocks
        for run_block in _RE_RUN_BLOCK.finditer(content):
            block_text = run_block.group(1)
            for cmd_match in _RE_PYTEST_CMD.finditer(block_text):
                cmd = cmd_match.group(0).strip()
                result.pytest_commands.append(cmd)

                k = self._extract_k(cmd)
                if k:
                    result.k_expressions.append(k)

                m = self._extract_m(cmd)
                if m:
                    result.m_expressions.append(m)

                for token in _SKIP_TOKENS.findall(cmd):
                    if token.lower() not in result.skip_signals:
                        result.skip_signals.append(token.lower())

        return result

    def parse_all(self, repo_path: str) -> tuple[PytestConfig, CIWorkflowConfig]:
        """
        Parse both pytest.ini and the first discovered CI workflow in *repo_path*.

        Returns a (PytestConfig, CIWorkflowConfig) tuple.
        """
        root = Path(repo_path)

        # Find pytest.ini or setup.cfg
        pytest_cfg = PytestConfig()
        for candidate in ("pytest.ini", "setup.cfg", "pyproject.toml"):
            ini = root / candidate
            if ini.exists():
                pytest_cfg = self.parse_pytest_ini(str(ini))
                break

        # Find CI workflow — try common locations
        workflow_cfg = CIWorkflowConfig()
        workflow_candidates = list((root / ".github" / "workflows").glob("*.yml"))
        workflow_candidates += list((root / ".github" / "workflows").glob("*.yaml"))
        if workflow_candidates:
            workflow_cfg = self.parse_workflow_yaml(str(workflow_candidates[0]))

        return pytest_cfg, workflow_cfg

    def get_skip_marker_names(self, pytest_cfg: PytestConfig) -> List[str]:
        """
        Return all marker names that are related to skipping / quarantining tests.
        Includes explicitly detected skip_markers plus any -m expression tokens.
        """
        names: List[str] = list(pytest_cfg.skip_markers)
        if pytest_cfg.m_expression:
            # e.g. "not (quarantine or slow)"  → extract individual tokens
            tokens = re.findall(r"\b\w+\b", pytest_cfg.m_expression)
            for t in tokens:
                if t.lower() not in ("not", "and", "or") and t not in names:
                    names.append(t)
        return names

    # ── Legacy compatibility ───────────────────────────────────────────────────

    def parse_github_actions(self, log_content: str, run_id: str):
        """
        Parse GitHub Actions test log output.
        Legacy method — parses pytest stdout (PASSED/FAILED lines).
        Kept for backward compatibility.
        """
        from backend.models.detection import TestRun, TestExecution, TestStatus
        import uuid

        executions = []
        pytest_pattern = r"(\S+\.py::\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)"
        for test_name, status in re.findall(pytest_pattern, log_content):
            status_map = {
                "PASSED": TestStatus.PASSED,
                "FAILED": TestStatus.FAILED,
                "SKIPPED": TestStatus.SKIPPED,
                "ERROR": TestStatus.ERROR,
            }
            executions.append(TestExecution(
                test_name=test_name,
                file_path=test_name.split("::")[0],
                status=status_map.get(status, TestStatus.ERROR),
                duration=0.0,
            ))

        return TestRun(
            run_id=run_id,
            repository="unknown",
            branch=self._extract_branch(log_content),
            commit_sha=self._extract_commit(log_content),
            executions=executions,
            total_tests=len(executions),
            passed=sum(1 for e in executions if e.status == TestStatus.PASSED),
            failed=sum(1 for e in executions if e.status == TestStatus.FAILED),
        )

    def parse_junit_xml(self, xml_path: str, run_id: str):
        """Parse JUnit XML test results. Legacy method kept for compatibility."""
        import xml.etree.ElementTree as ET
        from backend.models.detection import TestRun, TestExecution, TestStatus

        tree = ET.parse(xml_path)
        root = tree.getroot()
        executions = []

        for testcase in root.iter("testcase"):
            classname = testcase.get("classname", "")
            name = testcase.get("name", "")
            time = float(testcase.get("time", 0))
            status = TestStatus.PASSED
            error_msg = None

            if testcase.find("failure") is not None:
                status = TestStatus.FAILED
                error_msg = testcase.find("failure").get("message", "")
            elif testcase.find("error") is not None:
                status = TestStatus.ERROR
                error_msg = testcase.find("error").get("message", "")
            elif testcase.find("skipped") is not None:
                status = TestStatus.SKIPPED

            test_name = f"{classname}::{name}" if classname else name
            executions.append(TestExecution(
                test_name=test_name,
                file_path=classname.replace(".", "/") + ".py",
                status=status,
                duration=time,
                error_message=error_msg,
            ))

        return TestRun(
            run_id=run_id,
            repository="unknown",
            branch="unknown",
            commit_sha="unknown",
            executions=executions,
            total_tests=len(executions),
            passed=sum(1 for e in executions if e.status == TestStatus.PASSED),
            failed=sum(1 for e in executions if e.status == TestStatus.FAILED),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_pytest_ini_manual(self, content: str) -> PytestConfig:
        """Fallback: manually scan ini content when configparser fails."""
        result = PytestConfig()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("addopts"):
                _, _, val = line.partition("=")
                result.addopts = val.strip()
                result.k_expression = self._extract_k(result.addopts)
                result.m_expression = self._extract_m(result.addopts)
            elif line.startswith("testpaths"):
                _, _, val = line.partition("=")
                result.testpaths = val.strip().split()
        return result

    @staticmethod
    def _extract_k(text: str) -> Optional[str]:
        m = _RE_K_EXPR.search(text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_m(text: str) -> Optional[str]:
        m = _RE_M_EXPR.search(text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_env_vars(content: str) -> Dict[str, str]:
        """Extract simple key: value env-var entries from a workflow file."""
        result: Dict[str, str] = {}
        env_block_re = re.compile(r"env:\s*\n((?:[ \t]+\w+\s*:.+\n?)+)", re.MULTILINE)
        kv_re = re.compile(r"[ \t]+(?P<key>\w+)\s*:\s*(?P<val>.+)")
        for block in env_block_re.finditer(content):
            for kv in kv_re.finditer(block.group(1)):
                result[kv.group("key")] = kv.group("val").strip()
        return result

    @staticmethod
    def _extract_branch(log_content: str) -> str:
        m = re.search(r"ref:\s*refs/heads/(\S+)", log_content)
        return m.group(1) if m else "unknown"

    @staticmethod
    def _extract_commit(log_content: str) -> str:
        m = re.search(r"commit\s+([a-f0-9]{40})", log_content)
        return m.group(1) if m else "unknown"
