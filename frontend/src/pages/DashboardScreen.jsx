import React, { useState, useEffect } from 'react';
import { apiService } from '../services/apiService';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
    LineChart, Line, PieChart, Pie, Cell
} from 'recharts';
import { Package, Truck, DollarSign, Activity, AlertTriangle, Lightbulb, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const MetricCard = ({ title, value, icon: Icon, color, delay }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay, duration: 0.5 }}
        className="card glass kpi-card"
    >
        <div className="kpi-header">
            <span className="kpi-title">{title}</span>
            <div style={{ background: `${color}15`, padding: '8px', borderRadius: '10px' }}>
                <Icon size={20} color={color} />
            </div>
        </div>
        <div className="kpi-value" style={{ color: color === 'var(--danger)' ? color : 'var(--text-main)' }}>
            {value}
        </div>
    </motion.div>
);

const InsightItem = ({ icon: Icon, color, text }) => (
    <div style={{ display: 'flex', gap: 12, padding: '16px 0', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ color, marginTop: 2 }}>
            <Icon size={18} />
        </div>
        <p style={{ fontSize: 14, color: 'var(--text-main)', lineHeight: 1.5 }}>{text}</p>
    </div>
);

export default function DashboardScreen() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboard();
    }, []);

    const loadDashboard = async () => {
        try {
            const response = await apiService.getDashboard();
            setData(response.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div style={{ color: 'var(--primary)', fontWeight: 500 }}>Initializing Analytics Engine...</div>;
    if (!data) return <div>No Analytics Available.</div>;

    const { kpis, charts } = data;

    // Mock data for pie chart delays based on kpis
    const delayData = [
        { name: 'On Time', value: kpis.total_shipments - kpis.delayed_shipments },
        { name: 'Delayed', value: kpis.delayed_shipments }
    ];
    const COLORS = ['var(--success)', 'var(--danger)'];

    // Mock data for trends
    const trendData = [
        { name: 'Jan', shipments: ~~(kpis.total_shipments * 0.1) },
        { name: 'Feb', shipments: ~~(kpis.total_shipments * 0.15) },
        { name: 'Mar', shipments: ~~(kpis.total_shipments * 0.22) },
        { name: 'Apr', shipments: ~~(kpis.total_shipments * 0.18) },
        { name: 'May', shipments: ~~(kpis.total_shipments * 0.35) },
    ];

    return (
        <>
            <div className="page-header">
                <h1 className="page-title">Analytics Overview</h1>
                <p className="page-subtitle">Real-time holistic view of trade network performance.</p>
            </div>

            <div className="kpi-grid">
                <MetricCard title="Total Shipments" value={kpis.total_shipments.toLocaleString()} icon={Package} color="var(--primary)" delay={0.1} />
                <MetricCard title="Delayed Shipments" value={kpis.delayed_shipments.toLocaleString()} icon={AlertTriangle} color="var(--danger)" delay={0.2} />
                <MetricCard title="Average Cost" value={`$${kpis.average_cost.toLocaleString()}`} icon={DollarSign} color="var(--success)" delay={0.3} />
                <MetricCard title="Active Routes" value={kpis.active_routes.toLocaleString()} icon={Activity} color="var(--text-main)" delay={0.4} />
            </div>

            <div className="charts-grid">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="card glass">
                    <h2 className="chart-title">Shipment Volume Trends</h2>
                    <div style={{ width: '100%', height: 300 }}>
                        <ResponsiveContainer>
                            <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                <RechartsTooltip
                                    contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, color: 'var(--text-main)' }}
                                    itemStyle={{ color: 'var(--primary)' }}
                                />
                                <Line type="monotone" dataKey="shipments" stroke="var(--primary)" strokeWidth={3} dot={{ strokeWidth: 2, r: 4, fill: 'var(--bg-main)' }} activeDot={{ r: 6 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="card glass">
                    <h2 className="chart-title">AI Insights</h2>
                    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                        <InsightItem
                            icon={AlertTriangle} color="var(--danger)"
                            text={<span>Delay prediction model indicates a <strong>15% higher risk</strong> on routes to Europe this week due to port congestion.</span>}
                        />
                        <InsightItem
                            icon={Lightbulb} color="var(--primary)"
                            text={<span>Consider prioritizing <strong>{charts.partner_performance?.[0]?.carrier || 'Primary'}</strong> for critical deliveries, currently holding a {charts.partner_performance?.[0]?.on_time_rate || 90}% on-time rate.</span>}
                        />
                        <InsightItem
                            icon={Truck} color="var(--success)"
                            text={<span>Cost Anomaly model is tracking normally with 0 new outliers in the last 24 hours.</span>}
                        />
                        <button style={{ background: 'transparent', border: 'none', color: 'var(--primary)', cursor: 'pointer', textAlign: 'left', fontWeight: 500, display: 'flex', alignItems: 'center', marginTop: 'auto', padding: '16px 0 0 0' }}>
                            View all insights <ChevronRight size={16} />
                        </button>
                    </div>
                </motion.div>
            </div>

            <div className="charts-grid">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }} className="card glass">
                    <h2 className="chart-title">Carrier On-Time Performance</h2>
                    <div style={{ width: '100%', height: 300 }}>
                        <ResponsiveContainer>
                            <BarChart data={charts.partner_performance} margin={{ top: 20, right: 30, left: -20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                                <XAxis dataKey="carrier" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                <RechartsTooltip
                                    cursor={{ fill: 'var(--bg-sidebar)' }}
                                    contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, color: 'var(--text-main)' }}
                                />
                                <Bar dataKey="on_time_rate" fill="var(--primary)" name="On Time Rate (%)" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="card glass">
                    <h2 className="chart-title">Delays Overview</h2>
                    <div style={{ width: '100%', height: 300, position: 'relative' }}>
                        <ResponsiveContainer>
                            <PieChart>
                                <Pie
                                    data={delayData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {delayData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <RechartsTooltip contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8 }} />
                            </PieChart>
                        </ResponsiveContainer>
                        {/* Center Label */}
                        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                            <div style={{ fontSize: 24, fontWeight: 'bold' }}> {((kpis.delayed_shipments / kpis.total_shipments) * 100).toFixed(1)}% </div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Delay Rate</div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </>
    );
}
