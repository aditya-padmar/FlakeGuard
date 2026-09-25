import type { Metrics } from '../types';

interface MetricsPanelProps {
  metrics: Metrics;
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  return (
    <div className="metrics-panel">
      <h2>Key Metrics</h2>
      
      <div className="metrics-grid">
        <MetricCard
          title="Total Flaky Tests"
          value={metrics.total_flaky_tests.toString()}
          subtitle="Across all repositories"
        />
        
        <MetricCard
          title="Tests Quarantined"
          value={metrics.tests_quarantined.toString()}
          subtitle="Awaiting resolution"
        />
        
        <MetricCard
          title="Tests Fixed"
          value={metrics.tests_fixed.toString()}
          subtitle="Successfully resolved"
          highlight
        />
        
        <MetricCard
          title="Pending Classification"
          value={metrics.pending_classification.toString()}
          subtitle="Need analysis"
        />
        
        <MetricCard
          title="Avg Time to Fix"
          value={metrics.average_time_to_fix}
          subtitle="From detection to resolution"
        />
        
        <MetricCard
          title="Overall Flake Rate"
          value={metrics.flake_rate}
          subtitle="Of all test runs"
        />
        
        <MetricCard
          title="Top Root Cause"
          value={metrics.most_common_root_cause}
          subtitle="Most frequent issue"
        />
        
        <MetricCard
          title="Resolution Rate"
          value={metrics.resolution_rate}
          subtitle="Successfully fixed"
          highlight
        />
      </div>
    </div>
  );
}

function MetricCard({ 
  title, 
  value, 
  subtitle, 
  highlight = false 
}: { 
  title: string;
  value: string;
  subtitle: string;
  highlight?: boolean;
}) {
  return (
    <div className={`metric-card ${highlight ? 'highlight' : ''}`}>
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-subtitle">{subtitle}</div>
    </div>
  );
}
