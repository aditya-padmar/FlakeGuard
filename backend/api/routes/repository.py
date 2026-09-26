"""Repository and upload integration API routes for FlakeGuard."""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from backend.harness.git_service import GitService
from backend.harness.pipeline_service import PipelineService

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache of recent pipeline runs
_latest_analysis: Optional[Dict[str, Any]] = None
_analysis_history: List[Dict[str, Any]] = []


class CloneRequest(BaseModel):
    """Request payload to clone and analyze a GitHub repository."""
    repo_url: str = Field(..., description="GitHub repository URL (e.g. https://github.com/owner/repo)")
    branch: Optional[str] = Field(None, description="Optional Git branch or tag to analyze")
    token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token")
    num_runs: int = Field(default=5, ge=2, le=20, description="Number of test iterations for flake detection")
    test_pattern: Optional[str] = Field(None, description="Optional pytest -k pattern filter")


class LocalAnalyzeRequest(BaseModel):
    """Request payload to analyze an existing local directory."""
    repo_path: str = Field(default="sample-repo", description="Relative or absolute path to local repository")
    num_runs: int = Field(default=5, ge=2, le=20, description="Number of test iterations")
    test_pattern: Optional[str] = Field(None, description="Optional pytest -k pattern filter")


class CreatePRRequest(BaseModel):
    """Request payload to open a Pull Request with remediation diffs on GitHub."""
    repo_url: str = Field(..., description="GitHub repository URL")
    token: str = Field(..., description="GitHub Personal Access Token with repo/content write permissions")
    file_path: str = Field(..., description="File path relative to repository root")
    new_content: str = Field(..., description="Patched code content")
    title: str = Field(default="fix(flakeguard): auto-remediate flaky test", description="PR title")
    body: str = Field(..., description="PR description markdown")
    branch_name: Optional[str] = Field(None, description="Custom branch name")
    base_branch: str = Field(default="main", description="Target base branch")


@router.post("/clone-and-analyze")
async def clone_and_analyze(request: CloneRequest):
    """
    Clone a remote GitHub repository and run the end-to-end FlakeGuard pipeline.
    """
    global _latest_analysis
    try:
        # 1. Clone repository
        clone_result = GitService.clone_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            token=request.token
        )
        workspace = Path(clone_result["workspace_path"])

        # 2. Run FlakeGuard pipeline
        pipeline_result = await PipelineService.run_pipeline(
            repo_path=workspace,
            num_runs=request.num_runs,
            test_pattern=request.test_pattern,
            source_type="github",
            repo_url=clone_result["repo_url"],
            branch=clone_result["branch"],
            commit_sha=clone_result["commit_sha"]
        )

        pipeline_result["github_metadata"] = {
            "owner": clone_result["owner"],
            "repo": clone_result["repo"],
            "clone_id": clone_result["clone_id"],
            "test_files_count": clone_result["test_files_count"],
            "test_files": clone_result["test_files"]
        }

        _latest_analysis = pipeline_result
        _analysis_history.insert(0, pipeline_result)
        return pipeline_result

    except Exception as e:
        logger.exception("GitHub clone and analysis failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    num_runs: int = Form(5),
    test_pattern: Optional[str] = Form(None)
):
    """
    Upload a repository archive (.zip) or single test file (.py) and run analysis.
    """
    global _latest_analysis
    try:
        contents = await file.read()
        upload_result = GitService.handle_archive_upload(
            file_bytes=contents,
            filename=file.filename or "uploaded.zip"
        )
        workspace = Path(upload_result["workspace_path"])

        pipeline_result = await PipelineService.run_pipeline(
            repo_path=workspace,
            num_runs=num_runs,
            test_pattern=test_pattern,
            source_type="upload",
            repo_url=f"upload://{file.filename}"
        )

        pipeline_result["upload_metadata"] = {
            "upload_id": upload_result["upload_id"],
            "filename": file.filename,
            "test_files_count": upload_result["test_files_count"],
            "test_files": upload_result["test_files"]
        }

        _latest_analysis = pipeline_result
        _analysis_history.insert(0, pipeline_result)
        return pipeline_result

    except Exception as e:
        logger.exception("Upload analysis failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze-local")
async def analyze_local(request: LocalAnalyzeRequest):
    """
    Run FlakeGuard pipeline on a local repository or sample-repo path.
    """
    global _latest_analysis
    try:
        repo_path = Path(request.repo_path)
        if not repo_path.is_absolute():
            # Check relative to project root
            repo_path = Path(request.repo_path).resolve()

        if not repo_path.exists():
            raise FileNotFoundError(f"Path does not exist: {request.repo_path}")

        pipeline_result = await PipelineService.run_pipeline(
            repo_path=repo_path,
            num_runs=request.num_runs,
            test_pattern=request.test_pattern,
            source_type="local"
        )

        _latest_analysis = pipeline_result
        _analysis_history.insert(0, pipeline_result)
        return pipeline_result

    except Exception as e:
        logger.exception("Local repository analysis failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-pr")
async def create_pull_request(request: CreatePRRequest):
    """
    Open a Pull Request on GitHub with the remediation diff.
    """
    try:
        pr_result = await GitService.create_github_pr(
            repo_url=request.repo_url,
            token=request.token,
            pr_title=request.title,
            pr_body=request.body,
            file_path=request.file_path,
            new_content=request.new_content,
            branch_name=request.branch_name,
            base_branch=request.base_branch
        )
        return pr_result
    except Exception as e:
        logger.exception("GitHub PR creation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/latest")
async def get_latest_analysis():
    """Get the most recent pipeline analysis result."""
    if not _latest_analysis:
        return {"status": "none", "message": "No analysis has been run yet."}
    return _latest_analysis


@router.get("/sources")
async def get_sources():
    """List available preloaded local test sources."""
    sources = [
        {
            "id": "sample-repo",
            "name": "FlakeGuard Sample Suite (sample-repo/)",
            "type": "local",
            "path": "sample-repo",
            "description": "Pre-configured test suite containing timing, order, and environment flaky tests."
        },
        {
            "id": "tests",
            "name": "FlakeGuard Internal Unit Tests (tests/)",
            "type": "local",
            "path": "tests",
            "description": "FlakeGuard system test suite."
        }
    ]
    return {
        "sources": sources,
        "history_count": len(_analysis_history)
    }
