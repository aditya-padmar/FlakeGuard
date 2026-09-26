"""Repository validation and compatibility detection for FlakeGuard."""
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RepositoryValidator:
    """Validates if a repository is compatible with FlakeGuard analysis."""

    @staticmethod
    def detect_pytest_compatibility(repo_path: Path) -> Dict[str, any]:
        """
        Detect if a repository appears to be pytest-compatible.
        
        Returns:
            Dict with:
                - compatible: bool
                - confidence: float (0.0-1.0)
                - indicators: List[str] of detected pytest indicators
                - warnings: List[str] of potential issues
                - test_files: List[Path] of discovered test files
        """
        repo_path = Path(repo_path).resolve()
        
        result = {
            "compatible": False,
            "confidence": 0.0,
            "indicators": [],
            "warnings": [],
            "test_files": [],
            "config_files": []
        }

        if not repo_path.exists() or not repo_path.is_dir():
            result["warnings"].append(f"Repository path does not exist: {repo_path}")
            return result

        # Check for pytest configuration files
        config_indicators = {
            "pytest.ini": 0.8,
            "pyproject.toml": 0.4,
            "setup.cfg": 0.3,
            "tox.ini": 0.2
        }
        
        for config_file, weight in config_indicators.items():
            config_path = repo_path / config_file
            if config_path.exists():
                result["indicators"].append(f"Found {config_file}")
                result["config_files"].append(str(config_path))
                result["confidence"] += weight
                
                # Check for pytest-specific content
                if config_file in ["pytest.ini", "pyproject.toml", "setup.cfg"]:
                    try:
                        content = config_path.read_text(encoding="utf-8")
                        if "pytest" in content.lower():
                            result["confidence"] += 0.1
                    except Exception as e:
                        logger.debug(f"Could not read {config_file}: {e}")

        # Check for test directories
        test_dirs = ["tests", "test", "testing"]
        for test_dir in test_dirs:
            test_path = repo_path / test_dir
            if test_path.exists() and test_path.is_dir():
                result["indicators"].append(f"Found {test_dir}/ directory")
                result["confidence"] += 0.3
                break

        # Search for test files
        test_patterns = [
            "test_*.py",
            "*_test.py",
        ]
        
        for pattern in test_patterns:
            test_files = list(repo_path.glob(f"**/{pattern}"))
            if test_files:
                result["test_files"].extend([str(f.relative_to(repo_path)) for f in test_files[:10]])
                result["indicators"].append(f"Found {len(test_files)} files matching {pattern}")
                result["confidence"] += 0.4
                break

        # Check for conftest.py (strong pytest indicator)
        if list(repo_path.glob("**/conftest.py")):
            result["indicators"].append("Found conftest.py")
            result["confidence"] += 0.5

        # Check for requirements files mentioning pytest
        req_files = ["requirements.txt", "requirements-dev.txt", "dev-requirements.txt"]
        for req_file in req_files:
            req_path = repo_path / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text(encoding="utf-8")
                    if "pytest" in content.lower():
                        result["indicators"].append(f"pytest in {req_file}")
                        result["confidence"] += 0.3
                        break
                except Exception as e:
                    logger.debug(f"Could not read {req_file}: {e}")

        # Cap confidence at 1.0
        result["confidence"] = min(result["confidence"], 1.0)
        
        # Determine compatibility
        if result["confidence"] >= 0.5:
            result["compatible"] = True
        elif result["confidence"] > 0:
            result["warnings"].append(
                f"Low confidence ({result['confidence']:.1%}) - "
                "repository may not be pytest-compatible"
            )
        else:
            result["warnings"].append(
                "No pytest indicators found. Repository may not use pytest."
            )

        logger.info(
            f"Repository validation: compatible={result['compatible']}, "
            f"confidence={result['confidence']:.1%}, "
            f"indicators={len(result['indicators'])}"
        )

        return result

    @classmethod
    def detect_repository_compatibility(cls, repo_path: Path) -> Dict[str, any]:
        """
        Polyglot repository detector supporting any programming language.
        Detects Python (pytest), C/C++ (CMake/ESP-IDF/Make), JavaScript/TypeScript (Jest/Vitest),
        Go (go test), Java (Maven/Gradle), Rust (Cargo), and generic source code.
        """
        repo_path = Path(repo_path).resolve()
        
        # 1. First check pytest compatibility
        pytest_result = cls.detect_pytest_compatibility(repo_path)
        if pytest_result.get("compatible"):
            return {
                **pytest_result,
                "primary_language": "python",
                "framework": "pytest",
                "mode": "dynamic"
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

        ignore_dirs = {".git", ".venv", "venv", "node_modules", ".pytest_cache", "__pycache__", "build", "dist"}

        def find_files(exts: List[str], max_count: int = 20) -> List[Path]:
            matched = []
            for ext in exts:
                try:
                    for f in repo_path.glob(f"**/*{ext}"):
                        if f.is_file() and not any(part in ignore_dirs or part.startswith(".") for part in f.parts):
                            matched.append(f)
                            if len(matched) >= max_count:
                                return matched
                except Exception:
                    continue
            return matched

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
    def check_python_environment(repo_path: Path) -> Dict[str, any]:
        """
        Check for Python environment indicators in repository.
        
        Returns:
            Dict with python_version, virtualenv info, etc.
        """
        result = {
            "has_python": False,
            "python_files": [],
            "virtualenv": None,
            "warnings": []
        }

        repo_path = Path(repo_path).resolve()
        
        # Check for Python files
        py_files = list(repo_path.glob("**/*.py"))
        if py_files:
            result["has_python"] = True
            result["python_files"] = [str(f.relative_to(repo_path)) for f in py_files[:5]]

        # Check for virtual environment indicators
        venv_indicators = [".venv", "venv", "env", ".env"]
        for venv_name in venv_indicators:
            venv_path = repo_path / venv_name
            if venv_path.exists() and venv_path.is_dir():
                result["virtualenv"] = str(venv_path)
                result["warnings"].append(
                    f"Virtual environment detected at {venv_name}/. "
                    "FlakeGuard uses its own Python environment."
                )
                break

        return result
