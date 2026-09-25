import React, { useEffect, useState } from 'react';

export function AuditLogView({ token }) {
  const [logs, setLogs] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // New user form state
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('Analyst');
  const [newPassword, setNewPassword] = useState('');
  const [userMsg, setUserMsg] = useState(null);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/audit/logs?limit=50', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      const data = await res.json();
      setLogs(data.logs || []);
      setTotalCount(data.total_count || 0);
    } catch (err) {
      setError(err.message || 'Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch('/api/v1/users', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      }
    } catch {
      // Ignore user list fetch errors
    }
  };

  useEffect(() => {
    fetchAuditLogs();
    fetchUsers();
  }, [token]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setUserMsg(null);
    try {
      const res = await fetch('/api/v1/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: newEmail,
          full_name: newName,
          role: newRole,
          password: newPassword,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to create user');
      }

      setUserMsg('User created successfully!');
      setNewEmail('');
      setNewName('');
      setNewPassword('');
      fetchUsers();
      fetchAuditLogs();
    } catch (err) {
      setUserMsg(`Error: ${err.message}`);
    }
  };

  const getActionBadgeClass = (act) => {
    if (act.includes('LOGIN')) return 'badge-info';
    if (act.includes('EVALUATE') || act.includes('INGEST')) return 'badge-warning';
    if (act.includes('REPORT') || act.includes('STR')) return 'badge-danger';
    return 'badge-success';
  };

  const getStatusColor = (st) => {
    if (st === 'SUCCESS') return 'var(--color-success)';
    if (st === 'UNAUTHORIZED') return 'var(--color-danger)';
    return 'var(--color-warning)';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Control Header */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div className="card-title">Security & Audit Log Center</div>
            <div className="card-subtitle">
              Tamper-evident, append-only security log records and RBAC user management (Admin Access Only)
            </div>
          </div>
          <button
            onClick={fetchAuditLogs}
            className="btn"
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.82rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-color)' }}
          >
            Refresh Logs
          </button>
        </div>
      </div>

      {loading && <div className="state-box">Loading audit logs repository...</div>}
      {error && <div className="state-box error-box">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {/* User Management Panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card-title" style={{ fontSize: '1.05rem' }}>Active RBAC Users</div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '180px', overflowY: 'auto' }}>
            {users.map((u) => (
              <div key={u.user_id} style={{ padding: '0.6rem 0.75rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>{u.full_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.email}</div>
                </div>
                <span className={`badge ${u.role === 'Admin' ? 'badge-danger' : u.role === 'Analyst' ? 'badge-warning' : 'badge-info'}`} style={{ fontSize: '0.7rem' }}>
                  {u.role}
                </span>
              </div>
            ))}
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Create New User</div>
            {userMsg && <div style={{ fontSize: '0.78rem', marginBottom: '0.5rem', color: userMsg.startsWith('Error') ? 'var(--color-danger)' : 'var(--color-success)' }}>{userMsg}</div>}
            
            <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <input
                type="text"
                placeholder="Full Name"
                required
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                style={{ padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.8rem', backgroundColor: 'var(--bg-app)', color: 'var(--text-primary)' }}
              />
              <input
                type="email"
                placeholder="Email Address"
                required
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                style={{ padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.8rem', backgroundColor: 'var(--bg-app)', color: 'var(--text-primary)' }}
              />
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  style={{ flex: 1, padding: '0.4rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.8rem', backgroundColor: 'var(--bg-app)', color: 'var(--text-primary)' }}
                >
                  <option value="Viewer">Viewer</option>
                  <option value="Analyst">Analyst</option>
                  <option value="Admin">Admin</option>
                </select>
                <input
                  type="password"
                  placeholder="Password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={{ flex: 1, padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.8rem', backgroundColor: 'var(--bg-app)', color: 'var(--text-primary)' }}
                />
              </div>
              <button type="submit" style={{ padding: '0.45rem', backgroundColor: 'var(--primary-color)', color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer' }}>
                Create User
              </button>
            </form>
          </div>
        </div>

        {/* Audit Log Table */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="card-title" style={{ fontSize: '1.05rem' }}>Append-Only Audit Log Records</div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Total Records: <strong>{totalCount}</strong></span>
          </div>

          <div style={{ overflowX: 'auto', maxHeight: '420px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border-color)', backgroundColor: 'var(--bg-app)' }}>
                  <th style={{ padding: '0.5rem' }}>ID</th>
                  <th style={{ padding: '0.5rem' }}>Timestamp</th>
                  <th style={{ padding: '0.5rem' }}>User Email</th>
                  <th style={{ padding: '0.5rem' }}>Role</th>
                  <th style={{ padding: '0.5rem' }}>Action</th>
                  <th style={{ padding: '0.5rem' }}>Tx ID</th>
                  <th style={{ padding: '0.5rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.45rem 0.5rem', fontWeight: 600 }}>#{log.id}</td>
                    <td style={{ padding: '0.45rem 0.5rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '0.45rem 0.5rem', fontWeight: 600 }}>{log.user_email}</td>
                    <td style={{ padding: '0.45rem 0.5rem' }}>
                      <span className="badge" style={{ fontSize: '0.68rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-color)' }}>
                        {log.user_role}
                      </span>
                    </td>
                    <td style={{ padding: '0.45rem 0.5rem' }}>
                      <span className={`badge ${getActionBadgeClass(log.action)}`} style={{ fontSize: '0.68rem' }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ padding: '0.45rem 0.5rem', fontFamily: 'monospace' }}>
                      {log.transaction_id || '—'}
                    </td>
                    <td style={{ padding: '0.45rem 0.5rem', fontWeight: 700, color: getStatusColor(log.status) }}>
                      {log.status}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
