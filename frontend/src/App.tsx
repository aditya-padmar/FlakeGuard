import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>FlakeGuard</h1>
          <nav>
            <a href="/">Dashboard</a>
            <a href="/quarantine">Quarantine</a>
            <a href="/fixes">Fixes</a>
          </nav>
        </header>
        
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/quarantine" element={<Dashboard />} />
            <Route path="/fixes" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
