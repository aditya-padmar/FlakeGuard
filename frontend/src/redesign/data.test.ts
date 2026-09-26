import { describe, expect, it } from 'vitest';
import { adaptAnalysis, confidencePercent, createDemoData, normalizeCause, parseGithubUrl } from './data';
import type { PipelineAnalysisResult } from '../services/api';

const emptyResult: PipelineAnalysisResult = {
  pipeline_id: 'test', source_type: 'github', repository: 'https://github.com/acme/api', branch: 'main', commit_sha: 'abc',
  started_at: '', completed_at: '', runs: 10,
  detection: { total_runs: 10, flaky_tests_count: 0, confidence: 0, flaky_tests: [] },
  classifications: [], fixes: [],
};

describe('GitHub repository validation', () => {
  it.each(['https://github.com/acme/api', 'github.com/acme/api', ' https://github.com/acme/api.git/ '])('normalizes %s', value => {
    expect(parseGithubUrl(value)).toBe('https://github.com/acme/api');
  });
  it.each(['', 'https://github.com', 'https://github.com/acme/api/tree/main', 'https://github.com.evil.test/acme/api', 'http://github.com/acme/api', 'https://user:secret@github.com/acme/api', 'https://github.com/acme/api?q=x', 'javascript:alert(1)', 'https://gitlab.com/acme/api', 'https://github.com/acme/..', 'https://github.com/acme/.git'])('rejects %s', value => {
    expect(parseGithubUrl(value)).toBeNull();
  });
});

describe('classification normalization', () => {
  it('maps supported root causes and leaves unknown classifications explicit', () => {
    expect(normalizeCause('timing_race')).toBe('Timing / race');
    expect(normalizeCause('order_dependency')).toBe('Order dependency');
    expect(normalizeCause('state_leakage')).toBe('Data leakage');
    expect(normalizeCause('network_environment')).toBe('Environment');
    expect(normalizeCause('')).toBe('Unclassified');
  });
  it('handles numeric and percentage confidence without inventing categorical scores', () => {
    expect(confidencePercent('0.91')).toBe(91);
    expect(confidencePercent('91%')).toBe(91);
    expect(confidencePercent(0)).toBe(0);
    expect(confidencePercent('high')).toBeNull();
    expect(confidencePercent(undefined)).toBeNull();
  });
});

const quarantineEntry = (file_path: string, test_name = 'test_shared') => ({
  quarantine_id: file_path, test_name, file_path, reason: `Suppressed in ${file_path}`, status: 'active', quarantined_at: '',
});
const auditReport = (test_name = 'test_shared'): Required<NonNullable<PipelineAnalysisResult['quarantine_audit']>> => ({
  report_id: 'q', total_quarantined: 1, diagnosed_count: 1, fixable_count: 1, unexplained_count: 0,
  tests: [{ test_name, diagnosed: true, fixable: true, status: 'active', root_cause: 'timing', confidence: '0.8', fix_strategy: 'wait', quarantine_reason: 'Audit reason', quarantined_at: null, source: 'QUARANTINE.md' }],
});
const classification = (file_path: string): PipelineAnalysisResult['classifications'][number] => ({
  classification_id: file_path, test_name: 'test_shared', file_path, root_cause: 'state_leakage', confidence: '0.95', evidence: [`${file_path}:24`], reasoning: 'Isolate the fixture', suggested_fix_area: 'fixture',
});
const proposedFix = (file_path: string): PipelineAnalysisResult['fixes'][number] => ({
  fix_id: file_path, test_name: 'test_shared', file_path, status: 'proposed', suggestions: [{ suggestion_id: 's', fix_type: 'fixture', description: '', rationale: '', confidence: .9, diff: { file_path, unified_diff: '-shared\n+isolated', new_content: 'isolated()' } }],
});

