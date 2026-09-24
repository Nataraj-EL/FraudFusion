import React, { useEffect, useState } from 'react';

export function RiskAssessmentView() {
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sampleType, setSampleType] = useState('HIGH_RISK');
  const [expandedSignals, setExpandedSignals] = useState(false);

  const getSamplePayload = (type) => {
    if (type === 'HIGH_RISK') {
      return {
        transaction: {
          transaction_id: 'TX-RISK-HIGH-001',
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
    } else if (type === 'MEDIUM_RISK') {
      return {
        transaction: {
          transaction_id: 'TX-RISK-MED-002',
          account_id: 'ACC-4412',
          recipient_id: 'ACC-5521',
          amount: 850.0,
          currency: 'USD',
          channel: 'WEB',
          payment_method: 'CREDIT_CARD',
          status: 'PENDING',
          device_context: {
            user_agent: 'Safari (macOS)',
            ip_address: '192.168.1.50',
            is_vpn: false,
          },
        },
        custom_metrics: {
          stored_device: { browser: 'Safari (macOS)', ip_address: '192.168.1.50' },
          distance_km: 750.0,
          historical_mean_amount: 400.0,
          in_degree: 2,
          out_degree: 5,
          total_sent: 1000.0,
          retained_balance: 300.0,
          holding_minutes: 45.0,
          domain_age_days: 120.0,
          self_signed: false,
          local_listing: 'clean',
        },
      };
    } else {
      return {
        transaction: {
          transaction_id: 'TX-RISK-LOW-003',
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
          holding_minutes: 1440.0,
          domain_age_days: 365.0,
          self_signed: false,
          local_listing: 'clean',
        },
      };
    }
  };

  const computeRiskScore = async (type = sampleType) => {
    setLoading(true);
    setError(null);
    try {
      const payload = getSamplePayload(type);
      const res = await fetch('/api/v1/risk-score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      setAssessment(data);
    } catch (err) {
      setError(err.message || 'Failed to compute risk score');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    computeRiskScore('HIGH_RISK');
  }, []);

  const handleScenarioChange = (e) => {
    const selected = e.target.value;
    setSampleType(selected);
    computeRiskScore(selected);
  };

  const getBandColor = (band) => {
    switch (band) {
      case 'Critical':
        return 'var(--color-danger)';
      case 'High':
        return '#ef4444';
      case 'Medium':
        return 'var(--color-warning)';
      case 'Low':
        return '#3b82f6';
      case 'Very Low':
        return 'var(--color-success)';
      default:
        return 'var(--text-secondary)';
    }
  };

  const getActionBadgeClass = (action) => {
    if (action === 'BLOCK_AND_REPORT' || action === 'HOLD') return 'badge-danger';
    if (action === 'CHALLENGE' || action === 'MONITOR') return 'badge-warning';
    return 'badge-success';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Control Header */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div className="card-title">Unified Risk Assessment Engine</div>
            <div className="card-subtitle">
              Consolidated 0–100 risk score, dynamic band, recommended action, and deterministic explainability
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <label htmlFor="risk-scenario-select" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Test Vector Scenario:
            </label>
            <select
              id="risk-scenario-select"
              value={sampleType}
              onChange={handleScenarioChange}
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
              <option value="HIGH_RISK">Critical / High Risk Scenario</option>
              <option value="MEDIUM_RISK">Medium Risk Challenge Scenario</option>
              <option value="LOW_RISK">Low / Very Low Risk Scenario</option>
            </select>
          </div>
        </div>
      </div>

      {loading && <div className="state-box">Evaluating unified risk engine...</div>}
      {error && <div className="state-box error-box">{error}</div>}

      {assessment && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Main Risk Overview Score Banner */}
          <div className="card" style={{ borderLeft: `6px solid ${getBandColor(assessment.risk_band)}` }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem', alignItems: 'center' }}>
              
              {/* Large Score Badge */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div
                  style={{
                    width: '90px',
                    height: '90px',
                    borderRadius: '50%',
                    backgroundColor: `${getBandColor(assessment.risk_band)}15`,
                    border: `3px solid ${getBandColor(assessment.risk_band)}`,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: '1.8rem', fontWeight: 800, color: getBandColor(assessment.risk_band), lineHeight: 1 }}>
                    {assessment.consolidated_score.toFixed(0)}
                  </span>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>/ 100</span>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    Risk Classification
                  </div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 700, color: getBandColor(assessment.risk_band) }}>
                    {assessment.risk_band} Band
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    Tx ID: <strong>{assessment.transaction_id}</strong>
                  </div>
                </div>
              </div>

              {/* Recommended Action Card */}
              <div style={{ padding: '1rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  Recommended Action
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span className={`badge ${getActionBadgeClass(assessment.recommended_action)}`} style={{ fontSize: '0.9rem', padding: '0.35rem 0.75rem' }}>
                    {assessment.recommended_action}
                  </span>
                  {assessment.str_report_eligible && (
                    <span className="badge badge-danger" style={{ fontSize: '0.75rem' }}>
                      STR Eligible
                    </span>
                  )}
                </div>
              </div>

            </div>

            {/* Explanation Callout */}
            <div
              style={{
                marginTop: '1.25rem',
                padding: '0.85rem 1rem',
                backgroundColor: 'var(--bg-app)',
                borderRadius: 'var(--radius-sm)',
                borderLeft: `4px solid ${getBandColor(assessment.risk_band)}`,
                fontSize: '0.9rem',
                color: 'var(--text-primary)',
                lineHeight: 1.4,
              }}
            >
              <strong>Explainability Summary:</strong> {assessment.explanation}
            </div>
          </div>

          {/* Subscores Breakdown Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
            {/* AF Subscore */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="badge badge-info">AF GROUP (45%)</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {assessment.af_subscore.toFixed(1)} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/ 100</span>
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                Adaptive Friction Engine
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Session, device fingerprint, and geo distance anomaly evaluation
              </div>
            </div>

            {/* FF Subscore */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="badge badge-info">FF GROUP (35%)</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {assessment.ff_subscore.toFixed(1)} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/ 100</span>
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                Fund Flow Engine
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Balanced flow ratio, retained balance drain, and holding time velocity
              </div>
            </div>

            {/* PH Subscore */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="badge badge-info">PH GROUP (20%)</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {assessment.ph_subscore.toFixed(1)} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/ 100</span>
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                Phishing Engine
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Domain registration age, SSL certificate validity, and blacklist matches
              </div>
            </div>
          </div>

          {/* Expandable Signal Explanations */}
          <div className="card">
            <div
              onClick={() => setExpandedSignals(!expandedSignals)}
              style={{
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
                cursor: 'pointer',
                userSelect: 'none',
              }}
            >
              <div>
                <div className="card-title">Granular Signal Explanations & Factor Audit</div>
                <div className="card-subtitle">
                  {expandedSignals ? 'Click to collapse individual signal details' : 'Click to expand AF, FF, and PH factor-level details'}
                </div>
              </div>
              <button
                type="button"
                style={{
                  padding: '0.4rem 0.8rem',
                  backgroundColor: 'var(--bg-app)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {expandedSignals ? 'Collapse ▲' : 'Expand Details ▼'}
              </button>
            </div>

            {expandedSignals && (
              <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {Object.entries(assessment.all_signal_results).map(([grpCode, grp]) => (
                  <div key={grpCode} style={{ padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-app)' }}>
                    <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                      {grp.group_name} Factors ({grp.group_code})
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {grp.factors.map((factor) => (
                        <div
                          key={factor.signal_id}
                          style={{
                            padding: '0.75rem',
                            backgroundColor: 'var(--bg-surface)',
                            borderRadius: 'var(--radius-sm)',
                            border: '1px solid var(--border-color)',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span className="badge" style={{ backgroundColor: 'var(--primary-color)', color: '#fff', fontSize: '0.75rem' }}>
                                {factor.signal_id}
                              </span>
                              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{factor.name}</strong>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                Risk Factor: <strong>{factor.risk_factor.toFixed(2)}</strong>
                              </span>
                              <span className={`badge ${factor.triggered ? 'badge-danger' : 'badge-success'}`} style={{ fontSize: '0.72rem' }}>
                                {factor.triggered ? 'TRIGGERED' : 'NORMAL'}
                              </span>
                            </div>
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                            {factor.explanation}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
