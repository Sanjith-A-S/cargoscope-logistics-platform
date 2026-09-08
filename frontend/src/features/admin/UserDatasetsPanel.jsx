/**
 * features/admin/UserDatasetsPanel.jsx
 *
 * Drill-in panel: shows a user's datasets with row count, date range,
 * and a delete action per dataset.
 */
import React, { useEffect, useState } from 'react';
import { Trash2, AlertTriangle, Database, X } from 'lucide-react';
import { apiService } from '../../services/apiService';
import { useAdminUserDatasets } from './useAdminApi';

// ─── Confirm modal ────────────────────────────────────────────────────────────
function ConfirmDeleteModal({ title, body, onConfirm, onCancel, loading }) {
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
        maxWidth: 400, width: '90%',
        boxShadow: '0 8px 32px rgba(0,0,0,0.22)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <AlertTriangle size={18} color="var(--color-delayed-text)" />
          <strong style={{ fontSize: 15, color: 'var(--text-primary)' }}>{title}</strong>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 20 }}>
          {body}
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
            {loading ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Panel ────────────────────────────────────────────────────────────────────
export default function UserDatasetsPanel({ user, onClose, onDeleted }) {
  const { datasets, loading, error, refresh } = useAdminUserDatasets(user?.user_id);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  useEffect(() => {
    if (user) refresh();
  }, [user, refresh]);

  const handleDeleteDataset = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await apiService.adminDeleteDataset(pendingDelete.dataset_id);
      setPendingDelete(null);
      await refresh();
      if (onDeleted) onDeleted();
    } catch (e) {
      setDeleteError(e?.response?.data?.detail || 'Delete failed.');
    } finally {
      setDeleting(false);
    }
  };

  if (!user) return null;

  return (
    <>
      {pendingDelete && (
        <ConfirmDeleteModal
          title="Delete dataset?"
          body={
            `Permanently delete "${pendingDelete.name}" with ` +
            `${(pendingDelete.source_row_count || 0).toLocaleString()} shipment rows? ` +
            `This cannot be undone.`
          }
          onConfirm={handleDeleteDataset}
          onCancel={() => { setPendingDelete(null); setDeleteError(null); }}
          loading={deleting}
        />
      )}

      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 14,
        padding: '20px 24px',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
              {user.email}
            </h3>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {user.org_name} · {datasets.length} dataset{datasets.length !== 1 ? 's' : ''}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              width: 28, height: 28, borderRadius: 7, border: '1px solid var(--border)',
              background: 'transparent', cursor: 'pointer', display: 'flex',
              alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)',
            }}
          >
            <X size={14} />
          </button>
        </div>

        {deleteError && (
          <div style={{ fontSize: 12, color: 'var(--color-delayed-text)', marginBottom: 10 }}>
            {deleteError}
          </div>
        )}

        {loading && (
          <div style={{ fontSize: 13, color: 'var(--text-muted)', padding: '20px 0', textAlign: 'center' }}>
            Loading datasets…
          </div>
        )}

        {!loading && error && (
          <div style={{ fontSize: 13, color: 'var(--color-delayed-text)' }}>{error}</div>
        )}

        {!loading && !error && datasets.length === 0 && (
          <div style={{ fontSize: 13, color: 'var(--text-muted)', padding: '20px 0', textAlign: 'center' }}>
            No datasets yet.
          </div>
        )}

        {!loading && datasets.map(ds => (
          <div
            key={ds.dataset_id}
            style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 12px', borderRadius: 8, marginBottom: 6,
              background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <Database size={14} color="var(--accent)" style={{ marginTop: 2, flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {ds.name}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  {(ds.source_row_count || 0).toLocaleString()} rows
                  {ds.date_range_start && ` · ${ds.date_range_start.slice(0, 10)} → ${ds.date_range_end?.slice(0, 10)}`}
                </div>
              </div>
            </div>
            <button
              onClick={() => setPendingDelete(ds)}
              title="Delete dataset"
              style={{
                width: 28, height: 28, borderRadius: 7, border: '1px solid var(--border)',
                background: 'transparent', cursor: 'pointer', display: 'flex',
                alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)',
                flexShrink: 0,
              }}
              onMouseEnter={e => {
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
        ))}
      </div>
    </>
  );
}
