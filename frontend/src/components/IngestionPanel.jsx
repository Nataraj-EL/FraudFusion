import React, { useEffect, useState, useRef } from 'react';

export function IngestionPanel({ token }) {
  const [activeTab, setActiveTab] = useState('batch'); // 'batch' | 'statement'

  // Batch File Ingestion State
  const [file, setFile] = useState(null);
  const [sourceType, setSourceType] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [recentBatches, setRecentBatches] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Statement OCR Ingestion State
  const [stmtFile, setStmtFile] = useState(null);
  const [stmtUploading, setStmtUploading] = useState(false);
  const [stmtError, setStmtError] = useState(null);
  const [stmtResult, setStmtResult] = useState(null);

  const batchFileInputRef = useRef(null);
  const stmtFileInputRef = useRef(null);

  const fetchBatches = async () => {
    setLoadingHistory(true);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch('/api/v1/ingest/batches?limit=10', { headers });
      if (res.ok) {
        const data = await res.json();
        setRecentBatches(data);
      }
    } catch (err) {
      console.error('Failed to load batch history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadError('Please select a JSON/CSV file to upload');
      return;
    }

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);
    if (sourceType) {
      formData.append('source_type', sourceType);
    }

    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch('/api/v1/ingest/upload', {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || errData.message || `Upload failed with status ${res.status}`);
      }

      const result = await res.json();
      setLastResult(result);
      setFile(null);
      if (batchFileInputRef.current) batchFileInputRef.current.value = '';

      fetchBatches();
    } catch (err) {
      setUploadError(err.message || 'An unexpected error occurred during upload');
    } finally {
      setUploading(false);
    }
  };

  const handleStmtUpload = async (e) => {
    e.preventDefault();
    if (!stmtFile) {
      setStmtError('Please select a PDF or Image bank statement');
      return;
    }

    setStmtUploading(true);
    setStmtError(null);

    const formData = new FormData();
    formData.append('file', stmtFile);

    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch('/api/v1/ingest/statement', {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || errData.message || `Statement OCR failed (${res.status})`);
      }

      const result = await res.json();
      setStmtResult(result);
      setStmtFile(null);
      if (stmtFileInputRef.current) stmtFileInputRef.current.value = '';

      fetchBatches();
    } catch (err) {
      setStmtError(err.message || 'Error processing statement file');
    } finally {
      setStmtUploading(false);
    }
  };

  const getConfidenceBadge = (level) => {
    switch (level) {
      case 'HIGH':
        return 'badge-success';
      case 'MEDIUM':
        return 'badge-info';
      case 'LOW':
        return 'badge-warning';
      default:
        return 'badge-danger';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Sub-Tab Navigation Header */}
      <div className="card" style={{ padding: '0 1.25rem' }}>
        <div style={{ display: 'flex', gap: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setActiveTab('batch')}
            className={`sub-tab-btn ${activeTab === 'batch' ? 'active' : ''}`}
          >
            Ingest Data Batch (JSON / CSV)
          </button>
          <button
            onClick={() => setActiveTab('statement')}
            className={`sub-tab-btn ${activeTab === 'statement' ? 'active' : ''}`}
          >
            Bank Statement OCR Ingestion
          </button>
        </div>
      </div>

      {/* SUB-TAB 1: Batch File Ingestion */}
      {activeTab === 'batch' && (
        <div className="card">
          <div className="card-title">Ingest Data Batch (JSON / CSV)</div>
          <div className="card-subtitle">
            Upload Adaptive Friction (JSON), Fund Flow (CSV), or Phishing (JSON) batch files
          </div>

          <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginTop: '1rem' }}>
            <div
              className={`upload-dropzone ${file ? 'has-file' : ''}`}
              onClick={() => batchFileInputRef.current?.click()}
            >
              <input
                ref={batchFileInputRef}
                id="ingest-file-input"
                type="file"
                accept=".json,.csv"
                onChange={handleFileChange}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              {file ? (
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                    Selected File: {file.name}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    {(file.size / 1024).toFixed(1)} KB — Click to change file
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                    Drag and drop your batch file here, or click to browse
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.8rem' }}>
                    Supports JSON (Adaptive Friction, Phishing) & CSV (Fund Flow)
                  </div>
                  <button type="button" className="btn-browse">
                    Browse Batch File
                  </button>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ width: '260px' }}>
                <label
                  htmlFor="source-type-select"
                  style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}
                >
                  Source Domain
                </label>
                <select
                  id="source-type-select"
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  disabled={uploading}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-surface)',
                    fontSize: '0.85rem',
                    color: 'var(--text-primary)',
                  }}
                >
                  <option value="">Auto Detect (Default)</option>
                  <option value="ADAPTIVE_FRICTION">Adaptive Friction (JSON)</option>
                  <option value="FUND_FLOW">Fund Flow (CSV)</option>
                  <option value="PHISHING">Phishing Event (JSON)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={uploading || !file}
                style={{
                  padding: '0.6rem 1.5rem',
                  backgroundColor: uploading || !file ? 'var(--border-strong)' : 'var(--primary-color)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: 600,
                  cursor: uploading || !file ? 'not-allowed' : 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                {uploading ? 'Processing & Validating...' : 'Upload Batch'}
              </button>
            </div>

            {uploadError && (
              <div className="state-box error-box" style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.85rem' }}>
                <strong>Upload Failed:</strong> {uploadError}
              </div>
            )}
          </form>
        </div>
      )}

      {/* SUB-TAB 2: Statement OCR Ingestion */}
      {activeTab === 'statement' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <div className="card-title">Bank Statement OCR Ingestion (Optional)</div>
              <div className="card-subtitle">
                Extract transaction data from PDF or Image statements using PyMuPDF and Tesseract OCR.
              </div>
            </div>
            <span className="badge badge-info" style={{ fontSize: '0.75rem' }}>
              PDF & Image OCR
            </span>
          </div>

          <form onSubmit={handleStmtUpload} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div
              className={`upload-dropzone ${stmtFile ? 'has-file' : ''}`}
              onClick={() => stmtFileInputRef.current?.click()}
            >
              <input
                ref={stmtFileInputRef}
                id="stmt-file-input"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setStmtFile(e.target.files[0]);
                    setStmtError(null);
                  }
                }}
                disabled={stmtUploading}
                style={{ display: 'none' }}
              />
              {stmtFile ? (
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                    Selected Statement: {stmtFile.name}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    {(stmtFile.size / 1024).toFixed(1)} KB — Click to change statement file
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                    Drag and drop your bank statement file here, or click to browse
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.8rem' }}>
                    Supports PDF & Images (PNG, JPG, TIFF) via PyMuPDF + Tesseract OCR
                  </div>
                  <button type="button" className="btn-browse" style={{ backgroundColor: '#8b5cf6' }}>
                    Browse Statement File
                  </button>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="submit"
                disabled={stmtUploading || !stmtFile}
                style={{
                  padding: '0.6rem 1.5rem',
                  backgroundColor: stmtUploading || !stmtFile ? 'var(--border-strong)' : '#8b5cf6',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: 600,
                  cursor: stmtUploading || !stmtFile ? 'not-allowed' : 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                {stmtUploading ? 'Extracting Text & OCR...' : 'Analyze Statement (OCR)'}
              </button>
            </div>

            {stmtError && (
              <div className="state-box error-box" style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.85rem' }}>
                <strong>Statement Ingestion Error:</strong> {stmtError}
              </div>
            )}
          </form>

          {/* OCR Result Preview */}
          {stmtResult && (
            <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <div>
                  <strong style={{ fontSize: '0.9rem' }}>OCR Extraction Result: {stmtResult.filename}</strong>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Batch ID: <code className="font-mono">{stmtResult.batch_id}</code> | OCR Engine: <strong>{stmtResult.ocr_engine_used}</strong>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span className="badge badge-success">{stmtResult.valid_count} Valid</span>
                  <span className={`badge ${stmtResult.invalid_count > 0 ? 'badge-danger' : 'badge-info'}`}>{stmtResult.invalid_count} Invalid</span>
                </div>
              </div>

              {/* Extracted Transactions Table */}
              {stmtResult.extracted_transactions && stmtResult.extracted_transactions.length > 0 ? (
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Page</th>
                        <th>Ref / Tx ID</th>
                        <th>Sender Account</th>
                        <th>Recipient</th>
                        <th>Amount</th>
                        <th>Confidence</th>
                        <th>Status & Validation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stmtResult.extracted_transactions.map((tx, idx) => (
                        <tr key={idx}>
                          <td>Page {tx.page_number}</td>
                          <td><code className="font-mono">{tx.transaction_id || 'N/A'}</code></td>
                          <td>{tx.account_id || '—'}</td>
                          <td>{tx.recipient_id || '—'}</td>
                          <td>
                            {tx.amount !== null && tx.amount !== undefined ? (
                              <strong>{tx.amount.toFixed(2)} {tx.currency}</strong>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td>
                            <span className={`badge ${getConfidenceBadge(tx.confidence_level)}`}>
                              {tx.confidence_level} ({(tx.confidence_score * 100).toFixed(0)}%)
                            </span>
                          </td>
                          <td style={{ fontSize: '0.78rem' }}>
                            {tx.is_valid ? (
                              <span style={{ color: '#16a34a', fontWeight: 600 }}>Normalized</span>
                            ) : (
                              <span style={{ color: '#dc2626' }}>
                                Error: {tx.validation_errors.join('; ')}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="state-box">No structured transaction rows identified in statement file.</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Latest Ingestion Result */}
      {lastResult && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <div className="card-title">Batch Summary Result</div>
              <div className="card-subtitle">
                Batch ID: <code className="font-mono">{lastResult.batch.batch_id}</code> | File: {lastResult.batch.filename}
              </div>
            </div>
            <span className="badge badge-info">{lastResult.batch.source_type}</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.25rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>TOTAL RECORDS</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{lastResult.batch.total_records}</div>
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-success-subtle)', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-success)' }}>ACCEPTED</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-success)' }}>
                {lastResult.batch.accepted_count}
              </div>
            </div>
            <div
              style={{
                padding: '0.75rem',
                background: lastResult.batch.rejected_count > 0 ? 'var(--bg-danger-subtle)' : 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: '0.75rem',
                  color: lastResult.batch.rejected_count > 0 ? 'var(--color-danger)' : 'var(--text-muted)',
                }}
              >
                REJECTED
              </div>
              <div
                style={{
                  fontSize: '1.25rem',
                  fontWeight: 700,
                  color: lastResult.batch.rejected_count > 0 ? 'var(--color-danger)' : 'var(--text-primary)',
                }}
              >
                {lastResult.batch.rejected_count}
              </div>
            </div>
          </div>

          {/* Validation Errors Table */}
          {lastResult.validation_errors && lastResult.validation_errors.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--color-danger)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Structured Rejection & Validation Errors ({lastResult.validation_errors.length})
              </h4>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Index</th>
                    <th>Ref ID</th>
                    <th>Failed Field</th>
                    <th>Validation Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {lastResult.validation_errors.map((err, i) => (
                    <tr key={i}>
                      <td><code className="font-mono">#{err.record_index}</code></td>
                      <td><code className="font-mono">{err.reference_id || 'N/A'}</code></td>
                      <td><span className="badge badge-warning">{err.field}</span></td>
                      <td style={{ color: 'var(--color-danger)', fontSize: '0.8rem' }}>{err.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Accepted Transactions Table */}
          {lastResult.accepted_records && lastResult.accepted_records.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Normalized Canonical Records ({lastResult.accepted_records.length})
              </h4>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Tx ID</th>
                    <th>Account</th>
                    <th>Recipient</th>
                    <th>Amount</th>
                    <th>Channel</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {lastResult.accepted_records.map((tx) => (
                    <tr key={tx.transaction_id}>
                      <td><code className="font-mono">{tx.transaction_id}</code></td>
                      <td>{tx.account_id}</td>
                      <td>{tx.recipient_id}</td>
                      <td><strong>{tx.amount.toFixed(2)} {tx.currency}</strong></td>
                      <td><span className="badge badge-info">{tx.channel}</span></td>
                      <td><span className="badge badge-success">{tx.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Ingestion Batch History */}
      <div className="card">
        <div className="card-title">Recent Ingestion Batches</div>
        <div className="card-subtitle">SQLite audit history log of uploaded signal files</div>

        {loadingHistory && <div className="state-box">Loading audit history...</div>}

        {!loadingHistory && recentBatches.length === 0 && (
          <div className="state-box">No ingestion batches recorded yet. Upload a file above to start.</div>
        )}

        {!loadingHistory && recentBatches.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Batch ID</th>
                <th>Source Domain</th>
                <th>Filename</th>
                <th>Total</th>
                <th>Accepted</th>
                <th>Rejected</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {recentBatches.map((b) => (
                <tr key={b.batch_id}>
                  <td><code className="font-mono">{b.batch_id}</code></td>
                  <td><span className="badge badge-info">{b.source_type}</span></td>
                  <td>{b.filename}</td>
                  <td>{b.total_records}</td>
                  <td><span className="badge badge-success">{b.accepted_count}</span></td>
                  <td>
                    <span className={`badge ${b.rejected_count > 0 ? 'badge-danger' : 'badge-info'}`}>
                      {b.rejected_count}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                    {new Date(b.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default IngestionPanel;
