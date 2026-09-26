import React, { useState, useEffect } from 'react';
import { repositoryApi, PipelineAnalysisResult } from '../services/api';
import './RepositoryIngestion.css';

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
  const [activeTab, setActiveTab] = useState<'github' | 'upload' | 'local'>('github');
  
  // GitHub state
  const [repoUrl, setRepoUrl] = useState('https://github.com/aditya-padmar/FlakeGuard');
  const [branch, setBranch] = useState('main');
  const [token, setToken] = useState('');
  const [showToken, setShowToken] = useState(false);

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // Local state
  const [localPath, setLocalPath] = useState('sample-repo');
  const [availableSources, setAvailableSources] = useState<Array<{ id: string; name: string; path: string; description: string }>>([]);

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

  // Load preset sources on mount
  useEffect(() => {
    repositoryApi.getSources()
      .then(res => {
        if (res.data?.sources) {
          setAvailableSources(res.data.sources);
        }
      })
      .catch(() => {});
  }, []);

  const handleGitHubAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) {
      setErrorMessage('Please enter a valid GitHub repository URL.');
      return;
    }

    // Clear ALL previous results before starting a new analysis
    setLoading(true);
    setErrorMessage(null);
    setSuccessInfo(null);
    setCurrentStep(1);
    setStatusMessage(`Cloning ${repoUrl} (branch: ${branch || 'default'})...`);

    // Simulated progress transitions to reflect real agent pipeline stages
    const t1 = setTimeout(() => {
      setCurrentStep(2);
      setStatusMessage(`Running ${numRuns} test detection iterations (F1)...`);
    }, 2500);

    const t2 = setTimeout(() => {
      setCurrentStep(3);
      setStatusMessage('Classifying root causes with Bob Agent 4 parallel subagents (F2)...');
    }, 5500);

    const t3 = setTimeout(() => {
      setCurrentStep(4);
      setStatusMessage('Generating concrete code diffs and remediation templates (F3)...');
    }, 8500);

    try {
      const response = await repositoryApi.cloneAndAnalyze({
        repo_url: repoUrl.trim(),
        branch: branch.trim() || undefined,
        token: token.trim() || undefined,
        num_runs: numRuns,
        test_pattern: testPattern.trim() || undefined
      });

      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);

      const data = response.data;
      const flakyCount = data.detection?.flaky_tests_count ?? 0;
      const fixesCount = data.fixes?.length ?? 0;

      // Handle non-success responses without crashing
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
      setSuccessInfo({
        source: repoUrl,
        flakyCount,
        fixesCount,
        time: new Date().toLocaleTimeString()
      });
      onAnalysisComplete(data);
    } catch (err: any) {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      const detail = err.response?.data?.detail || err.message || 'Analysis failed';
      setCurrentStep(0);
      setSuccessInfo(null);
      setErrorMessage(`GitHub Analysis Failed: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please select or drop a .zip archive or .py test file.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    setSuccessInfo(null);
    setCurrentStep(1);
    setStatusMessage(`Unpacking and sandboxing ${selectedFile.name}...`);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('num_runs', numRuns.toString());
    if (testPattern.trim()) {
      formData.append('test_pattern', testPattern.trim());
    }

    const t1 = setTimeout(() => {
      setCurrentStep(2);
      setStatusMessage(`Executing test runs on uploaded files (${numRuns} iterations)...`);
    }, 1500);

    const t2 = setTimeout(() => {
      setCurrentStep(3);
      setStatusMessage('Orchestrating Bob root-cause subagents (Timing, Ordering, State, Env)...');
    }, 3500);

    try {
      const response = await repositoryApi.uploadAndAnalyze(formData);
      clearTimeout(t1);
      clearTimeout(t2);

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
      setSuccessInfo({
        source: selectedFile.name,
        flakyCount,
        fixesCount,
        time: new Date().toLocaleTimeString()
      });
      onAnalysisComplete(data);
    } catch (err: any) {
      clearTimeout(t1);
      clearTimeout(t2);
      const detail = err.response?.data?.detail || err.message || 'Upload analysis failed';
      setCurrentStep(0);
      setSuccessInfo(null);
      setErrorMessage(`Upload Analysis Failed: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLocalAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    // Clear ALL previous results before starting a new analysis
    setLoading(true);
    setErrorMessage(null);
    setSuccessInfo(null);
    setCurrentStep(2);
    setStatusMessage(`Executing ${numRuns} test iterations on local suite: ${localPath}...`);

    try {
      const response = await repositoryApi.analyzeLocal({
        repo_path: localPath,
        num_runs: numRuns,
        test_pattern: testPattern.trim() || undefined
      });

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
        setErrorMessage(`Local Analysis Failed: ${reason}`);
        return;
      }

      setCurrentStep(5);
      setStatusMessage('Local analysis complete!');
      setSuccessInfo({
        source: localPath,
        flakyCount,
        fixesCount,
        time: new Date().toLocaleTimeString()
      });
      onAnalysisComplete(data);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Local analysis failed';
      setCurrentStep(0);
      setSuccessInfo(null);
      setErrorMessage(`Local Analysis Failed: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.zip') || file.name.endsWith('.py')) {
        setSelectedFile(file);
        setErrorMessage(null);
      } else {
        setErrorMessage('Only .zip archives or .py test files are supported.');
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
            Clone remote GitHub repositories, upload custom test archives, or run the built-in local suite.
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
          <span className="tab-badge">.zip / .py</span>
        </button>

        <button
          type="button"
          className={`source-tab ${activeTab === 'local' ? 'active' : ''}`}
          onClick={() => setActiveTab('local')}
        >
          <span className="tab-icon">💻</span>
          <span className="tab-text">Local / Sample Repo</span>
          <span className="tab-badge">Instant</span>
        </button>
      </div>

      {/* Form Content */}
      <div className="ingestion-body">
        {activeTab === 'github' && (
          <form onSubmit={handleGitHubAnalyze} className="ingestion-form">
            <div className="form-row">
              <div className="form-group flex-2">
                <label htmlFor="repo-url">GitHub Repository URL</label>
                <div className="input-with-icon">
                  <span className="input-prefix">https://github.com/</span>
                  <input
                    id="repo-url"
                    type="text"
                    value={repoUrl.replace(/^https?:\/\/github\.com\//, '')}
                    onChange={(e) => setRepoUrl(`https://github.com/${e.target.value.replace(/^https?:\/\/github\.com\//, '')}`)}
                    placeholder="owner/repository"
                    required
                    disabled={loading}
                  />
                </div>
                <div className="quick-presets">
                  <span className="preset-label">Quick test repos:</span>
                  <button
                    type="button"
                    className="preset-chip"
                    onClick={() => { setRepoUrl('https://github.com/aditya-padmar/FlakeGuard'); setBranch('main'); }}
                  >
                    aditya-padmar/FlakeGuard
                  </button>
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

            <div className="form-row">
              <div className="form-group flex-2">
                <div className="label-with-hint">
                  <label htmlFor="github-token">GitHub Personal Access Token (Optional)</label>
                  <span className="hint-text">Required for private repos or 1-click PR creation</span>
                </div>
                <div className="input-with-action">
                  <input
                    id="github-token"
                    type={showToken ? 'text' : 'password'}
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="toggle-token-btn"
                    onClick={() => setShowToken(!showToken)}
                  >
                    {showToken ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

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
                accept=".zip,.py"
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
                    <p className="dropzone-title">Drag & drop project .zip or test .py file</p>
                    <p className="dropzone-subtitle">or click to browse from your machine</p>
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

        {activeTab === 'local' && (
          <form onSubmit={handleLocalAnalyze} className="ingestion-form">
            <div className="form-row">
              <div className="form-group flex-2">
                <label htmlFor="local-path-select">Pre-configured Local Repositories</label>
                <div className="preset-grid">
                  {availableSources.map((src) => (
                    <div
                      key={src.id}
                      className={`preset-card ${localPath === src.path ? 'selected' : ''}`}
                      onClick={() => setLocalPath(src.path)}
                    >
                      <div className="card-header">
                        <strong>{src.name}</strong>
                      </div>
                      <p className="card-desc">{src.description}</p>
                      <code className="card-path">{src.path}</code>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group flex-1">
                <label htmlFor="custom-local-path">Or Custom Directory Path</label>
                <input
                  id="custom-local-path"
                  type="text"
                  value={localPath}
                  onChange={(e) => setLocalPath(e.target.value)}
                  placeholder="sample-repo"
                  disabled={loading}
                />
                <div style={{ marginTop: '1rem' }}>
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
              </div>
            </div>

            <div className="action-row">
              <button type="submit" className="btn-run-pipeline" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    <span>Analyzing Local Suite...</span>
                  </>
                ) : (
                  <>
                    <span>⚡ Run Analysis on {localPath}</span>
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
            <div className="alert-text">{errorMessage}</div>
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
