export interface FlakyTest {
  test_name: string;
  file_path: string;
  flake_rate: number;
  total_runs: number;
  pass_count: number;
  fail_count: number;
  recent_failures: string[];
  status_history: string[];
  first_seen?: string;
  last_seen?: string;
}

export interface RootCause {
  type?: string;
  cause: string;
  count: number;
  percentage: number;
}

export interface QuarantineEntry {
  quarantine_id: string;
  test_name: string;
  file_path: string;
  reason: string;
  root_cause?: string;
  status: 'active' | 'under_review' | 'resolved' | 'removed';
  quarantined_at: string;
  runs_since_quarantine: number;
  runs_until_review: number;
}

export interface FixSuggestion {
  suggestion_id: string;
  fix_type: string;
  description: string;
  rationale: string;
  confidence: number;
  estimated_effort: string;
}

export interface Fix {
  fix_id: string;
  test_name: string;
  file_path: string;
  status: 'proposed' | 'accepted' | 'rejected' | 'applied' | 'verified';
  suggestions: FixSuggestion[];
  primary_suggestion_id: string;
  applied_at?: string;
  verified_runs: number;
}

export interface Metrics {
  total_flaky_tests: number;
  tests_quarantined: number;
  tests_fixed: number;
  pending_classification: number;
  average_time_to_fix: string;
  flake_rate: string;
  most_common_root_cause: string;
  resolution_rate: string;
}

export interface TrendData {
  date: string;
  flaky_tests_detected: number;
  tests_fixed: number;
  quarantine_additions: number;
}

// ── F3 types ──────────────────────────────────────────────────────────────────

export interface EvidenceItem {
  file: string;
  line?: number;
  reason?: string;
}

export interface EvidenceValidationDetail {
  valid: boolean;
  location: string | null;
  message: string;
  file_exists: boolean;
  line_exists: boolean | null;
  code_snippet: string | null;
  reason?: string;
}

export interface EvidenceValidationResult {
  valid: boolean;
  locations: string[];
  message: string;
  details: EvidenceValidationDetail[];
}

export interface StrategyResult {
  root_cause: string;
  strategies: string[];
  descriptions: string[];
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

export interface RetryDetail {
  mechanism: string;
  retry_count: number;
  line: number;
}

export interface RetrySource {
  retry_detected: boolean;
  source: string;
  file: string | null;
  retry_count: number;
  details: RetryDetail[];
}

export interface RetryDetectionResult {
  github_actions: RetrySource;
  pytest_config: RetrySource;
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

export interface QuarantineAuditReport {
  report_id: string;
  generated_at: string;
  quarantined_tests: AuditedTest[];
  total_quarantined: number;
  diagnosed_count: number;
  fixable_count: number;
  unexplained_count: number;
  summary: Record<string, unknown>;
}

export interface QuarantineReportSummary {
  total_quarantined: number;
  active_count: number;
  under_review_count: number;
  resolved_count: number;
  average_quarantine_duration: number;
  oldest_quarantine_days: number;
}

export interface FullAuditReport {
  quarantine_audit: QuarantineAuditReport | null;
  quarantine_report: QuarantineReportSummary;
  skip_detections: { detections: SkipDetection[]; summary: SkipSummary };
  retry_configuration: RetryDetectionResult;
}
