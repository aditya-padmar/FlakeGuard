"""Tests for GitHub cloning, file uploading, and repository integration."""
import io
import zipfile
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.harness.git_service import GitService
from backend.harness.pipeline_service import PipelineService


def test_parse_github_url_valid():
    """Verify various GitHub URL formats parse correctly."""
    valid_urls = [
        ("https://github.com/aditya-padmar/FlakeGuard", ("aditya-padmar", "FlakeGuard")),
        ("https://github.com/torvalds/linux.git", ("torvalds", "linux")),
        ("github.com/owner/my-repo", ("owner", "my-repo")),
        ("http://github.com/org/repo-name/", ("org", "repo-name")),
    ]
    for url, expected in valid_urls:
        res = GitService.parse_github_url(url)
        assert res == expected, f"Failed for {url}"


def test_parse_github_url_invalid():
    """Verify invalid URLs return None."""
    invalid_urls = [
        "https://gitlab.com/owner/repo",
        "https://notgithub.com/owner/repo",
        "random-string",
        "",
    ]
    for url in invalid_urls:
        assert GitService.parse_github_url(url) is None


def test_handle_archive_upload_single_py():
    """Verify single python test file upload wraps into workspace."""
    sample_code = b"""
import time
def test_sample_flake():
    time.sleep(0.01)
    assert True
"""
    result = GitService.handle_archive_upload(sample_code, "test_foo.py")
    assert "workspace_path" in result
    workspace = Path(result["workspace_path"])
    assert workspace.exists()
    assert (workspace / "pytest.ini").exists()
    assert (workspace / "tests" / "test_foo.py").exists()
    assert result["test_files_count"] >= 1


def test_handle_archive_upload_zip():
    """Verify zip archive upload unpacks cleanly."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("test_archive.py", "def test_in_zip(): assert True")
        z.writestr("README.md", "# Test Zip")
    zip_bytes = buf.getvalue()

    result = GitService.handle_archive_upload(zip_bytes, "project.zip")
    assert "workspace_path" in result
    workspace = Path(result["workspace_path"])
    assert workspace.exists()
    assert (workspace / "test_archive.py").exists()


@pytest.mark.asyncio
async def test_api_repository_sources():
    """Verify /api/repository/sources returns preloaded sources."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/repository/sources")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert any(s["id"] == "sample-repo" for s in data["sources"])


@pytest.mark.asyncio
async def test_api_analyze_local_sample_repo():
    """Verify /api/repository/analyze-local runs pipeline on sample-repo."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/repository/analyze-local",
            json={"repo_path": "sample-repo", "num_runs": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_type"] == "local"
        assert "detection" in data
        assert "classifications" in data
        assert "fixes" in data
        assert "quarantine_audit" in data
        assert "metrics" in data


@pytest.mark.asyncio
async def test_api_upload_and_analyze():
    """Verify /api/repository/upload processes uploaded test file and analyzes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_content = b"""
import time

def test_timing_flake():
    start = time.time()
    time.sleep(0.02)
    elapsed = time.time() - start
    assert elapsed < 0.001
"""
        files = {"file": ("test_timing.py", test_content, "text/x-python")}
        data = {"num_runs": "2"}
        response = await client.post(
            "/api/repository/upload",
            files=files,
            data=data
        )
        assert response.status_code == 200
        result = response.json()
        assert result["source_type"] == "upload"
        assert "detection" in result
        assert "metrics" in result
