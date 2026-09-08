import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, TrendingUp, Package, Truck, ChevronRight } from 'lucide-react';
import { apiService } from '../services/apiService';
import { useAuth } from '../App';

// ─── Static sample data card shown in the left panel ─────────────────────────
function SampleCard() {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      padding: '20px 24px',
      maxWidth: 320,
    }}>
      {/* Stat row */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: 0.3, marginBottom: 6 }}>
          On-time rate — last 90 days
        </div>
        <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--accent)', letterSpacing: -0.5 }}>
          87.3%
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
          <TrendingUp size={12} /> +2.1 pts from prior period
        </div>
      </div>

      {/* Carrier ranking snippet */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: 0.3, marginBottom: 10 }}>
          Top carriers by on-time rate
        </div>
        {[
          { rank: 1, name: 'Maersk Line',  rate: '94.1%' },
          { rank: 2, name: 'DHL Freight',  rate: '91.8%' },
          { rank: 3, name: 'FedEx Supply', rate: '88.2%' },
        ].map(c => (
          <div key={c.rank} style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 0',
            borderBottom: c.rank < 3 ? '1px solid var(--border)' : 'none',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', width: 16 }}>#{c.rank}</span>
              <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{c.name}</span>
            </div>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-ontime-text)' }}>{c.rate}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Login / Signup screen ────────────────────────────────────────────────────
export default function LoginScreen() {
  const [mode, setMode] = useState('login'); // 'login' | 'signup'

  // Login fields
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');

  // Signup-only fields
  const [orgName, setOrgName]     = useState('');
  const [confirmPw, setConfirmPw] = useState('');

  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);
  const { login }             = useAuth();
  const navigate              = useNavigate();

  useEffect(() => {
    const prev = document.documentElement.getAttribute('data-theme');
    document.documentElement.setAttribute('data-theme', prev || 'light');
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (mode === 'signup') {
      if (password !== confirmPw) {
        setError('Passwords do not match.');
        return;
      }
      if (!orgName.trim()) {
        setError('Organisation name is required.');
        return;
      }
    }

    setLoading(true);
    try {
      let res;
      if (mode === 'login') {
        res = await apiService.login(email, password);
      } else {
        res = await apiService.signup(email, password, orgName);
      }
      const token = res.data.access_token;
      login(token);

      // Decode JWT payload to detect admin role (signature verified server-side)
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.role === 'admin') {
          navigate('/admin', { replace: true });
          return;
        }
      } catch {
        // Non-fatal — fall through to regular redirect
      }

      navigate('/', { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : mode === 'login'
          ? 'Incorrect email or password.'
          : 'Could not create account. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'grid',
      gridTemplateColumns: '55fr 45fr',
      background: 'var(--bg-surface-2)',
    }}>

      {/* ── Left panel ─────────────────────────────────────────────────────── */}
      <div
        style={{
          background: 'var(--bg-surface-2)',
          padding: '48px 56px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
        className="login-left-panel"
      >
        {/* Wordmark */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Package size={20} color="var(--accent)" strokeWidth={2.5} />
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: -0.2 }}>
            CargoScope
          </span>
        </div>

        {/* Center content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32, maxWidth: 380 }}>
          <div>
            <h1 style={{
              fontSize: 28,
              fontWeight: 700,
              color: 'var(--text-primary)',
              letterSpacing: -0.5,
              lineHeight: 1.2,
              marginBottom: 12,
            }}>
              Track shipments and measure carrier performance.
            </h1>
            <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Upload your trade data CSV and get on-time rates, delay flags, and cost anomalies across every carrier in your network.
            </p>
          </div>
          <SampleCard />
        </div>

        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Internal operations tool
        </div>
      </div>

      {/* ── Right panel — form ──────────────────────────────────────────────── */}
      <div style={{
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 40px',
      }}>
        <div style={{ width: '100%', maxWidth: 360 }}>

          {/* Mobile-only: product name above form */}
          <div className="login-mobile-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8 }}>
              <Package size={18} color="var(--accent)" strokeWidth={2.5} />
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>CargoScope</span>
            </div>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 28, lineHeight: 1.5 }}>
              Track shipments and measure carrier performance.
            </p>
          </div>

          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: 'var(--bg-surface-2)', borderRadius: 8, padding: 4 }}>
            {['login', 'signup'].map(m => (
              <button
                key={m}
                type="button"
                onClick={() => { setMode(m); setError(''); }}
                style={{
                  flex: 1,
                  height: 34,
                  border: 'none',
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: mode === m ? 'var(--bg-surface)' : 'transparent',
                  color: mode === m ? 'var(--text-primary)' : 'var(--text-secondary)',
                  boxShadow: mode === m ? '0 1px 3px rgba(0,0,0,0.12)' : 'none',
                  transition: 'all .15s',
                }}
              >
                {m === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Email / Username */}
            <div>
              <label className="form-label" htmlFor="login-email">Email or Username</label>
              <input
                id="login-email"
                type="text"
                className="form-input"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="username"
                autoFocus
                required
                style={{ height: 42 }}
              />
            </div>

            {/* Password */}
            <div>
              <label className="form-label" htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                className="form-input"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                style={{ height: 42 }}
              />
            </div>

            {/* Signup-only fields */}
            {mode === 'signup' && (
              <>
                <div>
                  <label className="form-label" htmlFor="login-confirm-pw">Confirm password</label>
                  <input
                    id="login-confirm-pw"
                    type="password"
                    className="form-input"
                    value={confirmPw}
                    onChange={e => setConfirmPw(e.target.value)}
                    autoComplete="new-password"
                    required
                    style={{ height: 42 }}
                  />
                </div>
                <div>
                  <label className="form-label" htmlFor="login-org-name">Organisation name</label>
                  <input
                    id="login-org-name"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Acme Logistics"
                    value={orgName}
                    onChange={e => setOrgName(e.target.value)}
                    required
                    style={{ height: 42 }}
                  />
                </div>
              </>
            )}

            {error && (
              <div className="field-error" style={{ marginTop: 0 }}>
                <AlertCircle size={13} style={{ flexShrink: 0, marginTop: 1 }} />
                <span>{error}</span>
              </div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="btn-primary"
              style={{ height: 42, justifyContent: 'center', marginTop: 4, width: '100%' }}
            >
              {loading
                ? (mode === 'login' ? 'Signing in…' : 'Creating account…')
                : (mode === 'login' ? 'Sign in' : 'Create account & start')}
            </button>
          </form>
        </div>
      </div>

      {/* ── Responsive styles ───────────────────────────────────────────────── */}
      <style>{`
        .login-mobile-header { display: none; }

        @media (max-width: 768px) {
          div[style*="gridTemplateColumns"] {
            grid-template-columns: 1fr !important;
          }
          .login-left-panel { display: none !important; }
          .login-mobile-header { display: block !important; }
        }
      `}</style>
    </div>
  );
}
