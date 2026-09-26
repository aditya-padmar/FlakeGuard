import { useEffect, useRef, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { AlertCircle, ArrowDownToLine, Check, CheckCheck, ChevronRight, Copy, FileCode2, FlaskConical, GitBranch, LoaderCircle, ShieldCheck, ShieldOff, Sparkles, Terminal, X } from 'lucide-react';
import type { WorkspaceData, TestRecord } from './data';

export interface TestDrawerProps {
  test: TestRecord | null;
  mode: WorkspaceData['mode'];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onValidate: (id: string) => void;
}

export function TestDrawer({ test, mode, open, onOpenChange, onValidate }: TestDrawerProps) {
  const [tab, setTab] = useState<'analysis' | 'patch'>('analysis');
  const [notice, setNotice] = useState('');
  const [validating, setValidating] = useState(false);
  const [exported, setExported] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  const reducedMotion = useReducedMotion();
  useEffect(() => {
    setTab('analysis'); setNotice(''); setValidating(false); setExported(false);
    return () => { if (timer.current !== null) { clearTimeout(timer.current); timer.current = null; } };
  }, [test?.id, open]);
  const copy = async (text: string, label: string) => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(text);
      setNotice(`${label} copied to clipboard.`);
    } catch { setNotice(`Could not copy ${label.toLowerCase()}. Clipboard access may be unavailable. Select the text manually or download the patch.`); }
  };
  if (!test) return null;
  const slug = test.id.replace(/[^a-zA-Z0-9_-]/g, '-').slice(0, 50) || 'test';
  const filename = `flakeguard-${slug}.patch`;
  const instructions = `# In a clean checkout of the analyzed repository:\ngit switch -c flakeguard/fix-${slug}\n# Put the downloaded ${filename} in this checkout.\ngit apply --check ${filename}\ngit apply ${filename}\n# Run the relevant tests, then review and commit the changes.\n# Nothing has been pushed; create a PR manually after review.`;
  const downloadPatch = () => {
    if (!test.diff) return;
    let url: string | null = null;
    try {
      url = URL.createObjectURL(new Blob([test.diff.endsWith('\n') ? test.diff : `${test.diff}\n`], { type: 'text/x-diff;charset=utf-8' }));
      const link = document.createElement('a');
      link.href = url; link.download = filename;
      document.body.appendChild(link); link.click(); link.remove();
      setExported(true); setNotice('Patch download requested. Follow the local instructions below; no branch was created or pushed.');
    } catch { setNotice('Could not export the patch. Try copying the patch instead.'); }
    finally { if (url) URL.revokeObjectURL(url); }
  };
  const simulateValidation = () => {
    if (mode !== 'demo' || !test.diff || validating || test.fixStatus === 'validated') return;
    setValidating(true); setNotice('Simulating validation for this demo. No tests are being executed.');
    const id = test.id;
    timer.current = setTimeout(() => {
      timer.current = null; setValidating(false);
      onValidate(id); setNotice('10/10 PASS — demo simulation complete. This is not a real test validation.');
    }, 1400);
  };
  const passed = test.history.filter(outcome => outcome === 'pass').length;
  const failed = test.history.filter(outcome => outcome === 'fail').length;
  const confidence = test.confidence === null ? null : Math.min(100, Math.max(0, test.confidence));
  return <Dialog.Root open={open} onOpenChange={onOpenChange}>
    <AnimatePresence>
      {open && <Dialog.Portal forceMount>
        <Dialog.Overlay asChild forceMount><motion.div className="fg-drawer-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: reducedMotion ? 0 : .18 }} /></Dialog.Overlay>
        <Dialog.Content asChild forceMount onOpenAutoFocus={() => { opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null; }} onCloseAutoFocus={event => { if (opener.current?.isConnected) { event.preventDefault(); opener.current.focus(); } }}>
          <motion.aside className="fg-test-drawer" initial={reducedMotion ? false : { x: 60, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 60, opacity: 0 }} transition={{ duration: reducedMotion ? 0 : .22, ease: 'easeOut' }}>
            <div className="fg-drawer-topline"><span><FlaskConical size={14} /> Test intelligence <ChevronRight size={12} /><span>Details</span></span><Dialog.Close className="fg-drawer-close" aria-label="Close test details"><X size={19} /></Dialog.Close></div>
            <header className="fg-drawer-header"><div className="fg-drawer-context"><span className="fg-badge">{test.cause}</span>{mode === 'demo' && <span className="fg-demo-label">DEMO DATA</span>}</div><Dialog.Title>{test.name}</Dialog.Title><Dialog.Description className="fg-mono">{test.path || 'File path not reported'}</Dialog.Description></header>
            <div className="fg-drawer-stats"><div><span>Flake rate</span><strong className="fg-stat-orange">{test.totalRuns === 0 ? 'Not run' : `${test.rate.toFixed(1).replace(/\.0$/, '')}%`}</strong></div><div><span>Passed</span><strong className="fg-stat-green">{test.passCount}</strong></div><div><span>Failed</span><strong>{test.failCount}</strong></div><div><span>Total runs</span><strong>{test.totalRuns}</strong></div></div>
            <div className="fg-drawer-tabs" role="group" aria-label="Detail view"><button aria-pressed={tab === 'analysis'} className={tab === 'analysis' ? 'fg-drawer-tab-active' : ''} onClick={() => setTab('analysis')}><Sparkles size={14} /> Analysis</button><button aria-pressed={tab === 'patch'} className={tab === 'patch' ? 'fg-drawer-tab-active' : ''} onClick={() => setTab('patch')}><FileCode2 size={14} /> Suggested patch{test.diff && <i />}</button></div>
            <div className="fg-drawer-body">
              {tab === 'analysis' ? <>
                <section className="fg-drawer-section"><div className="fg-drawer-section-heading"><h3>Execution evidence</h3><span>{test.history.length ? `${test.history.length} outcomes supplied` : 'Aggregate data only'}</span></div>{test.history.length ? <><div className="fg-execution-matrix" role="img" aria-label={`${passed} passed and ${failed} failed in the supplied history. No timestamps were provided.`}>{test.history.map((outcome, index) => <span key={index} className={`fg-execution-cell fg-execution-${outcome}`} title={`Supplied outcome ${index + 1}: ${outcome}`}>{outcome === 'pass' ? <Check size={12} /> : <X size={12} />}</span>)}</div><div className="fg-execution-caption"><span><i className="fg-history-key-pass" />{passed} passed <i className="fg-history-key-fail" />{failed} failed</span><span>Supplied order · timestamps unavailable</span></div></> : <p className="fg-drawer-empty">Individual execution history was not supplied. Only the reported aggregate counts above are available; an execution sequence cannot be inferred.</p>}</section>
                <section className="fg-ai-analysis"><div className="fg-ai-heading"><span className="fg-ai-icon"><Sparkles size={18} /></span><div><h3>Root cause analysis</h3><span>AI-assisted diagnosis · human review required</span></div></div><p className="fg-ai-reasoning">{test.reasoning || 'No root cause reasoning was supplied for this test.'}</p><div className="fg-confidence-label"><span>Model confidence</span><strong>{confidence === null ? 'Not reported' : `${Number(confidence.toFixed(1))}%`}</strong></div>{confidence !== null && <div className="fg-confidence-track" role="meter" aria-label="Reported model confidence" aria-valuemin={0} aria-valuemax={100} aria-valuenow={confidence}><span style={{ width: `${confidence}%` }} /></div>}<p className="fg-confidence-note">Confidence describes the diagnosis, not a guarantee that the fix is correct.</p></section>
                <section className="fg-drawer-section"><div className="fg-drawer-section-heading"><h3>Supporting evidence</h3><span>{test.evidence.length} observations</span></div>{test.evidence.length ? <ul className="fg-evidence-list">{test.evidence.map((evidence, index) => <li key={index}><span className="fg-evidence-index">{String(index + 1).padStart(2, '0')}</span><p>{evidence}</p></li>)}</ul> : <p className="fg-drawer-empty">No supporting evidence was supplied.</p>}</section>
                {test.quarantine && <section className="fg-quarantine-detail"><ShieldOff size={17} /><div><h3>Quarantine entry</h3><p className="fg-mono">{test.quarantine}</p><span>Reported by the analysis. This view does not change exclusions.</span></div></section>}
                {test.diff && <button className="fg-drawer-patch-link" onClick={() => setTab('patch')}><span><FileCode2 size={16} /><span><strong>A suggested patch is available</strong><small>Inspect the change before you apply it.</small></span></span><ChevronRight size={17} /></button>}
              </> : <>
                <section className="fg-drawer-section"><div className="fg-drawer-section-heading"><h3>Suggested change</h3><span className={test.fixStatus === 'validated' ? 'fg-stat-green' : ''}>{test.fixStatus === 'validated' ? mode === 'demo' ? 'Demo validated' : 'Reported validated' : test.diff ? 'Awaiting review' : 'No patch supplied'}</span></div>{test.diff ? <div className="fg-diff-view"><div className="fg-diff-header"><FileCode2 size={13} /><span className="fg-mono">{test.path || 'Suggested patch'}</span><button aria-label="Copy patch" onClick={() => { void copy(test.diff!, 'Patch'); }}><Copy size={13} /></button></div><pre aria-label="Suggested patch diff"><code>{test.diff.split('\n').map((line, index) => <span key={index} className={`fg-diff-line ${line.startsWith('+++') || line.startsWith('---') ? 'fg-diff-file' : line.startsWith('+') ? 'fg-diff-add' : line.startsWith('-') ? 'fg-diff-remove' : line.startsWith('@@') ? 'fg-diff-hunk' : ''}`}><span className="fg-diff-line-number" aria-hidden="true">{index + 1}</span><span>{line || ' '}</span>{'\n'}</span>)}</code></pre></div> : <div className="fg-no-patch"><FileCode2 size={28} /><h3>No patch available</h3><p>This analysis did not provide an inline diff. No change or fix will be fabricated.</p></div>}</section>
                <div className="fg-patch-advisory"><AlertCircle size={16} /><p><strong>Advisory Fix — Review Required (No Auto-Merge)</strong><br />AI-generated changes are advisory. Review the patch and run your tests locally. FlakeGuard does not automatically merge changes, create a remote branch, or open a pull request.</p></div>
                <div className="fg-patch-actions"><button className="fg-button" disabled={!test.diff} onClick={() => { if (test.diff) void copy(test.diff, 'Patch'); }}><Copy size={14} /> Copy patch</button><button className="fg-button fg-button-primary" disabled={!test.diff} onClick={downloadPatch}><ArrowDownToLine size={14} /> Export PR branch <span className="fg-local-chip">LOCAL</span></button></div>
                <p className="fg-export-explanation">Exports a .patch download only. The commands below prepare a local branch; nothing is pushed.</p>
                {test.diff && <section className={`fg-local-instructions ${exported ? 'fg-local-exported' : ''}`}><div><h3><Terminal size={14} />{exported ? 'Patch exported · next steps' : 'Local branch instructions'}</h3><button aria-label="Copy local git instructions" onClick={() => { void copy(instructions, 'Instructions'); }}><Copy size={13} /></button></div><pre><code>{instructions}</code></pre></section>}
                <section className="fg-validation-card"><div className="fg-validation-title"><ShieldCheck size={17} /><h3>{mode === 'demo' ? 'Demo validation' : 'Validate before merging'}</h3></div><p>{mode === 'demo' ? 'Preview the validation state with a simulation. This does not execute tests or verify this patch.' : 'Live validation is not supported in this workspace. Apply the patch in a local checkout and run the relevant test suite yourself.'}</p><button className="fg-button" disabled={mode !== 'demo' || !test.diff || validating || test.fixStatus === 'validated'} onClick={simulateValidation}>{validating ? <LoaderCircle className="fg-spinning" size={14} /> : test.fixStatus === 'validated' ? <CheckCheck size={14} /> : <FlaskConical size={14} />}{validating ? 'Simulating…' : mode !== 'demo' ? 'Live validation unavailable' : test.fixStatus === 'validated' ? 'Demo validation complete' : 'Simulate validation (demo)'}</button></section>
              </>}
              {notice && <div className="fg-drawer-notice" role="status" aria-live="polite">{notice}</div>}
            </div>
            <footer className="fg-drawer-footer"><span><GitBranch size={12} /> No repository changes are made here</span><Dialog.Close className="fg-button">Done</Dialog.Close></footer>
          </motion.aside>
        </Dialog.Content>
      </Dialog.Portal>}
    </AnimatePresence>
  </Dialog.Root>;
}

export default TestDrawer;
