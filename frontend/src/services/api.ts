import axios from 'axios';

const API_BASE = '/api';

// ── Shared types ──────────────────────────────────────────────────────────────

export interface FlakyTest {
  test_name: string;
  file_path: string;
  flake_rate: number;
  total_runs: number;
  pass_count: number;
  fail_count: number;
  recent_failures: string[];
}

export interface RootCauseBreakdown {
  cause: string;
  count: number;
  percentage: number;
}

export interface QuarantineEntry {
  quarantine_id: string;
  test_name: string;
  file_path: string;
  reason: string;
  status: string;
  quarantined_at: string;
}

export interface Fix {
  fix_id: string;
  test_name: string;
  file_path: string;
  status: string;
  suggestions: FixSuggestion[];
}

export interface FixSuggestion {
  suggestion_id: string;
  fix_type: string;
  description: string;
  rationale: string;
  confidence: number;
}

// ── F3 types ──────────────────────────────────────────────────────────────────

export interface EvidenceItem {
  file: string;
  line?: number;
  reason?: string;
}

export interface EvidenceValidationRequest {
  test_name: string;
  root_cause: string;
  confidence: number;
  evidence: EvidenceItem[];
}

export interface EvidenceValidationResult {
  valid: boolean;
  locations: string[];
  message: string;
  details: Array<{
    valid: boolean;
    location: string | null;
    message: string;
    file_exists: boolean;
    line_exists: boolean | null;
    code_snippet: string | null;
    reason?: string;
  }>;
}

export interface StrategyRequest {
  root_cause: string;
  evidence?: EvidenceItem[];
}

export interface StrategyResult {
  root_cause: string;
  strategies: string[];
  descriptions: string[];
}

export interface F2ClassificationInput {
  test_name: string;
  root_cause: string;
  confidence: number;
  evidence: string[];
  file_path?: string;
}

// ── F4 types ──────────────────────────────────────────────────────────────────

export interface SkipDetection {
  test_name: string;
  file: string;
  line: number;
  suppression_type: 'skip' | 'xfail' | 'skip_call';
  reason: string | null;
  source: 'decorator' | 'inline';
}

export interface SkipSummary {
  total_suppressed: number;
  skip_count: number;
  xfail_count: number;
  tests: string[];
}

export interface RetryDetailItem {
  mechanism: string;
  retry_count: number;
  line: number;
}

export interface RetryDetectionResult {
  github_actions: { retry_detected: boolean; source: string; file: string | null; retry_count: number; details: RetryDetailItem[] };
  pytest_config: { retry_detected: boolean; source: string; file: string | null; retry_count: number; details: RetryDetailItem[] };
  summary: { retry_detected: boolean; sources: string[] };
}

export interface AuditedTest {
  test_name: string;
  diagnosed: boolean;
  fixable: boolean;
  status: string;
  root_cause: string | null;
  confidence: string | null;
  fix_strategy: string | null;
  quarantine_reason: string | null;
  quarantined_at: string | null;
  source: string;
}

export interface AuditReport {
  quarantine_audit: {
    report_id: string;
    generated_at: string;
    quarantined_tests: AuditedTest[];
    total_quarantined: number;
    diagnosed_count: number;
    fixable_count: number;
    unexplained_count: number;
    summary: Record<string, unknown>;
  } | null;
  quarantine_report: {
    total_quarantined: number;
    active_count: number;
    under_review_count: number;
    resolved_count: number;
    average_quarantine_duration: number;
    oldest_quarantine_days: number;
  };
  skip_detections: { detections: SkipDetection[]; summary: SkipSummary };
  retry_configuration: RetryDetectionResult;
}

// ── API clients ───────────────────────────────────────────────────────────────

// Detection API
export const detectionApi = {
  listRuns: () => axios.get(`${API_BASE}/detection/runs`),
  getRun: (runId: string) => axios.get(`${API_BASE}/detection/runs/${runId}`),
  analyze: () => axios.post(`${API_BASE}/detection/analyze`),
  listDetections: () => axios.get(`${API_BASE}/detection/detections`),
};

// Classification API
export const classificationApi = {
  classify: (test: FlakyTest) => axios.post(`${API_BASE}/classification/classify`, test),
  listClassifications: () => axios.get(`${API_BASE}/classification/classifications`),
  getRootCauses: () => axios.get(`${API_BASE}/classification/root-causes`),
};

// Remediation API (F3)
export const remediationApi = {
  // Existing endpoints
  listFixes: () => axios.get(`${API_BASE}/remediation/fixes`),
  getFix: (fixId: string) => axios.get(`${API_BASE}/remediation/fixes/${fixId}`),
  applyFix: (fixId: string, suggestionId: string) =>
    axios.post(`${API_BASE}/remediation/fixes/${fixId}/apply`, null, { params: { suggestion_id: suggestionId } }),
  // F3 endpoints
  generateFromF2: (input: F2ClassificationInput) =>
    axios.post(`${API_BASE}/remediation/generate-from-f2`, input),
  validateEvidence: (request: EvidenceValidationRequest) =>
    axios.post<EvidenceValidationResult>(`${API_BASE}/remediation/validate-evidence`, request),
  selectStrategy: (request: StrategyRequest) =>
    axios.post<StrategyResult>(`${API_BASE}/remediation/select-strategy`, request),
};

