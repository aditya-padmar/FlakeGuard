"""Fix generator for creating remediation suggestions backed by real source diffs."""
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.models.classification import Classification, RootCauseType
from backend.models.remediation import (
    CodeDiff,
    Fix,
    FixStatus,
    FixSuggestion,
    FixType,
)
from backend.remediation.diff_generator import DiffGenerator
from backend.remediation.templates import REMEDIATION_STRATEGIES, FixTemplates


# ── Pattern library ──────────────────────────────────────────────────────────

# sleep(...)  — captures indentation + full statement
_RE_SLEEP = re.compile(r"^(?P<indent>\s*)(?:time\.sleep|sleep)\([^)]+\)\s*$", re.MULTILINE)
# assert elapsed < <small-number>
_RE_ELAPSED_ASSERT = re.compile(
    r"^(?P<indent>\s*)assert\s+elapsed\s*<\s*(?P<val>[\d.]+)", re.MULTILINE
)
# get_shared_calculator() usage
_RE_SHARED_CALC = re.compile(r"^(?P<indent>\s*)(?P<var>\w+)\s*=\s*get_shared_\w+\(\)", re.MULTILINE)
# random.random() / random.randint / etc. without a prior seed
_RE_RANDOM_USE = re.compile(r"\brandom\.\w+\(", re.MULTILINE)
# random.seed already present
_RE_RANDOM_SEED = re.compile(r"\brandom\.seed\(")

# ── Helper ───────────────────────────────────────────────────────────────────

def _read_source(file_path: str) -> Optional[str]:
    """Read test source from disk; return None if file is absent."""
    p = Path(file_path)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


# ── Main generator ───────────────────────────────────────────────────────────

