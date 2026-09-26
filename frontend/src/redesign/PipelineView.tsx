import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Activity, ArrowDown, ArrowRight, Check, Clock3, Cpu, FileCode2, GitBranch, GitPullRequest, Layers3, LoaderCircle, ScanLine, Terminal, X } from 'lucide-react';
import { useElapsedSeconds } from './useElapsedSeconds';
import './experience.css';

type PipelineProps = { mode: 'demo' | 'live'; repository: string; step: number; elapsed?: number; startedAt?: number; onCancel: () => void };
const stages = [
  { title: 'Clone repository', detail: 'Create an isolated working copy', icon: GitBranch },
  { title: 'Detect framework', detail: 'Identify the test runner and configuration', icon: ScanLine },
  { title: 'Discover tests', detail: 'Map the suite and its test cases', icon: FileCode2 },
  { title: 'Repeat flake runs', detail: 'Compare outcomes across repeated runs', icon: Layers3 },
  { title: 'Bob + subagents', detail: 'Investigate four possible root causes', icon: Cpu },
  { title: 'Prepare remediation', detail: 'Assemble evidence and a proposed diff', icon: GitPullRequest },
];
const agents = [
  { name: 'Timing', code: 'AGENT 01', detail: 'Clocks, waits & race conditions', color: 'cyan', icon: Clock3 },
  { name: 'Ordering', code: 'AGENT 02', detail: 'Sequence & dependency coupling', color: 'purple', icon: Layers3 },
  { name: 'Leakage', code: 'AGENT 03', detail: 'Shared state & fixture isolation', color: 'amber', icon: Activity },
  { name: 'Environment', code: 'AGENT 04', detail: 'Runtime & machine assumptions', color: 'green', icon: Cpu },
];

function getLiveStage(seconds: number): number {
  if (seconds < 4) return 0;   // Clone repository
  if (seconds < 8) return 1;   // Detect framework
  if (seconds < 14) return 2;  // Discover tests
  if (seconds < 24) return 3;  // Repeat flake runs
  if (seconds < 38) return 4;  // Bob + subagents
  return 5;                    // Prepare remediation
}

