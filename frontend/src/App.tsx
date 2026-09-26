import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import RemediationPage from './pages/RemediationPage';
import AuditPage from './pages/AuditPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import './App.css';

function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="app-header">
      <div className="header-brand">
        <Link to="/" className="brand-logo">
          <div className="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>
          <span className="brand-name">FlakeGuard</span>
          <span className="brand-badge">AI SHIELD</span>
        </Link>
      </div>

      <nav className="header-nav">
        <Link to="/" className={location.pathname === '/' ? 'active' : ''}>Overview</Link>
        {isAuthenticated ? (
          <>
            <Link to="/dashboard" className={location.pathname === '/dashboard' ? 'active' : ''}>Dashboard</Link>
            <Link to="/quarantine" className={location.pathname === '/quarantine' ? 'active' : ''}>Quarantine</Link>
            <Link to="/fixes" className={location.pathname === '/fixes' ? 'active' : ''}>Fixes</Link>
            <Link to="/remediation" className={location.pathname === '/remediation' ? 'active' : ''}>Remediation</Link>
            <Link to="/audit" className={location.pathname === '/audit' ? 'active' : ''}>Audit</Link>
          </>
        ) : (
          <>
            <a href="/#capabilities">Capabilities</a>
            <a href="/#interactive-demo">Live Demo</a>
          </>
        )}
      </nav>

      <div className="header-actions">
        {isAuthenticated ? (
          <>
            <div className="user-profile-badge" title={user?.email}>
              <span className="user-avatar">{user?.avatar || 'U'}</span>
              <span>{user?.name}</span>
            </div>
            <button type="button" className="btn-logout" onClick={handleLogout}>
              Sign Out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn-nav-outline">
              Sign In
            </Link>
            <Link to="/signup" className="btn-nav-cta">
              Get Started →
            </Link>
          </>
        )}
      </div>
    </header>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Header />
          <main className="app-main">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/dashboard" element={<Dashboard initialTab="tests" />} />
              <Route path="/quarantine" element={<Dashboard initialTab="quarantine" />} />
              <Route path="/fixes" element={<Dashboard initialTab="fixes" />} />
              <Route path="/remediation" element={<RemediationPage />} />
              <Route path="/audit" element={<AuditPage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
