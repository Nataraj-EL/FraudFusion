import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { SystemStatus } from './components/SystemStatus';
import { RiskConfigCard } from './components/RiskConfigCard';
import { IngestionPanel } from './components/IngestionPanel';
import { SignalInspector } from './components/SignalInspector';
import { RiskAssessmentView } from './components/RiskAssessmentView';
import { LoginView } from './components/LoginView';
import { AuditLogView } from './components/AuditLogView';

export function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [activeTab, setActiveTab] = useState('risk');

  useEffect(() => {
    const savedToken = localStorage.getItem('ff_token');
    const savedUser = localStorage.getItem('ff_user');
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('ff_token');
        localStorage.removeItem('ff_user');
      }
    }
  }, []);

  const handleLoginSuccess = (userData, tokenStr) => {
    setUser(userData);
    setToken(tokenStr);
    localStorage.setItem('ff_token', tokenStr);
    localStorage.setItem('ff_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('ff_token');
    localStorage.removeItem('ff_user');
  };

  if (!user || !token) {
    return (
      <div className="app-container">
        <Header />
        <main className="main-content">
          <LoginView onLoginSuccess={handleLoginSuccess} />
        </main>
      </div>
    );
  }

  const isAdmin = user.role === 'Admin';
  const isAnalyst = user.role === 'Analyst' || isAdmin;
  const isViewer = user.role === 'Viewer';

  return (
    <div className="app-container">
      <Header />
      <main className="main-content">
        {/* User Session Bar & Header */}
        <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.2rem' }}>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Fraud Fusion Workspace
              </h1>
              <span className={`badge ${isAdmin ? 'badge-danger' : isAnalyst ? 'badge-warning' : 'badge-info'}`} style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}>
                {user.role} Role
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: 0 }}>
              Logged in as <strong>{user.full_name}</strong> ({user.email})
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => setActiveTab('risk')}
              style={{
                padding: '0.5rem 0.9rem',
                backgroundColor: activeTab === 'risk' ? 'var(--primary-color)' : 'var(--bg-surface)',
                color: activeTab === 'risk' ? '#ffffff' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.82rem',
              }}
            >
              Risk Assessment
            </button>

            <button
              onClick={() => setActiveTab('signals')}
              style={{
                padding: '0.5rem 0.9rem',
                backgroundColor: activeTab === 'signals' ? 'var(--primary-color)' : 'var(--bg-surface)',
                color: activeTab === 'signals' ? '#ffffff' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.82rem',
              }}
            >
              Signal Inspector
            </button>

            {isAnalyst && (
              <button
                onClick={() => setActiveTab('ingestion')}
                style={{
                  padding: '0.5rem 0.9rem',
                  backgroundColor: activeTab === 'ingestion' ? 'var(--primary-color)' : 'var(--bg-surface)',
                  color: activeTab === 'ingestion' ? '#ffffff' : 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '0.82rem',
                }}
              >
                Data Ingestion
              </button>
            )}

            {isAdmin && (
              <button
                onClick={() => setActiveTab('audit')}
                style={{
                  padding: '0.5rem 0.9rem',
                  backgroundColor: activeTab === 'audit' ? 'var(--primary-color)' : 'var(--bg-surface)',
                  color: activeTab === 'audit' ? '#ffffff' : 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '0.82rem',
                }}
              >
                🛡️ Audit & Security
              </button>
            )}

            <button
              onClick={() => setActiveTab('config')}
              style={{
                padding: '0.5rem 0.9rem',
                backgroundColor: activeTab === 'config' ? 'var(--primary-color)' : 'var(--bg-surface)',
                color: activeTab === 'config' ? '#ffffff' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.82rem',
              }}
            >
              System & Config
            </button>

            <button
              onClick={handleLogout}
              style={{
                padding: '0.5rem 0.8rem',
                backgroundColor: 'var(--bg-app)',
                color: 'var(--color-danger)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: '0.8rem',
                marginLeft: '0.5rem',
              }}
            >
              Sign Out
            </button>
          </div>
        </div>

        {activeTab === 'risk' && <RiskAssessmentView user={user} token={token} />}
        {activeTab === 'signals' && <SignalInspector />}
        {activeTab === 'ingestion' && isAnalyst && <IngestionPanel />}
        {activeTab === 'audit' && isAdmin && <AuditLogView token={token} />}
        {activeTab === 'config' && (
          <div className="grid-two-col">
            <SystemStatus />
            <RiskConfigCard />
          </div>
        )}
      </main>
      <footer className="app-footer">
        FraudFusion &copy; {new Date().getFullYear()} — Unified, Explainable Fraud Detection Platform with Tamper-Evident RBAC Audit Trail
      </footer>
    </div>
  );
}

export default App;
