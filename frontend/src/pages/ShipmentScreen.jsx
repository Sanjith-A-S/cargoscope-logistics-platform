import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiService } from '../services/apiService';
import { useDataset } from '../features/datasets/DatasetContext';
import {
  Search, X, Filter, ChevronLeft, ChevronRight,
  Package, Truck, Anchor, Plane, ArrowRight,
  Zap, AlertCircle, TrendingUp, TrendingDown, FileCheck, Hash
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// ─── Timeline progress bar ────────────────────────────────────────────────────
const TimelineProgress = ({ status, isDelayed }) => {
  const steps   = 4;
  const current = status === 'Delivered' ? 4 : status === 'In Transit' ? 2 : status === 'Pending' ? 1 : 0;

  const segColor = (i) => {
    if (i >= current) return 'var(--border-strong)';
    if (isDelayed)    return 'var(--color-delayed-text)';
    if (status === 'Delivered') return 'var(--color-ontime-text)';
    return 'var(--accent)';
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', width: 120, gap: 3 }}>
      {[...Array(steps)].map((_, i) => (
        <div key={i} style={{
          flex: 1, height: 4, borderRadius: 2,
          background: segColor(i),
          transition: 'background 0.2s ease',
        }} />
      ))}
    </div>
  );
};

// ─── Carrier icon ─────────────────────────────────────────────────────────────
const CarrierIcon = ({ carrier, size = 14 }) => {
  if (!carrier) return <Truck size={size} color="var(--text-muted)" />;
  const lower = carrier.toLowerCase();
  if (lower.includes('maersk') || lower.includes('msc')) return <Anchor size={size} color="var(--accent)" />;
  if (lower.includes('dhl') || lower.includes('fedex')) return <Plane size={size} color="var(--accent)" />;
  return <Truck size={size} color="var(--text-secondary)" />;
};

// ─── Status badge — badge only, never full row ────────────────────────────────
const StatusBadge = ({ status, isDelayed }) => {
  if (isDelayed)              return <span className="badge badge-delayed">Delayed</span>;
  if (status === 'Delivered') return <span className="badge badge-ontime">Delivered</span>;
  if (status === 'In Transit') return <span className="badge badge-atrisk">In transit</span>;
  return <span className="badge badge-resolved">{status}</span>;
};

// ─── Delay risk predictor panel ───────────────────────────────────────────────
const RISK_COLOR = {
  low:    'var(--color-ontime-text)',
  medium: 'var(--color-atrisk-text)',
  high:   'var(--color-delayed-text)',
};

const PredictRiskPanel = () => {
  const [form, setForm]     = useState({ carrier: '', origin: '', destination: '', distance: '', cost: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await apiService.predictDelay({
        carrier: form.carrier,
        origin: form.origin,
        destination: form.destination,
        distance: parseFloat(form.distance) || 0,
        cost: parseFloat(form.cost) || 0,
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed — is the model trained?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      style={{ overflow: 'hidden', marginBottom: 16 }}
    >
      <div className="card" style={{ padding: 18 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 7 }}>
          <Zap size={15} color="var(--accent)" /> Delay risk predictor
        </h3>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          {[
            { key: 'carrier',     label: 'Carrier',      placeholder: 'e.g. Maersk' },
            { key: 'origin',      label: 'Origin',       placeholder: 'e.g. SHA' },
            { key: 'destination', label: 'Destination',  placeholder: 'e.g. LAX' },
            { key: 'distance',    label: 'Distance (km)', placeholder: '12000', type: 'number' },
            { key: 'cost',        label: 'Cost ($)',     placeholder: '4500',  type: 'number' },
          ].map(({ key, label, placeholder, type }) => (
            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 120 }}>
              <label className="form-label">{label}</label>
              <input
                type={type || 'text'}
                className="form-input"
                placeholder={placeholder}
                value={form[key]}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                style={{ height: 34, fontSize: 13 }}
                required
              />
            </div>
          ))}
          <button type="submit" className="btn-primary" disabled={loading}
            style={{ height: 34, padding: '0 18px', fontSize: 13, alignSelf: 'flex-end' }}>
            {loading ? 'Predicting…' : 'Predict'}
          </button>
        </form>

        {error && (
          <div className="field-error" style={{ marginTop: 10 }}>
            <AlertCircle size={13} style={{ flexShrink: 0 }} />
            {error}
          </div>
        )}

        {result && (
          <div style={{ marginTop: 14, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
            <div style={{
              padding: '12px 18px', borderRadius: 8,
              background: 'var(--bg-surface-2)', border: `1px solid ${RISK_COLOR[result.risk_level]}`,
              textAlign: 'center', minWidth: 110,
            }}>
              <div style={{ fontSize: 26, fontWeight: 700, color: RISK_COLOR[result.risk_level] }}>
                {Math.round(result.delay_probability * 100)}%
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, color: RISK_COLOR[result.risk_level], textTransform: 'uppercase', letterSpacing: 0.3 }}>
                {result.risk_level} risk
              </div>
            </div>

            {result.top_features?.length > 0 && (
              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: 0.3, marginBottom: 8 }}>
                  Contributing factors
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {result.top_features.map(f => (
                    <div key={f.feature} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                      {f.direction === 'increases_risk'
                        ? <TrendingUp size={13} color="var(--color-delayed-text)" />
                        : <TrendingDown size={13} color="var(--color-ontime-text)" />}
                      <span style={{ color: 'var(--text-primary)', textTransform: 'capitalize' }}>{f.feature}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                        = {typeof f.value === 'number' ? f.value.toFixed(1) : f.value}
                      </span>
                      <span style={{
                        marginLeft: 'auto', fontSize: 12, fontWeight: 600,
                        color: f.direction === 'increases_risk' ? 'var(--color-delayed-text)' : 'var(--color-ontime-text)',
                      }}>
                        {f.direction === 'increases_risk' ? '↑ raises risk' : '↓ lowers risk'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

// ─── Sort icon ────────────────────────────────────────────────────────────────
const SortIcon = ({ field, sortBy, sortDesc }) => {
  if (sortBy !== field) return <span style={{ opacity: 0.25, marginLeft: 3 }}>↕</span>;
  return <span style={{ marginLeft: 3, color: 'var(--accent)' }}>{sortDesc ? '↓' : '↑'}</span>;
};

// ─── Shipments ────────────────────────────────────────────────────────────────
export default function ShipmentScreen() {
  const { activeDataset } = useDataset();
  const [searchParams]       = useSearchParams();
  const [search, setSearch]  = useState(() => searchParams.get('q') || '');
  const [debouncedSearch, setDebouncedSearch] = useState(() => searchParams.get('q') || '');

  const [showFilters, setShowFilters]     = useState(false);
  const [filterCarrier, setFilterCarrier] = useState('');
  const [filterStatus, setFilterStatus]   = useState('');
  const [filterOrigin, setFilterOrigin]   = useState('');

  const [shipments, setShipments]         = useState([]);
  const [loading, setLoading]             = useState(true);
  const [page, setPage]                   = useState(1);
  const [totalPages, setTotalPages]       = useState(1);
  const [totalItems, setTotalItems]       = useState(0);
  const [limit]                           = useState(15);
  const [sortBy, setSortBy]               = useState('shipment_id');
  const [sortDesc, setSortDesc]           = useState(false);
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [showPredict, setShowPredict]     = useState(false);

  const handleSort = (field) => {
    if (sortBy === field) setSortDesc(d => !d);
    else { setSortBy(field); setSortDesc(false); }
    setPage(1);
  };

  useEffect(() => {
    const h = setTimeout(() => { setDebouncedSearch(search); setPage(1); }, 500);
    return () => clearTimeout(h);
  }, [search]);

  const loadShipments = useCallback(async () => {
    if (!activeDataset) {
      setShipments([]);
      setTotalItems(0);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const resp = await apiService.getShipments(page, limit, debouncedSearch, filterCarrier, filterOrigin, filterStatus, sortBy, sortDesc, activeDataset.id);
      setShipments(resp.data.data);
      setTotalPages(resp.data.pagination.total_pages);
      setTotalItems(resp.data.pagination.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page, limit, debouncedSearch, filterCarrier, filterOrigin, filterStatus, sortBy, sortDesc, activeDataset?.id]);

  useEffect(() => { loadShipments(); }, [loadShipments]);

  const hasFilters = debouncedSearch || filterCarrier || filterStatus || filterOrigin;

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* ── Main list ── */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        transition: 'margin-right 0.3s ease',
        marginRight: selectedShipment ? 400 : 0,
        minWidth: 0,
      }}>
        <div className="page-header" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <h1 className="page-title">Shipments</h1>
              <p className="page-subtitle">Search and filter your shipment records.</p>
            </div>
            <button
              className={showPredict ? 'btn-primary' : 'btn-secondary'}
              onClick={() => setShowPredict(v => !v)}
              style={{ height: 36, fontSize: 13 }}
            >
              <Zap size={14} />
              {showPredict ? 'Close predictor' : 'Predict delay risk'}
            </button>
          </div>
        </div>

        {/* Predict panel */}
        <AnimatePresence>{showPredict && <PredictRiskPanel />}</AnimatePresence>

        {/* Search + filter row */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 220, maxWidth: 520 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: 11, color: 'var(--text-muted)', pointerEvents: 'none' }} />
            <input
              type="text"
              className="form-input"
              placeholder="Search by ID, customer, carrier, route…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: 38, height: 38 }}
            />
          </div>

          <button
            className={`btn-secondary ${showFilters ? '' : ''}`}
            onClick={() => setShowFilters(f => !f)}
            style={{
              height: 38,
              background: showFilters ? 'var(--accent-subtle)' : '',
              color: showFilters ? 'var(--accent)' : '',
              borderColor: showFilters ? 'var(--accent)' : '',
            }}
          >
            <Filter size={14} /> Filters
          </button>

          <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 'auto' }}>
            {totalItems > 0 ? `${totalItems.toLocaleString()} records` : ''}
          </span>
        </div>

        {/* Filter panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              style={{ overflow: 'hidden', marginBottom: 14 }}
            >
              <div className="card" style={{ display: 'flex', gap: 14, padding: 14, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 140 }}>
                  <label className="form-label">Carrier</label>
                  <select className="form-input" value={filterCarrier}
                    onChange={e => { setFilterCarrier(e.target.value); setPage(1); }} style={{ height: 36 }}>
                    <option value="">All carriers</option>
                    <option value="Maersk">Maersk</option>
                    <option value="MSC">MSC</option>
                    <option value="CMA CGM">CMA CGM</option>
                    <option value="Hapag-Lloyd">Hapag-Lloyd</option>
                    <option value="DHL">DHL</option>
                  </select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 140 }}>
                  <label className="form-label">Status</label>
                  <select className="form-input" value={filterStatus}
                    onChange={e => { setFilterStatus(e.target.value); setPage(1); }} style={{ height: 36 }}>
                    <option value="">All statuses</option>
                    <option value="Pending">Pending</option>
                    <option value="In Transit">In transit</option>
                    <option value="Delivered">Delivered</option>
                  </select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 130 }}>
                  <label className="form-label">Origin code</label>
                  <input type="text" className="form-input" placeholder="e.g. SHA"
                    value={filterOrigin} onChange={e => { setFilterOrigin(e.target.value); setPage(1); }}
                    style={{ height: 36 }} />
                </div>
                <button className="btn-ghost" onClick={() => {
                  setFilterCarrier(''); setFilterStatus(''); setFilterOrigin('');
                  setSearch(''); setPage(1);
                }} style={{ height: 36, fontSize: 13, padding: '0 12px', color: 'var(--text-secondary)' }}>
                  Clear all
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Table */}
        {loading && shipments.length === 0 ? (
          <div className="loading-row"><div className="pulse-dot" /> Loading…</div>
        ) : !loading && totalItems === 0 && !hasFilters ? (
          <div className="empty-state">
            <Package size={36} className="empty-state-icon" />
            <h3>No shipments yet</h3>
            <p>Upload a CSV to populate your shipment records.</p>
          </div>
        ) : (
          <div className="table-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto', overflowY: 'auto', flex: 1 }}>
              <table className="data-table" style={{ minWidth: 860 }}>
                <thead style={{ position: 'sticky', top: 0, zIndex: 5 }}>
                  <tr>
                    <th style={{ cursor: 'pointer', paddingLeft: 20 }} onClick={() => handleSort('shipment_id')}>
                      Shipment ID <SortIcon field="shipment_id" sortBy={sortBy} sortDesc={sortDesc} />
                    </th>
                    <th style={{ cursor: 'pointer' }} onClick={() => handleSort('customer')}>
                      Customer <SortIcon field="customer" sortBy={sortBy} sortDesc={sortDesc} />
                    </th>
                    <th style={{ cursor: 'pointer' }} onClick={() => handleSort('carrier')}>
                      Carrier <SortIcon field="carrier" sortBy={sortBy} sortDesc={sortDesc} />
                    </th>
                    <th>Route</th>
                    <th>Timeline</th>
                    <th style={{ cursor: 'pointer', paddingRight: 20 }} onClick={() => handleSort('status')}>
                      Status <SortIcon field="status" sortBy={sortBy} sortDesc={sortDesc} />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {shipments.map((s) => (
                    <motion.tr
                      key={s.shipment_id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.12 }}
                      onClick={() => setSelectedShipment(s)}
                      style={{
                        cursor: 'pointer',
                        outline: selectedShipment?.shipment_id === s.shipment_id
                          ? '2px solid var(--accent-subtle)' : 'none',
                        outlineOffset: -1,
                      }}
                    >
                      <td style={{ paddingLeft: 20, fontFamily: 'ui-monospace, monospace', fontSize: 12, fontWeight: 500 }}>
                        {s.shipment_id}
                      </td>
                      <td>{s.customer?.name || s.customer}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <CarrierIcon carrier={s.carrier} />
                          <span style={{ color: 'var(--text-secondary)' }}>{s.carrier || 'Unknown'}</span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                          <span>{s.route?.origin || s.origin}</span>
                          <ArrowRight size={11} color="var(--text-muted)" />
                          <span>{s.route?.destination || s.destination}</span>
                        </div>
                      </td>
                      <td>
                        <TimelineProgress status={s.status} isDelayed={s.is_delayed} />
                      </td>
                      <td style={{ paddingRight: 20 }}>
                        <StatusBadge status={s.status} isDelayed={s.is_delayed} />
                      </td>
                    </motion.tr>
                  ))}
                  {shipments.length === 0 && !loading && (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-muted)', fontSize: 14 }}>
                        Nothing matches your search — try different filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div style={{
              padding: '10px 20px',
              borderTop: '1px solid var(--border)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              background: 'var(--bg-surface)',
            }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Page {page} of {totalPages}
              </span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="btn-secondary" onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1 || loading} style={{ padding: '5px 10px' }}>
                  <ChevronLeft size={15} />
                </button>
                <button className="btn-secondary" onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages || loading} style={{ padding: '5px 10px' }}>
                  <ChevronRight size={15} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Slide-out detail panel ── */}
      <AnimatePresence>
        {selectedShipment && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', damping: 26, stiffness: 220 }}
            style={{
              position: 'absolute', top: 0, right: 0, bottom: 0, width: 400,
              background: 'var(--bg-surface)',
              borderLeft: '1px solid var(--border)',
              display: 'flex', flexDirection: 'column',
              zIndex: 50,
            }}
          >
            {/* Panel header */}
            <div style={{
              padding: '18px 20px',
              borderBottom: '1px solid var(--border)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, fontFamily: 'ui-monospace, monospace', color: 'var(--text-primary)', marginBottom: 6 }}>
                  {selectedShipment.shipment_id}
                </div>
                <StatusBadge status={selectedShipment.status} isDelayed={selectedShipment.is_delayed} />
              </div>
              <button className="btn-ghost" onClick={() => setSelectedShipment(null)} aria-label="Close">
                <X size={18} />
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Route */}
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: 0.3, marginBottom: 12 }}>
                  Route
                </div>
                <div style={{ position: 'relative', paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div style={{ position: 'absolute', left: 7, top: 10, bottom: 10, width: 2, background: 'var(--border)' }} />
                  {[
                    { label: 'Origin',      value: selectedShipment.route?.origin || selectedShipment.origin,          dotColor: 'var(--text-muted)' },
                    { label: 'Destination', value: selectedShipment.route?.destination || selectedShipment.destination, dotColor: 'var(--accent)' },
                  ].map(loc => (
                    <div key={loc.label} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                      <div style={{
                        width: 16, height: 16, borderRadius: '50%',
                        background: 'var(--bg-surface)', border: `2px solid ${loc.dotColor}`,
                        marginLeft: -20, flexShrink: 0, zIndex: 1,
                      }} />
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{loc.label}</div>
                        <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>{loc.value || '—'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Details */}
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: 0.3, marginBottom: 10 }}>
                  Details
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {[
                    { icon: FileCheck, label: 'Customer', value: selectedShipment.customer?.name || selectedShipment.customer || 'N/A' },
                    { icon: Truck,     label: 'Carrier',  value: selectedShipment.carrier || 'N/A' },
                    { icon: Hash,      label: 'Shipment ID', value: selectedShipment.shipment_id, mono: true },
                  ].map(row => (
                    <div key={row.label} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '9px 12px',
                      background: 'var(--bg-surface-2)',
                      borderRadius: 7,
                      border: '1px solid var(--border)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 13, color: 'var(--text-secondary)' }}>
                        <row.icon size={14} /> {row.label}
                      </div>
                      <span style={{
                        fontSize: 13,
                        fontFamily: row.mono ? 'ui-monospace, monospace' : 'inherit',
                        color: 'var(--text-primary)',
                        fontWeight: 500,
                      }}>
                        {row.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
