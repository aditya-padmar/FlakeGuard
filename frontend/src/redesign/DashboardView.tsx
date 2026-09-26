import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Activity, ArrowDownToLine, ArrowRight, ChevronDown, CircleDot, FileCode2, GitBranch, GitCommitHorizontal, ListFilter, Search, ShieldCheck, ShieldOff, Sparkles, TestTubeDiagonal } from 'lucide-react';
import type { WorkspaceData, TestRecord } from './data';
import { TestDrawer } from './TestDrawer';
import { AnimatedNumber } from './AnimatedNumber';
import { CauseChart, ReliabilityChart } from './Charts';
import './dashboard.css';

export interface DashboardViewProps {
  data: WorkspaceData;
  view: 'overview' | 'inventory' | 'quarantine' | 'fixes';
  onRerun: () => void;
  onValidate: (id: string) => void;
}

type Cause = TestRecord['cause'];
const causes: { name: Cause; color: string; className: string }[] = [
  { name: 'Timing / race', color: '#10b981', className: 'fg-cause-timing' },
  { name: 'Order dependency', color: '#a78bfa', className: 'fg-cause-order' },
  { name: 'Data leakage', color: '#ff7849', className: 'fg-cause-data' },
  { name: 'Environment', color: '#66a1ff', className: 'fg-cause-environment' },
  { name: 'Unclassified', color: '#667184', className: 'fg-cause-unknown' },
];
const titles = { overview: 'Trust overview', inventory: 'Test inventory', quarantine: 'Quarantine audit', fixes: 'Fix workspace' };
const descriptions = {
  overview: 'Test health, root causes, and the fixes worth reviewing.',
  inventory: 'Search test results and investigate inconsistent runs.',
  quarantine: 'Review suppressed tests and their available fixes.',
  fixes: 'Review suggested changes before applying them to your repository.',
};
const percent = (value: number) => `${value.toFixed(1).replace(/\.0$/, '')}%`;

function HistoryBars({ test }: { test: TestRecord }) {
  if (!test.history.length) return <span className="fg-history-unavailable">No run history</span>;
  const runs = test.history.slice(-28);
  return <div className="fg-history" role="img" aria-label={`${test.history.length} recorded outcomes: ${test.history.filter(run => run === 'pass').length} passed, ${test.history.filter(run => run === 'fail').length} failed. Showing ${runs.length} supplied outcomes, not a timestamped timeline.`}>
    {runs.map((run, index) => <span key={index} className={`fg-history-tick fg-history-${run}`} />)}
  </div>;
}

