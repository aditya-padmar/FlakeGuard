import type { PipelineAnalysisResult } from '../services/api';

export type RootCause = 'Timing / race' | 'Order dependency' | 'Data leakage' | 'Environment' | 'Unclassified';
export interface TestRecord {
  id: string;
  name: string;
  path: string;
  cause: RootCause;
  rate: number;
  history: ('pass' | 'fail')[];
  passCount: number;
  failCount: number;
  totalRuns: number;
  confidence: number | null;
  reasoning: string;
  evidence: string[];
  quarantine: string | null;
  fixStatus: 'validated' | 'proposed' | 'none';
  diff: string | null;
  newContent: string | null;
}
export interface WorkspaceData {
  mode: 'demo' | 'live';
  repository: string;
  branch: string;
  commit: string;
  framework: string;
  totalTests: number | null;
  tests: TestRecord[];
  analyzedAt: string | null;
  auditedCount: number;
  auditSources: { source: string; count: number | null }[];
}

export function parseGithubUrl(value: string): string | null {
  try {
    const url = new URL(value.trim().startsWith('github.com/') ? `https://${value.trim()}` : value.trim());
    const parts = url.pathname.replace(/\/$/, '').split('/').filter(Boolean);
    if (url.protocol !== 'https:' || url.hostname !== 'github.com' || url.port || url.username || url.password || url.search || url.hash || parts.length !== 2) return null;
    if (!/^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$/.test(parts[0]) || !/^[a-zA-Z0-9_.-]+$/.test(parts[1]) || /^\.+$/.test(parts[1])) return null;
    const repository = parts[1].replace(/\.git$/, '');
    if (!repository || /^\.+$/.test(repository)) return null;
    return `https://github.com/${parts[0]}/${repository}`;
  } catch { return null; }
}

export function normalizeCause(value: string): RootCause {
  const cause = value.toLowerCase();
  if (/timing|race|async|concurren/.test(cause)) return 'Timing / race';
  if (/order/.test(cause)) return 'Order dependency';
  if (/leak|state|pollut/.test(cause)) return 'Data leakage';
  if (/environ|network|external|resource/.test(cause)) return 'Environment';
  return 'Unclassified';
}

export function confidencePercent(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null;
  const numeric = typeof value === 'number' ? value : Number(value.replace('%', ''));
  if (!Number.isFinite(numeric)) return null;
  return Math.round(Math.max(0, Math.min(100, numeric <= 1 ? numeric * 100 : numeric)));
}

export function adaptAnalysis(result: PipelineAnalysisResult): WorkspaceData {
  type Audit = NonNullable<PipelineAnalysisResult['quarantine_audit']>['tests'][number];
  const inventory = new Map<string, TestRecord>();
  const knownPaths = new Map<string, Set<string>>();
  const quarantinePaths = new Map<string, Set<string>>();
  const addPath = (paths: Map<string, Set<string>>, name: string, path: string) => {
    if (!path) return;
    const matches = paths.get(name) ?? new Set<string>();
    matches.add(path);
    paths.set(name, matches);
  };
  for (const item of [...result.detection.flaky_tests, ...result.classifications, ...result.fixes, ...(result.quarantine_list ?? [])]) {
    addPath(knownPaths, item.test_name, item.file_path);
  }
  for (const item of result.quarantine_list ?? []) addPath(quarantinePaths, item.test_name, item.file_path);

  const createRecord = (name: string, path: string | null, id: string, audit?: Audit): TestRecord => {
    // Never attach file-qualified evidence or patches to an ambiguous name-only audit.
    const matches = (item: { test_name: string; file_path: string }) => path !== null && item.test_name === name && item.file_path === path;
    const test = result.detection.flaky_tests.find(matches);
    const classification = result.classifications.find(matches);
    const fix = result.fixes.find(matches);
    const suggestion = fix?.suggestions.find(item => item.diff?.unified_diff) ?? fix?.suggestions[0];
    const quarantine = result.quarantine_list?.find(matches);
    return {
      id, name, path: path || 'Path not returned',
      cause: normalizeCause(classification?.root_cause ?? audit?.root_cause ?? ''),
      rate: test ? Math.round(Math.max(0, Math.min(100, test.flake_rate * 100))) : 0,
      // The synchronous API exposes aggregates, not the chronological run sequence.
      history: [],
      passCount: test?.pass_count ?? 0,
      failCount: test?.fail_count ?? 0,
      totalRuns: test?.total_runs ?? 0,
      confidence: confidencePercent(classification?.confidence ?? audit?.confidence),
      reasoning: classification?.reasoning ?? audit?.quarantine_reason ?? (test ? 'No classification evidence was returned for this test.' : 'This suppressed test was not executed.'),
      evidence: classification?.evidence ?? [],
      quarantine: quarantine?.reason ?? audit?.quarantine_reason ?? audit?.source ?? null,
      fixStatus: fix?.status === 'verified' ? 'validated' : fix?.suggestions.length ? 'proposed' : 'none',
      diff: suggestion?.diff?.unified_diff ?? null,
      newContent: suggestion?.diff?.new_content ?? null,
    };
  };
  // Suppressed tests may never execute or have an audit report. Retain the union.
  for (const item of [...result.detection.flaky_tests, ...(result.quarantine_list ?? [])]) {
    const id = `${item.file_path}::${item.test_name}`;
    if (!inventory.has(id)) inventory.set(id, createRecord(item.test_name, item.file_path, id));
  }
  for (const [index, audit] of (result.quarantine_audit?.tests ?? []).entries()) {
    // Prefer an explicit quarantine identity over an unrelated executed namesake.
    // Otherwise all known file-qualified records must agree on the path.
    const paths = quarantinePaths.get(audit.test_name) ?? knownPaths.get(audit.test_name);
    const path = paths?.size === 1 ? [...paths][0] : null;
    const id = path === null ? `audit::${index}::${audit.test_name}` : `${path}::${audit.test_name}`;
    inventory.set(id, createRecord(audit.test_name, path, id, audit));
  }
  const tests = [...inventory.values()];
  return {
    mode: 'live', repository: result.repository, branch: result.branch, commit: result.commit_sha,
    framework: 'pytest pipeline', totalTests: result.metrics?.total_tests ?? null, tests,
    analyzedAt: result.completed_at, auditedCount: result.quarantine_audit?.total_quarantined ?? result.quarantine_list?.length ?? 0,
    auditSources: [
      { source: 'QUARANTINE.md', count: result.quarantine_audit?.tests.filter(test => /quarantine/i.test(test.source)).length ?? null },
      { source: '@pytest.mark.skip', count: null },
      { source: '@pytest.mark.xfail', count: null },
      { source: 'CI workflow retries', count: null },
    ],
  };
}

