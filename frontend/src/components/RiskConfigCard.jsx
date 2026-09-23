import React, { useEffect, useState } from 'react';

export function RiskConfigCard() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchConfig() {
      try {
        const res = await fetch('/api/v1/config');
        if (!res.ok) {
          throw new Error(`HTTP error ${res.status}`);
        }
        const data = await res.json();
        setConfig(data);
      } catch (err) {
        setError(err.message || 'Failed to load risk configuration');
      } finally {
        setLoading(false);
      }
    }
    fetchConfig();
  }, []);

  return (
    <div className="card">
      <div className="card-title">Risk Engine Configuration</div>
      <div className="card-subtitle">Active signal weights and score band thresholds</div>

      {loading && <div className="state-box">Loading configuration...</div>}

      {error && <div className="state-box error-box">{error}</div>}

      {config && (
        <>
          <div style={{ marginBottom: '1.25rem' }}>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              Signal Group Weights
            </h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Group</th>
                  <th>Code</th>
                  <th>Weight</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {config.signal_groups.map((group) => (
                  <tr key={group.code}>
                    <td><strong>{group.name}</strong></td>
                    <td><code className="badge badge-info">{group.code}</code></td>
                    <td><strong>{(group.weight * 100).toFixed(0)}%</strong></td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      {group.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              Risk Bands & Actions
            </h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Risk Band</th>
                  <th>Score Range</th>
                  <th>Recommended Action</th>
                </tr>
              </thead>
              <tbody>
                {config.risk_bands.map((band) => (
                  <tr key={band.band}>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: `${band.color}15`,
                          color: band.color,
                          borderColor: `${band.color}30`,
                        }}
                      >
                        {band.band}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      {band.min_score} – {band.max_score}
                    </td>
                    <td>
                      <code style={{ fontSize: '0.75rem', fontWeight: 600 }}>{band.action}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