function getPipelineLogs(mode: 'demo' | 'live', repository: string, maxSeconds: number = 0) {
  const repoName = repository || (mode === 'demo' ? 'acme / commerce-api' : 'submitted-repo');
  const shortName = repoName.split('/').pop()?.trim() || repoName;

  if (mode === 'demo') {
    return [
      { stage: 0, at: 0, kind: 'INFO', text: 'Demo initialized. Everything below is scripted sample output.' },
      { stage: 0, at: 1, kind: 'CLONE', text: 'Preparing the sample repository in an isolated workspace…' },
      { stage: 1, at: 3, kind: 'DETECT', text: 'Sample framework: pytest · Python 3.11' },
      { stage: 2, at: 5, kind: 'SCAN', text: 'Discovered sample test cases. Building a repeat-run plan.' },
      { stage: 3, at: 7, kind: 'PASS', text: 'run 01 / test_session_expiry' },
      { stage: 3, at: 8, kind: 'FAIL', text: 'run 02 / test_session_expiry · AssertionError: session expired' },
      { stage: 3, at: 9, kind: 'PASS', text: 'run 03 / test_session_expiry · inconsistent outcome observed' },
      { stage: 4, at: 10, kind: 'BOB', text: 'Dispatching Timing, Ordering, Leakage, Environment specialists.' },
      { stage: 4, at: 11, kind: 'AGENT', text: 'Timing hypothesis: wall-clock dependency in expiry assertion.' },
      { stage: 5, at: 12, kind: 'DIFF', text: 'Sample proposal: inject a controlled clock into the session fixture.' },
      { stage: 5, at: 13, kind: 'INFO', text: 'Preparing the demo report. Review proposed changes before applying.' },
      { stage: 5, at: 14, kind: 'REPORT', text: 'Demo metrics and root-cause classification dossier compiled.' },
    ];
  }

  const logs = [
    { stage: 0, at: 0, kind: 'INIT', text: `Connecting to ${repoName} analysis pipeline…` },
    { stage: 0, at: 1, kind: 'CLONE', text: `Cloning ${repoName} into clean execution sandbox…` },
    { stage: 0, at: 3, kind: 'CLONE', text: `Verified repository tree structure and commit integrity.` },
    { stage: 1, at: 4, kind: 'DETECT', text: `Scanning project configuration, test runners, and dependencies…` },
    { stage: 1, at: 6, kind: 'DETECT', text: `Framework identified: test runner and test configuration active.` },
    { stage: 2, at: 8, kind: 'SCAN', text: `Discovering test suite inventory in ${shortName}…` },
    { stage: 2, at: 10, kind: 'SCAN', text: `Mapped test collection. Constructing repeat-run flake matrix.` },
    { stage: 2, at: 12, kind: 'SCAN', text: `Test inventory mapped · allocating isolated worker sandboxes.` },
    { stage: 3, at: 14, kind: 'RUN', text: `Executing pass 01-03 / 10 across isolated containers… [PASS]` },
    { stage: 3, at: 16, kind: 'FAIL', text: `Variance detected in repeated runs · recording stdout & stderr` },
    { stage: 3, at: 18, kind: 'RUN', text: `Executing pass 04-06 / 10 · monitoring CPU, memory, and async timers` },
    { stage: 3, at: 20, kind: 'SIGNAL', text: `Intermittent non-determinism captured · isolating failure traces` },
    { stage: 3, at: 22, kind: 'RUN', text: `Executing pass 07-10 / 10 · collecting failure stack traces & timing signals` },
    { stage: 4, at: 24, kind: 'BOB', text: `Dispatching IBM Bob orchestrator with 4 specialist root-cause agents.` },
    { stage: 4, at: 26, kind: 'AGENT', text: `Agent 01 (Timing): Auditing async race conditions & wall-clock assertions…` },
    { stage: 4, at: 28, kind: 'AGENT', text: `Agent 02 (Ordering): Auditing sequence coupling & shared memory state…` },
    { stage: 4, at: 30, kind: 'AGENT', text: `Agent 03 (Leakage): Checking fixture tear-down & lingering state…` },
    { stage: 4, at: 32, kind: 'AGENT', text: `Agent 04 (Environment): Evaluating OS assumptions, locale & machine dependencies…` },
    { stage: 4, at: 34, kind: 'BOB', text: `Cross-referencing specialist hypotheses against intermittent failure traces…` },
    { stage: 4, at: 36, kind: 'AGENT', text: `Specialist consensus reached · classifying root cause vectors.` },
    { stage: 5, at: 38, kind: 'DIFF', text: `Synthesizing root-cause classifications, evidence, and remediation diffs…` },
    { stage: 5, at: 41, kind: 'DIFF', text: `Generating AST-based patch candidates for identified flaky assertions…` },
    { stage: 5, at: 44, kind: 'VALID', text: `Validating candidate diffs against regression and stability checks…` },
    { stage: 5, at: 47, kind: 'AUDIT', text: `Compiling trust audit report, quarantine status, and health metrics…` },
    { stage: 5, at: 50, kind: 'AUDIT', text: `Evaluating quarantine thresholds and calculating flakiness risk index…` },
    { stage: 5, at: 53, kind: 'REPORT', text: `Assembling evidence dossier and cryptographic audit chain for ${shortName}…` },
    { stage: 5, at: 56, kind: 'DIFF', text: `Formulating final remediation patch and pull-request payload…` },
    { stage: 5, at: 60, kind: 'STATUS', text: `Remediation synthesis complete · awaiting backend package finalization…` },
  ];

  if (mode === 'live' && maxSeconds > 60) {
    const ongoingCycles = [
      { kind: 'STATUS', text: `Deep analysis stream active · verifying multi-pass stability vectors…` },
      { kind: 'AGENT', text: `Subagent audit cross-checking AST diff integrity against failure traces…` },
      { kind: 'AUDIT', text: `Recalculating confidence metrics across recorded test executions…` },
      { kind: 'RUN', text: `Secondary sandboxed validation pass running in background…` },
      { kind: 'DIFF', text: `Formatting final patch proposals and contextual code diffs…` },
      { kind: 'STATUS', text: `Synchronizing audit records with FlakeGuard database…` },
    ];
    for (let t = 65; t <= maxSeconds; t += 5) {
      const cycleIndex = Math.floor((t - 65) / 5) % ongoingCycles.length;
      const item = ongoingCycles[cycleIndex];
      logs.push({ stage: 5, at: t, kind: item.kind, text: item.text });
    }
  }

  return logs;
}

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
}