const sampleTests: Array<{ name: string; file: string; cause: RootCause; failed: number[]; confidence: number | null; quarantine?: string; before: string; after: string; reasoning: string }> = [
  { name: 'test_payment_webhook', file: 'test_payment.py', cause: 'Timing / race', failed: [2, 5, 8], confidence: 91, before: '    time.sleep(2)', after: '    wait_until(lambda: payment.status == "confirmed", timeout=10)', reasoning: 'A fixed two-second sleep assumes the webhook finishes before the assertion. Under CI load the callback arrives late. Wait for an observable condition instead.' },
  { name: 'test_user_session_cleanup', file: 'test_auth.py', cause: 'Data leakage', failed: [1, 6], confidence: 96, before: '    session = shared_session', after: '    session = isolated_session()', reasoning: 'A shared session retains authentication state between tests. Allocate an isolated session fixture with teardown for each test.' },
  { name: 'test_cart_total', file: 'test_checkout.py', cause: 'Order dependency', failed: [0, 4, 7, 9], confidence: 94, before: '    cart = global_cart', after: '    cart = Cart(items=[])', reasoning: 'The assertion depends on a cart populated by a previous test. Construct a fresh cart so execution order does not change the result.', quarantine: '@pytest.mark.skip · unstable on CI' },
  { name: 'test_inventory_sync', file: 'test_inventory.py', cause: 'Timing / race', failed: [3], confidence: 89, before: '    time.sleep(1)', after: '    sync_task.result(timeout=10)', reasoning: 'The inventory worker is asynchronous. Waiting on its completion primitive removes the race between the worker and the assertion.' },
  { name: 'test_exchange_rate', file: 'test_currency.py', cause: 'Environment', failed: [1, 3, 6], confidence: 87, before: '    rate = fetch_live_rate("USD", "EUR")', after: '    rate = mocked_rate_client.get("USD", "EUR")', reasoning: 'An external exchange-rate endpoint introduces network latency and changing data. Use a deterministic fixture for this unit test.', quarantine: '@pytest.mark.xfail · upstream timeout' },
  { name: 'test_cache_invalidation', file: 'test_cache.py', cause: 'Timing / race', failed: [4, 8], confidence: 92, before: '    time.sleep(cache.ttl)', after: '    clock.advance(cache.ttl + 1)', reasoning: 'Wall-clock expiry races with the cache lookup. Advance an injected clock explicitly to test expiry deterministically.' },
  { name: 'test_notification_delivery', file: 'test_notifications.py', cause: 'Order dependency', failed: [2], confidence: 85, before: '    assert queue.size() == 1', after: '    assert isolated_queue.size() == 1', reasoning: 'The notification queue contains messages from earlier tests. Scope the queue to an individual test and clear it during teardown.', quarantine: 'QUARANTINE.md · intermittent queue state' },
  { name: 'test_report_generation', file: 'test_reports.py', cause: 'Unclassified', failed: [5, 9], confidence: null, before: '', after: '', reasoning: 'The evidence does not yet isolate a root cause. Additional runs and diagnostic traces are required before recommending a patch.' },
];

export function createDemoData(): WorkspaceData {
  return {
    mode: 'demo', repository: 'acme / commerce-api', branch: 'main', commit: 'a3f8c21', framework: 'Python 3.11 / pytest', totalTests: 126, analyzedAt: null, auditedCount: 3,
    auditSources: [{ source: 'QUARANTINE.md', count: 1 }, { source: '@pytest.mark.skip', count: 1 }, { source: '@pytest.mark.xfail', count: 1 }, { source: 'CI workflow retries', count: 2 }],
    tests: sampleTests.map((test, index) => ({
      id: `sample-${index}`, name: test.name, path: `tests/${test.file}`, cause: test.cause, rate: test.failed.length * 10,
      history: Array.from({ length: 10 }, (_, run) => test.failed.includes(run) ? 'fail' : 'pass'), passCount: 10 - test.failed.length, failCount: test.failed.length, totalRuns: 10,
      confidence: test.confidence, reasoning: test.reasoning, evidence: test.before ? [`tests/${test.file}:24`, test.before.trim()] : [], quarantine: test.quarantine ?? null,
      fixStatus: index < 5 ? 'validated' : index < 7 ? 'proposed' : 'none',
      diff: test.before ? `--- a/tests/${test.file}\n+++ b/tests/${test.file}\n@@ -24,1 +24,1 @@\n-${test.before}\n+${test.after}\n` : null,
      newContent: null,
    })),
  };
}
