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
