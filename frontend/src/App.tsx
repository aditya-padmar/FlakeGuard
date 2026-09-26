import { Suspense, lazy, useCallback, useEffect, useRef, useState } from 'react';
import { BrowserRouter, Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence, MotionConfig, motion } from 'framer-motion';
import { Activity, ArrowLeft, ArrowUpRight, Braces, ChevronRight, CircleHelp, Command, FlaskConical, GitBranch, LayoutDashboard, LogOut, Menu, Plus, ShieldOff, X } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WorkspaceProvider, useWorkspace } from './redesign/WorkspaceContext';
import { adaptAnalysis } from './redesign/data';
import AmbientBackground from './redesign/AmbientBackground';
import SourcesPage from './redesign/SourcesPage';
import './redesign/experience.css';
import './redesign/dashboard.css';

const Launchpad = lazy(() => import('./redesign/Launchpad'));
const DashboardView = lazy(() => import('./redesign/DashboardView'));
const PipelineView = lazy(() => import('./redesign/PipelineView'));
const RemediationTools = lazy(() => import('./pages/RemediationPage'));
const AuditTools = lazy(() => import('./pages/AuditPage'));
const RepositoryIngestion = lazy(() => import('./components/RepositoryIngestion'));

function Brand() {
  return (
    <Link className="fg-brand" to="/" aria-label="FlakeGuard launchpad">
      <span className="fg-brand-mark">
        <img src="/flakeguard-mark.png" alt="FlakeGuard logo" className="fg-brand-img" />
      </span>
      <span className="fg-brand-name">FlakeGuard</span>
    </Link>
  );
}

