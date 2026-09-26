import { useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Activity, ArrowDown, ArrowRight, Check, Clock3, Cpu, FileCode2, GitBranch, GitPullRequest, Layers3, LoaderCircle, Radio, ScanLine, Terminal, X } from 'lucide-react';
import './experience.css';

type PipelineProps = { mode: 'demo' | 'live'; repository: string; step: number; elapsed: number; onCancel: () => void };
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
// Parent demo lasts 15 seconds. Gate by both stage and elapsed time so a log
// never claims an event in the future, even if the two props advance separately.
const demoLogs = [
  { stage: 0, at: 0, kind: 'INFO', text: 'Demo initialized. Everything below is scripted sample output.' },
  { stage: 0, at: 1, kind: 'CLONE', text: 'Preparing the sample repository in an isolated workspace…' },
  { stage: 1, at: 3, kind: 'DETECT', text: 'Sample framework: pytest · Python 3.11' },
  { stage: 2, at: 5, kind: 'SCAN', text: 'Discovered sample test cases. Building a repeat-run plan.' },
  { stage: 3, at: 8, kind: 'PASS', text: 'run 01 / test_session_expiry' },
  { stage: 3, at: 9, kind: 'FAIL', text: 'run 02 / test_session_expiry · AssertionError: session expired' },
  { stage: 3, at: 9, kind: 'PASS', text: 'run 03 / test_session_expiry · inconsistent outcome observed' },
  { stage: 4, at: 10, kind: 'BOB', text: 'Dispatching Timing, Ordering, Leakage, Environment specialists.' },
  { stage: 4, at: 12, kind: 'AGENT', text: 'Timing hypothesis: wall-clock dependency in expiry assertion.' },
  { stage: 5, at: 13, kind: 'DIFF', text: 'Sample proposal: inject a controlled clock into the session fixture.' },
  { stage: 5, at: 14, kind: 'INFO', text: 'Preparing the demo report. Review proposed changes before applying.' },
];

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
}

