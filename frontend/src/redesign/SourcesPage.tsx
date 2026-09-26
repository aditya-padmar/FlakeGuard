import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ArrowUpRight, GitBranch } from 'lucide-react';
import './sources.css';

export default function SourcesPage({ children }: { children: ReactNode }) {
  return (
    <div className="fg-sources-page">
      <section className="fg-sources-form" aria-label="Repository source configuration">
        {children}
      </section>
      <footer className="fg-sources-help">
        <div className="fg-sources-help-copy">
          <span className="fg-sources-help-mark" aria-hidden="true"><GitBranch size={16} /></span>
          <p className="fg-sources-help-text">Prefer a guided first look? <Link className="fg-sources-inline-link" to="/">Explore the launchpad <ArrowUpRight size={13} aria-hidden="true" /></Link></p>
        </div>
        <Link className="fg-sources-results-link" to="/dashboard">View current results <ArrowRight size={15} aria-hidden="true" /></Link>
      </footer>
    </div>
  );
}
