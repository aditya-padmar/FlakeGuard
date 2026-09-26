import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Landing.css';

interface Scenario {
  id: string;
  name: string;
  category: string;
  file: string;
  flakeRate: string;
  errorLog: string;
  rootCause: string;
  confidence: number;
  fixDescription: string;
  originalCode: string;
  fixedCode: string;
}

const SCENARIOS: Scenario[] = [
  {
    id: 'timing',
    name: 'Async Timeout Race',
    category: 'Timing / Concurrency',
    file: 'tests/test_payment_gateway.py',
    flakeRate: '35%',
    errorLog: "TimeoutError: Waiting for event 'payment_intent.succeeded' timed out after 5000ms.\nExpected: status == 'succeeded'\nReceived: status == 'pending' (delayed by async queue)",
    rootCause: 'Fixed sleep duration under CI CPU contention fails when queue workers lag by > 20ms.',
    confidence: 94,
    fixDescription: 'Replaced fixed timeout with exponential polling condition and resilient retry boundary.',
    originalCode: `# Flaky implementation:\ndef test_payment_intent(client):\n    tx = client.create_payment(amount=5000)\n    time.sleep(5) # Race condition under CI load\n    assert client.get_status(tx.id) == "succeeded"`,
    fixedCode: `# FlakeGuard AI Remediation:\ndef test_payment_intent(client):\n    tx = client.create_payment(amount=5000)\n    # Resilient polling with exponential backoff\n    status = wait_for_condition(\n        lambda: client.get_status(tx.id),\n        predicate=lambda s: s == "succeeded",\n        timeout_secs=10, interval=0.2\n    )\n    assert status == "succeeded"`
  },
  {
    id: 'state',
    name: 'Shared State Leakage',
    category: 'State Leakage',
    file: 'tests/test_tenant_cache.py',
    flakeRate: '28%',
    errorLog: "AssertionError: Tenant count mismatch!\nExpected: 1 active tenant\nActual: 3 active tenants (leaked from tests/test_onboarding.py)",
    rootCause: 'Redis key prefix shared between test suites without teardown flush or database rollback isolation.',
    confidence: 96,
    fixDescription: 'Injected isolated session autouse fixture with automatic atomic flush on fixture cleanup.',
    originalCode: `# Flaky implementation:\ndef test_tenant_isolation(redis_conn):\n    # Assumes empty cache state\n    tenants = redis_conn.keys("tenant:*")\n    assert len(tenants) == 0`,
    fixedCode: `# FlakeGuard AI Remediation:\n@pytest.fixture(autouse=True)\ndef isolate_tenant_cache(redis_conn):\n    redis_conn.flushdb()\n    yield\n    redis_conn.flushdb()\n\ndef test_tenant_isolation(redis_conn):\n    assert len(redis_conn.keys("tenant:*")) == 0`
  },
  {
    id: 'order',
    name: 'Order Dependency',
    category: 'Ordering Dependency',
    file: 'tests/test_audit_export.py',
    flakeRate: '42%',
    errorLog: "FileNotFoundError: [Errno 2] No such file: '/tmp/audit_reports/daily_summary.json'\nTest fails when run in isolation or under pytest-xdist parallel workers.",
    rootCause: 'Implicit dependency on test_generate_report() running beforehand in alphabetical order.',
    confidence: 91,
    fixDescription: 'Decoupled file dependency by generating scoped temporary synthetic artifacts per test instance.',
    originalCode: `# Flaky implementation:\ndef test_audit_export():\n    # Implicitly relies on previous test output\n    with open("/tmp/audit_reports/daily_summary.json") as f:\n        assert "SUCCESS" in f.read()`,
    fixedCode: `# FlakeGuard AI Remediation:\ndef test_audit_export(tmp_path):\n    # Isolated synthetic fixture\n    report_file = tmp_path / "daily_summary.json"\n    seed_audit_report(report_file)\n    assert "SUCCESS" in report_file.read_text()`
  }
];