// Audit API (F4)
export const auditApi = {
  // Existing endpoints
  listQuarantine: () => axios.get(`${API_BASE}/audit/quarantine`),
  getQuarantineReport: () => axios.get(`${API_BASE}/audit/quarantine/report`),
  updateQuarantineStatus: (id: string, status: string, notes?: string) =>
    axios.put(`${API_BASE}/audit/quarantine/${id}/status`, { status, notes }),
  // F4 endpoints
  getSkipDetections: (repoPath = 'sample-repo') =>
    axios.get<{ repo_path: string; detections: SkipDetection[]; summary: SkipSummary }>(
      `${API_BASE}/audit/skip-detections`, { params: { repo_path: repoPath } }),
  getRetryDetections: (repoPath = 'sample-repo') =>
    axios.get<RetryDetectionResult>(`${API_BASE}/audit/retry-detections`, { params: { repo_path: repoPath } }),
  runAudit: (quarantinePath = 'sample-repo/QUARANTINE.md', repoPath = 'sample-repo') =>
    axios.post(`${API_BASE}/audit/run`, null, { params: { quarantine_path: quarantinePath, repo_path: repoPath } }),
  getReport: (quarantinePath = 'sample-repo/QUARANTINE.md', repoPath = 'sample-repo') =>
    axios.get<AuditReport>(`${API_BASE}/audit/report`, { params: { quarantine_path: quarantinePath, repo_path: repoPath } }),
};

// Metrics API
export const metricsApi = {
  getSummary: () => axios.get(`${API_BASE}/metrics/summary`),
  getRootCauseBreakdown: () => axios.get(`${API_BASE}/metrics/root-causes`),
  getTrends: (days = 30) => axios.get(`${API_BASE}/metrics/trends?days=${days}`),
  getPerformance: () => axios.get(`${API_BASE}/metrics/performance`),
};

// ── Repository Ingestion API (GitHub Clone & Local File Upload) ───────────────

export interface PipelineAnalysisResult {
  pipeline_id: string;
  source_type: 'github' | 'upload' | 'local';
  repository: string;
  branch: string;
  commit_sha: string;
  started_at: string;
  completed_at: string;
  runs: number;
  detection: {
    total_runs: number;
    flaky_tests_count: number;
    confidence: number;
    flaky_tests: FlakyTest[];
  };
  classifications: Array<{
    classification_id: string;
    test_name: string;
    file_path: string;
    root_cause: string;
    confidence: string;
    evidence: string[];
    reasoning: string;
    suggested_fix_area: string;
  }>;
  fixes: Array<{
    fix_id: string;
    test_name: string;
    file_path: string;
    status: string;
    suggestions: Array<{
      suggestion_id: string;
      fix_type: string;
      description: string;
      rationale: string;
      confidence: number;
      diff?: {
        file_path: string;
        old_content?: string;
        new_content?: string;
        unified_diff: string;
        line_start?: number;
        line_end?: number;
      } | null;
    }>;
  }>;
  quarantine_audit?: {
    report_id: string;
    total_quarantined: number;
    diagnosed_count: number;
    fixable_count: number;
    unexplained_count: number;
    tests: AuditedTest[];
  };
  quarantine_list?: QuarantineEntry[];
  root_causes_chart?: Array<{ root_cause: string; count: number; percentage: number }>;
  metrics?: {
    total_tests: number;
    flaky_tests: number;
    flakiness_rate: number;
    active_quarantined: number;
    fixes_applied: number;
    avg_resolution_time: number;
  };
  github_metadata?: {
    owner: string;
    repo: string;
    clone_id: string;
    test_files_count: number;
    test_files: string[];
  };
  upload_metadata?: {
    upload_id: string;
    filename: string;
    test_files_count: number;
    test_files: string[];
  };
}

export const repositoryApi = {
  cloneAndAnalyze: (data: {
    repo_url: string;
    branch?: string;
    token?: string;
    num_runs?: number;
    test_pattern?: string;
  }, signal?: AbortSignal) => axios.post<PipelineAnalysisResult>(`${API_BASE}/repository/clone-and-analyze`, data, { signal }),

  uploadAndAnalyze: (formData: FormData) =>
    axios.post<PipelineAnalysisResult>(`${API_BASE}/repository/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  analyzeLocal: (data: {
    repo_path: string;
    num_runs?: number;
    test_pattern?: string;
  }) => axios.post<PipelineAnalysisResult>(`${API_BASE}/repository/analyze-local`, data),

  createPR: (data: {
    repo_url: string;
    token: string;
    file_path: string;
    new_content: string;
    title?: string;
    body: string;
    branch_name?: string;
    base_branch?: string;
  }) => axios.post(`${API_BASE}/repository/create-pr`, data),

  getSources: () => axios.get(`${API_BASE}/repository/sources`),
  getLatest: () => axios.get<PipelineAnalysisResult>(`${API_BASE}/repository/latest`),
};

