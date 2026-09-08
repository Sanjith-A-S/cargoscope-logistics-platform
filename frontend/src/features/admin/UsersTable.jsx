/**
 * features/admin/UsersTable.jsx
 *
 * Table of all registered users/orgs. Supports search, click-to-drill-in,
 * and per-row delete with confirmation modal.
 */
import React, { useState } from 'react';
import { Search, Trash2, ChevronRight, AlertTriangle, Users } from 'lucide-react';
import { apiService } from '../../services/apiService';

// ─── Confirm modal ────────────────────────────────────────────────────────────
function ConfirmDeleteUserModal({ user, onConfirm, onCancel, loading }) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 300,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={e => { if (e.target === e.currentTarget) onCancel(); }}
    >
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 14,
        padding: '24px 28px',
        maxWidth: 440, width: '90%',
        boxShadow: '0 8px 32px rgba(0,0,0,0.22)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <AlertTriangle size={18} color="var(--color-delayed-text)" />
          <strong style={{ fontSize: 15, color: 'var(--text-primary)' }}>Delete user?</strong>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 20 }}>
          This will permanently delete user <strong style={{ color: 'var(--text-primary)' }}>{user.email}</strong>,
          their organisation <strong style={{ color: 'var(--text-primary)' }}>"{user.org_name}"</strong>,
          and all <strong style={{ color: 'var(--text-primary)' }}>
            {user.dataset_count} dataset{user.dataset_count !== 1 ? 's' : ''}
          </strong> with{' '}
          <strong style={{ color: 'var(--text-primary)' }}>
            {(user.total_shipment_rows || 0).toLocaleString()} shipment rows
          </strong>. This cannot be undone.
        </p>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            disabled={loading}
            style={{
              padding: '8px 16px', borderRadius: 7, border: '1px solid var(--border)',
              background: 'transparent', cursor: 'pointer', fontSize: 13,
              color: 'var(--text-primary)', fontWeight: 500,
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            style={{
              padding: '8px 16px', borderRadius: 7, border: 'none',
              background: 'var(--color-delayed-text)', cursor: 'pointer', fontSize: 13,
              color: '#fff', fontWeight: 600, opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Deleting…' : 'Delete user & all data'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Users table ──────────────────────────────────────────────────────────────
export default function UsersTable({ users, loading, error, onSelectUser, selectedUserId, onUserDeleted }) {
  const [search, setSearch] = useState('');
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const filtered = users.filter(u =>
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    u.org_name.toLowerCase().includes(search.toLowerCase())
  );

  const handleDeleteConfirm = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await apiService.adminDeleteUser(pendingDelete.user_id);
      setPendingDelete(null);
      if (onUserDeleted) onUserDeleted();
    } catch (e) {
      setDeleteError(e?.response?.data?.detail || 'Delete failed.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 14,
      overflow: 'hidden',
    }}>
      {pendingDelete && (
        <ConfirmDeleteUserModal
          user={pendingDelete}
          onConfirm={handleDeleteConfirm}
          onCancel={() => { setPendingDelete(null); setDeleteError(null); }}
          loading={deleting}
        />
      )}

      {/* Toolbar */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <Users size={15} color="var(--accent)" />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', flex: 1 }}>
          Users ({filtered.length})
        </span>
        <div style={{ position: 'relative', width: 220 }}>
          <Search size={13} style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by email or org…"
            style={{
              width: '100%', paddingLeft: 28, paddingRight: 10,
              height: 32, borderRadius: 7, border: '1px solid var(--border)',
              background: 'var(--bg-surface-2)', color: 'var(--text-primary)',
              fontSize: 12, outline: 'none', boxSizing: 'border-box',
            }}
          />
        </div>
      </div>

      {deleteError && (
        <div style={{ fontSize: 12, color: 'var(--color-delayed-text)', padding: '8px 16px' }}>
          {deleteError}
        </div>
      )}

      {/* Table header */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 140px 90px 90px 80px 50px',
        padding: '8px 16px',
        background: 'var(--bg-surface-2)',
        borderBottom: '1px solid var(--border)',
      }}>
        {['Email / Org', 'Signed up', 'Datasets', 'Shipments', '', ''].map((h, i) => (
          <span key={i} style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.4 }}>
            {h}
          </span>
        ))}
      </div>

      {/* Rows */}
      <div style={{ maxHeight: 460, overflowY: 'auto' }}>
        {loading && (
          <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
            Loading users…
          </div>
        )}
        {!loading && error && (
          <div style={{ padding: '24px 16px', fontSize: 13, color: 'var(--color-delayed-text)' }}>{error}</div>
        )}
        {!loading && !error && filtered.length === 0 && (
          <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
            {search ? 'No users match your search.' : 'No registered users yet.'}
          </div>
        )}
        {!loading && filtered.map((user, i) => {
          const isSelected = user.user_id === selectedUserId;
          return (
            <div
              key={user.user_id}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 140px 90px 90px 80px 50px',
                padding: '10px 16px',
                alignItems: 'center',
                borderBottom: i < filtered.length - 1 ? '1px solid var(--border)' : 'none',
                background: isSelected ? 'var(--accent-subtle)' : (i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-surface-2)'),
                cursor: 'pointer',
                transition: 'background 0.1s',
              }}
              onClick={() => onSelectUser(isSelected ? null : user)}
              onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'var(--bg-surface-2)'; }}
              onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-surface-2)'; }}
            >
              {/* Email + Org */}
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: isSelected ? 'var(--accent)' : 'var(--text-primary)' }}>
                  {user.email}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{user.org_name}</div>
              </div>

              {/* Signup date */}
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {new Date(user.signup_date).toLocaleDateString()}
              </span>

              {/* Dataset count */}
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                {user.dataset_count}
              </span>

              {/* Shipment rows */}
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {(user.total_shipment_rows || 0).toLocaleString()}
              </span>

              {/* View datasets arrow */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--accent)', fontSize: 11, fontWeight: 600 }}>
                <ChevronRight size={13} />
                {isSelected ? 'Close' : 'Datasets'}
              </div>

              {/* Delete */}
              <button
                onClick={e => { e.stopPropagation(); setPendingDelete(user); }}
                title="Delete user"
                style={{
                  width: 28, height: 28, borderRadius: 7, border: '1px solid var(--border)',
                  background: 'transparent', cursor: 'pointer', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)',
                }}
                onMouseEnter={e => {
                  e.stopPropagation();
                  e.currentTarget.style.background = 'var(--color-delayed-bg)';
                  e.currentTarget.style.color = 'var(--color-delayed-text)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-muted)';
                }}
              >
                <Trash2 size={12} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
