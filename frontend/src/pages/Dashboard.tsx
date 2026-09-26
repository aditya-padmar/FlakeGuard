import { useState, useEffect } from 'react';
import TestInventory from '../components/TestInventory';
import RootCauseChart from '../components/RootCauseChart';
import MetricsPanel from '../components/MetricsPanel';
import FixViewer from '../components/FixViewer';
import QuarantineTable from '../components/QuarantineTable';
import type { FlakyTest, RootCause, Fix, QuarantineEntry, Metrics } from '../types';
import demoData from '../mock/demo-data.json';

interface DashboardProps {
  initialTab?: 'tests' | 'quarantine' | 'fixes';
}

export default function Dashboard({ initialTab = 'tests' }: DashboardProps = {}) {
  const [selectedTest, setSelectedTest] = useState<FlakyTest | null>(null);
  const [flakyTests, setFlakyTests] = useState<FlakyTest[]>([]);
  const [rootCauses, setRootCauses] = useState<RootCause[]>([]);
  const [fixes, setFixes] = useState<Fix[]>([]);
  const [quarantine, setQuarantine] = useState<QuarantineEntry[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [activeTab, setActiveTab] = useState<'tests' | 'quarantine' | 'fixes'>(initialTab);
  
  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  useEffect(() => {
    // Load demo data
    setFlakyTests(demoData.flakyTests as FlakyTest[]);
    setRootCauses(demoData.rootCauses as RootCause[]);
    setFixes(demoData.fixes as Fix[]);
    setQuarantine(demoData.quarantine as QuarantineEntry[]);
    setMetrics(demoData.metrics as Metrics);
  }, []);
  
  const handleSelectTest = (test: FlakyTest) => {
    setSelectedTest(test);
    // In production, this would fetch the fix from the API
  };
  
  const handleApplyFix = (suggestionId: string) => {
    if (!selectedTest) return;
    
    const fix = fixes.find(f => f.test_name === selectedTest.test_name);
    if (fix) {
      console.log('Applying fix:', suggestionId);
      // In production, this would call the API
    }
  };
  
  const handleRejectFix = () => {
    console.log('Rejecting fix');
    // In production, this would call the API
  };
  
  const handleReviewQuarantine = (entry: QuarantineEntry) => {
    console.log('Reviewing:', entry);
    // In production, this would open a review modal
  };
  
  const selectedFix = selectedTest 
    ? fixes.find(f => f.test_name === selectedTest.test_name)
    : null;
  
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="tabs">
          <button 
            className={activeTab === 'tests' ? 'active' : ''}
            onClick={() => setActiveTab('tests')}
          >
            Flaky Tests
          </button>
          <button 
            className={activeTab === 'quarantine' ? 'active' : ''}
            onClick={() => setActiveTab('quarantine')}
          >
            Quarantine
          </button>
          <button 
            className={activeTab === 'fixes' ? 'active' : ''}
            onClick={() => setActiveTab('fixes')}
          >
            Fixes
          </button>
        </div>
      </div>
      
      {metrics && <MetricsPanel metrics={metrics} />}
      
      <div className="dashboard-content">
        <div className="main-content">
          {activeTab === 'tests' && (
            <TestInventory 
              tests={flakyTests}
              onSelectTest={handleSelectTest}
            />
          )}
          
          {activeTab === 'quarantine' && (
            <QuarantineTable
              entries={quarantine}
              onReview={handleReviewQuarantine}
            />
          )}
          
          {activeTab === 'fixes' && (
            <div className="fixes-list">
              <h2>Fix Suggestions</h2>
              {fixes.map(fix => (
                <FixViewer
                  key={fix.fix_id}
                  fix={fix}
                  onApply={handleApplyFix}
                  onReject={handleRejectFix}
                />
              ))}
            </div>
          )}
        </div>
        
        <div className="side-content">
          <RootCauseChart data={rootCauses} />
          
          {selectedFix && (
            <div className="selected-fix">
              <h3>Selected Test Fix</h3>
              <FixViewer
                fix={selectedFix}
                onApply={handleApplyFix}
                onReject={handleRejectFix}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
