import React from 'react';

export function Header() {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon">FF</div>
        <div>
          <span className="brand-title">FraudFusion</span>
          <span className="brand-subtitle">Explainable Fraud Detection Platform</span>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span className="badge badge-info">v0.1.0 Foundation</span>
      </div>
    </header>
  );
}