export function DashboardView({ data, view, onRerun, onValidate }: DashboardViewProps) {
  const [search, setSearch] = useState('');
  const [cause, setCause] = useState<Cause | 'all'>('all');
  const [status, setStatus] = useState('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const reducedMotion = useReducedMotion();
  const searchRef = useRef<HTMLInputElement>(null);
  useEffect(() => { setSearch(''); setCause('all'); setStatus('all'); setSelectedId(null); }, [view]);
  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k' && !selectedId) {
        event.preventDefault(); searchRef.current?.focus();
      }
    };
    window.addEventListener('keydown', focusSearch);
    return () => window.removeEventListener('keydown', focusSearch);
  }, [selectedId]);
  const selectedTest = data.tests.find(test => test.id === selectedId) ?? null;
  const quarantined = data.tests.filter(test => Boolean(test.quarantine));
  const diagnosed = data.tests.filter(test => test.cause !== 'Unclassified');
  const validated = data.tests.filter(test => test.fixStatus === 'validated');
  const flaky = data.tests.filter(test => test.rate > 0);
  const counts = causes.map(item => ({ ...item, count: data.tests.filter(test => test.cause === item.name).length }));
  const filtered = useMemo(() => data.tests.filter(test => {
    if (view === 'quarantine' && !test.quarantine) return false;
    if (view === 'fixes' && !test.diff && test.fixStatus === 'none') return false;
    if (cause !== 'all' && test.cause !== cause) return false;
    if (status === 'quarantined' && !test.quarantine) return false;
    if (status === 'proposed' && test.fixStatus !== 'proposed') return false;
    if (status === 'validated' && test.fixStatus !== 'validated') return false;
    if (status === 'unresolved' && test.fixStatus !== 'none') return false;
    if (status === 'flaky' && test.rate <= 0) return false;
    if (status === 'diagnosed' && test.cause === 'Unclassified') return false;
    return `${test.name} ${test.path} ${test.cause}`.toLowerCase().includes(search.toLowerCase().trim());
  }), [data.tests, view, cause, status, search]);
  const metricFilters = ['all', 'flaky', 'quarantined', 'diagnosed', 'validated'];
  const chooseStatus = (next: string) => { setStatus(next); setCause('all'); setSearch(''); };
  const scopedTests = data.tests.filter(test => view === 'quarantine' ? Boolean(test.quarantine) : view === 'fixes' ? test.fixStatus !== 'none' || Boolean(test.diff) : true);
  const quickFilters = [
    { label: 'All results', value: 'all', count: scopedTests.length },
    { label: 'Proposed fixes', value: 'proposed', count: scopedTests.filter(test => test.fixStatus === 'proposed').length },
    { label: 'Validated', value: 'validated', count: scopedTests.filter(test => test.fixStatus === 'validated').length },
  ];
  const metrics = [
    { label: 'Total tests', value: data.totalTests, note: data.totalTests === null ? 'Suite size not reported' : 'Reported suite inventory', icon: TestTubeDiagonal, tone: 'neutral' },
    { label: 'Flaky signals', value: flaky.length, note: `${data.tests.length} tests analyzed`, icon: Activity, tone: 'orange' },
    { label: 'Quarantined', value: quarantined.length, note: 'Matched analyzed tests', icon: ShieldOff, tone: 'purple' },
    { label: 'Bob AI diagnosed', value: diagnosed.length, denominator: data.tests.length, note: 'Evidence-backed root causes', icon: FileCode2, tone: 'cyan' },
    { label: data.mode === 'demo' ? 'Demo validated' : 'Validated fixes', value: validated.length, note: data.mode === 'demo' ? 'Simulated results only' : 'Reported validation status', icon: ShieldCheck, tone: 'green' },
  ];
  return <motion.div className="fg-dashboard" initial={reducedMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .35 }}>
    <header className="fg-dashboard-header">
      <div><h1>{titles[view]}</h1><p>{descriptions[view]}</p></div>
      <button className="fg-button fg-button-primary fg-analyze-button" onClick={onRerun}><Activity size={15} /> {data.mode === 'demo' ? 'Run demo again' : 'Run analysis'} <ArrowRight size={14} /></button>
    </header>
    <div className="fg-repository-strip">
      <div className="fg-repository-meta"><span className="fg-repository-name"><span className="fg-repo-mark">/</span>{data.repository || 'No repository selected'}</span><span><GitBranch size={13} />{data.branch || 'Branch not reported'}</span><span className="fg-mono"><GitCommitHorizontal size={14} />{data.commit ? data.commit.slice(0, 8) : 'Commit not reported'}</span>{data.framework && <span className="fg-framework">{data.framework}</span>}</div>
      <span className={`fg-dashboard-data-mode ${data.mode === 'demo' ? 'fg-data-demo' : ''}`}><i />{data.mode === 'demo' ? 'Demo dataset' : 'Repository analysis'}</span>
    </div>
    <section className="fg-metric-grid" aria-label="Workspace metrics">
      {metrics.map(({ label, value, denominator, note, icon: Icon, tone }, index) => <motion.button type="button" key={label} className={`fg-panel fg-spotlight fg-metric-card fg-metric-${tone}`} aria-label={`Filter inventory: ${label}, ${value === null ? 'not reported' : value.toLocaleString()}${denominator === undefined ? '' : ` of ${denominator.toLocaleString()}`}`} aria-pressed={status === metricFilters[index]} onClick={() => chooseStatus(metricFilters[index])} initial={reducedMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: index * .025, duration: .18 }}><div className="fg-metric-label">{label}<span className={tone === 'orange' && flaky.length > 0 ? 'fg-ember-badge' : undefined}><Icon size={15} /></span></div><strong><AnimatedNumber value={value} denominator={denominator} /></strong><span>{note}</span></motion.button>)}
    </section>
    {view === 'overview' && <div className="fg-insights-grid"><ReliabilityChart tests={data.tests} /><CauseChart counts={counts} cause={cause} onSelect={setCause} /></div>}
    {view === 'quarantine' && <section className="fg-panel fg-audit-panel" aria-labelledby="fg-audit-title"><div className="fg-panel-heading"><div><h2 id="fg-audit-title"><ShieldOff size={17} /> Exclusion audit</h2><p>Reported source counts are not necessarily unique tests.</p></div><span className="fg-badge">{data.auditedCount} audited exclusions</span></div><div className="fg-audit-grid">{data.auditSources.length ? data.auditSources.map((source, index) => <div key={`${source.source}-${index}`} className="fg-audit-source"><span className="fg-mono">{source.source}</span><strong>{source.count === null ? '—' : source.count}</strong><small>{source.count === null ? 'Count not reported' : 'Reported exclusions'}</small></div>) : <p className="fg-empty-audit">No quarantine source audit was supplied by this analysis.</p>}</div><div className="fg-audit-note"><ShieldCheck size={14} /><span>{quarantined.length} analyzed tests matched a quarantine entry. Audit totals can include tests outside this analysis.</span></div></section>}
    {view === 'fixes' && <div className="fg-fix-notice"><Sparkles size={19} /><div><strong>AI proposes. You stay in control.</strong><p>Patches are advisory. Review each diff and export locally; no automatic merge or remote branch creation.</p></div></div>}
    <section className="fg-panel fg-inventory-panel" aria-labelledby="fg-inventory-title">
      <div className="fg-panel-heading fg-inventory-heading"><div className="fg-inventory-title"><h2 id="fg-inventory-title">{view === 'quarantine' ? 'Quarantined tests' : view === 'fixes' ? 'Proposed & validated fixes' : 'Test inventory'}</h2><span className="fg-count-badge">{filtered.length}</span></div><span className="fg-inventory-note"><span className="fg-history-key-pass" /> Pass <span className="fg-history-key-fail" /> Fail</span></div>
      <div className="fg-inventory-tabs" role="group" aria-label="Quick inventory filters">{quickFilters.map(filter => <button type="button" className="fg-inventory-tab" key={filter.value} aria-pressed={status === filter.value} onClick={() => chooseStatus(filter.value)}><span>{filter.label}</span><span>{filter.count}</span>{status === filter.value && <motion.span className="fg-tab-indicator" layoutId="inventory-filter-underline" transition={reducedMotion ? { duration: 0 } : { type: 'spring', stiffness: 500, damping: 40 }} />}</button>)}</div>
      <div className="fg-inventory-toolbar"><label className="fg-search"><Search size={15} /><input ref={searchRef} aria-keyshortcuts="Control+k Meta+k" aria-label="Search tests by name or path" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search tests or file paths…" /><kbd aria-hidden="true">⌘ K</kbd></label><div className="fg-filter-controls"><div className="fg-select-wrap"><ListFilter size={13} /><select aria-label="Filter by root cause" value={cause} onChange={event => setCause(event.target.value as Cause | 'all')}><option value="all">All causes</option>{causes.map(item => <option key={item.name}>{item.name}</option>)}</select><ChevronDown size={12} /></div><div className="fg-select-wrap"><CircleDot size={13} /><select aria-label="Filter by status" value={status} onChange={event => setStatus(event.target.value)}><option value="all">All statuses</option><option value="flaky">Flaky tests</option><option value="diagnosed">Diagnosed</option><option value="quarantined">Quarantined</option><option value="proposed">Fix proposed</option><option value="validated">{data.mode === 'demo' ? 'Demo validated' : 'Validated'}</option><option value="unresolved">No fix</option></select><ChevronDown size={12} /></div></div></div>
      <div className="fg-table-scroll" tabIndex={0} aria-label="Test inventory, scroll horizontally on narrow screens"><table className="fg-test-table"><thead><tr><th scope="col">Test name</th><th scope="col">Root cause</th><th scope="col">Flake rate</th><th scope="col">Recorded outcomes</th><th scope="col">Status</th><th scope="col"><span className="fg-dashboard-sr-only">Open details</span></th></tr></thead><tbody>{filtered.map(test => <tr key={test.id}><td><button className="fg-test-name-button" onClick={() => setSelectedId(test.id)}><span className={`fg-test-status-dot ${test.totalRuns === 0 ? 'fg-test-unrun' : test.rate === 0 ? 'fg-test-stable' : ''}`} /><span><strong>{test.name}</strong><small className="fg-mono">{test.path || 'Path not reported'}</small></span></button></td><td><span className={`fg-cause-tag ${causes.find(item => item.name === test.cause)?.className ?? ''}`}><i />{test.cause}</span></td><td><div className="fg-rate-cell"><strong className={test.rate >= 30 ? 'fg-rate-high' : ''}>{test.totalRuns === 0 ? 'Not run' : percent(test.rate)}</strong>{test.totalRuns > 0 && <span><i style={{ width: `${Math.min(100, Math.max(0, test.rate))}%` }} /></span>}</div></td><td><HistoryBars test={test} /></td><td>{test.quarantine && <span className="fg-test-badge fg-test-badge-quarantine"><ShieldOff size={11} />Quarantined</span>}{test.fixStatus === 'validated' ? <span className="fg-test-badge fg-test-badge-success"><ShieldCheck size={11} />{data.mode === 'demo' ? 'Demo validated' : 'Validated'}</span> : test.fixStatus === 'proposed' ? <span className="fg-test-badge fg-test-badge-fix"><Sparkles size={11} />Fix proposed</span> : <span className="fg-test-badge fg-test-badge-open"><CircleDot size={11} />Needs review</span>}</td><td><button className="fg-row-open" aria-label={`Open details for ${test.name}`} onClick={() => setSelectedId(test.id)}><ArrowRight size={15} /></button></td></tr>)}</tbody></table></div>
      {!filtered.length && <div className="fg-inventory-empty"><Search size={25} /><h3>{search || cause !== 'all' || status !== 'all' ? 'No matching tests' : 'Nothing to review here'}</h3><p>{search || cause !== 'all' || status !== 'all' ? 'Try a different search or clear your filters.' : view === 'quarantine' ? 'No analyzed tests have a reported quarantine entry.' : view === 'fixes' ? 'No fixes were supplied for this analysis.' : 'Start an analysis to build your test inventory.'}</p>{(search || cause !== 'all' || status !== 'all') && <button className="fg-button" onClick={() => { setSearch(''); setCause('all'); setStatus('all'); }}>Clear filters</button>}</div>}
      <div className="fg-table-footer"><span>Showing {filtered.length} of {data.tests.length} analyzed tests</span><span><ArrowDownToLine size={12} /> Open a test to inspect evidence & patches</span></div>
    </section>
    <TestDrawer test={selectedTest} mode={data.mode} open={Boolean(selectedTest)} onOpenChange={open => { if (!open) setSelectedId(null); }} onValidate={onValidate} />
  </motion.div>;
}

export default DashboardView;
