"""Framework auto-detection for multi-language test runner support."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Supported framework identifiers
FRAMEWORK_PYTEST = "pytest"
FRAMEWORK_JEST = "jest"
FRAMEWORK_VITEST = "vitest"
FRAMEWORK_GO = "go"
FRAMEWORK_MAVEN = "maven"
FRAMEWORK_GRADLE = "gradle"
FRAMEWORK_RSPEC = "rspec"
FRAMEWORK_UNKNOWN = "unknown"


def detect_framework(repo_path: Path) -> Dict:
    """
    Inspect a cloned repository and return the best-match test framework.

    Returns a dict:
        framework   : str   — one of the FRAMEWORK_* constants
        confidence  : float — 0.0–1.0
        indicators  : list  — human-readable reasons
        test_files  : list  — up to 10 discovered test file paths (relative)
        run_command : list  — the command to execute tests (list form)
        language    : str   — e.g. "python", "javascript", "go", "java", "ruby"
    """
    repo_path = Path(repo_path).resolve()
    candidates: List[Dict] = []

    candidates.append(_probe_pytest(repo_path))
    candidates.append(_probe_jest_vitest(repo_path))
    candidates.append(_probe_go(repo_path))
    candidates.append(_probe_maven(repo_path))
    candidates.append(_probe_gradle(repo_path))
    candidates.append(_probe_rspec(repo_path))

    # Pick the highest-confidence candidate
    best = max(candidates, key=lambda c: c["confidence"])

    logger.info(
        "Framework detection: %s (confidence=%.0f%%) for %s",
        best["framework"], best["confidence"] * 100, repo_path,
    )
    return best


# ---------------------------------------------------------------------------
# Per-framework probes
# ---------------------------------------------------------------------------

def _probe_pytest(repo: Path) -> Dict:
    score = 0.0
    indicators: List[str] = []
    test_files: List[str] = []

    for name, weight in [("pytest.ini", 0.8), ("pyproject.toml", 0.3), ("setup.cfg", 0.2), ("tox.ini", 0.15)]:
        if (repo / name).exists():
            indicators.append(f"Found {name}")
            score += weight
            if name in ("pytest.ini", "pyproject.toml", "setup.cfg"):
                try:
                    content = (repo / name).read_text(encoding="utf-8", errors="ignore")
                    if "pytest" in content.lower():
                        score += 0.1
                except Exception:
                    pass

    for d in ("tests", "test", "testing"):
        if (repo / d).is_dir():
            indicators.append(f"Found {d}/")
            score += 0.2
            break

    for pat in ("test_*.py", "*_test.py"):
        found = list(repo.glob(f"**/{pat}"))
        if found:
            test_files = [str(f.relative_to(repo)) for f in found[:10]]
            indicators.append(f"Found {len(found)} Python test files")
            score += 0.4
            break

    if list(repo.glob("**/conftest.py")):
        indicators.append("Found conftest.py")
        score += 0.3

    for req in ("requirements.txt", "requirements-dev.txt", "dev-requirements.txt"):
        try:
            content = (repo / req).read_text(encoding="utf-8", errors="ignore")
            if "pytest" in content.lower():
                indicators.append(f"pytest in {req}")
                score += 0.2
                break
        except Exception:
            pass

    return {
        "framework": FRAMEWORK_PYTEST,
        "language": "python",
        "confidence": min(score, 1.0),
        "indicators": indicators,
        "test_files": test_files,
        "run_command": None,  # built dynamically by UniversalRunner
    }


def _probe_jest_vitest(repo: Path) -> Dict:
    score = 0.0
    indicators: List[str] = []
    test_files: List[str] = []
    framework = FRAMEWORK_JEST

    pkg = repo / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            scripts = data.get("scripts", {})
            if "vitest" in deps:
                framework = FRAMEWORK_VITEST
                score += 0.8
                indicators.append("vitest in package.json dependencies")
            elif "jest" in deps or "@jest/core" in deps:
                score += 0.8
                indicators.append("jest in package.json dependencies")
            for s_name, s_val in scripts.items():
                if "vitest" in s_val:
                    framework = FRAMEWORK_VITEST
                    score += 0.1
                    indicators.append(f"vitest in scripts.{s_name}")
                    break
                elif "jest" in s_val:
                    score += 0.1
                    indicators.append(f"jest in scripts.{s_name}")
                    break
        except Exception:
            pass

    for pat in ("**/*.test.ts", "**/*.test.js", "**/*.spec.ts", "**/*.spec.js", "**/*.test.tsx", "**/*.spec.tsx"):
        found = [f for f in repo.glob(pat) if "node_modules" not in f.parts]
        if found:
            test_files = [str(f.relative_to(repo)) for f in found[:10]]
            indicators.append(f"Found {len(found)} JS/TS test files")
            score += 0.3
            break

    if (repo / "jest.config.js").exists() or (repo / "jest.config.ts").exists() or (repo / "jest.config.mjs").exists():
        indicators.append("Found jest.config.*")
        score += 0.3
    if (repo / "vitest.config.ts").exists() or (repo / "vitest.config.js").exists():
        framework = FRAMEWORK_VITEST
        indicators.append("Found vitest.config.*")
        score += 0.4

    return {
        "framework": framework,
        "language": "javascript/typescript",
        "confidence": min(score, 1.0),
        "indicators": indicators,
        "test_files": test_files,
        "run_command": None,
    }


def _probe_go(repo: Path) -> Dict:
    score = 0.0
    indicators: List[str] = []
    test_files: List[str] = []

    if (repo / "go.mod").exists():
        indicators.append("Found go.mod")
        score += 0.6

    found = list(repo.glob("**/*_test.go"))
    if found:
        test_files = [str(f.relative_to(repo)) for f in found[:10]]
        indicators.append(f"Found {len(found)} Go test files (*_test.go)")
        score += 0.5

    return {
        "framework": FRAMEWORK_GO,
        "language": "go",
        "confidence": min(score, 1.0),
        "indicators": indicators,
        "test_files": test_files,
        "run_command": None,
    }


def _probe_maven(repo: Path) -> Dict:
    score = 0.0
    indicators: List[str] = []
    test_files: List[str] = []

    if (repo / "pom.xml").exists():
        indicators.append("Found pom.xml")
        score += 0.7

    found = list(repo.glob("**/src/test/**/*.java"))
    if found:
        test_files = [str(f.relative_to(repo)) for f in found[:10]]
        indicators.append(f"Found {len(found)} Java test files")
        score += 0.4

    return {
        "framework": FRAMEWORK_MAVEN,
        "language": "java",
        "confidence": min(score, 1.0),
        "indicators": indicators,
        "test_files": test_files,
        "run_command": None,
    }


def _probe_gradle(repo: Path) -> Dict:
    score = 0.0
    indicators: List[str] = []
    test_files: List[str] = []

    for f in ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"):
        if (repo / f).exists():
            indicators.append(f"Found {f}")
            score += 0.6
            break

    found = list(repo.glob("**/src/test/**/*.java")) + list(repo.glob("**/src/test/**/*.kt"))
    if found:
        test_files = [str(f.relative_to(repo)) for f in found[:10]]
        indicators.append(f"Found {len(found)} Java/Kotlin test files")
        score += 0.4

    # Prefer Gradle over Maven when both exist
    if (repo / "pom.xml").exists():
        score *= 0.5  # lower if pom.xml also present (Maven wins)

    return {
        "framework": FRAMEWORK_GRADLE,
        "language": "java/kotlin",
        "confidence": min(score, 1.0),
        "indicators": indicators,
        "test_files": test_files,
        "run_command": None,
    }


def _probe_rspec(repo: Path) -> Dict:
    score = 0.0
    indicators: List[str] = []
    test_files: List[str] = []

    if (repo / "Gemfile").exists():
        indicators.append("Found Gemfile")
        score += 0.3
        try:
            content = (repo / "Gemfile").read_text(encoding="utf-8", errors="ignore")
            if "rspec" in content.lower():
                indicators.append("rspec in Gemfile")
                score += 0.4
        except Exception:
            pass

    if (repo / ".rspec").exists():
        indicators.append("Found .rspec")
        score += 0.4

    found = list(repo.glob("spec/**/*_spec.rb"))
    if found:
        test_files = [str(f.relative_to(repo)) for f in found[:10]]
        indicators.append(f"Found {len(found)} RSpec files")
        score += 0.4

    return {
        "framework": FRAMEWORK_RSPEC,
        "language": "ruby",
        "confidence": min(score, 1.0),
        "indicators": indicators,
        "test_files": test_files,
        "run_command": None,
    }
