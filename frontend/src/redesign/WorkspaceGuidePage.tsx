import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  ArrowRight,
  Bot,
  Braces,
  ChevronDown,
  CircleHelp,
  Clock,
  Compass,
  FileCode2,
  FlaskConical,
  GitBranch,
  Globe,
  Layers,
  LayoutDashboard,
  Play,
  RotateCw,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  Sparkles,
  Terminal,
  Zap,
} from 'lucide-react';
import './guide.css';

interface WorkspaceGuidePageProps {
  onDemo?: () => void;
}

type GuideTab = 'pipeline' | 'taxonomy' | 'remediation' | 'views' | 'faq';
type TaxonomyCategory = 'timing' | 'ordering' | 'leakage' | 'environment';

export default function WorkspaceGuidePage({ onDemo }: WorkspaceGuidePageProps) {
  const [activeTab, setActiveTab] = useState<GuideTab>('pipeline');
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<TaxonomyCategory>('timing');
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const toggleFaq = (index: number) => {
    setOpenFaq(prev => (prev === index ? null : index));
  };

  return (
    <div className="fg-guide">
      {/* Hero Header */}
      <header className="fg-guide-hero">
        <div className="fg-guide-hero-badge">
          <CircleHelp size={14} />
          <span>Documentation & Architecture</span>
        </div>
        <h1>Workspace Guide</h1>
        <p>
          Welcome to FlakeGuard. This guide provides an end-to-end overview of our automated test flakiness
          detection engine, root cause analysis powered by specialized IBM Bob subagents, and human-in-the-loop remediation workflows.
        </p>
        <div className="fg-guide-hero-actions">
          <Link to="/sources" className="fg-button fg-button-primary">
            <GitBranch size={16} />
            Configure Repository
          </Link>
          {onDemo && (
            <button className="fg-button" onClick={onDemo}>
              <Play size={15} />
              Run Demo Simulation
            </button>
          )}
          <Link to="/dashboard" className="fg-button">
            <LayoutDashboard size={15} />
            View Results
          </Link>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="fg-guide-tabs" aria-label="Guide section navigation">
        <button
          className={`fg-guide-tab-btn ${activeTab === 'pipeline' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('pipeline')}
        >
          <Layers size={16} />
          <span>4-Stage Pipeline</span>
        </button>
        <button
          className={`fg-guide-tab-btn ${activeTab === 'taxonomy' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('taxonomy')}
        >
          <Bot size={16} />
          <span>Root Cause Taxonomy</span>
        </button>
        <button
          className={`fg-guide-tab-btn ${activeTab === 'remediation' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('remediation')}
        >
          <Braces size={16} />
          <span>Remediation & Safety</span>
        </button>
        <button
          className={`fg-guide-tab-btn ${activeTab === 'views' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('views')}
        >
          <Compass size={16} />
          <span>Platform Views Map</span>
        </button>
        <button
          className={`fg-guide-tab-btn ${activeTab === 'faq' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('faq')}
        >
          <Sparkles size={16} />
          <span>Developer FAQ</span>
        </button>
      </nav>

      {/* Tab Content */}
      <main className="fg-guide-content">
        <AnimatePresence mode="wait">
          {activeTab === 'pipeline' && (
            <motion.section
              key="pipeline"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fg-guide-panel"
            >
              <div className="fg-guide-panel-header">
                <div className="fg-guide-panel-title">
                  <div className="fg-guide-icon-badge">
                    <Layers size={20} />
                  </div>
                  <div>
                    <h2>The FlakeGuard Investigation Lifecycle</h2>
                    <span className="fg-ex-input-help">
                      From ingestion and statistical detection to AST validation and quarantine tracking.
                    </span>
                  </div>
                </div>
              </div>

              <div className="fg-guide-pipeline-flow">
                {/* Stage 1 */}
                <div className="fg-guide-stage-card">
                  <div className="fg-guide-stage-step">Stage 01 · Detection</div>
                  <h4>F1 Test Harness</h4>
                  <p>
                    Executes test suites across multiple repeated iterations (typically 5 to 10 runs) in isolated runner processes.
                    Computes test flake rate and distinguishes stochastic flakiness from deterministic failures.
                  </p>
                  <div className="fg-guide-stage-meta">
                    <code>backend/harness/</code> · Multi-run executor
                  </div>
                </div>

                {/* Stage 2 */}
                <div className="fg-guide-stage-card">
                  <div className="fg-guide-stage-step">Stage 02 · Intelligence</div>
                  <h4>F2 Bob AI Agent</h4>
                  <p>
                    Orchestrates specialized subagents (Timing, Ordering, State Leakage, Environment) to parse test syntax,
                    execution logs, and trace evidence. Produces calibrated confidence scores and specific line-pinned evidence.
                  </p>
                  <div className="fg-guide-stage-meta">
                    <code>backend/bob/</code> · Heuristics + AST models
                  </div>
                </div>

                {/* Stage 3 */}
                <div className="fg-guide-stage-card">
                  <div className="fg-guide-stage-step">Stage 03 · Remediation</div>
                  <h4>F3 Fix Engine</h4>
                  <p>
                    Validates the line numbers and AST tokens against the current branch, selects targeted fix strategies
                    (e.g., polling conditions, fixture isolation), and generates diffs for engineer review.
                  </p>
                  <div className="fg-guide-stage-meta">
                    <code>backend/remediation/</code> · Strategy selector
                  </div>
                </div>

                {/* Stage 4 */}
                <div className="fg-guide-stage-card">
                  <div className="fg-guide-stage-step">Stage 04 · Governance</div>
                  <h4>F4 Quarantine Auditor</h4>
                  <p>
                    Detects suppressed tests (e.g. <code>@pytest.mark.skip</code> or <code>xfail</code>), identifies CI retry bloat
                    in workflow files, and tracks test quarantine lists in <code>QUARANTINE.md</code>.
                  </p>
                  <div className="fg-guide-stage-meta">
                    <code>backend/auditor/</code> · CI & marker audit
                  </div>
                </div>
              </div>
            </motion.section>
          )}

          {activeTab === 'taxonomy' && (
            <motion.section
              key="taxonomy"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fg-guide-panel"
            >
              <div className="fg-guide-panel-header">
                <div className="fg-guide-panel-title">
                  <div className="fg-guide-icon-badge purple">
                    <Bot size={20} />
                  </div>
                  <div>
                    <h2>The 4 Root Cause Categories</h2>
                    <span className="fg-ex-input-help">
                      FlakeGuard classifies flaky test behavior into four distinct failure profiles.
                    </span>
                  </div>
                </div>
              </div>

              {/* Taxonomy Selector Buttons */}
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
                <button
                  className={`fg-button ${selectedTaxonomy === 'timing' ? 'fg-button-primary' : ''}`}
                  onClick={() => setSelectedTaxonomy('timing')}
                >
                  <Clock size={15} />
                  Timing & Concurrency
                </button>
                <button
                  className={`fg-button ${selectedTaxonomy === 'ordering' ? 'fg-button-primary' : ''}`}
                  onClick={() => setSelectedTaxonomy('ordering')}
                >
                  <RotateCw size={15} />
                  Order Dependency
                </button>
                <button
                  className={`fg-button ${selectedTaxonomy === 'leakage' ? 'fg-button-primary' : ''}`}
                  onClick={() => setSelectedTaxonomy('leakage')}
                >
                  <Zap size={15} />
                  State Leakage
                </button>
                <button
                  className={`fg-button ${selectedTaxonomy === 'environment' ? 'fg-button-primary' : ''}`}
                  onClick={() => setSelectedTaxonomy('environment')}
                >
                  <Globe size={15} />
                  Environment & Network
                </button>
              </div>

              {/* Category Detail View */}
              {selectedTaxonomy === 'timing' && (
                <div className="fg-taxonomy-card">
                  <div className="fg-taxonomy-pill timing">
                    <Clock size={12} />
                    Category: Timing & Race Conditions
                  </div>
                  <h3 style={{ margin: 0, fontSize: 18 }}>Non-deterministic execution speeds and async waits</h3>
                  <p style={{ color: 'var(--muted)', lineHeight: 1.7, margin: 0 }}>
                    Occurs when test assertions execute before asynchronous operations or background workers complete.
                    Typically triggered by arbitrary sleep delays (<code>time.sleep(2)</code>), thread race conditions,
                    or un-awaited promises.
                  </p>
                  <div>
                    <h4 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--muted)', margin: '12px 0 6px' }}>
                      Diagnostic Evidence & Pattern Fix
                    </h4>
                    <div className="fg-taxonomy-codeblock">
                      <pre>
                        <span className="fg-code-comment"># Flaky anti-pattern: arbitrary sleep duration</span>{'\n'}
                        <span className="fg-code-bad">- time.sleep(1.5)</span>{'\n'}
                        <span className="fg-code-bad">- assert worker.is_finished()</span>{'\n\n'}
                        <span className="fg-code-comment"># FlakeGuard recommended fix: explicit condition polling</span>{'\n'}
                        <span className="fg-code-good">+ wait_until(lambda: worker.is_finished(), timeout=5.0, poll_interval=0.1)</span>{'\n'}
                        <span className="fg-code-good">+ assert worker.is_finished()</span>
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {selectedTaxonomy === 'ordering' && (
                <div className="fg-taxonomy-card">
                  <div className="fg-taxonomy-pill ordering">
                    <RotateCw size={12} />
                    Category: Order Dependency
                  </div>
                  <h3 style={{ margin: 0, fontSize: 18 }}>Tests passing or failing based on execution sequence</h3>
                  <p style={{ color: 'var(--muted)', lineHeight: 1.7, margin: 0 }}>
                    Happens when a test assumes that previous tests set up module state, seeded a database,
                    or pre-populated in-memory caches. Running the test in isolation with <code>pytest -k</code> fails.
                  </p>
                  <div>
                    <h4 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--muted)', margin: '12px 0 6px' }}>
                      Diagnostic Evidence & Pattern Fix
                    </h4>
                    <div className="fg-taxonomy-codeblock">
                      <pre>
                        <span className="fg-code-comment"># Flaky anti-pattern: relies on global state modified by earlier test</span>{'\n'}
                        <span className="fg-code-bad">- def test_payment_processing():</span>{'\n'}
                        <span className="fg-code-bad">-     user = GLOBAL_SESSION['active_user'] # fails if run first</span>{'\n\n'}
                        <span className="fg-code-comment"># FlakeGuard recommended fix: isolated fixture injection</span>{'\n'}
                        <span className="fg-code-good">+ @pytest.fixture</span>{'\n'}
                        <span className="fg-code-good">+ def test_user():</span>{'\n'}
                        <span className="fg-code-good">+     return create_isolated_user(role="buyer")</span>
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {selectedTaxonomy === 'leakage' && (
                <div className="fg-taxonomy-card">
                  <div className="fg-taxonomy-pill leakage">
                    <Zap size={12} />
                    Category: State Leakage
                  </div>
                  <h3 style={{ margin: 0, fontSize: 18 }}>Pollution left behind in files, DBs, or mocks</h3>
                  <p style={{ color: 'var(--muted)', lineHeight: 1.7, margin: 0 }}>
                    Tests that modify singleton caches, files on disk, or start mocks without calling <code>stop()</code>
                    or using context managers. Subsequent tests fail because the environment is polluted.
                  </p>
                  <div>
                    <h4 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--muted)', margin: '12px 0 6px' }}>
                      Diagnostic Evidence & Pattern Fix
                    </h4>
                    <div className="fg-taxonomy-codeblock">
                      <pre>
                        <span className="fg-code-comment"># Flaky anti-pattern: un-stopped patch leaks into subsequent tests</span>{'\n'}
                        <span className="fg-code-bad">- patcher = mock.patch('app.api.call')</span>{'\n'}
                        <span className="fg-code-bad">- patcher.start()  # never stopped</span>{'\n\n'}
                        <span className="fg-code-comment"># FlakeGuard recommended fix: contextual patch or monkeypatch fixture</span>{'\n'}
                        <span className="fg-code-good">+ with mock.patch('app.api.call') as mock_call:</span>{'\n'}
                        <span className="fg-code-good">+     mock_call.return_value = 200</span>{'\n'}
                        <span className="fg-code-good">+     run_client_test()</span>
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {selectedTaxonomy === 'environment' && (
                <div className="fg-taxonomy-card">
                  <div className="fg-taxonomy-pill environment">
                    <Globe size={12} />
                    Category: Environment & Network
                  </div>
                  <h3 style={{ margin: 0, fontSize: 18 }}>External dependencies, ports, and hardware interactions</h3>
                  <p style={{ color: 'var(--muted)', lineHeight: 1.7, margin: 0 }}>
                    Failures triggered by external services, network latency, fixed port bindings (<code>8080</code>),
                    local timezone/locale formats, or hardware peripherals (e.g. GPIO/I2C buses on embedded targets).
                  </p>
                  <div>
                    <h4 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--muted)', margin: '12px 0 6px' }}>
                      Diagnostic Evidence & Pattern Fix
                    </h4>
                    <div className="fg-taxonomy-codeblock">
                      <pre>
                        <span className="fg-code-comment"># Flaky anti-pattern: hitting live external API in unit tests</span>{'\n'}
                        <span className="fg-code-bad">- response = requests.get('https://api.external.service/v1/health')</span>{'\n\n'}
                        <span className="fg-code-comment"># FlakeGuard recommended fix: mock response or local test container</span>{'\n'}
                        <span className="fg-code-good">+ @responses.activate</span>{'\n'}
                        <span className="fg-code-good">+ def test_external_sync():</span>{'\n'}
                        <span className="fg-code-good">+     responses.add(responses.GET, 'https://api.external.service/v1/health', json=&#123;'ok': True&#125;)</span>
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </motion.section>
          )}

          {activeTab === 'remediation' && (
            <motion.section
              key="remediation"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fg-guide-panel"
            >
              <div className="fg-guide-panel-header">
                <div className="fg-guide-panel-title">
                  <div className="fg-guide-icon-badge amber">
                    <Braces size={20} />
                  </div>
                  <div>
                    <h2>Safety-First Remediation Policy</h2>
                    <span className="fg-ex-input-help">
                      Human-in-the-loop validation: no changes are ever merged autonomously.
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
                <div className="fg-guide-stage-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--cyan)', marginBottom: 12 }}>
                    <FileCode2 size={18} />
                    <strong>AST Evidence Verification</strong>
                  </div>
                  <p>
                    Before any fix is proposed, FlakeGuard validates the line numbers, functions, and symbols against the
                    parsed Abstract Syntax Tree of the repository to prevent stale diffs.
                  </p>
                </div>

                <div className="fg-guide-stage-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', marginBottom: 12 }}>
                    <ShieldCheck size={18} />
                    <strong>Human Review Guarantee</strong>
                  </div>
                  <p>
                    FlakeGuard presents clear unified git diffs. You can copy the patch, download it, or submit it as a PR
                    branch. Production code is never silently altered.
                  </p>
                </div>

                <div className="fg-guide-stage-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--purple)', marginBottom: 12 }}>
                    <ShieldAlert size={18} />
                    <strong>Quarantine Governance</strong>
                  </div>
                  <p>
                    If a test cannot be remediated immediately, it can be quarantined in <code>QUARANTINE.md</code> so CI
                    remains green while enforcing SLA resolution reminders.
                  </p>
                </div>
              </div>
            </motion.section>
          )}

          {activeTab === 'views' && (
            <motion.section
              key="views"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fg-guide-panel"
            >
              <div className="fg-guide-panel-header">
                <div className="fg-guide-panel-title">
                  <div className="fg-guide-icon-badge green">
                    <Compass size={20} />
                  </div>
                  <div>
                    <h2>Workspace Views & Tools Map</h2>
                    <span className="fg-ex-input-help">
                      Quick overview and direct links to all views in your FlakeGuard workspace.
                    </span>
                  </div>
                </div>
              </div>

              <div className="fg-guide-nav-grid">
                <Link to="/" className="fg-guide-nav-item">
                  <div className="fg-guide-nav-item-top">
                    <div className="fg-guide-nav-item-title">
                      <FlaskConical size={16} color="var(--cyan)" />
                      <span>Launchpad</span>
                    </div>
                    <ArrowRight size={14} color="var(--muted)" />
                  </div>
                  <p>Start a new repository investigation or run the interactive demo dataset.</p>
                  <div className="fg-guide-nav-path">Route: /</div>
                </Link>

                <Link to="/dashboard" className="fg-guide-nav-item">
                  <div className="fg-guide-nav-item-top">
                    <div className="fg-guide-nav-item-title">
                      <LayoutDashboard size={16} color="var(--purple)" />
                      <span>Overview Dashboard</span>
                    </div>
                    <ArrowRight size={14} color="var(--muted)" />
                  </div>
                  <p>High-level metrics, health scores, flake rate distributions, and category donuts.</p>
                  <div className="fg-guide-nav-path">Route: /dashboard</div>
                </Link>

                <Link to="/inventory" className="fg-guide-nav-item">
                  <div className="fg-guide-nav-item-top">
                    <div className="fg-guide-nav-item-title">
                      <Terminal size={16} color="var(--orange)" />
                      <span>Test Inventory</span>
                    </div>
                    <ArrowRight size={14} color="var(--muted)" />
                  </div>
                  <p>Detailed breakdown of detected tests, run consistency, failure logs, and Bob subagent verdicts.</p>
                  <div className="fg-guide-nav-path">Route: /inventory</div>
                </Link>

                <Link to="/pipeline" className="fg-guide-nav-item">
                  <div className="fg-guide-nav-item-top">
                    <div className="fg-guide-nav-item-title">
                      <Activity size={16} color="var(--cyan)" />
                      <span>Live Pipeline</span>
                    </div>
                    <ArrowRight size={14} color="var(--muted)" />
                  </div>
                  <p>Real-time terminal stream, stage telemetry, and execution clock for ongoing analyses.</p>
                  <div className="fg-guide-nav-path">Route: /pipeline</div>
                </Link>

                <Link to="/fixes" className="fg-guide-nav-item">
                  <div className="fg-guide-nav-item-top">
                    <div className="fg-guide-nav-item-title">
                      <Braces size={16} color="var(--green)" />
                      <span>Remediation Hub</span>
                    </div>
                    <ArrowRight size={14} color="var(--muted)" />
                  </div>
                  <p>Review suggested code patches, inspect unified diffs, and validate changes before merging.</p>
                  <div className="fg-guide-nav-path">Route: /fixes</div>
                </Link>

                <Link to="/quarantine" className="fg-guide-nav-item">
                  <div className="fg-guide-nav-item-top">
                    <div className="fg-guide-nav-item-title">
                      <ShieldOff size={16} color="#ff7849" />
                      <span>Quarantine Audit</span>
                    </div>
                    <ArrowRight size={14} color="var(--muted)" />
                  </div>
                  <p>Monitor suppressed tests, skip markers, and hidden CI retries causing technical debt.</p>
                  <div className="fg-guide-nav-path">Route: /quarantine</div>
                </Link>

                <Link to="/sources" className="fg-guide-nav-item">
                  <div className="fg-guide-nav-item-top">
                    <div className="fg-guide-nav-item-title">
                      <GitBranch size={16} color="#7dd3fc" />
                      <span>Repository Sources</span>
                    </div>
                    <ArrowRight size={14} color="var(--muted)" />
                  </div>
                  <p>Connect remote GitHub repositories via URL and access token or upload custom test suites.</p>
                  <div className="fg-guide-nav-path">Route: /sources</div>
                </Link>
              </div>
            </motion.section>
          )}

          {activeTab === 'faq' && (
            <motion.section
              key="faq"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fg-guide-panel"
            >
              <div className="fg-guide-panel-header">
                <div className="fg-guide-panel-title">
                  <div className="fg-guide-icon-badge">
                    <Sparkles size={20} />
                  </div>
                  <div>
                    <h2>Frequently Asked Questions</h2>
                    <span className="fg-ex-input-help">Common questions about detection, accuracy, and workflows.</span>
                  </div>
                </div>
              </div>

              <div className="fg-guide-faq-list">
                {[
                  {
                    q: 'How does FlakeGuard distinguish a flaky test from a broken test?',
                    a: 'A broken test fails deterministically on every single run (100% fail rate). FlakeGuard executes tests across multiple iterations (e.g. 5 to 10 runs). Only tests that exhibit inconsistent outcomes (e.g., 2 passes and 3 fails) are classified as flaky and passed to the Bob AI Agent.',
                  },
                  {
                    q: 'How are subagent confidence scores calculated?',
                    a: 'Each specialized subagent (Timing, Ordering, State Leakage, Environment) analyzes the test source code using regex patterns, AST syntax matching, and test failure logs. If multiple strong indicators (e.g. sleep calls, thread joins) are found, the subagent returns a HIGH confidence score (≥80%). If ambiguous, confidence is set to MEDIUM or LOW.',
                  },
                  {
                    q: 'How do I test a private GitHub repository?',
                    a: 'Navigate to "Developer Tools > Repository Sources" (/sources). Select the GitHub tab, paste your repository URL and branch name, and provide a GitHub Personal Access Token (PAT) with read access to repository contents.',
                  },
                  {
                    q: 'Can I upload custom or local test archives?',
                    a: 'Yes. In the Repository Sources view (/sources), navigate to the "Upload Test Suite" tab to upload a ZIP or TAR archive containing your test files directly through the web UI.',
                  },
                  {
                    q: 'What languages and test frameworks does FlakeGuard support?',
                    a: 'FlakeGuard natively supports Python (pytest, unittest). The Bob Agent also includes heuristics for C / C++ embedded test suites (e.g., ESP32 ESP-IDF FreeRTOS tests) and JavaScript/TypeScript test suites.',
                  },
                ].map((item, index) => (
                  <div key={index} className="fg-guide-faq-card">
                    <button
                      className="fg-guide-faq-trigger"
                      onClick={() => toggleFaq(index)}
                      aria-expanded={openFaq === index}
                    >
                      <span>{item.q}</span>
                      <ChevronDown
                        size={16}
                        style={{
                          transform: openFaq === index ? 'rotate(180deg)' : 'rotate(0deg)',
                          transition: 'transform 0.2s ease',
                          flexShrink: 0,
                        }}
                      />
                    </button>
                    {openFaq === index && (
                      <div className="fg-guide-faq-body">
                        <p style={{ margin: 0 }}>{item.a}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
