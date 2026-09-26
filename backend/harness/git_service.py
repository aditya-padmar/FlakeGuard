"""Service for Git operations: cloning GitHub repositories, handling file uploads, and PR creation."""
import os
import re
import shutil
import zipfile
import tarfile
import uuid
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import httpx

logger = logging.getLogger(__name__)

# Base storage directories
BASE_DATA_DIR = Path("data")
REPOS_DIR = BASE_DATA_DIR / "repos"
UPLOADS_DIR = BASE_DATA_DIR / "uploads"

REPOS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class GitService:
    """Handles cloning remote repositories and processing uploaded test suites."""

    @staticmethod
    def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
        """
        Extract (owner, repo) from GitHub URL.
        Accepts:
            https://github.com/owner/repo
            https://github.com/owner/repo.git
            github.com/owner/repo
            git@github.com:owner/repo.git
        """
        url = url.strip()
        pattern = r"(?:https?://)?(?:www\.)?github\.com[:/](?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$"
        match = re.match(pattern, url, re.IGNORECASE)
        if match:
            return match.group("owner"), match.group("repo")
        return None

    @classmethod
    def clone_repository(
        cls,
        repo_url: str,
        branch: Optional[str] = None,
        token: Optional[str] = None,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Clone a remote GitHub repository into an isolated sandbox.
        Automatically falls back to default branch (HEAD) if requested branch is not found.
        """
        parsed = cls.parse_github_url(repo_url)
        if not parsed:
            raise ValueError(f"Invalid GitHub repository URL: '{repo_url}'. Expected format: https://github.com/owner/repo")

        owner, repo = parsed
        clone_id = f"{owner}_{repo}_{uuid.uuid4().hex[:8]}"
        destination = REPOS_DIR / clone_id

        # Build authenticated URL if token provided, but sanitize for logs
        if token and token.strip():
            auth_url = f"https://x-access-token:{token.strip()}@github.com/{owner}/{repo}.git"
        else:
            auth_url = f"https://github.com/{owner}/{repo}.git"

        cmd = ["git", "clone", f"--depth={depth}"]
        if branch and branch.strip():
            cmd.extend(["--branch", branch.strip()])
        cmd.extend([auth_url, str(destination)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Smart branch fallback: If branch was specified (e.g. 'main') but does not exist on remote
            # (e.g. repo uses 'master'), retry without --branch to clone the remote's default HEAD branch
            if result.returncode != 0 and branch and ("Remote branch" in result.stderr or "not found" in result.stderr.lower()):
                logger.warning(
                    "Branch '%s' not found for %s/%s. Retrying clone with upstream default branch...",
                    branch, owner, repo
                )
                if destination.exists():
                    shutil.rmtree(destination, ignore_errors=True)
                fallback_cmd = ["git", "clone", f"--depth={depth}", auth_url, str(destination)]
                result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

            if result.returncode != 0:
                sanitized_stderr = result.stderr.replace(token or "", "[REDACTED]") if token else result.stderr
                raise RuntimeError(f"Git clone failed: {sanitized_stderr.strip()}")

            # Extract current commit and branch
            commit_sha = cls._get_commit_sha(destination)
            actual_branch = cls._get_branch(destination)

            # Discover test & source files across any language
            test_files = cls.discover_tests(destination)

            return {
                "clone_id": clone_id,
                "owner": owner,
                "repo": repo,
                "repo_url": f"https://github.com/{owner}/{repo}",
                "workspace_path": str(destination.resolve()),
                "branch": actual_branch,
                "commit_sha": commit_sha,
                "test_files_count": len(test_files),
                "test_files": [str(p.relative_to(destination)) for p in test_files[:20]]
            }

        except subprocess.TimeoutExpired:
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            raise RuntimeError("Repository clone timed out after 120 seconds.")
        except Exception as e:
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            raise

    @classmethod
    def handle_archive_upload(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract uploaded archive (.zip, .tar, .tar.gz) or single code file across any programming language.
        
        Args:
            file_bytes: Raw bytes of the uploaded file
            filename: Original file name
            
        Returns:
            Dictionary with upload metadata and target workspace path
        """
        upload_id = f"upload_{uuid.uuid4().hex[:8]}"
        target_dir = UPLOADS_DIR / upload_id
        target_dir.mkdir(parents=True, exist_ok=True)

        lower_name = filename.lower()
        supported_code_exts = (
            ".py", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
            ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
            ".go", ".java", ".kt", ".rs", ".rb", ".php", ".cs",
            ".sh", ".txt", ".json", ".yaml", ".yml"
        )

        if lower_name.endswith(".zip"):
            zip_path = target_dir / "uploaded.zip"
            zip_path.write_bytes(file_bytes)

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Prevent Zip Slip directory traversal vulnerability
                    for member in zip_ref.namelist():
                        resolved = (target_dir / member).resolve()
                        if not str(resolved).startswith(str(target_dir.resolve())):
                            raise ValueError(f"Malicious zip entry detected: {member}")
                    zip_ref.extractall(target_dir)

                zip_path.unlink()

                # If zip contains a single top-level directory (e.g. repo-master/), use that as workspace
                entries = [e for e in target_dir.iterdir() if e.is_dir() and not e.name.startswith(".")]
                loose_files = [f for f in target_dir.iterdir() if f.is_file()]
                if len(entries) == 1 and not loose_files:
                    workspace = entries[0]
                else:
                    workspace = target_dir

            except zipfile.BadZipFile:
                shutil.rmtree(target_dir, ignore_errors=True)
                raise ValueError("Uploaded file is not a valid zip archive.")

        elif lower_name.endswith((".tar", ".tar.gz", ".tgz")):
            tar_path = target_dir / "uploaded.tar.gz"
            tar_path.write_bytes(file_bytes)

            try:
                with tarfile.open(tar_path, "r:*") as tar_ref:
                    for member in tar_ref.getmembers():
                        resolved = (target_dir / member.name).resolve()
                        if not str(resolved).startswith(str(target_dir.resolve())):
                            raise ValueError(f"Malicious tar entry detected: {member.name}")
                    tar_ref.extractall(target_dir)

                tar_path.unlink()

                entries = [e for e in target_dir.iterdir() if e.is_dir() and not e.name.startswith(".")]
                loose_files = [f for f in target_dir.iterdir() if f.is_file()]
                if len(entries) == 1 and not loose_files:
                    workspace = entries[0]
                else:
                    workspace = target_dir

            except Exception as e:
                shutil.rmtree(target_dir, ignore_errors=True)
                raise ValueError(f"Failed to extract tar archive: {e}")

        elif any(lower_name.endswith(ext) for ext in supported_code_exts):
            test_file = target_dir / filename
            test_file.write_bytes(file_bytes)

            if lower_name.endswith(".py"):
                ini_file = target_dir / "pytest.ini"
                ini_file.write_text(
                    "[pytest]\npythonpath = .\ntestpaths = .\nasyncio_mode = auto\n",
                    encoding="utf-8"
                )
            workspace = target_dir
        else:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise ValueError(
                f"Unsupported file format: '{filename}'. "
                f"FlakeGuard supports archives (.zip, .tar.gz) and source files ({', '.join(supported_code_exts[:10])}, ...)."
            )

        test_files = cls.discover_tests(workspace)

        return {
            "upload_id": upload_id,
            "filename": filename,
            "workspace_path": str(workspace.resolve()),
            "test_files_count": len(test_files),
            "test_files": [str(p.relative_to(workspace)) for p in test_files[:20]]
        }

    @staticmethod
    def discover_tests(directory: Path) -> List[Path]:
        """Find test files or primary source files in directory across any language."""
        test_patterns = [
            # Python
            "**/test_*.py", "**/*_test.py", "**/tests/**/*.py",
            # JavaScript / TypeScript
            "**/*.test.js", "**/*.test.ts", "**/*.test.jsx", "**/*.test.tsx",
            "**/*.spec.js", "**/*.spec.ts", "**/*.spec.jsx", "**/*.spec.tsx",
            "**/__tests__/**/*.js", "**/__tests__/**/*.ts",
            # Go
            "**/*_test.go",
            # Java / Kotlin
            "**/*Test.java", "**/*Tests.java", "**/*TestCase.java", "**/*Test.kt",
            # C / C++
            "**/test_*.c", "**/test_*.cpp", "**/*_test.c", "**/*_test.cpp",
            "**/test*.c", "**/test*.cpp", "**/tests/**/*.c", "**/tests/**/*.cpp",
            # Rust
            "**/tests/**/*.rs", "**/*_test.rs"
        ]
        found = set()
        ignore_dirs = {".git", ".venv", "venv", "node_modules", ".pytest_cache", "__pycache__", "build", "dist", ".vscode"}

        for pat in test_patterns:
            try:
                for p in directory.glob(pat):
                    if p.is_file() and not any(part in ignore_dirs or part.startswith(".") for part in p.parts):
                        found.add(p)
            except Exception:
                continue

        # If no explicit test files were discovered, fall back to discovering primary code files
        if not found:
            code_patterns = [
                "**/*.c", "**/*.cpp", "**/*.cc", "**/*.h", "**/*.hpp",
                "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",
                "**/*.py", "**/*.go", "**/*.java", "**/*.rs"
            ]
            for pat in code_patterns:
                try:
                    for p in directory.glob(pat):
                        if p.is_file() and not any(part in ignore_dirs or part.startswith(".") for part in p.parts):
                            found.add(p)
                except Exception:
                    continue

        return sorted(list(found))

    @staticmethod
    def _get_commit_sha(repo_path: Path) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return res.stdout.strip() or "HEAD"
        except Exception:
            return "unknown"

    @staticmethod
    def _get_branch(repo_path: Path) -> str:
        try:
            res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return res.stdout.strip() or "main"
        except Exception:
            return "main"

    @classmethod
    async def create_github_pr(
        cls,
        repo_url: str,
        token: str,
        pr_title: str,
        pr_body: str,
        file_path: str,
        new_content: str,
        branch_name: Optional[str] = None,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a new branch and open a Pull Request with the remediation fix on GitHub.
        
        Args:
            repo_url: GitHub repository URL
            token: GitHub Personal Access Token (requires 'repo' or 'contents:write, pull_requests:write' scope)
            pr_title: Title for the Pull Request
            pr_body: Markdown description of the fix
            file_path: Relative path of the file being patched
            new_content: Full text of the patched file
            branch_name: Optional name for new branch (default: flakeguard/fix-<short_uuid>)
            base_branch: Target base branch (default: main)
        """
        parsed = cls.parse_github_url(repo_url)
        if not parsed:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        owner, repo = parsed

        headers = {
            "Authorization": f"Bearer {token.strip()}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        branch = branch_name or f"flakeguard/fix-{uuid.uuid4().hex[:6]}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Get base branch commit SHA
            ref_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{base_branch}",
                headers=headers
            )
            if ref_resp.status_code != 200:
                # Try master if main failed
                if base_branch == "main":
                    ref_resp = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/master",
                        headers=headers
                    )
                    if ref_resp.status_code == 200:
                        base_branch = "master"

            if ref_resp.status_code != 200:
                raise RuntimeError(f"Could not find base branch '{base_branch}' in {owner}/{repo}: {ref_resp.text}")

            base_sha = ref_resp.json()["object"]["sha"]

            # 2. Create new branch
            create_branch_resp = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/git/refs",
                headers=headers,
                json={
                    "ref": f"refs/heads/{branch}",
                    "sha": base_sha
                }
            )
            if create_branch_resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to create branch '{branch}': {create_branch_resp.text}")

            # 3. Get existing file SHA if present
            clean_file_path = file_path.replace("\\", "/").lstrip("/")
            existing_file_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{clean_file_path}?ref={branch}",
                headers=headers
            )
            file_sha = None
            if existing_file_resp.status_code == 200:
                file_sha = existing_file_resp.json().get("sha")

            # 4. Commit updated file
            import base64
            encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            commit_payload: Dict[str, Any] = {
                "message": f"fix(flakeguard): remediate flakiness in {clean_file_path}",
                "content": encoded_content,
                "branch": branch
            }
            if file_sha:
                commit_payload["sha"] = file_sha

            commit_resp = await client.put(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{clean_file_path}",
                headers=headers,
                json=commit_payload
            )
            if commit_resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to commit file '{clean_file_path}': {commit_resp.text}")

            # 5. Open Pull Request
            pr_resp = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                headers=headers,
                json={
                    "title": pr_title,
                    "body": pr_body,
                    "head": branch,
                    "base": base_branch
                }
            )
            if pr_resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to open Pull Request: {pr_resp.text}")

            pr_data = pr_resp.json()
            return {
                "pr_number": pr_data.get("number"),
                "pr_url": pr_data.get("html_url"),
                "branch": branch,
                "base_branch": base_branch,
                "title": pr_title,
                "state": pr_data.get("state", "open")
            }
