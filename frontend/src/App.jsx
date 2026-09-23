import React from 'react';
import { Header } from './components/Header';
import { SystemStatus } from './components/SystemStatus';
import { RiskConfigCard } from './components/RiskConfigCard';

export function App() {
  return (
    <div className="app-container">
      <Header />
      <main className="main-content">
        <div style={{ marginBottom: '1.5rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Fraud Fusion Workspace
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Unified Risk Score & Explainable Fraud Engine Foundation
          </p>
        </div>

        <div className="grid-two-col">
          <SystemStatus />
          <RiskConfigCard />
        </div>
      </main>
      <footer className="app-footer">
        FraudFusion &copy; {new Date().getFullYear()} — Modular, Deterministic, Explainable Risk Architecture
      </footer>
    </div>
  );
}

export default App;