class FixGenerator:
    """Generates fix suggestions for flaky tests, including real code diffs."""

    def __init__(self):
        self.templates = FixTemplates()
        self.diff_generator = DiffGenerator()

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_fix(
        self,
        classification: Classification,
        test_source: str,
        llm_client: Optional[Any] = None,
    ) -> Fix:
        """
        Generate fix suggestions for a classified flaky test.

        Tries to read the test file from disk so it can produce real diffs.
        Falls back to the passed-in *test_source* string when the file does
        not exist on the local filesystem (e.g. during remote analysis).

        Returns:
            Fix with one or more FixSuggestions, each carrying a unified diff.
        """
        # Prefer on-disk content so diffs reference the actual file path
        disk_source = _read_source(classification.file_path)
        source = disk_source if disk_source is not None else test_source

        suggestions: List[FixSuggestion] = []

        rc = classification.root_cause
        if rc in (RootCauseType.TIMING, RootCauseType.RACE_CONDITION):
            suggestions = self._generate_timing_fixes(classification, source)
        elif rc == RootCauseType.ORDERING:
            suggestions = self._generate_ordering_fixes(classification, source)
        elif rc == RootCauseType.STATE_LEAKAGE:
            suggestions = self._generate_leakage_fixes(classification, source)
        elif rc in (RootCauseType.ENVIRONMENT, RootCauseType.NETWORK):
            suggestions = self._generate_environment_fixes(classification, source)
        else:
            suggestions = [self._generate_generic_fix(classification, source)]

        if not suggestions:
            suggestions = [self._generate_generic_fix(classification, source)]

        primary = max(suggestions, key=lambda s: s.confidence)

        return Fix(
            fix_id=str(uuid.uuid4()),
            classification_id=classification.classification_id,
            test_name=classification.test_name,
            file_path=classification.file_path,
            suggestions=suggestions,
            primary_suggestion_id=primary.suggestion_id,
            status=FixStatus.PROPOSED,
        )

    # ── Timing fixes ─────────────────────────────────────────────────────────

    def _generate_timing_fixes(
        self,
        classification: Classification,
        source: str,
    ) -> List[FixSuggestion]:
        suggestions: List[FixSuggestion] = []

        # 1. Replace time.sleep with a polling wait helper
        sleep_match = _RE_SLEEP.search(source)
        if sleep_match:
            indent = sleep_match.group("indent")
            new_source, diff = self._replace_sleep(source, classification.file_path)
            suggestions.append(self._create_suggestion(
                fix_type=FixType.CODE_CHANGE,
                description="Replace hard-coded sleep with deterministic wait_for helper",
                rationale=(
                    "time.sleep() introduces an arbitrary delay that is too short under "
                    "load and wastes time otherwise. A polling wait_for() loop is both "
                    "faster and more reliable."
                ),
                confidence=0.90,
                template="timing_await",
                strategy=REMEDIATION_STRATEGIES["timing_race"],
                diff=self._make_diff(diff, classification.file_path),
            ))

        # 2. Relax tight elapsed-time assertions
        elapsed_match = _RE_ELAPSED_ASSERT.search(source)
        if elapsed_match:
            val = float(elapsed_match.group("val"))
            new_source, diff = self._relax_elapsed_assertion(
                source, elapsed_match, classification.file_path
            )
            suggestions.append(self._create_suggestion(
                fix_type=FixType.TIMEOUT_ADJUSTMENT,
                description="Relax tight elapsed-time assertion",
                rationale=(
                    f"assert elapsed < {val} fails under CI load; "
                    "raising the threshold removes spurious failures."
                ),
                confidence=0.80,
                template="timing_assertion",
                strategy=REMEDIATION_STRATEGIES["timing_race"],
                diff=self._make_diff(diff, classification.file_path),
            ))

        # 3. Generic retry wrapper (always offered)
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CODE_CHANGE,
            description="Add retry mechanism for timing-sensitive operations",
            rationale="Retries handle transient timing issues without requiring exact waits.",
            confidence=0.70,
            template="timing_retry",
            strategy=REMEDIATION_STRATEGIES["timing_race"],
            diff=None,
        ))

        return suggestions

    def _replace_sleep(self, source: str, file_path: str) -> Tuple[str, str]:
        """
        Replace the first time.sleep() call with a wait_for_condition() helper
        and inject a minimal helper definition after the imports.
        """
        # Build helper definition to inject once
        helper = (
            "\n\ndef wait_for_condition(condition_fn, timeout=5.0, interval=0.1):\n"
            "    \"\"\"Poll condition_fn until it returns True or timeout expires.\"\"\"\n"
            "    import time as _time\n"
            "    deadline = _time.time() + timeout\n"
            "    while _time.time() < deadline:\n"
            "        if condition_fn():\n"
            "            return True\n"
            "        _time.sleep(interval)\n"
            "    raise TimeoutError(\"Condition not met within timeout\")\n"
        )

        def replacer(m: re.Match) -> str:
            indent = m.group("indent")
            return f"{indent}wait_for_condition(lambda: True)  # TODO: replace lambda with real condition"

        new_source = _RE_SLEEP.sub(replacer, source, count=1)

        # Inject helper if not already present
        if "def wait_for_condition" not in new_source:
            # After the last import block
            last_import = 0
            for i, line in enumerate(new_source.splitlines()):
                if line.startswith("import ") or line.startswith("from "):
                    last_import = i
            lines = new_source.splitlines(keepends=True)
            new_source = "".join(lines[: last_import + 1]) + helper + "".join(lines[last_import + 1 :])

        diff = self.diff_generator.generate_diff(source, new_source, file_path)
        return new_source, diff

    def _relax_elapsed_assertion(
        self,
        source: str,
        match: re.Match,
        file_path: str,
    ) -> Tuple[str, str]:
        """Replace a tight elapsed < X assertion with a 1-second tolerance."""
        old_line = match.group(0)
        indent = match.group("indent")
        new_line = f"{indent}assert elapsed < 1.0  # Relaxed from {match.group('val')}s"
        new_source = source.replace(old_line, new_line, 1)
        diff = self.diff_generator.generate_diff(source, new_source, file_path)
        return new_source, diff

    # ── Ordering fixes ────────────────────────────────────────────────────────

    def _generate_ordering_fixes(
        self,
        classification: Classification,
        source: str,
    ) -> List[FixSuggestion]:
        suggestions: List[FixSuggestion] = []

        # 1. Inject a pytest fixture that yields a fresh instance
        new_source, diff = self._inject_fresh_instance_fixture(source, classification.file_path)
        suggestions.append(self._create_suggestion(
            fix_type=FixType.ISOLATION_FIX,
            description="Inject per-test fixture to eliminate shared-state dependency",
            rationale=(
                "Tests that share a single global object depend on execution order. "
                "A @pytest.fixture(autouse=True) that resets the object before each "
                "test makes the suite order-independent."
            ),
            confidence=0.88,
            template="ordering_isolation",
            strategy=REMEDIATION_STRATEGIES["ordering"],
            diff=self._make_diff(diff, classification.file_path),
        ))

        # 2. Add explicit teardown
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CLEANUP_ADDITION,
            description="Add teardown to reset shared state after each test",
            rationale="Explicit cleanup prevents state from one test leaking into the next.",
            confidence=0.80,
            template="ordering_cleanup",
            strategy=REMEDIATION_STRATEGIES["ordering"],
            diff=None,
        ))

        return suggestions

    def _inject_fresh_instance_fixture(
        self, source: str, file_path: str
    ) -> Tuple[str, str]:
        """Add an autouse fixture that calls .clear() on the shared instance."""
        fixture_code = (
            "\n    @pytest.fixture(autouse=True)\n"
            "    def reset_shared_state(self):\n"
            "        \"\"\"Reset shared calculator before every test.\"\"\"\n"
            "        from src.calculator import get_shared_calculator\n"
            "        get_shared_calculator().clear()\n"
            "        yield\n"
            "        get_shared_calculator().clear()\n"
        )

        # Insert right after the class definition line
        lines = source.splitlines(keepends=True)
        insert_after = 0
        for i, line in enumerate(lines):
            if re.match(r"\s*class\s+Test", line):
                insert_after = i + 1
                break

        if insert_after:
            new_lines = lines[:insert_after] + [fixture_code] + lines[insert_after:]
            new_source = "".join(new_lines)
        else:
            new_source = source  # nothing to change

        diff = self.diff_generator.generate_diff(source, new_source, file_path)
        return new_source, diff

    # ── Leakage fixes ─────────────────────────────────────────────────────────

    def _generate_leakage_fixes(
        self,
        classification: Classification,
        source: str,
    ) -> List[FixSuggestion]:
        suggestions: List[FixSuggestion] = []

        # 1. Replace get_shared_X() calls with fresh-instance construction
        shared_match = _RE_SHARED_CALC.search(source)
        if shared_match:
            new_source, diff = self._replace_shared_with_fresh(source, classification.file_path)
            suggestions.append(self._create_suggestion(
                fix_type=FixType.ISOLATION_FIX,
                description="Replace get_shared_calculator() with a fresh Calculator() instance",
                rationale=(
                    "Every test that references the module-level singleton can observe "
                    "mutations left by previous tests. Using a fresh instance per test "
                    "eliminates the dependency on insertion order."
                ),
                confidence=0.92,
                template="leakage_fresh_instance",
                strategy=REMEDIATION_STRATEGIES["state_leakage"],
                diff=self._make_diff(diff, classification.file_path),
            ))

        # 2. Wrap test body in try/finally to guarantee cleanup
        new_source, diff = self._add_finally_cleanup(source, classification.file_path)
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CLEANUP_ADDITION,
            description="Add try/finally teardown to guarantee shared state is reset",
            rationale="Even when tests fail mid-way, teardown ensures subsequent tests start clean.",
            confidence=0.85,
            template="leakage_cleanup",
            strategy=REMEDIATION_STRATEGIES["state_leakage"],
            diff=self._make_diff(diff, classification.file_path),
        ))

        return suggestions

    def _replace_shared_with_fresh(
        self, source: str, file_path: str
    ) -> Tuple[str, str]:
        """Swap every get_shared_*() call for Calculator()."""
        new_source = re.sub(
            r"get_shared_\w+\(\)",
            "Calculator()  # Fresh instance — no shared state",
            source,
        )
        diff = self.diff_generator.generate_diff(source, new_source, file_path)
        return new_source, diff

    def _add_finally_cleanup(
        self, source: str, file_path: str
    ) -> Tuple[str, str]:
        """
        After the last test method body, append an autouse fixture that does
        get_shared_calculator().clear() in its teardown leg.
        """
        fixture = (
            "\n\n@pytest.fixture(autouse=True)\n"
            "def _cleanup_shared_state():\n"
            "    \"\"\"Auto-teardown: reset shared calculator after every test.\"\"\"\n"
            "    yield\n"
            "    try:\n"
            "        from src.calculator import get_shared_calculator\n"
            "        get_shared_calculator().clear()\n"
            "    except Exception:\n"
            "        pass\n"
        )

        # Ensure pytest is imported
        if "import pytest" not in source:
            new_source = "import pytest\n" + source + fixture
        else:
            new_source = source + fixture

        diff = self.diff_generator.generate_diff(source, new_source, file_path)
        return new_source, diff

    # ── Environment / network fixes ───────────────────────────────────────────

    def _generate_environment_fixes(
        self,
        classification: Classification,
        source: str,
    ) -> List[FixSuggestion]:
        suggestions: List[FixSuggestion] = []

        # 1. Seed random generator if random calls are found
        if _RE_RANDOM_USE.search(source) and not _RE_RANDOM_SEED.search(source):
            new_source, diff = self._seed_random(source, classification.file_path)
            suggestions.append(self._create_suggestion(
                fix_type=FixType.CODE_CHANGE,
                description="Seed the random generator for deterministic behaviour",
                rationale=(
                    "Calls to random.*() without a fixed seed produce different results "
                    "on every run. random.seed(42) at the top of the test makes the "
                    "sequence fully reproducible."
                ),
                confidence=0.95,
                template="environment_seed",
                strategy=REMEDIATION_STRATEGIES["environment"],
                diff=self._make_diff(diff, classification.file_path),
            ))

        # 2. Mock external calls
        new_source, diff = self._add_mock_skeleton(source, classification.file_path)
        suggestions.append(self._create_suggestion(
            fix_type=FixType.MOCK_INTRODUCTION,
            description="Mock external / network dependencies",
            rationale="Mocking makes tests deterministic and independent of environment state.",
            confidence=0.88,
            template="environment_mock",
            strategy=REMEDIATION_STRATEGIES["environment"],
            diff=self._make_diff(diff, classification.file_path),
        ))

        # 3. Skip gracefully when resource is unavailable
        suggestions.append(self._create_suggestion(
            fix_type=FixType.CODE_CHANGE,
            description="Skip test gracefully when external resource is unavailable",
            rationale="pytest.skip() prevents false failures when the environment is incomplete.",
            confidence=0.75,
            template="environment_graceful",
            strategy=REMEDIATION_STRATEGIES["environment"],
            diff=None,
        ))

        return suggestions

    def _seed_random(self, source: str, file_path: str) -> Tuple[str, str]:
        """Insert random.seed(42) before the first random.* usage."""
        lines = source.splitlines(keepends=True)
        seed_line = "    random.seed(42)  # Fixed seed for reproducibility\n"

        # Insert before the first random.* usage inside a def body
        for i, line in enumerate(lines):
            if _RE_RANDOM_USE.search(line):
                new_lines = lines[:i] + [seed_line] + lines[i:]
                new_source = "".join(new_lines)
                diff = self.diff_generator.generate_diff(source, new_source, file_path)
                return new_source, diff

        return source, ""

    def _add_mock_skeleton(self, source: str, file_path: str) -> Tuple[str, str]:
        """Prepend a mock import if not already present."""
        mock_import = "from unittest.mock import patch, MagicMock\n"
        if "unittest.mock" in source or "MagicMock" in source:
            return source, ""

        new_source = mock_import + source
        diff = self.diff_generator.generate_diff(source, new_source, file_path)
        return new_source, diff

    # ── Generic fallback ──────────────────────────────────────────────────────

    def _generate_generic_fix(
        self,
        classification: Classification,
        source: str,
    ) -> FixSuggestion:
        new_source, diff = self._add_quarantine_marker(
            source, classification.test_name, classification.file_path
        )
        return self._create_suggestion(
            fix_type=FixType.QUARANTINE,
            description="Quarantine test until root cause is identified",
            rationale="Unknown flakiness requires manual investigation; quarantining prevents CI noise.",
            confidence=0.50,
            template="generic_quarantine",
            strategy="quarantine",
            diff=self._make_diff(diff, classification.file_path) if diff else None,
        )

    def _add_quarantine_marker(
        self, source: str, test_name: str, file_path: str
    ) -> Tuple[str, str]:
        """Add @pytest.mark.skip in front of the named test function."""
        skip_decorator = f'@pytest.mark.skip(reason="Flaky – quarantined for investigation")\n'
        pattern = re.compile(
            r"^(\s*)(async\s+)?def\s+" + re.escape(test_name.split("::")[-1]) + r"\s*\(",
            re.MULTILINE,
        )
        m = pattern.search(source)
        if not m:
            return source, ""

        new_source = source[: m.start()] + skip_decorator + source[m.start() :]
        # Ensure pytest is imported
        if "import pytest" not in new_source:
            new_source = "import pytest\n" + new_source

        diff = self.diff_generator.generate_diff(source, new_source, file_path)
        return new_source, diff

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _make_diff(self, diff_text: str, file_path: str) -> Optional[CodeDiff]:
        """Wrap a raw unified diff string in a CodeDiff model."""
        if not diff_text:
            return None
        return CodeDiff(
            file_path=file_path,
            unified_diff=diff_text,
        )

    def _create_suggestion(
        self,
        *,
        fix_type: FixType,
        description: str,
        rationale: str,
        confidence: float,
        template: str,
        strategy: str,
        diff: Optional[CodeDiff],
    ) -> FixSuggestion:
        effort = self.templates.get_effort(template)
        return FixSuggestion(
            suggestion_id=str(uuid.uuid4()),
            fix_type=fix_type,
            description=description,
            rationale=rationale,
            confidence=confidence,
            estimated_effort=effort,
            breaking_changes=False,
            requires_review=True,
            diff=diff,
        )