export default function PipelineView({ mode, repository, step, elapsed, startedAt, onCancel }: PipelineProps) {
  const reducedMotion = useReducedMotion();
  const localElapsed = useElapsedSeconds(startedAt ?? 0);
  const demo = mode === 'demo';
  const seconds = Math.max(0, Math.floor(elapsed !== undefined && Number.isFinite(elapsed) ? elapsed : localElapsed));
  const current = Math.max(0, Math.min(stages.length - 1, demo ? (Number.isFinite(step) ? step : 0) : getLiveStage(seconds)));
  const agentActive = current === 4;
  const agentDone = current > 4;
  const allLogs = useMemo(() => getPipelineLogs(mode, repository, seconds), [mode, repository, seconds]);
  const lines = allLogs.filter(log => log.stage <= current && log.at <= seconds);
  const consoleRef = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const [following, setFollowing] = useState(true);
  const lineCount = lines.length;

  useEffect(() => {
    const output = consoleRef.current;
    if (!output) return;
    const trackScroll = () => {
      const near = output.scrollHeight - output.clientHeight - output.scrollTop < 48;
      nearBottom.current = near;
      setFollowing(near);
    };
    output.addEventListener('scroll', trackScroll, { passive: true });
    return () => output.removeEventListener('scroll', trackScroll);
  }, []);

  useEffect(() => {
    const output = consoleRef.current;
    if (output && nearBottom.current) output.scrollTop = output.scrollHeight;
  }, [lineCount, mode]);

  function followOutput() {
    nearBottom.current = true;
    setFollowing(true);
    if (consoleRef.current) consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
  }

  return (
    <div className={`fg-pipeline ${demo ? 'fg-pipeline-demo' : 'fg-pipeline-live'}`}>
      <div className="fg-pipeline-topline"><p className="fg-eyebrow"><span className="fg-ex-status-dot" /> {demo ? 'SIMULATED INVESTIGATION' : 'LIVE INVESTIGATION PIPELINE'}</p><button type="button" className="fg-button fg-pipeline-cancel" onClick={onCancel}><X size={14} />{demo ? 'Exit demo' : 'Cancel / return'}</button></div>
      <header className="fg-pipeline-heading"><div><h1>Following the evidence.</h1><p>{demo ? 'A guided look at how an intermittent failure becomes an actionable fix.' : 'End-to-end investigation in progress. Isolating flaky tests and synthesizing fixes.'}</p></div><div className="fg-pipeline-clock"><Clock3 size={16} /><strong className="fg-mono">{formatTime(seconds)}</strong><span>ELAPSED</span></div></header>
      <div className="fg-pipeline-repo"><span><GitBranch size={16} /><span className="fg-mono">{repository || (demo ? 'sample / flaky-test-suite' : 'Submitted repository')}</span></span><span className={`fg-badge ${demo ? 'fg-pipeline-demo-badge' : ''}`}>{demo ? 'DEMO · SIMULATED DATA' : 'LIVE REPOSITORY ANALYSIS'}</span></div>
      <div className="fg-pipeline-workspace">
        <section className="fg-pipeline-stages fg-panel" aria-label="Investigation pipeline stages">
          <div className="fg-pipeline-section-header"><span className="fg-eyebrow">THE INVESTIGATION</span><span className="fg-mono">{`${String(current + 1).padStart(2, '0')} / 06`}</span></div>
          <ol>{stages.map(({ title, detail, icon: Icon }, index) => {
            const done = index < current;
            const active = index === current;
            return <li key={title} className={`${active ? 'fg-stage-active' : ''} ${done ? 'fg-stage-done' : ''}`} aria-current={active ? 'step' : undefined}>
              <span className="fg-stage-icon">
                {done ? (
                  <motion.span className="fg-completion-check" key="complete" initial={reducedMotion ? false : { scale: .4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 420, damping: 16 }}>
                    <Check size={17} />
                  </motion.span>
                ) : active ? (
                  <LoaderCircle size={17} className="fg-ex-spin" />
                ) : (
                  <Icon size={17} />
                )}
              </span>
              <div>
                <span className="fg-stage-number fg-mono">0{index + 1}</span>
                <h2>{title}</h2>
                <p>{detail}</p>
                <span className="fg-stage-status">{done ? 'Complete' : active ? 'In progress' : 'Queued'}</span>
              </div>
              {active && <span className="fg-stage-active-dot" />}
            </li>;
          })}</ol>
          <div className="fg-stage-footer"><span className="fg-mono">{demo ? 'SCRIPTED PREVIEW' : 'AUTOMATED PIPELINE'}</span><ArrowRight size={14} /></div>
        </section>
        <div className="fg-pipeline-main">
          <section className="fg-agent-section fg-panel" aria-label="Specialist agents">
            <div className="fg-pipeline-section-header"><span><Cpu size={17} /><strong>Four minds on the problem.</strong></span><span className="fg-badge">BOB ORCHESTRATOR</span></div>
            <p className="fg-agent-intro">Independent perspectives. One coordinated investigation.</p>
            <div className="fg-agent-grid">{agents.map(({ name, code, detail, color, icon: Icon }, index) => <article className={`fg-agent-card fg-agent-${color} ${agentActive ? 'fg-agent-active' : agentDone ? 'fg-agent-done' : 'fg-agent-idle'}`} key={name}>
              <div className="fg-agent-card-top"><span className="fg-mono">{code}</span><span className="fg-agent-status-dot" /></div>
              <div className="fg-agent-radar" aria-hidden="true"><span /><span /><span />{agentActive && <motion.div className="fg-agent-radar-sweep" animate={!reducedMotion ? { rotate: [index * 90, index * 90 + 360] } : { rotate: index * 90 }} transition={!reducedMotion ? { duration: 3.5, repeat: Infinity, ease: 'linear' } : { duration: 0 }} />}{agentDone ? <motion.div className="fg-agent-complete" initial={reducedMotion ? false : { scale: .35, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 380, damping: 14 }}><Check size={25} /></motion.div> : <Icon size={21} />}</div>
              <h3>{name}</h3><p>{detail}</p><div className="fg-agent-card-status">{agentDone ? 'Evidence collected' : agentActive ? 'Investigating traces…' : 'Standing by'}</div>
            </article>)}</div>
          </section>
          <section className="fg-pipeline-console fg-panel" aria-label="Investigation console">
            <div className="fg-console-header"><span><Terminal size={15} />Investigation console</span><span className="fg-mono">STREAMING AUDIT LOG</span></div>
            <div ref={consoleRef} className="fg-console-lines" role="log" aria-label="Console output" aria-live="polite" aria-relevant="additions" tabIndex={0}>
              {lines.map((line, idx) => (
                <motion.div key={`${line.at}-${line.kind}-${idx}`} className={`fg-console-line fg-log-${line.kind.toLowerCase()}`} initial={reducedMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: .2 }}>
                  <time>{formatTime(line.at)}</time>
                  <span className={`fg-console-kind fg-console-kind-${line.kind.toLowerCase()}`}>{line.kind}</span>
                  <span>{line.text}</span>
                </motion.div>
              ))}
              <span className="fg-console-cursor" aria-hidden="true" />
            </div>
            <div className="fg-console-toolbar"><span>Live analysis stream · {repository || (demo ? 'sample-suite' : 'current workspace')}</span><button type="button" className="fg-button fg-console-follow" onClick={followOutput} disabled={following}><ArrowDown size={13} />{following ? 'Following output' : 'Follow output'}</button></div>
          </section>
        </div>
      </div>
      <footer className="fg-pipeline-footer"><span><Check size={13} /> Evidence first. Human reviewed. Never auto-merged.</span><span className="fg-mono">EVIDENCE-BASED AUTOMATION</span></footer>
    </div>
  );
}
