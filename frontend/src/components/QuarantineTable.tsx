import { useState } from 'react';
import type { QuarantineEntry } from '../types';

interface QuarantineTableProps {
  entries: QuarantineEntry[];
  onReview: (entry: QuarantineEntry) => void;
}

export default function QuarantineTable({ entries, onReview }: QuarantineTableProps) {
  const [filter, setFilter] = useState<string>('all');
  
  const filteredEntries = filter === 'all' 
    ? entries 
    : entries.filter(e => e.status === filter);
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'var(--color-warning)';
      case 'under_review': return 'var(--color-info)';
      case 'resolved': return 'var(--color-success)';
      default: return 'var(--color-text)';
    }
  };
  
  const getProgressPercent = (entry: QuarantineEntry) => {
    return (entry.runs_since_quarantine / entry.runs_until_review) * 100;
  };
  
  return (
    <div className="quarantine-table">
      <div className="quarantine-header">
        <h2>Quarantined Tests</h2>
        
        <div className="filter-group">
          <button 
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button 
            className={filter === 'active' ? 'active' : ''}
            onClick={() => setFilter('active')}
          >
            Active
          </button>
          <button 
            className={filter === 'under_review' ? 'active' : ''}
            onClick={() => setFilter('under_review')}
          >
            Under Review
          </button>
          <button 
            className={filter === 'resolved' ? 'active' : ''}
            onClick={() => setFilter('resolved')}
          >
            Resolved
          </button>
        </div>
      </div>
      
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Test Name</th>
              <th>Reason</th>
              <th>Status</th>
              <th>Quarantined</th>
              <th>Progress to Review</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredEntries.map((entry) => (
              <tr key={entry.quarantine_id}>
                <td className="test-name">{entry.test_name}</td>
                <td className="reason">{entry.reason}</td>
                <td>
                  <span 
                    className="status-badge"
                    style={{ color: getStatusColor(entry.status) }}
                  >
                    {entry.status.replace('_', ' ')}
                  </span>
                </td>
                <td>{new Date(entry.quarantined_at).toLocaleDateString()}</td>
                <td>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ 
                        width: `${Math.min(getProgressPercent(entry), 100)}%`,
                        backgroundColor: getProgressPercent(entry) >= 80 
                          ? 'var(--color-warning)' 
                          : 'var(--color-primary)'
                      }}
                    />
                    <span className="progress-text">
                      {entry.runs_since_quarantine}/{entry.runs_until_review}
                    </span>
                  </div>
                </td>
                <td>
                  <button 
                    className="btn-secondary"
                    onClick={() => onReview(entry)}
                  >
                    Review
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="quarantine-summary">
        <span>Total: {entries.length} tests in quarantine</span>
        <span>Active: {entries.filter(e => e.status === 'active').length}</span>
        <span>Resolved: {entries.filter(e => e.status === 'resolved').length}</span>
      </div>
    </div>
  );
}
