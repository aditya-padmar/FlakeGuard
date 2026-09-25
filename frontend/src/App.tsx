import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import RemediationPage from './pages/RemediationPage'
import AuditPage from './pages/AuditPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>FlakeGuard</h1>
          <nav>
            <NavLink to="/" end>Dashboard</NavLink>
            <NavLink to="/remediation">F3 Remediation</NavLink>
            <NavLink to="/audit">F4 Audit</NavLink>
          </nav>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/remediation" element={<RemediationPage />} />
            <Route path="/audit" element={<AuditPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