export default function Landing() {
  const [activeScenarioId, setActiveScenarioId] = useState('timing');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulatedFixed, setSimulatedFixed] = useState(false);

  const { isAuthenticated } = useAuth();

  const activeScenario = SCENARIOS.find(s => s.id === activeScenarioId) || SCENARIOS[0];

  const handleSimulateFix = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
      setSimulatedFixed(true);
    }, 700);
  };

  const handleScenarioChange = (id: string) => {
    setActiveScenarioId(id);
    setSimulatedFixed(false);
  };

  return (
    <div className="landing-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          FlakeGuard v1.0 • Intelligent CI/CD Flakiness Defense
        </div>

        <h1 className="hero-title">
          Stop Chasing Flaky Tests.<br />
          <span className="gradient-text">Detect, Quarantine & Fix Them Automatically.</span>
        </h1>

        <p className="hero-subtitle">
          FlakeGuard uses specialized AI agents to analyze test failures, isolate unstable tests in zero-risk quarantine, pinpoint root causes, and propose verified code fixes.
        </p>

        <div className="hero-actions">
          {isAuthenticated ? (
            <Link to="/dashboard" className="btn-hero-primary">
              <span>Go to Live Dashboard</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>
          ) : (
            <>
              <Link to="/signup" className="btn-hero-primary">
                <span>Get Started — Sign Up</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
              <Link to="/login" className="btn-hero-secondary">
                <span>Sign In to Dashboard</span>
              </Link>
            </>
          )}

          <a href="#interactive-demo" className="btn-hero-secondary">
            <span>Interactive Simulator</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </a>

          <a
            href="https://github.com/aditya-padmar/FlakeGuard"
            target="_blank"
            rel="noreferrer"
            className="btn-hero-secondary"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
            </svg>
            <span>GitHub</span>
          </a>
        </div>

        {/* Stats Ribbon */}
        <div className="hero-stats-ribbon">
          <div className="stat-item">
            <span className="stat-value">92%</span>
            <span className="stat-label">Reduction in False CI Failures</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">&lt; 3s</span>
            <span className="stat-label">Root Cause Diagnostic Speed</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">4 Core</span>
            <span className="stat-label">Flakiness Domains Classified</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">Zero</span>
            <span className="stat-label">Unblocked CI Releases in Quarantine</span>
          </div>
        </div>

        {/* Hero Interactive Mockup Preview */}
        <div className="hero-mockup-wrapper">
          <div className="mockup-header">
            <div className="mockup-dots">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
            </div>
            <div className="mockup-title">flakeguard-agent://inspection-stream/live</div>
            <div className="mockup-live-indicator">
              <span className="pulse-dot"></span>
              ACTIVE MONITORING
            </div>
          </div>

          <div className="mockup-content">
            <div className="mockup-card-dark">
              <div className="mockup-card-label">Detected Anomaly</div>
              <div className="mockup-test-title">tests/test_order_concurrency.py::test_inventory_lock</div>
              <div className="mockup-badges">
                <span className="tag-red">Flake Rate: 35%</span>
                <span className="tag-purple">Timing / Race Condition</span>
                <span className="tag-amber">Quarantined (q-108)</span>
              </div>
              <p className="mockup-text-muted">
                Assertion failed: <code>available_inventory != reserved_stock</code> under simultaneous thread execution. Root cause identified as un-synchronized in-memory counter update.
              </p>
            </div>

            <div className="mockup-card-dark">
              <div className="mockup-card-label">AI Remediation Patch (Confidence 95%)</div>
              <div className="mockup-code-block">
                <span className="diff-del">- inventory.reserve(item_id, count=1)</span>
                <span className="diff-add">+ with inventory.atomic_lock(item_id):</span>
                <span className="diff-add">+     inventory.reserve(item_id, count=1)</span>
                <span className="diff-add">+ assert inventory.get_available(item_id) == 0</span>
              </div>
              <div style={{ marginTop: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>✓ Verified against 20 virtual runs</span>
                <Link to={isAuthenticated ? '/fixes' : '/login'} style={{ fontSize: '0.75rem', color: '#818cf8', textDecoration: 'none', fontWeight: 600 }}>
                  View in Fixes Tab →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Capabilities Grid */}
      <section className="landing-section" id="capabilities">
        <div className="section-header">
          <span className="section-tag">Key Capabilities</span>
          <h2 className="section-title">End-to-End Flakiness Intelligence</h2>
          <p className="section-description">
            Traditional test runners give you noisy red builds. FlakeGuard equips your team with automated detection, quarantine isolation, and intelligent code remediation.
          </p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="m10 15 5-3-5-3v6z" />
              </svg>
            </div>
            <h3 className="feature-title">Multi-Run Flake Detection</h3>
            <p className="feature-description">
              Continuously runs and tracks test variances across builds to distinguish real code regressions from non-deterministic test instability.
            </p>
            <span className="feature-highlight">
              Statistical variance models
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10H12V2z" />
                <path d="M12 12 2.1 12.5" />
                <path d="m16.2 7.8 5.7-5.7" />
              </svg>
            </div>
            <h3 className="feature-title">AI Root Cause Classification</h3>
            <p className="feature-description">
              Specialized classifier identifies whether failure stems from timing & races, shared state leakage, execution ordering, or network environment.
            </p>
            <span className="feature-highlight">
              Timing, State, Ordering & Env
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <h3 className="feature-title">Smart Quarantine Sandbox</h3>
            <p className="feature-description">
              Isolates flaky tests so they never block production deployments, while continuing to run them passively to verify stability and auto-graduation.
            </p>
            <span className="feature-highlight">
              Zero-risk CI pipeline unblocking
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
              </svg>
            </div>
            <h3 className="feature-title">Automated Code Remediation</h3>
            <p className="feature-description">
              Generates ready-to-merge patches, clear explanations, and estimated effort levels to eliminate flakiness without manual debugging.
            </p>
            <span className="feature-highlight">
              Diffs with confidence scoring
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </div>
            <h3 className="feature-title">Telemetry & Health Metrics</h3>
            <p className="feature-description">
              Visualize resolution rates, mean-time-to-fix (MTTF), flakiness trends over time, and quarantine queues in an interactive dashboard.
            </p>
            <span className="feature-highlight">
              Full visibility for engineering leads
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
            </span>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
                <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
                <line x1="6" y1="6" x2="6.01" y2="6" />
                <line x1="6" y1="18" x2="6.01" y2="18" />
              </svg>
            </div>
            <h3 className="feature-title">CI Ingestion & Webhooks</h3>
            <p className="feature-description">
              Plugs right into Pytest, Jest, GitHub Actions, GitLab CI, and JUnit XML reporters without requiring custom test rewriting.
            </p>
            <span className="feature-highlight">
              Drop-in integration
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
            </span>
          </div>
        </div>
      </section>

      {/* Interactive Simulator Section */}
      <section className="landing-section" id="interactive-demo">
        <div className="section-header">
          <span className="section-tag">Live Demonstration</span>
          <h2 className="section-title">See FlakeGuard In Action</h2>
          <p className="section-description">
            Select a common flaky test pattern below to see how FlakeGuard isolates the failure, analyzes root causes, and generates verified fixes.
          </p>
        </div>

        <div className="playground-box">
          <div className="scenario-tabs">
            {SCENARIOS.map(s => (
              <button
                key={s.id}
                className={`scenario-btn ${activeScenarioId === s.id ? 'active' : ''}`}
                onClick={() => handleScenarioChange(s.id)}
              >
                {s.name} ({s.category})
              </button>
            ))}
          </div>

          <div className="playground-body">
            {/* Left: Original Test & Error */}
            <div className="panel-left">
              <div className="panel-header-title">
                <span>Flaky Test & Failure Trace</span>
                <span className="tag-red">Fail Rate: {activeScenario.flakeRate}</span>
              </div>
              <pre className="playground-code">{activeScenario.originalCode}</pre>
              <div className="panel-diagnostics">
                <div className="diag-item">
                  <span className="diag-label">File:</span>
                  <span className="diag-value"><code>{activeScenario.file}</code></span>
                </div>
                <div className="diag-item">
                  <span className="diag-label">Detected Trace:</span>
                  <span className="diag-value" style={{ color: '#ef4444', fontSize: '0.8rem' }}>
                    {activeScenario.errorLog}
                  </span>
                </div>
              </div>
            </div>

            {/* Right: AI Diagnosis & Fix */}
            <div className="panel-right">
              <div className="panel-header-title">
                <span>FlakeGuard AI Remediation</span>
                <span className="tag-purple">Confidence: {activeScenario.confidence}%</span>
              </div>
              <pre className="playground-code" style={{ borderColor: simulatedFixed ? '#22c55e' : 'transparent' }}>
                {activeScenario.fixedCode}
              </pre>
              <div className="panel-diagnostics">
                <div className="diag-item">
                  <span className="diag-label">Root Cause:</span>
                  <span className="diag-value">{activeScenario.rootCause}</span>
                </div>
                <div className="diag-item">
                  <span className="diag-label">Remediation:</span>
                  <span className="diag-value">{activeScenario.fixDescription}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="playground-action-bar">
            {simulatedFixed && (
              <div className="verification-status">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                Patch Verified: 10/10 synthetic runs passed (0% flakiness)
              </div>
            )}

            <button
              className="btn-hero-primary"
              onClick={handleSimulateFix}
              disabled={isSimulating}
              style={{ padding: '0.65rem 1.35rem', fontSize: '0.9rem' }}
            >
              {isSimulating ? 'Validating Patch...' : simulatedFixed ? 'Re-run Verification' : 'Simulate AI Remediation'}
            </button>
          </div>
        </div>
      </section>

      {/* 4-Step Lifecycle Workflow */}
      <section className="landing-section">
        <div className="section-header">
          <span className="section-tag">How It Works</span>
          <h2 className="section-title">The FlakeGuard Continuous Lifecycle</h2>
          <p className="section-description">
            From the moment your test suite runs to the moment a fix is merged, FlakeGuard handles each phase automatically.
          </p>
        </div>

        <div className="workflow-steps-grid">
          <div className="step-card">
            <div className="step-number">1</div>
            <h4 className="step-title">Ingest CI Runs</h4>
            <p className="step-desc">
              Parses test run logs, traces, and JUnit artifacts across PRs and main branch executions.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number">2</div>
            <h4 className="step-title">Classify Root Cause</h4>
            <p className="step-desc">
              AI agents inspect error messages, async timing, and shared fixture usage to determine root cause.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number">3</div>
            <h4 className="step-title">Quarantine Safely</h4>
            <p className="step-desc">
              Unstable tests are moved into a quarantine sandbox so CI builds and deploy pipelines stay unblocked.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number">4</div>
            <h4 className="step-title">Generate & Auto-Fix</h4>
            <p className="step-desc">
              Produces actionable code patches, validates them with repeated runs, and restores the test to the suite.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="cta-banner">
        <h2>Ready to Stabilize Your Test Suite?</h2>
        <p>
          Experience FlakeGuard live on your machine. Explore detected flaky tests, review automated quarantine tables, and inspect AI-generated code patches right now.
        </p>
        <Link to={isAuthenticated ? '/dashboard' : '/signup'} className="btn-cta-launch">
          <span>{isAuthenticated ? 'Open FlakeGuard Dashboard' : 'Get Started — Sign Up Free'}</span>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </Link>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div>
          <strong>FlakeGuard</strong> • AI-Powered Flaky Test Detection & Remediation System
        </div>
        <div className="footer-links">
          <Link to="/">Home</Link>
          {isAuthenticated ? (
            <>
              <Link to="/dashboard">Dashboard</Link>
              <Link to="/quarantine">Quarantine</Link>
              <Link to="/fixes">Fixes</Link>
            </>
          ) : (
            <>
              <Link to="/login">Sign In</Link>
              <Link to="/signup">Create Account</Link>
            </>
          )}
          <a href="https://github.com/aditya-padmar/FlakeGuard" target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}
