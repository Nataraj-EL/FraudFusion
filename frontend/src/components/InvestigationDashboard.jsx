import React, { useEffect, useState, useCallback } from 'react';
import { ReportExportModal } from './ReportExportModal';

export function InvestigationDashboard({ user, token }) {
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [totalTx, setTotalTx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [search, setSearch] = useState('');
  const [riskBandFilter, setRiskBandFilter] = useState('');
  const [accountIdFilter, setAccountIdFilter] = useState('');

  // Selected Transaction Investigation Detail Modal
  const [selectedTxId, setSelectedTxId] = useState(null);
  const [txDetail, setTxDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailTab, setDetailTab] = useState('risk'); // 'risk' | 'fund_flow' | 'audit'

  // Report Export Modal
  const [showExportModal, setShowExportModal] = useState(false);

  const fetchDashboardSummary = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/investigations/summary', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to load dashboard summary metrics');
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  }, [token]);

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (riskBandFilter) params.append('risk_band', riskBandFilter);
      if (accountIdFilter) params.append('account_id', accountIdFilter);
      params.append('limit', '50');

      const res = await fetch(`/api/v1/investigations/transactions?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to fetch transaction list');
      const data = await res.json();
      setTransactions(data.items || []);
      setTotalTx(data.total || 0);
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [search, riskBandFilter, accountIdFilter, token]);

  useEffect(() => {
    fetchDashboardSummary();
    fetchTransactions();
  }, [fetchDashboardSummary, fetchTransactions]);

  const openInvestigation = async (txId) => {
    setSelectedTxId(txId);
    setLoadingDetail(true);
    setDetailTab('risk');
    try {
      const res = await fetch(`/api/v1/investigations/transactions/${txId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to load transaction investigation details');
      const data = await res.json();
      setTxDetail(data);
    } catch (err) {
      alert(`Error loading transaction detail: ${err.message}`);
    } finally {
      setLoadingDetail(false);
    }
  };

  const closeInvestigation = () => {
    setSelectedTxId(null);
    setTxDetail(null);
  };

  const isAnalyst = user.role === 'Analyst' || user.role === 'Admin';

  const getBandBadgeClass = (band) => {
    switch (band) {
      case 'Critical':
        return 'badge-danger';
      case 'High':
        return 'badge-warning';
      case 'Medium':
        return 'badge-info';
      case 'Low':
      case 'Very Low':
        return 'badge-success';
      default:
        return 'badge-secondary';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner / Summary Cards */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              🔍 Unified Analyst Investigation Dashboard
            </h2>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Real-time transaction risk monitoring, signal domain breakdown, and fund flow network topology.
            </p>
          </div>
          <button
            onClick={() => {
              fetchDashboardSummary();
              fetchTransactions();
            }}
            style={{
              padding: '0.4rem 0.8rem',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 600,
            }}
          >
            🔄 Refresh Data
          </button>
        </div>

        {summary && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '1rem',
              marginTop: '0.5rem',
            }}
          >
            <div
              style={{
                background: 'var(--bg-app)',
                padding: '0.9rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                Total Ingested
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {summary.total_transactions}
              </div>
            </div>

            <div
              style={{
                background: '#fef2f2',
                padding: '0.9rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #fca5a5',
                cursor: 'pointer',
              }}
              onClick={() => setRiskBandFilter('Critical')}
            >
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#991b1b', fontWeight: 700 }}>
                Critical Risk
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#dc2626' }}>
                {summary.risk_band_counts['Critical'] || 0}
              </div>
            </div>

            <div
              style={{
                background: '#fff7ed',
                padding: '0.9rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #fdba74',
                cursor: 'pointer',
              }}
              onClick={() => setRiskBandFilter('High')}
            >
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#9a3412', fontWeight: 700 }}>
                High Risk
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ea580c' }}>
                {summary.risk_band_counts['High'] || 0}
              </div>
            </div>

            <div
              style={{
                background: '#fefce8',
                padding: '0.9rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #fde047',
                cursor: 'pointer',
              }}
              onClick={() => setRiskBandFilter('Medium')}
            >
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#854d0e', fontWeight: 700 }}>
                Medium Risk
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ca8a04' }}>
                {summary.risk_band_counts['Medium'] || 0}
              </div>
            </div>

            <div
              style={{
                background: '#f0fdf4',
                padding: '0.9rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #86efac',
                cursor: 'pointer',
              }}
              onClick={() => setRiskBandFilter('Low')}
            >
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#166534', fontWeight: 700 }}>
                Low & Very Low
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#16a34a' }}>
                {(summary.risk_band_counts['Low'] || 0) + (summary.risk_band_counts['Very Low'] || 0)}
              </div>
            </div>

            <div
              style={{
                background: 'var(--bg-app)',
                padding: '0.9rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                cursor: 'pointer',
              }}
              onClick={() => setRiskBandFilter('Unassessed')}
            >
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                Unassessed
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-secondary)' }}>
                {summary.risk_band_counts['Unassessed'] || 0}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Search & Transaction Table Card */}
      <div className="card">
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ flex: 1, minWidth: '220px' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Search Transaction ID, Account ID, Recipient..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ width: '180px' }}>
            <select
              className="form-control"
              value={riskBandFilter}
              onChange={(e) => setRiskBandFilter(e.target.value)}
            >
              <option value="">All Risk Bands</option>
              <option value="Critical">Critical (81–100)</option>
              <option value="High">High (61–80)</option>
              <option value="Medium">Medium (41–60)</option>
              <option value="Low">Low (21–40)</option>
              <option value="Very Low">Very Low (0–20)</option>
              <option value="Unassessed">Unassessed</option>
            </select>
          </div>

          <div style={{ width: '180px' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Account ID Filter"
              value={accountIdFilter}
              onChange={(e) => setAccountIdFilter(e.target.value)}
            />
          </div>

          {(search || riskBandFilter || accountIdFilter) && (
            <button
              onClick={() => {
                setSearch('');
                setRiskBandFilter('');
                setAccountIdFilter('');
              }}
              style={{
                padding: '0.5rem 0.8rem',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontSize: '0.8rem',
              }}
            >
              Clear Filters
            </button>
          )}
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            Loading transactions dataset...
          </div>
        ) : transactions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 0.5rem 0' }}>No transactions found</p>
            <p style={{ fontSize: '0.85rem', margin: 0 }}>
              No transactions match your search query or risk band filter criteria.
            </p>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              Showing {transactions.length} of {totalTx} transactions
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-app)', borderBottom: '2px solid var(--border-color)', textAlign: 'left' }}>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Transaction ID</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Source</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Origin & Beneficiary</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Amount</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Risk Score</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Risk Band</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Action</th>
                    <th style={{ padding: '0.6rem 0.8rem' }}>Status</th>
                    <th style={{ padding: '0.6rem 0.8rem', textAlign: 'right' }}>Investigation</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr
                      key={tx.transaction_id}
                      style={{
                        borderBottom: '1px solid var(--border-color)',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      <td style={{ padding: '0.6rem 0.8rem', fontWeight: 700, fontFamily: 'monospace' }}>
                        {tx.transaction_id}
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem', color: 'var(--text-secondary)' }}>
                        {tx.source_type}
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem' }}>
                        <div><strong>From:</strong> {tx.account_id}</div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}><strong>To:</strong> {tx.recipient_id}</div>
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600 }}>
                        {tx.amount.toFixed(2)} {tx.currency}
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem', fontWeight: 800 }}>
                        {tx.consolidated_score !== null && tx.consolidated_score !== undefined
                          ? `${tx.consolidated_score.toFixed(0)} / 100`
                          : '—'}
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem' }}>
                        <span className={`badge ${getBandBadgeClass(tx.risk_band)}`}>
                          {tx.risk_band}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600, fontSize: '0.78rem' }}>
                        {tx.recommended_action || 'N/A'}
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem', fontSize: '0.75rem' }}>
                        {tx.str_status === 'DRAFT_GENERATED' ? (
                          <span style={{ color: '#dc2626', fontWeight: 700 }}>🚨 STR DRAFT</span>
                        ) : tx.report_status === 'REPORT_GENERATED' ? (
                          <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ REPORT READY</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>UNASSESSED</span>
                        )}
                      </td>
                      <td style={{ padding: '0.6rem 0.8rem', textAlign: 'right' }}>
                        <button
                          onClick={() => openInvestigation(tx.transaction_id)}
                          style={{
                            padding: '0.35rem 0.75rem',
                            backgroundColor: 'var(--primary-color)',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: 'var(--radius-sm)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '0.78rem',
                          }}
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Recent Security & Audit Activity (for Analyst & Admin) */}
      {summary && summary.recent_audit_logs && summary.recent_audit_logs.length > 0 && (
        <div className="card">
          <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 700 }}>
            🛡️ Recent Compliance & Audit Log Activity
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-app)', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem' }}>Timestamp</th>
                  <th style={{ padding: '0.5rem' }}>User</th>
                  <th style={{ padding: '0.5rem' }}>Role</th>
                  <th style={{ padding: '0.5rem' }}>Action</th>
                  <th style={{ padding: '0.5rem' }}>Resource</th>
                  <th style={{ padding: '0.5rem' }}>Tx ID</th>
                  <th style={{ padding: '0.5rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_audit_logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.5rem', fontWeight: 600 }}>{log.user_email}</td>
                    <td style={{ padding: '0.5rem' }}>{log.user_role}</td>
                    <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontWeight: 700 }}>{log.action}</td>
                    <td style={{ padding: '0.5rem' }}>{log.resource_type}</td>
                    <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{log.transaction_id || '—'}</td>
                    <td style={{ padding: '0.5rem' }}>
                      <span className={`badge ${log.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SINGLE TRANSACTION INVESTIGATION MODAL */}
      {selectedTxId && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1.5rem',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
              width: '100%',
              maxWidth: '900px',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '1.25rem 1.5rem',
                borderBottom: '1px solid var(--border-color)',
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
                background: 'var(--bg-app)',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, fontFamily: 'monospace' }}>
                    Investigation: {selectedTxId}
                  </h3>
                  {txDetail && txDetail.risk_report && (
                    <span className={`badge ${getBandBadgeClass(txDetail.risk_report.risk_band)}`}>
                      {txDetail.risk_report.risk_band} ({txDetail.risk_report.consolidated_score.toFixed(0)} / 100)
                    </span>
                  )}
                </div>
                <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Detailed signal factor breakdown, network fund flow topology, and compliance audit history.
                </p>
              </div>

              <button
                onClick={closeInvestigation}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                }}
              >
                &times;
              </button>
            </div>

            {/* Modal Navigation Tabs */}
            <div
              style={{
                display: 'flex',
                borderBottom: '1px solid var(--border-color)',
                padding: '0 1.5rem',
                background: 'var(--bg-surface)',
                gap: '1rem',
              }}
            >
              <button
                onClick={() => setDetailTab('risk')}
                style={{
                  padding: '0.75rem 0.5rem',
                  border: 'none',
                  borderBottom: detailTab === 'risk' ? '3px solid var(--primary-color)' : '3px solid transparent',
                  fontWeight: detailTab === 'risk' ? 700 : 500,
                  color: detailTab === 'risk' ? 'var(--primary-color)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  background: 'none',
                  fontSize: '0.85rem',
                }}
              >
                📊 Risk & Signals
              </button>

              <button
                onClick={() => setDetailTab('fund_flow')}
                style={{
                  padding: '0.75rem 0.5rem',
                  border: 'none',
                  borderBottom: detailTab === 'fund_flow' ? '3px solid var(--primary-color)' : '3px solid transparent',
                  fontWeight: detailTab === 'fund_flow' ? 700 : 500,
                  color: detailTab === 'fund_flow' ? 'var(--primary-color)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  background: 'none',
                  fontSize: '0.85rem',
                }}
              >
                🕸️ Fund Flow Visualization
              </button>

              <button
                onClick={() => setDetailTab('audit')}
                style={{
                  padding: '0.75rem 0.5rem',
                  border: 'none',
                  borderBottom: detailTab === 'audit' ? '3px solid var(--primary-color)' : '3px solid transparent',
                  fontWeight: detailTab === 'audit' ? 700 : 500,
                  color: detailTab === 'audit' ? 'var(--primary-color)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  background: 'none',
                  fontSize: '0.85rem',
                }}
              >
                📜 Compliance & Audit Logs
              </button>
            </div>

            {/* Modal Content Body */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
              {loadingDetail ? (
                <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  Evaluating risk engines and fetching topology...
                </div>
              ) : !txDetail ? (
                <div className="alert alert-danger">Failed to load investigation details.</div>
              ) : (
                <>
                  {/* TAB 1: RISK & SIGNALS */}
                  {detailTab === 'risk' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      {/* Action & Explanation Banner */}
                      <div
                        style={{
                          background: txDetail.risk_report.consolidated_score >= 61 ? '#fef2f2' : 'var(--bg-app)',
                          border: `1px solid ${txDetail.risk_report.consolidated_score >= 61 ? '#fca5a5' : 'var(--border-color)'}`,
                          borderRadius: 'var(--radius-md)',
                          padding: '1rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                              Recommended Action
                            </span>
                            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                              {txDetail.risk_report.recommended_action}
                            </div>
                          </div>
                          <button
                            onClick={() => setShowExportModal(true)}
                            style={{
                              padding: '0.5rem 0.9rem',
                              backgroundColor: 'var(--primary-color)',
                              color: '#ffffff',
                              border: 'none',
                              borderRadius: 'var(--radius-sm)',
                              fontWeight: 600,
                              cursor: 'pointer',
                              fontSize: '0.82rem',
                            }}
                          >
                            📥 Export / STR Draft
                          </button>
                        </div>
                        <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          <strong>Deterministic Summary:</strong> {txDetail.risk_report.explanation}
                        </p>
                      </div>

                      {/* Subscore Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                        <div style={{ background: 'var(--bg-app)', padding: '0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Adaptive Friction (AF)</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{txDetail.risk_report.af_subscore.toFixed(1)} / 100</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Group Weight: 45%</div>
                        </div>

                        <div style={{ background: 'var(--bg-app)', padding: '0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Fund Flow (FF)</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{txDetail.risk_report.ff_subscore.toFixed(1)} / 100</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Group Weight: 35%</div>
                        </div>

                        <div style={{ background: 'var(--bg-app)', padding: '0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Phishing (PH)</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{txDetail.risk_report.ph_subscore.toFixed(1)} / 100</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Group Weight: 20%</div>
                        </div>
                      </div>

                      {/* Triggered Signals */}
                      <div>
                        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', fontWeight: 700 }}>
                          Triggered Signal Factors ({txDetail.risk_report.triggered_signals?.length || 0})
                        </h4>
                        {txDetail.risk_report.triggered_signals && txDetail.risk_report.triggered_signals.length > 0 ? (
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                            <thead>
                              <tr style={{ background: 'var(--bg-app)', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                                <th style={{ padding: '0.5rem' }}>Code</th>
                                <th style={{ padding: '0.5rem' }}>Factor Name</th>
                                <th style={{ padding: '0.5rem' }}>Factor Value</th>
                                <th style={{ padding: '0.5rem' }}>Weight</th>
                                <th style={{ padding: '0.5rem' }}>Explanation</th>
                              </tr>
                            </thead>
                            <tbody>
                              {txDetail.risk_report.triggered_signals.map((sig) => (
                                <tr key={sig.signal_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                  <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontWeight: 700 }}>{sig.signal_id}</td>
                                  <td style={{ padding: '0.5rem', fontWeight: 600 }}>{sig.name}</td>
                                  <td style={{ padding: '0.5rem', fontWeight: 700, color: '#dc2626' }}>{sig.risk_factor.toFixed(2)}</td>
                                  <td style={{ padding: '0.5rem' }}>{(sig.weight * 100).toFixed(0)}%</td>
                                  <td style={{ padding: '0.5rem', color: 'var(--text-secondary)' }}>{sig.explanation}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : (
                          <div style={{ padding: '0.75rem', background: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            No individual risk factors exceeded anomaly thresholds for this transaction.
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB 2: FUND FLOW VISUALIZATION */}
                  {detailTab === 'fund_flow' && txDetail.fund_flow && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      <div style={{ background: 'var(--bg-app)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                        <h4 style={{ margin: '0 0 0.25rem 0', fontSize: '0.9rem', fontWeight: 700 }}>
                          Network Topology & Dwell Dynamics
                        </h4>
                        <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {txDetail.fund_flow.explanation}
                        </p>
                      </div>

                      {/* Lightweight SVG Graph Diagram */}
                      <div
                        style={{
                          background: '#0f172a',
                          borderRadius: 'var(--radius-md)',
                          padding: '2rem 1rem',
                          display: 'flex',
                          justify: 'center',
                          alignItems: 'center',
                        }}
                      >
                        <svg width="100%" height="180" viewBox="0 0 700 180" style={{ maxWidth: '700px' }}>
                          <defs>
                            <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                              <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
                            </marker>
                            <marker id="arrow-danger" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
                            </marker>
                          </defs>

                          {txDetail.fund_flow.nodes.length === 2 ? (
                            <>
                              {/* Direct Sender -> Recipient */}
                              {/* Sender Node */}
                              <circle cx="150" cy="90" r="35" fill="#1e293b" stroke="#3b82f6" strokeWidth="3" />
                              <text x="150" y="85" textAnchor="middle" fill="#f8fafc" fontSize="11" fontWeight="bold">SENDER</text>
                              <text x="150" y="102" textAnchor="middle" fill="#94a3b8" fontSize="9">{txDetail.fund_flow.nodes[0].id.slice(0, 12)}</text>

                              {/* Edge */}
                              <line
                                x1="190" y1="90" x2="510" y2="90"
                                stroke={txDetail.fund_flow.edges[0]?.is_suspicious ? '#ef4444' : '#38bdf8'}
                                strokeWidth={txDetail.fund_flow.edges[0]?.is_suspicious ? '3' : '2'}
                                strokeDasharray={txDetail.fund_flow.edges[0]?.is_suspicious ? '4 2' : 'none'}
                                markerEnd={txDetail.fund_flow.edges[0]?.is_suspicious ? 'url(#arrow-danger)' : 'url(#arrow)'}
                              />
                              <text x="350" y="75" textAnchor="middle" fill="#f8fafc" fontSize="11" fontWeight="bold">
                                {txDetail.transaction.amount.toFixed(2)} {txDetail.transaction.currency}
                              </text>
                              <text x="350" y="112" textAnchor="middle" fill={txDetail.fund_flow.edges[0]?.is_suspicious ? '#fca5a5' : '#94a3b8'} fontSize="9">
                                {txDetail.fund_flow.edges[0]?.flow_type}
                              </text>

                              {/* Recipient Node */}
                              <circle cx="550" cy="90" r="35" fill="#1e293b" stroke={txDetail.fund_flow.nodes[1].risk_level === 'critical' ? '#ef4444' : '#10b981'} strokeWidth="3" />
                              <text x="550" y="85" textAnchor="middle" fill="#f8fafc" fontSize="11" fontWeight="bold">RECIPIENT</text>
                              <text x="550" y="102" textAnchor="middle" fill="#94a3b8" fontSize="9">{txDetail.fund_flow.nodes[1].id.slice(0, 12)}</text>
                            </>
                          ) : (
                            <>
                              {/* 3 Nodes: Sender -> Relay -> Recipient */}
                              {/* Node 1: Sender */}
                              <circle cx="100" cy="90" r="32" fill="#1e293b" stroke="#3b82f6" strokeWidth="3" />
                              <text x="100" y="85" textAnchor="middle" fill="#f8fafc" fontSize="10" fontWeight="bold">ORIGIN</text>
                              <text x="100" y="100" textAnchor="middle" fill="#94a3b8" fontSize="8">{txDetail.fund_flow.nodes[0].id.slice(0, 10)}</text>

                              {/* Edge 1 */}
                              <line
                                x1="135" y1="90" x2="315" y2="90"
                                stroke={txDetail.fund_flow.edges[0]?.is_suspicious ? '#ef4444' : '#38bdf8'}
                                strokeWidth="2.5"
                                markerEnd={txDetail.fund_flow.edges[0]?.is_suspicious ? 'url(#arrow-danger)' : 'url(#arrow)'}
                              />
                              <text x="225" y="75" textAnchor="middle" fill="#f8fafc" fontSize="10" fontWeight="bold">
                                {txDetail.transaction.amount.toFixed(2)} {txDetail.transaction.currency}
                              </text>

                              {/* Node 2: Relay */}
                              <circle cx="350" cy="90" r="32" fill="#1e293b" stroke="#f59e0b" strokeWidth="3" />
                              <text x="350" y="85" textAnchor="middle" fill="#f59e0b" fontSize="10" fontWeight="bold">RELAY</text>
                              <text x="350" y="100" textAnchor="middle" fill="#94a3b8" fontSize="8">Dwell: {txDetail.fund_flow.metrics.holding_minutes?.toFixed(0)}m</text>

                              {/* Edge 2 */}
                              <line
                                x1="385" y1="90" x2="565" y2="90"
                                stroke={txDetail.fund_flow.edges[1]?.is_suspicious ? '#ef4444' : '#38bdf8'}
                                strokeWidth="2.5"
                                strokeDasharray="4 2"
                                markerEnd={txDetail.fund_flow.edges[1]?.is_suspicious ? 'url(#arrow-danger)' : 'url(#arrow)'}
                              />
                              <text x="475" y="75" textAnchor="middle" fill="#fca5a5" fontSize="10" fontWeight="bold">
                                {txDetail.fund_flow.edges[1]?.flow_type || 'RAPID DRAIN'}
                              </text>

                              {/* Node 3: Recipient */}
                              <circle cx="600" cy="90" r="32" fill="#1e293b" stroke="#ef4444" strokeWidth="3" />
                              <text x="600" y="85" textAnchor="middle" fill="#f8fafc" fontSize="10" fontWeight="bold">TARGET</text>
                              <text x="600" y="100" textAnchor="middle" fill="#94a3b8" fontSize="8">{txDetail.fund_flow.nodes[2]?.id.slice(0, 10)}</text>
                            </>
                          )}
                        </svg>
                      </div>

                      {/* Fund Flow Metrics Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
                        <div style={{ background: 'var(--bg-app)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>In-Degree</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{txDetail.fund_flow.metrics.in_degree}</div>
                        </div>

                        <div style={{ background: 'var(--bg-app)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>Out-Degree</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{txDetail.fund_flow.metrics.out_degree}</div>
                        </div>

                        <div style={{ background: 'var(--bg-app)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>Retained Balance</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: txDetail.fund_flow.metrics.near_zero_balance_flag ? '#dc2626' : 'var(--text-primary)' }}>
                            {txDetail.fund_flow.metrics.retained_balance?.toFixed(2)} {txDetail.transaction.currency}
                          </div>
                        </div>

                        <div style={{ background: 'var(--bg-app)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>Fund Holding Time</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: txDetail.fund_flow.metrics.short_holding_flag ? '#dc2626' : 'var(--text-primary)' }}>
                            {txDetail.fund_flow.metrics.holding_minutes?.toFixed(1)} mins
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 3: COMPLIANCE & AUDIT LOGS */}
                  {detailTab === 'audit' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700 }}>
                          Transaction Audit Trail History ({txDetail.audit_history.length})
                        </h4>
                        {!isAnalyst && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            Read-Only Viewer Access Mode
                          </div>
                        )}
                      </div>

                      {txDetail.audit_history.length > 0 ? (
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                          <thead>
                            <tr style={{ background: 'var(--bg-app)', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                              <th style={{ padding: '0.5rem' }}>Timestamp</th>
                              <th style={{ padding: '0.5rem' }}>User Email</th>
                              <th style={{ padding: '0.5rem' }}>Role</th>
                              <th style={{ padding: '0.5rem' }}>Action</th>
                              <th style={{ padding: '0.5rem' }}>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {txDetail.audit_history.map((log) => (
                              <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>
                                  {new Date(log.timestamp).toLocaleString()}
                                </td>
                                <td style={{ padding: '0.5rem', fontWeight: 600 }}>{log.user_email}</td>
                                <td style={{ padding: '0.5rem' }}>{log.user_role}</td>
                                <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontWeight: 700 }}>{log.action}</td>
                                <td style={{ padding: '0.5rem' }}>
                                  <span className={`badge ${log.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}`}>
                                    {log.status}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                          No audit entries logged for this transaction yet.
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* REPORT & EXPORT MODAL */}
      {showExportModal && txDetail && txDetail.risk_report && (
        <ReportExportModal
          report={txDetail.risk_report}
          user={user}
          token={token}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
}
