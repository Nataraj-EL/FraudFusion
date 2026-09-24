import React, { useEffect, useState } from 'react';

export function SignalInspector() {
  const [evalResult, setEvalResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sample test inputs
  const [sampleType, setSampleType] = useState('HIGH_RISK');

  const getSamplePayload = (type) => {
    if (type === 'HIGH_RISK') {
      return {
        transaction: {
          transaction_id: 'TX-HIGH-001',
          account_id: 'ACC-8821',
          recipient_id: 'ACC-9904',
          amount: 2500.0,
          currency: 'USD',
          channel: 'MOBILE_APP',
          payment_method: 'WIRE_TRANSFER',
          status: 'PENDING',
          device_context: {
            user_agent: 'Chrome 120 (macOS)',
            ip_address: '198.51.100.45',
            is_vpn: true,
          },
        },
        custom_metrics: {
          stored_device: { browser: 'Firefox 115', ip_address: '10.0.0.1' },
          distance_km: 1200.0,
          historical_mean_amount: 1000.0,
          in_degree: 10,
          out_degree: 10,
          total_sent: 2500.0,
          retained_balance: 25.0,
          holding_minutes: 5.0,
          domain_age_days: 18.0,
          self_signed: true,
          local_listing: 'blacklist',
        },
      };
    } else {
      return {
        transaction: {
          transaction_id: 'TX-LOW-001',
          account_id: 'ACC-1001',
          recipient_id: 'ACC-1002',
          amount: 80.0,
          currency: 'USD',
          channel: 'WEB',
          payment_method: 'CREDIT_CARD',
          status: 'COMPLETED',
          device_context: {
            user_agent: 'Safari (iOS)',
            ip_address: '192.168.1.5',
            is_vpn: false,
          },
        },
        custom_metrics: {
          stored_device: { browser: 'Safari (iOS)', ip_address: '192.168.1.5' },
          distance_km: 0.0,
          historical_mean_amount: 100.0,
          in_degree: 0,
          out_degree: 2,
          total_sent: 1000.0,
          retained_balance: 5000.0,
          holding_minutes: 120.0,
          domain_age_days: 365.0,
          self_signed: false,
          local_listing: 'clean',
        },
      };
    }
  };

  const evaluateSignals = async (type = sampleType) => {
    setLoading(true);
    setError(null);
    try {
      const payload = getSamplePayload(type);
      const res = await fetch('/api/v1/signals/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      setEvalResult(data);
    } catch (err) {
      setError(err.message || 'Failed to evaluate signal engines');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    evaluateSignals('HIGH_RISK');
  }, []);

  const handleSampleChange = (e) => {
    const selected = e.target.value;
    setSampleType(selected);
    evaluateSignals(selected);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Test Controls */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div className="card-title">Fraud Signal Inspector Engine</div>
            <div className="card-subtitle">
              Independent evaluation of Adaptive Friction (AF), Fund Flow (FF), and Phishing (PH) signals
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <label htmlFor="sample-select" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Test Vector Scenario:
            </label>
            <select
              id="sample-select"
              value={sampleType}
              onChange={handleSampleChange}
              disabled={loading}
              style={{
                padding: '0.45rem 0.8rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '0.85rem',
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="HIGH_RISK">High Risk Anomaly Scenario</option>
              <option value="LOW_RISK">Low Risk Normal Scenario</option>
            </select>
          </div>
        </div>
      </div>

      {loading && <div className="state-box">Evaluating fraud signal engines...</div>}

      {error && <div className="state-box error-box">{error}</div>}

      {evalResult && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {Object.entries(evalResult.signal_groups).map(([groupCode, group]) => (
            <div key={groupCode} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <div className="card-title" style={{ fontSize: '1.05rem' }}>
                    {group.group_name} Engine ({group.group_code})
                  </div>
                  <div className="card-subtitle">
                    Group Weight: <strong>{(group.group_weight * 100).toFixed(0)}%</strong> | Raw Score: <strong>{group.raw_score.toFixed(4)}</strong>
                  </div>
                </div>
                <span className="badge badge-info">{group.group_code} GROUP</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {group.factors.map((factor) => {
                  const factorColor =
                    factor.risk_factor >= 0.7
                      ? 'var(--color-danger)'
                      : factor.risk_factor >= 0.3
                      ? 'var(--color-warning)'
                      : 'var(--color-success)';

                  return (
                    <div
                      key={factor.signal_id}
                      style={{
                        padding: '1rem',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--bg-app)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                          <span
                            className="badge"
                            style={{
                              backgroundColor: 'var(--primary-color)',
                              color: '#ffffff',
                            }}
                          >
                            {factor.signal_id}
                          </span>
                          <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                            {factor.name}
                          </strong>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            Weight: <strong>{(factor.weight * 100).toFixed(0)}%</strong>
                          </span>
                          <span
                            className="badge"
                            style={{
                              backgroundColor: `${factorColor}15`,
                              color: factorColor,
                              border: `1px solid ${factorColor}40`,
                              fontSize: '0.8rem',
                            }}
                          >
                            Risk Factor: {factor.risk_factor.toFixed(2)}
                          </span>
                          <span
                            className={`badge ${factor.triggered ? 'badge-danger' : 'badge-success'}`}
                          >
                            {factor.triggered ? 'TRIGGERED' : 'NORMAL'}
                          </span>
                        </div>
                      </div>

                      {/* Plain-Language Explanation */}
                      <div
                        style={{
                          fontSize: '0.82rem',
                          color: 'var(--text-secondary)',
                          lineHeight: 1.4,
                          padding: '0.5rem 0.75rem',
                          backgroundColor: 'var(--bg-surface)',
                          borderRadius: 'var(--radius-sm)',
                          borderLeft: `3px solid ${factorColor}`,
                        }}
                      >
                        <strong>Explanation:</strong> {factor.explanation}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