describe('real analysis adapter', () => {
  it('clears stale demo data when the backend returns empty collections', () => {
    const data = adaptAnalysis(emptyResult);
    expect(data.mode).toBe('live');
    expect(data.tests).toEqual([]);
    expect(data.auditedCount).toBe(0);
    expect(data.totalTests).toBeNull();
  });
  it.each([{}, null])('accepts an empty backend audit without inventing source counts', quarantine_audit => {
    const data = adaptAnalysis({ ...emptyResult, quarantine_audit });
    expect(data.tests).toEqual([]);
    expect(data.auditedCount).toBe(0);
    expect(data.auditSources.every(source => source.count === null)).toBe(true);
  });
  it('preserves a legitimate zero total', () => {
    expect(adaptAnalysis({ ...emptyResult, metrics: { total_tests: 0, flaky_tests: 0, flakiness_rate: 0, active_quarantined: 0, fixes_applied: 0, avg_resolution_time: 0 } }).totalTests).toBe(0);
  });
  it('retains the first duplicate match in every indexed collection', () => {
    const file_path = 'tests/a.py';
    const test = { test_name: 'test_shared', file_path, flake_rate: .2, total_runs: 10, pass_count: 8, fail_count: 2, recent_failures: [] };
    const firstFix = proposedFix(file_path);
    firstFix.suggestions.unshift({ ...firstFix.suggestions[0], suggestion_id: 'no-diff', diff: null });
    const data = adaptAnalysis({ ...emptyResult,
      detection: { ...emptyResult.detection, flaky_tests: [test, { ...test, flake_rate: .9, pass_count: 1, fail_count: 9 }] },
      classifications: [classification(file_path), { ...classification(file_path), reasoning: 'Wrong duplicate', root_cause: 'environment' }],
      fixes: [firstFix, { ...proposedFix(file_path), status: 'verified' }],
      quarantine_list: [quarantineEntry(file_path), { ...quarantineEntry(file_path), reason: 'Wrong duplicate' }],
      quarantine_audit: auditReport(),
    });
    expect(data.tests).toHaveLength(1);
    expect(data.tests[0]).toMatchObject({ rate: 20, passCount: 8, failCount: 2, cause: 'Data leakage', reasoning: 'Isolate the fixture', fixStatus: 'proposed', diff: '-shared\n+isolated', quarantine: 'Suppressed in tests/a.py' });
  });
  it.each([500, 2000])('joins %i records correctly with linear identity lookup work', count => {
    let identityReads = 0;
    const track = <T extends { test_name: string; file_path: string }>(item: T): T => new Proxy(item, {
      get(target, key, receiver) {
        if (key === 'test_name' || key === 'file_path') identityReads += 1;
        return Reflect.get(target, key, receiver);
      },
    });
    const identities = Array.from({ length: count }, (_, index) => ({ test_name: `test_shared_${index % 5}`, file_path: `tests/${index}.py` }));
    const data = adaptAnalysis({ ...emptyResult,
      detection: { ...emptyResult.detection, flaky_tests: identities.map(identity => track({ ...identity, flake_rate: .2, total_runs: 10, pass_count: 8, fail_count: 2, recent_failures: [] })) },
      classifications: identities.map(identity => track({ ...classification(identity.file_path), ...identity, reasoning: `Diagnosis for ${identity.file_path}` })).reverse(),
      fixes: identities.map(identity => track({ ...proposedFix(identity.file_path), ...identity })).reverse(),
      quarantine_list: identities.map(identity => track(quarantineEntry(identity.file_path, identity.test_name))),
    });
    expect(data.tests.map(test => ({ id: test.id, reasoning: test.reasoning, quarantine: test.quarantine, diff: test.diff, passCount: test.passCount }))).toEqual(identities.map(identity => ({
      id: `${identity.file_path}::${identity.test_name}`, reasoning: `Diagnosis for ${identity.file_path}`, quarantine: `Suppressed in ${identity.file_path}`, diff: '-shared\n+isolated', passCount: 8,
    })));
    // Deterministic work budget, not a wall-clock assertion that flakes on slow CI.
    expect(identityReads).toBeLessThanOrEqual(count * 50);
  });
  it('joins same-name tests by file, preserves real evidence and does not fabricate run order', () => {
    const data = adaptAnalysis({ ...emptyResult,
      detection: { ...emptyResult.detection, flaky_tests_count: 1, flaky_tests: [{ test_name: 'test_a', file_path: 'tests/a.py', flake_rate: .2, total_runs: 10, pass_count: 8, fail_count: 2, recent_failures: [] }] },
      classifications: [{ classification_id: 'c', test_name: 'test_a', file_path: 'tests/b.py', root_cause: 'timing', confidence: '0.99', evidence: ['wrong file'], reasoning: 'wrong', suggested_fix_area: '' }],
      fixes: [{ fix_id: 'f', test_name: 'test_a', file_path: 'tests/a.py', status: 'proposed', suggestions: [{ suggestion_id: 's', fix_type: 'wait', description: '', rationale: '', confidence: .9, diff: { file_path: 'tests/a.py', unified_diff: '-sleep\n+wait', new_content: 'wait()' } }] }],
    });
    expect(data.tests[0]).toMatchObject({ rate: 20, history: [], confidence: null, evidence: [], cause: 'Unclassified', fixStatus: 'proposed', diff: '-sleep\n+wait', newContent: 'wait()' });
  });
  it('keeps an executed namesake separate from the quarantined file and preserves its diagnosis and patch', () => {
    const data = adaptAnalysis({ ...emptyResult,
      detection: { ...emptyResult.detection, flaky_tests_count: 1, flaky_tests: [{ test_name: 'test_shared', file_path: 'tests/a.py', flake_rate: .2, total_runs: 10, pass_count: 8, fail_count: 2, recent_failures: [] }] },
      quarantine_list: [quarantineEntry('tests/b.py')], quarantine_audit: auditReport(),
      classifications: [classification('tests/b.py')], fixes: [proposedFix('tests/b.py')],
    });
    expect(data.tests).toHaveLength(2);
    expect(data.tests.find(test => test.path === 'tests/a.py')).toMatchObject({ totalRuns: 10, quarantine: null, cause: 'Unclassified', diff: null });
    expect(data.tests.find(test => test.path === 'tests/b.py')).toMatchObject({ totalRuns: 0, quarantine: 'Suppressed in tests/b.py', cause: 'Data leakage', confidence: 95, reasoning: 'Isolate the fixture', evidence: ['tests/b.py:24'], fixStatus: 'proposed', diff: '-shared\n+isolated', newContent: 'isolated()' });
  });
  it.each([undefined, { ...auditReport(), tests: [], total_quarantined: 0 }])('retains list-only exclusions with an absent or empty audit', quarantine_audit => {
    const data = adaptAnalysis({ ...emptyResult, quarantine_audit,
      quarantine_list: [quarantineEntry('tests/a.py'), quarantineEntry('tests/b.py')],
      classifications: [classification('tests/b.py')], fixes: [{ ...proposedFix('tests/b.py'), status: 'verified' }],
    });
    expect(data.tests).toHaveLength(2);
    expect(data.tests.map(test => test.id)).toEqual(['tests/a.py::test_shared', 'tests/b.py::test_shared']);
    expect(data.tests[0]).toMatchObject({ totalRuns: 0, quarantine: 'Suppressed in tests/a.py', cause: 'Unclassified', fixStatus: 'none', diff: null });
    expect(data.tests[1]).toMatchObject({ totalRuns: 0, cause: 'Data leakage', confidence: 95, fixStatus: 'validated', diff: '-shared\n+isolated' });
    if (!quarantine_audit) expect(data.auditedCount).toBe(2);
  });
  it('joins audit-only records to an unambiguous classification and fix even without a quarantine list', () => {
    const data = adaptAnalysis({ ...emptyResult, quarantine_audit: auditReport(), classifications: [classification('tests/b.py')], fixes: [proposedFix('tests/b.py')] });
    expect(data.tests).toHaveLength(1);
    expect(data.tests[0]).toMatchObject({ path: 'tests/b.py', totalRuns: 0, quarantine: 'Audit reason', cause: 'Data leakage', evidence: ['tests/b.py:24'], fixStatus: 'proposed', diff: '-shared\n+isolated' });
  });
  it('preserves ambiguous name-only audits without borrowing either file’s evidence or fix', () => {
    const audit = auditReport();
    audit.tests.push({ ...audit.tests[0], source: '@pytest.mark.skip', quarantine_reason: 'Second audit' });
    const data = adaptAnalysis({ ...emptyResult, quarantine_audit: audit,
      quarantine_list: [quarantineEntry('tests/a.py'), quarantineEntry('tests/b.py')],
      classifications: [classification('tests/a.py'), classification('tests/b.py')], fixes: [proposedFix('tests/a.py'), proposedFix('tests/b.py')],
    });
    expect(data.tests).toHaveLength(4);
    expect(new Set(data.tests.map(test => test.id)).size).toBe(4);
    const unresolved = data.tests.filter(test => test.path === 'Path not returned');
    expect(unresolved).toHaveLength(2);
    unresolved.forEach(test => expect(test).toMatchObject({ totalRuns: 0, cause: 'Timing / race', confidence: 80, evidence: [], fixStatus: 'none', diff: null }));
    expect(unresolved.map(test => test.quarantine)).toEqual(['Audit reason', 'Second audit']);
  });
  it('does not infer an audit path from conflicting classification and fix identities', () => {
    const data = adaptAnalysis({ ...emptyResult, quarantine_audit: auditReport(), classifications: [classification('tests/a.py')], fixes: [proposedFix('tests/b.py')] });
    expect(data.tests).toHaveLength(1);
    expect(data.tests[0]).toMatchObject({ path: 'Path not returned', evidence: [], fixStatus: 'none', diff: null });
  });
  it('deduplicates a test present in detection, quarantine list, and audit without losing execution counts', () => {
    const data = adaptAnalysis({ ...emptyResult,
      detection: { ...emptyResult.detection, flaky_tests_count: 1, flaky_tests: [{ test_name: 'test_shared', file_path: 'tests/a.py', flake_rate: .2, total_runs: 10, pass_count: 8, fail_count: 2, recent_failures: [] }] },
      quarantine_list: [quarantineEntry('tests/a.py')], quarantine_audit: auditReport(),
    });
    expect(data.tests).toHaveLength(1);
    expect(data.tests[0]).toMatchObject({ totalRuns: 10, passCount: 8, failCount: 2, rate: 20, cause: 'Timing / race', quarantine: 'Suppressed in tests/a.py' });
  });
  it('retains suppressed tests that were never executed without marking them validated', () => {
    const data = adaptAnalysis({ ...emptyResult, quarantine_audit: { report_id: 'q', total_quarantined: 1, diagnosed_count: 1, fixable_count: 1, unexplained_count: 0, tests: [{ test_name: 'test_skipped', diagnosed: true, fixable: true, status: 'active', root_cause: 'timing', confidence: 'high', fix_strategy: 'wait', quarantine_reason: 'unstable', quarantined_at: null, source: 'QUARANTINE.md' }] } });
    expect(data.tests[0]).toMatchObject({ totalRuns: 0, history: [], quarantine: 'unstable', fixStatus: 'none' });
  });
});

describe('sample dataset integrity', () => {
  it('keeps all dashboard metrics consistent with sample records', () => {
    const data = createDemoData();
    expect(data.totalTests).toBe(126);
    expect(data.tests).toHaveLength(8);
    expect(data.tests.filter(test => test.confidence !== null)).toHaveLength(7);
    expect(data.tests.filter(test => test.fixStatus === 'validated')).toHaveLength(5);
    expect(data.tests.filter(test => test.quarantine)).toHaveLength(3);
    data.tests.forEach(test => {
      expect(test.history.filter(status => status === 'fail').length).toBe(test.failCount);
      expect(test.rate).toBe(test.failCount / test.totalRuns * 100);
    });
  });
  it('returns fresh records for each demo session', () => {
    const data = createDemoData();
    data.tests[0].fixStatus = 'none';
    expect(createDemoData().tests[0].fixStatus).toBe('validated');
  });
});
