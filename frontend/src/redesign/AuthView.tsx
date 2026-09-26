import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, ArrowUpRight, Check, Eye, EyeOff, LockKeyhole, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './experience.css';

function GitHubIcon({ size = 18 }: { size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .8a11.3 11.3 0 0 0-3.57 22c.56.1.77-.24.77-.54v-2.1c-3.15.69-3.82-1.34-3.82-1.34-.51-1.3-1.26-1.65-1.26-1.65-1.03-.7.08-.69.08-.69 1.14.08 1.74 1.17 1.74 1.17 1.02 1.74 2.66 1.24 3.31.95.1-.74.4-1.24.72-1.52-2.52-.29-5.17-1.26-5.17-5.59 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.99 0 0 .95-.3 3.11 1.16a10.8 10.8 0 0 1 5.67 0c2.16-1.46 3.11-1.16 3.11-1.16.61 1.56.23 2.71.11 2.99.72.79 1.16 1.8 1.16 3.03 0 4.34-2.66 5.3-5.19 5.58.41.35.77 1.04.77 2.1v3.09c0 .3.21.65.78.54A11.3 11.3 0 0 0 12 .8Z" /></svg>;
}

export default function AuthView({ mode }: { mode: 'login' | 'signup' }) {
  const signupMode = mode === 'signup';
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const reducedMotion = useReducedMotion();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const strength = [password.length >= 8, /[A-Z]/.test(password) && /[a-z]/.test(password), /\d/.test(password), /[^a-zA-Z0-9]/.test(password)].filter(Boolean).length;

  useEffect(() => { setPassword(''); setVisible(false); setError(null); }, [mode]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;
    setError(null);
    if (signupMode && name.trim().length < 2) { setError('Enter a display name with at least 2 characters.'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setError('Enter a valid email address for your local demo profile.'); return; }
    if (password.length < 8) { setError('Use a made-up demo password of at least 8 characters. It is never saved or verified.'); return; }
    setSubmitting(true);
    try {
      // Only profile fields reach the local demo provider. Passwords stay in memory.
      setPassword('');
      if (signupMode) signup(name.trim(), email.trim());
      else login(email.trim());
      navigate('/dashboard', { replace: true });
    } catch {
      setError('The demo profile could not be opened. Please try again.');
      setSubmitting(false);
    }
  }

  return (
    <div className="fg-auth">
      <section className="fg-auth-editorial" aria-label="About FlakeGuard">
        <Link className="fg-ex-brand" to="/" aria-label="FlakeGuard home"><span className="fg-ex-brand-symbol"><ShieldCheck size={23} /></span>FlakeGuard</Link>
        <div className="fg-auth-story">
          <p className="fg-eyebrow"><span className="fg-ex-status-dot" /> A closer look at unreliable tests</p>
          <h1>Green should<br />mean <span>go.</span></h1>
          <p>Investigate intermittent failures with repeated runs, specialist analysis, and fixes you can review.</p>
          <div className="fg-auth-dag" aria-label="Illustration: Bob coordinates Timing, Ordering, Leakage, and Environment agents">
            <svg viewBox="0 0 560 290" role="img" aria-label="Four specialist agents connected to the Bob orchestrator">
              <g fill="none" stroke="rgba(137,147,166,.25)" strokeWidth="1"><path d="M280 83V123M70 123H490M70 123V161M210 123V161M350 123V161M490 123V161" /><path d="M70 207V239H490V207M210 207V239M350 207V239M280 239V274" /></g>
              {['var(--cyan)', 'var(--purple)', '#fbbf24', 'var(--green)'].map((color, index) => <path key={color} className="fg-dag-signal" style={{ animationDelay: `${index * -.8}s` }} d={`M280 83V123H${70 + index * 140}V161`} fill="none" stroke={color} strokeWidth="2" />)}
              <rect x="212" y="33" width="136" height="50" rx="10" fill="var(--surface-raised)" stroke="rgba(101,205,181,.35)" />
              <text x="280" y="54" textAnchor="middle" className="fg-dag-kicker">Orchestrator</text><text x="280" y="72" textAnchor="middle" className="fg-dag-label">Bob</text>
              {['Timing', 'Ordering', 'Leakage', 'Environment'].map((agent, index) => <g key={agent}><rect x={10 + index * 140} y="161" width="120" height="46" rx="8" fill="var(--surface)" stroke="rgba(255,255,255,.12)" /><circle className="fg-dag-node" style={{ animationDelay: `${index * -.8}s` }} cx={26 + index * 140} cy="184" r="3" fill={['var(--cyan)', 'var(--purple)', '#fbbf24', 'var(--green)'][index]} /><text x={78 + index * 140} y="188" textAnchor="middle" className="fg-dag-agent">{agent}</text></g>)}
              <circle cx="280" cy="274" r="4" fill="var(--cyan)" />
            </svg>
            <p className="fg-dag-caption"><span>ILLUSTRATIVE CI / AGENT GRAPH</span>Four specialists investigate different sources of flaky behavior. Animation illustrates the architecture, not live activity.</p>
          </div>
        </div>
        <div className="fg-auth-editorial-footer"><span>Built for engineering teams</span><span>Developer preview</span></div>
      </section>
      <section className="fg-auth-form-side">
        <Link to="/" className="fg-auth-back">Back to overview <ArrowUpRight size={14} /></Link>
        <motion.div className="fg-auth-form-wrap fg-spotlight" initial={reducedMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .4 }}>
          <nav className="fg-auth-tabs" aria-label="Demo access mode"><Link to="/login" aria-current={!signupMode ? 'page' : undefined}>Sign in</Link><Link to="/signup" aria-current={signupMode ? 'page' : undefined}>Create account</Link></nav>
          <p className="fg-eyebrow">Your workspace</p>
          <h2>{signupMode ? 'Create a demo profile' : 'Welcome back'}</h2>
          <p className="fg-auth-description">{signupMode ? 'Try FlakeGuard with a profile stored in this browser.' : 'Open your local workspace to explore FlakeGuard.'}</p>
          <div className="fg-auth-disclosure"><LockKeyhole size={17} /><p><strong>Local demo only — no real authentication.</strong> Your profile is stored in this browser. Use made-up details; passwords are never saved, sent, or verified.</p></div>
          <button type="button" className="fg-button fg-auth-github" onClick={() => setError('GitHub OAuth is not configured. No sign-in was attempted. Use the local demo form below to continue.')}><GitHubIcon size={18} /><span>Continue with GitHub<small>OAuth not configured</small></span><ArrowUpRight size={15} /></button>
          <div className="fg-auth-divider"><span />or use a local demo profile<span /></div>
          <form onSubmit={submit} className="fg-auth-form">
            {signupMode && <div className="fg-ex-field fg-floating-field"><input id="fg-auth-name" name="demo-name" autoComplete="off" placeholder=" " value={name} onChange={event => setName(event.target.value)} required minLength={2} maxLength={100} /><label htmlFor="fg-auth-name">Display name</label></div>}
            <div className="fg-ex-field fg-floating-field"><input id="fg-auth-email" name="demo-email" type="email" autoComplete="off" placeholder=" " value={email} onChange={event => setEmail(event.target.value)} required maxLength={254} /><label htmlFor="fg-auth-email">Demo email</label></div>
            <div className="fg-ex-field"><div className="fg-password-wrap fg-floating-field"><input id="fg-auth-password" type={visible ? 'text' : 'password'} autoComplete="new-password" placeholder=" " value={password} onChange={event => setPassword(event.target.value)} required minLength={8} maxLength={128} aria-describedby="fg-password-help" /><label htmlFor="fg-auth-password">Made-up demo password</label><button type="button" aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={17} /> : <Eye size={17} />}</button></div>
              {signupMode && <div className="fg-password-strength"><div aria-hidden="true">{[1, 2, 3, 4].map(level => <span key={level} data-filled={strength >= level} />)}</div><span id="fg-password-help">{password ? ['Add more variety', 'Basic', 'Fair', 'Good', 'Strong'][strength] : 'Use a made-up password, not a real one'}</span></div>}
              {!signupMode && <span id="fg-password-help" className="fg-ex-input-help">For demo interaction only. Not a credential check.</span>}
            </div>
            {error && <p className="fg-ex-error" role="alert">{error}</p>}
            <button type="submit" className="fg-button fg-button-primary fg-auth-submit" disabled={submitting}>{submitting ? 'Opening workspace…' : signupMode ? 'Create demo profile' : 'Enter demo workspace'}<ArrowRight size={17} /></button>
          </form>
          <p className="fg-auth-footnote"><Check size={14} /> No account required. No credentials leave this page.</p>
        </motion.div>
        <div className="fg-auth-form-footer"><span>FlakeGuard / Developer preview</span><Link to="/">Explore the product <ArrowRight size={13} /></Link></div>
      </section>
    </div>
  );
}
