import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiService';
import { useDataset } from '../features/datasets/DatasetContext';
import { Truck, Anchor, Plane, AlertTriangle, Navigation, X, TrendingDown, DollarSign } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const CarrierIcon = ({ carrier }) => {
  if (!carrier) return <Truck size={18} color="var(--text-muted)" />;
  const lower = carrier.toLowerCase();
  if (lower.includes('maersk') || lower.includes('msc')) return <Anchor size={18} color="var(--accent)" />;
  if (lower.includes('dhl') || lower.includes('fedex')) return <Plane size={18} color="var(--accent)" />;
  return <Truck size={18} color="var(--text-secondary)" />;
};

// Badge helper — delay rate threshold
function DelayBadge({ rate }) {
  if (rate > 15) return <span className="badge badge-delayed">{rate.toFixed(1)}%</span>;
  if (rate > 5)  return <span className="badge badge-atrisk">{rate.toFixed(1)}%</span>;
  return <span className="badge badge-ontime">{rate.toFixed(1)}%</span>;
}

export default function CarrierPerformance() {
  const { activeDataset } = useDataset();
  const [rankings, setRankings]           = useState([]);
  const [loading, setLoading]             = useState(true);
  const [selectedCarrier, setSelectedCarrier] = useState(null);
  const [routeDetails, setRouteDetails]   = useState([]);
  const [loadingRoutes, setLoadingRoutes] = useState(false);

  useEffect(() => {
    if (!activeDataset) {
      setLoading(false);
      setRankings([]);
      return;
    }
    loadRankings();
  }, [activeDataset?.id]);

  const loadRankings = async () => {
    setLoading(true);
    try {
      const res = await apiService.getCarrierRanking(activeDataset.id);
      setRankings(res.data || []);
    } catch (e) {
      console.error('Error loading carrier ranking', e);
      setRankings([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCarrier = async (carrier) => {
    setSelectedCarrier(carrier);
    setLoadingRoutes(true);
    try {
      const res = await apiService.getCarrierRoutes(carrier, activeDataset?.id);
      setRouteDetails(res.data || []);
    } catch (e) {
      console.error('Error loading route details', e);
      setRouteDetails([]);
    } finally {
      setLoadingRoutes(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* ── Main list ── */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        transition: 'margin-right 0.3s ease',
        marginRight: selectedCarrier ? 440 : 0,
        minWidth: 0,
      }}>
        <div className="page-header" style={{ marginBottom: 20 }}>
          <h1 className="page-title">Carriers</h1>
          <p className="page-subtitle">On-time rate, delay rate, and shipment volume by carrier.</p>
        </div>

        {loading ? (
          <div className="loading-row">
            <div className="pulse-dot" /> Loading…
          </div>
        ) : rankings.length === 0 ? (
          <div className="empty-state">
            <Truck size={36} className="empty-state-icon" />
            <h3>No carrier data yet</h3>
            <p>Upload a CSV dataset in <strong>Settings</strong> to see carrier rankings.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table" style={{ minWidth: 700 }}>
              <thead>
                <tr>
                  <th style={{ width: 52, paddingLeft: 20 }}>Rank</th>
                  <th>Carrier</th>
                  <th>Volume</th>
                  <th>Exceptions</th>
                  <th>Delay rate</th>
                  <th>Avg cost</th>
                  <th style={{ width: 40 }} />
                </tr>
              </thead>
              <tbody>
                {rankings.map((c, idx) => (
                  <motion.tr
                    key={c.carrier}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.12, delay: idx * 0.04 }}
                    onClick={() => handleSelectCarrier(c.carrier)}
                    style={{
                      cursor: 'pointer',
                      outline: selectedCarrier === c.carrier ? '2px solid var(--accent-subtle)' : 'none',
                      outlineOffset: -1,
                    }}
                  >
                    {/* Rank — typographic, no colored bar */}
                    <td style={{ paddingLeft: 20, fontWeight: 700, fontSize: 15, color: 'var(--text-secondary)' }}>
                      #{idx + 1}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: '50%',
                          background: 'var(--bg-surface-2)',
                          border: '1px solid var(--border)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          flexShrink: 0,
                        }}>
                          <CarrierIcon carrier={c.carrier} />
                        </div>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>{c.carrier}</span>
                      </div>
                    </td>
                    <td style={{ fontWeight: 500 }}>{c.total_shipments.toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--color-atrisk-text)', fontSize: 13 }}>
                        <AlertTriangle size={13} /> {c.delayed_shipments}
                      </div>
                    </td>
                    <td><DelayBadge rate={c.delay_rate} /></td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                      ${c.avg_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: 12, paddingRight: 16 }}>
                      View routes →
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Slide-out route detail panel ── */}
      <AnimatePresence>
        {selectedCarrier && (
          <motion.div
            initial={{ x: 440, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 440, opacity: 0 }}
            transition={{ type: 'spring', damping: 26, stiffness: 220 }}
            style={{
              position: 'absolute', top: 0, right: 0, bottom: 0, width: 440,
              background: 'var(--bg-surface)',
              borderLeft: '1px solid var(--border)',
              display: 'flex', flexDirection: 'column',
              zIndex: 50,
            }}
          >
            {/* Panel header */}
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', gap: 14,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: '50%',
                background: 'var(--bg-surface-2)', border: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <CarrierIcon carrier={selectedCarrier} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {selectedCarrier}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 1 }}>
                  Route breakdown
                </div>
              </div>
              <button
                className="btn-ghost"
                onClick={() => setSelectedCarrier(null)}
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>

            {/* Route list */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {loadingRoutes ? (
                <div className="loading-row"><div className="pulse-dot" /></div>
              ) : routeDetails.length > 0 ? routeDetails.map((route, i) => (
                <div key={i} style={{
                  background: 'var(--bg-surface-2)',
                  border: '1px solid var(--border)',
                  borderRadius: 10,
                  padding: '14px 16px',
                }}>
                  {/* Route label */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {route.origin}
                    </span>
                    <Navigation size={12} color="var(--text-muted)" />
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {route.destination}
                    </span>
                  </div>
                  {/* Metrics */}
                  <div style={{ display: 'flex', gap: 20 }}>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Volume</div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                        {route.total_shipments}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Delay rate</div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: route.delay_rate > 15 ? 'var(--color-delayed-text)' : 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                        {route.delay_rate > 15 && <TrendingDown size={13} />}
                        {route.delay_rate.toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Avg cost</div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                        ${route.avg_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </div>
                    </div>
                  </div>
                </div>
              )) : (
                <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
                  No route data available for this carrier.
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
