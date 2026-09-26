import React, { useState } from 'react';

export function ReportExportModal({ report, onClose }) {
  const [activeTab, setActiveTab] = useState('report');
  const [copied, setCopied] = useState(false);

  if (!report) return null;

  const hasStr = report.str_draft !== null && report.str_draft !== undefined;

  const handleCopyStr = () => {
    if (report.str_draft?.narrative) {
      navigator.clipboard.writeText(report.str_draft.narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = (format) => {
    const url = `/api/v1/reports/${report.transaction_id}/download?format=${format}`;
    window.open(url, '_blank');
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '850px',
          maxHeight: '90vh',
          overflowY: 'auto',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
          <div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Risk Assessment Report & Compliance Export
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Transaction ID: <strong>{report.transaction_id}</strong> | Report Ref: <strong>{report.report_id}</strong>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.25rem',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              fontWeight: 700,
            }}
          >
            &times;
          </button>
        </div>

        {/* Modal Controls & Export Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setActiveTab('report')}
              style={{
                padding: '0.45rem 0.9rem',
                backgroundColor: activeTab === 'report' ? 'var(--primary-color)' : 'var(--bg-app)',
                color: activeTab === 'report' ? '#ffffff' : 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                fontSize: '0.82rem',
                cursor: 'pointer',
              }}
            >
              Full Risk Report
            </button>
            <button
              onClick={() => setActiveTab('str')}
              disabled={!hasStr}
              style={{
                padding: '0.45rem 0.9rem',
                backgroundColor: activeTab === 'str' ? 'var(--primary-color)' : 'var(--bg-app)',
                color: activeTab === 'str' ? '#ffffff' : hasStr ? 'var(--text-primary)' : 'var(--text-muted)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                fontSize: '0.82rem',
                cursor: hasStr ? 'pointer' : 'not-allowed',
                opacity: hasStr ? 1 : 0.6,
              }}
            >
              STR Regulatory Draft {hasStr ? ' (Draft Generated)' : ' (Not Required)'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '0.4rem' }}>
            <button
              onClick={() => handleDownload('json')}
              className="btn"
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-color)' }}
            >
              JSON
            </button>
            <button
              onClick={() => handleDownload('csv')}
              className="btn"
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-color)' }}
            >
              CSV
            </button>
            <button
              onClick={() => handleDownload('html')}
              className="btn"
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-color)' }}
            >
              HTML Report
            </button>
            <button
              onClick={() => handleDownload('pdf')}
              className="btn"
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem', backgroundColor: 'var(--primary-color)', color: '#fff' }}
            >
              PDF Report
            </button>
          </div>
        </div>

        {/* Modal Tab Content */}
        {activeTab === 'report' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.85rem' }}>
            {/* Overview Metric Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>SCORE & BAND</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {report.consolidated_score.toFixed(0)} / 100 ({report.risk_band})
                </div>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>RECOMMENDED ACTION</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {report.recommended_action}
                </div>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>STR FILING STATUS</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: hasStr ? 'var(--color-danger)' : 'var(--color-success)' }}>
                  {report.str_status}
                </div>
              </div>
            </div>

            {/* Parties & Amounts Table */}
            <div style={{ padding: '0.85rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Subject Identifiers & Details</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.82rem' }}>
                <div>Sender / Account ID: <strong>{report.account_id}</strong></div>
                <div>Recipient / Beneficiary ID: <strong>{report.recipient_id}</strong></div>
                <div>Amount: <strong>{report.amount.toFixed(2)} {report.currency}</strong></div>
                <div>Channel / Method: <strong>{report.channel} / {report.payment_method}</strong></div>
              </div>
            </div>

            {/* Explanation Box */}
            <div style={{ padding: '0.85rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--primary-color)' }}>
              <strong>Deterministic Explanation:</strong> {report.explanation}
            </div>

            {/* Triggered Signals */}
            {report.triggered_signals && report.triggered_signals.length > 0 && (
              <div>
                <div style={{ fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Triggered Risk Factors</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {report.triggered_signals.map((f) => (
                    <div key={f.signal_id} style={{ padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                      <span className="badge" style={{ backgroundColor: 'var(--primary-color)', color: '#fff', marginRight: '0.5rem' }}>{f.signal_id}</span>
                      <strong>{f.name}:</strong> {f.explanation}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'str' && hasStr && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="badge badge-danger" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
                STR DRAFT (UNFILED)
              </span>
              <button
                onClick={handleCopyStr}
                style={{
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.8rem',
                  backgroundColor: copied ? 'var(--color-success)' : 'var(--bg-app)',
                  color: copied ? '#fff' : 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                {copied ? 'Copied to Clipboard!' : 'Copy Narrative Text'}
              </button>
            </div>

            <div style={{ padding: '0.75rem', backgroundColor: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 'var(--radius-sm)', fontSize: '0.82rem', color: '#991b1b' }}>
              <strong>Notice:</strong> {report.str_draft.regulatory_notes}
            </div>

            <pre
              style={{
                padding: '1rem',
                backgroundColor: 'var(--bg-app)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '0.8rem',
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.45,
                color: 'var(--text-primary)',
                maxHeight: '350px',
                overflowY: 'auto',
              }}
            >
              {report.str_draft.narrative}
            </pre>
          </div>
        )}

        {/* Modal Footer */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
          <button
            onClick={onClose}
            className="btn"
            style={{ padding: '0.45rem 1.25rem', fontSize: '0.85rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-color)' }}
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
}
