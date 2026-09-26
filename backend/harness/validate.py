"""Repository validation and compatibility detection for FlakeGuard."""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from backend.harness.framework_detector import detect_framework

logger = logging.getLogger(__name__)


class RepositoryValidator:
    """Validates if a repository is compatible with FlakeGuard analysis."""

    @staticmethod
    def detect_pytest_compatibility(repo_path: Path) -> Dict:
        """
        Backwards-compatible entry point — now delegates to the universal
        framework detector so any supported language passes validation.

        Returns a dict shaped like the old pytest-only result so callers
        that still reference 'compatible' / 'confidence' keep working.
        """
        info = detect_framework(Path(repo_path).resolve())
        compatible = info["confidence"] >= 0.3
        warnings: List[str] = []
        if not compatible:
            supported = (
                "Python/pytest, JavaScript/Jest, JavaScript/Vitest, "
                "Go, Java/Maven, Java/Gradle, Ruby/RSpec"
            )
            warnings.append(
                f"No recognised test framework detected "
                f"(confidence {info['confidence']:.0%}). "
                f"Supported frameworks: {supported}."
            )
        return {
            "compatible": compatible,
            "confidence": info["confidence"],
            "indicators": info["indicators"],
            "warnings": warnings,
            "test_files": info["test_files"],
            "config_files": info.get("config_files", []),
            "framework": info["framework"],
            "language": info["language"],
        }

    @classmethod
    def detect_repository_compatibility(cls, repo_path: Path) -> Dict[str, Any]:
        """
        Polyglot repository detector supporting any programming language.
        Detects Python (pytest), C/C++ (CMake/ESP-IDF/Make), JavaScript/TypeScript (Jest/Vitest),
        Go (go test), Java (Maven/Gradle), Rust (Cargo), and generic source code.
        """
        repo_path = Path(repo_path).resolve()
        if not repo_path.is_dir():
            return {
                "compatible": False,
                "primary_language": "unknown",
                "framework": "unknown",
                "mode": "static_audit",
                "confidence": 0.0,
                "indicators": [],
                "warnings": [f"Repository path is not a directory: {repo_path}"],
                "test_files": [],
                "config_files": [],
            }

        # The compatibility entry point now detects multiple frameworks. Preserve
        # its identity; a Jest/Go/Java project must never be relabelled as pytest.
        framework_result = cls.detect_pytest_compatibility(repo_path)
        if framework_result.get("compatible"):
            return {
                **framework_result,
                "primary_language": framework_result["language"],
                "mode": "dynamic" if framework_result["framework"] == "pytest" else "static_audit",
            }

        # 2. Check polyglot indicators
        result = {
            "compatible": False,
            "primary_language": "unknown",
            "framework": "unknown",
            "mode": "static_audit",
            "confidence": 0.0,
            "indicators": [],
            "warnings": [],
            "test_files": [],
            "config_files": []
        }

        if not repo_path.exists() or not repo_path.is_dir():
            result["warnings"].append(f"Repository path does not exist: {repo_path}")
            return result

        ignore_dirs = {".git", ".venv", "venv", "env", "node_modules", ".pytest_cache", "__pycache__", "build", "dist", "target", "vendor"}
        # Scan once and prune before descending. Applying ignores after globbing
        # still traverses dependencies and repeated extensions multiply that cost.
        files_by_extension: Dict[str, List[Path]] = {}
        for directory, subdirs, filenames in os.walk(repo_path, followlinks=False):
            subdirs[:] = sorted(
                name for name in subdirs
                if name not in ignore_dirs and not name.startswith(".")
            )
            for name in sorted(filenames):
                if name.startswith("."):
                    continue
                path = Path(directory) / name
                matches = files_by_extension.setdefault(path.suffix.lower(), [])
                if len(matches) < 20:
                    matches.append(path)

        def find_files(exts: List[str], max_count: int = 20) -> List[Path]:
            return [path for ext in exts for path in files_by_extension.get(ext, [])][:max_count]

        # C / C++ / Embedded (ESP32, CMake, Arduino, Make)
        c_configs = ["CMakeLists.txt", "Makefile", "sdkconfig", "platformio.ini", "sdkconfig.defaults"]
        c_found_configs = [c for c in c_configs if (repo_path / c).exists()]
        c_files = find_files([".c", ".cpp", ".cc", ".h", ".hpp"])
        if c_found_configs or c_files:
            is_embedded = any("sdkconfig" in c or "esp" in (repo_path / c).read_text(errors="ignore").lower() for c in c_found_configs if (repo_path / c).exists())
            result["compatible"] = True
            result["primary_language"] = "c/c++"
            result["framework"] = "cmake/esp-idf" if is_embedded else ("cmake" if "CMakeLists.txt" in c_found_configs else "make/c")
            result["mode"] = "static_audit"
            result["confidence"] = 0.9 if c_found_configs else 0.7
            result["indicators"].extend([f"Found {c}" for c in c_found_configs])
            if is_embedded:
                result["indicators"].append("Detected ESP32 / embedded firmware configuration")
            result["indicators"].append(f"Found {len(c_files)} C/C++ source files")
            result["config_files"] = [str(repo_path / c) for c in c_found_configs]
            result["test_files"] = [str(f.relative_to(repo_path)) for f in c_files[:10]]
            return result

        # JavaScript / TypeScript (Node.js, Jest, Vitest, Mocha)
        js_configs = ["package.json", "tsconfig.json", "jest.config.js", "vitest.config.ts", "package-lock.json"]
        js_found_configs = [c for c in js_configs if (repo_path / c).exists()]
        js_files = find_files([".js", ".jsx", ".ts", ".tsx", ".mjs"])
        if js_found_configs or js_files:
            result["compatible"] = True
            result["primary_language"] = "javascript/typescript"
            result["framework"] = "jest/vitest" if "package.json" in js_found_configs else "node"
            result["mode"] = "dynamic" if "package.json" in js_found_configs else "static_audit"
            result["confidence"] = 0.85 if js_found_configs else 0.65
            result["indicators"].extend([f"Found {c}" for c in js_found_configs])
            result["indicators"].append(f"Found {len(js_files)} JS/TS source files")
            result["config_files"] = [str(repo_path / c) for c in js_found_configs]
            result["test_files"] = [str(f.relative_to(repo_path)) for f in js_files[:10]]
            return result

        # Go
        go_configs = ["go.mod", "go.sum"]
        go_found_configs = [c for c in go_configs if (repo_path / c).exists()]
        go_files = find_files([".go"])
        if go_found_configs or go_files:
            result["compatible"] = True
            result["primary_language"] = "go"
            result["framework"] = "go_test"
            result["mode"] = "static_audit"
            result["confidence"] = 0.85 if go_found_configs else 0.6
            result["indicators"].extend([f"Found {c}" for c in go_found_configs])
            result["indicators"].append(f"Found {len(go_files)} Go source files")
            result["config_files"] = [str(repo_path / c) for c in go_found_configs]
            result["test_files"] = [str(f.relative_to(repo_path)) for f in go_files[:10]]
            return result

        # Java / Kotlin
        java_configs = ["pom.xml", "build.gradle", "build.gradle.kts"]
        java_found_configs = [c for c in java_configs if (repo_path / c).exists()]
        java_files = find_files([".java", ".kt"])
        if java_found_configs or java_files:
            result["compatible"] = True
            result["primary_language"] = "java"
            result["framework"] = "junit/maven" if "pom.xml" in java_found_configs else "junit/gradle"
            result["mode"] = "static_audit"
            result["confidence"] = 0.85 if java_found_configs else 0.6
            result["indicators"].extend([f"Found {c}" for c in java_found_configs])
            result["indicators"].append(f"Found {len(java_files)} Java/Kotlin source files")
            result["config_files"] = [str(repo_path / c) for c in java_found_configs]
            result["test_files"] = [str(f.relative_to(repo_path)) for f in java_files[:10]]
            return result

        # Rust
        if (repo_path / "Cargo.toml").exists() or find_files([".rs"]):
            rs_files = find_files([".rs"])
            result["compatible"] = True
            result["primary_language"] = "rust"
            result["framework"] = "cargo_test"
            result["mode"] = "static_audit"
            result["confidence"] = 0.8
            result["indicators"].append("Found Rust repository")
            result["test_files"] = [str(f.relative_to(repo_path)) for f in rs_files[:10]]
            return result

        # Python without standard pytest indicators (fallback)
        py_files = find_files([".py"])
        if py_files:
            result["compatible"] = True
            result["primary_language"] = "python"
            result["framework"] = "python_unittest"
            result["mode"] = "static_audit"
            result["confidence"] = 0.6
            result["indicators"].append(f"Found {len(py_files)} Python source files")
            result["test_files"] = [str(f.relative_to(repo_path)) for f in py_files[:10]]
            return result

        # If repo is empty or has no code files
        result["warnings"].append("No recognizable programming language files or build manifests found in repository.")
        return result

    @staticmethod
    def check_python_environment(repo_path: Path) -> Dict:
        """Check for Python environment indicators in the repository."""
        result: Dict = {
            "has_python": False,
            "python_files": [],
            "virtualenv": None,
            "warnings": [],
        }
        repo_path = Path(repo_path).resolve()
        ignored = {"venv", "env", "node_modules", "__pycache__", "build", "dist", "target", "vendor"}
        for directory, subdirs, filenames in os.walk(repo_path, followlinks=False):
            subdirs[:] = [name for name in subdirs if name not in ignored and not name.startswith(".")]
            for name in filenames:
                if name.endswith(".py") and not name.startswith("."):
                    result["python_files"].append(str((Path(directory) / name).relative_to(repo_path)))
                    if len(result["python_files"]) >= 5:
                        break
            if len(result["python_files"]) >= 5:
                break
        result["has_python"] = bool(result["python_files"])
        for venv_name in (".venv", "venv", "env", ".env"):
            if (repo_path / venv_name).is_dir():
                result["virtualenv"] = venv_name
                result["warnings"].append(
                    f"Virtual environment detected at {venv_name}/. "
                    "FlakeGuard uses its own environment."
                )
                break
        return result
