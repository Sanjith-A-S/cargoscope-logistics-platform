/**
 * features/risk_queue/RiskQueueScreen.jsx
 *
 * The new home screen (mounted at "/"). Displays in-transit shipments scored
 * by projected delay severity, sorted most-urgent-first.
 *
 * Columns: Severity badge | Shipment ID | Carrier | Origin → Dest |
 *          Days in transit | Expected | Overrun | Confidence | Reason
 */
import React, { useEffect, useState } from 'react';
import api from '../../services/apiService';
import { useDataset } from '../datasets/DatasetContext';

const SEVERITY_META = {
  high:   { label: 'High',   color: 'var(--color-danger)',  bg: 'var(--color-danger-faint)'  },
  medium: { label: 'Medium', color: 'var(--color-warning)', bg: 'var(--color-warning-faint)' },
  low:    { label: 'Low',    color: 'var(--color-success)', bg: 'var(--color-success-faint)' },
};

const CONFIDENCE_META = {
  high:   { label: 'High (historical)',      icon: '🟢' },
  medium: { label: 'Medium (regression)',    icon: '🟡' },
  low:    { label: 'Low (global estimate)',  icon: '🔴' },
};

export default function RiskQueueScreen() {
  const { activeDataset } = useDataset();
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (!activeDataset) return;

    setLoading(true);
    setError(null);

    api.get('/risk-queue', { params: { dataset_id: activeDataset.id } })
      .then(r => {
        setShipments(r.data.shipments ?? []);
      })
      .catch(e => {
        if (e?.response?.status === 409) {
          setShipments([]);
        } else {
          setError('Failed to load risk queue.');
        }
      })
      .finally(() => setLoading(false));
  }, [activeDataset?.id]);

  const high   = shipments.filter(s => s.severity_level === 'high');
  const medium = shipments.filter(s => s.severity_level === 'medium');
  const low    = shipments.filter(s => s.severity_level === 'low');

  return (
    <div className="risk-queue page-fade-in">
      {/* Header */}
      <div className="risk-queue__header">
        <div>
          <h1 className="risk-queue__title">Live Risk Queue</h1>
          <p className="risk-queue__subtitle">
            In-transit shipments ranked by projected delay severity.
            {activeDataset && (
              <span className="risk-queue__dataset-badge"> {activeDataset.name}</span>
            )}
          </p>
        </div>
        {/* Summary chips */}
        <div className="risk-queue__chips">
          {[{ level: 'high', count: high.length }, { level: 'medium', count: medium.length }, { level: 'low', count: low.length }]
            .filter(c => c.count > 0)
            .map(({ level, count }) => (
              <span
                key={level}
                className="risk-queue__chip"
                style={{
                  color: SEVERITY_META[level].color,
                  background: SEVERITY_META[level].bg,
                }}
              >
                {count} {SEVERITY_META[level].label}
              </span>
            ))}
        </div>
      </div>

      {/* States */}
      {!activeDataset && (
        <div className="risk-queue__empty">
          <p>Select or upload a dataset to view in-transit shipments.</p>
        </div>
      )}

      {loading && activeDataset && (
        <div className="risk-queue__loading">
          <span className="spinner" /> Loading…
        </div>
      )}

      {error && <div className="risk-queue__error">{error}</div>}

      {!loading && !error && activeDataset && shipments.length === 0 && (
        <div className="risk-queue__empty">
          <span className="risk-queue__empty-icon">✅</span>
          <p>No in-transit shipments in this dataset.</p>
        </div>
      )}

      {/* Table */}
      {!loading && shipments.length > 0 && (
        <div className="risk-queue__table-wrap">
          <table className="risk-queue__table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Shipment ID</th>
                <th>Carrier</th>
                <th>Lane</th>
                <th>Days in Transit</th>
                <th>Expected (days)</th>
                <th>Overrun (days)</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {shipments.map(s => {
                const sev = SEVERITY_META[s.severity_level] ?? SEVERITY_META.low;
                const conf = CONFIDENCE_META[s.confidence] ?? CONFIDENCE_META.low;
                const isExpanded = expandedId === s.shipment_id;

                return (
                  <React.Fragment key={s.shipment_id}>
                    <tr
                      className={`risk-queue__row risk-queue__row--${s.severity_level}${isExpanded ? ' risk-queue__row--expanded' : ''}`}
                      onClick={() => setExpandedId(isExpanded ? null : s.shipment_id)}
                      title="Click to see reason"
                    >
                      <td>
                        <span
                          className="risk-queue__badge"
                          style={{ color: sev.color, background: sev.bg }}
                        >
                          {sev.label}
                        </span>
                      </td>
                      <td className="risk-queue__id">{s.shipment_id}</td>
                      <td>{s.carrier}</td>
                      <td>{s.origin} → {s.destination}</td>
                      <td>{s.days_in_transit}</td>
                      <td>{s.expected_transit_days}</td>
                      <td
                        className={s.projected_overrun_days > 0 ? 'risk-queue__overrun--positive' : ''}
                      >
                        {s.projected_overrun_days > 0 ? `+${s.projected_overrun_days}` : s.projected_overrun_days}
                      </td>
                      <td title={conf.label}>{conf.icon}</td>
                    </tr>
                    {isExpanded && (
                      <tr className="risk-queue__detail-row">
                        <td colSpan={8} className="risk-queue__detail">
                          <strong>Why flagged:</strong> {s.reason}
                          {s.delay_probability != null && (
                            <span className="risk-queue__prob">
                              {' · '}ML delay probability: {Math.round(s.delay_probability * 100)}%
                            </span>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
