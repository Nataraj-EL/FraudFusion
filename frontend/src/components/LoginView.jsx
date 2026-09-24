import React, { useState } from 'react';

export function LoginView({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Authentication failed');
      }

      const data = await res.json();
      onLoginSuccess(data.user, data.access_token);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (roleEmail, rolePass) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    // Submit login
    setLoading(true);
    setError(null);
    fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: roleEmail, password: rolePass }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Authentication failed');
        return res.json();
      })
      .then((data) => {
        onLoginSuccess(data.user, data.access_token);
      })
      .catch((err) => {
        setError(err.message || 'Quick login failed');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div
      style={{
        display: 'flex',
        justify: 'center',
        alignItems: 'center',
        minHeight: '70vh',
        padding: '1rem',
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '440px',
          padding: '2rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 0.4rem 0' }}>
            FraudFusion Portal Login
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
            Role-Based Access Control & Audit Security System
          </p>
        </div>

        {error && <div className="state-box error-box" style={{ fontSize: '0.82rem' }}>{error}</div>}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label htmlFor="email-input" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Email Address
            </label>
            <input
              id="email-input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. analyst@fraudfusion.io"
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '0.85rem',
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          <div>
            <label htmlFor="password-input" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Password
            </label>
            <input
              id="password-input"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '0.85rem',
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '0.65rem',
              backgroundColor: 'var(--primary-color)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '0.5rem',
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In to Workspace'}
          </button>
        </form>

        {/* Quick Demo Access Buttons */}
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', textAlign: 'center', marginBottom: '0.75rem' }}>
            Quick Demo Login Presets
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button
              onClick={() => handleQuickLogin('admin@fraudfusion.io', 'AdminPass123!')}
              style={{
                padding: '0.5rem',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>🛡️ <strong>System Admin</strong></span>
              <span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>ADMIN</span>
            </button>

            <button
              onClick={() => handleQuickLogin('analyst@fraudfusion.io', 'AnalystPass123!')}
              style={{
                padding: '0.5rem',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>🔍 <strong>Fraud Analyst</strong></span>
              <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>ANALYST</span>
            </button>

            <button
              onClick={() => handleQuickLogin('viewer@fraudfusion.io', 'ViewerPass123!')}
              style={{
                padding: '0.5rem',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>👁️ <strong>Compliance Auditor</strong></span>
              <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>VIEWER</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
