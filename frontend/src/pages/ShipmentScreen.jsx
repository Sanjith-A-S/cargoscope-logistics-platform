import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiService';
import { Search, MapPin, Navigation, CheckCircle2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const TimelineProgress = ({ status, isDelayed }) => {
    // Simple deterministic progress based on string (just for UI demonstration)
    let steps = 4;
    let current = status === 'Delivered' ? 4 : status === 'In Transit' ? 2 : 1;

    return (
        <div style={{ display: 'flex', alignItems: 'center', width: 200, gap: 4 }}>
            {[...Array(steps)].map((_, i) => (
                <div key={i} style={{
                    flex: 1,
                    height: 4,
                    borderRadius: 2,
                    background: i < current ? (isDelayed ? 'var(--danger)' : 'var(--success)') : 'var(--bg-main)'
                }} />
            ))}
        </div>
    )
}

export default function ShipmentScreen() {
    const [search, setSearch] = useState('');
    const [shipments, setShipments] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadShipments();
    }, []);

    const loadShipments = async () => {
        try {
            const resp = await apiService.getShipments(0, 50); // Get first 50
            setShipments(resp.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const filtered = shipments.filter(s =>
        (s.customer && s.customer.toLowerCase().includes(search.toLowerCase())) ||
        (s.shipment_id && s.shipment_id.toLowerCase().includes(search.toLowerCase())) ||
        (s.destination && s.destination.toLowerCase().includes(search.toLowerCase()))
    );

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Shipment Explorer</h1>
                <p className="page-subtitle">Track individual logistics timelines and relational endpoints.</p>
            </div>

            <div style={{ position: 'relative', marginBottom: 24, maxWidth: 600 }}>
                <input
                    type="text"
                    className="header-search"
                    placeholder="Filter by ID, Customer, or Destination..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    style={{ width: '100%', paddingLeft: 45, height: 48, fontSize: 15 }}
                />
                <Search size={20} style={{ position: 'absolute', left: 16, top: 14, color: 'var(--primary)' }} />
            </div>

            {loading ? (
                <div style={{ color: 'var(--primary)', fontWeight: 500 }}>Querying database...</div>
            ) : (
                <div className="card glass table-container" style={{ padding: 0 }}>
                    <div style={{ overflowX: 'auto', maxHeight: '72vh' }}>
                        <table className="data-table">
                            <thead style={{ position: 'sticky', top: 0, zIndex: 10, background: 'var(--bg-card)' }}>
                                <tr>
                                    <th>Shipment ID</th>
                                    <th>Customer (deduped)</th>
                                    <th>Route</th>
                                    <th style={{ minWidth: 220 }}>Timeline</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((s, idx) => (
                                    <motion.tr
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.02, duration: 0.2 }}
                                        key={s.shipment_id}
                                    >
                                        <td style={{ fontWeight: 600 }}>{s.shipment_id}</td>
                                        <td>{s.customer}</td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                <MapPin size={14} color="var(--text-muted)" />
                                                <span style={{ fontSize: 13 }}>{s.origin}</span>
                                                <Navigation size={12} color="var(--primary)" />
                                                <span style={{ fontSize: 13 }}>{s.destination}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <TimelineProgress status={s.status} isDelayed={s.is_delayed} />
                                        </td>
                                        <td>
                                            <span className={`badge ${s.is_delayed ? 'danger' : s.status === 'Delivered' ? 'success' : 'info'}`}>
                                                {s.is_delayed ? 'Delayed' : s.status}
                                            </span>
                                        </td>
                                    </motion.tr>
                                ))}
                                {filtered.length === 0 && (
                                    <tr>
                                        <td colSpan="5" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                                            No shipments match your criteria.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
