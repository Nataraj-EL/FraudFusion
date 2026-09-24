import React, { useState } from 'react';
import { Header } from './components/Header';
import { SystemStatus } from './components/SystemStatus';
import { RiskConfigCard } from './components/RiskConfigCard';
import { IngestionPanel } from './components/IngestionPanel';

export function App() {
  const [activeTab, setActiveTab] = useState('ingestion');

  return (
    <div className="app-container">
      <Header />
      <main className="main-content">
        <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Fraud Fusion Workspace
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Unified Data Ingestion & Validation Engine
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setActiveTab('ingestion')}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: activeTab === 'ingestion' ? 'var(--primary-color)' : 'var(--bg-surface)',
                color: activeTab === 'ingestion' ? '#ffffff' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.85rem',
              }}
            >
              Data Ingestion
            </button>
            <button
              onClick={() => setActiveTab('config')}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: activeTab === 'config' ? 'var(--primary-color)' : 'var(--bg-surface)',
                color: activeTab === 'config' ? '#ffffff' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.85rem',
              }}
            >
              System & Config
            </button>
          </div>
        </div>

        {activeTab === 'ingestion' && <IngestionPanel />}

        {activeTab === 'config' && (
          <div className="grid-two-col">
            <SystemStatus />
            <RiskConfigCard />
          </div>
        )}
      </main>
      <footer className="app-footer">
        FraudFusion &copy; {new Date().getFullYear()} — Modular, Deterministic, Explainable Risk Architecture
      </footer>
    </div>
  );
}

export default App;
