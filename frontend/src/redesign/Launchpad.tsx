import { useEffect, useRef, useState, type FormEvent } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowDown, ArrowRight, ArrowUpRight, Braces, Check, ChevronRight, CircleDot, Command, GitBranch, Layers3, LoaderCircle, Play, Radar, ScanLine, ShieldCheck, Sparkles, Terminal } from 'lucide-react';
import { parseGithubUrl } from './data';
import './experience.css';

function GitHubIcon({ size = 18 }: { size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .8a11.3 11.3 0 0 0-3.57 22c.56.1.77-.24.77-.54v-2.1c-3.15.69-3.82-1.34-3.82-1.34-.51-1.3-1.26-1.65-1.26-1.65-1.03-.7.08-.69.08-.69 1.14.08 1.74 1.17 1.74 1.17 1.02 1.74 2.66 1.24 3.31.95.1-.74.4-1.24.72-1.52-2.52-.29-5.17-1.26-5.17-5.59 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.99 0 0 .95-.3 3.11 1.16a10.8 10.8 0 0 1 5.67 0c2.16-1.46 3.11-1.16 3.11-1.16.61 1.56.23 2.71.11 2.99.72.79 1.16 1.8 1.16 3.03 0 4.34-2.66 5.3-5.19 5.58.41.35.77 1.04.77 2.1v3.09c0 .3.21.65.78.54A11.3 11.3 0 0 0 12 .8Z" /></svg>;
}

type LaunchpadProps = { onRun: (url: string, branch: string) => Promise<void>; onDemo: () => void; error: string | null; busy: boolean };

export default function Launchpad({ onRun, onDemo, error, busy }: LaunchpadProps) {
  const [url, setUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [validation, setValidation] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const runLock = useRef(false);
  const reducedMotion = useReducedMotion();
  const normalized = url.trim() ? parseGithubUrl(url.trim()) : null;
  const waiting = busy || submitting;

  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); input.current?.focus(); }
    };
    window.addEventListener('keydown', shortcut);
    return () => window.removeEventListener('keydown', shortcut);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || runLock.current) return;
    const repository = parseGithubUrl(url.trim());
    if (!repository) { setValidation('Enter a GitHub repository URL, such as https://github.com/owner/repository.'); input.current?.focus(); return; }
    const selectedBranch = branch.trim() || 'main';
    if (/\s|\.\.|[~^:?*[\\]/.test(selectedBranch) || selectedBranch.startsWith('-') || selectedBranch.startsWith('/') || selectedBranch.endsWith('/') || selectedBranch.endsWith('.') || selectedBranch.endsWith('.lock') || selectedBranch.includes('//') || selectedBranch.includes('@{') || selectedBranch === '@') { setValidation('Enter a valid branch name without spaces or Git special characters.'); return; }
    setValidation(null);
    runLock.current = true;
    setSubmitting(true);
    try { await onRun(repository, selectedBranch); }
    catch { setValidation('The analysis could not be started. Check that the API is available and try again.'); }
    finally { runLock.current = false; setSubmitting(false); }
  }

  return (
    <div className="fg-launchpad">
      <section className="fg-launch-hero fg-spotlight">
        <motion.div className="fg-launch-copy" initial={reducedMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .35 }}>
          <div className="fg-launch-announcement"><span className="fg-ex-status-dot" /><span>Flaky test investigation</span><span className="fg-launch-announcement-tag">Developer preview</span></div>
          <h1>Find the tests<br />you <span>can’t trust.</span></h1>
          <p className="fg-launch-lede">Understand why a test passes, then fails.</p>
          <p className="fg-launch-subcopy">Run your suite repeatedly, investigate inconsistent results, and review proposed fixes alongside the evidence.</p>
          <div className="fg-launch-points"><span><Check size={14} /> Run-by-run evidence</span><span><Check size={14} /> Reviewable fixes</span></div>
        </motion.div>
        <motion.div className="fg-command-panel fg-panel" initial={reducedMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .35, delay: .1 }}>
          <div className="fg-command-header"><span><Terminal size={16} /> New analysis</span><span>Public repositories</span></div>
          <form onSubmit={submit}>
            <label htmlFor="fg-repository">Analyze a repository</label>
            <p>Start with a public GitHub repository.</p>
            <div className={`fg-repository-input ${normalized ? 'fg-repository-valid' : ''}`}><GitHubIcon size={20} /><input ref={input} id="fg-repository" name="repository" placeholder="github.com/your-org/your-repo" value={url} onChange={event => { setUrl(event.target.value); setValidation(null); }} autoComplete="url" spellCheck={false} disabled={waiting} aria-describedby="fg-repository-help" aria-invalid={!!validation} />{normalized ? <Check size={17} className="fg-ex-positive" aria-label="Valid repository URL" /> : <kbd><Command size={11} /> K</kbd>}</div>
            <div className="fg-command-options"><div className="fg-branch-input"><GitBranch size={15} /><label htmlFor="fg-branch">Branch</label><input id="fg-branch" value={branch} onChange={event => setBranch(event.target.value)} placeholder="main" disabled={waiting} maxLength={200} spellCheck={false} /></div><span className="fg-framework-status"><ScanLine size={14} className="fg-detection-pulse" aria-hidden="true" /><span>Automatic framework detection<small>Awaits analysis API</small></span></span></div>
            <p id="fg-repository-help" className="fg-ex-input-help">Repository and branch are sent to the analysis API. Private-repo authentication is not configured.</p>
            {(validation || error) && <div className="fg-ex-error" role="alert">{validation || error}</div>}
            <button className="fg-button fg-button-primary fg-launch-run" type="submit" disabled={waiting}>{waiting ? <LoaderCircle size={17} className="fg-ex-spin" /> : <Radar size={18} />}{waiting ? 'Starting analysis…' : 'Run diagnostics'}<ArrowRight size={18} /></button>
          </form>
          <div className="fg-command-demo"><span>Just taking a look?</span><button type="button" onClick={onDemo} disabled={waiting}>Explore demo <ArrowUpRight size={15} /></button></div>
        </motion.div>
      </section>
      <div className="fg-launch-section-nav"><a href="#capabilities">How FlakeGuard works <ArrowDown size={15} /></a><span>From inconsistent runs to a fix you can review</span></div>
      <section id="interactive-demo" className="fg-preview-section" aria-label="Illustrative analysis preview">
        <div className="fg-preview-copy"><p className="fg-eyebrow">Inside an investigation</p><h2>One test. Ten runs.<br />A clearer picture.</h2><p>See how run history, a diagnosis, and a proposed code change come together in a sample report.</p><button type="button" className="fg-button fg-preview-demo-button" onClick={onDemo} disabled={waiting}><Play size={14} /> See the investigation <ArrowRight size={15} /></button><span className="fg-preview-disclaimer">Interactive demo · simulated data, no API call</span></div>
        <div className="fg-sample-window fg-panel">
          <div className="fg-sample-title"><span><span className="fg-window-dots"><i /><i /><i /></span><span className="fg-mono">analysis / sample-repository</span></span><span className="fg-badge">Sample · pytest</span></div>
          <div className="fg-sample-flow"><span className="fg-sample-node"><GitHubIcon size={19} /><small>Repository</small></span><ChevronRight size={16} /><span className="fg-sample-node"><Layers3 size={19} /><small>Repeat runs</small></span><ChevronRight size={16} /><span className="fg-sample-node fg-sample-node-active"><Sparkles size={19} /><small>Investigate</small></span><ChevronRight size={16} /><span className="fg-sample-node"><Braces size={19} /><small>Review fix</small></span></div>
          <div className="fg-sample-result"><div><span className="fg-sample-test-icon"><CircleDot size={19} /></span><div><span className="fg-mono">test_session_expiry</span><p>Timing dependency detected in this example</p></div></div><span className="fg-badge fg-sample-flaky">Flaky</span></div>
          <div className="fg-sample-runs"><span className="fg-mono">Runs</span><div aria-label="Example: eight passing runs and two failing runs">{Array.from({ length: 10 }, (_, index) => <span className={index === 3 || index === 7 ? 'fg-sample-run-fail' : ''} key={index} title={`Sample run ${index + 1}: ${index === 3 || index === 7 ? 'fail' : 'pass'}`} />)}</div><span className="fg-mono">8 / 10 pass</span></div>
          <div className="fg-sample-insight"><Sparkles size={15} /><span>“The assertion depends on wall-clock time, not a controlled clock.”</span></div>
        </div>
      </section>
      <section id="capabilities" className="fg-capabilities" aria-label="FlakeGuard capabilities">
        {[{ icon: ScanLine, number: '01', title: 'Reproduce the failure', body: 'Compare repeated runs to distinguish a consistent regression from an intermittent failure.', foot: 'See sample run results' }, { icon: Radar, number: '02', title: 'Investigate the cause', body: 'Specialist agents examine timing, test ordering, shared state, and environment differences.', foot: 'See the investigation' }, { icon: ShieldCheck, number: '03', title: 'Review the proposed fix', body: 'Inspect the diagnosis and suggested code change before deciding what to apply.', foot: 'Explore the demo' }].map(({ icon: Icon, number, title, body, foot }) => <article className="fg-capability" key={number}><div className="fg-capability-top"><Icon size={22} /><span className="fg-mono">{number}</span></div><h3>{title}</h3><p>{body}</p><a className="fg-capability-foot" href="#interactive-demo">{foot}<ArrowUpRight size={15} /></a></article>)}
      </section>
      <footer className="fg-launch-footer"><span>FlakeGuard</span><span>Test reliability, with evidence.</span><a href="#interactive-demo">View the sample investigation <ArrowUpRight size={13} /></a></footer>
    </div>
  );
}
