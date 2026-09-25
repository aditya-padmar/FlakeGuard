import { useState } from 'react';
import { remediationApi } from '../services/api';
import type {
  EvidenceItem,
  EvidenceValidationResult,
  StrategyResult,
  F2ClassificationInput,
  Fix,
} from '../services/api';

// ── helpers ───────────────────────────────────────────────────────────────────

const ROOT_CAUSES = [
  'timing_race',
  'timing',
  'order_dependency',
  'ordering',
  'data_leakage',
  'state_leakage',
  'environment_network',
  'environment',
  'network',
];

// ── sub-components ────────────────────────────────────────────────────────────

function EvidenceValidatePanel() {
  const [testName, setTestName] = useState('test_payment_timeout');
  const [rootCause, setRootCause] = useState('timing_race');
  const [confidence, setConfidence] = useState(0.91);
  const [evidenceText, setEvidenceText] = useState(
    JSON.stringify(
      [
        { file: 'tests/test_timing.py', line: 10, reason: 'sleep before assertion' },
      ],
      null,
      2,
    ),
  );
  const [result, setResult] = useState<EvidenceValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleValidate = async () => {
    setError(null);
    setResult(null);
    let evidence: EvidenceItem[];
    try {
      evidence = JSON.parse(evidenceText);
    } catch {
      setError('Evidence must be valid JSON.');
      return;
    }
    setLoading(true);
    try {
      const res = await remediationApi.validateEvidence({ test_name: testName, root_cause: rootCause, confidence, evidence });
      setResult(res.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Validate Evidence <span className="badge">POST /api/remediation/validate-evidence</span></h2>
      <div className="form-grid">
        <label>Test name
          <input value={testName} onChange={e => setTestName(e.target.value)} />
        </label>
        <label>Root cause
          <select value={rootCause} onChange={e => setRootCause(e.target.value)}>
            {ROOT_CAUSES.map(rc => <option key={rc}>{rc}</option>)}
          </select>
        </label>
        <label>Confidence (0–1)
          <input type="number" step="0.01" min="0" max="1" value={confidence}
            onChange={e => setConfidence(parseFloat(e.target.value))} />
        </label>
        <label className="full-width">Evidence (JSON array)
          <textarea rows={6} value={evidenceText} onChange={e => setEvidenceText(e.target.value)} />
        </label>
      </div>
      <button className="btn-primary" onClick={handleValidate} disabled={loading}>
        {loading ? 'Validating…' : 'Validate Evidence'}
      </button>

      {error && <p className="error-msg">{error}</p>}
      {result && (
        <div className={`result-block ${result.valid ? 'result-ok' : 'result-fail'}`}>
          <strong>{result.valid ? '✓ Valid' : '✗ Invalid'}</strong> — {result.message}
          <ul>
            {result.details.map((d, i) => (
              <li key={i} className={d.valid ? 'detail-ok' : 'detail-fail'}>
                <code>{d.location ?? 'unknown'}</code>: {d.message}
                {d.code_snippet && <pre className="code-snippet">{d.code_snippet}</pre>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function StrategyPanel() {
  const [rootCause, setRootCause] = useState('timing_race');
  const [result, setResult] = useState<StrategyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSelect = async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await remediationApi.selectStrategy({ root_cause: rootCause });
      setResult(res.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Select Strategy <span className="badge">POST /api/remediation/select-strategy</span></h2>
      <div className="form-grid">
        <label>Root cause
          <select value={rootCause} onChange={e => setRootCause(e.target.value)}>
            {ROOT_CAUSES.map(rc => <option key={rc}>{rc}</option>)}
          </select>
        </label>
      </div>
      <button className="btn-primary" onClick={handleSelect} disabled={loading}>
        {loading ? 'Loading…' : 'Get Strategies'}
      </button>

      {error && <p className="error-msg">{error}</p>}
      {result && (
        <div className="result-block result-ok">
          <strong>Strategies for <code>{result.root_cause}</code></strong>
          <ol>
            {result.strategies.map((s, i) => (
              <li key={s}>
                <code>{s}</code> — {result.descriptions[i]}
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}

function GenerateFromF2Panel() {
  const [form, setForm] = useState<F2ClassificationInput>({
    test_name: 'test_payment_timeout',
    root_cause: 'timing_race',
    confidence: 0.91,
    evidence: ['Background thread started', 'Assertion occurs before thread completion'],
    file_path: 'tests/test_timing.py',
  });
  const [evidenceText, setEvidenceText] = useState(form.evidence.join('\n'));
  const [result, setResult] = useState<Fix | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setError(null);
    setResult(null);
    setLoading(true);
    const payload: F2ClassificationInput = {
      ...form,
      evidence: evidenceText.split('\n').filter(Boolean),
    };
    try {
      const res = await remediationApi.generateFromF2(payload);
      setResult(res.data as Fix);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const field = (key: keyof F2ClassificationInput, label: string, type = 'text') => (
    <label>{label}
      <input
        type={type}
        value={String(form[key] ?? '')}
        onChange={e => setForm(f => ({ ...f, [key]: type === 'number' ? parseFloat(e.target.value) : e.target.value }))}
      />
    </label>
  );

  return (
    <section className="card">
      <h2>Generate Fix from F2 <span className="badge">POST /api/remediation/generate-from-f2</span></h2>
      <div className="form-grid">
        {field('test_name', 'Test name')}
        <label>Root cause
          <select value={form.root_cause} onChange={e => setForm(f => ({ ...f, root_cause: e.target.value }))}>
            {ROOT_CAUSES.map(rc => <option key={rc}>{rc}</option>)}
          </select>
        </label>
        {field('confidence', 'Confidence (0–1)', 'number')}
        {field('file_path', 'File path')}
        <label className="full-width">Evidence (one item per line)
          <textarea rows={4} value={evidenceText} onChange={e => setEvidenceText(e.target.value)} />
        </label>
      </div>
      <button className="btn-primary" onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating…' : 'Generate Fix'}
      </button>

      {error && <p className="error-msg">{error}</p>}
      {result && (
        <div className="result-block result-ok">
          <strong>Fix generated — <code>{result.fix_id}</code></strong>
          <p>Status: <strong>{result.status}</strong> &nbsp;|&nbsp; {result.suggestions.length} suggestion(s)</p>
          {result.suggestions.map((s, i) => (
            <div key={s.suggestion_id} className="suggestion-preview">
              <strong>#{i + 1} {s.fix_type}</strong> ({Math.round(s.confidence * 100)}% confidence)
              <p>{s.description}</p>
              <p><em>{s.rationale}</em></p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

// ── page ──────────────────────────────────────────────────────────────────────

export default function RemediationPage() {
  return (
    <div className="page">
      <div className="page-header">
        <h1>F3 — Remediation</h1>
        <p className="page-subtitle">
          Validate F2 evidence, select a remediation strategy, and generate fix suggestions.
        </p>
      </div>

      <div className="pipeline-note">
        <span className="pipeline-step">F2 Classification</span>
        <span className="pipeline-arrow">→</span>
        <span className="pipeline-step active">F3 Remediation</span>
        <span className="pipeline-arrow">→</span>
        <span className="pipeline-step">F4 Audit</span>
      </div>

      <div className="panels">
        <EvidenceValidatePanel />
        <StrategyPanel />
        <GenerateFromF2Panel />
      </div>
    </div>
  );
}
