export interface FlakyTest {
  test_name: string;
  file_path: string;
  flake_rate: number;
  total_runs: number;
  pass_count: number;
  fail_count: number;
  recent_failures: string[];
  status_history: string[];
  first_seen: string;
  last_seen: string;
}

export interface RootCause {
  type: string;
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
