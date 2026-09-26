import { useState, useCallback } from 'react';
import { auditApi } from '../services/api';
import type { AuditReport, AuditedTest, SkipDetection, SkipSummary, RetryDetectionResult } from '../services/api';

// ── helpers ────────────────────────────────────────────────────────────────────

function statusColor(status: string) {
  switch (status) {
    case 'diagnosed_but_still_quarantined': return 'var(--color-warning)';
    case 'unexplained': return 'var(--color-error)';
    case 'ready_to_unquarantine': return 'var(--color-success)';
    default: return 'var(--color-text)';
  }
}

// ── sub-components ─────────────────────────────────────────────────────────────

function AuditedTestsTable({ tests }: { tests: AuditedTest[] }) {
  if (!tests.length) return <p className="muted">No quarantined tests found.</p>;
  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Test</th>
            <th>Diagnosed</th>
            <th>Fixable</th>
            <th>Status</th>
            <th>Root Cause</th>
            <th>Strategy</th>
          </tr>
        </thead>
        <tbody>
          {tests.map(t => (
            <tr key={t.test_name}>
              <td className="test-name">{t.test_name}</td>
              <td>{t.diagnosed ? '✓' : '✗'}</td>
              <td>{t.fixable ? '✓' : '—'}</td>
              <td>
                <span className="status-badge" style={{ color: statusColor(t.status) }}>
                  {t.status.replace(/_/g, ' ')}
                </span>
              </td>
              <td>{t.root_cause ?? '—'}</td>
              <td>{t.fix_strategy ? <code>{t.fix_strategy}</code> : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SkipPanel({ data }: { data: { detections: SkipDetection[]; summary: SkipSummary } }) {
  const { detections, summary } = data;
  return (
    <div>
      <div className="stat-row">
        <span className="stat-item"><strong>{summary.total_suppressed}</strong> suppressed tests</span>
        <span className="stat-item"><strong>{summary.skip_count}</strong> skips</span>
        <span className="stat-item"><strong>{summary.xfail_count}</strong> xfails</span>
      </div>
      {detections.length > 0 ? (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Test</th>
                <th>File</th>
                <th>Line</th>
                <th>Type</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((d, i) => (
                <tr key={i}>
                  <td className="test-name">{d.test_name}</td>
                  <td><code>{d.file}</code></td>
                  <td>{d.line}</td>
                  <td><span className="status-badge">{d.suppression_type}</span></td>
                  <td>{d.reason ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="muted">No skip/xfail markers detected.</p>
      )}
    </div>
  );
}

function RetryPanel({ data }: { data: RetryDetectionResult }) {
  const { github_actions, pytest_config, summary } = data;
  return (
    <div>
      <div className="stat-row">
        <span className="stat-item">
          Retry detected: <strong>{summary.retry_detected ? 'Yes' : 'No'}</strong>
        </span>
        {summary.retry_detected && (
          <span className="stat-item">Sources: <strong>{summary.sources.join(', ')}</strong></span>
        )}
      </div>
      <div className="retry-sources">
        {[github_actions, pytest_config].map(src => (
          <div key={src.source} className={`retry-source-card ${src.retry_detected ? 'retry-found' : ''}`}>
            <strong>{src.source}</strong>
            {src.retry_detected ? (
              <>
                <p>File: <code>{src.file}</code></p>
                <p>Max retry count: <strong>{src.retry_count}</strong></p>
                {src.details.map((d, i) => (
                  <p key={i} className="retry-detail">
                    {d.mechanism} (×{d.retry_count}, line {d.line})
                  </p>
                ))}
              </>
            ) : (
              <p className="muted">Not detected</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── page ──────────────────────────────────────────────────────────────────────

type Tab = 'report' | 'skips' | 'retries';

export default function AuditPage() {
  const [repoPath, setRepoPath] = useState('sample-repo');
  const [quarantinePath, setQuarantinePath] = useState('sample-repo/QUARANTINE.md');
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('report');
  const [runLoading, setRunLoading] = useState(false);
  const [runResult, setRunResult] = useState<string | null>(null);

  const loadReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await auditApi.getReport(quarantinePath, repoPath);
      setReport(res.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [quarantinePath, repoPath]);

  const runAudit = async () => {
    setRunLoading(true);
    setRunResult(null);
    setError(null);
    try {
      const res = await auditApi.runAudit(quarantinePath, repoPath);
      const r = res.data as { total_quarantined: number; diagnosed_count: number; fixable_count: number };
      setRunResult(
        `Audit complete — ${r.total_quarantined} quarantined, ${r.diagnosed_count} diagnosed, ${r.fixable_count} fixable`,
      );
      // Refresh the full report panel
      await loadReport();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setRunLoading(false);
    }
  };

  const qa = report?.quarantine_audit;

  return (
    <div className="page">
      <div className="page-header">
        <h1>F4 — Audit</h1>
        <p className="page-subtitle">
          Cross-reference quarantined tests with F2 diagnoses, and detect CI suppression mechanisms.
        </p>
      </div>

      <div className="pipeline-note">
        <span className="pipeline-step">F2 Classification</span>
        <span className="pipeline-arrow">→</span>
        <span className="pipeline-step">F3 Remediation</span>
        <span className="pipeline-arrow">→</span>
        <span className="pipeline-step active">F4 Audit</span>
      </div>

      {/* Config bar */}
      <div className="card config-bar">
        <label>Repo path
          <input value={repoPath} onChange={e => setRepoPath(e.target.value)} />
        </label>
        <label>Quarantine file
          <input value={quarantinePath} onChange={e => setQuarantinePath(e.target.value)} />
        </label>
        <div className="config-actions">
          <button className="btn-secondary" onClick={loadReport} disabled={loading}>
            {loading ? 'Loading…' : 'GET /api/audit/report'}
          </button>
          <button className="btn-primary" onClick={runAudit} disabled={runLoading}>
            {runLoading ? 'Running…' : 'POST /api/audit/run'}
          </button>
        </div>
      </div>

      {runResult && <div className="banner-success">{runResult}</div>}
      {error && <div className="banner-error">{error}</div>}

      {report && (
        <>
          {/* Summary stats */}
          <div className="stats-strip card">
            <div className="stat-box">
              <span className="stat-label">Total quarantined</span>
              <span className="stat-value">{qa?.total_quarantined ?? report.quarantine_report.total_quarantined}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Diagnosed</span>
              <span className="stat-value">{qa?.diagnosed_count ?? '—'}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Fixable</span>
              <span className="stat-value">{qa?.fixable_count ?? '—'}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Unexplained</span>
              <span className="stat-value">{qa?.unexplained_count ?? '—'}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Suppressed tests</span>
              <span className="stat-value">{report.skip_detections.summary.total_suppressed}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">CI retry</span>
              <span className="stat-value">{report.retry_configuration.summary.retry_detected ? 'Yes' : 'No'}</span>
            </div>
          </div>

          {/* Tabs */}
          <div className="tabs">
            {(['report', 'skips', 'retries'] as Tab[]).map(t => (
              <button
                key={t}
                className={activeTab === t ? 'active' : ''}
                onClick={() => setActiveTab(t)}
              >
                {t === 'report' ? 'Quarantine Audit' : t === 'skips' ? 'Skip / xfail' : 'CI Retries'}
              </button>
            ))}
          </div>

          <div className="card tab-content">
            {activeTab === 'report' && (
              <AuditedTestsTable tests={qa?.quarantined_tests ?? []} />
            )}
            {activeTab === 'skips' && (
              <SkipPanel data={report.skip_detections} />
            )}
            {activeTab === 'retries' && (
              <RetryPanel data={report.retry_configuration} />
            )}
          </div>
        </>
      )}

      {!report && !loading && (
        <div className="empty-state card">
          <p>Click <strong>GET /api/audit/report</strong> to load the audit report, or <strong>POST /api/audit/run</strong> to run a full audit.</p>
        </div>
      )}
    </div>
  );
}