export default function PipelineView({ mode, repository, step, elapsed, onCancel }: PipelineProps) {
  const reducedMotion = useReducedMotion();
  const demo = mode === 'demo';
  const current = Math.max(0, Math.min(stages.length - 1, Math.floor(Number.isFinite(step) ? step : 0)));
  const seconds = Math.max(0, Math.floor(Number.isFinite(elapsed) ? elapsed : 0));
  const agentActive = demo && current === 4;
  const agentDone = demo && current > 4;
  const lines = demoLogs.filter(log => log.stage <= current && log.at <= seconds);
  const consoleRef = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const [following, setFollowing] = useState(true);
  const lineCount = demo ? lines.length : 3;

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
      <div className="fg-pipeline-topline"><p className="fg-eyebrow"><span className="fg-ex-status-dot" /> {demo ? 'SIMULATED INVESTIGATION' : 'ANALYSIS REQUEST IN PROGRESS'}</p><button type="button" className="fg-button fg-pipeline-cancel" onClick={onCancel}><X size={14} />{demo ? 'Exit demo' : 'Cancel / return'}</button></div>
      <header className="fg-pipeline-heading"><div><h1>{demo ? 'Following the evidence.' : 'Your repository. Awaiting results.'}</h1><p>{demo ? 'A guided look at how an intermittent failure becomes an actionable fix.' : 'Your request has been sent. We’ll show the report when the API responds.'}</p></div><div className="fg-pipeline-clock"><Clock3 size={16} /><strong className="fg-mono">{formatTime(seconds)}</strong><span>ELAPSED</span></div></header>
      <div className="fg-pipeline-repo"><span><GitBranch size={16} /><span className="fg-mono">{repository || (demo ? 'sample / flaky-test-suite' : 'Submitted repository')}</span></span><span className={`fg-badge ${demo ? 'fg-pipeline-demo-badge' : ''}`}>{demo ? 'DEMO · SIMULATED DATA' : 'LIVE API REQUEST'}</span></div>
      {!demo && <div className="fg-pipeline-honesty" role="status"><Radio size={19} /><div><strong>Live progress unavailable · waiting for the API response</strong><p>This API returns completed results, not a stream. Individual milestones, test outcomes, and agent activity are unavailable while it runs. The stages below describe the expected workflow, not live progress.</p></div></div>}
      <div className="fg-pipeline-workspace">
        <section className="fg-pipeline-stages fg-panel" aria-label={demo ? 'Simulated pipeline progress' : 'Expected pipeline stages, status unavailable'}>
          <div className="fg-pipeline-section-header"><span className="fg-eyebrow">THE INVESTIGATION</span><span className="fg-mono">{demo ? `${String(current + 1).padStart(2, '0')} / 06` : 'STATUS UNAVAILABLE'}</span></div>
          <ol>{stages.map(({ title, detail, icon: Icon }, index) => {
            const done = demo && index < current;
            const active = demo && index === current;
            return <li key={title} className={`${active ? 'fg-stage-active' : ''} ${done ? 'fg-stage-done' : ''}`} aria-current={active ? 'step' : undefined}><span className="fg-stage-icon">{done ? <motion.span className="fg-completion-check" key="complete" initial={reducedMotion ? false : { scale: .4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 420, damping: 16 }}><Check size={17} /></motion.span> : active ? <LoaderCircle size={17} className="fg-ex-spin" /> : <Icon size={17} />}</span><div><span className="fg-stage-number fg-mono">0{index + 1}</span><h2>{title}</h2><p>{detail}</p><span className="fg-stage-status">{!demo ? 'Not reported' : done ? 'Simulated · complete' : active ? 'Simulated · in progress' : 'Queued in demo'}</span></div>{active && <span className="fg-stage-active-dot" />}</li>;
          })}</ol>
          <div className="fg-stage-footer"><span className="fg-mono">{demo ? 'SCRIPTED PREVIEW' : 'NO ESTIMATED COMPLETION'}</span><ArrowRight size={14} /></div>
        </section>
        <div className="fg-pipeline-main">
          <section className="fg-agent-section fg-panel" aria-label="Specialist agents">
            <div className="fg-pipeline-section-header"><span><Cpu size={17} /><strong>Four minds on the problem.</strong></span><span className="fg-badge">BOB ORCHESTRATOR</span></div>
            <p className="fg-agent-intro">{demo ? 'Independent perspectives. One coordinated investigation.' : 'Specialist roles shown for reference only. Standby display — execution status is unavailable.'}</p>
            <div className="fg-agent-grid">{agents.map(({ name, code, detail, color, icon: Icon }, index) => <article className={`fg-agent-card fg-agent-${color} ${agentActive ? 'fg-agent-active' : agentDone ? 'fg-agent-done' : 'fg-agent-idle'}`} key={name}>
              <div className="fg-agent-card-top"><span className="fg-mono">{code}</span><span className="fg-agent-status-dot" /></div>
              <div className="fg-agent-radar" aria-hidden="true"><span /><span /><span />{agentActive && <motion.div className="fg-agent-radar-sweep" animate={!reducedMotion ? { rotate: [index * 90, index * 90 + 360] } : { rotate: index * 90 }} transition={!reducedMotion ? { duration: 3.5, repeat: Infinity, ease: 'linear' } : { duration: 0 }} />}{agentDone ? <motion.div className="fg-agent-complete" initial={reducedMotion ? false : { scale: .35, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 380, damping: 14 }}><Check size={25} /></motion.div> : <Icon size={21} />}</div>
              <h3>{name}</h3><p>{detail}</p><div className="fg-agent-card-status">{!demo ? 'Standby · status unavailable' : agentDone ? 'Sample evidence ready' : agentActive ? 'Simulating investigation' : 'Standing by in demo'}</div>
            </article>)}</div>
          </section>
          <section className="fg-pipeline-console fg-panel" aria-label={demo ? 'Scripted demo console output' : 'Live request status'}>
            <div className="fg-console-header"><span><Terminal size={15} />{demo ? 'Investigation console' : 'Request console'}</span><span className="fg-mono">{demo ? 'SIMULATED OUTPUT' : 'NOT A LOG STREAM'}</span></div>
            <div ref={consoleRef} className="fg-console-lines" role="log" aria-label="Console output" aria-live="polite" aria-relevant="additions" tabIndex={0}>
              {demo ? lines.map(line => <motion.div key={`${line.at}-${line.kind}`} className={`fg-console-line fg-log-${line.kind.toLowerCase()}`} initial={reducedMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: .2 }}><time>{formatTime(line.at)}</time><span className={`fg-console-kind fg-console-kind-${line.kind.toLowerCase()}`}>{line.kind}</span><span>{line.text}</span></motion.div>) : <><div className="fg-console-line"><time>--:--</time><span className="fg-console-kind">API</span><span>Analysis request sent. Awaiting a completed response.</span></div><div className="fg-console-line"><time>--:--</time><span className="fg-console-kind">INFO</span><span>No intermediate logs or PASS/FAIL results have been received.</span></div><div className="fg-console-line"><time>--:--</time><span className="fg-console-kind">NOTE</span><span>Leaving this view may not stop work already running on the server.</span></div></>}
              {demo && <span className="fg-console-cursor" aria-hidden="true" />}
            </div>
            <div className="fg-console-toolbar"><span>{demo ? 'Scripted preview · no real log stream' : 'Intermediate output unavailable'}</span><button type="button" className="fg-button fg-console-follow" onClick={followOutput} disabled={following}><ArrowDown size={13} />{following ? 'Following output' : 'Follow output'}</button></div>
          </section>
        </div>
      </div>
      <footer className="fg-pipeline-footer"><span><Check size={13} /> {demo ? 'No repository is being cloned. No tests are running.' : 'Results appear only after the API responds.'}</span><span className="fg-mono">{demo ? 'A WALKTHROUGH, NOT A LIVE RUN' : 'EVIDENCE BEFORE ASSUMPTIONS'}</span></footer>
    </div>
  );
}
