import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiService';
import { AlertCircle, CheckCircle, XCircle, Clock, ChevronDown } from 'lucide-react';
import { useDataset } from '../features/datasets/DatasetContext';

// ─── Status config — investigated is intentionally neutral ────────────────────
const STATUS_CONFIG = {
  open:         { label: 'Open',         icon: Clock,        badgeClass: 'badge badge-delayed'  },
  investigated: { label: 'Investigated', icon: CheckCircle,  badgeClass: 'badge badge-resolved' },
  dismissed:    { label: 'Dismissed',    icon: XCircle,      badgeClass: 'badge badge-resolved' },
};

// ─── Individual anomaly row ───────────────────────────────────────────────────
function AnomalyRow({ anomaly, onStatusChange }) {
  const [status, setStatus]   = useState(anomaly.review_status || 'open');
  const [notes, setNotes]     = useState(anomaly.review_notes || '');
  const [saving, setSaving]   = useState(false);
  const [saved, setSaved]     = useState(false);

  const config     = STATUS_CONFIG[status] || STATUS_CONFIG.open;
  const StatusIcon = config.icon;

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiService.updateAnomalyStatus(anomaly.shipment_id, status, notes);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      onStatusChange(anomaly.shipment_id, status);
    } catch (e) {
      console.error('Failed to update anomaly status', e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      padding: '14px 16px',
      borderBottom: '1px solid var(--border)',
      flexWrap: 'wrap',
    }}>
      {/* Shipment ID */}
      <div style={{ minWidth: 140 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Shipment</div>
        <div style={{ fontSize: 13, fontWeight: 600, fontFamily: 'ui-monospace, monospace', color: 'var(--text-primary)' }}>
          {anomaly.shipment_id}
        </div>
      </div>

      {/* Cost */}
      <div style={{ minWidth: 100 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Cost</div>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-delayed-text)' }}>
          ${Number(anomaly.cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>

      {/* Distance */}
      <div style={{ minWidth: 100 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Distance</div>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
          {Number(anomaly.distance || 0).toLocaleString()} km
        </div>
      </div>

      {/* Status badge */}
      <span className={config.badgeClass} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <StatusIcon size={11} />
        {config.label}
      </span>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 8, marginLeft: 'auto', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          type="text"
          className="form-input"
          placeholder="Notes (optional)"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          style={{ height: 32, minWidth: 160, fontSize: 13 }}
        />
        <div style={{ position: 'relative' }}>
          <select
            className="form-input"
            value={status}
            onChange={e => setStatus(e.target.value)}
            style={{ height: 32, paddingRight: 28, fontSize: 13 }}
          >
            <option value="open">Open</option>
            <option value="investigated">Investigated</option>
            <option value="dismissed">Dismissed</option>
          </select>
          <ChevronDown size={13} style={{ position: 'absolute', right: 8, top: 9, pointerEvents: 'none', color: 'var(--text-muted)' }} />
        </div>
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={saving}
          style={{ height: 32, padding: '0 14px', fontSize: 13 }}
        >
          {saving ? 'Saving…' : saved ? '✓ Saved' : 'Mark as investigated'}
        </button>
      </div>
    </div>
  );
}

// ─── Insights (Anomaly review) ────────────────────────────────────────────────
export default function AnomalyReview() {
  const { activeDataset } = useDataset();
  const [anomalies, setAnomalies]     = useState([]);
  const [loading, setLoading]         = useState(true);
  const [modelTrained, setModelTrained] = useState(false);
  const [filter, setFilter]           = useState('all');

  useEffect(() => {
    if (!activeDataset) {
      setAnomalies([]);
      setLoading(false);
      return;
    }
    loadAnomalies();
  }, [activeDataset?.id]);

  const loadAnomalies = async () => {
    setLoading(true);
    try {
      const res = await apiService.getAnomalies(activeDataset.id);
      setAnomalies(res.data.anomalies || []);
      setModelTrained(res.data.model_trained || false);
    } catch (e) {
      console.error('Error loading anomalies', e);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = (shipmentId, newStatus) => {
    setAnomalies(prev =>
      prev.map(a => a.shipment_id === shipmentId ? { ...a, review_status: newStatus } : a)
    );
  };

  const filtered   = filter === 'all' ? anomalies : anomalies.filter(a => a.review_status === filter);
  const openCount  = anomalies.filter(a => (a.review_status || 'open') === 'open').length;

  const tabs = [
    { key: 'all',          label: `All (${anomalies.length})` },
    { key: 'open',         label: `Open (${anomalies.filter(a => (a.review_status || 'open') === 'open').length})` },
    { key: 'investigated', label: `Investigated (${anomalies.filter(a => a.review_status === 'investigated').length})` },
    { key: 'dismissed',    label: `Dismissed (${anomalies.filter(a => a.review_status === 'dismissed').length})` },
  ];

  return (
    <div style={{ maxWidth: 1100, paddingBottom: 60 }}>
      <div className="page-header" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <h1 className="page-title">Insights</h1>
          {openCount > 0 && (
            <span className="badge badge-delayed">{openCount} open</span>
          )}
        </div>
        <p className="page-subtitle">
          Cost anomalies flagged by the detection model. Mark each as investigated or dismissed.
        </p>
      </div>

      {/* ── Underline tabs ── */}
      {!loading && anomalies.length > 0 && (
        <div className="tab-bar">
          {tabs.map(t => (
            <button
              key={t.key}
              className={`tab-item ${filter === t.key ? 'active' : ''}`}
              onClick={() => setFilter(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}

      {/* ── States ── */}
      {loading && (
        <div className="loading-row">
          <div className="pulse-dot" /> Loading…
        </div>
      )}

      {!loading && !modelTrained && (
        <div className="card">
          <div className="empty-state" style={{ padding: '32px 0' }}>
            <AlertCircle size={28} className="empty-state-icon" />
            <h3>Detection model not trained yet</h3>
            <p>
              Upload a CSV dataset in <strong>Settings</strong> to train the model.
              At least 50 shipment records are needed.
            </p>
          </div>
        </div>
      )}

      {!loading && modelTrained && anomalies.length === 0 && (
        <div className="card">
          <div className="empty-state" style={{ padding: '32px 0' }}>
            <CheckCircle size={28} style={{ color: 'var(--color-ontime-text)' }} />
            <h3>No anomalies detected</h3>
            <p>All shipment costs are within the expected range for their route distances.</p>
          </div>
        </div>
      )}

      {!loading && filtered.length === 0 && anomalies.length > 0 && (
        <div style={{ padding: '24px 0', color: 'var(--text-muted)', fontSize: 14 }}>
          Nothing with status "{filter}" — try a different filter.
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="table-container">
          {filtered.map(anomaly => (
            <AnomalyRow
              key={anomaly.shipment_id}
              anomaly={anomaly}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}
