import axios from 'axios';

const API_BASE = '/api';

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

// Remediation API
export const remediationApi = {
  listFixes: () => axios.get(`${API_BASE}/remediation/fixes`),
  getFix: (fixId: string) => axios.get(`${API_BASE}/remediation/fixes/${fixId}`),
  applyFix: (fixId: string, suggestionId: string) => 
    axios.post(`${API_BASE}/remediation/fixes/${fixId}/apply`, { suggestion_id: suggestionId }),
};

// Audit API
export const auditApi = {
  listQuarantine: () => axios.get(`${API_BASE}/audit/quarantine`),
  getQuarantineReport: () => axios.get(`${API_BASE}/audit/quarantine/report`),
  updateQuarantineStatus: (id: string, status: string, notes?: string) =>
    axios.put(`${API_BASE}/audit/quarantine/${id}/status`, { status, notes }),
};

// Metrics API
export const metricsApi = {
  getSummary: () => axios.get(`${API_BASE}/metrics/summary`),
  getRootCauseBreakdown: () => axios.get(`${API_BASE}/metrics/root-causes`),
  getTrends: (days = 30) => axios.get(`${API_BASE}/metrics/trends?days=${days}`),
  getPerformance: () => axios.get(`${API_BASE}/metrics/performance`),
};