function Shell() {
  const { data, process, error, startDemo, startLive, cancel, validateDemo } = useWorkspace();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const navigationTrigger = useRef<HTMLButtonElement>(null);
  const completedProcess = useRef(false);
  useEffect(() => {
    if (!menuOpen) return;
    const sidebar = sidebarRef.current;
    const content = contentRef.current;
    const trigger = navigationTrigger.current;
    const previousOverflow = document.body.style.overflow;
    content?.setAttribute('inert', '');
    document.body.style.overflow = 'hidden';
    const focusable = () => Array.from(sidebar?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])') ?? []).filter(element => element.getClientRects().length > 0);
    focusable()[0]?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); setMenuOpen(false); }
      if (event.key === 'Tab') {
        const elements = focusable();
        const first = elements[0]; const last = elements[elements.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    const handleResize = () => { if (window.innerWidth > 900) setMenuOpen(false); };
    window.addEventListener('keydown', handleKey);
    window.addEventListener('resize', handleResize);
    return () => { content?.removeAttribute('inert'); document.body.style.overflow = previousOverflow; window.removeEventListener('keydown', handleKey); window.removeEventListener('resize', handleResize); trigger?.focus(); };
  }, [menuOpen]);
  const isLanding = location.pathname === '/';
  const navItems = [
    { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
    { to: '/inventory', label: 'Test inventory', icon: FlaskConical },
    { to: '/pipeline', label: 'Live pipeline', icon: Activity },
    { to: '/fixes', label: 'Remediation', icon: Braces },
    { to: '/quarantine', label: 'Quarantine audit', icon: ShieldOff },
  ];
  useEffect(() => { setMenuOpen(false); window.scrollTo(0, 0); }, [location.pathname]);
  useEffect(() => {
    if (location.pathname === '/pipeline' && !process && completedProcess.current) navigate(error ? '/' : '/dashboard', { replace: true });
    completedProcess.current = Boolean(process);
  }, [process, error, location.pathname, navigate]);
  const runDemo = useCallback(() => { startDemo(); navigate('/pipeline'); }, [startDemo, navigate]);
  const runLive = useCallback(async (url: string, branch: string) => { const request = startLive(url, branch); navigate('/pipeline'); await request; }, [startLive, navigate]);
  const rerun = useCallback(() => { if (data.mode === 'demo') runDemo(); else navigate('/'); }, [data.mode, runDemo, navigate]);
  const pageName = navItems.find(item => item.to === location.pathname)?.label ?? (location.pathname === '/sources' ? 'Repository sources' : location.pathname.startsWith('/tools') ? 'Developer tools' : 'Workspace');

  if (location.pathname === '/login' || location.pathname === '/signup') return <Navigate to="/" replace />;

  return <div className={isLanding ? 'fg-app fg-public' : 'fg-app'}>
    <a className="fg-skip-link" href="#main-content">Skip to content</a>
    {!isLanding && <>
      {menuOpen && <button className="fg-sidebar-backdrop" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
      <aside ref={sidebarRef} role={menuOpen ? 'dialog' : undefined} aria-modal={menuOpen || undefined} aria-label="Workspace sidebar" className={`fg-sidebar ${menuOpen ? 'is-open' : ''}`}>
        <div className="fg-sidebar-brand"><Brand /><button className="fg-icon-button fg-mobile-only" onClick={() => setMenuOpen(false)} aria-label="Close sidebar"><X size={18} /></button></div>
        <div className="fg-workspace-switch"><span className="fg-workspace-avatar">F</span><div><strong>Engineering</strong><span>Team workspace</span></div></div>
        <span className="fg-nav-label">Workspace</span>
        <nav aria-label="Workspace navigation">{navItems.map(item => <NavLink key={item.to} to={item.to} className={({ isActive }) => `fg-nav-item ${isActive ? 'is-active' : ''}`}><item.icon size={18} /><span>{item.label}</span>{item.to === '/fixes' && <span className="fg-nav-count">{data.tests.filter(test => test.fixStatus !== 'none').length}</span>}{item.to === '/pipeline' && process && <span className="fg-status-dot" />}</NavLink>)}</nav>
        <div className="fg-sidebar-divider" /><span className="fg-nav-label">Developer tools</span>
        <nav aria-label="Developer tools"><NavLink className="fg-nav-item" to="/sources"><GitBranch size={18} />Repository sources</NavLink></nav>
        <div className="fg-sidebar-bottom">
          <button className="fg-nav-item" onClick={() => setHelpOpen(value => !value)} aria-expanded={helpOpen}><CircleHelp size={17} />Workspace guide</button>
          <div className="fg-account"><span className="fg-account-avatar">{user?.avatar ?? 'D'}</span><div><strong>{user?.name ?? 'Demo workspace'}</strong><span>{user ? 'Local demo profile' : 'Developer workspace'}</span></div>{user && <button className="fg-icon-button" aria-label="Sign out" onClick={() => { logout(); navigate('/'); }}><LogOut size={16} /></button>}</div>
        </div>
      </aside>
    </>}
    <div ref={contentRef} className="fg-app-body">
      <header className="fg-topbar">
        {isLanding ? <Brand /> : <div className="fg-breadcrumb"><button ref={navigationTrigger} className="fg-icon-button fg-mobile-only" aria-label="Open navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen(true)}><Menu size={19} /></button><span>Workspace</span><ChevronRight size={13} /><strong>{pageName}</strong></div>}
        {isLanding && <nav className="fg-public-nav" aria-label="Product navigation"><a href="#capabilities">Platform</a><a href="#interactive-demo">How it works</a><Link to="/dashboard">Explore workspace <ArrowUpRight size={12} /></Link></nav>}
        <div className="fg-topbar-actions">
          {!isLanding && (
            <>
              <span className={`fg-data-mode ${data.mode === 'demo' ? 'is-demo' : ''}`}><span className="fg-status-dot" />{process ? 'Analysis running' : data.mode === 'demo' ? 'Sample dataset' : 'API results'}</span>
              <Link to="/" className="fg-button fg-button-small"><Plus size={15} />New analysis</Link>
            </>
          )}
        </div>
      </header>
      <main id="main-content" className={isLanding ? 'fg-public-main' : 'fg-workspace-main'}>
        {helpOpen && !isLanding && <section className="fg-help-panel fg-panel"><div><strong>From flaky to trustworthy.</strong><p>Start an analysis, inspect the evidence, then review a suggested patch. Sample runs and validations are simulations; real repository analysis requires the backend. No fixes are auto-merged.</p></div><button className="fg-icon-button" aria-label="Close workspace guide" onClick={() => setHelpOpen(false)}><X size={16} /></button></section>}
        <AnimatePresence mode="wait"><motion.div key={isLanding ? 'landing' : 'workspace'} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: .22 }}>
          <Suspense fallback={<div className="fg-loading" role="status"><Activity size={22} />Loading workspace…</div>}><Routes>
            <Route path="/" element={<Launchpad onRun={runLive} onDemo={runDemo} error={error} busy={!!process} />} />
            <Route path="/dashboard" element={<DashboardView data={data} view="overview" onRerun={rerun} onValidate={validateDemo} />} />
            <Route path="/inventory" element={<DashboardView data={data} view="inventory" onRerun={rerun} onValidate={validateDemo} />} />
            <Route path="/quarantine" element={<DashboardView data={data} view="quarantine" onRerun={rerun} onValidate={validateDemo} />} />
            <Route path="/audit" element={<Navigate to="/quarantine" replace />} />
            <Route path="/fixes" element={<DashboardView data={data} view="fixes" onRerun={rerun} onValidate={validateDemo} />} />
            <Route path="/remediation" element={<Navigate to="/fixes" replace />} />
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="/signup" element={<Navigate to="/" replace />} />
            <Route path="/pipeline" element={process ? <PipelineView {...process} onCancel={() => { cancel(); navigate('/'); }} /> : <section className="fg-not-found"><span className="fg-eyebrow">PIPELINE / STANDING BY</span><h1>Ready for the next investigation.</h1><p className="fg-source-intro">No analysis is running. Your current results are unchanged.</p><Link to="/" className="fg-button fg-button-primary">Analyze a repository <ArrowUpRight size={15} /></Link><button className="fg-button" style={{ marginLeft: 12 }} onClick={runDemo}>Start sample demo</button></section>} />
            <Route path="/tools/remediation" element={<div className="fg-legacy-tools"><div className="fg-eyebrow">ADVANCED · LIVE BACKEND</div><RemediationTools /></div>} />
            <Route path="/tools/audit" element={<div className="fg-legacy-tools"><div className="fg-eyebrow">ADVANCED · LIVE BACKEND</div><AuditTools /></div>} />
            <Route path="/sources" element={<SourcesPage><RepositorySources /></SourcesPage>} />
            <Route path="*" element={<div className="fg-not-found"><span className="fg-eyebrow">404 / SIGNAL LOST</span><h1>This page isn’t in the pipeline.</h1><Link className="fg-button fg-button-primary" to="/"><ArrowLeft size={16} />Back to launchpad</Link></div>} />
          </Routes></Suspense>
        </motion.div></AnimatePresence>
      </main>
      {!isLanding && <footer className="fg-workspace-footer"><span><img src="/flakeguard-mark.png" alt="FlakeGuard" style={{ width: 14, height: 14, objectFit: 'contain', verticalAlign: 'middle', marginRight: 6 }} />Evidence first. Human reviewed. Never auto-merged.</span><span><Command size={12} />FlakeGuard <span className="fg-footer-dot">·</span> Built with IBM Bob</span></footer>}
    </div>
  </div>;
}

function RepositorySources() {
  const { loadAnalysis } = useRepositoryResult();
  return <RepositoryIngestion onAnalysisComplete={loadAnalysis} />;
}

function useRepositoryResult() {
  const { setAnalysis } = useWorkspace();
  const navigate = useNavigate();
  const mounted = useRef(false);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  return { loadAnalysis: (result: Parameters<typeof adaptAnalysis>[0]) => {
    // The legacy source request can resolve after this route has been left.
    if (!mounted.current) return;
    setAnalysis(result); navigate('/dashboard');
  } };
}

export default function App() {
  return <MotionConfig reducedMotion="user"><AuthProvider><WorkspaceProvider><BrowserRouter><AmbientBackground /><Shell /></BrowserRouter></WorkspaceProvider></AuthProvider></MotionConfig>;
}
