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
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        minHeight: 'calc(80vh - 80px)',
        padding: '1rem',
        boxSizing: 'border-box',
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '440px',
          margin: '0 auto',
          padding: '2rem 1.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 0.4rem 0', letterSpacing: '-0.02em' }}>
            FraudFusion Portal Login
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
            Role-Based Access Control & Audit Security System
          </p>
        </div>

        {error && (
          <div
            className="state-box error-box"
            style={{
              padding: '0.75rem 1rem',
              fontSize: '0.82rem',
              textAlign: 'left',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <strong>Authentication Error:</strong> {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          <div>
            <label
              htmlFor="email-input"
              style={{
                fontSize: '0.8rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                display: 'block',
                marginBottom: '0.4rem',
              }}
            >
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
                padding: '0.6rem 0.8rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '0.875rem',
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
                boxSizing: 'border-box',
                outline: 'none',
                transition: 'border-color 0.2s ease',
              }}
            />
          </div>

          <div>
            <label
              htmlFor="password-input"
              style={{
                fontSize: '0.8rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                display: 'block',
                marginBottom: '0.4rem',
              }}
            >
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
                padding: '0.6rem 0.8rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '0.875rem',
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
                boxSizing: 'border-box',
                outline: 'none',
                transition: 'border-color 0.2s ease',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.7rem',
              backgroundColor: 'var(--primary-color)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '0.4rem',
              transition: 'background-color 0.2s ease',
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In to Workspace'}
          </button>
        </form>

        {/* Quick Demo Access Buttons */}
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
          <div
            style={{
              fontSize: '0.725rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              textAlign: 'center',
              marginBottom: '0.75rem',
            }}
          >
            Quick Demo Login Presets
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
            <button
              type="button"
              onClick={() => handleQuickLogin('admin@fraudfusion.io', 'AdminPass123!')}
              style={{
                width: '100%',
                padding: '0.6rem 0.75rem',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.825rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxSizing: 'border-box',
                transition: 'border-color 0.15s ease, background-color 0.15s ease',
              }}
            >
              <span>🛡️ <strong>System Admin</strong></span>
              <span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>ADMIN</span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('analyst@fraudfusion.io', 'AnalystPass123!')}
              style={{
                width: '100%',
                padding: '0.6rem 0.75rem',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.825rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxSizing: 'border-box',
                transition: 'border-color 0.15s ease, background-color 0.15s ease',
              }}
            >
              <span>🔍 <strong>Fraud Analyst</strong></span>
              <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>ANALYST</span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('viewer@fraudfusion.io', 'ViewerPass123!')}
              style={{
                width: '100%',
                padding: '0.6rem 0.75rem',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.825rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxSizing: 'border-box',
                transition: 'border-color 0.15s ease, background-color 0.15s ease',
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
