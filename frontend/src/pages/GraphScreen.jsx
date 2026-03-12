import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { apiService } from '../services/apiService';
import { AlertTriangle, Clock, Server } from 'lucide-react';
import { motion } from 'framer-motion';
import { ReactFlow, Controls, Background, useNodesState, useEdgesState, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const MOCK_NODES = [
    { id: '1', position: { x: 50, y: 150 }, data: { label: 'Customer: Apple Inc' }, style: { background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--primary)', borderRadius: '8px', padding: '12px 20px', fontWeight: 'bold' } },
    { id: '2', position: { x: 300, y: 50 }, data: { label: 'Order #847' }, style: { background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '10px' } },
    { id: '3', position: { x: 300, y: 250 }, data: { label: 'Order #882' }, style: { background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '10px' } },
    { id: '4', position: { x: 550, y: 50 }, data: { label: 'Shipment SHP-101' }, style: { background: 'rgba(239, 68, 68, 0.15)', color: 'var(--danger)', border: '1px solid var(--danger)', borderRadius: '8px', padding: '10px' } },
    { id: '5', position: { x: 550, y: 250 }, data: { label: 'Shipment SHP-204' }, style: { background: 'rgba(16, 185, 129, 0.15)', color: 'var(--success)', border: '1px solid var(--success)', borderRadius: '8px', padding: '10px' } },
    { id: '6', position: { x: 800, y: 150 }, data: { label: 'Invoice $4,500' }, style: { background: 'var(--bg-card)', color: 'var(--text-main)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '10px' } },
];

const MOCK_EDGES = [
    { id: 'e1-2', source: '1', target: '2', animated: true, markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--primary)' }, style: { stroke: 'var(--primary)' } },
    { id: 'e1-3', source: '1', target: '3', animated: true, markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--primary)' }, style: { stroke: 'var(--primary)' } },
    { id: 'e2-4', source: '2', target: '4', markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--text-muted)' }, style: { stroke: 'var(--text-muted)' } },
    { id: 'e3-5', source: '3', target: '5', markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--text-muted)' }, style: { stroke: 'var(--text-muted)' } },
    { id: 'e4-6', source: '4', target: '6', label: 'Anomaly', labelStyle: { fill: 'var(--danger)', fontWeight: 700 }, style: { stroke: 'var(--danger)', strokeDasharray: '5 5' } },
    { id: 'e5-6', source: '5', target: '6', style: { stroke: 'var(--text-muted)' } },
];

export default function GraphScreen() {
    const [insights, setInsights] = useState(null);
    const [loading, setLoading] = useState(true);

    const [nodes, setNodes, onNodesChange] = useNodesState(MOCK_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(MOCK_EDGES);

    useEffect(() => {
        loadInsights();
    }, []);

    const loadInsights = async () => {
        try {
            const resp = await apiService.getInsights();
            setInsights(resp.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Entity Knowledge Graph</h1>
                <p className="page-subtitle">Interactive relationship visualizer using React Flow with isolated anomaly traces.</p>
            </div>

            {loading ? (
                <div style={{ color: 'var(--primary)', fontWeight: 500 }}>Consulting AI Engine...</div>
            ) : (
                <>
                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: 24, marginBottom: 24 }}>
                        {/* Delay Prediction Card */}
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card glass">
                            <h2 style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, color: 'var(--primary)', fontSize: 18 }}>
                                <Clock size={20} /> ML Delay Model Predictor
                            </h2>
                            {insights?.delay_prediction_sample ? (
                                <div>
                                    <p style={{ marginBottom: 16, color: 'var(--text-muted)' }}>
                                        Sample target: <strong style={{ color: 'var(--text-main)' }}>{insights.delay_prediction_sample.sample_route}</strong>
                                    </p>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                                        <div style={{ fontSize: 42, fontWeight: 'bold', color: 'var(--primary)', lineHeight: 1 }}>
                                            {(insights.delay_prediction_sample.delay_probability * 100).toFixed(1)}%
                                        </div>
                                        <div style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 180 }}>
                                            Calculated probability of logistics delay exceeding expected SLA by Scikit classification.
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <p style={{ color: 'var(--text-muted)' }}>Classification model not trained. (Requires more Data)</p>
                            )}
                        </motion.div>

                        {/* Cost Anomaly Card */}
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card glass">
                            <h2 style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, color: 'var(--danger)', fontSize: 18 }}>
                                <AlertTriangle size={20} /> Isolation Forest Anomalies
                            </h2>
                            <div className="alerts-list" style={{ maxHeight: 200, overflowY: 'auto' }}>
                                {insights?.recent_cost_anomalies?.length > 0 ? (
                                    insights.recent_cost_anomalies.map((anom, idx) => (
                                        <div key={idx} className="alert-item">
                                            <AlertTriangle size={18} color="var(--danger)" style={{ minWidth: 18 }} />
                                            <div>
                                                <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: 14 }}>Shipment {anom.shipment_id}</div>
                                                <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 2 }}>
                                                    Distance <span style={{ color: 'var(--text-main)' }}>{anom.distance.toFixed(0)} km</span> yielded anomalous cost of <span style={{ color: 'var(--danger)', fontWeight: 600 }}>${anom.cost.toFixed(2)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <p style={{ color: 'var(--text-muted)' }}>No historical cost anomalies bounded within standard deviation.</p>
                                )}
                            </div>
                        </motion.div>
                    </div>

                    {/* Knowledge Graph UI */}
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }} className="card glass">
                        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, color: 'var(--text-main)', fontSize: 18 }}>
                            <Server size={20} color="var(--primary)" /> Database Graph Mapping
                        </h2>
                        <div style={{ height: 400, borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border-color)', background: 'var(--bg-main)' }}>
                            <ReactFlow
                                nodes={nodes}
                                edges={edges}
                                onNodesChange={onNodesChange}
                                onEdgesChange={onEdgesChange}
                                fitView
                                colorMode={"dark"}
                            >
                                <Background color="var(--border-color)" gap={16} />
                                <Controls showInteractive={false} style={{ button: { background: 'var(--bg-card)', border: '1px solid var(--border-color)', fill: 'var(--primary)' } }} />
                            </ReactFlow>
                        </div>
                    </motion.div>
                </>
            )}
        </div>
    );
}
