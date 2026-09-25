import { useState } from 'react';
import type { FlakyTest } from '../types';

interface TestInventoryProps {
  tests: FlakyTest[];
  onSelectTest: (test: FlakyTest) => void;
}

export default function TestInventory({ tests, onSelectTest }: TestInventoryProps) {
  const [sortBy, setSortBy] = useState<keyof FlakyTest>('flake_rate');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const sortedTests = [...tests].sort((a, b) => {
    const aValue = a[sortBy];
    const bValue = b[sortBy];
    
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    }
    
    return sortOrder === 'asc' 
      ? String(aValue).localeCompare(String(bValue))
      : String(bValue).localeCompare(String(aValue));
  });

  const handleSort = (key: keyof FlakyTest) => {
    if (sortBy === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(key);
      setSortOrder('desc');
    }
  };

  const getFlakeRateColor = (rate: number) => {
    if (rate < 0.1) return 'var(--color-success)';
    if (rate < 0.3) return 'var(--color-warning)';
    return 'var(--color-error)';
  };

  return (
    <div className="test-inventory">
      <h2>Flaky Tests</h2>
      
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th onClick={() => handleSort('test_name')}>
                Test Name {sortBy === 'test_name' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('file_path')}>
                File {sortBy === 'file_path' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('flake_rate')}>
                Flake Rate {sortBy === 'flake_rate' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('total_runs')}>
                Runs {sortBy === 'total_runs' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedTests.map((test) => (
              <tr key={test.test_name} onClick={() => onSelectTest(test)}>
                <td className="test-name">{test.test_name}</td>
                <td className="file-path">{test.file_path}</td>
                <td>
                  <span 
                    className="flake-rate"
                    style={{ color: getFlakeRateColor(test.flake_rate) }}
                  >
                    {(test.flake_rate * 100).toFixed(1)}%
                  </span>
                </td>
                <td>{test.total_runs}</td>
                <td>
                  <div className="status-badges">
                    {test.status_history.slice(-5).map((status, i) => (
                      <span 
                        key={i}
                        className={`status-badge ${status}`}
                        title={status}
                      >
                        {status === 'passed' ? '✓' : '✗'}
                      </span>
                    ))}
                  </div>
                </td>
                <td>
                  <button className="btn-secondary" onClick={(e) => {
                    e.stopPropagation();
                    onSelectTest(test);
                  }}>
                    Analyze
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="inventory-summary">
        <span>Total: {tests.length} flaky tests</span>
        <span>Avg Flake Rate: {(tests.reduce((sum, t) => sum + t.flake_rate, 0) / tests.length * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
