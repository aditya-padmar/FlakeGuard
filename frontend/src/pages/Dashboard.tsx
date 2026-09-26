import { useState, useEffect } from 'react';
import TestInventory from '../components/TestInventory';
import RootCauseChart from '../components/RootCauseChart';
import MetricsPanel from '../components/MetricsPanel';
import FixViewer from '../components/FixViewer';
import QuarantineTable from '../components/QuarantineTable';
import RepositoryIngestion from '../components/RepositoryIngestion';
import GitHubPRModal from '../components/GitHubPRModal';
import type { FlakyTest, RootCause, Fix, QuarantineEntry, Metrics } from '../types';
import type { PipelineAnalysisResult } from '../services/api';
import demoData from '../mock/demo-data.json';

export default function Dashboard() {
  const [selectedTest, setSelectedTest] = useState<FlakyTest | null>(null);
  const [flakyTests, setFlakyTests] = useState<FlakyTest[]>([]);
  const [rootCauses, setRootCauses] = useState<RootCause[]>([]);
  const [fixes, setFixes] = useState<Fix[]>([]);
  const [quarantine, setQuarantine] = useState<QuarantineEntry[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [activeTab, setActiveTab] = useState<'tests' | 'quarantine' | 'fixes'>('tests');

  // Ingestion & Source state
  const [activeSourceInfo, setActiveSourceInfo] = useState<{
    type: 'github' | 'upload' | 'local';
    name: string;
    branch?: string;
  } | null>({
    type: 'local',
    name: 'sample-repo (Pre-loaded)',
    branch: 'main'
  });

  // GitHub PR Modal state
  const [prModalOpen, setPrModalOpen] = useState(false);
  const [selectedFixForPR, setSelectedFixForPR] = useState<{
    testName: string;
    filePath: string;
    diff?: string;
    newContent?: string;
  } | null>(null);

  useEffect(() => {
    // Load default demo/sample data
    setFlakyTests(demoData.flakyTests as FlakyTest[]);
    setRootCauses(demoData.rootCauses as RootCause[]);
    setFixes(demoData.fixes as Fix[]);
    setQuarantine(demoData.quarantine as QuarantineEntry[]);
    setMetrics(demoData.metrics as Metrics);
  }, []);

  const handleAnalysisComplete = (result: PipelineAnalysisResult) => {
    // 1. Update source info pill
    setActiveSourceInfo({
      type: result.source_type,
      name: result.repository,
      branch: result.branch
    });

    // 2. Map Flaky Tests
    if (result.detection?.flaky_tests) {
      const mappedTests: FlakyTest[] = result.detection.flaky_tests.map((t: any) => ({
        test_name: t.test_name,
        file_path: t.file_path,
        flake_rate: t.flake_rate || 0.5,
        total_runs: t.total_runs || result.runs || 5,
        pass_count: t.pass_count || 0,
        fail_count: t.fail_count || 0,
        recent_failures: t.recent_failures || [],
        status_history: ['failed', 'passed']
      }));
      setFlakyTests(mappedTests);
      if (mappedTests.length > 0) {
        setSelectedTest(mappedTests[0]);
      }
    }

    // 3. Map Root Causes
    if (result.root_causes_chart && result.root_causes_chart.length > 0) {
      setRootCauses(result.root_causes_chart.map((rc: any) => ({
        cause: rc.root_cause,
        count: rc.count,
        percentage: rc.percentage
      })));
    } else if (result.classifications?.length) {
      const counts: Record<string, number> = {};
      result.classifications.forEach((c) => {
        counts[c.root_cause] = (counts[c.root_cause] || 0) + 1;
      });
      const total = result.classifications.length;
      setRootCauses(Object.entries(counts).map(([cause, count]) => ({
        cause,
        count,
        percentage: Math.round((count / total) * 100)
      })));
    }

    // 4. Map Fixes
    if (result.fixes && result.fixes.length > 0) {
      const mappedFixes: Fix[] = result.fixes.map((f: any) => {
        const primaryId = f.suggestions?.[0]?.suggestion_id || 's1';
        return {
          fix_id: f.fix_id || `fix-${f.test_name}`,
          test_name: f.test_name,
          file_path: f.file_path,
          status: (f.status as any) || 'proposed',
          primary_suggestion_id: primaryId,
          verified_runs: 0,
          suggestions: (f.suggestions || []).map((s: any) => ({
            suggestion_id: s.suggestion_id,
            fix_type: s.fix_type || 'code_change',
            description: s.description || 'Remediate flaky test',
            rationale: s.rationale || 'Addresses identified root cause',
            confidence: s.confidence || 0.85,
            estimated_effort: s.estimated_effort || 'low',
            diff: s.diff || null
          }))
        };
      });
      setFixes(mappedFixes);
    }

    // 5. Map Quarantine
    if (result.quarantine_list && result.quarantine_list.length > 0) {
      setQuarantine(result.quarantine_list.map((q: any) => ({
        quarantine_id: q.quarantine_id,
        test_name: q.test_name,
        file_path: q.file_path,
        reason: q.reason,
        status: (q.status as any) || 'active',
        quarantined_at: q.quarantined_at || new Date().toISOString(),
        runs_since_quarantine: 0,
        runs_until_review: 5
      })));
    }

    // 6. Map Metrics
    if (result.metrics) {
      const topCause = result.root_causes_chart?.[0]?.root_cause || 'Timing';
      setMetrics({
        total_flaky_tests: result.metrics.flaky_tests,
        tests_quarantined: result.metrics.active_quarantined,
        tests_fixed: result.metrics.fixes_applied,
        pending_classification: 0,
        average_time_to_fix: `${result.metrics.avg_resolution_time}m`,
        flake_rate: `${result.metrics.flakiness_rate}%`,
        most_common_root_cause: topCause.toUpperCase(),
        resolution_rate: '100%'
      });
    }

    // Switch to Flaky Tests tab
    setActiveTab('tests');
  };

  const handleSelectTest = (test: FlakyTest) => {
    setSelectedTest(test);
  };

  const handleApplyFix = (suggestionId: string) => {
    if (!selectedTest) return;
    const fix = fixes.find((f) => f.test_name === selectedTest.test_name);
    if (fix) {
      console.log('Applying fix:', suggestionId);
      setFixes(fixes.map((f) => (f.fix_id === fix.fix_id ? { ...f, status: 'applied' } : f)));
    }
  };

  const handleRejectFix = () => {
    if (!selectedTest) return;
    const fix = fixes.find((f) => f.test_name === selectedTest.test_name);
    if (fix) {
      setFixes(fixes.map((f) => (f.fix_id === fix.fix_id ? { ...f, status: 'rejected' } : f)));
    }
  };

  const handleReviewQuarantine = (entry: QuarantineEntry) => {
    console.log('Reviewing quarantine entry:', entry);
  };

  const handleOpenPRModalForTest = (fix: Fix) => {
    const primarySuggestion = fix.suggestions?.find(
      (s) => s.suggestion_id === fix.primary_suggestion_id
    ) || fix.suggestions?.[0];
    const diff = (primarySuggestion as any)?.diff?.unified_diff;
    const newContent = (primarySuggestion as any)?.diff?.new_content;

    setSelectedFixForPR({
      testName: fix.test_name,
      filePath: fix.file_path,
      diff: diff,
      newContent: newContent
    });
    setPrModalOpen(true);
  };

  const selectedFix = selectedTest
    ? fixes.find((f) => f.test_name === selectedTest.test_name)
    : null;

  return (
    <div className="dashboard">
      {/* Repository Ingestion Card: GitHub Clone / Upload / Local Analysis */}
      <RepositoryIngestion
        onAnalysisComplete={handleAnalysisComplete}
        activeSourceInfo={activeSourceInfo}
      />

      <div className="dashboard-header">
        <div className="tabs">
          <button
            className={activeTab === 'tests' ? 'active' : ''}
            onClick={() => setActiveTab('tests')}
          >
            Flaky Tests ({flakyTests.length})
          </button>
          <button
            className={activeTab === 'quarantine' ? 'active' : ''}
            onClick={() => setActiveTab('quarantine')}
          >
            Quarantine ({quarantine.length})
          </button>
          <button
            className={activeTab === 'fixes' ? 'active' : ''}
            onClick={() => setActiveTab('fixes')}
          >
            Fix Suggestions ({fixes.length})
          </button>
        </div>
      </div>

      {metrics && <MetricsPanel metrics={metrics} />}

      <div className="dashboard-content">
        <div className="main-content">
          {activeTab === 'tests' && (
            <TestInventory
              tests={flakyTests}
              onSelectTest={handleSelectTest}
            />
          )}

          {activeTab === 'quarantine' && (
            <QuarantineTable
              entries={quarantine}
              onReview={handleReviewQuarantine}
            />
          )}

          {activeTab === 'fixes' && (
            <div className="fixes-list">
              <h2>Fix Suggestions & Code Diffs</h2>
              {fixes.map((fix) => (
                <div key={fix.fix_id} style={{ position: 'relative' }}>
                  <FixViewer
                    fix={fix}
                    onApply={handleApplyFix}
                    onReject={handleRejectFix}
                  />
                  <div style={{ margin: '-0.75rem 0 1.5rem', display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
                      onClick={() => handleOpenPRModalForTest(fix)}
                    >
                      <span>🐙 Create GitHub PR</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="side-content">
          <RootCauseChart data={rootCauses} />

          {selectedFix && (
            <div className="selected-fix">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0 }}>Selected Test Fix</h3>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}
                  onClick={() => handleOpenPRModalForTest(selectedFix)}
                >
                  🐙 PR to GitHub
                </button>
              </div>
              <FixViewer
                fix={selectedFix}
                onApply={handleApplyFix}
                onReject={handleRejectFix}
              />
            </div>
          )}
        </div>
      </div>

      {/* GitHub PR Modal */}
      {selectedFixForPR && (
        <GitHubPRModal
          isOpen={prModalOpen}
          onClose={() => setPrModalOpen(false)}
          defaultRepoUrl={activeSourceInfo?.type === 'github' ? activeSourceInfo.name : 'https://github.com/aditya-padmar/FlakeGuard'}
          testName={selectedFixForPR.testName}
          filePath={selectedFixForPR.filePath}
          unifiedDiff={selectedFixForPR.diff}
          newContent={selectedFixForPR.newContent}
        />
      )}
    </div>
  );
}
