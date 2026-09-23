import React, { useEffect, useState } from 'react';

export function SystemStatus() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/health');
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="card">
      <div className="card-title">System Status & Environment</div>
      <div className="card-subtitle">FastAPI backend connectivity and runtime metadata</div>

      {loading && <div className="state-box">Connecting to backend service...</div>}

      {error && (
        <div className="state-box error-box">
          <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Backend Connection Error</p>
          <p style={{ fontSize: '0.8rem' }}>{error}</p>
          <button
            onClick={fetchHealth}
            style={{
              marginTop: '0.75rem',
              padding: '0.4rem 0.8rem',
              background: 'var(--primary-color)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
            }}
          >
            Retry Connection
          </button>
        </div>
      )}

      {health && (
        <table className="data-table">
          <tbody>
            <tr>
              <td><strong>Status</strong></td>
              <td>
                <span className="badge badge-success">ONLINE</span>
              </td>
            </tr>
            <tr>
              <td><strong>Service</strong></td>
              <td>{health.service}</td>
            </tr>
            <tr>
              <td><strong>Version</strong></td>
              <td><code className="font-mono">{health.version}</code></td>
            </tr>
            <tr>
              <td><strong>Environment</strong></td>
              <td><span className="badge badge-info">{health.environment}</span></td>
            </tr>
            <tr>
              <td><strong>Server Time</strong></td>
              <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                {new Date(health.timestamp).toLocaleString()}
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}
