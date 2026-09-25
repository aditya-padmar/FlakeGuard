import type { Fix, FixSuggestion } from '../types';

interface FixViewerProps {
  fix: Fix;
  onApply: (suggestionId: string) => void;
  onReject: () => void;
}

export default function FixViewer({ fix, onApply, onReject }: FixViewerProps) {
  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'low': return 'var(--color-success)';
      case 'medium': return 'var(--color-warning)';
      case 'high': return 'var(--color-error)';
      default: return 'var(--color-text)';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'proposed': return 'var(--color-info)';
      case 'applied': return 'var(--color-warning)';
      case 'verified': return 'var(--color-success)';
      case 'rejected': return 'var(--color-error)';
      default: return 'var(--color-text)';
    }
  };

  return (
    <div className="fix-viewer">
      <div className="fix-header">
        <h3>Fix Suggestions</h3>
        <span 
          className="fix-status"
          style={{ color: getStatusColor(fix.status) }}
        >
          {fix.status.toUpperCase()}
        </span>
      </div>
      
      <div className="fix-meta">
        <div className="meta-item">
          <label>Test:</label>
          <span>{fix.test_name}</span>
        </div>
        <div className="meta-item">
          <label>File:</label>
          <span>{fix.file_path}</span>
        </div>
        {fix.applied_at && (
          <div className="meta-item">
            <label>Applied:</label>
            <span>{new Date(fix.applied_at).toLocaleDateString()}</span>
          </div>
        )}
        {fix.verified_runs > 0 && (
          <div className="meta-item">
            <label>Verified Runs:</label>
            <span>{fix.verified_runs}</span>
          </div>
        )}
      </div>
      
      <div className="suggestions-list">
        {fix.suggestions.map((suggestion) => (
          <SuggestionCard
            key={suggestion.suggestion_id}
            suggestion={suggestion}
            isPrimary={suggestion.suggestion_id === fix.primary_suggestion_id}
            onApply={() => onApply(suggestion.suggestion_id)}
            disabled={fix.status !== 'proposed'}
          />
        ))}
      </div>
      
      {fix.status === 'proposed' && (
        <div className="fix-actions">
          <button className="btn-primary" onClick={() => onApply(fix.primary_suggestion_id)}>
            Apply Primary Fix
          </button>
          <button className="btn-danger" onClick={onReject}>
            Reject All
          </button>
        </div>
      )}
    </div>
  );
}

function SuggestionCard({ 
  suggestion, 
  isPrimary,
  onApply,
  disabled 
}: { 
  suggestion: FixSuggestion;
  isPrimary: boolean;
  onApply: () => void;
  disabled: boolean;
}) {
  const confidencePercent = Math.round(suggestion.confidence * 100);
  
  return (
    <div className={`suggestion-card ${isPrimary ? 'primary' : ''}`}>
      {isPrimary && <span className="primary-badge">RECOMMENDED</span>}
      
      <div className="suggestion-header">
        <h4>{suggestion.fix_type.replace(/_/g, ' ')}</h4>
        <div className="confidence-meter">
          <div 
            className="confidence-fill"
            style={{ width: `${confidencePercent}%` }}
          />
          <span>{confidencePercent}% confidence</span>
        </div>
      </div>
      
      <div className="suggestion-description">
        <p><strong>Description:</strong> {suggestion.description}</p>
        <p><strong>Rationale:</strong> {suggestion.rationale}</p>
      </div>
      
      <div className="suggestion-footer">
        <span 
          className="effort-badge"
          style={{ color: getEffortColor(suggestion.estimated_effort) }}
        >
          {suggestion.estimated_effort} effort
        </span>
        
        {!disabled && !isPrimary && (
          <button className="btn-secondary" onClick={onApply}>
            Apply
          </button>
        )}
      </div>
    </div>
  );
}
