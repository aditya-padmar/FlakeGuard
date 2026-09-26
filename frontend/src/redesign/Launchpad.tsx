import { useEffect, useRef, useState, type FormEvent } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, ArrowUpRight, Braces, Check, ChevronRight, CircleDot, Command, Layers3, LoaderCircle, Play, Radar, ScanLine, ShieldCheck, Sparkles } from 'lucide-react';
import { parseGithubUrl } from './data';
import { useSamplePlayback } from './useSamplePlayback';
import { BeamsBackground } from '@/components/ui/beams-background';
import { ShineBorder } from '@/components/ui/shine-border';
import { BorderBeam } from '@/registry/magicui/border-beam';
import { ShimmerButton } from '@/registry/magicui/shimmer-button';
import './experience.css';

function GitHubIcon({ size = 18 }: { size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .8a11.3 11.3 0 0 0-3.57 22c.56.1.77-.24.77-.54v-2.1c-3.15.69-3.82-1.34-3.82-1.34-.51-1.3-1.26-1.65-1.26-1.65-1.03-.7.08-.69.08-.69 1.14.08 1.74 1.17 1.74 1.17 1.74 1.17 1.02 1.74 2.66 1.24 3.31.95.1-.74.4-1.24.72-1.52-2.52-.29-5.17-1.26-5.17-5.59 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.99 0 0 .95-.3 3.11 1.16a10.8 10.8 0 0 1 5.67 0c2.16-1.46 3.11-1.16 3.11-1.16.61 1.56.23 2.71.11 2.99.72.79 1.16 1.8 1.16 3.03 0 4.34-2.66 5.3-5.19 5.58.41.35.77 1.04.77 2.1v3.09c0 .3.21.65.78.54A11.3 11.3 0 0 0 12 .8Z" /></svg>;
}

type SampleScenario = {
  repo: string;
  badge: string;
  testName: string;
  category: string;
  flakyRate: string;
  failIndices: number[];
  stages: {
    cmd: string;
    output: string;
    tag: string;
    diffDel?: string;
    diffAdd?: string;
  }[];
  insight: string;
  verified: string;
};

const SAMPLE_SCENARIOS: SampleScenario[] = [
  {
    repo: 'analysis / auth-session-service',
    badge: 'Sample · pytest',
    testName: 'test_session_expiry',
    category: 'Timing dependency detected in this example',
    flakyRate: 'Flaky · 20%',
    failIndices: [3, 7],
    stages: [
      {
        tag: 'Target Discovery',
        cmd: 'pytest --collect-only tests/test_session.py',
        output: 'Discovered: tests/test_session.py::test_session_expiry',
      },
      {
        tag: 'Chaos Execution',
        cmd: 'pytest -k test_session_expiry --repeat=10 --chaos=jitter',
        output: 'Run #4: AssertionError: token expired (delta: +14ms clock drift)',
      },
      {
        tag: 'Root Cause Diagnosis',
        cmd: 'agent.bob: analyzing AST stack frames and wall-clock jitter...',
        output: 'Diagnosis: wall-clock drift between token issuance and assertion',
      },
      {
        tag: 'Automated Fix Applied',
        cmd: 'git diff patch/test_session_expiry.py',
        output: 'Verified: 10 / 10 runs passed with monotonic clock fixture',
        diffDel: '- if time.time() - token.created_at > 3600:',
        diffAdd: '+ if time.monotonic() - token.created_at > 3600:',
      },
    ],
    insight: '“The assertion depends on wall-clock time, not a controlled clock.”',
    verified: '“Patch verified: 10 / 10 repeated runs passed successfully.”',
  },
  {
    repo: 'analysis / worker-pipeline-service',
    badge: 'Sample · pytest',
    testName: 'test_worker_thread_race',
    category: 'Concurrency race & thread unsafety detected',
    flakyRate: 'Flaky · 30%',
    failIndices: [2, 5, 8],
    stages: [
      {
        tag: 'Target Discovery',
        cmd: 'pytest --collect-only tests/test_workers.py',
        output: 'Discovered: tests/test_workers.py::test_worker_thread_race',
      },
      {
        tag: 'Thread Chaos',
        cmd: 'pytest -k test_worker_thread_race --repeat=10 --threads=4',
        output: 'Run #3: ConcurrencyHazard: Counter lost 2 increments under load',
      },
      {
        tag: 'Root Cause Diagnosis',
        cmd: 'agent.bob: detecting unsynchronized memory mutation...',
        output: 'Diagnosis: concurrent write hazard on unprotected accumulator',
      },
      {
        tag: 'Automated Fix Applied',
        cmd: 'git diff patch/test_worker_thread_race.py',
        output: 'Verified: 10 / 10 runs passed with mutex synchronization',
        diffDel: '- self.counter += delta',
        diffAdd: '+ with self._lock: self.counter += delta',
      },
    ],
    insight: '“Shared counter mutated across worker threads without an acquisition lock.”',
    verified: '“Patch verified: Lock acquisition prevents concurrent race conditions.”',
  },
  {
    repo: 'analysis / redis-cache-store',
    badge: 'Sample · jest',
    testName: 'test_cache_state_leakage',
    category: 'State pollution & unisolated singleton cache',
    flakyRate: 'Flaky · 40%',
    failIndices: [1, 4, 6, 9],
    stages: [
      {
        tag: 'Target Discovery',
        cmd: 'jest --listTests --testPathPattern=cache',
        output: 'Discovered: tests/cache.spec.ts::test_cache_state_leakage',
      },
      {
        tag: 'State Chaos',
        cmd: 'jest --repeat=10 --runInBand --shuffleSeed=4821',
        output: 'Run #2: Expected null, received persisted session key usr_9921',
      },
      {
        tag: 'Root Cause Diagnosis',
        cmd: 'agent.bob: tracing fixture lifecycle and global singleton...',
        output: 'Diagnosis: preceding test mutated Redis cache without eviction',
      },
      {
        tag: 'Automated Fix Applied',
        cmd: 'git diff patch/cache.spec.ts',
        output: 'Verified: 10 / 10 runs passed with teardown cache eviction',
        diffDel: '- beforeEach(() => { initCache(); })',
        diffAdd: '+ afterEach(async () => { await cache.flushAll(); })',
      },
    ],
    insight: '“Preceding test mutated cache singleton without an afterEach() eviction.”',
    verified: '“Patch verified: Automated teardown guarantees pristine sandbox state.”',
  },
  {
    repo: 'analysis / gateway-http-client',
    badge: 'Sample · pytest',
    testName: 'test_network_retry_backoff',
    category: 'Async I/O socket timeout under latency jitter',
    flakyRate: 'Flaky · 20%',
    failIndices: [0, 6],
    stages: [
      {
        tag: 'Target Discovery',
        cmd: 'pytest --collect-only tests/test_gateway.py',
        output: 'Discovered: tests/test_gateway.py::test_network_retry_backoff',
      },
      {
        tag: 'Network Chaos',
        cmd: 'pytest -k test_network_retry_backoff --repeat=10 --sim-jitter',
        output: 'Run #1: TimeoutError: Gateway read exceeded 100ms socket deadline',
      },
      {
        tag: 'Root Cause Diagnosis',
        cmd: 'agent.bob: measuring socket latency distribution curve...',
        output: 'Diagnosis: static 100ms deadline violates P95 simulated latency',
      },
      {
        tag: 'Automated Fix Applied',
        cmd: 'git diff patch/test_gateway.py',
        output: 'Verified: 10 / 10 runs passed with exponential retry backoff',
        diffDel: '- response = await client.get(url, timeout=0.100)',
        diffAdd: '+ response = await client.get(url, timeout=backoff(attempt))',
      },
    ],
    insight: '“Static 100ms timeout fails whenever simulated CI network exceeds P95.”',
    verified: '“Patch verified: Exponential backoff accommodates transient spikes.”',
  },
];

type LaunchpadProps = { onRun: (url: string, branch: string) => Promise<void>; onDemo: () => void; error: string | null; busy: boolean };

export default function Launchpad({ onRun, onDemo, error, busy }: LaunchpadProps) {
  const [url, setUrl] = useState('');
  const [branch] = useState('main');
  const [validation, setValidation] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const runLock = useRef(false);
  const reducedMotion = useReducedMotion();
  const normalized = url.trim() ? parseGithubUrl(url.trim()) : null;
  const waiting = busy || submitting;

  const { previewRef, activeStage, scenarioIndex, runProgress } = useSamplePlayback(SAMPLE_SCENARIOS.length, reducedMotion);

  const activeScenario = SAMPLE_SCENARIOS[scenarioIndex];
  const stageData = activeScenario.stages[activeStage];

  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); input.current?.focus(); }
    };
    window.addEventListener('keydown', shortcut);
    return () => window.removeEventListener('keydown', shortcut);
  }, []);

  const [isRolling, setIsRolling] = useState(false);
  const mounted = useRef(false);
  const rollTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; clearTimeout(rollTimer.current); };
  }, []);
  const radarRef = useRef<HTMLSpanElement>(null);
  const arrowRef = useRef<HTMLSpanElement>(null);
  const [rollDistance, setRollDistance] = useState(0);

  useEffect(() => {
    const updateDistance = () => {
      if (radarRef.current && arrowRef.current) {
        const dist = arrowRef.current.offsetLeft - radarRef.current.offsetLeft;
        if (dist > 0) setRollDistance(dist);
      }
    };
    updateDistance();
    window.addEventListener('resize', updateDistance);
    return () => window.removeEventListener('resize', updateDistance);
  }, []);

  async function executeDiagnostics(repository: string, selectedBranch: string) {
    if (!mounted.current) return;
    setSubmitting(true);
    try { await onRun(repository, selectedBranch); }
    catch { if (mounted.current) setValidation('The analysis could not be started. Check that the API is available and try again.'); }
    finally { runLock.current = false; if (mounted.current) setSubmitting(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || runLock.current || isRolling) return;
    const repository = parseGithubUrl(url.trim());
    if (!repository) { setValidation('Enter a GitHub repository URL, such as https://github.com/owner/repository.'); input.current?.focus(); return; }
    setValidation(null);
    const selectedBranch = branch.trim() || 'main';
    runLock.current = true;

    if (radarRef.current && arrowRef.current) {
      const dist = arrowRef.current.offsetLeft - radarRef.current.offsetLeft;
      if (dist > 0) setRollDistance(dist);
    }

    if (!reducedMotion) {
      setIsRolling(true);
      rollTimer.current = setTimeout(() => {
        if (!mounted.current) return;
        setIsRolling(false);
        void executeDiagnostics(repository, selectedBranch);
      }, 550);
    } else {
      await executeDiagnostics(repository, selectedBranch);
    }
  }

  return (
    <div className="fg-launchpad">
      <div className="fg-launch-gradient" aria-hidden="true">
        <BeamsBackground intensity="strong" className="h-full min-h-0" />
      </div>
      <section className="fg-launch-hero">
        <motion.div className="fg-launch-copy" initial={reducedMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .35 }}>
          <h1>Find the tests<br />you <span>can’t trust.</span></h1>
          <p className="fg-launch-lede">Understand why a test passes, then fails.</p>
          <p className="fg-launch-subcopy">Run your suite repeatedly, investigate inconsistent results, and review proposed fixes alongside the evidence.</p>
          <div className="fg-launch-points"><span><Check size={14} /> Run-by-run evidence</span><span><Check size={14} /> Reviewable fixes</span></div>
        </motion.div>
        <motion.div className="fg-command-panel" initial={reducedMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .35, delay: .1 }}>
          <form onSubmit={submit}>
            <label htmlFor="fg-repository">Analyze a repository</label>
            <p>Start with a public GitHub repository.</p>
            <div className={`fg-repository-input ${normalized ? 'fg-repository-valid' : ''}`}>
              <GitHubIcon size={20} />
              <input ref={input} id="fg-repository" name="repository" placeholder="github.com/your-org/your-repo" value={url} onChange={event => { setUrl(event.target.value); setValidation(null); }} autoComplete="url" spellCheck={false} disabled={waiting || isRolling} aria-invalid={!!validation} />
              {normalized ? <Check size={17} className="fg-ex-positive" aria-label="Valid repository URL" /> : <kbd><Command size={11} /> K</kbd>}
              <BorderBeam duration={8} size={100} />
            </div>
            {(validation || error) && <div className="fg-ex-error" role="alert">{validation || error}</div>}
            <button className="fg-button fg-button-primary fg-launch-run" type="submit" disabled={waiting || isRolling}>
              {isRolling && (
                <motion.div
                  className="fg-launch-run-trail"
                  initial={{ width: 0, opacity: 0.6 }}
                  animate={{ width: rollDistance || 320, opacity: 0 }}
                  transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                />
              )}
              <motion.span
                ref={radarRef}
                className="fg-launch-run-radar"
                animate={
                  isRolling
                    ? {
                        x: rollDistance || 320,
                        rotate: 1080,
                        scale: [1, 1.2, 1],
                      }
                    : {
                        x: 0,
                        rotate: 0,
                        scale: 1,
                      }
                }
                transition={
                  isRolling
                    ? {
                        duration: 0.55,
                        ease: [0.22, 1, 0.36, 1],
                      }
                    : { duration: 0.15 }
                }
              >
                {waiting ? <LoaderCircle size={17} className="fg-ex-spin" /> : <Radar size={18} />}
              </motion.span>
              <span className="fg-launch-run-label">
                {waiting ? 'Starting analysis…' : isRolling ? 'Targeting…' : 'Run diagnostics'}
              </span>
              <motion.span
                ref={arrowRef}
                className="fg-launch-run-arrow"
                animate={
                  isRolling
                    ? {
                        x: [0, 0, 5, 0],
                        scale: [1, 1, 1.45, 1],
                      }
                    : { x: 0, scale: 1 }
                }
                transition={
                  isRolling
                    ? {
                        duration: 0.55,
                        times: [0, 0.78, 0.9, 1],
                        ease: 'easeOut',
                      }
                    : { duration: 0.15 }
                }
              >
                <ArrowRight size={18} />
              </motion.span>
            </button>
          </form>
          <div className="fg-command-demo"><span>Just taking a look?</span><button type="button" onClick={onDemo} disabled={waiting || isRolling}>Explore demo <ArrowUpRight size={15} /></button></div>
        </motion.div>
      </section>
      <section ref={previewRef} id="interactive-demo" className="fg-preview-section" aria-label="Illustrative analysis preview">
        <div className="fg-preview-copy">
          <p className="fg-eyebrow">Inside an investigation</p>
          <h2>One test. Ten runs.<br />A clearer picture.</h2>
          <p>See how run history, a diagnosis, and a proposed code change come together in a sample report.</p>
          <ShimmerButton
            shimmerColor="#00F0FF"
            shimmerDuration="3s"
            shimmerSize="0.08em"
            borderRadius="8px"
            background="rgba(12, 16, 23, 0.95)"
            className="fg-preview-demo-button shadow-2xl hover:scale-[1.02] border-[#00f0ff25] mt-3"
            onClick={onDemo}
            disabled={waiting || isRolling}
          >
            <span className="flex items-center gap-2 text-[13px] font-medium text-slate-100 group-hover:text-white">
              <Play size={14} className="text-[#00F0FF]" />
              <span>See the investigation</span>
              <ArrowRight size={15} className="text-slate-300 transition-transform group-hover:text-[#00F0FF] group-hover:translate-x-0.5" />
            </span>
          </ShimmerButton>
          <span className="fg-preview-disclaimer">Interactive demo · simulated data, no API call</span>
        </div>
        <ShineBorder
          borderRadius={10}
          borderWidth={1.5}
          duration={8}
          color={["#00F0FF", "#A07CFE", "#FF7849"]}
          className="fg-sample-window"
        >
          <div className="fg-sample-title">
            <span>
              <span className="fg-window-dots"><i /><i /><i /></span>
              <span className="fg-mono">{activeScenario.repo}</span>
            </span>
          </div>
          <div className="fg-sample-flow">
            <span className={`fg-sample-node ${activeStage === 0 ? 'fg-sample-node-active' : ''}`}>
              <GitHubIcon size={19} />
              <small>Repository</small>
            </span>
            <ChevronRight size={16} className={`fg-sample-chevron ${activeStage >= 1 ? 'fg-sample-chevron-active' : ''}`} />
            <span className={`fg-sample-node ${activeStage === 1 ? 'fg-sample-node-active' : ''}`}>
              <Layers3 size={19} />
              <small>Repeat runs</small>
            </span>
            <ChevronRight size={16} className={`fg-sample-chevron ${activeStage >= 2 ? 'fg-sample-chevron-active' : ''}`} />
            <span className={`fg-sample-node ${activeStage === 2 ? 'fg-sample-node-active' : ''}`}>
              <Sparkles size={19} />
              <small>Investigate</small>
            </span>
            <ChevronRight size={16} className={`fg-sample-chevron ${activeStage >= 3 ? 'fg-sample-chevron-active' : ''}`} />
            <span className={`fg-sample-node ${activeStage === 3 ? 'fg-sample-node-active' : ''}`}>
              <Braces size={19} />
              <small>Review fix</small>
            </span>
          </div>

          <div className="fg-sample-result">
            <div>
              <span className="fg-sample-test-icon"><CircleDot size={19} /></span>
              <div>
                <span className="fg-mono">{activeScenario.testName}</span>
                <p>{activeScenario.category}</p>
              </div>
            </div>
            <span className={`fg-badge ${activeStage === 3 ? 'fg-sample-passing' : 'fg-sample-flaky'}`}>
              {activeStage === 3 ? 'Fixed · 10/10' : activeScenario.flakyRate}
            </span>
          </div>

          <div className="fg-sample-console" role="region" aria-label="Simulated code execution">
            <div className="fg-sample-console-header">
              <span className="fg-sample-console-status">
                <span className="fg-sample-console-status-dot" />
                <span>{stageData.tag}</span>
              </span>
              <span className="fg-mono">Stage {activeStage + 1} of 4</span>
            </div>
            <div className="fg-sample-cmd">
              <span className="fg-sample-prompt">$</span>
              <span className="fg-mono">{stageData.cmd}</span>
              <span className="fg-cursor-blink" />
            </div>
            {activeStage === 3 && stageData.diffDel && stageData.diffAdd ? (
              <div className="fg-sample-diff">
                <span className="fg-diff-del">{stageData.diffDel}</span>
                <span className="fg-diff-add">{stageData.diffAdd}</span>
              </div>
            ) : (
              <div className="fg-sample-output">
                <span className="fg-mono">{stageData.output}</span>
              </div>
            )}
          </div>

          <div className="fg-sample-runs">
            <span className="fg-mono">Runs</span>
            <div aria-label="Sample test runs">
              {Array.from({ length: 10 }, (_, index) => {
                const executed = activeStage === 0 ? false : index < runProgress;
                const isFail = activeStage !== 3 && activeScenario.failIndices.includes(index);
                return (
                  <span
                    key={index}
                    className={`fg-sample-run-cell ${!executed ? 'fg-sample-run-pending' : isFail ? 'fg-sample-run-fail' : 'fg-sample-run-pass'}`}
                    title={`Run ${index + 1}: ${!executed ? 'queued' : isFail ? 'fail' : 'pass'}`}
                  />
                );
              })}
            </div>
            <span className="fg-mono">
              {activeStage === 0
                ? 'Queued'
                : activeStage === 3
                ? '10 / 10 pass'
                : `${Math.max(0, runProgress - activeScenario.failIndices.filter(i => i < runProgress).length)} / ${runProgress} pass`}
            </span>
          </div>
        </ShineBorder>
      </section>
      <section id="capabilities" className="fg-capabilities" aria-label="FlakeGuard capabilities">
        {[{ icon: ScanLine, number: '01', title: 'Reproduce the failure', body: 'Compare repeated runs to distinguish a consistent regression from an intermittent failure.', foot: 'See sample run results' }, { icon: Radar, number: '02', title: 'Investigate the cause', body: 'Specialist agents examine timing, test ordering, shared state, and environment differences.', foot: 'See the investigation' }, { icon: ShieldCheck, number: '03', title: 'Review the proposed fix', body: 'Inspect the diagnosis and suggested code change before deciding what to apply.', foot: 'Explore the demo' }].map(({ icon: Icon, number, title, body, foot }) => (
          <ShineBorder
            as="article"
            key={number}
            borderRadius={9}
            borderWidth={1.5}
            duration={8}
            color={number === '01' ? ["#00F0FF", "#0070F3", "#A07CFE"] : number === '02' ? ["#A07CFE", "#FE8FB5", "#8A3FFC"] : ["#10B981", "#00F0FF", "#FFBE7B"]}
            className="fg-capability"
          >
            <div className="fg-capability-top"><Icon size={22} /><span className="fg-mono">{number}</span></div>
            <h3>{title}</h3>
            <p>{body}</p>
            <a className="fg-capability-foot" href="#interactive-demo">{foot}<ArrowUpRight size={15} /></a>
          </ShineBorder>
        ))}
      </section>
      <footer className="fg-launch-footer"><span>FlakeGuard</span><span>Test reliability, with evidence.</span><a href="#interactive-demo">View the sample investigation <ArrowUpRight size={13} /></a></footer>
    </div>
  );
}
