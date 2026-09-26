import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { repositoryApi, type PipelineAnalysisResult, type TokenVerificationResult } from '../services/api';
import './RepositoryIngestion.css';

interface AnalysisRequest {
  generation: number;
  controller: AbortController;
  timers: Set<ReturnType<typeof setTimeout>>;
}

function clearRequestTimers(request: AnalysisRequest) {
  request.timers.forEach(timer => clearTimeout(timer));
  request.timers.clear();
}

function analysisError(cause: unknown, fallback: string): string {
  const detail = axios.isAxiosError<{ detail?: unknown }>(cause) ? cause.response?.data?.detail : undefined;
  if (typeof detail === 'string' && detail.trim()) return detail;
  return cause instanceof Error && cause.message ? cause.message : fallback;
}

interface RepositoryIngestionProps {
  onAnalysisComplete: (result: PipelineAnalysisResult) => void;
  activeSourceInfo?: {
    type: 'github' | 'upload' | 'local';
    name: string;
    branch?: string;
  } | null;
}

export default function RepositoryIngestion({
  onAnalysisComplete,
  activeSourceInfo
}: RepositoryIngestionProps) {
  const [searchParams] = useSearchParams();
  const repoParam = searchParams.get('repo');
  const visibilityParam = searchParams.get('visibility');
  const branchParam = searchParams.get('branch');

  const normalizeUrlParam = (raw: string | null) => {
    if (!raw) return '';
    const trimmed = raw.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed;
    return `https://github.com/${trimmed.replace(/^github\.com\//, '')}`;
  };

  const [activeTab, setActiveTab] = useState<'github' | 'upload'>('github');
  
  // GitHub state
  const [repoUrl, setRepoUrl] = useState(() => normalizeUrlParam(repoParam));
  const [branch, setBranch] = useState(branchParam?.trim() || 'main');
  const [repoVisibility, setRepoVisibility] = useState<'public' | 'private'>(
    visibilityParam === 'private' ? 'private' : 'public'
  );
  const [token, setToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [verifyingToken, setVerifyingToken] = useState(false);
  const [tokenVerificationResult, setTokenVerificationResult] = useState<TokenVerificationResult | null>(null);
  const tokenInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const r = searchParams.get('repo');
    const v = searchParams.get('visibility');
    const b = searchParams.get('branch');
    if (r !== null) {
      setRepoUrl(normalizeUrlParam(r));
    }
    if (b !== null && b.trim()) {
      setBranch(b.trim());
    }
    if (v === 'private') {
      setRepoVisibility('private');
      const timer = setTimeout(() => {
        if (!r && !repoUrl) {
          const urlInput = document.getElementById('repo-url') as HTMLInputElement | null;
          urlInput?.focus();
        } else {
          tokenInputRef.current?.focus();
        }
      }, 150);
      return () => clearTimeout(timer);
    } else if (v === 'public') {
      setRepoVisibility('public');
    }
  }, [searchParams]);

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // Shared execution settings
  const [numRuns, setNumRuns] = useState(5);
  const [testPattern, setTestPattern] = useState('');

  // Status & Progress state
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{
    source: string;
    flakyCount: number;
    fixesCount: number;
    time: string;
  } | null>(null);

  const mounted = useRef(false);
  const generation = useRef(0);
  const activeRequest = useRef<AnalysisRequest | null>(null);

  // The per-setup signal also rejects responses from StrictMode's discarded mount.
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      generation.current += 1;
      const request = activeRequest.current;
      if (request) { request.controller.abort(); clearRequestTimers(request); }
      activeRequest.current = null;
    };
  }, []);

  const isCurrentRequest = (request: AnalysisRequest) => mounted.current
    && generation.current === request.generation
    && activeRequest.current === request
    && !request.controller.signal.aborted;
  const beginRequest = () => {
    // A ref closes the gap before React paints the disabled submit button.
    if (!mounted.current || activeRequest.current) return null;
    const request: AnalysisRequest = { generation: ++generation.current, controller: new AbortController(), timers: new Set() };
    activeRequest.current = request;
    return request;
  };
  const scheduleProgress = (request: AnalysisRequest, delay: number, update: () => void) => {
    const timer = setTimeout(() => {
      request.timers.delete(timer);
      if (isCurrentRequest(request)) update();
    }, delay);
    request.timers.add(timer);
  };
  const finishRequest = (request: AnalysisRequest) => {
    clearRequestTimers(request);
    if (isCurrentRequest(request)) {
      activeRequest.current = null;
      setLoading(false);
    }
  };

  const isTokenFormatRecognized = (tok: string) => {
    const t = tok.trim();
    return !t || t.startsWith('ghp_') || t.startsWith('github_pat_');
  };

  const handleVerifyToken = async () => {
    let cleanUrl = repoUrl.trim();
    if (!cleanUrl) {
      setErrorMessage('Please enter a GitHub repository URL first.');
      return;
    }
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = `https://github.com/${cleanUrl.replace(/^github\.com\//, '')}`;
    }
    if (!token.trim()) {
      setErrorMessage('Please enter a GitHub Personal Access Token to verify.');
      tokenInputRef.current?.focus();
      return;
    }
    setVerifyingToken(true);
    setTokenVerificationResult(null);
    setErrorMessage(null);
    try {
      const res = await repositoryApi.verifyToken({
        repo_url: cleanUrl,
        token: token.trim()
      });
      setTokenVerificationResult(res.data);
      if (res.data.valid && res.data.default_branch && (!branch || branch === 'main')) {
        setBranch(res.data.default_branch);
      }
    } catch (err: unknown) {
      setTokenVerificationResult({
        valid: false,
        error: analysisError(err, 'Token verification request failed.')
      });
    } finally {
      setVerifyingToken(false);
    }
  };

  const handleGitHubAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (activeRequest.current) return;
    let cleanUrl = repoUrl.trim();
    if (!cleanUrl) {
      setErrorMessage('Please enter a valid GitHub repository URL.');
      return;
    }
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = `https://github.com/${cleanUrl.replace(/^github\.com\//, '')}`;
    }

    // Required checks for private repository mode
    if (repoVisibility === 'private') {
      if (!token.trim()) {
        setErrorMessage('A GitHub Personal Access Token is required to clone and analyze a private repository.');
        tokenInputRef.current?.focus();
        return;
      }
      if (token.trim().length < 15) {
        setErrorMessage('The Personal Access Token appears too short. Please provide a valid GitHub token (e.g. ghp_... or github_pat_...).');
        tokenInputRef.current?.focus();
        return;
      }
    }

    const request = beginRequest();
    if (!request) return;

    // Clear previous feedback before starting a new analysis.
    setLoading(true);
    setErrorMessage(null);
    setSuccessInfo(null);
    setCurrentStep(1);
    setStatusMessage(`Cloning ${repoUrl} (branch: ${branch || 'default'})...`);

    // Simulated progress transitions; callbacks belong only to this request.
    scheduleProgress(request, 2500, () => {
      setCurrentStep(2);
      setStatusMessage(`Running ${numRuns} test detection iterations (F1)...`);
    });
    scheduleProgress(request, 5500, () => {
      setCurrentStep(3);
      setStatusMessage('Classifying root causes with Bob Agent 4 parallel subagents (F2)...');
    });
    scheduleProgress(request, 8500, () => {
      setCurrentStep(4);
      setStatusMessage('Generating concrete code diffs and remediation templates (F3)...');
    });

    try {
      const response = await repositoryApi.cloneAndAnalyze({
        repo_url: cleanUrl,
        branch: branch.trim() || undefined,
        token: repoVisibility === 'private' ? token.trim() : (token.trim() || undefined),
        num_runs: numRuns,
        test_pattern: testPattern.trim() || undefined
      }, request.controller.signal);
      if (!isCurrentRequest(request)) return;
      clearRequestTimers(request);

      const data = response.data;
      const flakyCount = data.detection?.flaky_tests_count ?? 0;
      const fixesCount = data.fixes?.length ?? 0;
      if (data.status === 'no_tests' || data.status === 'unsupported') {
        const reason = data.errors?.[0]?.message || data.message || 'No supported pytest tests were found.';
        setCurrentStep(0);
        setSuccessInfo(null);
        setErrorMessage(`No Tests Found: ${reason}`);
        return;
      }
      if (data.status === 'error') {
        const reason = data.errors?.[0]?.message || data.message || 'Analysis failed.';
        setCurrentStep(0);
        setSuccessInfo(null);
        setErrorMessage(`GitHub Analysis Failed: ${reason}`);
        return;
      }
      setCurrentStep(5);
      setStatusMessage('Pipeline complete!');
      setSuccessInfo({ source: repoUrl, flakyCount, fixesCount, time: new Date().toLocaleTimeString() });
      onAnalysisComplete(data);
    } catch (cause: unknown) {
      if (!isCurrentRequest(request) || axios.isCancel(cause)) return;
      setCurrentStep(0);
      setSuccessInfo(null);
      setErrorMessage(`GitHub Analysis Failed: ${analysisError(cause, 'Analysis failed')}`);
    } finally {
      finishRequest(request);
    }
  };

  const handleUploadAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (activeRequest.current) return;
    if (!selectedFile) {
      setErrorMessage('Please select or drop a .zip archive or .py test file.');
      return;
    }
    const request = beginRequest();
    if (!request) return;

    setLoading(true);
    setErrorMessage(null);
    setSuccessInfo(null);
    setCurrentStep(1);
    setStatusMessage(`Unpacking and sandboxing ${selectedFile.name}...`);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('num_runs', numRuns.toString());
    if (testPattern.trim()) formData.append('test_pattern', testPattern.trim());

    scheduleProgress(request, 1500, () => {
      setCurrentStep(2);
      setStatusMessage(`Executing test runs on uploaded files (${numRuns} iterations)...`);
    });
    scheduleProgress(request, 3500, () => {
      setCurrentStep(3);
      setStatusMessage('Orchestrating Bob root-cause subagents (Timing, Ordering, State, Env)...');
    });

    try {
      const response = await repositoryApi.uploadAndAnalyze(formData, request.controller.signal);
      if (!isCurrentRequest(request)) return;
      clearRequestTimers(request);

      const data = response.data;
      const flakyCount = data.detection?.flaky_tests_count ?? 0;
      const fixesCount = data.fixes?.length ?? 0;
      if (data.status === 'no_tests' || data.status === 'unsupported') {
        const reason = data.errors?.[0]?.message || data.message || 'No supported pytest tests were found.';
        setCurrentStep(0);
        setSuccessInfo(null);
        setErrorMessage(`No Tests Found: ${reason}`);
        return;
      }
      if (data.status === 'error') {
        const reason = data.errors?.[0]?.message || data.message || 'Analysis failed.';
        setCurrentStep(0);
        setSuccessInfo(null);
        setErrorMessage(`Upload Analysis Failed: ${reason}`);
        return;
      }
      setCurrentStep(5);
      setStatusMessage('Analysis complete!');
      setSuccessInfo({ source: selectedFile.name, flakyCount, fixesCount, time: new Date().toLocaleTimeString() });
      onAnalysisComplete(data);
    } catch (cause: unknown) {
      if (!isCurrentRequest(request) || axios.isCancel(cause)) return;
      setCurrentStep(0);
      setSuccessInfo(null);
      setErrorMessage(`Upload Analysis Failed: ${analysisError(cause, 'Upload analysis failed')}`);
    } finally {
      finishRequest(request);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      const validExts = ['.zip', '.tar', '.gz', '.tgz', '.py', '.c', '.cpp', '.cc', '.h', '.hpp', '.js', '.jsx', '.ts', '.tsx', '.go', '.java', '.kt', '.rs'];
      const lower = file.name.toLowerCase();
      if (validExts.some(ext => lower.endsWith(ext))) {
        setSelectedFile(file);
        setErrorMessage(null);
      } else {
        setErrorMessage('Unsupported file format. Please upload an archive (.zip, .tar.gz) or code file (.c, .cpp, .js, .ts, .go, .java, .py).');
      }
    }
  };

  return (
    <div className="ingestion-card">
      <div className="ingestion-header">
        <div className="header-titles">
          <div className="badge-live-tag">F1 ➔ F2 ➔ F3 ➔ F4 Live Pipeline</div>
          <h2>Repository Ingestion & Flaky Analysis Engine</h2>
          <p className="subtitle">
            Clone remote GitHub repositories or upload custom test suites and archives for automated analysis.
          </p>
        </div>

        {activeSourceInfo && (
          <div className="active-source-pill">
            <span className="source-dot pulse"></span>
            <span className="source-type">{activeSourceInfo.type.toUpperCase()}</span>
            <span className="source-name">{activeSourceInfo.name}</span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="source-tabs">
        <button
          type="button"
          className={`source-tab ${activeTab === 'github' ? 'active' : ''}`}
          onClick={() => setActiveTab('github')}
        >
          <span className="tab-icon">🐙</span>
          <span className="tab-text">GitHub Repository</span>
          <span className="tab-badge">Cloud</span>
        </button>

        <button
          type="button"
          className={`source-tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          <span className="tab-icon">📁</span>
          <span className="tab-text">Upload Test Suite</span>
          <span className="tab-badge">Polyglot / Archive</span>
        </button>
      </div>

      {/* Form Content */}
      <div className="ingestion-body">
        {activeTab === 'github' && (
          <form onSubmit={handleGitHubAnalyze} className="ingestion-form">
            {searchParams.get('repo') && repoVisibility === 'private' && (
              <div className="bridge-notice-banner">
                <span className="bridge-notice-icon">🔑</span>
                <div className="bridge-notice-content">
                  <strong>Private repository linked from Launchpad:</strong> Please provide your GitHub Personal Access Token below to authorize cloning and begin test discovery.
                </div>
              </div>
            )}
            <div className="form-row">
              <div className="form-group flex-2">
                <label htmlFor="repo-url">GitHub Repository URL</label>
                <div className="input-with-icon">
                  <span className="input-prefix">https://github.com/</span>
                  <input
                    id="repo-url"
                    type="text"
                    value={repoUrl.replace(/^https?:\/\/github\.com\//, '')}
                    onChange={(e) => setRepoUrl(e.target.value.trim() ? `https://github.com/${e.target.value.replace(/^https?:\/\/github\.com\//, '')}` : '')}
                    placeholder="owner/repository (e.g. your-org/your-repo)"
                    required
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="form-group flex-1">
                <label htmlFor="repo-branch">Branch / Ref</label>
                <input
                  id="repo-branch"
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Repository Visibility Segmented Control */}
            <div className="visibility-segmented-wrapper">
              <div className="visibility-label-row">
                <label className="section-label">Repository Access & Visibility</label>
                <span className="visibility-subtext">Choose access mode for cloning and authentication</span>
              </div>
              <div className="visibility-segmented-control" role="radiogroup" aria-label="Repository Visibility">
                <button
                  type="button"
                  role="radio"
                  aria-checked={repoVisibility === 'public'}
                  className={`visibility-btn ${repoVisibility === 'public' ? 'active' : ''}`}
                  onClick={() => {
                    setRepoVisibility('public');
                    setErrorMessage(null);
                    setTokenVerificationResult(null);
                  }}
                  disabled={loading}
                >
                  <span className="vis-icon">🌐</span>
                  <div className="vis-meta">
                    <div className="vis-title">Public Repository</div>
                    <div className="vis-desc">Open-source • No token needed</div>
                  </div>
                  {repoVisibility === 'public' && <span className="vis-badge-active">Selected</span>}
                </button>

                <button
                  type="button"
                  role="radio"
                  aria-checked={repoVisibility === 'private'}
                  className={`visibility-btn ${repoVisibility === 'private' ? 'active' : ''}`}
                  onClick={() => {
                    setRepoVisibility('private');
                    setErrorMessage(null);
                    setTimeout(() => tokenInputRef.current?.focus(), 60);
                  }}
                  disabled={loading}
                >
                  <span className="vis-icon">🔒</span>
                  <div className="vis-meta">
                    <div className="vis-title">Private Repository</div>
                    <div className="vis-desc">Encrypted • Requires GitHub Personal Access Token</div>
                  </div>
                  {repoVisibility === 'private' && <span className="vis-badge-active">Selected</span>}
                </button>
              </div>
            </div>

            {/* Private Repository Authentication Card */}
            {repoVisibility === 'private' && (
              <div className="private-auth-card">
                <div className="private-auth-header">
                  <div className="label-with-hint">
                    <label htmlFor="github-token" className="token-label">
                      <span className="required-badge">REQUIRED</span>
                      GitHub Personal Access Token (PAT)
                    </label>
                    <a
                      href="https://github.com/settings/tokens/new?scopes=repo&description=FlakeGuard%20Analysis"
                      target="_blank"
                      rel="noreferrer"
                      className="token-helper-link"
                    >
                      Generate Token on GitHub ↗
                    </a>
                  </div>
                  <p className="token-desc">
                    Requires <code className="scope-code">repo</code> scope (classic) or <code className="scope-code">Contents: Read</code> (fine-grained) to clone private test suites.
                  </p>
                </div>

                <div className="token-input-bar">
                  <div className="input-with-action flex-grow">
                    <span className="input-key-prefix">🔑</span>
                    <input
                      ref={tokenInputRef}
                      id="github-token"
                      type={showToken ? 'text' : 'password'}
                      value={token}
                      onChange={(e) => {
                        setToken(e.target.value);
                        setTokenVerificationResult(null);
                        setErrorMessage(null);
                      }}
                      placeholder="ghp_xxxxxxxxxxxxxxxxxxxx or github_pat_xxxxxxxxxxxxxxxxxxxx"
                      disabled={loading || verifyingToken}
                      required
                      autoComplete="off"
                    />
                    <button
                      type="button"
                      className="toggle-token-btn"
                      onClick={() => setShowToken(!showToken)}
                      tabIndex={-1}
                    >
                      {showToken ? 'Hide' : 'Show'}
                    </button>
                  </div>

                  <button
                    type="button"
                    className="btn-verify-token"
                    onClick={handleVerifyToken}
                    disabled={loading || verifyingToken || !token.trim() || !repoUrl.trim()}
                    title={!repoUrl.trim() ? 'Enter Repository URL first' : 'Verify token credentials with GitHub'}
                  >
                    {verifyingToken ? (
                      <>
                        <span className="spinner-sm"></span>
                        <span>Verifying...</span>
                      </>
                    ) : (
                      <>
                        <span>⚡ Verify Access</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Token format hint */}
                {token.trim().length > 0 && !isTokenFormatRecognized(token) && (
                  <div className="token-format-notice">
                    <span className="notice-icon">ℹ️</span>
                    <span>GitHub PATs typically start with <code className="scope-code">ghp_</code> (classic) or <code className="scope-code">github_pat_</code> (fine-grained).</span>
                  </div>
                )}

                {/* Verification result status */}
                {tokenVerificationResult && (
                  <div className={`token-status-pill ${tokenVerificationResult.valid ? 'success' : 'error'}`}>
                    <span className="status-indicator-icon">{tokenVerificationResult.valid ? '✅' : '❌'}</span>
                    <div className="status-meta">
                      <div className="status-headline">
                        {tokenVerificationResult.valid ? 'Token Verified & Read Access Confirmed' : 'Verification Failed'}
                      </div>
                      <div className="status-subline">
                        {tokenVerificationResult.valid ? (
                          <>
                            <span>Repository: <strong>{tokenVerificationResult.full_name || tokenVerificationResult.repo}</strong></span>
                            <span className="perm-chips">
                              <span className="perm-chip">Pull: {tokenVerificationResult.permissions?.pull ? '✓' : '✗'}</span>
                              <span className="perm-chip">Push: {tokenVerificationResult.permissions?.push ? '✓' : '✗'}</span>
                              <span className="perm-chip">Admin: {tokenVerificationResult.permissions?.admin ? '✓' : '✗'}</span>
                            </span>
                          </>
                        ) : (
                          tokenVerificationResult.error || 'Failed to authenticate token with GitHub.'
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="form-row">
              <div className="form-group flex-1">
                <label htmlFor="runs-slider">Execution Passes: <strong>{numRuns} runs</strong></label>
                <input
                  id="runs-slider"
                  type="range"
                  min="2"
                  max="10"
                  value={numRuns}
                  onChange={(e) => setNumRuns(Number(e.target.value))}
                  disabled={loading}
                />
                <span className="slider-hint">More runs = higher confidence</span>
              </div>
            </div>

            <div className="action-row">
              <button type="submit" className="btn-run-pipeline" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    <span>Cloning & Running Pipeline...</span>
                  </>
                ) : (
                  <>
                    <span>🚀 Clone & Analyze with Bob Agent</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {activeTab === 'upload' && (
          <form onSubmit={handleUploadAnalyze} className="ingestion-form">
            <div
              className={`dropzone ${dragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              onClick={() => document.getElementById('archive-file-input')?.click()}
            >
              <input
                id="archive-file-input"
                type="file"
                accept=".zip,.tar,.gz,.tgz,.py,.c,.cpp,.cc,.h,.hpp,.js,.jsx,.ts,.tsx,.go,.java,.kt,.rs"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setSelectedFile(e.target.files[0]);
                    setErrorMessage(null);
                  }
                }}
                disabled={loading}
              />
              <div className="dropzone-content">
                <span className="drop-icon">{selectedFile ? '📦' : '☁️'}</span>
                {selectedFile ? (
                  <div className="file-info-pill">
                    <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(1)} KB)
                    <button
                      type="button"
                      className="clear-file-btn"
                      onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <>
                    <p className="dropzone-title">Drag & drop archive (.zip, .tar.gz) or source/test file</p>
                    <p className="dropzone-subtitle">Supports C/C++, Embedded, JS/TS, Python, Go, Java, Rust</p>
                  </>
                )}
              </div>
            </div>

            <div className="form-row" style={{ marginTop: '1rem' }}>
              <div className="form-group flex-1">
                <label>Execution Passes: <strong>{numRuns} runs</strong></label>
                <input
                  type="range"
                  min="2"
                  max="10"
                  value={numRuns}
                  onChange={(e) => setNumRuns(Number(e.target.value))}
                  disabled={loading}
                />
              </div>

              <div className="form-group flex-1">
                <label htmlFor="test-filter-upload">Test Name Filter (Optional)</label>
                <input
                  id="test-filter-upload"
                  type="text"
                  placeholder="e.g. test_order or timing"
                  value={testPattern}
                  onChange={(e) => setTestPattern(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="action-row">
              <button
                type="submit"
                className="btn-run-pipeline"
                disabled={loading || !selectedFile}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    <span>Extracting & Running Analysis...</span>
                  </>
                ) : (
                  <>
                    <span>🚀 Upload & Run Full Analysis</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {/* Live Stepper & Feedback */}
        {loading && (
          <div className="pipeline-stepper-box">
            <div className="stepper-header">
              <span className="stepper-title">Executing FlakeGuard Full Pipeline</span>
              <span className="stepper-status">{statusMessage}</span>
            </div>

            <div className="stepper-stages">
              <div className={`step-item ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
                <div className="step-circle">{currentStep > 1 ? '✓' : '1'}</div>
                <div className="step-label">Ingest / Clone</div>
              </div>
              <div className="step-connector"></div>

              <div className={`step-item ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
                <div className="step-circle">{currentStep > 2 ? '✓' : '2'}</div>
                <div className="step-label">F1: Detection</div>
              </div>
              <div className="step-connector"></div>

              <div className={`step-item ${currentStep >= 3 ? 'active' : ''} ${currentStep > 3 ? 'completed' : ''}`}>
                <div className="step-circle">{currentStep > 3 ? '✓' : '3'}</div>
                <div className="step-label">F2: Bob AI</div>
              </div>
              <div className="step-connector"></div>

              <div className={`step-item ${currentStep >= 4 ? 'active' : ''} ${currentStep > 4 ? 'completed' : ''}`}>
                <div className="step-circle">{currentStep > 4 ? '✓' : '4'}</div>
                <div className="step-label">F3: Diffs</div>
              </div>
              <div className="step-connector"></div>

              <div className={`step-item ${currentStep >= 5 ? 'active' : ''} ${currentStep > 5 ? 'completed' : ''}`}>
                <div className="step-circle">{currentStep >= 5 ? '✓' : '5'}</div>
                <div className="step-label">F4: Audit</div>
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {errorMessage && (
          <div className="ingestion-alert error">
            <span className="alert-icon">⚠️</span>
            <div className="alert-text">
              <div className="alert-message-line">{errorMessage}</div>
              {repoVisibility === 'public' && errorMessage.toLowerCase().includes('private') && (
                <div className="alert-action-line">
                  <button
                    type="button"
                    className="btn-switch-to-private"
                    onClick={() => {
                      setRepoVisibility('private');
                      setErrorMessage(null);
                      setTimeout(() => tokenInputRef.current?.focus(), 60);
                    }}
                  >
                    🔒 Switch to Private Repository & Enter Token
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Success message */}
        {successInfo && !loading && (
          <div className="ingestion-alert success">
            <span className="alert-icon">✅</span>
            <div className="alert-text">
              <strong>Analysis Completed Successfully!</strong> Found{' '}
              <span className="stat-highlight">{successInfo.flakyCount} flaky tests</span> and generated{' '}
              <span className="stat-highlight">{successInfo.fixesCount} concrete code diffs</span> from{' '}
              <code>{successInfo.source}</code>. Dashboard has been updated below.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
