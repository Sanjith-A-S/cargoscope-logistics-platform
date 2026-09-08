import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Upload, Trash2, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/apiService';
import { useDataset } from '../features/datasets/DatasetContext';

// ─── Info row ─────────────────────────────────────────────────────────────────
const InfoRow = ({ label, value, valueStyle }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '11px 0',
    borderBottom: '1px solid var(--border)',
    gap: 16,
  }}>
    <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{label}</span>
    <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', ...valueStyle }}>{value}</span>
  </div>
);

// ─── Delete confirmation modal ────────────────────────────────────────────────
function DeleteDatasetModal({ dataset, onConfirm, onCancel, loading }) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(0,0,0,0.45)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={e => { if (e.target === e.currentTarget) onCancel(); }}
    >
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 16,
        padding: '28px 32px',
        maxWidth: 420, width: '100%',
        boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <div style={{
            width: 36, height: 36, borderRadius: '50%',
            background: 'var(--color-delayed-bg)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <AlertTriangle size={18} color="var(--color-delayed-text)" />
          </div>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
            Delete dataset?
          </h2>
        </div>

        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 8 }}>
          This will permanently delete{' '}
          <strong style={{ color: 'var(--text-primary)' }}>"{dataset.name}"</strong> and all{' '}
          <strong style={{ color: 'var(--text-primary)' }}>
            {(dataset.source_row_count || 0).toLocaleString()} shipment rows
          </strong>{' '}
          associated with it. This cannot be undone.
        </p>

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 24 }}>
          <button
            onClick={onCancel}
            disabled={loading}
            style={{
              padding: '9px 18px', borderRadius: 8, border: '1px solid var(--border)',
              background: 'transparent', cursor: 'pointer',
              fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            style={{
              padding: '9px 18px', borderRadius: 8, border: 'none',
              background: 'var(--color-delayed-text)', cursor: loading ? 'wait' : 'pointer',
              fontSize: 13, fontWeight: 600, color: '#fff',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Deleting…' : 'Delete permanently'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Account panel ────────────────────────────────────────────────────────────
function AccountPanel() {
  const [me, setMe] = useState(null);

  useEffect(() => {
    apiService.getMe().then(r => setMe(r.data)).catch(() => {});
  }, []);

  if (!me) return null;

  return (
    <section>
      <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
        Account
      </h3>
      <InfoRow label="Email"           value={me.email} />
      <InfoRow label="Organisation"    value={me.org_name} />
      <InfoRow label="Organisation ID" value={`#${me.org_id}`} valueStyle={{ fontFamily: 'ui-monospace, monospace', fontSize: 12 }} />
    </section>
  );
}

// ─── Dataset panel ────────────────────────────────────────────────────────────
function DatasetPanel() {
  const { datasets, activeDataset, reload } = useDataset();
  const [pendingDelete, setPendingDelete] = useState(null); // dataset object to confirm
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const handleDeleteConfirm = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await apiService.deleteDataset(pendingDelete.id);
      setPendingDelete(null);
      await reload(); // DatasetContext auto-sets activeDataset = null when list empties
    } catch (e) {
      setDeleteError(e?.response?.data?.detail || 'Delete failed. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <section>
      {pendingDelete && (
        <DeleteDatasetModal
          dataset={pendingDelete}
          onConfirm={handleDeleteConfirm}
          onCancel={() => { setPendingDelete(null); setDeleteError(null); }}
          loading={deleting}
        />
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Datasets
        </h3>
        <Link
          to="/upload"
          style={{
            display: 'flex', alignItems: 'center', gap: 5,
            fontSize: 12, fontWeight: 500, color: 'var(--accent)',
            textDecoration: 'none',
          }}
        >
          <Upload size={13} /> Upload new
        </Link>
      </div>

      {deleteError && (
        <div style={{ fontSize: 12, color: 'var(--color-delayed-text)', marginBottom: 10 }}>
          {deleteError}
        </div>
      )}

      {datasets.length === 0 ? (
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          No datasets yet —{' '}
          <Link to="/upload" style={{ color: 'var(--accent)' }}>upload a CSV</Link>
          {' '}to create one.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {datasets.map(ds => (
            <div
              key={ds.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '10px 14px',
                borderRadius: 8,
                background: ds.id === activeDataset?.id ? 'var(--accent-subtle)' : 'var(--bg-surface-2)',
                border: `1px solid ${ds.id === activeDataset?.id ? 'var(--accent)' : 'var(--border)'}`,
              }}
            >
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{ds.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  {ds.source_row_count?.toLocaleString() ?? 0} rows
                  {ds.date_range_start && ` · ${ds.date_range_start.slice(0, 10)} → ${ds.date_range_end?.slice(0, 10)}`}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {ds.id === activeDataset?.id && (
                  <span style={{
                    fontSize: 11, fontWeight: 600, color: 'var(--accent)',
                    background: 'var(--accent-subtle)', padding: '2px 8px', borderRadius: 10,
                  }}>
                    Active
                  </span>
                )}
                <button
                  onClick={() => setPendingDelete(ds)}
                  title="Delete dataset"
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    width: 30, height: 30, borderRadius: 7,
                    border: '1px solid var(--border)',
                    background: 'transparent',
                    cursor: 'pointer',
                    color: 'var(--text-muted)',
                    transition: 'background 0.15s, color 0.15s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'var(--color-delayed-bg)';
                    e.currentTarget.style.color = 'var(--color-delayed-text)';
                    e.currentTarget.style.borderColor = 'var(--color-delayed-text)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--text-muted)';
                    e.currentTarget.style.borderColor = 'var(--border)';
                  }}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

// ─── Settings ─────────────────────────────────────────────────────────────────
export default function SettingsScreen() {
  return (
    <div style={{ maxWidth: 1200, paddingBottom: 60 }}>
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Account, datasets, and configuration.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 36 }}>

        {/* Account info */}
        <AccountPanel />

        <div style={{ height: 1, background: 'var(--border)' }} />

        {/* Dataset management with delete */}
        <DatasetPanel />

        <div style={{ height: 1, background: 'var(--border)' }} />

        {/* Database */}
        <section>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            Database
          </h3>
          <InfoRow label="Engine"   value="SQLite (zero-infra, file-based)" />
          <InfoRow label="Location" value="datasets/trade_intelligence.db" valueStyle={{ fontFamily: 'ui-monospace, monospace', fontSize: 12 }} />
        </section>

        <div style={{ height: 1, background: 'var(--border)' }} />

        {/* API config */}
        <section>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            API
          </h3>
          <InfoRow label="Backend URL"     value="http://localhost:8000" />
          <InfoRow label="CORS"            value="Enabled (localhost:5173 only)"   valueStyle={{ color: 'var(--color-ontime-text)' }} />
          <InfoRow label="Authentication"  value="JWT (HS256, 24-hour sessions)"   valueStyle={{ color: 'var(--color-ontime-text)' }} />
        </section>

        <div style={{ height: 1, background: 'var(--border)' }} />

        {/* Models */}
        <section>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
            Models
          </h3>
          <InfoRow label="Delay predictor"    value="Logistic Regression (scikit-learn)" />
          <InfoRow label="Anomaly detection"  value="Isolation Forest — contract deviation if contracted_rate col present" />
          <InfoRow label="Transit model"      value="Weight-adjusted bucket median + regression (Module 5)" />
          <InfoRow label="Model persistence"  value="joblib (survives server restarts)" />
        </section>

      </div>
    </div>
  );
}
