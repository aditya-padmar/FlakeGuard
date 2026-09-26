import { useId, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Activity, ArrowLeft, ArrowRight, Check, CircleDot } from 'lucide-react';
import type { TestRecord } from './data';

type Cause = TestRecord['cause'];
export interface CauseCount { name: Cause; color: string; className: string; count: number }
const percent = (value: number) => `${value.toFixed(1).replace(/\.0$/, '')}%`;
const stats = (test: TestRecord) => {
  const total = test.passCount + test.failCount;
  return `${test.name}: ${test.passCount.toLocaleString()} passed, ${test.failCount.toLocaleString()} failed, ${total.toLocaleString()} recorded outcomes; ${percent(test.passCount / total * 100)} passed.${test.totalRuns !== total ? ` Reported total runs: ${test.totalRuns.toLocaleString()}.` : ''}`;
};

export function ReliabilityChart({ tests }: { tests: TestRecord[] }) {
  const reducedMotion = useReducedMotion();
  const id = useId();
  const [page, setPage] = useState(0);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [pinnedId, setPinnedId] = useState<string | null>(null);
  const observed = tests.filter(test => test.passCount + test.failCount > 0);
  const total = observed.reduce((sum, test) => sum + test.passCount + test.failCount, 0);
  const passed = observed.reduce((sum, test) => sum + test.passCount, 0);
  // Keep generous touch targets even when a live repository supplies many tests.
  const pages = Math.ceil(observed.length / 8);
  const currentPage = Math.min(page, Math.max(0, pages - 1));
  const visible = observed.slice(currentPage * 8, currentPage * 8 + 8);
  const active = visible.find(test => test.id === (activeId ?? pinnedId));
  const points = visible.map((test, index) => ({ x: (index + .5) * 800 / visible.length, y: 105 - test.passCount / (test.passCount + test.failCount) * 100 }));
  const line = points.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ');
  const area = points.length > 1 ? `${line} L ${points[points.length - 1].x} 105 L ${points[0].x} 105 Z` : '';
  const changePage = (next: number) => { setPage(next); setActiveId(null); setPinnedId(null); };
  return <section className="fg-panel fg-reliability-panel" aria-labelledby={`${id}-title`}>
    <div className="fg-panel-heading"><div><h2 id={`${id}-title`}>Execution reliability</h2><p>Observed pass rate across analyzed tests</p></div><span className="fg-chart-legend"><i /> Passed</span></div>
    <div className="fg-chart-summary"><strong>{total ? percent(passed / total * 100) : '—'}</strong><span>{total ? `${passed.toLocaleString()} of ${total.toLocaleString()} recorded outcomes passed` : 'No execution outcomes available'}</span></div>
    {observed.length ? <>
      <div className="fg-reliability-plot" role="group" aria-label="Per-test pass rates, in inventory order" onKeyDown={event => { if (event.key === 'Escape') { setActiveId(null); setPinnedId(null); } }}>
        <div className="fg-chart-axis" aria-hidden="true">{[100, 75, 50, 25, 0].map(value => <span key={value}>{value}%</span>)}</div>
        <div className="fg-chart-bars fg-chart-line-plot">
          <svg className="fg-chart-line-canvas" viewBox="0 0 800 110" preserveAspectRatio="none" aria-hidden="true">
            <defs><linearGradient id={`${id}-area`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#00f0ff" stopOpacity=".2" /><stop offset="100%" stopColor="#00f0ff" stopOpacity="0" /></linearGradient></defs>
            {area && <path d={area} fill={`url(#${id}-area)`} />}
            <motion.path d={line} fill="none" stroke="#00f0ff" strokeWidth="2" vectorEffect="non-scaling-stroke" strokeLinejoin="round" initial={reducedMotion !== false ? false : { pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: reducedMotion !== false ? 0 : .7, ease: 'easeOut' }} />
          </svg>
          {visible.map((test, index) => {
            const rate = test.passCount / (test.passCount + test.failCount) * 100;
            const selected = active?.id === test.id;
            return <button type="button" key={test.id} className={`fg-chart-bar ${selected ? 'fg-chart-bar-active' : ''}`} aria-label={stats(test)} aria-pressed={pinnedId === test.id} aria-describedby={selected ? `${id}-tooltip` : undefined}
              onPointerEnter={event => { if (event.pointerType !== 'touch') setActiveId(test.id); }}
              onPointerLeave={event => { if (document.activeElement !== event.currentTarget) setActiveId(null); }}
              onFocus={() => setActiveId(test.id)} onBlur={() => setActiveId(null)}
              onClick={() => { setPinnedId(pinnedId === test.id ? null : test.id); setActiveId(test.id); }}
              onKeyDown={event => {
                const next = event.key === 'ArrowRight' ? index + 1 : event.key === 'ArrowLeft' ? index - 1 : event.key === 'Home' ? 0 : event.key === 'End' ? visible.length - 1 : null;
                if (next !== null) { event.preventDefault(); event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('button')[Math.max(0, Math.min(visible.length - 1, next))]?.focus(); }
              }}>
              <span className="fg-chart-point-track" aria-hidden="true"><i className="fg-chart-point" style={{ top: `${(105 - rate) / 110 * 100}%` }} /></span><span aria-hidden="true">{currentPage * 8 + index + 1}</span>
            </button>;
          })}
        </div>
      </div>
      <div className={`fg-chart-tooltip ${active ? 'fg-chart-tooltip-visible' : ''}`} id={`${id}-tooltip`} role={active ? 'tooltip' : undefined}>
        {active ? <><strong>{active.name}</strong><span><b>{percent(active.passCount / (active.passCount + active.failCount) * 100)}</b> passed · {active.passCount.toLocaleString()} pass / {active.failCount.toLocaleString()} fail / {(active.passCount + active.failCount).toLocaleString()} total outcomes{active.totalRuns !== active.passCount + active.failCount ? ` · ${active.totalRuns.toLocaleString()} reported total runs` : ''}</span></> : <span>Hover, focus or tap a point for exact test outcomes.</span>}
      </div>
      {pages > 1 && <nav className="fg-chart-pagination" aria-label="Reliability chart pages"><button type="button" aria-label="Previous tests" disabled={currentPage === 0} onClick={() => changePage(currentPage - 1)}><ArrowLeft size={14} /></button><span aria-live="polite">Tests {currentPage * 8 + 1}–{currentPage * 8 + visible.length} of {observed.length}</span><button type="button" aria-label="Next tests" disabled={currentPage === pages - 1} onClick={() => changePage(currentPage + 1)}><ArrowRight size={14} /></button></nav>}
    </> : <div className="fg-chart-empty"><Activity size={30} /><span>Run an analysis to see execution reliability.</span></div>}
    <div className="fg-chart-footnote"><CircleDot size={12} /><span>Per-test observations · inventory order, not a time series{tests.length > observed.length ? ` · ${tests.length - observed.length} without recorded outcomes omitted` : ''}</span></div>
  </section>;
}

export function CauseChart({ counts, cause, onSelect }: { counts: CauseCount[]; cause: Cause | 'all'; onSelect: (cause: Cause | 'all') => void }) {
  const id = useId();
  const [hover, setHover] = useState<Cause | null>(null);
  const [focus, setFocus] = useState<Cause | null>(null);
  const total = counts.reduce((sum, item) => sum + item.count, 0);
  const active = counts.find(item => item.name === (hover ?? focus ?? cause));
  const select = (name: Cause) => onSelect(cause === name ? 'all' : name);
  let offset = 0;
  const slices = counts.filter(item => item.count > 0).map(item => {
    const start = offset;
    offset += item.count / total * 100;
    const length = item.count / total * 100;
    const point = (fraction: number) => `${100 + 76 * Math.cos(fraction * Math.PI / 50)} ${100 + 76 * Math.sin(fraction * Math.PI / 50)}`;
    // Real arc geometry, not dashed full circles: each slice owns only its hit area.
    const path = length === 100
      ? 'M 176 100 A 76 76 0 1 1 24 100 A 76 76 0 1 1 176 100'
      : `M ${point(start)} A 76 76 0 ${length > 50 ? 1 : 0} 1 ${point(start + length)}`;
    return { ...item, length, path };
  });
  return <section className="fg-panel fg-causes-panel" aria-labelledby={`${id}-title`}>
    <div className="fg-panel-heading"><div><h2 id={`${id}-title`}>Root causes</h2><p>Why these tests fail intermittently</p></div><span className="fg-badge">{total} tests</span></div>
    <div className="fg-donut-wrap">
      <svg className="fg-cause-donut" viewBox="0 0 200 200" role="group" aria-label="Root cause distribution. Select a segment to filter tests.">
        <circle cx="100" cy="100" r="76" fill="none" stroke="#ffffff0a" strokeWidth="22" />
        {slices.map(item => <path key={item.name} className="fg-donut-slice" d={item.path} fill="none" stroke={item.color} strokeWidth={active?.name === item.name ? 27 : 22} transform="rotate(-90 100 100)" tabIndex={0} role="button" aria-label={`${item.name}: ${item.count} of ${total} tests, ${percent(item.length)}. Filter inventory.`} aria-pressed={cause === item.name}
          onPointerEnter={event => { if (event.pointerType !== 'touch') setHover(item.name); }} onPointerLeave={() => setHover(null)} onFocus={() => setFocus(item.name)} onBlur={() => setFocus(null)} onClick={() => select(item.name)} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(item.name); } }} />)}
      </svg>
      <div className="fg-donut-center" aria-hidden="true"><strong>{active ? percent(total ? active.count / total * 100 : 0) : total.toLocaleString()}</strong><span>{active?.name ?? (total ? 'Analyzed tests' : 'No analyzed tests')}</span>{active && <small>{active.count} of {total} tests</small>}</div>
    </div>
    <div className="fg-cause-list">{counts.map(item => <button type="button" key={item.name} className={`fg-cause-row ${item.className} ${cause === item.name ? 'fg-cause-active' : ''}`} aria-pressed={cause === item.name} onPointerEnter={event => { if (event.pointerType !== 'touch') setHover(item.name); }} onPointerLeave={() => setHover(null)} onFocus={() => setFocus(item.name)} onBlur={() => setFocus(null)} onClick={() => select(item.name)}><span><i style={{ background: item.color }} />{item.name}</span><span className="fg-cause-count">{item.count}<span>{total ? percent(item.count / total * 100) : '0%'}</span>{cause === item.name ? <Check size={12} /> : <ArrowRight size={12} />}</span></button>)}</div>
    <p className="fg-panel-hint">Select a cause to focus the inventory below.</p>
  </section>;
}
