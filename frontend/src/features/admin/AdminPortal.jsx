/**
 * features/admin/AdminPortal.jsx
 *
 * Top-level admin management UI. Completely separate from the regular app:
 *   - No NavRail, no DatasetProvider
 *   - Only reachable via /admin/* with a role:admin JWT
 *   - Clean data table layout — a person can manage users and data without DB access
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, LogOut, RefreshCw } from 'lucide-react';
import { useAuth } from '../../App';
import UsersTable from './UsersTable';
import UserDatasetsPanel from './UserDatasetsPanel';
import { useAdminUsers } from './useAdminApi';

export default function AdminPortal() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { users, loading, error, refresh } = useAdminUsers();
  const [selectedUser, setSelectedUser] = useState(null);

  // Load users on mount
  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleUserDeleted = async () => {
    setSelectedUser(null);
    await refresh();
  };

  const handleDatasetDeleted = async () => {
    await refresh(); // refresh user row counts
  };

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-surface-2)',
      // Apply light theme tokens for admin (readable without fighting the user's theme pref)
    }}>
      {/* ── Topbar ──────────────────────────────────────────────────────────── */}
      <div style={{
        height: 52,
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        gap: 10,
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div style={{
          width: 28, height: 28, borderRadius: 8,
          background: 'var(--accent-subtle)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Shield size={14} color="var(--accent)" />
        </div>
        <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
          Admin Portal
        </span>
        <span style={{
          fontSize: 10, fontWeight: 700, letterSpacing: 0.6,
          color: 'var(--accent)', background: 'var(--accent-subtle)',
          padding: '2px 7px', borderRadius: 5, textTransform: 'uppercase',
        }}>
          Internal
        </span>

        <div style={{ flex: 1 }} />

        <button
          onClick={refresh}
          disabled={loading}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '6px 12px', borderRadius: 7, border: '1px solid var(--border)',
            background: 'transparent', cursor: 'pointer', fontSize: 12,
            color: 'var(--text-secondary)', fontWeight: 500,
          }}
          title="Refresh"
        >
          <RefreshCw size={12} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>

        <button
          onClick={handleLogout}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '6px 12px', borderRadius: 7, border: '1px solid var(--border)',
            background: 'transparent', cursor: 'pointer', fontSize: 12,
            color: 'var(--color-delayed-text)', fontWeight: 500,
          }}
        >
          <LogOut size={12} />
          Sign out
        </button>
      </div>

      {/* ── Main content ─────────────────────────────────────────────────────── */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '28px 24px' }}>

        {/* Page header */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: -0.3 }}>
            User management
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            View all registered users, browse their datasets, and manage data without touching the database.
          </p>
        </div>

        {/* Stats strip */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          marginBottom: 24,
        }}>
          {[
            { label: 'Total users', value: loading ? '…' : users.length },
            {
              label: 'Total datasets',
              value: loading ? '…' : users.reduce((s, u) => s + u.dataset_count, 0),
            },
            {
              label: 'Total shipment rows',
              value: loading ? '…' : users.reduce((s, u) => s + u.total_shipment_rows, 0).toLocaleString(),
            },
          ].map((stat, i) => (
            <div
              key={i}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 12,
                padding: '16px 20px',
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.4, marginBottom: 8 }}>
                {stat.label}
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: -0.5 }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Users table + optional drill-in panel side by side */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: selectedUser ? '1fr 340px' : '1fr',
          gap: 16,
          alignItems: 'start',
        }}>
          <UsersTable
            users={users}
            loading={loading}
            error={error}
            selectedUserId={selectedUser?.user_id}
            onSelectUser={setSelectedUser}
            onUserDeleted={handleUserDeleted}
          />

          {selectedUser && (
            <UserDatasetsPanel
              user={selectedUser}
              onClose={() => setSelectedUser(null)}
              onDeleted={handleDatasetDeleted}
            />
          )}
        </div>
      </div>

      {/* Spinner animation */}
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
